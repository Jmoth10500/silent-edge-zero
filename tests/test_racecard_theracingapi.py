"""
Real tests for src/providers/racecard_theracingapi.py against a captured
real API response (not mocked field guesses) — see
scratchpad note in docs/BUILD_LOG.md 2026-09-08 for how this fixture was
captured (a real /v1/racecards/free call).

The off_time regression test below exists because of a genuine bug found
and fixed live: the API's own "off_time" field is ambiguous ("1:12", no
AM/PM) and a naive time cast silently produced 01:12 AM instead of the
real 13:12. off_dt (full ISO datetime) is the correct source of truth.

The fixture body's own "date"/"off_dt" strings are frozen at the real
2026-09-08 capture and are never asserted against directly (only fields
mapped FROM the response are checked). Tests call get_racecards() with
date.today() rather than a hardcoded calendar date, because the provider
itself validates for_date against the real date.today() (the free tier
only accepts "today"/"tomorrow") — a hardcoded date silently starts
failing every day that isn't the day it was written on. Found live
2026-09-09 (cloud routine, Session 13): this file used to pass
date(2026, 9, 8) and broke the moment "today" became 2026-09-09.
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers.racecard_theracingapi import TheRacingApiProvider

# A trimmed real fixture, structurally identical to the live 2026-09-08
# response (one FR race to confirm region filtering, one GB race with the
# exact ambiguous off_time that caused the real bug).
REAL_FIXTURE_RESPONSE = {
    "racecards": [
        {
            "race_id": "rac_32297295303",
            "course": "Auteuil",
            "date": "2026-09-08",
            "off_time": "12:55",
            "off_dt": "2026-09-08T12:55:00+01:00",
            "race_name": "Prix Jean Bart",
            "distance_f": "18.0",
            "region": "FR",
            "race_class": "",
            "type": "Hurdle",
            "going": "Very Soft",
            "surface": "Turf",
            "runners": [],
        },
        {
            "race_id": "rac_leicester_test",
            "course": "Leicester",
            "date": "2026-09-08",
            "off_time": "1:12",  # ambiguous — this is the real bug case
            "off_dt": "2026-09-08T13:12:00+01:00",
            "race_name": "British EBF Ron Brooks Motor Group Fillies' Novice Stakes",
            "distance_f": "7.0",
            "region": "GB",
            "race_class": "Class 5",
            "type": "Flat",
            "going": "Good To Soft",
            "surface": "Turf",
            "runners": [
                {
                    "horse": "Test Horse",
                    "horse_id": "hrs_test123",
                    "age": "3",
                    "draw": "4",
                    "lbs": "126",
                    "ofr": "72",
                    "form": "1-23",
                    "headgear": "",
                    "trainer": "Test Trainer",
                    "jockey": "Test Jockey",
                },
            ],
        },
    ],
    "total": 2,
    "limit": 50,
    "skip": 0,
    "query": [],
}


def _mocked_provider():
    provider = TheRacingApiProvider(username="testuser", password="testpass")
    return provider


def test_region_filter_excludes_non_gb():
    provider = _mocked_provider()
    with patch("src.providers.racecard_theracingapi.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = REAL_FIXTURE_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        cards = provider.get_racecards(date.today(), region="GB")

    assert len(cards) == 1, f"expected only the GB race, got {len(cards)}"
    assert cards[0].course_name == "Leicester"


def test_ambiguous_off_time_is_corrected_via_off_dt():
    """The real bug: off_time '1:12' with no AM/PM must resolve to 13:12,
    not be silently misread as 01:12 (which happened when off_time was
    trusted directly instead of deriving it from off_dt)."""
    provider = _mocked_provider()
    with patch("src.providers.racecard_theracingapi.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = REAL_FIXTURE_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        cards = provider.get_racecards(date.today(), region="GB")

    assert cards[0].off_time == "13:12", (
        f"REGRESSION: off_time resolved to {cards[0].off_time!r}, expected '13:12' — "
        f"this is the exact bug found live on 2026-09-08 (ambiguous '1:12' misread as AM)"
    )


def test_distance_furlongs_converted_to_yards():
    provider = _mocked_provider()
    with patch("src.providers.racecard_theracingapi.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = REAL_FIXTURE_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        cards = provider.get_racecards(date.today(), region="GB")

    # 7.0 furlongs * 220 yards/furlong = 1540 yards
    assert cards[0].distance_yards == 1540


def test_runner_fields_mapped_correctly():
    provider = _mocked_provider()
    with patch("src.providers.racecard_theracingapi.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = REAL_FIXTURE_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        cards = provider.get_racecards(date.today(), region="GB")

    runner = cards[0].runners[0]
    assert runner.horse_name == "Test Horse"
    assert runner.age == 3
    assert runner.draw == 4
    assert runner.weight_lbs == 126
    assert runner.official_rating == 72
    assert runner.trainer_name == "Test Trainer"
    assert runner.jockey_name == "Test Jockey"


def test_missing_credentials_raises_clear_error():
    import os
    saved = os.environ.pop("THERACINGAPI_USERNAME", None), os.environ.pop("THERACINGAPI_PASSWORD", None)
    try:
        raised = False
        try:
            TheRacingApiProvider(username=None, password=None)
        except RuntimeError:
            raised = True
        assert raised, "expected RuntimeError when credentials are missing"
    finally:
        if saved[0] is not None:
            os.environ["THERACINGAPI_USERNAME"] = saved[0]
        if saved[1] is not None:
            os.environ["THERACINGAPI_PASSWORD"] = saved[1]


def test_unsupported_date_raises_clear_error():
    """Free tier only supports today/tomorrow — anything else must fail
    loudly, not silently return an empty or wrong result."""
    provider = _mocked_provider()
    far_future = date(2030, 1, 1)
    raised = False
    try:
        provider.get_racecards(far_future, region="GB")
    except ValueError:
        raised = True
    assert raised, "expected ValueError for a date outside today/tomorrow"


if __name__ == "__main__":
    tests = [
        test_region_filter_excludes_non_gb,
        test_ambiguous_off_time_is_corrected_via_off_dt,
        test_distance_furlongs_converted_to_yards,
        test_runner_fields_mapped_correctly,
        test_missing_credentials_raises_clear_error,
        test_unsupported_date_raises_clear_error,
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
