"""
Model 0 — the market baseline (build brief Sections 18/19-ish territory,
plus the Section 24/29 pipeline plumbing wired around it).

This is deliberately NOT a trained model: it has no parameters, nothing is
fit, and it never will be improved by more data on its own. It treats the
de-vigged market-implied probability (src/market/probability.py) AS the
prediction. Its purpose is to give the rest of the pipeline — chronological
walk-forward splitting (src/validation/walk_forward.py) and Brier/log-loss/
calibration scoring (src/evaluation/calibration.py) — something real, if
dumb, to run end-to-end before any actual trained model exists. Every real
model built later should beat this baseline; if it can't, it isn't adding
anything the market didn't already know.

Still synthetic-fixture-only for now (see tests/test_model0_market_baseline.py)
— Model 0 needs the same odds data any other model would need, and that
data source (The Racing API / Betfair, see docs/FREE_DATA_SOURCES.md) is
still blocked on account signups only Jonathan can do. The plumbing itself
has no such dependency and is fully real and tested.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional, Sequence

from src.evaluation.calibration import CalibrationBin, brier_score, calibration_curve, log_loss
from src.market.probability import METHODS
from src.validation.walk_forward import walk_forward_splits


@dataclass(frozen=True)
class RunnerOdds:
    horse_id: int
    decimal_odds: float


@dataclass(frozen=True)
class RaceRecord:
    """One race for the purposes of this baseline: its runners' odds, its
    date (for chronological splitting), and which horse actually won."""

    race_id: int
    race_date: date
    runners: Sequence[RunnerOdds]
    winner_horse_id: int


def predict_race_probabilities(
    runners: Sequence[RunnerOdds], method: str = "power"
) -> dict[int, float]:
    """Model 0's entire "prediction": the chosen de-vig method's fair
    probability for each runner, keyed by horse_id. Raises ValueError for
    an unknown method or an empty race — both are caller bugs, not data
    conditions to silently paper over."""
    if method not in METHODS:
        raise ValueError(f"unknown method {method!r}, must be one of {sorted(METHODS)}")
    if not runners:
        raise ValueError("cannot predict an empty race")
    odds = [r.decimal_odds for r in runners]
    probs = METHODS[method](odds)
    return {r.horse_id: p for r, p in zip(runners, probs)}


@dataclass(frozen=True)
class SplitEvaluation:
    train_end: date
    test_end: date
    n_races: int
    n_runner_predictions: int
    brier: float
    log_loss: float
    calibration: list[CalibrationBin]


def evaluate_market_baseline_walk_forward(
    races: Sequence[RaceRecord],
    min_train_days: int,
    test_window_days: int,
    method: str = "power",
    step_days: Optional[int] = None,
    expanding: bool = True,
    n_calibration_bins: int = 10,
) -> list[SplitEvaluation]:
    """End-to-end smoke pipeline: chronological walk-forward split
    (Section 29) -> Model 0 prediction per test-window race -> Brier/log
    loss/calibration scoring (Section 24), all against `races`.

    Model 0 has no parameters to fit, so each split's `train_indices` are
    produced by walk_forward_splits but genuinely unused here — that is
    intentional, not a bug: this function exercises the exact split/predict/
    score shape a real trained model will use later, with a baseline that
    happens not to need the train half. Only rows in each split's
    `test_indices` are ever scored.

    Raises ValueError if `races` is empty, or if any race's
    winner_horse_id isn't one of that race's own runners (a caller data bug
    — silently skipping it would hide the mistake, not fix it).
    """
    if not races:
        raise ValueError("cannot evaluate an empty race list")

    dates = [r.race_date for r in races]
    splits = walk_forward_splits(
        dates,
        min_train_days=min_train_days,
        test_window_days=test_window_days,
        step_days=step_days,
        expanding=expanding,
    )

    evaluations: list[SplitEvaluation] = []
    for split in splits:
        predicted_probs: list[float] = []
        outcomes: list[int] = []
        for i in split.test_indices:
            race = races[i]
            horse_ids = {r.horse_id for r in race.runners}
            if race.winner_horse_id not in horse_ids:
                raise ValueError(
                    f"race_id={race.race_id}: winner_horse_id={race.winner_horse_id} "
                    f"is not among its own runners {sorted(horse_ids)}"
                )
            probs = predict_race_probabilities(race.runners, method=method)
            for horse_id, p in probs.items():
                predicted_probs.append(p)
                outcomes.append(1 if horse_id == race.winner_horse_id else 0)

        evaluations.append(
            SplitEvaluation(
                train_end=split.train_end,
                test_end=split.test_end,
                n_races=len(split.test_indices),
                n_runner_predictions=len(predicted_probs),
                brier=brier_score(predicted_probs, outcomes),
                log_loss=log_loss(predicted_probs, outcomes),
                calibration=calibration_curve(predicted_probs, outcomes, n_bins=n_calibration_bins),
            )
        )
    return evaluations
