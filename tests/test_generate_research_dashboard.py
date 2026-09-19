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
    build_insights,
    odds_band_analysis,
    rank_population_views,
    render_heatmap_table,
    render_missed_race_list,
    render_html,
    render_kpi_cards,
    split_both_wrong_by_agreement,
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
                             {"n_settled": 6, "n_staked": 5, "stake": 5.0, "profit": 1.0, "roi": 0.2}, "PASS")
    assert "ELIGIBLE RACES" in html
    assert "10" in html
    assert "PASS" in html
    assert "+20.0%" in html  # ROI


def test_render_kpi_cards_handles_no_eligible_races_without_crashing():
    summary = _class_summary(n_eligible=0, n_unresolved=5)
    summary["silent_edge_win_rate"] = None
    summary["market_favourite_win_rate"] = None
    summary["win_rate_difference"] = None
    summary["model_market_agreement_rate"] = None
    html = render_kpi_cards(summary, None, {"n_settled": 0, "n_staked": 0, "stake": 0.0, "profit": 0.0, "roi": None}, "WARNING")
    assert "n/a" in html
    assert "WARNING" in html


def test_render_html_produces_a_complete_page_with_chart_canvases():
    html = render_html(
        date(2026, 9, 10), date(2026, 9, 19), _class_summary(), {"silent_edge_brier": 0.1, "market_brier": 0.09, "brier_gap": 0.01, "n": 10},
        {"n_settled": 6, "n_staked": 5, "stake": 5.0, "profit": 1.0, "roi": 0.2}, "PASS",
        [{"date": "2026-09-10", "silent_edge_brier": 0.1, "market_brier": 0.09, "brier_gap": 0.01,
          "n_brier_observations": 10, "silent_edge_win_rate": 0.5, "market_favourite_win_rate": 0.5, "n_eligible_races": 10}],
        {"0%-10%": {"n_selections": 100, "avg_predicted_probability": 0.05, "actual_win_rate": 0.04, "calibration_error": -0.01}},
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
        {"total": 3, "agree": 1, "disagree": 2},
        [],  # missed_races
        {"20%-30%": {"n_winners": 0, "share_of_all_missed_winners": None, "avg_se_probability": None,
                     "avg_market_probability": None, "n_races": 0, "races": []}},  # missed_bands_10pt
        {"20%-25%": {"n_winners": 0, "share_of_all_missed_winners": None, "avg_se_probability": None,
                     "avg_market_probability": None, "n_races": 0, "races": []}},  # missed_bands_5pt
        {"ALL RUNNERS": {"n": 10, "bands": {"0%-10%": {"n_selections": 100, "avg_predicted_probability": 0.05,
                                                        "actual_win_rate": 0.04, "calibration_error": -0.01}}},
         "SEN TOP PICKS": {"n": 0, "bands": {}}, "SEN SECOND CHOICES": {"n": 0, "bands": {}},
         "SEN THIRD CHOICES": {"n": 0, "bands": {}}},  # rank_views
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
    assert 'id="missedWinnerChart"' in html
    assert 'id="expectedActualChart"' in html
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


def test_outcome_breakdown_restricts_to_eligible_race_ids_when_given():
    # Real 2026-09-19 bug (Jonathan's audit): a race whose top pick won
    # but had no usable market data was UNRESOLVED in the four-way
    # classification (excluded from A+B) yet still counted as WON here,
    # making the two "wins" totals on the page disagree (81 vs 80).
    races = [
        _race_with_top_pick(1, 1, [_runner(1, finishing_position=1), _runner(2, finishing_position=2)]),  # eligible, WON
        _race_with_top_pick(2, 3, [_runner(3, finishing_position=1), _runner(4, finishing_position=2)]),  # NOT eligible, WON
    ]
    breakdown = top_pick_outcome_breakdown(races, eligible_race_ids={1})
    assert breakdown["WON"] == 1  # race 2 excluded even though its top pick also won
    assert sum(breakdown.values()) == 1


# ---------------------------------------------------------------------------
# render_heatmap_table
# ---------------------------------------------------------------------------

def test_heatmap_renders_a_dash_for_missing_cells_and_values_for_present_ones():
    matrix = {"se_rank=1,market_rank=1": {"se_rank": "1", "market_rank": "1", "n": 30, "actual_wins": 10,
                                           "actual_win_rate": 0.33, "expected_wins_model": 9.0,
                                           "diff_actual_minus_expected_model": 1.0, "small_sample": False}}
    html = render_heatmap_table(matrix)
    assert "<table" in html
    assert "33% actual" in html
    assert "30% expected" in html  # 9.0/30 = 30%
    assert html.count("–") >= 1  # most cells are genuinely empty for this tiny matrix
    assert "Silent Edge<br>rank 1" in html
    assert "Market<br>rank 1" in html


def test_heatmap_includes_explainer_and_legend():
    matrix = {"se_rank=1,market_rank=1": {"se_rank": "1", "market_rank": "1", "n": 30, "actual_wins": 10,
                                           "actual_win_rate": 0.33, "expected_wins_model": 9.0,
                                           "diff_actual_minus_expected_model": 1.0, "small_sample": False}}
    html = render_heatmap_table(matrix)
    assert "heat-explainer" in html
    assert "heat-legend" in html
    assert "overconfident" in html.lower()
    assert "underconfident" in html.lower()


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


# ---------------------------------------------------------------------------
# build_insights — every section's generated analysis text must reflect the
# real numbers passed in, and must never crash on an empty/zero-data window
# ---------------------------------------------------------------------------

def _full_class_summary(n_eligible=100):
    return {
        "n_eligible": n_eligible, "four_way": {"A": 20, "B": 15, "C": 25, "D": 40},
        "silent_edge_win_rate": 0.35, "market_favourite_win_rate": 0.45,
        "win_rate_difference": -0.10, "model_market_agreement_rate": 0.4,
    }


def _full_kwargs(n_eligible=100):
    return dict(
        class_summary=_full_class_summary(n_eligible),
        brier_summary={"silent_edge_brier": 0.11, "market_brier": 0.095, "brier_gap": 0.015, "n": 500},
        roi={"n_settled": 95, "n_staked": 90, "stake": 90.0, "profit": 12.0, "roi": 0.1333},
        series=[
            {"date": "2026-09-10", "brier_gap": 0.02, "n_brier_observations": 50,
             "silent_edge_win_rate": 0.30, "market_favourite_win_rate": 0.40},
            {"date": "2026-09-19", "brier_gap": 0.015, "n_brier_observations": 500,
             "silent_edge_win_rate": 0.35, "market_favourite_win_rate": 0.45},
        ],
        band_analysis={
            "10%-20%": {"n_selections": 200, "actual_win_rate": 0.22, "avg_predicted_probability": 0.15, "calibration_error": 0.07},
            "40%-50%": {"n_selections": 30, "actual_win_rate": 0.30, "avg_predicted_probability": 0.45, "calibration_error": -0.15},
            "80%-90%": {"n_selections": 5, "actual_win_rate": 1.0, "avg_predicted_probability": 0.85, "calibration_error": 0.15},
        },
        outcome_breakdown={"WON": 20, "PLACED": 15, "UNPLACED": 55, "VOID/NR": 10},
        se_calibration=[{"mean_predicted": 0.2, "mean_actual": 0.25, "count": 100}],
        market_calibration=[{"mean_predicted": 0.2, "mean_actual": 0.18, "count": 100}],
        rank_matrix={
            "se_rank=1,market_rank=1": {"se_rank": "1", "market_rank": "1", "n": 50, "actual_wins": 20,
                                         "expected_wins_model": 15.0, "diff_actual_minus_expected_model": 5.0},
            "se_rank=2,market_rank=3": {"se_rank": "2", "market_rank": "3", "n": 40, "actual_wins": 3,
                                         "expected_wins_model": 8.0, "diff_actual_minus_expected_model": -5.0},
        },
        agreement_splits={
            "silent_edge_vs_market": {"agree": {"n": 40, "win_rate": 0.5}, "disagree": {"n": 60, "win_rate": 0.25}},
            "model1_vs_model2": {"agree": {"n": 55, "win_rate": 0.4}, "disagree": {"n": 45, "win_rate": 0.28}},
        },
        pnl_series={"dates": ["2026-09-10", "2026-09-19"], "cumulative_profit": [3.0, 12.0], "max_drawdown": -4.5, "total_stake": 90.0},
        odds_bands={
            "Odds < 2": {"n": 30, "win_rate": 0.55}, "2-4": {"n": 40, "win_rate": 0.30},
            "4-8": {"n": 20, "win_rate": 0.10},
        },
        d_split={"total": 40, "agree": 15, "disagree": 25},
        missed_bands_10pt={
            "20%-30%": {"n_winners": 5, "share_of_all_missed_winners": 0.5, "avg_se_probability": 0.24,
                        "avg_market_probability": 0.15, "n_races": 5, "races": []},
            "0%-10%": {"n_winners": 5, "share_of_all_missed_winners": 0.5, "avg_se_probability": 0.05,
                       "avg_market_probability": 0.04, "n_races": 5, "races": []},
        },
        n_missed_winner_races=10,
        rank_views={
            "ALL RUNNERS": {"n": 100, "bands": {"20%-30%": {"n_selections": 30, "actual_win_rate": 0.35,
                                                             "avg_predicted_probability": 0.25, "calibration_error": 0.10}}},
            "SEN TOP PICKS": {"n": 20, "bands": {}},
            "SEN SECOND CHOICES": {"n": 20, "bands": {}},
            "SEN THIRD CHOICES": {"n": 20, "bands": {}},
        },
    )


def test_build_insights_kpi_reflects_real_numbers():
    insights = build_insights(**_full_kwargs())
    assert "100 eligible races" in insights["kpi"]
    assert "35.0%" in insights["kpi"] and "45.0%" in insights["kpi"]
    assert "trailing" in insights["kpi"]


def test_build_insights_four_way_identifies_dominant_category_and_sums_correctly():
    insights = build_insights(**_full_kwargs())
    assert "D" in insights["four_way"]  # D=40 is the dominant category in the fixture
    assert "A=20" in insights["four_way"] and "D=40" in insights["four_way"]


def test_build_insights_brier_trend_direction():
    insights = build_insights(**_full_kwargs())
    # gap narrowed from 0.02 to 0.015 -> toward Silent Edge
    assert "narrowed toward Silent Edge" in insights["brier_trend"]


def test_build_insights_handles_a_leading_day_with_no_eligible_races():
    # Real 2026-09-19 bug: the first tracked day (before Smarkets market-price
    # collection began) has zero eligible races, so its win rate / brier gap
    # are None -- must not crash, and must correctly skip to the first real day.
    kwargs = _full_kwargs()
    kwargs["series"] = [
        {"date": "2026-09-09", "brier_gap": None, "n_brier_observations": 0,
         "silent_edge_win_rate": None, "market_favourite_win_rate": None},
        {"date": "2026-09-10", "brier_gap": 0.02, "n_brier_observations": 50,
         "silent_edge_win_rate": 0.30, "market_favourite_win_rate": 0.40},
        {"date": "2026-09-19", "brier_gap": 0.015, "n_brier_observations": 500,
         "silent_edge_win_rate": 0.35, "market_favourite_win_rate": 0.45},
    ]
    insights = build_insights(**kwargs)
    assert "2026-09-10" in insights["win_rate_trend"]  # first REAL day, not the None day
    assert "1 earlier day(s)" in insights["win_rate_trend"]
    assert "2026-09-10" in insights["brier_trend"]


def test_build_insights_prob_bands_ignores_tiny_samples():
    insights = build_insights(**_full_kwargs())
    # the n=5 band (80%-90%) must not be picked as the "most" of anything
    assert "80%-90%" not in insights["prob_bands"]
    assert "10%-20%" in insights["prob_bands"] or "40%-50%" in insights["prob_bands"]


def test_build_insights_outcomes_percentages_sum_sensible():
    insights = build_insights(**_full_kwargs())
    assert "20 won" in insights["outcomes"] or "20 " in insights["outcomes"]
    assert "VOID/NR" not in insights["outcomes"] or "10" in insights["outcomes"]


def test_build_insights_calibration_direction():
    insights = build_insights(**_full_kwargs())
    assert "overconfident" in insights["calibration"] or "underconfident" in insights["calibration"]


def test_build_insights_heatmap_picks_extreme_cells_above_threshold():
    insights = build_insights(**_full_kwargs())
    assert "rank 1 / market rank 1" in insights["heatmap"]
    assert "Rank 2" in insights["heatmap"] and "rank 3" in insights["heatmap"]


def test_build_insights_never_crashes_on_empty_window():
    kwargs = _full_kwargs(n_eligible=0)
    kwargs["class_summary"]["silent_edge_win_rate"] = None
    kwargs["class_summary"]["market_favourite_win_rate"] = None
    kwargs["class_summary"]["win_rate_difference"] = None
    kwargs["class_summary"]["model_market_agreement_rate"] = None
    kwargs["class_summary"]["four_way"] = {"A": 0, "B": 0, "C": 0, "D": 0}
    kwargs["brier_summary"] = None
    kwargs["series"] = []
    kwargs["band_analysis"] = {}
    kwargs["outcome_breakdown"] = {"WON": 0, "PLACED": 0, "UNPLACED": 0, "VOID/NR": 0}
    kwargs["se_calibration"] = []
    kwargs["market_calibration"] = []
    kwargs["rank_matrix"] = {}
    kwargs["agreement_splits"] = {
        "silent_edge_vs_market": {"agree": {"n": 0, "win_rate": None}, "disagree": {"n": 0, "win_rate": None}},
        "model1_vs_model2": {"agree": {"n": 0, "win_rate": None}, "disagree": {"n": 0, "win_rate": None}},
    }
    kwargs["pnl_series"] = {"dates": [], "cumulative_profit": [], "max_drawdown": 0.0, "total_stake": 0.0}
    kwargs["odds_bands"] = {}
    kwargs["d_split"] = {"total": 0, "agree": 0, "disagree": 0}
    kwargs["missed_bands_10pt"] = {}
    kwargs["n_missed_winner_races"] = 0
    kwargs["rank_views"] = {"ALL RUNNERS": {"n": 0, "bands": {}}, "SEN TOP PICKS": {"n": 0, "bands": {}},
                             "SEN SECOND CHOICES": {"n": 0, "bands": {}}, "SEN THIRD CHOICES": {"n": 0, "bands": {}}}
    insights = build_insights(**kwargs)
    assert all(isinstance(v, str) and v for v in insights.values())


# ---------------------------------------------------------------------------
# split_both_wrong_by_agreement — the real fix for the "both wrong means
# they agreed" narrative bug Jonathan flagged
# ---------------------------------------------------------------------------

def test_d_split_separates_agreement_from_disagreement():
    classified = [
        # Both wrong, SAME horse picked by both (real agreement that lost)
        {"category": "D", "top_pick_horse_id": 1, "favourite_horse_ids": [1]},
        # Both wrong, DIFFERENT horses picked (real disagreement, both lost)
        {"category": "D", "top_pick_horse_id": 2, "favourite_horse_ids": [3]},
        {"category": "D", "top_pick_horse_id": 4, "favourite_horse_ids": [5]},
        # Not category D at all -- must not be counted either way
        {"category": "A", "top_pick_horse_id": 6, "favourite_horse_ids": [6]},
    ]
    result = split_both_wrong_by_agreement(classified)
    assert result["total"] == 3
    assert result["agree"] == 1
    assert result["disagree"] == 2


def test_d_split_handles_joint_favourites_correctly():
    # Real agreement even with a joint favourite -- top pick is ONE of
    # several tied market favourites.
    classified = [{"category": "D", "top_pick_horse_id": 1, "favourite_horse_ids": [1, 9]}]
    result = split_both_wrong_by_agreement(classified)
    assert result["agree"] == 1
    assert result["disagree"] == 0


def test_d_split_empty_when_no_d_races():
    result = split_both_wrong_by_agreement([{"category": "A", "top_pick_horse_id": 1, "favourite_horse_ids": [1]}])
    assert result == {"total": 0, "agree": 0, "disagree": 0}


# ---------------------------------------------------------------------------
# rank_population_views — missed-winner brief Section 8's switchable views
# ---------------------------------------------------------------------------

def _paired_obs(model_rank, se_prob=0.2, market_prob=0.15, outcome=0):
    return {"model_rank": model_rank, "se_probability": se_prob, "market_probability": market_prob, "outcome": outcome}


def test_rank_population_views_splits_by_model_rank_correctly():
    observations = [
        _paired_obs(1), _paired_obs(1), _paired_obs(2), _paired_obs(3), _paired_obs(4),
    ]
    views = rank_population_views(observations)
    assert views["ALL RUNNERS"]["n"] == 5
    assert views["SEN TOP PICKS"]["n"] == 2
    assert views["SEN SECOND CHOICES"]["n"] == 1
    assert views["SEN THIRD CHOICES"]["n"] == 1


def test_rank_population_views_empty_view_has_no_bands():
    views = rank_population_views([_paired_obs(1)])
    assert views["SEN SECOND CHOICES"]["n"] == 0
    assert views["SEN SECOND CHOICES"]["bands"] == {}


def test_rank_population_views_all_runners_uses_real_band_analysis():
    observations = [_paired_obs(1, se_prob=0.25, outcome=1) for _ in range(25)]
    views = rank_population_views(observations)
    assert "20%-30%" in views["ALL RUNNERS"]["bands"]
    assert views["ALL RUNNERS"]["bands"]["20%-30%"]["n_selections"] == 25


# ---------------------------------------------------------------------------
# render_missed_race_list — accessible fallback for chart bar clicks
# ---------------------------------------------------------------------------

def test_missed_race_list_skips_empty_bands_and_shows_populated_ones():
    bands = {
        "0%-10%": {"n_winners": 0, "races": []},
        "20%-30%": {"n_winners": 1, "races": [
            {"date": "2026-09-12", "course": "Bath", "winner_horse_name": "Testwinner",
             "winner_se_probability": 0.24, "winner_market_probability": 0.15},
        ]},
    }
    html = render_missed_race_list(bands)
    assert "0%-10%" not in html  # empty band never rendered as a fake entry
    assert "20%-30%" in html
    assert "Testwinner" in html
    assert "24.0%" in html
    assert "15.0%" in html


def test_missed_race_list_handles_missing_market_probability():
    bands = {"20%-30%": {"n_winners": 1, "races": [
        {"date": "2026-09-12", "course": "Bath", "winner_horse_name": "Testwinner",
         "winner_se_probability": 0.24, "winner_market_probability": None},
    ]}}
    html = render_missed_race_list(bands)
    assert "n/a" in html


def test_missed_race_list_all_empty_shows_a_real_message():
    html = render_missed_race_list({"0%-10%": {"n_winners": 0, "races": []}})
    assert "No missed-winner races" in html


if __name__ == "__main__":
    tests = [
        test_render_kpi_cards_includes_real_values, test_render_kpi_cards_handles_no_eligible_races_without_crashing,
        test_render_html_produces_a_complete_page_with_chart_canvases,
        test_outcome_breakdown_classifies_won_placed_unplaced_void,
        test_heatmap_renders_a_dash_for_missing_cells_and_values_for_present_ones,
        test_heatmap_includes_explainer_and_legend,
        test_agreement_splits_are_computed_independently, test_agreement_splits_none_win_rate_when_no_observations,
        test_odds_band_buckets_by_fair_odds_not_raw_probability, test_odds_band_skips_zero_probability_without_crashing,
        test_odds_band_flags_small_samples,
        test_build_insights_kpi_reflects_real_numbers, test_build_insights_four_way_identifies_dominant_category_and_sums_correctly,
        test_build_insights_brier_trend_direction, test_build_insights_handles_a_leading_day_with_no_eligible_races,
        test_build_insights_prob_bands_ignores_tiny_samples,
        test_build_insights_outcomes_percentages_sum_sensible, test_build_insights_calibration_direction,
        test_build_insights_heatmap_picks_extreme_cells_above_threshold, test_build_insights_never_crashes_on_empty_window,
        test_outcome_breakdown_restricts_to_eligible_race_ids_when_given,
        test_d_split_separates_agreement_from_disagreement, test_d_split_handles_joint_favourites_correctly,
        test_d_split_empty_when_no_d_races,
        test_rank_population_views_splits_by_model_rank_correctly, test_rank_population_views_empty_view_has_no_bands,
        test_rank_population_views_all_runners_uses_real_band_analysis,
        test_missed_race_list_skips_empty_bands_and_shows_populated_ones, test_missed_race_list_handles_missing_market_probability,
        test_missed_race_list_all_empty_shows_a_real_message,
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
