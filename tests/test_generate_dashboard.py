"""
Real tests for scripts/generate_dashboard.py's pure rendering helpers.
The DB-reading half (load_predictions) is exercised by actually running
the script against the real DB, same discipline as predict_todays_races.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, time

from scripts.generate_dashboard import (
    _bar_html,
    _bet_calculator_html,
    _ew_defaults,
    _going_hint,
    _pct,
    _stat_row,
    build_race_analysis,
    fetch_course_weather,
    find_market_favourite,
    real_calibration_confidence,
    render_html,
    render_overview_chart,
    render_summary,
    render_day_history_dialog,
    render_days_tracked_dialog,
    render_live_calibration,
    render_track_record,
    render_weather,
)


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


def test_stat_row_no_racecard_stats_still_shows_odds_pending_chip():
    # the odds chip always renders (real data or an honest "pending"
    # placeholder), so a runner with zero OTHER stats still gets one chip,
    # not the "no stats at all" empty state.
    html = _stat_row({})
    assert "Odds: not yet available" in html
    assert "No racecard stats" not in html


def test_stat_row_real_odds_render_when_present():
    html = _stat_row({"midprice": 4.2, "exchange_back": 4.0, "exchange_lay": 4.4})
    assert "Odds 4.2" in html
    assert "back 4.0" in html
    assert "lay 4.4" in html
    assert "not yet available" not in html


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


def test_going_hint_real_thresholds():
    assert "soft" in _going_hint({"precip_mm": 12}).lower()
    assert "fast" in _going_hint({"precip_mm": 0.0}).lower()
    assert "easing" in _going_hint({"precip_mm": 5}).lower()
    assert "little change" in _going_hint({"precip_mm": 1}).lower()


def test_fetch_course_weather_real_gb_course_parses_real_response_shape():
    from datetime import date

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"daily": {
                "time": ["2026-09-10"],
                "precipitation_sum": [4.2],
                "precipitation_probability_max": [60],
                "temperature_2m_max": [18.0],
                "temperature_2m_min": [11.0],
                "wind_speed_10m_max": [22.0],
            }}

    def fake_get(url, params=None, timeout=None):
        return FakeResp()

    result = fetch_course_weather({"Epsom Downs"}, date(2026, 9, 10), http_get=fake_get)
    assert result["Epsom Downs"]["precip_mm"] == 4.2
    assert result["Epsom Downs"]["temp_max"] == 18.0


def test_fetch_course_weather_skips_unknown_course():
    from datetime import date
    result = fetch_course_weather({"Not A Real Course"}, date(2026, 9, 10), http_get=lambda *a, **k: None)
    assert result == {}


def test_fetch_course_weather_best_effort_on_http_failure():
    from datetime import date

    def failing_get(url, params=None, timeout=None):
        raise ConnectionError("simulated failure")

    result = fetch_course_weather({"Epsom Downs"}, date(2026, 9, 10), http_get=failing_get)
    assert result == {}  # never raises, never crashes the dashboard


def test_render_weather_empty_returns_empty_string():
    assert render_weather({}) == ""


def test_render_weather_renders_real_figures():
    html = render_weather({"Epsom Downs": {
        "precip_mm": 4.2, "precip_prob": 60, "temp_max": 18.0, "temp_min": 11.0, "wind_kmh": 22.0,
    }})
    assert "Epsom Downs" in html
    assert "4.2mm" in html


def test_render_overview_chart_empty_races_returns_empty_string():
    assert render_overview_chart([]) == ""


def test_render_overview_chart_shows_top_pick_per_race():
    from datetime import time
    races = [{
        "off_time": time(13, 21), "course_name": "Redcar",
        "model1": {}, "model2": {"Deputy Vice": 0.197, "Blue Pete": 0.178},
    }]
    html = render_overview_chart(races)
    assert "Deputy Vice" in html
    assert "19.7%" in html


def test_render_overview_chart_click_opens_matching_race_dialog():
    from datetime import time
    races = [{
        "race_id": 57401, "off_time": time(13, 21), "course_name": "Redcar",
        "model1": {}, "model2": {"Deputy Vice": 0.197},
    }]
    html = render_overview_chart(races)
    assert "getElementById('race-57401')" in html
    assert "showModal()" in html


def test_find_market_favourite_none_when_no_real_odds():
    stats = {"Horse A": {"exchange_back": None}, "Horse B": {"exchange_back": None}}
    assert find_market_favourite(stats) is None


def test_find_market_favourite_shortest_odds_wins():
    stats = {
        "Horse A": {"exchange_back": 4.5},
        "Horse B": {"exchange_back": 2.1},   # shortest = favourite
        "Horse C": {"exchange_back": None},  # no real odds yet, excluded
    }
    fav = find_market_favourite(stats)
    assert fav == ("Horse B", 2.1)


def test_real_calibration_confidence_grounds_in_real_bin():
    text = real_calibration_confidence(0.15)
    assert "14.1%" in text  # the real bin's "actual" value formatted as a %


def test_real_calibration_confidence_flags_small_real_sample():
    text = real_calibration_confidence(0.85)  # the n=5 bin, well under 150
    assert "small real sample" in text.lower()


def test_build_race_analysis_empty_when_no_model2_predictions():
    assert build_race_analysis({"model2": {}, "stats": {}}) == ""


def test_build_race_analysis_real_features_and_market_comparison():
    race = {
        "model2": {"Deputy Vice": 0.5, "Blue Pete": 0.5},
        "stats": {
            "Deputy Vice": {"horse_id": 1, "draw": 1, "weight_lbs": 130, "official_rating": 100,
                            "recent_form": "111", "exchange_back": 2.0},
            "Blue Pete": {"horse_id": 2, "draw": 8, "weight_lbs": 120, "official_rating": 70,
                          "recent_form": "666", "exchange_back": 5.0},
        },
    }
    html = build_race_analysis(race)
    assert "Deputy Vice" in html
    assert "above the field average" in html  # real rating edge, +15 vs mean of 85
    assert "market also makes Deputy Vice favourite" in html  # real odds agree
    assert "real odds 2.0" in html


def test_build_race_analysis_debutant_top_pick_reads_grammatically():
    # real bug found and fixed 2026-09-09: "X is has no official rating"
    race = {
        "model2": {"No Rating Horse": 0.5, "Other Horse": 0.5},
        "stats": {
            "No Rating Horse": {"horse_id": 1, "draw": 1, "weight_lbs": 130, "official_rating": None,
                                 "recent_form": None, "exchange_back": None},
            "Other Horse": {"horse_id": 2, "draw": 8, "weight_lbs": 120, "official_rating": 90,
                             "recent_form": "111", "exchange_back": None},
        },
    }
    html = build_race_analysis(race)
    assert "is has" not in html
    assert "No Rating Horse is a likely debutant" in html


def test_ew_defaults_real_field_size_bands():
    assert _ew_defaults(3) == ("1/4", 1)
    assert _ew_defaults(6) == ("1/4", 2)
    assert _ew_defaults(9) == ("1/5", 3)
    assert _ew_defaults(14) == ("1/4", 4)


def test_bet_calculator_html_empty_without_real_odds():
    assert _bet_calculator_html("bc-1-1", None, 8) == ""


def test_bet_calculator_html_renders_with_real_odds():
    html = _bet_calculator_html("bc-1-1", 5.5, 9)
    assert 'data-odds="5.5"' in html
    assert 'data-domid="bc-1-1"' in html
    assert "bc-1-1-stake" in html
    assert "1/5 odds" in html  # real default for a 9-runner field
    assert 'selected>1/5 odds' in html  # actually selected, not just present


def test_render_html_emits_no_tracking_script_when_site_code_blank():
    import scripts.generate_dashboard as dashboard_module
    original = dashboard_module.GOATCOUNTER_SITE_CODE
    try:
        dashboard_module.GOATCOUNTER_SITE_CODE = ""
        html = dashboard_module.render_html(date(2026, 9, 9), [])
        assert "goatcounter" not in html
    finally:
        dashboard_module.GOATCOUNTER_SITE_CODE = original


def test_render_html_emits_real_tracking_script_when_site_code_set():
    import scripts.generate_dashboard as dashboard_module
    original = dashboard_module.GOATCOUNTER_SITE_CODE
    try:
        dashboard_module.GOATCOUNTER_SITE_CODE = "silent-edge-zero"
        html = dashboard_module.render_html(date(2026, 9, 9), [])
        assert 'data-goatcounter="https://silent-edge-zero.goatcounter.com/count"' in html
        assert 'src="//gc.zgo.at/count.js"' in html
    finally:
        dashboard_module.GOATCOUNTER_SITE_CODE = original


def test_render_html_includes_backtest_context():
    from datetime import date
    html = render_html(date(2026, 9, 9), [])
    assert "0.0795" in html  # Model 0's real committed Brier score
    assert "0.0875" in html  # Model 1's
    assert "0.0866" in html  # Model 2's (RL-010, with trainer/jockey features)


def test_render_track_record_empty_when_no_real_summaries():
    html = render_track_record([])
    assert "No settled results yet" in html


def test_render_track_record_real_cumulative_stats():
    summaries = [{
        "race_date": date(2026, 9, 10), "races_total": 31, "races_settled": 30,
        "top_pick_wins": 7, "top_pick_placed": 16, "favourite_wins": 9,
        "win_stake_total": 30.0, "win_profit": 24.24,
        "ew_stake_total": 60.0, "ew_profit": 27.73,
    }]
    html = render_track_record(summaries)
    assert "23.3%" in html  # top-pick hit rate: 7/30
    assert "£+24.24" in html
    assert "£+27.73" in html
    assert "30.0%" in html  # favourite rate: 9/30


def test_render_track_record_shows_small_sample_caveat_under_20_days():
    summaries = [{
        "race_date": date(2026, 9, 10), "races_total": 5, "races_settled": 5,
        "top_pick_wins": 1, "top_pick_placed": 2, "favourite_wins": 1,
        "win_stake_total": 5.0, "win_profit": -1.0,
        "ew_stake_total": 10.0, "ew_profit": -2.0,
    }]
    html = render_track_record(summaries)
    assert "far too small a sample" in html
    assert "£-1.00" in html  # a real loss renders with the minus sign, not hidden


def test_render_days_tracked_dialog_empty_when_no_dates():
    assert render_days_tracked_dialog([]) == ""


def test_render_days_tracked_dialog_lists_real_dates_newest_first():
    html = render_days_tracked_dialog([date(2026, 9, 8), date(2026, 9, 10), date(2026, 9, 9)])
    i10 = html.index("10 September 2026")
    i9 = html.index("09 September 2026")
    i8 = html.index("08 September 2026")
    assert i10 < i9 < i8  # newest first
    assert "day-2026-09-10" in html  # onclick target matches the per-day dialog's dom id


def test_render_day_history_dialog_shows_win_loss_placed_badges():
    races = [
        {"off_time": time(13, 15), "course_name": "Doncaster", "race_name": "Race A",
         "horse_name": "Winner Horse", "model_probability": 0.3, "finishing_position": 1,
         "result_note": None, "field_size": 9, "status": "WIN"},
        {"off_time": time(13, 50), "course_name": "Doncaster", "race_name": "Race B",
         "horse_name": "Placed Horse", "model_probability": 0.2, "finishing_position": 3,
         "result_note": None, "field_size": 9, "status": "PLACED"},
        {"off_time": time(14, 0), "course_name": "Epsom", "race_name": "Race C",
         "horse_name": "Loser Horse", "model_probability": 0.25, "finishing_position": 6,
         "result_note": None, "field_size": 9, "status": "LOSS"},
        {"off_time": time(14, 10), "course_name": "Epsom", "race_name": "Race D",
         "horse_name": "Pending Horse", "model_probability": 0.18, "finishing_position": None,
         "result_note": None, "field_size": 9, "status": "PENDING"},
    ]
    html = render_day_history_dialog(date(2026, 9, 10), races)
    assert 'id="day-2026-09-10"' in html
    assert "dayhist-badge-win\">WIN" in html
    assert "dayhist-badge-placed\">PLACED" in html
    assert "dayhist-badge-loss\">LOSS" in html
    assert "dayhist-badge-pending\">PENDING" in html
    assert "Winner Horse" in html and "finished 1" in html
    assert "result pending" in html  # pending race has no finishing_position or result_note


def test_render_day_history_dialog_shows_tally_of_win_placed_loss():
    races = [
        {"off_time": time(13, 15), "course_name": "Doncaster", "race_name": "Race A",
         "horse_name": "Winner Horse", "model_probability": 0.3, "finishing_position": 1,
         "result_note": None, "field_size": 9, "status": "WIN"},
        {"off_time": time(13, 20), "course_name": "Doncaster", "race_name": "Race A2",
         "horse_name": "Winner Horse 2", "model_probability": 0.3, "finishing_position": 1,
         "result_note": None, "field_size": 9, "status": "WIN"},
        {"off_time": time(13, 50), "course_name": "Doncaster", "race_name": "Race B",
         "horse_name": "Placed Horse", "model_probability": 0.2, "finishing_position": 3,
         "result_note": None, "field_size": 9, "status": "PLACED"},
        {"off_time": time(14, 0), "course_name": "Epsom", "race_name": "Race C",
         "horse_name": "Loser Horse", "model_probability": 0.25, "finishing_position": 6,
         "result_note": None, "field_size": 9, "status": "LOSS"},
    ]
    html = render_day_history_dialog(date(2026, 9, 10), races)
    assert "2 wins" in html
    assert "1 placed" in html
    assert "1 loss" in html
    assert "dayhist-tally-item dayhist-badge-pending" not in html  # no pending chip when count is 0


def test_render_day_history_dialog_shows_result_note_for_non_finishes():
    races = [{"off_time": time(13, 15), "course_name": "Doncaster", "race_name": "Race A",
              "horse_name": "Pulled Up Horse", "model_probability": 0.3, "finishing_position": None,
              "result_note": "PU", "field_size": 9, "status": "LOSS"}]
    html = render_day_history_dialog(date(2026, 9, 10), races)
    assert "PU" in html


def test_render_live_calibration_empty_when_no_settled_races():
    race_history = {date(2026, 9, 10): [
        {"off_time": time(13, 15), "course_name": "Doncaster", "race_name": "Race A",
         "horse_name": "Pending Horse", "model_probability": 0.3, "finishing_position": None,
         "result_note": None, "field_size": 9, "status": "PENDING"},
    ]}
    assert render_live_calibration(race_history) == ""


def test_render_live_calibration_empty_with_no_history():
    assert render_live_calibration({}) == ""


def test_render_live_calibration_buckets_real_settled_races_and_excludes_pending():
    race_history = {date(2026, 9, 10): [
        {"off_time": time(13, 15), "course_name": "Doncaster", "race_name": "Race A",
         "horse_name": "Winner", "model_probability": 0.22, "finishing_position": 1,
         "result_note": None, "field_size": 9, "status": "WIN"},
        {"off_time": time(13, 50), "course_name": "Doncaster", "race_name": "Race B",
         "horse_name": "Loser", "model_probability": 0.24, "finishing_position": 4,
         "result_note": None, "field_size": 9, "status": "LOSS"},
        {"off_time": time(14, 0), "course_name": "Epsom", "race_name": "Race C",
         "horse_name": "Pending", "model_probability": 0.30, "finishing_position": None,
         "result_note": None, "field_size": 9, "status": "PENDING"},
    ]}
    html = render_live_calibration(race_history)
    assert "20" in html and "25" in html  # the 20-25% bucket both real settled races fall in
    assert "n=2" in html  # only the 2 settled races counted, PENDING excluded
    assert "50.0%" in html  # 1 win of 2 in that bucket


def test_render_live_calibration_flags_small_sample():
    race_history = {date(2026, 9, 10): [
        {"off_time": time(13, 15), "course_name": "Doncaster", "race_name": "Race A",
         "horse_name": "Winner", "model_probability": 0.22, "finishing_position": 1,
         "result_note": None, "field_size": 9, "status": "WIN"},
    ]}
    html = render_live_calibration(race_history)
    assert "small live sample" in html


def test_render_track_record_no_caveat_at_20_plus_days():
    summaries = [{
        "race_date": date(2026, 9, 1 + i % 28), "races_total": 3, "races_settled": 3,
        "top_pick_wins": 1, "top_pick_placed": 1, "favourite_wins": 1,
        "win_stake_total": 3.0, "win_profit": 1.0,
        "ew_stake_total": 6.0, "ew_profit": 1.0,
    } for i in range(20)]
    html = render_track_record(summaries)
    assert "far too small a sample" not in html


if __name__ == "__main__":
    tests = [
        test_pct_formats_probability_as_percentage,
        test_bar_html_width_scales_with_probability_and_has_a_floor,
        test_render_html_with_no_races_shows_empty_state,
        test_stat_row_renders_known_real_fields,
        test_stat_row_no_racecard_stats_still_shows_odds_pending_chip,
        test_stat_row_real_odds_render_when_present,
        test_render_summary_computes_real_agreement_and_top_pick,
        test_render_summary_empty_races_returns_empty_string,
        test_going_hint_real_thresholds,
        test_fetch_course_weather_real_gb_course_parses_real_response_shape,
        test_fetch_course_weather_skips_unknown_course,
        test_fetch_course_weather_best_effort_on_http_failure,
        test_render_weather_empty_returns_empty_string,
        test_render_weather_renders_real_figures,
        test_render_overview_chart_empty_races_returns_empty_string,
        test_render_overview_chart_shows_top_pick_per_race,
        test_render_overview_chart_click_opens_matching_race_dialog,
        test_find_market_favourite_none_when_no_real_odds,
        test_find_market_favourite_shortest_odds_wins,
        test_real_calibration_confidence_grounds_in_real_bin,
        test_real_calibration_confidence_flags_small_real_sample,
        test_build_race_analysis_empty_when_no_model2_predictions,
        test_build_race_analysis_real_features_and_market_comparison,
        test_build_race_analysis_debutant_top_pick_reads_grammatically,
        test_ew_defaults_real_field_size_bands,
        test_bet_calculator_html_empty_without_real_odds,
        test_bet_calculator_html_renders_with_real_odds,
        test_render_html_includes_backtest_context,
        test_render_track_record_empty_when_no_real_summaries,
        test_render_track_record_real_cumulative_stats,
        test_render_track_record_shows_small_sample_caveat_under_20_days,
        test_render_track_record_no_caveat_at_20_plus_days,
        test_render_days_tracked_dialog_empty_when_no_dates,
        test_render_days_tracked_dialog_lists_real_dates_newest_first,
        test_render_day_history_dialog_shows_win_loss_placed_badges,
        test_render_day_history_dialog_shows_tally_of_win_placed_loss,
        test_render_day_history_dialog_shows_result_note_for_non_finishes,
        test_render_live_calibration_empty_when_no_settled_races,
        test_render_live_calibration_empty_with_no_history,
        test_render_live_calibration_buckets_real_settled_races_and_excludes_pending,
        test_render_live_calibration_flags_small_sample,
        test_render_html_emits_no_tracking_script_when_site_code_blank,
        test_render_html_emits_real_tracking_script_when_site_code_set,
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
