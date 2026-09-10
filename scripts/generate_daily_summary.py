#!/usr/bin/env python3
"""
Computes one real, persisted `daily_summary` row for a race date, from
whatever real `runner_result` rows currently exist for it — reusing
scripts/generate_eod_report.py's own top-pick/favourite loading and
settlement math (same numbers, same discipline, no re-derivation).

Built to answer Jonathan's request (2026-09-10): "there needs to be a
round up of the day with a report using graphs and data that is stored so
it can be used to build an overall success report." A single day's
generate_eod_report.py output is real but transient (printed, not saved);
this script is what makes it durable and accumulable across days for the
dashboard's track-record chart (see generate_dashboard.py's
render_track_record).

**Honest by construction:** a race whose top pick has no settled result
yet (`runner_result` has no row, or `finishing_position IS NULL` — e.g.
non-runner/pulled-up) is simply excluded from that day's counts, exactly
as generate_eod_report.py already treats it as PENDING rather than a
loss. `races_settled` <= `races_total` always shows how much of the day
is actually counted. Safe to re-run any time (UPSERT) — running it again
after more results land just updates the same day's row with better
numbers, never duplicates it.

Usage: python3 scripts/generate_daily_summary.py [race_date]
Defaults to today.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.generate_eod_report import (
    ew_terms_for_field_size,
    load_results,
    load_top_picks_and_favourites,
    settle_each_way,
    settle_win,
)


def compute_daily_summary(races: list[dict], results: dict) -> dict:
    """Real per-day aggregate from the same race/result data
    generate_eod_report.py prints, never re-deriving or guessing anything."""
    races_total = len(races)
    races_settled = 0
    top_pick_wins = 0
    top_pick_placed = 0
    favourite_wins = 0
    win_stake_total = 0.0
    win_profit = 0.0
    ew_stake_total = 0.0
    ew_profit = 0.0

    for race in races:
        tp = race["top_pick"]
        fav = race["favourite"]
        field_size = race["field_size"]

        tp_result = results.get((race["race_id"], tp["horse_id"]))
        tp_pos = tp_result[0] if tp_result else None
        if tp_pos is None:
            continue  # real result not in yet — honestly excluded, not a loss
        races_settled += 1

        if tp_pos == 1:
            top_pick_wins += 1
        _, _, n_places = ew_terms_for_field_size(field_size)
        if n_places and tp_pos <= n_places:
            top_pick_placed += 1

        if fav is not None:
            fav_result = results.get((race["race_id"], fav["horse_id"]))
            fav_pos = fav_result[0] if fav_result else None
            if fav_pos == 1:
                favourite_wins += 1

        wp, _ = settle_win(1.0, tp["exchange_back"], tp_pos)
        if wp is not None:
            win_stake_total += 1.0
            win_profit += wp

        ep, _ = settle_each_way(2.0, tp["exchange_back"], tp_pos, field_size)
        if ep is not None:
            ew_stake_total += 2.0
            ew_profit += ep

    return {
        "races_total": races_total,
        "races_settled": races_settled,
        "top_pick_wins": top_pick_wins,
        "top_pick_placed": top_pick_placed,
        "favourite_wins": favourite_wins,
        "win_stake_total": round(win_stake_total, 2),
        "win_profit": round(win_profit, 2),
        "ew_stake_total": round(ew_stake_total, 2),
        "ew_profit": round(ew_profit, 2),
    }


def upsert_daily_summary(conn, race_date: date, summary: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO daily_summary
            (race_date, races_total, races_settled, top_pick_wins, top_pick_placed,
             favourite_wins, win_stake_total, win_profit, ew_stake_total, ew_profit)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (race_date) DO UPDATE SET
            races_total = EXCLUDED.races_total,
            races_settled = EXCLUDED.races_settled,
            top_pick_wins = EXCLUDED.top_pick_wins,
            top_pick_placed = EXCLUDED.top_pick_placed,
            favourite_wins = EXCLUDED.favourite_wins,
            win_stake_total = EXCLUDED.win_stake_total,
            win_profit = EXCLUDED.win_profit,
            ew_stake_total = EXCLUDED.ew_stake_total,
            ew_profit = EXCLUDED.ew_profit,
            computed_at = now()
        """,
        (
            race_date, summary["races_total"], summary["races_settled"],
            summary["top_pick_wins"], summary["top_pick_placed"], summary["favourite_wins"],
            summary["win_stake_total"], summary["win_profit"],
            summary["ew_stake_total"], summary["ew_profit"],
        ),
    )
    conn.commit()
    cur.close()


def main():
    race_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()

    conn = psycopg2.connect(dbname="silent_edge_zero")
    races = load_top_picks_and_favourites(conn, race_date)
    if not races:
        print(f"No locked gbm_v1 predictions found for {race_date} — nothing to summarise.")
        conn.close()
        return
    results = load_results(conn, race_date)
    summary = compute_daily_summary(races, results)
    upsert_daily_summary(conn, race_date, summary)
    conn.close()

    print(f"{race_date}: {summary['races_settled']}/{summary['races_total']} races settled — "
          f"top pick won {summary['top_pick_wins']} ({summary['top_pick_wins'] / summary['races_settled']:.1%}), "
          f"placed {summary['top_pick_placed']} ({summary['top_pick_placed'] / summary['races_settled']:.1%}), "
          f"favourite won {summary['favourite_wins']}. "
          f"£1 win P&L £{summary['win_profit']:.2f}, £2 EW P&L £{summary['ew_profit']:.2f}."
          if summary["races_settled"] else
          f"{race_date}: 0/{summary['races_total']} races settled yet — daily_summary row written as all-zero, "
          f"not fabricated.")


if __name__ == "__main__":
    main()
