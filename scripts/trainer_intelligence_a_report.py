#!/usr/bin/env python3
"""
Trainer Intelligence Lab, Hypothesis A (handicap positioning) report —
Silent Edge Zero V2 brief, Section 12A. Read-only, completely separate
from the live prediction algorithm. Runs over the full historical
bootstrap (2023-present) by default, since this hypothesis needs a real
long-run career trend per horse, not just the last few weeks.

Usage: python3 scripts/trainer_intelligence_a_report.py [--since YYYY-MM-DD] [--rating-drop N]
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.research.trainer_intelligence_a import compute_handicap_features, load_horse_career_runs
from src.research.trainer_intelligence_a import test_rating_drop_hypothesis as run_rating_drop_hypothesis_test

REPO_ROOT = Path(__file__).parent.parent


def main():
    since = None
    if "--since" in sys.argv:
        since = date.fromisoformat(sys.argv[sys.argv.index("--since") + 1])
    rating_drop = 5.0
    if "--rating-drop" in sys.argv:
        rating_drop = float(sys.argv[sys.argv.index("--rating-drop") + 1])

    conn = psycopg2.connect(dbname="silent_edge_zero")
    runs_by_horse = load_horse_career_runs(conn, since=since)
    conn.close()

    n_horses = len(runs_by_horse)
    n_runs = sum(len(v) for v in runs_by_horse.values())
    print(f"Loaded {n_runs} real rated runs across {n_horses} distinct horse names"
          f"{f' since {since}' if since else ' (full history)'}.")

    features = compute_handicap_features(runs_by_horse)
    print(f"{len(features)} real runs have at least one prior rated run (features computable).")

    result = run_rating_drop_hypothesis_test(features, rating_drop_threshold=rating_drop)

    out_path = REPO_ROOT / "data" / f"trainer_intelligence_a_{date.today().isoformat()}.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print(f"\nHYPOTHESIS A: rating_drop >= {rating_drop} AND a real previous win exists")
    print(f"  {result['n_races_excluded_insufficient_market_data']} races excluded — insufficient market data to de-vig")
    for label, group in (("QUALIFYING", result["qualifying_group"]), ("CONTROL", result["control_group"])):
        if group is None:
            print(f"  {label}: no observations")
            continue
        flag = " (small sample)" if group["small_sample"] else ""
        print(f"  {label}: n={group['n']}  actual_wins={group['actual_wins']} ({group['actual_win_rate']:.1%})  "
              f"market_expected={group['expected_wins_market']}  diff={group['diff_actual_minus_expected_market']:+}  "
              f"95% CI={group['win_rate_confidence_interval']}{flag}")
    print(f"\n  CAVEAT: {result['statistical_caveat']}")
    print(f"\nFull detail written to {out_path}")


if __name__ == "__main__":
    main()
