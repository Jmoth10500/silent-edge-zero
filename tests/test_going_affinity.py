"""
Real tests for src/features/going_affinity.py — synthetic fixtures only.
See the module docstring for why this is an interaction feature (RL-001),
not a bare weather/going main effect.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.going_affinity import (
    HistoricalGoingRecord,
    build_going_affinity_table,
    going_interaction_edge,
    going_scale_and_value,
    is_soft_side,
)


def _rec(horse_id, going, finishing_position, field_size=8):
    return HistoricalGoingRecord(
        horse_id=horse_id, going=going, finishing_position=finishing_position, field_size=field_size,
    )


# ---------------------------------------------------------------------------
# going_scale_and_value / is_soft_side
# ---------------------------------------------------------------------------

def test_turf_scale_recognised():
    scale, value = going_scale_and_value("Good To Soft")
    assert scale == "turf"
    assert value == 3


def test_aw_scale_recognised():
    scale, value = going_scale_and_value("Standard To Slow")
    assert scale == "aw"
    assert value == 2


def test_unrecognised_going_returns_none():
    assert going_scale_and_value("Sloppy") == (None, None)
    assert going_scale_and_value(None) == (None, None)
    assert going_scale_and_value("") == (None, None)


def test_is_soft_side_turf_threshold():
    assert is_soft_side("Heavy") is True
    assert is_soft_side("Good To Soft") is True   # exactly at threshold
    assert is_soft_side("Good") is False
    assert is_soft_side("Firm") is False


def test_is_soft_side_aw_threshold():
    assert is_soft_side("Slow") is True
    assert is_soft_side("Standard To Slow") is True  # exactly at threshold
    assert is_soft_side("Standard") is False
    assert is_soft_side("Fast") is False


def test_is_soft_side_none_for_unrecognised():
    assert is_soft_side("Muddy") is None


# ---------------------------------------------------------------------------
# build_going_affinity_table
# ---------------------------------------------------------------------------

def test_table_requires_min_runs_on_both_sides():
    # horse 1: only 1 soft run, 3 fast runs -> excluded (needs >=2 on EACH side)
    records = [
        _rec(1, "Heavy", finishing_position=1, field_size=8),
        _rec(1, "Good", finishing_position=2, field_size=8),
        _rec(1, "Good", finishing_position=3, field_size=8),
        _rec(1, "Good", finishing_position=1, field_size=8),
    ]
    table = build_going_affinity_table(records, min_runs_per_side=2)
    assert 1 not in table


def test_table_computes_real_affinity_difference():
    # horse 2: soft-side runs win (percentile 1.0 both), fast-side runs
    # finish last (percentile 0.0 both) -> affinity = 1.0 - 0.0 = 1.0
    records = [
        _rec(2, "Heavy", finishing_position=1, field_size=8),
        _rec(2, "Soft", finishing_position=1, field_size=8),
        _rec(2, "Firm", finishing_position=8, field_size=8),
        _rec(2, "Good To Firm", finishing_position=8, field_size=8),
    ]
    table = build_going_affinity_table(records, min_runs_per_side=2)
    assert math.isclose(table[2], 1.0)


def test_table_excludes_unrecognised_going_from_either_side():
    # 'Sloppy' runs are simply dropped, not counted toward either side
    records = [
        _rec(3, "Sloppy", finishing_position=1, field_size=8),
        _rec(3, "Heavy", finishing_position=1, field_size=8),
        _rec(3, "Soft", finishing_position=2, field_size=8),
        _rec(3, "Good", finishing_position=4, field_size=8),
        _rec(3, "Firm", finishing_position=5, field_size=8),
    ]
    table = build_going_affinity_table(records, min_runs_per_side=2)
    assert 3 in table  # 2 soft, 2 fast real runs — enough


def test_table_empty_records_returns_empty_table():
    assert build_going_affinity_table([]) == {}


# ---------------------------------------------------------------------------
# going_interaction_edge
# ---------------------------------------------------------------------------

def test_interaction_edge_positive_when_soft_specialist_runs_on_soft_ground():
    table = {5: 0.4}  # soft-ground specialist
    edge = going_interaction_edge(5, "Heavy", table)
    assert math.isclose(edge, 0.4)


def test_interaction_edge_negative_when_soft_specialist_runs_on_fast_ground():
    table = {5: 0.4}
    edge = going_interaction_edge(5, "Firm", table)
    assert math.isclose(edge, -0.4)


def test_interaction_edge_zero_for_unknown_horse():
    table = {5: 0.4}
    assert going_interaction_edge(999, "Heavy", table) == 0.0


def test_interaction_edge_zero_for_missing_or_unrecognised_going():
    table = {5: 0.4}
    assert going_interaction_edge(5, None, table) == 0.0
    assert going_interaction_edge(5, "Sloppy", table) == 0.0


def test_interaction_edge_zero_for_none_horse_id():
    table = {5: 0.4}
    assert going_interaction_edge(None, "Heavy", table) == 0.0


if __name__ == "__main__":
    tests = [
        test_turf_scale_recognised,
        test_aw_scale_recognised,
        test_unrecognised_going_returns_none,
        test_is_soft_side_turf_threshold,
        test_is_soft_side_aw_threshold,
        test_is_soft_side_none_for_unrecognised,
        test_table_requires_min_runs_on_both_sides,
        test_table_computes_real_affinity_difference,
        test_table_excludes_unrecognised_going_from_either_side,
        test_table_empty_records_returns_empty_table,
        test_interaction_edge_positive_when_soft_specialist_runs_on_soft_ground,
        test_interaction_edge_negative_when_soft_specialist_runs_on_fast_ground,
        test_interaction_edge_zero_for_unknown_horse,
        test_interaction_edge_zero_for_missing_or_unrecognised_going,
        test_interaction_edge_zero_for_none_horse_id,
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
