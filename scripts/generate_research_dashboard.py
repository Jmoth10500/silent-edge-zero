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
and top-pick WON/PLACED/UNPLACED/VOID (18) — a cumulative Brier-gap line
chart, a win-rate-trend line chart, a calibration curve (17, Graphs A/B/D),
a probability-band grouped bar chart (17, Graph E), and an SE-rank vs
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

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.data_integrity_audit import run_audit
from scripts.generate_eod_report import VOID_RESULT_CODES, ew_terms_for_field_size
from src.evaluation.calibration import calibration_curve
from src.research.brier_live import compute_paired_observations, coverage_report, paired_brier_summary
from src.research.market_vs_model import classify_races, summarise_classification
from src.research.probability_bands import probability_band_analysis
from src.research.race_dataset import attach_market_data, load_race_dataset
from src.research.ranking_matrix import aggregate_rank_matrix, build_rank_observations

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = REPO_ROOT / "research_dashboard.html"
LIVE_TRACKING_START = date(2026, 9, 10)


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
        card("TOTAL SETTLED RACES", str(n), f"{class_summary['n_unresolved']} unresolved"),
        card("SILENT EDGE WIN RATE", f"{class_summary['silent_edge_win_rate']:.1%}" if n else "n/a", "top pick"),
        card("MARKET FAVOURITE WIN RATE", f"{class_summary['market_favourite_win_rate']:.1%}" if n else "n/a", "lock-time favourite"),
        card("WIN-RATE DIFFERENCE", f"{class_summary['win_rate_difference']:+.1%}" if n else "n/a",
             "negative = market ahead", "var(--red)" if (class_summary['win_rate_difference'] or 0) < 0 else "var(--teal)"),
        card("SILENT EDGE BRIER", f"{brier_summary['silent_edge_brier']:.4f}" if brier_summary else "n/a", "lower is better"),
        card("MARKET BRIER", f"{brier_summary['market_brier']:.4f}" if brier_summary else "n/a", "lower is better"),
        card("BRIER GAP", f"{brier_summary['brier_gap']:+.4f}" if brier_summary else "n/a",
             "positive = market leading", "var(--red)" if brier_summary and brier_summary['brier_gap'] > 0 else "var(--teal)"),
        card("£1 FLAT-STAKE ROI", f"{roi['roi']:+.1%}" if roi["n"] else "n/a", f"n={roi['n']} staked races"),
        card("MODEL AGREEMENT", f"{class_summary['model_market_agreement_rate']:.1%}" if n else "n/a", "top pick == favourite"),
        card("DATA INTEGRITY STATUS", integrity_status, "see audit detail below", integrity_color),
    ]
    return f'<div class="kpi-grid">{"".join(cards)}</div>'


def top_pick_outcome_breakdown(races: list[dict]) -> dict:
    """Real WON/PLACED/UNPLACED/VOID breakdown for each race's top pick
    only (Section 18's second donut) — pending races are excluded
    entirely, never counted into any settled-outcome bucket (the brief's
    own instruction: "do not mix pending races into settled-result
    percentages")."""
    counts = {"WON": 0, "PLACED": 0, "UNPLACED": 0, "VOID/NR": 0}
    for race in races:
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


def compute_roi(conn, start: date, end: date) -> dict:
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(SUM(win_stake_total),0), COALESCE(SUM(win_profit),0), COALESCE(SUM(races_settled),0) "
        "FROM daily_summary WHERE race_date BETWEEN %s AND %s",
        (start, end),
    )
    stake, profit, n = cur.fetchone()
    cur.close()
    stake, profit = float(stake), float(profit)
    return {"n": int(n), "stake": stake, "profit": profit, "roi": (profit / stake) if stake else None}


def render_heatmap_table(matrix: dict, max_rank: int = 6) -> str:
    """Real coloured HTML table — SE rank (rows) vs market rank (columns),
    each cell showing n/win-rate, coloured by diff_actual_minus_expected_model
    (teal = Silent Edge underconfident there, red = overconfident there),
    small-sample cells (n<20) visually dimmed rather than hidden. A cell
    with no real observations renders as an empty dash, never a
    fabricated zero."""
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
    header = "<tr><th></th>" + "".join(f"<th>Mkt {r}</th>" for r in ranks) + "</tr>"
    for se_rank in ranks:
        cells = [f"<th>SE {se_rank}</th>"]
        for mkt_rank in ranks:
            key = f"se_rank={se_rank},market_rank={mkt_rank}"
            cell = matrix.get(key)
            if cell is None:
                cells.append('<td class="heat-cell empty">–</td>')
                continue
            color = cell_color(cell["diff_actual_minus_expected_model"], max_abs_diff)
            opacity_class = " dim" if cell["small_sample"] else ""
            cells.append(
                f'<td class="heat-cell{opacity_class}" style="background:{color}" '
                f'title="n={cell["n"]}, actual={cell["actual_wins"]}, expected={cell["expected_wins_model"]}, '
                f'diff={cell["diff_actual_minus_expected_model"]:+}">'
                f'<div class="heat-n">{cell["n"]}</div><div class="heat-rate">{cell["actual_win_rate"]:.0%}</div></td>'
            )
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    return f'<table class="heatmap"><thead>{header}</thead><tbody>{"".join(rows_html)}</tbody></table>'


def render_html(start: date, end: date, class_summary: dict, brier_summary, roi: dict,
                 integrity_status: str, series: list[dict], band_analysis: dict,
                 outcome_breakdown: dict, se_calibration: list[dict], market_calibration: list[dict],
                 rank_matrix: dict) -> str:
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
  .heatmap {{ border-collapse: collapse; width: 100%; font-size: 0.75rem; }}
  .heatmap th {{ color: var(--muted); font-weight: 500; padding: 4px 6px; text-align: center; }}
  .heat-cell {{ text-align: center; padding: 6px 4px; border-radius: 4px; }}
  .heat-cell.empty {{ color: var(--muted); background: transparent; }}
  .heat-cell.dim {{ opacity: 0.45; }}
  .heat-n {{ font-size: 0.65rem; color: var(--muted); }}
  .heat-rate {{ font-weight: 600; }}
  .heatmap-wrap {{ overflow-x: auto; }}
</style>
</head>
<body>
<h1>Silent Edge Zero — Research Intelligence</h1>
<div class="subtitle">{start} to {end} · live-tracked window · descriptive/observational, never fed back into the live algorithm</div>

{render_kpi_cards(class_summary, brier_summary, roi, integrity_status)}
<div class="not-yet" style="margin-bottom:24px;">
  <strong>On the £1 flat-stake ROI above:</strong> a positive (or negative) short-term ROI over a small,
  recent sample is <em>not</em> proof of a real statistical advantage — it can easily reflect the variance
  of a few winning or losing prices rather than a repeatable edge (brief Section 16). Read it alongside the
  Brier gap and win-rate difference above, not in isolation.
</div>

<div class="charts-grid">
  <div class="chart-panel">
    <h2>Four-way outcome classification (eligible races: {class_summary['n_eligible']})</h2>
    <canvas id="donutChart"></canvas>
  </div>
  <div class="chart-panel">
    <h2>Cumulative Brier — Silent Edge vs Market (lower is better)</h2>
    <canvas id="brierChart"></canvas>
  </div>
  <div class="chart-panel">
    <h2>Win-rate trend — Silent Edge top pick vs market favourite</h2>
    <canvas id="winRateChart"></canvas>
  </div>
  <div class="chart-panel">
    <h2>Probability bands — expected vs actual win rate</h2>
    <canvas id="bandChart"></canvas>
  </div>
  <div class="chart-panel">
    <h2>Top-pick outcomes (won / placed / unplaced / void)</h2>
    <canvas id="outcomeDonutChart"></canvas>
  </div>
  <div class="chart-panel">
    <h2>Calibration — predicted probability vs actual win frequency</h2>
    <canvas id="calibrationChart"></canvas>
  </div>
</div>

<div class="chart-panel" style="margin-bottom:32px;">
  <h2>Silent Edge rank vs market rank — win rate, coloured by actual minus expected (teal = Silent Edge underconfident there, red = overconfident)</h2>
  <div class="heatmap-wrap">{heatmap_html}</div>
</div>

<div class="not-yet">
  <strong>Not yet built (real, honest — Phase 3 is not complete):</strong>
  <ul>
    <li>Per-race drill-down / click-through from any chart, donut segment, or heat-map cell.</li>
    <li>Remaining Graph types C (profitability drawdown) and F (agreement win-rate split), and odds-band
        breakdown (Graph G).</li>
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
  options: {{ plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#e8edf5' }} }} }} }}
}});

const series = {series_json};
const dates = series.map(s => s.date);
new Chart(document.getElementById('brierChart'), {{
  type: 'line',
  data: {{ labels: dates, datasets: [
    {{ label: 'Silent Edge Brier', data: series.map(s => s.silent_edge_brier), borderColor: '#4f8ff7', tension: 0.2 }},
    {{ label: 'Market Brier', data: series.map(s => s.market_brier), borderColor: '#a679f0', tension: 0.2 }},
  ]}},
  options: {{ scales: {{ x: {{ ticks: {{ color: '#93a1b8' }} }}, y: {{ ticks: {{ color: '#93a1b8' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});

new Chart(document.getElementById('winRateChart'), {{
  type: 'line',
  data: {{ labels: dates, datasets: [
    {{ label: 'Silent Edge win rate', data: series.map(s => s.silent_edge_win_rate * 100), borderColor: '#2fd6b8', tension: 0.2 }},
    {{ label: 'Market favourite win rate', data: series.map(s => s.market_favourite_win_rate * 100), borderColor: '#f5b942', tension: 0.2 }},
  ]}},
  options: {{ scales: {{ x: {{ ticks: {{ color: '#93a1b8' }} }},
    y: {{ ticks: {{ color: '#93a1b8', callback: v => v + '%' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});

new Chart(document.getElementById('bandChart'), {{
  type: 'bar',
  data: {{ labels: {band_keys_json}, datasets: [
    {{ label: 'Expected (avg predicted %)', data: {band_expected_json}, backgroundColor: '#4f8ff7' }},
    {{ label: 'Actual win %', data: {band_actual_json}, backgroundColor: '#2fd6b8' }},
  ]}},
  options: {{ scales: {{ x: {{ ticks: {{ color: '#93a1b8' }} }},
    y: {{ ticks: {{ color: '#93a1b8', callback: v => v + '%' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});

new Chart(document.getElementById('outcomeDonutChart'), {{
  type: 'doughnut',
  data: {{ labels: {outcome_labels_json}, datasets: [{{ data: {outcome_data_json},
    backgroundColor: ['#2fd6b8', '#4f8ff7', '#f5b942', '#93a1b8'] }}] }},
  options: {{ plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#e8edf5' }} }} }} }}
}});

new Chart(document.getElementById('calibrationChart'), {{
  type: 'scatter',
  data: {{ datasets: [
    {{ label: 'Silent Edge', data: {se_cal_points_json}, backgroundColor: '#4f8ff7', pointRadius: 5 }},
    {{ label: 'Market', data: {market_cal_points_json}, backgroundColor: '#a679f0', pointRadius: 5 }},
    {{ label: 'Perfect calibration', data: [{{x:0,y:0}},{{x:100,y:100}}], type: 'line', borderColor: '#93a1b8',
       borderDash: [4,4], pointRadius: 0, fill: false }},
  ]}},
  options: {{ scales: {{
    x: {{ title: {{ display: true, text: 'Predicted %', color: '#93a1b8' }}, ticks: {{ color: '#93a1b8' }}, min: 0, max: 100 }},
    y: {{ title: {{ display: true, text: 'Actual %', color: '#93a1b8' }}, ticks: {{ color: '#93a1b8' }}, min: 0, max: 100 }},
  }}, plugins: {{ legend: {{ labels: {{ color: '#e8edf5' }} }} }} }}
}});
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

    outcome_breakdown = top_pick_outcome_breakdown(all_races)

    rank_observations = build_rank_observations(all_races)
    rank_matrix = aggregate_rank_matrix(rank_observations)

    roi = compute_roi(conn, start, end)
    integrity_result = run_audit(conn, start, end)
    series = daily_series(conn, start, end)

    conn.close()

    html = render_html(start, end, class_summary, brier_summary, roi, integrity_result["status"], series, band_analysis,
                        outcome_breakdown, se_calibration, market_calibration, rank_matrix)
    OUTPUT_PATH.write_text(html)
    print(f"Research dashboard written to {OUTPUT_PATH} ({len(html)} bytes).")
    print(f"Range: {start} .. {end}  |  {class_summary['n_eligible']} eligible races  |  "
          f"data integrity: {integrity_result['status']}")


if __name__ == "__main__":
    main()
