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
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
import requests

from data.gb_racecourse_coordinates import GB_RACECOURSE_COORDINATES, normalise_course_name
from scripts.analyze_top_pick_calibration import summarise as summarise_calibration_bins
from scripts.generate_eod_report import ew_terms_for_field_size
from src.features.runner_features import (
    RunnerFeatureInput,
    draw_bias_features,
    form_score,
    relative_official_rating,
    relative_weight,
)

OUTPUT_PATH = Path(__file__).parent.parent / "dashboard.html"

# Real, privacy-first visitor tracking (GoatCounter — goatcounter.com), per
# Jonathan's request (2026-09-11) to see whether anyone besides him is
# actually opening the Netlify dashboard. Set once he's signed up for his
# own free account and given the real site code — left blank renders no
# tracking script at all, never a fake/placeholder one. GoatCounter honours
# the browser's Do Not Track setting by default, which is the real,
# reliable way for Jonathan to exclude his own visits — no account-specific
# setup needed on top of that. See docs/BUILD_LOG.md for the real code
# once it's set.
GOATCOUNTER_SITE_CODE = ""

# Real, committed backtest results (docs/RESEARCH_LAB.md RL-008, 2026-09-09,
# 9 walk-forward folds, ~487k real predictions, 2023-06 to 2026-06) — shown
# as honest context for what these live picks' accuracy should be expected
# to look like, NOT recomputed here (that's scripts/train_model2.py's job,
# a multi-minute real training run, not something to redo on every
# dashboard refresh).
BACKTEST_CONTEXT = {
    "model0": {"label": "Market baseline", "brier": 0.0795, "logloss": 0.2738},
    "model1": {"label": "Model 1 (statistical)", "brier": 0.0875, "logloss": 0.3096},
    "model2": {"label": "Model 2 (gradient boosting) — shown below", "brier": 0.0866, "logloss": 0.3051},
}

# Real, committed calibration curve (docs/RESEARCH_LAB.md RL-010,
# scripts/train_model2.py real output with the current active 8-feature
# model incl. real trainer/jockey strike rate, 9 real walk-forward folds,
# ~487k real predictions, 2026-09-10). Each bin's "actual" is the REAL
# observed win rate for predictions that fell in that range — this is
# what "confidence" below is grounded in: not a new invented score, the
# real historical accuracy of a prediction this strong. A bin with n<150
# is flagged as too small a real sample to trust on its own.
REAL_CALIBRATION_BINS = [
    # (low, high, predicted, actual, n)
    (0.0, 0.1, 0.061, 0.059, 296317),
    (0.1, 0.2, 0.137, 0.141, 150284),
    (0.2, 0.3, 0.238, 0.239, 30474),
    (0.3, 0.4, 0.339, 0.329, 7466),
    (0.4, 0.5, 0.441, 0.423, 2069),
    (0.5, 0.6, 0.540, 0.504, 569),
    (0.6, 0.7, 0.641, 0.541, 196),
    (0.7, 0.8, 0.739, 0.681, 47),
    (0.8, 0.9, 0.817, 0.600, 5),
]


def load_predictions(conn, race_date: date):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.off_time, c.name, r.race_name, h.id, h.name, mv.name, p.model_probability,
               rs.age, rs.draw, rs.weight_lbs, rs.official_rating, rs.recent_form,
               t.name, j.name, ms.exchange_back, ms.exchange_lay, ms.midprice
        FROM prediction p
        JOIN race r ON r.id = p.race_id
        JOIN course c ON c.id = r.course_id
        JOIN horse h ON h.id = p.horse_id
        JOIN model_version mv ON mv.id = p.model_version_id
        LEFT JOIN runner_snapshot rs ON rs.race_id = r.id AND rs.horse_id = p.horse_id
        LEFT JOIN trainer t ON t.id = rs.trainer_id
        LEFT JOIN jockey j ON j.id = rs.jockey_id
        LEFT JOIN LATERAL (
            SELECT exchange_back, exchange_lay, midprice
            FROM market_snapshot ms2
            WHERE ms2.race_id = r.id AND ms2.horse_id = p.horse_id
            ORDER BY ms2.observed_at DESC LIMIT 1
        ) ms ON true
        WHERE r.race_date = %s AND p.locked_at IS NOT NULL
        ORDER BY r.off_time, r.id, mv.name, p.model_probability DESC
        """,
        (race_date,),
    )
    rows = cur.fetchall()
    cur.close()

    races: dict[int, dict] = {}
    order: list[int] = []
    for (race_id, off_time, course_name, race_name, horse_id, horse_name, model_name, prob,
         age, draw, weight_lbs, official_rating, recent_form, trainer_name, jockey_name,
         exchange_back, exchange_lay, midprice) in rows:
        if race_id not in races:
            races[race_id] = {
                "race_id": race_id, "off_time": off_time, "course_name": course_name,
                "race_name": race_name, "model1": {}, "model2": {}, "stats": {},
            }
            order.append(race_id)
        key = "model1" if model_name == "statistical_v1" else "model2"
        races[race_id][key][horse_name] = float(prob)
        races[race_id]["stats"][horse_name] = {
            "horse_id": horse_id, "age": age, "draw": draw, "weight_lbs": weight_lbs,
            "official_rating": official_rating, "recent_form": recent_form,
            "trainer": trainer_name, "jockey": jockey_name,
            "exchange_back": float(exchange_back) if exchange_back is not None else None,
            "exchange_lay": float(exchange_lay) if exchange_lay is not None else None,
            "midprice": float(midprice) if midprice is not None else None,
        }

    return [races[rid] for rid in order]


def load_daily_summaries(conn) -> list[dict]:
    """Real, persisted per-day track record — written by
    scripts/generate_daily_summary.py from actually-settled runner_result
    rows. Every day this returns is real; a day with no results yet
    simply has no row (never a zero-filled placeholder invented here)."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT race_date, races_total, races_settled, top_pick_wins, top_pick_placed,
               favourite_wins, win_stake_total, win_profit, ew_stake_total, ew_profit
        FROM daily_summary
        WHERE races_settled > 0
        ORDER BY race_date
        """
    )
    rows = cur.fetchall()
    cur.close()
    out = []
    for (race_date_, races_total, races_settled, top_pick_wins, top_pick_placed,
         favourite_wins, win_stake_total, win_profit, ew_stake_total, ew_profit) in rows:
        out.append({
            "race_date": race_date_, "races_total": races_total, "races_settled": races_settled,
            "top_pick_wins": top_pick_wins, "top_pick_placed": top_pick_placed,
            "favourite_wins": favourite_wins,
            "win_stake_total": float(win_stake_total), "win_profit": float(win_profit),
            "ew_stake_total": float(ew_stake_total), "ew_profit": float(ew_profit),
        })
    return out


def load_race_history(conn, race_dates: list[date]) -> dict[date, list[dict]]:
    """Real per-race top-pick + real settled outcome, for every real
    tracked day (see daily_summary) — feeds the "Days tracked" popup so
    Jonathan can click through to a specific day's race-by-race
    breakdown. Restricted to gbm_v1's locked top pick per race, same
    definition scripts/generate_eod_report.py already uses (never a
    second, different notion of "the pick" invented here)."""
    if not race_dates:
        return {}
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.race_date, r.id, r.off_time, c.name, r.race_name, h.name, p.model_probability,
               rr.finishing_position, rr.result_note,
               (SELECT COUNT(*) FROM prediction p2
                JOIN model_version mv2 ON mv2.id = p2.model_version_id
                WHERE p2.race_id = r.id AND mv2.name = 'gbm_v1' AND p2.locked_at IS NOT NULL) AS field_size
        FROM prediction p
        JOIN race r ON r.id = p.race_id
        JOIN course c ON c.id = r.course_id
        JOIN horse h ON h.id = p.horse_id
        JOIN model_version mv ON mv.id = p.model_version_id
        LEFT JOIN runner_result rr ON rr.race_id = r.id AND rr.horse_id = p.horse_id
        WHERE mv.name = 'gbm_v1' AND p.locked_at IS NOT NULL AND r.race_date = ANY(%s)
        ORDER BY r.race_date, r.off_time, r.id, p.model_probability DESC
        """,
        (race_dates,),
    )
    rows = cur.fetchall()
    cur.close()

    out: dict[date, list[dict]] = {}
    seen_races: set[int] = set()
    for (race_date_, race_id, off_time, course_name, race_name, horse_name, prob,
         position, result_note, field_size) in rows:
        if race_id in seen_races:
            continue  # rows are ordered by probability desc — first row per race is the real top pick
        seen_races.add(race_id)
        _, _, n_places = ew_terms_for_field_size(field_size)
        if position is None:
            status = "PENDING"
        elif position == 1:
            status = "WIN"
        elif n_places and position <= n_places:
            status = "PLACED"
        else:
            status = "LOSS"
        out.setdefault(race_date_, []).append({
            "off_time": off_time, "course_name": course_name, "race_name": race_name,
            "horse_name": horse_name, "model_probability": float(prob),
            "finishing_position": position, "result_note": result_note,
            "field_size": field_size, "status": status,
        })
    return out


def fetch_course_weather(course_names: set[str], race_date: date, http_get=requests.get) -> dict[str, dict]:
    """Real, live daily forecast per real GB course — Open-Meteo's free
    forecast endpoint (no key, same provider as src/providers/weather_open_meteo.py,
    but the daily-aggregate fields rather than an hourly snapshot, since
    this is for "what's the going likely to be today" context, not a
    leakage-safe model feature). A course with no known coordinates (not
    yet in our real 59-course list, or a non-GB course) is skipped
    entirely — never guessed. `http_get` is injectable for testing.
    """
    out: dict[str, dict] = {}
    for name in sorted(course_names):
        key = normalise_course_name(name)
        coords = GB_RACECOURSE_COORDINATES.get(key)
        if coords is None:
            continue
        lat, lon = coords
        try:
            resp = http_get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat, "longitude": lon,
                    "daily": "precipitation_sum,precipitation_probability_max,"
                             "temperature_2m_max,temperature_2m_min,wind_speed_10m_max",
                    "timezone": "Europe/London",
                    "start_date": race_date.isoformat(), "end_date": race_date.isoformat(),
                },
                timeout=10,
            )
            resp.raise_for_status()
            daily = resp.json().get("daily", {})
            if not daily.get("time"):
                continue
            out[name] = {
                "precip_mm": daily["precipitation_sum"][0],
                "precip_prob": daily["precipitation_probability_max"][0],
                "temp_max": daily["temperature_2m_max"][0],
                "temp_min": daily["temperature_2m_min"][0],
                "wind_kmh": daily["wind_speed_10m_max"][0],
            }
        except Exception:
            continue  # best-effort — a weather-fetch failure never breaks the dashboard
    return out


def _going_hint(w: dict) -> str:
    """Plain-language going hint from real real forecast numbers — never a
    precise going prediction (that needs course drainage/soil knowledge
    this project doesn't have), just an honest, coarse steer."""
    precip = w.get("precip_mm") or 0
    if precip >= 10:
        return "Likely soft/heavy"
    if precip >= 3:
        return "Possible easing"
    if precip <= 0.2:
        return "Likely fast-side"
    return "Little change expected"


def render_weather(course_weather: dict[str, dict]) -> str:
    if not course_weather:
        return ""
    cards = []
    for course, w in course_weather.items():
        cards.append(f"""
        <div class="weather-card">
          <div class="weather-course">{course}</div>
          <div class="weather-figures">
            <span>{w['precip_mm']:.1f}mm rain ({w['precip_prob']:.0f}%)</span>
            <span>{w['temp_min']:.0f}-{w['temp_max']:.0f}°C</span>
            <span>{w['wind_kmh']:.0f} km/h wind</span>
          </div>
          <div class="weather-going">{_going_hint(w)}</div>
        </div>""")
    return f"""
    <div class="section-label">Today's course conditions (live forecast)</div>
    <div class="weather-row">{''.join(cards)}</div>"""


def render_overview_chart(races: list[dict]) -> str:
    """Real horizontal bar chart: every race today, sorted by off_time,
    bar length = Model 2's top-pick confidence — lets you see at a glance
    where the model is most/least sure today, before scrolling every card."""
    if not races:
        return ""
    rows = []
    for race in races:
        m2 = race["model2"]
        if not m2:
            continue
        top_horse = max(m2, key=m2.get)
        p = m2[top_horse]
        t = race["off_time"].strftime("%H:%M") if hasattr(race["off_time"], "strftime") else race["off_time"]
        width = max(2, round(p * 100))
        race_id = race.get("race_id")
        onclick = f"document.getElementById('race-{race_id}').showModal()" if race_id is not None else ""
        rows.append(f"""
        <div class="overview-row" onclick="{onclick}">
          <span class="overview-time">{t}</span>
          <span class="overview-course">{race['course_name']}</span>
          <span class="overview-pct">{_pct(p)}</span>
          <div class="overview-bar-wrap">
            <div class="overview-bar-track"><div class="overview-bar-fill" style="width:{width}%"></div></div>
            <span class="overview-horse">{top_horse}</span>
          </div>
        </div>""")
    return f"""
    <div class="section-label">Today's confidence, at a glance — click a race to open it</div>
    <div class="overview-chart">{''.join(rows)}</div>"""


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
    odds = _odds_chip(stats)
    if odds:
        parts.append(odds)
    if not parts:
        return '<div class="stat-empty">No racecard stats collected for this runner yet.</div>'
    return f'<div class="stat-chips">{"".join(parts)}</div>'


def _odds_chip(stats: dict) -> str:
    """Real market odds (Smarkets, when a snapshot has been collected for
    this runner — see scripts/collect_smarkets_prices.py) or an honest
    'not yet available' chip. Never fabricated: a race with no real
    snapshot yet says so plainly rather than showing a blank or a guess."""
    mid = stats.get("midprice")
    back = stats.get("exchange_back")
    lay = stats.get("exchange_lay")
    if mid is not None:
        return f'<span class="stat-chip odds-chip">Odds {mid:.1f} (back {back:.1f} / lay {lay:.1f})</span>'
    return '<span class="stat-chip odds-chip odds-pending">Odds: not yet available</span>'


def find_market_favourite(stats: dict[str, dict]) -> tuple[str, float] | None:
    """The real horse with the shortest real back price (highest implied
    probability) among runners with an actual Smarkets snapshot. Returns
    None if no runner in this race has real odds yet — never guessed."""
    priced = [(h, s["exchange_back"]) for h, s in stats.items() if s.get("exchange_back")]
    if not priced:
        return None
    return min(priced, key=lambda hp: hp[1])  # shortest odds = favourite


def real_calibration_confidence(p: float) -> str:
    """Grounds a model probability in the REAL observed win rate for
    predictions that strong, from the current model's actual walk-forward
    backtest (REAL_CALIBRATION_BINS) — not an invented confidence score.
    A bin with under 150 real samples is flagged as too small to trust on
    its own, honestly, rather than presented as equally solid."""
    for low, high, predicted, actual, n in REAL_CALIBRATION_BINS:
        if low <= p < high or (high == REAL_CALIBRATION_BINS[-1][1] and p >= high):
            caveat = " (small real sample — treat cautiously)" if n < 150 else ""
            return (f"Predictions in this {_pct(low)}–{_pct(high)} range have historically won "
                    f"{_pct(actual)} of the time in real backtesting (n={n:,}){caveat}.")
    return "No real calibration data for this probability range."


def build_race_analysis(race: dict) -> str:
    """A deterministic, template-built explanation of the model's top
    pick — grounded ENTIRELY in real computed feature values (rating,
    form, draw, weight vs. the real field), never freeform LLM prose.

    **Why deterministic, not a live LLM call, given Jonathan explicitly
    asked for this to be 'good and reliable':** a template over real
    numbers is 100% reproducible and carries zero hallucination risk — it
    can only ever say what the real data actually shows. A live LLM call
    synthesizing prose could occasionally add a claim not actually
    grounded in the inputs, which is the opposite of reliable for a tool
    whose whole point is "never guessed, never fabricated" (the same
    discipline every real feature/backtest in this repo already follows).
    If this ever needs literal free-text narration, that's a real,
    separate decision — not the default here.

    Deliberately does NOT include draw_bias_edge (the 6th active feature)
    — that needs the full 57k-race historical table rebuilt, real but
    expensive to redo on every dashboard refresh, and it's a minor
    contributor at that. rating/form/draw/weight cover the intuitive,
    high-signal features.
    """
    m2, stats = race["model2"], race["stats"]
    if not m2:
        return ""
    top_horse = max(m2, key=m2.get)
    top_prob = m2[top_horse]

    runners = []
    for h, s in stats.items():
        hid = s.get("horse_id")
        if hid is None:
            continue
        runners.append(RunnerFeatureInput(
            horse_id=hid, age=s.get("age"), draw=s.get("draw"), weight_lbs=s.get("weight_lbs"),
            official_rating=s.get("official_rating"), recent_form=s.get("recent_form"),
        ))
    if not runners:
        return ""

    top_hid = stats.get(top_horse, {}).get("horse_id")
    rating = relative_official_rating(runners)
    draw_feats = draw_bias_features(runners)
    weight = relative_weight(runners)
    form_scores = {r.horse_id: form_score(r.recent_form) for r in runners}
    known_form = [v for v in form_scores.values() if v is not None]
    mean_form = sum(known_form) / len(known_form) if known_form else None

    sentences = []
    if top_hid in rating:
        edge = rating[top_hid]["rating_vs_mean"]
        if edge > 3:
            sentences.append(f"rated {edge:.0f} points above the field average")
        elif edge < -3:
            sentences.append(f"rated {abs(edge):.0f} points below the field average")
        else:
            sentences.append("rated close to the field average")
    else:
        sentences.append("a likely debutant with no official rating yet")

    fs = form_scores.get(top_hid)
    if fs is not None and mean_form is not None:
        if fs < mean_form - 0.5:
            sentences.append("in better recent form than its rivals")
        elif fs > mean_form + 0.5:
            sentences.append("in weaker recent form than its rivals")
        else:
            sentences.append("with recent form typical of this field")

    if top_hid in draw_feats:
        pct = draw_feats[top_hid]["draw_percentile"]
        if pct <= 0.25:
            sentences.append("drawn towards the low/rail side")
        elif pct >= 0.75:
            sentences.append("drawn towards the wide side")

    explanation = f"{top_horse} is " + ", ".join(sentences) + "."

    favourite = find_market_favourite(stats)
    if favourite:
        fav_name, fav_odds = favourite
        if fav_name == top_horse:
            explanation += f" The market also makes {top_horse} favourite (real odds {fav_odds:.1f})."
        else:
            explanation += (f" The market favourite is actually {fav_name} (real odds {fav_odds:.1f}) "
                             f"— the model disagrees with the market here.")
    else:
        explanation += " No real market odds collected for this race yet."

    confidence = real_calibration_confidence(top_prob)
    return f'<p>{explanation}</p><p class="analysis-confidence">{confidence}</p>'


def _ew_defaults(field_size: int) -> tuple[str, int]:
    """A real, commonly-used default UK each-way term for a given field
    size — NOT a universal rule (terms genuinely vary by bookmaker and by
    handicap vs non-handicap), which is why the calculator lets you change
    both values. Returns (fraction_str, places)."""
    if field_size >= 12:
        return "1/4", 4
    if field_size >= 8:
        return "1/5", 3
    if field_size >= 5:
        return "1/4", 2
    return "1/4", 1  # small fields — many bookmakers won't offer each-way at all; calc still works


def _bet_calculator_html(dom_id: str, odds: Optional[float], field_size: int) -> str:
    """A real, pure-arithmetic bet calculator — no server round-trip, just
    vanilla JS reading the stake/terms the viewer enters against the real
    odds already on the page. Only rendered when a real odds figure
    exists (never calculated against a guessed number)."""
    if odds is None:
        return ""
    frac_default, places_default = _ew_defaults(field_size)
    return f"""
        <details class="bet-calc" data-odds="{odds}" data-domid="{dom_id}">
          <summary>🧮 Bet calculator</summary>
          <div class="bet-calc-body">
            <label>Stake (£)
              <input type="number" class="bc-stake" id="{dom_id}-stake" value="10" min="0" step="1" oninput="calcBet('{dom_id}')">
            </label>
            <div class="bet-calc-result" id="{dom_id}-win-result"></div>
            <div class="bet-calc-ew">
              <span class="bet-calc-ew-label">Each-way terms:</span>
              <select id="{dom_id}-frac" onchange="calcBet('{dom_id}')">
                <option value="0.25" {"selected" if frac_default == "1/4" else ""}>1/4 odds</option>
                <option value="0.2" {"selected" if frac_default == "1/5" else ""}>1/5 odds</option>
              </select>
              <select id="{dom_id}-places" onchange="calcBet('{dom_id}')">
                {"".join(f'<option value="{p}" {"selected" if p == places_default else ""}>{p} place{"s" if p != 1 else ""}</option>' for p in (1, 2, 3, 4))}
              </select>
            </div>
            <div class="bet-calc-result" id="{dom_id}-ew-result"></div>
            <div class="bet-calc-note">Standard terms vary by bookmaker/race type — adjust if needed.
            Each-way stake is per side (£10 each-way = £20 total outlay).</div>
          </div>
        </details>"""


def render_race(race: dict, course_weather: dict[str, dict] | None = None) -> str:
    course_weather = course_weather or {}
    m1, m2, stats = race["model1"], race["model2"], race["stats"]
    horses = sorted(set(m1) | set(m2), key=lambda h: -m2.get(h, m1.get(h, 0.0)))

    m1_top = max(m1, key=m1.get) if m1 else None
    m2_top = max(m2, key=m2.get) if m2 else None
    agree = m1_top is not None and m1_top == m2_top

    field_size = len(horses)
    rows_html = []
    for h in horses:
        p2 = m2.get(h, 0.0)
        is_top = h == m2_top
        row_class = "runner-row top-pick" if is_top else "runner-row"

        m1_note = ""
        if not agree and h == m1_top:
            m1_note = f'<span class="m1-note">M1 prefers this one ({_pct(m1.get(h, 0.0))})</span>'

        h_stats = stats.get(h, {})
        horse_id = h_stats.get("horse_id")
        dom_id = f"bc-{race['race_id']}-{horse_id}" if horse_id is not None else None
        bet_calc_html = _bet_calculator_html(dom_id, h_stats.get("exchange_back"), field_size) if dom_id else ""

        rows_html.append(f"""
        <div class="{row_class}">
          <div class="runner-summary">
            <span class="runner-name">{h}{' <span class="top-badge">TOP PICK</span>' if is_top else ''}</span>
            <span class="runner-prob">
              {m1_note}
              {_bar_html(p2, 'var(--series-1)')}
              <span class="prob-value">{_pct(p2)}</span>
            </span>
          </div>
          {_stat_row(h_stats)}
          {bet_calc_html}
        </div>""")

    agree_badge = '<span class="agree-badge agree">MODELS AGREE</span>' if agree else '<span class="agree-badge disagree">MODELS DISAGREE</span>'

    w = course_weather.get(race["course_name"])
    weather_html = ""
    if w:
        weather_html = f"""
        <div class="race-weather">
          {w['precip_mm']:.1f}mm rain ({w['precip_prob']:.0f}%) · {w['temp_min']:.0f}-{w['temp_max']:.0f}°C ·
          {w['wind_kmh']:.0f} km/h wind · <strong>{_going_hint(w)}</strong>
        </div>"""

    analysis_html = build_race_analysis(race)

    return f"""
    <dialog class="race-card" id="race-{race['race_id']}">
      <div class="race-header">
        <div class="race-time">{race['off_time'].strftime('%H:%M') if hasattr(race['off_time'], 'strftime') else race['off_time']}</div>
        <div class="race-title">
          <div class="race-course">{race['course_name']}</div>
          <div class="race-name">{race['race_name']}</div>
        </div>
        {agree_badge}
        <button class="close-btn" onclick="this.closest('dialog').close()" aria-label="Close">✕</button>
      </div>
      {weather_html}
      <div class="race-analysis">{analysis_html}</div>
      <div class="runner-list">
        {''.join(rows_html)}
      </div>
    </dialog>"""


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


def render_days_tracked_dialog(dates: list[date]) -> str:
    """Popup listing every real tracked day — click a date to open that
    day's real race-by-race breakdown (render_day_history_dialog)."""
    if not dates:
        return ""
    rows = []
    for d in sorted(dates, reverse=True):
        dom_id = f"day-{d.isoformat()}"
        rows.append(f"""
        <button class="days-list-row" onclick="document.getElementById('days-tracked-dialog').close();
          document.getElementById('{dom_id}').showModal()">
          <span>{d.strftime('%A %d %B %Y')}</span>
          <span class="days-list-arrow">›</span>
        </button>""")
    return f"""
    <dialog class="help-dialog" id="days-tracked-dialog">
      <button class="close-btn" onclick="this.closest('dialog').close()" aria-label="Close">✕</button>
      <h2>Tracked days</h2>
      <div class="days-list">{''.join(rows)}</div>
    </dialog>"""


def render_day_history_dialog(day: date, races: list[dict]) -> str:
    """One real day's race-by-race breakdown: the real top pick, its
    real model probability, and its real settled outcome — WIN, PLACED
    (within that race's real each-way terms), LOSS, or PENDING if no
    real result has been collected yet. Never a guessed outcome."""
    badge_class = {"WIN": "win", "PLACED": "placed", "LOSS": "loss", "PENDING": "pending"}

    tally = {"WIN": 0, "PLACED": 0, "LOSS": 0, "PENDING": 0}
    for r in races:
        tally[r["status"]] += 1
    tally_html = f"""
    <div class="dayhist-tally">
      <span class="dayhist-tally-item dayhist-badge-win">{tally['WIN']} win{'s' if tally['WIN'] != 1 else ''}</span>
      <span class="dayhist-tally-item dayhist-badge-placed">{tally['PLACED']} placed</span>
      <span class="dayhist-tally-item dayhist-badge-loss">{tally['LOSS']} loss{'es' if tally['LOSS'] != 1 else ''}</span>
      {f'<span class="dayhist-tally-item dayhist-badge-pending">{tally["PENDING"]} pending</span>' if tally['PENDING'] else ''}
    </div>"""

    rows = []
    for r in sorted(races, key=lambda x: x["off_time"]):
        t = r["off_time"].strftime("%H:%M") if hasattr(r["off_time"], "strftime") else r["off_time"]
        status = r["status"]
        if r["finishing_position"] is not None:
            pos_text = f"finished {r['finishing_position']}"
        elif r["result_note"]:
            pos_text = r["result_note"]
        else:
            pos_text = "result pending"
        rows.append(f"""
        <div class="dayhist-row">
          <span class="dayhist-time">{t}</span>
          <div class="dayhist-main">
            <span class="dayhist-course">{r['course_name']} — {r['race_name']}</span>
            <span class="dayhist-horse">{r['horse_name']} · model p={_pct(r['model_probability'])} · {pos_text}</span>
          </div>
          <span class="dayhist-badge dayhist-badge-{badge_class[status]}">{status}</span>
        </div>""")
    dom_id = f"day-{day.isoformat()}"
    return f"""
    <dialog class="help-dialog dayhist-dialog" id="{dom_id}">
      <button class="close-btn" onclick="this.closest('dialog').close()" aria-label="Close">✕</button>
      <h2>{day.strftime('%A %d %B %Y')}</h2>
      {tally_html}
      <div class="dayhist-list">{''.join(rows)}</div>
    </dialog>"""


def render_track_record(summaries: list[dict], race_history: dict[date, list[dict]] | None = None) -> str:
    """Real, persisted day-by-day track record — cumulative hit rate and
    P&L across every real settled day, plus a per-day breakdown, built
    from `daily_summary` (see scripts/generate_daily_summary.py). Empty
    entirely (never a placeholder chart) until at least one day has real
    settled results. `race_history` (see load_race_history) feeds the
    per-day click-through popups — omitted, those dialogs are simply
    not rendered rather than showing a broken link."""
    race_history = race_history or {}
    if not summaries:
        return """
    <div class="section-label">Track record</div>
    <div class="track-record-empty">No settled results yet — this section fills in once
      scripts/collect_race_results.py and scripts/generate_daily_summary.py have run
      for at least one real race day.</div>"""

    days = len(summaries)
    races_settled = sum(s["races_settled"] for s in summaries)
    top_pick_wins = sum(s["top_pick_wins"] for s in summaries)
    top_pick_placed = sum(s["top_pick_placed"] for s in summaries)
    favourite_wins = sum(s["favourite_wins"] for s in summaries)
    win_profit = sum(s["win_profit"] for s in summaries)
    win_stake = sum(s["win_stake_total"] for s in summaries)
    ew_profit = sum(s["ew_profit"] for s in summaries)
    ew_stake = sum(s["ew_stake_total"] for s in summaries)

    hit_rate = top_pick_wins / races_settled if races_settled else 0.0
    fav_rate = favourite_wins / races_settled if races_settled else 0.0
    win_roi = win_profit / win_stake if win_stake else 0.0
    ew_roi = ew_profit / ew_stake if ew_stake else 0.0

    tiles = f"""
    <div class="stats-row">
      <div class="stat-tile stat-tile-clickable" onclick="document.getElementById('days-tracked-dialog').showModal()">
        <div class="stat-label">Days tracked</div>
        <div class="stat-value">{days}</div>
        <div class="stat-sub">{races_settled} real settled races — tap to view by day</div>
      </div>
      <div class="stat-tile">
        <div class="stat-label">Top-pick hit rate (real)</div>
        <div class="stat-value">{_pct(hit_rate)}</div>
        <div class="stat-sub">vs {_pct(fav_rate)} for the market favourite, this period</div>
      </div>
      <div class="stat-tile">
        <div class="stat-label">£1 win P&amp;L</div>
        <div class="stat-value" style="color:{'var(--good)' if win_profit >= 0 else 'var(--bad)'}">£{win_profit:+.2f}</div>
        <div class="stat-sub">{_pct(win_roi)} ROI on £{win_stake:.0f} staked</div>
      </div>
      <div class="stat-tile">
        <div class="stat-label">£2 each-way P&amp;L</div>
        <div class="stat-value" style="color:{'var(--good)' if ew_profit >= 0 else 'var(--bad)'}">£{ew_profit:+.2f}</div>
        <div class="stat-sub">{_pct(ew_roi)} ROI on £{ew_stake:.0f} staked</div>
      </div>
    </div>"""

    caveat = ""
    if days < 20:
        caveat = (f'<div class="track-record-caveat">Only {days} real day(s) of live results so far — '
                  f'far too small a sample to judge against the {_pct(0.232)} real backtested hit rate or the '
                  f'{_pct(0.333)} market-favourite rate. Shown as-is, not smoothed or projected.</div>')

    day_rows = []
    for s in summaries:
        d_hit = s["top_pick_wins"] / s["races_settled"] if s["races_settled"] else 0.0
        width = max(2, round(d_hit * 100))
        pnl = s["win_profit"]
        pnl_color = "var(--good)" if pnl >= 0 else "var(--bad)"
        day_dom_id = f"day-{s['race_date'].isoformat()}"
        day_rows.append(f"""
        <div class="trackrow" onclick="document.getElementById('{day_dom_id}').showModal()">
          <span class="trackrow-date">{s['race_date'].strftime('%d %b')}</span>
          <span class="trackrow-pct">{_pct(d_hit)}</span>
          <div class="trackrow-bar-wrap">
            <div class="trackrow-bar-track"><div class="trackrow-bar-fill" style="width:{width}%"></div></div>
            <span class="trackrow-pnl" style="color:{pnl_color}">£{pnl:+.2f}</span>
          </div>
        </div>""")

    dates = [s["race_date"] for s in summaries]
    day_dialogs = "".join(
        render_day_history_dialog(d, race_history[d]) for d in dates if d in race_history
    )
    return f"""
    <div class="section-label">Track record — real settled results, day by day</div>
    {tiles}
    {caveat}
    <div class="track-record-chart">{''.join(day_rows)}</div>
    {render_days_tracked_dialog(dates)}
    {day_dialogs}"""


# Real backtested validation-fold numbers from RL-012 (docs/RESEARCH_LAB.md,
# 2026-09-11) — the top pick's own probability, bucketed, actual win rate on
# 10,207 real validation races never touched during discovery. Shown here as
# a fixed reference alongside the live numbers below, NOT recomputed here.
RL012_BACKTEST_VALIDATION = [
    (0.0, 0.15, 0.141, 1509),
    (0.15, 0.20, 0.184, 2570),
    (0.20, 0.25, 0.213, 2204),
    (0.25, 0.30, 0.275, 1488),
    (0.30, 0.35, 0.298, 995),
    (0.35, 0.40, 0.357, 589),
    (0.40, 0.45, 0.394, 376),
    (0.45, 0.50, 0.450, 202),
    (0.50, 1.01, 0.504, 274),
]


def render_live_calibration(race_history: dict[date, list[dict]]) -> str:
    """Real, live version of RL-012's top-pick calibration analysis —
    buckets every real settled top pick's own model probability (across
    every tracked day, same bucket edges as
    scripts/analyze_top_pick_calibration.py) and shows it next to the
    real backtested validation numbers (RL012_BACKTEST_VALIDATION) for
    comparison. PENDING races are excluded — never counted as a loss.
    Empty entirely until at least one real settled result exists.
    RL-012's own correction attempt did NOT survive validation (tested
    and rejected — see docs/RESEARCH_LAB.md), so this is purely
    observational: nothing here changes any displayed or used
    probability."""
    records = []
    for races in race_history.values():
        for r in races:
            if r["status"] == "PENDING":
                continue
            records.append((r["model_probability"], r["status"] == "WIN"))
    if not records:
        return ""

    live_bins = summarise_calibration_bins(records)
    backtest_by_range = {(round(low, 2), round(high, 2)): actual for low, high, actual, _n in RL012_BACKTEST_VALIDATION}

    rows = []
    for b in live_bins:
        key = (round(b["low"], 2), round(b["high"], 2))
        bt_actual = backtest_by_range.get(key)
        small_note = '<span class="calib-flag">small live sample</span>' if b["n"] < 30 else ""
        rows.append(f"""
        <div class="calib-row">
          <span class="calib-range">{b['low']*100:.0f}–{b['high']*100:.0f}%</span>
          <span class="calib-live">{_pct(b['actual'])} live (n={b['n']})</span>
          <span class="calib-backtest">{_pct(bt_actual) if bt_actual is not None else '—'} backtested</span>
          {small_note}
        </div>""")

    return f"""
    <div class="section-label">Confidence calibration — live vs real backtest (RL-012)</div>
    <div class="calib-note">Watching whether real live results confirm the real backtested
      pattern (a top pick shown above ~40% tends to overstate its real chances) — live sample
      sizes are still tiny, so treat every row here as an early read, not a conclusion, until
      many more real days accumulate. Purely observational: nothing here changes any
      probability shown elsewhere on this page.</div>
    <div class="calib-chart">{''.join(rows)}</div>"""


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


def render_html(race_date: date, races: list[dict], course_weather: dict[str, dict] | None = None,
                 daily_summaries: list[dict] | None = None,
                 race_history: dict[date, list[dict]] | None = None) -> str:
    course_weather = course_weather or {}
    daily_summaries = daily_summaries or []
    race_history = race_history or {}
    race_dialogs = "".join(render_race(r, course_weather) for r in races)
    empty_message = '' if races else '<p class="empty">No predictions locked for this date yet.</p>'

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
    --bad: #d64545;
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
      --bad: #e5636b;
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
    --bad: #e5636b;
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
  .stat-tile-clickable {{ cursor: pointer; }}
  .stat-tile-clickable:hover {{ border-color: var(--series-1); }}
  .race-card {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px 18px; margin-bottom: 14px;
  }}
  .race-header {{ display: flex; flex-wrap: wrap; align-items: flex-start; gap: 10px 14px; margin-bottom: 12px; }}
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
  .runner-row {{ border-top: 1px solid var(--border); }}
  .runner-row:first-child {{ border-top: none; }}
  .runner-row .runner-summary {{
    display: flex; align-items: center; justify-content: space-between; gap: 12px;
    padding: 8px 6px 0;
  }}
  .runner-row.top-pick {{ background: color-mix(in srgb, var(--series-1) 6%, transparent); border-radius: 6px; }}
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

  .bet-calc {{
    margin: 0 6px 12px; border: 1px solid var(--border); border-radius: 8px;
    background: var(--surface-2);
  }}
  .bet-calc summary {{
    padding: 8px 12px; font-size: 12px; font-weight: 600; cursor: pointer;
    list-style: none; color: var(--text-secondary);
  }}
  .bet-calc summary::-webkit-details-marker {{ display: none; }}
  .bet-calc-body {{ padding: 4px 12px 12px; }}
  .bet-calc-body label {{
    display: flex; align-items: center; gap: 8px; font-size: 12px;
    color: var(--text-secondary); margin-bottom: 8px;
  }}
  .bet-calc-body input[type="number"] {{
    width: 80px; padding: 5px 8px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--surface-1); color: var(--text-primary); font-size: 13px;
  }}
  .bet-calc-result {{
    font-size: 12px; color: var(--text-primary); background: var(--surface-1);
    border-radius: 6px; padding: 8px 10px; margin-bottom: 8px; line-height: 1.6;
  }}
  .bet-calc-result .bc-row {{ display: flex; justify-content: space-between; }}
  .bet-calc-result .bc-label {{ color: var(--text-muted); }}
  .bet-calc-ew {{ display: flex; align-items: center; gap: 6px; font-size: 12px; margin-bottom: 8px; flex-wrap: wrap; }}
  .bet-calc-ew-label {{ color: var(--text-muted); }}
  .bet-calc-body select {{
    padding: 5px 6px; border-radius: 6px; border: 1px solid var(--border);
    background: var(--surface-1); color: var(--text-primary); font-size: 12px;
  }}
  .bet-calc-note {{ font-size: 10.5px; color: var(--text-muted); line-height: 1.4; }}
  .empty {{ color: var(--text-muted); }}
  footer {{ margin-top: 32px; font-size: 11px; color: var(--text-muted); }}

  .top-bar {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }}
  .top-bar-buttons {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .theme-toggle {{
    background: var(--surface-1); border: 1px solid var(--border); color: var(--text-secondary);
    border-radius: 20px; padding: 6px 14px; font-size: 12px; cursor: pointer;
    display: flex; align-items: center; gap: 6px; white-space: nowrap;
  }}
  .theme-toggle:hover {{ border-color: var(--series-1); color: var(--text-primary); }}

  dialog.help-dialog {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 14px;
    padding: 24px 26px; margin: auto; max-width: 520px; width: calc(100% - 48px);
    color: var(--text-primary); box-shadow: 0 20px 60px rgba(0,0,0,0.35); position: relative;
  }}
  dialog.help-dialog::backdrop {{ background: rgba(0,0,0,0.55); backdrop-filter: blur(2px); }}
  dialog.help-dialog h2 {{ font-size: 17px; margin: 0 0 12px; }}
  dialog.help-dialog h3 {{ font-size: 13px; margin: 16px 0 6px; color: var(--series-1); }}
  dialog.help-dialog p, dialog.help-dialog li {{ font-size: 13px; color: var(--text-secondary); line-height: 1.5; }}
  dialog.help-dialog ul {{ margin: 6px 0; padding-left: 18px; }}

  .days-list {{ display: flex; flex-direction: column; }}
  .days-list-row {{
    display: flex; justify-content: space-between; align-items: center;
    width: 100%; text-align: left; background: none; border: none;
    border-top: 1px solid var(--border); padding: 12px 4px; font-size: 13px;
    color: var(--text-primary); cursor: pointer; font-family: inherit;
  }}
  .days-list-row:first-child {{ border-top: none; }}
  .days-list-row:hover, .days-list-row:active {{ color: var(--series-1); }}
  .days-list-arrow {{ color: var(--text-muted); font-size: 16px; }}

  dialog.dayhist-dialog {{ max-width: 600px; }}
  .dayhist-list {{ display: flex; flex-direction: column; }}
  .dayhist-row {{
    display: grid; grid-template-columns: 44px 1fr auto;
    align-items: center; column-gap: 10px;
    padding: 10px 4px; border-top: 1px solid var(--border); font-size: 12px;
  }}
  .dayhist-row:first-child {{ border-top: none; }}
  .dayhist-time {{ color: var(--series-1); font-weight: 600; }}
  .dayhist-main {{ display: flex; flex-direction: column; gap: 2px; overflow: hidden; }}
  .dayhist-course {{ color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .dayhist-horse {{ color: var(--text-muted); font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .dayhist-badge {{
    font-size: 10px; font-weight: 700; letter-spacing: .03em; padding: 4px 8px;
    border-radius: 20px; white-space: nowrap;
  }}
  .dayhist-badge-win {{ background: color-mix(in srgb, var(--good) 18%, transparent); color: var(--good); }}
  .dayhist-badge-placed {{ background: color-mix(in srgb, var(--warn) 18%, transparent); color: var(--warn); }}
  .dayhist-badge-loss {{ background: color-mix(in srgb, var(--bad) 18%, transparent); color: var(--bad); }}
  .dayhist-badge-pending {{ background: var(--surface-2); color: var(--text-muted); }}

  .dayhist-tally {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }}
  .dayhist-tally-item {{
    font-size: 12px; font-weight: 700; padding: 5px 12px; border-radius: 20px;
  }}

  .race-weather {{
    font-size: 11px; color: var(--text-secondary); background: var(--surface-2);
    border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;
  }}
  .odds-chip {{ color: var(--good); font-weight: 600; }}
  .odds-chip.odds-pending {{ color: var(--text-muted); font-weight: 400; font-style: italic; }}

  .race-analysis {{
    background: color-mix(in srgb, var(--series-1) 8%, transparent);
    border: 1px solid color-mix(in srgb, var(--series-1) 25%, transparent);
    border-radius: 10px; padding: 12px 14px; margin-bottom: 14px;
  }}
  .race-analysis p {{ margin: 0 0 6px; font-size: 12.5px; color: var(--text-primary); line-height: 1.5; }}
  .race-analysis p:last-child {{ margin-bottom: 0; }}
  .analysis-confidence {{ color: var(--text-secondary) !important; font-size: 11px !important; }}

  .section-label {{
    font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em;
    color: var(--text-muted); margin: 28px 0 10px;
  }}
  .weather-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin-bottom: 8px; }}
  .weather-card {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px;
  }}
  .weather-course {{ font-weight: 600; font-size: 13px; margin-bottom: 6px; }}
  .weather-figures {{ display: flex; flex-direction: column; gap: 2px; font-size: 11px; color: var(--text-secondary); }}
  .weather-going {{ font-size: 11px; color: var(--series-1); font-weight: 600; margin-top: 6px; }}

  .overview-chart {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 6px 14px; margin-bottom: 8px;
  }}
  /* Mobile-first: stacked two-line layout by default */
  .overview-row {{
    display: grid;
    grid-template-columns: 44px 1fr auto;
    grid-template-areas: "time course pct" "bar bar bar";
    align-items: center; column-gap: 8px; row-gap: 6px;
    padding: 10px 8px; border-top: 1px solid var(--border); font-size: 12px;
    cursor: pointer; border-radius: 6px;
  }}
  .overview-row:first-child {{ border-top: none; }}
  .overview-row:hover, .overview-row:active {{ background: var(--surface-2); }}
  .overview-time {{ grid-area: time; color: var(--series-1); font-weight: 600; }}
  .overview-course {{ grid-area: course; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .overview-pct {{ grid-area: pct; text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}
  .overview-bar-wrap {{ grid-area: bar; display: flex; align-items: center; gap: 8px; }}
  .overview-bar-track {{ flex: 1; height: 8px; background: var(--surface-2); border-radius: 4px; overflow: hidden; }}
  .overview-bar-fill {{ height: 100%; border-radius: 4px; background: var(--series-1); }}
  .overview-horse {{ font-size: 11px; color: var(--text-muted); white-space: nowrap; max-width: 45%; overflow: hidden; text-overflow: ellipsis; }}

  /* Wider screens: collapse to one row */
  @media (min-width: 480px) {{
    .overview-row {{
      grid-template-columns: 46px 90px 1fr 120px 46px;
      grid-template-areas: "time course bar horse pct";
      row-gap: 0;
    }}
    .overview-bar-wrap {{ display: contents; }}
    .overview-bar-track {{ grid-area: bar; }}
    .overview-horse {{ grid-area: horse; max-width: none; }}
  }}

  .track-record-empty {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 14px; margin-bottom: 20px; font-size: 12px; color: var(--text-muted);
  }}
  .track-record-caveat {{
    font-size: 11px; color: var(--text-muted); margin: 4px 0 10px;
  }}
  .track-record-chart {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 6px 14px; margin-bottom: 20px;
  }}
  /* Mobile-first: stacked two-line layout, same pattern as .overview-row */
  .trackrow {{
    display: grid;
    grid-template-columns: 52px 1fr;
    grid-template-areas: "date pct" "bar bar";
    align-items: center; column-gap: 8px; row-gap: 6px;
    padding: 10px 8px; border-top: 1px solid var(--border); font-size: 12px;
    cursor: pointer; border-radius: 6px;
  }}
  .trackrow:first-child {{ border-top: none; }}
  .trackrow:hover, .trackrow:active {{ background: var(--surface-2); }}
  .trackrow-date {{ grid-area: date; color: var(--text-secondary); font-weight: 600; }}
  .trackrow-pct {{ grid-area: pct; text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}
  .trackrow-bar-wrap {{ grid-area: bar; display: flex; align-items: center; gap: 8px; }}
  .trackrow-bar-track {{ flex: 1; height: 8px; background: var(--surface-2); border-radius: 4px; overflow: hidden; }}
  .trackrow-bar-fill {{ height: 100%; border-radius: 4px; background: var(--series-1); }}
  .trackrow-pnl {{ font-size: 11px; font-weight: 600; white-space: nowrap; font-variant-numeric: tabular-nums; }}

  @media (min-width: 480px) {{
    .trackrow {{
      grid-template-columns: 60px 1fr 80px 70px;
      grid-template-areas: "date bar pnl pct";
      row-gap: 0;
    }}
    .trackrow-bar-wrap {{ display: contents; }}
    .trackrow-bar-track {{ grid-area: bar; }}
    .trackrow-pnl {{ grid-area: pnl; text-align: right; }}
  }}

  .calib-note {{
    font-size: 11px; color: var(--text-muted); margin-bottom: 10px; line-height: 1.5;
  }}
  .calib-chart {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 6px 14px; margin-bottom: 20px;
  }}
  .calib-row {{
    display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px;
    padding: 10px 8px; border-top: 1px solid var(--border); font-size: 12px;
  }}
  .calib-row:first-child {{ border-top: none; }}
  .calib-range {{ color: var(--text-secondary); font-weight: 600; min-width: 70px; }}
  .calib-live {{ color: var(--series-1); font-variant-numeric: tabular-nums; }}
  .calib-backtest {{ color: var(--text-muted); font-variant-numeric: tabular-nums; }}
  .calib-flag {{
    font-size: 10px; font-weight: 700; color: var(--warn);
    background: color-mix(in srgb, var(--warn) 18%, transparent);
    padding: 3px 8px; border-radius: 20px;
  }}

  dialog.race-card {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 14px;
    padding: 20px 22px; margin: auto; max-width: 640px; width: calc(100% - 48px);
    color: var(--text-primary); box-shadow: 0 20px 60px rgba(0,0,0,0.35);
  }}
  dialog.race-card::backdrop {{ background: rgba(0,0,0,0.55); backdrop-filter: blur(2px); }}
  dialog.race-card .race-header {{ position: relative; }}
  .close-btn {{
    position: absolute; top: -6px; right: -6px; background: none; border: none;
    color: var(--text-muted); font-size: 16px; cursor: pointer; padding: 4px 8px;
  }}
  .close-btn:hover {{ color: var(--text-primary); }}
</style>
</head>
<body>
<div class="wrap">
  <div class="top-bar">
    <div>
      <h1>Silent Edge Zero</h1>
      <div class="subtitle">Live predictions — {race_date.strftime('%A %-d %B %Y')}</div>
    </div>
    <div class="top-bar-buttons">
      <button class="theme-toggle" onclick="document.getElementById('help-dialog').showModal()">❓ What do OR / Form mean?</button>
      <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()">🌓 Toggle theme</button>
    </div>
  </div>

  <dialog class="help-dialog" id="help-dialog">
    <button class="close-btn" onclick="this.closest('dialog').close()" aria-label="Close">✕</button>
    <h2>Reading the stats</h2>
    <h3>OR — Official Rating</h3>
    <p>A number the British Horseracing Authority assigns to every horse based on its past
    performances — the official measure of how good it is, and what handicap races use to
    decide how much weight each horse carries. <strong>Higher OR = a faster/better-rated horse.</strong>
    A horse with no OR yet (often a first-time-out debutant) shows no OR chip at all — never
    guessed.</p>
    <p><strong>The scale is open-ended, not capped at 100</strong> — it goes as high as a horse's
    real ability:</p>
    <ul>
      <li><strong>40–90</strong> — most ordinary handicappers</li>
      <li><strong>90–110</strong> — good handicappers / minor stakes horses</li>
      <li><strong>110–130</strong> — Group/Graded class</li>
      <li><strong>130–140+</strong> — elite Flat horses (top milers/sprinters)</li>
      <li><strong>150–170+</strong> — the best National Hunt (jumps) chasers/hurdlers can rate even higher</li>
    </ul>
    <p>There's no single "average" — it depends entirely on the class of race. A maiden
    hurdle will mostly show ratings in the 80s–110s; a Group 1 will be 120+.</p>
    <h3>Form — recent finishing positions</h3>
    <p>Read <strong>left to right, oldest race first</strong> — so the <strong>last character
    is the horse's most recent run</strong>. Each character is one race:</p>
    <ul>
      <li><strong>1-9</strong> — the finishing position (1st, 2nd, 3rd...)</li>
      <li><strong>0</strong> — finished 10th or worse</li>
      <li><strong>-</strong> — a break between seasons</li>
      <li><strong>F / P / U / O / R / S / B</strong> — did not complete: Fell, Pulled up,
        Unseated rider, refused (O), Ran out, Slipped up, Brought down</li>
    </ul>
    <p>Example: <strong>"3-4333"</strong> → 3rd, <em>(season break)</em>, 4th, 3rd, 3rd, 3rd
    — the horse's LAST run (right-most) was a 3rd.</p>
    <h3>Odds</h3>
    <p>Real live back/lay prices from the Smarkets exchange, when a snapshot has been
    collected for that runner (see docs — this is forward-collecting only, so early races
    or races before the collector started running may show "not yet available", never a
    guessed number).</p>
    <h3>Race analysis</h3>
    <p>A plain-English summary of why the model backs its top pick — built entirely from
    real computed numbers (rating vs. the field, recent form, draw), not free-text AI
    generation. This is deliberate: a template over real data can only ever say what the
    numbers actually show, with zero risk of inventing a claim. The confidence line is the
    REAL observed win rate for predictions this strong, from actual backtesting — not a new
    made-up score. Model 2 has a genuine, tested ~23% chance of picking the actual
    winner (vs. 33.3% for just backing the market favourite) — this analysis explains the
    reasoning honestly, it doesn't make the underlying prediction better than that.</p>
  </dialog>

  <div class="disclaimer">
    Not a tipster service. These are research predictions from a walk-forward-validated
    model that has NOT beaten the market baseline in real backtesting (see stats below) —
    shown as research output, not betting advice. The probability shown is Model 2
    (gradient boosting, the better-backtested of the two models built) — Model 1's pick is
    only flagged when it disagrees. Real hit rate (RL-010): picks the actual winner ~23.2%
    of races, vs 11.8% for a random guess, vs 33.3% for the market favourite alone.
  </div>

  {render_summary(races)}

  <div class="stats-row">
    {render_backtest_context()}
  </div>

  {render_track_record(daily_summaries, race_history)}

  {render_live_calibration(race_history)}

  {render_weather(course_weather)}

  {render_overview_chart(races)}
  {empty_message}

  <footer>Generated by scripts/generate_dashboard.py — real, locked predictions only, never fabricated.</footer>
</div>

{race_dialogs}
<script>
  function applyTheme(theme) {{
    if (theme) {{ document.documentElement.setAttribute('data-theme', theme); }}
    else {{ document.documentElement.removeAttribute('data-theme'); }}
  }}
  function toggleTheme() {{
    var current = document.documentElement.getAttribute('data-theme');
    var systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    var effectiveIsDark = current ? current === 'dark' : systemDark;
    var next = effectiveIsDark ? 'light' : 'dark';
    applyTheme(next);
    try {{ localStorage.setItem('sez-theme', next); }} catch (e) {{}}
  }}
  try {{
    var saved = localStorage.getItem('sez-theme');
    if (saved) applyTheme(saved);
  }} catch (e) {{}}
  document.querySelectorAll('dialog.race-card, dialog.help-dialog').forEach(function(d) {{
    d.addEventListener('click', function(e) {{ if (e.target === d) d.close(); }});
  }});

  // Real bet calculator — pure client-side arithmetic on the real odds
  // already rendered on the page. No server round-trip, no external data.
  function calcBet(domId) {{
    var container = document.getElementById(domId + '-stake').closest('.bet-calc');
    var odds = parseFloat(container.dataset.odds);
    var stake = parseFloat(document.getElementById(domId + '-stake').value) || 0;
    var frac = parseFloat(document.getElementById(domId + '-frac').value);

    var winResult = document.getElementById(domId + '-win-result');
    var ewResult = document.getElementById(domId + '-ew-result');

    var winReturn = stake * odds;
    var winProfit = winReturn - stake;
    winResult.innerHTML =
      '<div class="bc-row"><span class="bc-label">Win bet, £' + stake.toFixed(2) + ' stake</span>' +
      '<span>Returns £' + winReturn.toFixed(2) + ' (profit £' + winProfit.toFixed(2) + ')</span></div>';

    var placeOdds = 1 + (odds - 1) * frac;
    var placeReturn = stake * placeOdds;
    var totalOutlay = stake * 2;
    var ifWins = winReturn + placeReturn;
    var ifPlaces = placeReturn;
    ewResult.innerHTML =
      '<div class="bc-row"><span class="bc-label">Each-way, £' + stake.toFixed(2) + ' each side (£' + totalOutlay.toFixed(2) + ' total)</span></div>' +
      '<div class="bc-row"><span class="bc-label">If it wins</span><span>Returns £' + ifWins.toFixed(2) + ' (profit £' + (ifWins - totalOutlay).toFixed(2) + ')</span></div>' +
      '<div class="bc-row"><span class="bc-label">If it places only</span><span>Returns £' + ifPlaces.toFixed(2) + ' (profit £' + (ifPlaces - totalOutlay).toFixed(2) + ')</span></div>' +
      '<div class="bc-row"><span class="bc-label">If it neither wins nor places</span><span>Returns £0.00 (loses £' + totalOutlay.toFixed(2) + ')</span></div>';
  }}
  document.querySelectorAll('.bet-calc').forEach(function(el) {{
    calcBet(el.dataset.domid);
  }});
</script>
{f'<script data-goatcounter="https://{GOATCOUNTER_SITE_CODE}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>' if GOATCOUNTER_SITE_CODE else ''}
</body>
</html>"""


def main():
    race_date_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    race_date = date.fromisoformat(race_date_str)

    conn = psycopg2.connect(dbname="silent_edge_zero")
    races = load_predictions(conn, race_date)
    daily_summaries = load_daily_summaries(conn)
    race_history = load_race_history(conn, [s["race_date"] for s in daily_summaries])
    conn.close()

    course_names = {r["course_name"] for r in races}
    course_weather = fetch_course_weather(course_names, race_date)

    html = render_html(race_date, races, course_weather, daily_summaries, race_history)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {OUTPUT_PATH} ({len(races)} races).")


if __name__ == "__main__":
    main()
