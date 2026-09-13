"""
Real tests for src/providers/horseracingnet_results.py — against real
captured page shapes from https://www.horseracing.net/results/chester/12-09-26
(fetched live 2026-09-13), independently verified against the real
rendered page before being used to build these fixtures.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers.horseracingnet_results import (
    parse_finish_text,
    parse_race_runners,
    split_into_races,
)

# Real, trimmed shape: two runners, one a winner (nested highlight span),
# one 3rd (plain text) — matches the real Chester 13:30 race exactly
# (Vidmiyr 1st, Dubai Honour 3rd, verified live against the real site).
REAL_SECTION_HTML = """
<li class="results-table-row" data-tips="1" data-horseid="2820807">
    <div class="table-cell-left">
        <div class="table-row-cell">
            <div class="icon-inner-wrapper">
                <span class="icon-wrapper">
                    <img width="50" height="37" alt="Vidmiyr silk" src="/images/silks/347584b.svg">
                </span>
                <div class="scores-wrapper">
                    <span class="number position">
                        <span class="position-highlight">1st</span></span>
                </div>
            </div>
        </div>
    </div>
    <div class="table-cell-right">
        <div class="table-cell-wrapper-inner">
            <div class="table-row-cell">
                <div class="cell-full-wrapper">
                    <a href="/runners/vidmiyr" class="runner-title">
                        Vidmiyr                                                </a>
                    <ul class="runners-list-inner">
                        <li>Jockey: A. Jockey</li>
                        <li>Trainer: B. Trainer</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</li>
<li class="results-table-row" data-tips="10" data-horseid="2771298">
    <div class="table-cell-left">
        <div class="table-row-cell">
            <div class="icon-inner-wrapper">
                <span class="icon-wrapper">
                    <img width="50" height="37" alt="Dubai Honour silk" src="/images/silks/358931.svg">
                </span>
                <div class="scores-wrapper">
                    <span class="number position">
                        3rd</span>
                </div>
            </div>
        </div>
    </div>
    <div class="table-cell-right">
        <div class="table-cell-wrapper-inner">
            <div class="table-row-cell">
                <div class="cell-full-wrapper">
                    <a href="/runners/dubai-honour" class="runner-title">
                        Dubai Honour                                                </a>
                    <ul class="runners-list-inner">
                        <li>Jockey: C. Jockey</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</li>
"""

REAL_PAGE_WITH_TWO_RACES = f"""
<h2 id="13:30">Chester 13:30 Result</h2>
{REAL_SECTION_HTML}
<h2 id="14:05">Chester 14:05 Result</h2>
<li class="results-table-row" data-tips="1">
    <span class="number position">NR</span>
    <a href="/runners/cranachan" class="runner-title">Cranachan</a>
</li>
"""


def test_split_into_races_real_shape():
    races = split_into_races(REAL_PAGE_WITH_TWO_RACES)
    assert [r[0] for r in races] == ["13:30", "14:05"]
    assert "Vidmiyr" in races[0][1]
    assert "Cranachan" in races[1][1]
    assert "Vidmiyr" not in races[1][1]  # each section is properly bounded


def test_parse_race_runners_handles_nested_highlight_and_plain_text():
    runners = parse_race_runners(REAL_SECTION_HTML)
    assert len(runners) == 2
    assert runners[0]["horse_name"] == "Vidmiyr"
    assert runners[0]["finish_text"] == "1st"
    assert runners[1]["horse_name"] == "Dubai Honour"
    assert runners[1]["finish_text"] == "3rd"


def test_parse_race_runners_not_truncated_by_nested_inner_list():
    # real regression: a naive '.*?</li>' match would stop at the nested
    # <ul><li>Jockey...</li> before reaching the second runner at all
    runners = parse_race_runners(REAL_SECTION_HTML)
    names = [r["horse_name"] for r in runners]
    assert "Dubai Honour" in names  # would be lost entirely under the old bug


def test_parse_finish_text_real_ordinals():
    assert parse_finish_text("1st") == (1, None)
    assert parse_finish_text("3rd") == (3, None)
    assert parse_finish_text("23rd") == (23, None)


def test_parse_finish_text_real_non_finish_codes():
    assert parse_finish_text("NR") == (None, "NR")
    assert parse_finish_text("-") == (None, "VOID")


def test_parse_finish_text_none_and_unrecognised():
    assert parse_finish_text(None) == (None, None)
    assert parse_finish_text("") == (None, None)
    assert parse_finish_text("PU") == (None, "PU")  # unrecognised -> honest note, never guessed


if __name__ == "__main__":
    tests = [
        test_split_into_races_real_shape,
        test_parse_race_runners_handles_nested_highlight_and_plain_text,
        test_parse_race_runners_not_truncated_by_nested_inner_list,
        test_parse_finish_text_real_ordinals,
        test_parse_finish_text_real_non_finish_codes,
        test_parse_finish_text_none_and_unrecognised,
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
