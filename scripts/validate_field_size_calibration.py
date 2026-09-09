#!/usr/bin/env python3
"""
RL-011 validation — does field-size temperature scaling genuinely help on
data it never touched?

Runs all 9 real walk-forward folds once. The first 7 (DISCOVERY) fit a
best temperature per field-size bucket (src/evaluation/temperature_scaling.py::fit_best_temperature) —
grid-searched to minimise real Brier score, same discipline as every
other "fit on training data" step in this repo. The last 2 folds
(VALIDATION, 2025-10 onward) are held back from that fitting step
entirely — the discovered per-bucket temperatures are applied to their
real predictions and scored, honestly, against the SAME predictions with
no adjustment. This is the actual test of whether the RL-011 discovery
finding (field_size z=-25.3) is a real, usable pattern or an artifact of
the discovery data alone.

Usage: python3 scripts/validate_field_size_calibration.py [start_date] [min_train_days] [test_window_days] [max_iter]
Defaults match scripts/train_model2.py / analyze_residuals.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.train_model1 import build_split_connections_tables, build_split_draw_bias_table, load_races
from src.evaluation.calibration import brier_score, log_loss
from src.evaluation.temperature_scaling import apply_temperature, field_size_bucket, fit_best_temperature
from src.models.model2_gradient_boosting import TrainingRace as M2TrainingRace
from src.models.model2_gradient_boosting import fit_gradient_boosting
from src.models.model2_gradient_boosting import predict_race_probabilities as m2_predict
from src.validation.walk_forward import walk_forward_splits

DISCOVERY_FOLD_COUNT = 7


def main():
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"
    min_train_days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    test_window_days = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    max_iter = int(sys.argv[4]) if len(sys.argv) > 4 else 50

    conn = psycopg2.connect(dbname="silent_edge_zero")
    print(f"Loading real races from {start_date}...")
    all_races = load_races(conn, start_date)
    conn.close()

    usable = [r for r in all_races if r.winner_horse_id is not None and len(r.runners) >= 3]
    dates = [r.race_date for r in usable]
    splits = walk_forward_splits(dates, min_train_days=min_train_days, test_window_days=test_window_days)
    print(f"{len(splits)} real walk-forward folds. First {DISCOVERY_FOLD_COUNT} = discovery "
          f"(fit temperatures here), last {len(splits) - DISCOVERY_FOLD_COUNT} = validation (never fitted on).\n")

    # bucket -> list of (race_probs, winner_horse_id), discovery folds only
    discovery_by_bucket: dict[str, list] = {"small": [], "medium": [], "large": []}
    # validation folds' real predictions, kept race-by-race for honest before/after scoring
    validation_races = []  # list of (race_probs, winner_horse_id, field_size)

    for i, split in enumerate(splits):
        train_races = [usable[j] for j in split.train_indices]
        test_races = [usable[j] for j in split.test_indices]

        draw_bias_table = build_split_draw_bias_table(train_races)
        trainer_table, jockey_table = build_split_connections_tables(train_races)

        m2_train = [
            M2TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id,
                            course_id=r.course_id, distance_yards=r.distance_yards)
            for r in train_races if len(r.runners) >= 2
        ]
        if not m2_train:
            continue
        model = fit_gradient_boosting(
            m2_train, max_iter=max_iter, draw_bias_table=draw_bias_table,
            trainer_table=trainer_table, jockey_table=jockey_table,
        )

        is_discovery = i < DISCOVERY_FOLD_COUNT
        for r in test_races:
            probs = m2_predict(
                r.runners, model, draw_bias_table=draw_bias_table,
                course_id=r.course_id, distance_yards=r.distance_yards,
                trainer_table=trainer_table, jockey_table=jockey_table,
            )
            bucket = field_size_bucket(len(r.runners))
            if is_discovery:
                discovery_by_bucket[bucket].append((probs, r.winner_horse_id))
            else:
                validation_races.append((probs, r.winner_horse_id, bucket))

        print(f"Fold {i+1}/{len(splits)} ({'discovery' if is_discovery else 'VALIDATION'}) done — "
              f"{len(test_races):,} real races.")

    print("\nFitting best temperature per field-size bucket on DISCOVERY data only...")
    best_temps = {}
    for bucket, races in discovery_by_bucket.items():
        if not races:
            continue
        t = fit_best_temperature(races)
        best_temps[bucket] = t
        print(f"  {bucket}: best T = {t} (from {len(races):,} real discovery races)")

    print(f"\n{len(validation_races):,} real validation races (never used in the fitting step above).\n")

    # Honest before/after on VALIDATION data only
    baseline_probs, baseline_outcomes = [], []
    adjusted_probs, adjusted_outcomes = [], []
    baseline_hits = adjusted_hits = 0

    for probs, winner_id, bucket in validation_races:
        for hid, p in probs.items():
            baseline_probs.append(p)
            baseline_outcomes.append(1 if hid == winner_id else 0)
        baseline_pick = max(probs, key=probs.get)
        baseline_hits += int(baseline_pick == winner_id)

        t = best_temps.get(bucket, 1.0)
        adjusted = apply_temperature(probs, t)
        for hid, p in adjusted.items():
            adjusted_probs.append(p)
            adjusted_outcomes.append(1 if hid == winner_id else 0)
        adjusted_pick = max(adjusted, key=adjusted.get)
        adjusted_hits += int(adjusted_pick == winner_id)

    n = len(validation_races)
    print("Real validation result (fold 8-9, never touched by the fitting step):")
    print(f"  {'':20}{'Brier':>10}{'LogLoss':>10}{'Hit rate':>10}")
    print(f"  {'No adjustment':20}{brier_score(baseline_probs, baseline_outcomes):>10.4f}"
          f"{log_loss(baseline_probs, baseline_outcomes):>10.4f}{100*baseline_hits/n:>9.1f}%")
    print(f"  {'Field-size scaled':20}{brier_score(adjusted_probs, adjusted_outcomes):>10.4f}"
          f"{log_loss(adjusted_probs, adjusted_outcomes):>10.4f}{100*adjusted_hits/n:>9.1f}%")

    if adjusted_hits > baseline_hits:
        print("\nReal result: field-size temperature scaling IMPROVED the real held-out hit rate.")
    elif adjusted_hits < baseline_hits:
        print("\nReal result: field-size temperature scaling WORSENED the real held-out hit rate.")
    else:
        print("\nReal result: no change in hit rate on real held-out data.")


if __name__ == "__main__":
    main()
