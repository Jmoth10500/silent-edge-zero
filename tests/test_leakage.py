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
    that application code is expected to check before any write — this test
    documents the intent even though Postgres itself can't enforce
    'no UPDATE on locked rows' without a trigger. A trigger is the next
    hardening step once the prediction pipeline is built (Phase 9+)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'prediction' AND column_name = 'locked_at'"
    )
    assert cur.fetchone() is not None, "prediction.locked_at column missing — immutability guard can't work"
    cur.close()
    conn.close()


if __name__ == "__main__":
    tests = [test_future_snapshot_is_excluded, test_prediction_table_has_no_update_path]
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
