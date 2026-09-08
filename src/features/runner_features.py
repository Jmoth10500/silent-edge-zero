"""
Runner-level feature engineering — build brief Section 8 (per-runner raw
features: official rating, age, weight, draw, form) and Section 10
(relative/percentile features within a race).

Built and tested against clearly-labelled synthetic fixtures — see
tests/test_runner_features.py — never presented as real predictions. Every
function here is pure: given already leakage-filtered inputs (the caller's
job — see tests/test_leakage.py's query pattern), it returns numbers,
nothing else. No DB access, no external data.
"""
from dataclasses import dataclass
from typing import Optional, Sequence


# ---------------------------------------------------------------------------
# Section 8: per-runner raw features
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RunnerFeatureInput:
    """Mirrors the columns of runner_snapshot that feed features directly."""

    horse_id: int
    age: Optional[int] = None
    draw: Optional[int] = None
    weight_lbs: Optional[int] = None
    official_rating: Optional[int] = None
    recent_form: Optional[str] = None  # e.g. '1-3-6-2', '132F6'
    days_since_last_run: Optional[int] = None


# Non-completion codes in a UK/Ireland form string, scored as a bad finish
# rather than dropped — a horse that fell tells you something; silently
# ignoring it would overstate its form.
_NON_COMPLETION_CODES = set("FPUORSB")  # Fell, Pulled up, Unseated, refOsal, Ran out, Slipped up, Brought down
_NON_COMPLETION_PENALTY = 12  # worse than any realistic finishing position


def parse_recent_form(recent_form: Optional[str]) -> list[int]:
    """Turn a form string into a list of finishing positions, oldest run
    FIRST (that's the standard UK/Ireland left-to-right reading order).
    '0' means '10th or worse' and is scored as 10. Non-completion letters
    score _NON_COMPLETION_PENALTY. Separators (-, /, spaces) are ignored.
    Unrecognised characters are skipped rather than raising, since real
    form strings are messy. Returns [] for None/empty input."""
    if not recent_form:
        return []
    positions = []
    for ch in recent_form.upper():
        if ch in "-/ ":
            continue
        if ch.isdigit():
            positions.append(10 if ch == "0" else int(ch))
        elif ch in _NON_COMPLETION_CODES:
            positions.append(_NON_COMPLETION_PENALTY)
    return positions


def form_score(recent_form: Optional[str], recency_weighted: bool = True) -> Optional[float]:
    """Average finishing position — lower is better. With
    recency_weighted=True (default), the most recent run counts most
    (linear weights 1, 2, 3, ... oldest to newest), matching Section 8's
    'recent form matters more than older form'. None if there's no
    parseable form at all."""
    positions = parse_recent_form(recent_form)
    if not positions:
        return None
    if not recency_weighted or len(positions) == 1:
        return sum(positions) / len(positions)
    weights = list(range(1, len(positions) + 1))
    return sum(p * w for p, w in zip(positions, weights)) / sum(weights)


# ---------------------------------------------------------------------------
# Section 10: relative/percentile features within a race
# ---------------------------------------------------------------------------

def _rank_best_first(values: Sequence[float], value: float) -> int:
    """1-based rank of `value` within `values` when sorted highest-first
    (rank 1 = the best/highest value). Ties take the rank of their first
    occurrence in the sorted order (i.e. shared rank, not averaged)."""
    ordered = sorted(values, reverse=True)
    return ordered.index(value) + 1


def relative_official_rating(runners: Sequence[RunnerFeatureInput]) -> dict[int, dict]:
    """For each runner with a known official_rating: rank (1 = highest
    rated), percentile (0-1, 1.0 = best in the race), and rating_vs_mean
    (rating points above/below the field average of RATED runners only).
    Runners with no official rating are omitted entirely — a missing rating
    is its own signal and must never be silently imputed as average."""
    rated = [(r.horse_id, r.official_rating) for r in runners if r.official_rating is not None]
    if not rated:
        return {}
    ratings = [rating for _, rating in rated]
    mean_rating = sum(ratings) / len(ratings)
    n = len(rated)
    out = {}
    for horse_id, rating in rated:
        rank = _rank_best_first(ratings, rating)
        out[horse_id] = {
            "official_rating": rating,
            "rank": rank,
            "percentile": (1.0 - (rank - 1) / (n - 1)) if n > 1 else 1.0,
            "rating_vs_mean": rating - mean_rating,
        }
    return out


def draw_bias_features(runners: Sequence[RunnerFeatureInput]) -> dict[int, dict]:
    """Draw position relative to field size. This is the neutral geometric
    fact only — draw_percentile of 0.0 is the lowest (rail) draw present,
    1.0 the widest. No track/distance-specific draw-bias data is applied
    here (that needs real historical results per course+distance, Phase 5+
    once real data exists) — this is deliberately just the raw positional
    feature, not a bias claim."""
    drawn = [(r.horse_id, r.draw) for r in runners if r.draw is not None]
    if not drawn:
        return {}
    draws = [d for _, d in drawn]
    lo, hi = min(draws), max(draws)
    out = {}
    for horse_id, draw in drawn:
        out[horse_id] = {
            "draw": draw,
            "field_size": len(runners),
            "draw_percentile": (draw - lo) / (hi - lo) if hi > lo else 0.5,
        }
    return out


def relative_weight(runners: Sequence[RunnerFeatureInput]) -> dict[int, dict]:
    """Weight carried relative to the field average (of runners with a
    known weight). Positive weight_vs_mean_lbs = carrying more than
    average."""
    weighed = [(r.horse_id, r.weight_lbs) for r in runners if r.weight_lbs is not None]
    if not weighed:
        return {}
    weights = [w for _, w in weighed]
    mean_weight = sum(weights) / len(weights)
    return {
        horse_id: {"weight_lbs": w, "weight_vs_mean_lbs": w - mean_weight}
        for horse_id, w in weighed
    }
