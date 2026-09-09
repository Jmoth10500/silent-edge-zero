#!/usr/bin/env python3
"""
Phase 8 — the live daily prediction pipeline.

Every prior script in this repo either backtests against real PAST results
(scripts/train_model1.py, train_model2.py) or is a one-shot backfill. This
is the first script that predicts races that haven't happened yet, using
today's real racecard (scripts/collect_racecards.py, Mac-only, runs daily
at 07:00 via com.dave.meeting-brief... no, via
com.silentedgezero.collect-racecards.plist) and models fit on ALL real
historical data available up to today.

**No leakage, still:** the historical training set is built via
`scripts/train_model1.py::load_races()`, which inner-joins `runner_result`
— today's races have no results yet, so they are automatically excluded
from training, not filtered out by a special case here.

**Market probability is NULL for now:** The Racing API's free tier has no
odds (see docs/FREE_DATA_SOURCES.md #3), and Betfair is still blocked
(account under identity verification as of 2026-09-09 — see
docs/BUILD_LOG.md). `prediction.market_probability`/`fair_odds`/
`absolute_edge`/etc. are left NULL, honestly, rather than guessed — this
becomes fillable the moment either source unblocks.

**Immutable ledger, per Section 32 / the DB's own enforced trigger:**
every row is inserted with `locked_at` set at insert time and a
`record_hash` (SHA-256 of the fields that define the prediction) — once
locked, the DB itself rejects any UPDATE (see
`trg_prevent_locked_prediction_update` in db/schema.sql, tested in
tests/test_leakage.py). A re-run for a race/model_version pair that
already has a locked row is skipped, not overwritten — see
`_already_predicted()`.

Usage: python3 scripts/predict_todays_races.py [race_date]
Defaults to today.
"""
import hashlib
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.train_model1 import build_split_draw_bias_table, load_races
from src.features.runner_features import RunnerFeatureInput
from src.models.model1_logistic_baseline import DEFAULT_WEIGHTS
from src.models.model1_logistic_baseline import TrainingRace as M1TrainingRace
from src.models.model1_logistic_baseline import fit_logistic_baseline
from src.models.model1_logistic_baseline import predict_race_probabilities as m1_predict
from src.models.model2_gradient_boosting import TrainingRace as M2TrainingRace
from src.models.model2_gradient_boosting import fit_gradient_boosting
from src.models.model2_gradient_boosting import predict_race_probabilities as m2_predict

MODEL1_NAME, MODEL1_VERSION = "statistical_v1", "1.0"
MODEL2_NAME, MODEL2_VERSION = "gbm_v1", "1.0"


def get_or_create_model_version(conn, name: str, version: str, feature_version: str, description: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO model_version (name, version, feature_version, description) "
        "VALUES (%s, %s, %s, %s) ON CONFLICT (name, version) DO NOTHING",
        (name, version, feature_version, description),
    )
    cur.execute("SELECT id FROM model_version WHERE name = %s AND version = %s", (name, version))
    model_version_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    return model_version_id


def load_todays_races(conn, race_date: date):
    """Races for `race_date` with no result requirement (they haven't run
    yet) — real racecard rows only, no synthetic data. Returns the same
    shape as train_model1.RaceRow but winner_horse_id is always None and
    odds is always empty (free tier has no odds — see module docstring)."""
    from scripts.train_model1 import RaceRow

    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.race_name, r.off_time, r.course_id, c.name, r.distance_yards, r.going,
               rs.horse_id, h.name, rs.age, rs.draw, rs.weight_lbs, rs.official_rating, rs.recent_form
        FROM race r
        JOIN course c ON c.id = r.course_id
        JOIN runner_snapshot rs ON rs.race_id = r.id
        JOIN horse h ON h.id = rs.horse_id
        WHERE r.race_date = %s AND rs.non_runner = FALSE
        ORDER BY r.off_time, r.id
        """,
        (race_date,),
    )

    by_race: dict[int, dict] = {}
    order: list[int] = []
    horse_names: dict[int, str] = {}
    for (race_id, race_name, off_time, course_id, course_name, distance_yards, going,
         horse_id, horse_name, age, draw, weight_lbs, official_rating, recent_form) in cur:
        if race_id not in by_race:
            by_race[race_id] = {
                "race_name": race_name, "off_time": off_time, "course_id": course_id,
                "course_name": course_name, "distance_yards": distance_yards, "going": going,
                "runners": [],
            }
            order.append(race_id)
        by_race[race_id]["runners"].append(RunnerFeatureInput(
            horse_id=horse_id, age=age, draw=draw, weight_lbs=weight_lbs,
            official_rating=official_rating, recent_form=recent_form,
        ))
        horse_names[horse_id] = horse_name
    cur.close()

    races = []
    for race_id in order:
        e = by_race[race_id]
        races.append(RaceRow(
            race_id=race_id, race_date=race_date, runners=e["runners"], odds=[],
            winner_horse_id=None, course_id=e["course_id"], distance_yards=e["distance_yards"],
            going=e["going"],
        ))
    meta = {race_id: {"race_name": by_race[race_id]["race_name"], "off_time": by_race[race_id]["off_time"],
                       "course_name": by_race[race_id]["course_name"]} for race_id in order}
    return races, meta, horse_names


def record_hash(race_id: int, horse_id: int, model_version_id: int, model_probability: float, locked_at: datetime) -> str:
    payload = f"{race_id}|{horse_id}|{model_version_id}|{model_probability:.10f}|{locked_at.isoformat()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def already_predicted(conn, race_id: int, model_version_id: int) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM prediction WHERE race_id = %s AND model_version_id = %s AND locked_at IS NOT NULL LIMIT 1",
        (race_id, model_version_id),
    )
    row = cur.fetchone()
    cur.close()
    return row is not None


def insert_predictions(conn, race_id: int, model_version_id: int, probs: dict[int, float]) -> None:
    cur = conn.cursor()
    locked_at = datetime.now(timezone.utc)
    for horse_id, p in probs.items():
        cur.execute(
            """
            INSERT INTO prediction (race_id, horse_id, model_version_id, model_probability, locked_at, record_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (race_id, horse_id, model_version_id, p, locked_at,
             record_hash(race_id, horse_id, model_version_id, p, locked_at)),
        )
    conn.commit()
    cur.close()


def main():
    race_date_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    race_date = date.fromisoformat(race_date_str)

    conn = psycopg2.connect(dbname="silent_edge_zero")

    print(f"Loading real historical results (strictly before {race_date}) to fit today's models...")
    all_historical = load_races(conn, "2023-01-01")
    historical = [r for r in all_historical if r.race_date < race_date
                  and r.winner_horse_id is not None and len(r.runners) >= 3]
    print(f"{len(historical):,} real historical races available for fitting.")

    draw_bias_table = build_split_draw_bias_table(historical)

    m1_train = [
        M1TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id,
                        course_id=r.course_id, distance_yards=r.distance_yards)
        for r in historical
    ]
    print("Fitting Model 1 (logistic baseline) on all real historical data...")
    m1_weights = fit_logistic_baseline(m1_train, iterations=150, draw_bias_table=draw_bias_table)

    m2_train = [
        M2TrainingRace(runners=r.runners, winner_horse_id=r.winner_horse_id,
                        course_id=r.course_id, distance_yards=r.distance_yards)
        for r in historical if len(r.runners) >= 2
    ]
    print("Fitting Model 2 (gradient boosting) on all real historical data...")
    m2_model = fit_gradient_boosting(m2_train, max_iter=150, draw_bias_table=draw_bias_table)

    m1_version_id = get_or_create_model_version(
        conn, MODEL1_NAME, MODEL1_VERSION, "6-feature-v1",
        "Logistic baseline, real fit on all historical data as of the prediction date, live daily prediction (Phase 8).",
    )
    m2_version_id = get_or_create_model_version(
        conn, MODEL2_NAME, MODEL2_VERSION, "6-feature-v1",
        "Gradient boosting, real fit on all historical data as of the prediction date, live daily prediction (Phase 8).",
    )

    todays_races, meta, horse_names = load_todays_races(conn, race_date)
    print(f"\n{len(todays_races):,} real races for {race_date} with known runners.\n")

    n_m1, n_m2, n_skipped = 0, 0, 0
    for r in todays_races:
        if len(r.runners) < 2:
            n_skipped += 1
            continue

        m = meta[r.race_id]
        print(f"{m['off_time']} {m['course_name']} — {m['race_name']} ({len(r.runners)} runners)")

        if not already_predicted(conn, r.race_id, m1_version_id):
            m1_probs = m1_predict(r.runners, weights=m1_weights, draw_bias_table=draw_bias_table,
                                   course_id=r.course_id, distance_yards=r.distance_yards)
            insert_predictions(conn, r.race_id, m1_version_id, m1_probs)
            n_m1 += 1
            top = max(m1_probs.items(), key=lambda kv: kv[1])
            print(f"  Model 1 top pick: {horse_names[top[0]]} ({top[1]:.1%})")
        else:
            print("  Model 1: already predicted (locked), skipping.")

        if not already_predicted(conn, r.race_id, m2_version_id):
            m2_probs = m2_predict(r.runners, m2_model, draw_bias_table=draw_bias_table,
                                   course_id=r.course_id, distance_yards=r.distance_yards)
            insert_predictions(conn, r.race_id, m2_version_id, m2_probs)
            n_m2 += 1
            top = max(m2_probs.items(), key=lambda kv: kv[1])
            print(f"  Model 2 top pick: {horse_names[top[0]]} ({top[1]:.1%})")
        else:
            print("  Model 2: already predicted (locked), skipping.")

    print(f"\n{n_m1} races newly predicted by Model 1, {n_m2} by Model 2, "
          f"{n_skipped} skipped (fewer than 2 runners).")
    print("Every inserted row is locked immediately (locked_at set, record_hash computed) — "
          "immutable per the DB's own trigger, never overwritten by a re-run.")

    conn.close()


if __name__ == "__main__":
    main()
