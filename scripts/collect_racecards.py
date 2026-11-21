#!/usr/bin/env python3
"""
Real daily racecard collector — Phase 3, finally live.
Pulls GB racecards from The Racing API free tier and stores them as
PRE_RACE_SNAPSHOT rows (runner_snapshot), never overwriting a prior snapshot
for the same race+horse — a re-run just adds another row with a later
ingested_at, per the schema's own design (see db/schema.sql comments).

**Real, per Jonathan's request (2026-09-11) "how do I see tomorrow's
races?":** fetches BOTH today's and tomorrow's real card — the free tier
genuinely supports both (see src/providers/racecard_theracingapi.py's own
docstring: 'today'/'tomorrow' only, no arbitrary date). Each date is
best-effort and independent: if tomorrow's card isn't published yet (or
any other real fetch error), that date is skipped and reported, not a
reason to abort today's real collection.
"""
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from src.providers.racecard_theracingapi import TheRacingApiProvider


def store_races(conn, cur, source_id: int, races: list, target_date: date) -> tuple[int, int]:
    """Canonical-keyed ingestion (2026-10-17 integrity repair).

    The old implementation upserted on (course, race_date, off_time), i.e. it
    treated the mutable scheduled time as the race's identity and never
    retired races that dropped out of the feed -- the root cause of the 16 Oct
    phantom Redcar/Haydock cards (see docs/DATA_INTEGRITY.md). Identity is now
    the provider race id; off-time changes update the SAME race; races absent
    from the newest complete feed are RETIRED; the raw payload is kept as an
    immutable feed snapshot; runner rows are only re-written when the field
    actually changed. Caller commits. Returns (races_stored, runners_stored)
    for log compatibility.
    """
    from src.integrity.store import ingest_racecards

    rep = ingest_racecards(conn, source_id, "theracingapi", target_date, races,
                           run_id="collect_racecards")
    print(f"  ingest: created={rep['created']} rescheduled={rep['rescheduled']} unchanged={rep['unchanged']} "
          f"retired={rep['retired']} slot_conflicts={rep['slot_conflicts']} "
          f"runner_sets_written={rep['runner_sets_written']} snapshot_id={rep['snapshot_id']}"
          + (" STALE-SNAPSHOT-NOT-APPLIED" if rep["stale_snapshot"] else ""))
    return rep["created"] + rep["rescheduled"] + rep["unchanged"], rep["runner_sets_written"]


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

    any_success = False
    for i, target_date in enumerate((today, today + timedelta(days=1))):
        if i > 0:
            time.sleep(2.0)  # real rate-limit avoidance — confirmed live 2026-09-11 (a 429 hit
                              # two consecutive calls with no gap between them)
        try:
            races = provider.get_racecards(target_date, region="GB")
        except Exception as e:
            print(f"{target_date}: FAILED to fetch racecards ({e}) — skipping this date, "
                  f"not aborting the other real date.")
            continue

        print(f"Fetched {len(races)} real GB races for {target_date} from The Racing API.")
        races_stored, runners_stored = store_races(conn, cur, source_id, races, target_date)
        conn.commit()
        print(f"  Stored {races_stored} races, {runners_stored} runner snapshots for {target_date}.")
        any_success = True

    cur.close()
    conn.close()

    if not any_success:
        sys.exit(1)


if __name__ == "__main__":
    main()
