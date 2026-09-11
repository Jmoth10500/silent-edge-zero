"""
Real tests for src/analysis/runner_classification.py (Stage 2 of the
model-vs-market upgrade).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.runner_classification import (
    RUNNER_STATUS_BEST_VALUE,
    RUNNER_STATUS_INSUFFICIENT_DATA,
    RUNNER_STATUS_MODEL_WARNING,
    RUNNER_STATUS_NO_EDGE,
    ValueFilterConfig,
    classify_runner_value,
    pick_race_best_value,
)


def test_classify_insufficient_data_without_real_edge():
    assert classify_runner_value(0.22, None, None) == RUNNER_STATUS_INSUFFICIENT_DATA
    assert classify_runner_value(0.22, 0.10, None) == RUNNER_STATUS_INSUFFICIENT_DATA


def test_classify_no_edge_when_below_configured_threshold():
    config = ValueFilterConfig(min_edge_pts=0.05, min_ev=0.0)
    assert classify_runner_value(0.22, 0.02, 0.10, config) == RUNNER_STATUS_NO_EDGE  # edge too small
    assert classify_runner_value(0.10, -0.05, -0.20, config) == RUNNER_STATUS_NO_EDGE  # negative edge


def test_classify_best_value_real_worked_example():
    # spec's own example: 22% model, +10.4pt edge, +£0.89 EV
    config = ValueFilterConfig(min_edge_pts=0.05, min_ev=0.0)
    assert classify_runner_value(0.22, 0.104, 0.89, config) == RUNNER_STATUS_BEST_VALUE


def test_classify_model_warning_uses_real_rl012_threshold():
    # a real, large edge — but model probability is in the RL-012
    # validated overconfident band (>=40%) — must NOT be labelled BEST VALUE
    config = ValueFilterConfig(min_edge_pts=0.05, min_ev=0.0, overconfidence_threshold=0.40)
    assert classify_runner_value(0.45, 0.15, 0.50, config) == RUNNER_STATUS_MODEL_WARNING


def test_classify_never_auto_labels_biggest_edge_as_best_value_in_warning_band():
    # same real edge as the BEST VALUE example, but the model prob alone
    # pushes it into MODEL WARNING territory — proves the classification
    # doesn't just chase the raw edge number
    config = ValueFilterConfig(min_edge_pts=0.05, min_ev=0.0)
    warned = classify_runner_value(0.41, 0.104, 0.89, config)
    ok = classify_runner_value(0.30, 0.104, 0.89, config)
    assert warned == RUNNER_STATUS_MODEL_WARNING
    assert ok == RUNNER_STATUS_BEST_VALUE


def test_classify_respects_configured_probability_bounds():
    config = ValueFilterConfig(min_edge_pts=0.0, min_ev=-10.0,
                                min_model_probability=0.15, max_model_probability=0.35)
    assert classify_runner_value(0.10, 0.20, 1.0, config) == RUNNER_STATUS_NO_EDGE  # below min
    assert classify_runner_value(0.50, 0.20, 1.0, config) == RUNNER_STATUS_NO_EDGE  # above max
    assert classify_runner_value(0.20, 0.20, 1.0, config) == RUNNER_STATUS_BEST_VALUE  # within bounds


def test_pick_race_best_value_picks_strongest_qualifying_edge():
    runners = [
        {"horse": "A", "status": RUNNER_STATUS_BEST_VALUE, "edge": 0.06},
        {"horse": "B", "status": RUNNER_STATUS_BEST_VALUE, "edge": 0.12},
        {"horse": "C", "status": RUNNER_STATUS_NO_EDGE, "edge": 0.20},  # bigger raw edge but didn't qualify
    ]
    best = pick_race_best_value(runners)
    assert best["horse"] == "B"  # strongest edge AMONG QUALIFYING runners, not the biggest raw number


def test_pick_race_best_value_ignores_model_warning_runners():
    runners = [
        {"horse": "A", "status": RUNNER_STATUS_MODEL_WARNING, "edge": 0.50},  # huge edge but flagged
        {"horse": "B", "status": RUNNER_STATUS_BEST_VALUE, "edge": 0.06},
    ]
    best = pick_race_best_value(runners)
    assert best["horse"] == "B"


def test_pick_race_best_value_none_when_nothing_qualifies():
    runners = [
        {"horse": "A", "status": RUNNER_STATUS_NO_EDGE, "edge": 0.01},
        {"horse": "B", "status": RUNNER_STATUS_INSUFFICIENT_DATA, "edge": None},
    ]
    assert pick_race_best_value(runners) is None


if __name__ == "__main__":
    tests = [
        test_classify_insufficient_data_without_real_edge,
        test_classify_no_edge_when_below_configured_threshold,
        test_classify_best_value_real_worked_example,
        test_classify_model_warning_uses_real_rl012_threshold,
        test_classify_never_auto_labels_biggest_edge_as_best_value_in_warning_band,
        test_classify_respects_configured_probability_bounds,
        test_pick_race_best_value_picks_strongest_qualifying_edge,
        test_pick_race_best_value_ignores_model_warning_runners,
        test_pick_race_best_value_none_when_nothing_qualifies,
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
