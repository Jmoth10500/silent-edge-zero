"""
Probability-band research — Silent Edge Zero V2 brief, Phase 4, Section 11.
Read-only, pure functions over the same paired observations
src/research/brier_live.py builds (se_probability, market_probability,
outcome per runner) — not a second, independently-computed dataset.

**Confidence intervals:** a Wilson score interval for the actual win rate
within each band — chosen over the naive normal approximation because it
stays inside [0, 1] and behaves sensibly for small samples (a band with
only a handful of observations is exactly where the brief warns "never
conclude one band is superior merely because it contains more total
winners" matters most).

**Never claims manipulation or deliberate underperformance** (brief's own
instruction) — this module only reports the numbers; any interpretation
is left to whoever reads the report.
"""
import math
from typing import Optional


def wilson_score_interval(successes: int, n: int, confidence: float = 0.95) -> Optional[tuple[float, float]]:
    """Real Wilson score interval for a binomial proportion. None if n=0
    (no interval can be computed from zero observations)."""
    if n == 0:
        return None
    z = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(confidence)
    if z is None:
        raise ValueError(f"unsupported confidence level {confidence}; use 0.90, 0.95, or 0.99")

    p_hat = successes / n
    denom = 1 + z ** 2 / n
    centre = (p_hat + z ** 2 / (2 * n)) / denom
    half_width = (z * math.sqrt((p_hat * (1 - p_hat) + z ** 2 / (4 * n)) / n)) / denom
    return (max(0.0, centre - half_width), min(1.0, centre + half_width))


def band_key(probability: float, band_width: float = 0.10) -> str:
    lo = min(int(probability / band_width) * band_width, 1 - band_width)
    hi = lo + band_width
    return f"{lo:.0%}-{hi:.0%}"


def probability_band_analysis(observations: list[dict], band_width: float = 0.10,
                               confidence: float = 0.95) -> dict:
    """Real per-band analysis (Section 11): selections, expected wins (real
    sum of Silent Edge's own probability), actual wins, actual win rate
    with a Wilson confidence interval, average predicted probability,
    market-expected wins (only over the subset with a real de-vigged
    market probability — n_with_market tracked separately so a partial
    subset is never silently presented as the full band), calibration
    error (actual_win_rate - avg_predicted_probability), and Brier
    contribution (reusing the same brier_score used everywhere else in
    this project)."""
    from src.evaluation.calibration import brier_score

    bands: dict[str, list[dict]] = {}
    for obs in observations:
        bands.setdefault(band_key(obs["se_probability"], band_width), []).append(obs)

    out = {}
    for key, group in bands.items():
        n = len(group)
        actual_wins = sum(o["outcome"] for o in group)
        expected_wins = sum(o["se_probability"] for o in group)
        avg_predicted = expected_wins / n
        actual_rate = actual_wins / n
        ci = wilson_score_interval(actual_wins, n, confidence=confidence)

        priced = [o for o in group if o["market_probability"] is not None]
        market_expected = sum(o["market_probability"] for o in priced) if priced else None

        se_probs = [o["se_probability"] for o in group]
        outcomes = [o["outcome"] for o in group]
        brier_contribution = brier_score(se_probs, outcomes)

        out[key] = {
            "band": key,
            "n_selections": n,
            "expected_wins_model": round(expected_wins, 2),
            "actual_wins": actual_wins,
            "actual_win_rate": round(actual_rate, 4),
            "win_rate_confidence_interval": (
                [round(ci[0], 4), round(ci[1], 4)] if ci else None
            ),
            "avg_predicted_probability": round(avg_predicted, 4),
            "calibration_error": round(actual_rate - avg_predicted, 4),
            "market_expected_wins": round(market_expected, 2) if market_expected is not None else None,
            "n_with_market_probability": len(priced),
            "brier_contribution": round(brier_contribution, 6),
            "small_sample": n < 20,
        }
    return out
