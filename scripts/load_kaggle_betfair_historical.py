#!/usr/bin/env python3
"""
Loads the real historical Betfair price data from
data/kaggle_historical/betfair/betfair/betfair_mapping_2026_part_{i,ii}.csv
into `historical_betfair_price` — Silent Edge Zero V2 brief, Phase 5
(Section 14), unlocking Phase 6's Hypothesis B (market-behaviour research,
Section 12B), which needs real multi-point pre-race pricing the live,
forward-only Smarkets collector (running since 2026-09-10) cannot supply
in any useful volume yet.

**Real, honest coverage correction:** this file's own contents cover
2026-03-01 to 2026-04-29 only (confirmed directly from the CSVs) — NOT
the multi-year 2015-2025 backfill the dataset's own README implies for
its other files. Worldwide courses; filtered to GB here via
`data.gb_racecourse_coordinates.is_gb_course` equivalent check (reusing
the exact course-name set already used elsewhere in this project).

**Matching, verified live before writing this loader (never assumed):**
this CSV's own `course`/`off`/`horse` columns use EXACTLY the same
spelling/format as scripts/load_kaggle_historical.py's raceform loader —
confirmed by a direct check (Ayr, 2026-03-06, 16:20, 10 real matching
horse names including country suffixes). This loader therefore matches
against our EXISTING `race`/`horse` rows (created by the raceform loader)
by (course.name, race_date, off_time) and (race_id, horse.name) directly
— it never creates a new race or horse row itself; a row whose race or
horse can't be found in our existing data is skipped and counted, never
guessed into existence.

Usage: python3 scripts/load_kaggle_betfair_historical.py
"""
import csv
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.load_kaggle_historical import parse_sp_to_decimal, safe_float

CSV_PATHS = [
    Path(__file__).parent.parent / "data/kaggle_historical/betfair/betfair/betfair_mapping_2026_part_i.csv",
    Path(__file__).parent.parent / "data/kaggle_historical/betfair/betfair/betfair_mapping_2026_part_ii.csv",
]


def get_or_create_source(conn) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO data_source (name, url, free_tier, terms_checked, notes) "
        "VALUES ('kaggle-betfair-historical', 'https://www.kaggle.com/datasets/', TRUE, %s, "
        "'CDLA-Sharing-1.0. Community-compiled real historical Betfair prices, 2026-03-01 to "
        "2026-04-29 only (confirmed from the file itself, not the wider README claim) — see "
        "scripts/load_kaggle_betfair_historical.py module docstring.') "
        "ON CONFLICT (name) DO NOTHING",
        (date.today(),),
    )
    cur.execute("SELECT id FROM data_source WHERE name = 'kaggle-betfair-historical'")
    source_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return source_id


def main():
    conn = psycopg2.connect(dbname="silent_edge_zero")
    source_id = get_or_create_source(conn)
    cur = conn.cursor()

    race_id_cache: dict[tuple, int | None] = {}
    horse_id_cache: dict[tuple, int | None] = {}

    n_rows, n_loaded, n_no_race_match, n_no_horse_match = 0, 0, 0, 0

    for csv_path in CSV_PATHS:
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                n_rows += 1

                race_key = (row["course"], row["date"], row["off"])
                if race_key not in race_id_cache:
                    cur.execute(
                        "SELECT r.id FROM race r JOIN course c ON c.id = r.course_id "
                        "WHERE c.name = %s AND r.race_date = %s AND r.off_time = %s",
                        race_key,
                    )
                    found = cur.fetchone()
                    race_id_cache[race_key] = found[0] if found else None
                race_id = race_id_cache[race_key]
                if race_id is None:
                    n_no_race_match += 1
                    continue

                horse_key = (race_id, row["horse"])
                if horse_key not in horse_id_cache:
                    cur.execute(
                        "SELECT h.id FROM runner_snapshot rs JOIN horse h ON h.id = rs.horse_id "
                        "WHERE rs.race_id = %s AND h.name = %s",
                        horse_key,
                    )
                    found = cur.fetchone()
                    horse_id_cache[horse_key] = found[0] if found else None
                horse_id = horse_id_cache[horse_key]
                if horse_id is None:
                    n_no_horse_match += 1
                    continue

                cur.execute(
                    """
                    INSERT INTO historical_betfair_price
                        (race_id, horse_id, starting_price, bsp, wap, morning_wap, pre_min, pre_max,
                         ip_min, ip_max, morning_vol, pre_vol, ip_vol, source_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (race_id, horse_id) DO UPDATE SET
                        starting_price = EXCLUDED.starting_price, bsp = EXCLUDED.bsp, wap = EXCLUDED.wap,
                        morning_wap = EXCLUDED.morning_wap, pre_min = EXCLUDED.pre_min, pre_max = EXCLUDED.pre_max,
                        ip_min = EXCLUDED.ip_min, ip_max = EXCLUDED.ip_max, morning_vol = EXCLUDED.morning_vol,
                        pre_vol = EXCLUDED.pre_vol, ip_vol = EXCLUDED.ip_vol
                    """,
                    (
                        race_id, horse_id, parse_sp_to_decimal(row["sp"]), safe_float(row["bsp"]),
                        safe_float(row["wap"]), safe_float(row["morning_wap"]), safe_float(row["pre_min"]),
                        safe_float(row["pre_max"]), safe_float(row["ip_min"]), safe_float(row["ip_max"]),
                        safe_float(row["morning_vol"]), safe_float(row["pre_vol"]), safe_float(row["ip_vol"]),
                        source_id,
                    ),
                )
                n_loaded += 1

                if n_rows % 5000 == 0:
                    conn.commit()

    conn.commit()
    cur.close()
    conn.close()

    print(f"{n_rows} real CSV rows processed.")
    print(f"{n_loaded} real rows loaded into historical_betfair_price.")
    print(f"{n_no_race_match} rows skipped — no matching race in our own DB (e.g. non-GB, or a race our "
          f"raceform loader doesn't have).")
    print(f"{n_no_horse_match} rows skipped — race matched but no runner_snapshot row for that horse name.")


if __name__ == "__main__":
    main()
