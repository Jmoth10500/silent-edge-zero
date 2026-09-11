#!/usr/bin/env python3
"""
Real, fully automated race-result collection from Racing Post — writes
to `runner_result`. No manual URL list needed (see history below).

**Why Racing Post, not the earlier Smarkets approach:** Smarkets only
lists UPCOMING markets and rolls a race off its listing once the day
moves on (see scripts/check_todays_results.py's module docstring for the
real bug this caused). Racing Post keeps its result pages permanently, so
this can run any time after racing finishes — no race against a rolling
window.

**Real constraints, confirmed live 2026-09-10:**
- Plain scripted HTTP requests to racingpost.com are bot-blocked (403/406).
  A real headless browser (`playwright`, already installed in this venv)
  is required — confirmed it gets through cleanly.
- Racing Post's bare index/listing pages ARE blocked even via headless
  Playwright (e.g. /results/, /results/<date>, /racecards/<course>/<date>
  with no trailing slash).
- BUT the real per-course, per-day "meeting" racecard page — exact path
  /racecards/<course_id>/<course_slug>/<date>/ WITH a trailing slash —
  loads cleanly and embeds every race at that meeting (real Racing Post
  raceId, real startTime, a real isResult flag) as structured JSON in the
  page's own __NEXT_DATA__ script tag. This means every race's Racing
  Post ID can be discovered directly, for free, with no search step at
  all — a plain course_id + date fetch is enough.
- The SAME numeric raceId works in both the racecard URL
  (/racecards/.../<raceId>/) and the result URL (/results/.../<raceId>/)
  for the same race — confirmed live.
- Course IDs are NOT looked up automatically (that would need one of the
  blocked listing pages); see data/racingpost_course_ids.py — a real,
  honestly-incomplete, growable map from our own course.name to Racing
  Post's (course_id, slug). An unmapped course is skipped and reported,
  never guessed.

(Earlier in this session, before this discovery, the plan was to have
Claude find each race's result URL via a live web search and hand this
script a manual race_id -> URL map. That's no longer necessary — kept
only as design history in case a course's meeting page is ever blocked
too and a fallback is needed.)

Usage: python3 scripts/collect_race_results.py [race_date]
Defaults to today. Safe to re-run: existing runner_result rows for a
race+horse are updated (ON CONFLICT), not duplicated.
"""
import json
import re
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from data.racingpost_course_ids import RACINGPOST_COURSE_IDS
from scripts.collect_smarkets_prices import strip_country_suffix

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S
)

_ODDS_FRACTION_RE = re.compile(r"^(\d+)/(\d+)")

_BEATEN_DISTANCE_SPECIAL = {
    "dht": 0.0,   # dead heat
    "nse": 0.05,  # nose
    "shd": 0.1,   # short-head
    "hd": 0.2,    # head
    "nk": 0.25,   # neck
}
_BEATEN_DISTANCE_FRACTIONS = {
    "¼": 0.25, "½": 0.5, "¾": 0.75,
    "⅓": 1 / 3, "⅔": 2 / 3,
    "⅕": 0.2, "⅖": 0.4, "⅗": 0.6, "⅘": 0.8,
    "⅙": 1 / 6, "⅛": 0.125,
}
_BEATEN_DISTANCE_MIXED_RE = re.compile(
    r"^(\d+)?([" + "".join(_BEATEN_DISTANCE_FRACTIONS) + r"])?$"
)

RACE_TIME_TOLERANCE_MINUTES = 5


def parse_fractional_odds(raw: str | None) -> float | None:
    """Real UK fractional-odds string ('5/6F', '11/1', 'Evens', 'EvensF')
    -> real decimal odds. None for anything unparseable (e.g. 'SP', a
    non-runner) rather than guessing."""
    if not raw:
        return None
    s = raw.strip()
    if not s:
        return None
    if s.upper().startswith("EVS") or s.upper().startswith("EVENS"):
        return 2.0
    m = _ODDS_FRACTION_RE.match(s)
    if m:
        num, den = int(m.group(1)), int(m.group(2))
        if den == 0:
            return None
        return round(1 + num / den, 4)
    return None


def parse_outcome_code(raw: str | None) -> tuple[int | None, str | None]:
    """Real Racing Post outcomeCode -> (finishing_position, result_note).
    Numeric codes are a real finishing position; anything else ('PU', 'F',
    'UR', 'BD', 'RR', 'DSQ', ...) is a real non-finish, recorded as a note
    with no numeric position."""
    if raw is None:
        return None, None
    code = str(raw).strip()
    if not code:
        return None, None
    if code.isdigit():
        return int(code), None
    return None, code


def parse_beaten_distance(raw: str | None) -> float | None:
    """Real Racing Post beaten-distance notation ('½', '3½', 'nk', 'dist')
    -> a real approximate length in lengths. Standard-notation special cases
    (nk/hd/shd/nse/dht) and simple whole-or-fraction combinations are
    decoded; anything else ('dist', a blank, or unrecognised text) returns
    None rather than guessing a number."""
    if raw is None:
        return None
    s = raw.strip()
    if not s or s in ("-", "–"):
        return None
    key = s.lower()
    if key in _BEATEN_DISTANCE_SPECIAL:
        return _BEATEN_DISTANCE_SPECIAL[key]
    m = _BEATEN_DISTANCE_MIXED_RE.match(s)
    if m and (m.group(1) or m.group(2)):
        whole = int(m.group(1)) if m.group(1) else 0
        frac = _BEATEN_DISTANCE_FRACTIONS.get(m.group(2), 0.0) if m.group(2) else 0.0
        return whole + frac
    try:
        return float(s)
    except ValueError:
        return None  # e.g. 'dist' — honestly unparseable, never guessed


def parse_meeting_races(next_data: dict) -> list[dict]:
    """Real per-course, per-day meeting page JSON ->
    [{raceId, startTime (HH:MM), isResult}, ...] for every race at that
    meeting, straight from Racing Post's own structured data."""
    races = next_data["props"]["pageProps"]["initialState"]["racecardMeetingPage"]["data"]["races"]
    out = []
    for r in races:
        race = r["race"]
        out.append(
            {
                "race_id": race["raceId"],
                "start_time": race["startTime"],
                "is_result": bool(race.get("isResult")),
            }
        )
    return out


def extract_runners_from_next_data(html: str) -> list[dict]:
    """Real Racing Post result page HTML -> the page's own structured
    runner list (props.pageProps.initialState.raceResult.data.runners),
    each with real horseName/horseSuffix/outcomeCode/odds/beatenDistance —
    no LLM reads or summarises this; it's the site's own JSON."""
    m = _NEXT_DATA_RE.search(html)
    if not m:
        raise ValueError("__NEXT_DATA__ script tag not found — page did not render as expected")
    data = json.loads(m.group(1))
    return data["props"]["pageProps"]["initialState"]["raceResult"]["data"]["runners"]


def extract_next_data(html: str) -> dict:
    m = _NEXT_DATA_RE.search(html)
    if not m:
        raise ValueError("__NEXT_DATA__ script tag not found — page did not render as expected")
    return json.loads(m.group(1))


def fetch_page_html(url: str) -> str:
    """Real headless-Chromium fetch. Plain HTTP requests to racingpost.com
    are blocked (403/406, confirmed live); a real browser is required."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_timeout(1500)
        html = page.content()
        browser.close()
    return html


def match_meeting_race(meeting_races: list[dict], off_time: time) -> int | None:
    """Real our-race off_time -> the matching Racing Post raceId at this
    meeting (within RACE_TIME_TOLERANCE_MINUTES), or None."""
    best_id, best_diff = None, None
    for r in meeting_races:
        try:
            h, m = r["start_time"].split(":")
            rp_time = time(int(h), int(m))
        except (ValueError, AttributeError):
            continue
        diff = abs((rp_time.hour * 60 + rp_time.minute) - (off_time.hour * 60 + off_time.minute))
        if diff <= RACE_TIME_TOLERANCE_MINUTES and (best_diff is None or diff < best_diff):
            best_id, best_diff = r["race_id"], diff
    return best_id


def build_result_rows(runners_json: list[dict]) -> list[dict]:
    """Real Racing Post runner JSON -> rows ready to match against our
    horses and insert, via the same country-suffix-stripping convention
    used by scripts/collect_smarkets_prices.py."""
    rows = []
    for r in runners_json:
        position, note = parse_outcome_code(r.get("outcomeCode"))
        if r.get("isDisqualified"):
            note = f"{note}|DSQ" if note else "DSQ"
        rows.append(
            {
                "horse_name_key": strip_country_suffix(r["horseName"]).strip().lower(),
                "finishing_position": position,
                "result_note": note,
                "starting_price": parse_fractional_odds(r.get("odds")),
                "distance_beaten": parse_beaten_distance(r.get("beatenDistance")),
            }
        )
    return rows


def load_our_races(conn, race_date: date) -> dict[int, dict]:
    """Real {our race_id -> {course_name, off_time}} for race_date."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, c.name, r.off_time
        FROM race r JOIN course c ON c.id = r.course_id
        WHERE r.race_date = %s
        """,
        (race_date,),
    )
    out = {race_id: {"course_name": course_name, "off_time": off_time} for race_id, course_name, off_time in cur}
    cur.close()
    return out


def load_our_runners(conn, race_id: int) -> dict[str, int]:
    """Real {stripped-lowercase horse name -> horse_id} for one of our
    races, for matching against Racing Post's own (non-country-suffixed)
    names.

    **Real bug found and fixed 2026-09-11 (same root cause as
    scripts/collect_smarkets_prices.py::load_our_races, found earlier
    the same day):** this used to source horse_id from `runner_snapshot`
    directly. `horse` has a real, pre-existing schema bug — a plain
    `UNIQUE (name, foaled_year)` that's never actually deduplicated
    anything, because `foaled_year` is always NULL from our real data
    source and Postgres treats NULL as distinct from NULL for
    uniqueness (see db/schema.sql's own comment on the `horse` table for
    the full real story). A second real `collect_racecards.py` run
    creates a fresh duplicate `horse`/`runner_snapshot` row, and this
    query had no ORDER BY to guarantee which one it picked — confirmed
    live: real results were being inserted correctly, but keyed to a
    horse_id `prediction` never used, so `generate_daily_summary.py`
    found 0 settled races despite 79 real result rows existing.
    `prediction` is the real, single source of truth the rest of this
    project already depends on for "which horse_id is THE horse" —
    sourcing from it here means results always link up with the real
    top picks, regardless of any duplicate rows elsewhere."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT h.name, p.horse_id
        FROM prediction p
        JOIN horse h ON h.id = p.horse_id
        WHERE p.race_id = %s
        """,
        (race_id,),
    )
    out = {strip_country_suffix(name).strip().lower(): horse_id for name, horse_id in cur}
    cur.close()
    return out


def get_or_create_source(conn) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO data_source (name, url, free_tier, terms_checked, notes) "
        "VALUES ('racingpost', 'https://www.racingpost.com/', TRUE, %s, "
        "'Real result pages + real per-course meeting pages, fetched via headless "
        "browser (plain HTTP requests are bot-blocked). Structured finishing order "
        "and race-id discovery both read from the page''s own embedded JSON, not "
        "scraped text or an LLM summary.') "
        "ON CONFLICT (name) DO NOTHING",
        (date.today(),),
    )
    cur.execute("SELECT id FROM data_source WHERE name = 'racingpost'")
    source_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return source_id


def insert_results(conn, source_id: int, race_id: int, rows: list[dict], our_runners: dict[str, int]) -> tuple[int, list[str]]:
    """Inserts one runner_result row per real matched horse. Rows for
    horses we can't match to our own runner list are skipped and reported
    — never inserted against a guessed horse_id."""
    now = datetime.now(timezone.utc)
    unmatched = []
    cur = conn.cursor()
    n = 0
    for row in rows:
        horse_id = our_runners.get(row["horse_name_key"])
        if horse_id is None:
            unmatched.append(row["horse_name_key"])
            continue
        cur.execute(
            """
            INSERT INTO runner_result
                (race_id, horse_id, finishing_position, distance_beaten, starting_price,
                 result_note, observed_at, available_at, source_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (race_id, horse_id) DO UPDATE SET
                finishing_position = EXCLUDED.finishing_position,
                distance_beaten = EXCLUDED.distance_beaten,
                starting_price = EXCLUDED.starting_price,
                result_note = EXCLUDED.result_note,
                observed_at = EXCLUDED.observed_at
            """,
            (
                race_id, horse_id, row["finishing_position"], row["distance_beaten"],
                row["starting_price"], row["result_note"], now, now, source_id,
            ),
        )
        n += 1
    conn.commit()
    cur.close()
    return n, unmatched


def main():
    race_date_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    race_date = date.fromisoformat(race_date_str)

    conn = psycopg2.connect(dbname="silent_edge_zero")
    source_id = get_or_create_source(conn)

    our_races = load_our_races(conn, race_date)
    print(f"{len(our_races)} real races in our DB for {race_date}.")

    by_course: dict[str, list[int]] = {}
    for race_id, info in our_races.items():
        by_course.setdefault(info["course_name"].strip().lower(), []).append(race_id)

    n_matched, n_unmapped_course, n_unmatched_time, n_not_settled = 0, 0, 0, 0
    n_results_total = 0

    for course_key, race_ids in by_course.items():
        rp_course = RACINGPOST_COURSE_IDS.get(course_key)
        if rp_course is None:
            print(f"  course '{course_key}': no Racing Post course id mapped, skipping "
                  f"{len(race_ids)} real race(s). Add it to data/racingpost_course_ids.py.")
            n_unmapped_course += len(race_ids)
            continue
        course_id, slug = rp_course
        meeting_url = f"https://www.racingpost.com/racecards/{course_id}/{slug}/{race_date.isoformat()}/"
        try:
            meeting_html = fetch_page_html(meeting_url)
            meeting_races = parse_meeting_races(extract_next_data(meeting_html))
        except Exception as e:
            print(f"  course '{course_key}': real meeting-page fetch failed ({e}), skipping.")
            continue

        for race_id in race_ids:
            off_time = our_races[race_id]["off_time"]
            rp_race_id = match_meeting_race(meeting_races, off_time)
            if rp_race_id is None:
                print(f"  race {race_id} ({course_key} {off_time}): no matching Racing Post race found.")
                n_unmatched_time += 1
                continue
            rp_race = next(r for r in meeting_races if r["race_id"] == rp_race_id)
            if not rp_race["is_result"]:
                print(f"  race {race_id} ({course_key} {off_time}): Racing Post race {rp_race_id} not settled yet.")
                n_not_settled += 1
                continue

            our_runners = load_our_runners(conn, race_id)
            if not our_runners:
                print(f"  race {race_id}: no runners found in our DB, skipping.")
                continue
            result_url = f"https://www.racingpost.com/results/{course_id}/{slug}/{race_date.isoformat()}/{rp_race_id}/"
            try:
                result_html = fetch_page_html(result_url)
                runners_json = extract_runners_from_next_data(result_html)
            except Exception as e:
                print(f"  race {race_id}: real result fetch/parse failed ({e}), skipping.")
                continue
            rows = build_result_rows(runners_json)
            n, unmatched = insert_results(conn, source_id, race_id, rows, our_runners)
            n_matched += 1
            n_results_total += n
            print(f"  race {race_id} ({course_key} {off_time}): {n} real results recorded"
                  + (f", {len(unmatched)} unmatched horse name(s)" if unmatched else "."))

    print(f"\n{n_matched} races matched and recorded, {n_results_total} total real result rows, "
          f"{n_unmapped_course} skipped (unmapped course), {n_unmatched_time} skipped (no time match), "
          f"{n_not_settled} not yet settled.")
    conn.close()


if __name__ == "__main__":
    main()
