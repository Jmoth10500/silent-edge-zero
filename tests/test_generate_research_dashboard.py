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

from scripts.generate_research_dashboard import render_html, render_kpi_cards


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
    )
    assert "<!DOCTYPE html>" in html
    assert 'id="donutChart"' in html
    assert 'id="brierChart"' in html
    assert 'id="winRateChart"' in html
    assert 'id="bandChart"' in html
    assert "chart.js" in html.lower()
    assert "2026-09-10" in html


if __name__ == "__main__":
    tests = [
        test_render_kpi_cards_includes_real_values, test_render_kpi_cards_handles_no_eligible_races_without_crashing,
        test_render_html_produces_a_complete_page_with_chart_canvases,
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
