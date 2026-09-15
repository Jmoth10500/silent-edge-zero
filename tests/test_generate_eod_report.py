"""
Real tests for scripts/generate_eod_report.py's pure settlement logic.
The DB-reading half is exercised by actually running the script (it
already reports every outcome as honestly PENDING when no real
runner_result rows exist — see docs/BUILD_LOG.md), same discipline as
predict_todays_races.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_eod_report import ew_terms_for_field_size, settle_each_way, settle_win


def test_ew_terms_real_field_size_bands():
    assert ew_terms_for_field_size(3) == ("Win only (2-4 runners)", None, 0)
    assert ew_terms_for_field_size(6) == ("1/4 odds, 2 places (5-7 runners)", 0.25, 2)
    assert ew_terms_for_field_size(9) == ("1/5 odds, 3 places (8-11 runners)", 0.2, 3)
    assert ew_terms_for_field_size(14) == ("1/4 odds, 3 places (12-15 runners)", 0.25, 3)
    assert ew_terms_for_field_size(20) == ("1/4 odds, 4 places (16+ runners)", 0.25, 4)


def test_settle_win_no_price_is_pending():
    profit, note = settle_win(1.0, None, 1)
    assert profit is None
    assert "no real price" in note


def test_settle_win_no_result_is_pending():
    profit, note = settle_win(1.0, 5.0, None)
    assert profit is None
    assert "PENDING" in note


def test_settle_win_real_win():
    profit, note = settle_win(1.0, 5.0, 1)
    assert profit == 4.0
    assert note == "WON"


def test_settle_win_real_loss():
    profit, note = settle_win(1.0, 5.0, 3)
    assert profit == -1.0
    assert note == "lost"


def test_settle_each_way_no_price_is_pending():
    profit, note = settle_each_way(2.0, None, 1, 9)
    assert profit is None


def test_settle_each_way_no_result_is_pending():
    profit, note = settle_each_way(2.0, 5.0, None, 9)
    assert profit is None
    assert "PENDING" in note


def test_settle_each_way_real_win_pays_both_legs():
    # 9 runners -> 1/5 odds, 3 places. Odds 5.0, £2 total (£1 each side).
    # Win leg: 1*(5.0-1) = 4.0. Place odds = 1+(5.0-1)*0.2 = 1.8, place leg: 1*(1.8-1) = 0.8
    profit, note = settle_each_way(2.0, 5.0, 1, 9)
    assert profit == 4.8
    assert "WON" in note


def test_settle_each_way_real_place_only():
    # Same terms, finishes 3rd (within 3 places) but doesn't win:
    # win leg: -1 (lost), place leg: 1*(1.8-1) = 0.8 -> total -0.2
    profit, note = settle_each_way(2.0, 5.0, 3, 9)
    assert profit == -0.2
    assert "PLACED" in note


def test_settle_each_way_real_neither_wins_nor_places():
    # finishes 5th, outside 3 places -> both legs lose -> -2.0 total
    profit, note = settle_each_way(2.0, 5.0, 5, 9)
    assert profit == -2.0
    assert note.startswith("lost")


def test_settle_each_way_win_only_field_voids_place_portion():
    # 3 runners -> win-only terms (frac=None) — place stake voided/returned,
    # only the win leg is live
    profit, note = settle_each_way(2.0, 5.0, 1, 3)
    assert profit == 4.0  # just the win leg: 1*(5.0-1)
    assert "void" in note


# Real, terminal non-finish states (2026-09-15, see docs/BUILD_LOG.md) —
# a withdrawn horse (NR/VOID) never had a bet stand at all, so the stake
# is refunded (profit 0), not still PENDING and not a loss. Any other
# code (PU/F/UR/BD/RR/RO/DSQ/SU/REF/CO/FELL) means the horse actually
# ran and didn't finish — a real loss.

def test_settle_win_non_runner_is_void_not_pending():
    profit, note = settle_win(1.0, 5.0, None, "NR")
    assert profit == 0.0
    assert "VOID" in note and "NR" in note


def test_settle_win_real_non_finish_is_a_loss():
    profit, note = settle_win(1.0, 5.0, None, "PU")
    assert profit == -1.0
    assert "PU" in note


def test_settle_each_way_non_runner_is_void_not_pending():
    profit, note = settle_each_way(2.0, 5.0, None, 9, "NR")
    assert profit == 0.0
    assert "VOID" in note


def test_settle_each_way_real_non_finish_is_a_full_loss():
    profit, note = settle_each_way(2.0, 5.0, None, 9, "F")
    assert profit == -2.0
    assert "F" in note


if __name__ == "__main__":
    tests = [
        test_ew_terms_real_field_size_bands,
        test_settle_win_no_price_is_pending,
        test_settle_win_no_result_is_pending,
        test_settle_win_real_win,
        test_settle_win_real_loss,
        test_settle_each_way_no_price_is_pending,
        test_settle_each_way_no_result_is_pending,
        test_settle_each_way_real_win_pays_both_legs,
        test_settle_each_way_real_place_only,
        test_settle_each_way_real_neither_wins_nor_places,
        test_settle_each_way_win_only_field_voids_place_portion,
        test_settle_win_non_runner_is_void_not_pending,
        test_settle_win_real_non_finish_is_a_loss,
        test_settle_each_way_non_runner_is_void_not_pending,
        test_settle_each_way_real_non_finish_is_a_full_loss,
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
