"""
Trainer Intelligence Lab, Hypothesis C: observable hidden improvement —
Silent Edge Zero V2 brief, Section 12C. Completely separate from the live
prediction algorithm.

**Real, honest data-availability correction, checked before writing this
module:** the brief's suggested candidate variables include "improved
speed figures", "strong late sectionals", and "finishing speed" — none of
these exist anywhere in this project's schema (confirmed: `runner_result`
has no finishing-time or sectional-time column at all, and no paid speed-
figure source has been purchased — see docs/FUTURE_PAID_UPGRADES.md).
Per the brief's own Section 13 instruction ("if historical information is
unavailable, mark it unavailable... never estimate and present as
official"), this module does NOT attempt those variables. It uses
candidates that genuinely exist and are well-populated:
`distance_beaten` (94.6% coverage), `equipment` (44%), and
`days_since_last_run` (85%) — real, observable, lawful public information,
exactly as the brief requires ("use observable, lawful public
information").

**Horse identity by NAME**, same real reason and same convention as
src/research/trainer_intelligence_a.py — sidesteps the unresolved
horse.id dedup bug for career-trend purposes.

**Market benchmark:** real starting_price, de-vigged per race, same as
Hypothesis A — this hypothesis needs the full historical bootstrap
(2023-present), which has no live exchange market_snapshot coverage.
"""
from datetime import date as date_type
from typing import Optional

from src.analysis.edge_metrics import normalized_market_probabilities
from scripts.generate_eod_report import VOID_RESULT_CODES

RETURN_FROM_BREAK_DAYS = 60


def load_horse_career_runs_with_equipment(conn, since: Optional[date_type] = None) -> dict[str, list[dict]]:
    """Real, flat per-runner history grouped by horse name, chronological
    within each horse — same shape as trainer_intelligence_a.py's loader,
    plus equipment and days_since_last_run, and NOT requiring a real
    official_rating (Hypothesis C doesn't need it)."""
    cur = conn.cursor()
    params: list = []
    where = "1=1"
    if since is not None:
        where += " AND r.race_date >= %s"
        params.append(since)
    cur.execute(
        f"""
        SELECT h.name, r.id, r.race_date, r.race_class, r.distance_yards, r.going,
               rs.equipment, rs.days_since_last_run,
               rr.finishing_position, rr.result_note, rr.distance_beaten, rr.starting_price
        FROM runner_snapshot rs
        JOIN horse h ON h.id = rs.horse_id
        JOIN race r ON r.id = rs.race_id
        LEFT JOIN runner_result rr ON rr.race_id = rs.race_id AND rr.horse_id = rs.horse_id
        WHERE {where}
        ORDER BY h.name, r.race_date
        """,
        params,
    )
    rows = cur.fetchall()
    cur.close()

    by_horse: dict[str, list[dict]] = {}
    for (name, race_id, race_date, race_class, distance_yards, going, equipment,
         days_since_last_run, finishing_position, result_note, distance_beaten, starting_price) in rows:
        by_horse.setdefault(name, []).append({
            "race_id": race_id, "race_date": race_date, "race_class": race_class,
            "distance_yards": distance_yards, "going": going, "equipment": equipment,
            "days_since_last_run": days_since_last_run, "finishing_position": finishing_position,
            "result_note": result_note,
            "distance_beaten": float(distance_beaten) if distance_beaten is not None else None,
            "starting_price": float(starting_price) if starting_price is not None else None,
        })
    return by_horse


def compute_improvement_features(runs_by_horse: dict[str, list[dict]]) -> list[dict]:
    """Pure function (no DB). For every run with at least 2 strictly
    earlier runs (so a real two-point beaten-length trend can be formed),
    computes:
    - improving_beaten_length_trend: real, both prior runs finished
      (distance_beaten known for both) AND the most recent prior run's
      distance_beaten < the one before it (finished closer last time)
    - equipment_change: real, current run's equipment is set and differs
      from the most recent prior run's equipment (a genuine first-time-
      with-this-kit signal; two runs both with no recorded equipment are
      NOT a "change" — never inferred from missing data)
    - return_from_break: days_since_last_run >= RETURN_FROM_BREAK_DAYS

    A run missing the two prior beaten-length data points gets
    improving_beaten_length_trend = None (unknown, not False — never
    conflated with "confirmed not improving")."""
    features = []
    for horse_name, runs in runs_by_horse.items():
        for i in range(2, len(runs)):
            current = runs[i]
            prior_1 = runs[i - 1]
            prior_2 = runs[i - 2]

            improving_trend = None
            if prior_1["distance_beaten"] is not None and prior_2["distance_beaten"] is not None:
                improving_trend = prior_1["distance_beaten"] < prior_2["distance_beaten"]

            equipment_change = (
                current["equipment"] is not None and current["equipment"] != ""
                and current["equipment"] != prior_1["equipment"]
            )
            return_from_break = (
                current["days_since_last_run"] is not None
                and current["days_since_last_run"] >= RETURN_FROM_BREAK_DAYS
            )

            features.append({
                "horse_name": horse_name,
                "race_id": current["race_id"],
                "race_date": current["race_date"],
                "improving_beaten_length_trend": improving_trend,
                "equipment_change": equipment_change,
                "return_from_break": return_from_break,
                "finishing_position": current["finishing_position"],
                "result_note": current["result_note"],
                "starting_price": current["starting_price"],
            })
    return features


def _outcome(feature: dict) -> Optional[int]:
    if feature["finishing_position"] == 1:
        return 1
    if feature["finishing_position"] is not None:
        return 0
    if feature["result_note"] is None:
        return None
    if feature["result_note"] in VOID_RESULT_CODES:
        return None
    return 0


def test_hidden_improvement_hypothesis(features: list[dict]) -> dict:
    """QUALIFYING: a real improving beaten-length trend AND (a real
    equipment change OR a real return from a break >= RETURN_FROM_BREAK_DAYS)
    — the brief's own "observable hidden improvement" combination. CONTROL:
    everyone else with a known trend value (runs where the trend itself is
    unknown are excluded from both groups entirely, never defaulted into
    CONTROL). Compared against the market's own de-vigged starting-price
    implied probability, same discipline as Hypothesis A/B."""
    from src.research.probability_bands import wilson_score_interval

    by_race: dict[int, list[dict]] = {}
    for f in features:
        if f["improving_beaten_length_trend"] is None:
            continue  # genuinely unknown -- excluded from both groups
        by_race.setdefault(f["race_id"], []).append(f)

    def _summary(rows: list[dict]) -> Optional[dict]:
        n = len(rows)
        if n == 0:
            return None
        actual_wins = sum(r["outcome"] for r in rows)
        expected_wins = sum(r["market_probability"] for r in rows)
        ci = wilson_score_interval(actual_wins, n)
        return {
            "n": n, "actual_wins": actual_wins, "actual_win_rate": round(actual_wins / n, 4),
            "expected_wins_market": round(expected_wins, 2),
            "diff_actual_minus_expected_market": round(actual_wins - expected_wins, 2),
            "win_rate_confidence_interval": [round(ci[0], 4), round(ci[1], 4)] if ci else None,
            "small_sample": n < 20,
        }

    qualifying_rows, control_rows = [], []
    n_races_excluded_no_devig = 0
    for race_id, race_features in by_race.items():
        odds_by_index = {i: f["starting_price"] for i, f in enumerate(race_features) if f["starting_price"] is not None}
        market_probs = normalized_market_probabilities(odds_by_index)
        if not market_probs:
            n_races_excluded_no_devig += 1
            continue
        for i, f in enumerate(race_features):
            outcome = _outcome(f)
            market_prob = market_probs.get(i)
            if outcome is None or market_prob is None:
                continue
            row = {**f, "outcome": outcome, "market_probability": market_prob}
            qualifies = f["improving_beaten_length_trend"] and (f["equipment_change"] or f["return_from_break"])
            (qualifying_rows if qualifies else control_rows).append(row)

    return {
        "n_races_excluded_insufficient_market_data": n_races_excluded_no_devig,
        "qualifying_group": _summary(qualifying_rows),
        "control_group": _summary(control_rows),
        "rule": (
            "improving beaten-length trend (finished closer last time than the time before) "
            f"AND (a real equipment change OR return from a break of >= {RETURN_FROM_BREAK_DAYS} days)"
        ),
        "statistical_caveat": (
            "Pooled at runner level, NOT race-level resampled (brief Section 24) -- read as "
            "descriptive/suggestive, not a validated statistical test."
        ),
    }
