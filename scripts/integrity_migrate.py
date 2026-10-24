#!/usr/bin/env python3
"""Integrity migration / reconciliation (spec sections 7, 9, 13 steps 4 and 6).

Idempotent. Preserves every original row: it only (1) applies the additive
schema in db/migrations/001_integrity.sql, (2) backfills canonical race
identity, (3) reconstructs prediction_lock rows for pre-existing locks
(provenance LEGACY_RECONSTRUCTED — we never claim a feed snapshot we did not
store), (4) classifies every race into race_integrity with a correction
ledger entry per change, (5) recomputes derived bet_settlement/metrics.
It never touches prediction, runner_result, runner_snapshot or market_snapshot.

Usage:
  python3 scripts/integrity_migrate.py            # apply
  python3 scripts/integrity_migrate.py --dry-run  # compute + print, write nothing except the (idempotent) schema
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.integrity.canonical import build_input_snapshot, course_key, horse_key, meeting_id, parse_division
from src.integrity.metrics import compute, load_dataset, persist, reconcile
from src.integrity.store import ledger

ROOT = Path(__file__).parent.parent
SINCE = date(2026, 9, 1)


def old_headline(cur) -> dict:
    cur.execute("SELECT count(*), coalesce(sum(races_settled),0), coalesce(sum(top_pick_wins),0), "
                "coalesce(sum(win_stake_total),0), coalesce(sum(win_profit),0), coalesce(sum(sp_priced_races),0), "
                "min(race_date), max(race_date) FROM daily_summary")
    days, settled, wins, stake, profit, sp, d0, d1 = cur.fetchone()
    return dict(days=days, settled=int(settled), wins=int(wins), stake=float(stake), profit=float(profit),
                sp_priced=int(sp), first=str(d0), last=str(d1),
                roi=(float(profit) / float(stake)) if stake else None)


def backfill_canonical(cur, run_id: str) -> dict:
    cur.execute("""SELECT r.id, r.race_date, r.course_id, c.name, r.off_time, r.external_ref, r.race_name, r.ingested_at
                   FROM race r JOIN course c ON c.id = r.course_id
                   WHERE r.race_date >= %s AND EXISTS (SELECT 1 FROM prediction p WHERE p.race_id = r.id)
                     AND NOT EXISTS (SELECT 1 FROM canonical_race cr WHERE cr.race_row_id = r.id)
                   ORDER BY r.id""", (SINCE,))
    rows = cur.fetchall()
    claimed = set()
    cur.execute("SELECT provider_race_id FROM canonical_race WHERE provider_race_id IS NOT NULL")
    claimed.update(x[0] for x in cur.fetchall())
    n_p = n_c = 0
    for rid, rdate, course_id, cname, off, ref, name, ingested in rows:
        if ref and ref not in claimed:
            cid, basis, pid, status = f"P:{ref}", "PROVIDER_ID", ref, "ACTIVE"
            claimed.add(ref)
            n_p += 1
        else:
            cid, basis, pid, status = f"C:{rdate.isoformat()}|{course_key(cname)}|legacy-{rid}", "COMPOSITE", None, "QUARANTINED"
            n_c += 1
        cur.execute(
            """INSERT INTO canonical_race (canonical_race_id, id_basis, meeting_id, provider_race_id, race_date, course_id,
                   division, race_row_id, scheduled_off_time, status, first_seen_at, last_seen_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cid, basis, meeting_id(rdate, cname), pid, rdate, course_id, parse_division(name), rid, off, status,
             ingested, ingested))
        ledger(cur, run_id, "canonical_race", cid, "BACKFILLED",
               "legacy race row given a canonical identity" + ("" if basis == "PROVIDER_ID" else
               " (provider id missing or already claimed by another race row: composite legacy id, QUARANTINED)"),
               after={"race_id": rid, "off_time": str(off)})
    return dict(provider_id=n_p, composite_quarantined=n_c)


def reconstruct_locks(cur) -> int:
    cur.execute("""SELECT p.race_id, p.model_version_id, p.horse_id, h.name, p.model_probability, p.locked_at
                   FROM prediction p JOIN horse h ON h.id = p.horse_id JOIN race r ON r.id = p.race_id
                   WHERE p.locked_at IS NOT NULL AND r.race_date >= %s
                     AND NOT EXISTS (SELECT 1 FROM prediction_lock pl WHERE pl.race_id = p.race_id
                                     AND pl.model_version_id = p.model_version_id)
                   ORDER BY p.race_id, p.model_version_id""", (SINCE,))
    groups: dict = {}
    for race_id, mv, hid, hname, prob, locked in cur.fetchall():
        g = groups.setdefault((race_id, mv), dict(runners=[], probs={}, locked=locked))
        g["runners"].append((hid, hname))
        g["probs"][hid] = float(prob)
        g["locked"] = min(g["locked"], locked)
    cur.execute("SELECT id, name, version FROM model_version")
    mvs = {i: f"{n}:{v}" for i, n, v in cur.fetchall()}
    cur.execute("SELECT race_row_id, canonical_race_id, meeting_id, provider_race_id, scheduled_off_time FROM canonical_race WHERE race_row_id IS NOT NULL")
    canon = {r[0]: r[1:] for r in cur.fetchall()}
    n = 0
    for (race_id, mv), g in groups.items():
        if race_id not in canon:
            continue
        cid, meeting, pid, off = canon[race_id]
        snap = build_input_snapshot(canonical_race_id=cid, meeting=meeting, source_race_id=pid, source_snapshot_at=None,
                                    scheduled_off_time=str(off), runners=g["runners"], model_version=mvs[mv],
                                    probabilities=g["probs"], locked_at=g["locked"].isoformat())
        cur.execute(
            """INSERT INTO prediction_lock (race_id, model_version_id, canonical_race_id, meeting_id, source_race_id,
                   scheduled_off_time, runner_ids, runner_names, probabilities, locked_at, input_sha256, provenance)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'LEGACY_RECONSTRUCTED')""",
            (race_id, mv, cid, meeting, pid, off, list(snap.runner_ids), list(snap.runner_names),
             json.dumps({str(h): p for h, p in snap.probabilities}), g["locked"], snap.sha256()))
        n += 1
    return n


def write_classifications(cur, ds, run_id: str) -> dict:
    cur.execute("SELECT race_id, classification, include_in_metrics, has_result, has_lock_market FROM race_integrity")
    prev = {r[0]: r[1:] for r in cur.fetchall()}
    changed = 0
    for rid, c in ds.classifications.items():
        new = (c.classification, c.include_in_metrics, c.has_result, c.has_lock_market)
        if prev.get(rid) == new:
            continue
        cur.execute(
            """INSERT INTO race_integrity (race_id, classification, include_in_metrics, has_result, has_lock_market,
                   reason, evidence, run_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (race_id) DO UPDATE SET classification=EXCLUDED.classification,
                   include_in_metrics=EXCLUDED.include_in_metrics, has_result=EXCLUDED.has_result,
                   has_lock_market=EXCLUDED.has_lock_market, reason=EXCLUDED.reason, evidence=EXCLUDED.evidence,
                   run_id=EXCLUDED.run_id, classified_at=now()""",
            (rid, c.classification, c.include_in_metrics, c.has_result, c.has_lock_market, c.reason,
             json.dumps(c.evidence, default=str), run_id))
        ledger(cur, run_id, "race_integrity", rid, "CLASSIFIED" if rid not in prev else "RECLASSIFIED", c.reason,
               before=dict(zip(("classification", "include", "has_result", "has_lock"), prev[rid])) if rid in prev else None,
               after=dict(classification=c.classification, include=c.include_in_metrics, **{k: v for k, v in c.evidence.items()}))
        changed += 1
        if not c.include_in_metrics:
            cur.execute("UPDATE canonical_race SET status='RETIRED' WHERE race_row_id=%s AND status<>'RETIRED'", (rid,))
    return dict(changed=changed)


def main():
    dry = "--dry-run" in sys.argv
    run_id = "integrity-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()
    cur.execute((ROOT / "db/migrations/001_integrity.sql").read_text())
    conn.commit()

    before = old_headline(cur)
    print(f"[{run_id}] BEFORE (legacy daily_summary headline): {json.dumps(before)}")

    if dry:
        conn.rollback()
    print("canonical backfill:", backfill_canonical(cur, run_id))
    print("prediction_lock reconstructed (LEGACY_RECONSTRUCTED):", reconstruct_locks(cur))
    ds = load_dataset(conn, SINCE, date.today())
    print("classification:", write_classifications(cur, ds, run_id))
    c = compute(ds)
    checks = reconcile(ds, c)
    for name, a, b, ok in checks:
        print(f"  reconcile {'OK  ' if ok else 'FAIL'} {name}: {a} vs {b}")
    if not all(ok for *_, ok in checks):
        conn.rollback()
        sys.exit("reconciliation FAILED — nothing committed")
    if dry:
        conn.rollback()
        print("dry-run: rolled back all data writes")
    else:
        persist(conn, ds, c, run_id)
        conn.commit()
    m = c["metrics"]
    for k in ("raw_predicted_races", "valid_races", "excluded_races", "settled_races", "pending_races", "void_races",
              "genuine_runner_races", "top_pick_win_rate", "pnl_exchange_lock", "pnl_exchange_other", "pnl_sp",
              "pnl_mixed", "unstaked_genuine", "lock_market_coverage"):
        x = m[k]
        print(f"  {k:24} n={x.numerator!s:>10} d={x.denominator!s:>8} value={x.value if x.value is None else round(x.value, 4)}  {x.exclusions or ''}")
    conn.close()


if __name__ == "__main__":
    main()
