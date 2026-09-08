"""
Real unit tests for src/evaluation/calibration.py — run with:
    python3 -m pytest tests/test_calibration.py -v
or directly: python3 tests/test_calibration.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.calibration import brier_score, log_loss, calibration_curve

TOL = 1e-9


def test_brier_score_perfect_predictions_is_zero():
    assert brier_score([1.0, 0.0, 1.0], [1, 0, 1]) == 0.0


def test_brier_score_worst_case_is_one():
    assert brier_score([0.0, 1.0], [1, 0]) == 1.0


def test_brier_score_constant_half_guess():
    # (0.5-1)^2 and (0.5-0)^2 are both 0.25, average 0.25 -- the textbook
    # "no skill" baseline score against a 50/50 outcome distribution.
    assert abs(brier_score([0.5, 0.5], [1, 0]) - 0.25) < TOL


def test_brier_score_rejects_mismatched_lengths():
    try:
        brier_score([0.5, 0.5], [1])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_brier_score_rejects_empty_input():
    try:
        brier_score([], [])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_brier_score_rejects_non_binary_outcomes():
    try:
        brier_score([0.5], [2])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_log_loss_perfect_predictions_near_zero():
    # Can't hit exactly 0 due to eps clipping, but should be tiny.
    assert log_loss([1.0, 0.0], [1, 0]) < 1e-10


def test_log_loss_confident_and_wrong_is_large_but_finite():
    loss = log_loss([0.0], [1])  # predicted certain loser, actually won
    assert math.isfinite(loss)
    assert loss > 30  # clipped at eps=1e-15, -log(1e-15) ~= 34.5


def test_log_loss_uniform_half_matches_known_value():
    # -log(0.5) = ln(2) regardless of outcome, for every row at p=0.5.
    loss = log_loss([0.5, 0.5, 0.5], [1, 0, 1])
    assert abs(loss - math.log(2)) < TOL


def test_calibration_curve_perfectly_calibrated_bucket():
    # 10 predictions all at p=0.7, 7 of them win -> mean_actual should be 0.7.
    preds = [0.7] * 10
    outcomes = [1] * 7 + [0] * 3
    curve = calibration_curve(preds, outcomes, n_bins=10)
    assert len(curve) == 1
    bucket = curve[0]
    assert abs(bucket["mean_predicted"] - 0.7) < TOL
    assert abs(bucket["mean_actual"] - 0.7) < TOL
    assert bucket["count"] == 10


def test_calibration_curve_omits_empty_bins():
    preds = [0.05, 0.95]
    outcomes = [0, 1]
    curve = calibration_curve(preds, outcomes, n_bins=10)
    # only the bin containing 0.05 and the bin containing 0.95 should appear
    assert len(curve) == 2
    bin_indices = {b["bin_index"] for b in curve}
    assert bin_indices == {0, 9}


def test_calibration_curve_p_equal_one_lands_in_last_bin():
    # p=1.0 * n_bins == n_bins, which must clamp into the last bin, not
    # overflow into a non-existent bin n_bins.
    curve = calibration_curve([1.0], [1], n_bins=10)
    assert len(curve) == 1
    assert curve[0]["bin_index"] == 9


if __name__ == "__main__":
    tests = [
        test_brier_score_perfect_predictions_is_zero,
        test_brier_score_worst_case_is_one,
        test_brier_score_constant_half_guess,
        test_brier_score_rejects_mismatched_lengths,
        test_brier_score_rejects_empty_input,
        test_brier_score_rejects_non_binary_outcomes,
        test_log_loss_perfect_predictions_near_zero,
        test_log_loss_confident_and_wrong_is_large_but_finite,
        test_log_loss_uniform_half_matches_known_value,
        test_calibration_curve_perfectly_calibrated_bucket,
        test_calibration_curve_omits_empty_bins,
        test_calibration_curve_p_equal_one_lands_in_last_bin,
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
