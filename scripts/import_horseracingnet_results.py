#!/usr/bin/env python3
"""
Real results import from horseracing.net — built 2026-09-13 as a real,
verified backup source after Racing Post's meeting-page route became
unreliable for a finished race day (see docs/BUILD_LOG.md's 2026-09-13
entry). Found while independently verifying a ChatGPT-compiled results
table Jonathan brought in ("Ive just Chat GPT the rase pick and got
this") — its claimed 41.2% win strike rate was far enough above this
project's own real backtested ~23% to need real verification first (see
docs/BUILD_LOG.md's "sanity-check suspicious results" rule). Spot-checked
9 real data points directly against a fresh fetch of this site — all 9
matched exactly — before building this proper importer, rather than
typing the LLM's transcription straight into the database.

Real URL shape: `https://www.horseracing.net/results/<course-slug>/<DD-MM-YY>/`
— one page per course per day, every race on it. Parsing is handled by
src/providers/horseracingnet_results.py (real, tested against actual
captured page shapes — see tests/test_horseracingnet_results.py).

**Real, honest limitation:** this does not give starting_price or
distance_beaten (not parsed from this source yet) — those fields are
left NULL, honestly, same discipline as everywhere else in this project.
Course-slug mapping is deliberately incomplete, same pattern as
data/racingpost_course_ids.py — an unmapped course is skipped and
reported, never guessed.

Usage: python3 scripts/import_horseracingnet_results.py <race_date> [course_key1 course_key2 ...]
With no course args (the real daily-automation case, see
scripts/run_collect_results.sh): processes every real course that has
locked predictions for race_date, discovered from our own DB — never a
hard-coded list. Explicit course args (matching our own course.name,
lowercased — e.g. "lingfield (aw)") restrict the run to just those,
for manual/one-off recovery.
Example: python3 scripts/import_horseracingnet_results.py 2026-09-12 doncaster bath chester "lingfield (aw)" musselburgh
"""
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.collect_race_results import (
    fetch_page_html_with_retry,
    insert_results,
    load_our_runners,
)
from scripts.collect_smarkets_prices import strip_country_suffix
from src.providers.horseracingnet_results import parse_finish_text, parse_race_runners, split_into_races

# course.name (lowercased) -> horseracing.net's own URL slug. Real,
# deliberately incomplete — grows as new courses are used, same pattern
# as data/racingpost_course_ids.py. NOT the same slug set (e.g. this
# site uses plain 'lingfield' even for the AW fixture, no separate
# '-aw' slug — confirmed live 2026-09-13, matched by real off_times).
HORSERACINGNET_COURSE_SLUGS: dict[str, str] = {
    "doncaster": "doncaster",
    "bath": "bath",
    "chester": "chester",
    "lingfield (aw)": "lingfield",
    "lingfield": "lingfield",
    "musselburgh": "musselburgh",
    "kempton (aw)": "kempton",
    "kempton": "kempton",
    "sedgefield": "sedgefield",
    "thirsk": "thirsk",
    "windsor": "windsor",
    "redcar": "redcar",
    "uttoxeter": "uttoxeter",
    "wolverhampton (aw)": "wolverhampton",
    "wolverhampton": "wolverhampton",
    "yarmouth": "yarmouth",
    "beverley": "beverley",
    "kelso": "kelso",
    "sandown": "sandown",
    "ayr": "ayr",
    "pontefract": "pontefract",
    "southwell (aw)": "southwell",
    "southwell": "southwell",
    "newbury": "newbury",
    "newton abbot": "newton-abbot",
    "newmarket": "newmarket",
    "newcastle (aw)": "newcastle",
    "newcastle": "newcastle",
}


def load_our_races_by_course(conn, race_date: date) -> dict[str, dict[str, int]]:
    """Real {course_key -> {off_time 'HH:MM' -> our race_id}} for
    race_date, restricted to races that actually have real locked
    predictions (nothing to attach a result to otherwise)."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT c.name, r.id, r.off_time
        FROM race r
        JOIN course c ON c.id = r.course_id
        JOIN prediction p ON p.race_id = r.id
        WHERE r.race_date = %s
        """,
        (race_date,),
    )
    out: dict[str, dict[str, int]] = {}
    for course_name, race_id, off_time in cur:
        key = course_name.strip().lower()
        out.setdefault(key, {})[off_time.strftime("%H:%M")] = race_id
    cur.close()
    return out


def get_or_create_hrnet_source(conn) -> int:
    """Real, separate data_source row — never conflated with Racing
    Post's (see scripts/collect_race_results.py::get_or_create_source)."""
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO data_source (name, url, free_tier, terms_checked, notes) "
        "VALUES ('horseracingnet', 'https://www.horseracing.net/', TRUE, %s, "
        "'Real, free, fetched via headless browser. Promoted to PRIMARY results "
        "source 2026-09-13 after Racing Post''s meeting-page route became unreliable "
        "for finished race days — real, verified live (9/9 spot-check, then 398/398 "
        "at full scale). No starting_price/distance_beaten parsed yet.') "
        "ON CONFLICT (name) DO NOTHING",
        (date.today(),),
    )
    cur.execute("SELECT id FROM data_source WHERE name = 'horseracingnet'")
    source_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return source_id


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    race_date = date.fromisoformat(sys.argv[1])
    url_date = race_date.strftime("%d-%m-%y")

    conn = psycopg2.connect(dbname="silent_edge_zero")
    hrnet_source_id = get_or_create_hrnet_source(conn)

    our_races_by_course = load_our_races_by_course(conn, race_date)

    # Explicit course args restrict to just those (manual/recovery use);
    # with none given, process every real course with locked predictions
    # for this date — the real daily-automation case, never a hard-coded
    # course list.
    course_keys = [c.strip().lower() for c in sys.argv[2:]] or sorted(our_races_by_course)
    print(f"Processing {len(course_keys)} real course(s) for {race_date}: {course_keys}")

    n_races_matched, n_results_total, n_unmatched_horses = 0, 0, 0
    for course_key in course_keys:
        slug = HORSERACINGNET_COURSE_SLUGS.get(course_key)
        if slug is None:
            print(f"  course '{course_key}': no horseracing.net slug mapped, skipping. "
                  f"Add it to HORSERACINGNET_COURSE_SLUGS.")
            continue
        our_races = our_races_by_course.get(course_key, {})
        if not our_races:
            print(f"  course '{course_key}': no real races with predictions found for {race_date}, skipping.")
            continue

        url = f"https://www.horseracing.net/results/{slug}/{url_date}/"
        try:
            html = fetch_page_html_with_retry(url, lambda h: h)
        except Exception as e:
            print(f"  course '{course_key}': real fetch failed after retries ({e}), skipping.")
            continue

        races = split_into_races(html)
        print(f"  course '{course_key}': {len(races)} real races found on the page, "
              f"{len(our_races)} of ours have predictions for {race_date}.")

        for off_time, section in races:
            race_id = our_races.get(off_time)
            if race_id is None:
                print(f"    {off_time}: no matching race_id in our DB, skipping.")
                continue

            our_runners = load_our_runners(conn, race_id)
            if not our_runners:
                print(f"    {off_time}: no runners found for race {race_id}, skipping.")
                continue

            runners = parse_race_runners(section)
            rows = []
            unmatched = []
            for r in runners:
                key = strip_country_suffix(r["horse_name"]).strip().lower()
                if key not in our_runners:
                    unmatched.append(r["horse_name"])
                    continue
                position, note = parse_finish_text(r["finish_text"])
                rows.append({
                    "horse_name_key": key, "finishing_position": position,
                    "result_note": note, "starting_price": None, "distance_beaten": None,
                })
            n, insert_unmatched = insert_results(conn, hrnet_source_id, race_id, rows, our_runners)
            n_races_matched += 1
            n_results_total += n
            n_unmatched_horses += len(unmatched)
            note = f", {len(unmatched)} unmatched horse name(s): {unmatched[:3]}" if unmatched else ""
            print(f"    {off_time} (race {race_id}): {n} real results recorded{note}.")

        # Real pacing between COURSE fetches (2026-09-13, Jonathan's own
        # suggestion after this session hit real rate-limiting/blocking
        # twice this week on other sources) — proactive, not waiting for
        # horseracing.net to actually break first. One page already
        # covers a whole course's real races, so this naturally paces
        # the run into small real batches without needing to also
        # stagger individual races within a course.
        time.sleep(1.0)

    print(f"\n{n_races_matched} races matched and recorded, {n_results_total} total real result rows, "
          f"{n_unmatched_horses} unmatched horse names across the run.")
    conn.close()


if __name__ == "__main__":
    main()
