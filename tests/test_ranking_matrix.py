"""
Real tests for src/research/ranking_matrix.py — the shared SE-rank vs
market-rank matrix (brief Section 9), including the ranking-tie handling
and the "expected wins = real sum of probabilities" rule Section 8/9
explicitly require (never n_runners * an arbitrary band midpoint).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.ranking_matrix import aggregate_rank_matrix, build_rank_observations, rank_by_market


def _runner(horse_id, se_prob, se_rank, at_lock_back=None, finishing_position=None, result_note=None):
    return {
        "horse": {"horse_id": horse_id},
        "silent_edge": {"model_probability": se_prob, "model_rank": se_rank},
        "market": {"at_lock": {"exchange_back": at_lock_back} if at_lock_back is not None else None},
        "result": {"finishing_position": finishing_position, "result_note": result_note},
    }


def _race(race_id, runners):
    return {"race": {"race_id": race_id}, "runners": runners}


# ---------------------------------------------------------------------------
# rank_by_market — competition ranking with real ties
# ---------------------------------------------------------------------------

def test_rank_by_market_simple_ordering():
    runners = [_runner(1, 0.3, 1, at_lock_back=5.0), _runner(2, 0.5, 2, at_lock_back=2.0),
               _runner(3, 0.2, 3, at_lock_back=8.0)]
    ranks = rank_by_market(runners)
    assert ranks == {1: 2, 2: 1, 3: 3}


def test_rank_by_market_joint_favourites_share_rank_and_next_skips():
    runners = [_runner(1, 0.3, 1, at_lock_back=2.0), _runner(2, 0.3, 2, at_lock_back=2.0),
               _runner(3, 0.4, 3, at_lock_back=4.0)]
    ranks = rank_by_market(runners)
    assert ranks[1] == 1
    assert ranks[2] == 1
    assert ranks[3] == 3  # skips rank 2 — real competition ranking, not 1/2/3


def test_rank_by_market_none_for_unpriced_runner():
    runners = [_runner(1, 0.5, 1, at_lock_back=2.0), _runner(2, 0.5, 2, at_lock_back=None)]
    ranks = rank_by_market(runners)
    assert ranks[2] is None


# ---------------------------------------------------------------------------
# build_rank_observations — exclusions
# ---------------------------------------------------------------------------

def test_build_observations_excludes_pending_and_unranked():
    race = _race(1, [
        _runner(1, 0.5, 1, at_lock_back=2.0, finishing_position=1),
        _runner(2, 0.5, 2, at_lock_back=None, finishing_position=2),  # no market rank
        _runner(3, 0.5, None, at_lock_back=3.0, finishing_position=2),  # no SE rank (shouldn't happen live, defensive)
    ])
    obs = build_rank_observations([race])
    assert len(obs) == 1
    assert obs[0]["horse_id"] == 1


def test_build_observations_carries_devigged_market_probability():
    race = _race(1, [
        _runner(1, 0.4, 1, at_lock_back=2.0, finishing_position=1),
        _runner(2, 0.6, 2, at_lock_back=3.0, finishing_position=2),
    ])
    obs = build_rank_observations([race])
    winner = next(o for o in obs if o["horse_id"] == 1)
    assert abs(winner["market_probability"] - (0.5 / (0.5 + 1 / 3))) < 1e-9


def test_build_observations_excludes_whole_race_when_only_one_runner_priced():
    # Real 2026-09-19 bug (Jonathan's audit): rank_by_market trivially
    # assigns the sole priced runner market_rank=1, but a market
    # PROBABILITY needs >=2 priced runners to de-vig at all. Must be
    # excluded entirely here, matching brier_live.py's population exactly
    # -- this is what previously caused the heat map (2,229 runners) and
    # the Brier chart (2,225 paired observations) to silently disagree.
    race = _race(1, [
        _runner(1, 0.4, 1, at_lock_back=2.0, finishing_position=1),
        _runner(2, 0.6, 2, at_lock_back=None, finishing_position=2),  # no real price
        _runner(3, 0.3, 3, at_lock_back=None, finishing_position=3),  # no real price
    ])
    assert build_rank_observations([race]) == []


# ---------------------------------------------------------------------------
# aggregate_rank_matrix — real sum-of-probabilities expected wins, never a
# fabricated n * midpoint
# ---------------------------------------------------------------------------

def test_expected_wins_is_a_real_sum_not_a_count_times_midpoint():
    observations = [
        {"race_id": 1, "horse_id": 1, "se_rank": 2, "market_rank": 2, "se_probability": 0.15, "market_probability": 0.10, "outcome": 0},
        {"race_id": 2, "horse_id": 2, "se_rank": 2, "market_rank": 2, "se_probability": 0.25, "market_probability": 0.20, "outcome": 1},
        {"race_id": 3, "horse_id": 3, "se_rank": 2, "market_rank": 2, "se_probability": 0.35, "market_probability": 0.30, "outcome": 0},
    ]
    matrix = aggregate_rank_matrix(observations, max_rank=6)
    cell = matrix["se_rank=2,market_rank=2"]
    assert cell["n"] == 3
    assert cell["actual_wins"] == 1
    # real sum: 0.15+0.25+0.35 = 0.75, NOT 3 * some fixed midpoint
    assert abs(cell["expected_wins_model"] - 0.75) < 1e-9
    assert abs(cell["diff_actual_minus_expected_model"] - (1 - 0.75)) < 1e-9
    assert abs(cell["expected_wins_market"] - 0.60) < 1e-9


def test_ranks_beyond_max_rank_are_pooled_into_a_plus_bucket():
    observations = [
        {"race_id": 1, "horse_id": 1, "se_rank": 9, "market_rank": 1, "se_probability": 0.02, "market_probability": 0.5, "outcome": 0},
        {"race_id": 2, "horse_id": 2, "se_rank": 12, "market_rank": 1, "se_probability": 0.01, "market_probability": 0.4, "outcome": 0},
    ]
    matrix = aggregate_rank_matrix(observations, max_rank=6)
    assert "se_rank=6+,market_rank=1" in matrix
    assert matrix["se_rank=6+,market_rank=1"]["n"] == 2


def test_small_sample_flagged():
    observations = [
        {"race_id": i, "horse_id": i, "se_rank": 3, "market_rank": 3, "se_probability": 0.1, "market_probability": 0.1, "outcome": 0}
        for i in range(5)
    ]
    matrix = aggregate_rank_matrix(observations)
    assert matrix["se_rank=3,market_rank=3"]["small_sample"] is True


def test_market_expectation_none_when_no_runner_in_cell_has_a_price():
    observations = [
        {"race_id": 1, "horse_id": 1, "se_rank": 4, "market_rank": 4, "se_probability": 0.1, "market_probability": None, "outcome": 0},
    ]
    matrix = aggregate_rank_matrix(observations)
    cell = matrix["se_rank=4,market_rank=4"]
    assert cell["expected_wins_market"] is None
    assert cell["diff_actual_minus_expected_market"] is None


if __name__ == "__main__":
    tests = [
        test_rank_by_market_simple_ordering, test_rank_by_market_joint_favourites_share_rank_and_next_skips,
        test_rank_by_market_none_for_unpriced_runner,
        test_build_observations_excludes_pending_and_unranked, test_build_observations_carries_devigged_market_probability,
        test_build_observations_excludes_whole_race_when_only_one_runner_priced,
        test_expected_wins_is_a_real_sum_not_a_count_times_midpoint,
        test_ranks_beyond_max_rank_are_pooled_into_a_plus_bucket,
        test_small_sample_flagged, test_market_expectation_none_when_no_runner_in_cell_has_a_price,
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
