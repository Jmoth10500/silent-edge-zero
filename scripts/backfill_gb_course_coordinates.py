#!/usr/bin/env python3
"""
Backfill course.latitude/longitude for real British racecourses, using the
verified coordinate set in data/gb_racecourse_coordinates.py.

Real gap this fixes: only 13 of 412 course rows had coordinates (~8% of
real GB races since 2023) — see that module's docstring for the full
story and sourcing. Matches by normalised course name (strips (AW)/(July)/
etc. suffixes), so every DB name-variant of the same physical GB course
(e.g. 'Kempton (AW)', 'Kempton Park', 'Kempton') gets the same real
coordinates. Deliberately GB-only — see the coordinates module's docstring
for why the ~200 non-GB course rows are out of scope.

One-shot backfill, safe to re-run (idempotent — only ever sets rows that
are currently NULL).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from data.gb_racecourse_coordinates import GB_RACECOURSE_COORDINATES, normalise_course_name


def main():
    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM course WHERE latitude IS NULL")
    rows = cur.fetchall()
    print(f"{len(rows):,} course rows currently have no coordinates.")

    updates = []
    unmatched_names = set()
    for course_id, name in rows:
        key = normalise_course_name(name)
        coords = GB_RACECOURSE_COORDINATES.get(key)
        if coords is None:
            unmatched_names.add(name)
            continue
        lat, lon = coords
        updates.append((lat, lon, course_id))

    print(f"Matched {len(updates):,} course rows to a real GB racecourse coordinate "
          f"({len(unmatched_names):,} distinct unmatched names — expected, these are "
          f"non-GB courses out of scope, or GB name variants not yet in the lookup).")

    if updates:
        from psycopg2.extras import execute_batch
        execute_batch(cur, "UPDATE course SET latitude = %s, longitude = %s WHERE id = %s", updates)
        conn.commit()
        print(f"Updated {len(updates):,} real course rows.")

    cur.execute("""
        SELECT count(*) FROM race r JOIN course c ON c.id = r.course_id
        WHERE r.race_date >= '2023-01-01' AND c.latitude IS NOT NULL
    """)
    covered = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM race WHERE race_date >= '2023-01-01'")
    total = cur.fetchone()[0]
    print(f"Real race coverage with a known course coordinate: {covered:,} of {total:,} "
          f"({100 * covered / total:.1f}%).")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
