"""DB glue for the integrity layer: feed snapshots, canonical-keyed
ingestion, retirement of races that left the authoritative feed, the
validation gate, and immutable prediction-lock records.

Everything is additive. It never UPDATEs/DELETEs a locked prediction, a
runner_result or any historical row.
"""
import json
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Optional

from src.integrity.canonical import (
    build_input_snapshot, canonical_race_id as make_canonical_id, course_key, horse_key,
    meeting_id as make_meeting_id, parse_division, sha256_of,
)
from src.integrity.validation import RaceView, ValidationResult, validate_races

PARTIAL_FEED_RATIO = 0.5       # a snapshot with < 50% of the previous race count cannot retire races


# ----------------------------------------------------------------- feed ---
def _payload(racecards: list) -> list:
    out = []
    for rc in racecards:
        d = asdict(rc)
        d["race_date"] = rc.race_date.isoformat()
        out.append(d)
    return out


def record_feed_snapshot(cur, source: str, target_date: date, fetched_at: datetime, racecards: list):
    """Store the raw fetch. Returns (snapshot_id, is_stale). A snapshot older
    than one we already hold for the date is stored (for the record) but
    flagged stale: it must never be applied over fresher race metadata."""
    payload = _payload(racecards)
    cur.execute("SELECT max(fetched_at) FROM race_feed_snapshot WHERE source=%s AND target_date=%s",
                (source, target_date))
    newest = cur.fetchone()[0]
    is_stale = newest is not None and fetched_at < newest
    cur.execute(
        """INSERT INTO race_feed_snapshot (source, target_date, fetched_at, payload, payload_sha256, race_count)
           VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
        (source, target_date, fetched_at, json.dumps(payload), sha256_of(payload), len(payload)),
    )
    return cur.fetchone()[0], is_stale


def raise_alert(cur, alert_type: str, severity: str, message: str, race_id: Optional[int] = None, detail=None):
    cur.execute("INSERT INTO integrity_alert (alert_type, severity, race_id, message, detail) VALUES (%s,%s,%s,%s,%s)",
                (alert_type, severity, race_id, message, json.dumps(detail, default=str) if detail else None))


def ledger(cur, run_id: str, table: str, record_id, action: str, reason: str, before=None, after=None,
           actor: str = "integrity-pipeline"):
    cur.execute(
        """INSERT INTO correction_ledger (run_id, table_name, record_id, action, before_state, after_state, reason, actor)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (run_id, table, str(record_id), action,
         json.dumps(before, default=str) if before is not None else None,
         json.dumps(after, default=str) if after is not None else None, reason, actor))


# -------------------------------------------------------------- runners ---
def current_runners(cur, race_id: int) -> list:
    """The CURRENT runner set of a race: the rows of its latest ingest, de-duplicated
    by canonical horse key (maps around the duplicate `horse` rows), withdrawn
    horses excluded. Returns [(horse_id, horse_name)] ordered by name."""
    cur.execute(
        """SELECT rs.horse_id, h.name FROM runner_snapshot rs JOIN horse h ON h.id = rs.horse_id
           WHERE rs.race_id = %s AND rs.non_runner = FALSE
             AND rs.ingested_at = (SELECT max(ingested_at) FROM runner_snapshot WHERE race_id = %s)
           ORDER BY h.name, rs.horse_id""", (race_id, race_id))
    seen, out = set(), []
    for hid, name in cur.fetchall():
        k = horse_key(name)
        if k not in seen:
            seen.add(k)
            out.append((hid, name))
    return out


def _runner_signature(runners) -> str:
    return sha256_of(sorted(
        [horse_key(r.horse_name), r.draw, r.weight_lbs, r.official_rating, r.jockey_name, r.trainer_name]
        for r in runners))


def _existing_signature(cur, race_id: int) -> Optional[str]:
    cur.execute(
        """SELECT h.name, rs.draw, rs.weight_lbs, rs.official_rating, j.name, t.name
           FROM runner_snapshot rs JOIN horse h ON h.id = rs.horse_id
           LEFT JOIN jockey j ON j.id = rs.jockey_id LEFT JOIN trainer t ON t.id = rs.trainer_id
           WHERE rs.race_id = %s AND rs.non_runner = FALSE
             AND rs.ingested_at = (SELECT max(ingested_at) FROM runner_snapshot WHERE race_id = %s)""",
        (race_id, race_id))
    rows = cur.fetchall()
    if not rows:
        return None
    return sha256_of(sorted([horse_key(n), d, w, o, jn, tn] for n, d, w, o, jn, tn in rows))


def _get_or_create_horse(cur, name: str, source_id: int) -> int:
    """Reuse the existing horse row with this exact name instead of letting the
    NULL foaled_year bug mint a new duplicate on every ingest."""
    cur.execute("SELECT min(id) FROM horse WHERE name = %s", (name,))
    row = cur.fetchone()
    if row and row[0] is not None:
        return row[0]
    cur.execute("INSERT INTO horse (name, source_id) VALUES (%s,%s) RETURNING id", (name, source_id))
    return cur.fetchone()[0]


def _upsert_named(cur, table: str, name: str) -> int:
    cur.execute(f"INSERT INTO {table} (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id", (name,))
    return cur.fetchone()[0]


def _insert_runners(cur, race_id: int, runners: list, source_id: int, now: datetime):
    for rn in runners:
        horse_id = _get_or_create_horse(cur, rn.horse_name, source_id)
        trainer_id = _upsert_named(cur, "trainer", rn.trainer_name) if rn.trainer_name else None
        jockey_id = _upsert_named(cur, "jockey", rn.jockey_name) if rn.jockey_name else None
        cur.execute(
            """INSERT INTO runner_snapshot (race_id, horse_id, trainer_id, jockey_id, age, draw, weight_lbs,
                   official_rating, recent_form, equipment, observed_at, available_at, ingested_at, source_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (race_id, horse_id, trainer_id, jockey_id, rn.age, rn.draw, rn.weight_lbs, rn.official_rating,
             rn.recent_form, rn.equipment, now, now, now, source_id))


# --------------------------------------------------------------- ingest ---
class IngestReport(dict):
    pass


def ingest_racecards(conn, source_id: int, source_name: str, target_date: date, racecards: list,
                     fetched_at: Optional[datetime] = None, run_id: str = "ingest") -> IngestReport:
    """Canonical-keyed replacement for the old (course, date, off_time) upsert.
    The provider race id is the identity; off-time is mutable metadata."""
    fetched_at = fetched_at or datetime.now(timezone.utc)
    cur = conn.cursor()
    rep = IngestReport(created=0, rescheduled=0, unchanged=0, runner_sets_written=0, retired=0,
                       slot_conflicts=0, skipped_wrong_date=0, stale_snapshot=False, snapshot_id=None)

    snap_id, is_stale = record_feed_snapshot(cur, source_name, target_date, fetched_at, racecards)
    rep["snapshot_id"], rep["stale_snapshot"] = snap_id, is_stale
    if is_stale:
        raise_alert(cur, "STALE_FEED_SNAPSHOT", "WARN",
                    f"snapshot for {target_date} fetched at {fetched_at} is older than a stored snapshot; not applied")
        return rep

    seen_canonical: set = set()
    for rc in racecards:
        if rc.race_date != target_date:
            rep["skipped_wrong_date"] += 1
            raise_alert(cur, "WRONG_DATE_IN_FEED", "WARN",
                        f"race {rc.race_name!r} dated {rc.race_date}, expected {target_date}")
            continue
        cid, basis = make_canonical_id(rc.external_ref, rc.race_date, rc.course_name,
                                       sequence=None if rc.external_ref else _composite_sequence(racecards, rc),
                                       division=parse_division(rc.race_name))
        seen_canonical.add(cid)
        cur.execute("INSERT INTO course (name, country) VALUES (%s,'GB') ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id",
                    (rc.course_name,))
        course_id = cur.fetchone()[0]
        meeting = make_meeting_id(rc.race_date, rc.course_name)

        cur.execute("SELECT alias.canonical_race_id FROM canonical_race_alias alias WHERE alias.provider_race_id=%s", (rc.external_ref,))
        al = cur.fetchone()
        if al:
            cid = al[0]                  # provider re-issued this race's id earlier: same canonical race
        cur.execute("SELECT race_row_id, scheduled_off_time, status FROM canonical_race WHERE canonical_race_id=%s", (cid,))
        existing = cur.fetchone()
        if existing is None:
            occupant = _same_race_in_slot(cur, course_id, rc, fetched_at)
            if occupant:                 # same slot + same runners, new provider id => alias, not a second race
                cid = occupant
                cur.execute("INSERT INTO canonical_race_alias (provider_race_id, canonical_race_id, reason) VALUES (%s,%s,%s)",
                            (rc.external_ref, cid, "provider re-issued race id: same meeting/time slot and runner set"))
                ledger(cur, run_id, "canonical_race_alias", rc.external_ref, "ALIASED",
                       f"provider id {rc.external_ref} is the same race as {cid} (same slot, runner overlap >= 80%)")
                cur.execute("SELECT race_row_id, scheduled_off_time, status FROM canonical_race WHERE canonical_race_id=%s", (cid,))
                existing = cur.fetchone()
        seen_canonical.add(cid)

        if existing:
            race_id, old_time, status = existing
            new_time = datetime.strptime(rc.off_time, "%H:%M").time()
            if race_id is not None and old_time != new_time:
                cur.execute("SAVEPOINT resched")
                try:
                    cur.execute("UPDATE race SET off_time=%s, going=%s, ingested_at=%s WHERE id=%s",
                                (new_time, rc.going, fetched_at, race_id))
                    cur.execute("RELEASE SAVEPOINT resched")
                    cur.execute("UPDATE canonical_race SET scheduled_off_time=%s WHERE canonical_race_id=%s", (new_time, cid))
                    cur.execute("INSERT INTO canonical_race_time_history (canonical_race_id, scheduled_off_time, observed_at, snapshot_id) VALUES (%s,%s,%s,%s)",
                                (cid, new_time, fetched_at, snap_id))
                    ledger(cur, run_id, "canonical_race", cid, "RESCHEDULED", "provider amended the off-time; same canonical race updated, no new race created",
                           before={"off_time": str(old_time)}, after={"off_time": str(new_time)})
                    rep["rescheduled"] += 1
                except Exception as e:      # slot taken by a different race: do not guess
                    cur.execute("ROLLBACK TO SAVEPOINT resched")
                    cur.execute("UPDATE canonical_race SET status='QUARANTINED' WHERE canonical_race_id=%s", (cid,))
                    raise_alert(cur, "RESCHEDULE_SLOT_CONFLICT", "CRITICAL",
                                f"{cid} moved to {new_time} but that slot is held by another race: {e}",
                                race_id=race_id)
                    rep["slot_conflicts"] += 1
            else:
                rep["unchanged"] += 1
                if race_id is not None:
                    cur.execute("UPDATE race SET going=%s, ingested_at=%s WHERE id=%s", (rc.going, fetched_at, race_id))
            if status == "RETIRED":      # reappeared in the authoritative feed
                cur.execute("UPDATE canonical_race SET status='ACTIVE' WHERE canonical_race_id=%s", (cid,))
            cur.execute("UPDATE canonical_race SET last_seen_at=%s, last_snapshot_id=%s WHERE canonical_race_id=%s",
                        (fetched_at, snap_id, cid))
        else:
            off_time = datetime.strptime(rc.off_time, "%H:%M").time()
            cur.execute("SAVEPOINT newrace")
            try:
                cur.execute(
                    """INSERT INTO race (course_id, race_date, off_time, race_name, race_class, race_type,
                           distance_yards, surface, going, field_size, external_ref, source_id, ingested_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (course_id, rc.race_date, off_time, rc.race_name, rc.race_class, rc.race_type,
                     rc.distance_yards, rc.surface, rc.going, len(rc.runners), rc.external_ref, source_id, fetched_at))
                race_id, status = cur.fetchone()[0], "ACTIVE"
                cur.execute("RELEASE SAVEPOINT newrace")
            except Exception as e:      # (course,date,off_time) slot held by a different canonical race
                cur.execute("ROLLBACK TO SAVEPOINT newrace")
                race_id, status = None, "QUARANTINED"
                raise_alert(cur, "NEW_RACE_SLOT_CONFLICT", "CRITICAL",
                            f"{cid} at {rc.off_time}: slot already held by a different race row ({e}); quarantined",
                            detail={"canonical_race_id": cid})
                rep["slot_conflicts"] += 1
            cur.execute(
                """INSERT INTO canonical_race (canonical_race_id, id_basis, meeting_id, provider_race_id, race_date,
                       course_id, division, race_row_id, scheduled_off_time, status, first_seen_at, last_seen_at, last_snapshot_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (cid, basis, meeting, rc.external_ref, rc.race_date, course_id, parse_division(rc.race_name),
                 race_id, off_time, status, fetched_at, fetched_at, snap_id))
            cur.execute("INSERT INTO canonical_race_time_history (canonical_race_id, scheduled_off_time, observed_at, snapshot_id) VALUES (%s,%s,%s,%s)",
                        (cid, off_time, fetched_at, snap_id))
            rep["created"] += 1

        if race_id is not None and rc.runners and _existing_signature(cur, race_id) != _runner_signature(rc.runners):
            _insert_runners(cur, race_id, rc.runners, source_id, fetched_at)
            cur.execute("UPDATE race SET field_size=%s WHERE id=%s", (len(rc.runners), race_id))
            rep["runner_sets_written"] += 1

    rep["retired"] = _retire_missing(cur, target_date, seen_canonical, snap_id, len(racecards), run_id)
    return rep


def _same_race_in_slot(cur, course_id: int, rc, fetched_at) -> Optional[str]:
    """If a DIFFERENT canonical race already holds this (course, date, off_time) slot and shares >= 80% of the
    incoming runners, return its canonical id (the provider re-issued the id for the same race)."""
    cur.execute("""SELECT cr.canonical_race_id, cr.race_row_id FROM canonical_race cr JOIN race r ON r.id = cr.race_row_id
                   WHERE r.course_id=%s AND r.race_date=%s AND r.off_time=%s""",
                (course_id, rc.race_date, datetime.strptime(rc.off_time, "%H:%M").time()))
    row = cur.fetchone()
    if not row or not rc.runners:
        return None
    incoming = {horse_key(r.horse_name) for r in rc.runners}
    have = {horse_key(n) for _, n in current_runners(cur, row[1])}
    return row[0] if have and len(incoming & have) >= 0.8 * len(incoming) else None


def _composite_sequence(racecards: list, rc) -> int:
    same = sorted((r for r in racecards if course_key(r.course_name) == course_key(rc.course_name)),
                  key=lambda r: (r.off_time or "", r.race_name or ""))
    return same.index(rc) + 1


def _retire_missing(cur, target_date: date, seen: set, snap_id: int, n_in_feed: int, run_id: str) -> int:
    """Races absent from the newest COMPLETE authoritative snapshot are RETIRED
    (never deleted). A thin/partial snapshot cannot retire anything."""
    cur.execute("SELECT max(race_count) FROM race_feed_snapshot WHERE target_date=%s AND id<>%s", (target_date, snap_id))
    prev_max = cur.fetchone()[0] or 0
    if n_in_feed == 0 or (prev_max and n_in_feed < prev_max * PARTIAL_FEED_RATIO):
        raise_alert(cur, "PARTIAL_FEED_NO_RETIREMENT", "WARN",
                    f"{target_date}: snapshot has {n_in_feed} races vs previous max {prev_max}; no races retired")
        return 0
    cur.execute("SELECT canonical_race_id, race_row_id FROM canonical_race WHERE race_date=%s AND status='ACTIVE'", (target_date,))
    n = 0
    for cid, race_id in cur.fetchall():
        if cid not in seen:
            cur.execute("UPDATE canonical_race SET status='RETIRED' WHERE canonical_race_id=%s", (cid,))
            ledger(cur, run_id, "canonical_race", cid, "RETIRED",
                   "absent from the newest complete authoritative feed snapshot (stale/provisional card)",
                   before={"status": "ACTIVE"}, after={"status": "RETIRED", "race_id": race_id})
            raise_alert(cur, "RACE_RETIRED", "INFO", f"{cid} (race {race_id}) left the authoritative feed", race_id=race_id)
            n += 1
    return n


# ----------------------------------------------------------------- gate ---
def run_gate(conn, race_date: date, now: Optional[datetime] = None) -> list:
    """Validate every canonical race for `race_date`; append verdicts (only
    when changed) and return the ValidationResults."""
    now = now or datetime.now(timezone.utc)
    cur = conn.cursor()
    cur.execute("SELECT id, fetched_at, payload FROM race_feed_snapshot WHERE target_date=%s ORDER BY fetched_at DESC LIMIT 1", (race_date,))
    latest = cur.fetchone()
    latest_id, latest_at, latest_payload = (latest if latest else (None, None, []))
    feed_counts = {p.get("external_ref"): len(p.get("runners") or []) for p in (latest_payload or [])}

    cur.execute(
        """SELECT cr.canonical_race_id, cr.provider_race_id, cr.race_row_id, cr.status, cr.last_snapshot_id,
                  cr.meeting_id, c.name, cr.scheduled_off_time, r.race_name, cr.division, fs.fetched_at
           FROM canonical_race cr JOIN course c ON c.id = cr.course_id
           LEFT JOIN race r ON r.id = cr.race_row_id
           LEFT JOIN race_feed_snapshot fs ON fs.id = cr.last_snapshot_id
           WHERE cr.race_date = %s""", (race_date,))
    views, raw = [], {}
    for (cid, pid, race_id, status, last_snap, meeting, course, off, name, div, snap_at) in cur.fetchall():
        if race_id is None:
            continue
        runners = current_runners(cur, race_id)
        views.append(RaceView(
            race_id=race_id, canonical_race_id=cid, provider_race_id=pid, race_date=race_date,
            snapshot_date=race_date, meeting_id=meeting, course_name=course,
            off_time=str(off) if off else None, race_name=name or "", runner_names=[n for _, n in runners],
            feed_runner_count=feed_counts.get(pid) if pid in feed_counts else None, status=status,
            snapshot_at=snap_at, in_latest_feed=(last_snap == latest_id), division=div))
        raw[race_id] = {"canonical_race_id": cid, "provider_race_id": pid, "off_time": str(off),
                        "race_name": name, "runners": [n for _, n in runners], "status": status}
    results = validate_races(views, now)
    for res in results:
        cur.execute("SELECT status, failed_rules FROM race_validation WHERE race_id=%s ORDER BY id DESC LIMIT 1", (res.race_id,))
        prev = cur.fetchone()
        if prev and prev[0] == res.status and list(prev[1]) == res.failed_rules:
            continue
        cur.execute(
            """INSERT INTO race_validation (race_id, canonical_race_id, status, failed_rules, detail, feed_snapshot_id, raw_payload)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (res.race_id, res.canonical_race_id, res.status, res.failed_rules,
             json.dumps(res.detail, default=str), latest_id, json.dumps(raw[res.race_id])))
        if not res.ok:
            raise_alert(cur, "RACE_QUARANTINED", "WARN",
                        f"race {res.race_id} {res.canonical_race_id} quarantined: {', '.join(res.failed_rules)}",
                        race_id=res.race_id, detail=res.detail)
    conn.commit()
    return results


# ------------------------------------------------------ prediction lock ---
def write_prediction_lock(conn, race_id: int, model_version_id: int, probs: dict, provenance: str = "LIVE_GATED"):
    """Record the complete input snapshot behind a just-inserted locked
    prediction. Idempotent (UNIQUE race+model); never updates."""
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM prediction_lock WHERE race_id=%s AND model_version_id=%s", (race_id, model_version_id))
    if cur.fetchone():
        return False
    cur.execute("SELECT min(locked_at) FROM prediction WHERE race_id=%s AND model_version_id=%s AND locked_at IS NOT NULL",
                (race_id, model_version_id))
    locked_at = cur.fetchone()[0]
    cur.execute("SELECT name, version FROM model_version WHERE id=%s", (model_version_id,))
    mname, mver = cur.fetchone()
    cur.execute(
        """SELECT cr.canonical_race_id, cr.meeting_id, cr.provider_race_id, cr.scheduled_off_time,
                  cr.last_snapshot_id, fs.fetched_at
           FROM canonical_race cr LEFT JOIN race_feed_snapshot fs ON fs.id = cr.last_snapshot_id
           WHERE cr.race_row_id=%s""", (race_id,))
    row = cur.fetchone()
    if row is None:
        raise ValueError(f"race {race_id} has no canonical_race row — refusing to lock without a canonical identity")
    cid, meeting, pid, off, snap_id, snap_at = row
    cur.execute("SELECT h.id, h.name FROM horse h WHERE h.id = ANY(%s)", (list(probs.keys()),))
    runners = cur.fetchall()
    snap = build_input_snapshot(
        canonical_race_id=cid, meeting=meeting, source_race_id=pid,
        source_snapshot_at=snap_at.isoformat() if snap_at else None, scheduled_off_time=str(off),
        runners=runners, model_version=f"{mname}:{mver}", probabilities=probs, locked_at=locked_at.isoformat())
    cur.execute(
        """INSERT INTO prediction_lock (race_id, model_version_id, canonical_race_id, meeting_id, source_race_id,
               feed_snapshot_id, source_snapshot_at, scheduled_off_time, runner_ids, runner_names, probabilities,
               locked_at, input_sha256, provenance)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (race_id, model_version_id, cid, meeting, pid, snap_id, snap_at, off, list(snap.runner_ids),
         list(snap.runner_names), json.dumps({str(h): p for h, p in snap.probabilities}), locked_at,
         snap.sha256(), provenance))
    conn.commit()
    return True
