#!/usr/bin/env python3
"""
Market favourite vs. Silent Edge top pick report — Silent Edge Zero V2
brief, Phase 2 (Sections 5-7). Read-only. No dashboard UI yet (Phase 3) —
prints a summary and writes a JSON detail file, same pattern as
scripts/data_integrity_audit.py.

Built entirely on src/research/race_dataset.py (Phase 1) and
src/research/market_vs_model.py (this phase) — never recomputes a
probability or touches `prediction`.

Usage: python3 scripts/market_vs_model_report.py [race_date] [--days N] [--price-source at_lock|latest|closing]
Defaults to today, N=1, at_lock (the fair, same-moment comparison against
Silent Edge's own locked pick — see market_vs_model.py's module docstring
for why 'latest'/SP are different questions).
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.research.market_vs_model import classify_races, summarise_classification
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
    all_classified = []
    d = start
    while d <= race_date:
        races = load_race_dataset(conn, d)
        attach_market_data(conn, races)
        all_classified.extend(classify_races(races, price_source=price_source))
        d += timedelta(days=1)
    conn.close()

    summary = summarise_classification(all_classified)
    result = {
        "range": {"start": str(start), "end": str(race_date)},
        "price_source": price_source,
        "summary": summary,
        "races": all_classified,
    }

    out_path = REPO_ROOT / "data" / f"market_vs_model_{race_date.isoformat()}.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print(f"MARKET VS SILENT EDGE [{start} .. {race_date}] (favourite at: {price_source})")
    print(f"  {summary['n_eligible']} eligible races ({summary['n_unresolved']} unresolved of {summary['n_races_total']} total)")
    if summary["n_unresolved"]:
        for reason, n in summary["unresolved_reasons"].items():
            print(f"    unresolved: {n} — {reason}")
    print(f"  Four-way: A(both correct)={summary['four_way']['A']}  "
          f"B(Silent Edge only)={summary['four_way']['B']}  "
          f"C(market only)={summary['four_way']['C']}  "
          f"D(both wrong)={summary['four_way']['D']}")
    if summary["n_eligible"]:
        print(f"  Silent Edge win rate: {summary['silent_edge_win_rate']:.1%}   "
              f"Market favourite win rate: {summary['market_favourite_win_rate']:.1%}   "
              f"Difference: {summary['win_rate_difference']:+.1%}")
        print(f"  Model/market agreement rate: {summary['model_market_agreement_rate']:.1%} "
              f"({summary['n_agree']}/{summary['n_eligible']})")
    print(f"\nFull detail written to {out_path}")


if __name__ == "__main__":
    main()
