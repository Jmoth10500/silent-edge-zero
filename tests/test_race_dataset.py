"""
Real tests for src/research/race_dataset.py's pure helpers. The two
DB-querying functions (load_race_dataset, attach_market_data) are verified
live against the real local Postgres (same convention as every other
DB-query function in this project — see scripts/generate_eod_report.py's
load_top_picks_and_favourites, which has no unit test either), not mocked
here.
"""
import sys
from datetime import date, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.race_dataset import _race_off_datetime, _snapshot_dict


def test_snapshot_dict_none_when_no_row():
    assert _snapshot_dict(None) is None


def test_snapshot_dict_converts_real_row():
    row = (5.5, 6.0, 5.75, 0.04, "ok", "2026-09-19T10:00:00+00:00")
    d = _snapshot_dict(row)
    assert d["exchange_back"] == 5.5
    assert d["exchange_lay"] == 6.0
    assert d["midprice"] == 5.75
    assert d["spread"] == 0.04
    assert d["price_quality"] == "ok"
    assert d["observed_at"] == "2026-09-19T10:00:00+00:00"


def test_snapshot_dict_handles_null_prices_without_guessing():
    row = (None, None, None, None, "thin_book", "2026-09-19T10:00:00+00:00")
    d = _snapshot_dict(row)
    assert d["exchange_back"] is None
    assert d["exchange_lay"] is None
    assert d["price_quality"] == "thin_book"


def test_race_off_datetime_combines_date_and_off_time():
    race = {"date": date(2026, 9, 19), "off_time": time(14, 30)}
    dt = _race_off_datetime(race)
    assert dt.date() == date(2026, 9, 19)
    assert dt.time() == time(14, 30)


if __name__ == "__main__":
    tests = [
        test_snapshot_dict_none_when_no_row,
        test_snapshot_dict_converts_real_row,
        test_snapshot_dict_handles_null_prices_without_guessing,
        test_race_off_datetime_combines_date_and_off_time,
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
