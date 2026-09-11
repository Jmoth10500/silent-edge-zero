#!/usr/bin/env python3
"""
Real, live Smarkets exchange price collection — writes to `market_snapshot`.

**Why Smarkets, not Betfair:** Betfair is blocked (account SUSPENDED even
after identity verification, 2026-09-09). Smarkets is a genuine, separate
exchange with a real public read-only API needing no auth at all — see
src/providers/odds_smarkets.py's module docstring for the live
verification behind that.

**Real limitation:** Smarkets only exposes UPCOMING markets — there is no
historical endpoint, so this can only ever build a price-movement dataset
GOING FORWARD from whenever it starts running, same shape as the weather
work. It cannot backfill the 2023-2026 Kaggle backtest window. Meant to
run repeatedly through a race day (see the LaunchAgent this ships with),
each run capturing one real snapshot in time — the sequence of snapshots
across runs IS the movement data.

**Matching, real and imperfect — never guessed when uncertain:**
- Course: Smarkets venue name -> our course via
  `data.gb_racecourse_coordinates.normalise_course_name` (the same real,
  tested normaliser used for the weather/coordinate work).
- Race: matched to our `race` row by (course, same calendar date, off_time
  within `TIME_TOLERANCE_MINUTES` of Smarkets' own start_datetime) — the
  two sources' clocks/scheduled times aren't always identical to the
  minute, but should never differ by more than a few minutes for the same
  real race.
- Horse: our DB stores country-suffixed names ('Arbaawy (GB)',
  'Pay The Piper (IRE)'); Smarkets does not ('Arbaawy'). Matched by
  stripping any real country suffix and comparing case-insensitively. A
  race where the runner COUNT doesn't match between the two sources is
  skipped entirely and logged — a partial/uncertain match is worse than
  no match, never inserted as if it were certain.

Usage: python3 scripts/collect_smarkets_prices.py [race_date]
Defaults to today. Safe to run repeatedly — every run inserts a NEW
market_snapshot row (this table is a time series by design, unlike the
immutable prediction ledger; see db/schema.sql's own comment on it).
"""
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.providers.odds_smarkets import get_runner_prices, get_win_market_id, is_gb_course, list_horse_racing_events

TIME_TOLERANCE_MINUTES = 10
_COUNTRY_SUFFIX_RE = re.compile(r"\s*\([A-Z]{2,4}\)\s*$")


def strip_country_suffix(name: str) -> str:
    return _COUNTRY_SUFFIX_RE.sub("", name).strip()


def get_or_create_source(conn) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO data_source (name, url, free_tier, terms_checked, notes) "
        "VALUES ('smarkets', 'https://api.smarkets.com/', TRUE, %s, "
        "'Public read-only Exchange API, no auth. Delayed/live back-lay prices for research use. "
        "No historical endpoint — forward-only collection.') "
        "ON CONFLICT (name) DO NOTHING",
        (date.today(),),
    )
    cur.execute("SELECT id FROM data_source WHERE name = 'smarkets'")
    source_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return source_id


def load_our_races(conn, race_date: date):
    """Our real races for race_date with real course names and runner
    (horse_id, horse_name) pairs, for matching against Smarkets."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.off_time, c.name, rs.horse_id, h.name
        FROM race r
        JOIN course c ON c.id = r.course_id
        JOIN runner_snapshot rs ON rs.race_id = r.id
        JOIN horse h ON h.id = rs.horse_id
        WHERE r.race_date = %s AND rs.non_runner = FALSE
        """,
        (race_date,),
    )
    by_race: dict[int, dict] = {}
    for race_id, off_time, course_name, horse_id, horse_name in cur:
        if race_id not in by_race:
            by_race[race_id] = {"off_time": off_time, "course_name": course_name, "runners": {}}
        by_race[race_id]["runners"][strip_country_suffix(horse_name).lower()] = horse_id
    cur.close()
    return by_race


def match_race(our_races: dict, smk_event, race_date: date) -> int | None:
    """Returns our race_id matching this Smarkets event, or None. Course
    must normalise to the same real GB course, the event's real LOCAL
    calendar date must equal `race_date`, and off_time must be within
    TIME_TOLERANCE_MINUTES of Smarkets' scheduled start.

    **Real bug found and fixed 2026-09-10 (timezone):** Smarkets'
    `start_datetime` is real UTC; our `race.off_time` is real UK LOCAL
    wall-clock time (see `src/providers/racecard_theracingapi.py` —
    derived from the API's own `off_dt`, which carries a real timezone
    offset, e.g. '+01:00' during BST). Comparing them as if both were UTC
    silently matched every race to the wrong one during BST (currently
    UTC+1) — confirmed live: a Smarkets 'Epsom 15:52' event was matching
    our race at local off_time 15:42 (a coincidental 10-minute gap inside
    the old tolerance) when the REAL same race was at local off_time
    16:52 (a full hour later — the real BST offset). Fixed by converting
    Smarkets' UTC time to Europe/London local time (`zoneinfo`, stdlib,
    handles BST/GMT automatically) before comparing to our local off_time.

    **Real bug found and fixed the same day (missing date check):** the
    function never actually verified the Smarkets event's real calendar
    date matched `race_date` — it built the comparison datetime by
    borrowing the Smarkets event's OWN date, so the date check was a
    silent no-op; only course+time-of-day were ever really compared.
    Found live: by evening, Smarkets had already rolled its listing over
    to tomorrow's races, and a tomorrow Doncaster race nearly false-matched
    today's Doncaster race purely because their time-of-day happened to be
    close. Fixed by requiring the event's real local date to equal
    `race_date` before any time comparison happens at all.
    """
    from data.gb_racecourse_coordinates import normalise_course_name
    from zoneinfo import ZoneInfo

    smk_course = normalise_course_name(smk_event.venue_name)
    smk_time_local = smk_event.start_datetime.astimezone(ZoneInfo("Europe/London"))
    if smk_time_local.date() != race_date:
        return None

    best_race_id, best_diff = None, None
    for race_id, info in our_races.items():
        if normalise_course_name(info["course_name"]) != smk_course:
            continue
        our_dt = datetime.combine(race_date, info["off_time"], tzinfo=smk_time_local.tzinfo)
        diff = abs((our_dt - smk_time_local).total_seconds()) / 60
        if diff <= TIME_TOLERANCE_MINUTES and (best_diff is None or diff < best_diff):
            best_race_id, best_diff = race_id, diff
    return best_race_id


def insert_snapshots(conn, source_id: int, race_id: int, matched: list[tuple[int, "SmarketsRunnerPrice"]]) -> int:
    cur = conn.cursor()
    now = datetime.now(timezone.utc)
    n = 0
    for horse_id, price in matched:
        if price.exchange_back is None and price.exchange_lay is None:
            continue  # no real book yet for this runner — nothing to record
        cur.execute(
            """
            INSERT INTO market_snapshot
                (race_id, horse_id, exchange_back, exchange_lay, midprice, spread,
                 observed_at, available_at, source_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (race_id, horse_id, price.exchange_back, price.exchange_lay, price.midprice,
             price.spread, now, now, source_id),
        )
        n += 1
    conn.commit()
    cur.close()
    return n


def main():
    race_date_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    race_date = date.fromisoformat(race_date_str)

    conn = psycopg2.connect(dbname="silent_edge_zero")
    source_id = get_or_create_source(conn)

    our_races = load_our_races(conn, race_date)
    print(f"{len(our_races)} real races in our DB for {race_date}.")

    events = list_horse_racing_events(race_date)
    gb_events = [e for e in events if is_gb_course(e.venue_name)]
    print(f"{len(gb_events)} real GB events currently listed on Smarkets (any date — "
          f"Smarkets' own date filter is loose, matching is done against our real races).")

    n_races_matched, n_snapshots, n_errors = 0, 0, 0
    for event in gb_events:
        race_id = match_race(our_races, event, race_date)
        if race_id is None:
            continue

        # Real bug found and fixed 2026-09-10: an unhandled error fetching
        # ONE race's real Smarkets prices (e.g. a 429 rate-limit response)
        # used to crash the whole run, losing every other race's real data
        # for this trigger too. Best-effort per race instead — log and
        # move on, same discipline as fetch_course_weather in
        # generate_dashboard.py.
        try:
            market_id = get_win_market_id(event.event_id)
            if market_id is None:
                continue
            prices = get_runner_prices(market_id)
        except Exception as e:
            n_errors += 1
            print(f"  Race {race_id} ({event.venue_name} {event.start_datetime.strftime('%H:%M')}): "
                  f"real Smarkets fetch failed ({e}), skipping this race this run.")
            time.sleep(1.0)  # back off before the next race, in case it's a rate limit
            continue

        # 0.3s -> 0.5s (2026-09-11): real live testing showed a course whose
        # races happen to land later in Smarkets' event order could still
        # trip a 429 with the tighter delay, even with get_win_market_id/
        # get_runner_prices' own retry-with-backoff (src/providers/
        # odds_smarkets.py::_get_with_retry) absorbing some of it.
        time.sleep(0.5)

        our_runners = our_races[race_id]["runners"]
        matched = []
        unmatched_smk, unmatched_ours = [], set(our_runners)
        for p in prices:
            key = p.horse_name.strip().lower()
            if key in our_runners:
                matched.append((our_runners[key], p))
                unmatched_ours.discard(key)
            else:
                unmatched_smk.append(p.horse_name)

        if unmatched_smk or unmatched_ours:
            print(f"  Race {race_id} ({event.venue_name} {event.start_datetime.strftime('%H:%M')}): "
                  f"runner count mismatch — {len(unmatched_smk)} Smarkets runners unmatched "
                  f"({unmatched_smk[:3]}...), {len(unmatched_ours)} of our runners unmatched. Skipping.")
            continue

        n = insert_snapshots(conn, source_id, race_id, matched)
        n_races_matched += 1
        n_snapshots += n
        print(f"  Race {race_id} ({event.venue_name} {event.start_datetime.strftime('%H:%M')}): "
              f"{n} real price snapshots recorded.")

    print(f"\n{n_races_matched} races matched and recorded, {n_snapshots} total real price snapshots, "
          f"{n_errors} races skipped this run due to a real fetch error (e.g. rate limit).")
    conn.close()


if __name__ == "__main__":
    main()
