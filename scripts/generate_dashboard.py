#!/usr/bin/env python3
"""
Phase 8 continued — a real local dashboard for today's live predictions.

Not a claude.ai Artifact: this shows Jonathan's own private prediction
data (Model 1/Model 2 picks on real races), for his own local viewing —
same pattern as this ecosystem's other Dave reports (daily_brief.html
etc.), a plain local HTML file, not a hosted/shareable link.

Reads real, already-locked rows from the `prediction` table (written by
scripts/predict_todays_races.py) — this script has no fitting/predicting
logic of its own, it only renders what's already real and locked.

Usage: python3 scripts/generate_dashboard.py [race_date]
Defaults to today. Writes dashboard.html in the project root (overwritten
each run — the HTML file itself carries no history, the DB is the
permanent record).
"""
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

OUTPUT_PATH = Path(__file__).parent.parent / "dashboard.html"

# Real, committed backtest results (docs/RESEARCH_LAB.md RL-008, 2026-09-09,
# 9 walk-forward folds, ~487k real predictions, 2023-06 to 2026-06) — shown
# as honest context for what these live picks' accuracy should be expected
# to look like, NOT recomputed here (that's scripts/train_model2.py's job,
# a multi-minute real training run, not something to redo on every
# dashboard refresh).
BACKTEST_CONTEXT = {
    "model0": {"label": "Market baseline", "brier": 0.0795, "logloss": 0.2738},
    "model1": {"label": "Model 1 (statistical)", "brier": 0.0875, "logloss": 0.3097},
    "model2": {"label": "Model 2 (gradient boosting)", "brier": 0.0874, "logloss": 0.3089},
}


def load_predictions(conn, race_date: date):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.off_time, c.name, r.race_name, h.name, mv.name, p.model_probability
        FROM prediction p
        JOIN race r ON r.id = p.race_id
        JOIN course c ON c.id = r.course_id
        JOIN horse h ON h.id = p.horse_id
        JOIN model_version mv ON mv.id = p.model_version_id
        WHERE r.race_date = %s AND p.locked_at IS NOT NULL
        ORDER BY r.off_time, r.id, mv.name, p.model_probability DESC
        """,
        (race_date,),
    )
    rows = cur.fetchall()
    cur.close()

    races: dict[int, dict] = {}
    order: list[int] = []
    for race_id, off_time, course_name, race_name, horse_name, model_name, prob in rows:
        if race_id not in races:
            races[race_id] = {
                "off_time": off_time, "course_name": course_name, "race_name": race_name,
                "model1": {}, "model2": {},
            }
            order.append(race_id)
        key = "model1" if model_name == "statistical_v1" else "model2"
        races[race_id][key][horse_name] = float(prob)

    return [races[rid] for rid in order]


def _pct(p: float) -> str:
    return f"{p * 100:.1f}%"


def _bar_html(p: float, color: str) -> str:
    width = max(2, round(p * 100))
    return (f'<div class="bar-track"><div class="bar-fill" '
            f'style="width:{width}%;background:{color}"></div></div>')


def render_race(race: dict) -> str:
    m1, m2 = race["model1"], race["model2"]
    horses = sorted(set(m1) | set(m2), key=lambda h: -m1.get(h, 0.0))

    m1_top = max(m1, key=m1.get) if m1 else None
    m2_top = max(m2, key=m2.get) if m2 else None
    agree = m1_top is not None and m1_top == m2_top

    rows_html = []
    for h in horses:
        p1, p2 = m1.get(h, 0.0), m2.get(h, 0.0)
        is_top = h == m1_top or h == m2_top
        row_class = "runner-row top-pick" if is_top else "runner-row"
        rows_html.append(f"""
        <div class="{row_class}">
          <div class="runner-name">{h}{' <span class="top-badge">TOP PICK</span>' if is_top else ''}</div>
          <div class="runner-probs">
            <div class="prob-cell"><span class="prob-label">M1</span> {_bar_html(p1, 'var(--series-1)')} <span class="prob-value">{_pct(p1)}</span></div>
            <div class="prob-cell"><span class="prob-label">M2</span> {_bar_html(p2, 'var(--series-2)')} <span class="prob-value">{_pct(p2)}</span></div>
          </div>
        </div>""")

    agree_badge = '<span class="agree-badge agree">MODELS AGREE</span>' if agree else '<span class="agree-badge disagree">MODELS DISAGREE</span>'

    return f"""
    <div class="race-card">
      <div class="race-header">
        <div class="race-time">{race['off_time'].strftime('%H:%M') if hasattr(race['off_time'], 'strftime') else race['off_time']}</div>
        <div class="race-title">
          <div class="race-course">{race['course_name']}</div>
          <div class="race-name">{race['race_name']}</div>
        </div>
        {agree_badge}
      </div>
      <div class="runner-list">
        {''.join(rows_html)}
      </div>
    </div>"""


def render_backtest_context() -> str:
    cards = []
    for key, d in BACKTEST_CONTEXT.items():
        cards.append(f"""
        <div class="stat-tile">
          <div class="stat-label">{d['label']}</div>
          <div class="stat-value">{d['brier']:.4f}</div>
          <div class="stat-sub">Brier score, real walk-forward backtest</div>
        </div>""")
    return "".join(cards)


def render_html(race_date: date, races: list[dict]) -> str:
    race_cards = "".join(render_race(r) for r in races) if races else '<p class="empty">No predictions locked for this date yet.</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Silent Edge Zero — {race_date.isoformat()}</title>
<style>
  :root {{
    color-scheme: light;
    --surface-0: #fcfcfb;
    --surface-1: #ffffff;
    --surface-2: #f2f1ee;
    --border: #e4e2dc;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --text-muted: #86847d;
    --series-1: #2a78d6;
    --series-2: #eb6834;
    --good: #1baf7a;
    --warn: #eda100;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      color-scheme: dark;
      --surface-0: #141413;
      --surface-1: #1a1a19;
      --surface-2: #222220;
      --border: #33322f;
      --text-primary: #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted: #8a887f;
      --series-1: #3987e5;
      --series-2: #d95926;
      --good: #199e70;
      --warn: #c98500;
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --surface-0: #141413;
    --surface-1: #1a1a19;
    --surface-2: #222220;
    --border: #33322f;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted: #8a887f;
    --series-1: #3987e5;
    --series-2: #d95926;
    --good: #199e70;
    --warn: #c98500;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--surface-0); color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    padding: 24px 16px 64px;
  }}
  .wrap {{ max-width: 880px; margin: 0 auto; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  .subtitle {{ color: var(--text-secondary); font-size: 14px; margin-bottom: 24px; }}
  .disclaimer {{
    background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px;
    padding: 12px 16px; font-size: 13px; color: var(--text-secondary); margin-bottom: 24px;
  }}
  .stats-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 32px; }}
  .stat-tile {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px;
  }}
  .stat-label {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .03em; }}
  .stat-value {{ font-size: 24px; font-weight: 600; margin-top: 2px; }}
  .stat-sub {{ font-size: 11px; color: var(--text-muted); margin-top: 2px; }}
  .race-card {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px 18px; margin-bottom: 14px;
  }}
  .race-header {{ display: flex; align-items: flex-start; gap: 14px; margin-bottom: 12px; }}
  .race-time {{ font-size: 20px; font-weight: 700; color: var(--series-1); min-width: 52px; }}
  .race-title {{ flex: 1; }}
  .race-course {{ font-weight: 600; font-size: 15px; }}
  .race-name {{ font-size: 13px; color: var(--text-secondary); }}
  .agree-badge {{
    font-size: 10px; font-weight: 700; letter-spacing: .04em; padding: 3px 8px;
    border-radius: 20px; white-space: nowrap; align-self: center;
  }}
  .agree-badge.agree {{ background: color-mix(in srgb, var(--good) 18%, transparent); color: var(--good); }}
  .agree-badge.disagree {{ background: color-mix(in srgb, var(--warn) 18%, transparent); color: var(--warn); }}
  .runner-row {{
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    padding: 7px 0; border-top: 1px solid var(--border);
  }}
  .runner-row:first-child {{ border-top: none; }}
  .runner-row.top-pick {{ background: color-mix(in srgb, var(--series-1) 6%, transparent); border-radius: 6px; padding-left: 8px; padding-right: 8px; }}
  .runner-name {{ font-size: 13.5px; min-width: 160px; }}
  .top-badge {{
    font-size: 9px; font-weight: 700; letter-spacing: .03em; color: var(--series-1);
    border: 1px solid var(--series-1); border-radius: 10px; padding: 1px 6px; margin-left: 6px;
  }}
  .runner-probs {{ display: flex; gap: 16px; }}
  .prob-cell {{ display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-muted); }}
  .prob-label {{ width: 18px; }}
  .bar-track {{ width: 80px; height: 6px; background: var(--surface-2); border-radius: 3px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 3px; }}
  .prob-value {{ width: 42px; text-align: right; color: var(--text-primary); font-variant-numeric: tabular-nums; }}
  .empty {{ color: var(--text-muted); }}
  footer {{ margin-top: 32px; font-size: 11px; color: var(--text-muted); }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Silent Edge Zero</h1>
  <div class="subtitle">Live predictions — {race_date.strftime('%A %-d %B %Y')}</div>

  <div class="disclaimer">
    Not a tipster service. These are research predictions from a walk-forward-validated
    model that has NOT beaten the market baseline in real backtesting (see stats below) —
    shown as research output, not betting advice. Model 1/Model 2 (M1/M2) are two different
    model classes on the same feature set; when they agree, that's the strongest internal signal.
  </div>

  <div class="stats-row">
    {render_backtest_context()}
  </div>

  {race_cards}

  <footer>Generated by scripts/generate_dashboard.py — real, locked predictions only, never fabricated.</footer>
</div>
</body>
</html>"""


def main():
    race_date_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    race_date = date.fromisoformat(race_date_str)

    conn = psycopg2.connect(dbname="silent_edge_zero")
    races = load_predictions(conn, race_date)
    conn.close()

    html = render_html(race_date, races)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {OUTPUT_PATH} ({len(races)} races).")


if __name__ == "__main__":
    main()
