import sys
from datetime import datetime, date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import health_check as h

NOW = datetime(2026, 9, 30, 14, 0)


def test_odds_none_today_alerts():
    assert h.check_odds(30, None, NOW)
    assert h.check_odds(30, datetime(2026, 9, 29, 20, 0), NOW)


def test_odds_fresh_ok_stale_alerts():
    assert not h.check_odds(30, datetime(2026, 9, 30, 13, 45), NOW)
    assert h.check_odds(30, datetime(2026, 9, 30, 10, 0), NOW)


def test_odds_outside_racing_hours_or_no_races_silent():
    assert not h.check_odds(30, None, datetime(2026, 9, 30, 7, 0))
    assert not h.check_odds(30, None, datetime(2026, 9, 30, 21, 0))
    assert not h.check_odds(0, None, NOW)


def test_predictions():
    assert h.check_predictions(0, 0, NOW)
    assert h.check_predictions(30, 20, NOW)
    assert not h.check_predictions(30, 30, NOW)
    assert not h.check_predictions(0, 0, datetime(2026, 9, 30, 7, 0))


def test_unmapped_courses():
    assert "perth" in h.check_unmapped(["perth", "ayr"], {"ayr": "ayr"}, {})[0]
    assert not h.check_unmapped(["ayr"], {"ayr": "ayr"}, {})


def test_results_tolerance_and_timing():
    assert not h.check_results(date(2026, 9, 29), 30, 2, NOW)       # 6.7% ok
    assert h.check_results(date(2026, 9, 29), 30, 10, NOW)
    assert not h.check_results(date(2026, 9, 30), 30, 30, NOW)      # today, before 22:00
    assert h.check_results(date(2026, 9, 30), 30, 30, datetime(2026, 9, 30, 22, 30))


def test_notify_dedupes_within_day(tmp_path, monkeypatch):
    monkeypatch.setattr(h, "STATUS_PATH", tmp_path / "s.json")
    assert h.notify_new(["a"], NOW) == ["a"]
    assert h.notify_new(["a", "b"], NOW) == ["b"]
    assert h.notify_new(["a"], datetime(2026, 10, 1, 10, 0)) == ["a"]  # new day re-alerts
