"""
Real tests for src/models/model2_gradient_boosting.py — synthetic fixtures
only, same discipline as tests/test_model1_logistic_baseline.py (this is
Model 2, the first NON-linear model in this repo; see the module docstring
and docs/RESEARCH_LAB.md RL-008 for why it is still not a real prediction).
Fixtures use exactly the field shapes confirmed live against The Racing API
in tests/test_racecard_theracingapi.py: official_rating as an int, draw as
an int, recent_form as an undelimited string like '1582F3'.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.runner_features import RunnerFeatureInput
from src.models.model1_logistic_baseline import TrainingRace
from src.models.model2_gradient_boosting import (
    DEFAULT_GBM_KWARGS,
    _renormalize,
    fit_gradient_boosting_baseline,
    predict_race_probabilities,
)


def _runner(horse_id, age=None, draw=None, weight_lbs=None, official_rating=None, recent_form=None):
    return RunnerFeatureInput(
        horse_id=horse_id,
        age=age,
        draw=draw,
        weight_lbs=weight_lbs,
        official_rating=official_rating,
        recent_form=recent_form,
    )


# A small, fast set of GBM kwargs so the test suite stays quick — the real
# hyperparameters used for an actual Mac-side training run
# (scripts/train_model2.py) can differ; these are only about proving the
# pipeline is correct, not about tuning for accuracy.
_FAST_KWARGS = dict(max_iter=30, max_depth=2, learning_rate=0.3, random_state=0)


# ---------------------------------------------------------------------------
# _renormalize
# ---------------------------------------------------------------------------

def test_renormalize_sums_to_one():
    out = _renormalize([0.2, 0.5, 0.1])
    assert math.isclose(sum(out), 1.0, rel_tol=1e-12)
    # order and relative proportions preserved
    assert out[1] > out[0] > out[2]


def test_renormalize_all_zero_falls_back_to_uniform():
    out = _renormalize([0.0, 0.0, 0.0, 0.0])
    assert out == [0.25, 0.25, 0.25, 0.25]


def test_renormalize_empty_returns_empty():
    assert _renormalize([]) == []


def test_renormalize_negative_total_falls_back_to_uniform():
    # sklearn predict_proba can never actually go negative, but _renormalize
    # is a general-purpose pure function — a non-positive total should never
    # be divided into, regardless of why it happened.
    out = _renormalize([-0.1, -0.2])
    assert out == [0.5, 0.5]


# ---------------------------------------------------------------------------
# fit_gradient_boosting_baseline
# ---------------------------------------------------------------------------

def test_fit_raises_on_empty_races():
    raised = False
    try:
        fit_gradient_boosting_baseline([])
    except ValueError:
        raised = True
    assert raised, "expected ValueError for an empty race list"


def test_fit_raises_on_winner_not_in_runners():
    race = TrainingRace(
        runners=[_runner(1, official_rating=80), _runner(2, official_rating=70)],
        winner_horse_id=999,
    )
    raised = False
    try:
        fit_gradient_boosting_baseline([race])
    except ValueError:
        raised = True
    assert raised, "expected ValueError when winner_horse_id isn't among the race's runners"


def test_fit_returns_model_wrapping_a_fitted_classifier():
    races = [
        TrainingRace(
            runners=[_runner(1, official_rating=80), _runner(2, official_rating=70)],
            winner_horse_id=1,
        ),
        TrainingRace(
            runners=[_runner(3, official_rating=65), _runner(4, official_rating=85)],
            winner_horse_id=4,
        ),
    ]
    model = fit_gradient_boosting_baseline(races, **_FAST_KWARGS)
    # a fitted sklearn classifier exposes classes_ only after fit() succeeds
    assert list(model.classifier.classes_) == [0, 1]


def test_fit_default_kwargs_are_deterministic():
    assert DEFAULT_GBM_KWARGS["random_state"] == 0, (
        "Model 2's default random_state must be fixed for reproducibility — "
        "this is unrelated to ground rule 5 (no random train/test SPLITS), "
        "which src/validation/walk_forward.py already handles chronologically"
    )


# ---------------------------------------------------------------------------
# predict_race_probabilities
# ---------------------------------------------------------------------------

def test_predict_empty_race_raises():
    raised = False
    try:
        predict_race_probabilities([], model=None)
    except ValueError:
        raised = True
    assert raised, "expected ValueError for an empty race"


def test_predict_without_model_raises():
    """Unlike Model 0/1, Model 2 has no meaningful untrained prediction —
    model=None must raise, not silently fall back to uniform."""
    runners = [_runner(1, official_rating=80), _runner(2, official_rating=70)]
    raised = False
    try:
        predict_race_probabilities(runners)
    except ValueError:
        raised = True
    assert raised, "expected ValueError when no model is passed"


def test_predict_sums_to_one_and_covers_every_runner():
    races = []
    for i in range(15):
        runners = [
            _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
            _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
            _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
        ]
        # alternate the winner so both classes appear with real variety
        winner = 30 if i % 3 == 0 else (20 if i % 3 == 1 else 10)
        races.append(TrainingRace(runners=runners, winner_horse_id=winner))

    model = fit_gradient_boosting_baseline(races, **_FAST_KWARGS)

    held_out = [
        _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
        _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
        _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
        _runner(40),  # a runner the API returned with nothing filled in yet
    ]
    probs = predict_race_probabilities(held_out, model=model)

    assert set(probs.keys()) == {10, 20, 30, 40}
    assert math.isclose(sum(probs.values()), 1.0, rel_tol=1e-9)
    for p in probs.values():
        assert 0.0 <= p <= 1.0


def test_fit_and_predict_accept_draw_bias_lookup_and_weather_via_training_race():
    """RL-004/RL-001 wiring, Model 2 side: TrainingRace.draw_bias_lookup and
    .weather (added to src/models/model1_logistic_baseline.py, shared by
    this module via build_race_features) must round-trip through
    fit_gradient_boosting_baseline and predict_race_probabilities without
    error. Unlike Model 1's per-race softmax (see
    test_model1_logistic_baseline.py::test_race_constant_weather_feature_never_gets_gradient),
    Model 2 fits each runner as an INDEPENDENT binary classification, so a
    race-level weather feature is not mathematically barred from carrying
    information here — this test only proves the plumbing works end to end,
    not that Model 2 actually learns anything from it (that needs real
    data, same as every other claim in this module)."""
    favoured = {"win_rate_vs_baseline": 0.3}
    unfavoured = {"win_rate_vs_baseline": -0.3}
    wet = {"turf_rainfall_interaction": 15.0}
    races = []
    for i in range(15):
        runners = [
            _runner(10, official_rating=60, draw=3),
            _runner(20, official_rating=75, draw=5),
            _runner(30, official_rating=90, draw=7),
        ]
        winner = 30 if i % 3 == 0 else (20 if i % 3 == 1 else 10)
        races.append(TrainingRace(
            runners=runners,
            winner_horse_id=winner,
            draw_bias_lookup={10: unfavoured, 20: favoured, 30: favoured},
            weather=wet,
        ))

    model = fit_gradient_boosting_baseline(races, **_FAST_KWARGS)

    held_out = [
        _runner(10, official_rating=60, draw=3),
        _runner(20, official_rating=75, draw=5),
        _runner(30, official_rating=90, draw=7),
    ]
    probs = predict_race_probabilities(
        held_out, model=model, draw_bias_lookup={10: unfavoured, 20: favoured, 30: favoured}, weather=wet
    )
    assert set(probs.keys()) == {10, 20, 30}
    assert math.isclose(sum(probs.values()), 1.0, rel_tol=1e-9)


def test_fit_recovers_rating_signal_on_held_out_race():
    """Not a benchmark (needs real outcomes for that — see RL-006/RL-008,
    same discipline as Model 1's own convergence tests) — just a pipeline
    correctness check: on synthetic races where the highest-rated runner
    ALWAYS wins, the fitted boosted-tree classifier must rate that same
    runner-shape above the other two on a held-out race of the identical
    shape."""
    races = []
    for i in range(25):
        runners = [
            _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
            _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
            _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
        ]
        races.append(TrainingRace(runners=runners, winner_horse_id=30))  # highest rating always wins

    model = fit_gradient_boosting_baseline(races, **_FAST_KWARGS)

    held_out = [
        _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
        _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
        _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
    ]
    probs = predict_race_probabilities(held_out, model=model)
    assert probs[30] == max(probs.values()), (
        "fitted Model 2 should rate the historically-always-wins runner-shape "
        "highest on a held-out race of the identical shape"
    )
    assert probs[30] > 1.0 / 3.0


if __name__ == "__main__":
    tests = [
        test_renormalize_sums_to_one,
        test_renormalize_all_zero_falls_back_to_uniform,
        test_renormalize_empty_returns_empty,
        test_renormalize_negative_total_falls_back_to_uniform,
        test_fit_raises_on_empty_races,
        test_fit_raises_on_winner_not_in_runners,
        test_fit_returns_model_wrapping_a_fitted_classifier,
        test_fit_default_kwargs_are_deterministic,
        test_predict_empty_race_raises,
        test_predict_without_model_raises,
        test_predict_sums_to_one_and_covers_every_runner,
        test_fit_and_predict_accept_draw_bias_lookup_and_weather_via_training_race,
        test_fit_recovers_rating_signal_on_held_out_race,
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
