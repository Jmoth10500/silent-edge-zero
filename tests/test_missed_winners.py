"""
Real tests for src/research/missed_winners.py — brief Section 8. Checks
that "missed winner" races are exactly four-way category D (reusing
market_vs_model's classification, not a re-derived definition), and that
the descriptive summary never stands without a full-population cross-check.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.missed_winners import (
    cross_check_against_full_population,
    find_missed_winner_races,
    missed_winner_probability_bands,
    summarise_missed_winner_rank_combinations,
)


def _runner(horse_id, se_prob, se_rank, at_lock_back=None, finishing_position=None,
            trainer=None, jockey=None):
    return {
        "horse": {"horse_id": horse_id, "trainer": trainer, "jockey": jockey},
        "silent_edge": {"model_probability": se_prob, "model_rank": se_rank},
        "market": {"at_lock": {"exchange_back": at_lock_back} if at_lock_back is not None else None},
        "result": {"finishing_position": finishing_position, "result_note": None, "starting_price": None},
    }


def _race(race_id, top_pick_id, runners, race_type="Flat", distance_yards=1600, going="Good", field_size=None):
    return {
        "race": {"race_id": race_id, "date": "2026-09-19", "off_time": "14:00", "course": "Test",
                 "race_type": race_type, "distance_yards": distance_yards, "going": going,
                 "field_size_declared": field_size or len(runners)},
        "top_pick_horse_id": top_pick_id,
        "runners": runners,
    }


def test_finds_only_category_d_races():
    races = [
        # Category A: top pick (1) == favourite (lowest back 2.0), wins -> NOT a missed winner
        _race(1, 1, [
            _runner(1, 0.5, 1, at_lock_back=2.0, finishing_position=1),
            _runner(2, 0.5, 2, at_lock_back=4.0, finishing_position=2),
        ]),
        # Category D: top pick (1) and favourite (1, same horse) both lose to horse 3 -> a real missed winner
        _race(2, 1, [
            _runner(1, 0.5, 1, at_lock_back=2.0, finishing_position=2, trainer="T. Trainer", jockey="J. Jockey"),
            _runner(2, 0.3, 2, at_lock_back=3.0, finishing_position=3),
            _runner(3, 0.2, 3, at_lock_back=5.0, finishing_position=1),
        ]),
    ]
    missed = find_missed_winner_races(races)
    assert len(missed) == 1
    assert missed[0]["race_id"] == 2
    assert missed[0]["winner_horse_id"] == 3
    assert missed[0]["winner_se_rank"] == 3
    assert missed[0]["winner_market_rank"] == 3
    assert missed[0]["winner_trainer"] is None  # winner's own trainer, not the beaten top pick's


def test_skips_a_real_dead_heat_rather_than_guessing_the_winner():
    races = [_race(1, 1, [
        _runner(1, 0.4, 1, at_lock_back=3.0, finishing_position=1),
        _runner(2, 0.3, 2, at_lock_back=2.0, finishing_position=1),  # dead heat for 1st
        _runner(3, 0.3, 3, at_lock_back=4.0, finishing_position=3),
    ])]
    assert find_missed_winner_races(races) == []


def test_summary_counts_combinations_and_shares():
    missed = [
        {"winner_se_rank": 2, "winner_market_rank": 3},
        {"winner_se_rank": 2, "winner_market_rank": 3},
        {"winner_se_rank": 4, "winner_market_rank": 2},
    ]
    summary = summarise_missed_winner_rank_combinations(missed)
    top = summary["se_rank=2,market_rank=3"]
    assert top["n_missed_winners_from_this_combo"] == 2
    assert top["share_of_all_missed_winners"] == round(2 / 3, 4)
    assert "cross-check" in top["note"]


def test_cross_check_attaches_full_population_cell():
    races = [
        _race(1, 1, [
            _runner(1, 0.5, 1, at_lock_back=2.0, finishing_position=2),
            _runner(2, 0.3, 2, at_lock_back=3.0, finishing_position=1),
            _runner(3, 0.2, 3, at_lock_back=5.0, finishing_position=3),
        ]),
    ]
    missed_summary = {"se_rank=2,market_rank=2": {"se_rank": 2, "market_rank": 2, "n_missed_winners_from_this_combo": 1}}
    result = cross_check_against_full_population(missed_summary, races)
    cell = result["se_rank=2,market_rank=2"]["full_population_cell"]
    assert cell is not None
    assert cell["n"] == 1  # horse 2: se_rank 2, market_rank 2, won
    assert cell["actual_wins"] == 1


# ---------------------------------------------------------------------------
# missed_winner_probability_bands — brief Section 7
# ---------------------------------------------------------------------------

def _missed_race(winner_se_prob, winner_market_prob=None):
    return {"winner_se_probability": winner_se_prob, "winner_market_probability": winner_market_prob}


def test_bands_are_evenly_spaced_and_cover_zero_to_hundred():
    result = missed_winner_probability_bands([], band_width=0.10)
    assert list(result.keys()) == [
        "0%-10%", "10%-20%", "20%-30%", "30%-40%", "40%-50%",
        "50%-60%", "60%-70%", "70%-80%", "80%-90%", "90%-100%",
    ]


def test_empty_band_shows_a_real_zero_not_omitted():
    result = missed_winner_probability_bands([_missed_race(0.05)], band_width=0.10)
    assert result["50%-60%"]["n_winners"] == 0
    assert result["50%-60%"]["avg_se_probability"] is None


def test_bands_group_winners_and_compute_real_averages():
    races = [_missed_race(0.22, 0.10), _missed_race(0.27, 0.20), _missed_race(0.05, 0.03)]
    result = missed_winner_probability_bands(races, band_width=0.10)
    band = result["20%-30%"]
    assert band["n_winners"] == 2
    assert abs(band["avg_se_probability"] - (0.22 + 0.27) / 2) < 1e-9
    assert abs(band["avg_market_probability"] - (0.10 + 0.20) / 2) < 1e-9
    assert band["share_of_all_missed_winners"] == round(2 / 3, 4)
    assert len(band["races"]) == 2


def test_bands_handle_missing_market_probability_without_crashing():
    races = [_missed_race(0.22, None)]
    result = missed_winner_probability_bands(races, band_width=0.10)
    assert result["20%-30%"]["avg_market_probability"] is None
    assert result["20%-30%"]["avg_se_probability"] == 0.22


def test_bands_report_priced_vs_unpriced_winners_separately():
    # Real 2026-09-20 bug (Jonathan's audit): n_winners alone is NOT a
    # valid subset of the ALL-RUNNERS Brier population, since a winner can
    # lack its own market price even when the race was de-vig-able
    # overall. n_winners_priced IS a true subset (same per-runner pricing
    # rule as probability_band_analysis) and must be reported separately.
    races = [_missed_race(0.05, 0.03), _missed_race(0.08, None), _missed_race(0.02, None)]
    result = missed_winner_probability_bands(races, band_width=0.10)
    band = result["0%-10%"]
    assert band["n_winners"] == 3
    assert band["n_winners_priced"] == 1
    assert band["n_winners_unpriced"] == 2


def test_five_point_bands_supported():
    result = missed_winner_probability_bands([_missed_race(0.22)], band_width=0.05)
    assert len(result) == 20
    assert result["20%-25%"]["n_winners"] == 1


if __name__ == "__main__":
    tests = [
        test_finds_only_category_d_races,
        test_skips_a_real_dead_heat_rather_than_guessing_the_winner,
        test_summary_counts_combinations_and_shares,
        test_cross_check_attaches_full_population_cell,
        test_bands_are_evenly_spaced_and_cover_zero_to_hundred, test_empty_band_shows_a_real_zero_not_omitted,
        test_bands_group_winners_and_compute_real_averages, test_bands_handle_missing_market_probability_without_crashing,
        test_bands_report_priced_vs_unpriced_winners_separately,
        test_five_point_bands_supported,
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
