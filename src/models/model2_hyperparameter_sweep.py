"""
Model 2 hyperparameter-sweep stability check (build brief Phase 7 follow-up).

**Status: synthetic-fixture-only, same discipline as every other module in
this repo before it touches real data.** This is NOT a benchmark of which
hyperparameters are "best" for real racing — that question needs real
(racecard, result) pairs, which this cloud routine cannot reach (no
THERACINGAPI_*/Kaggle credentials, see docs/BUILD_LOG.md). What this module
answers instead is narrower and genuinely answerable now: across a range of
reasonable `HistGradientBoostingClassifier` settings, does
`fit_gradient_boosting_baseline`/`predict_race_probabilities`
(`src/models/model2_gradient_boosting.py`) behave sanely and consistently on
the same injected signal, or is the current default an accident that a
slightly different setting would silently break?

**Why this exists now:** flagged as open since Session 10
(`docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` / `docs/BUILD_LOG.md`, "a
hyperparameter sweep... to confirm the fitting is reasonably stable across
settings before a real run burns Mac time on a bad default") and repeated,
still undone, in Session 11 and Session 12's own "next session" lists. The
real payoff: `scripts/train_model2.py` is Mac-only and every run against the
real 558K-row Kaggle data costs real wall-clock time on Jonathan's machine.
Confirming here, for free, that Model 2's fitting isn't fragile to
`max_depth`/`learning_rate`/`max_iter` choices means that Mac-side run can
trust its own default kwargs (or a small sensible grid) instead of
discovering instability only after burning that time.

**What "stability" means here, precisely:** on a synthetic fixture where one
runner-shape (via official_rating, deliberately the same shape
`test_model2_gradient_boosting.py::test_fit_recovers_rating_signal_on_held_out_race`
already uses) wins every training race, a stable fit should recover that
signal — rate the same runner-shape highest on a held-out race — across
every combination in a reasonable hyperparameter grid, not just the one
default combination the existing test happens to check. This says nothing
about which combination generalises best to real racing; it only says the
fitting procedure itself doesn't quietly fail to learn an unambiguous
signal for some fraction of reasonable settings.
"""
import itertools
from dataclasses import dataclass
from typing import Sequence

from src.models.model1_logistic_baseline import TrainingRace
from src.models.model2_gradient_boosting import (
    fit_gradient_boosting_baseline,
    predict_race_probabilities,
)


@dataclass(frozen=True)
class SweepResult:
    """One hyperparameter combination's outcome against the held-out race.

    `predicted_prob` is the fitted model's probability for
    `expected_winner_horse_id` specifically (not just "the argmax") so a
    caller can see gradations of confidence, not only a pass/fail bit.
    """

    params: dict
    predicted_prob: float
    is_top_ranked: bool


def sweep_gradient_boosting_hyperparameters(
    param_grid: dict,
    training_races: Sequence[TrainingRace],
    held_out_runners: Sequence,
    expected_winner_horse_id,
) -> list:
    """Fit Model 2 once per combination in the cartesian product of
    `param_grid` (e.g. {"max_depth": [2, 3, 4], "learning_rate": [0.1, 0.3]}),
    predict on the same `held_out_runners` race each time, and record whether
    `expected_winner_horse_id` came out on top.

    Raises ValueError for an empty grid, an empty grid value list, an empty
    `training_races`, or a `held_out_runners` that doesn't actually contain
    `expected_winner_horse_id` — all caller data bugs, never silently
    skipped, same discipline as `fit_gradient_boosting_baseline` itself.
    """
    if not param_grid:
        raise ValueError("param_grid must not be empty")
    for key, values in param_grid.items():
        if not values:
            raise ValueError(f"param_grid[{key!r}] must not be empty")
    if not training_races:
        raise ValueError("training_races must not be empty")

    held_out_ids = {r.horse_id for r in held_out_runners}
    if expected_winner_horse_id not in held_out_ids:
        raise ValueError(
            f"expected_winner_horse_id={expected_winner_horse_id!r} is not "
            f"among held_out_runners {sorted(held_out_ids, key=str)}"
        )

    keys = list(param_grid.keys())
    combos = itertools.product(*(param_grid[k] for k in keys))

    results = []
    for combo in combos:
        kwargs = dict(zip(keys, combo))
        model = fit_gradient_boosting_baseline(training_races, **kwargs)
        probs = predict_race_probabilities(held_out_runners, model=model)
        top_horse_id = max(probs, key=probs.get)
        results.append(
            SweepResult(
                params=kwargs,
                predicted_prob=probs[expected_winner_horse_id],
                is_top_ranked=(top_horse_id == expected_winner_horse_id),
            )
        )
    return results


def summarize_sweep(results: Sequence[SweepResult]) -> dict:
    """Roll a list of `SweepResult` up into pass-rate/probability summary
    stats. Pulled out as its own pure function (rather than inlined wherever
    a sweep is run) so it can be unit-tested directly against hand-built
    result lists, without needing a real classifier fit to construct the
    degenerate all-pass/all-fail/mixed cases.

    Raises ValueError on an empty `results` — there is no meaningful summary
    of zero combinations, and silently returning e.g. a 0/0 pass rate would
    misleadingly look like "0% stable" rather than "nothing was run".
    """
    if not results:
        raise ValueError("cannot summarize an empty results list")

    n = len(results)
    n_top_ranked = sum(1 for r in results if r.is_top_ranked)
    probs = [r.predicted_prob for r in results]
    return {
        "n_combinations": n,
        "n_top_ranked": n_top_ranked,
        "top_ranked_rate": n_top_ranked / n,
        "min_predicted_prob": min(probs),
        "max_predicted_prob": max(probs),
        "mean_predicted_prob": sum(probs) / n,
    }
