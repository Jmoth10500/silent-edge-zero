"""
Real tests for src/research/brier_live.py — the live paired Brier module
(brief Section 10, the brief's own "primary scientific objective"). Covers
the exclusion rules explicitly, since a silently-wrong inclusion/exclusion
here would corrupt the headline scientific comparison.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.brier_live import (
    _runner_outcome,
    compute_paired_observations,
    coverage_report,
    field_size_key,
    paired_brier_summary,
    probability_band_key,
    rolling_paired_brier,
)


def _runner(horse_id, se_prob, at_lock_back=None, finishing_position=None, result_note=None, model_rank=None):
    return {
        "horse": {"horse_id": horse_id},
        "silent_edge": {"model_probability": se_prob, "other_model_probability": None, "model_rank": model_rank},
        "market": {"at_lock": {"exchange_back": at_lock_back} if at_lock_back is not None else None},
        "result": {"finishing_position": finishing_position, "result_note": result_note},
    }


def _race(race_id, runners, date="2026-09-19", course="Test", race_type="Flat", field_size=None):
    return {
        "race": {"race_id": race_id, "date": date, "course": course, "race_type": race_type,
                 "field_size_declared": field_size or len(runners)},
        "runners": runners,
    }


# ---------------------------------------------------------------------------
# _runner_outcome — the exclusion rules
# ---------------------------------------------------------------------------

def test_outcome_win():
    assert _runner_outcome({"finishing_position": 1, "result_note": None}) == 1


def test_outcome_real_loss_by_position():
    assert _runner_outcome({"finishing_position": 4, "result_note": None}) == 0


def test_outcome_real_non_finish_is_a_loss():
    assert _runner_outcome({"finishing_position": None, "result_note": "PU"}) == 0


def test_outcome_non_runner_excluded_not_a_loss():
    assert _runner_outcome({"finishing_position": None, "result_note": "NR"}) is None
    assert _runner_outcome({"finishing_position": None, "result_note": "VOID"}) is None


def test_outcome_pending_excluded():
    assert _runner_outcome({"finishing_position": None, "result_note": None}) is None


# ---------------------------------------------------------------------------
# compute_paired_observations — race-level de-vig exclusion
# ---------------------------------------------------------------------------

def test_race_excluded_when_fewer_than_two_priced_runners():
    race = _race(1, [
        _runner(1, 0.4, at_lock_back=2.0, finishing_position=1),
        _runner(2, 0.6, at_lock_back=None, finishing_position=2),  # no real price
    ])
    assert compute_paired_observations([race]) == []


def test_race_included_with_two_priced_runners():
    race = _race(1, [
        _runner(1, 0.4, at_lock_back=2.0, finishing_position=1),
        _runner(2, 0.6, at_lock_back=3.0, finishing_position=2),
    ])
    obs = compute_paired_observations([race])
    assert len(obs) == 2
    winner = next(o for o in obs if o["horse_id"] == 1)
    assert winner["outcome"] == 1
    assert abs(winner["market_probability"] - (0.5 / (0.5 + 1 / 3))) < 1e-9


def test_pending_and_nonrunner_excluded_from_observations():
    race = _race(1, [
        _runner(1, 0.4, at_lock_back=2.0, finishing_position=1),
        _runner(2, 0.3, at_lock_back=3.0, finishing_position=None, result_note=None),  # pending
        _runner(3, 0.3, at_lock_back=4.0, finishing_position=None, result_note="NR"),  # non-runner
    ])
    obs = compute_paired_observations([race])
    assert {o["horse_id"] for o in obs} == {1}


def test_never_uses_a_snapshot_type_other_than_the_requested_one():
    race = _race(1, [
        _runner(1, 0.4, at_lock_back=2.0, finishing_position=1),
        _runner(2, 0.6, at_lock_back=3.0, finishing_position=2),
    ])
    # only 'at_lock' populated -> requesting 'closing' finds no priced runners at all
    assert compute_paired_observations([race], price_source="closing") == []


# ---------------------------------------------------------------------------
# paired_brier_summary
# ---------------------------------------------------------------------------

def test_summary_none_for_no_observations():
    assert paired_brier_summary([]) is None


def test_summary_computes_real_gap_and_leader():
    # Silent Edge scores worse (further from outcome) than the market here.
    observations = [
        {"se_probability": 0.9, "market_probability": 0.5, "outcome": 0},
        {"se_probability": 0.9, "market_probability": 0.5, "outcome": 1},
    ]
    summary = paired_brier_summary(observations)
    assert summary["n"] == 2
    se_expected = ((0.9 - 0) ** 2 + (0.9 - 1) ** 2) / 2
    market_expected = ((0.5 - 0) ** 2 + (0.5 - 1) ** 2) / 2
    assert abs(summary["silent_edge_brier"] - se_expected) < 1e-6
    assert abs(summary["market_brier"] - market_expected) < 1e-6
    assert summary["leader"] == "market"  # market's score is lower (better)
    assert summary["brier_gap"] > 0  # positive = market leading, per module docstring


# ---------------------------------------------------------------------------
# coverage_report
# ---------------------------------------------------------------------------

def test_coverage_report_counts_every_exclusion_reason():
    races = [
        _race(1, [
            _runner(1, 0.4, at_lock_back=2.0, finishing_position=1),
            _runner(2, 0.6, at_lock_back=3.0, finishing_position=2),
        ]),
        _race(2, [  # whole race excluded — only 1 priced runner
            _runner(3, 0.5, at_lock_back=2.0, finishing_position=1),
            _runner(4, 0.5, at_lock_back=None, finishing_position=2),
        ]),
    ]
    report = coverage_report(races)
    assert report["n_races"] == 2
    assert report["n_runners_total"] == 4
    assert report["n_races_excluded_insufficient_market_data"] == 1
    assert report["n_included_observations"] == 2


# ---------------------------------------------------------------------------
# rolling_paired_brier — race-count windows, never computed on a partial window
# ---------------------------------------------------------------------------

def test_rolling_brier_none_when_not_enough_races():
    observations = [
        {"race_id": 1, "se_probability": 0.5, "market_probability": 0.5, "outcome": 1},
        {"race_id": 2, "se_probability": 0.5, "market_probability": 0.5, "outcome": 0},
    ]
    result = rolling_paired_brier(observations, window_sizes=(1, 2, 5))
    assert result[5] is None
    assert result[1] is not None
    assert result[2] is not None


def test_rolling_brier_windows_use_only_the_most_recent_n_races():
    observations = [
        {"race_id": 1, "se_probability": 0.1, "market_probability": 0.1, "outcome": 1},   # bad SE score
        {"race_id": 2, "se_probability": 0.9, "market_probability": 0.9, "outcome": 1},   # good SE score
    ]
    result = rolling_paired_brier(observations, window_sizes=(1,))
    # window of 1 race -> only race_id 2's observation
    assert result[1]["n"] == 1
    assert abs(result[1]["silent_edge_brier"] - (0.9 - 1) ** 2) < 1e-9


# ---------------------------------------------------------------------------
# grouping key helpers
# ---------------------------------------------------------------------------

def test_probability_band_key_buckets_correctly():
    key_fn = probability_band_key(0.10)
    assert key_fn({"se_probability": 0.05}) == "0%-10%"
    assert key_fn({"se_probability": 0.24}) == "20%-30%"
    assert key_fn({"se_probability": 0.999}) == "90%-100%"  # clamped, never out of range


def test_field_size_key_buckets():
    assert field_size_key({"field_size_declared": 5}) == "small (<=7)"
    assert field_size_key({"field_size_declared": 10}) == "medium (8-12)"
    assert field_size_key({"field_size_declared": 16}) == "large (13+)"
    assert field_size_key({"field_size_declared": None}) == "unknown"


if __name__ == "__main__":
    tests = [
        test_outcome_win, test_outcome_real_loss_by_position, test_outcome_real_non_finish_is_a_loss,
        test_outcome_non_runner_excluded_not_a_loss, test_outcome_pending_excluded,
        test_race_excluded_when_fewer_than_two_priced_runners, test_race_included_with_two_priced_runners,
        test_pending_and_nonrunner_excluded_from_observations, test_never_uses_a_snapshot_type_other_than_the_requested_one,
        test_summary_none_for_no_observations, test_summary_computes_real_gap_and_leader,
        test_coverage_report_counts_every_exclusion_reason,
        test_rolling_brier_none_when_not_enough_races, test_rolling_brier_windows_use_only_the_most_recent_n_races,
        test_probability_band_key_buckets_correctly, test_field_size_key_buckets,
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
