"""
Leakage / time-travel tests (build brief Section 6 and 30).

The core rule: a prediction made at time T must never be built from data
whose available_at is after T. These tests exercise the query-time filter
directly against the real database (not mocked), so a schema or query
change that reintroduces leakage actually gets caught.

Run: python3 tests/test_leakage.py
Requires: db/init_db.py already run (silent_edge_zero database exists).
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2


def get_conn():
    return psycopg2.connect(dbname="silent_edge_zero")


def leakage_safe_snapshot_query(conn, race_id: int, horse_id: int, prediction_time: datetime):
    """The canonical 'what did we know at time T' query. Every feature-building
    step in the real pipeline MUST go through a query shaped like this —
    never a bare SELECT * FROM runner_snapshot WHERE race_id = ...
    """
    cur = conn.cursor()
    cur.execute(
        """SELECT id, official_rating, draw, available_at
           FROM runner_snapshot
           WHERE race_id = %s AND horse_id = %s AND available_at <= %s
           ORDER BY available_at DESC LIMIT 1""",
        (race_id, horse_id, prediction_time),
    )
    return cur.fetchone()


def test_future_snapshot_is_excluded():
    """Insert a snapshot available_at 2 hours in the future relative to the
    prediction time, and confirm the leakage-safe query does NOT return it."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("INSERT INTO course (name, country) VALUES ('__TEST_COURSE__', 'GB') "
                "ON CONFLICT (name) DO NOTHING RETURNING id")
    row = cur.fetchone()
    if row is None:
        cur.execute("SELECT id FROM course WHERE name = '__TEST_COURSE__'")
        row = cur.fetchone()
    course_id = row[0]

    cur.execute(
        "INSERT INTO race (course_id, race_date, off_time, race_name) "
        "VALUES (%s, CURRENT_DATE, '14:00', '__TEST_RACE__') "
        "ON CONFLICT (course_id, race_date, off_time) DO UPDATE SET race_name = EXCLUDED.race_name "
        "RETURNING id",
        (course_id,),
    )
    race_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO horse (name, foaled_year) VALUES ('__TEST_HORSE__', 2020) "
        "ON CONFLICT (name, foaled_year) DO UPDATE SET name = EXCLUDED.name RETURNING id"
    )
    horse_id = cur.fetchone()[0]

    now = datetime.now(timezone.utc)
    prediction_time = now
    future_available_at = now + timedelta(hours=2)
    past_available_at = now - timedelta(hours=1)

    # A snapshot that becomes available AFTER our prediction time — this is
    # the leak. It must never be visible to the leakage-safe query.
    cur.execute(
        """INSERT INTO runner_snapshot
           (race_id, horse_id, official_rating, draw, observed_at, available_at)
           VALUES (%s, %s, 999, 9, %s, %s)""",
        (race_id, horse_id, future_available_at, future_available_at),
    )
    # A legitimate snapshot available before prediction time.
    cur.execute(
        """INSERT INTO runner_snapshot
           (race_id, horse_id, official_rating, draw, observed_at, available_at)
           VALUES (%s, %s, 85, 4, %s, %s)""",
        (race_id, horse_id, past_available_at, past_available_at),
    )
    conn.commit()

    result = leakage_safe_snapshot_query(conn, race_id, horse_id, prediction_time)
    assert result is not None, "expected the past snapshot to be found"
    official_rating = result[1]
    assert official_rating == 85, (
        f"LEAKAGE DETECTED: query returned official_rating={official_rating}, "
        f"expected 85 (the past snapshot) — the future snapshot (rating 999) leaked through"
    )

    # cleanup
    cur.execute("DELETE FROM runner_snapshot WHERE race_id = %s", (race_id,))
    cur.execute("DELETE FROM race WHERE id = %s", (race_id,))
    cur.execute("DELETE FROM horse WHERE id = %s", (horse_id,))
    cur.execute("DELETE FROM course WHERE id = %s", (course_id,))
    conn.commit()
    cur.close()
    conn.close()


def test_prediction_table_has_no_update_path():
    """Structural check: confirm the prediction table has a locked_at column
    that the immutability trigger (below) actually enforces against."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'prediction' AND column_name = 'locked_at'"
    )
    assert cur.fetchone() is not None, "prediction.locked_at column missing — immutability guard can't work"
    cur.close()
    conn.close()


def test_locked_prediction_cannot_be_updated():
    """Database-level enforcement test (Section 32): once locked_at is set
    on a prediction row, the trg_prevent_locked_prediction_update trigger
    must reject ANY update to that row — not just app-layer discipline.
    An unlocked row (locked_at IS NULL) must still be freely updatable,
    since that's how a row gets locked in the first place."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("INSERT INTO course (name, country) VALUES ('__TEST_COURSE_2__', 'GB') "
                "ON CONFLICT (name) DO NOTHING RETURNING id")
    row = cur.fetchone()
    if row is None:
        cur.execute("SELECT id FROM course WHERE name = '__TEST_COURSE_2__'")
        row = cur.fetchone()
    course_id = row[0]

    cur.execute(
        "INSERT INTO race (course_id, race_date, off_time, race_name) "
        "VALUES (%s, CURRENT_DATE, '15:00', '__TEST_RACE_2__') "
        "ON CONFLICT (course_id, race_date, off_time) DO UPDATE SET race_name = EXCLUDED.race_name "
        "RETURNING id",
        (course_id,),
    )
    race_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO horse (name, foaled_year) VALUES ('__TEST_HORSE_2__', 2020) "
        "ON CONFLICT (name, foaled_year) DO UPDATE SET name = EXCLUDED.name RETURNING id"
    )
    horse_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO model_version (name, version) VALUES ('__TEST_MODEL__', 'v0') "
        "ON CONFLICT (name, version) DO UPDATE SET name = EXCLUDED.name RETURNING id"
    )
    model_version_id = cur.fetchone()[0]

    now = datetime.now(timezone.utc)

    # An unlocked prediction: must still be updatable (this is how locking happens).
    cur.execute(
        """INSERT INTO prediction (race_id, horse_id, model_version_id, model_probability)
           VALUES (%s, %s, %s, 0.20) RETURNING id""",
        (race_id, horse_id, model_version_id),
    )
    unlocked_id = cur.fetchone()[0]
    conn.commit()

    cur.execute("UPDATE prediction SET model_probability = 0.25 WHERE id = %s", (unlocked_id,))
    conn.commit()
    cur.execute("SELECT model_probability FROM prediction WHERE id = %s", (unlocked_id,))
    assert float(cur.fetchone()[0]) == 0.25, "an unlocked prediction row should be freely updatable"

    # Lock it, then confirm the trigger rejects any further update.
    cur.execute("UPDATE prediction SET locked_at = %s WHERE id = %s", (now, unlocked_id))
    conn.commit()

    rejected = False
    try:
        cur.execute("UPDATE prediction SET model_probability = 0.99 WHERE id = %s", (unlocked_id,))
    except psycopg2.errors.RaiseException:
        rejected = True
        conn.rollback()
    else:
        conn.commit()

    assert rejected, (
        "LEAKAGE/INTEGRITY BUG: a locked prediction row was updated — "
        "trg_prevent_locked_prediction_update did not fire"
    )

    # cleanup
    cur.execute("DELETE FROM prediction WHERE id = %s", (unlocked_id,))
    cur.execute("DELETE FROM model_version WHERE id = %s", (model_version_id,))
    cur.execute("DELETE FROM race WHERE id = %s", (race_id,))
    cur.execute("DELETE FROM horse WHERE id = %s", (horse_id,))
    cur.execute("DELETE FROM course WHERE id = %s", (course_id,))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    tests = [
        test_future_snapshot_is_excluded,
        test_prediction_table_has_no_update_path,
        test_locked_prediction_cannot_be_updated,
    ]
    passed = 0
    for t in tests:
        print(f"{t.__name__}:")
        try:
            t()
            print("  PASS")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
    sys.exit(0 if passed == len(tests) else 1)
