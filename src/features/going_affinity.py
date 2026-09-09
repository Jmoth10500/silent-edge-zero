"""
Per-horse going affinity — RL-001's real implementation.

**Reframed from "weather" to "going" (2026-09-09):** RL-001's original
hypothesis was about weather (rainfall) affecting turf races more than
all-weather ones. But weather only ever matters through its effect on
going (ground condition) — and the real dataset already records the
ACTUAL going for every historical race (`race.going`, e.g. 'Good To Soft',
'Heavy', populated for ~57K real races). That's direct ground truth, not
a noisy weather proxy, and it needs no API calls or course coordinates —
see docs/RESEARCH_LAB.md RL-001 for the full reframing.

**Why this has to be an interaction, not a main effect:** every runner in
a given race runs on the SAME going. A feature that's identical for every
runner in a race contributes nothing after Model 1's softmax or Model 2's
per-race renormalisation — it's mathematically invariant under both. So
this module builds a genuinely per-RUNNER feature instead: how well does
THIS horse historically perform on going like today's, relative to how it
performs on going unlike today's. That varies runner-by-runner even
though today's going itself doesn't.

**Leakage discipline, same as draw_bias_history.py:** the caller builds
`build_going_affinity_table()` from ONLY strictly-earlier real outcomes
(a walk-forward split's training races) — see
`scripts/train_model1.py::build_split_going_affinity_table`.

**Going scale — a real, sourced-from-standard-racing-convention ordinal,
not an empirically validated one (flagged honestly, same as RL-004's
draw-percentile placeholder):** turf and all-weather (AW/Polytrack/Tapeta)
going use physically different, non-comparable vocabularies (turf:
Firm...Heavy; AW: Fast...Slow), so they're scored on separate scales and
never mixed. A going string this module doesn't recognise (rare US/dirt
terms like 'Sloppy'/'Muddy'/'Frozen' that occasionally appear in the wider
international Kaggle set) returns None — never guessed.
"""
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Sequence

# Ordinal position on each scale: higher = softer/slower ground. Sourced
# from standard UK/Irish going terminology (turf) and the Fast-Standard-Slow
# convention used for Polytrack/Tapeta all-weather surfaces.
_TURF_GOING_SCALE = {
    "firm": 0, "good to firm": 1, "good": 2, "good to yielding": 2.5,
    "yielding": 3, "good to soft": 3, "yielding to soft": 3.5, "soft": 4,
    "soft to heavy": 5, "very soft": 5, "heavy": 6,
}
_AW_GOING_SCALE = {
    "fast": 0, "standard to fast": 0.5, "standard": 1,
    "standard to slow": 2, "slow": 3,
}
# The threshold (on either scale) at/above which going counts as the
# "soft/slow side" for this feature's binary interaction term.
_TURF_SOFT_THRESHOLD = 3   # Good To Soft or softer
_AW_SOFT_THRESHOLD = 2     # Standard To Slow or slower


def _normalise_going(going: Optional[str]) -> Optional[str]:
    return going.strip().lower() if going else None


def going_scale_and_value(going: Optional[str]) -> tuple[Optional[str], Optional[float]]:
    """Returns (scale, ordinal_value) — scale is 'turf' or 'aw', or
    (None, None) if `going` is missing or not a recognised term on either
    scale (never guessed)."""
    g = _normalise_going(going)
    if g is None:
        return None, None
    if g in _TURF_GOING_SCALE:
        return "turf", _TURF_GOING_SCALE[g]
    if g in _AW_GOING_SCALE:
        return "aw", _AW_GOING_SCALE[g]
    return None, None


def is_soft_side(going: Optional[str]) -> Optional[bool]:
    """True = soft/slow side of its own scale, False = fast/firm side,
    None = going missing/unrecognised."""
    scale, value = going_scale_and_value(going)
    if scale is None:
        return None
    threshold = _TURF_SOFT_THRESHOLD if scale == "turf" else _AW_SOFT_THRESHOLD
    return value >= threshold


@dataclass(frozen=True)
class HistoricalGoingRecord:
    """One real, strictly-past completed run for a horse — the shape
    needed to compute per-horse going affinity. `finishing_position`/
    `field_size` must both be real (a DNF has no meaningful percentile and
    is excluded by the caller, never guessed at)."""

    horse_id: int
    going: Optional[str]
    finishing_position: int
    field_size: int


def _finish_percentile(finishing_position: int, field_size: int) -> Optional[float]:
    """1.0 = won, 0.0 = last. None for a field of 1 (no spread)."""
    if field_size <= 1:
        return None
    return (field_size - finishing_position) / (field_size - 1)


def build_going_affinity_table(
    records: Sequence[HistoricalGoingRecord], min_runs_per_side: int = 2,
) -> dict[int, float]:
    """Per-horse `soft_ground_affinity`: (avg finish percentile on the
    soft/slow side of its own going scale) minus (avg finish percentile on
    the fast/firm side). Positive = this horse has historically finished
    relatively better in soft/heavy-type going than in fast/firm-type
    going. A horse needs at least `min_runs_per_side` real completed runs
    on EACH side to get an entry — otherwise it's left out of the table
    entirely (never guessed from too little evidence, same discipline as
    `draw_bias_history.py`'s `min_sample_size`).
    """
    soft_pcts: dict[int, list[float]] = defaultdict(list)
    fast_pcts: dict[int, list[float]] = defaultdict(list)

    for r in records:
        soft = is_soft_side(r.going)
        if soft is None:
            continue
        pct = _finish_percentile(r.finishing_position, r.field_size)
        if pct is None:
            continue
        (soft_pcts if soft else fast_pcts)[r.horse_id].append(pct)

    table: dict[int, float] = {}
    horse_ids = set(soft_pcts) & set(fast_pcts)
    for horse_id in horse_ids:
        soft_runs = soft_pcts[horse_id]
        fast_runs = fast_pcts[horse_id]
        if len(soft_runs) >= min_runs_per_side and len(fast_runs) >= min_runs_per_side:
            table[horse_id] = (sum(soft_runs) / len(soft_runs)) - (sum(fast_runs) / len(fast_runs))
    return table


def going_interaction_edge(
    horse_id: Optional[int], todays_going: Optional[str],
    affinity_table: dict[int, float],
) -> float:
    """This runner's `going_affinity_edge` for the feature vector:
    `soft_ground_affinity * (+1 if today is soft-side, -1 if fast-side)`.
    A soft-ground specialist (positive affinity) running on soft ground
    today gets a positive edge; the same horse on fast ground today gets a
    negative edge — the mismatch is scored, not just the affinity alone.
    Returns 0.0 ("no evidence") when the horse has no table entry, or
    today's going is missing/unrecognised.
    """
    if horse_id is None or horse_id not in affinity_table:
        return 0.0
    soft = is_soft_side(todays_going)
    if soft is None:
        return 0.0
    affinity = affinity_table[horse_id]
    return affinity if soft else -affinity
