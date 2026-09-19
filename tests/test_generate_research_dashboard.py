"""
Real tests for scripts/generate_research_dashboard.py's pure rendering
functions (render_kpi_cards, render_html) — no DB. The DB-querying
functions (load_all_races, daily_series, compute_roi) are DB-integration
verified live, same convention as every other DB-query function in this
project.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_research_dashboard import (
    agreement_win_rate_splits,
    odds_band_analysis,
    render_heatmap_table,
    render_html,
    render_kpi_cards,
    top_pick_outcome_breakdown,
)


def _class_summary(n_eligible=10, n_unresolved=1):
    return {
        "n_races_total": n_eligible + n_unresolved, "n_eligible": n_eligible, "n_unresolved": n_unresolved,
        "unresolved_reasons": {}, "four_way": {"A": 3, "B": 2, "C": 2, "D": 3},
        "silent_edge_win_rate": 0.5, "market_favourite_win_rate": 0.5, "win_rate_difference": 0.0,
        "model_market_agreement_rate": 0.4, "n_agree": 4,
    }


def test_render_kpi_cards_includes_real_values():
    html = render_kpi_cards(_class_summary(), {"silent_edge_brier": 0.1, "market_brier": 0.09, "brier_gap": 0.01, "n": 10},
                             {"n": 5, "stake": 5.0, "profit": 1.0, "roi": 0.2}, "PASS")
    assert "TOTAL SETTLED RACES" in html
    assert "10" in html
    assert "PASS" in html
    assert "+20.0%" in html  # ROI


def test_render_kpi_cards_handles_no_eligible_races_without_crashing():
    summary = _class_summary(n_eligible=0, n_unresolved=5)
    summary["silent_edge_win_rate"] = None
    summary["market_favourite_win_rate"] = None
    summary["win_rate_difference"] = None
    summary["model_market_agreement_rate"] = None
    html = render_kpi_cards(summary, None, {"n": 0, "stake": 0.0, "profit": 0.0, "roi": None}, "WARNING")
    assert "n/a" in html
    assert "WARNING" in html


def test_render_html_produces_a_complete_page_with_chart_canvases():
    html = render_html(
        date(2026, 9, 10), date(2026, 9, 19), _class_summary(), {"silent_edge_brier": 0.1, "market_brier": 0.09, "brier_gap": 0.01, "n": 10},
        {"n": 5, "stake": 5.0, "profit": 1.0, "roi": 0.2}, "PASS",
        [{"date": "2026-09-10", "silent_edge_brier": 0.1, "market_brier": 0.09, "brier_gap": 0.01,
          "n_brier_observations": 10, "silent_edge_win_rate": 0.5, "market_favourite_win_rate": 0.5, "n_eligible_races": 10}],
        {"0%-10%": {"avg_predicted_probability": 0.05, "actual_win_rate": 0.04}},
        {"WON": 3, "PLACED": 2, "UNPLACED": 4, "VOID/NR": 1},
        [{"bin_index": 0, "bin_range": (0.0, 0.1), "mean_predicted": 0.05, "mean_actual": 0.04, "count": 10}],
        [{"bin_index": 0, "bin_range": (0.0, 0.1), "mean_predicted": 0.06, "mean_actual": 0.05, "count": 10}],
        {"se_rank=1,market_rank=1": {"se_rank": "1", "market_rank": "1", "n": 30, "actual_wins": 10,
                                      "actual_win_rate": 0.33, "expected_wins_model": 9.0,
                                      "diff_actual_minus_expected_model": 1.0, "small_sample": False}},
        {"silent_edge_vs_market": {"agree": {"n": 10, "win_rate": 0.4}, "disagree": {"n": 20, "win_rate": 0.2}},
         "model1_vs_model2": {"agree": {"n": 15, "win_rate": 0.3}, "disagree": {"n": 15, "win_rate": 0.15}}},
        {"dates": ["2026-09-10"], "cumulative_profit": [1.5], "max_drawdown": -0.5, "total_stake": 10.0},
        {"2-4": {"n": 30, "wins": 8, "win_rate": 0.27, "brier_contribution": 0.15, "small_sample": False}},
    )
    assert "<!DOCTYPE html>" in html
    assert 'id="donutChart"' in html
    assert 'id="brierChart"' in html
    assert 'id="winRateChart"' in html
    assert 'id="bandChart"' in html
    assert 'id="outcomeDonutChart"' in html
    assert 'id="calibrationChart"' in html
    assert 'id="agreementChart"' in html
    assert 'id="pnlChart"' in html
    assert 'id="oddsBandChart"' in html
    assert "heatmap" in html
    assert "chart.js" in html.lower()
    assert "2026-09-10" in html


# ---------------------------------------------------------------------------
# top_pick_outcome_breakdown
# ---------------------------------------------------------------------------

def _race_with_top_pick(race_id, top_pick_id, runners, field_size=None):
    return {
        "race": {"race_id": race_id, "field_size_declared": field_size or len(runners)},
        "top_pick_horse_id": top_pick_id, "runners": runners,
    }


def _runner(horse_id, finishing_position=None, result_note=None):
    return {"horse": {"horse_id": horse_id}, "result": {"finishing_position": finishing_position, "result_note": result_note}}


def test_outcome_breakdown_classifies_won_placed_unplaced_void():
    races = [
        _race_with_top_pick(1, 1, [_runner(1, finishing_position=1), _runner(2, finishing_position=2)]),
        _race_with_top_pick(2, 3, [_runner(3, finishing_position=2), _runner(4, finishing_position=1)], field_size=9),  # 1/5, 3 places -> placed
        _race_with_top_pick(3, 5, [_runner(5, finishing_position=8), _runner(6, finishing_position=1)], field_size=9),  # unplaced
        _race_with_top_pick(4, 7, [_runner(7, finishing_position=None, result_note="NR")]),
        _race_with_top_pick(5, 9, [_runner(9, finishing_position=None, result_note=None)]),  # pending -> excluded
    ]
    breakdown = top_pick_outcome_breakdown(races)
    assert breakdown["WON"] == 1
    assert breakdown["PLACED"] == 1
    assert breakdown["UNPLACED"] == 1
    assert breakdown["VOID/NR"] == 1
    assert sum(breakdown.values()) == 4  # the pending race contributes nothing


# ---------------------------------------------------------------------------
# render_heatmap_table
# ---------------------------------------------------------------------------

def test_heatmap_renders_a_dash_for_missing_cells_and_values_for_present_ones():
    matrix = {"se_rank=1,market_rank=1": {"se_rank": "1", "market_rank": "1", "n": 30, "actual_wins": 10,
                                           "actual_win_rate": 0.33, "expected_wins_model": 9.0,
                                           "diff_actual_minus_expected_model": 1.0, "small_sample": False}}
    html = render_heatmap_table(matrix)
    assert "<table" in html
    assert "33%" in html
    assert html.count("–") >= 1  # most cells are genuinely empty for this tiny matrix


# ---------------------------------------------------------------------------
# agreement_win_rate_splits — the two agreement notions must stay separate
# ---------------------------------------------------------------------------

def _race_full(race_id, top_pick_id, favourite_ids, winner_id, category, runners):
    return {
        "classified": {"race_id": race_id, "category": category, "top_pick_horse_id": top_pick_id, "favourite_horse_ids": favourite_ids},
        "race": {"race": {"race_id": race_id}, "top_pick_horse_id": top_pick_id, "runners": runners},
    }


def _m_runner(horse_id, other_model_prob, finishing_position=None, result_note=None):
    return {
        "horse": {"horse_id": horse_id},
        "silent_edge": {"other_model_probability": other_model_prob},
        "result": {"finishing_position": finishing_position, "result_note": result_note},
    }


def test_agreement_splits_are_computed_independently():
    # Race 1: SE top pick (1) == market favourite (1), SE wins -> category A -> SE/market AGREE, win.
    # Model 1's own top pick (by other_model_probability) is horse 2, DISAGREEING with Model 2's pick (1).
    race1 = _race_full(1, 1, [1], 1, "A", [
        _m_runner(1, other_model_prob=0.3, finishing_position=1),
        _m_runner(2, other_model_prob=0.5, finishing_position=2),
    ])
    # Race 2: SE top pick (3) != market favourite (4) -> category B (SE wins, market doesn't) -> SE/market DISAGREE, win.
    # Model 1 also picks horse 3 here -> Model1/Model2 AGREE.
    race2 = _race_full(2, 3, [4], 3, "B", [
        _m_runner(3, other_model_prob=0.6, finishing_position=1),
        _m_runner(4, other_model_prob=0.2, finishing_position=2),
    ])
    races = [race1["race"], race2["race"]]
    classified = [race1["classified"], race2["classified"]]

    result = agreement_win_rate_splits(races, classified)

    sem = result["silent_edge_vs_market"]
    assert sem["agree"]["n"] == 1 and sem["agree"]["win_rate"] == 1.0     # race 1
    assert sem["disagree"]["n"] == 1 and sem["disagree"]["win_rate"] == 1.0  # race 2 (SE won despite disagreeing)

    m1m2 = result["model1_vs_model2"]
    assert m1m2["disagree"]["n"] == 1 and m1m2["disagree"]["win_rate"] == 1.0  # race 1: Model2 won even though Model1 disagreed
    assert m1m2["agree"]["n"] == 1 and m1m2["agree"]["win_rate"] == 1.0        # race 2: both models agreed


def test_agreement_splits_none_win_rate_when_no_observations():
    result = agreement_win_rate_splits([], [])
    assert result["silent_edge_vs_market"]["agree"]["win_rate"] is None
    assert result["model1_vs_model2"]["disagree"]["n"] == 0


# ---------------------------------------------------------------------------
# odds_band_analysis — buckets by Silent Edge's own FAIR ODDS, a different
# axis from the probability-band chart
# ---------------------------------------------------------------------------

def _obs(se_prob, outcome):
    return {"se_probability": se_prob, "outcome": outcome}


def test_odds_band_buckets_by_fair_odds_not_raw_probability():
    # fair odds = 1/prob: 0.5 -> 2.0 (band "2-4"), 0.2 -> 5.0 (band "4-8")
    observations = [_obs(0.5, 1), _obs(0.5, 0), _obs(0.2, 0)]
    result = odds_band_analysis(observations)
    assert result["2-4"]["n"] == 2
    assert result["2-4"]["wins"] == 1
    assert result["4-8"]["n"] == 1


def test_odds_band_skips_zero_probability_without_crashing():
    observations = [_obs(0.0, 0), _obs(0.5, 1)]
    result = odds_band_analysis(observations)
    assert sum(b["n"] for b in result.values()) == 1


def test_odds_band_flags_small_samples():
    observations = [_obs(0.5, 0) for _ in range(5)]
    result = odds_band_analysis(observations)
    assert result["2-4"]["small_sample"] is True


if __name__ == "__main__":
    tests = [
        test_render_kpi_cards_includes_real_values, test_render_kpi_cards_handles_no_eligible_races_without_crashing,
        test_render_html_produces_a_complete_page_with_chart_canvases,
        test_outcome_breakdown_classifies_won_placed_unplaced_void,
        test_heatmap_renders_a_dash_for_missing_cells_and_values_for_present_ones,
        test_agreement_splits_are_computed_independently, test_agreement_splits_none_win_rate_when_no_observations,
        test_odds_band_buckets_by_fair_odds_not_raw_probability, test_odds_band_skips_zero_probability_without_crashing,
        test_odds_band_flags_small_samples,
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
