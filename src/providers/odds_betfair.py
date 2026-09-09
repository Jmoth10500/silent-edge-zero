"""
Betfair Exchange odds provider — STUB, UNTESTED against a real account.

Written against Betfair's public Betting API (Exchange, "Sports API") docs
(developer.betfair.com) — the JSON-RPC method names, parameter shapes, and
response field names below are the ones those docs publish, not guesses.
But — same honest status `racecard_theracingapi.py` carried before Session
4 verified it live — nothing here has been confirmed against a real
response yet, because there is no Betfair Delayed App Key to test it with
(see docs/FREE_DATA_SOURCES.md #4, still BLOCKED on Jonathan). Do not treat
any field mapping below as confirmed until a live call has actually been
made and checked, the same discipline every other provider in this repo
has followed (see the off_time/off_dt bug racecard_theracingapi.py caught
by doing exactly that).

Auth (per the public docs, genuinely different from The Racing API's plain
HTTP Basic): a Betfair session requires BOTH an App Key (BETFAIR_APP_KEY,
issued once at signup) AND a session token (BETFAIR_SESSION_TOKEN) obtained
by logging in against Betfair's separate identity service
(identitysso.betfair.com) with a username/password or a client certificate
— that login step is NOT implemented here, deliberately: a session token
expires (hours, not indefinitely) and re-authenticating is itself either
an interactive login or a certificate Jonathan would need to generate and
install, which is Jonathan's call to make, not something to build blind
against undocumented specifics. This provider only consumes an
already-obtained session token; whoever runs it is responsible for that
token being current.

A second, separate, real gap (not solved here, flagged honestly rather
than papered over): Betfair identifies a race by its own marketId (e.g.
"1.170258175"), which lives in a completely different ID space from The
Racing API's race_id (e.g. "rac_32297295303"). `get_odds()` below takes a
Betfair marketId as `race_external_ref` — there is no reconciliation logic
anywhere in this repo yet that maps one provider's race identity to the
other's (the natural approach would be matching on course name + off_time,
but that hasn't been built or tested). Wiring this provider into the rest
of the pipeline needs that matching step first.

Set BETFAIR_APP_KEY and BETFAIR_SESSION_TOKEN (in .env, gitignored, never
commit these) once real access exists.
"""
import os
from datetime import datetime, timezone
from typing import Optional

import requests

from .base import OddsProvider, OddsSnapshot

# Per Betfair's public Betting API docs — the JSON-RPC endpoint for the
# Exchange (Sports) API. Identity/login is a SEPARATE service
# (identitysso.betfair.com), not this URL — not implemented here, see
# module docstring.
JSONRPC_URL = "https://api.betfair.com/exchange/betting/json-rpc/v1"


class BetfairOddsProvider(OddsProvider):
    source_name = "betfair_exchange"

    def __init__(self, app_key: str | None = None, session_token: str | None = None):
        self.app_key = app_key or os.environ.get("BETFAIR_APP_KEY")
        self.session_token = session_token or os.environ.get("BETFAIR_SESSION_TOKEN")
        if not self.app_key or not self.session_token:
            raise RuntimeError(
                "BETFAIR_APP_KEY / BETFAIR_SESSION_TOKEN not set. "
                "See docs/FREE_DATA_SOURCES.md #4 for how to get these — "
                "note the session token also needs a separate login step "
                "this provider does not perform (see module docstring)."
            )

    def _jsonrpc_call(self, method: str, params: dict) -> dict:
        """One JSON-RPC 2.0 call against the Betting API, per the public docs'
        documented request/header shape. Not exercised against a real
        endpoint by any test in this repo — mocked only."""
        resp = requests.post(
            JSONRPC_URL,
            json={
                "jsonrpc": "2.0",
                "method": f"SportsAPING/v1.0/{method}",
                "params": params,
                "id": 1,
            },
            headers={
                "X-Application": self.app_key,
                "X-Authentication": self.session_token,
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        if "error" in body:
            # Per the docs, a JSON-RPC error comes back as a top-level
            # "error" key rather than an HTTP error status — raise loudly
            # rather than silently returning nothing.
            raise RuntimeError(f"Betfair JSON-RPC error: {body['error']}")
        return body.get("result", {})

    def get_odds(self, race_external_ref: str) -> list[OddsSnapshot]:
        """race_external_ref is a Betfair marketId (e.g. "1.170258175") —
        see module docstring for the unresolved gap this leaves versus
        other providers' race identifiers."""
        observed_at = datetime.now(timezone.utc)

        # listMarketCatalogue: the only call that returns runner NAMES
        # (listMarketBook below returns prices keyed by selectionId only).
        catalogue = self._jsonrpc_call(
            "listMarketCatalogue",
            {
                "filter": {"marketIds": [race_external_ref]},
                "marketProjection": ["RUNNER_METADATA"],
                "maxResults": 1,
            },
        )
        selection_names: dict[int, str] = {}
        for market in catalogue:
            for runner in market.get("runners", []):
                selection_id = runner.get("selectionId")
                runner_name = runner.get("runnerName")
                if selection_id is not None and runner_name:
                    selection_names[selection_id] = runner_name

        # listMarketBook: prices, keyed by selectionId, no names attached.
        books = self._jsonrpc_call(
            "listMarketBook",
            {
                "marketIds": [race_external_ref],
                "priceProjection": {"priceData": ["EX_BEST_OFFERS"]},
            },
        )

        snapshots: list[OddsSnapshot] = []
        for book in books:
            for runner in book.get("runners", []):
                selection_id = runner.get("selectionId")
                horse_name = selection_names.get(selection_id)
                if horse_name is None:
                    # A runner listMarketBook knows about but
                    # listMarketCatalogue didn't name — never guess a
                    # name, skip it rather than fabricate one.
                    continue

                ex = runner.get("ex", {})
                exchange_back = _best_price(ex.get("availableToBack"))
                exchange_lay = _best_price(ex.get("availableToLay"))

                snapshots.append(OddsSnapshot(
                    horse_name=horse_name,
                    bookmaker_odds=None,  # Betfair is an exchange, not a bookmaker
                    exchange_back=exchange_back,
                    exchange_lay=exchange_lay,
                    observed_at=observed_at,
                ))
        return snapshots


def _best_price(price_ladder: Optional[list]) -> Optional[float]:
    """Per the docs, availableToBack/availableToLay are ordered best-price-
    first. Returns None (never a guess) for an empty or missing ladder —
    e.g. a runner with no current liquidity on one side."""
    if not price_ladder:
        return None
    return price_ladder[0].get("price")
