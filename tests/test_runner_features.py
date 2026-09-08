"""
Real unit tests for src/features/runner_features.py, run against clearly
synthetic fixtures (never real racecard data) — run with:
    python3 -m pytest tests/test_runner_features.py -v
or directly: python3 tests/test_runner_features.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.runner_features import (
    RunnerFeatureInput,
    parse_recent_form,
    form_score,
    relative_official_rating,
    draw_bias_features,
    relative_weight,
)

TOL = 1e-9


# ---- form parsing -----------------------------------------------------

def test_parse_recent_form_handles_digits_and_zero():
    assert parse_recent_form("1-3-6-2") == [1, 3, 6, 2]
    assert parse_recent_form("10") == [1, 10]  # '1' then '0' (10th-or-worse)


def test_parse_recent_form_handles_non_completion_codes():
    assert parse_recent_form("132F6") == [1, 3, 2, 12, 6]


def test_parse_recent_form_empty_input():
    assert parse_recent_form(None) == []
    assert parse_recent_form("") == []


def test_form_score_unweighted_average():
    assert form_score("1-3-6-2", recency_weighted=False) == (1 + 3 + 6 + 2) / 4


def test_form_score_recency_weighted_matches_hand_calc():
    # positions [1,3,6,2], weights [1,2,3,4] -> (1+6+18+8)/10 = 3.3
    score = form_score("1-3-6-2", recency_weighted=True)
    assert abs(score - 3.3) < TOL


def test_form_score_none_for_unparseable_form():
    assert form_score(None) is None
    assert form_score("") is None


def test_form_score_single_run_ignores_weighting_flag():
    assert form_score("5", recency_weighted=True) == 5.0
    assert form_score("5", recency_weighted=False) == 5.0


# ---- Section 10: relative/percentile features --------------------------

# A 4-runner synthetic race — never real racecard data.
RACE = [
    RunnerFeatureInput(horse_id=1, official_rating=90, draw=1, weight_lbs=126),
    RunnerFeatureInput(horse_id=2, official_rating=80, draw=4, weight_lbs=140),
    RunnerFeatureInput(horse_id=3, official_rating=100, draw=2, weight_lbs=133),
    RunnerFeatureInput(horse_id=4, official_rating=None, draw=None, weight_lbs=None),  # missing data on purpose
]


def test_relative_official_rating_ranks_and_percentiles():
    result = relative_official_rating(RACE)
    assert set(result.keys()) == {1, 2, 3}  # horse 4 omitted, no rating
    assert result[3]["rank"] == 1  # 100 is the highest rating
    assert result[1]["rank"] == 2  # 90
    assert result[2]["rank"] == 3  # 80 is the lowest of the three rated
    assert result[3]["percentile"] == 1.0
    assert result[2]["percentile"] == 0.0
    mean_rating = (90 + 80 + 100) / 3
    assert abs(result[1]["rating_vs_mean"] - (90 - mean_rating)) < TOL


def test_relative_official_rating_ties_share_rank_one():
    tied = [
        RunnerFeatureInput(horse_id=1, official_rating=90),
        RunnerFeatureInput(horse_id=2, official_rating=90),
        RunnerFeatureInput(horse_id=3, official_rating=70),
    ]
    result = relative_official_rating(tied)
    assert result[1]["rank"] == 1
    assert result[2]["rank"] == 1
    assert result[3]["rank"] == 3


def test_relative_official_rating_empty_when_nobody_rated():
    unrated = [RunnerFeatureInput(horse_id=1), RunnerFeatureInput(horse_id=2)]
    assert relative_official_rating(unrated) == {}


def test_draw_bias_features_percentiles_span_zero_to_one():
    result = draw_bias_features(RACE)
    assert set(result.keys()) == {1, 2, 3}  # horse 4 has no draw
    assert result[1]["draw_percentile"] == 0.0  # draw 1 is lowest present
    assert result[2]["draw_percentile"] == 1.0  # draw 4 is highest present
    assert 0.0 < result[3]["draw_percentile"] < 1.0  # draw 2 is in between
    assert result[1]["field_size"] == len(RACE)


def test_draw_bias_features_single_draw_defaults_to_midpoint():
    single = [RunnerFeatureInput(horse_id=1, draw=3)]
    result = draw_bias_features(single)
    assert result[1]["draw_percentile"] == 0.5


def test_relative_weight_vs_mean():
    result = relative_weight(RACE)
    assert set(result.keys()) == {1, 2, 3}
    mean_weight = (126 + 140 + 133) / 3
    assert abs(result[1]["weight_vs_mean_lbs"] - (126 - mean_weight)) < TOL
    assert result[2]["weight_vs_mean_lbs"] > 0  # 140 is above average
    assert result[1]["weight_vs_mean_lbs"] < 0  # 126 is below average


if __name__ == "__main__":
    tests = [
        test_parse_recent_form_handles_digits_and_zero,
        test_parse_recent_form_handles_non_completion_codes,
        test_parse_recent_form_empty_input,
        test_form_score_unweighted_average,
        test_form_score_recency_weighted_matches_hand_calc,
        test_form_score_none_for_unparseable_form,
        test_form_score_single_run_ignores_weighting_flag,
        test_relative_official_rating_ranks_and_percentiles,
        test_relative_official_rating_ties_share_rank_one,
        test_relative_official_rating_empty_when_nobody_rated,
        test_draw_bias_features_percentiles_span_zero_to_one,
        test_draw_bias_features_single_draw_defaults_to_midpoint,
        test_relative_weight_vs_mean,
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
