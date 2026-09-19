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

from scripts.generate_research_dashboard import render_heatmap_table, render_html, render_kpi_cards, top_pick_outcome_breakdown


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
    )
    assert "<!DOCTYPE html>" in html
    assert 'id="donutChart"' in html
    assert 'id="brierChart"' in html
    assert 'id="winRateChart"' in html
    assert 'id="bandChart"' in html
    assert 'id="outcomeDonutChart"' in html
    assert 'id="calibrationChart"' in html
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


if __name__ == "__main__":
    tests = [
        test_render_kpi_cards_includes_real_values, test_render_kpi_cards_handles_no_eligible_races_without_crashing,
        test_render_html_produces_a_complete_page_with_chart_canvases,
        test_outcome_breakdown_classifies_won_placed_unplaced_void,
        test_heatmap_renders_a_dash_for_missing_cells_and_values_for_present_ones,
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
