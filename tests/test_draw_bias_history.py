"""
Real tests for src/features/draw_bias_history.py — synthetic outcome
fixtures only. This module is deliberately opinionated about a real
course+distance draw bias (unlike runner_features.py's neutral
draw_percentile) — see the module docstring and docs/RESEARCH_LAB.md
RL-004/RL-008 for why, and why the sample-size floor matters.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.draw_bias_history import (
    HistoricalRaceOutcome,
    build_draw_bias_table,
    distance_band,
    draw_bias_edge,
    draw_tercile,
)


def _outcome(course_id=1, distance_yards=1400, draw=1, field_size=8, won=False):
    return HistoricalRaceOutcome(
        course_id=course_id, distance_yards=distance_yards, draw=draw,
        field_size=field_size, won=won,
    )


# ---------------------------------------------------------------------------
# distance_band / draw_tercile
# ---------------------------------------------------------------------------

def test_distance_band_rounds_down_to_band_width():
    assert distance_band(1400, band_width=220) == 1320  # 6f = 1320 yards
    assert distance_band(1320, band_width=220) == 1320
    assert distance_band(1539, band_width=220) == 1320
    assert distance_band(1540, band_width=220) == 1540  # 7f = 1540 yards


def test_draw_tercile_splits_field_into_thirds():
    # field_size=10 -> draws 1..10, percentile = (draw-1)/9
    assert draw_tercile(1, 10) == "LOW"    # percentile 0.0
    assert draw_tercile(3, 10) == "LOW"    # percentile 0.222
    assert draw_tercile(4, 10) == "MID"    # percentile 0.333
    assert draw_tercile(6, 10) == "MID"    # percentile 0.556
    assert draw_tercile(7, 10) == "HIGH"   # percentile 0.667 == 2/3, boundary lands in HIGH
    assert draw_tercile(10, 10) == "HIGH"  # percentile 1.0


def test_draw_tercile_single_runner_field_is_mid():
    assert draw_tercile(1, 1) == "MID"


# ---------------------------------------------------------------------------
# build_draw_bias_table
# ---------------------------------------------------------------------------

def test_build_table_excludes_buckets_below_min_sample_size():
    # 10 real outcomes in one bucket, min_sample_size=30 -> excluded
    outcomes = [_outcome(course_id=1, distance_yards=1400, draw=1, field_size=8, won=(i == 0)) for i in range(10)]
    table = build_draw_bias_table(outcomes, min_sample_size=30)
    assert table == {}


def test_build_table_includes_buckets_at_or_above_min_sample_size():
    # 30 real outcomes, low draw, 6 winners -> win rate 0.2 for that bucket
    outcomes = [
        _outcome(course_id=1, distance_yards=1400, draw=1, field_size=8, won=(i < 6))
        for i in range(30)
    ]
    table = build_draw_bias_table(outcomes, min_sample_size=30)
    key = (1, 1320, "LOW")  # 1400 yards bands down to 1320, draw=1/field=8 -> percentile 0.0 -> LOW
    assert key in table
    assert math.isclose(table[key], 0.2)


def test_build_table_separates_different_courses_distances_terciles():
    outcomes = (
        [_outcome(course_id=1, distance_yards=1400, draw=1, field_size=8, won=True) for _ in range(30)]
        + [_outcome(course_id=1, distance_yards=1400, draw=8, field_size=8, won=False) for _ in range(30)]
        + [_outcome(course_id=2, distance_yards=1400, draw=1, field_size=8, won=False) for _ in range(30)]
    )
    table = build_draw_bias_table(outcomes, min_sample_size=30)
    assert math.isclose(table[(1, 1320, "LOW")], 1.0)
    assert math.isclose(table[(1, 1320, "HIGH")], 0.0)
    assert math.isclose(table[(2, 1320, "LOW")], 0.0)


def test_build_table_empty_outcomes_returns_empty_table():
    assert build_draw_bias_table([]) == {}


# ---------------------------------------------------------------------------
# draw_bias_edge
# ---------------------------------------------------------------------------

def test_draw_bias_edge_returns_zero_for_missing_inputs():
    table = {(1, 1320, "LOW"): 0.5}
    assert draw_bias_edge(table, None, 1400, 1, 8) == 0.0
    assert draw_bias_edge(table, 1, None, 1, 8) == 0.0
    assert draw_bias_edge(table, 1, 1400, None, 8) == 0.0
    assert draw_bias_edge(table, 1, 1400, 1, 0) == 0.0
    assert draw_bias_edge(table, 1, 1400, 1, None) == 0.0


def test_draw_bias_edge_returns_zero_when_bucket_missing_from_table():
    table = {(1, 1320, "LOW"): 0.5}
    # this course/distance/tercile combo was never in the table (e.g. below min sample size)
    assert draw_bias_edge(table, 99, 1400, 1, 8) == 0.0


def test_draw_bias_edge_computes_edge_vs_uniform_expectation():
    # field_size=8 -> uniform expectation 0.125; table says this bucket
    # actually wins 0.3 of the time -> edge = 0.3 - 0.125 = 0.175
    table = {(1, 1320, "LOW"): 0.3}
    edge = draw_bias_edge(table, course_id=1, distance_yards=1400, draw=1, field_size=8)
    assert math.isclose(edge, 0.175)


def test_draw_bias_edge_negative_when_bucket_underperforms_uniform():
    table = {(1, 1320, "HIGH"): 0.05}  # worse than 1/8=0.125 uniform expectation
    edge = draw_bias_edge(table, course_id=1, distance_yards=1400, draw=8, field_size=8)
    assert edge < 0.0
    assert math.isclose(edge, 0.05 - 0.125)


if __name__ == "__main__":
    tests = [
        test_distance_band_rounds_down_to_band_width,
        test_draw_tercile_splits_field_into_thirds,
        test_draw_tercile_single_runner_field_is_mid,
        test_build_table_excludes_buckets_below_min_sample_size,
        test_build_table_includes_buckets_at_or_above_min_sample_size,
        test_build_table_separates_different_courses_distances_terciles,
        test_build_table_empty_outcomes_returns_empty_table,
        test_draw_bias_edge_returns_zero_for_missing_inputs,
        test_draw_bias_edge_returns_zero_when_bucket_missing_from_table,
        test_draw_bias_edge_computes_edge_vs_uniform_expectation,
        test_draw_bias_edge_negative_when_bucket_underperforms_uniform,
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
