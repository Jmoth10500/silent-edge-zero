"""
Real unit tests for src/features/feature_vector.py, run against clearly
synthetic fixtures (never real racecard data) — run with:
    python3 -m pytest tests/test_feature_vector.py -v
or directly: python3 tests/test_feature_vector.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.feature_vector import build_runner_feature_vectors
from src.features.runner_features import RunnerFeatureInput, form_score
from src.market.movement import PriceObservation

TOL = 1e-9


def _t(minutes_ago: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc) - timedelta(minutes=minutes_ago)


def test_empty_runners_returns_empty_dict():
    assert build_runner_feature_vectors([]) == {}


def test_every_runner_gets_an_entry_even_with_no_known_fields():
    runners = [RunnerFeatureInput(horse_id=1)]
    out = build_runner_feature_vectors(runners)
    assert out == {1: {"horse_id": 1}}


def test_full_merge_across_all_three_sources():
    runners = [
        RunnerFeatureInput(
            horse_id=1,
            age=5,
            draw=2,
            weight_lbs=126,
            official_rating=90,
            recent_form="1-2-1",
            days_since_last_run=21,
        ),
        RunnerFeatureInput(
            horse_id=2,
            age=4,
            draw=8,
            weight_lbs=120,
            official_rating=80,
            recent_form="5-4-3",
            days_since_last_run=14,
        ),
    ]
    price_history = {
        1: [
            PriceObservation(observed_at=_t(60), decimal_odds=5.0),
            PriceObservation(observed_at=_t(10), decimal_odds=4.0),
        ],
        2: [
            PriceObservation(observed_at=_t(60), decimal_odds=6.0),
            PriceObservation(observed_at=_t(10), decimal_odds=8.0),
        ],
    }

    out = build_runner_feature_vectors(runners, price_history=price_history)

    assert set(out.keys()) == {1, 2}

    v1 = out[1]
    # Section 8 raw fields carried straight through.
    assert v1["age"] == 5
    assert v1["days_since_last_run"] == 21
    assert abs(v1["form_score"] - form_score("1-2-1", recency_weighted=True)) < TOL
    # Section 10 relative fields: horse 1 is the better-rated, lower-drawn,
    # heavier-weighted runner of the pair.
    assert v1["official_rating"] == 90
    assert v1["rating_rank"] == 1
    assert v1["rating_percentile"] == 1.0
    assert v1["rating_vs_mean"] == 5.0
    assert v1["draw"] == 2
    assert v1["field_size"] == 2
    assert v1["draw_percentile"] == 0.0  # lowest draw present
    assert v1["weight_lbs"] == 126
    assert v1["weight_vs_mean_lbs"] == 3.0
    # Section 16 price fields: shortened from 5.0 to 4.0.
    assert v1["opening_price"] == 5.0
    assert v1["current_price"] == 4.0
    assert abs(v1["price_change_pct"] - ((4.0 - 5.0) / 5.0 * 100.0)) < TOL
    assert v1["movement_classification"] == "SHORTENING"

    v2 = out[2]
    assert v2["rating_rank"] == 2
    assert v2["rating_percentile"] == 0.0
    assert v2["draw_percentile"] == 1.0  # highest draw present
    assert v2["movement_classification"] == "DRIFTING"


def test_missing_rating_omits_only_rating_keys_not_the_whole_runner():
    runners = [
        RunnerFeatureInput(horse_id=1, official_rating=90),
        RunnerFeatureInput(horse_id=2, official_rating=None, age=6),
    ]
    out = build_runner_feature_vectors(runners)
    assert "official_rating" not in out[2]
    assert "rating_rank" not in out[2]
    assert out[2]["age"] == 6
    assert out[1]["official_rating"] == 90


def test_no_price_history_entry_means_no_price_keys():
    runners = [RunnerFeatureInput(horse_id=1, age=5)]
    out = build_runner_feature_vectors(runners, price_history={})
    assert "opening_price" not in out[1]
    assert "current_price" not in out[1]
    assert "movement_classification" not in out[1]


def test_single_price_observation_gives_prices_but_no_change_pct():
    runners = [RunnerFeatureInput(horse_id=1)]
    price_history = {1: [PriceObservation(observed_at=_t(5), decimal_odds=3.0)]}
    out = build_runner_feature_vectors(runners, price_history=price_history)
    assert out[1]["opening_price"] == 3.0
    assert out[1]["current_price"] == 3.0
    assert "price_change_pct" not in out[1]
    assert out[1]["movement_classification"] == "UNKNOWN"


def test_recency_weighted_form_flag_is_threaded_through():
    runners = [RunnerFeatureInput(horse_id=1, recent_form="1-5")]
    weighted = build_runner_feature_vectors(runners, recency_weighted_form=True)[1]["form_score"]
    flat = build_runner_feature_vectors(runners, recency_weighted_form=False)[1]["form_score"]
    assert weighted != flat
    assert flat == 3.0  # (1 + 5) / 2
    assert abs(weighted - (1 * 1 + 5 * 2) / 3) < TOL


if __name__ == "__main__":
    tests = [
        test_empty_runners_returns_empty_dict,
        test_every_runner_gets_an_entry_even_with_no_known_fields,
        test_full_merge_across_all_three_sources,
        test_missing_rating_omits_only_rating_keys_not_the_whole_runner,
        test_no_price_history_entry_means_no_price_keys,
        test_single_price_observation_gives_prices_but_no_change_pct,
        test_recency_weighted_form_flag_is_threaded_through,
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
