"""Silent-failure alerting for the collection pipeline.

Built 2026-09-30 after two failures went unnoticed for ~6 days: Smarkets
changed its API (odds collection 400'd on every run from ~24 Sep) and 13
courses had no horseracing.net slug (their races were skipped every night).
Both logged errors; nothing told a human.

Runs hourly (com.silentedgezero.health-check). Each check is a pure
function over plain data so it is unit-tested without a DB. Alerts go to a
macOS notification (once per distinct problem per day), logs/health_status.json
and stdout.

Usage: python3 scripts/health_check.py [--now YYYY-MM-DDTHH:MM] [--no-notify]
"""
import json
import subprocess
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

STATUS_PATH = ROOT / "logs" / "health_status.json"
ODDS_STALE_HOURS = 2          # during racing hours, no new snapshot for this long = alert
RACING_HOURS = (9, 20)        # local hours in which odds should be flowing
UNSETTLED_TOLERANCE = 0.10    # some whole-race voids are legitimate


def check_predictions(today_races: int, today_predicted: int, now: datetime) -> list[str]:
    if now.hour >= 9 and today_races == 0:
        return [f"No races for {now.date()} in the DB after 09:00 — racecard collection failed?"]
    if now.hour >= 9 and today_races and today_predicted < today_races:
        return [f"Only {today_predicted}/{today_races} of today's races have predictions."]
    return []


def check_odds(today_races: int, latest_snapshot: datetime | None, now: datetime) -> list[str]:
    if not today_races or not (RACING_HOURS[0] <= now.hour < RACING_HOURS[1]):
        return []
    if latest_snapshot is None or latest_snapshot.date() != now.date():
        return ["No odds collected at all today (Smarkets collector failing? Check "
                "logs/collect_smarkets_prices_error.log)."]
    age = now - latest_snapshot
    if age > timedelta(hours=ODDS_STALE_HOURS):
        return [f"Odds stale: last snapshot {age.total_seconds() / 3600:.1f}h ago."]
    return []


def check_unmapped(courses: list[str], hn_slugs: dict, rp_ids: dict) -> list[str]:
    """Flag courses that the primary results source (horseracing.net) cannot
    fetch. Racing Post is only a fallback, so it is not required."""
    missing = sorted(c for c in courses if c not in hn_slugs)
    return [f"Courses with no horseracing.net slug (results will be skipped): "
            f"{', '.join(missing)}"] if missing else []


def check_results(day: date, total: int, unsettled: int, now: datetime) -> list[str]:
    """Only meaningful once the day's evening results run has happened."""
    if not total:
        return []
    if day == now.date() and now.hour < 22:
        return []
    if unsettled / total > UNSETTLED_TOLERANCE:
        return [f"{day}: {unsettled}/{total} races have no result "
                f"({unsettled / total:.0%}) — results collection incomplete."]
    return []


def gather(now: datetime) -> dict:
    import psycopg2
    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()
    today, yday = now.date(), now.date() - timedelta(days=1)
    cur.execute("select count(*), count(*) filter (where exists(select 1 from prediction p "
                "where p.race_id=r.id)) from race r where race_date=%s", (today,))
    races, predicted = cur.fetchone()
    cur.execute("select max(m.observed_at) from market_snapshot m join race r on r.id=m.race_id "
                "where r.race_date=%s", (today,))
    latest = cur.fetchone()[0]
    results = {}
    for d in (yday, today):
        # a race counts as settled with a finishing position OR a terminal note (NR etc)
        cur.execute("select count(*), count(*) filter (where not exists(select 1 from runner_result x "
                    "where x.race_id=r.id and (x.finishing_position is not null or x.result_note is not null))) "
                    "from race r where race_date=%s", (d,))
        results[d] = cur.fetchone()
    cur.execute("select distinct lower(c.name) from race r join course c on c.id=r.course_id "
                "where r.race_date in (%s,%s)", (yday, today))
    courses = [row[0] for row in cur.fetchall()]
    conn.close()
    return dict(races=races, predicted=predicted, latest=latest, results=results, courses=courses)


def run_checks(now: datetime, data: dict, hn_slugs: dict, rp_ids: dict) -> list[str]:
    problems = []
    problems += check_predictions(data["races"], data["predicted"], now)
    problems += check_odds(data["races"], data["latest"], now)
    problems += check_unmapped(data["courses"], hn_slugs, rp_ids)
    for d, (total, unsettled) in data["results"].items():
        problems += check_results(d, total, unsettled, now)
    return problems


def notify_new(problems: list[str], now: datetime) -> list[str]:
    """Return only problems not already notified today, and persist state."""
    try:
        prev = json.loads(STATUS_PATH.read_text())
    except Exception:
        prev = {}
    seen = set(prev.get("notified", [])) if prev.get("date") == str(now.date()) else set()
    new = [p for p in problems if p not in seen]
    STATUS_PATH.write_text(json.dumps({
        "date": str(now.date()), "checked_at": now.isoformat(timespec="seconds"),
        "ok": not problems, "problems": problems, "notified": sorted(seen | set(new)),
    }, indent=2))
    return new


def main() -> int:
    args = sys.argv[1:]
    now = datetime.fromisoformat(args[args.index("--now") + 1]) if "--now" in args else datetime.now()
    from import_horseracingnet_results import HORSERACINGNET_COURSE_SLUGS
    from data.racingpost_course_ids import RACINGPOST_COURSE_IDS
    problems = run_checks(now, gather(now), HORSERACINGNET_COURSE_SLUGS, RACINGPOST_COURSE_IDS)
    new = notify_new(problems, now)
    print(f"[{now:%Y-%m-%d %H:%M}] " + ("OK" if not problems else f"{len(problems)} problem(s)"))
    for p in problems:
        print("  -", p)
    if new and "--no-notify" not in args:
        msg = " | ".join(new).replace('"', "'")[:220]
        subprocess.run(["osascript", "-e",
                        f'display notification "{msg}" with title "Silent Edge Zero: pipeline problem"'])
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
