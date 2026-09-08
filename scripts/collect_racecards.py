#!/usr/bin/env python3
"""
Real daily racecard collector — Phase 3, finally live.
Pulls today's GB racecards from The Racing API free tier and stores them as
PRE_RACE_SNAPSHOT rows (runner_snapshot), never overwriting a prior snapshot
for the same race+horse — a re-run just adds another row with a later
ingested_at, per the schema's own design (see db/schema.sql comments).
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from src.providers.racecard_theracingapi import TheRacingApiProvider


def main():
    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO data_source (name, url, free_tier, terms_checked, notes) "
        "VALUES ('theracingapi', 'https://www.theracingapi.com/', TRUE, %s, "
        "'Free tier: racecards+results (basic), no odds. Confirmed live 2026-09-08.') "
        "ON CONFLICT (name) DO NOTHING",
        (date.today(),),
    )
    cur.execute("SELECT id FROM data_source WHERE name = 'theracingapi'")
    source_id = cur.fetchone()[0]

    provider = TheRacingApiProvider()
    today = date.today()
    now = datetime.now(timezone.utc)

    try:
        races = provider.get_racecards(today, region="GB")
    except Exception as e:
        print(f"FAILED to fetch racecards: {e}")
        cur.close()
        conn.close()
        sys.exit(1)

    print(f"Fetched {len(races)} real GB races for {today} from The Racing API.")

    races_stored, runners_stored = 0, 0

    for rc in races:
        cur.execute(
            "INSERT INTO course (name, country) VALUES (%s, 'GB') "
            "ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
            (rc.course_name,),
        )
        course_id = cur.fetchone()[0]

        cur.execute(
            """INSERT INTO race
               (course_id, race_date, off_time, race_name, race_class, race_type,
                distance_yards, surface, going, field_size, external_ref, source_id, ingested_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (course_id, race_date, off_time)
               DO UPDATE SET going = EXCLUDED.going, ingested_at = EXCLUDED.ingested_at
               RETURNING id""",
            (course_id, rc.race_date, rc.off_time, rc.race_name, rc.race_class,
             rc.race_type, rc.distance_yards, rc.surface, rc.going, len(rc.runners),
             rc.external_ref, source_id, now),
        )
        race_id = cur.fetchone()[0]
        races_stored += 1

        for runner in rc.runners:
            cur.execute(
                "INSERT INTO horse (name, source_id) VALUES (%s, %s) "
                "ON CONFLICT (name, foaled_year) DO UPDATE SET name = EXCLUDED.name "
                "RETURNING id",
                (runner.horse_name, source_id),
            )
            horse_id = cur.fetchone()[0]

            trainer_id = None
            if runner.trainer_name:
                cur.execute(
                    "INSERT INTO trainer (name) VALUES (%s) "
                    "ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                    (runner.trainer_name,),
                )
                trainer_id = cur.fetchone()[0]

            jockey_id = None
            if runner.jockey_name:
                cur.execute(
                    "INSERT INTO jockey (name) VALUES (%s) "
                    "ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                    (runner.jockey_name,),
                )
                jockey_id = cur.fetchone()[0]

            # Immutable pre-race snapshot — never UPDATE an existing one.
            cur.execute(
                """INSERT INTO runner_snapshot
                   (race_id, horse_id, trainer_id, jockey_id, age, draw, weight_lbs,
                    official_rating, recent_form, equipment, observed_at, available_at,
                    ingested_at, source_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (race_id, horse_id, trainer_id, jockey_id, runner.age, runner.draw,
                 runner.weight_lbs, runner.official_rating, runner.recent_form,
                 runner.equipment, now, now, now, source_id),
            )
            runners_stored += 1

    conn.commit()
    print(f"Stored {races_stored} races, {runners_stored} runner snapshots.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
