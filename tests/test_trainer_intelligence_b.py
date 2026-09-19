"""
Real tests for src/research/trainer_intelligence_b.py — brief Section
12B (Trainer Intelligence Lab, Hypothesis B). Checks the leakage-safe
benchmark discipline explicitly: the comparison must always be against
the EARLY (pre_max) price, never the later (bsp) one.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.trainer_intelligence_b import (
    compute_movement_features,
    trainer_shortening_summary,
)
from src.research.trainer_intelligence_b import test_price_movement_hypothesis as run_price_movement_test


def _row(race_id, horse_id, pre_max, bsp, finishing_position=None, result_note=None,
         trainer="T. Trainer", course="Test"):
    return {
        "race_id": race_id, "horse_id": horse_id, "race_date": "2026-03-01", "course": course,
        "trainer": trainer, "jockey": "J. Jockey", "pre_max": pre_max, "bsp": bsp,
        "finishing_position": finishing_position, "result_note": result_note,
    }


# ---------------------------------------------------------------------------
# compute_movement_features
# ---------------------------------------------------------------------------

def test_price_shortened_pct_computed_correctly():
    rows = [
        _row(1, 1, pre_max=10.0, bsp=8.0, finishing_position=1),   # shortened 20%
        _row(1, 2, pre_max=5.0, bsp=6.0, finishing_position=2),    # drifted -20%
    ]
    features = compute_movement_features(rows)
    winner = next(f for f in features if f["horse_id"] == 1)
    assert abs(winner["price_shortened_pct"] - 0.2) < 1e-9
    loser = next(f for f in features if f["horse_id"] == 2)
    assert abs(loser["price_shortened_pct"] - (-0.2)) < 1e-9


def test_excludes_race_with_fewer_than_two_usable_runners():
    rows = [
        _row(1, 1, pre_max=10.0, bsp=8.0, finishing_position=1),
        _row(1, 2, pre_max=None, bsp=6.0, finishing_position=2),  # no early (pre_max) price -> unusable
    ]
    assert compute_movement_features(rows) == []


def test_excludes_pending_and_nonrunner():
    rows = [
        _row(1, 1, pre_max=10.0, bsp=8.0, finishing_position=1),
        _row(1, 2, pre_max=5.0, bsp=5.0, finishing_position=None, result_note=None),  # pending
        _row(1, 3, pre_max=6.0, bsp=6.0, finishing_position=None, result_note="NR"),  # non-runner
    ]
    features = compute_movement_features(rows)
    assert {f["horse_id"] for f in features} == {1}


def test_never_uses_ip_fields_no_such_field_exists_on_input():
    # Defensive documentation test: the feature dict never carries ip_min/ip_max
    # at all -- there's no way for this function to accidentally use them.
    rows = [_row(1, 1, pre_max=10.0, bsp=8.0, finishing_position=1),
            _row(1, 2, pre_max=5.0, bsp=6.0, finishing_position=2)]
    features = compute_movement_features(rows)
    assert all("ip_min" not in f and "ip_max" not in f for f in features)


# ---------------------------------------------------------------------------
# test_price_movement_hypothesis — the leakage-safe benchmark
# ---------------------------------------------------------------------------

def _feature(race_id, horse_id, early_prob, shortened_pct, outcome, trainer="T. Trainer"):
    return {
        "race_id": race_id, "horse_id": horse_id, "trainer": trainer, "jockey": "J",
        "course": "Test", "early_implied_probability": early_prob,
        "price_shortened_pct": shortened_pct, "outcome": outcome,
    }


def test_hypothesis_benchmarks_against_the_early_not_late_probability():
    features = [
        _feature(1, 1, early_prob=0.20, shortened_pct=0.20, outcome=1),  # qualifies, wins -- beat its EARLY price
        _feature(2, 2, early_prob=0.20, shortened_pct=0.05, outcome=0),  # control
    ]
    result = run_price_movement_test(features, shorten_threshold=0.15)
    assert result["qualifying_group"]["n"] == 1
    assert result["qualifying_group"]["expected_wins_from_early_price"] == 0.20
    assert result["qualifying_group"]["diff_actual_minus_expected"] == round(1 - 0.20, 2)
    assert "pre_max-based" in result["benchmark"]
    assert result["control_group"]["n"] == 1


def test_hypothesis_groups_split_on_threshold_correctly():
    features = [
        _feature(1, 1, 0.3, shortened_pct=0.15, outcome=0),  # exactly at threshold -> qualifies
        _feature(1, 2, 0.3, shortened_pct=0.149, outcome=1),  # just under -> control
    ]
    result = run_price_movement_test(features, shorten_threshold=0.15)
    assert result["qualifying_group"]["n"] == 1
    assert result["control_group"]["n"] == 1


def test_hypothesis_none_group_when_empty():
    features = [_feature(1, 1, 0.3, shortened_pct=0.5, outcome=1)]
    result = run_price_movement_test(features, shorten_threshold=0.15)
    assert result["control_group"] is None


# ---------------------------------------------------------------------------
# trainer_shortening_summary
# ---------------------------------------------------------------------------

def test_trainer_summary_excludes_below_min_runs():
    features = [_feature(i, i, 0.2, shortened_pct=0.1, outcome=0, trainer="Small Trainer") for i in range(5)]
    summary = trainer_shortening_summary(features, min_runs=15)
    assert summary == {}


def test_trainer_summary_includes_trainers_meeting_min_runs():
    features = [_feature(i, i, 0.2, shortened_pct=0.1, outcome=1 if i == 0 else 0, trainer="Big Trainer") for i in range(20)]
    summary = trainer_shortening_summary(features, min_runs=15)
    assert summary["Big Trainer"]["n"] == 20
    assert summary["Big Trainer"]["actual_wins"] == 1
    assert abs(summary["Big Trainer"]["avg_price_shortened_pct"] - 0.1) < 1e-9


if __name__ == "__main__":
    tests = [
        test_price_shortened_pct_computed_correctly, test_excludes_race_with_fewer_than_two_usable_runners,
        test_excludes_pending_and_nonrunner, test_never_uses_ip_fields_no_such_field_exists_on_input,
        test_hypothesis_benchmarks_against_the_early_not_late_probability, test_hypothesis_groups_split_on_threshold_correctly,
        test_hypothesis_none_group_when_empty,
        test_trainer_summary_excludes_below_min_runs, test_trainer_summary_includes_trainers_meeting_min_runs,
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
