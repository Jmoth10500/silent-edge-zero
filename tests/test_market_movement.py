"""
Real unit tests for src/market/movement.py — run with:
    python3 -m pytest tests/test_market_movement.py -v
or directly: python3 tests/test_market_movement.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.market.movement import (
    PriceObservation,
    opening_price,
    current_price,
    price_change_pct,
    max_price,
    min_price,
    movement_classification,
)

T0 = datetime(2026, 9, 8, 10, 0, tzinfo=timezone.utc)


def obs(hours_after_t0: float, odds: float) -> PriceObservation:
    return PriceObservation(observed_at=T0 + timedelta(hours=hours_after_t0), decimal_odds=odds)


def test_empty_observations_return_none():
    assert opening_price([]) is None
    assert current_price([]) is None
    assert price_change_pct([]) is None
    assert max_price([]) is None
    assert min_price([]) is None
    assert movement_classification([]) == "UNKNOWN"


def test_single_observation_has_no_change():
    single = [obs(0, 5.0)]
    assert opening_price(single) == 5.0
    assert current_price(single) == 5.0
    assert price_change_pct(single) is None  # need >= 2 points to measure movement
    assert movement_classification(single) == "UNKNOWN"


def test_opening_and_current_price_use_time_order_not_list_order():
    # Deliberately out of chronological order in the list itself.
    observations = [obs(3, 4.0), obs(0, 6.0), obs(1.5, 5.0)]
    assert opening_price(observations) == 6.0   # earliest by observed_at
    assert current_price(observations) == 4.0   # latest by observed_at


def test_shortening_price_change_is_negative():
    observations = [obs(0, 10.0), obs(1, 8.0), obs(2, 5.0)]
    pct = price_change_pct(observations)
    assert pct == (5.0 - 10.0) / 10.0 * 100.0
    assert pct < 0
    assert movement_classification(observations) == "SHORTENING"


def test_drifting_price_change_is_positive():
    observations = [obs(0, 4.0), obs(1, 6.0)]
    pct = price_change_pct(observations)
    assert pct == (6.0 - 4.0) / 4.0 * 100.0
    assert pct > 0
    assert movement_classification(observations) == "DRIFTING"


def test_small_movement_classified_as_steady():
    # 4.0 -> 4.1 is a 2.5% drift, inside the default +-5% noise threshold.
    observations = [obs(0, 4.0), obs(1, 4.1)]
    assert movement_classification(observations) == "STEADY"


def test_threshold_is_configurable():
    observations = [obs(0, 4.0), obs(1, 4.1)]  # +2.5%
    assert movement_classification(observations, threshold_pct=1.0) == "DRIFTING"


def test_max_and_min_price_across_history():
    observations = [obs(0, 5.0), obs(1, 3.0), obs(2, 7.0), obs(3, 4.0)]
    assert max_price(observations) == 7.0
    assert min_price(observations) == 3.0


if __name__ == "__main__":
    tests = [
        test_empty_observations_return_none,
        test_single_observation_has_no_change,
        test_opening_and_current_price_use_time_order_not_list_order,
        test_shortening_price_change_is_negative,
        test_drifting_price_change_is_positive,
        test_small_movement_classified_as_steady,
        test_threshold_is_configurable,
        test_max_and_min_price_across_history,
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
