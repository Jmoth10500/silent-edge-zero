"""
Real tests for src/research/trainer_intelligence_c.py — brief Section 12C
(Trainer Intelligence Lab, Hypothesis C: observable hidden improvement).
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.trainer_intelligence_c import compute_improvement_features
from src.research.trainer_intelligence_c import test_hidden_improvement_hypothesis as run_hidden_improvement_test


def _run(race_id, race_date, distance_beaten=None, equipment=None, days_since_last_run=None,
         finishing_position=None, result_note=None, starting_price=None):
    return {
        "race_id": race_id, "race_date": race_date, "race_class": 4, "distance_yards": 1600, "going": "Good",
        "equipment": equipment, "days_since_last_run": days_since_last_run,
        "finishing_position": finishing_position, "result_note": result_note,
        "distance_beaten": distance_beaten, "starting_price": starting_price,
    }


# ---------------------------------------------------------------------------
# compute_improvement_features
# ---------------------------------------------------------------------------

def test_needs_two_strictly_prior_runs():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), distance_beaten=5.0),
        _run(2, date(2026, 2, 1), distance_beaten=3.0),
    ]}
    # only 2 runs total -> the 3rd (index 2) doesn't exist, so no features
    assert compute_improvement_features(runs_by_horse) == []


def test_improving_trend_true_when_beaten_lengths_shrink():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), distance_beaten=8.0),
        _run(2, date(2026, 2, 1), distance_beaten=3.0),  # closer than run 1
        _run(3, date(2026, 3, 1), distance_beaten=1.0),
    ]}
    features = compute_improvement_features(runs_by_horse)
    assert len(features) == 1
    assert features[0]["improving_beaten_length_trend"] is True


def test_improving_trend_false_when_beaten_lengths_grow():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), distance_beaten=1.0),
        _run(2, date(2026, 2, 1), distance_beaten=5.0),  # further back than run 1
        _run(3, date(2026, 3, 1), distance_beaten=2.0),
    ]}
    features = compute_improvement_features(runs_by_horse)
    assert features[0]["improving_beaten_length_trend"] is False


def test_improving_trend_none_when_data_missing():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), distance_beaten=None),  # unknown
        _run(2, date(2026, 2, 1), distance_beaten=3.0),
        _run(3, date(2026, 3, 1), distance_beaten=1.0),
    ]}
    features = compute_improvement_features(runs_by_horse)
    assert features[0]["improving_beaten_length_trend"] is None


def test_equipment_change_detected_only_on_a_real_change():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), distance_beaten=5.0, equipment="blinkers"),
        _run(2, date(2026, 2, 1), distance_beaten=3.0, equipment="blinkers"),
        _run(3, date(2026, 3, 1), distance_beaten=1.0, equipment="visor"),  # real change from "blinkers"
    ]}
    features = compute_improvement_features(runs_by_horse)
    assert features[0]["equipment_change"] is True


def test_equipment_change_false_when_both_runs_have_no_equipment():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), distance_beaten=5.0, equipment=None),
        _run(2, date(2026, 2, 1), distance_beaten=3.0, equipment=None),
        _run(3, date(2026, 3, 1), distance_beaten=1.0, equipment=None),  # never inferred as a "change"
    ]}
    features = compute_improvement_features(runs_by_horse)
    assert features[0]["equipment_change"] is False


def test_return_from_break_threshold():
    runs_by_horse = {"Horse A": [
        _run(1, date(2026, 1, 1), distance_beaten=5.0),
        _run(2, date(2026, 2, 1), distance_beaten=3.0),
        _run(3, date(2026, 3, 1), distance_beaten=1.0, days_since_last_run=59),
        _run(4, date(2026, 4, 1), distance_beaten=1.0, days_since_last_run=60),
    ]}
    features = compute_improvement_features(runs_by_horse)
    assert features[0]["return_from_break"] is False  # 59 days
    assert features[1]["return_from_break"] is True    # 60 days


# ---------------------------------------------------------------------------
# test_hidden_improvement_hypothesis
# ---------------------------------------------------------------------------

def _feature(race_id, improving, equipment_change, return_from_break, finishing_position, starting_price):
    return {
        "race_id": race_id, "improving_beaten_length_trend": improving, "equipment_change": equipment_change,
        "return_from_break": return_from_break, "finishing_position": finishing_position,
        "result_note": None, "starting_price": starting_price,
    }


def test_hypothesis_qualifies_only_on_the_full_combination():
    features = [
        # Race 1: qualifies (improving trend + equipment change), wins
        _feature(1, True, True, False, finishing_position=1, starting_price=3.0),
        _feature(1, False, False, False, finishing_position=2, starting_price=2.0),
        # Race 2: improving trend alone, no equipment/break change -> control
        _feature(2, True, False, False, finishing_position=1, starting_price=2.0),
        _feature(2, False, False, False, finishing_position=2, starting_price=3.0),
    ]
    result = run_hidden_improvement_test(features)
    assert result["qualifying_group"]["n"] == 1
    assert result["qualifying_group"]["actual_wins"] == 1
    assert result["control_group"]["n"] == 3


def test_hypothesis_excludes_unknown_trend_from_both_groups():
    features = [
        _feature(1, None, True, False, finishing_position=1, starting_price=2.0),  # unknown trend -> excluded
        _feature(1, False, False, False, finishing_position=2, starting_price=3.0),
        _feature(1, False, False, False, finishing_position=3, starting_price=4.0),
    ]
    result = run_hidden_improvement_test(features)
    # only the two known-trend runners contribute; the unknown-trend one is dropped entirely
    assert result["control_group"]["n"] == 2
    assert result["qualifying_group"] is None


if __name__ == "__main__":
    tests = [
        test_needs_two_strictly_prior_runs, test_improving_trend_true_when_beaten_lengths_shrink,
        test_improving_trend_false_when_beaten_lengths_grow, test_improving_trend_none_when_data_missing,
        test_equipment_change_detected_only_on_a_real_change, test_equipment_change_false_when_both_runs_have_no_equipment,
        test_return_from_break_threshold,
        test_hypothesis_qualifies_only_on_the_full_combination, test_hypothesis_excludes_unknown_trend_from_both_groups,
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
