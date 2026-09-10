#!/usr/bin/env python3
"""
RL-012 validation — does temperature-scaling races where Model 2's own
top pick is >=40% genuinely help on data it never touched?

Same real walk-forward folds and same discipline as
scripts/validate_field_size_calibration.py (RL-011): the first 7 folds
(DISCOVERY) fit a single best temperature — via
src/evaluation/temperature_scaling.py::fit_best_temperature, grid-
searched to minimise real Brier score — using ONLY the real races whose
raw top-pick probability is >= TOP_PICK_THRESHOLD. The remaining folds
(VALIDATION) are held back entirely from that fitting step; the fitted
temperature is applied to their real >=threshold races and scored,
honestly, against the SAME predictions with no adjustment. Races below
the threshold are never touched by this correction in either phase —
RL-012's discovery/validation analysis (docs/RESEARCH_LAB.md) found no
real gap there, so there's nothing to correct.

This is the actual test of whether RL-012's finding (top picks >=40%
overconfident by 4-9pp, consistent on discovery AND validation) is
usable as a real calibration correction, or — like RL-011's field-size
idea — a real discovery-phase pattern that doesn't survive contact with
genuinely fresh data once turned into an actual adjustment.

Usage: python3 scripts/validate_top_pick_overconfidence_scaling.py [start_date] [min_train_days] [test_window_days] [max_iter]
Defaults match scripts/analyze_top_pick_calibration.py / validate_field_size_calibration.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.train_model1 import build_split_connections_tables, build_split_draw_bias_table, load_races
from src.evaluation.calibration import brier_score, log_loss
from src.evaluation.temperature_scaling import apply_temperature, fit_best_temperature
from src.models.model2_gradient_boosting import TrainingRace as M2TrainingRace
from src.models.model2_gradient_boosting import fit_gradient_boosting
from src.models.model2_gradient_boosting import predict_race_probabilities as m2_predict
from src.validation.walk_forward import walk_forward_splits

DISCOVERY_FOLD_COUNT = 7
TOP_PICK_THRESHOLD = 0.40  # from RL-012's real discovery+validation finding


def main():
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"
    min_train_days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    test_window_days = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    max_iter = int(sys.argv[4]) if len(sys.argv) > 4 else 50

    conn = psycopg2.connect(dbname="silent_edge_zero")
    print(f"Loading real races from {start_date}...", flush=True)
    all_races = load_races(conn, start_date)
    conn.close()

    usable = [r for r in all_races if r.winner_horse_id is not None and len(r.runners) >= 3]
    dates = [r.race_date for r in usable]
    splits = walk_forward_splits(dates, min_train_days=min_train_days, test_window_days=test_window_days)
    print(f"{len(splits)} real walk-forward folds. First {DISCOVERY_FOLD_COUNT} = discovery "
          f"(fit temperature here), last {len(splits) - DISCOVERY_FOLD_COUNT} = validation "
          f"(never fitted on).\n", flush=True)

    discovery_trigger_races = []  # (race_probs, winner_horse_id) — top pick >= threshold, discovery only
    validation_races = []  # (race_probs, winner_horse_id, is_trigger)

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
            top_prob = max(probs.values())
            is_trigger = top_prob >= TOP_PICK_THRESHOLD
            if is_discovery:
                if is_trigger:
                    discovery_trigger_races.append((probs, r.winner_horse_id))
            else:
                validation_races.append((probs, r.winner_horse_id, is_trigger))

        print(f"Fold {i+1}/{len(splits)} ({'discovery' if is_discovery else 'VALIDATION'}) done — "
              f"{len(test_races):,} real races.", flush=True)

    print(f"\nFitting best temperature on {len(discovery_trigger_races):,} real DISCOVERY races "
          f"with top pick >= {TOP_PICK_THRESHOLD*100:.0f}%...", flush=True)
    best_t = fit_best_temperature(discovery_trigger_races) if discovery_trigger_races else 1.0
    print(f"  best T = {best_t}", flush=True)

    n_trigger_val = sum(1 for _, _, trig in validation_races if trig)
    print(f"\n{len(validation_races):,} real validation races "
          f"({n_trigger_val:,} with top pick >= {TOP_PICK_THRESHOLD*100:.0f}%, "
          f"never used in the fitting step above).\n", flush=True)

    baseline_probs, baseline_outcomes = [], []
    adjusted_probs, adjusted_outcomes = [], []
    baseline_hits = adjusted_hits = 0

    for probs, winner_id, is_trigger in validation_races:
        for hid, p in probs.items():
            baseline_probs.append(p)
            baseline_outcomes.append(1 if hid == winner_id else 0)
        baseline_pick = max(probs, key=probs.get)
        baseline_hits += int(baseline_pick == winner_id)

        adjusted = apply_temperature(probs, best_t) if is_trigger else probs
        for hid, p in adjusted.items():
            adjusted_probs.append(p)
            adjusted_outcomes.append(1 if hid == winner_id else 0)
        adjusted_pick = max(adjusted, key=adjusted.get)
        adjusted_hits += int(adjusted_pick == winner_id)

    n = len(validation_races)
    print("Real validation result — ALL validation races (only ~5% are actually touched by "
          f"the correction, so any real effect is diluted almost to invisibility here):")
    print(f"  {'':20}{'Brier':>12}{'LogLoss':>10}{'Hit rate':>10}")
    print(f"  {'No adjustment':20}{brier_score(baseline_probs, baseline_outcomes):>12.6f}"
          f"{log_loss(baseline_probs, baseline_outcomes):>10.4f}{100*baseline_hits/n:>9.1f}%")
    print(f"  {'Top-pick scaled':20}{brier_score(adjusted_probs, adjusted_outcomes):>12.6f}"
          f"{log_loss(adjusted_probs, adjusted_outcomes):>10.4f}{100*adjusted_hits/n:>9.1f}%")

    # The actual test: restrict to just the real validation races the correction
    # touches (top pick >= threshold) — never diluted by the ~95% it leaves alone.
    sub_base_probs, sub_base_outcomes = [], []
    sub_adj_probs, sub_adj_outcomes = [], []
    sub_base_hits = sub_adj_hits = 0
    for probs, winner_id, is_trigger in validation_races:
        if not is_trigger:
            continue
        for hid, p in probs.items():
            sub_base_probs.append(p)
            sub_base_outcomes.append(1 if hid == winner_id else 0)
        sub_base_hits += int(max(probs, key=probs.get) == winner_id)
        adjusted = apply_temperature(probs, best_t)
        for hid, p in adjusted.items():
            sub_adj_probs.append(p)
            sub_adj_outcomes.append(1 if hid == winner_id else 0)
        sub_adj_hits += int(max(adjusted, key=adjusted.get) == winner_id)

    n_sub = n_trigger_val
    print(f"\nReal validation result — ONLY the {n_sub:,} real validation races the correction "
          f"actually touches (top pick >= {TOP_PICK_THRESHOLD*100:.0f}%):")
    print(f"  {'':20}{'Brier':>12}{'LogLoss':>10}{'Hit rate':>10}")
    print(f"  {'No adjustment':20}{brier_score(sub_base_probs, sub_base_outcomes):>12.6f}"
          f"{log_loss(sub_base_probs, sub_base_outcomes):>10.4f}{100*sub_base_hits/n_sub:>9.1f}%")
    print(f"  {'Top-pick scaled':20}{brier_score(sub_adj_probs, sub_adj_outcomes):>12.6f}"
          f"{log_loss(sub_adj_probs, sub_adj_outcomes):>10.4f}{100*sub_adj_hits/n_sub:>9.1f}%")

    base_brier = brier_score(sub_base_probs, sub_base_outcomes)
    adj_brier = brier_score(sub_adj_probs, sub_adj_outcomes)
    if adj_brier < base_brier:
        print(f"\nReal result (on the affected subset): top-pick temperature scaling IMPROVED "
              f"real held-out Brier score ({base_brier:.6f} -> {adj_brier:.6f}).")
    elif adj_brier > base_brier:
        print(f"\nReal result (on the affected subset): top-pick temperature scaling WORSENED "
              f"real held-out Brier score ({base_brier:.6f} -> {adj_brier:.6f}).")
    else:
        print("\nReal result (on the affected subset): no change in Brier score on real held-out data.")


if __name__ == "__main__":
    main()
