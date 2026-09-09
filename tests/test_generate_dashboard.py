"""
Real tests for scripts/generate_dashboard.py's pure rendering helpers.
The DB-reading half (load_predictions) is exercised by actually running
the script against the real DB, same discipline as predict_todays_races.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_dashboard import _bar_html, _pct, _stat_row, render_html, render_summary


def test_pct_formats_probability_as_percentage():
    assert _pct(0.1971) == "19.7%"
    assert _pct(0.0) == "0.0%"
    assert _pct(1.0) == "100.0%"


def test_bar_html_width_scales_with_probability_and_has_a_floor():
    # a real 0.0 probability still renders a visible sliver (floor=2%),
    # not an invisible 0-width bar
    assert "width:2%" in _bar_html(0.0, "red")
    assert "width:50%" in _bar_html(0.5, "red")
    assert "width:100%" in _bar_html(1.0, "red")
    assert "background:red" in _bar_html(0.5, "red")


def test_render_html_with_no_races_shows_empty_state():
    from datetime import date
    html = render_html(date(2026, 9, 9), [])
    assert "No predictions locked" in html
    assert "<!doctype html>" in html.lower()


def test_stat_row_renders_known_real_fields():
    stats = {"age": 4, "draw": 7, "weight_lbs": 126, "official_rating": 82,
              "recent_form": "1582F3", "trainer": "J Butler", "jockey": "C J Whiteley"}
    html = _stat_row(stats)
    assert "Age 4" in html
    assert "Draw 7" in html
    assert "126 lbs" in html
    assert "OR 82" in html
    assert "1582F3" in html
    assert "J Butler" in html
    assert "C J Whiteley" in html


def test_stat_row_empty_state_when_nothing_known():
    html = _stat_row({})
    assert "No racecard stats" in html


def test_render_summary_computes_real_agreement_and_top_pick():
    from datetime import time
    races = [
        {
            "off_time": time(13, 21), "course_name": "Redcar", "race_name": "Race A",
            "model1": {"Horse A": 0.3, "Horse B": 0.7}, "model2": {"Horse A": 0.6, "Horse B": 0.4},
        },
        {
            "off_time": time(14, 0), "course_name": "Sedgefield", "race_name": "Race B",
            "model1": {"Horse C": 0.3, "Horse D": 0.7}, "model2": {"Horse C": 0.3, "Horse D": 0.7},
        },
    ]
    html = render_summary(races)
    assert "2" in html  # 2 races
    assert "50%" in html  # 1 of 2 agree (race B agrees, race A disagrees)
    assert "Horse D" in html  # highest-confidence pick (0.7) across both races


def test_render_summary_empty_races_returns_empty_string():
    assert render_summary([]) == ""


def test_render_html_includes_backtest_context():
    from datetime import date
    html = render_html(date(2026, 9, 9), [])
    assert "0.0795" in html  # Model 0's real committed Brier score
    assert "0.0875" in html  # Model 1's
    assert "0.0874" in html  # Model 2's


if __name__ == "__main__":
    tests = [
        test_pct_formats_probability_as_percentage,
        test_bar_html_width_scales_with_probability_and_has_a_floor,
        test_render_html_with_no_races_shows_empty_state,
        test_stat_row_renders_known_real_fields,
        test_stat_row_empty_state_when_nothing_known,
        test_render_summary_computes_real_agreement_and_top_pick,
        test_render_summary_empty_races_returns_empty_string,
        test_render_html_includes_backtest_context,
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
