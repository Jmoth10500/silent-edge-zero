"""
Live paired Brier score — Silent Edge Zero V2 brief, Phase 4 (Section 10,
the brief's own "primary scientific objective"). Read-only, pure functions
over the canonical dataset (src/research/race_dataset.py). Never touches
`prediction`, never recalibrates or retrains anything.

**Methodology, deliberately matching the project's existing definition —
never a new, incompatible one:** `src/evaluation/calibration.py::brier_score`
scores a flattened list of (predicted_probability, binary_outcome) pairs at
RUNNER level, pooled across races — not a whole-race multiclass score. This
module reuses that exact function for both Silent Edge and the market, so
the two scores are computed the same way and are genuinely comparable.

**What counts as "the market's probability" here:** the de-vigged
(normalised) implied probability from `src.analysis.edge_metrics.
normalized_market_probabilities`, using real exchange_back prices at a
chosen snapshot (`price_source`: 'at_lock' by default — the fair,
same-moment comparison against Silent Edge's own locked prediction, same
default as src/research/market_vs_model.py). A race where fewer than 2
runners have a real price at that snapshot cannot be de-vigged at all and
is excluded entirely from the market side (and, for a genuinely paired
comparison, from Silent Edge's side too) — never guessed, never scored
against a single un-de-vigged quote.

**Which runners get an outcome:** a runner's own win/loss is knowable
independently of whether the rest of the field has fully settled — outcome
= 1 if `finishing_position == 1`, 0 if it has a real finishing_position > 1
or a real terminal non-finish code (PU/F/UR/BD/RR/RO/DSQ/SU/REF/CO/FELL —
the horse ran and didn't win). A genuine non-runner (NR/VOID — no bet ever
stood) is excluded, same discipline as every settlement function elsewhere
in this project (see scripts/generate_eod_report.py::VOID_RESULT_CODES). A
runner with no real result yet is excluded as genuinely pending, never
scored as a loss.

**BRIER GAP = Silent Edge Brier − Market Brier. Positive means the market
is leading (lower score = better); negative means Silent Edge is leading.**
"""
from typing import Callable, Optional

from src.analysis.edge_metrics import normalized_market_probabilities
from src.evaluation.calibration import brier_score
from scripts.generate_eod_report import VOID_RESULT_CODES


def _runner_outcome(result: dict) -> Optional[int]:
    """1 if this runner won, 0 if it has a real known loss, None if
    genuinely unresolved (pending) or a real non-runner (excluded, not a
    loss) — see module docstring."""
    if result["finishing_position"] == 1:
        return 1
    if result["finishing_position"] is not None:
        return 0
    if result["result_note"] is None:
        return None  # genuinely pending
    if result["result_note"] in VOID_RESULT_CODES:
        return None  # non-runner — no bet ever stood, excluded not scored as a loss
    return 0  # a real terminal non-finish (PU/F/UR/... ) — the horse ran and didn't win


def compute_paired_observations(races: list[dict], price_source: str = "at_lock") -> list[dict]:
    """One dict per (race, horse) pair that has BOTH a real Silent Edge
    probability and a real de-vigged market probability at `price_source`,
    AND a known win/loss outcome. Every exclusion reason is real and
    counted by the caller via `race["exclusion_reason"]` entries this
    function does not itself surface — see `coverage_report` below for
    that."""
    observations = []
    for race in races:
        runners = race["runners"]
        odds_by_horse = {
            r["horse"]["horse_id"]: r["market"][price_source]["exchange_back"]
            for r in runners
            if r["market"].get(price_source) and r["market"][price_source]["exchange_back"] is not None
        }
        market_probs = normalized_market_probabilities(odds_by_horse)
        if not market_probs:
            continue  # fewer than 2 real priced runners — cannot de-vig, whole race excluded

        for r in runners:
            horse_id = r["horse"]["horse_id"]
            market_prob = market_probs.get(horse_id)
            if market_prob is None:
                continue  # this specific runner had no real price even though others did
            outcome = _runner_outcome(r["result"])
            if outcome is None:
                continue

            se_prob = r["silent_edge"]["model_probability"]
            observations.append({
                "race_id": race["race"]["race_id"],
                "date": race["race"]["date"],
                "course": race["race"]["course"],
                "race_type": race["race"].get("race_type"),
                "field_size_declared": race["race"].get("field_size_declared"),
                "horse_id": horse_id,
                "se_probability": se_prob,
                "market_probability": market_prob,
                "outcome": outcome,
                "se_brier_contribution": (se_prob - outcome) ** 2,
                "market_brier_contribution": (market_prob - outcome) ** 2,
                "model_agreement": r["silent_edge"].get("other_model_probability"),
                "model_rank": r["silent_edge"].get("model_rank"),
            })
    return observations


def coverage_report(races: list[dict], price_source: str = "at_lock") -> dict:
    """Real counts of what was included vs excluded and why — the brief
    requires coverage/exclusions to be shown alongside any Brier number,
    never just a bare score."""
    n_races = len(races)
    n_runners_total = sum(len(r["runners"]) for r in races)
    observations = compute_paired_observations(races, price_source=price_source)
    n_included = len(observations)

    n_races_no_devig = 0
    for race in races:
        odds_by_horse = {
            r["horse"]["horse_id"]: r["market"][price_source]["exchange_back"]
            for r in race["runners"]
            if r["market"].get(price_source) and r["market"][price_source]["exchange_back"] is not None
        }
        if not normalized_market_probabilities(odds_by_horse):
            n_races_no_devig += 1

    n_pending_or_void = 0
    for race in races:
        for r in race["runners"]:
            if _runner_outcome(r["result"]) is None:
                n_pending_or_void += 1

    return {
        "n_races": n_races,
        "n_runners_total": n_runners_total,
        "n_races_excluded_insufficient_market_data": n_races_no_devig,
        "n_runner_observations_excluded_pending_or_nonrunner": n_pending_or_void,
        "n_included_observations": n_included,
    }


def paired_brier_summary(observations: list[dict]) -> Optional[dict]:
    """None if there are no observations (never a fabricated 0.0 score).
    Otherwise the real paired Brier comparison plus the gap."""
    if not observations:
        return None
    se_probs = [o["se_probability"] for o in observations]
    market_probs = [o["market_probability"] for o in observations]
    outcomes = [o["outcome"] for o in observations]

    se_brier = brier_score(se_probs, outcomes)
    market_brier = brier_score(market_probs, outcomes)
    return {
        "n": len(observations),
        "silent_edge_brier": round(se_brier, 6),
        "market_brier": round(market_brier, 6),
        "brier_gap": round(se_brier - market_brier, 6),
        "leader": "market" if se_brier > market_brier else ("silent_edge" if se_brier < market_brier else "tied"),
    }


def rolling_paired_brier(observations_by_race_order: list[dict], window_sizes=(25, 50, 100, 250)) -> dict:
    """Real rolling Brier over the last N RACES (not N runner-observations
    — a race can have any number of runners), only reported for a window
    size where at least that many distinct races actually exist in
    `observations_by_race_order` (already assumed sorted oldest-to-newest
    by the caller — this function does not re-sort, to avoid silently
    masking a caller bug). A window with insufficient races is reported as
    None, never computed on a partial/smaller sample silently."""
    race_ids_in_order: list[int] = []
    for obs in observations_by_race_order:
        if obs["race_id"] not in race_ids_in_order:
            race_ids_in_order.append(obs["race_id"])

    result = {}
    for window in window_sizes:
        if len(race_ids_in_order) < window:
            result[window] = None
            continue
        recent_race_ids = set(race_ids_in_order[-window:])
        recent_obs = [o for o in observations_by_race_order if o["race_id"] in recent_race_ids]
        result[window] = paired_brier_summary(recent_obs)
        result[window]["n_races"] = window
    return result


def brier_by_group(observations: list[dict], group_key_fn: Callable[[dict], str]) -> dict:
    """Generic breakdown (Section 10: by model probability band, market
    probability band, agreement/disagreement, field size, race type,
    model version) — groups observations by `group_key_fn(obs)` and
    reports the paired summary per group, plus how many groups had too few
    observations to be meaningful (n < 20, flagged not hidden)."""
    groups: dict[str, list[dict]] = {}
    for obs in observations:
        key = group_key_fn(obs)
        groups.setdefault(key, []).append(obs)

    out = {}
    for key, group_obs in groups.items():
        summary = paired_brier_summary(group_obs)
        if summary:
            summary["small_sample"] = summary["n"] < 20
        out[key] = summary
    return out


def probability_band_key(band_width: float = 0.10) -> Callable[[dict], str]:
    """Returns a group_key_fn bucketing by Silent Edge's own probability
    into band_width-wide bands (default 0-10%, 10-20%, ... matching brief
    Section 11's suggested bands)."""
    def _key(obs: dict) -> str:
        p = obs["se_probability"]
        lo = min(int(p / band_width) * band_width, 1 - band_width)
        hi = lo + band_width
        return f"{lo:.0%}-{hi:.0%}"
    return _key


def market_probability_band_key(band_width: float = 0.10) -> Callable[[dict], str]:
    def _key(obs: dict) -> str:
        p = obs["market_probability"]
        lo = min(int(p / band_width) * band_width, 1 - band_width)
        hi = lo + band_width
        return f"{lo:.0%}-{hi:.0%}"
    return _key


def field_size_key(obs: dict) -> str:
    n = obs.get("field_size_declared")
    if n is None:
        return "unknown"
    if n <= 7:
        return "small (<=7)"
    if n <= 12:
        return "medium (8-12)"
    return "large (13+)"
