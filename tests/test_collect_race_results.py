"""
Real tests for scripts/collect_race_results.py's pure parsing functions,
against real Racing Post value formats (confirmed live, 2026-09-10 —
e.g. https://www.racingpost.com/results/15/doncaster/2026-09-10/912529/).
The Playwright-fetching and DB-writing parts are exercised by actually
running the script, same discipline as the other real collectors.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import time
from unittest.mock import patch

import scripts.collect_race_results as collect_race_results
from scripts.collect_race_results import (
    build_result_rows,
    extract_runners_from_next_data,
    fetch_page_html_with_retry,
    match_meeting_race,
    parse_beaten_distance,
    parse_fractional_odds,
    parse_meeting_races,
    parse_outcome_code,
)


def test_parse_fractional_odds_real_formats():
    assert parse_fractional_odds("5/6F") == round(1 + 5 / 6, 4)
    assert parse_fractional_odds("11/1") == 12.0
    assert parse_fractional_odds("100/30") == round(1 + 100 / 30, 4)


def test_parse_fractional_odds_evens():
    assert parse_fractional_odds("Evens") == 2.0
    assert parse_fractional_odds("EvensF") == 2.0
    assert parse_fractional_odds("evs") == 2.0


def test_parse_fractional_odds_unparseable_is_none():
    assert parse_fractional_odds(None) is None
    assert parse_fractional_odds("") is None
    assert parse_fractional_odds("SP") is None


def test_parse_outcome_code_real_positions():
    assert parse_outcome_code("1") == (1, None)
    assert parse_outcome_code("17") == (17, None)


def test_parse_outcome_code_real_non_finishes():
    assert parse_outcome_code("PU") == (None, "PU")
    assert parse_outcome_code("UR") == (None, "UR")
    assert parse_outcome_code("F") == (None, "F")


def test_parse_outcome_code_empty():
    assert parse_outcome_code(None) == (None, None)
    assert parse_outcome_code("") == (None, None)


def test_parse_beaten_distance_real_fractions():
    assert parse_beaten_distance("½") == 0.5
    assert parse_beaten_distance("3½") == 3.5
    assert parse_beaten_distance("¾") == 0.75


def test_parse_beaten_distance_real_special_cases():
    assert parse_beaten_distance("nk") == 0.25
    assert parse_beaten_distance("hd") == 0.2
    assert parse_beaten_distance("shd") == 0.1
    assert parse_beaten_distance("nse") == 0.05
    assert parse_beaten_distance("dht") == 0.0


def test_parse_beaten_distance_unparseable_is_none():
    assert parse_beaten_distance(None) is None
    assert parse_beaten_distance("") is None
    assert parse_beaten_distance("dist") is None


def test_parse_beaten_distance_plain_whole_number():
    assert parse_beaten_distance("5") == 5.0


def test_extract_runners_from_next_data_real_shape():
    html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        '{"props":{"pageProps":{"initialState":{"raceResult":{"data":'
        '{"runners":[{"horseName":"Night In Vegas","outcomeCode":"1"}]}}}}}}'
        "</script></html>"
    )
    runners = extract_runners_from_next_data(html)
    assert runners == [{"horseName": "Night In Vegas", "outcomeCode": "1"}]


def test_extract_runners_from_next_data_missing_script_raises():
    try:
        extract_runners_from_next_data("<html>no script here</html>")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_build_result_rows_real_shape_and_country_suffix_stripping():
    runners_json = [
        {
            "horseName": "Arbaawy",
            "outcomeCode": "1",
            "odds": "5/6F",
            "beatenDistance": None,
            "isDisqualified": False,
        },
        {
            "horseName": "Pay The Piper",
            "outcomeCode": "PU",
            "odds": "11/1",
            "beatenDistance": None,
            "isDisqualified": False,
        },
    ]
    rows = build_result_rows(runners_json)
    assert rows[0]["horse_name_key"] == "arbaawy"
    assert rows[0]["finishing_position"] == 1
    assert rows[0]["starting_price"] == round(1 + 5 / 6, 4)
    assert rows[1]["finishing_position"] is None
    assert rows[1]["result_note"] == "PU"


def test_build_result_rows_disqualified_appends_note():
    runners_json = [
        {
            "horseName": "Dorigo",
            "outcomeCode": "1",
            "odds": "11/1",
            "beatenDistance": None,
            "isDisqualified": True,
        }
    ]
    rows = build_result_rows(runners_json)
    assert rows[0]["result_note"] == "DSQ"


def test_parse_meeting_races_real_shape():
    next_data = {
        "props": {
            "pageProps": {
                "initialState": {
                    "racecardMeetingPage": {
                        "data": {
                            "races": [
                                {"race": {"raceId": 926640, "startTime": "13:15", "isResult": True}},
                                {"race": {"raceId": 912529, "startTime": "13:50", "isResult": False}},
                            ]
                        }
                    }
                }
            }
        }
    }
    races = parse_meeting_races(next_data)
    assert races == [
        {"race_id": 926640, "start_time": "13:15", "is_result": True},
        {"race_id": 912529, "start_time": "13:50", "is_result": False},
    ]


def test_match_meeting_race_real_exact_and_within_tolerance():
    meeting_races = [
        {"race_id": 926640, "start_time": "13:15", "is_result": True},
        {"race_id": 912529, "start_time": "13:50", "is_result": True},
    ]
    assert match_meeting_race(meeting_races, time(13, 15)) == 926640
    assert match_meeting_race(meeting_races, time(13, 52)) == 912529  # within 5-min tolerance


def test_match_meeting_race_rejects_time_outside_tolerance():
    meeting_races = [{"race_id": 926640, "start_time": "13:15", "is_result": True}]
    assert match_meeting_race(meeting_races, time(13, 40)) is None


def test_match_meeting_race_picks_closest_among_candidates():
    meeting_races = [
        {"race_id": 1, "start_time": "14:00", "is_result": True},
        {"race_id": 2, "start_time": "14:08", "is_result": True},
    ]
    assert match_meeting_race(meeting_races, time(14, 6)) == 2


def test_fetch_page_html_with_retry_succeeds_first_try():
    with patch.object(collect_race_results, "fetch_page_html", return_value="<html>ok</html>") as mock_fetch:
        result = fetch_page_html_with_retry("https://example.com", lambda html: html.upper())
    assert result == "<HTML>OK</HTML>"
    assert mock_fetch.call_count == 1


def test_fetch_page_html_with_retry_recovers_from_real_intermittent_block():
    # Real, observed live shape (2026-09-12/13): a real Racing Post
    # bot-block error page (no __NEXT_DATA__) on the first attempt, a
    # real successful page on a later attempt — the exact transient
    # pattern found live (Doncaster succeeded seconds after Epsom and
    # Sandown both failed the same way).
    calls = {"n": 0}

    def flaky_fetch(url):
        calls["n"] += 1
        if calls["n"] < 3:
            return "<html>block page, no next data</html>"
        return "<html>__NEXT_DATA__real content</html>"

    def parse_fn(html):
        if "__NEXT_DATA__" not in html:
            raise ValueError("__NEXT_DATA__ script tag not found — page did not render as expected")
        return html

    with patch.object(collect_race_results, "fetch_page_html", side_effect=flaky_fetch):
        with patch.object(collect_race_results, "time_module") as mock_time:
            result = fetch_page_html_with_retry("https://example.com", parse_fn, max_attempts=4)
    assert "__NEXT_DATA__" in result
    assert calls["n"] == 3
    assert mock_time.sleep.call_count == 2  # 2 real backoff waits before the 3rd, successful attempt


def test_fetch_page_html_with_retry_raises_last_real_error_after_exhausting_attempts():
    def always_fails(url):
        raise ValueError("__NEXT_DATA__ script tag not found — page did not render as expected")

    with patch.object(collect_race_results, "fetch_page_html", side_effect=always_fails) as mock_fetch:
        with patch.object(collect_race_results, "time_module"):
            try:
                fetch_page_html_with_retry("https://example.com", lambda html: html, max_attempts=3)
                assert False, "expected the real last error to be raised"
            except ValueError as e:
                assert "__NEXT_DATA__" in str(e)
    assert mock_fetch.call_count == 3  # exhausted all real attempts, never silently gave up early


if __name__ == "__main__":
    tests = [
        test_parse_fractional_odds_real_formats,
        test_parse_fractional_odds_evens,
        test_parse_fractional_odds_unparseable_is_none,
        test_parse_outcome_code_real_positions,
        test_parse_outcome_code_real_non_finishes,
        test_parse_outcome_code_empty,
        test_parse_beaten_distance_real_fractions,
        test_parse_beaten_distance_real_special_cases,
        test_parse_beaten_distance_unparseable_is_none,
        test_parse_beaten_distance_plain_whole_number,
        test_extract_runners_from_next_data_real_shape,
        test_extract_runners_from_next_data_missing_script_raises,
        test_build_result_rows_real_shape_and_country_suffix_stripping,
        test_build_result_rows_disqualified_appends_note,
        test_parse_meeting_races_real_shape,
        test_match_meeting_race_real_exact_and_within_tolerance,
        test_match_meeting_race_rejects_time_outside_tolerance,
        test_match_meeting_race_picks_closest_among_candidates,
        test_fetch_page_html_with_retry_succeeds_first_try,
        test_fetch_page_html_with_retry_recovers_from_real_intermittent_block,
        test_fetch_page_html_with_retry_raises_last_real_error_after_exhausting_attempts,
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
