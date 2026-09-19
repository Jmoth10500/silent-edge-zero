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
    count_joint_favourite_agree_but_market_only_correct,
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
        eligible_race_ids={1},
        settled_race_ids={1},
        missed_bands={},
        all_runners_bands={},
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


# ---------------------------------------------------------------------------
# count_joint_favourite_agree_but_market_only_correct — Jonathan's
# 2026-09-20 finding: race 57991 (Kelso), a real joint favourite
# ---------------------------------------------------------------------------

def test_joint_favourite_c_case_detected():
    # top pick (1) IS one of two tied favourites [1, 2], but the OTHER
    # tied favourite (2) actually won -- market correct, SE wrong -> C.
    classified = [_classified(1, "C", 1, [1, 2])]
    result = count_joint_favourite_agree_but_market_only_correct(classified)
    assert result["n"] == 1
    assert result["race_ids"] == [1]


def test_joint_favourite_c_case_not_triggered_by_ordinary_disagreement():
    # top pick (1) is NOT among the favourites [2] at all -- ordinary C, not the joint-favourite case.
    classified = [_classified(1, "C", 1, [2])]
    result = count_joint_favourite_agree_but_market_only_correct(classified)
    assert result["n"] == 0


def test_joint_favourite_c_case_ignores_non_C_categories():
    classified = [_classified(1, "A", 1, [1]), _classified(2, "D", 1, [1])]
    result = count_joint_favourite_agree_but_market_only_correct(classified)
    assert result["n"] == 0


# ---------------------------------------------------------------------------
# Check 6 — agreement decomposes exactly into A + D-agree + joint-fav-C
# ---------------------------------------------------------------------------

def test_check6_passes_when_joint_favourite_c_accounts_for_the_remainder():
    # agree=2: race 1 (A, real agreement+win) and race 2 (C, joint-favourite case).
    inputs = _base_inputs(
        classified=[_classified(1, "A", 1, [1]), _classified(2, "C", 3, [3, 4])],
        agreement_splits={"silent_edge_vs_market": {"agree": {"n": 2, "win_rate": 0.5}, "disagree": {"n": 0, "win_rate": None}}},
        rank_matrix={"se_rank=1,market_rank=1": {"n": 2, "actual_wins": 1, "expected_wins_model": 1.0,
                                                  "diff_actual_minus_expected_model": 0.0, "small_sample": True}},
        brier_summary={"n": 2, "silent_edge_brier": 0.1, "market_brier": 0.1, "brier_gap": 0.0},
    )
    result = run_reconciliation(**inputs)
    assert result["status"] == "PASS"


def test_check6_raises_when_agreement_count_has_no_explanation():
    inputs = _base_inputs(
        agreement_splits={"silent_edge_vs_market": {"agree": {"n": 5, "win_rate": 0.5}, "disagree": {"n": 0, "win_rate": None}}},
        rank_matrix={"se_rank=1,market_rank=1": {"n": 5, "actual_wins": 1, "expected_wins_model": 1.0,
                                                  "diff_actual_minus_expected_model": 0.0, "small_sample": True}},
        brier_summary={"n": 5, "silent_edge_brier": 0.1, "market_brier": 0.1, "brier_gap": 0.0},
    )
    try:
        run_reconciliation(**inputs)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "agreement_decomposes_exactly_into_A_plus_D_agree_plus_joint_favourite_C" in str(e)


# ---------------------------------------------------------------------------
# Check 7 — eligible vs settled, exact set-based reconciliation
# ---------------------------------------------------------------------------

def test_check7_raises_when_roi_settled_disagrees_with_independent_set():
    inputs = _base_inputs(roi={"n_settled": 999, "n_staked": 1, "stake": 1.0, "profit": 1.0, "roi": 1.0})
    try:
        run_reconciliation(**inputs)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "roi_n_settled_equals_independently_computed_settled_set" in str(e)


def test_check7_raises_when_outcome_total_disagrees_with_intersection():
    inputs = _base_inputs(eligible_race_ids={1, 2}, settled_race_ids={1})  # race 2 eligible but not settled
    # outcome_breakdown total is still 1 (from base), but |eligible ∩ settled| is also 1 -> should PASS actually
    result = run_reconciliation(**inputs)
    assert result["status"] == "PASS"
    # Now genuinely break it: outcome total says 2 races counted, but only 1 is in the intersection.
    inputs2 = _base_inputs(outcome_breakdown={"WON": 2, "PLACED": 0, "UNPLACED": 0, "VOID/NR": 0})
    try:
        run_reconciliation(**inputs2)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "outcome_breakdown_total_equals_eligible_and_settled_intersection" in str(e)


# ---------------------------------------------------------------------------
# Check 8 — missed-winner priced subset must never exceed ALL-RUNNERS actual wins
# ---------------------------------------------------------------------------

def test_check8_passes_when_priced_subset_fits_within_all_runners():
    inputs = _base_inputs(
        missed_bands={"0%-10%": {"n_winners": 5, "n_winners_priced": 3, "n_winners_unpriced": 2}},
        all_runners_bands={"0%-10%": {"actual_wins": 4}},
    )
    result = run_reconciliation(**inputs)
    assert result["status"] == "PASS"


def test_check8_raises_when_priced_subset_exceeds_all_runners_actual_wins():
    # Real 2026-09-20 bug shape: missed-winner priced count (72) must never
    # exceed the ALL-RUNNERS population's own actual wins for the same band.
    inputs = _base_inputs(
        missed_bands={"0%-10%": {"n_winners": 95, "n_winners_priced": 90, "n_winners_unpriced": 5}},
        all_runners_bands={"0%-10%": {"actual_wins": 86}},
    )
    try:
        run_reconciliation(**inputs)
        assert False, "expected ReconciliationError"
    except ReconciliationError as e:
        assert "missed_winner_priced_subset_le_all_runners_actual_wins[0%-10%]" in str(e)


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
        test_joint_favourite_c_case_detected,
        test_joint_favourite_c_case_not_triggered_by_ordinary_disagreement,
        test_joint_favourite_c_case_ignores_non_C_categories,
        test_check6_passes_when_joint_favourite_c_accounts_for_the_remainder,
        test_check6_raises_when_agreement_count_has_no_explanation,
        test_check7_raises_when_roi_settled_disagrees_with_independent_set,
        test_check7_raises_when_outcome_total_disagrees_with_intersection,
        test_check8_passes_when_priced_subset_fits_within_all_runners,
        test_check8_raises_when_priced_subset_exceeds_all_runners_actual_wins,
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
