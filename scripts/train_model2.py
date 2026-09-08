#!/usr/bin/env python3
"""
Phase 7 — train and walk-forward validate Model 2 (gradient-boosted trees
baseline, src/models/model2_gradient_boosting.py) against the REAL Kaggle
historical results, alongside Model 0 (market baseline) and Model 1
(logistic baseline) on the exact same walk-forward splits, for a real,
apples-to-apples three-way comparison.

Mirrors scripts/train_model1.py's shape exactly (load_races, walk-forward
loop, pooled scoring, calibration print) — this is Mac-only, needs the
local Postgres holding the real Kaggle-loaded (racecard, result) pairs from
Sessions 6/8/9 (interactive). The cloud routine cannot run this (no DB, no
credentials) — see docs/BUILD_LOG.md.

No random splits: every train/test boundary comes from walk_forward_splits()
(src/validation/walk_forward.py), which is purely chronological.

Usage: python3 scripts/train_model2.py [start_date] [min_train_days] [test_window_days] [gbm_max_iter]
Defaults: 2023-01-01, 180, 60, 100
"""
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.evaluation.calibration import brier_score, calibration_curve, log_loss
from src.features.runner_features import RunnerFeatureInput
from src.models.model0_market_baseline import RaceRecord as M0RaceRecord
from src.models.model0_market_baseline import RunnerOdds
from src.models.model0_market_baseline import predict_race_probabilities as m0_predict
from src.models.model1_logistic_baseline import DEFAULT_WEIGHTS
from src.models.model1_logistic_baseline import TrainingRace
from src.models.model1_logistic_baseline import fit_logistic_baseline
from src.models.model1_logistic_baseline import predict_race_probabilities as m1_predict
from src.models.model2_gradient_boosting import fit_gradient_boosting_baseline
from src.models.model2_gradient_boosting import predict_race_probabilities as m2_predict
from src.validation.walk_forward import walk_forward_splits

_NON_RUNNER_NOTES = {"NR", "WD"}


@dataclass
class RaceRow:
    race_id: int
    race_date: date
    runners: list
    odds: list
    winner_horse_id: "int | None"


def load_races(conn, start_date: str) -> list:
    # Identical query to scripts/train_model1.py's load_races — kept as a
    # copy rather than a shared import so each training script stays a
    # single, standalone, read-top-to-bottom file (same reasoning as why
    # this repo doesn't share ETL code between one-shot scripts).
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.race_date, rs.horse_id, rs.age, rs.draw, rs.weight_lbs,
               rs.official_rating, rs.recent_form, rr.finishing_position,
               rr.starting_price, rr.result_note
        FROM race r
        JOIN runner_snapshot rs ON rs.race_id = r.id
        JOIN runner_result rr ON rr.race_id = r.id AND rr.horse_id = rs.horse_id
        WHERE r.race_date >= %s
        ORDER BY r.race_date, r.id
        """,
        (start_date,),
    )

    by_race: dict = {}
    order: list = []
    for (race_id, race_date, horse_id, age, draw, weight_lbs, official_rating,
         recent_form, finishing_position, starting_price, result_note) in cur:
        note = (result_note or "").strip().upper()
        if finishing_position is None and note in _NON_RUNNER_NOTES:
            continue

        if race_id not in by_race:
            by_race[race_id] = {"race_date": race_date, "runners": [], "odds": [], "winner": None}
            order.append(race_id)
        entry = by_race[race_id]

        entry["runners"].append(RunnerFeatureInput(
            horse_id=horse_id, age=age, draw=draw, weight_lbs=weight_lbs,
            official_rating=official_rating, recent_form=recent_form,
        ))
        if starting_price is not None and starting_price > 1.0:
            entry["odds"].append(RunnerOdds(horse_id=horse_id, decimal_odds=float(starting_price)))
        if finishing_position == 1:
            entry["winner"] = horse_id

    cur.close()

    races = []
    for race_id in order:
        e = by_race[race_id]
        races.append(RaceRow(
            race_id=race_id, race_date=e["race_date"], runners=e["runners"],
            odds=e["odds"], winner_horse_id=e["winner"],
        ))
    return races


def main():
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"
    min_train_days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    test_window_days = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    gbm_max_iter = int(sys.argv[4]) if len(sys.argv) > 4 else 100

    conn = psycopg2.connect(dbname="silent_edge_zero")
    print(f"Loading real races from {start_date}...")
    all_races = load_races(conn, start_date)
    conn.close()
    print(f"Loaded {len(all_races):,} races (raw, before field-size/winner filtering).")

    usable = [r for r in all_races if r.winner_horse_id is not None and len(r.runners) >= 3]
    print(f"Usable for Model 1/Model 2 (winner known, field >= 3): {len(usable):,} races.")

    m0_usable = [r for r in usable if len(r.odds) == len(r.runners)]
    print(f"Also usable for Model 0 (every runner has a starting price): {len(m0_usable):,} races.\n")

    dates = [r.race_date for r in usable]
    splits = walk_forward_splits(
        dates, min_train_days=min_train_days, test_window_days=test_window_days,
    )
    print(f"{len(splits)} walk-forward splits "
          f"(min_train_days={min_train_days}, test_window_days={test_window_days}, expanding=True)\n")

    if not splits:
        print("No splits produced — not enough date range yet. Exiting.")
        return

    all_m0_probs, all_m0_outcomes = [], []
    all_m1_probs, all_m1_outcomes = [], []
    all_m2_probs, all_m2_outcomes = [], []

    header = (f"{'train_end':<12}{'test_end':<12}{'n_races':>8}"
              f"{'m0_brier':>10}{'m1_brier':>10}{'m2_brier':>10}"
              f"{'m0_ll':>9}{'m1_ll':>9}{'m2_ll':>9}")
    print(header)
    print("-" * len(header))

    for split in splits:
        train_races = [usable[i] for i in split.train_indices]
        test_races = [usable[i] for i in split.test_indices]

        train_set = [
            TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id)
            for r in train_races
        ]
        m1_weights = fit_logistic_baseline(train_set) if train_set else dict(DEFAULT_WEIGHTS)
        m2_model = fit_gradient_boosting_baseline(train_set, max_iter=gbm_max_iter) if train_set else None

        split_m0_probs, split_m0_outcomes = [], []
        split_m1_probs, split_m1_outcomes = [], []
        split_m2_probs, split_m2_outcomes = [], []

        for r in test_races:
            m1_probs = m1_predict(r.runners, weights=m1_weights)
            for horse_id, p in m1_probs.items():
                split_m1_probs.append(p)
                split_m1_outcomes.append(1 if horse_id == r.winner_horse_id else 0)

            if m2_model is not None:
                m2_probs = m2_predict(r.runners, model=m2_model)
                for horse_id, p in m2_probs.items():
                    split_m2_probs.append(p)
                    split_m2_outcomes.append(1 if horse_id == r.winner_horse_id else 0)

            if len(r.odds) == len(r.runners) and r.odds:
                m0_probs = m0_predict(r.odds, method="power")
                for horse_id, p in m0_probs.items():
                    split_m0_probs.append(p)
                    split_m0_outcomes.append(1 if horse_id == r.winner_horse_id else 0)

        m0_b = brier_score(split_m0_probs, split_m0_outcomes) if split_m0_probs else float("nan")
        m1_b = brier_score(split_m1_probs, split_m1_outcomes) if split_m1_probs else float("nan")
        m2_b = brier_score(split_m2_probs, split_m2_outcomes) if split_m2_probs else float("nan")
        m0_l = log_loss(split_m0_probs, split_m0_outcomes) if split_m0_probs else float("nan")
        m1_l = log_loss(split_m1_probs, split_m1_outcomes) if split_m1_probs else float("nan")
        m2_l = log_loss(split_m2_probs, split_m2_outcomes) if split_m2_probs else float("nan")

        print(f"{str(split.train_end):<12}{str(split.test_end):<12}{len(test_races):>8}"
              f"{m0_b:>10.4f}{m1_b:>10.4f}{m2_b:>10.4f}"
              f"{m0_l:>9.3f}{m1_l:>9.3f}{m2_l:>9.3f}")

        all_m0_probs.extend(split_m0_probs); all_m0_outcomes.extend(split_m0_outcomes)
        all_m1_probs.extend(split_m1_probs); all_m1_outcomes.extend(split_m1_outcomes)
        all_m2_probs.extend(split_m2_probs); all_m2_outcomes.extend(split_m2_outcomes)

    print("-" * len(header))
    print(f"\nPooled across all {len(splits)} out-of-sample test windows:")
    if all_m0_probs:
        print(f"  Model 0 (de-vigged market, power method): Brier={brier_score(all_m0_probs, all_m0_outcomes):.4f}  "
              f"LogLoss={log_loss(all_m0_probs, all_m0_outcomes):.4f}  n={len(all_m0_probs):,}")
    if all_m1_probs:
        print(f"  Model 1 (fitted logistic baseline):       Brier={brier_score(all_m1_probs, all_m1_outcomes):.4f}  "
              f"LogLoss={log_loss(all_m1_probs, all_m1_outcomes):.4f}  n={len(all_m1_probs):,}")
    if all_m2_probs:
        print(f"  Model 2 (gradient-boosted trees):         Brier={brier_score(all_m2_probs, all_m2_outcomes):.4f}  "
              f"LogLoss={log_loss(all_m2_probs, all_m2_outcomes):.4f}  n={len(all_m2_probs):,}")

    if all_m0_probs and all_m2_probs:
        print("\nModel 2 vs Model 0 (the actual research question, RL-008):")
        if brier_score(all_m2_probs, all_m2_outcomes) < brier_score(all_m0_probs, all_m0_outcomes):
            print("  Model 2 beat the market baseline on Brier score, out-of-sample, walk-forward.")
        else:
            print("  Model 2 did NOT beat the market baseline on Brier score, out-of-sample. "
                  "Same honest reporting discipline as Model 1's RL-006 result — a loss here is "
                  "real information, not a failed run.")

    if all_m2_probs:
        print("\nCalibration (Model 2, pooled, 10 bins):")
        for b in calibration_curve(all_m2_probs, all_m2_outcomes, n_bins=10):
            print(f"  [{b['bin_range'][0]:.1f}-{b['bin_range'][1]:.1f}) "
                  f"predicted={b['mean_predicted']:.3f} actual={b['mean_actual']:.3f} n={b['count']}")


if __name__ == "__main__":
    main()
