"""
Real unit tests for src/models/model0_market_baseline.py, run against
clearly synthetic odds/results fixtures (never real racecard data) — run
with:
    python3 -m pytest tests/test_model0_market_baseline.py -v
or directly: python3 tests/test_model0_market_baseline.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.model0_market_baseline import (
    RaceRecord,
    RunnerOdds,
    evaluate_market_baseline_walk_forward,
    predict_race_probabilities,
)

TOL = 1e-9
DAY0 = date(2026, 1, 1)


def test_predict_race_probabilities_matches_devig_method():
    runners = [RunnerOdds(horse_id=1, decimal_odds=2.0), RunnerOdds(horse_id=2, decimal_odds=2.0)]
    probs = predict_race_probabilities(runners, method="proportional")
    assert abs(probs[1] - 0.5) < TOL
    assert abs(probs[2] - 0.5) < TOL


def test_predict_race_probabilities_rejects_unknown_method():
    runners = [RunnerOdds(horse_id=1, decimal_odds=2.0)]
    try:
        predict_race_probabilities(runners, method="not_a_real_method")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_predict_race_probabilities_rejects_empty_race():
    try:
        predict_race_probabilities([], method="proportional")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_evaluate_rejects_empty_races():
    try:
        evaluate_market_baseline_walk_forward([], min_train_days=1, test_window_days=1)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_evaluate_rejects_winner_not_among_runners():
    races = [
        # Train-only row, just so a later cutoff exists at all.
        RaceRecord(
            race_id=1,
            race_date=DAY0,
            runners=[RunnerOdds(horse_id=1, decimal_odds=2.0), RunnerOdds(horse_id=2, decimal_odds=2.0)],
            winner_horse_id=1,
        ),
        # This one lands in the test window and has the bad winner_horse_id.
        RaceRecord(
            race_id=2,
            race_date=DAY0 + timedelta(days=2),
            runners=[RunnerOdds(horse_id=1, decimal_odds=2.0), RunnerOdds(horse_id=2, decimal_odds=2.0)],
            winner_horse_id=999,  # not in the race
        ),
    ]
    try:
        evaluate_market_baseline_walk_forward(races, min_train_days=1, test_window_days=2)
        assert False, "expected ValueError"
    except ValueError:
        pass


def _no_vig_race(race_id, days_after_day0, odds_and_ids, winner_horse_id):
    runners = [RunnerOdds(horse_id=hid, decimal_odds=o) for hid, o in odds_and_ids]
    return RaceRecord(
        race_id=race_id,
        race_date=DAY0 + timedelta(days=days_after_day0),
        runners=runners,
        winner_horse_id=winner_horse_id,
    )


def test_evaluate_end_to_end_produces_hand_verifiable_scores():
    # Two odds-of-exactly-1.0-overround races (no vig) so proportional_method
    # leaves the raw 1/odds probabilities untouched -- lets this test
    # hand-verify the resulting Brier score exactly, not just "some number".
    races = [
        # Train-only: before the first cutoff (day0 + 3 = day3), never scored.
        _no_vig_race(1, 0, [(1, 2.0), (2, 2.0)], winner_horse_id=1),
        # Test split 1 (cutoff day3, window (day3, day6]): day5.
        # Even odds -> probs [0.5, 0.5], winner is horse 10.
        # Brier = ((0.5-1)^2 + (0.5-0)^2) / 2 = 0.25
        _no_vig_race(2, 5, [(10, 2.0), (11, 2.0)], winner_horse_id=10),
        # Test split 2 (cutoff day6, window (day6, day9]): day8.
        # 1/1.5 + 1/3.0 == 1.0 exactly (no vig) -> probs [2/3, 1/3].
        # Favourite (horse 20) wins.
        # Brier = ((2/3-1)^2 + (1/3-0)^2) / 2 = (1/9 + 1/9) / 2 = 1/9
        _no_vig_race(3, 8, [(20, 1.5), (21, 3.0)], winner_horse_id=20),
    ]

    evaluations = evaluate_market_baseline_walk_forward(
        races,
        min_train_days=3,
        test_window_days=3,
        method="proportional",
    )

    assert len(evaluations) == 2

    split1, split2 = evaluations

    assert split1.train_end == DAY0 + timedelta(days=3)
    assert split1.test_end == DAY0 + timedelta(days=6)
    assert split1.n_races == 1
    assert split1.n_runner_predictions == 2
    assert abs(split1.brier - 0.25) < TOL

    assert split2.train_end == DAY0 + timedelta(days=6)
    assert split2.test_end == DAY0 + timedelta(days=9)
    assert split2.n_races == 1
    assert split2.n_runner_predictions == 2
    assert abs(split2.brier - (1.0 / 9.0)) < TOL

    # The train-only race (day0) never appears in either test window's score.
    total_scored_races = split1.n_races + split2.n_races
    assert total_scored_races == 2  # not 3 -- the day0 race is excluded


def test_evaluate_calibration_curve_is_populated_and_matches_brier_inputs():
    races = [
        _no_vig_race(1, 0, [(1, 2.0), (2, 2.0)], winner_horse_id=1),
        _no_vig_race(2, 5, [(10, 2.0), (11, 2.0)], winner_horse_id=10),
    ]
    evaluations = evaluate_market_baseline_walk_forward(
        races, min_train_days=3, test_window_days=3, method="proportional"
    )
    assert len(evaluations) == 1
    curve = evaluations[0].calibration
    assert sum(b["count"] for b in curve) == evaluations[0].n_runner_predictions


if __name__ == "__main__":
    tests = [
        test_predict_race_probabilities_matches_devig_method,
        test_predict_race_probabilities_rejects_unknown_method,
        test_predict_race_probabilities_rejects_empty_race,
        test_evaluate_rejects_empty_races,
        test_evaluate_rejects_winner_not_among_runners,
        test_evaluate_end_to_end_produces_hand_verifiable_scores,
        test_evaluate_calibration_curve_is_populated_and_matches_brier_inputs,
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
