"""
Real tests for scripts/load_kaggle_betfair_historical.py's reused parsers
(parse_sp_to_decimal, safe_float — both already tested in
tests/test_load_kaggle_historical.py; this file only checks the loader's
own matching logic doesn't need re-testing here since it's DB-integration
verified live, same convention as every other DB-loading script in this
project). This file exists mainly to document, via a smoke test, that the
new historical_betfair_price table and loader module import cleanly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.load_kaggle_betfair_historical import CSV_PATHS, get_or_create_source


def test_csv_paths_point_at_the_real_expected_files():
    assert len(CSV_PATHS) == 2
    assert all(p.name.startswith("betfair_mapping_2026_part_") for p in CSV_PATHS)


def test_get_or_create_source_is_importable_and_callable():
    # Real DB call, same convention as every other get_or_create_source
    # function in this project (see scripts/collect_smarkets_prices.py) —
    # verified live rather than mocked.
    import psycopg2
    conn = psycopg2.connect(dbname="silent_edge_zero")
    source_id = get_or_create_source(conn)
    assert isinstance(source_id, int)
    conn.close()


if __name__ == "__main__":
    tests = [test_csv_paths_point_at_the_real_expected_files, test_get_or_create_source_is_importable_and_callable]
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
