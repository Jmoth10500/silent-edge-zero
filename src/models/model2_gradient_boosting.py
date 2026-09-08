"""
Model 2 — gradient-boosted trees baseline (build brief Phase 7).

**Status: still synthetic-fixture-only, the same status Model 1 had before
Sessions 8/9 (interactive, Jonathan's Mac) trained it on real Kaggle data.**
This module and its test suite (`tests/test_model2_gradient_boosting.py`)
prove the maths and plumbing are correct against fixtures shaped exactly
like the real, verified racecard schema (`src/providers/racecard_theracingapi.py`
/ `tests/test_racecard_theracingapi.py`) — they are NOT evidence this model
predicts real racing. This cloud routine has no THERACINGAPI_* or Kaggle
credentials (see docs/BUILD_LOG.md) and cannot reach or reproduce the real
558K-row historical dataset that lives only in Postgres on Jonathan's Mac.
Training Model 2 against that real data is Mac-only work for a future
interactive session — `scripts/train_model2.py` (added alongside this
module) mirrors `scripts/train_model1.py`'s shape exactly and is ready to
run there.

**Why a new model class, not another Model 1 feature:** `docs/RESEARCH_LAB.md`
RL-006 concluded that Model 1 (a linear conditional-logit/softmax) did not
beat the market baseline (Model 0) even with a clean, confound-free 5-feature
set, and that further tuning of that same linear feature shape was unlikely
to close the gap. The next real lever flagged there is a genuinely different
model class capable of nonlinearities and feature interactions a linear
score cannot represent — the "Model 2, gradient boosting" option named
explicitly in that entry and anticipated since Phase 1 in
`requirements.txt`'s "Phase 6+ (not yet used...)" comment block.

**Model shape:** unlike Model 1's true per-race multinomial logit (one joint
softmax fit jointly across a race's own runners), Model 2 is a per-RUNNER
binary classifier — P(this runner wins | features) — fit by gradient-boosted
decision trees (`sklearn.ensemble.HistGradientBoostingClassifier`) on the
observed win/lose label, one training row per (race, runner). Because each
runner's raw predicted probability comes from an INDEPENDENT binary
classification rather than a joint per-race softmax, the raw outputs do not
sum to 1.0 per race on their own; `predict_race_probabilities` renormalises
them to do so (`_renormalize` below) — a real per-race probability
distribution, arrived at a third way after Model 0's de-vigging and Model
1's softmax. This is a simpler normalisation than a true joint tree model
would need (it cannot, for instance, represent "if runner A is strong,
runner B's chances fall by more than proportionally") and is flagged as a
modelling simplification in `docs/RESEARCH_LAB.md` RL-008, not asserted as
equivalent to a joint model.

**Why scikit-learn, unlike this repo's other numerical work:** the market
de-vig bisection solvers (`src/market/probability.py`) and Model 1's own
gradient ascent (`src/models/model1_logistic_baseline.py`) are small enough
that this repo implemented them from scratch rather than add a dependency.
A correct, efficient gradient-boosted tree implementation (histogram
binning, split-gain search, leaf-value shrinkage, tree pruning, ...) is a
different scale of surface area — using the same free, open-source,
well-tested library most of the industry uses is the responsible choice
here, not a shortcut. `requirements.txt`'s scikit-learn line is uncommented
for the first time this session; no other Phase 6+ dependency (catboost/
xgboost/lightgbm/pandas/polars) is needed yet.

**Same features as Model 1, deliberately:** this module reuses
`src/models/model1_logistic_baseline.py::build_race_features`/
`FEATURE_NAMES` (rating vs. field mean, draw percentile vs. 0.5,
recency-weighted form vs. field mean, weight vs. field mean, and the
missing-rating indicator) rather than inventing a new feature set. The
point of Model 2 is to test whether a different MODEL CLASS over the SAME
information does better — isolating that one variable — not to also change
what the model can see.
"""
from dataclasses import dataclass
from typing import Optional, Sequence

from src.features.runner_features import RunnerFeatureInput
from src.models.model1_logistic_baseline import (
    FEATURE_NAMES,
    TrainingRace,
    build_race_features,
)

try:
    from sklearn.ensemble import HistGradientBoostingClassifier
except ImportError as exc:  # pragma: no cover - environment guard, not exercised by tests
    raise ImportError(
        "Model 2 needs scikit-learn (uncommented in requirements.txt for "
        "Phase 7). Run `pip install -r requirements.txt`."
    ) from exc


# Deterministic (random_state fixed), never used to draw a random train/test
# split — ground rule 5 ("no random train/test splits, ever") is about
# chronological data splitting (src/validation/walk_forward.py handles
# that), not an estimator's own internal tie-breaking. Fixing it here only
# makes repeated fits on the SAME data reproducible, the same reason
# fit_logistic_baseline's tests always pass explicit learning_rate/l2/
# iterations rather than relying on defaults that might change.
DEFAULT_GBM_KWARGS: dict = dict(
    max_iter=100,
    max_depth=3,
    learning_rate=0.1,
    l2_regularization=0.0,
    random_state=0,
)


@dataclass(frozen=True)
class GradientBoostingModel:
    """A fitted Model 2. Just a thin wrapper around the fitted sklearn
    estimator so callers elsewhere in this codebase never need to import
    sklearn types directly — same "hide the library behind our own shape"
    pattern the rest of this module follows."""

    classifier: HistGradientBoostingClassifier


def _feature_row(features: dict) -> list:
    return [features[name] for name in FEATURE_NAMES]


def _renormalize(raw: Sequence[float]) -> list:
    """Scale independent per-runner probabilities so they sum to 1.0 across
    a race. Pulled out as its own pure function (rather than inlined in
    `predict_race_probabilities`) so the degenerate all-zero case can be
    unit-tested directly, without needing a real fitted classifier to force
    it. Returns a uniform 1/n split if every raw value is <= 0.0 (not a
    valid probability distribution to divide by zero into) rather than
    raising or silently returning all-0.0."""
    total = sum(raw)
    n = len(raw)
    if n == 0:
        return []
    if total <= 0.0:
        return [1.0 / n] * n
    return [float(p) / total for p in raw]


def fit_gradient_boosting_baseline(
    races: Sequence[TrainingRace],
    **gbm_kwargs,
) -> GradientBoostingModel:
    """Fit Model 2: one training row per (race, runner) — features from
    `build_race_features` (Model 1's same 5-key race-relative vector),
    label 1 for the race's observed winner, 0 for every other runner in
    that race. Raises ValueError for an empty `races`, or if any race's
    `winner_horse_id` isn't among that race's own runners — same discipline
    as `fit_logistic_baseline`, a caller data bug, never silently skipped.
    """
    if not races:
        raise ValueError("cannot fit on an empty race list")

    X: list = []
    y: list = []
    for race in races:
        horse_ids = {r.horse_id for r in race.runners}
        if race.winner_horse_id not in horse_ids:
            raise ValueError(
                f"winner_horse_id={race.winner_horse_id} is not among this "
                f"race's own runners {sorted(horse_ids)}"
            )
        feats = build_race_features(race.runners)
        for hid, f in feats.items():
            X.append(_feature_row(f))
            y.append(1 if hid == race.winner_horse_id else 0)

    params = dict(DEFAULT_GBM_KWARGS)
    params.update(gbm_kwargs)
    clf = HistGradientBoostingClassifier(**params)
    clf.fit(X, y)
    return GradientBoostingModel(classifier=clf)


def predict_race_probabilities(
    runners: Sequence[RunnerFeatureInput],
    model: Optional[GradientBoostingModel] = None,
) -> dict:
    """Model 2's prediction: each runner's independent P(win) from the
    fitted binary classifier, renormalised to sum to 1.0 across the race
    (see module docstring for why this differs from Model 1's softmax,
    which sums to 1.0 by construction with no separate step needed).

    Unlike Model 0/1, there is no meaningful "untrained but well-defined"
    prediction — `model=None` raises ValueError rather than silently
    falling back to uniform, because an unfitted sklearn estimator can't
    produce a probability at all (it would raise inside sklearn instead,
    less clearly). Also raises ValueError for an empty race, matching
    `model0_market_baseline.predict_race_probabilities` and
    `model1_logistic_baseline.predict_race_probabilities`.
    """
    if not runners:
        raise ValueError("cannot predict an empty race")
    if model is None:
        raise ValueError(
            "Model 2 has no meaningful untrained prediction (unlike Model "
            "0/1) — pass a GradientBoostingModel from "
            "fit_gradient_boosting_baseline"
        )

    feats = build_race_features(runners)
    horse_ids = [r.horse_id for r in runners]
    X = [_feature_row(feats[hid]) for hid in horse_ids]
    raw = model.classifier.predict_proba(X)[:, 1]  # P(class=1, i.e. "wins")

    normalized = _renormalize(list(raw))
    return dict(zip(horse_ids, normalized))
