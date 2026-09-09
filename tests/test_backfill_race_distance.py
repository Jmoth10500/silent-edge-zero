"""
Real tests for scripts/backfill_race_distance.py::parse_distance_to_yards —
the pure-function distance parser used to fix the real
race.distance_yards IS NULL bug found 2026-09-09 (see the script's module
docstring and docs/BUILD_LOG.md Session 10 for how this was found).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.backfill_race_distance import parse_distance_to_yards


def test_furlongs_only():
    assert parse_distance_to_yards("6f") == 6 * 220
    assert parse_distance_to_yards("5f") == 5 * 220


def test_half_furlong():
    assert parse_distance_to_yards("6½f") == 6 * 220 + 110
    assert parse_distance_to_yards("4½f") == 4 * 220 + 110


def test_miles_only():
    assert parse_distance_to_yards("2m") == 2 * 1760
    assert parse_distance_to_yards("1m") == 1760


def test_miles_and_furlongs():
    assert parse_distance_to_yards("1m4f") == 1760 + 4 * 220
    assert parse_distance_to_yards("2m3½f") == 2 * 1760 + 3 * 220 + 110


def test_miles_half_furlong_only():
    assert parse_distance_to_yards("1m½f") == 1760 + 110


def test_unparseable_returns_none():
    assert parse_distance_to_yards("") is None
    assert parse_distance_to_yards(None) is None
    assert parse_distance_to_yards("garbage") is None
    assert parse_distance_to_yards("5 furlongs") is None


if __name__ == "__main__":
    tests = [
        test_furlongs_only,
        test_half_furlong,
        test_miles_only,
        test_miles_and_furlongs,
        test_miles_half_furlong_only,
        test_unparseable_returns_none,
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
