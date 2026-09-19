"""
Real tests for src/research/hypothesis_tracker.py — brief Section 22.
Redirects HYPOTHESES_DIR to a temp directory for every test so these
never touch the real data/hypotheses/ directory.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import src.research.hypothesis_tracker as ht


def _use_temp_dir():
    tmp = tempfile.mkdtemp()
    ht.HYPOTHESES_DIR = Path(tmp)
    return Path(tmp)


def test_create_and_load_round_trips():
    _use_temp_dir()
    slug = ht.create_hypothesis(
        name="Test Finding One",
        description="A real descriptive finding for testing.",
        rule_definition="se_rank == 2 and market_rank == 2",
        source_finding="scripts/missed_winners_report.py 2026-09-18",
        historical_evidence={"n": 45, "actual_wins": 13, "expected_wins": 8.41},
    )
    assert slug == "test-finding-one"
    record = ht.load_hypothesis(slug)
    assert record["name"] == "Test Finding One"
    assert record["status"] == "descriptive"
    assert record["prospective_results"] == []


def test_create_with_prospective_start_date_sets_awaiting_status():
    _use_temp_dir()
    from datetime import date
    slug = ht.create_hypothesis(
        "Prospective One", "desc", "rule", "source", {"n": 10},
        prospective_test_start_date=date(2026, 9, 20),
    )
    record = ht.load_hypothesis(slug)
    assert record["status"] == "awaiting_prospective_test"
    assert record["prospective_test_start_date"] == "2026-09-20"


def test_refuses_to_overwrite_existing_hypothesis():
    _use_temp_dir()
    ht.create_hypothesis("Dup", "d", "r", "s", {})
    try:
        ht.create_hypothesis("Dup", "different description", "different rule", "s", {})
        assert False, "expected FileExistsError"
    except FileExistsError:
        pass


def test_append_prospective_result_never_touches_historical_evidence():
    _use_temp_dir()
    slug = ht.create_hypothesis("Grows Over Time", "d", "r", "s", {"n": 45, "actual_wins": 13})
    ht.append_prospective_result(slug, {"n": 20, "actual_wins": 6, "expected_wins": 4.2})
    ht.append_prospective_result(slug, {"n": 15, "actual_wins": 3, "expected_wins": 3.0})
    record = ht.load_hypothesis(slug)
    assert record["historical_evidence"] == {"n": 45, "actual_wins": 13}  # untouched
    assert len(record["prospective_results"]) == 2
    assert record["prospective_results"][0]["n"] == 20
    assert "recorded_at" in record["prospective_results"][0]


def test_append_prospective_result_rejects_protected_field_smuggling():
    _use_temp_dir()
    slug = ht.create_hypothesis("Protected", "d", "r", "s", {"n": 1})
    try:
        ht.append_prospective_result(slug, {"rule_definition": "sneaky new rule"})
        assert False, "expected ValueError"
    except ValueError:
        pass
    # confirm nothing was actually written
    assert ht.load_hypothesis(slug)["rule_definition"] == "r"


def test_append_prospective_result_can_update_status():
    _use_temp_dir()
    slug = ht.create_hypothesis("Status Change", "d", "r", "s", {})
    ht.append_prospective_result(slug, {"n": 30, "actual_wins": 9}, new_status="prospective_supported")
    assert ht.load_hypothesis(slug)["status"] == "prospective_supported"


def test_list_hypotheses_returns_all():
    _use_temp_dir()
    ht.create_hypothesis("A", "d", "r", "s", {})
    ht.create_hypothesis("B", "d", "r", "s", {})
    names = {h["name"] for h in ht.list_hypotheses()}
    assert names == {"A", "B"}


def test_list_hypotheses_empty_dir_returns_empty_list():
    tmp_dir = _use_temp_dir()
    (tmp_dir).rmdir()  # remove it so the dir doesn't even exist
    assert ht.list_hypotheses() == []


if __name__ == "__main__":
    tests = [
        test_create_and_load_round_trips, test_create_with_prospective_start_date_sets_awaiting_status,
        test_refuses_to_overwrite_existing_hypothesis, test_append_prospective_result_never_touches_historical_evidence,
        test_append_prospective_result_rejects_protected_field_smuggling, test_append_prospective_result_can_update_status,
        test_list_hypotheses_returns_all, test_list_hypotheses_empty_dir_returns_empty_list,
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
