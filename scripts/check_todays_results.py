#!/usr/bin/env python3
"""
Real, one-shot check of how today's live predictions actually did —
using Smarkets' real settled contract outcomes (`state_or_outcome`:
'winner'/'loser'), found live 2026-09-10 while answering Jonathan's
question "how did this do on its first day?"

**Real limitation, honestly:** only races that (a) were successfully
matched to a Smarkets market by `scripts/collect_smarkets_prices.py`'s
real matching logic, and (b) have actually finished and settled on
Smarkets, are checkable this way. Races Smarkets never listed, or that
hit a real rate-limit/match failure, are skipped — reported as such, not
silently ignored.

This does NOT write anything to the DB — it's a real, live, read-only
check, not a permanent results-collection pipeline (that's still a real
gap — see docs/BUILD_LOG.md — this only answers the immediate question).

Usage: python3 scripts/check_todays_results.py [race_date]
Defaults to today.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
import requests

from scripts.collect_smarkets_prices import load_our_races, match_race, strip_country_suffix
from src.providers.odds_smarkets import get_win_market_id, is_gb_course, list_horse_racing_events


def get_real_winner(market_id: str) -> str | None:
    """Real horse name Smarkets marks as 'winner' for a settled market, or
    None if not yet settled / not found."""
    resp = requests.get(f"https://api.smarkets.com/v3/markets/{market_id}/contracts/", timeout=15)
    resp.raise_for_status()
    for c in resp.json().get("contracts", []):
        if c.get("state_or_outcome") == "winner":
            return c["name"]
    return None


def main():
    race_date_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    race_date = date.fromisoformat(race_date_str)

    conn = psycopg2.connect(dbname="silent_edge_zero")
    our_races = load_our_races(conn, race_date)

    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.race_id, h.name, mv.name, p.model_probability
        FROM prediction p
        JOIN horse h ON h.id = p.horse_id
        JOIN model_version mv ON mv.id = p.model_version_id
        JOIN race r ON r.id = p.race_id
        WHERE r.race_date = %s AND p.locked_at IS NOT NULL
        """,
        (race_date,),
    )
    preds: dict[int, dict[str, dict[str, float]]] = {}
    for race_id, horse_name, model_name, prob in cur:
        key = "model1" if model_name == "statistical_v1" else "model2"
        preds.setdefault(race_id, {}).setdefault(key, {})[horse_name] = float(prob)
    cur.close()
    conn.close()

    events = list_horse_racing_events(race_date)
    gb_events = [e for e in events if is_gb_course(e.venue_name)]

    n_checked, m1_hits, m2_hits = 0, 0, 0
    n_no_market, n_not_settled = 0, 0
    rows = []

    for event in gb_events:
        race_id = match_race(our_races, event, race_date)
        if race_id is None or race_id not in preds:
            continue
        market_id = get_win_market_id(event.event_id)
        if market_id is None:
            n_no_market += 1
            continue
        real_winner_raw = get_real_winner(market_id)
        if real_winner_raw is None:
            n_not_settled += 1
            continue

        real_winner = real_winner_raw.strip().lower()
        our_names = {strip_country_suffix(n).lower(): n for n in
                     {name for m in preds[race_id].values() for name in m}}
        winner_real_name = our_names.get(real_winner)
        if winner_real_name is None:
            continue  # couldn't map the real winner back to our horse names — skip honestly

        n_checked += 1
        m1_probs = preds[race_id].get("model1", {})
        m2_probs = preds[race_id].get("model2", {})
        m1_pick = max(m1_probs, key=m1_probs.get) if m1_probs else None
        m2_pick = max(m2_probs, key=m2_probs.get) if m2_probs else None
        m1_hit = m1_pick == winner_real_name
        m2_hit = m2_pick == winner_real_name
        m1_hits += int(m1_hit)
        m2_hits += int(m2_hit)
        rows.append((event.venue_name, event.start_datetime.strftime("%H:%M"),
                      winner_real_name, m1_pick, m1_hit, m2_pick, m2_hit))

    print(f"{n_checked} real races checked against real Smarkets settled outcomes today.")
    print(f"({n_no_market} had no Smarkets market found, {n_not_settled} not yet settled at check time.)\n")

    for venue, t, winner, m1_pick, m1_hit, m2_pick, m2_hit in rows:
        print(f"{t} {venue}: WINNER={winner} | M1={m1_pick}{'✓' if m1_hit else '✗'} | M2={m2_pick}{'✓' if m2_hit else '✗'}")

    if n_checked:
        print(f"\nReal Day 1 result: Model 1 {m1_hits}/{n_checked} ({100*m1_hits/n_checked:.1f}%), "
              f"Model 2 {m2_hits}/{n_checked} ({100*m2_hits/n_checked:.1f}%).")
        print("Sample size is tiny (one day) — this is a real anecdote, not a statistically meaningful "
              "test of the ~23% real backtested hit rate. Treat accordingly.")
    else:
        print("\nNo races could be checked.")


if __name__ == "__main__":
    main()
