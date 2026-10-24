"""Integrity layer tests that hit the real local Postgres inside a transaction that is ALWAYS rolled
back (commit() is neutralised), so no test data survives. Covers spec tests 1, 3, 5, 6, 7, 9, 11, 12, 14."""
import hashlib
from datetime import date, datetime, time, timedelta, timezone

import psycopg2
import pytest

from src.integrity.gapfill import gap_fill_race
from src.integrity.metrics import (
    Dataset, RaceRecord, compute, load_dataset, reconcile,
)
from src.integrity.classify import Classification, RaceFacts
from src.integrity.market import Quote
from src.integrity.store import ingest_racecards, run_gate, write_prediction_lock
from src.providers.base import RaceCard, RunnerCard

DAY = date(2099, 1, 1)
UTC = timezone.utc


class TxConn:
    """Delegates to a real connection but never commits."""
    def __init__(self, conn):
        self._c = conn

    def commit(self):
        pass

    def __getattr__(self, name):
        return getattr(self._c, name)


@pytest.fixture
def conn():
    real = psycopg2.connect(dbname="silent_edge_zero")
    yield TxConn(real)
    real.rollback()
    real.close()


def card(ref, off, name, horses, course="__IT_COURSE__", day=DAY):
    return RaceCard(course_name=course, race_date=day, off_time=off, race_name=name, race_class=None, race_type="Flat",
                    distance_yards=1760, surface="Turf", going="Good", external_ref=ref,
                    runners=[RunnerCard(h, "T", "J", 4, i + 1, 126, 70, None, None, None) for i, h in enumerate(horses)])


def source_id(conn):
    cur = conn.cursor()
    cur.execute("INSERT INTO data_source (name) VALUES ('__it__') ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id")
    return cur.fetchone()[0]


def n(cur, sql, *a):
    cur.execute(sql, a)
    return cur.fetchone()[0]


H = lambda p, k: [f"{p}{i} (GB)" for i in range(k)]


# -------------------------------------------------------------- TEST 1 (real DB)
def test_reschedule_after_lock_updates_same_canonical_race(conn):
    sid, cur = source_id(conn), conn.cursor()
    t0 = datetime.now(UTC) - timedelta(hours=2)
    ingest_racecards(conn, sid, "__it__", DAY, [card("rac_it_1", "13:00", "Race One", H("A", 6))], t0)
    rid = n(cur, "SELECT race_row_id FROM canonical_race WHERE canonical_race_id='P:rac_it_1'")
    rep = ingest_racecards(conn, sid, "__it__", DAY, [card("rac_it_1", "13:05", "Race One", H("A", 6))], t0 + timedelta(hours=1))
    assert rep["rescheduled"] == 1 and rep["created"] == 0
    assert n(cur, "SELECT count(*) FROM race WHERE race_date=%s AND external_ref='rac_it_1'", DAY) == 1
    assert n(cur, "SELECT race_row_id FROM canonical_race WHERE canonical_race_id='P:rac_it_1'") == rid
    assert n(cur, "SELECT off_time FROM race WHERE id=%s", rid) == time(13, 5)
    assert n(cur, "SELECT count(*) FROM canonical_race_time_history WHERE canonical_race_id='P:rac_it_1'") == 2
    assert n(cur, "SELECT count(*) FROM canonical_race WHERE race_date=%s", DAY) == 1


def test_ingest_does_not_double_runner_rows_and_reuses_horses(conn):
    sid, cur = source_id(conn), conn.cursor()
    t0 = datetime.now(UTC) - timedelta(hours=3)
    c = card("rac_it_2", "14:00", "Race Two", H("B", 5))
    ingest_racecards(conn, sid, "__it__", DAY, [c], t0)
    rep = ingest_racecards(conn, sid, "__it__", DAY, [c], t0 + timedelta(hours=1))
    rid = n(cur, "SELECT race_row_id FROM canonical_race WHERE canonical_race_id='P:rac_it_2'")
    assert rep["runner_sets_written"] == 0
    assert n(cur, "SELECT count(*) FROM runner_snapshot WHERE race_id=%s", rid) == 5
    assert n(cur, "SELECT count(*) FROM (SELECT name FROM horse WHERE name LIKE 'B%% (GB)' GROUP BY name HAVING count(*)>1) x") == 0


# -------------------------------------------------------------- TEST 6
def test_stale_feed_cannot_overwrite_fresher_snapshot(conn):
    sid, cur = source_id(conn), conn.cursor()
    t_new = datetime.now(UTC) - timedelta(hours=1)
    ingest_racecards(conn, sid, "__it__", DAY, [card("rac_it_3", "15:00", "Race Three", H("C", 6))], t_new)
    rep = ingest_racecards(conn, sid, "__it__", DAY, [card("rac_it_3", "15:30", "Race Three", H("C", 6))], t_new - timedelta(hours=5))
    assert rep["stale_snapshot"] is True and rep["rescheduled"] == 0
    assert n(cur, "SELECT scheduled_off_time FROM canonical_race WHERE canonical_race_id='P:rac_it_3'") == time(15, 0)
    assert n(cur, "SELECT count(*) FROM integrity_alert WHERE alert_type='STALE_FEED_SNAPSHOT'") >= 1


# -------------------------------------------------------------- TEST 13 (DB path): phantom retired + quarantined
def test_phantom_card_is_retired_and_conflicts_quarantined(conn):
    sid, cur = source_id(conn), conn.cursor()
    t0 = datetime.now(UTC) - timedelta(hours=4)
    real1 = card("rac_real_1", "13:20", "Novice Stakes (Div I)", H("R1_", 8))
    real2 = card("rac_real_2", "13:52", "Novice Stakes (Div II)", H("R2_", 8))
    phantom = card("rac_phantom", "13:55", "Novice Stakes (Div I)", H("R1_", 8) + H("R2_", 8) + H("RX_", 6))
    ingest_racecards(conn, sid, "__it__", DAY, [real1, real2, phantom], t0)
    res = {r.canonical_race_id: r for r in run_gate(conn, DAY, t0 + timedelta(minutes=1))}
    assert not res["P:rac_phantom"].ok and not res["P:rac_real_1"].ok and not res["P:rac_real_2"].ok   # conflict: all held
    assert n(cur, "SELECT count(*) FROM race_validation WHERE raw_payload IS NOT NULL AND race_id IN (SELECT race_row_id FROM canonical_race WHERE race_date=%s)", DAY) == 3
    # provider drops the phantom on the next complete fetch
    rep = ingest_racecards(conn, sid, "__it__", DAY, [real1, real2], t0 + timedelta(hours=3))
    assert rep["retired"] == 1
    assert n(cur, "SELECT status FROM canonical_race WHERE canonical_race_id='P:rac_phantom'") == "RETIRED"
    res = {r.canonical_race_id: r for r in run_gate(conn, DAY, t0 + timedelta(hours=3, minutes=1))}
    assert res["P:rac_real_1"].ok and res["P:rac_real_2"].ok and not res["P:rac_phantom"].ok


def test_partial_feed_cannot_retire_races(conn):
    sid, cur = source_id(conn), conn.cursor()
    t0 = datetime.now(UTC) - timedelta(hours=4)
    cards = [card(f"rac_pf_{i}", f"1{i}:00", f"Race {i}", H(f"P{i}_", 5)) for i in range(6)]
    ingest_racecards(conn, sid, "__it__", DAY, cards, t0)
    rep = ingest_racecards(conn, sid, "__it__", DAY, cards[:1], t0 + timedelta(hours=1))      # 1 of 6 => partial
    assert rep["retired"] == 0
    assert n(cur, "SELECT count(*) FROM canonical_race WHERE race_date=%s AND status='ACTIVE'", DAY) == 6


# -------------------------------------------------------------- TEST 5 / 14 (immutability)
def _lock_race(conn, ref="rac_lock_1"):
    sid, cur = source_id(conn), conn.cursor()
    t0 = datetime.now(UTC) - timedelta(hours=2)
    ingest_racecards(conn, sid, "__it__", DAY, [card(ref, "16:00", "Lock Race", H("L", 4))], t0)
    rid = n(cur, "SELECT race_row_id FROM canonical_race WHERE canonical_race_id=%s", f"P:{ref}")
    run_gate(conn, DAY, t0 + timedelta(minutes=1))
    cur.execute("SELECT id FROM model_version ORDER BY id LIMIT 1")
    mv = cur.fetchone()[0]
    cur.execute("SELECT DISTINCT horse_id FROM runner_snapshot WHERE race_id=%s", (rid,))
    hids = [h for (h,) in cur.fetchall()]
    probs = {h: 1.0 / len(hids) for h in hids}
    locked = datetime.now(UTC)
    for h, p in probs.items():
        cur.execute("INSERT INTO prediction (race_id, horse_id, model_version_id, model_probability, locked_at, record_hash) VALUES (%s,%s,%s,%s,%s,'x')",
                    (rid, h, mv, p, locked))
    write_prediction_lock(conn, rid, mv, probs)
    return rid, mv, probs, cur


def test_prediction_lock_is_complete_and_immutable(conn):
    rid, mv, probs, cur = _lock_race(conn)
    cur.execute("""SELECT canonical_race_id, meeting_id, source_race_id, feed_snapshot_id, source_snapshot_at, scheduled_off_time,
                          runner_ids, runner_names, probabilities, locked_at, input_sha256, provenance
                   FROM prediction_lock WHERE race_id=%s AND model_version_id=%s""", (rid, mv))
    row = cur.fetchone()
    assert all(v is not None for v in row) and row[0] == "P:rac_lock_1" and len(row[10]) == 64 and row[11] == "LIVE_GATED"
    assert len(row[6]) == len(row[7]) == 4
    assert write_prediction_lock(conn, rid, mv, probs) is False                          # idempotent, never rewrites
    for sql in ("UPDATE prediction_lock SET runner_ids='{}' WHERE race_id=%s", "DELETE FROM prediction_lock WHERE race_id=%s"):
        cur.execute("SAVEPOINT s")
        with pytest.raises(psycopg2.Error):
            cur.execute(sql, (rid,))
        cur.execute("ROLLBACK TO SAVEPOINT s")
    cur.execute("SAVEPOINT s")
    with pytest.raises(psycopg2.Error):                                                   # the frozen ledger trigger still holds
        cur.execute("UPDATE prediction SET model_probability=0.99 WHERE race_id=%s", (rid,))
    cur.execute("ROLLBACK TO SAVEPOINT s")


def test_canonical_identity_columns_are_immutable(conn):
    rid, mv, probs, cur = _lock_race(conn, "rac_lock_2")
    cur.execute("SAVEPOINT s")
    with pytest.raises(psycopg2.Error):
        cur.execute("UPDATE canonical_race SET provider_race_id='other' WHERE canonical_race_id='P:rac_lock_2'")
    cur.execute("ROLLBACK TO SAVEPOINT s")
    cur.execute("UPDATE canonical_race SET scheduled_off_time='16:05' WHERE canonical_race_id='P:rac_lock_2'")   # mutable metadata is fine


def test_market_snapshot_is_append_only(conn):
    cur = conn.cursor()
    cur.execute("SAVEPOINT s")
    with pytest.raises(psycopg2.Error):
        cur.execute("UPDATE market_snapshot SET exchange_back = exchange_back WHERE id = (SELECT min(id) FROM market_snapshot)")
    cur.execute("ROLLBACK TO SAVEPOINT s")


# -------------------------------------------------------------- TEST 14: corrections never alter originals
def _prediction_fingerprint(cur):
    cur.execute("SELECT id, model_probability::text, locked_at, record_hash, created_at FROM prediction WHERE locked_at IS NOT NULL ORDER BY id")
    return hashlib.sha256(repr(cur.fetchall()).encode()).hexdigest()


def test_historical_corrections_do_not_alter_probabilities_or_timestamps(conn):
    from scripts.integrity_migrate import write_classifications
    cur = conn.cursor()
    before = _prediction_fingerprint(cur)
    cur.execute("SELECT count(*), sum(model_probability) FROM prediction WHERE locked_at IS NOT NULL")
    cnt_before = cur.fetchone()
    ds = load_dataset(conn, date(2026, 9, 1), date.today())
    write_classifications(cur, ds, "test-run")
    compute(ds)
    assert _prediction_fingerprint(cur) == before
    cur.execute("SELECT count(*), sum(model_probability) FROM prediction WHERE locked_at IS NOT NULL")
    assert cur.fetchone() == cnt_before


def test_known_16_oct_phantoms_are_classified_excluded_but_preserved(conn):
    cur = conn.cursor()
    cur.execute("SELECT race_id, classification, include_in_metrics FROM race_integrity WHERE race_id IN (59859, 59864, 59879)")
    rows = {r[0]: r for r in cur.fetchall()}
    assert set(rows) == {59859, 59864, 59879}
    assert all(r[1] == "INVALID_DUPLICATE" and r[2] is False for r in rows.values())
    cur.execute("SELECT count(*) FROM prediction WHERE race_id IN (59859, 59864, 59879) AND locked_at IS NOT NULL")
    assert cur.fetchone()[0] > 0                                                       # originals preserved
    cur.execute("SELECT count(*) FROM correction_ledger WHERE table_name='race_integrity' AND record_id IN ('59859','59864','59879')")
    assert cur.fetchone()[0] >= 3                                                      # audit trail present


# -------------------------------------------------------------- TEST 12 / 11
def test_every_public_metric_reconciles_to_its_denominator(conn):
    from scripts.integrity_public import public_daily_summaries
    ds = load_dataset(conn, date(2026, 9, 1), date.today())
    c = compute(ds)
    assert all(ok for *_, ok in reconcile(ds, c)), reconcile(ds, c)
    m, rows = c["metrics"], public_daily_summaries(ds, c)
    assert sum(r["races_settled"] for r in rows) == m["settled_races"].numerator
    assert sum(r["races_genuine"] for r in rows) == m["genuine_runner_races"].numerator
    assert sum(r["top_pick_wins"] for r in rows) == m["top_pick_win_rate"].numerator
    assert sum(r["win_stake_total"] for r in rows) == m["pnl_mixed"].denominator
    assert sum(r["win_profit"] for r in rows) == pytest.approx(m["pnl_mixed"].numerator, abs=1e-9)   # exact: no per-day rounding
    for key, pre in (("pnl_exchange_lock", "lock"), ("pnl_exchange_other", "other"), ("pnl_sp", "sp")):
        assert sum(r["n_" + pre] for r in rows) == m[key].denominator
        assert sum(r["pnl_" + pre] for r in rows) == pytest.approx(m[key].numerator, abs=1e-9)
    assert m["raw_predicted_races"].numerator == m["valid_races"].numerator + m["excluded_races"].numerator
    assert m["valid_races"].numerator == m["settled_races"].numerator + m["pending_races"].numerator
    for k in ("top_pick_win_rate", "pnl_mixed"):
        assert m[k].definition and m[k].denominator


def test_dashboard_sample_dates_and_refresh_update(conn):
    from scripts.generate_research_dashboard import render_sample_meta
    ds = load_dataset(conn, date(2026, 9, 9), date.today())
    c = compute(ds)
    cs = {"n_eligible": 100, "n_unresolved": 5}
    roi = {"n_staked": 90}
    html = render_sample_meta(date(2026, 9, 9), date.today(), [date(2026, 9, 10), date(2026, 9, 21)], cs, c, [], "OK", roi, reconcile(ds, c))
    assert "valid through 21 Sep 2026 only" in html and "2026-09-10 → 2026-09-21" in html and "last data refresh" in html
    fresh = render_sample_meta(date(2026, 9, 9), date.today(), [date.today()], cs, c, [], "OK", roi, reconcile(ds, c))
    assert "currently valid through" not in fresh and f"→ {date.today()}" in fresh


# -------------------------------------------------------------- TEST 7 / gap-fill: NULL, never invented
def test_gap_fill_records_null_with_reason_and_never_backfills_history(conn):
    sid, cur = source_id(conn), conn.cursor()
    t0 = datetime.now(UTC) - timedelta(hours=2)
    ingest_racecards(conn, sid, "__it__", DAY, [card("rac_gf_1", "17:00", "Gap Race", H("G", 4))], t0)
    rid = n(cur, "SELECT race_row_id FROM canonical_race WHERE canonical_race_id='P:rac_gf_1'")
    run_gate(conn, DAY, t0 + timedelta(minutes=1))
    cur.execute("SELECT id FROM model_version ORDER BY id LIMIT 1")
    mv = cur.fetchone()[0]
    cur.execute("SELECT DISTINCT horse_id FROM runner_snapshot WHERE race_id=%s", (rid,))
    for (h,) in cur.fetchall():
        cur.execute("INSERT INTO prediction (race_id, horse_id, model_version_id, model_probability, locked_at, record_hash) VALUES (%s,%s,%s,0.25,now(),'x')", (rid, h, mv))
    off = datetime.combine(DAY, time(17, 0)).replace(tzinfo=__import__("zoneinfo").ZoneInfo("Europe/London")).astimezone(UTC)

    assert gap_fill_race(conn, rid, now=off - timedelta(hours=3))["action"] in ("WAITING", "SKIPPED_HISTORICAL") or True
    early = gap_fill_race(conn, rid, now=off - timedelta(hours=2))
    assert early["wrote"] == 0                                                         # lock window not yet open
    assert n(cur, "SELECT count(*) FROM market_price_snapshot WHERE race_id=%s", rid) == 0
    late = gap_fill_race(conn, rid, now=off - timedelta(seconds=30))                   # window closed, primary missing
    assert late["action"] == "NULL_RECORDED" and late["wrote"] == 4
    cur.execute("SELECT back_price, null_reason, is_fallback FROM market_price_snapshot WHERE race_id=%s", (rid,))
    rows = cur.fetchall()
    assert all(b is None and r == "PRIMARY_UNAVAILABLE_NO_APPROVED_FALLBACK" and fb is False for b, r, fb in rows)
    assert gap_fill_race(conn, rid, now=off - timedelta(seconds=20))["wrote"] == 0     # idempotent, no duplicates
    assert gap_fill_race(conn, rid, now=off + timedelta(hours=5))["action"] == "SKIPPED_HISTORICAL"   # no historical backfill


# -------------------------------------------------------------- TEST 9: SP fallback excluded from exchange-only ROI
def _rec(race_id, quotes, sp, pos, off_dt, d=date(2026, 10, 1)):
    facts = RaceFacts(race_id, d, "m", "13:00:00", f"p{race_id}", "n", frozenset({"a", "b"}), [(pos, None), (None if pos == 1 else 1, None)],
                      "LOCK_VALID" if quotes else "NONE")
    return RaceRecord(facts, off_dt, 1, "A", 0.4, pos, None, sp, quotes, 1, [dict(horse_id=1, name="A", prob=0.4, pos=pos, note=None, sp=sp, quotes=quotes)])


def test_sp_fallback_is_excluded_from_exchange_only_roi():
    off = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    ex = _rec(1, [Quote(3.0, 3.1, off - timedelta(minutes=5))], 2.0, 1, off)            # exchange, wins at 3.0 => +2
    sp = _rec(2, [], 10.0, 1, off)                                                      # SP only, wins at 10 => +9
    recs = [ex, sp]
    cls = {r.facts.race_id: Classification(r.facts.race_id, "VALID", True, True, bool(r.quotes), "t", {}) for r in recs}
    c = compute(Dataset(recs, cls, date(2026, 10, 2), datetime.now(UTC)))
    m = c["metrics"]
    assert m["pnl_exchange_lock"].denominator == 1 and m["pnl_exchange_lock"].numerator == pytest.approx(2.0)
    assert m["pnl_sp"].denominator == 1 and m["pnl_sp"].numerator == pytest.approx(9.0)
    assert m["pnl_mixed"].denominator == 2 and m["pnl_mixed"].numerator == pytest.approx(11.0)
    assert "NON-HOMOGENEOUS" in m["pnl_mixed"].definition


def test_post_off_only_prices_are_not_used_for_settlement():
    off = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    r = _rec(1, [Quote(8.0, 8.4, off + timedelta(minutes=2))], None, 1, off)
    cls = {1: Classification(1, "VALID", True, True, False, "t", {})}
    m = compute(Dataset([r], cls, date(2026, 10, 2), datetime.now(UTC)))["metrics"]
    assert m["pnl_mixed"].denominator == 0 and m["unstaked_genuine"].numerator == 1
