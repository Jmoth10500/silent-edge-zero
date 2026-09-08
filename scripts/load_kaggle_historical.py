#!/usr/bin/env python3
"""
Load real historical UK/Ireland race results from the Kaggle community
dataset into the database, as immutable runner_result / race rows.

Source: kaggle.com/datasets/deltaromeo/horse-racing-results-ukireland-2015-2025
Licence: Community Data License Agreement - Sharing - Version 1.0 (confirmed
2026-09-08 from the real Kaggle download output — CDLA-Sharing requires any
redistributed derivative dataset to carry the same licence; internal
research/backtesting use, which is all this project does with it, is fine).

Auth: a single API token (KAGGLE_API_TOKEN env var, or ~/.kaggle/access_token)
— a newer, simpler Kaggle auth method than the old username+key kaggle.json.

By default loads from --start-date (default 2023-01-01) onward, to keep the
initial load fast — the full file goes back to 2015-01-01. Re-run with an
earlier --start-date to backfill more; this is idempotent (ON CONFLICT DO
UPDATE on race, and runner_result has a UNIQUE(race_id, horse_id) so re-runs
don't duplicate).

Every row's observed_at/available_at is set to the race's actual off_dt —
this is genuinely when that result became known, not "today". ingested_at
is when THIS script ran. Getting this right matters: an incorrectly-dated
historical load would poison the leakage tests' whole premise.
"""
import csv
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import execute_values

DATASET = "deltaromeo/horse-racing-results-ukireland-2015-2025"
DOWNLOAD_DIR = Path(__file__).parent.parent / "data" / "kaggle_historical"
CSV_RELATIVE_PATH = "form_2015-present/form_2015-present/raceform.csv"


def download_if_needed():
    csv_path = DOWNLOAD_DIR / CSV_RELATIVE_PATH
    if csv_path.exists():
        print(f"Already downloaded: {csv_path}")
        return csv_path

    token_path = Path.home() / ".kaggle" / "access_token"
    import os
    if not token_path.exists() and not os.environ.get("KAGGLE_API_TOKEN"):
        print(
            "BLOCKED: no Kaggle credential found (~/.kaggle/access_token or "
            "KAGGLE_API_TOKEN env var). See docs/FREE_DATA_SOURCES.md #2."
        )
        sys.exit(1)

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(DOWNLOAD_DIR), "--unzip"],
        capture_output=True, text=True,
    )
    print(r.stdout)
    if r.returncode != 0:
        print("Download failed:", r.stderr, file=sys.stderr)
        sys.exit(1)
    return csv_path


def parse_sp_to_decimal(sp: str) -> float | None:
    """Convert a fractional starting price like '11/4F', '5/2', 'Evens',
    'EVS' to decimal odds. Returns None for anything unparseable rather
    than guessing — a wrong odds value is worse than a missing one."""
    if not sp:
        return None
    sp = sp.strip().upper().rstrip("FJC")  # strip Favourite/Joint-fav/Co-fav suffix
    if sp in ("EVS", "EVENS"):
        return 2.0
    if "/" in sp:
        try:
            num, denom = sp.split("/")
            return round(float(num) / float(denom) + 1.0, 3)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(sp)
    except ValueError:
        return None


def safe_float(val: str) -> float | None:
    """CSV 'missing' markers vary across rows in this real dataset: '', '–'
    (en-dash), '-' (hyphen), sometimes others. Never guess a value — any
    non-numeric string just means None, not a crash and not a fabricated 0."""
    if not val:
        return None
    val = val.strip()
    if not val or val in ("-", "–", "—"):
        return None
    try:
        return float(val)
    except ValueError:
        return None


def safe_int(val: str) -> int | None:
    parsed = safe_float(val)
    return int(parsed) if parsed is not None else None


def parse_weight_lbs(wgt: str) -> int | None:
    """'11-6' (stone-lbs) -> 11*14+6 = 160 lbs."""
    if not wgt or "-" not in wgt:
        return None
    try:
        st, lbs = wgt.split("-")
        return int(st) * 14 + int(lbs)
    except ValueError:
        return None


def main():
    start_date = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"
    csv_path = download_if_needed()

    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO data_source (name, url, free_tier, terms_checked, notes) "
        "VALUES ('kaggle-ukire-results', %s, TRUE, %s, "
        "'CDLA-Sharing-1.0. Community-compiled, not official — treat as backtest/research aid.') "
        "ON CONFLICT (name) DO NOTHING",
        (f"https://www.kaggle.com/datasets/{DATASET}", datetime.now(timezone.utc).date()),
    )
    cur.execute("SELECT id FROM data_source WHERE name = 'kaggle-ukire-results'")
    source_id = cur.fetchone()[0]

    course_cache: dict[str, int] = {}
    race_cache: dict[tuple, int] = {}
    horse_cache: dict[str, int] = {}
    trainer_cache: dict[str, int] = {}
    jockey_cache: dict[str, int] = {}

    def get_course_id(name):
        if name not in course_cache:
            cur.execute(
                "INSERT INTO course (name, country) VALUES (%s, 'GB') "
                "ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                (name,),
            )
            course_cache[name] = cur.fetchone()[0]
        return course_cache[name]

    def get_horse_id(name):
        if name not in horse_cache:
            cur.execute(
                "INSERT INTO horse (name, source_id) VALUES (%s, %s) "
                "ON CONFLICT (name, foaled_year) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                (name, source_id),
            )
            horse_cache[name] = cur.fetchone()[0]
        return horse_cache[name]

    def get_trainer_id(name):
        if not name:
            return None
        if name not in trainer_cache:
            cur.execute(
                "INSERT INTO trainer (name) VALUES (%s) "
                "ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                (name,),
            )
            trainer_cache[name] = cur.fetchone()[0]
        return trainer_cache[name]

    def get_jockey_id(name):
        if not name:
            return None
        if name not in jockey_cache:
            cur.execute(
                "INSERT INTO jockey (name) VALUES (%s) "
                "ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                (name,),
            )
            jockey_cache[name] = cur.fetchone()[0]
        return jockey_cache[name]

    rows_processed, rows_loaded, rows_skipped_old, races_created = 0, 0, 0, 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_processed += 1
            if rows_processed % 100_000 == 0:
                conn.commit()
                print(f"  ...{rows_processed:,} rows processed, {rows_loaded:,} loaded")

            date_str = row["date"]
            if date_str < start_date:
                rows_skipped_old += 1
                continue

            course_id = get_course_id(row["course"])
            race_key = (course_id, date_str, row["off"])
            if race_key not in race_cache:
                cur.execute(
                    """INSERT INTO race
                       (course_id, race_date, off_time, race_name, race_class, race_type,
                        going, field_size, prize_money, external_ref, source_id, ingested_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (course_id, race_date, off_time) DO UPDATE SET race_name = EXCLUDED.race_name
                       RETURNING id""",
                    (course_id, date_str, row["off"], row["race_name"], row["class"] or None,
                     row["type"] or None, row["going"] or None,
                     safe_int(row["ran"]),
                     safe_float(row["prize"]),
                     row["race_id"], source_id, datetime.now(timezone.utc)),
                )
                race_cache[race_key] = cur.fetchone()[0]
                races_created += 1
            race_id = race_cache[race_key]

            horse_id = get_horse_id(row["horse"])
            trainer_id = get_trainer_id(row["trainer"])
            jockey_id = get_jockey_id(row["jockey"])

            pos_raw = row["pos"].strip()
            finishing_position = safe_int(pos_raw)
            result_note = None if finishing_position else (pos_raw or None)

            # The race's off_dt is when this result genuinely became known —
            # this is what makes it valid leakage-safe historical data,
            # not "today's" data pretending to be from the past.
            try:
                off_dt = datetime.strptime(f"{date_str} {row['off']}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                off_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

            cur.execute(
                """INSERT INTO runner_result
                   (race_id, horse_id, finishing_position, distance_beaten, starting_price,
                    result_note, observed_at, available_at, ingested_at, source_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (race_id, horse_id) DO UPDATE SET
                     finishing_position = EXCLUDED.finishing_position,
                     starting_price = EXCLUDED.starting_price""",
                (race_id, horse_id, finishing_position,
                 safe_float(row["ovr_btn"]),
                 parse_sp_to_decimal(row["sp"]), result_note,
                 off_dt, off_dt, datetime.now(timezone.utc), source_id),
            )

            # Also store the pre-race-relevant fields (rating, weight, form
            # context) as a runner_snapshot — this IS genuinely pre-race
            # information (official rating, weight, draw were known before
            # the race ran), so it belongs in runner_snapshot, not bundled
            # into the result row.
            official_rating = None
            or_raw = row["or"].strip()
            if or_raw and or_raw != "–":
                try:
                    official_rating = int(or_raw)
                except ValueError:
                    pass

            cur.execute(
                """INSERT INTO runner_snapshot
                   (race_id, horse_id, trainer_id, jockey_id, age, draw, weight_lbs,
                    official_rating, equipment, observed_at, available_at, ingested_at, source_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (race_id, horse_id, trainer_id, jockey_id,
                 safe_int(row["age"]),
                 safe_int(row["draw"]),
                 parse_weight_lbs(row["wgt"]), official_rating, row["hg"] or None,
                 off_dt, off_dt, datetime.now(timezone.utc), source_id),
            )

            rows_loaded += 1

    conn.commit()
    print(f"\nDone. {rows_processed:,} rows read ({rows_skipped_old:,} before {start_date} skipped), "
          f"{rows_loaded:,} loaded, {races_created:,} new races.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
