"""
Model 2 — gradient boosting (Phase 7, per the build brief's Section 39
progression: only reach for a more complex model once the simpler one has
been honestly tested and found wanting — see docs/RESEARCH_LAB.md RL-006/
RL-008).

**Update 2026-09-09 — this HAS now been fit and walk-forward validated
against real outcomes** (`scripts/train_model2.py`, ~487k real runner
predictions across the same 9 chronological folds and same real Kaggle
data as Model 1's own real test, 2023-06 to 2026-06). The honest result:
Model 2 beat Model 1 (pooled Brier 0.0873 vs. 0.0875, on 8 of 9 individual
folds) — a small but consistent edge from the different model class over
the IDENTICAL feature set — but did NOT beat Model 0 (the de-vigged market
baseline, Brier 0.0795) on any fold, and the gap to the market barely
moved versus Model 1's own gap. Full detail in `docs/RESEARCH_LAB.md`
RL-008. As with Model 1, this module's own tests only ever proved the
plumbing works on synthetic fixtures; the real predictive claim lives in
the training script's real output, not here.

**Why scikit-learn now, when Model 1 deliberately avoided numpy/scikit-learn:**
Model 1's own docstring explains that a hand-rolled solver was reasonable
for a 4-5 parameter logistic regression. A boosted-tree ensemble is a
different scale of problem — reimplementing histogram-based tree splitting
well would be a real project in itself, not a good use of time, and
scikit-learn's `HistGradientBoostingClassifier` is free/open-source and
was already anticipated in requirements.txt since Phase 6. This is the
first point in the project real justification exists to add the
dependency.

**Same discipline as Model 0/Model 1, carried forward:**
- Same race-relative feature set (`build_race_features` from
  `src/models/model1_logistic_baseline.py` — rating/draw/form/weight edges
  plus `no_rating_flag`), so any accuracy difference vs Model 1 is
  attributable to the model class, not a different feature shape. This is
  deliberate — the RL-006 question is "does a genuinely different model
  class do better with the SAME information", not "does more feature
  engineering help" (that's a separate, still-open question — see RL-004/
  RL-001).
- Framed as a per-runner binary classification (did THIS runner win: yes/
  no), not a native multiclass/per-race softmax — `HistGradientBoostingClassifier`
  has no race-grouped-choice objective built in, so raw per-runner win
  probabilities are renormalised to sum to 1.0 within each race
  (`_renormalise_race`), the same guarantee Model 0/Model 1 get a different
  way. This is a real, named modelling simplification (see RL-008), not
  hidden.
- No random splits anywhere in this module or its tests — training data
  ordering is the caller's responsibility (see `scripts/train_model2.py`
  for the real walk-forward-safe caller), same rule as Model 1.
- Every function here is testable on synthetic fixtures shaped like the
  real, verified racecard schema — this module makes no claim about real
  predictive power on its own; that claim (if any) lives in
  `scripts/train_model2.py`'s real walk-forward output, exactly like
  Model 1's split between "the maths works" (this module + its tests) and
  "here is what it actually does on real racing" (the training script).
"""
from dataclasses import dataclass
from typing import Optional, Sequence

from sklearn.ensemble import HistGradientBoostingClassifier

from src.models.model1_logistic_baseline import FEATURE_NAMES, build_race_features
from src.features.runner_features import RunnerFeatureInput

# Kept modest on purpose: the feature set is only 5 columns, all already
# heavily aggregated (race-relative edges, not raw per-row noise) — a deep,
# heavily-boosted model on 5 low-cardinality features risks overfitting to
# the training folds' particular noise rather than finding real signal.
# These are reasonable, documented starting defaults, not tuned; a
# hyperparameter sweep against the real walk-forward harness is flagged as
# a natural next step in RL-008, not done here.
DEFAULT_MAX_ITER = 150
DEFAULT_MAX_DEPTH = 4
DEFAULT_LEARNING_RATE = 0.05
DEFAULT_L2_REGULARIZATION = 0.1


def _feature_row(features: dict[str, float]) -> list[float]:
    return [features[name] for name in FEATURE_NAMES]


@dataclass(frozen=True)
class TrainingRace:
    """One labelled race for fitting — same shape and same discipline as
    `model1_logistic_baseline.TrainingRace`: never construct this from
    anything but a real result once real results exist; every caller in
    this module's own tests builds these from clearly-labelled synthetic
    fixtures."""

    runners: Sequence[RunnerFeatureInput]
    winner_horse_id: int


def fit_gradient_boosting(
    races: Sequence[TrainingRace],
    max_iter: int = DEFAULT_MAX_ITER,
    max_depth: int = DEFAULT_MAX_DEPTH,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    l2_regularization: float = DEFAULT_L2_REGULARIZATION,
    random_state: int = 0,
) -> HistGradientBoostingClassifier:
    """Fit a per-runner win/lose binary classifier over the race-relative
    feature set. `random_state` is fixed by default so a given training set
    always produces the same fitted model — determinism matters more here
    than exploring the seed space, same reasoning as everywhere else in
    this repo that avoids unexplained randomness.

    Raises ValueError for an empty `races`, or if any race's
    winner_horse_id isn't among that race's own runners — same discipline
    as `model1_logistic_baseline.fit_logistic_baseline`.
    """
    if not races:
        raise ValueError("cannot fit on an empty race list")

    X: list[list[float]] = []
    y: list[int] = []
    for race in races:
        horse_ids = {r.horse_id for r in race.runners}
        if race.winner_horse_id not in horse_ids:
            raise ValueError(
                f"winner_horse_id={race.winner_horse_id} is not among this "
                f"race's own runners {sorted(horse_ids)}"
            )
        feats = build_race_features(race.runners)
        for r in race.runners:
            X.append(_feature_row(feats[r.horse_id]))
            y.append(1 if r.horse_id == race.winner_horse_id else 0)

    if len(set(y)) < 2:
        # HistGradientBoostingClassifier cannot fit a single-class target —
        # every race contributes exactly one winner, so this can only
        # happen if every race in `races` has just one runner. Raise
        # honestly rather than let sklearn's own less-obvious error surface.
        raise ValueError(
            "cannot fit: no race in `races` produced both a winner (1) and "
            "at least one loser (0) row — every race needs >= 2 runners"
        )

    model = HistGradientBoostingClassifier(
        max_iter=max_iter,
        max_depth=max_depth,
        learning_rate=learning_rate,
        l2_regularization=l2_regularization,
        random_state=random_state,
    )
    model.fit(X, y)
    return model


def _renormalise_race(raw_probs: dict[int, float]) -> dict[int, float]:
    """Per-runner win probabilities from a binary classifier don't sum to
    1.0 over a race by construction (unlike Model 1's softmax or Model 0's
    de-vig) — divide each by the race's own total so the output is a real
    probability distribution over "which runner in THIS race wins", the
    same contract every other model in this repo honours.

    If every runner's raw probability is exactly 0.0 (degenerate, but
    possible from an undertrained model on an unusual feature combination),
    falls back to a uniform 1/n split rather than dividing by zero — same
    honest fallback shape as Model 1's untrained (all-zero-weight) case.
    """
    total = sum(raw_probs.values())
    if total <= 0.0:
        n = len(raw_probs)
        return {hid: 1.0 / n for hid in raw_probs}
    return {hid: p / total for hid, p in raw_probs.items()}


def predict_race_probabilities(
    runners: Sequence[RunnerFeatureInput],
    model: HistGradientBoostingClassifier,
) -> dict[int, float]:
    """Model 2's prediction: the fitted classifier's per-runner P(win) raw
    score, renormalised to sum to 1.0 across the race. Raises ValueError for
    an empty race, matching Model 0/Model 1.
    """
    if not runners:
        raise ValueError("cannot predict an empty race")

    feats = build_race_features(runners)
    rows = [_feature_row(feats[r.horse_id]) for r in runners]
    # predict_proba's column order matches model.classes_; class 1 = winner.
    win_col = list(model.classes_).index(1)
    raw = model.predict_proba(rows)[:, win_col]
    raw_probs = {r.horse_id: float(p) for r, p in zip(runners, raw)}
    return _renormalise_race(raw_probs)
