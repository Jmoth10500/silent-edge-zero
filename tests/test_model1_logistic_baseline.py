"""
Real tests for src/models/model1_logistic_baseline.py — synthetic fixtures
only (this is Model 1, the first FITTED model in this repo; see the module
docstring and docs/RESEARCH_LAB.md RL-006 for why it is still not a real
prediction). Fixtures use exactly the field shapes confirmed live against
The Racing API in tests/test_racecard_theracingapi.py: official_rating as
an int, draw as an int, recent_form as an undelimited string like
'1582F3'.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

TOL = 1e-9

from src.features.runner_features import RunnerFeatureInput
from src.models.model1_logistic_baseline import (
    DEFAULT_WEIGHTS,
    FEATURE_NAMES,
    TrainingRace,
    build_race_features,
    fit_logistic_baseline,
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
# build_race_features
# ---------------------------------------------------------------------------

def test_build_race_features_centers_on_field_mean():
    # 3 runners, all fields known, realistic-schema values (real racecard
    # field shapes: official_rating/draw as int, recent_form as '1582F3'-style).
    runners = [
        _runner(1, draw=2, weight_lbs=130, official_rating=90, recent_form="1582F3"),
        _runner(2, draw=4, weight_lbs=126, official_rating=80, recent_form="2213"),
        _runner(3, draw=6, weight_lbs=122, official_rating=70, recent_form="4456"),
    ]
    feats = build_race_features(runners)

    assert set(feats.keys()) == {1, 2, 3}
    for hid in feats:
        assert set(feats[hid].keys()) == set(FEATURE_NAMES)

    # rating mean = (90+80+70)/3 = 80 -> edges 10, 0, -10
    assert feats[1]["rating_edge"] == 10.0
    assert feats[2]["rating_edge"] == 0.0
    assert feats[3]["rating_edge"] == -10.0

    # weight mean = (130+126+122)/3 = 126 -> edges 4, 0, -4
    assert feats[1]["weight_edge"] == 4.0
    assert feats[2]["weight_edge"] == 0.0
    assert feats[3]["weight_edge"] == -4.0

    # draw_percentile (lo=2, hi=6): runner1=0.0, runner2=0.5, runner3=1.0
    # draw_edge = percentile - 0.5
    assert feats[1]["draw_edge"] == -0.5
    assert feats[2]["draw_edge"] == 0.0
    assert feats[3]["draw_edge"] == 0.5

    # all three have a known official_rating -> no_rating_flag is 0.0 for everyone
    assert feats[1]["no_rating_flag"] == 0.0
    assert feats[2]["no_rating_flag"] == 0.0
    assert feats[3]["no_rating_flag"] == 0.0


def test_build_race_features_missing_fields_default_to_zero():
    runners = [
        _runner(1, draw=2, weight_lbs=130, official_rating=90, recent_form="121"),
        _runner(2),  # nothing known at all
        _runner(3, draw=4, weight_lbs=None, official_rating=None, recent_form=None),
    ]
    feats = build_race_features(runners)

    # every runner gets a full dict, even the one with nothing known
    assert set(feats.keys()) == {1, 2, 3}
    # runner 2 has nothing known at all, INCLUDING no official_rating -> every
    # feature is the neutral 0.0 EXCEPT no_rating_flag, which is 1.0 (missing
    # rating is its own signal, not silently folded into "average" — RL-006)
    expected_runner_2 = {name: 0.0 for name in FEATURE_NAMES}
    expected_runner_2["no_rating_flag"] = 1.0
    assert feats[2] == expected_runner_2

    # runner 3 has a draw but nothing else -> draw_edge computed (from the
    # 2 runners with a known draw), everything else 0.0 except no_rating_flag
    assert feats[3]["rating_edge"] == 0.0
    assert feats[3]["weight_edge"] == 0.0
    assert feats[3]["form_edge"] == 0.0
    # draws are 2 and 4 -> lo=2,hi=4 -> runner3 (draw=4) percentile=1.0 -> edge=0.5
    assert feats[3]["draw_edge"] == 0.5
    # runner 3 has no official_rating either -> flagged the same as runner 2
    assert feats[3]["no_rating_flag"] == 1.0
    # runner 1 has a rating -> not flagged
    assert feats[1]["no_rating_flag"] == 0.0


def test_build_race_features_empty_runners_returns_empty_dict():
    assert build_race_features([]) == {}


# ---------------------------------------------------------------------------
# predict_race_probabilities
# ---------------------------------------------------------------------------

def test_predict_with_default_weights_is_uniform():
    """Untrained model (DEFAULT_WEIGHTS, all zero) must be provably uniform
    — every runner's linear score is 0.0 regardless of its features, so
    softmax degenerates to 1/n exactly. This is the honesty check: Model 1
    with no fitting behind it must not silently favour anyone."""
    runners = [
        _runner(1, official_rating=95, draw=1, weight_lbs=140, recent_form="1111"),
        _runner(2, official_rating=60, draw=8, weight_lbs=110, recent_form="6654"),
        _runner(3, official_rating=75, draw=4, weight_lbs=126, recent_form="3322"),
        _runner(4),
    ]
    probs = predict_race_probabilities(runners)  # weights=None -> DEFAULT_WEIGHTS
    assert set(probs.keys()) == {1, 2, 3, 4}
    for p in probs.values():
        assert p == 0.25
    assert math.isclose(sum(probs.values()), 1.0, abs_tol=1e-12)


def test_predict_sums_to_one_with_nonzero_weights():
    runners = [
        _runner(1, official_rating=88, draw=3, weight_lbs=128, recent_form="1582F3"),
        _runner(2, official_rating=74, draw=7, weight_lbs=124, recent_form="42P16"),
        _runner(3, official_rating=91, draw=1, weight_lbs=133, recent_form="211"),
        _runner(4, official_rating=65, draw=9, weight_lbs=118, recent_form="6564"),
        _runner(5),  # a runner the API returned with nothing filled in yet
    ]
    weights = {
        "rating_edge": 0.08,
        "draw_edge": -0.3,
        "form_edge": -0.15,
        "weight_edge": 0.02,
        "no_rating_flag": -0.4,
    }
    probs = predict_race_probabilities(runners, weights=weights)

    assert set(probs.keys()) == {1, 2, 3, 4, 5}
    assert math.isclose(sum(probs.values()), 1.0, abs_tol=1e-9)
    for p in probs.values():
        assert 0.0 < p < 1.0


def test_predict_empty_race_raises():
    raised = False
    try:
        predict_race_probabilities([])
    except ValueError:
        raised = True
    assert raised, "expected ValueError for an empty race"


# ---------------------------------------------------------------------------
# fit_logistic_baseline
# ---------------------------------------------------------------------------

def test_fit_raises_on_empty_races():
    raised = False
    try:
        fit_logistic_baseline([])
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
        fit_logistic_baseline([race])
    except ValueError:
        raised = True
    assert raised, "expected ValueError when winner_horse_id isn't among the race's runners"


def test_fit_single_race_single_step_hand_verified():
    """Hand-verified single gradient-ascent step, matching the style of
    tests/test_model0_market_baseline.py and tests/test_calibration.py.

    Race: 2 runners, official_rating 80 (winner) and 70. rating mean = 75,
    so rating_edge = +5 (winner) and -5 (loser); every other feature is
    0.0 for both (no draw/weight/form given), so only rating_edge's
    weight should move.

    With weights starting at zero, both runners score 0 -> softmax gives
    p=0.5 each. Gradient for rating_edge =
        f_winner * (1 - 0.5) + f_loser * (0 - 0.5)
      = 5*0.5 + (-5)*(-0.5) = 2.5 + 2.5 = 5.0
    Divided by n_races=1, minus l2*0 (weight starts at 0) = 5.0.
    One step at learning_rate=0.05 -> weight["rating_edge"] = 0.05*5.0 = 0.25.
    Every other feature's gradient is 0 (all runners have 0.0 there — both
    runners have a known official_rating, so no_rating_flag is 0.0 for both
    too), and l2*0=0, so every other weight stays exactly 0.0.
    """
    race = TrainingRace(
        runners=[
            _runner(1, official_rating=80),
            _runner(2, official_rating=70),
        ],
        winner_horse_id=1,
    )
    weights = fit_logistic_baseline([race], learning_rate=0.05, iterations=1, l2=0.01)

    assert abs(weights["rating_edge"] - 0.25) < TOL
    assert weights["draw_edge"] == 0.0
    assert weights["form_edge"] == 0.0
    assert weights["weight_edge"] == 0.0
    assert weights["no_rating_flag"] == 0.0


def test_fit_recovers_rating_signal_sign():
    """Not a benchmark (needs real outcomes for that — see RL-006) — just a
    convergence check: on synthetic races where the highest-rated runner
    always wins, gradient ascent must recover a POSITIVE weight on
    rating_edge, and the fitted model must then rate that same runner-shape
    above uniform on a held-out race of the same shape."""
    races = []
    for i in range(20):
        runners = [
            _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
            _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
            _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
        ]
        races.append(TrainingRace(runners=runners, winner_horse_id=30))  # highest rating always wins

    weights = fit_logistic_baseline(races, learning_rate=0.1, iterations=300, l2=0.001)
    assert weights["rating_edge"] > 0.0, (
        f"expected a positive rating_edge weight after fitting on a rating-determines-winner "
        f"synthetic set, got {weights['rating_edge']}"
    )

    held_out = [
        _runner(10, official_rating=60, draw=3, weight_lbs=120, recent_form="4455"),
        _runner(20, official_rating=75, draw=5, weight_lbs=124, recent_form="3322"),
        _runner(30, official_rating=90, draw=7, weight_lbs=128, recent_form="1211"),
    ]
    probs = predict_race_probabilities(held_out, weights=weights)
    assert probs[30] > 1.0 / 3.0, "fitted model should rate the historically-always-wins runner above uniform"
    assert probs[30] == max(probs.values())


def test_fit_recovers_debutant_signal_sign():
    """Convergence check for `no_rating_flag` (added this session, see
    RL-006): two 'regular' runners with IDENTICAL rating/draw/weight/form
    (so their other four features are exactly 0.0 and cancel out — neither
    is systematically favoured by anything else) against one runner with no
    fields known at all (a debutant-shaped runner: no_rating_flag=1.0,
    every other feature 0.0). The winner alternates between the two regular
    runners across the synthetic set; the debutant never wins. Gradient
    ascent must recover a NEGATIVE weight on no_rating_flag, and the fitted
    model must then rate that debutant-shaped runner below uniform on a
    held-out race — while the two identically-featured regular runners stay
    exactly tied with each other, since nothing else here distinguishes
    them.

    Not a benchmark (needs real outcomes for that — see RL-006), just proof
    the maths recovers the injected signal, the same discipline as
    test_fit_recovers_rating_signal_sign above.
    """
    races = []
    for i in range(20):
        runners = [
            _runner(10, official_rating=75, draw=3, weight_lbs=120, recent_form="3322"),
            _runner(20, official_rating=75, draw=3, weight_lbs=120, recent_form="3322"),
            _runner(30),  # debutant: nothing known
        ]
        winner = 10 if i % 2 == 0 else 20  # alternates; the debutant never wins
        races.append(TrainingRace(runners=runners, winner_horse_id=winner))

    weights = fit_logistic_baseline(races, learning_rate=0.1, iterations=300, l2=0.001)
    assert weights["no_rating_flag"] < 0.0, (
        f"expected a negative no_rating_flag weight after fitting on a set where the "
        f"debutant-shaped runner never wins, got {weights['no_rating_flag']}"
    )
    # nothing else differentiates runners 10 and 20 in any race, so their
    # weights should never have moved off the zero-initialised default
    assert weights["rating_edge"] == 0.0
    assert weights["draw_edge"] == 0.0
    assert weights["form_edge"] == 0.0
    assert weights["weight_edge"] == 0.0

    held_out = [
        _runner(10, official_rating=75, draw=3, weight_lbs=120, recent_form="3322"),
        _runner(20, official_rating=75, draw=3, weight_lbs=120, recent_form="3322"),
        _runner(30),
    ]
    probs = predict_race_probabilities(held_out, weights=weights)
    assert probs[30] < 1.0 / 3.0, "fitted model should rate the debutant-shaped runner below uniform"
    assert math.isclose(probs[10], probs[20], rel_tol=1e-9), (
        "runners 10 and 20 are featurally identical in every race and should stay exactly tied"
    )


if __name__ == "__main__":
    tests = [
        test_build_race_features_centers_on_field_mean,
        test_build_race_features_missing_fields_default_to_zero,
        test_build_race_features_empty_runners_returns_empty_dict,
        test_predict_with_default_weights_is_uniform,
        test_predict_sums_to_one_with_nonzero_weights,
        test_predict_empty_race_raises,
        test_fit_raises_on_empty_races,
        test_fit_raises_on_winner_not_in_runners,
        test_fit_single_race_single_step_hand_verified,
        test_fit_recovers_rating_signal_sign,
        test_fit_recovers_debutant_signal_sign,
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
