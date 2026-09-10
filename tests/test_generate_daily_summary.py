"""
Real tests for scripts/generate_daily_summary.py's pure aggregation
function. Uses the same race/result shapes
scripts/generate_eod_report.py's own loaders produce, reusing its real
settlement math (not re-derived here).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_daily_summary import compute_daily_summary


def _race(race_id, tp_horse_id, tp_prob, tp_price, fav_horse_id, fav_price, field_size):
    return {
        "race_id": race_id,
        "field_size": field_size,
        "top_pick": {"horse_id": tp_horse_id, "horse_name": f"H{tp_horse_id}",
                     "model_probability": tp_prob, "exchange_back": tp_price},
        "favourite": {"horse_id": fav_horse_id, "horse_name": f"H{fav_horse_id}",
                      "exchange_back": fav_price} if fav_horse_id else None,
    }


def test_empty_races_gives_all_zero():
    summary = compute_daily_summary([], {})
    assert summary["races_total"] == 0
    assert summary["races_settled"] == 0
    assert summary["win_profit"] == 0.0


def test_no_results_yet_excludes_all_races_honestly():
    races = [_race(1, 10, 0.3, 5.0, 20, 3.0, 9)]
    summary = compute_daily_summary(races, {})  # no results at all
    assert summary["races_total"] == 1
    assert summary["races_settled"] == 0
    assert summary["top_pick_wins"] == 0
    assert summary["win_profit"] == 0.0


def test_top_pick_win_counts_correctly():
    races = [_race(1, 10, 0.3, 5.0, 20, 3.0, 9)]  # 9 runners -> 1/5 odds, 3 places
    results = {(1, 10): (1, None), (1, 20): (3, None)}
    summary = compute_daily_summary(races, results)
    assert summary["races_settled"] == 1
    assert summary["top_pick_wins"] == 1
    assert summary["top_pick_placed"] == 1  # winning also counts as placed
    assert summary["favourite_wins"] == 0
    assert summary["win_stake_total"] == 1.0
    assert summary["win_profit"] == 4.0  # 1*(5.0-1)
    assert summary["ew_stake_total"] == 2.0


def test_top_pick_placed_but_not_won():
    races = [_race(1, 10, 0.3, 5.0, 20, 3.0, 9)]
    results = {(1, 10): (2, None)}  # placed, not won
    summary = compute_daily_summary(races, results)
    assert summary["top_pick_wins"] == 0
    assert summary["top_pick_placed"] == 1


def test_top_pick_outside_places_not_counted():
    races = [_race(1, 10, 0.3, 5.0, 20, 3.0, 9)]
    results = {(1, 10): (7, None)}  # outside 3 places for a 9-runner field
    summary = compute_daily_summary(races, results)
    assert summary["top_pick_wins"] == 0
    assert summary["top_pick_placed"] == 0


def test_win_only_field_never_counts_as_placed_unless_won():
    races = [_race(1, 10, 0.3, 5.0, 20, 3.0, 3)]  # 3 runners -> win-only terms
    results = {(1, 10): (2, None)}
    summary = compute_daily_summary(races, results)
    assert summary["top_pick_placed"] == 0  # no place terms exist for this field size


def test_favourite_win_counted_separately_from_top_pick():
    races = [_race(1, 10, 0.3, 5.0, 20, 3.0, 9)]
    results = {(1, 10): (4, None), (1, 20): (1, None)}  # favourite won, top pick didn't
    summary = compute_daily_summary(races, results)
    assert summary["favourite_wins"] == 1
    assert summary["top_pick_wins"] == 0


def test_no_price_race_excluded_from_pnl_but_not_from_settled_count():
    races = [_race(1, 10, 0.3, None, 20, 3.0, 9)]  # top pick has no real price
    results = {(1, 10): (1, None)}
    summary = compute_daily_summary(races, results)
    assert summary["races_settled"] == 1  # a real result exists
    assert summary["top_pick_wins"] == 1
    assert summary["win_stake_total"] == 0.0  # but nothing staked — no real price to settle against
    assert summary["win_profit"] == 0.0


def test_multiple_races_accumulate():
    races = [
        _race(1, 10, 0.3, 5.0, 20, 3.0, 9),
        _race(2, 11, 0.4, 2.0, 21, 2.0, 4),  # 4 runners -> win-only
    ]
    results = {(1, 10): (1, None), (2, 11): (1, None)}
    summary = compute_daily_summary(races, results)
    assert summary["races_settled"] == 2
    assert summary["top_pick_wins"] == 2
    assert summary["win_profit"] == round(4.0 + 1.0, 2)  # (5-1) + (2-1)


if __name__ == "__main__":
    tests = [
        test_empty_races_gives_all_zero,
        test_no_results_yet_excludes_all_races_honestly,
        test_top_pick_win_counts_correctly,
        test_top_pick_placed_but_not_won,
        test_top_pick_outside_places_not_counted,
        test_win_only_field_never_counts_as_placed_unless_won,
        test_favourite_win_counted_separately_from_top_pick,
        test_no_price_race_excluded_from_pnl_but_not_from_settled_count,
        test_multiple_races_accumulate,
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
