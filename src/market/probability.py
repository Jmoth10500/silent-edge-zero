"""
Overround removal — converting raw bookmaker/exchange odds into fair
(de-vigged) probabilities. Build brief Section 15.

Three methods, benchmarked against each other empirically once real odds
history exists (Section 15: "Benchmark them empirically"). For now, all
three are implemented and unit-tested against known synthetic odds sets —
see tests/test_market_probability.py.
"""
from typing import Sequence


def raw_probabilities(decimal_odds: Sequence[float]) -> list[float]:
    """RAW_MARKET_PROBABILITY = 1 / decimal_odds, per runner. Sums to > 1.0
    (the overround/vig) — this is deliberately NOT normalised here."""
    return [1.0 / o for o in decimal_odds]


def proportional_method(decimal_odds: Sequence[float]) -> list[float]:
    """Simplest de-vig: scale raw probabilities down so they sum to 1.0.
    Fast, but doesn't account for the fact that overround is usually
    concentrated more heavily on shorter-priced runners."""
    raw = raw_probabilities(decimal_odds)
    total = sum(raw)
    return [p / total for p in raw]


def power_method(decimal_odds: Sequence[float], tol: float = 1e-10, max_iter: int = 200) -> list[float]:
    """Power method: find exponent k such that sum(p_i^k) = 1, where p_i are
    raw probabilities. Redistributes overround more realistically than
    proportional scaling — shorter prices get relatively less of the
    correction. Solved via bisection on k."""
    raw = raw_probabilities(decimal_odds)

    def total_for_k(k: float) -> float:
        return sum(p ** k for p in raw)

    # k=1 reproduces the raw (overrounded) probabilities. Real odds always
    # overround (total_for_k(1) > 1), needing k>1 to shrink them to sum=1.
    # But don't assume that — a synthetic or unusually tight-margin book can
    # underround (total < 1 already), which needs k<1 to inflate probabilities
    # instead. Widen the bracket in whichever direction is actually needed
    # rather than hardcoding lo=1.0.
    if total_for_k(1.0) >= 1.0:
        lo, hi = 1.0, 10.0
        while total_for_k(hi) > 1.0 and hi < 1000:
            hi *= 2
    else:
        lo, hi = 1e-6, 1.0
        while total_for_k(lo) < 1.0 and lo > 1e-9:
            lo /= 2

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        t = total_for_k(mid)
        if abs(t - 1.0) < tol:
            break
        if t > 1.0:
            lo = mid
        else:
            hi = mid

    k = (lo + hi) / 2
    return [p ** k for p in raw]


def shin_method(decimal_odds: Sequence[float], tol: float = 1e-10, max_iter: int = 200) -> list[float]:
    """Shin's method: models the overround as arising partly from insider
    trading risk (favourite-longshot bias). Solves for z (the implied
    proportion of informed money) such that fair probabilities sum to 1.

    p_i = raw probability, n = number of runners.
    Shin fair probability: q_i = [sqrt(z^2 + 4(1-z)*p_i^2/sum(p_i)) - z] / (2(1-z))
    """
    raw = raw_probabilities(decimal_odds)
    total_raw = sum(raw)
    n = len(raw)

    # Shin's model is only defined for a book with genuine overround
    # (total_raw > 1). A real bookmaker/exchange book always overrounds —
    # if this ever sees total_raw <= 1, it's bad input data (stale odds,
    # an API glitch), not a real market. Fail back to proportional rather
    # than solve a meaningless equation and return silently-wrong numbers.
    if total_raw <= 1.0:
        return proportional_method(decimal_odds)

    def fair_probs(z: float) -> list[float]:
        if z >= 1.0:
            z = 1.0 - 1e-9
        return [
            (( (z ** 2 + 4 * (1 - z) * (p ** 2) / total_raw) ** 0.5) - z) / (2 * (1 - z))
            for p in raw
        ]

    lo, hi = 0.0, 0.5
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        probs = fair_probs(mid)
        s = sum(probs)
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            lo = mid
        else:
            hi = mid

    return fair_probs((lo + hi) / 2)


METHODS = {
    "proportional": proportional_method,
    "power": power_method,
    "shin": shin_method,
}
