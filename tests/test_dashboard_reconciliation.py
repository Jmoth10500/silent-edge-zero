"""
Real tests for scripts/dashboard_reconciliation.py — the hard gate built
in direct response to Jonathan's audit of the research dashboard (five
real cross-panel discrepancies, 2026-09-19). Every check here must fail
loudly (raise ReconciliationError) when the underlying numbers genuinely
don't reconcile, and pass cleanly when they do -- there is no partial
"WARNING" state for this module, unlike data_integrity_audit.py, because
a dashboard that contradicts itself should never be published at all.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.dashboard_reconciliation import (
    ReconciliationError,
    count_void_agree_races_from_races,
    run_reconciliation,
)


def _runner(horse_id, finishing_position=None, result_note=None):
    return {"horse": {"horse_id": horse_id}, "result": {"finishing_position": finishing_position, "result_note": result_note}}


def _race(race_id, top_pick_id, runners):
    return {"race": {"race_id": race_id}, "runners": runners}


def _classified(race_id, category, top_pick_id, favourite_ids):
    return {"race_id": race_id, "category": category, "top_pick_horse_id": top_pick_id, "favourite_horse_ids": favourite_ids}


def _base_inputs(**overrides):
    """A fully self-consistent baseline every check should pass against;
    tests break exactly one piece of it to prove that check catches it."""
    base = dict(
        all_races=[
            _race(1, 1, [_runner(1, finishing_position=1), _runner(2, finishing_position=2)]),
        ],
        classified=[_classified(1, "A", 1, [1])],
        class_summary={"four_way": {"A": 1, "B": 0, "C": 0, "D": 0}},
        outcome_breakdown={"WON": 1, "PLACED": 0, "UNPLACED": 0, "VOID/NR": 0},
        roi={"n_settled": 1, "n_staked": 1, "stake": 1.0, "profit": 1.0, "roi": 1.0},
        agreement_splits={"silent_edge_vs_market": {"agree": {"n": 1, "win_rate": 1.0}, "disagree": {"n": 0, "win_rate": None}}},
        rank_matrix={"se_rank=1,market_rank=1": {"n": 1, "actual_wins": 1, "expected_wins_model": 0.5,
                                                  "diff_actual_minus_expected_model": 0.5, "small_sample": True}},
        brier_summary={"n": 1, "silent_edge_brier": 0.1, "market_brier": 0.1, "brier_gap": 0.0},
        d_split={"total": 0, "agree": 0, "disagree": 0},
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# count_void_agree_races_from_races
# ---------------------------------------------------------------------------

def test_counts_a_void_top_pick_that_agreed_with_the_favourite():
    all_races = [_race(1, 1, [_runner(1, finishing_position=None, result_note="NR"), _runner(2, finishing_position=1)])]
    classified = [_classified(1, "D", 1, [1])]  # top pick (1) == favourite (1), agreement, but voided
    result = count_void_agree_races_from_races(all_races, classified)
    assert result["n"] == 1
    assert result["race_ids"] == [1]


def test_does_not_count_a_real_finisher_even_if_it_lost():
    all_races = [_race(1, 1, [_runner(1, finishing_position=2), _runner(2, finishing_position=1)])]
    classified = [_classified(1, "D", 1, [1])]
    result = count_void_agree_races_from_races(all_races, classified)
    assert result["n"] == 0


def test_does_not_count_disagreement_races_regardless_of_void_status():
    all_races = [_race(1, 1, [_runner(1, finishing_position=None, result_note="NR"), _runner(2, finishing_position=1)])]
    classified = [_classified(1, "D", 1, [2])]  # top pick (1) != favourite (2) -- disagreement
    result = count_void_agree_races_from_races(all_races, classified)
    assert result["n"] == 0


# ---------------------------------------------------------------------------
# run_reconciliation — passes on consistent input, raises on each real
# discrepancy Jonathan's audit found
# ---------------------------------------------------------------------------

def test_passes_on_fully_consistent_input():
    result = run_reconciliation(**_base_inputs())
    assert result["status"] == "PASS"
    assert all(c["passed"] for c in result["checks"])


def test_raises_when_four_way_AB_disagrees_with_outcome_WON():
    inputs = _base_inputs(outcome_breakdown={"WON": 2, "PLACED": 0, "UNPLACED": 0, "VOID/NR": 0})
    try:
        run_reconciliation(**inputs)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "four_way_AB_equals_outcome_WON" in str(e)


def test_raises_when_n_staked_does_not_match_rounded_stake():
    inputs = _base_inputs(roi={"n_settled": 1, "n_staked": 5, "stake": 1.0, "profit": 1.0, "roi": 1.0})
    try:
        run_reconciliation(**inputs)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "roi_n_staked_equals_rounded_stake" in str(e)


def test_raises_when_agreement_and_heatmap_cell_dont_reconcile_via_void_top_picks():
    # agree=1, cell=1, void_agree computed as 0 from all_races/classified below
    # -> 1 != 1+0 is actually fine; break it by bumping the reported agree count.
    inputs = _base_inputs(
        agreement_splits={"silent_edge_vs_market": {"agree": {"n": 5, "win_rate": 1.0}, "disagree": {"n": 0, "win_rate": None}}},
    )
    try:
        run_reconciliation(**inputs)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "agreement_reconciles_with_heatmap_cell_via_void_top_picks" in str(e)


def test_passes_when_void_top_pick_explains_the_agreement_gap():
    # Race 1: real agreement, real win (as in base). Race 2: agreement,
    # but top pick voided -- contributes to "agree" (127-style count) but
    # NOT to the heat-map cell (needs a real outcome).
    all_races = _base_inputs()["all_races"] + [
        _race(2, 3, [_runner(3, finishing_position=None, result_note="NR"), _runner(4, finishing_position=1)]),
    ]
    classified = _base_inputs()["classified"] + [_classified(2, "D", 3, [3])]
    inputs = _base_inputs(
        all_races=all_races, classified=classified,
        agreement_splits={"silent_edge_vs_market": {"agree": {"n": 2, "win_rate": 0.5}, "disagree": {"n": 0, "win_rate": None}}},
        class_summary={"four_way": {"A": 1, "B": 0, "C": 0, "D": 1}},
        d_split={"total": 1, "agree": 1, "disagree": 0},
    )
    result = run_reconciliation(**inputs)
    assert result["status"] == "PASS"


def test_raises_when_heatmap_population_disagrees_with_brier_population():
    inputs = _base_inputs(brier_summary={"n": 999, "silent_edge_brier": 0.1, "market_brier": 0.1, "brier_gap": 0.0})
    try:
        run_reconciliation(**inputs)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "heatmap_population_equals_brier_population" in str(e)


def test_raises_when_d_split_does_not_sum_to_four_way_D():
    inputs = _base_inputs(
        class_summary={"four_way": {"A": 1, "B": 0, "C": 0, "D": 5}},
        d_split={"total": 3, "agree": 1, "disagree": 2},
    )
    try:
        run_reconciliation(**inputs)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "d_split_sums_to_four_way_D" in str(e)


def test_error_message_names_every_failing_check():
    inputs = _base_inputs(
        outcome_breakdown={"WON": 99, "PLACED": 0, "UNPLACED": 0, "VOID/NR": 0},
        brier_summary={"n": 999, "silent_edge_brier": 0.1, "market_brier": 0.1, "brier_gap": 0.0},
    )
    try:
        run_reconciliation(**inputs)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "four_way_AB_equals_outcome_WON" in str(e)
        assert "heatmap_population_equals_brier_population" in str(e)


if __name__ == "__main__":
    tests = [
        test_counts_a_void_top_pick_that_agreed_with_the_favourite,
        test_does_not_count_a_real_finisher_even_if_it_lost,
        test_does_not_count_disagreement_races_regardless_of_void_status,
        test_passes_on_fully_consistent_input,
        test_raises_when_four_way_AB_disagrees_with_outcome_WON,
        test_raises_when_n_staked_does_not_match_rounded_stake,
        test_raises_when_agreement_and_heatmap_cell_dont_reconcile_via_void_top_picks,
        test_passes_when_void_top_pick_explains_the_agreement_gap,
        test_raises_when_heatmap_population_disagrees_with_brier_population,
        test_raises_when_d_split_does_not_sum_to_four_way_D,
        test_error_message_names_every_failing_check,
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
