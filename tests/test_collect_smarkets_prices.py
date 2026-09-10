"""
Real tests for scripts/collect_smarkets_prices.py's pure matching
functions — synthetic fixtures shaped like the real captured data (real
country-suffix format 'Arbaawy (GB)', real Smarkets venue names). The
HTTP-calling and DB-writing parts are exercised by actually running the
script (documented as forward-only, un-backfillable — see its module
docstring), same discipline as predict_todays_races.py.
"""
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.collect_smarkets_prices import match_race, strip_country_suffix
from src.providers.odds_smarkets import SmarketsEvent


def test_strip_country_suffix_real_formats():
    assert strip_country_suffix("Arbaawy (GB)") == "Arbaawy"
    assert strip_country_suffix("Pay The Piper (IRE)") == "Pay The Piper"
    assert strip_country_suffix("No Suffix") == "No Suffix"


def test_match_race_converts_real_utc_to_uk_local_during_bst():
    # Real bug found and fixed 2026-09-10: a real Smarkets event at
    # 15:52 UTC (2026-09-10, BST in effect, UTC+1) is the SAME real race
    # as our off_time 16:52 UK LOCAL — a full hour apart in raw numbers,
    # correctly matched only once UTC->Europe/London conversion happens.
    our_races = {
        101: {"off_time": time(16, 52), "course_name": "Epsom Downs", "runners": {}},
    }
    smk_event = SmarketsEvent(
        event_id="e1", venue_name="Epsom Downs",
        start_datetime=datetime(2026, 9, 10, 15, 52, tzinfo=timezone.utc),
    )
    assert match_race(our_races, smk_event) == 101


def test_match_race_does_not_false_match_the_naive_utc_reading():
    # The exact false-positive the real bug produced: naively comparing
    # UTC 15:52 to a DIFFERENT real race's local off_time of 15:42 (only
    # 10 minutes apart in raw numbers, inside the old tolerance) must NOT
    # match once the real hour-long BST offset is accounted for.
    our_races = {
        102: {"off_time": time(15, 42), "course_name": "Epsom Downs", "runners": {}},
    }
    smk_event = SmarketsEvent(
        event_id="e1", venue_name="Epsom Downs",
        start_datetime=datetime(2026, 9, 10, 15, 52, tzinfo=timezone.utc),
    )
    assert match_race(our_races, smk_event) is None


def test_match_race_finds_same_course_within_tolerance():
    our_races = {
        101: {"off_time": time(16, 52), "course_name": "Epsom Downs", "runners": {}},
        102: {"off_time": time(14, 0), "course_name": "Worcester", "runners": {}},
    }
    smk_event = SmarketsEvent(
        event_id="e1", venue_name="Epsom Downs",
        start_datetime=datetime(2026, 9, 10, 15, 55, tzinfo=timezone.utc),  # 3 real min off, within tolerance
    )
    assert match_race(our_races, smk_event) == 101


def test_match_race_rejects_time_outside_tolerance():
    our_races = {
        101: {"off_time": time(16, 52), "course_name": "Epsom Downs", "runners": {}},
    }
    smk_event = SmarketsEvent(
        event_id="e1", venue_name="Epsom Downs",
        start_datetime=datetime(2026, 9, 10, 16, 30, tzinfo=timezone.utc),  # 38 real min off (17:30 local)
    )
    assert match_race(our_races, smk_event) is None


def test_match_race_rejects_wrong_course():
    our_races = {
        101: {"off_time": time(16, 52), "course_name": "Epsom Downs", "runners": {}},
    }
    smk_event = SmarketsEvent(
        event_id="e1", venue_name="Worcester",
        start_datetime=datetime(2026, 9, 10, 15, 52, tzinfo=timezone.utc),
    )
    assert match_race(our_races, smk_event) is None


def test_match_race_picks_closest_time_among_same_course_candidates():
    # two real races at the same course on the same day (different off_times)
    our_races = {
        101: {"off_time": time(14, 0), "course_name": "Epsom Downs", "runners": {}},
        102: {"off_time": time(14, 8), "course_name": "Epsom Downs", "runners": {}},
    }
    smk_event = SmarketsEvent(
        event_id="e1", venue_name="Epsom Downs",
        start_datetime=datetime(2026, 9, 10, 13, 6, tzinfo=timezone.utc),  # 14:06 local
    )
    assert match_race(our_races, smk_event) == 102


def test_match_race_handles_gmt_winter_dates_with_no_offset():
    # In GMT (winter, UTC+0) UTC and UK local time ARE the same — the fix
    # must not break this real, common case.
    our_races = {
        101: {"off_time": time(14, 0), "course_name": "Epsom Downs", "runners": {}},
    }
    smk_event = SmarketsEvent(
        event_id="e1", venue_name="Epsom Downs",
        start_datetime=datetime(2026, 1, 10, 14, 0, tzinfo=timezone.utc),  # January -> GMT
    )
    assert match_race(our_races, smk_event) == 101


if __name__ == "__main__":
    tests = [
        test_strip_country_suffix_real_formats,
        test_match_race_converts_real_utc_to_uk_local_during_bst,
        test_match_race_does_not_false_match_the_naive_utc_reading,
        test_match_race_finds_same_course_within_tolerance,
        test_match_race_rejects_time_outside_tolerance,
        test_match_race_rejects_wrong_course,
        test_match_race_picks_closest_time_among_same_course_candidates,
        test_match_race_handles_gmt_winter_dates_with_no_offset,
    ]
    passed = 0
    for t in tests:
        print(f"{t.__name__}:")
        try:
            t()
            print("  PASS")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
    sys.exit(0 if passed == len(tests) else 1)
