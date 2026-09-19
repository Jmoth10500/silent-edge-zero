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

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers.odds_smarkets import (
    MIN_QUANTITY_FOR_OK,
    _get_with_retry,
    classify_price_quality,
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
    # Real observed quantity scale (Chester, 2026-09-19 live check) is in
    # the hundreds of thousands — using a comfortably-above-threshold value
    # here so these existing fixtures stay classified 'ok'.
    "451148090": {"bids": [{"price": 571, "quantity": 250000}], "offers": [{"price": 1087, "quantity": 250000}]},
    "451148091": {"bids": [{"price": 1562, "quantity": 250000}, {"price": 909, "quantity": 250000}],
                  "offers": [{"price": 1613, "quantity": 250000}, {"price": 1786, "quantity": 250000}]},
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
    assert arbaawy.best_back_quantity == 250000
    assert arbaawy.best_lay_quantity == 250000
    assert arbaawy.price_quality == "ok"

    # multiple bids/offers -> best (highest bid, lowest offer) is used
    eastern_veil = by_name["Eastern Veil"]
    assert eastern_veil.best_back_prob == 0.1562  # max(0.1562, 0.0909)
    assert eastern_veil.best_lay_prob == 0.1613   # min(0.1613, 0.1786)
    assert eastern_veil.price_quality == "ok"


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
    assert no_book.price_quality == "thin_book"  # no real two-sided book at all


# ---------------------------------------------------------------------------
# classify_price_quality — the real fix for the 2026-09-18 "Hellion" bug:
# a Smarkets back price of decimal 10000.0 (implied probability 0.01%) was
# displayed as "BEST VALUE, EV +1954%" with nothing checking whether real
# liquidity or a sane spread stood behind it.
# ---------------------------------------------------------------------------

def test_classify_price_quality_ok_for_a_liquid_two_sided_book():
    assert classify_price_quality(0.196, 0.204, 250000, 250000) == "ok"


def test_classify_price_quality_thin_book_when_a_side_is_missing():
    assert classify_price_quality(None, 0.204, None, 250000) == "thin_book"
    assert classify_price_quality(0.196, None, 250000, None) == "thin_book"


def test_classify_price_quality_thin_book_when_quantity_too_low():
    assert classify_price_quality(0.196, 0.204, MIN_QUANTITY_FOR_OK - 1, 250000) == "thin_book"
    assert classify_price_quality(0.196, 0.204, 250000, MIN_QUANTITY_FOR_OK - 1) == "thin_book"


def test_classify_price_quality_wide_spread_when_both_sides_real_but_far_apart():
    # both sides clear the liquidity bar, but implied probabilities are
    # 30 percentage points apart — no real shared market yet.
    assert classify_price_quality(0.10, 0.40, 250000, 250000) == "wide_spread"


def test_classify_price_quality_flags_the_real_hellion_regression_case():
    # Real 2026-09-18 case: back decimal odds 10000.0 (prob 0.0001), lay
    # decimal odds 38.0 (prob ~0.0263). A near-worthless stub bid, not a
    # real market. Must never come back 'ok'.
    back_prob = 1 / 10000.0
    lay_prob = 1 / 38.0
    assert classify_price_quality(back_prob, lay_prob, 1, 250000) == "thin_book"


# ---------------------------------------------------------------------------
# _get_with_retry — real 429 retry logic (found live 2026-09-11: Doncaster's
# races consistently 429'd every real collection run — see
# scripts/collect_smarkets_prices.py's real investigation)
# ---------------------------------------------------------------------------

def _fake_response(status_code, headers=None, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.json.return_value = json_data or {}
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"{status_code} error")
    else:
        resp.raise_for_status.return_value = None
    return resp


def test_get_with_retry_succeeds_first_try():
    ok = _fake_response(200, json_data={"ok": True})
    with patch("src.providers.odds_smarkets.requests.get", return_value=ok) as mock_get:
        resp = _get_with_retry("https://api.smarkets.com/v3/events/")
    assert resp.json() == {"ok": True}
    assert mock_get.call_count == 1


def test_get_with_retry_retries_past_a_real_429():
    rate_limited = _fake_response(429)
    ok = _fake_response(200, json_data={"ok": True})
    with patch("src.providers.odds_smarkets.requests.get", side_effect=[rate_limited, ok]):
        with patch("src.providers.odds_smarkets.time.sleep") as mock_sleep:
            resp = _get_with_retry("https://api.smarkets.com/v3/events/")
    assert resp.json() == {"ok": True}
    mock_sleep.assert_called_once()


def test_get_with_retry_honours_real_retry_after_header():
    rate_limited = _fake_response(429, headers={"Retry-After": "5"})
    ok = _fake_response(200)
    with patch("src.providers.odds_smarkets.requests.get", side_effect=[rate_limited, ok]):
        with patch("src.providers.odds_smarkets.time.sleep") as mock_sleep:
            _get_with_retry("https://api.smarkets.com/v3/events/")
    mock_sleep.assert_called_once_with(5.0)


def test_get_with_retry_raises_after_exhausting_real_attempts():
    always_limited = _fake_response(429)
    with patch("src.providers.odds_smarkets.requests.get", return_value=always_limited):
        with patch("src.providers.odds_smarkets.time.sleep"):
            try:
                _get_with_retry("https://api.smarkets.com/v3/events/", max_attempts=3)
                assert False, "expected an HTTPError"
            except requests.HTTPError:
                pass


def test_get_with_retry_raises_immediately_on_non_429_error():
    server_error = _fake_response(500)
    with patch("src.providers.odds_smarkets.requests.get", return_value=server_error) as mock_get:
        try:
            _get_with_retry("https://api.smarkets.com/v3/events/")
            assert False, "expected an HTTPError"
        except requests.HTTPError:
            pass
    assert mock_get.call_count == 1  # no real retry for a genuine non-rate-limit error


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
        test_classify_price_quality_ok_for_a_liquid_two_sided_book,
        test_classify_price_quality_thin_book_when_a_side_is_missing,
        test_classify_price_quality_thin_book_when_quantity_too_low,
        test_classify_price_quality_wide_spread_when_both_sides_real_but_far_apart,
        test_classify_price_quality_flags_the_real_hellion_regression_case,
        test_get_with_retry_succeeds_first_try,
        test_get_with_retry_retries_past_a_real_429,
        test_get_with_retry_honours_real_retry_after_header,
        test_get_with_retry_raises_after_exhausting_real_attempts,
        test_get_with_retry_raises_immediately_on_non_429_error,
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
