#!/usr/bin/env python3
"""
Real, honest daily health check on the automated pipeline — built
2026-09-11 after a real gap was found: the morning racecard+predict jobs
simply hadn't fired yet when Jonathan checked the live dashboard, and a
manual run was needed to confirm they'd actually work. Jonathan then
asked to monitor the pipeline daily for the next 7 days after moving the
morning jobs to 01:00.

Checks, for the real current date:
1. `collect-racecards` (01:00) actually stored real races for today.
2. `predict-races` (01:15) actually locked real predictions for today,
   AND the Netlify deploy step succeeded (no real errors in its log).
3. `collect-results` (21:30, previous evening) actually recorded real
   settled results for the most recent real race day.

Never guesses a PASS — each check queries the real DB or reads the
real log file; a missing/stale/empty result is reported as a real FAIL,
not silently skipped.

Usage: python3 scripts/check_pipeline_health.py
Exit code 0 if everything real looks healthy, 1 otherwise.
"""
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

LOG_DIR = Path(__file__).parent.parent / "logs"


def check_racecards_collected(conn, today: date) -> tuple[bool, str]:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM race WHERE race_date = %s", (today,))
    n = cur.fetchone()[0]
    cur.close()
    if n == 0:
        return False, f"0 real races stored for {today} — collect-racecards may not have run or found nothing."
    return True, f"{n} real races stored for {today}."


def check_predictions_locked(conn, today: date) -> tuple[bool, str]:
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(DISTINCT p.race_id) FROM prediction p JOIN race r ON r.id = p.race_id "
        "WHERE r.race_date = %s AND p.locked_at IS NOT NULL",
        (today,),
    )
    n = cur.fetchone()[0]
    cur.close()
    if n == 0:
        return False, f"0 real races have locked predictions for {today}."
    return True, f"{n} real races have locked predictions for {today}."


_DEPLOY_SUCCESS_MARKERS = ("Deploy is live!", "Deploy complete")


def check_deploy_log_fresh(today: date) -> tuple[bool, str]:
    """Real bug found and fixed 2026-09-12: this used to check ONLY
    predict_races.log (stdout) for the literal 'Deploy is live!' line —
    a real false positive, confirmed live: the deploy genuinely
    succeeded (site's own title tag showed today's real date), but the
    Netlify CLI happened to write that particular spinner-status line to
    STDERR that run instead of stdout (it did so twice, in fact), while
    stdout still carried its own real 'Deploy complete' success line.
    Netlify's own stdout/stderr allocation for these lines isn't
    consistent run to run, so this now checks BOTH real log files for
    EITHER real success marker, combined."""
    log_path = LOG_DIR / "predict_races.log"
    err_path = LOG_DIR / "predict_races_error.log"
    if not log_path.exists():
        return False, "predict_races.log does not exist."
    mtime = date.fromtimestamp(log_path.stat().st_mtime)
    if mtime != today:
        return False, f"predict_races.log last modified {mtime}, not today ({today}) — the job may not have run yet."

    combined_text = log_path.read_text()
    if err_path.exists():
        combined_text += err_path.read_text()

    if not any(marker in combined_text for marker in _DEPLOY_SUCCESS_MARKERS):
        return False, ("Neither predict_races.log nor predict_races_error.log contains a real "
                        f"success marker ({' / '.join(_DEPLOY_SUCCESS_MARKERS)}) — the Netlify deploy may have failed.")
    return True, f"predict_races.log is fresh ({today}) and a real successful deploy marker was found."


def check_recent_results(conn, today: date) -> tuple[bool, str]:
    """Checks the most recent real race day with any predictions has at
    least some real settled results — a real day can legitimately have
    0 if results haven't been collected yet (same-evening), so this only
    checks days more than 1 real day old."""
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT r.race_date FROM race r JOIN prediction p ON p.race_id = r.id "
        "WHERE p.locked_at IS NOT NULL AND r.race_date < %s ORDER BY r.race_date DESC LIMIT 1",
        (today,),
    )
    row = cur.fetchone()
    if row is None:
        cur.close()
        return True, "No real prior race day with predictions yet — nothing to check."
    last_day = row[0]
    if (today - last_day).days < 2:
        cur.close()
        return True, f"Most recent real race day ({last_day}) is too fresh to expect results yet — skipped."
    cur.execute("SELECT COUNT(*) FROM runner_result rr JOIN race r ON r.id = rr.race_id WHERE r.race_date = %s", (last_day,))
    n = cur.fetchone()[0]
    cur.close()
    if n == 0:
        return False, f"0 real results collected for {last_day} (2+ days ago) — collect-results may have failed."
    return True, f"{n} real result rows exist for {last_day}."


def main():
    today = date.today()
    conn = psycopg2.connect(dbname="silent_edge_zero")

    checks = [
        ("Racecards collected", check_racecards_collected(conn, today)),
        ("Predictions locked", check_predictions_locked(conn, today)),
        ("Dashboard deployed", check_deploy_log_fresh(today)),
        ("Recent results collected", check_recent_results(conn, today)),
    ]
    conn.close()

    print(f"Pipeline health check — {today} ({datetime.now().strftime('%H:%M')})")
    print("=" * 70)
    all_ok = True
    for name, (ok, detail) in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {detail}")
        all_ok = all_ok and ok
    print("=" * 70)
    print("Overall: " + ("HEALTHY" if all_ok else "REAL ISSUE FOUND — see FAIL line(s) above"))

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
