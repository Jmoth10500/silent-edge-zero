#!/usr/bin/env python3
"""
"Who did we both miss?" + Silent Edge rank vs market rank matrix — Silent
Edge Zero V2 brief, Phase 4, Sections 8-9. Read-only. No dashboard UI yet
(Phase 3) — prints a summary and writes a JSON detail file.

Usage: python3 scripts/missed_winners_report.py [race_date] [--days N] [--price-source at_lock|latest|closing]
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.research.missed_winners import (
    cross_check_against_full_population,
    find_missed_winner_races,
    summarise_missed_winner_rank_combinations,
)
from src.research.race_dataset import attach_market_data, load_race_dataset
from src.research.ranking_matrix import aggregate_rank_matrix, build_rank_observations

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

    missed = find_missed_winner_races(all_races, price_source=price_source)
    missed_summary = summarise_missed_winner_rank_combinations(missed)
    missed_summary_checked = cross_check_against_full_population(missed_summary, all_races, price_source=price_source)

    observations = build_rank_observations(all_races, price_source=price_source)
    full_matrix = aggregate_rank_matrix(observations)

    result = {
        "range": {"start": str(start), "end": str(race_date)},
        "price_source": price_source,
        "n_missed_winner_races": len(missed),
        "missed_winner_races": missed,
        "missed_winner_rank_combinations": missed_summary_checked,
        "full_rank_matrix": full_matrix,
    }

    out_path = REPO_ROOT / "data" / f"missed_winners_{race_date.isoformat()}.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print(f"WHO DID WE BOTH MISS? [{start} .. {race_date}] (favourite/market rank at: {price_source})")
    print(f"  {len(missed)} real missed-winner races (both Silent Edge's top pick and the market favourite lost)")
    print("  Top rank combinations the missed winner came from (descriptive — see full-population cell before trusting):")
    for key, entry in sorted(missed_summary_checked.items(),
                              key=lambda kv: kv[1]["n_missed_winners_from_this_combo"], reverse=True)[:8]:
        full = entry.get("full_population_cell")
        full_str = (f"full population: {full['n']} runners, {full['actual_wins']} actual wins, "
                    f"{full['expected_wins_model']} expected (model), diff {full['diff_actual_minus_expected_model']:+}"
                    if full else "no full-population data for this cell")
        print(f"    SE rank {entry['se_rank']} / market rank {entry['market_rank']}: "
              f"{entry['n_missed_winners_from_this_combo']} missed winners ({entry['share_of_all_missed_winners']:.1%} of all) — {full_str}")

    print(f"\nFull rank matrix has {len(full_matrix)} populated cells (full detail in the JSON file).")
    print(f"Full detail written to {out_path}")


if __name__ == "__main__":
    main()
