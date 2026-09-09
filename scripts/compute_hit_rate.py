#!/usr/bin/env python3
"""
Real "does the top pick actually win" hit rate — a different, more
intuitive question than Brier score, and a real one Jonathan asked
directly (2026-09-09): "how likely is this app able to choose the
winning horses?"

Brier score measures CALIBRATION (is a 20% prediction right ~20% of the
time across many races) — it does not directly answer "how often is the
single highest-probability pick the actual winner". This script computes
that real number, on the SAME real walk-forward folds and real Kaggle
data every other backtest in this repo uses — no new data, just a
different real metric on it.

Also reports the "always uniform" baseline (1/field_size averaged across
real races) as a floor for comparison — the naive rate you'd expect from
picking a random runner with no information at all.

Usage: python3 scripts/compute_hit_rate.py [start_date] [min_train_days] [test_window_days] [max_iter]
Defaults match scripts/train_model2.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.train_model1 import build_split_connections_tables, build_split_draw_bias_table, load_races
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
    test_window_days = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    max_iter = int(sys.argv[4]) if len(sys.argv) > 4 else 50

    conn = psycopg2.connect(dbname="silent_edge_zero")
    print(f"Loading real races from {start_date}...")
    all_races = load_races(conn, start_date)
    conn.close()

    usable = [r for r in all_races if r.winner_horse_id is not None and len(r.runners) >= 3]
    m0_usable_ids = {id(r) for r in usable if len(r.odds) == len(r.runners)}
    print(f"{len(usable):,} real races usable.\n")

    dates = [r.race_date for r in usable]
    splits = walk_forward_splits(dates, min_train_days=min_train_days, test_window_days=test_window_days)

    m0_hits = m0_total = 0
    m1_hits = m1_total = 0
    m2_hits = m2_total = 0
    uniform_baseline_sum = 0.0
    uniform_baseline_n = 0

    for split in splits:
        train_races = [usable[i] for i in split.train_indices]
        test_races = [usable[i] for i in split.test_indices]

        draw_bias_table = build_split_draw_bias_table(train_races)
        trainer_table, jockey_table = build_split_connections_tables(train_races)

        m1_train = [M1TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id,
                                    course_id=r.course_id, distance_yards=r.distance_yards)
                    for r in train_races]
        m1_weights = (
            fit_logistic_baseline(m1_train, iterations=max_iter, draw_bias_table=draw_bias_table,
                                   trainer_table=trainer_table, jockey_table=jockey_table)
            if m1_train else dict(DEFAULT_WEIGHTS)
        )

        m2_train = [M2TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id,
                                    course_id=r.course_id, distance_yards=r.distance_yards)
                    for r in train_races if len(r.runners) >= 2]
        m2_model = (
            fit_gradient_boosting(m2_train, max_iter=max_iter, draw_bias_table=draw_bias_table,
                                   trainer_table=trainer_table, jockey_table=jockey_table)
            if m2_train else None
        )

        for r in test_races:
            uniform_baseline_sum += 1.0 / len(r.runners)
            uniform_baseline_n += 1

            m1_probs = m1_predict(r.runners, weights=m1_weights, draw_bias_table=draw_bias_table,
                                   course_id=r.course_id, distance_yards=r.distance_yards,
                                   trainer_table=trainer_table, jockey_table=jockey_table)
            m1_pick = max(m1_probs, key=m1_probs.get)
            m1_total += 1
            m1_hits += int(m1_pick == r.winner_horse_id)

            if m2_model is not None:
                m2_probs = m2_predict(r.runners, m2_model, draw_bias_table=draw_bias_table,
                                       course_id=r.course_id, distance_yards=r.distance_yards,
                                       trainer_table=trainer_table, jockey_table=jockey_table)
                m2_pick = max(m2_probs, key=m2_probs.get)
                m2_total += 1
                m2_hits += int(m2_pick == r.winner_horse_id)

            if len(r.odds) == len(r.runners) and r.odds:
                m0_probs = m0_predict(r.odds, method="power")
                m0_pick = max(m0_probs, key=m0_probs.get)
                m0_total += 1
                m0_hits += int(m0_pick == r.winner_horse_id)

    uniform_rate = uniform_baseline_sum / uniform_baseline_n if uniform_baseline_n else 0.0

    print(f"{'':30}{'hits':>10}{'races':>10}{'hit rate':>12}")
    print("-" * 62)
    print(f"{'No-info baseline (1/field)':30}{'':>10}{'':>10}{uniform_rate*100:>11.1f}%  <- avg 1/field_size, no model at all")
    if m0_total:
        print(f"{'Model 0 (market baseline)':30}{m0_hits:>10}{m0_total:>10}{100*m0_hits/m0_total:>11.1f}%")
    print(f"{'Model 1 (statistical)':30}{m1_hits:>10}{m1_total:>10}{100*m1_hits/m1_total:>11.1f}%")
    print(f"{'Model 2 (gradient boosting)':30}{m2_hits:>10}{m2_total:>10}{100*m2_hits/m2_total:>11.1f}%")


if __name__ == "__main__":
    main()
