"""
Real tests for src/providers/odds_smarkets.py — against real captured
Smarkets API responses (2026-09-09, a live Epsom Downs race), same
discipline as tests/test_racecard_theracingapi.py: fixtures are real
captured shapes, not guessed field names.
"""
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers.odds_smarkets import (
    get_runner_prices,
    get_win_market_id,
    is_gb_course,
    list_horse_racing_events,
)

# Real, trimmed captured response (2026-09-09) — one GB event (Epsom
# Downs), one US event (to confirm non-GB isn't filtered here — that's
# is_gb_course's job, not list_horse_racing_events').
REAL_EVENTS_RESPONSE = {
    "events": [
        {
            "id": "45309211", "name": "16:52",
            "start_datetime": "2026-09-10T15:52:00Z",
            "venue": {"name": "Epsom Downs", "neutral": False},
            "type": "horse_racing_race",
        },
        {
            "id": "45308272", "name": "21:05",
            "start_datetime": "2026-09-09T20:05:00Z",
            "venue": {"name": "Belterra Pk", "neutral": False},
            "type": "horse_racing_race",
        },
    ],
    "pagination": {},
}

REAL_MARKETS_RESPONSE = {
    "markets": [
        {"id": "163078436", "event_id": "45309211", "market_type": {"name": "WINNER"}, "name": "To win"},
        {"id": "163352039", "event_id": "45309211", "market_type": {"name": "PLACE", "param": "2"}, "name": "To place (top 2)"},
    ]
}

# Real, trimmed contracts/quotes (2 real runners from the real Epsom race).
REAL_CONTRACTS_RESPONSE = {
    "contracts": [
        {"id": "451148090", "name": "Arbaawy", "market_id": "163078436"},
        {"id": "451148091", "name": "Eastern Veil", "market_id": "163078436"},
        {"id": "999999999", "name": "No Book Yet", "market_id": "163078436"},
    ]
}
REAL_QUOTES_RESPONSE = {
    "451148090": {"bids": [{"price": 571, "quantity": 1}], "offers": [{"price": 1087, "quantity": 1}]},
    "451148091": {"bids": [{"price": 1562, "quantity": 1}, {"price": 909, "quantity": 1}],
                  "offers": [{"price": 1613, "quantity": 1}, {"price": 1786, "quantity": 1}]},
    # "999999999" deliberately absent — no real bids/offers yet
}


def _mock_get(responses_by_url_fragment):
    def fake_get(url, params=None, timeout=None):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        for fragment, payload in responses_by_url_fragment.items():
            if fragment in url:
                resp.json.return_value = payload
                return resp
        raise AssertionError(f"no mock for URL {url}")
    return fake_get


# ---------------------------------------------------------------------------
# is_gb_course
# ---------------------------------------------------------------------------

def test_is_gb_course_true_for_real_gb_venue():
    assert is_gb_course("Epsom Downs") is True
    assert is_gb_course("Worcester") is True
    assert is_gb_course("Kempton Park") is True


def test_is_gb_course_false_for_non_gb_venue():
    assert is_gb_course("Belterra Pk") is False
    assert is_gb_course("Louisiana Dn") is False


# ---------------------------------------------------------------------------
# list_horse_racing_events
# ---------------------------------------------------------------------------

def test_list_events_parses_real_response_shape():
    with patch("src.providers.odds_smarkets.requests.get", side_effect=_mock_get({"/events/": REAL_EVENTS_RESPONSE})):
        events = list_horse_racing_events(date(2026, 9, 10))
    assert len(events) == 2
    names = {e.venue_name for e in events}
    assert names == {"Epsom Downs", "Belterra Pk"}


def test_list_events_follows_real_pagination():
    page1 = {"events": [REAL_EVENTS_RESPONSE["events"][0]], "pagination": {"next_page": "?pagination_last_id=1"}}
    page2 = {"events": [REAL_EVENTS_RESPONSE["events"][1]], "pagination": {}}
    call_count = {"n": 0}

    def fake_get(url, params=None, timeout=None):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        call_count["n"] += 1
        resp.json.return_value = page1 if call_count["n"] == 1 else page2
        return resp

    with patch("src.providers.odds_smarkets.requests.get", side_effect=fake_get):
        events = list_horse_racing_events(date(2026, 9, 10))
    assert len(events) == 2
    assert call_count["n"] == 2


# ---------------------------------------------------------------------------
# get_win_market_id
# ---------------------------------------------------------------------------

def test_get_win_market_id_finds_winner_market():
    with patch("src.providers.odds_smarkets.requests.get", side_effect=_mock_get({"/markets/": REAL_MARKETS_RESPONSE})):
        market_id = get_win_market_id("45309211")
    assert market_id == "163078436"


def test_get_win_market_id_returns_none_when_no_winner_market():
    with patch("src.providers.odds_smarkets.requests.get", side_effect=_mock_get({"/markets/": {"markets": []}})):
        market_id = get_win_market_id("45309211")
    assert market_id is None


# ---------------------------------------------------------------------------
# get_runner_prices
# ---------------------------------------------------------------------------

def test_get_runner_prices_computes_real_probabilities_and_odds():
    with patch("src.providers.odds_smarkets.requests.get", side_effect=_mock_get({
        "/contracts/": REAL_CONTRACTS_RESPONSE, "/quotes/": REAL_QUOTES_RESPONSE,
    })):
        prices = get_runner_prices("163078436")

    by_name = {p.horse_name: p for p in prices}
    assert set(by_name) == {"Arbaawy", "Eastern Veil", "No Book Yet"}

    arbaawy = by_name["Arbaawy"]
    assert arbaawy.best_back_prob == 0.0571
    assert arbaawy.best_lay_prob == 0.1087
    assert abs(arbaawy.exchange_back - 1 / 0.0571) < 1e-9
    assert abs(arbaawy.exchange_lay - 1 / 0.1087) < 1e-9
    mid_prob = (0.0571 + 0.1087) / 2
    assert abs(arbaawy.midprice - 1 / mid_prob) < 1e-9
    assert abs(arbaawy.spread - (0.1087 - 0.0571)) < 1e-9

    # multiple bids/offers -> best (highest bid, lowest offer) is used
    eastern_veil = by_name["Eastern Veil"]
    assert eastern_veil.best_back_prob == 0.1562  # max(0.1562, 0.0909)
    assert eastern_veil.best_lay_prob == 0.1613   # min(0.1613, 0.1786)


def test_get_runner_prices_no_real_book_yet_is_none_not_guessed():
    with patch("src.providers.odds_smarkets.requests.get", side_effect=_mock_get({
        "/contracts/": REAL_CONTRACTS_RESPONSE, "/quotes/": REAL_QUOTES_RESPONSE,
    })):
        prices = get_runner_prices("163078436")

    no_book = next(p for p in prices if p.horse_name == "No Book Yet")
    assert no_book.best_back_prob is None
    assert no_book.best_lay_prob is None
    assert no_book.exchange_back is None
    assert no_book.exchange_lay is None
    assert no_book.midprice is None
    assert no_book.spread is None


if __name__ == "__main__":
    tests = [
        test_is_gb_course_true_for_real_gb_venue,
        test_is_gb_course_false_for_non_gb_venue,
        test_list_events_parses_real_response_shape,
        test_list_events_follows_real_pagination,
        test_get_win_market_id_finds_winner_market,
        test_get_win_market_id_returns_none_when_no_winner_market,
        test_get_runner_prices_computes_real_probabilities_and_odds,
        test_get_runner_prices_no_real_book_yet_is_none_not_guessed,
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
