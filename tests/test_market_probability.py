"""
Real unit tests for the overround-removal methods — run with:
    python3 -m pytest tests/test_market_probability.py -v
or directly: python3 tests/test_market_probability.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.market.probability import (
    raw_probabilities, proportional_method, power_method, shin_method, METHODS
)

TOL = 1e-6

# A realistic 6-runner race with ~15% overround (typical UK bookmaker book)
SAMPLE_ODDS = [2.5, 4.0, 5.0, 7.0, 10.0, 15.0]


def test_raw_probabilities_sum_above_one():
    raw = raw_probabilities(SAMPLE_ODDS)
    total = sum(raw)
    assert total > 1.0, f"expected overround > 1.0, got {total}"
    print(f"  raw sum = {total:.4f} (overround = {(total-1)*100:.1f}%)")


def test_all_methods_sum_to_one():
    for name, fn in METHODS.items():
        probs = fn(SAMPLE_ODDS)
        total = sum(probs)
        assert abs(total - 1.0) < 1e-4, f"{name}: sum={total}, expected ~1.0"
        assert all(0 < p < 1 for p in probs), f"{name}: probabilities out of (0,1) range"
        print(f"  {name}: sum={total:.6f}, probs={[round(p,4) for p in probs]}")


def test_favourite_gets_highest_probability():
    for name, fn in METHODS.items():
        probs = fn(SAMPLE_ODDS)
        assert probs[0] == max(probs), f"{name}: shortest-priced runner should have highest probability"


def test_two_runner_race_sums_to_one():
    """Edge case: a match race, 2 runners."""
    for name, fn in METHODS.items():
        probs = fn([1.8, 2.1])
        assert abs(sum(probs) - 1.0) < 1e-4, f"{name} failed on 2-runner race"


def test_uniform_odds_gives_uniform_probabilities():
    """Sanity check: if every runner has identical odds, every method should
    return identical (uniform) probabilities. Uses odds with a realistic
    ~8% overround (3.7 for 4 runners) — real bookmaker books always
    overround; a book that doesn't (e.g. 5.0 x 4 runners = 80% raw total)
    isn't a real scenario and Shin's method has no defined solution for it
    (it explicitly models overround, not underround)."""
    odds = [3.7] * 4
    for name, fn in METHODS.items():
        probs = fn(odds)
        assert all(abs(p - 0.25) < 1e-3 for p in probs), f"{name} failed uniform-odds sanity check: {probs}"


if __name__ == "__main__":
    tests = [
        test_raw_probabilities_sum_above_one,
        test_all_methods_sum_to_one,
        test_favourite_gets_highest_probability,
        test_two_runner_race_sums_to_one,
        test_uniform_odds_gives_uniform_probabilities,
    ]
    passed = 0
    for t in tests:
        print(f"\n{t.__name__}:")
        try:
            t()
            print("  PASS")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
    sys.exit(0 if passed == len(tests) else 1)
