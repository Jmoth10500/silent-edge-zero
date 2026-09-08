"""
Price movement features (build brief Section 16: opening price, current
price, price change %, drift/shortening classification).

Pure math over a runner's own price history — no external data, no DB
access. The caller is responsible for supplying an already leakage-safe
list of observations (i.e. only prices whose available_at is <= the
prediction time — see tests/test_leakage.py for the query pattern that
guarantees that). This module never queries the database itself.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

# Movement inside +-DRIFT_THRESHOLD_PCT is treated as noise, not signal —
# real markets jitter a little even with no genuine information change.
DRIFT_THRESHOLD_PCT = 5.0


@dataclass(frozen=True)
class PriceObservation:
    observed_at: datetime
    decimal_odds: float


def _sorted_by_time(observations: Sequence[PriceObservation]) -> list[PriceObservation]:
    return sorted(observations, key=lambda o: o.observed_at)


def opening_price(observations: Sequence[PriceObservation]) -> Optional[float]:
    """Earliest observation's odds — the first price seen for this runner."""
    if not observations:
        return None
    return _sorted_by_time(observations)[0].decimal_odds


def current_price(observations: Sequence[PriceObservation]) -> Optional[float]:
    """Latest observation's odds."""
    if not observations:
        return None
    return _sorted_by_time(observations)[-1].decimal_odds


def price_change_pct(observations: Sequence[PriceObservation]) -> Optional[float]:
    """(current - opening) / opening * 100. Positive = drifted (odds
    lengthened, less market confidence). Negative = shortened (more market
    confidence). None with fewer than two observations — there's no
    movement to measure from a single price."""
    if len(observations) < 2:
        return None
    op = opening_price(observations)
    cp = current_price(observations)
    if not op:
        return None
    return (cp - op) / op * 100.0


def max_price(observations: Sequence[PriceObservation]) -> Optional[float]:
    """Highest (longest) price seen — the runner was least fancied at this point."""
    if not observations:
        return None
    return max(o.decimal_odds for o in observations)


def min_price(observations: Sequence[PriceObservation]) -> Optional[float]:
    """Lowest (shortest) price seen — the runner was most fancied at this point."""
    if not observations:
        return None
    return min(o.decimal_odds for o in observations)


def movement_classification(
    observations: Sequence[PriceObservation],
    threshold_pct: float = DRIFT_THRESHOLD_PCT,
) -> str:
    """DRIFTING / SHORTENING / STEADY based on price_change_pct vs
    threshold_pct. UNKNOWN when there isn't enough history to classify."""
    pct = price_change_pct(observations)
    if pct is None:
        return "UNKNOWN"
    if pct > threshold_pct:
        return "DRIFTING"
    if pct < -threshold_pct:
        return "SHORTENING"
    return "STEADY"
