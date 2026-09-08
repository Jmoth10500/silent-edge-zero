"""
Real unit tests for src/features/draw_bias.py, run against clearly
synthetic fixtures (never real racecard/results data) — run with:
    python3 -m pytest tests/test_draw_bias.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.draw_bias import (
    HistoricalDrawRecord,
    draw_percentile_bucket,
    compute_course_distance_draw_bias,
)

TOL = 1e-9


# ---- draw_percentile_bucket --------------------------------------------

def test_bucket_boundaries_nine_runner_field_three_buckets():
    # draws 1-9, num_buckets=3 -> buckets of 3: [1,2,3]=0 [4,5,6]=1 [7,8,9]=2
    expected = {1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1, 7: 2, 8: 2, 9: 2}
    for draw, bucket in expected.items():
        assert draw_percentile_bucket(draw, field_size=9, num_buckets=3) == bucket


def test_bucket_uneven_field_size_still_partitions_every_draw():
    # field_size=10, num_buckets=3 -> bucket = (d-1)*3 // 10, hand-worked:
    # draw 1..4 -> 0,3,6,9 // 10 = 0; draw 5..7 -> 12,15,18 // 10 = 1;
    # draw 8..10 -> 21,24,27 // 10 = 2
    expected = {1: 0, 2: 0, 3: 0, 4: 0, 5: 1, 6: 1, 7: 1, 8: 2, 9: 2, 10: 2}
    for draw, bucket in expected.items():
        assert draw_percentile_bucket(draw, field_size=10, num_buckets=3) == bucket


def test_bucket_none_when_field_too_small_for_bucket_count():
    assert draw_percentile_bucket(1, field_size=2, num_buckets=3) is None


def test_bucket_none_when_draw_out_of_range():
    assert draw_percentile_bucket(0, field_size=9, num_buckets=3) is None
    assert draw_percentile_bucket(10, field_size=9, num_buckets=3) is None


# ---- compute_course_distance_draw_bias ----------------------------------

def _ten_races_low_draw_bias(course_id=1, distance_yards=1600, surface="Turf"):
    """10 synthetic 9-runner historical races at the same course/distance/
    surface. In every race, draw=2 wins and nothing else does. Hand-worked
    bucket stats (num_buckets=3, so buckets are draws {1,2,3}/{4,5,6}/{7,8,9}):
      bucket0: 10 races * 3 draws (1,2,3) = 30 runners, 10 wins (draw=2 each time)
      bucket1: 30 runners, 0 wins
      bucket2: 30 runners, 0 wins
      totals:  90 runners, 10 wins -> baseline_win_rate = 10/90 = 1/9
    """
    records = []
    for _ in range(10):
        for draw in range(1, 10):
            records.append(
                HistoricalDrawRecord(
                    course_id=course_id,
                    distance_yards=distance_yards,
                    draw=draw,
                    field_size=9,
                    finishing_position=1 if draw == 2 else 2,
                    surface=surface,
                )
            )
    return records


def test_bias_hand_verified_favoured_bucket():
    records = _ten_races_low_draw_bias()
    result = compute_course_distance_draw_bias(
        records, course_id=1, distance_yards=1600, draw=2, field_size=9,
        surface="Turf", num_buckets=3, min_sample_size=30,
    )
    assert result is not None
    assert result["draw_bucket"] == 0
    assert abs(result["bucket_win_rate"] - (1 / 3)) < TOL
    assert abs(result["baseline_win_rate"] - (1 / 9)) < TOL
    assert abs(result["win_rate_vs_baseline"] - (2 / 9)) < TOL
    assert result["bucket_sample_size"] == 30
    assert result["group_sample_size"] == 90


def test_bias_hand_verified_unfavoured_bucket():
    records = _ten_races_low_draw_bias()
    result = compute_course_distance_draw_bias(
        records, course_id=1, distance_yards=1600, draw=8, field_size=9,
        surface="Turf", num_buckets=3, min_sample_size=30,
    )
    assert result is not None
    assert result["draw_bucket"] == 2
    assert result["bucket_win_rate"] == 0.0
    assert abs(result["baseline_win_rate"] - (1 / 9)) < TOL
    assert abs(result["win_rate_vs_baseline"] - (-1 / 9)) < TOL


def test_bias_none_when_query_draw_unbucketable():
    records = _ten_races_low_draw_bias()
    result = compute_course_distance_draw_bias(
        records, course_id=1, distance_yards=1600, draw=0, field_size=9,
        surface="Turf",
    )
    assert result is None


def test_bias_none_when_sample_size_below_threshold():
    records = _ten_races_low_draw_bias()[:20]  # only ~20 historical runners
    result = compute_course_distance_draw_bias(
        records, course_id=1, distance_yards=1600, draw=2, field_size=9,
        surface="Turf", min_sample_size=30,
    )
    assert result is None


def test_bias_none_when_course_does_not_match():
    records = _ten_races_low_draw_bias(course_id=1)
    result = compute_course_distance_draw_bias(
        records, course_id=999, distance_yards=1600, draw=2, field_size=9,
        surface="Turf",
    )
    assert result is None


def test_bias_none_when_surface_does_not_match():
    records = _ten_races_low_draw_bias(surface="Turf")
    result = compute_course_distance_draw_bias(
        records, course_id=1, distance_yards=1600, draw=2, field_size=9,
        surface="AW",
    )
    assert result is None


def test_bias_surface_none_pools_separately_from_a_named_surface():
    # Records with surface=None form their own group, distinct from "Turf".
    records = _ten_races_low_draw_bias(surface=None)
    result_matching = compute_course_distance_draw_bias(
        records, course_id=1, distance_yards=1600, draw=2, field_size=9,
        surface=None, min_sample_size=30,
    )
    result_mismatched = compute_course_distance_draw_bias(
        records, course_id=1, distance_yards=1600, draw=2, field_size=9,
        surface="Turf", min_sample_size=30,
    )
    assert result_matching is not None
    assert result_mismatched is None


def test_bias_none_when_target_bucket_has_zero_historical_runners():
    # Group meets min_sample_size overall, but every historical draw is in
    # bucket 0 or 1 -- bucket 2 (draws 7-9) has literally no data.
    records = []
    for _ in range(10):
        for draw in (1, 2, 3, 4, 5, 6):
            records.append(
                HistoricalDrawRecord(
                    course_id=1, distance_yards=1600, draw=draw,
                    field_size=9, finishing_position=2, surface="Turf",
                )
            )
    result = compute_course_distance_draw_bias(
        records, course_id=1, distance_yards=1600, draw=8, field_size=9,
        surface="Turf", min_sample_size=30,
    )
    assert result is None


def test_bias_finishing_position_none_excluded_from_sample():
    # Non-runners (finishing_position=None) must not count toward the
    # sample size or the win-rate arithmetic.
    records = [
        HistoricalDrawRecord(
            course_id=1, distance_yards=1600, draw=d, field_size=9,
            finishing_position=None, surface="Turf",
        )
        for d in range(1, 10)
    ] * 5  # 45 non-runner rows, all excluded
    result = compute_course_distance_draw_bias(
        records, course_id=1, distance_yards=1600, draw=2, field_size=9,
        surface="Turf", min_sample_size=30,
    )
    assert result is None  # 0 real runners in the group despite 45 rows


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
