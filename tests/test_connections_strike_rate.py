"""
Real tests for src/features/connections_strike_rate.py — synthetic
fixtures only. See the module docstring (RL-010) for the real trainer/
jockey win-rate spread found in the live data that motivated this.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.connections_strike_rate import (
    HistoricalConnectionOutcome,
    build_win_rate_table,
    connections_edges,
)


def _outcome(entity_id, won):
    return HistoricalConnectionOutcome(entity_id=entity_id, won=won)


# ---------------------------------------------------------------------------
# build_win_rate_table
# ---------------------------------------------------------------------------

def test_build_table_excludes_below_min_runs():
    outcomes = [_outcome(1, won=(i == 0)) for i in range(10)]  # only 10 real runs
    table = build_win_rate_table(outcomes, min_runs=20)
    assert 1 not in table


def test_build_table_includes_at_min_runs_with_real_rate():
    outcomes = [_outcome(1, won=(i < 5)) for i in range(20)]  # 5 wins of 20 real runs
    table = build_win_rate_table(outcomes, min_runs=20)
    assert math.isclose(table[1], 0.25)


def test_build_table_separates_different_entities():
    outcomes = (
        [_outcome(1, won=True) for _ in range(20)]   # 100% over 20 runs
        + [_outcome(2, won=False) for _ in range(20)]  # 0% over 20 runs
    )
    table = build_win_rate_table(outcomes, min_runs=20)
    assert math.isclose(table[1], 1.0)
    assert math.isclose(table[2], 0.0)


def test_build_table_empty_outcomes_returns_empty_table():
    assert build_win_rate_table([]) == {}


# ---------------------------------------------------------------------------
# connections_edges
# ---------------------------------------------------------------------------

def test_connections_edges_computes_real_field_relative_edges():
    trainer_table = {100: 0.30, 200: 0.10}  # trainer 100 real rate 30%, trainer 200 real rate 10%
    jockey_table = {}  # no real jockey data at all
    # (horse_id, trainer_id, jockey_id)
    runners = [(1, 100, 900), (2, 200, 901)]
    edges = connections_edges(runners, trainer_table, jockey_table)

    # trainer mean = (0.30 + 0.10) / 2 = 0.20
    assert math.isclose(edges[1]["trainer_edge"], 0.10)   # 0.30 - 0.20
    assert math.isclose(edges[2]["trainer_edge"], -0.10)  # 0.10 - 0.20
    # no jockey table entries at all -> 0.0 for everyone, "no evidence"
    assert edges[1]["jockey_edge"] == 0.0
    assert edges[2]["jockey_edge"] == 0.0


def test_connections_edges_missing_entity_gets_zero_not_averaged_in():
    trainer_table = {100: 0.30}  # only trainer 100 has a real table entry
    runners = [(1, 100, None), (2, None, None)]  # horse 2's trainer unknown entirely
    edges = connections_edges(runners, trainer_table, {})
    # trainer_mean computed from ONLY the known runner (100) -> mean = 0.30
    # -> horse 1's edge = 0.30 - 0.30 = 0.0 (not because it's average, because it IS the only data point)
    assert math.isclose(edges[1]["trainer_edge"], 0.0)
    # horse 2 has no trainer_id at all -> "no evidence", also 0.0, for a different reason
    assert edges[2]["trainer_edge"] == 0.0


def test_connections_edges_every_runner_gets_both_keys_always():
    edges = connections_edges([(1, None, None), (2, None, None)], {}, {})
    assert set(edges[1].keys()) == {"trainer_edge", "jockey_edge"}
    assert edges[1]["trainer_edge"] == 0.0
    assert edges[1]["jockey_edge"] == 0.0


if __name__ == "__main__":
    tests = [
        test_build_table_excludes_below_min_runs,
        test_build_table_includes_at_min_runs_with_real_rate,
        test_build_table_separates_different_entities,
        test_build_table_empty_outcomes_returns_empty_table,
        test_connections_edges_computes_real_field_relative_edges,
        test_connections_edges_missing_entity_gets_zero_not_averaged_in,
        test_connections_edges_every_runner_gets_both_keys_always,
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
