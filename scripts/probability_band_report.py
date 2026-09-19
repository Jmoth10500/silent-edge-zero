#!/usr/bin/env python3
"""
Probability-band research report — Silent Edge Zero V2 brief, Phase 4,
Section 11. Read-only. No dashboard UI yet (Phase 3).

Usage: python3 scripts/probability_band_report.py [race_date] [--days N] [--price-source at_lock|latest|closing]
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.research.brier_live import compute_paired_observations
from src.research.probability_bands import probability_band_analysis
from src.research.race_dataset import attach_market_data, load_race_dataset

REPO_ROOT = Path(__file__).parent.parent


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    race_date = date.fromisoformat(args[0]) if args else date.today()
    days = 1
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    price_source = "at_lock"
    if "--price-source" in sys.argv:
        price_source = sys.argv[sys.argv.index("--price-source") + 1]

    start = race_date - timedelta(days=days - 1)

    conn = psycopg2.connect(dbname="silent_edge_zero")
    all_races = []
    d = start
    while d <= race_date:
        races = load_race_dataset(conn, d)
        attach_market_data(conn, races)
        all_races.extend(races)
        d += timedelta(days=1)
    conn.close()

    observations = compute_paired_observations(all_races, price_source=price_source)
    bands = probability_band_analysis(observations)

    out_path = REPO_ROOT / "data" / f"probability_bands_{race_date.isoformat()}.json"
    out_path.write_text(json.dumps({
        "range": {"start": str(start), "end": str(race_date)}, "price_source": price_source, "bands": bands,
    }, indent=2, default=str))

    print(f"PROBABILITY-BAND RESEARCH [{start} .. {race_date}]")
    print(f"{'band':>10} {'n':>5} {'exp_wins':>9} {'act_wins':>9} {'act_rate':>9} {'95% CI':>18} {'calib_err':>10} {'brier':>9}")
    for key in sorted(bands, key=lambda k: bands[k]["avg_predicted_probability"]):
        b = bands[key]
        ci = f"[{b['win_rate_confidence_interval'][0]:.2f},{b['win_rate_confidence_interval'][1]:.2f}]" if b["win_rate_confidence_interval"] else "n/a"
        flag = " (small n)" if b["small_sample"] else ""
        print(f"{b['band']:>10} {b['n_selections']:>5} {b['expected_wins_model']:>9.1f} {b['actual_wins']:>9} "
              f"{b['actual_win_rate']:>9.1%} {ci:>18} {b['calibration_error']:>+10.3f} {b['brier_contribution']:>9.4f}{flag}")

    print(f"\nFull detail written to {out_path}")


if __name__ == "__main__":
    main()
