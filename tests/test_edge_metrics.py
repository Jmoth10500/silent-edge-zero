"""
Real tests for src/analysis/edge_metrics.py — validated against the
exact worked examples in Jonathan's own spec (2026-09-11) wherever he
gave one, so the implementation is checked against his own numbers, not
just internal consistency.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.edge_metrics import (
    expected_value,
    model_agreement_label,
    model_fair_odds,
    normalized_market_probabilities,
    price_advantage,
    probability_edge,
    raw_market_implied_probability,
)


def test_model_fair_odds_real_example():
    # spec: 22% probability = decimal fair odds of 4.55
    assert round(model_fair_odds(0.22), 2) == 4.55


def test_model_fair_odds_none_for_non_positive():
    assert model_fair_odds(0.0) is None
    assert model_fair_odds(None) is None


def test_raw_market_implied_probability_real_example():
    # spec: 8.60 = 11.63%
    assert round(raw_market_implied_probability(8.60), 4) == round(0.11628, 4)


def test_raw_market_implied_probability_none_without_price():
    assert raw_market_implied_probability(None) is None
    assert raw_market_implied_probability(0) is None


def test_normalized_market_probabilities_sums_to_one():
    odds = {"A": 2.0, "B": 4.0, "C": 4.0}  # raw implied: 0.5, 0.25, 0.25 -> already sums to 1.0
    probs = normalized_market_probabilities(odds)
    assert abs(sum(probs.values()) - 1.0) < 1e-9
    assert probs["A"] == 0.5


def test_normalized_market_probabilities_real_overround_removed():
    # real book with overround: raw implieds sum to > 1.0
    odds = {"A": 2.0, "B": 3.0, "C": 3.0}  # raw: 0.5 + 0.333 + 0.333 = 1.167 (16.7% overround)
    probs = normalized_market_probabilities(odds)
    assert abs(sum(probs.values()) - 1.0) < 1e-9
    # A's real share of that book should still be proportionally the largest
    assert probs["A"] > probs["B"] == probs["C"]


def test_normalized_market_probabilities_needs_two_priced_runners():
    assert normalized_market_probabilities({"A": 2.0}) == {}
    assert normalized_market_probabilities({}) == {}
    assert normalized_market_probabilities({"A": 2.0, "B": None}) == {}


def test_probability_edge_real_example():
    # spec: 22.0% model, 11.6% market = +10.4 percentage-point edge
    edge = probability_edge(0.220, 0.116)
    assert round(edge, 3) == round(0.104, 3)


def test_probability_edge_none_without_market_probability():
    assert probability_edge(0.22, None) is None


def test_price_advantage_real_example():
    # spec: 8.60 / 4.55 - 1 = +89%
    adv = price_advantage(8.60, 4.55)
    assert round(adv, 2) == 0.89


def test_price_advantage_none_without_real_prices():
    assert price_advantage(None, 4.55) is None
    assert price_advantage(8.60, None) is None


def test_expected_value_real_example_no_commission():
    # spec: 0.22 * 8.60 - 1 = +0.892
    ev = expected_value(0.22, 8.60, commission=0.0)
    assert round(ev["gross_ev"], 3) == round(0.892, 3)
    assert ev["net_ev"] == ev["gross_ev"]  # no commission -> identical
    assert ev["commission"] == 0.0


def test_expected_value_never_assumes_commission_by_default():
    ev = expected_value(0.22, 8.60)
    assert ev["commission"] == 0.0


def test_expected_value_net_lower_than_gross_with_real_commission():
    ev = expected_value(0.22, 8.60, commission=0.02)  # Smarkets' real standard rate
    assert ev["net_ev"] < ev["gross_ev"]
    # commission only bites the winning-profit portion, never the stake
    expected_net = 0.22 * (8.60 - 1.0) * 0.98 - 0.78 * 1.0
    assert round(ev["net_ev"], 4) == round(expected_net, 4)


def test_expected_value_none_without_real_market_odds():
    ev = expected_value(0.22, None)
    assert ev["gross_ev"] is None and ev["net_ev"] is None


def test_expected_value_rejects_invalid_commission():
    try:
        expected_value(0.22, 8.60, commission=1.5)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_model_agreement_label_real_examples():
    # spec: Model 1: 24%, Model 2: 22% -> STRONG (diff 2pts)
    assert model_agreement_label(0.24, 0.22) == "Strong Agreement"
    # spec: Model 1: 28%, Model 2: 12% -> LOW/disagreement (diff 16pts)
    assert model_agreement_label(0.28, 0.12) == "Disagreement"


def test_model_agreement_label_moderate_band():
    assert model_agreement_label(0.20, 0.25) == "Moderate Agreement"  # diff 5pts


def test_model_agreement_label_none_without_both_probabilities():
    assert model_agreement_label(0.20, None) is None
    assert model_agreement_label(None, 0.20) is None


if __name__ == "__main__":
    tests = [
        test_model_fair_odds_real_example,
        test_model_fair_odds_none_for_non_positive,
        test_raw_market_implied_probability_real_example,
        test_raw_market_implied_probability_none_without_price,
        test_normalized_market_probabilities_sums_to_one,
        test_normalized_market_probabilities_real_overround_removed,
        test_normalized_market_probabilities_needs_two_priced_runners,
        test_probability_edge_real_example,
        test_probability_edge_none_without_market_probability,
        test_price_advantage_real_example,
        test_price_advantage_none_without_real_prices,
        test_expected_value_real_example_no_commission,
        test_expected_value_never_assumes_commission_by_default,
        test_expected_value_net_lower_than_gross_with_real_commission,
        test_expected_value_none_without_real_market_odds,
        test_expected_value_rejects_invalid_commission,
        test_model_agreement_label_real_examples,
        test_model_agreement_label_moderate_band,
        test_model_agreement_label_none_without_both_probabilities,
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
