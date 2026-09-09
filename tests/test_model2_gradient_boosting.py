"""
Real tests for src/models/model2_gradient_boosting.py — synthetic fixtures
only, same discipline as tests/test_model1_logistic_baseline.py. This suite
proves the plumbing (fit/predict/renormalise/error-handling) is correct; it
makes no claim about real predictive power — see the module docstring and
docs/RESEARCH_LAB.md RL-008 for that split.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.runner_features import RunnerFeatureInput
from src.models.model2_gradient_boosting import (
    TrainingRace,
    _renormalise_race,
    fit_gradient_boosting,
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


# ---------------------------------------------------------------------------
# _renormalise_race
# ---------------------------------------------------------------------------

def test_renormalise_divides_by_race_total():
    raw = {1: 0.6, 2: 0.3, 3: 0.3}
    out = _renormalise_race(raw)
    assert math.isclose(sum(out.values()), 1.0, abs_tol=1e-12)
    assert math.isclose(out[1], 0.6 / 1.2)
    assert math.isclose(out[2], 0.25)
    assert math.isclose(out[3], 0.25)


def test_renormalise_falls_back_to_uniform_when_all_zero():
    raw = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    out = _renormalise_race(raw)
    for p in out.values():
        assert p == 0.25
    assert math.isclose(sum(out.values()), 1.0, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# fit_gradient_boosting
# ---------------------------------------------------------------------------

def test_fit_raises_on_empty_races():
    raised = False
    try:
        fit_gradient_boosting([])
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
        fit_gradient_boosting([race])
    except ValueError:
        raised = True
    assert raised, "expected ValueError when winner_horse_id isn't among the race's runners"


def test_fit_raises_when_every_race_has_a_single_runner():
    # Every race contributes exactly one row (its lone runner, who is by
    # definition the winner) -> the training target has only one class, and
    # HistGradientBoostingClassifier can't fit that. Must raise honestly.
    races = [
        TrainingRace(runners=[_runner(1, official_rating=80)], winner_horse_id=1)
        for _ in range(5)
    ]
    raised = False
    try:
        fit_gradient_boosting(races)
    except ValueError:
        raised = True
    assert raised, "expected ValueError when the training target has only one class"


# ---------------------------------------------------------------------------
# predict_race_probabilities (end-to-end fit -> predict)
# ---------------------------------------------------------------------------

def test_predict_sums_to_one_and_stays_in_range():
    races = []
    for i in range(30):
        runners = [
            _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
            _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
            _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
        ]
        # alternate the winner so the training target has real variety,
        # rather than "the same runner always wins" (that's the next test)
        winner = 30 if i % 3 != 0 else 10
        races.append(TrainingRace(runners=runners, winner_horse_id=winner))

    model = fit_gradient_boosting(races, max_iter=30)

    held_out = [
        _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
        _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
        _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
    ]
    probs = predict_race_probabilities(held_out, model)
    assert set(probs.keys()) == {10, 20, 30}
    assert math.isclose(sum(probs.values()), 1.0, abs_tol=1e-9)
    for p in probs.values():
        assert 0.0 <= p <= 1.0


def test_fit_recovers_rating_signal():
    """Same convergence-check style as
    test_model1_logistic_baseline.test_fit_recovers_rating_signal_sign —
    not a benchmark (needs real outcomes for that, see RL-008), just proof
    the plumbing can recover an injected pattern: on synthetic races where
    the highest-rated runner always wins, the fitted model must rate that
    same runner-shape above uniform on a held-out race of the same shape."""
    races = []
    for i in range(40):
        runners = [
            _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
            _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
            _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
        ]
        races.append(TrainingRace(runners=runners, winner_horse_id=30))  # highest rating always wins

    model = fit_gradient_boosting(races, max_iter=50)

    held_out = [
        _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
        _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
        _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
    ]
    probs = predict_race_probabilities(held_out, model)
    assert probs[30] > 1.0 / 3.0, (
        f"expected the fitted model to rate the historically-always-wins runner above "
        f"uniform, got {probs[30]}"
    )
    assert probs[30] == max(probs.values())


def test_fit_and_predict_thread_draw_bias_table_and_race_context():
    """Not a benchmark — just confirms the draw_bias_table/course_id/
    distance_yards plumbing added for RL-008's real feature actually
    reaches build_race_features on both the fit and predict paths (i.e.
    TrainingRace's course_id/distance_yards fields are used, not ignored).
    A strong, sample-size-clearing table entry should be enough to move
    the fitted model's prediction even when every other feature is tied."""
    table = {(1, 1320, "LOW"): 0.9, (1, 1320, "HIGH"): 0.01}
    races = []
    for i in range(30):
        runners = [
            _runner(10, official_rating=75, draw=1, weight_lbs=120, recent_form="3322"),
            _runner(20, official_rating=75, draw=8, weight_lbs=120, recent_form="3322"),
        ]
        # winner determined ONLY by the (course, distance, draw-tercile)
        # signal in `table`, alternating slightly so both classes appear
        winner = 10 if i % 5 != 0 else 20
        races.append(TrainingRace(
            runners=runners, winner_horse_id=winner, course_id=1, distance_yards=1400,
        ))

    model = fit_gradient_boosting(races, max_iter=50, draw_bias_table=table)

    held_out = [
        _runner(10, official_rating=75, draw=1, weight_lbs=120, recent_form="3322"),
        _runner(20, official_rating=75, draw=8, weight_lbs=120, recent_form="3322"),
    ]
    probs_with_table = predict_race_probabilities(
        held_out, model, draw_bias_table=table, course_id=1, distance_yards=1400,
    )

    assert probs_with_table[10] > probs_with_table[20], (
        "the LOW-draw runner (table win rate 0.9) should be rated above the "
        "HIGH-draw runner (table win rate 0.01) when the table/context is supplied "
        "on both the fit and predict paths"
    )


def test_predict_empty_race_raises():
    races = [
        TrainingRace(
            runners=[_runner(1, official_rating=80), _runner(2, official_rating=70)],
            winner_horse_id=1,
        )
    ]
    model = fit_gradient_boosting(races, max_iter=10)
    raised = False
    try:
        predict_race_probabilities([], model)
    except ValueError:
        raised = True
    assert raised, "expected ValueError for an empty race"


if __name__ == "__main__":
    tests = [
        test_renormalise_divides_by_race_total,
        test_renormalise_falls_back_to_uniform_when_all_zero,
        test_fit_raises_on_empty_races,
        test_fit_raises_on_winner_not_in_runners,
        test_fit_raises_when_every_race_has_a_single_runner,
        test_predict_sums_to_one_and_stays_in_range,
        test_fit_recovers_rating_signal,
        test_fit_and_predict_thread_draw_bias_table_and_race_context,
        test_predict_empty_race_raises,
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
