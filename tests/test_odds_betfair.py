"""
Tests for src/providers/odds_betfair.py — a STUB provider, written against
Betfair's public Betting API docs, NOT YET verified against a real
account/response (see that module's docstring for why: no Delayed App Key
exists yet, docs/FREE_DATA_SOURCES.md #4 is still BLOCKED).

The fixtures below are shaped to match what those public docs document
listMarketCatalogue/listMarketBook as returning — they are NOT captured
from a real Betfair call, unlike tests/test_racecard_theracingapi.py's
fixture (which IS a real captured response). Do not treat a pass here as
evidence the field mapping is correct against a live account — only that
the code does what it's written to do against the documented shape. The
same "verify against a live response before trusting it" discipline
Session 4 used for racecard_theracingapi.py's off_time/off_dt bug applies
here the moment real access exists.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers.odds_betfair import BetfairOddsProvider, _best_price

MARKET_ID = "1.170258175"

# Shaped from the public docs' documented listMarketCatalogue response —
# NOT a real captured call.
CATALOGUE_RESPONSE = [
    {
        "marketId": MARKET_ID,
        "marketName": "Win Market",
        "runners": [
            {"selectionId": 11111, "runnerName": "Test Horse One"},
            {"selectionId": 22222, "runnerName": "Test Horse Two"},
            # Deliberately no entry for selectionId 33333 — used below to
            # confirm a nameless runner is skipped, not fabricated.
        ],
    }
]

# Shaped from the public docs' documented listMarketBook response (EX_BEST_OFFERS)
# — NOT a real captured call.
MARKET_BOOK_RESPONSE = [
    {
        "marketId": MARKET_ID,
        "runners": [
            {
                "selectionId": 11111,
                "status": "ACTIVE",
                "ex": {
                    "availableToBack": [{"price": 3.5, "size": 120.5}, {"price": 3.45, "size": 80.0}],
                    "availableToLay": [{"price": 3.55, "size": 60.0}],
                },
            },
            {
                "selectionId": 22222,
                "status": "ACTIVE",
                "ex": {
                    "availableToBack": [],  # no current liquidity — must come back None, not 0
                    "availableToLay": [{"price": 9.0, "size": 15.0}],
                },
            },
            {
                # No matching name in the catalogue fixture above — must
                # be skipped entirely, never given a fabricated name.
                "selectionId": 33333,
                "status": "ACTIVE",
                "ex": {
                    "availableToBack": [{"price": 5.0, "size": 10.0}],
                    "availableToLay": [{"price": 5.2, "size": 10.0}],
                },
            },
        ],
    }
]


def _provider():
    return BetfairOddsProvider(app_key="test_app_key", session_token="test_session_token")


def _mock_post_side_effect(url, json=None, headers=None, timeout=None):
    """Routes the two JSON-RPC calls get_odds() makes to their respective
    fixture responses, keyed by method name."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    method = json["method"]
    if method == "SportsAPING/v1.0/listMarketCatalogue":
        mock_resp.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": CATALOGUE_RESPONSE}
    elif method == "SportsAPING/v1.0/listMarketBook":
        mock_resp.json.return_value = {"jsonrpc": "2.0", "id": 1, "result": MARKET_BOOK_RESPONSE}
    else:
        raise AssertionError(f"unexpected JSON-RPC method: {method}")
    return mock_resp


def test_missing_credentials_raises_clear_error():
    import os
    saved = os.environ.pop("BETFAIR_APP_KEY", None), os.environ.pop("BETFAIR_SESSION_TOKEN", None)
    try:
        raised = False
        try:
            BetfairOddsProvider(app_key=None, session_token=None)
        except RuntimeError:
            raised = True
        assert raised, "expected RuntimeError when credentials are missing"
    finally:
        if saved[0] is not None:
            os.environ["BETFAIR_APP_KEY"] = saved[0]
        if saved[1] is not None:
            os.environ["BETFAIR_SESSION_TOKEN"] = saved[1]


def test_runner_names_and_prices_merged_correctly():
    provider = _provider()
    with patch("src.providers.odds_betfair.requests.post", side_effect=_mock_post_side_effect):
        snapshots = provider.get_odds(MARKET_ID)

    # selectionId 33333 has no catalogue name -> must be excluded, so only 2 snapshots
    assert len(snapshots) == 2, f"expected 2 named runners, got {len(snapshots)}"

    by_name = {s.horse_name: s for s in snapshots}
    assert "Test Horse One" in by_name
    assert "Test Horse Two" in by_name
    assert "33333" not in str(by_name.keys())  # never fabricated a name for the unmatched selection


def test_best_back_and_lay_prices_are_first_rung():
    provider = _provider()
    with patch("src.providers.odds_betfair.requests.post", side_effect=_mock_post_side_effect):
        snapshots = provider.get_odds(MARKET_ID)

    by_name = {s.horse_name: s for s in snapshots}
    horse_one = by_name["Test Horse One"]
    assert horse_one.exchange_back == 3.5   # first (best) rung of availableToBack, not 3.45
    assert horse_one.exchange_lay == 3.55
    assert horse_one.bookmaker_odds is None  # exchange, not a bookmaker — never guessed


def test_empty_price_ladder_returns_none_not_zero():
    provider = _provider()
    with patch("src.providers.odds_betfair.requests.post", side_effect=_mock_post_side_effect):
        snapshots = provider.get_odds(MARKET_ID)

    by_name = {s.horse_name: s for s in snapshots}
    horse_two = by_name["Test Horse Two"]
    assert horse_two.exchange_back is None, "empty availableToBack ladder must be None, not 0 or missing"
    assert horse_two.exchange_lay == 9.0


def test_unmatched_selection_id_is_skipped_not_fabricated():
    provider = _provider()
    with patch("src.providers.odds_betfair.requests.post", side_effect=_mock_post_side_effect):
        snapshots = provider.get_odds(MARKET_ID)

    names = {s.horse_name for s in snapshots}
    assert len(snapshots) == 2
    assert all(name in ("Test Horse One", "Test Horse Two") for name in names)


def test_jsonrpc_error_key_raises_runtime_error():
    """Per the public docs, a JSON-RPC error comes back as a top-level
    "error" key on an otherwise-200 HTTP response — must be raised, not
    silently treated as an empty result."""
    provider = _provider()

    def error_side_effect(url, json=None, headers=None, timeout=None):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "jsonrpc": "2.0", "id": 1,
            "error": {"code": -32099, "message": "ANGX-0001: TOO_MUCH_DATA"},
        }
        return mock_resp

    with patch("src.providers.odds_betfair.requests.post", side_effect=error_side_effect):
        raised = False
        try:
            provider.get_odds(MARKET_ID)
        except RuntimeError:
            raised = True
        assert raised, "expected RuntimeError on a JSON-RPC error response"


def test_best_price_helper_handles_missing_and_empty_ladders():
    assert _best_price(None) is None
    assert _best_price([]) is None
    assert _best_price([{"price": 4.2, "size": 10.0}]) == 4.2
    assert _best_price([{"price": 4.2, "size": 10.0}, {"price": 4.0, "size": 5.0}]) == 4.2


def test_observed_at_is_real_utc_datetime():
    provider = _provider()
    before = datetime.now(timezone.utc)
    with patch("src.providers.odds_betfair.requests.post", side_effect=_mock_post_side_effect):
        snapshots = provider.get_odds(MARKET_ID)
    after = datetime.now(timezone.utc)

    assert len(snapshots) > 0
    for s in snapshots:
        assert before <= s.observed_at <= after
        assert s.observed_at.tzinfo is not None


if __name__ == "__main__":
    tests = [
        test_missing_credentials_raises_clear_error,
        test_runner_names_and_prices_merged_correctly,
        test_best_back_and_lay_prices_are_first_rung,
        test_empty_price_ladder_returns_none_not_zero,
        test_unmatched_selection_id_is_skipped_not_fabricated,
        test_jsonrpc_error_key_raises_runtime_error,
        test_best_price_helper_handles_missing_and_empty_ladders,
        test_observed_at_is_real_utc_datetime,
    ]
    passed = 0
    for t in tests:
        print(f"{t.__name__}:")
        try:
            t()
            print("  PASS")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
    sys.exit(0 if passed == len(tests) else 1)
