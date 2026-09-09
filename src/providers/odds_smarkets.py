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
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from data.gb_racecourse_coordinates import GB_RACECOURSE_COORDINATES, normalise_course_name

BASE_URL = "https://api.smarkets.com/v3"


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
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
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
    resp = requests.get(f"{BASE_URL}/events/{event_id}/markets/", timeout=15)
    resp.raise_for_status()
    for m in resp.json().get("markets", []):
        if (m.get("market_type") or {}).get("name") == "WINNER":
            return m["id"]
    return None


def get_runner_prices(market_id: str) -> list[SmarketsRunnerPrice]:
    """Real fetch of a win market's contracts (runners) and quotes
    (current bid/offer book), combined into one real price reading per
    runner. A runner with no real bids or offers yet gets None for every
    price field — never guessed."""
    contracts_resp = requests.get(f"{BASE_URL}/markets/{market_id}/contracts/", timeout=15)
    contracts_resp.raise_for_status()
    contracts = contracts_resp.json().get("contracts", [])

    quotes_resp = requests.get(f"{BASE_URL}/markets/{market_id}/quotes/", timeout=15)
    quotes_resp.raise_for_status()
    quotes = quotes_resp.json()

    out = []
    for c in contracts:
        cid = c["id"]
        q = quotes.get(cid, {})
        bids = q.get("bids", [])
        offers = q.get("offers", [])

        best_bid = max((b["price"] for b in bids), default=None)
        best_offer = min((o["price"] for o in offers), default=None)

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
        ))
    return out
