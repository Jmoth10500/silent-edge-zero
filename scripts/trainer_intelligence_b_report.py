#!/usr/bin/env python3
"""
Trainer Intelligence Lab, Hypothesis B (market behaviour / price
movement) report — Silent Edge Zero V2 brief, Section 12B. Read-only,
completely separate from the live prediction algorithm. Runs over
historical_betfair_price (2026-03-01 to 2026-04-29 — see
scripts/load_kaggle_betfair_historical.py's module docstring for the real
coverage window).

Usage: python3 scripts/trainer_intelligence_b_report.py [--shorten-threshold N] [--min-trainer-runs N]
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.research.trainer_intelligence_b import (
    compute_movement_features,
    load_price_movement_rows,
    trainer_shortening_summary,
)
from src.research.trainer_intelligence_b import test_price_movement_hypothesis as run_price_movement_test

REPO_ROOT = Path(__file__).parent.parent


def main():
    threshold = 0.15
    if "--shorten-threshold" in sys.argv:
        threshold = float(sys.argv[sys.argv.index("--shorten-threshold") + 1])
    min_trainer_runs = 15
    if "--min-trainer-runs" in sys.argv:
        min_trainer_runs = int(sys.argv[sys.argv.index("--min-trainer-runs") + 1])

    conn = psycopg2.connect(dbname="silent_edge_zero")
    rows = load_price_movement_rows(conn)
    conn.close()

    print(f"Loaded {len(rows)} real historical_betfair_price rows.")
    features = compute_movement_features(rows)
    print(f"{len(features)} real runner-observations have both a usable pre_max price and a real outcome.")

    result = run_price_movement_test(features, shorten_threshold=threshold)
    trainer_summary = trainer_shortening_summary(features, min_runs=min_trainer_runs)

    out_path = REPO_ROOT / "data" / f"trainer_intelligence_b_{date.today().isoformat()}.json"
    out_path.write_text(json.dumps({"hypothesis_test": result, "trainer_summary": trainer_summary}, indent=2, default=str))

    print(f"\nHYPOTHESIS B: price shortened by >= {threshold:.0%} between pre_max and bsp")
    print(f"  Benchmark: {result['benchmark']}")
    for label, group in (("QUALIFYING (shortened)", result["qualifying_group"]), ("CONTROL", result["control_group"])):
        if group is None:
            print(f"  {label}: no observations")
            continue
        flag = " (small sample)" if group["small_sample"] else ""
        print(f"  {label}: n={group['n']}  actual_wins={group['actual_wins']} ({group['actual_win_rate']:.1%})  "
              f"expected_from_early_price={group['expected_wins_from_early_price']}  "
              f"diff={group['diff_actual_minus_expected']:+}  95% CI={group['win_rate_confidence_interval']}{flag}")
    print(f"\n  CAVEAT: {result['statistical_caveat']}")

    print(f"\nTrainer price-shortening summary ({len(trainer_summary)} trainers with >= {min_trainer_runs} runs):")
    for trainer, s in sorted(trainer_summary.items(), key=lambda kv: kv[1]["avg_price_shortened_pct"], reverse=True)[:10]:
        print(f"  {trainer}: n={s['n']}  avg_shortened={s['avg_price_shortened_pct']:+.1%}  win_rate={s['actual_win_rate']:.1%}")

    print(f"\nFull detail written to {out_path}")


if __name__ == "__main__":
    main()
