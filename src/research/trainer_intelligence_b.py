"""
Trainer Intelligence Lab, Hypothesis B: trainer/market behaviour — Silent
Edge Zero V2 brief, Section 12B. Completely separate from the live
prediction algorithm — nothing here is imported by
scripts/predict_todays_races.py or anything in FROZEN_FILES.

**Real, honest data-coverage correction (discovered live, not assumed):**
this module was originally designed around `morning_wap` as the early
snapshot per its own column name. Checked directly against the loaded
data before writing a line of the hypothesis test: `morning_wap` and
`wap` are 0% populated across all 27,637 real rows in
`historical_betfair_price` — only `pre_min`/`pre_max`/`bsp` have real
coverage (~88%). The morning-price comparison this hypothesis needs
simply isn't available in this dataset, despite the column existing in
the schema for it. **Redesigned, real substitute:** `pre_max` (the
widest — i.e. earliest-available, most conservative — price reached
before the off) stands in as the "early" snapshot, and `bsp` (the final
Betfair Starting Price, settled at the off) as "late". This is narrower
than the brief's own multi-point ask (morning/pre-off/SP) but is what
this specific data source can actually support — the alternative would
be inventing data that doesn't exist, which this project never does.

**Real, leakage-safe question, stated precisely:** does a runner's price
movement from `pre_max` to `bsp` predict performance BEYOND what
`pre_max`'s own de-vigged probability already implied? This is exactly
brief Section 12B's own framing: "determine whether early market
movements predict performance beyond the market probability already
available at the chosen decision time." The comparison benchmark is
deliberately the EARLY (`pre_max`) probability, never the later one —
using the later price as the benchmark would make "the market moved and
the horse that shortened won more" a tautology, not a finding.

**Never uses in-play data.** `historical_betfair_price.ip_min`/`ip_max`
are explicitly excluded from every function in this module (see that
table's own schema comment, db/schema.sql) — they are recorded after the
race started and would be a real, direct leakage violation if used here.

**Never claims misconduct.** Per the brief's own instruction: "do not
interpret price movement alone as evidence of misconduct or inside
information." This module reports numbers; it does not speculate about
why a price moved.
"""
from typing import Optional

from scripts.generate_eod_report import VOID_RESULT_CODES


def load_price_movement_rows(conn, since=None) -> list[dict]:
    """Real, flat per-runner rows from historical_betfair_price joined to
    the race/runner_snapshot/runner_result it belongs to — trainer/jockey
    included for the descriptive trainer-pattern breakdown. Only rows with
    a real pre_max AND a real bsp are usable for the core hypothesis (both
    filtered by the caller, not here, so exclusion counts stay visible) —
    see module docstring for why pre_max/bsp are used instead of the
    originally-planned morning_wap (0% populated in this real dataset)."""
    cur = conn.cursor()
    where = "1=1"
    params: list = []
    if since is not None:
        where += " AND r.race_date >= %s"
        params.append(since)
    cur.execute(
        f"""
        SELECT hbp.race_id, hbp.horse_id, r.race_date, c.name,
               tr.name, jk.name, hbp.pre_max, hbp.bsp,
               rr.finishing_position, rr.result_note
        FROM historical_betfair_price hbp
        JOIN race r ON r.id = hbp.race_id
        JOIN course c ON c.id = r.course_id
        LEFT JOIN runner_snapshot rs ON rs.race_id = hbp.race_id AND rs.horse_id = hbp.horse_id
        LEFT JOIN trainer tr ON tr.id = rs.trainer_id
        LEFT JOIN jockey jk ON jk.id = rs.jockey_id
        LEFT JOIN runner_result rr ON rr.race_id = hbp.race_id AND rr.horse_id = hbp.horse_id
        WHERE {where}
        """,
        params,
    )
    rows = cur.fetchall()
    cur.close()

    out = []
    for (race_id, horse_id, race_date, course, trainer, jockey, pre_max, bsp,
         finishing_position, result_note) in rows:
        out.append({
            "race_id": race_id, "horse_id": horse_id, "race_date": race_date, "course": course,
            "trainer": trainer, "jockey": jockey,
            "pre_max": float(pre_max) if pre_max is not None else None,
            "bsp": float(bsp) if bsp is not None else None,
            "finishing_position": finishing_position, "result_note": result_note,
        })
    return out


def _outcome(row: dict) -> Optional[int]:
    if row["finishing_position"] == 1:
        return 1
    if row["finishing_position"] is not None:
        return 0
    if row["result_note"] is None:
        return None
    if row["result_note"] in VOID_RESULT_CODES:
        return None
    return 0


def compute_movement_features(rows: list[dict]) -> list[dict]:
    """Pure function (no DB). For every race with >=2 runners carrying a
    real pre_max, computes each such runner's early (pre_max-based)
    de-vigged implied probability and its real price-shortening
    percentage (pre_max - bsp) / pre_max — positive means the price
    shortened (the market moved toward this horse) between the widest
    pre-off price and the final BSP, negative means it drifted. A runner
    missing either pre_max or bsp is excluded from this race's computation
    entirely (never guessed), and a race with fewer than 2 runners left
    after that exclusion can't be de-vigged and contributes nothing."""
    from src.analysis.edge_metrics import normalized_market_probabilities

    by_race: dict[int, list[dict]] = {}
    for row in rows:
        by_race.setdefault(row["race_id"], []).append(row)

    features = []
    for race_id, race_rows in by_race.items():
        usable = [r for r in race_rows if r["pre_max"] is not None and r["bsp"] is not None]
        if len(usable) < 2:
            continue
        odds_by_index = {i: r["pre_max"] for i, r in enumerate(usable)}
        early_probs = normalized_market_probabilities(odds_by_index)
        if not early_probs:
            continue

        for i, r in enumerate(usable):
            outcome = _outcome(r)
            if outcome is None:
                continue
            early_prob = early_probs.get(i)
            if early_prob is None:
                continue
            price_shortened_pct = (r["pre_max"] - r["bsp"]) / r["pre_max"]
            features.append({
                "race_id": race_id, "horse_id": r["horse_id"], "trainer": r["trainer"], "jockey": r["jockey"],
                "course": r["course"], "early_implied_probability": early_prob,
                "price_shortened_pct": round(price_shortened_pct, 4),
                "outcome": outcome,
            })
    return features


def test_price_movement_hypothesis(features: list[dict], shorten_threshold: float = 0.15) -> dict:
    """Splits into QUALIFYING (price shortened by >= shorten_threshold
    between pre_max and bsp, e.g. 0.15 = odds fell by 15%+) vs CONTROL,
    and compares each group's actual win rate against the EARLY
    (pre_max-based) implied probability — the leakage-safe benchmark, see
    module docstring. A positive diff for the qualifying group would mean
    "the shortening itself carried real forward-looking information
    beyond what the early price already reflected"."""
    from src.research.probability_bands import wilson_score_interval

    def _summary(rows: list[dict]) -> Optional[dict]:
        n = len(rows)
        if n == 0:
            return None
        actual_wins = sum(r["outcome"] for r in rows)
        expected_wins = sum(r["early_implied_probability"] for r in rows)
        ci = wilson_score_interval(actual_wins, n)
        return {
            "n": n, "actual_wins": actual_wins, "actual_win_rate": round(actual_wins / n, 4),
            "expected_wins_from_early_price": round(expected_wins, 2),
            "diff_actual_minus_expected": round(actual_wins - expected_wins, 2),
            "win_rate_confidence_interval": [round(ci[0], 4), round(ci[1], 4)] if ci else None,
            "small_sample": n < 20,
        }

    qualifying = [f for f in features if f["price_shortened_pct"] >= shorten_threshold]
    control = [f for f in features if f["price_shortened_pct"] < shorten_threshold]

    return {
        "shorten_threshold": shorten_threshold,
        "qualifying_group": _summary(qualifying),
        "control_group": _summary(control),
        "benchmark": "pre_max-based de-vigged implied probability (the earliest available price this dataset supports — see module docstring)",
        "statistical_caveat": (
            "Pooled at runner level, NOT race-level resampled (brief Section 24) -- read as "
            "descriptive/suggestive, not a validated statistical test."
        ),
    }


def trainer_shortening_summary(features: list[dict], min_runs: int = 15) -> dict:
    """Real, purely descriptive per-trainer average price-shortening,
    for trainers with at least `min_runs` real observations. No claim of
    outperformance or misconduct is made here — see module docstring."""
    by_trainer: dict[str, list[dict]] = {}
    for f in features:
        if f["trainer"]:
            by_trainer.setdefault(f["trainer"], []).append(f)

    out = {}
    for trainer, rows in by_trainer.items():
        if len(rows) < min_runs:
            continue
        out[trainer] = {
            "n": len(rows),
            "avg_price_shortened_pct": round(sum(r["price_shortened_pct"] for r in rows) / len(rows), 4),
            "actual_wins": sum(r["outcome"] for r in rows),
            "actual_win_rate": round(sum(r["outcome"] for r in rows) / len(rows), 4),
        }
    return out
