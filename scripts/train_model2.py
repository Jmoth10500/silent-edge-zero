#!/usr/bin/env python3
"""
Phase 7 — train and walk-forward validate Model 2 (gradient boosting,
src/models/model2_gradient_boosting.py) against the same real Kaggle
historical results used in scripts/train_model1.py, scored against both
Model 0 (market baseline) and Model 1 (logistic baseline) on the identical
walk-forward folds — the real test behind RL-006/RL-008's question: does a
genuinely different model class do better than Model 1 with the same
feature set, and does either beat the market?

No random splits: every train/test boundary comes from walk_forward_splits()
(src/validation/walk_forward.py), purely chronological, same as Model 1's
script.

Usage: python3 scripts/train_model2.py [start_date] [min_train_days] [test_window_days] [max_iter]
Defaults: 2023-01-01, 180, 60, 150
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.train_model1 import RaceRow, load_races
from src.evaluation.calibration import brier_score, calibration_curve, log_loss
from src.models.model0_market_baseline import RaceRecord as M0RaceRecord  # noqa: F401 (kept for parity/reference)
from src.models.model0_market_baseline import predict_race_probabilities as m0_predict
from src.models.model1_logistic_baseline import DEFAULT_WEIGHTS
from src.models.model1_logistic_baseline import TrainingRace as M1TrainingRace
from src.models.model1_logistic_baseline import fit_logistic_baseline
from src.models.model1_logistic_baseline import predict_race_probabilities as m1_predict
from src.models.model2_gradient_boosting import TrainingRace as M2TrainingRace
from src.models.model2_gradient_boosting import fit_gradient_boosting
from src.models.model2_gradient_boosting import predict_race_probabilities as m2_predict
from src.validation.walk_forward import walk_forward_splits


def main():
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"
    min_train_days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    test_window_days = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    max_iter = int(sys.argv[4]) if len(sys.argv) > 4 else 150

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

    all_m2_probs, all_m2_outcomes = [], []
    all_m1_probs, all_m1_outcomes = [], []
    all_m0_probs, all_m0_outcomes = [], []

    header = (f"{'train_end':<12}{'test_end':<12}{'n_races':>8}"
              f"{'m2_brier':>10}{'m2_logloss':>12}{'m1_brier':>10}{'m1_logloss':>12}"
              f"{'m0_brier':>10}{'m0_logloss':>12}")
    print(header)
    print("-" * len(header))

    for split in splits:
        train_races = [usable[i] for i in split.train_indices]
        test_races = [usable[i] for i in split.test_indices]

        m2_train_set = [
            M2TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id)
            for r in train_races
            if len(r.runners) >= 2  # a single-runner "race" can't teach the binary classifier anything
        ]
        m2_model = fit_gradient_boosting(m2_train_set, max_iter=max_iter) if m2_train_set else None

        m1_train_set = [
            M1TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id)
            for r in train_races
        ]
        m1_weights = fit_logistic_baseline(m1_train_set, iterations=max_iter) if m1_train_set else dict(DEFAULT_WEIGHTS)

        split_m2_probs, split_m2_outcomes = [], []
        split_m1_probs, split_m1_outcomes = [], []
        split_m0_probs, split_m0_outcomes = [], []

        for r in test_races:
            if m2_model is not None:
                m2_probs = m2_predict(r.runners, m2_model)
                for horse_id, p in m2_probs.items():
                    split_m2_probs.append(p)
                    split_m2_outcomes.append(1 if horse_id == r.winner_horse_id else 0)

            probs = m1_predict(r.runners, weights=m1_weights)
            for horse_id, p in probs.items():
                split_m1_probs.append(p)
                split_m1_outcomes.append(1 if horse_id == r.winner_horse_id else 0)

            if len(r.odds) == len(r.runners) and r.odds:
                m0_probs = m0_predict(r.odds, method="power")
                for horse_id, p in m0_probs.items():
                    split_m0_probs.append(p)
                    split_m0_outcomes.append(1 if horse_id == r.winner_horse_id else 0)

        m2_b = brier_score(split_m2_probs, split_m2_outcomes) if split_m2_probs else float("nan")
        m2_l = log_loss(split_m2_probs, split_m2_outcomes) if split_m2_probs else float("nan")
        m1_b = brier_score(split_m1_probs, split_m1_outcomes) if split_m1_probs else float("nan")
        m1_l = log_loss(split_m1_probs, split_m1_outcomes) if split_m1_probs else float("nan")
        m0_b = brier_score(split_m0_probs, split_m0_outcomes) if split_m0_probs else float("nan")
        m0_l = log_loss(split_m0_probs, split_m0_outcomes) if split_m0_probs else float("nan")

        print(f"{str(split.train_end):<12}{str(split.test_end):<12}{len(test_races):>8}"
              f"{m2_b:>10.4f}{m2_l:>12.4f}{m1_b:>10.4f}{m1_l:>12.4f}{m0_b:>10.4f}{m0_l:>12.4f}")

        all_m2_probs.extend(split_m2_probs)
        all_m2_outcomes.extend(split_m2_outcomes)
        all_m1_probs.extend(split_m1_probs)
        all_m1_outcomes.extend(split_m1_outcomes)
        all_m0_probs.extend(split_m0_probs)
        all_m0_outcomes.extend(split_m0_outcomes)

    print("-" * len(header))
    print(f"\nPooled across all {len(splits)} out-of-sample test windows:")
    if all_m2_probs:
        print(f"  Model 2 (gradient boosting):        Brier={brier_score(all_m2_probs, all_m2_outcomes):.4f}  "
              f"LogLoss={log_loss(all_m2_probs, all_m2_outcomes):.4f}  n={len(all_m2_probs):,}")
    if all_m1_probs:
        print(f"  Model 1 (fitted logistic baseline): Brier={brier_score(all_m1_probs, all_m1_outcomes):.4f}  "
              f"LogLoss={log_loss(all_m1_probs, all_m1_outcomes):.4f}  n={len(all_m1_probs):,}")
    if all_m0_probs:
        print(f"  Model 0 (de-vigged market, power):  Brier={brier_score(all_m0_probs, all_m0_outcomes):.4f}  "
              f"LogLoss={log_loss(all_m0_probs, all_m0_outcomes):.4f}  n={len(all_m0_probs):,}")

    if all_m2_probs and all_m0_probs:
        print("\nModel 2 vs Model 0 (the RL-008 research question):")
        if brier_score(all_m2_probs, all_m2_outcomes) < brier_score(all_m0_probs, all_m0_outcomes):
            print("  Model 2 beat the market baseline on Brier score, out-of-sample, walk-forward.")
        else:
            print("  Model 2 did NOT beat the market baseline on Brier score, out-of-sample.")

    if all_m2_probs and all_m1_probs:
        print("\nModel 2 vs Model 1 (does a different model class beat the same features):")
        if brier_score(all_m2_probs, all_m2_outcomes) < brier_score(all_m1_probs, all_m1_outcomes):
            print("  Model 2 beat Model 1 on Brier score, same feature set, out-of-sample.")
        else:
            print("  Model 2 did NOT beat Model 1 on Brier score, same feature set, out-of-sample.")

    print("\nCalibration (Model 2, pooled, 10 bins):")
    for b in calibration_curve(all_m2_probs, all_m2_outcomes, n_bins=10):
        print(f"  [{b['bin_range'][0]:.1f}-{b['bin_range'][1]:.1f}) "
              f"predicted={b['mean_predicted']:.3f} actual={b['mean_actual']:.3f} n={b['count']}")


if __name__ == "__main__":
    main()
