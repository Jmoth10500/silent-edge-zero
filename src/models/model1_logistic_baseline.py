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

**Update — wiring RL-004 (course/distance draw bias) and RL-001 (weather)
in, still synthetic-only:** `src/features/draw_bias.py` and
`src/features/weather_features.py` have existed as standalone, unit-tested
pure computations since Sessions 11/12, but neither was ever actually
plugged into a model's feature vector — every session since flagged this as
open plumbing rather than closing it. `build_race_features` now accepts two
optional, caller-supplied extras: `draw_bias_lookup` (one
`compute_course_distance_draw_bias()` result per horse_id, keyed the same
way the rest of this module keys everything) and `weather` (one
`weather_race_features()` result dict, applied identically to every runner
in the race — rainfall is a fact about the RACE, not about any one horse).
Both default to `None`, and when omitted every runner in that race gets the
SAME neutral 0.0 value plus a 1.0 "no data" flag for the corresponding
feature — because that flag is then a CONSTANT across every runner in the
race, and softmax is invariant to adding the same constant to every
runner's score, omitting these extras changes nothing about
`predict_race_probabilities`'s or `fit_logistic_baseline`'s existing
behaviour (verified in
`tests/test_model1_logistic_baseline.py::test_omitting_extras_matches_prior_behaviour`).
This is still no claim that a real draw bias or rainfall effect exists —
RL-004 and RL-001's actual hypotheses remain untested against real data,
completely unchanged by this — only that the plumbing to let a fitted
weight test them, the moment real historical draw-bias stats and real
racecard-linked weather exist, is no longer missing. `TrainingRace` and
`predict_race_probabilities` both thread the same two optional extras
through, per-race, so a future Mac-side training run can pass real data in
without any further wiring.

**A real mathematical finding surfaced while wiring this in, not a bug:**
`draw_bias_edge` varies PER RUNNER within a race (each horse has its own
draw), so it behaves like every other feature here. `rainfall_edge`/
`no_weather_flag` do not — weather is a fact about the RACE, identical for
every runner in it. Model 1's score is a per-race softmax, and softmax is
provably invariant to adding the same constant to every alternative's score
(this is the classic conditional-logit "choice-invariant covariate" result
— see e.g. McFadden 1974). That means, for THIS model class specifically,
the rainfall features' fitted weight can never move off its 0.0
initialisation, for ANY input data, ANY number of iterations — the gradient
w.r.t. a genuinely race-constant feature is exactly 0.0 by construction, not
just empirically small. `tests/test_model1_logistic_baseline.py::test_race_constant_weather_feature_never_gets_gradient`
proves this directly. This is NOT true of Model 2
(`src/models/model2_gradient_boosting.py`), which fits each runner as an
independent binary classification rather than a joint per-race choice, so a
race-level feature genuinely can carry information there — weather is a
real candidate feature for Model 2, not for Model 1 as built. The wiring
above is kept in this module anyway (both models share `build_race_features`,
and `draw_bias_edge` is genuinely useful here) but Model 1's own weight on
`rainfall_edge`/`no_weather_flag` should be expected to sit at exactly 0.0
even after a real Mac-side training run — that would be the model working
correctly, not a bug to chase.

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

from src.features.runner_features import (
    RunnerFeatureInput,
    draw_bias_features,
    form_score,
    relative_official_rating,
    relative_weight,
)

FEATURE_NAMES = (
    "rating_edge",
    "draw_edge",
    "form_edge",
    "weight_edge",
    "no_rating_flag",
    "draw_bias_edge",
    "no_draw_bias_flag",
    "rainfall_edge",
    "no_weather_flag",
)

# Untrained default: every weight at 0.0 means every runner's score is 0.0
# regardless of its features, so predict_race_probabilities falls back to a
# uniform 1/n split — an honest "we have learned nothing" starting point,
# not a disguised guess. Mirrors Model 0's own "no parameters" honesty
# (src/models/model0_market_baseline.py), just at the weight-vector level.
DEFAULT_WEIGHTS: dict[str, float] = {name: 0.0 for name in FEATURE_NAMES}


def build_race_features(
    runners: Sequence[RunnerFeatureInput],
    draw_bias_lookup: Optional[dict[int, Optional[dict]]] = None,
    weather: Optional[dict] = None,
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
    every runner still gets a full feature dict (every key in FEATURE_NAMES,
    always), unlike `src/features/feature_vector.py` which omits missing
    keys entirely; a softmax score needs a real number for every runner or
    the race can't be scored at all.

    `no_rating_flag` is the one exception to "0.0 = no evidence either
    way": it is 1.0 whenever `official_rating` is missing (and 0.0 when
    it's known), so a debutant-shaped runner is distinguishable from a
    genuinely average-rated one — see the module docstring and RL-006.

    `draw_bias_lookup` (optional) is this runner's own
    `src/features/draw_bias.py::compute_course_distance_draw_bias()` result,
    keyed by horse_id — pass `None` for a horse_id (or omit it from the
    dict, or omit `draw_bias_lookup` entirely) when that runner's draw
    couldn't be bucketed or there wasn't enough historical sample size;
    `draw_bias_edge` is that result's `win_rate_vs_baseline` when present,
    0.0 otherwise, with `no_draw_bias_flag` marking which case applies —
    same "flag, don't silently impute" discipline as `no_rating_flag`.

    `weather` (optional) is one `src/features/weather_features.py::weather_race_features()`
    result — a fact about the RACE, not about any one horse, so unlike
    `draw_bias_lookup` it is applied identically to every runner in `runners`.
    `rainfall_edge` is `weather["turf_rainfall_interaction"]` when present,
    0.0 otherwise, with `no_weather_flag` marking which case applies.

    Omitting `draw_bias_lookup`/`weather` entirely (the default) gives every
    runner in the race the SAME 0.0/1.0 pair for the corresponding features
    — a constant across that race's own runners — which leaves
    `predict_race_probabilities`/`fit_logistic_baseline`'s behaviour exactly
    as it was before these two extras existed (softmax is invariant to a
    constant added to every runner's score); see the module docstring.

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

    draw_bias_lookup = draw_bias_lookup or {}
    if weather and weather.get("turf_rainfall_interaction") is not None:
        rainfall_edge = weather["turf_rainfall_interaction"]
        no_weather_flag = 0.0
    else:
        rainfall_edge = 0.0
        no_weather_flag = 1.0

    out: dict[int, dict[str, float]] = {}
    for r in runners:
        rating_edge = rating[r.horse_id]["rating_vs_mean"] if r.horse_id in rating else 0.0
        draw_edge = (draw[r.horse_id]["draw_percentile"] - 0.5) if r.horse_id in draw else 0.0
        weight_edge = weight[r.horse_id]["weight_vs_mean_lbs"] if r.horse_id in weight else 0.0
        fs = form_scores.get(r.horse_id)
        form_edge = (fs - mean_form) if (fs is not None and mean_form is not None) else 0.0
        no_rating_flag = 0.0 if r.horse_id in rating else 1.0

        db = draw_bias_lookup.get(r.horse_id)
        draw_bias_edge = db["win_rate_vs_baseline"] if db is not None else 0.0
        no_draw_bias_flag = 0.0 if db is not None else 1.0

        out[r.horse_id] = {
            "rating_edge": rating_edge,
            "draw_edge": draw_edge,
            "form_edge": form_edge,
            "weight_edge": weight_edge,
            "no_rating_flag": no_rating_flag,
            "draw_bias_edge": draw_bias_edge,
            "no_draw_bias_flag": no_draw_bias_flag,
            "rainfall_edge": rainfall_edge,
            "no_weather_flag": no_weather_flag,
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
    draw_bias_lookup: Optional[dict[int, Optional[dict]]] = None,
    weather: Optional[dict] = None,
) -> dict[int, float]:
    """Model 1's prediction: softmax over the linear score of each runner's
    race-relative feature vector, keyed by horse_id. Sums to 1.0 (up to
    float rounding) by construction. `weights=None` (default) uses
    DEFAULT_WEIGHTS — i.e. an untrained model, which is provably uniform
    (see `test_predict_with_default_weights_is_uniform`). `draw_bias_lookup`/
    `weather` are passed straight through to `build_race_features` — see
    its docstring. Raises ValueError for an empty race, matching
    `model0_market_baseline.predict_race_probabilities`.
    """
    if not runners:
        raise ValueError("cannot predict an empty race")
    weights = weights if weights is not None else DEFAULT_WEIGHTS
    feats = build_race_features(runners, draw_bias_lookup=draw_bias_lookup, weather=weather)
    scores = {hid: _linear_score(f, weights) for hid, f in feats.items()}
    return _softmax(scores)


@dataclass(frozen=True)
class TrainingRace:
    """One labelled race for fitting: its runners' features and which
    horse_id actually won. NEVER construct this from anything but a real
    result once real results exist — in this repo today every caller of
    `fit_logistic_baseline` in tests/ builds these from synthetic fixtures,
    clearly labelled as such, per the ground rule against presenting
    fabricated data as real.

    `draw_bias_lookup`/`weather` are the same optional per-race extras
    `build_race_features` accepts (see its docstring) — both default to
    `None`, matching every `TrainingRace` built anywhere in this repo before
    they existed."""

    runners: Sequence[RunnerFeatureInput]
    winner_horse_id: int
    draw_bias_lookup: Optional[dict[int, Optional[dict]]] = None
    weather: Optional[dict] = None


def fit_logistic_baseline(
    races: Sequence[TrainingRace],
    learning_rate: float = 0.05,
    iterations: int = 500,
    l2: float = 0.01,
    initial_weights: Optional[dict[str, float]] = None,
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
        feats = build_race_features(
            race.runners, draw_bias_lookup=race.draw_bias_lookup, weather=race.weather
        )
        race_features.append((feats, race.winner_horse_id))

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
