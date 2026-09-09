#!/usr/bin/env python3
"""
Phase 8 continued — a real local dashboard for today's live predictions.

Not a claude.ai Artifact: this shows Jonathan's own private prediction
data (Model 2's picks on real races, real racecard stats per horse), for
his own local viewing — same pattern as this ecosystem's other Dave
reports (daily_brief.html etc.), a plain local HTML file, not a
hosted/shareable link.

Reads real, already-locked rows from the `prediction` table (written by
scripts/predict_todays_races.py) plus real racecard stats from
`runner_snapshot`/`trainer`/`jockey` — this script has no fitting/
predicting logic of its own, it only renders what's already real and
locked/collected.

**Design, per Jonathan's own feedback on the first version (2026-09-09):**
Model 2 (gradient boosting) is the single primary pick shown per horse —
it edges out Model 1 very slightly in real backtesting (0.0874 vs 0.0875
Brier). Model 1's pick is shown only as a small secondary note, and ONLY
when it disagrees with Model 2 — two full columns of near-identical
numbers wasn't useful. Each horse row is a real `<details>` element (no
JS needed) — click to expand real racecard stats (age, draw, weight,
official rating, recent form, trainer, jockey), not just a name and a
percentage.

Usage: python3 scripts/generate_dashboard.py [race_date]
Defaults to today. Writes dashboard.html in the project root (overwritten
each run — the HTML file itself carries no history, the DB is the
permanent record).
"""
import sys
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
    "model2": {"label": "Model 2 (gradient boosting) — shown below", "brier": 0.0874, "logloss": 0.3089},
}


def load_predictions(conn, race_date: date):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.off_time, c.name, r.race_name, h.name, mv.name, p.model_probability,
               rs.age, rs.draw, rs.weight_lbs, rs.official_rating, rs.recent_form,
               t.name, j.name
        FROM prediction p
        JOIN race r ON r.id = p.race_id
        JOIN course c ON c.id = r.course_id
        JOIN horse h ON h.id = p.horse_id
        JOIN model_version mv ON mv.id = p.model_version_id
        LEFT JOIN runner_snapshot rs ON rs.race_id = r.id AND rs.horse_id = p.horse_id
        LEFT JOIN trainer t ON t.id = rs.trainer_id
        LEFT JOIN jockey j ON j.id = rs.jockey_id
        WHERE r.race_date = %s AND p.locked_at IS NOT NULL
        ORDER BY r.off_time, r.id, mv.name, p.model_probability DESC
        """,
        (race_date,),
    )
    rows = cur.fetchall()
    cur.close()

    races: dict[int, dict] = {}
    order: list[int] = []
    for (race_id, off_time, course_name, race_name, horse_name, model_name, prob,
         age, draw, weight_lbs, official_rating, recent_form, trainer_name, jockey_name) in rows:
        if race_id not in races:
            races[race_id] = {
                "off_time": off_time, "course_name": course_name, "race_name": race_name,
                "model1": {}, "model2": {}, "stats": {},
            }
            order.append(race_id)
        key = "model1" if model_name == "statistical_v1" else "model2"
        races[race_id][key][horse_name] = float(prob)
        races[race_id]["stats"][horse_name] = {
            "age": age, "draw": draw, "weight_lbs": weight_lbs, "official_rating": official_rating,
            "recent_form": recent_form, "trainer": trainer_name, "jockey": jockey_name,
        }

    return [races[rid] for rid in order]


def _pct(p: float) -> str:
    return f"{p * 100:.1f}%"


def _bar_html(p: float, color: str) -> str:
    width = max(2, round(p * 100))
    return (f'<div class="bar-track"><div class="bar-fill" '
            f'style="width:{width}%;background:{color}"></div></div>')


def _stat_row(stats: dict) -> str:
    parts = []
    if stats.get("age") is not None:
        parts.append(f'<span class="stat-chip">Age {stats["age"]}</span>')
    if stats.get("draw") is not None:
        parts.append(f'<span class="stat-chip">Draw {stats["draw"]}</span>')
    if stats.get("weight_lbs") is not None:
        parts.append(f'<span class="stat-chip">{stats["weight_lbs"]} lbs</span>')
    if stats.get("official_rating") is not None:
        parts.append(f'<span class="stat-chip">OR {stats["official_rating"]}</span>')
    if stats.get("recent_form"):
        parts.append(f'<span class="stat-chip">Form {stats["recent_form"]}</span>')
    if stats.get("trainer"):
        parts.append(f'<span class="stat-chip">Trainer: {stats["trainer"]}</span>')
    if stats.get("jockey"):
        parts.append(f'<span class="stat-chip">Jockey: {stats["jockey"]}</span>')
    if not parts:
        return '<div class="stat-empty">No racecard stats collected for this runner yet.</div>'
    return f'<div class="stat-chips">{"".join(parts)}</div>'


def render_race(race: dict) -> str:
    m1, m2, stats = race["model1"], race["model2"], race["stats"]
    horses = sorted(set(m1) | set(m2), key=lambda h: -m2.get(h, m1.get(h, 0.0)))

    m1_top = max(m1, key=m1.get) if m1 else None
    m2_top = max(m2, key=m2.get) if m2 else None
    agree = m1_top is not None and m1_top == m2_top

    rows_html = []
    for h in horses:
        p2 = m2.get(h, 0.0)
        is_top = h == m2_top
        row_class = "runner-row top-pick" if is_top else "runner-row"

        m1_note = ""
        if not agree and h == m1_top:
            m1_note = f'<span class="m1-note">M1 prefers this one ({_pct(m1.get(h, 0.0))})</span>'

        rows_html.append(f"""
        <details class="{row_class}">
          <summary>
            <span class="runner-name">{h}{' <span class="top-badge">TOP PICK</span>' if is_top else ''}</span>
            <span class="runner-prob">
              {m1_note}
              {_bar_html(p2, 'var(--series-1)')}
              <span class="prob-value">{_pct(p2)}</span>
            </span>
          </summary>
          {_stat_row(stats.get(h, {}))}
        </details>""")

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


def render_summary(races: list[dict]) -> str:
    """Day-level summary: race count, agreement rate, most confident pick
    of the day across every race — real numbers computed from the same
    data the race cards render, not a separate query."""
    if not races:
        return ""

    n_races = len(races)
    n_agree = 0
    best_pick = None  # (course, off_time, race_name, horse, prob)

    for race in races:
        m1, m2 = race["model1"], race["model2"]
        m1_top = max(m1, key=m1.get) if m1 else None
        m2_top = max(m2, key=m2.get) if m2 else None
        if m1_top is not None and m1_top == m2_top:
            n_agree += 1
        if m2_top is not None:
            p = m2[m2_top]
            if best_pick is None or p > best_pick[4]:
                best_pick = (race["course_name"], race["off_time"], race["race_name"], m2_top, p)

    agree_pct = round(100 * n_agree / n_races)
    best_html = ""
    if best_pick:
        course, off_time, race_name, horse, p = best_pick
        t = off_time.strftime("%H:%M") if hasattr(off_time, "strftime") else off_time
        best_html = f"""
        <div class="stat-tile">
          <div class="stat-label">Highest-confidence pick today</div>
          <div class="stat-value">{horse}</div>
          <div class="stat-sub">{_pct(p)} — {t} {course}</div>
        </div>"""

    return f"""
    <div class="stats-row">
      <div class="stat-tile">
        <div class="stat-label">Races today</div>
        <div class="stat-value">{n_races}</div>
        <div class="stat-sub">real, locked predictions</div>
      </div>
      <div class="stat-tile">
        <div class="stat-label">Model agreement</div>
        <div class="stat-value">{agree_pct}%</div>
        <div class="stat-sub">{n_agree} of {n_races} races — M1 and M2 pick the same horse</div>
      </div>
      {best_html}
    </div>"""


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
  .stats-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px; }}
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
  details.runner-row {{ border-top: 1px solid var(--border); }}
  details.runner-row:first-child {{ border-top: none; }}
  details.runner-row summary {{
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    padding: 8px 6px; cursor: pointer; list-style: none;
  }}
  details.runner-row summary::-webkit-details-marker {{ display: none; }}
  details.runner-row summary::after {{
    content: "›"; color: var(--text-muted); font-size: 16px; margin-left: 8px;
    transform: rotate(90deg); transition: transform .15s;
  }}
  details[open].runner-row summary::after {{ transform: rotate(270deg); }}
  details.runner-row.top-pick {{ background: color-mix(in srgb, var(--series-1) 6%, transparent); border-radius: 6px; }}
  .runner-name {{ font-size: 13.5px; }}
  .top-badge {{
    font-size: 9px; font-weight: 700; letter-spacing: .03em; color: var(--series-1);
    border: 1px solid var(--series-1); border-radius: 10px; padding: 1px 6px; margin-left: 6px;
  }}
  .runner-prob {{ display: flex; align-items: center; gap: 10px; font-size: 11px; color: var(--text-muted); }}
  .m1-note {{ font-size: 10px; color: var(--warn); white-space: nowrap; }}
  .bar-track {{ width: 90px; height: 6px; background: var(--surface-2); border-radius: 3px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 3px; }}
  .prob-value {{ width: 46px; text-align: right; color: var(--text-primary); font-variant-numeric: tabular-nums; font-weight: 600; }}
  .stat-chips {{ display: flex; flex-wrap: wrap; gap: 6px; padding: 4px 6px 12px; }}
  .stat-chip {{
    font-size: 11px; color: var(--text-secondary); background: var(--surface-2);
    border-radius: 6px; padding: 3px 8px;
  }}
  .stat-empty {{ font-size: 11px; color: var(--text-muted); padding: 4px 6px 12px; }}
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
    shown as research output, not betting advice. The probability shown is Model 2
    (gradient boosting, the better-backtested of the two models built) — Model 1's pick is
    only flagged when it disagrees. Click any horse for its real racecard stats.
  </div>

  {render_summary(races)}

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
