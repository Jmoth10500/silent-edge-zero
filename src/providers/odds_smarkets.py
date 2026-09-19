"""
Smarkets Exchange — LIVE, free, no API key, no account, no signup.

**Why this exists:** Betfair (the project's originally-intended exchange
source) is blocked — Jonathan's account, though identity-verified, still
returns SUSPENDED on a real login test as of 2026-09-09 (see
docs/BUILD_LOG.md). Smarkets is a genuine, separate betting exchange
(back/lay, same market shape as Betfair) with a real public read-only API
that needs no authentication at all — confirmed live: real GB horse racing
events (Doncaster, Epsom Downs, Lingfield, Warwick, Worcester) pulled with
zero credentials.

**Real limitation, same as weather (RL-001):** this only ever gives
CURRENT prices — there is no historical/retroactive endpoint, so it can
never backfill the 2023-2026 backtest window the way Kaggle's starting
prices did. It can only start a real, live price-movement dataset going
forward from whenever polling begins — see scripts/collect_smarkets_prices.py.

**Price interpretation, verified live (2026-09-09), not assumed:** the
quotes endpoint (`/v3/markets/{id}/quotes/`) returns each contract's bids
(back) and offers (lay) as `price` values in basis points of implied
probability (10000 = 100%) — confirmed by checking a real race's full
book: summing every runner's best-bid probability gave 78.6%, sane for a
thin, >24h-out back-side book (would be ~100%+overround close to race
time), and each individual value was plausible against the race's own
real official ratings/form (the market's outright favourite matched the
two highest-rated runners). This is the ONLY verification done — treat
the exact probability numbers as a reasonable real reading, not something
independently cross-checked against a second exchange.

**Course matching:** Smarkets' event venue name (e.g. 'Epsom Downs',
'Worcester') is matched against our real GB course list via
`data.gb_racecourse_coordinates.normalise_course_name` — the same real,
tested normaliser already used for the coordinate/weather work, so
'Epsom Downs' and 'Epsom' resolve to the same course consistently.
"""
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from data.gb_racecourse_coordinates import GB_RACECOURSE_COORDINATES, normalise_course_name

BASE_URL = "https://api.smarkets.com/v3"


def _get_with_retry(url: str, params: dict | None = None, timeout: int = 15,
                     max_attempts: int = 6) -> requests.Response:
    """Real GET with real 429-aware retry — found live 2026-09-11: a
    course whose races happen to land later in Smarkets' own event
    listing order consistently hit a 429 every single collection run
    (confirmed: same 8 Doncaster races failed identically across
    multiple real runs, while other courses succeeded), because a race's
    3 real HTTP calls (win-market lookup + contracts + quotes) run with
    zero gap between them and the whole run only pauses 0.3s between
    races — a real, structural rate-limit trap, not a one-off blip.
    Honours a real `Retry-After` header when Smarkets sends one; falls
    back to real exponential backoff (2s, 4s, 8s, 16s, 32s) otherwise.
    Real, live-tuned: the first version (4 attempts, 1s base) recovered
    3 of 8 previously-failing Doncaster races but still lost 5 — this
    wider backoff was re-tested live and recovered all of them (see
    docs/BUILD_LOG.md, 2026-09-11). Still raises on a real non-429 error
    or after exhausting real attempts — never silently swallows a
    genuine failure."""
    for attempt in range(max_attempts):
        resp = requests.get(url, params=params, timeout=timeout)
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp
        if attempt == max_attempts - 1:
            resp.raise_for_status()  # real final attempt failed — raise the real 429
        retry_after = resp.headers.get("Retry-After")
        wait = float(retry_after) if retry_after else float(2 ** (attempt + 1))
        time.sleep(wait)
    raise RuntimeError("unreachable")  # loop always returns or raises above


@dataclass(frozen=True)
class SmarketsEvent:
    event_id: str
    venue_name: str
    start_datetime: datetime  # UTC


@dataclass(frozen=True)
class SmarketsRunnerPrice:
    contract_id: str
    horse_name: str
    best_back_prob: Optional[float]   # 0.0-1.0, from the highest real bid
    best_lay_prob: Optional[float]    # 0.0-1.0, from the lowest real offer
    exchange_back: Optional[float]    # decimal odds, 1/best_back_prob
    exchange_lay: Optional[float]     # decimal odds, 1/best_lay_prob
    midprice: Optional[float]         # decimal odds at the midpoint probability
    spread: Optional[float]           # best_lay_prob - best_back_prob (probability space)
    best_back_quantity: Optional[int] # real stake available at the best bid, Smarkets' own minor-unit quantity
    best_lay_quantity: Optional[int]  # real stake available at the best offer, same units
    price_quality: str                # 'ok' / 'thin_book' / 'wide_spread' — see classify_price_quality()


# Real, live-verified minimums — a 2026-09-18 finding on Hellion (Wolverhampton)
# showed a back price of decimal 10000.0 (implied probability 0.01%) getting
# treated as a genuine market price and driving a nonsensical "BEST VALUE,
# EV +1954%" display. Real cause: the code took the single best bid/offer
# price with no check on how much real stake stood behind it, nor on how far
# apart the two sides were — a lone stub order at an absurd price was
# indistinguishable from a real, liquid two-sided market. These thresholds
# are a first-pass heuristic (Research V2 brief, Phase 1), not empirically
# tuned against a large sample of confirmed-thin books — worth revisiting
# once scripts/data_integrity_audit.py has accumulated real evidence of
# where they under/over-fire.
MIN_QUANTITY_FOR_OK = 200          # Smarkets' own quantity units (minor currency unit); a live example carried ~250,000+
MAX_SANE_SPREAD_PROBABILITY = 0.20  # 20 percentage points between best back/lay implied probability


def classify_price_quality(
    back_prob: Optional[float], lay_prob: Optional[float],
    back_quantity: Optional[int], lay_quantity: Optional[int],
) -> str:
    """Real, conservative price-quality flag — never silently drops a
    snapshot, only labels it so downstream analysis (and the Data Integrity
    Audit) can exclude or discount it explicitly. A missing side (no back or
    no lay quote at all) or a real quantity below MIN_QUANTITY_FOR_OK on
    either present side means there's no genuine two-sided market backing
    this price — 'thin_book'. A present two-sided book with an implausibly
    wide gap between the two implied probabilities means the two sides
    aren't really quoting the same market yet — 'wide_spread'. Checked in
    that order: a thin one-sided stub book is the more direct explanation
    for an absurd price than a "wide spread" framing that assumes both
    sides are real."""
    if back_prob is None or lay_prob is None:
        return "thin_book"
    if (back_quantity is not None and back_quantity < MIN_QUANTITY_FOR_OK) or \
       (lay_quantity is not None and lay_quantity < MIN_QUANTITY_FOR_OK):
        return "thin_book"
    if (lay_prob - back_prob) > MAX_SANE_SPREAD_PROBABILITY:
        return "wide_spread"
    return "ok"


def is_gb_course(venue_name: str) -> bool:
    """True if `venue_name` normalises to one of our 59 real GB racecourses."""
    return normalise_course_name(venue_name) in GB_RACECOURSE_COORDINATES


def list_horse_racing_events(target_date: date) -> list[SmarketsEvent]:
    """Real, paginated fetch of every horse_racing_race event for
    `target_date`, any country — filtering to GB is the caller's job (see
    `is_gb_course`), since Smarkets' own `country_name` field is
    unreliable (frequently null even for real GB venues, confirmed live)."""
    events: list[SmarketsEvent] = []
    params = {
        "type": "horse_racing_race",
        "start_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
    }
    url = f"{BASE_URL}/events/"

    while True:
        resp = _get_with_retry(url, params=params)
        data = resp.json()
        for e in data.get("events", []):
            venue = (e.get("venue") or {}).get("name")
            if not venue:
                continue
            events.append(SmarketsEvent(
                event_id=e["id"], venue_name=venue,
                start_datetime=datetime.fromisoformat(e["start_datetime"].replace("Z", "+00:00")),
            ))
        next_page = (data.get("pagination") or {}).get("next_page")
        if not next_page:
            break
        url = f"{BASE_URL}/events/{next_page}"
        params = None
        if len(events) > 2000:  # real safety cap, not expected to trigger in one day's events
            break

    return events


def get_win_market_id(event_id: str) -> Optional[str]:
    """Real fetch of an event's markets, returns the 'To win' (WINNER)
    market id, or None if the event has no win market (shouldn't happen
    for a real horse race, but never assumed)."""
    resp = _get_with_retry(f"{BASE_URL}/events/{event_id}/markets/")
    for m in resp.json().get("markets", []):
        if (m.get("market_type") or {}).get("name") == "WINNER":
            return m["id"]
    return None


def get_runner_prices(market_id: str) -> list[SmarketsRunnerPrice]:
    """Real fetch of a win market's contracts (runners) and quotes
    (current bid/offer book), combined into one real price reading per
    runner. A runner with no real bids or offers yet gets None for every
    price field — never guessed."""
    contracts_resp = _get_with_retry(f"{BASE_URL}/markets/{market_id}/contracts/")
    contracts = contracts_resp.json().get("contracts", [])

    quotes_resp = _get_with_retry(f"{BASE_URL}/markets/{market_id}/quotes/")
    quotes = quotes_resp.json()

    out = []
    for c in contracts:
        cid = c["id"]
        q = quotes.get(cid, {})
        bids = q.get("bids", [])
        offers = q.get("offers", [])

        best_bid_entry = max(bids, key=lambda b: b["price"], default=None)
        best_offer_entry = min(offers, key=lambda o: o["price"], default=None)
        best_bid = best_bid_entry["price"] if best_bid_entry else None
        best_offer = best_offer_entry["price"] if best_offer_entry else None
        best_back_quantity = best_bid_entry["quantity"] if best_bid_entry else None
        best_lay_quantity = best_offer_entry["quantity"] if best_offer_entry else None

        back_prob = best_bid / 10000 if best_bid else None
        lay_prob = best_offer / 10000 if best_offer else None

        exchange_back = (1.0 / back_prob) if back_prob else None
        exchange_lay = (1.0 / lay_prob) if lay_prob else None
        midprice = None
        spread = None
        if back_prob is not None and lay_prob is not None:
            mid_prob = (back_prob + lay_prob) / 2
            midprice = 1.0 / mid_prob if mid_prob > 0 else None
            spread = lay_prob - back_prob

        out.append(SmarketsRunnerPrice(
            contract_id=cid, horse_name=c["name"],
            best_back_prob=back_prob, best_lay_prob=lay_prob,
            exchange_back=exchange_back, exchange_lay=exchange_lay,
            midprice=midprice, spread=spread,
            best_back_quantity=best_back_quantity, best_lay_quantity=best_lay_quantity,
            price_quality=classify_price_quality(back_prob, lay_prob, best_back_quantity, best_lay_quantity),
        ))
    return out
