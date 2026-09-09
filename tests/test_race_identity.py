"""
Real tests for src/reconciliation/race_identity.py.

Fixtures use the real RaceCard shape (see racecard_theracingapi.py /
test_racecard_theracingapi.py — course_name, race_date, off_time as a
"HH:MM" string, external_ref as the real "rac_..." id format) on the
Racing API side. The Betfair side (BetfairMarketIdentity) is written
against the publicly documented listMarketCatalogue response shape, same
"not yet live-verified" status test_odds_betfair.py's own fixture carries
(explicitly NOT a real captured response).

This module's own hypothesis (does the two providers' course-name spelling
and clock actually line up on a real side-by-side capture) is NOT tested
here and can't be — that needs live Betfair credentials, still BLOCKED.
These tests only prove the matching LOGIC is correct given inputs already
in a comparable form, per the module's own documented caller-responsibility
contract.
"""
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers.base import RaceCard
from src.reconciliation.race_identity import (
    BetfairMarketIdentity,
    normalize_course_name,
    reconcile_race_identities,
)


def _racecard(course_name, off_time, race_date=date(2026, 9, 8), external_ref="rac_test1", runners=None):
    return RaceCard(
        course_name=course_name,
        race_date=race_date,
        off_time=off_time,
        race_name="Test Race",
        race_class="Class 5",
        race_type="Flat",
        distance_yards=1540,
        surface="Turf",
        going="Good To Soft",
        runners=runners or [],
        external_ref=external_ref,
    )


def _market(venue, market_start_time, market_id="1.170258175"):
    return BetfairMarketIdentity(market_id=market_id, venue=venue, market_start_time=market_start_time)


# --- normalize_course_name ---

def test_normalize_handles_case_whitespace_punctuation():
    assert normalize_course_name("  Leicester  ") == "leicester"
    assert normalize_course_name("LEICESTER") == "leicester"
    assert normalize_course_name("Leicester,") == "leicester"


def test_normalize_strips_racecourse_suffix():
    assert normalize_course_name("Leicester Racecourse") == "leicester"


def test_normalize_strips_aw_qualifiers():
    assert normalize_course_name("Kempton (AW)") == "kempton"
    assert normalize_course_name("Kempton - All Weather") == "kempton"
    assert normalize_course_name("Kempton") == "kempton"
    # same normalized value on purpose: this is the exact case that lets a
    # turf-carded and AW-carded mention of the same course still match.


def test_normalize_does_not_fuzzy_match_genuinely_different_courses():
    """The deliberate non-goal stated in the module docstring: 'Newmarket
    (July)' and 'Newmarket July Course' must NOT normalize to the same
    string — this is exactly the kind of ambiguity this module refuses to
    guess through."""
    a = normalize_course_name("Newmarket (July)")
    b = normalize_course_name("Newmarket July Course")
    assert a != b, f"expected these to stay distinct, both normalized to {a!r}"


def test_normalize_empty_input():
    assert normalize_course_name("") == ""
    assert normalize_course_name(None) == ""


# --- reconcile_race_identities: happy path ---

def test_exact_course_and_time_match():
    racecards = [_racecard("Leicester", "13:12", external_ref="rac_leicester_test")]
    markets = [_market("Leicester", datetime(2026, 9, 8, 13, 12))]

    result = reconcile_race_identities(racecards, markets)

    assert len(result.matched) == 1
    assert result.matched[0].race_external_ref == "rac_leicester_test"
    assert result.matched[0].market_id == "1.170258175"
    assert result.matched[0].time_diff_minutes == 0.0
    assert result.unmatched_racecards == []
    assert result.unmatched_betfair_markets == []


def test_course_name_variant_still_matches():
    racecards = [_racecard("Kempton", "19:00")]
    markets = [_market("Kempton (AW)", datetime(2026, 9, 8, 19, 0))]

    result = reconcile_race_identities(racecards, markets)

    assert len(result.matched) == 1
    assert result.matched[0].time_diff_minutes == 0.0


def test_small_time_difference_within_tolerance_matches():
    racecards = [_racecard("Leicester", "13:12")]
    markets = [_market("Leicester", datetime(2026, 9, 8, 13, 15))]  # 3 min later

    result = reconcile_race_identities(racecards, markets, max_time_diff_minutes=5.0)

    assert len(result.matched) == 1
    assert result.matched[0].time_diff_minutes == 3.0


def test_time_difference_beyond_tolerance_does_not_match():
    racecards = [_racecard("Leicester", "13:12")]
    markets = [_market("Leicester", datetime(2026, 9, 8, 13, 20))]  # 8 min later

    result = reconcile_race_identities(racecards, markets, max_time_diff_minutes=5.0)

    assert result.matched == []
    assert len(result.unmatched_racecards) == 1
    assert len(result.unmatched_betfair_markets) == 1


def test_time_difference_exactly_at_boundary_matches():
    racecards = [_racecard("Leicester", "13:12")]
    markets = [_market("Leicester", datetime(2026, 9, 8, 13, 17))]  # exactly 5 min later

    result = reconcile_race_identities(racecards, markets, max_time_diff_minutes=5.0)

    assert len(result.matched) == 1
    assert result.matched[0].time_diff_minutes == 5.0


def test_different_course_never_matches_even_with_identical_time():
    racecards = [_racecard("Leicester", "13:12")]
    markets = [_market("Newcastle", datetime(2026, 9, 8, 13, 12))]

    result = reconcile_race_identities(racecards, markets)

    assert result.matched == []
    assert len(result.unmatched_racecards) == 1
    assert len(result.unmatched_betfair_markets) == 1


# --- greedy assignment across multiple candidates ---

def test_multiple_races_same_course_match_by_closest_time_not_first_seen():
    """Two races at the same course on the same day, two markets — each
    must pair with its OWN closest match, not whichever gets processed
    first in list order."""
    racecards = [
        _racecard("Leicester", "13:12", external_ref="rac_early"),
        _racecard("Leicester", "15:40", external_ref="rac_late"),
    ]
    # Markets listed in an order that would trip up a naive "first
    # candidate wins" implementation: market for the LATE race appears
    # first in the list, but is still closer in time to the late racecard.
    markets = [
        _market("Leicester", datetime(2026, 9, 8, 15, 41), market_id="mkt_late"),
        _market("Leicester", datetime(2026, 9, 8, 13, 13), market_id="mkt_early"),
    ]

    result = reconcile_race_identities(racecards, markets, max_time_diff_minutes=5.0)

    assert len(result.matched) == 2
    by_race = {m.race_external_ref: m.market_id for m in result.matched}
    assert by_race["rac_early"] == "mkt_early"
    assert by_race["rac_late"] == "mkt_late"


def test_closer_candidate_wins_leaving_the_other_side_unmatched():
    """One market, two racecards both within tolerance — the closer-in-time
    racecard must win the match; the other stays unmatched rather than
    being guessed."""
    racecards = [
        _racecard("Leicester", "13:10", external_ref="rac_close"),  # 2 min away
        _racecard("Leicester", "13:16", external_ref="rac_far"),    # 4 min away
    ]
    markets = [_market("Leicester", datetime(2026, 9, 8, 13, 12))]

    result = reconcile_race_identities(racecards, markets, max_time_diff_minutes=5.0)

    assert len(result.matched) == 1
    assert result.matched[0].race_external_ref == "rac_close"
    assert len(result.unmatched_racecards) == 1
    assert result.unmatched_racecards[0].external_ref == "rac_far"


# --- tz-aware market_start_time handled without crashing ---

def test_tz_aware_market_start_time_compared_as_naive_wall_clock():
    from datetime import timezone
    racecards = [_racecard("Leicester", "13:12")]
    markets = [_market("Leicester", datetime(2026, 9, 8, 13, 12, tzinfo=timezone.utc))]

    result = reconcile_race_identities(racecards, markets)

    assert len(result.matched) == 1
    assert result.matched[0].time_diff_minutes == 0.0


# --- input validation / defensive handling ---

def test_negative_max_time_diff_raises():
    raised = False
    try:
        reconcile_race_identities([], [], max_time_diff_minutes=-1.0)
    except ValueError:
        raised = True
    assert raised, "expected ValueError for a negative max_time_diff_minutes"


def test_unparseable_off_time_leaves_racecard_unmatched_not_crashed():
    racecards = [_racecard("Leicester", off_time="")]
    markets = [_market("Leicester", datetime(2026, 9, 8, 13, 12))]

    result = reconcile_race_identities(racecards, markets)

    assert result.matched == []
    assert len(result.unmatched_racecards) == 1
    assert len(result.unmatched_betfair_markets) == 1


def test_empty_inputs_return_empty_result():
    result = reconcile_race_identities([], [])
    assert result.matched == []
    assert result.unmatched_racecards == []
    assert result.unmatched_betfair_markets == []


if __name__ == "__main__":
    tests = [
        test_normalize_handles_case_whitespace_punctuation,
        test_normalize_strips_racecourse_suffix,
        test_normalize_strips_aw_qualifiers,
        test_normalize_does_not_fuzzy_match_genuinely_different_courses,
        test_normalize_empty_input,
        test_exact_course_and_time_match,
        test_course_name_variant_still_matches,
        test_small_time_difference_within_tolerance_matches,
        test_time_difference_beyond_tolerance_does_not_match,
        test_time_difference_exactly_at_boundary_matches,
        test_different_course_never_matches_even_with_identical_time,
        test_multiple_races_same_course_match_by_closest_time_not_first_seen,
        test_closer_candidate_wins_leaving_the_other_side_unmatched,
        test_tz_aware_market_start_time_compared_as_naive_wall_clock,
        test_negative_max_time_diff_raises,
        test_unparseable_off_time_leaves_racecard_unmatched_not_crashed,
        test_empty_inputs_return_empty_result,
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
