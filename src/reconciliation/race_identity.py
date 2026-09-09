"""
Race-identity reconciliation: matching a The Racing API race (identified by
its own `race_id`, e.g. "rac_32297295303") to a Betfair Exchange market
(identified by its own `marketId`, e.g. "1.170258175") — two completely
different ID spaces with no shared key.

Flagged as an open, not-yet-built gap in `src/providers/odds_betfair.py`'s
module docstring since Session 14: `get_odds()` takes a Betfair marketId
directly and has no way to discover it from a Racing API race, so wiring
Betfair odds into the rest of the pipeline needs this matching step first,
even once real Betfair credentials exist.

Approach: match on (normalized course name, off-time proximity), the same
natural approach flagged (but not built) in `odds_betfair.py`'s docstring.
This is deliberately conservative, not fuzzy matching — normalization only
strips case/whitespace/punctuation and known non-identifying suffixes (AW/
turf course qualifiers), it does NOT try to reconcile genuinely different
spellings (e.g. "Newmarket (July)" vs "Newmarket July Course") or merge
same-day meetings at different courses that happen to share a word. A
missed match is safe (falls into unmatched_*); a wrong match is not, so
this errs toward leaving ambiguous cases unmatched rather than guessing.

**Two real, honestly-flagged gaps, same discipline as odds_betfair.py's own
docstring — this module does NOT resolve them, it works around them:**

1. Timezone/wall-clock alignment between the two providers is UNVERIFIED.
   `RaceCard.off_time` is a "HH:MM" string derived from The Racing API's
   own `off_dt` (see racecard_theracingapi.py — that field carries a UTC
   offset, e.g. "+01:00" for BST, but off_time itself is just the local
   HH:MM with no timezone attached). Betfair's `marketStartTime` is
   documented as UTC. Nothing in this repo has confirmed live whether the
   two providers' clocks for the same real race land within a few minutes
   of each other once compared correctly — that needs a real side-by-side
   capture, which needs the still-blocked Betfair credentials. This
   function therefore does NOT perform timezone conversion itself: the
   caller is responsible for passing both times in the same convention
   (mirrors the caller-responsibility pattern already used by
   `draw_bias.py` and `weather_features.py` in this repo). `max_time_diff_minutes`
   exists to absorb small, expected clock/rounding differences (post/off
   delays, to-the-minute vs to-the-second reporting) — NOT to paper over an
   unresolved timezone offset; a systematic ~60-minute BST/UTC mismatch
   would silently produce zero matches rather than wrong ones, which is the
   safe failure direction.

2. No real Betfair response has ever been captured (the credentials are
   still BLOCKED) — `BetfairMarketIdentity` below is written against the
   publicly documented `listMarketCatalogue` response shape (a market's
   `event.venue` and `marketStartTime`, alongside its own `marketId`), same
   "STUB, not live-verified" status as the rest of `odds_betfair.py`.

This module is pure computation only — no HTTP, no DB access, no
timezone conversion — same shape as `draw_bias.py`/`weather_features.py`.
"""
import re
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional

from src.providers.base import RaceCard

# Suffixes/qualifiers that identify the SAME physical course but would
# otherwise break an exact-string match — e.g. Racing API might say
# "Kempton" for a turf card and "Kempton (AW)" for an all-weather one on a
# different date, or a provider might include "Racecourse" in one feed and
# not the other. Deliberately short and conservative: anything not on this
# list is left as a genuine mismatch rather than guessed away.
_STRIPPABLE_TOKENS = (
    "racecourse",
    "aw",
)


def normalize_course_name(name: str) -> str:
    """Lowercase, strip punctuation down to letters/digits/spaces, collapse
    whitespace, and drop known non-identifying words/phrases (see module
    docstring). Never fuzzy-matches genuinely different spellings — e.g.
    "Newmarket (July)" and "Newmarket July Course" normalize to
    "newmarket july" and "newmarket july course" respectively, and are
    correctly left as a non-match (the (July) vs "July Course" distinction
    is exactly the kind of case this deliberately does NOT try to resolve)."""
    if not name:
        return ""
    lowered = name.lower()
    # Drop everything except letters, digits, and whitespace (this also
    # turns a hyphen in "All-Weather" into a space, same as a literal space
    # in "All Weather" — both end up as the same two tokens below).
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Strip the two-word phrase "all weather" before single-token filtering
    # (a per-token filter alone would never see "all"+"weather" as a unit).
    cleaned = re.sub(r"\ball weather\b", " ", cleaned)
    tokens = [t for t in cleaned.split() if t not in _STRIPPABLE_TOKENS]
    return " ".join(tokens)


@dataclass
class BetfairMarketIdentity:
    """The subset of a Betfair `listMarketCatalogue` result needed to
    identify WHICH race a market is for — not the odds themselves (see
    `src/providers/odds_betfair.py` for that). STUB shape, written against
    the public docs, not yet confirmed against a real response (see module
    docstring gap #2)."""
    market_id: str
    venue: str
    market_start_time: datetime  # caller's responsibility to align timezone/convention with off_time — see gap #1


@dataclass
class RaceMatch:
    race_external_ref: str
    market_id: str
    course_name: str  # the Racing API's course_name, as matched
    time_diff_minutes: float


@dataclass
class ReconciliationResult:
    matched: list[RaceMatch]
    unmatched_racecards: list[RaceCard]
    unmatched_betfair_markets: list[BetfairMarketIdentity]


def reconcile_race_identities(
    racecards: list[RaceCard],
    betfair_markets: list[BetfairMarketIdentity],
    max_time_diff_minutes: float = 5.0,
) -> ReconciliationResult:
    """Match each RaceCard to at most one BetfairMarketIdentity (and vice
    versa) by normalized course name + closest off-time within
    `max_time_diff_minutes`, greedily assigning the globally closest-in-time
    candidate pair first so a race is never stolen from its true match by a
    slightly-worse-but-processed-first alternative.

    A RaceCard with no `off_time` (should not happen per the real schema,
    but defensively handled — never guessed) is left unmatched rather than
    crashing on an unparseable time.

    Never presented as evidence the mapping is correct against a real
    Betfair account — see the two gaps in the module docstring. This is
    pure identity-matching logic, testable and correct on its own terms
    regardless of whether the timezone alignment assumption eventually
    holds live.
    """
    if max_time_diff_minutes < 0:
        raise ValueError(f"max_time_diff_minutes must be >= 0, got {max_time_diff_minutes}")

    candidates: list[tuple[float, int, int]] = []  # (time_diff, racecard_idx, market_idx)
    racecard_datetimes: dict[int, Optional[datetime]] = {}

    for i, rc in enumerate(racecards):
        racecard_datetimes[i] = _racecard_datetime(rc)

    for i, rc in enumerate(racecards):
        rc_dt = racecard_datetimes[i]
        if rc_dt is None:
            continue
        rc_course = normalize_course_name(rc.course_name)
        for j, mkt in enumerate(betfair_markets):
            if normalize_course_name(mkt.venue) != rc_course:
                continue
            # rc_dt is always naive (built from a plain "HH:MM" string with no
            # tz attached). market_start_time may arrive tz-aware (Betfair's
            # docs say marketStartTime is UTC) — strip tzinfo rather than
            # convert, since no timezone-conversion claim is made here (see
            # gap #1 in the module docstring): this is a naive wall-clock-value
            # comparison, on purpose, not a real UTC-to-local conversion.
            mkt_dt = mkt.market_start_time.replace(tzinfo=None) if mkt.market_start_time.tzinfo else mkt.market_start_time
            diff_minutes = abs((rc_dt - mkt_dt).total_seconds()) / 60.0
            if diff_minutes <= max_time_diff_minutes:
                candidates.append((diff_minutes, i, j))

    # Greedy: closest-in-time candidates win first, so a race with an exact
    # or near-exact time match is never bumped by a coarser match to a
    # different racecard/market that merely got processed earlier.
    candidates.sort(key=lambda c: (c[0], c[1], c[2]))

    matched_racecard_idx: set[int] = set()
    matched_market_idx: set[int] = set()
    matches: list[RaceMatch] = []

    for diff_minutes, i, j in candidates:
        if i in matched_racecard_idx or j in matched_market_idx:
            continue
        matched_racecard_idx.add(i)
        matched_market_idx.add(j)
        matches.append(RaceMatch(
            race_external_ref=racecards[i].external_ref,
            market_id=betfair_markets[j].market_id,
            course_name=racecards[i].course_name,
            time_diff_minutes=diff_minutes,
        ))

    unmatched_racecards = [rc for i, rc in enumerate(racecards) if i not in matched_racecard_idx]
    unmatched_markets = [m for j, m in enumerate(betfair_markets) if j not in matched_market_idx]

    return ReconciliationResult(
        matched=matches,
        unmatched_racecards=unmatched_racecards,
        unmatched_betfair_markets=unmatched_markets,
    )


def _racecard_datetime(rc: RaceCard) -> Optional[datetime]:
    """Combine RaceCard.race_date + off_time ("HH:MM") into a naive
    datetime. Returns None (never guessed) if off_time can't be parsed."""
    if not rc.off_time:
        return None
    try:
        hh, mm = rc.off_time.split(":")
        t = time(hour=int(hh), minute=int(mm))
    except (ValueError, AttributeError):
        return None
    return datetime.combine(rc.race_date, t)
