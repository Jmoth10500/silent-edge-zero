#!/usr/bin/env python3
"""
Real calibration analysis of Model 2's TOP PICK specifically — a
different, narrower question than REAL_CALIBRATION_BINS in
generate_dashboard.py (which pools every runner's probability, diluted
by all the low-probability non-picks). Jonathan's question (2026-09-10),
looking at a real 21.6% top pick on the dashboard: "If we were to find
an average percentage of the winners and monitor if there is a sweet
spot to act on... a score of 31% could end up being too confident and a
20.5% horse statistically is more than likely to win."

Same real walk-forward folds every other backtest in this repo uses (no
new data). Same discovery/validation discipline as RL-011 (see
docs/RESEARCH_LAB.md): the first 7 folds (chronologically earliest) are
DISCOVERY — where a "sweet spot" bin is allowed to be found — and the
last 2 folds (2025-10 onward) are VALIDATION, never touched by the
discovery step. A bin only counts as a real, usable sweet spot if
(predicted vs actual) disagreement seen in discovery ALSO shows up on
validation. Same failure mode RL-011 was built to catch: a discovery
step alone can find a real-looking pattern that's pure noise once tested
fresh.

Usage: python3 scripts/analyze_top_pick_calibration.py [start_date] [min_train_days] [test_window_days] [max_iter]
Defaults match scripts/compute_hit_rate.py / scripts/validate_field_size_calibration.py
(test_window_days=120, not train_model2.py's 60) — this is what actually
produces the canonical 9 real folds RL-011's discovery/validation split
(7/2) was defined against. Confirmed live: the 60-day default used
elsewhere in this repo produces 19 folds instead, a different split
entirely — caught before trusting a mismatched discovery/validation
boundary.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.train_model1 import build_split_connections_tables, build_split_draw_bias_table, load_races
from src.models.model1_logistic_baseline import DEFAULT_WEIGHTS
from src.models.model1_logistic_baseline import TrainingRace as M1TrainingRace
from src.models.model1_logistic_baseline import fit_logistic_baseline
from src.models.model2_gradient_boosting import TrainingRace as M2TrainingRace
from src.models.model2_gradient_boosting import fit_gradient_boosting
from src.models.model2_gradient_boosting import predict_race_probabilities as m2_predict
from src.validation.walk_forward import walk_forward_splits

# Finer than REAL_CALIBRATION_BINS since top picks concentrate in a
# narrower band (they're always the highest-probability runner in their
# own race, so rarely below ~0.10).
BIN_EDGES = [0.0, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 1.01]

DISCOVERY_FOLDS = 7  # same split as RL-011


def bucket(p: float) -> int:
    for i in range(len(BIN_EDGES) - 1):
        if BIN_EDGES[i] <= p < BIN_EDGES[i + 1]:
            return i
    return len(BIN_EDGES) - 2


def summarise(records: list[tuple[float, bool]]) -> list[dict]:
    """records: list of (top_pick_probability, won). Returns one dict per
    non-empty bin: predicted (mean prob in bin), actual (real win rate),
    n. Never fabricates a bin with zero real observations."""
    bins: dict[int, list[tuple[float, bool]]] = {}
    for p, won in records:
        bins.setdefault(bucket(p), []).append((p, won))
    out = []
    for i in sorted(bins):
        rows = bins[i]
        n = len(rows)
        predicted = sum(p for p, _ in rows) / n
        actual = sum(1 for _, won in rows if won) / n
        out.append({
            "low": BIN_EDGES[i], "high": BIN_EDGES[i + 1],
            "predicted": predicted, "actual": actual, "n": n,
        })
    return out


def main():
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"
    min_train_days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    test_window_days = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    max_iter = int(sys.argv[4]) if len(sys.argv) > 4 else 150

    conn = psycopg2.connect(dbname="silent_edge_zero")
    print(f"Loading real races from {start_date}...", flush=True)
    all_races = load_races(conn, start_date)
    conn.close()

    usable = [r for r in all_races if r.winner_horse_id is not None and len(r.runners) >= 3]
    print(f"{len(usable):,} real races usable.\n", flush=True)

    dates = [r.race_date for r in usable]
    splits = walk_forward_splits(dates, min_train_days=min_train_days, test_window_days=test_window_days)
    print(f"{len(splits)} real walk-forward folds. "
          f"Discovery = first {DISCOVERY_FOLDS}, validation = last {len(splits) - DISCOVERY_FOLDS}.\n", flush=True)

    discovery_records: list[tuple[float, bool]] = []
    validation_records: list[tuple[float, bool]] = []

    for fold_idx, split in enumerate(splits):
        train_races = [usable[i] for i in split.train_indices]
        test_races = [usable[i] for i in split.test_indices]

        draw_bias_table = build_split_draw_bias_table(train_races)
        trainer_table, jockey_table = build_split_connections_tables(train_races)

        m1_train = [M1TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id,
                                    course_id=r.course_id, distance_yards=r.distance_yards)
                    for r in train_races]
        _ = (
            fit_logistic_baseline(m1_train, iterations=max_iter, draw_bias_table=draw_bias_table,
                                   trainer_table=trainer_table, jockey_table=jockey_table)
            if m1_train else dict(DEFAULT_WEIGHTS)
        )  # Model 1 not needed for this analysis — kept only for parity/consistency with compute_hit_rate.py

        m2_train = [M2TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id,
                                    course_id=r.course_id, distance_yards=r.distance_yards)
                    for r in train_races if len(r.runners) >= 2]
        m2_model = (
            fit_gradient_boosting(m2_train, max_iter=max_iter, draw_bias_table=draw_bias_table,
                                   trainer_table=trainer_table, jockey_table=jockey_table)
            if m2_train else None
        )
        if m2_model is None:
            continue

        target = discovery_records if fold_idx < DISCOVERY_FOLDS else validation_records
        for r in test_races:
            m2_probs = m2_predict(r.runners, m2_model, draw_bias_table=draw_bias_table,
                                   trainer_table=trainer_table, jockey_table=jockey_table)
            pick, p = max(m2_probs.items(), key=lambda kv: kv[1])
            target.append((p, pick == r.winner_horse_id))

        print(f"fold {fold_idx + 1}/{len(splits)} ({'discovery' if fold_idx < DISCOVERY_FOLDS else 'VALIDATION'}) "
              f"done — {len(test_races)} test races", flush=True)

    def print_table(label: str, records: list[tuple[float, bool]]) -> None:
        print(f"\n{'=' * 70}\n{label} ({len(records):,} real top-pick predictions)\n{'=' * 70}")
        print(f"{'range':<14}{'predicted':>10}{'actual':>10}{'n':>8}   note")
        for row in summarise(records):
            gap = row["actual"] - row["predicted"]
            note = ""
            if row["n"] < 150:
                note = "small sample — treat cautiously"
            elif gap > 0.03:
                note = f"actual beats predicted by {gap*100:+.1f}pp — real edge candidate"
            elif gap < -0.03:
                note = f"actual falls short by {gap*100:+.1f}pp — real overconfidence"
            print(f"{row['low']*100:>4.0f}-{row['high']*100:<7.0f}%"
                  f"{row['predicted']*100:>9.1f}%{row['actual']*100:>9.1f}%{row['n']:>8,}   {note}")

    print_table("DISCOVERY (first 7 folds — sweet-spot candidates may be found here)", discovery_records)
    print_table("VALIDATION (last folds — never touched during discovery)", validation_records)
    print(
        "\nA bin only counts as a real, usable sweet spot if it shows the same "
        "direction and a meaningful gap on BOTH tables above — same discipline as "
        "RL-011. A discovery-only pattern is not enough to act on."
    )


if __name__ == "__main__":
    main()
