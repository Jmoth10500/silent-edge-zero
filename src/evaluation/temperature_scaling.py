"""
Temperature scaling — a real, standard post-hoc calibration technique
(RL-011 / "GC" investigation).

**Why this exists, not a new input feature:** discovery analysis
(scripts/analyze_residuals.py) found real field-size effect on Model 2's
top-pick reliability (z=-25.3, hits average 9.0 runners, misses average
10.0) — but field size is identical for every runner in a race, so it's
mathematically invisible to a per-race softmax/renormalisation as a bare
input feature (same trap as RL-001's original weather hypothesis). The
correct fix is applying it AFTER prediction: sharpen (more confident) the
probability distribution for small fields, flatten (less confident) it
for large ones.

Temperature scaling is the standard technique for this: given a race's
raw predicted probabilities, raise each to the power `1/T` then
renormalise. T < 1 sharpens (pushes the leader's probability up,
others down) — appropriate when the model is UNDERconfident (real
observed spread narrower than raw probabilities suggest). T > 1 flattens
— appropriate when OVERconfident. T = 1 is a no-op.
"""
from typing import Optional


def apply_temperature(probs: dict[int, float], temperature: float) -> dict[int, float]:
    """Returns a new race probability dict, each raw probability raised to
    `1/temperature` then renormalised to sum to 1.0. `temperature=1.0` is
    a no-op (returns the input unchanged, up to renormalisation rounding).
    Raises ValueError for a non-positive temperature (undefined) or an
    empty `probs`.
    """
    if temperature <= 0:
        raise ValueError(f"temperature must be positive, got {temperature}")
    if not probs:
        raise ValueError("cannot apply temperature scaling to an empty race")

    scaled = {hid: p ** (1.0 / temperature) for hid, p in probs.items()}
    total = sum(scaled.values())
    if total <= 0.0:
        n = len(probs)
        return {hid: 1.0 / n for hid in probs}
    return {hid: v / total for hid, v in scaled.items()}


def field_size_bucket(field_size: int) -> str:
    """Real bucket boundaries chosen from the discovery data's own real
    distribution (hit mean 9.0, miss mean 10.0 runners) — small/medium/
    large fields, not an arbitrary guess."""
    if field_size <= 8:
        return "small"
    if field_size <= 12:
        return "medium"
    return "large"


def fit_best_temperature(
    races: list[tuple[dict[int, float], int]], candidate_temperatures: Optional[list[float]] = None,
) -> float:
    """Real grid search: given a list of (race_probs, winner_horse_id)
    pairs, returns the temperature (from `candidate_temperatures`) that
    minimises real Brier score across all of them. Caller is responsible
    for only passing DISCOVERY data here — this function has no notion of
    leakage discipline itself, same as every other fitting function in
    this repo."""
    from src.evaluation.calibration import brier_score

    if candidate_temperatures is None:
        candidate_temperatures = [round(0.5 + 0.05 * i, 2) for i in range(31)]  # 0.5 to 2.0

    best_t, best_brier = 1.0, float("inf")
    for t in candidate_temperatures:
        all_probs, all_outcomes = [], []
        for race_probs, winner_id in races:
            adjusted = apply_temperature(race_probs, t)
            for hid, p in adjusted.items():
                all_probs.append(p)
                all_outcomes.append(1 if hid == winner_id else 0)
        b = brier_score(all_probs, all_outcomes)
        if b < best_brier:
            best_t, best_brier = t, b
    return best_t
