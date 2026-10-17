"""Historical race classification (spec section 7). Pure functions.

Never deletes or rewrites anything: each race gets a classification and an
include_in_metrics flag; the original rows stay as they were.
"""
import math
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from src.integrity.settlement import ResultStatus, VOIDING, classify_result

MAX_RUNNERS = 40


@dataclass
class RaceFacts:
    race_id: int
    race_date: date
    meeting: str                      # date|course
    off_time: str
    provider_race_id: Optional[str]
    race_name: str
    pred_keys: frozenset              # canonical horse keys in the locked prediction field
    result_notes: list = field(default_factory=list)   # [(position, note)] for every result row
    lock_market_state: str = "NONE"   # LOCK_VALID | OTHER_ONLY | NONE


@dataclass
class Classification:
    race_id: int
    classification: str
    include_in_metrics: bool
    has_result: bool
    has_lock_market: bool
    reason: str
    evidence: dict


def _container_of(a: RaceFacts, group: list) -> Optional[tuple]:
    """If `a` is a larger provisional/combined card that contains most of the
    runners of another race at the same meeting, return (other_race_id, overlap)."""
    for b in group:
        if b.race_id == a.race_id or len(b.pred_keys) >= len(a.pred_keys) or not b.pred_keys:
            continue
        overlap = len(a.pred_keys & b.pred_keys)
        if overlap >= max(2, math.ceil(0.5 * len(b.pred_keys))):
            return b.race_id, overlap
    return None


def classify_races(races: list, today: date) -> dict:
    by_meeting: dict = {}
    for r in races:
        by_meeting.setdefault(r.meeting, []).append(r)
    by_ref: dict = {}
    for r in races:
        if r.provider_race_id:
            by_ref.setdefault(r.provider_race_id, []).append(r)

    out: dict = {}
    for r in races:
        has_result = any(pos is not None or (n is not None and str(n).strip()) for pos, n in r.result_notes)
        has_lock = r.lock_market_state == "LOCK_VALID"
        mk = lambda cls, incl, reason, **ev: Classification(
            r.race_id, cls, incl, has_result, has_lock, reason, ev)

        cont = _container_of(r, by_meeting[r.meeting])
        if cont:
            out[r.race_id] = mk("INVALID_DUPLICATE", False,
                                f"larger provisional/combined card ({len(r.pred_keys)} runners) containing {cont[1]} runners "
                                f"of race {cont[0]} at the same meeting; superseded by the real card",
                                superseded_by_race=cont[0], shared_runners=cont[1], runners=len(r.pred_keys),
                                has_results_attached=has_result)
            continue
        if r.provider_race_id and len(by_ref[r.provider_race_id]) > 1:
            group = by_ref[r.provider_race_id]
            keeper = max(group, key=lambda x: (sum(1 for p, n in x.result_notes if p is not None or n), -x.race_id))
            if keeper.race_id != r.race_id:
                out[r.race_id] = mk("INVALID_RACE_ID", False,
                                    f"provider race id {r.provider_race_id} is shared with race {keeper.race_id}; "
                                    "this row is a rescheduled copy of the same race",
                                    keeper_race=keeper.race_id, provider_race_id=r.provider_race_id)
                continue
        n_res = len([1 for p, n in r.result_notes if p is not None or n])
        if len(r.pred_keys) > MAX_RUNNERS or (n_res >= 2 and len(r.pred_keys) >= 2 * n_res and len(r.pred_keys) - n_res >= 5):
            out[r.race_id] = mk("OTHER", False,
                                f"prediction was locked on a non-final entries field of {len(r.pred_keys)} runners "
                                f"but only {n_res} actually ran/declared; probabilities normalised over a field that never raced",
                                predicted_runners=len(r.pred_keys), result_rows=n_res)
            continue
        if not has_result:
            if r.race_date < today:
                out[r.race_id] = mk("MISSING_RESULT", True, "race date has passed and no result rows were collected "
                                    "(abandoned meeting or result-collector gap — not distinguishable from our data)")
            else:
                out[r.race_id] = mk("VALID", True, "pending: race not yet run")
            continue
        statuses = [classify_result(p, n) for p, n in r.result_notes]
        if statuses and all(s in VOIDING for s in statuses):
            out[r.race_id] = mk("NON_RUNNER", True, "every result row is a non-runner/void: race void")
            continue
        if r.lock_market_state != "LOCK_VALID":
            out[r.race_id] = mk("MISSING_MARKET", True,
                                "settled race with no valid lock-time exchange snapshot "
                                f"(state={r.lock_market_state}); SP/other-exchange series only",
                                lock_market_state=r.lock_market_state)
            continue
        out[r.race_id] = mk("VALID", True, "unique race, results present, valid lock-time exchange snapshot")
    return out
