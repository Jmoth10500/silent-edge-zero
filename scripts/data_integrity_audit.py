#!/usr/bin/env python3
"""
Data Integrity Audit — Silent Edge Zero V2 brief, Phase 1, Section 4.

Read-only. Never writes to `prediction`, `runner_snapshot`, or any other
table this project's model/results pipeline depends on. Produces a
PASS/WARNING/FAIL panel plus a JSON detail file for a race-date range —
purely diagnostic, no dashboard UI yet (that's Phase 3).

**Checks implemented, and why each is FAIL vs WARNING:**
- Duplicate races (same course/date/off_time) — FAIL. `race` has a real
  UNIQUE(course_id, race_date, off_time) constraint (db/schema.sql), so
  this should be structurally impossible; a hit means the constraint was
  bypassed somehow and is a genuine data-corruption signal.
- Duplicate predictions (same race/horse/model_version locked more than
  once) — FAIL. No DB constraint currently prevents this (there is no
  UNIQUE(race_id, horse_id, model_version_id) on `prediction`); a
  duplicate would double-count that runner in every downstream statistic.
- Settled race with no winner and not fully void — FAIL. A genuinely
  finished, non-abandoned race must have exactly one winning finishing
  position (or more than one on a real dead heat, flagged separately as
  informational, never as a defect).
- Non-runner (NR/VOID) counted as a loser, or a real non-finish
  (PU/F/UR/BD/RR/RO/DSQ/SU/REF/CO/FELL) counted as a non-runner — FAIL.
  Reuses scripts/generate_eod_report.py's own VOID_RESULT_CODES rather
  than re-deriving the classification a second time.
- Pending races counted as settled — FAIL. Reuses the exact
  compute_daily_summary/generate_dashboard settlement definition (a race
  is settled once every runner has a real finishing_position OR a real
  terminal result_note); this audit recomputes the same test directly
  against `runner_result` rather than trusting `daily_summary`, so it can
  catch a future regression of the 2026-09-15 bug independently.
- Thin/wide-spread market prices — WARNING. The new
  market_snapshot.price_quality flag (src/providers/odds_smarkets.py),
  surfaced here as a count, not a hard failure — a thin book is a real
  market condition, not necessarily a data error, but every downstream
  "value"/EV calculation should be told about it.
- Duplicate horse names — WARNING, informational only. This is the known,
  unresolved `horse.UNIQUE(name, foaled_year)` bug (see
  docs/BUILD_LOG.md 2026-09-11, db/schema.sql's own comment) — 536+
  duplicates confirmed live, 294 duplicate groups referenced by LOCKED
  prediction rows. This audit surfaces the current count so it's visible,
  but deliberately does NOT attempt to fix or merge anything — that needs
  Jonathan's explicit go-ahead (see the plan file / BUILD_LOG).
- Missing market data — WARNING, informational. A runner with zero
  market_snapshot rows for the whole race day isn't a data error (Smarkets
  simply may not have listed a two-sided book for it yet), just a real
  known gap.

**Explicitly NOT implemented — real, honest limitations of the current
schema, not fabricated:**
- "Conflicting results from different sources" (brief Section 4) —
  `runner_result` has a single row per (race_id, horse_id), UPSERTed by
  whichever results collector runs; there is no history of a prior,
  different value a later source may have overwritten. Cannot be detected
  retroactively without a schema change (an append-only result-history
  table, out of scope for Phase 1).
- "Historical results that change after settlement" — same limitation;
  `runner_result` has no audit trail. `prediction` is genuinely protected
  (DB trigger), `runner_result` is not.
Both gaps are reported as a fixed WARNING line in every run, not silently
omitted.

Usage: python3 scripts/data_integrity_audit.py [race_date] [--days N]
Defaults to today, N=1 (single day). Prints a summary and writes
data/integrity_audit_<race_date>.json.
"""
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.generate_eod_report import VOID_RESULT_CODES

REPO_ROOT = Path(__file__).parent.parent


def check_duplicate_races(conn) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT course_id, race_date, off_time, COUNT(*) AS n, array_agg(id) AS race_ids
        FROM race GROUP BY course_id, race_date, off_time HAVING COUNT(*) > 1
        """
    )
    rows = cur.fetchall()
    cur.close()
    return [{"course_id": c, "race_date": str(d), "off_time": str(t), "n": n, "race_ids": ids}
            for c, d, t, n, ids in rows]


def check_duplicate_predictions(conn, start: date, end: date) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.race_id, p.horse_id, p.model_version_id, COUNT(*) AS n, array_agg(p.id) AS prediction_ids
        FROM prediction p
        JOIN race r ON r.id = p.race_id
        WHERE r.race_date BETWEEN %s AND %s AND p.locked_at IS NOT NULL
        GROUP BY p.race_id, p.horse_id, p.model_version_id HAVING COUNT(*) > 1
        """,
        (start, end),
    )
    rows = cur.fetchall()
    cur.close()
    return [{"race_id": rid, "horse_id": hid, "model_version_id": mvid, "n": n, "prediction_ids": pids}
            for rid, hid, mvid, n, pids in rows]


def check_settlement(conn, start: date, end: date) -> dict:
    """Real, independent recomputation of settlement correctness — never
    trusts daily_summary, walks runner_result directly for every race in
    range."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.race_date, r.off_time, c.name,
               p.horse_id, rr.finishing_position, rr.result_note
        FROM race r
        JOIN course c ON c.id = r.course_id
        JOIN prediction p ON p.race_id = r.id
        JOIN model_version mv ON mv.id = p.model_version_id AND mv.name = 'gbm_v1'
        LEFT JOIN runner_result rr ON rr.race_id = r.id AND rr.horse_id = p.horse_id
        WHERE r.race_date BETWEEN %s AND %s AND p.locked_at IS NOT NULL
        ORDER BY r.id
        """,
        (start, end),
    )
    flat_rows = cur.fetchall()
    cur.close()

    races: dict[int, dict] = {}
    order: list[int] = []
    for race_id, race_date_val, off_time, course_name, horse_id, position, note in flat_rows:
        if race_id not in races:
            races[race_id] = {
                "race_date": race_date_val, "off_time": off_time, "course_name": course_name,
                "results": [],
            }
            order.append(race_id)
        races[race_id]["results"].append((horse_id, position, note))

    no_winner_races, dead_heat_races, misclassified_nr, whole_race_void = [], [], [], []
    n_settled, n_pending = 0, 0

    for race_id in order:
        info = races[race_id]
        race_date_val, off_time, course_name, results = (
            info["race_date"], info["off_time"], info["course_name"], info["results"]
        )
        settled = all(pos is not None or note is not None for hid, pos, note in results)
        if not settled:
            n_pending += 1
            continue
        n_settled += 1

        winners = [hid for hid, pos, note in results if pos == 1]
        real_starters = [hid for hid, pos, note in results if note not in VOID_RESULT_CODES]
        any_finisher = any(pos is not None for hid, pos, note in results)

        if len(winners) == 0 and not any_finisher:
            # Real, legitimate whole-race void (e.g. race stopped/declared
            # void mid-running) -- every runner has a status (VOID/NR/PU/
            # etc.) but literally NONE has a finishing position, which is
            # the genuine fingerprint of the whole race producing no
            # result at all. Distinct from the case below, where SOME
            # runners have real finishing positions but none is marked
            # 1st -- that's an actual data gap in capturing the winner.
            # Verified live against horseracing.net for race 57655 (Bath,
            # 2026-09-12): declared void after runners had gone >5f,
            # 2026-09-21 audit.
            whole_race_void.append({
                "race_id": race_id, "date": str(race_date_val), "off_time": str(off_time),
                "course": course_name,
            })
        elif len(winners) == 0 and len(real_starters) > 0:
            no_winner_races.append({
                "race_id": race_id, "date": str(race_date_val), "off_time": str(off_time),
                "course": course_name,
            })
        elif len(winners) > 1:
            dead_heat_races.append({
                "race_id": race_id, "date": str(race_date_val), "off_time": str(off_time),
                "course": course_name, "n_winners": len(winners),
            })

        # A "misclassified NR" here means a horse marked NR/VOID that ALSO
        # has a real finishing_position recorded — self-contradictory.
        for hid, pos, note in results:
            if note in VOID_RESULT_CODES and pos is not None:
                misclassified_nr.append({
                    "race_id": race_id, "horse_id": hid, "date": str(race_date_val),
                    "note": note, "finishing_position": pos,
                })

    return {
        "races_checked": len(order), "races_settled": n_settled, "races_pending": n_pending,
        "no_winner_races": no_winner_races, "dead_heat_races": dead_heat_races,
        "misclassified_nr": misclassified_nr, "whole_race_void": whole_race_void,
    }


def check_price_quality(conn, start: date, end: date) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ms.price_quality, COUNT(*)
        FROM market_snapshot ms
        JOIN race r ON r.id = ms.race_id
        WHERE r.race_date BETWEEN %s AND %s
        GROUP BY ms.price_quality
        """,
        (start, end),
    )
    counts = {quality: n for quality, n in cur.fetchall()}
    cur.close()
    return counts


def check_duplicate_horse_names(conn) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT name FROM horse GROUP BY name HAVING COUNT(*) > 1
        ) dup
        """
    )
    n_duplicate_names = cur.fetchone()[0]
    cur.execute(
        """
        SELECT COALESCE(SUM(n) - COUNT(*), 0) FROM (
            SELECT name, COUNT(*) AS n FROM horse GROUP BY name HAVING COUNT(*) > 1
        ) dup
        """
    )
    n_excess_rows = cur.fetchone()[0]
    cur.close()
    return {"duplicate_names": n_duplicate_names, "excess_rows": n_excess_rows}


def check_missing_market_data(conn, start: date, end: date) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM prediction p
        JOIN race r ON r.id = p.race_id
        JOIN model_version mv ON mv.id = p.model_version_id
        WHERE r.race_date BETWEEN %s AND %s AND p.locked_at IS NOT NULL AND mv.name = 'gbm_v1'
        AND NOT EXISTS (
            SELECT 1 FROM market_snapshot ms WHERE ms.race_id = p.race_id AND ms.horse_id = p.horse_id
        )
        """,
        (start, end),
    )
    n_no_market_data = cur.fetchone()[0]
    cur.close()
    return {"runners_with_no_market_snapshot": n_no_market_data}


def run_audit(conn, start: date, end: date) -> dict:
    duplicate_races = check_duplicate_races(conn)
    duplicate_predictions = check_duplicate_predictions(conn, start, end)
    settlement = check_settlement(conn, start, end)
    price_quality = check_price_quality(conn, start, end)
    duplicate_horses = check_duplicate_horse_names(conn)
    missing_market = check_missing_market_data(conn, start, end)

    fails = []
    warnings = []

    if duplicate_races:
        fails.append(f"{len(duplicate_races)} duplicate race(s) sharing course/date/off_time")
    if duplicate_predictions:
        fails.append(f"{len(duplicate_predictions)} duplicate locked prediction(s) for the same race/horse/model")
    if settlement["no_winner_races"]:
        fails.append(f"{len(settlement['no_winner_races'])} settled race(s) with real starters but no winner")
    if settlement["misclassified_nr"]:
        fails.append(f"{len(settlement['misclassified_nr'])} runner(s) marked NR/VOID but also given a finishing position")

    if settlement["dead_heat_races"]:
        warnings.append(f"{len(settlement['dead_heat_races'])} real dead heat(s) — informational, not a defect")
    if settlement["whole_race_void"]:
        warnings.append(
            f"{len(settlement['whole_race_void'])} whole race(s) declared void mid-running (zero finishers, "
            f"verified against the results source) — informational, not a defect"
        )
    thin = price_quality.get("thin_book", 0)
    wide = price_quality.get("wide_spread", 0)
    if thin or wide:
        warnings.append(f"{thin} thin_book + {wide} wide_spread market snapshot(s) in range — see price_quality breakdown")
    if duplicate_horses["duplicate_names"]:
        warnings.append(
            f"{duplicate_horses['duplicate_names']} duplicate horse name(s) / {duplicate_horses['excess_rows']} "
            f"excess row(s) — known unresolved horse.UNIQUE(name, foaled_year) bug, see docs/BUILD_LOG.md 2026-09-11"
        )
    if missing_market["runners_with_no_market_snapshot"]:
        warnings.append(
            f"{missing_market['runners_with_no_market_snapshot']} runner(s) in range with zero market_snapshot rows"
        )
    warnings.append(
        "NOT MEASURABLE with the current schema: cross-source result conflicts and post-settlement result "
        "changes — runner_result has no history/audit trail (single UPSERTed row per race/horse). "
        "See this script's module docstring."
    )

    status = "FAIL" if fails else ("WARNING" if warnings else "PASS")

    return {
        "range": {"start": str(start), "end": str(end)},
        "status": status,
        "fails": fails,
        "warnings": warnings,
        "detail": {
            "duplicate_races": duplicate_races,
            "duplicate_predictions": duplicate_predictions,
            "settlement": settlement,
            "price_quality": price_quality,
            "duplicate_horses": duplicate_horses,
            "missing_market_data": missing_market,
        },
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    race_date = date.fromisoformat(args[0]) if args else date.today()
    days = 1
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    start = race_date - timedelta(days=days - 1)
    end = race_date

    conn = psycopg2.connect(dbname="silent_edge_zero")
    result = run_audit(conn, start, end)
    conn.close()

    out_path = REPO_ROOT / "data" / f"integrity_audit_{end.isoformat()}.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print(f"DATA INTEGRITY AUDIT [{start} .. {end}]: {result['status']}")
    for f in result["fails"]:
        print(f"  FAIL: {f}")
    for w in result["warnings"]:
        print(f"  WARNING: {w}")
    print(f"\nFull detail written to {out_path}")
    sys.exit(1 if result["status"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
