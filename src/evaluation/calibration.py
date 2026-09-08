"""
Calibration & scoring math (build brief Section 24: Brier score, log loss,
calibration curve). Pure functions over (predicted_probability, outcome)
pairs — no model, no DB. Testable now with synthetic prediction/outcome
pairs; ready to run against real predictions the moment the walk-forward
harness (Section 29, src/validation/walk_forward.py) produces them.
"""
import math
from typing import Sequence, TypedDict


def _validate(predicted_probs: Sequence[float], outcomes: Sequence[int]) -> None:
    if len(predicted_probs) != len(outcomes):
        raise ValueError(
            f"predicted_probs and outcomes must be the same length "
            f"(got {len(predicted_probs)} and {len(outcomes)})"
        )
    if len(predicted_probs) == 0:
        raise ValueError("cannot score an empty prediction set")
    if any(y not in (0, 1) for y in outcomes):
        raise ValueError("outcomes must be binary 0/1 (1 = winner, 0 = loser)")


def brier_score(predicted_probs: Sequence[float], outcomes: Sequence[int]) -> float:
    """Mean squared error between predicted probability and binary outcome.
    Lower is better: 0.0 = perfect, 0.25 = a constant p=0.5 guess against a
    coin-flip outcome distribution, 1.0 = maximally, confidently wrong."""
    _validate(predicted_probs, outcomes)
    n = len(predicted_probs)
    return sum((p - y) ** 2 for p, y in zip(predicted_probs, outcomes)) / n


def log_loss(predicted_probs: Sequence[float], outcomes: Sequence[int], eps: float = 1e-15) -> float:
    """Binary cross-entropy / log loss. Probabilities are clipped to
    [eps, 1-eps] first so a confident-and-wrong prediction (p=0.0 exactly
    for a winner, or p=1.0 exactly for a loser) doesn't blow up to +inf."""
    _validate(predicted_probs, outcomes)
    n = len(predicted_probs)
    total = 0.0
    for p, y in zip(predicted_probs, outcomes):
        p = min(max(p, eps), 1 - eps)
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / n


class CalibrationBin(TypedDict):
    bin_index: int
    bin_range: tuple[float, float]
    mean_predicted: float
    mean_actual: float
    count: int


def calibration_curve(
    predicted_probs: Sequence[float],
    outcomes: Sequence[int],
    n_bins: int = 10,
) -> list[CalibrationBin]:
    """Bucket predictions into n_bins equal-width bins over [0, 1] and
    return per-bin (mean_predicted, mean_actual, count) — the reliability
    diagram data behind Section 24's core question, 'is our 30% actually
    winning 30% of the time?'. Empty bins are omitted, not padded with
    zeros, so callers don't mistake 'no data' for 'zero probability'."""
    _validate(predicted_probs, outcomes)
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")

    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, y in zip(predicted_probs, outcomes):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))

    curve: list[CalibrationBin] = []
    for idx, bucket in enumerate(bins):
        if not bucket:
            continue
        mean_predicted = sum(p for p, _ in bucket) / len(bucket)
        mean_actual = sum(y for _, y in bucket) / len(bucket)
        curve.append(
            {
                "bin_index": idx,
                "bin_range": (idx / n_bins, (idx + 1) / n_bins),
                "mean_predicted": mean_predicted,
                "mean_actual": mean_actual,
                "count": len(bucket),
            }
        )
    return curve
