#!/usr/bin/env python3
"""
Research Intelligence Dashboard — Silent Edge Zero V2 brief, Phase 3
(Sections 15-19). A NEW, SEPARATE static page (research_dashboard.html),
deliberately not a modification of scripts/generate_dashboard.py.

**Why separate, not merged in:** generate_dashboard.py is a 1,946-line
monolithic script Jonathan already relies on daily; editing it carries
real regression risk for zero benefit to this phase's actual goal (adding
new visual research surfaces). This script queries the same DB through
the same Phase 1-4 analytics layer (src/research/*) and writes its own
HTML file with its own Chart.js-based charts — the existing dashboard is
completely untouched by this file's existence, and the model-freeze
regression guard doesn't even need to check it (nothing here is near
FROZEN_FILES).

Charts use Chart.js (CDN, confirmed as the approach with Jonathan) — the
project previously had no JS charting library at all; every existing
"chart" on the main dashboard is a CSS div bar.

Sections implemented: KPI cards (16), two donuts — four-way classification
and top-pick WON/PLACED/UNPLACED/VOID (18) — Graphs A (win-rate trend), B
(cumulative Brier), C (cumulative P&L with real max drawdown from
daily_summary), D (calibration curve), E (probability bands), F (win rate
by agreement — Silent Edge/market and Model1/Model2 kept deliberately
separate), and G (odds-band breakdown) from Section 17, and an SE-rank vs
market-rank heat map as a coloured HTML table, not a JS matrix plugin (9,
19 — kept dependency-free; Chart.js has no first-party matrix chart type
and pulling in a plugin for one table wasn't worth it). Small-sample
cells (n<20) are visually dimmed, never hidden.
NOT implemented this pass (real, honest, listed at the bottom of the
generated page itself, not hidden): per-race click-through/drill-down,
remaining Graph types C (profitability drawdown) and F (agreement
win-rate split), odds-band breakdown (Graph G), mobile-specific polish
beyond basic responsive CSS grid.

Usage: python3 scripts/generate_research_dashboard.py [--days N]
Defaults to the full live-tracked window (2026-09-10 onward).
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.dashboard_reconciliation import compute_settled_race_ids, run_reconciliation
from scripts.data_integrity_audit import run_audit
from scripts.generate_eod_report import VOID_RESULT_CODES, ew_terms_for_field_size
from src.evaluation.calibration import calibration_curve
from src.research.brier_live import compute_paired_observations, coverage_report, paired_brier_summary
from src.research.market_vs_model import classify_races, summarise_classification
from src.research.missed_winners import find_missed_winner_races, missed_winner_probability_bands
from src.research.probability_bands import probability_band_analysis
from src.research.race_dataset import attach_market_data, load_race_dataset
from src.research.ranking_matrix import aggregate_rank_matrix, build_rank_observations

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = REPO_ROOT / "research_dashboard.html"
LIVE_TRACKING_START = date(2026, 9, 9)  # earliest real locked gbm_v1 predictions exist (verified live, 2026-09-19 audit).
# Real limitation, not fixed by this constant: Smarkets market-price collection only started 2026-09-10,
# so 2026-09-09's races are real (results genuinely recovered) but will show UNRESOLVED for every
# market-comparison metric on this page (no de-vig-able price ever existed for that day).


def load_all_races(conn, start: date, end: date) -> list[dict]:
    all_races = []
    d = start
    while d <= end:
        races = load_race_dataset(conn, d)
        attach_market_data(conn, races)
        all_races.extend(races)
        d += timedelta(days=1)
    return all_races


def daily_series(conn, start: date, end: date) -> list[dict]:
    """Real day-by-day cumulative series for the two trend charts —
    walks forward one day at a time, accumulating races, and records the
    cumulative paired Brier and cumulative win rates as of each day."""
    series = []
    cumulative_races: list[dict] = []
    d = start
    while d <= end:
        races = load_race_dataset(conn, d)
        attach_market_data(conn, races)
        cumulative_races.extend(races)

        observations = compute_paired_observations(cumulative_races)
        brier = paired_brier_summary(observations)
        classified = classify_races(cumulative_races)
        class_summary = summarise_classification(classified)

        series.append({
            "date": str(d),
            "silent_edge_brier": brier["silent_edge_brier"] if brier else None,
            "market_brier": brier["market_brier"] if brier else None,
            "brier_gap": brier["brier_gap"] if brier else None,
            "n_brier_observations": brier["n"] if brier else 0,
            "silent_edge_win_rate": class_summary["silent_edge_win_rate"],
            "market_favourite_win_rate": class_summary["market_favourite_win_rate"],
            "n_eligible_races": class_summary["n_eligible"],
        })
        d += timedelta(days=1)
    return series


def render_kpi_cards(class_summary: dict, brier_summary: dict | None, roi: dict, integrity_status: str) -> str:
    def card(label: str, value: str, sub: str = "", color: str = "var(--fg)") -> str:
        return (f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value" style="color:{color}">{value}</div>'
                f'<div class="kpi-sub">{sub}</div></div>')

    n = class_summary["n_eligible"]
    integrity_color = {"PASS": "var(--teal)", "WARNING": "var(--amber)", "FAIL": "var(--red)"}.get(integrity_status, "var(--fg)")

    cards = [
        card("ELIGIBLE RACES (WIN COMPARISON)", str(n),
             f"{class_summary['n_unresolved']} excluded — no usable market data or no clear winner. "
             f"A different, real count appears elsewhere on this page: daily_summary's own 'settled' figure "
             f"(used by the ROI card) requires only that the TOP PICK's own result is known, not full market "
             f"data — the two counts measure genuinely different things and will not always match."),
        card("SILENT EDGE WIN RATE", f"{class_summary['silent_edge_win_rate']:.1%}" if n else "n/a", "top pick"),
        card("MARKET FAVOURITE WIN RATE", f"{class_summary['market_favourite_win_rate']:.1%}" if n else "n/a", "lock-time favourite"),
        card("WIN-RATE DIFFERENCE", f"{class_summary['win_rate_difference']:+.1%}" if n else "n/a",
             "negative = market ahead", "var(--red)" if (class_summary['win_rate_difference'] or 0) < 0 else "var(--teal)"),
        card("SILENT EDGE BRIER", f"{brier_summary['silent_edge_brier']:.4f}" if brier_summary else "n/a", "lower is better"),
        card("MARKET BRIER", f"{brier_summary['market_brier']:.4f}" if brier_summary else "n/a", "lower is better"),
        card("BRIER GAP", f"{brier_summary['brier_gap']:+.4f}" if brier_summary else "n/a",
             "positive = market leading", "var(--red)" if brier_summary and brier_summary['brier_gap'] > 0 else "var(--teal)"),
        card("£1 FLAT-STAKE ROI", f"{roi['roi']:+.1%}" if roi["n_staked"] else "n/a",
             f"n={roi['n_staked']} genuinely staked races ({roi['n_settled']} settled in total, "
             f"{roi['n_settled']-roi['n_staked']} had no stake — void/non-runner top pick or no market price)"),
        card("MODEL AGREEMENT", f"{class_summary['model_market_agreement_rate']:.1%}" if n else "n/a", "top pick == favourite"),
        card("DATA INTEGRITY STATUS", integrity_status, "see audit detail below", integrity_color),
    ]
    return f'<div class="kpi-grid">{"".join(cards)}</div>'


def top_pick_outcome_breakdown(races: list[dict], eligible_race_ids: Optional[set] = None) -> dict:
    """Real WON/PLACED/UNPLACED/VOID breakdown for each race's top pick
    only (Section 18's second donut) — pending races are excluded
    entirely, never counted into any settled-outcome bucket (the brief's
    own instruction: "do not mix pending races into settled-result
    percentages").

    `eligible_race_ids`, when given, restricts this to the SAME race
    population the four-way classification uses (real fix, 2026-09-19,
    for a bug Jonathan's own audit found: WON here previously totalled 81
    while the four-way donut's A+B totalled 80 for the exact same window
    — traced to race 57666, where the top pick won but had no usable
    market price at lock time, so it was UNRESOLVED in the four-way
    classification yet still counted here since this function never
    needed market data at all). Restricting both to one shared population
    means A+B and WON can never silently drift apart again — enforced at
    generation time by scripts/dashboard_reconciliation.py."""
    counts = {"WON": 0, "PLACED": 0, "UNPLACED": 0, "VOID/NR": 0}
    for race in races:
        if eligible_race_ids is not None and race["race"]["race_id"] not in eligible_race_ids:
            continue
        top_pick_id = race.get("top_pick_horse_id")
        if top_pick_id is None:
            continue
        top_pick = next((r for r in race["runners"] if r["horse"]["horse_id"] == top_pick_id), None)
        if top_pick is None:
            continue
        result = top_pick["result"]
        position, note = result["finishing_position"], result["result_note"]
        if position is None and note is None:
            continue  # pending — never counted
        if note in VOID_RESULT_CODES:
            counts["VOID/NR"] += 1
        elif position == 1:
            counts["WON"] += 1
        elif position is not None:
            field_size = race["race"].get("field_size_declared") or len(race["runners"])
            _, _, n_places = ew_terms_for_field_size(field_size)
            counts["PLACED" if position <= n_places else "UNPLACED"] += 1
        else:
            counts["UNPLACED"] += 1  # a real non-finish code (PU/F/UR/...) — ran, didn't place
    return counts


def split_both_wrong_by_agreement(classified: list[dict]) -> dict:
    """Real split of category D ("both wrong") races by whether Silent
    Edge and the market actually agreed on the (losing) horse.

    This distinction matters and was previously conflated on this
    dashboard: categories A/B/C are unambiguous about agreement (A is
    necessarily agreement — same horse, and it won; B and C are
    necessarily disagreement, since if the two forecasts shared a horse
    and it lost that pair would be D, not B or C). Category D alone is
    ambiguous — it covers BOTH "they agreed on a horse and it lost" AND
    "they picked two different horses and both lost". Collapsing those
    into one category and calling it "agreement" (as this dashboard's
    text previously did) was a real, wrong claim to correct."""
    d_races = [c for c in classified if c["category"] == "D"]
    agree = sum(1 for c in d_races if c["top_pick_horse_id"] in c["favourite_horse_ids"])
    disagree = len(d_races) - agree
    return {"total": len(d_races), "agree": agree, "disagree": disagree}


def agreement_win_rate_splits(races: list[dict], classified: list[dict]) -> dict:
    """Real win-rate comparison for two DELIBERATELY SEPARATE agreement
    notions (brief Section 17, Graph F: "do not confuse the two agreement
    measurements"):

    1. Silent Edge vs MARKET agreement — does the top pick's win rate
       differ depending on whether it also happened to be the market
       favourite (reuses market_vs_model.classify_races' own
       favourite_horse_ids, never re-derived).
    2. MODEL 1 vs MODEL 2 agreement — does Model 2's (the live/display
       model) top pick win more often when Model 1 independently agreed
       with it, using each runner's own `other_model_probability` (Model
       1's probability for that horse) already carried on the dataset.

    Both splits report n and win rate for AGREE/DISAGREE; a group with
    zero races reports None rather than a fabricated rate."""
    def _rate(hits: int, n: int) -> Optional[float]:
        return round(hits / n, 4) if n else None

    # Split 1: Silent Edge vs market.
    se_market_agree_n, se_market_agree_wins = 0, 0
    se_market_disagree_n, se_market_disagree_wins = 0, 0
    by_race_id = {c["race_id"]: c for c in classified}
    for race in races:
        c = by_race_id.get(race["race"]["race_id"])
        if c is None or c["category"] == "UNRESOLVED":
            continue
        top_pick_won = c["category"] in ("A", "B")
        agrees = c["top_pick_horse_id"] in c["favourite_horse_ids"]
        if agrees:
            se_market_agree_n += 1
            se_market_agree_wins += int(top_pick_won)
        else:
            se_market_disagree_n += 1
            se_market_disagree_wins += int(top_pick_won)

    # Split 2: Model 1 vs Model 2, entirely independent of the above.
    m1_m2_agree_n, m1_m2_agree_wins = 0, 0
    m1_m2_disagree_n, m1_m2_disagree_wins = 0, 0
    for race in races:
        runners = race["runners"]
        m2_top = race.get("top_pick_horse_id")
        if m2_top is None:
            continue
        with_m1 = [r for r in runners if r["silent_edge"].get("other_model_probability") is not None]
        if not with_m1:
            continue
        m1_top = max(with_m1, key=lambda r: r["silent_edge"]["other_model_probability"])["horse"]["horse_id"]
        m2_runner = next((r for r in runners if r["horse"]["horse_id"] == m2_top), None)
        if m2_runner is None or m2_runner["result"]["finishing_position"] is None and m2_runner["result"]["result_note"] is None:
            continue  # pending
        m2_won = m2_runner["result"]["finishing_position"] == 1
        if m1_top == m2_top:
            m1_m2_agree_n += 1
            m1_m2_agree_wins += int(m2_won)
        else:
            m1_m2_disagree_n += 1
            m1_m2_disagree_wins += int(m2_won)

    return {
        "silent_edge_vs_market": {
            "agree": {"n": se_market_agree_n, "win_rate": _rate(se_market_agree_wins, se_market_agree_n)},
            "disagree": {"n": se_market_disagree_n, "win_rate": _rate(se_market_disagree_wins, se_market_disagree_n)},
        },
        "model1_vs_model2": {
            "agree": {"n": m1_m2_agree_n, "win_rate": _rate(m1_m2_agree_wins, m1_m2_agree_n)},
            "disagree": {"n": m1_m2_disagree_n, "win_rate": _rate(m1_m2_disagree_wins, m1_m2_disagree_n)},
        },
    }


def cumulative_pnl_series(conn, start: date, end: date) -> dict:
    """Real cumulative £1 flat-stake profit series (Graph C) plus real
    maximum drawdown, sourced directly from `daily_summary` — the same
    persisted, already-correct daily win_profit figures the main
    dashboard's bank tracker uses (never re-derived independently, so the
    two can't silently disagree)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT race_date, win_profit, win_stake_total FROM daily_summary "
        "WHERE race_date BETWEEN %s AND %s AND races_settled > 0 ORDER BY race_date",
        (start, end),
    )
    rows = cur.fetchall()
    cur.close()

    dates, cumulative, running = [], [], 0.0
    peak, max_drawdown = 0.0, 0.0
    total_stake = 0.0
    for race_date, profit, stake in rows:
        running += float(profit)
        total_stake += float(stake)
        dates.append(str(race_date))
        cumulative.append(round(running, 2))
        peak = max(peak, running)
        max_drawdown = min(max_drawdown, running - peak)

    return {
        "dates": dates, "cumulative_profit": cumulative,
        "max_drawdown": round(max_drawdown, 2), "total_stake": round(total_stake, 2),
    }


def rank_population_views(observations: list[dict], band_analysis_fn=probability_band_analysis) -> dict:
    """Missed-winner brief Section 8's switchable population views:
    ALL RUNNERS, SEN TOP PICKS (model_rank==1), SEN SECOND CHOICES
    (model_rank==2), SEN THIRD CHOICES (model_rank==3) — each a
    genuinely separate, correctly-scoped population fed through the SAME
    `probability_band_analysis` function everything else on this page
    uses, so the expected-wins-by-summation discipline is identical
    across every view. A view with zero real observations returns an
    empty band dict, never fabricated bands."""
    views = {
        "ALL RUNNERS": observations,
        "SEN TOP PICKS": [o for o in observations if o.get("model_rank") == 1],
        "SEN SECOND CHOICES": [o for o in observations if o.get("model_rank") == 2],
        "SEN THIRD CHOICES": [o for o in observations if o.get("model_rank") == 3],
    }
    return {name: {"n": len(obs), "bands": band_analysis_fn(obs) if obs else {}} for name, obs in views.items()}


def odds_band_analysis(observations: list[dict]) -> dict:
    """Real odds-band breakdown (Graph G) — buckets each paired
    observation by its Silent Edge FAIR decimal odds (1/model_probability),
    not the raw model probability (that's the probability-band chart
    already built) — a genuinely different axis, per the brief's own
    Graph G. Reports selections, winners, and Brier contribution per band;
    deliberately does NOT compute a combined rate+financial figure on one
    shared axis (brief: "do not combine rates and financial totals on an
    unlabeled shared axis") — ROI is reported as its own separate field,
    not plotted against the win-rate bars."""
    from src.evaluation.calibration import brier_score

    bands = [(1, 2, "Odds < 2"), (2, 4, "2-4"), (4, 8, "4-8"), (8, 16, "8-16"), (16, float("inf"), "16+")]

    def _band_for(odds: float) -> str:
        for lo, hi, label in bands:
            if lo <= odds < hi:
                return label
        return bands[-1][2]

    grouped: dict[str, list[dict]] = {}
    for o in observations:
        if o["se_probability"] <= 0:
            continue
        fair_odds = 1.0 / o["se_probability"]
        grouped.setdefault(_band_for(fair_odds), []).append(o)

    out = {}
    for _, _, label in bands:
        rows = grouped.get(label, [])
        if not rows:
            continue
        n = len(rows)
        wins = sum(r["outcome"] for r in rows)
        out[label] = {
            "n": n, "wins": wins, "win_rate": round(wins / n, 4),
            "brier_contribution": round(brier_score([r["se_probability"] for r in rows], [r["outcome"] for r in rows]), 6),
            "small_sample": n < 20,
        }
    return out


def compute_roi(conn, start: date, end: date) -> dict:
    """Real ROI over the window. Returns BOTH `n_settled` (every race
    where the top pick's result is known, regardless of whether a real
    stake could be placed — void/non-runner top picks and top picks with
    no real market price at all are still "settled") and `n_staked` (only
    races that actually contributed a real £1 to `stake`, i.e.
    win_stake_total). These are genuinely different counts and a real
    bug, found in Jonathan's own audit 2026-09-19, was labelling the KPI
    card with `n_settled` under the words "staked races" — e.g. 297
    settled vs a real £277 staked (19 void top picks + 1 top pick with no
    market price at all, exact race IDs in
    scripts/dashboard_reconciliation.py's own check). `n_staked` is
    computed as `round(stake)` — exact because every real stake is a flat
    £1, so the two must be integers that agree by construction; the
    reconciliation check asserts this holds rather than assuming it."""
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(SUM(win_stake_total),0), COALESCE(SUM(win_profit),0), COALESCE(SUM(races_settled),0) "
        "FROM daily_summary WHERE race_date BETWEEN %s AND %s",
        (start, end),
    )
    stake, profit, n_settled = cur.fetchone()
    cur.close()
    stake, profit = float(stake), float(profit)
    return {
        "n_settled": int(n_settled), "n_staked": int(round(stake)),
        "stake": stake, "profit": profit, "roi": (profit / stake) if stake else None,
    }


def _band_extremes_sentence(bands: dict, population_label: str) -> str:
    """Shared logic behind the probability-band insight text — extracted
    so the main 'all runners' chart and each of the switchable population
    views (missed-winner brief Section 8) describe themselves the same,
    correct way rather than duplicating (and risking drifting) the
    under/overconfidence-finding logic."""
    substantial = {k: v for k, v in bands.items() if v["n_selections"] >= 20}
    if not substantial:
        return f"{population_label}: every band has fewer than 20 observations — no reliable calibration read yet."
    most_under = max(substantial, key=lambda k: substantial[k]["calibration_error"])
    most_over = min(substantial, key=lambda k: substantial[k]["calibration_error"])
    u, o = substantial[most_under], substantial[most_over]
    return (
        f"{population_label}: the {most_under} band is the most underconfident (n={u['n_selections']}, "
        f"{u['actual_win_rate']:.1%} actual vs {u['avg_predicted_probability']:.1%} predicted, "
        f"{u['calibration_error']:+.1%}); the {most_over} band the most overconfident (n={o['n_selections']}, "
        f"{o['actual_win_rate']:.1%} vs {o['avg_predicted_probability']:.1%}, {o['calibration_error']:+.1%})."
    )


def build_population_insights(rank_views: dict) -> dict:
    """One insight sentence per switchable population view (missed-winner
    brief Section 8) — 'All runners' reuses the exact same extraction
    logic as the main probability-band chart, so the two never silently
    disagree about which band is most notable for the same population."""
    return {name: _band_extremes_sentence(view["bands"], name) if view["bands"]
            else f"{name}: no eligible observations in this window yet."
            for name, view in rank_views.items()}


def build_insights(class_summary: dict, brier_summary: Optional[dict], roi: dict, series: list[dict],
                    band_analysis: dict, outcome_breakdown: dict, se_calibration: list[dict],
                    market_calibration: list[dict], rank_matrix: dict, agreement_splits: dict,
                    pnl_series: dict, odds_bands: dict, d_split: dict, missed_bands_10pt: dict,
                    n_missed_winner_races: int, rank_views: dict) -> dict:
    """Real, computed plain-language analysis for every KPI/chart/table on
    the page — every sentence below is derived directly from the same
    numbers already rendered, never a generic caption. Written at the
    register of a statistically literate analyst: point estimates are
    always given alongside sample size, and no claim of a "real edge" or
    "significant" pattern is made without that qualification attached.
    Returns one string per section, keyed by the section's anchor id."""
    insights: dict[str, str] = {}
    n = class_summary["n_eligible"]

    # --- Overall KPI summary --------------------------------------------
    if n == 0:
        insights["kpi"] = "No eligible races in this window yet — no summary can be drawn."
    else:
        wr_diff = class_summary["win_rate_difference"]
        direction = "trailing" if wr_diff < 0 else ("ahead of" if wr_diff > 0 else "level with")
        brier_txt = ""
        if brier_summary:
            leader = "the market" if brier_summary["brier_gap"] > 0 else "Silent Edge"
            brier_txt = (f" On calibrated probability accuracy (Brier score, lower is better), {leader} currently "
                         f"leads by {abs(brier_summary['brier_gap']):.4f} over {brier_summary['n']:,} paired "
                         f"observations — a real but modest gap at this sample size.")
        insights["kpi"] = (
            f"Across {n} eligible races, Silent Edge's top pick is {direction} the market favourite by "
            f"{abs(wr_diff):.1%} in win rate ({class_summary['silent_edge_win_rate']:.1%} vs "
            f"{class_summary['market_favourite_win_rate']:.1%}).{brier_txt} The model and market agree on the "
            f"same horse in {class_summary['model_market_agreement_rate']:.1%} of races — the other "
            f"{1 - class_summary['model_market_agreement_rate']:.1%} are races where the two forecasts genuinely "
            f"diverge (NOT the same thing as statistical independence — disagreement just means a different pick, "
            f"it says nothing about whether the two processes are independent). It's this divergent subset where "
            f"any real edge, if one exists, would have to be found — see categories B and C below."
        )

    # --- Four-way donut ---------------------------------------------------
    if n == 0:
        insights["four_way"] = "No eligible races to classify yet."
    else:
        fw = class_summary["four_way"]
        dominant = max(fw, key=fw.get)
        dominant_label = {"A": "both were right", "B": "Silent Edge alone was right",
                           "C": "the market alone was right", "D": "both were wrong"}[dominant]
        d_note = ""
        if d_split["total"]:
            d_note = (
                f" Category D is NOT the same as 'they agreed' — of its {d_split['total']} races, "
                f"{d_split['agree']} ({d_split['agree']/d_split['total']:.0%}) were genuine agreement (same horse, "
                f"and it lost), while {d_split['disagree']} ({d_split['disagree']/d_split['total']:.0%}) were real "
                f"disagreement (two different horses picked, both lost). Agreement and correctness are separate "
                f"questions — only category A guarantees agreement; A is not the only route to a shared miss."
            )
        insights["four_way"] = (
            f"A={fw['A']} ({fw['A']/n:.0%}), B={fw['B']} ({fw['B']/n:.0%}), C={fw['C']} ({fw['C']/n:.0%}), "
            f"D={fw['D']} ({fw['D']/n:.0%}). The modal outcome is category {dominant} — {dominant_label} — in "
            f"{fw[dominant]/n:.0%} of races. Categories B and C isolate the {fw['B']+fw['C']} races "
            f"({(fw['B']+fw['C'])/n:.0%}) where the two forecasters necessarily diverged and only one was correct "
            f"(a shared pick that lost is impossible in B/C by construction); comparing B to C directly "
            f"({fw['B']} vs {fw['C']}) is the cleanest read on relative skill.{d_note}"
        )

    # --- Cumulative Brier & win-rate trend ---------------------------------
    days_with_brier = [s for s in series if s["brier_gap"] is not None]
    if len(days_with_brier) >= 2:
        first, last = days_with_brier[0], days_with_brier[-1]
        gap0, gap1 = first["brier_gap"], last["brier_gap"]
        trend = "widened in the market's favour" if gap1 > gap0 else ("narrowed toward Silent Edge" if gap1 < gap0 else "held steady")
        insights["brier_trend"] = (
            f"The Brier gap has {trend} over the tracked window, from {gap0:+.4f} on {first['date']} to "
            f"{gap1:+.4f} on {last['date']} (n={last['n_brier_observations']:,} cumulative pairs by the last "
            f"day with data). With under two weeks of live data, this trajectory should be read as noisy — a "
            f"single unusual day can move it materially; it is not yet long enough to distinguish a genuine "
            f"drift in relative accuracy from sampling variance."
        )
    else:
        insights["brier_trend"] = "Insufficient paired observations yet to describe a trend."

    # A day with zero eligible races (e.g. before market-price collection began)
    # reports None for these fields — find the first/last day that actually has
    # a real value rather than assuming series[0]/series[-1] are populated.
    days_with_win_rate = [s for s in series if s["silent_edge_win_rate"] is not None]
    if len(days_with_win_rate) >= 2:
        first, last = days_with_win_rate[0], days_with_win_rate[-1]
        wr0, wr1 = first["silent_edge_win_rate"], last["silent_edge_win_rate"]
        mk0, mk1 = first["market_favourite_win_rate"], last["market_favourite_win_rate"]
        excluded_note = ""
        n_excluded = len(series) - len(days_with_win_rate)
        if n_excluded:
            excluded_note = (f" ({n_excluded} earlier day(s) in the window had zero eligible races for this "
                              f"comparison — e.g. before market-price collection began — and are excluded from "
                              f"this specific trend, though their real results still count elsewhere on this page.)")
        insights["win_rate_trend"] = (
            f"Silent Edge's cumulative win rate moved from {wr0:.1%} ({first['date']}) to {wr1:.1%} "
            f"({last['date']}); the market favourite's moved from {mk0:.1%} to {mk1:.1%}. Both series are "
            f"cumulative averages over a growing sample, so early-window volatility is expected and later "
            f"movement is more informative than early movement — the lines should visibly stabilise as more "
            f"races accumulate.{excluded_note}"
        )
    else:
        insights["win_rate_trend"] = "Insufficient days with eligible races yet to describe a trend."

    # --- Probability bands --------------------------------------------------
    if band_analysis:
        # Largest positive (underconfident) and negative (overconfident) calibration errors, excluding tiny n.
        substantial = {k: v for k, v in band_analysis.items() if v["n_selections"] >= 20}
        if substantial:
            most_under = max(substantial, key=lambda k: substantial[k]["calibration_error"])
            most_over = min(substantial, key=lambda k: substantial[k]["calibration_error"])
            u, o = substantial[most_under], substantial[most_over]
            insights["prob_bands"] = (
                f"The largest calibration gaps among bands with a meaningful sample (n≥20): the {most_under} band "
                f"is underconfident — {u['actual_win_rate']:.1%} actual vs {u['avg_predicted_probability']:.1%} "
                f"predicted (n={u['n_selections']}, {u['calibration_error']:+.1%} error) — while the {most_over} band runs "
                f"the other way ({o['actual_win_rate']:.1%} vs {o['avg_predicted_probability']:.1%}, "
                f"{o['calibration_error']:+.1%}). Bands below n=20 (shown dimmed logic aside, check the raw table) "
                f"carry confidence intervals too wide to draw any conclusion from a single point estimate."
            )
        else:
            insights["prob_bands"] = "Every band has fewer than 20 observations — no band supports a reliable calibration read yet."
    else:
        insights["prob_bands"] = "No probability-band data available for this window."

    # --- Missed-winner probability bands (both wrong only) -----------------
    if n_missed_winner_races == 0:
        insights["missed_winners"] = "No 'both wrong' races in this window yet — nothing to analyse."
    else:
        populated = {k: v for k, v in missed_bands_10pt.items() if v["n_winners"] > 0}
        total_unpriced = sum(v["n_winners_unpriced"] for v in missed_bands_10pt.values())
        if populated:
            top_band = max(populated, key=lambda k: populated[k]["n_winners"])
            tb = populated[top_band]
            mkt_txt = f"{tb['avg_market_probability']:.1%}" if tb["avg_market_probability"] is not None else "n/a"
            unpriced_note = (
                f" {tb['n_winners_unpriced']} of the {top_band} band's {tb['n_winners']} winners had no market "
                f"price of their own (only {tb['n_winners_priced']} are priced) — do not compare {tb['n_winners']} "
                f"directly against the Expected vs Actual panel's actual-win counts below, which require a real "
                f"market price on every runner; compare against {tb['n_winners_priced']} instead."
                if tb["n_winners_unpriced"] > 0 else ""
            )
            insights["missed_winners"] = (
                f"Of {n_missed_winner_races} 'both wrong' races, the {top_band} band produced the most missed "
                f"winners ({tb['n_winners']}, {tb['share_of_all_missed_winners']:.0%} of all missed winners), "
                f"averaging {tb['avg_se_probability']:.1%} original Silent Edge probability and {mkt_txt} market "
                f"probability. This describes WHERE missed winners cluster by their own probability — it does "
                f"NOT by itself show Silent Edge underestimates that band; the Expected vs Actual panel below, "
                f"using ALL eligible runners rather than only the winners we missed, is the real test of that."
                f"{unpriced_note}"
            )
        else:
            insights["missed_winners"] = f"{n_missed_winner_races} 'both wrong' races, but no band has a real observation yet."
        if total_unpriced > 0:
            insights["missed_winners"] += (
                f" Overall, {total_unpriced} of the {n_missed_winner_races} missed winners across all bands had no "
                f"market price of their own — these are real winners, but they cannot be matched against the "
                f"priced-only ALL RUNNERS population used elsewhere on this page, so every band count above is "
                f"reported both as a total (n_winners) and as a priced subset (n_winners_priced) side by side."
            )

    # --- Expected vs Actual (default population view = ALL RUNNERS) --------
    all_runners_view = rank_views.get("ALL RUNNERS", {"bands": {}})
    insights["expected_vs_actual"] = _band_extremes_sentence(all_runners_view["bands"], "All runners")

    # --- Top-pick outcome donut ---------------------------------------------
    total_outcomes = sum(outcome_breakdown.values())
    if total_outcomes:
        insights["outcomes"] = (
            f"Of {total_outcomes} settled top-pick selections: {outcome_breakdown['WON']} won "
            f"({outcome_breakdown['WON']/total_outcomes:.0%}), {outcome_breakdown['PLACED']} placed without "
            f"winning ({outcome_breakdown['PLACED']/total_outcomes:.0%}), {outcome_breakdown['UNPLACED']} finished "
            f"unplaced ({outcome_breakdown['UNPLACED']/total_outcomes:.0%}), and {outcome_breakdown['VOID/NR']} "
            f"were void or non-runners ({outcome_breakdown['VOID/NR']/total_outcomes:.0%}, excluded from every "
            f"other rate calculation on this page). The WON+PLACED share "
            f"({(outcome_breakdown['WON']+outcome_breakdown['PLACED'])/total_outcomes:.0%}) is the relevant figure "
            f"for each-way betting interest specifically; the win-only KPIs above use WON alone."
        )
    else:
        insights["outcomes"] = "No settled top-pick selections yet."

    # --- Calibration curve ---------------------------------------------------
    def _mean_signed_error(curve: list[dict]) -> Optional[float]:
        if not curve:
            return None
        weighted = sum((b["mean_actual"] - b["mean_predicted"]) * b["count"] for b in curve)
        total = sum(b["count"] for b in curve)
        return weighted / total if total else None

    se_err = _mean_signed_error(se_calibration)
    mk_err = _mean_signed_error(market_calibration)
    if se_err is not None and mk_err is not None:
        se_dir = "overconfident (predictions running ahead of outcomes)" if se_err < 0 else "underconfident"
        mk_dir = "overconfident" if mk_err < 0 else "underconfident"
        insights["calibration"] = (
            f"Weighted across all bins, Silent Edge's mean signed calibration error is {se_err:+.1%} — "
            f"{se_dir} on average — versus the market's {mk_err:+.1%} ({mk_dir}). A point sitting above the "
            f"diagonal wins more than its own stated probability implies; below the diagonal means it wins "
            f"less. This is the same information as the probability-band table above, presented per-bin rather "
            f"than aggregated."
        )
    else:
        insights["calibration"] = "Insufficient data to compute a calibration curve for either forecaster yet."

    # --- Agreement chart ------------------------------------------------------
    sem = agreement_splits["silent_edge_vs_market"]
    m1m2 = agreement_splits["model1_vs_model2"]
    parts = []
    if sem["agree"]["win_rate"] is not None and sem["disagree"]["win_rate"] is not None:
        parts.append(
            f"When Silent Edge's top pick matches the market favourite (n={sem['agree']['n']}), the win rate is "
            f"{sem['agree']['win_rate']:.1%}; when it doesn't (n={sem['disagree']['n']}), it's "
            f"{sem['disagree']['win_rate']:.1%}. This gap is expected and largely mechanical — favourites win "
            f"more often than longshots by construction, regardless of which model is doing the picking — so it "
            f"should not itself be read as evidence for or against the model."
        )
    if m1m2["agree"]["win_rate"] is not None and m1m2["disagree"]["win_rate"] is not None:
        parts.append(
            f"Independently, when Model 1 and Model 2 agree on the top pick (n={m1m2['agree']['n']}), the live "
            f"win rate is {m1m2['agree']['win_rate']:.1%} versus {m1m2['disagree']['win_rate']:.1%} when they "
            f"don't (n={m1m2['disagree']['n']}) — a genuinely different question (internal model consensus, not "
            f"model-vs-market agreement) and should not be conflated with the first figure."
        )
    insights["agreement"] = " ".join(parts) if parts else "Insufficient data for either agreement comparison yet."

    # --- P&L chart --------------------------------------------------------
    if pnl_series["dates"]:
        final = pnl_series["cumulative_profit"][-1]
        insights["pnl"] = (
            f"£1 level-stake profit stands at £{final:+.2f} on £{pnl_series['total_stake']:.0f} staked "
            f"({final/pnl_series['total_stake']:+.1%} ROI if stake > 0), with a maximum peak-to-trough drawdown "
            f"of £{pnl_series['max_drawdown']:.2f} across the window. As noted above, a P&L curve over "
            f"{len(pnl_series['dates'])} days is dominated by the variance of individual winning prices, not by "
            f"strike rate — the Brier gap and win-rate difference are the more reliable measures of forecasting "
            f"quality; this chart answers a different question ('what would a bettor's balance have done'), not "
            f"'is the model good'."
        )
    else:
        insights["pnl"] = "No settled staking data yet."

    # --- Odds bands ---------------------------------------------------------
    if odds_bands:
        ordered = sorted(odds_bands.items(), key=lambda kv: ["Odds < 2", "2-4", "4-8", "8-16", "16+"].index(kv[0]) if kv[0] in ["Odds < 2", "2-4", "4-8", "8-16", "16+"] else 99)
        monotonic = all(ordered[i][1]["win_rate"] >= ordered[i + 1][1]["win_rate"] for i in range(len(ordered) - 1))
        shape = ("declines monotonically from short to long odds, as basic favourite-longshot logic predicts"
                 if monotonic else "does not decline monotonically from short to long odds — worth a closer look at whichever band breaks the pattern")
        band_list = ", ".join(f"{label}: {d['win_rate']:.0%} (n={d['n']})" for label, d in ordered)
        insights["odds_bands"] = f"Win rate by Silent Edge's own fair-odds band {shape}. Raw figures: {band_list}."
    else:
        insights["odds_bands"] = "No odds-band data available yet."

    # --- Heat map -------------------------------------------------------------
    substantial_cells = {k: v for k, v in rank_matrix.items() if v["n"] >= 20}
    if substantial_cells:
        most_under = max(substantial_cells, key=lambda k: substantial_cells[k]["diff_actual_minus_expected_model"])
        most_over = min(substantial_cells, key=lambda k: substantial_cells[k]["diff_actual_minus_expected_model"])
        u, o = substantial_cells[most_under], substantial_cells[most_over]
        insights["heatmap"] = (
            f"Among cells with n≥20, Silent Edge rank {u['se_rank']} / market rank {u['market_rank']} shows the "
            f"largest underconfidence — {u['actual_wins']} actual wins against {u['expected_wins_model']} "
            f"expected from n={u['n']} runners ({u['diff_actual_minus_expected_model']:+.1f}). Rank {o['se_rank']} "
            f"/ rank {o['market_rank']} shows the sharpest overconfidence in the opposite direction "
            f"({o['actual_wins']} actual vs {o['expected_wins_model']} expected, n={o['n']}, "
            f"{o['diff_actual_minus_expected_model']:+.1f}). Both are single-cell observations from a two-week "
            f"window — treat as hypotheses to monitor (see the Research Lab tracker), not conclusions."
        )
    else:
        insights["heatmap"] = "No rank-matrix cell yet has 20 or more observations — too early to highlight any cell with confidence."

    return insights


def render_missed_race_list(bands: dict) -> str:
    """Real, accessible fallback for 'click a bar to see the underlying
    races' (Section 7) — native <details>/<summary> per band, works
    without JavaScript and on any device. Chart.js bar clicks (wired in
    the page's own <script> block) additionally open the matching
    <details> element for a nicer interaction, but the information is
    never gated behind that — every race is already in the page."""
    def _row(r: dict) -> str:
        market_cell = f'{r["winner_market_probability"]:.1%}' if r["winner_market_probability"] is not None else "n/a"
        return (f'<tr><td>{r["date"]}</td><td>{r["course"]}</td><td>{r["winner_horse_name"] or "—"}</td>'
                f'<td>{r["winner_se_probability"]:.1%}</td><td>{market_cell}</td></tr>')

    parts = []
    for band_key, band in bands.items():
        if band["n_winners"] == 0:
            continue
        rows = "".join(_row(r) for r in band["races"])
        unpriced_note = (
            f' ({band["n_winners_priced"]} priced, {band["n_winners_unpriced"]} with no market price of their own '
            f'— compare only the priced count against the Expected vs Actual panel)'
            if band["n_winners_unpriced"] > 0 else ""
        )
        parts.append(
            f'<details id="missed-band-{band_key.replace("%","").replace("-","to")}">'
            f'<summary>{band_key}: {band["n_winners"]} winner(s){unpriced_note}</summary>'
            f'<table class="race-list"><thead><tr><th>Date</th><th>Course</th><th>Winner</th>'
            f'<th>SEN prob</th><th>Market prob</th></tr></thead><tbody>{rows}</tbody></table></details>'
        )
    return "".join(parts) if parts else "<p>No missed-winner races in this window.</p>"


def render_heatmap_table(matrix: dict, max_rank: int = 6) -> str:
    """Real coloured HTML table — Silent Edge's rank for a runner (rows)
    against the market's own rank for that SAME runner (columns), one cell
    per combination. Each cell shows three numbers directly (sample size,
    real actual win rate, and the win rate Silent Edge's own probabilities
    implied it SHOULD have been) rather than hiding the comparison behind
    a hover-only tooltip — the point of the chart is that comparison, so
    it has to be readable at a glance. Colour is a restatement of the same
    two numbers (actual minus expected), included for fast visual scanning
    only, never as the sole source of the information (accessibility: the
    numbers alone tell the whole story). Small-sample cells (n<20) are
    dimmed, never hidden; a combination with zero real observations shows
    a plain dash, never a fabricated value."""
    ranks = [str(r) for r in range(1, max_rank)] + [f"{max_rank}+"]

    def cell_color(diff: float, max_abs: float) -> str:
        if max_abs == 0:
            return "rgba(255,255,255,0.04)"
        intensity = min(abs(diff) / max_abs, 1.0)
        if diff >= 0:
            return f"rgba(47,214,184,{0.12 + 0.55 * intensity:.2f})"
        return f"rgba(242,85,90,{0.12 + 0.55 * intensity:.2f})"

    all_diffs = [c["diff_actual_minus_expected_model"] for c in matrix.values()]
    max_abs_diff = max((abs(d) for d in all_diffs), default=0) or 1

    rows_html = []
    header = ('<tr><th></th><th colspan="' + str(len(ranks)) + '" class="heat-axis-title">'
               '&#8592; Where the market ranked this same horse (1 = market favourite) &#8594;</th></tr>')
    header += "<tr><th></th>" + "".join(f"<th>Market<br>rank {r}</th>" for r in ranks) + "</tr>"
    for se_rank in ranks:
        cells = [f'<th>Silent Edge<br>rank {se_rank}</th>']
        for mkt_rank in ranks:
            key = f"se_rank={se_rank},market_rank={mkt_rank}"
            cell = matrix.get(key)
            if cell is None:
                cells.append('<td class="heat-cell empty">–</td>')
                continue
            color = cell_color(cell["diff_actual_minus_expected_model"], max_abs_diff)
            opacity_class = " dim" if cell["small_sample"] else ""
            expected_rate = cell["expected_wins_model"] / cell["n"] if cell["n"] else 0
            cells.append(
                f'<td class="heat-cell{opacity_class}" style="background:{color}" '
                f'title="{cell["n"]} runners fell into this combination; {cell["actual_wins"]} of them actually won '
                f'({cell["actual_win_rate"]:.0%}); Silent Edge\'s own probabilities implied {expected_rate:.0%} should '
                f'have won ({cell["expected_wins_model"]:.1f} expected winners)">'
                f'<div class="heat-n">n={cell["n"]}</div>'
                f'<div class="heat-rate">{cell["actual_win_rate"]:.0%} actual</div>'
                f'<div class="heat-exp">{expected_rate:.0%} expected</div></td>'
            )
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    table_html = f'<table class="heatmap"><thead>{header}</thead><tbody>{"".join(rows_html)}</tbody></table>'

    legend = (
        '<div class="heat-legend">'
        '<div class="heat-legend-swatch"><span class="heat-swatch-box" style="background:rgba(242,85,90,0.55)"></span>'
        'Red = Silent Edge was <strong>overconfident</strong> here (actual win rate came in below its own prediction)</div>'
        '<div class="heat-legend-swatch"><span class="heat-swatch-box" style="background:rgba(47,214,184,0.55)"></span>'
        'Teal = Silent Edge was <strong>underconfident</strong> here (actual win rate came in above its own prediction)</div>'
        '<div class="heat-legend-swatch"><span class="heat-swatch-box" style="background:rgba(255,255,255,0.04);border:1px dashed var(--border)"></span>'
        'Dimmed / greyed text = fewer than 20 runners in that combination — too small a sample to trust the colour</div>'
        '</div>'
    )
    explainer = (
        '<p class="heat-explainer">Every runner falls into exactly one cell here, based on two independent '
        'rankings of the SAME race: which place Silent Edge put it in its own list (rows), and which place '
        'the betting market put it in (columns, 1 = market favourite). A cell reading "119 runners, 40% actual, '
        '29% expected" means: 119 times a horse was Silent Edge\'s top pick AND the market\'s favourite at once, '
        'and 40% of those actually won — versus the ~29% Silent Edge itself predicted for that group on '
        'average. When actual comes in noticeably above expected (teal), Silent Edge is underselling that '
        'group\'s real chances; noticeably below (red) means it\'s overselling them.</p>'
    )
    return explainer + table_html + legend


def render_html(start: date, end: date, class_summary: dict, brier_summary, roi: dict,
                 integrity_status: str, series: list[dict], band_analysis: dict,
                 outcome_breakdown: dict, se_calibration: list[dict], market_calibration: list[dict],
                 rank_matrix: dict, agreement_splits: dict, pnl_series: dict, odds_bands: dict,
                 d_split: dict, missed_races: list[dict], missed_bands_10pt: dict, missed_bands_5pt: dict,
                 rank_views: dict) -> str:
    n_missed_winner_races = len(missed_races)
    insights = build_insights(class_summary, brier_summary, roi, series, band_analysis, outcome_breakdown,
                               se_calibration, market_calibration, rank_matrix, agreement_splits, pnl_series,
                               odds_bands, d_split, missed_bands_10pt, n_missed_winner_races, rank_views)
    population_insights = build_population_insights(rank_views)

    donut_labels = ["A: Both correct", "B: Silent Edge only", "C: Market only", "D: Both wrong"]
    donut_data = [class_summary["four_way"][k] for k in ("A", "B", "C", "D")]

    band_keys = sorted(band_analysis, key=lambda k: band_analysis[k]["avg_predicted_probability"])
    band_expected = [band_analysis[k]["avg_predicted_probability"] * 100 for k in band_keys]
    band_actual = [band_analysis[k]["actual_win_rate"] * 100 for k in band_keys]

    outcome_labels = ["WON", "PLACED", "UNPLACED", "VOID/NR"]
    outcome_data = [outcome_breakdown[k] for k in outcome_labels]

    se_cal_points = [{"x": b["mean_predicted"] * 100, "y": b["mean_actual"] * 100} for b in se_calibration]
    market_cal_points = [{"x": b["mean_predicted"] * 100, "y": b["mean_actual"] * 100} for b in market_calibration]

    series_json = json.dumps(series)
    band_keys_json = json.dumps(band_keys)
    band_expected_json = json.dumps(band_expected)
    band_actual_json = json.dumps(band_actual)
    donut_labels_json = json.dumps(donut_labels)
    donut_data_json = json.dumps(donut_data)
    outcome_labels_json = json.dumps(outcome_labels)
    outcome_data_json = json.dumps(outcome_data)
    se_cal_points_json = json.dumps(se_cal_points)
    market_cal_points_json = json.dumps(market_cal_points)
    heatmap_html = render_heatmap_table(rank_matrix)

    sem = agreement_splits["silent_edge_vs_market"]
    m1m2 = agreement_splits["model1_vs_model2"]
    agreement_chart_data = {
        "labels": ["SE vs Market: Agree", "SE vs Market: Disagree", "Model1 vs Model2: Agree", "Model1 vs Model2: Disagree"],
        "rates": [
            (sem["agree"]["win_rate"] or 0) * 100, (sem["disagree"]["win_rate"] or 0) * 100,
            (m1m2["agree"]["win_rate"] or 0) * 100, (m1m2["disagree"]["win_rate"] or 0) * 100,
        ],
        "ns": [sem["agree"]["n"], sem["disagree"]["n"], m1m2["agree"]["n"], m1m2["disagree"]["n"]],
    }
    agreement_chart_json = json.dumps(agreement_chart_data)

    pnl_json = json.dumps(pnl_series)
    odds_band_labels = list(odds_bands.keys())
    odds_band_win_rates = [odds_bands[k]["win_rate"] * 100 for k in odds_band_labels]
    odds_band_labels_json = json.dumps(odds_band_labels)
    odds_band_win_rates_json = json.dumps(odds_band_win_rates)

    def _missed_chart_dataset(bands: dict) -> dict:
        keys = list(bands.keys())
        return {"labels": keys, "n_winners": [bands[k]["n_winners"] for k in keys]}
    missed_bands_10pt_json = json.dumps(_missed_chart_dataset(missed_bands_10pt))
    missed_bands_5pt_json = json.dumps(_missed_chart_dataset(missed_bands_5pt))

    def _population_chart_dataset(view: dict) -> dict:
        keys = sorted(view["bands"], key=lambda k: view["bands"][k]["avg_predicted_probability"]) if view["bands"] else []
        return {
            "labels": keys,
            "expected": [view["bands"][k]["avg_predicted_probability"] * 100 for k in keys],
            "actual": [view["bands"][k]["actual_win_rate"] * 100 for k in keys],
            "n": view["n"],
        }
    population_views_json = json.dumps({name: _population_chart_dataset(v) for name, v in rank_views.items()})
    population_insights_json = json.dumps(population_insights)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Silent Edge Zero — Research Intelligence</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0b1220; --panel: #121a2b; --fg: #e8edf5; --muted: #93a1b8;
    --blue: #4f8ff7; --purple: #a679f0; --teal: #2fd6b8; --amber: #f5b942; --red: #f2555a;
    --border: #24304a;
  }}
  * {{ box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--fg); font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
          margin: 0; padding: 24px 16px; }}
  h1 {{ font-size: 1.4rem; margin: 0 0 4px; }}
  .subtitle {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 24px; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 32px; }}
  .kpi-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }}
  .kpi-label {{ font-size: 0.7rem; letter-spacing: 0.04em; color: var(--muted); margin-bottom: 6px; }}
  .kpi-value {{ font-size: 1.5rem; font-weight: 600; }}
  .kpi-sub {{ font-size: 0.75rem; color: var(--muted); margin-top: 4px; }}
  .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-bottom: 32px; }}
  .chart-panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
  .chart-panel h2 {{ font-size: 0.95rem; margin: 0 0 12px; color: var(--fg); }}
  .not-yet {{ background: var(--panel); border: 1px dashed var(--border); border-radius: 10px; padding: 16px;
              color: var(--muted); font-size: 0.85rem; }}
  .not-yet ul {{ margin: 8px 0 0 18px; padding: 0; }}
  canvas {{ max-width: 100%; }}
  .chart-canvas-wrap {{ position: relative; height: 260px; }}
  .insight {{ margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border); font-size: 0.78rem;
              line-height: 1.45; color: var(--muted); }}
  .insight strong {{ color: var(--fg); }}
  .kpi-analysis {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px;
                    font-size: 0.82rem; line-height: 1.5; color: var(--muted); margin-bottom: 20px; }}
  .kpi-analysis strong {{ color: var(--fg); }}
  .heatmap {{ border-collapse: collapse; width: 100%; font-size: 0.75rem; }}
  .heatmap th {{ color: var(--muted); font-weight: 500; padding: 4px 6px; text-align: center; }}
  .heat-cell {{ text-align: center; padding: 6px 4px; border-radius: 4px; }}
  .heat-cell.empty {{ color: var(--muted); background: transparent; }}
  .heat-cell.dim {{ opacity: 0.45; }}
  .heat-n {{ font-size: 0.65rem; color: var(--muted); }}
  .heat-rate {{ font-weight: 600; }}
  .heat-exp {{ font-size: 0.65rem; color: var(--muted); }}
  .heatmap-wrap {{ overflow-x: auto; }}
  .heat-axis-title {{ color: var(--muted); font-weight: 400; font-size: 0.75rem; padding-bottom: 6px; }}
  .heatmap th {{ line-height: 1.3; }}
  .heat-explainer {{ font-size: 0.82rem; color: var(--muted); line-height: 1.5; margin: 0 0 14px; }}
  .heat-legend {{ display: flex; flex-wrap: wrap; gap: 18px; margin-top: 14px; font-size: 0.75rem; color: var(--muted); }}
  .heat-legend-swatch {{ display: flex; align-items: center; gap: 6px; }}
  .heat-swatch-box {{ display: inline-block; width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0; }}
  details {{ background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 8px;
             margin-bottom: 6px; padding: 8px 12px; }}
  details summary {{ cursor: pointer; font-size: 0.85rem; color: var(--fg); }}
  .race-list {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.78rem; }}
  .race-list th {{ text-align: left; color: var(--muted); font-weight: 500; padding: 4px 8px; }}
  .race-list td {{ padding: 4px 8px; border-top: 1px solid var(--border); }}
  .toggle-btn {{ background: var(--panel); border: 1px solid var(--border); color: var(--fg); border-radius: 6px;
                 padding: 4px 12px; font-size: 0.78rem; cursor: pointer; margin-right: 8px; }}
  .toggle-btn.active {{ background: var(--blue); border-color: var(--blue); }}
  select.population-select {{ background: var(--panel); border: 1px solid var(--border); color: var(--fg);
                               border-radius: 6px; padding: 4px 10px; font-size: 0.8rem; margin-bottom: 12px; }}
</style>
</head>
<body>
<h1>Silent Edge Zero — Research Intelligence</h1>
<div class="subtitle">{start} to {end} · live-tracked window · descriptive/observational, never fed back into the live algorithm</div>

{render_kpi_cards(class_summary, brier_summary, roi, integrity_status)}
<div class="kpi-analysis"><strong>Analysis:</strong> {insights['kpi']}</div>
<div class="not-yet" style="margin-bottom:24px;">
  <strong>On the £1 flat-stake ROI above:</strong> a positive (or negative) short-term ROI over a small,
  recent sample is <em>not</em> proof of a real statistical advantage — it can easily reflect the variance
  of a few winning or losing prices rather than a repeatable edge (brief Section 16). Read it alongside the
  Brier gap and win-rate difference above, not in isolation.
</div>

<div class="charts-grid">
  <div class="chart-panel">
    <h2>Four-way outcome classification (eligible races: {class_summary['n_eligible']})</h2>
    <div class="chart-canvas-wrap"><canvas id="donutChart"></canvas></div>
    <div class="insight"><strong>Analysis:</strong> {insights['four_way']}</div>
  </div>
  <div class="chart-panel">
    <h2>Cumulative Brier — Silent Edge vs Market (lower is better)</h2>
    <div class="chart-canvas-wrap"><canvas id="brierChart"></canvas></div>
    <div class="insight"><strong>Analysis:</strong> {insights['brier_trend']}</div>
  </div>
  <div class="chart-panel">
    <h2>Win-rate trend — Silent Edge top pick vs market favourite</h2>
    <div class="chart-canvas-wrap"><canvas id="winRateChart"></canvas></div>
    <div class="insight"><strong>Analysis:</strong> {insights['win_rate_trend']}</div>
  </div>
  <div class="chart-panel">
    <h2>Probability bands — expected vs actual win rate</h2>
    <div class="chart-canvas-wrap"><canvas id="bandChart"></canvas></div>
    <div class="insight"><strong>Analysis:</strong> {insights['prob_bands']}</div>
  </div>
  <div class="chart-panel">
    <h2>Top-pick outcomes (won / placed / unplaced / void)</h2>
    <div class="chart-canvas-wrap"><canvas id="outcomeDonutChart"></canvas></div>
    <div class="insight"><strong>Analysis:</strong> {insights['outcomes']}</div>
  </div>
  <div class="chart-panel">
    <h2>Calibration — predicted probability vs actual win frequency</h2>
    <div class="chart-canvas-wrap"><canvas id="calibrationChart"></canvas></div>
    <div class="insight"><strong>Analysis:</strong> {insights['calibration']}</div>
  </div>
  <div class="chart-panel">
    <h2>Win rate by agreement (two separate, never-conflated measures)</h2>
    <div class="chart-canvas-wrap"><canvas id="agreementChart"></canvas></div>
    <div class="insight"><strong>Analysis:</strong> {insights['agreement']}</div>
  </div>
  <div class="chart-panel">
    <h2>Cumulative £1 flat-stake profit (max drawdown: £{pnl_series['max_drawdown']}, total staked: £{pnl_series['total_stake']})</h2>
    <div class="chart-canvas-wrap"><canvas id="pnlChart"></canvas></div>
    <div class="insight"><strong>Analysis:</strong> {insights['pnl']}</div>
  </div>
  <div class="chart-panel">
    <h2>Win rate by odds band (Silent Edge's own fair odds)</h2>
    <div class="chart-canvas-wrap"><canvas id="oddsBandChart"></canvas></div>
    <div class="insight"><strong>Analysis:</strong> {insights['odds_bands']}</div>
  </div>
</div>

<div class="chart-panel" style="margin-bottom:32px;">
  <h2>Where Silent Edge and the market disagree on ranking — and who's right more often</h2>
  <div class="heatmap-wrap">{heatmap_html}</div>
  <div class="insight"><strong>Analysis:</strong> {insights['heatmap']}</div>
</div>

<div class="chart-panel" style="margin-bottom:32px;">
  <h2>WHO DID WE BOTH MISS? — What probability did SEN give the actual winner?</h2>
  <p class="heat-explainer">Restricted to races where BOTH Silent Edge's top pick and the market favourite lost
    (category D — {n_missed_winner_races} races in this window). For each such race, this groups the ACTUAL
    winner by the probability Silent Edge's own locked prediction originally gave it. This is purely descriptive
    — it says nothing on its own about whether Silent Edge is miscalibrated (see the Expected vs Actual panel
    below for that test, over ALL eligible runners, not just missed winners).</p>
  <div>
    <button class="toggle-btn active" id="btn10pt" onclick="showMissedWinnerBands(10)">10-point bands</button>
    <button class="toggle-btn" id="btn5pt" onclick="showMissedWinnerBands(5)">5-point bands</button>
  </div>
  <div class="chart-canvas-wrap"><canvas id="missedWinnerChart"></canvas></div>
  <div class="insight"><strong>Analysis:</strong> {insights['missed_winners']}</div>
  <div style="margin-top:16px;">
    <strong style="font-size:0.85rem;">Underlying races by band (10-point):</strong>
    {render_missed_race_list(missed_bands_10pt)}
  </div>
</div>

<div class="chart-panel" style="margin-bottom:32px;">
  <h2>Expected vs Actual — full eligible population (not just missed winners)</h2>
  <p class="heat-explainer">This is the scientifically load-bearing chart: it uses EVERY eligible runner in the
    selected population, not a hindsight-selected subset, and "expected wins" is a real sum of the individual
    runners' own probabilities (never an arbitrary band midpoint). A high actual-win count in a band only means
    something if it exceeds what this population's own probabilities already implied.</p>
  <select class="population-select" id="populationSelect" onchange="showPopulationView(this.value)">
    <option value="ALL RUNNERS">All runners</option>
    <option value="SEN TOP PICKS">Silent Edge top picks only</option>
    <option value="SEN SECOND CHOICES">Silent Edge 2nd choices only</option>
    <option value="SEN THIRD CHOICES">Silent Edge 3rd choices only</option>
  </select>
  <div class="chart-canvas-wrap"><canvas id="expectedActualChart"></canvas></div>
  <div class="insight"><strong>Analysis:</strong> <span id="populationInsight">{insights['expected_vs_actual']}</span></div>
</div>

<div class="not-yet">
  <strong>Not yet built (real, honest — Phase 3 is not complete):</strong>
  <ul>
    <li>Per-race drill-down / click-through from any chart, donut segment, or heat-map cell (the missed-winner
        band lists above are a real, working exception — see the expandable race tables).</li>
    <li>SEN-vs-market probability scatter plot for missed winners (brief Section 10).</li>
    <li>Winner-ranking analysis charts by SEN/market rank for missed winners specifically (Section 9) — the
        underlying data already exists in the rank-vs-rank heat map above and
        scripts/missed_winners_report.py, not yet a dedicated chart here.</li>
    <li>Race-card integration (Section 11), Track Record day-by-day missed-winner summaries (Section 12), and
        the Research Findings panel with hypothesis auto-registration (Section 14) — the Research Lab tracker
        (src/research/hypothesis_tracker.py) already exists and is used for other findings this session, just
        not wired into this specific UI yet.</li>
    <li>Mobile-specific layout polish beyond basic CSS grid responsiveness.</li>
  </ul>
</div>

<script>
const donutLabels = {donut_labels_json};
const donutData = {donut_data_json};
new Chart(document.getElementById('donutChart'), {{
  type: 'doughnut',
  data: {{ labels: donutLabels, datasets: [{{ data: donutData,
    backgroundColor: ['#2fd6b8', '#4f8ff7', '#a679f0', '#f2555a'] }}] }},
  options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#e8edf5' }} }} }} }}
}});

const series = {series_json};
const dates = series.map(s => s.date);
new Chart(document.getElementById('brierChart'), {{
  type: 'line',
  data: {{ labels: dates, datasets: [
    {{ label: 'Silent Edge Brier', data: series.map(s => s.silent_edge_brier), borderColor: '#4f8ff7', tension: 0.2 }},
    {{ label: 'Market Brier', data: series.map(s => s.market_brier), borderColor: '#a679f0', tension: 0.2 }},
  ]}},
  options: {{ maintainAspectRatio: false, scales: {{ x: {{ ticks: {{ color: '#93a1b8' }} }}, y: {{ ticks: {{ color: '#93a1b8' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});

new Chart(document.getElementById('winRateChart'), {{
  type: 'line',
  data: {{ labels: dates, datasets: [
    {{ label: 'Silent Edge win rate', data: series.map(s => s.silent_edge_win_rate * 100), borderColor: '#2fd6b8', tension: 0.2 }},
    {{ label: 'Market favourite win rate', data: series.map(s => s.market_favourite_win_rate * 100), borderColor: '#f5b942', tension: 0.2 }},
  ]}},
  options: {{ maintainAspectRatio: false, scales: {{ x: {{ ticks: {{ color: '#93a1b8' }} }},
    y: {{ ticks: {{ color: '#93a1b8', callback: v => v + '%' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});

new Chart(document.getElementById('bandChart'), {{
  type: 'bar',
  data: {{ labels: {band_keys_json}, datasets: [
    {{ label: 'Expected (avg predicted %)', data: {band_expected_json}, backgroundColor: '#4f8ff7' }},
    {{ label: 'Actual win %', data: {band_actual_json}, backgroundColor: '#2fd6b8' }},
  ]}},
  options: {{ maintainAspectRatio: false, scales: {{ x: {{ ticks: {{ color: '#93a1b8' }} }},
    y: {{ ticks: {{ color: '#93a1b8', callback: v => v + '%' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});

new Chart(document.getElementById('outcomeDonutChart'), {{
  type: 'doughnut',
  data: {{ labels: {outcome_labels_json}, datasets: [{{ data: {outcome_data_json},
    backgroundColor: ['#2fd6b8', '#4f8ff7', '#f5b942', '#93a1b8'] }}] }},
  options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#e8edf5' }} }} }} }}
}});

new Chart(document.getElementById('calibrationChart'), {{
  type: 'scatter',
  data: {{ datasets: [
    {{ label: 'Silent Edge', data: {se_cal_points_json}, backgroundColor: '#4f8ff7', pointRadius: 5 }},
    {{ label: 'Market', data: {market_cal_points_json}, backgroundColor: '#a679f0', pointRadius: 5 }},
    {{ label: 'Perfect calibration', data: [{{x:0,y:0}},{{x:100,y:100}}], type: 'line', borderColor: '#93a1b8',
       borderDash: [4,4], pointRadius: 0, fill: false }},
  ]}},
  options: {{ maintainAspectRatio: false, scales: {{
    x: {{ title: {{ display: true, text: 'Predicted %', color: '#93a1b8' }}, ticks: {{ color: '#93a1b8' }}, min: 0, max: 100 }},
    y: {{ title: {{ display: true, text: 'Actual %', color: '#93a1b8' }}, ticks: {{ color: '#93a1b8' }}, min: 0, max: 100 }},
  }}, plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});

const agreementChartData = {agreement_chart_json};
new Chart(document.getElementById('agreementChart'), {{
  type: 'bar',
  data: {{ labels: agreementChartData.labels, datasets: [
    {{ label: 'Win rate %', data: agreementChartData.rates,
       backgroundColor: ['#2fd6b8', '#f2555a', '#4f8ff7', '#a679f0'] }},
  ]}},
  options: {{ maintainAspectRatio: false, indexAxis: 'y',
    scales: {{ x: {{ ticks: {{ color: '#93a1b8', callback: v => v + '%' }} }}, y: {{ ticks: {{ color: '#93a1b8' }} }} }},
    plugins: {{ legend: {{ display: false }},
      tooltip: {{ callbacks: {{ afterLabel: ctx => 'n=' + agreementChartData.ns[ctx.dataIndex] }} }} }} }}
}});

const pnl = {pnl_json};
new Chart(document.getElementById('pnlChart'), {{
  type: 'line',
  data: {{ labels: pnl.dates, datasets: [
    {{ label: 'Cumulative profit (£)', data: pnl.cumulative_profit, borderColor: '#2fd6b8',
       backgroundColor: 'rgba(47,214,184,0.15)', fill: true, tension: 0.15 }},
  ]}},
  options: {{ maintainAspectRatio: false, scales: {{ x: {{ ticks: {{ color: '#93a1b8' }} }}, y: {{ ticks: {{ color: '#93a1b8' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});

new Chart(document.getElementById('oddsBandChart'), {{
  type: 'bar',
  data: {{ labels: {odds_band_labels_json}, datasets: [
    {{ label: 'Win rate %', data: {odds_band_win_rates_json}, backgroundColor: '#4f8ff7' }},
  ]}},
  options: {{ maintainAspectRatio: false, scales: {{ x: {{ ticks: {{ color: '#93a1b8' }} }},
    y: {{ ticks: {{ color: '#93a1b8', callback: v => v + '%' }} }} }},
    plugins: {{ legend: {{ display: false }} }} }}
}});

// --- Missed-winner probability-band chart (5pt/10pt toggle) ---
const missedBands10 = {missed_bands_10pt_json};
const missedBands5 = {missed_bands_5pt_json};
const missedWinnerChart = new Chart(document.getElementById('missedWinnerChart'), {{
  type: 'bar',
  data: {{ labels: missedBands10.labels, datasets: [
    {{ label: 'Missed winners', data: missedBands10.n_winners, backgroundColor: '#f5b942' }},
  ]}},
  options: {{ maintainAspectRatio: false,
    scales: {{ x: {{ ticks: {{ color: '#93a1b8', maxRotation: 60, minRotation: 60 }} }}, y: {{ ticks: {{ color: '#93a1b8' }} }} }},
    plugins: {{ legend: {{ display: false }} }},
    onClick: (evt, elements) => {{
      if (!elements.length) return;
      const label = missedWinnerChart.data.labels[elements[0].index];
      const id = 'missed-band-' + label.replace(/%/g, '').replace(/-/g, 'to');
      const el = document.getElementById(id);
      if (el) {{ el.open = true; el.scrollIntoView({{behavior: 'smooth', block: 'center'}}); }}
    }}
  }}
}});
function showMissedWinnerBands(width) {{
  const data = width === 5 ? missedBands5 : missedBands10;
  missedWinnerChart.data.labels = data.labels;
  missedWinnerChart.data.datasets[0].data = data.n_winners;
  missedWinnerChart.update();
  document.getElementById('btn10pt').classList.toggle('active', width === 10);
  document.getElementById('btn5pt').classList.toggle('active', width === 5);
}}

// --- Expected vs Actual chart (switchable population) ---
const populationViews = {population_views_json};
const populationInsights = {population_insights_json};
const expectedActualChart = new Chart(document.getElementById('expectedActualChart'), {{
  type: 'bar',
  data: {{ labels: populationViews['ALL RUNNERS'].labels, datasets: [
    {{ label: 'Expected (avg predicted %)', data: populationViews['ALL RUNNERS'].expected, backgroundColor: '#4f8ff7' }},
    {{ label: 'Actual win %', data: populationViews['ALL RUNNERS'].actual, backgroundColor: '#2fd6b8' }},
  ]}},
  options: {{ maintainAspectRatio: false,
    scales: {{ x: {{ ticks: {{ color: '#93a1b8' }} }}, y: {{ ticks: {{ color: '#93a1b8', callback: v => v + '%' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});
function showPopulationView(name) {{
  const data = populationViews[name];
  expectedActualChart.data.labels = data.labels;
  expectedActualChart.data.datasets[0].data = data.expected;
  expectedActualChart.data.datasets[1].data = data.actual;
  expectedActualChart.update();
  document.getElementById('populationInsight').textContent = populationInsights[name] + ' (n=' + data.n + ' runners in this view)';
}}
</script>
</body>
</html>
"""


def main():
    days = None
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])

    end = date.today()
    start = (end - timedelta(days=days - 1)) if days else LIVE_TRACKING_START

    conn = psycopg2.connect(dbname="silent_edge_zero")

    all_races = load_all_races(conn, start, end)
    classified = classify_races(all_races)
    class_summary = summarise_classification(classified)

    observations = compute_paired_observations(all_races)
    brier_summary = paired_brier_summary(observations)
    band_analysis = probability_band_analysis(observations) if observations else {}

    se_calibration = calibration_curve([o["se_probability"] for o in observations], [o["outcome"] for o in observations]) if observations else []
    market_calibration = calibration_curve([o["market_probability"] for o in observations], [o["outcome"] for o in observations]) if observations else []

    eligible_race_ids = {c["race_id"] for c in classified if c["category"] != "UNRESOLVED"}
    outcome_breakdown = top_pick_outcome_breakdown(all_races, eligible_race_ids=eligible_race_ids)

    rank_observations = build_rank_observations(all_races)
    rank_matrix = aggregate_rank_matrix(rank_observations)

    agreement_splits = agreement_win_rate_splits(all_races, classified)
    odds_bands = odds_band_analysis(observations)
    d_split = split_both_wrong_by_agreement(classified)

    missed_races = find_missed_winner_races(all_races)
    missed_bands_10pt = missed_winner_probability_bands(missed_races, band_width=0.10)
    missed_bands_5pt = missed_winner_probability_bands(missed_races, band_width=0.05)
    rank_views = rank_population_views(observations)

    roi = compute_roi(conn, start, end)
    integrity_result = run_audit(conn, start, end)
    series = daily_series(conn, start, end)
    pnl_series = cumulative_pnl_series(conn, start, end)
    settled_race_ids = compute_settled_race_ids(conn, start, end)

    conn.close()

    reconciliation = run_reconciliation(all_races, classified, class_summary, outcome_breakdown, roi,
                                         agreement_splits, rank_matrix, brier_summary, d_split,
                                         eligible_race_ids, settled_race_ids, missed_bands_10pt, band_analysis)
    print(f"Dashboard reconciliation: {reconciliation['status']} ({len(reconciliation['checks'])} checks)")
    print(f"Missed-winner races (both wrong): {len(missed_races)}")

    html = render_html(start, end, class_summary, brier_summary, roi, integrity_result["status"], series, band_analysis,
                        outcome_breakdown, se_calibration, market_calibration, rank_matrix, agreement_splits,
                        pnl_series, odds_bands, d_split, missed_races, missed_bands_10pt, missed_bands_5pt, rank_views)
    OUTPUT_PATH.write_text(html)
    print(f"Research dashboard written to {OUTPUT_PATH} ({len(html)} bytes).")
    print(f"Range: {start} .. {end}  |  {class_summary['n_eligible']} eligible races  |  "
          f"data integrity: {integrity_result['status']}")


if __name__ == "__main__":
    main()
