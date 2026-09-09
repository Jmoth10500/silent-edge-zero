"""
Model 1 — statistical/logistic baseline (Phase 6, the first FITTED model in
this repo).

**Update 2026-09-08 — this HAS now been fit and walk-forward validated
against real outcomes** (`scripts/train_model1.py`, ~487k real runner
predictions across 18 chronological folds, 2023-06 to 2026-06, sourced from
the real Kaggle historical dataset — see `docs/FREE_DATA_SOURCES.md` #2).
The honest result: Model 1 did NOT beat Model 0 (the de-vigged market
baseline) on Brier score or log loss, on any of the 18 folds. Full detail
in `docs/RESEARCH_LAB.md` RL-006, including a known confound (the Kaggle
data has no form-history column, so `form_edge` has been running on zero
real signal so far — effectively three working features, not four). This
module's maths and unit tests were originally built and verified against
synthetic fixtures only, exactly as described below; that description is
kept for the historical record of what was and wasn't tested when.

Every weight this module's *tests* produce still comes from synthetic
fixtures shaped like the real, verified racecard schema
(`src/providers/racecard_theracingapi.py` /
`tests/test_racecard_theracingapi.py` — e.g. `official_rating` as an int,
`draw` as an int, `recent_form` as an undelimited string like `"1582F3"`) —
that part of the module (`tests/test_model1_logistic_baseline.py`) was never
about proving real predictive power, only that gradient ascent recovers the
sign of an injected signal. The real predictive claim now lives in the
`scripts/train_model1.py` result above, not in this module's own test
suite.

Model shape: a per-race multinomial logit (softmax) over a small, fixed set
of race-RELATIVE runner features built from `src/features/runner_features.py`
(rating vs. field mean, draw percentile vs. 0.5, recency-weighted form score
vs. field mean, weight vs. field mean). Because the softmax's normalising
sum is taken over that race's own runners (not some global constant), the
output is a probability distribution over "which runner in THIS race wins"
by construction — it sums to 1.0 per race without a separate renormalisation
step, same guarantee Model 0 gets from de-vigging, arrived at a different
way.

Every feature is deliberately UNDIRECTED: `build_race_features` centers each
stat on the race's own mean (among runners with a known value) and leaves
the fitted weight's sign to say whether higher is better — it never assumes
e.g. "a low draw is an advantage" the way an earlier draft might have. This
follows the same discipline as RL-004's `draw_bias_features` (a neutral
positional fact, not a bias claim) one level up: the feature is neutral AND
the weight that would turn it into a claim only gets set by `fit`, which
this repo has never run on real outcomes.

**Update 2026-09-09 — a real 6th feature, `draw_bias_edge` (RL-004), was
added and re-tested against the same real data:** pooled Brier barely
moved (0.0875, unchanged). A genuine null result — see RL-004 in
`docs/RESEARCH_LAB.md` for the real `race.distance_yards` data bug found
and fixed along the way (the feature was silently getting zero real data
on the first attempt, which is why that first run looked unchanged for
the wrong reason).

**Update 2026-09-09 — a real 7th feature, `going_affinity_edge` (RL-001b,
reframed from a weather hypothesis to real per-horse ground-going
affinity — see `src/features/going_affinity.py`'s module docstring for
why a bare weather/going value can't work as a main effect in a per-race
softmax), was added and re-tested:** pooled Brier unchanged for THIS
model (0.0875) but measurably worsened Model 2's real result (see
`src/models/model2_gradient_boosting.py`). A genuine result, feature
confirmed genuinely populated before trusting it.

Session 5's RL-006 entry flagged one simplification explicitly for review:
a runner missing `official_rating` got `rating_edge=0.0`, the same value as
a genuinely average-rated runner — "no evidence" and "average" were
indistinguishable to the model. `no_rating_flag` (added this session, still
synthetic-only) fixes that: it's a plain 1.0/0.0 indicator, 1.0 for a
runner with no official_rating at all (the common shape of a first-time-out
debutant), 0.0 otherwise, with its own separately-fitted weight — so
`fit_logistic_baseline` can learn that missing-rating itself carries signal
distinct from "average rating", instead of the two being silently
conflated. Like every other feature here, this is a hypothesis the fitted
weight's sign will decide, never asserted up front.

Trained by plain batch gradient ascent on the observed winner's
log-likelihood, in pure Python — no numpy/scikit-learn. Both are still
commented out in requirements.txt; this repo has done its own small-scale
numerical methods throughout (e.g. `src/market/probability.py`'s bisection
solvers for the power/Shin de-vig methods), and a handful of race-relative
features doesn't yet justify pulling in a heavier dependency.
"""
import math
from dataclasses import dataclass
from typing import Optional, Sequence

from src.features.draw_bias_history import DrawBiasTable, draw_bias_edge as _draw_bias_edge
from src.features.going_affinity import going_interaction_edge as _going_interaction_edge
from src.features.runner_features import (
    RunnerFeatureInput,
    draw_bias_features,
    form_score,
    relative_official_rating,
    relative_weight,
)

FEATURE_NAMES = (
    "rating_edge", "draw_edge", "form_edge", "weight_edge", "no_rating_flag",
    "draw_bias_edge",
)
# `going_affinity_edge` (RL-001b) is deliberately NOT in the active feature
# set: real-tested 2026-09-09, it made no difference to Model 1 and
# measurably WORSENED Model 2 (0.0874 -> 0.0878 pooled Brier, see
# docs/RESEARCH_LAB.md RL-001b) — a genuine negative result, not a bug.
# `build_race_features` below still computes it (the plumbing is real,
# tested, and cheap to keep) so it's a one-line re-add to FEATURE_NAMES if
# future evidence (e.g. a stricter min_runs_per_side, or more real data)
# changes this conclusion — it is simply excluded from what either model
# actually trains on or scores with, same "same feature set" comparison
# discipline RL-008 established between Model 1 and Model 2.
#
# ALL_COMPUTED_FEATURE_NAMES is the full shape build_race_features() always
# returns (including the excluded going_affinity_edge) — use this, not
# FEATURE_NAMES, when asserting against the RAW per-runner dict shape;
# FEATURE_NAMES is specifically "what the models score/fit with".
ALL_COMPUTED_FEATURE_NAMES = FEATURE_NAMES + ("going_affinity_edge",)

# Untrained default: every weight at 0.0 means every runner's score is 0.0
# regardless of its features, so predict_race_probabilities falls back to a
# uniform 1/n split — an honest "we have learned nothing" starting point,
# not a disguised guess. Mirrors Model 0's own "no parameters" honesty
# (src/models/model0_market_baseline.py), just at the weight-vector level.
DEFAULT_WEIGHTS: dict[str, float] = {name: 0.0 for name in FEATURE_NAMES}


def build_race_features(
    runners: Sequence[RunnerFeatureInput],
    draw_bias_table: Optional[DrawBiasTable] = None,
    course_id: Optional[int] = None,
    distance_yards: Optional[int] = None,
    going_affinity_table: Optional[dict[int, float]] = None,
    going: Optional[str] = None,
) -> dict[int, dict[str, float]]:
    """Race-relative, zero-centered feature vector per horse_id — Model 1's
    input row.

    Every value is "this runner's raw stat minus the race's own mean among
    runners with a KNOWN value for that stat" (or, for draw, percentile
    minus 0.5 — the same centering, just already 0-1 scaled by
    `draw_bias_features`). A runner missing a given underlying field (no
    rating, no parseable form, ...) gets 0.0 for that one feature — read as
    "no evidence either way for this runner", not as a claim that the
    runner is exactly average. This is a modelling simplification (it
    treats missing != average as if they were interchangeable for scoring
    purposes), flagged honestly rather than silently — see RL-006 — and
    every runner still gets a full feature dict (all four keys, always),
    unlike `src/features/feature_vector.py` which omits missing keys
    entirely; a softmax score needs a real number for every runner or the
    race can't be scored at all.

    `no_rating_flag` is the one exception to "0.0 = no evidence either
    way": it is 1.0 whenever `official_rating` is missing (and 0.0 when
    it's known), so a debutant-shaped runner is distinguishable from a
    genuinely average-rated one — see the module docstring and RL-006.

    `draw_bias_edge` (RL-004/RL-008) is this runner's historical
    course+distance draw-tercile win rate vs. the naive uniform
    expectation, looked up from `draw_bias_table` (built by the caller
    from ONLY strictly-earlier real outcomes — see
    `src/features/draw_bias_history.py` for the leakage discipline this
    relies on). Defaults to 0.0 ("no evidence") whenever `draw_bias_table`
    is None, `course_id`/`distance_yards` aren't given, or the specific
    bucket has insufficient real sample size — same convention as every
    other feature here.

    `going_affinity_edge` (RL-001) is this runner's own historical
    soft/fast-ground affinity (looked up from `going_affinity_table`, built
    by the caller from ONLY strictly-earlier real outcomes — see
    `src/features/going_affinity.py`) times a +1/-1 indicator of whether
    TODAY's `going` is on the soft or fast side of its own scale. Unlike
    every other feature here, this one is a deliberate INTERACTION term —
    `going` itself is identical for every runner in a race and would be
    mathematically invisible to a per-race softmax (or Model 2's per-race
    renormalisation), so it only enters through each horse's own past
    affinity. Defaults to 0.0 ("no evidence") whenever the table is None,
    the horse has no table entry, or today's `going` is missing/
    unrecognised — see `going_affinity.py` for the "never guessed" rule
    this follows.

    Returns {} for an empty `runners` sequence.
    """
    if not runners:
        return {}

    rating = relative_official_rating(runners)
    draw = draw_bias_features(runners)
    weight = relative_weight(runners)

    form_scores = {r.horse_id: form_score(r.recent_form) for r in runners}
    known_form = [v for v in form_scores.values() if v is not None]
    mean_form = sum(known_form) / len(known_form) if known_form else None

    out: dict[int, dict[str, float]] = {}
    for r in runners:
        rating_edge = rating[r.horse_id]["rating_vs_mean"] if r.horse_id in rating else 0.0
        draw_edge = (draw[r.horse_id]["draw_percentile"] - 0.5) if r.horse_id in draw else 0.0
        weight_edge = weight[r.horse_id]["weight_vs_mean_lbs"] if r.horse_id in weight else 0.0
        fs = form_scores.get(r.horse_id)
        form_edge = (fs - mean_form) if (fs is not None and mean_form is not None) else 0.0
        no_rating_flag = 0.0 if r.horse_id in rating else 1.0
        db_edge = _draw_bias_edge(
            draw_bias_table or {}, course_id, distance_yards, r.draw, len(runners),
        )
        ga_edge = _going_interaction_edge(r.horse_id, going, going_affinity_table or {})
        out[r.horse_id] = {
            "rating_edge": rating_edge,
            "draw_edge": draw_edge,
            "form_edge": form_edge,
            "weight_edge": weight_edge,
            "no_rating_flag": no_rating_flag,
            "draw_bias_edge": db_edge,
            "going_affinity_edge": ga_edge,
        }
    return out


def _linear_score(features: dict[str, float], weights: dict[str, float]) -> float:
    return sum(weights.get(name, 0.0) * features[name] for name in FEATURE_NAMES)


def _softmax(scores: dict[int, float]) -> dict[int, float]:
    """Softmax with max-subtraction for numerical stability (standard trick
    — exp() of a large raw score would otherwise overflow before the
    normalising division ever happens)."""
    max_score = max(scores.values())
    exps = {hid: math.exp(s - max_score) for hid, s in scores.items()}
    total = sum(exps.values())
    return {hid: e / total for hid, e in exps.items()}


def predict_race_probabilities(
    runners: Sequence[RunnerFeatureInput],
    weights: Optional[dict[str, float]] = None,
    draw_bias_table: Optional[DrawBiasTable] = None,
    course_id: Optional[int] = None,
    distance_yards: Optional[int] = None,
    going_affinity_table: Optional[dict[int, float]] = None,
    going: Optional[str] = None,
) -> dict[int, float]:
    """Model 1's prediction: softmax over the linear score of each runner's
    race-relative feature vector, keyed by horse_id. Sums to 1.0 (up to
    float rounding) by construction. `weights=None` (default) uses
    DEFAULT_WEIGHTS — i.e. an untrained model, which is provably uniform
    (see `test_predict_with_default_weights_is_uniform`). Raises ValueError
    for an empty race, matching `model0_market_baseline.predict_race_probabilities`.
    `draw_bias_table`/`course_id`/`distance_yards` and
    `going_affinity_table`/`going` are optional and only feed
    `draw_bias_edge`/`going_affinity_edge` — see `build_race_features`.
    """
    if not runners:
        raise ValueError("cannot predict an empty race")
    weights = weights if weights is not None else DEFAULT_WEIGHTS
    feats = build_race_features(
        runners, draw_bias_table, course_id, distance_yards, going_affinity_table, going,
    )
    scores = {hid: _linear_score(f, weights) for hid, f in feats.items()}
    return _softmax(scores)


@dataclass(frozen=True)
class TrainingRace:
    """One labelled race for fitting: its runners' features and which
    horse_id actually won. NEVER construct this from anything but a real
    result once real results exist — in this repo today every caller of
    `fit_logistic_baseline` in tests/ builds these from synthetic fixtures,
    clearly labelled as such, per the ground rule against presenting
    fabricated data as real."""

    runners: Sequence[RunnerFeatureInput]
    winner_horse_id: int
    course_id: Optional[int] = None
    distance_yards: Optional[int] = None
    going: Optional[str] = None


def fit_logistic_baseline(
    races: Sequence[TrainingRace],
    learning_rate: float = 0.05,
    iterations: int = 500,
    l2: float = 0.01,
    initial_weights: Optional[dict[str, float]] = None,
    draw_bias_table: Optional[DrawBiasTable] = None,
    going_affinity_table: Optional[dict[int, float]] = None,
) -> dict[str, float]:
    """Batch gradient ASCENT on the multinomial-logit log-likelihood of the
    observed winners (equivalently: descent on cross-entropy loss). Pure
    Python — see module docstring for why no numpy/scikit-learn yet.

    Standard softmax-regression gradient: for feature `name`, summed over
    races, d(log-likelihood)/d(weight[name]) = sum over runners of
    features[name] * (is_winner - predicted_probability). L2-regularised
    (`l2 * weight` subtracted from the gradient each step) to keep weights
    bounded — without it, gradient ascent can run away when a field is
    small or a feature is mostly the neutral 0.0 default (see
    `build_race_features`'s missing-data handling).

    Raises ValueError for an empty `races`, or if any race's
    winner_horse_id isn't among that race's own runners — same discipline
    as `model0_market_baseline.evaluate_market_baseline_walk_forward`: a
    caller data bug, never silently skipped.
    """
    if not races:
        raise ValueError("cannot fit on an empty race list")

    weights = dict(initial_weights) if initial_weights is not None else dict(DEFAULT_WEIGHTS)

    race_features: list[tuple[dict[int, dict[str, float]], int]] = []
    for race in races:
        horse_ids = {r.horse_id for r in race.runners}
        if race.winner_horse_id not in horse_ids:
            raise ValueError(
                f"winner_horse_id={race.winner_horse_id} is not among this "
                f"race's own runners {sorted(horse_ids)}"
            )
        race_features.append((
            build_race_features(
                race.runners, draw_bias_table, race.course_id, race.distance_yards,
                going_affinity_table, race.going,
            ),
            race.winner_horse_id,
        ))

    n_races = len(race_features)
    for _ in range(iterations):
        gradients = {name: 0.0 for name in FEATURE_NAMES}
        for feats, winner_id in race_features:
            scores = {hid: _linear_score(f, weights) for hid, f in feats.items()}
            probs = _softmax(scores)
            for hid, f in feats.items():
                error = (1.0 if hid == winner_id else 0.0) - probs[hid]
                for name in FEATURE_NAMES:
                    gradients[name] += f[name] * error

        for name in FEATURE_NAMES:
            step = (gradients[name] / n_races) - l2 * weights[name]
            weights[name] += learning_rate * step

    return weights
