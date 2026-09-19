"""
Real tests for src/research/probability_bands.py — brief Section 11.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.probability_bands import band_key, probability_band_analysis, wilson_score_interval


# ---------------------------------------------------------------------------
# wilson_score_interval — checked against a known published reference value
# ---------------------------------------------------------------------------

def test_wilson_interval_matches_hand_calculation():
    # 8 successes in 20 trials, 95% confidence (z=1.96): hand-derived via
    # the standard Wilson formula -- p_hat=0.4, centre=(0.4+z^2/40)/(1+z^2/20)
    # = 0.41611, half-width = 0.19731 -> (0.21880, 0.61342).
    lo, hi = wilson_score_interval(8, 20, confidence=0.95)
    assert abs(lo - 0.21880) < 0.001
    assert abs(hi - 0.61342) < 0.001


def test_wilson_interval_none_for_zero_observations():
    assert wilson_score_interval(0, 0) is None


def test_wilson_interval_stays_within_zero_one():
    lo, hi = wilson_score_interval(0, 5)
    assert 0.0 <= lo <= hi <= 1.0
    lo, hi = wilson_score_interval(5, 5)
    assert 0.0 <= lo <= hi <= 1.0


def test_wilson_interval_rejects_unsupported_confidence():
    try:
        wilson_score_interval(1, 2, confidence=0.5)
        assert False, "expected ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# band_key
# ---------------------------------------------------------------------------

def test_band_key_buckets():
    assert band_key(0.05) == "0%-10%"
    assert band_key(0.34) == "30%-40%"
    assert band_key(0.999) == "90%-100%"


# ---------------------------------------------------------------------------
# probability_band_analysis
# ---------------------------------------------------------------------------

def _obs(se_prob, outcome, market_prob=None):
    return {"se_probability": se_prob, "outcome": outcome, "market_probability": market_prob}


def test_analysis_computes_real_expected_and_calibration_error():
    observations = [
        _obs(0.20, 1, 0.15), _obs(0.20, 0, 0.18), _obs(0.20, 0, None),
        _obs(0.25, 1, 0.22),
    ]
    result = probability_band_analysis(observations, band_width=0.10)
    band = result["20%-30%"]
    assert band["n_selections"] == 4
    assert abs(band["expected_wins_model"] - (0.20 + 0.20 + 0.20 + 0.25)) < 1e-9
    assert band["actual_wins"] == 2
    assert band["actual_win_rate"] == 0.5
    assert abs(band["avg_predicted_probability"] - (0.85 / 4)) < 1e-9
    assert abs(band["calibration_error"] - (0.5 - 0.85 / 4)) < 1e-9
    assert band["n_with_market_probability"] == 3
    assert abs(band["market_expected_wins"] - (0.15 + 0.18 + 0.22)) < 1e-9
    assert band["win_rate_confidence_interval"] is not None
    assert band["small_sample"] is True  # n=4 < 20


def test_analysis_market_expected_none_when_nothing_priced():
    observations = [_obs(0.5, 1, None), _obs(0.5, 0, None)]
    result = probability_band_analysis(observations)
    band = result["50%-60%"]
    assert band["market_expected_wins"] is None
    assert band["n_with_market_probability"] == 0


if __name__ == "__main__":
    tests = [
        test_wilson_interval_matches_hand_calculation, test_wilson_interval_none_for_zero_observations,
        test_wilson_interval_stays_within_zero_one, test_wilson_interval_rejects_unsupported_confidence,
        test_band_key_buckets,
        test_analysis_computes_real_expected_and_calibration_error, test_analysis_market_expected_none_when_nothing_priced,
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
