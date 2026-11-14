"""Per-race market gap-filling (spec section 4). GAP-FILL ONLY.

For ONE race at a time, after the lock window has closed: if the primary
(Smarkets) lock-time snapshot is missing, either record a fallback price from
an APPROVED source for that race alone, or record NULL + reason code for each
runner. It never scrapes a day's odds, never backfills old races, never
overwrites a primary price, never labels a post-off price as lock-time.
APPROVED_FALLBACK_SOURCES ships empty, so today the outcome is always NULL.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Optional

from src.integrity.market import (
    APPROVED_FALLBACK_SOURCES, LOCK_WINDOW, NULL_PRIMARY_DOWN, PRE_OFF_BUFFER, Quote,
    fallback_decision, lock_market_state,
)
from src.integrity.metrics import off_datetime

# name -> callable(race_ctx) -> {horse_id: Quote}; empty until an owner-approved source exists.
FALLBACK_FETCHERS: dict = {}
MAX_RACE_AGE = timedelta(hours=3)       # window closed longer ago than this: do nothing (no historical backfill)


def gap_fill_race(conn, race_id: int, now: Optional[datetime] = None, job_id: Optional[str] = None,
                  fetchers: Optional[dict] = None) -> dict:
    now = now or datetime.now(timezone.utc)
    job_id = job_id or f"gapfill-{uuid.uuid4().hex[:8]}"
    fetchers = FALLBACK_FETCHERS if fetchers is None else fetchers
    cur = conn.cursor()
    cur.execute("""SELECT r.race_date, r.off_time, cr.canonical_race_id,
                          EXISTS (SELECT 1 FROM excluded_race x WHERE x.race_id = r.id),
                          COALESCE((SELECT status FROM race_validation v WHERE v.race_id = r.id ORDER BY v.id DESC LIMIT 1), 'NONE')
                   FROM race r LEFT JOIN canonical_race cr ON cr.race_row_id = r.id WHERE r.id = %s""", (race_id,))
    race_date, off_time, cid, excluded, vstatus = cur.fetchone()
    off_dt = off_datetime(race_date, off_time)
    validated = (vstatus == "VALID") and not excluded
    if now - off_dt > MAX_RACE_AGE:
        return dict(race_id=race_id, action="SKIPPED_HISTORICAL", wrote=0)

    cur.execute("SELECT DISTINCT horse_id FROM prediction WHERE race_id = %s AND locked_at IS NOT NULL", (race_id,))
    horses = [h for (h,) in cur.fetchall()]
    cur.execute("""SELECT horse_id, back_price, lay_price, captured_at, source_name, source_type, is_fallback, price_quality
                   FROM price_observation WHERE race_id = %s""", (race_id,))
    by_horse: dict = {}
    for hid, back, lay, at, sn, st, fb, pq in cur.fetchall():
        by_horse.setdefault(hid, []).append(Quote(float(back) if back is not None else None,
                                                  float(lay) if lay is not None else None, at, sn, st, fb, pq))
    missing = [h for h in horses if lock_market_state(by_horse.get(h, []), off_dt) != "LOCK_VALID"]
    if not missing:
        return dict(race_id=race_id, action="PRIMARY_OK", wrote=0)

    dec = fallback_decision(race_validated=validated, primary_lock_state="NONE", now=now, off_dt=off_dt)
    wrote = 0
    if dec.allowed:
        for name in dec.sources:
            fetch: Optional[Callable] = fetchers.get(name)
            if not fetch:
                continue
            quotes = fetch({"race_id": race_id, "canonical_race_id": cid, "off_dt": off_dt})   # ONE race only
            for hid in list(missing):
                q = quotes.get(hid)
                # Stamp with OUR clock, never a source-supplied time, and refuse anything outside the pre-off window.
                if q is None or q.back_price is None or now > off_dt - PRE_OFF_BUFFER or now < off_dt - LOCK_WINDOW:
                    continue
                cur.execute(
                    """INSERT INTO market_price_snapshot (race_id, horse_id, canonical_race_id, source_name, source_type,
                           is_fallback, back_price, lay_price, captured_at, checkpoint, secs_rel_off, api_status,
                           fallback_reason, job_id)
                       VALUES (%s,%s,%s,%s,%s,TRUE,%s,%s,%s,'LOCK',%s,'OK',%s,%s)""",
                    (race_id, hid, cid, name, APPROVED_FALLBACK_SOURCES[name], q.back_price, q.lay_price, now,
                     int((now - off_dt).total_seconds()), "primary lock-window snapshot missing", job_id))
                wrote += 1
                missing.remove(hid)
    # Anything still missing once the window has CLOSED is recorded as NULL + reason (never estimated).
    if now >= off_dt - PRE_OFF_BUFFER:
        reason = NULL_PRIMARY_DOWN if not APPROVED_FALLBACK_SOURCES else "PRIMARY_AND_FALLBACK_UNAVAILABLE"
        for hid in missing:
            cur.execute("SELECT 1 FROM market_price_snapshot WHERE race_id=%s AND horse_id=%s AND back_price IS NULL AND checkpoint='LOCK'",
                        (race_id, hid))
            if cur.fetchone():
                continue
            cur.execute(
                """INSERT INTO market_price_snapshot (race_id, horse_id, canonical_race_id, source_name, source_type,
                       is_fallback, captured_at, checkpoint, secs_rel_off, api_status, null_reason, job_id)
                   VALUES (%s,%s,%s,'smarkets','EXCHANGE',FALSE,%s,'LOCK',%s,'UNAVAILABLE',%s,%s)""",
                (race_id, hid, cid, now, int((now - off_dt).total_seconds()), reason, job_id))
            wrote += 1
    conn.commit()
    return dict(race_id=race_id, action="GAP_FILLED" if wrote and dec.allowed else "NULL_RECORDED" if wrote else "WAITING",
                wrote=wrote, decision=dec.reason)


def gap_fill_day(conn, race_date: date, now: Optional[datetime] = None) -> list:
    """Every race of the day, each evaluated independently (still per-race, never a bulk fetch)."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM race WHERE race_date = %s ORDER BY off_time", (race_date,))
    ids = [i for (i,) in cur.fetchall()]
    return [gap_fill_race(conn, i, now) for i in ids]
