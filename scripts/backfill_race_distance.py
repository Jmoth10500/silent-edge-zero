#!/usr/bin/env python3
"""
Backfill race.distance_yards from the raw Kaggle CSV's `dist` column.

**Real bug found 2026-09-09 (RL-008 draw-bias work):** `scripts/load_kaggle_historical.py`
(Session 6) never populated `race.distance_yards` at all — confirmed via a
real DB query, `race.distance_yards IS NULL` for all 57,267 loaded races.
This silently zeroed out the new course+distance draw-bias feature (every
lookup failed on a missing `distance_yards`, so the real training run
below found ZERO table entries and the feature contributed nothing) —
caught by sanity-checking `build_split_draw_bias_table()`'s output before
trusting a suspiciously-unchanged Brier score, not by assuming the null
result was real.

The CSV's `dist` column (e.g. `'2m3½f'`, `'1m4½f'`, `'6f'`) IS real,
parseable distance data — it was just never read. This is a genuine
data-engineering gap, not a missing source, same shape as RL-007's
recent_form gap.

Join key: `race.external_ref` stores the CSV's own `race_id` (see
`load_kaggle_historical.py`), and every row for a given `race_id` in the
CSV carries the same `dist` value (spot-checked), so only the first row
per `race_id` needs to be read.

Leakage: distance is a fixed, pre-race-known fact (the race conditions,
not an outcome) — backfilling it from the full CSV in one pass carries no
leakage risk the way recent_form's per-horse history did; there's no
"future" version of a race's own advertised distance.

One-shot backfill, not part of the live daily collector (which will get
distance_yards from The Racing API's own `distance_f` field going forward,
same as `scripts/collect_racecards.py` already does for live racecards).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

CSV_PATH = (
    Path(__file__).parent.parent / "data" / "kaggle_historical"
    / "form_2015-present" / "form_2015-present" / "raceform.csv"
)

# e.g. '2m3½f' -> 2 miles, 3.5 furlongs. '6f' -> 0 miles, 6 furlongs.
# '1m' -> 1 mile, 0 furlongs. '1m½f' -> 1 mile, 0.5 furlongs (furlong digits
# are optional so a bare half-furlong marker after 'm' still matches).
# Half-furlong marker is the single '½' glyph.
_DIST_RE = re.compile(r"^(?:(\d+)m)?(?:(\d+)?(½)?f)?$")

YARDS_PER_MILE = 1760
YARDS_PER_FURLONG = 220


def parse_distance_to_yards(dist: str) -> int | None:
    """Returns whole yards, or None if `dist` doesn't match the expected
    shape (never guessed) — e.g. an empty string or an unexpected format."""
    if not dist:
        return None
    m = _DIST_RE.match(dist.strip())
    if not m or (m.group(1) is None and m.group(2) is None and m.group(3) is None):
        return None
    miles = int(m.group(1)) if m.group(1) else 0
    furlongs = int(m.group(2)) if m.group(2) else 0
    half = 0.5 if m.group(3) else 0.0
    total_furlongs = furlongs + half
    return miles * YARDS_PER_MILE + round(total_furlongs * YARDS_PER_FURLONG)


def load_distances_by_csv_race_id(csv_path: Path) -> dict[str, int]:
    """First `dist` value seen per CSV race_id, parsed to yards. Skips any
    race_id whose dist string doesn't parse (never guessed) rather than
    silently defaulting."""
    import csv

    out: dict[str, int] = {}
    skipped_unparsed = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            race_id = row["race_id"]
            if race_id in out:
                continue
            yards = parse_distance_to_yards(row["dist"])
            if yards is None:
                skipped_unparsed += 1
                continue
            out[race_id] = yards
    print(f"Parsed distance for {len(out):,} distinct CSV race_ids "
          f"({skipped_unparsed:,} unparsed dist strings skipped, never guessed).")
    return out


def main():
    if not CSV_PATH.exists():
        print(f"CSV not found at {CSV_PATH} — nothing to backfill from.")
        return

    distances = load_distances_by_csv_race_id(CSV_PATH)

    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()
    cur.execute("SELECT id, external_ref FROM race WHERE distance_yards IS NULL")
    rows = cur.fetchall()
    print(f"{len(rows):,} real DB races currently have distance_yards IS NULL.")

    updates = [(distances[ext_ref], race_id) for race_id, ext_ref in rows if ext_ref in distances]
    missing = len(rows) - len(updates)
    print(f"Matched {len(updates):,} races to a real parsed distance "
          f"({missing:,} had no matching/parseable CSV row — left NULL, not guessed).")

    if updates:
        from psycopg2.extras import execute_batch
        execute_batch(cur, "UPDATE race SET distance_yards = %s WHERE id = %s", updates)
        conn.commit()
        print(f"Updated {len(updates):,} real race rows.")

    cur.execute("SELECT count(*) FROM race")
    total = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM race WHERE distance_yards IS NULL")
    remaining = cur.fetchone()[0]
    print(f"race.distance_yards still NULL for {remaining:,} of {total:,} total races "
          f"(any real unmatched/unparseable CSV rows, or non-Kaggle rows).")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
