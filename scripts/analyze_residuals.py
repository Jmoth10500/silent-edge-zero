#!/usr/bin/env python3
"""
RL-011 ("GC" — Jonathan's name for it in conversation, kept out of the
actual code/data as a name since it implies more certainty than anything
here has earned — see docs/BUILD_LOG.md's honesty note on this).

Real, disciplined residual/miss-pattern analysis: where does Model 2's
CONFIDENT top pick actually lose, and is there a genuine, explainable,
real pattern among those losses — not one fitted to the same data that
produced it.

**The discipline that makes this legitimate rather than data-dredging:**
the 9 real walk-forward folds are split into a DISCOVERY set (the first 7,
chronologically earliest) and a VALIDATION set (the last 2, chronologically
latest, 2025-10 onward) that this script's pattern-FINDING step never
touches. Any candidate pattern found in discovery must be tested fresh
against validation before it's trusted — that's a separate script
(scripts/validate_residual_pattern.py, built once discovery finds a real
candidate worth testing, not before).

This script only does discovery: it fits Model 2 on each of the first 7
folds' training data (same real walk-forward harness as every other
backtest here), predicts the held-out test fold, and for every real
runner logs its predicted probability, real outcome, and the real
feature-edge values already computed for it — then compares the real
distribution of those values between CONFIDENT HITS (the race's top pick,
which won) and CONFIDENT MISSES (the race's top pick, which lost).

Usage: python3 scripts/analyze_residuals.py [start_date] [min_train_days] [test_window_days] [max_iter]
Defaults match scripts/train_model2.py.
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.train_model1 import (
    build_split_connections_tables, build_split_draw_bias_table,
    build_split_going_affinity_table, load_races,
)
from src.models.model1_logistic_baseline import build_race_features
from src.models.model2_gradient_boosting import TrainingRace as M2TrainingRace
from src.models.model2_gradient_boosting import fit_gradient_boosting
from src.models.model2_gradient_boosting import predict_race_probabilities as m2_predict
from src.validation.walk_forward import walk_forward_splits

DISCOVERY_FOLD_COUNT = 7  # of 9 real folds — the rest are held for validation, untouched here


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
    print(f"{len(splits)} real walk-forward folds total. "
          f"Using the first {DISCOVERY_FOLD_COUNT} for discovery, "
          f"holding the last {len(splits) - DISCOVERY_FOLD_COUNT} back untouched for validation.\n")

    discovery_splits = splits[:DISCOVERY_FOLD_COUNT]

    # Real per-runner rows for every top pick in every discovery-fold test race:
    # (is_hit, rating_edge, form_edge, draw_edge, weight_edge, trainer_edge,
    #  jockey_edge, field_size, distance_yards, going, favourite_prob)
    rows = []

    for split in discovery_splits:
        train_races = [usable[i] for i in split.train_indices]
        test_races = [usable[i] for i in split.test_indices]

        draw_bias_table = build_split_draw_bias_table(train_races)
        going_affinity_table = build_split_going_affinity_table(train_races)
        trainer_table, jockey_table = build_split_connections_tables(train_races)

        m2_train = [
            M2TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id,
                            course_id=r.course_id, distance_yards=r.distance_yards, going=r.going)
            for r in train_races if len(r.runners) >= 2
        ]
        if not m2_train:
            continue
        model = fit_gradient_boosting(
            m2_train, max_iter=max_iter, draw_bias_table=draw_bias_table,
            trainer_table=trainer_table, jockey_table=jockey_table,
        )

        for r in test_races:
            probs = m2_predict(
                r.runners, model, draw_bias_table=draw_bias_table,
                course_id=r.course_id, distance_yards=r.distance_yards,
                trainer_table=trainer_table, jockey_table=jockey_table,
            )
            top_horse_id = max(probs, key=probs.get)
            feats = build_race_features(
                r.runners, draw_bias_table, r.course_id, r.distance_yards,
                going_affinity_table, r.going, trainer_table, jockey_table,
            )
            f = feats[top_horse_id]
            rows.append({
                "is_hit": top_horse_id == r.winner_horse_id,
                "prob": probs[top_horse_id],
                "rating_edge": f["rating_edge"],
                "form_edge": f["form_edge"],
                "draw_edge": f["draw_edge"],
                "weight_edge": f["weight_edge"],
                "trainer_edge": f["trainer_edge"],
                "jockey_edge": f["jockey_edge"],
                "field_size": len(r.runners),
                "distance_yards": r.distance_yards,
            })

    hits = [row for row in rows if row["is_hit"]]
    misses = [row for row in rows if not row["is_hit"]]
    print(f"Real discovery-fold top picks: {len(rows):,} total — {len(hits):,} hits, {len(misses):,} misses "
          f"(real hit rate on top picks: {100*len(hits)/len(rows):.1f}%)\n")

    numeric_fields = ["prob", "rating_edge", "form_edge", "draw_edge", "weight_edge",
                       "trainer_edge", "jockey_edge", "field_size", "distance_yards"]

    print(f"{'field':<16}{'hit mean':>12}{'miss mean':>12}{'diff':>10}{'std-err diff':>14}{'z-ish':>8}")
    print("-" * 72)
    for field in numeric_fields:
        hit_vals = [row[field] for row in hits if row[field] is not None]
        miss_vals = [row[field] for row in misses if row[field] is not None]
        if len(hit_vals) < 30 or len(miss_vals) < 30:
            continue
        hit_mean = statistics.mean(hit_vals)
        miss_mean = statistics.mean(miss_vals)
        hit_se = statistics.pstdev(hit_vals) / (len(hit_vals) ** 0.5)
        miss_se = statistics.pstdev(miss_vals) / (len(miss_vals) ** 0.5)
        pooled_se = (hit_se ** 2 + miss_se ** 2) ** 0.5
        diff = hit_mean - miss_mean
        z = diff / pooled_se if pooled_se > 0 else float("nan")
        print(f"{field:<16}{hit_mean:>12.3f}{miss_mean:>12.3f}{diff:>10.3f}{pooled_se:>14.4f}{z:>8.2f}")

    print("\n|z| > ~2 is a real, unlikely-by-chance difference given these real sample sizes — "
          "still needs fresh validation on the held-out folds before being trusted as a usable pattern.")


if __name__ == "__main__":
    main()
