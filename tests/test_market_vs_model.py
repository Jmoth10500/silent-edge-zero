"""
Real tests for src/research/market_vs_model.py — the four-way
classification (brief Section 6) and market-favourite determination
(Section 5), including the edge cases the brief explicitly calls out:
joint favourites, dead heats, and keeping the agreement metric separate
from the win/loss categories.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.market_vs_model import (
    classify_race_outcome,
    classify_races,
    determine_favourites,
    determine_sp_favourites,
    summarise_classification,
)


def _runner(horse_id, at_lock_back=None, sp=None, finishing_position=None):
    return {
        "horse": {"horse_id": horse_id},
        "market": {"at_lock": {"exchange_back": at_lock_back} if at_lock_back is not None else None},
        "result": {"starting_price": sp, "finishing_position": finishing_position},
    }


# ---------------------------------------------------------------------------
# determine_favourites / determine_sp_favourites
# ---------------------------------------------------------------------------

def test_determine_favourites_picks_lowest_price():
    runners = [_runner(1, 5.0), _runner(2, 2.0), _runner(3, 3.0)]
    assert determine_favourites(runners) == [2]


def test_determine_favourites_returns_joint_favourites():
    runners = [_runner(1, 2.0), _runner(2, 2.0), _runner(3, 5.0)]
    assert sorted(determine_favourites(runners)) == [1, 2]


def test_determine_favourites_empty_when_no_real_prices():
    runners = [_runner(1), _runner(2)]
    assert determine_favourites(runners) == []


def test_determine_favourites_ignores_runners_missing_the_price_source():
    runners = [_runner(1, at_lock_back=None), _runner(2, at_lock_back=4.0)]
    assert determine_favourites(runners) == [2]


def test_determine_sp_favourites_separate_from_lock_favourites():
    runners = [_runner(1, at_lock_back=5.0, sp=2.0), _runner(2, at_lock_back=2.0, sp=6.0)]
    assert determine_favourites(runners) == [2]      # lock-time favourite
    assert determine_sp_favourites(runners) == [1]   # SP favourite — genuinely different horse


# ---------------------------------------------------------------------------
# classify_race_outcome — the four categories + UNRESOLVED
# ---------------------------------------------------------------------------

def test_category_a_both_correct_same_horse_wins():
    assert classify_race_outcome(top_pick_horse_id=1, favourite_horse_ids=[1], winner_horse_ids=[1])["category"] == "A"


def test_category_b_silent_edge_only_correct():
    assert classify_race_outcome(top_pick_horse_id=1, favourite_horse_ids=[2], winner_horse_ids=[1])["category"] == "B"


def test_category_c_market_only_correct():
    assert classify_race_outcome(top_pick_horse_id=1, favourite_horse_ids=[2], winner_horse_ids=[2])["category"] == "C"


def test_category_d_both_wrong_same_pick_that_loses():
    # brief Section 6: "If the model and market select the same horse and
    # it loses, the race is BOTH WRONG" — not UNRESOLVED, not a fifth case.
    assert classify_race_outcome(top_pick_horse_id=1, favourite_horse_ids=[1], winner_horse_ids=[3])["category"] == "D"


def test_category_d_both_wrong_different_picks_that_lose():
    assert classify_race_outcome(top_pick_horse_id=1, favourite_horse_ids=[2], winner_horse_ids=[3])["category"] == "D"


def test_category_a_with_joint_favourites_when_one_of_them_wins():
    assert classify_race_outcome(top_pick_horse_id=1, favourite_horse_ids=[1, 4], winner_horse_ids=[1])["category"] == "A"


def test_unresolved_when_dead_heat():
    result = classify_race_outcome(top_pick_horse_id=1, favourite_horse_ids=[1], winner_horse_ids=[1, 2])
    assert result["category"] == "UNRESOLVED"
    assert "dead heat" in result["reason"]


def test_unresolved_when_no_winner_recorded():
    result = classify_race_outcome(top_pick_horse_id=1, favourite_horse_ids=[1], winner_horse_ids=[])
    assert result["category"] == "UNRESOLVED"


def test_unresolved_when_no_favourite_data():
    result = classify_race_outcome(top_pick_horse_id=1, favourite_horse_ids=[], winner_horse_ids=[1])
    assert result["category"] == "UNRESOLVED"
    assert "no usable market favourite data" in result["reason"]


def test_unresolved_when_no_top_pick():
    result = classify_race_outcome(top_pick_horse_id=None, favourite_horse_ids=[1], winner_horse_ids=[1])
    assert result["category"] == "UNRESOLVED"


# ---------------------------------------------------------------------------
# classify_races + summarise_classification — reconciliation and the
# agreement metric staying independent of the four-way win/loss categories
# ---------------------------------------------------------------------------

def _race(race_id, top_pick_id, runners):
    return {
        "race": {"race_id": race_id, "date": "2026-09-19", "course": "Test", "off_time": "14:00"},
        "top_pick_horse_id": top_pick_id,
        "runners": runners,
    }


def test_classify_races_and_summary_reconcile_exactly():
    races = [
        _race(1, 1, [_runner(1, 2.0, finishing_position=1), _runner(2, 4.0, finishing_position=2)]),  # A
        _race(2, 1, [_runner(1, 3.0, finishing_position=1), _runner(2, 2.0, finishing_position=2)]),  # B
        _race(3, 1, [_runner(1, 3.0, finishing_position=2), _runner(2, 2.0, finishing_position=1)]),  # C
        _race(4, 1, [_runner(1, 3.0, finishing_position=2), _runner(2, 2.0, finishing_position=3),
                     _runner(3, 5.0, finishing_position=1)]),  # D, different picks
        _race(5, 1, [_runner(1, 2.0, finishing_position=2), _runner(2, 5.0, finishing_position=3),
                     _runner(3, 6.0, finishing_position=1)]),  # D, same pick (1==favourite) that loses
        _race(6, 1, [_runner(1, 2.0)]),  # UNRESOLVED — not settled
    ]
    classified = classify_races(races)
    summary = summarise_classification(classified)

    assert summary["n_races_total"] == 6
    assert summary["n_eligible"] == 5
    assert summary["n_unresolved"] == 1
    assert summary["four_way"] == {"A": 1, "B": 1, "C": 1, "D": 2}
    assert summary["four_way"]["A"] + summary["four_way"]["B"] + summary["four_way"]["C"] + summary["four_way"]["D"] == summary["n_eligible"]

    # Agreement (top pick == a favourite) happens in races 1 and 5 only —
    # race 2's top pick (1) differs from its favourite (2), which is
    # exactly what makes it a category B race, not an agreement.
    assert summary["n_agree"] == 2
    assert summary["model_market_agreement_rate"] == 0.4

    assert summary["silent_edge_win_rate"] == round(2 / 5, 4)       # races 1, 2
    assert summary["market_favourite_win_rate"] == round(2 / 5, 4)  # races 1, 3


if __name__ == "__main__":
    tests = [
        test_determine_favourites_picks_lowest_price,
        test_determine_favourites_returns_joint_favourites,
        test_determine_favourites_empty_when_no_real_prices,
        test_determine_favourites_ignores_runners_missing_the_price_source,
        test_determine_sp_favourites_separate_from_lock_favourites,
        test_category_a_both_correct_same_horse_wins,
        test_category_b_silent_edge_only_correct,
        test_category_c_market_only_correct,
        test_category_d_both_wrong_same_pick_that_loses,
        test_category_d_both_wrong_different_picks_that_lose,
        test_category_a_with_joint_favourites_when_one_of_them_wins,
        test_unresolved_when_dead_heat,
        test_unresolved_when_no_winner_recorded,
        test_unresolved_when_no_favourite_data,
        test_unresolved_when_no_top_pick,
        test_classify_races_and_summary_reconcile_exactly,
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
