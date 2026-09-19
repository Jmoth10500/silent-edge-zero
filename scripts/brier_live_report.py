#!/usr/bin/env python3
"""
Live paired Brier report — Silent Edge Zero V2 brief, Phase 4, Section 10
(the brief's own "primary scientific objective"). Read-only. No dashboard
UI yet (Phase 3) — prints a summary and writes a JSON detail file, same
pattern as scripts/data_integrity_audit.py and market_vs_model_report.py.

Usage: python3 scripts/brier_live_report.py [race_date] [--days N] [--price-source at_lock|latest|closing]
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.research.brier_live import (
    brier_by_group,
    compute_paired_observations,
    coverage_report,
    field_size_key,
    market_probability_band_key,
    paired_brier_summary,
    probability_band_key,
    rolling_paired_brier,
)
from src.research.market_vs_model import determine_favourites
from src.research.race_dataset import attach_market_data, load_race_dataset

REPO_ROOT = Path(__file__).parent.parent


def agreement_key_fn(favourite_by_race: dict):
    def _key(obs: dict) -> str:
        favs = favourite_by_race.get(obs["race_id"], [])
        # agreement is a per-race, not per-runner, notion normally, but for
        # a Brier breakdown we tag each runner's OWN observation by whether
        # IT is the model's top pick (rank 1) matching a race favourite —
        # a coarser, real, honestly-labelled proxy, not the race-level
        # agreement metric from market_vs_model.py (kept separate, per the
        # brief's own warning not to conflate the two agreement notions).
        if obs.get("model_rank") == 1 and obs["horse_id"] in favs:
            return "top-pick agrees with favourite"
        return "top-pick disagrees / not rank 1"
    return _key


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

    coverage = coverage_report(all_races, price_source=price_source)
    observations = compute_paired_observations(all_races, price_source=price_source)
    summary = paired_brier_summary(observations)
    rolling = rolling_paired_brier(observations, window_sizes=(25, 50, 100, 250))

    favourite_by_race = {r["race"]["race_id"]: determine_favourites(r["runners"], price_source=price_source) for r in all_races}
    by_prob_band = brier_by_group(observations, probability_band_key(0.10))
    by_market_band = brier_by_group(observations, market_probability_band_key(0.10))
    by_field_size = brier_by_group(observations, field_size_key)
    by_agreement = brier_by_group(observations, agreement_key_fn(favourite_by_race))

    result = {
        "range": {"start": str(start), "end": str(race_date)},
        "price_source": price_source,
        "coverage": coverage,
        "summary": summary,
        "rolling": rolling,
        "by_silent_edge_probability_band": by_prob_band,
        "by_market_probability_band": by_market_band,
        "by_field_size": by_field_size,
        "by_top_pick_vs_favourite_agreement": by_agreement,
    }

    out_path = REPO_ROOT / "data" / f"brier_live_{race_date.isoformat()}.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print(f"LIVE PAIRED BRIER [{start} .. {race_date}] (market price at: {price_source})")
    print(f"  Coverage: {coverage['n_included_observations']} paired observations from {coverage['n_races']} races "
          f"({coverage['n_races_excluded_insufficient_market_data']} races excluded — insufficient market data; "
          f"{coverage['n_runner_observations_excluded_pending_or_nonrunner']} runner-observations excluded — pending/non-runner)")
    if summary:
        print(f"  Silent Edge Brier: {summary['silent_edge_brier']:.6f}   Market Brier: {summary['market_brier']:.6f}   "
              f"Gap: {summary['brier_gap']:+.6f}   Leader: {summary['leader']}")
    else:
        print("  No paired observations available — cannot compute a Brier score.")
    print("  Rolling (most recent N races):")
    for window, r in rolling.items():
        if r is None:
            print(f"    last {window} races: not enough races yet")
        else:
            print(f"    last {window} races: gap {r['brier_gap']:+.6f} (n={r['n']}, leader={r['leader']})")

    print(f"\nFull detail written to {out_path}")


if __name__ == "__main__":
    main()
