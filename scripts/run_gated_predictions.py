#!/usr/bin/env python3
"""Gated wrapper around the FROZEN scorer (scripts/predict_todays_races.py).

The scorer file and model code are hash-frozen and are NOT modified. This
wrapper (1) runs the pre-prediction validation gate, (2) swaps the scorer's
race loader for one that only returns VALIDATED races with their CURRENT,
de-duplicated runner set (quarantined races are never scored), and (3) wraps
the scorer's insert so every new lock also writes an immutable
prediction_lock (full input snapshot + SHA-256). Models, features, fitting
and probabilities are untouched.

Usage: python3 scripts/run_gated_predictions.py [YYYY-MM-DD]
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

import scripts.predict_todays_races as scorer
from scripts.train_model1 import RaceRow
from src.features.runner_features import RunnerFeatureInput
from src.integrity.store import current_runners, run_gate, write_prediction_lock
from src.integrity.validation import status_label


def make_gated_loader(valid_ids: set):
    def gated_load_todays_races(conn, race_date: date):
        cur = conn.cursor()
        cur.execute(
            """SELECT r.id, r.race_name, r.off_time, r.course_id, c.name, r.distance_yards, r.going
               FROM race r JOIN course c ON c.id = r.course_id
               WHERE r.race_date = %s AND r.id = ANY(%s) ORDER BY r.off_time, r.id""",
            (race_date, sorted(valid_ids)))
        races, meta, horse_names = [], {}, {}
        for race_id, race_name, off_time, course_id, course_name, distance_yards, going in cur.fetchall():
            runners = []
            for horse_id, hname in current_runners(cur, race_id):
                cur.execute(
                    """SELECT age, draw, weight_lbs, official_rating, recent_form, trainer_id, jockey_id
                       FROM runner_snapshot WHERE race_id=%s AND horse_id=%s AND non_runner=FALSE
                       ORDER BY ingested_at DESC, id DESC LIMIT 1""", (race_id, horse_id))
                age, draw, weight, rating, form, trainer_id, jockey_id = cur.fetchone()
                runners.append(RunnerFeatureInput(horse_id=horse_id, age=age, draw=draw, weight_lbs=weight,
                                                  official_rating=rating, recent_form=form,
                                                  trainer_id=trainer_id, jockey_id=jockey_id))
                horse_names[horse_id] = hname
            races.append(RaceRow(race_id=race_id, race_date=race_date, runners=runners, odds=[],
                                 winner_horse_id=None, course_id=course_id, distance_yards=distance_yards, going=going))
            meta[race_id] = {"race_name": race_name, "off_time": off_time, "course_name": course_name}
        cur.close()
        return races, meta, horse_names
    return gated_load_todays_races


def main():
    race_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    conn = psycopg2.connect(dbname="silent_edge_zero")
    results = run_gate(conn, race_date, datetime.now(timezone.utc))
    valid = {r.race_id for r in results if r.ok}
    quarantined = [r for r in results if not r.ok]
    print(f"GATE {race_date}: {len(results)} canonical races, {len(valid)} validated, {len(quarantined)} quarantined")
    for r in quarantined:
        print(f"  race {r.race_id} {r.canonical_race_id}: {status_label(r)}")

    original_insert = scorer.insert_predictions

    def insert_and_lock(conn_, race_id, model_version_id, probs):
        original_insert(conn_, race_id, model_version_id, probs)
        write_prediction_lock(conn_, race_id, model_version_id, probs)

    scorer.load_todays_races = make_gated_loader(valid)
    scorer.insert_predictions = insert_and_lock
    sys.argv = [sys.argv[0], race_date.isoformat()]
    conn.close()
    scorer.main()


if __name__ == "__main__":
    main()
