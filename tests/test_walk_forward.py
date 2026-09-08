"""
Real unit tests for src/validation/walk_forward.py, run against synthetic
chronological data (never real race dates) — run with:
    python3 -m pytest tests/test_walk_forward.py -v
or directly: python3 tests/test_walk_forward.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.walk_forward import walk_forward_splits

BASE = date(2026, 1, 1)


def day(offset: int) -> date:
    return BASE + timedelta(days=offset)


def test_splits_are_always_chronological():
    dates = [day(i) for i in range(100)]
    splits = walk_forward_splits(dates, min_train_days=30, test_window_days=10)
    assert len(splits) > 0
    for split in splits:
        max_train_date = max(dates[i] for i in split.train_indices)
        min_test_date = min(dates[i] for i in split.test_indices)
        assert max_train_date < min_test_date, "train must strictly precede test in every split"


def test_expanding_window_exact_split_count_and_sizes():
    dates = [day(i) for i in range(100)]  # offsets 0..99
    splits = walk_forward_splits(dates, min_train_days=30, test_window_days=10, expanding=True)
    # cutoffs at offset 30,40,...,90 (7 splits) -- see module docstring for the rule.
    assert len(splits) == 7
    assert splits[0].train_end == day(30)
    assert len(splits[0].train_indices) == 31  # offsets 0..30 inclusive
    assert len(splits[0].test_indices) == 10   # offsets 31..40 inclusive
    # expanding: train size must be non-decreasing split over split.
    sizes = [len(s.train_indices) for s in splits]
    assert sizes == sorted(sizes)
    assert sizes[-1] > sizes[0]


def test_rolling_window_train_size_stays_bounded():
    dates = [day(i) for i in range(100)]
    splits = walk_forward_splits(dates, min_train_days=30, test_window_days=10, expanding=False)
    assert len(splits) > 0
    for split in splits:
        # a rolling window of min_train_days can hold at most min_train_days rows
        # (one per day here), unlike the expanding case which keeps growing.
        assert len(split.train_indices) <= 30
    # confirm it's actually NOT expanding: last split's train shouldn't be
    # bigger than the first's, unlike the expanding-window test above.
    assert len(splits[-1].train_indices) <= len(splits[0].train_indices) + 1


def test_step_days_defaults_to_test_window_days():
    dates = [day(i) for i in range(100)]
    default_step = walk_forward_splits(dates, min_train_days=30, test_window_days=10)
    explicit_step = walk_forward_splits(dates, min_train_days=30, test_window_days=10, step_days=10)
    assert [ (s.train_end, s.test_end) for s in default_step] == [ (s.train_end, s.test_end) for s in explicit_step]


def test_smaller_step_than_window_overlaps_test_windows_but_stays_chronological():
    dates = [day(i) for i in range(60)]
    splits = walk_forward_splits(dates, min_train_days=20, test_window_days=10, step_days=5)
    assert len(splits) > 1
    # consecutive test windows can overlap now, but each split individually
    # must still respect train < test.
    for split in splits:
        assert max(dates[i] for i in split.train_indices) < min(dates[i] for i in split.test_indices)


def test_insufficient_history_produces_no_splits():
    dates = [day(i) for i in range(10)]  # only 10 days, need 30 to even start
    splits = walk_forward_splits(dates, min_train_days=30, test_window_days=10)
    assert splits == []


def test_indices_map_back_to_original_unsorted_order():
    # Deliberately shuffled so index order != chronological order.
    offsets = [50, 10, 90, 30, 70, 20, 80, 40, 60, 0] + list(range(1, 100))
    offsets = list(dict.fromkeys(offsets))  # dedupe, preserve first occurrence
    dates = [day(o) for o in offsets]
    splits = walk_forward_splits(dates, min_train_days=30, test_window_days=10)
    assert len(splits) > 0
    for split in splits:
        for i in split.train_indices:
            assert dates[i] <= split.train_end
        for i in split.test_indices:
            assert split.train_end < dates[i] <= split.test_end


def test_rejects_empty_dates():
    try:
        walk_forward_splits([], min_train_days=10, test_window_days=5)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_rejects_non_positive_parameters():
    dates = [day(i) for i in range(10)]
    for kwargs in [
        dict(min_train_days=0, test_window_days=5),
        dict(min_train_days=5, test_window_days=0),
        dict(min_train_days=5, test_window_days=5, step_days=0),
        dict(min_train_days=-1, test_window_days=5),
    ]:
        try:
            walk_forward_splits(dates, **kwargs)
            assert False, f"expected ValueError for {kwargs}"
        except ValueError:
            pass


if __name__ == "__main__":
    tests = [
        test_splits_are_always_chronological,
        test_expanding_window_exact_split_count_and_sizes,
        test_rolling_window_train_size_stays_bounded,
        test_step_days_defaults_to_test_window_days,
        test_smaller_step_than_window_overlaps_test_windows_but_stays_chronological,
        test_insufficient_history_produces_no_splits,
        test_indices_map_back_to_original_unsorted_order,
        test_rejects_empty_dates,
        test_rejects_non_positive_parameters,
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
