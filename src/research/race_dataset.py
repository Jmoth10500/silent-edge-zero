"""
Canonical race-level research dataset — Silent Edge Zero V2 brief, Phase 1
(Section 3). Read-only query functions assembling the RACE / HORSES /
SILENT EDGE / MARKET / RESULT record shape the brief specifies, built
entirely from tables that already exist (`db/schema.sql`) — no new tables
for this MVP, one new column (`market_snapshot.price_quality`, see
src/providers/odds_smarkets.py).

**Never touches a single file that produces a prediction, ranking, or top
pick.** This module only reads `prediction` rows already written by
scripts/predict_todays_races.py; it never calls a model or recomputes a
probability.

**Horse identity convention (real, load-bearing):** `horse.UNIQUE(name,
foaled_year)` has never actually deduplicated real horses (`foaled_year` is
always NULL from the real data source — see db/schema.sql's own comment on
`horse`, and docs/BUILD_LOG.md's 2026-09-11 entry: 536 duplicate horse
names / 1,085 excess rows, confirmed live). Every query in this module
resolves `horse_id` via `prediction.horse_id` — the real source of truth
already relied on everywhere else in this project (see
scripts/collect_smarkets_prices.py::load_our_races, scripts/collect_race_results.py)
— and never joins `runner_snapshot`/`market_snapshot` to `horse` directly.

**Never fabricates a missing field.** Sectional/finishing times and BSP are
not collected anywhere in this project yet (confirmed against
`runner_result`'s real schema and every results collector) — every such
field here is `None`, explicitly, never estimated.
"""
from datetime import date, datetime
from typing import Optional


def load_race_dataset(conn, race_date: date, model_version_name: str = "gbm_v1") -> list[dict]:
    """Real, canonical per-race research record for every race on
    `race_date` that has at least one locked prediction under
    `model_version_name` (the primary/display model — 'gbm_v1' — by
    default; pass 'statistical_v1' for Model 1's own view of the same
    races). Each returned race dict has `race`, `runners` (one per horse,
    itself nesting `horse`/`silent_edge`/`market`/`result`), and
    `settlement_status` ('settled' / 'pending' / 'no_predictions').

    Runs one primary query plus one lookup query (the other model's
    probabilities, for model-agreement) — deliberately not N+1 per race.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            r.id, r.race_date, r.off_time, c.name, r.race_name, r.race_class,
            r.race_type, r.distance_yards, r.surface, r.going, r.field_size,
            p.horse_id, h.name, tr.name, jk.name,
            rs.official_rating, rs.draw, rs.weight_lbs, rs.recent_form,
            rs.age, rs.equipment, rs.non_runner, rs.days_since_last_run,
            p.model_probability, p.locked_at, p.record_hash,
            rr.finishing_position, rr.result_note, rr.starting_price,
            rr.distance_beaten, rr.bsp
        FROM prediction p
        JOIN race r ON r.id = p.race_id
        JOIN course c ON c.id = r.course_id
        JOIN horse h ON h.id = p.horse_id
        JOIN model_version mv ON mv.id = p.model_version_id
        LEFT JOIN runner_snapshot rs ON rs.race_id = p.race_id AND rs.horse_id = p.horse_id
        LEFT JOIN trainer tr ON tr.id = rs.trainer_id
        LEFT JOIN jockey jk ON jk.id = rs.jockey_id
        LEFT JOIN runner_result rr ON rr.race_id = p.race_id AND rr.horse_id = p.horse_id
        WHERE r.race_date = %s AND p.locked_at IS NOT NULL AND mv.name = %s
        ORDER BY r.off_time, r.id, p.model_probability DESC
        """,
        (race_date, model_version_name),
    )
    rows = cur.fetchall()

    # Second model's probabilities, keyed the same way, for model agreement —
    # a second targeted query rather than a wider join that would duplicate
    # every other column per model.
    other_model = "statistical_v1" if model_version_name == "gbm_v1" else "gbm_v1"
    cur.execute(
        """
        SELECT p.race_id, p.horse_id, p.model_probability
        FROM prediction p
        JOIN race r ON r.id = p.race_id
        JOIN model_version mv ON mv.id = p.model_version_id
        WHERE r.race_date = %s AND p.locked_at IS NOT NULL AND mv.name = %s
        """,
        (race_date, other_model),
    )
    other_model_probs = {(race_id, horse_id): float(prob) for race_id, horse_id, prob in cur.fetchall()}
    cur.close()

    races: dict[int, dict] = {}
    order: list[int] = []
    for (race_id, r_date, off_time, course_name, race_name, race_class, race_type,
         distance_yards, surface, going, field_size_declared,
         horse_id, horse_name, trainer_name, jockey_name,
         official_rating, draw, weight_lbs, recent_form, age, equipment, non_runner,
         days_since_last_run, model_probability, locked_at, record_hash,
         finishing_position, result_note, starting_price, distance_beaten, bsp) in rows:

        if race_id not in races:
            races[race_id] = {
                "race": {
                    "race_id": race_id, "date": r_date, "off_time": off_time,
                    "course": course_name, "race_name": race_name, "race_class": race_class,
                    "race_type": race_type, "distance_yards": distance_yards, "surface": surface,
                    "going": going, "field_size_declared": field_size_declared,
                    "actual_starters": None,  # filled below once runners are known
                },
                "model_version": model_version_name,
                "runners": [],
            }
            order.append(race_id)

        races[race_id]["runners"].append({
            "horse": {
                "horse_id": horse_id, "name": horse_name, "trainer": trainer_name,
                "jockey": jockey_name, "official_rating": float(official_rating) if official_rating is not None else None,
                "draw": draw, "weight_lbs": weight_lbs, "recent_form": recent_form,
                "age": age, "equipment": equipment, "days_since_last_run": days_since_last_run,
            },
            "silent_edge": {
                "model_probability": float(model_probability),
                "other_model_probability": other_model_probs.get((race_id, horse_id)),
                "locked_at": locked_at,
                "record_hash": record_hash,
            },
            "market": None,  # filled by attach_market_data(), separate call — see its docstring
            "result": {
                "finishing_position": finishing_position,
                "result_note": result_note,
                "starting_price": float(starting_price) if starting_price is not None else None,
                "distance_beaten": float(distance_beaten) if distance_beaten is not None else None,
                "bsp": float(bsp) if bsp is not None else None,  # always None today — never populated, see module docstring
                "non_runner": non_runner,
            },
        })

    out = []
    for rid in order:
        race = races[rid]
        runners = race["runners"]
        has_any_result = any(
            x["result"]["finishing_position"] is not None or x["result"]["result_note"] is not None
            for x in runners
        )
        # "Actual starters" excludes confirmed non-runners (NR/VOID) — real
        # only once every runner has at least a result_note or a finishing
        # position; otherwise honestly unknown rather than guessed.
        settled = all(
            x["result"]["finishing_position"] is not None or x["result"]["result_note"] is not None
            for x in runners
        )
        race["race"]["actual_starters"] = (
            sum(1 for x in runners if x["result"]["result_note"] not in ("NR", "VOID")) if settled else None
        )
        race["settlement_status"] = "settled" if settled else "pending"
        # top pick and ranking, purely observational — never recomputed as a
        # new "prediction", just reading the max of what's already there.
        ranked = sorted(runners, key=lambda x: x["silent_edge"]["model_probability"], reverse=True)
        for i, r in enumerate(ranked, start=1):
            r["silent_edge"]["model_rank"] = i
        race["top_pick_horse_id"] = ranked[0]["horse"]["horse_id"] if ranked else None
        out.append(race)
    return out


def attach_market_data(conn, races: list[dict]) -> None:
    """Mutates `races` in place, attaching `market` per runner: the latest
    snapshot (as the dashboard already shows), the snapshot nearest at/after
    `prediction.locked_at` ("lock price"), and the latest snapshot strictly
    before `race.off_time` ("closing price") — the two derived queries
    `docs/SCIENTIFIC_AUDIT_PLAN.md` already identified as needing "no new
    data collection, just two new queries". A race/horse with no real
    market_snapshot row at all gets `market = {"latest": None, "at_lock":
    None, "closing": None}` — never inferred from the model's own
    probability."""
    cur = conn.cursor()
    for race in races:
        race_id = race["race"]["race_id"]
        off_time = race["race"]["off_time"]
        for runner in race["runners"]:
            horse_id = runner["horse"]["horse_id"]
            locked_at = runner["silent_edge"]["locked_at"]

            cur.execute(
                """
                SELECT exchange_back, exchange_lay, midprice, spread, price_quality, observed_at
                FROM market_snapshot WHERE race_id = %s AND horse_id = %s
                ORDER BY observed_at DESC LIMIT 1
                """,
                (race_id, horse_id),
            )
            latest = cur.fetchone()

            at_lock = None
            if locked_at is not None:
                cur.execute(
                    """
                    SELECT exchange_back, exchange_lay, midprice, spread, price_quality, observed_at
                    FROM market_snapshot WHERE race_id = %s AND horse_id = %s AND observed_at >= %s
                    ORDER BY observed_at ASC LIMIT 1
                    """,
                    (race_id, horse_id, locked_at),
                )
                at_lock = cur.fetchone()

            cur.execute(
                """
                SELECT exchange_back, exchange_lay, midprice, spread, price_quality, observed_at
                FROM market_snapshot WHERE race_id = %s AND horse_id = %s AND observed_at < %s
                ORDER BY observed_at DESC LIMIT 1
                """,
                (race_id, horse_id, _race_off_datetime(race["race"])),
            )
            closing = cur.fetchone()

            runner["market"] = {
                "latest": _snapshot_dict(latest),
                "at_lock": _snapshot_dict(at_lock),
                "closing": _snapshot_dict(closing),
            }

        # market favourite (Section 5) — lowest current exchange_back among
        # runners with a real price, same rule already used in
        # scripts/generate_eod_report.py/generate_dashboard.py, computed
        # once here so downstream research code doesn't re-derive it
        # independently a fourth time.
        priced = [r for r in race["runners"] if r["market"]["latest"] and r["market"]["latest"]["exchange_back"] is not None]
        favourite = min(priced, key=lambda r: r["market"]["latest"]["exchange_back"]) if priced else None
        race["market_favourite_horse_id"] = favourite["horse"]["horse_id"] if favourite else None
    cur.close()


def _snapshot_dict(row) -> Optional[dict]:
    if row is None:
        return None
    exchange_back, exchange_lay, midprice, spread, price_quality, observed_at = row
    return {
        "exchange_back": float(exchange_back) if exchange_back is not None else None,
        "exchange_lay": float(exchange_lay) if exchange_lay is not None else None,
        "midprice": float(midprice) if midprice is not None else None,
        "spread": float(spread) if spread is not None else None,
        "price_quality": price_quality,
        "observed_at": observed_at,
    }


def _race_off_datetime(race: dict) -> datetime:
    return datetime.combine(race["date"], race["off_time"])
