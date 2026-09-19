"""
Trainer Intelligence Lab, Hypothesis A: handicap positioning — Silent Edge
Zero V2 brief, Section 12A. Completely separate from the live prediction
algorithm — nothing here is imported by scripts/predict_todays_races.py or
any file in scripts/check_model_freeze.py's FROZEN_FILES list.

**Horse identity, deliberately by NAME here, not horse_id:** the known,
unresolved `horse.UNIQUE(name, foaled_year)` dedup bug (db/schema.sql's
own comment, docs/BUILD_LOG.md 2026-09-11) means the same real horse can
have more than one `horse.id` across different collection runs. For a
CAREER TREND across many races — exactly what this hypothesis needs — a
duplicate horse_id would silently break the trend into two disconnected
fragments. Grouping by `horse.name` directly sidesteps this: duplicate
rows sharing the same real horse still share the same name string, so a
name-based career history stays intact regardless of the id-level bug.
This is a deliberate, real design choice for this module only — it does
NOT fix the underlying bug (still needs Jonathan's go-ahead, see the
project's own build log) and other modules in this project correctly keep
using horse_id via `prediction` for their own, different purposes.

**Market benchmark:** uses real official `starting_price` (near-complete
coverage in the historical bootstrap — the primary use case for this
module, since it needs long historical runs no live market_snapshot
data covers) rather than exchange_back, de-vigged the same way
(src.analysis.edge_metrics.normalized_market_probabilities) per race.

**Real, honest statistical limitation, not glossed over:** this module
pools observations at RUNNER level. The brief's own Section 24 warns that
"a large number of runner-level observations does not necessarily mean an
equally large number of independent races" and calls for race-level
resampling — this module does NOT implement that (out of scope for this
pass); its win-rate comparisons should be read as suggestive, not as a
validated statistical test, and are reported to the hypothesis tracker
with that caveat attached explicitly, never silently omitted.
"""
from datetime import date as date_type
from typing import Optional

from src.analysis.edge_metrics import normalized_market_probabilities
from scripts.generate_eod_report import VOID_RESULT_CODES


def load_horse_career_runs(conn, since: Optional[date_type] = None) -> dict[str, list[dict]]:
    """Real, flat per-runner history across the whole DB (not restricted
    to races with a locked Silent Edge prediction — this needs the full
    historical bootstrap), grouped by horse name and sorted chronologically
    within each horse. `since` restricts to races on/after that date if
    given (None = everything, the real default for a career-trend query)."""
    cur = conn.cursor()
    params = []
    where = "rs.official_rating IS NOT NULL"
    if since is not None:
        where += " AND r.race_date >= %s"
        params.append(since)
    cur.execute(
        f"""
        SELECT h.name, r.id, r.race_date, r.race_class, r.distance_yards, r.going,
               rs.official_rating, rs.weight_lbs,
               rr.finishing_position, rr.result_note, rr.starting_price
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
    for (name, race_id, race_date, race_class, distance_yards, going,
         official_rating, weight_lbs, finishing_position, result_note, starting_price) in rows:
        by_horse.setdefault(name, []).append({
            "race_id": race_id, "race_date": race_date, "race_class": race_class,
            "distance_yards": distance_yards, "going": going,
            "official_rating": float(official_rating), "weight_lbs": weight_lbs,
            "finishing_position": finishing_position, "result_note": result_note,
            "starting_price": float(starting_price) if starting_price is not None else None,
        })
    return by_horse


def compute_handicap_features(runs_by_horse: dict[str, list[dict]]) -> list[dict]:
    """Pure function (no DB) — for every run after a horse's first rated
    run, computes prior_max_rating (real max OR from strictly earlier
    runs), rating_drop (prior_max_rating - this run's OR; a positive
    number means the horse is racing off a lower mark than its career
    best), and, if the horse has a real prior win, that win's rating/
    distance/going and days_since_previous_win. A horse's first rated run
    has no "prior" anything and is skipped — never guessed."""
    features = []
    for horse_name, runs in runs_by_horse.items():
        for i in range(1, len(runs)):
            current = runs[i]
            prior_runs = runs[:i]
            prior_max_rating = max(p["official_rating"] for p in prior_runs)
            prior_wins = [p for p in prior_runs if p["finishing_position"] == 1]
            previous_win = prior_wins[-1] if prior_wins else None

            features.append({
                "horse_name": horse_name,
                "race_id": current["race_id"],
                "race_date": current["race_date"],
                "race_class": current["race_class"],
                "distance_yards": current["distance_yards"],
                "going": current["going"],
                "official_rating": current["official_rating"],
                "prior_max_rating": prior_max_rating,
                "rating_drop": round(prior_max_rating - current["official_rating"], 1),
                "has_previous_win": previous_win is not None,
                "previous_win_rating": previous_win["official_rating"] if previous_win else None,
                "previous_win_distance_yards": previous_win["distance_yards"] if previous_win else None,
                "previous_win_going": previous_win["going"] if previous_win else None,
                "days_since_previous_win": (
                    (current["race_date"] - previous_win["race_date"]).days if previous_win else None
                ),
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


def test_rating_drop_hypothesis(features: list[dict], rating_drop_threshold: float = 5.0) -> dict:
    """Splits `features` into a QUALIFYING group (real rating_drop >=
    threshold AND a real previous win exists — "returning to a favourable
    handicap mark" per the brief) and a CONTROL group (everyone else with
    a known outcome and a real starting price), then compares each
    group's actual win rate against the market's own de-vigged implied
    probability for the SAME runners — never against a flat/unconditional
    baseline, so this measures "beyond market expectation", not just "wins
    a lot" (brief's own requirement, Section 12A: "test whether
    combinations of these variables predict performance beyond market
    probability").

    De-vigging is computed PER RACE from all runners of that race with a
    real starting_price — races with fewer than 2 such runners can't be
    de-vigged and are excluded, same rule as everywhere else in this
    project.
    """
    from src.research.probability_bands import wilson_score_interval

    # Group features by race_id first, since de-vigging needs the whole race.
    by_race: dict[int, list[dict]] = {}
    for f in features:
        by_race.setdefault(f["race_id"], []).append(f)

    def _group_summary(rows: list[dict]) -> Optional[dict]:
        n, actual_wins, expected_wins = 0, 0, 0.0
        for row in rows:
            n += 1
            actual_wins += row["outcome"]
            expected_wins += row["market_probability"]
        if n == 0:
            return None
        ci = wilson_score_interval(actual_wins, n)
        return {
            "n": n,
            "actual_wins": actual_wins,
            "actual_win_rate": round(actual_wins / n, 4),
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
            if f["rating_drop"] >= rating_drop_threshold and f["has_previous_win"]:
                qualifying_rows.append(row)
            else:
                control_rows.append(row)

    return {
        "rating_drop_threshold": rating_drop_threshold,
        "n_races_excluded_insufficient_market_data": n_races_excluded_no_devig,
        "qualifying_group": _group_summary(qualifying_rows),
        "control_group": _group_summary(control_rows),
        "statistical_caveat": (
            "Pooled at runner level, NOT race-level resampled (brief Section 24's own "
            "requirement) -- observations within the same race are not independent. Read "
            "this as a descriptive/suggestive comparison, not a validated statistical test."
        ),
    }
