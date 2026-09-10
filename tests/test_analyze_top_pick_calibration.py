"""
Real tests for scripts/analyze_top_pick_calibration.py's pure bucketing
and summarising functions. The walk-forward retraining half is exercised
by actually running the script (same discipline as every other backtest
script in this repo).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.analyze_top_pick_calibration import BIN_EDGES, bucket, summarise


def test_bucket_real_edges():
    assert bucket(0.05) == 0    # [0.0, 0.15)
    assert bucket(0.149) == 0
    assert bucket(0.15) == 1    # [0.15, 0.20)
    assert bucket(0.216) == 2   # [0.20, 0.25) — matches the real 21.6% example that prompted this
    assert bucket(0.50) == len(BIN_EDGES) - 2  # top bin
    assert bucket(0.99) == len(BIN_EDGES) - 2


def test_summarise_real_shape():
    records = [(0.20, True), (0.22, False), (0.24, False), (0.24, True)]
    out = summarise(records)
    assert len(out) == 1
    row = out[0]
    assert row["n"] == 4
    assert row["predicted"] == (0.20 + 0.22 + 0.24 + 0.24) / 4
    assert row["actual"] == 0.5  # 2 of 4 won


def test_summarise_never_fabricates_empty_bins():
    records = [(0.20, True)]
    out = summarise(records)
    assert len(out) == 1  # only the one real bin with data, not all 9 possible bins


def test_summarise_multiple_bins_independent():
    records = [(0.20, True), (0.20, False), (0.40, True)]
    out = summarise(records)
    low_bin = next(r for r in out if r["low"] == 0.20)
    high_bin = next(r for r in out if r["low"] == 0.40)
    assert low_bin["n"] == 2
    assert low_bin["actual"] == 0.5
    assert high_bin["n"] == 1
    assert high_bin["actual"] == 1.0


if __name__ == "__main__":
    tests = [
        test_bucket_real_edges,
        test_summarise_real_shape,
        test_summarise_never_fabricates_empty_bins,
        test_summarise_multiple_bins_independent,
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
