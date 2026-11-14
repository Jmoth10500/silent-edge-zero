"""Observability: alerts computed from the data itself (spec section 12) and
the Data Integrity Status that is DERIVED from them — status becomes OK only
because every check passes, never because a warning was removed by hand.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")
COVERAGE_WARN, COVERAGE_CRIT = 0.70, 0.30
COLLECTOR_STALE = timedelta(minutes=90)
RACING_HOURS = (9, 20)
FALLBACK_USAGE_WARN = 0.20
RESULT_STALE_AFTER = timedelta(hours=3)


@dataclass
class Alert:
    kind: str
    severity: str            # INFO | WARN | CRITICAL
    message: str
    link: str = ""           # where to find the raw record / audit log
    race_ids: list = field(default_factory=list)


def status_from_alerts(alerts: list) -> str:
    if any(a.severity == "CRITICAL" for a in alerts):
        return "FAIL"
    if any(a.severity == "WARN" for a in alerts):
        return "WARNING"
    return "OK"


def _off_utc(race_date, off_time):
    return datetime.combine(race_date, off_time).replace(tzinfo=LONDON).astimezone(timezone.utc)


def collect_alerts(conn, today: date, now: Optional[datetime] = None, reconciliation: Optional[list] = None) -> list:
    now = now or datetime.now(timezone.utc)
    cur = conn.cursor()
    alerts: list = []
    A = lambda *a, **k: alerts.append(Alert(*a, **k))

    # --- market capture coverage per recent past day --------------------------
    cur.execute("""
        SELECT r.race_date, count(DISTINCT r.id),
               count(DISTINCT r.id) FILTER (WHERE EXISTS (
                   SELECT 1 FROM price_observation po WHERE po.race_id = r.id AND po.back_price IS NOT NULL
                     AND po.price_quality = 'ok'
                     AND po.captured_at BETWEEN race_off_utc(r.race_date, r.off_time) - interval '30 minutes'
                                            AND race_off_utc(r.race_date, r.off_time) - interval '60 seconds'))
        FROM race r
        WHERE r.race_date BETWEEN %s AND %s AND NOT EXISTS (SELECT 1 FROM excluded_race x WHERE x.race_id = r.id)
          AND EXISTS (SELECT 1 FROM prediction p WHERE p.race_id = r.id)
          AND race_off_utc(r.race_date, r.off_time) < %s
        GROUP BY 1 ORDER BY 1""", (today - timedelta(days=3), today, now))
    for d, total, covered in cur.fetchall():
        if not total:
            continue
        cov = covered / total
        sev = "CRITICAL" if cov < COVERAGE_CRIT else "WARN" if cov < COVERAGE_WARN else None
        if sev:
            A("MARKET_COVERAGE_LOW", sev, f"{d}: lock-time exchange snapshot for only {covered}/{total} races ({cov:.0%})",
              "market_snapshot / price_observation view")

    # --- collector liveness ----------------------------------------------------
    cur.execute("SELECT max(observed_at) FROM market_snapshot")
    last_snap = cur.fetchone()[0]
    cur.execute("""SELECT count(*), count(*) FILTER (WHERE race_off_utc(race_date, off_time) > %s)
                   FROM race WHERE race_date = %s""", (now, today))
    n_today, n_pending_today = cur.fetchone()
    local = now.astimezone(LONDON)
    if n_today:
        if last_snap is None or now - last_snap > timedelta(hours=24):
            A("MARKET_COLLECTOR_DOWN", "CRITICAL",
              f"no market snapshot written for >24h (last: {last_snap}) while {n_today} races are scheduled today",
              "logs/collect_smarkets_prices_error.log")
        elif RACING_HOURS[0] <= local.hour < RACING_HOURS[1] and n_pending_today and now - last_snap > COLLECTOR_STALE:
            A("MARKET_COLLECTOR_STALE", "CRITICAL", f"last snapshot {(now - last_snap).total_seconds() / 60:.0f} min ago "
              f"(threshold {COLLECTOR_STALE.total_seconds() / 60:.0f} min) with races still to run", "logs/collect_smarkets_prices.log")
    cur.execute("""SELECT count(*), max(raised_at) FROM integrity_alert
                   WHERE alert_type = 'MARKET_API_ERROR' AND raised_at > %s""", (now - timedelta(hours=3),))
    n_err, last_err = cur.fetchone()
    if n_err >= 3:
        A("MARKET_API_ERRORS", "CRITICAL", f"{n_err} market API errors in the last 3h (latest {last_err})", "integrity_alert")

    # --- fallback / spread quality ----------------------------------------------
    cur.execute("""SELECT count(*), count(*) FILTER (WHERE is_fallback) FROM market_price_snapshot WHERE captured_at > %s""",
                (now - timedelta(days=1),))
    tot, fb = cur.fetchone()
    if tot and fb / tot > FALLBACK_USAGE_WARN:
        A("FALLBACK_USAGE_HIGH", "WARN", f"fallback prices are {fb}/{tot} of the last day's captures", "market_price_snapshot")
    cur.execute("""SELECT count(*), count(*) FILTER (WHERE price_quality <> 'ok') FROM market_snapshot WHERE observed_at > %s""",
                (now - timedelta(days=1),))
    tot, bad = cur.fetchone()
    if tot and bad / tot > 0.25:
        A("IMPLAUSIBLE_PRICES", "WARN", f"{bad}/{tot} recent snapshots are thin_book/wide_spread", "market_snapshot.price_quality")

    # --- price used for settlement must never be post-off ------------------------
    cur.execute("""SELECT count(*) FROM bet_settlement b JOIN race r ON r.id = b.race_id
                   WHERE b.price_timestamp IS NOT NULL
                     AND b.price_timestamp > race_off_utc(r.race_date, r.off_time)""")
    n = cur.fetchone()[0]
    if n:
        A("POST_OFF_PRICE_USED", "CRITICAL", f"{n} settlements use a price timestamped after the off", "bet_settlement")

    # --- identity / duplicates ---------------------------------------------------
    cur.execute("""SELECT provider_race_id, count(*) FROM canonical_race WHERE provider_race_id IS NOT NULL
                   GROUP BY 1 HAVING count(*) > 1""")
    for pid, n in cur.fetchall():
        A("CONFLICTING_RACE_IDS", "CRITICAL", f"provider race id {pid} on {n} canonical races", "canonical_race")
    cur.execute("""SELECT r.race_date, count(*) FROM race_integrity ri JOIN race r ON r.id = ri.race_id
                   WHERE NOT ri.include_in_metrics AND r.race_date >= %s GROUP BY 1 ORDER BY 1""", (today,))
    for d, n in cur.fetchall():
        A("DUPLICATE_RACES_ACTIVE_DATE", "WARN", f"{n} race(s) on {d} classified as duplicates/invalid but still current",
          "race_integrity / correction_ledger")
    cur.execute("""SELECT count(*) FROM (SELECT DISTINCT ON (race_id) race_id, status, failed_rules FROM race_validation
                   WHERE race_id IN (SELECT id FROM race WHERE race_date >= %s) ORDER BY race_id, id DESC) v
                   WHERE v.status = 'QUARANTINED'""", (today,))
    nq = cur.fetchone()[0]
    if nq:
        A("RACES_QUARANTINED", "WARN", f"{nq} race(s) today/future are under review and not being scored", "race_validation")
    cur.execute("""SELECT count(*) FROM (SELECT DISTINCT ON (race_id) race_id, failed_rules FROM race_validation
                   WHERE race_id IN (SELECT id FROM race WHERE race_date >= %s) ORDER BY race_id, id DESC) v
                   WHERE 'V07_RUNNER_IN_MULTIPLE_RACES_AT_MEETING' = ANY(v.failed_rules)""", (today,))
    n = cur.fetchone()[0]
    if n:
        A("DUPLICATE_RUNNER_ASSIGNMENT", "WARN", f"{n} race(s) share a runner with another race at the meeting", "race_validation")

    # --- feeds ------------------------------------------------------------------
    cur.execute("SELECT max(fetched_at) FROM race_feed_snapshot WHERE target_date = %s", (today,))
    feed_at = cur.fetchone()[0]
    if n_today and (feed_at is None or feed_at.astimezone(LONDON).date() != local.date()) and local.hour >= 9:
        A("STALE_FEED", "WARN", f"no racecard feed snapshot for {today} fetched today (last: {feed_at}); "
          "races predate the integrity layer or collection failed", "race_feed_snapshot")
    cur.execute("""SELECT count(*) FROM race r WHERE r.race_date = %s
                     AND race_off_utc(r.race_date, r.off_time) < %s
                     AND NOT EXISTS (SELECT 1 FROM runner_result x WHERE x.race_id = r.id)
                     AND NOT EXISTS (SELECT 1 FROM excluded_race e WHERE e.race_id = r.id)""",
                (today, now - RESULT_STALE_AFTER))
    n = cur.fetchone()[0]
    if n:
        A("RESULT_FEED_STALE", "WARN", f"{n} race(s) finished >3h ago with no result", "runner_result")

    # --- impossible timestamps / settlement ---------------------------------------
    cur.execute("""SELECT count(*) FROM prediction_lock pl JOIN race r ON r.id = pl.race_id
                   WHERE pl.provenance = 'LIVE_GATED'
                     AND pl.locked_at > race_off_utc(r.race_date, r.off_time)""")
    n = cur.fetchone()[0]
    if n:
        A("IMPOSSIBLE_TIMESTAMP", "CRITICAL", f"{n} prediction lock(s) timestamped after the scheduled off", "prediction_lock")
    cur.execute("""SELECT count(*), array_agg(DISTINCT result_note) FROM runner_result
                   WHERE finishing_position IS NULL AND result_note IS NOT NULL
                     AND upper(result_note) NOT IN ('PU','F','FELL','UR','SU','U','REF','RR','RO','BD','CO','DSQ','NR','WD','VOID','ABD')""")
    n, notes = cur.fetchone()
    if n:
        A("UNKNOWN_RESULT_CODE", "WARN", f"{n} result rows carry an unmapped code {notes}; left unsettled, not guessed", "runner_result")

    # --- denominators -----------------------------------------------------------
    for name, a, b, ok in (reconciliation or []):
        if not ok:
            A("RECONCILIATION_FAILURE", "CRITICAL", f"{name}: {a} != {b}", "metric_snapshot")

    cur.close()
    return alerts
