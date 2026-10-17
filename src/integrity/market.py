"""Market-price rules (spec sections 4 and 5). Pure functions.

Hard rules encoded here:
  * A price captured AFTER the off (or within PRE_OFF_BUFFER of it) is never a
    pre-off market price and can never be labelled lock-time.
  * A lock-time price is the last valid EXCHANGE snapshot captured inside
    [off - LOCK_WINDOW, off - PRE_OFF_BUFFER]. Valid exchange prices outside
    that window are EXCHANGE_OTHER (usable, but never called lock-time).
  * Missing -> NULL with a reason code. Never inferred / interpolated / invented.
  * SP is a separate series; it never replaces or blends into exchange prices.
  * Fallback is gap-filling ONLY: one race at a time, only after validation,
    only when the primary lock snapshot is genuinely missing, never after the
    off, never overwriting a primary price, and only from APPROVED sources.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.integrity.settlement import PriceType

LOCK_WINDOW = timedelta(minutes=30)
PRE_OFF_BUFFER = timedelta(seconds=60)
MAX_PLAUSIBLE_PRICE = 1000.0          # Smarkets stub bids (e.g. 10000.0) are not real prices
MAX_SPREAD_RATIO = 3.0                # lay/back wider than this is flagged implausible

# Fallback sources must be explicitly approved by the owner. Ships EMPTY:
# with no approved source the answer is NULL + reason code.
APPROVED_FALLBACK_SOURCES: dict = {}   # name -> source_type ('EXCHANGE' | 'BOOKMAKER' | 'WEB_FALLBACK')

# Reason codes
NULL_PRIMARY_DOWN = "PRIMARY_UNAVAILABLE_NO_APPROVED_FALLBACK"
NULL_PRIMARY_NO_LOCK_SNAPSHOT = "PRIMARY_NO_LOCK_WINDOW_SNAPSHOT"
NULL_AFTER_OFF = "ONLY_POST_OFF_PRICES_AVAILABLE"
NULL_INVALID_PRICE = "PRIMARY_PRICE_INVALID"


@dataclass
class Quote:
    back_price: Optional[float]
    lay_price: Optional[float]
    captured_at: datetime
    source_name: str = "smarkets"
    source_type: str = "EXCHANGE"
    is_fallback: bool = False
    price_quality: str = "ok"


@dataclass
class PriceChoice:
    price_type: PriceType
    price: Optional[float]
    captured_at: Optional[datetime]
    source: Optional[str]
    reason: Optional[str] = None


def valid_exchange_quote(q: Quote) -> bool:
    return (q.source_type == "EXCHANGE" and not q.is_fallback and q.back_price is not None
            and 1.01 <= q.back_price <= MAX_PLAUSIBLE_PRICE and q.price_quality == "ok")


def plausible_spread(q: Quote) -> bool:
    if q.back_price is None or q.lay_price is None:
        return True
    return q.lay_price / q.back_price <= MAX_SPREAD_RATIO


def choose_bet_price(quotes: list, off_dt: datetime, sp: Optional[float]) -> PriceChoice:
    """Settlement price for ONE runner: the lock-time exchange price if one
    exists, else another pre-off exchange price, else SP, else NO_PRICE.
    Timestamps must be tz-aware and comparable to `off_dt`."""
    cutoff = off_dt - PRE_OFF_BUFFER
    pre_off = sorted((q for q in quotes if valid_exchange_quote(q) and q.captured_at <= cutoff),
                     key=lambda q: q.captured_at)
    in_window = [q for q in pre_off if q.captured_at >= off_dt - LOCK_WINDOW]
    if in_window:
        q = in_window[-1]
        return PriceChoice(PriceType.EXCHANGE_LOCK, q.back_price, q.captured_at, q.source_name)
    if pre_off:
        q = pre_off[-1]
        return PriceChoice(PriceType.EXCHANGE_OTHER, q.back_price, q.captured_at, q.source_name)
    if sp is not None and sp >= 1.0:
        return PriceChoice(PriceType.SP, float(sp), None, "starting_price")
    reason = NULL_AFTER_OFF if any(valid_exchange_quote(q) for q in quotes) else NULL_PRIMARY_DOWN
    return PriceChoice(PriceType.NO_PRICE, None, None, None, reason)


def lock_market_state(quotes: list, off_dt: datetime) -> str:
    """For coverage reporting: LOCK_VALID | OTHER_ONLY | NONE."""
    pre = [q for q in quotes if valid_exchange_quote(q) and q.captured_at <= off_dt - PRE_OFF_BUFFER]
    if any(q.captured_at >= off_dt - LOCK_WINDOW for q in pre):
        return "LOCK_VALID"
    return "OTHER_ONLY" if pre else "NONE"


@dataclass
class FallbackDecision:
    allowed: bool
    reason: str
    sources: list


def fallback_decision(*, race_validated: bool, primary_lock_state: str, now: datetime, off_dt: datetime,
                      lock_window_open_at: Optional[datetime] = None) -> FallbackDecision:
    """Is a gap-fill attempt for THIS race allowed right now? (Per race, never bulk.)"""
    if not race_validated:
        return FallbackDecision(False, "race not validated/quarantined", [])
    if primary_lock_state == "LOCK_VALID":
        return FallbackDecision(False, "primary lock-time snapshot exists; fallback must not overwrite it", [])
    if now >= off_dt - PRE_OFF_BUFFER:
        return FallbackDecision(False, "race is at/after the off; a later price can never be labelled lock-time", [])
    window_open = lock_window_open_at or (off_dt - LOCK_WINDOW)
    if now < window_open:
        return FallbackDecision(False, "lock window not yet open; primary may still capture", [])
    if not APPROVED_FALLBACK_SOURCES:
        return FallbackDecision(False, NULL_PRIMARY_DOWN, [])
    return FallbackDecision(True, "primary lock snapshot missing inside lock window", list(APPROVED_FALLBACK_SOURCES))


def checkpoint_label(captured_at: datetime, off_dt: datetime) -> str:
    """Nearest defined checkpoint for a capture (T-30 / T-15 / T-5 / T-1 / ADHOC)."""
    mins = (off_dt - captured_at).total_seconds() / 60.0
    if mins < 0:
        return "POST_OFF"
    for label, target in (("T-1", 1), ("T-5", 5), ("T-15", 15), ("T-30", 30)):
        if abs(mins - target) <= 2.5:
            return label
    return "ADHOC"
