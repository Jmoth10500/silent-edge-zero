"""
Real tests for src/evaluation/temperature_scaling.py — synthetic
fixtures only, real math verified by hand. See the module docstring for
why this exists (RL-011 field-size finding).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.temperature_scaling import (
    apply_temperature,
    field_size_bucket,
    fit_best_temperature,
)


def test_apply_temperature_one_is_a_noop():
    probs = {1: 0.5, 2: 0.3, 3: 0.2}
    out = apply_temperature(probs, 1.0)
    for hid in probs:
        assert math.isclose(out[hid], probs[hid], abs_tol=1e-9)


def test_apply_temperature_sharpens_below_one():
    # T < 1 should push the leader's probability UP relative to the field
    probs = {1: 0.5, 2: 0.3, 3: 0.2}
    out = apply_temperature(probs, 0.5)
    assert out[1] > 0.5
    assert math.isclose(sum(out.values()), 1.0, abs_tol=1e-9)


def test_apply_temperature_flattens_above_one():
    # T > 1 should push the leader's probability DOWN relative to the field
    probs = {1: 0.5, 2: 0.3, 3: 0.2}
    out = apply_temperature(probs, 2.0)
    assert out[1] < 0.5
    assert math.isclose(sum(out.values()), 1.0, abs_tol=1e-9)


def test_apply_temperature_hand_verified():
    # T=2: raise to power 0.5 (sqrt), then renormalise
    probs = {1: 0.64, 2: 0.36}
    out = apply_temperature(probs, 2.0)
    # sqrt(0.64)=0.8, sqrt(0.36)=0.6, sum=1.4 -> 0.8/1.4=0.5714..., 0.6/1.4=0.4286...
    assert math.isclose(out[1], 0.8 / 1.4, abs_tol=1e-9)
    assert math.isclose(out[2], 0.6 / 1.4, abs_tol=1e-9)


def test_apply_temperature_rejects_non_positive():
    raised = False
    try:
        apply_temperature({1: 0.5, 2: 0.5}, 0.0)
    except ValueError:
        raised = True
    assert raised


def test_apply_temperature_rejects_empty_race():
    raised = False
    try:
        apply_temperature({}, 1.0)
    except ValueError:
        raised = True
    assert raised


def test_field_size_bucket_real_boundaries():
    assert field_size_bucket(5) == "small"
    assert field_size_bucket(8) == "small"
    assert field_size_bucket(9) == "medium"
    assert field_size_bucket(12) == "medium"
    assert field_size_bucket(13) == "large"
    assert field_size_bucket(20) == "large"


def test_fit_best_temperature_recovers_known_sharpening_need():
    # Synthetic: the true winner is ALWAYS the raw favourite, but raw
    # probabilities are under-confident (favourite always 0.4 in a
    # 3-runner race that it always wins) -> sharpening (T<1) should win
    races = [({1: 0.4, 2: 0.3, 3: 0.3}, 1) for _ in range(50)]
    best_t = fit_best_temperature(races, candidate_temperatures=[0.5, 1.0, 1.5, 2.0])
    assert best_t < 1.0


def test_fit_best_temperature_recovers_known_flattening_need():
    # Synthetic: raw favourite (0.6) only wins half the time -> the raw
    # probabilities are OVER-confident -> flattening (T>1) should win
    races = (
        [({1: 0.6, 2: 0.4}, 1) for _ in range(25)]
        + [({1: 0.6, 2: 0.4}, 2) for _ in range(25)]
    )
    best_t = fit_best_temperature(races, candidate_temperatures=[0.5, 1.0, 1.5, 2.0])
    assert best_t > 1.0


if __name__ == "__main__":
    tests = [
        test_apply_temperature_one_is_a_noop,
        test_apply_temperature_sharpens_below_one,
        test_apply_temperature_flattens_above_one,
        test_apply_temperature_hand_verified,
        test_apply_temperature_rejects_non_positive,
        test_apply_temperature_rejects_empty_race,
        test_field_size_bucket_real_boundaries,
        test_fit_best_temperature_recovers_known_sharpening_need,
        test_fit_best_temperature_recovers_known_flattening_need,
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
