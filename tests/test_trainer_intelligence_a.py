"""
Real tests for src/research/trainer_intelligence_a.py — brief Section 12A
(Trainer Intelligence Lab, Hypothesis A). compute_handicap_features and
test_rating_drop_hypothesis are pure functions (no DB) and fully testable
here; load_horse_career_runs is DB-integration-verified live, same
convention as every other DB-query function in this project.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.trainer_intelligence_a import compute_handicap_features
from src.research.trainer_intelligence_a import test_rating_drop_hypothesis as run_rating_drop_hypothesis_test


def _run(race_id, race_date, official_rating, finishing_position=None, result_note=None,
         starting_price=None, distance_yards=1600, going="Good", race_class=4):
    return {
        "race_id": race_id, "race_date": race_date, "race_class": race_class,
        "distance_yards": distance_yards, "going": going, "official_rating": official_rating,
        "weight_lbs": 140, "finishing_position": finishing_position, "result_note": result_note,
        "starting_price": starting_price,
    }


# ---------------------------------------------------------------------------
# compute_handicap_features
# ---------------------------------------------------------------------------

def test_first_rated_run_is_skipped_no_prior_data():
    runs_by_horse = {"Horse A": [_run(1, date(2026, 1, 1), 70, finishing_position=2)]}
    features = compute_handicap_features(runs_by_horse)
    assert features == []


def test_prior_max_rating_is_the_real_max_of_strictly_earlier_runs():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), 70, finishing_position=1),
        _run(2, date(2026, 2, 1), 75, finishing_position=3),
        _run(3, date(2026, 3, 1), 65, finishing_position=2),
    ]}
    features = compute_handicap_features(runs_by_horse)
    assert len(features) == 2
    run2, run3 = features
    assert run2["prior_max_rating"] == 70  # only one prior run
    assert run3["prior_max_rating"] == 75  # max(70, 75)
    assert run3["rating_drop"] == 75 - 65


def test_previous_win_uses_the_most_recent_prior_win_not_the_first():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), 60, finishing_position=1),   # first win
        _run(2, date(2026, 2, 1), 65, finishing_position=1, distance_yards=2000, going="Soft"),  # more recent win
        _run(3, date(2026, 3, 1), 68, finishing_position=4),
    ]}
    features = compute_handicap_features(runs_by_horse)
    run3 = features[-1]
    assert run3["has_previous_win"] is True
    assert run3["previous_win_rating"] == 65  # the more recent win, not 60
    assert run3["previous_win_distance_yards"] == 2000
    assert run3["previous_win_going"] == "Soft"
    assert run3["days_since_previous_win"] == (date(2026, 3, 1) - date(2026, 2, 1)).days


def test_no_previous_win_when_horse_never_won_before():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), 60, finishing_position=3),
        _run(2, date(2026, 2, 1), 62, finishing_position=2),
    ]}
    features = compute_handicap_features(runs_by_horse)
    assert features[0]["has_previous_win"] is False
    assert features[0]["previous_win_rating"] is None


# ---------------------------------------------------------------------------
# test_rating_drop_hypothesis
# ---------------------------------------------------------------------------

def _feature(race_id, rating_drop, has_previous_win, finishing_position, starting_price, result_note=None):
    return {
        "race_id": race_id, "race_date": date(2026, 1, 1), "race_class": 4, "distance_yards": 1600,
        "going": "Good", "official_rating": 70, "rating_drop": rating_drop, "has_previous_win": has_previous_win,
        "previous_win_rating": None, "previous_win_distance_yards": None, "previous_win_going": None,
        "days_since_previous_win": None, "finishing_position": finishing_position, "result_note": result_note,
        "starting_price": starting_price,
    }


def test_hypothesis_splits_qualifying_and_control_groups_correctly():
    features = [
        # Race 1: 2 runners, both priced -> de-vig succeeds.
        _feature(1, rating_drop=8.0, has_previous_win=True, finishing_position=1, starting_price=3.0),   # qualifies, wins
        _feature(1, rating_drop=1.0, has_previous_win=False, finishing_position=2, starting_price=2.0),  # control
        # Race 2: only 1 priced runner -> excluded entirely (no de-vig possible)
        _feature(2, rating_drop=10.0, has_previous_win=True, finishing_position=1, starting_price=2.0),
    ]
    result = run_rating_drop_hypothesis_test(features, rating_drop_threshold=5.0)
    assert result["n_races_excluded_insufficient_market_data"] == 1
    assert result["qualifying_group"]["n"] == 1
    assert result["qualifying_group"]["actual_wins"] == 1
    assert result["control_group"]["n"] == 1
    assert result["control_group"]["actual_wins"] == 0
    assert "statistical_caveat" in result
    assert "NOT race-level resampled" in result["statistical_caveat"]


def test_hypothesis_excludes_non_runners_and_pending():
    features = [
        _feature(1, rating_drop=8.0, has_previous_win=True, finishing_position=1, starting_price=3.0),
        _feature(1, rating_drop=1.0, has_previous_win=False, finishing_position=None, starting_price=2.0, result_note="NR"),
        _feature(1, rating_drop=2.0, has_previous_win=False, finishing_position=None, starting_price=4.0, result_note=None),  # pending
    ]
    result = run_rating_drop_hypothesis_test(features, rating_drop_threshold=5.0)
    # only the qualifying winner should be scored -- the NR and pending runners contribute no observation
    assert result["qualifying_group"]["n"] == 1
    assert result["control_group"] is None


def test_hypothesis_none_group_when_empty():
    features = [
        _feature(1, rating_drop=1.0, has_previous_win=False, finishing_position=1, starting_price=2.0),
        _feature(1, rating_drop=1.0, has_previous_win=False, finishing_position=2, starting_price=3.0),
    ]
    result = run_rating_drop_hypothesis_test(features, rating_drop_threshold=5.0)
    assert result["qualifying_group"] is None
    assert result["control_group"]["n"] == 2


if __name__ == "__main__":
    tests = [
        test_first_rated_run_is_skipped_no_prior_data, test_prior_max_rating_is_the_real_max_of_strictly_earlier_runs,
        test_previous_win_uses_the_most_recent_prior_win_not_the_first, test_no_previous_win_when_horse_never_won_before,
        test_hypothesis_splits_qualifying_and_control_groups_correctly, test_hypothesis_excludes_non_runners_and_pending,
        test_hypothesis_none_group_when_empty,
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
