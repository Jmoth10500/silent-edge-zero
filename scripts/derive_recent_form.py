#!/usr/bin/env python3
"""
Derive a real recent_form / days_since_last_run for every runner_snapshot row
loaded from Kaggle (RL-007) — the raw CSV has no such column, so this has to
be built from each horse's own prior rows in the same dataset, not loaded.

Leakage safety by construction: for the snapshot attached to a given race,
only that horse's OWN races with an earlier off_dt are ever used. A horse's
very first race in the dataset gets recent_form=NULL, days_since_last_run=
NULL — an honest "no prior form", never a fabricated one.

Form string format matches src/features/runner_features.py::parse_recent_form
exactly: oldest run FIRST (left-to-right), digits 1-9 for that finishing
position, '0' for 10th-or-worse, and a single non-completion letter
(F/P/U/O/R/S/B) for a DNF, taken from runner_result.result_note. A run whose
outcome can't be classified into either shape is skipped from the string
entirely rather than guessed. Last 6 prior runs kept per race, matching the
form-string lengths real racecards typically show.

This is a one-shot backfill over already-loaded runner_snapshot rows, not
part of the live daily collector (which will populate this from the real
API's own recent-form field once results collection exists there).
"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import execute_values

_NON_COMPLETION_CODES = set("FPUORSB")
_FORM_HISTORY_LEN = 6


def position_to_form_char(finishing_position, result_note):
    """One form-string character for a single past run, or None if this
    run's outcome can't be honestly classified (never guess)."""
    if finishing_position is not None:
        return "0" if finishing_position >= 10 else str(finishing_position)
    if result_note:
        for ch in result_note.strip().upper():
            if ch in _NON_COMPLETION_CODES:
                return ch
    return None


def main():
    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()

    print("Loading every (snapshot, race_date, off_time, finishing_position, result_note) "
          "row, ordered per-horse chronologically...")
    cur.execute(
        """
        SELECT rs.id, rs.horse_id, r.race_date, r.off_time,
               rr.finishing_position, rr.result_note
        FROM runner_snapshot rs
        JOIN race r ON r.id = rs.race_id
        LEFT JOIN runner_result rr ON rr.race_id = rs.race_id AND rr.horse_id = rs.horse_id
        ORDER BY rs.horse_id, r.race_date, r.off_time
        """
    )
    rows = cur.fetchall()
    print(f"Loaded {len(rows):,} runner_snapshot rows.")

    updates: list[tuple] = []
    current_horse = None
    history: list[tuple] = []  # (race_date, form_char)

    def flush_horse():
        nonlocal history
        history = []

    total_with_form = 0
    for snapshot_id, horse_id, race_date, off_time, finishing_position, result_note in rows:
        if horse_id != current_horse:
            flush_horse()
            current_horse = horse_id

        if history:
            recent_form = "".join(ch for _, ch in history[-_FORM_HISTORY_LEN:])
            days_since_last_run = (race_date - history[-1][0]).days
            updates.append((snapshot_id, recent_form, days_since_last_run))
            total_with_form += 1

        form_char = position_to_form_char(finishing_position, result_note)
        if form_char is not None:
            history.append((race_date, form_char))

    print(f"{total_with_form:,} of {len(rows):,} rows have at least one real prior run "
          f"(the rest are each horse's first appearance in the dataset — left NULL, "
          f"honestly, not guessed).")

    print("Writing updates in batches of 5,000...")
    for i in range(0, len(updates), 5000):
        batch = updates[i:i + 5000]
        execute_values(
            cur,
            """
            UPDATE runner_snapshot AS rs
            SET recent_form = data.recent_form,
                days_since_last_run = data.days_since_last_run
            FROM (VALUES %s) AS data(id, recent_form, days_since_last_run)
            WHERE rs.id = data.id
            """,
            batch,
            template="(%s, %s, %s)",
        )
        conn.commit()
        if (i // 5000) % 20 == 0:
            print(f"  ...{i + len(batch):,} / {len(updates):,} written")

    print(f"\nDone. {len(updates):,} runner_snapshot rows updated with real, leakage-safe "
          f"recent_form and days_since_last_run.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
