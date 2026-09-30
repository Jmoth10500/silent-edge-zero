"""
Real tests for src/models/model2_hyperparameter_sweep.py — synthetic
fixtures only, same discipline as tests/test_model2_gradient_boosting.py
(this is a stability check over Model 2's own hyperparameters, not a real
benchmark; see the module docstring and docs/RESEARCH_LAB.md RL-008).
Fixtures use exactly the field shapes confirmed live against The Racing API
in tests/test_racecard_theracingapi.py: official_rating as an int, draw as
an int, recent_form as an undelimited string like '1582F3'.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.runner_features import RunnerFeatureInput
from src.models.model1_logistic_baseline import TrainingRace
from src.models.model2_hyperparameter_sweep import (
    SweepResult,
    summarize_sweep,
    sweep_gradient_boosting_hyperparameters,
)


def _runner(horse_id, age=None, draw=None, weight_lbs=None, official_rating=None, recent_form=None):
    return RunnerFeatureInput(
        horse_id=horse_id,
        age=age,
        draw=draw,
        weight_lbs=weight_lbs,
        official_rating=official_rating,
        recent_form=recent_form,
    )


def _signal_races(n=25):
    """Same injected signal as
    test_model2_gradient_boosting.py::test_fit_recovers_rating_signal_on_held_out_race:
    the highest-rated runner-shape (horse_id=30) wins every training race."""
    races = []
    for _ in range(n):
        runners = [
            _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
            _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
            _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
        ]
        races.append(TrainingRace(runners=runners, winner_horse_id=30))
    return races


def _held_out_race():
    return [
        _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
        _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
        _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
    ]


# ---------------------------------------------------------------------------
# sweep_gradient_boosting_hyperparameters — input validation
# ---------------------------------------------------------------------------

def test_sweep_raises_on_empty_param_grid():
    raised = False
    try:
        sweep_gradient_boosting_hyperparameters({}, _signal_races(), _held_out_race(), 30)
    except ValueError:
        raised = True
    assert raised, "expected ValueError for an empty param_grid"


def test_sweep_raises_on_empty_grid_value_list():
    raised = False
    try:
        sweep_gradient_boosting_hyperparameters(
            {"max_depth": []}, _signal_races(), _held_out_race(), 30
        )
    except ValueError:
        raised = True
    assert raised, "expected ValueError for an empty grid value list"


def test_sweep_raises_on_empty_training_races():
    raised = False
    try:
        sweep_gradient_boosting_hyperparameters(
            {"max_depth": [2, 3]}, [], _held_out_race(), 30
        )
    except ValueError:
        raised = True
    assert raised, "expected ValueError for empty training_races"


def test_sweep_raises_on_winner_not_in_held_out_race():
    raised = False
    try:
        sweep_gradient_boosting_hyperparameters(
            {"max_depth": [2]}, _signal_races(), _held_out_race(), expected_winner_horse_id=999
        )
    except ValueError:
        raised = True
    assert raised, "expected ValueError when expected_winner_horse_id isn't in held_out_runners"


# ---------------------------------------------------------------------------
# sweep_gradient_boosting_hyperparameters — real cartesian-product behaviour
# ---------------------------------------------------------------------------

def test_sweep_runs_every_combination_in_the_cartesian_product():
    grid = {
        "max_depth": [2, 3],
        "learning_rate": [0.1, 0.3, 0.5],
        "max_iter": [30],
    }
    results = sweep_gradient_boosting_hyperparameters(
        grid, _signal_races(), _held_out_race(), expected_winner_horse_id=30
    )
    # 2 * 3 * 1 = 6 combinations, no more, no fewer
    assert len(results) == 6
    seen_params = {tuple(sorted(r.params.items())) for r in results}
    assert len(seen_params) == 6, "every combination must be distinct, none skipped or duplicated"
    for max_depth in (2, 3):
        for lr in (0.1, 0.3, 0.5):
            assert (
                ("learning_rate", lr),
                ("max_depth", max_depth),
                ("max_iter", 30),
            ) in seen_params


def test_sweep_recovers_signal_across_a_reasonable_grid():
    """The actual stability check this module exists for: across a grid of
    reasonable, non-default hyperparameters, the injected always-wins signal
    (horse_id=30, highest rating) must still come out on top every time, and
    with a probability genuinely above uniform (1/3) — not just barely."""
    grid = {
        "max_depth": [2, 3, 4],
        "learning_rate": [0.1, 0.3],
        "max_iter": [30, 60],
    }
    results = sweep_gradient_boosting_hyperparameters(
        grid, _signal_races(), _held_out_race(), expected_winner_horse_id=30
    )
    assert len(results) == 3 * 2 * 2  # 12 combinations

    for r in results:
        assert r.is_top_ranked, (
            f"combination {r.params} failed to rank the always-wins runner-shape "
            f"highest (predicted_prob={r.predicted_prob}) — Model 2's fitting is "
            f"NOT stable across this grid"
        )
        assert r.predicted_prob > 1.0 / 3.0, (
            f"combination {r.params} rated the always-wins runner-shape at only "
            f"{r.predicted_prob}, not meaningfully above uniform"
        )


# ---------------------------------------------------------------------------
# summarize_sweep
# ---------------------------------------------------------------------------

def test_summarize_sweep_raises_on_empty_results():
    raised = False
    try:
        summarize_sweep([])
    except ValueError:
        raised = True
    assert raised, "expected ValueError for an empty results list"


def test_summarize_sweep_all_pass():
    results = [
        SweepResult(params={"max_depth": 2}, predicted_prob=0.5, is_top_ranked=True),
        SweepResult(params={"max_depth": 3}, predicted_prob=0.7, is_top_ranked=True),
    ]
    summary = summarize_sweep(results)
    assert summary["n_combinations"] == 2
    assert summary["n_top_ranked"] == 2
    assert summary["top_ranked_rate"] == 1.0
    assert summary["min_predicted_prob"] == 0.5
    assert summary["max_predicted_prob"] == 0.7
    assert abs(summary["mean_predicted_prob"] - 0.6) < 1e-12


def test_summarize_sweep_mixed_pass_and_fail():
    results = [
        SweepResult(params={"max_depth": 2}, predicted_prob=0.9, is_top_ranked=True),
        SweepResult(params={"max_depth": 3}, predicted_prob=0.2, is_top_ranked=False),
        SweepResult(params={"max_depth": 4}, predicted_prob=0.4, is_top_ranked=False),
    ]
    summary = summarize_sweep(results)
    assert summary["n_combinations"] == 3
    assert summary["n_top_ranked"] == 1
    assert abs(summary["top_ranked_rate"] - (1 / 3)) < 1e-12
    assert summary["min_predicted_prob"] == 0.2
    assert summary["max_predicted_prob"] == 0.9


if __name__ == "__main__":
    tests = [
        test_sweep_raises_on_empty_param_grid,
        test_sweep_raises_on_empty_grid_value_list,
        test_sweep_raises_on_empty_training_races,
        test_sweep_raises_on_winner_not_in_held_out_race,
        test_sweep_runs_every_combination_in_the_cartesian_product,
        test_sweep_recovers_signal_across_a_reasonable_grid,
        test_summarize_sweep_raises_on_empty_results,
        test_summarize_sweep_all_pass,
        test_summarize_sweep_mixed_pass_and_fail,
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
