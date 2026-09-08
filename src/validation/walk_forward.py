"""
Walk-forward validation harness (build brief Section 29). No random
train/test splits, anywhere, ever (see docs/SILENT_EDGE_ZERO_ARCHITECTURE.md
rule 4) — every split produced here is defined purely by a chronological
cutoff. Tested against synthetic chronological data in
tests/test_walk_forward.py; ready to run against real race dates the moment
they exist.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence


@dataclass(frozen=True)
class WalkForwardSplit:
    """Indices refer back into the ORIGINAL `dates` sequence passed to
    walk_forward_splits, not into any sorted copy — callers can align a
    split straight back to their own row order (e.g. a list of predictions)
    without re-sorting anything themselves."""

    train_indices: list[int]
    test_indices: list[int]
    train_end: date  # inclusive: latest date allowed into train
    test_end: date  # inclusive: latest date allowed into this test window


def walk_forward_splits(
    dates: Sequence[date],
    min_train_days: int,
    test_window_days: int,
    step_days: int | None = None,
    expanding: bool = True,
) -> list[WalkForwardSplit]:
    """Produce a list of chronological walk-forward splits.

    - `dates[i]` is the date associated with row `i` (e.g. a race date).
      Not required to be sorted; sorting happens internally.
    - The first cutoff sits at `min(dates) + min_train_days` days, so the
      first split always has at least `min_train_days` of history behind it.
    - Each split's test window covers `(cutoff, cutoff + test_window_days]`
      — strictly after the cutoff, so no test row can share a date with the
      train cutoff itself.
    - `expanding=True` (default): train = every row with date <= cutoff
      (grows every split — the standard walk-forward shape).
      `expanding=False`: train = rows with date in
      `(cutoff - min_train_days, cutoff]` (a fixed-size rolling window).
    - The cutoff advances by `step_days` (default: `test_window_days`, i.e.
      non-overlapping test windows) each iteration until it reaches the
      last available date.
    - A split is only emitted if BOTH train and test are non-empty — a
      cutoff that lands past all available data produces no more splits.

    Raises ValueError on empty `dates`, or non-positive
    min_train_days/test_window_days/step_days.
    """
    if not dates:
        raise ValueError("dates must not be empty")
    if min_train_days <= 0:
        raise ValueError("min_train_days must be positive")
    if test_window_days <= 0:
        raise ValueError("test_window_days must be positive")
    step = step_days if step_days is not None else test_window_days
    if step <= 0:
        raise ValueError("step_days must be positive")

    indexed = sorted(range(len(dates)), key=lambda i: dates[i])
    max_date = dates[indexed[-1]]
    min_date = dates[indexed[0]]

    cutoff = min_date + timedelta(days=min_train_days)
    splits: list[WalkForwardSplit] = []

    while cutoff < max_date:
        test_end = cutoff + timedelta(days=test_window_days)

        if expanding:
            train_indices = [i for i in indexed if dates[i] <= cutoff]
        else:
            window_start = cutoff - timedelta(days=min_train_days)
            train_indices = [i for i in indexed if window_start < dates[i] <= cutoff]

        test_indices = [i for i in indexed if cutoff < dates[i] <= test_end]

        if train_indices and test_indices:
            # Hard safety net, not just documentation: every split produced
            # must actually be chronological. If this ever fires, it's a
            # bug in this function, not in a caller.
            assert max(dates[i] for i in train_indices) < min(dates[i] for i in test_indices), (
                "walk_forward_splits produced an overlapping/leaking split — this is a bug"
            )
            splits.append(
                WalkForwardSplit(
                    train_indices=train_indices,
                    test_indices=test_indices,
                    train_end=cutoff,
                    test_end=test_end,
                )
            )

        cutoff = cutoff + timedelta(days=step)

    return splits
