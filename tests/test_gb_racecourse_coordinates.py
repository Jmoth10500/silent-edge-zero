"""
Real tests for data/gb_racecourse_coordinates.py::normalise_course_name —
confirms the name-matching logic that makes the coordinate backfill
(scripts/backfill_gb_course_coordinates.py) work across Kaggle's DB
name variants of the same physical GB racecourse.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.gb_racecourse_coordinates import GB_RACECOURSE_COORDINATES, normalise_course_name


def test_strips_parenthetical_suffix():
    assert normalise_course_name("Kempton (AW)") == "kempton"
    assert normalise_course_name("Newmarket (July)") == "newmarket"
    assert normalise_course_name("Dundalk (AW)") == "dundalk"


def test_strips_generic_venue_words():
    assert normalise_course_name("Kempton Park") == "kempton"
    assert normalise_course_name("Sandown Park") == "sandown"
    assert normalise_course_name("Epsom Downs") == "epsom"
    assert normalise_course_name("Chelmsford City") == "chelmsford"


def test_strips_leading_great():
    assert normalise_course_name("Great Yarmouth") == "yarmouth"


def test_plain_name_unchanged():
    assert normalise_course_name("Ascot") == "ascot"
    assert normalise_course_name("York") == "york"


def test_name_variants_of_same_course_normalise_identically():
    variants = ["Kempton Park", "Kempton (AW)", "Kempton"]
    normalised = {normalise_course_name(v) for v in variants}
    assert normalised == {"kempton"}


def test_all_59_real_gb_courses_present():
    assert len(GB_RACECOURSE_COORDINATES) == 59


def test_every_coordinate_is_within_gb_bounding_box():
    # Rough real bounding box for Great Britain (mainland + islands):
    # latitude 49.8-60.9, longitude -8.7 to 1.9. Every entry should be a
    # real coordinate inside this box, not a placeholder or typo.
    for name, (lat, lon) in GB_RACECOURSE_COORDINATES.items():
        assert 49.5 <= lat <= 61.0, f"{name}: latitude {lat} outside GB bounding box"
        assert -9.0 <= lon <= 2.0, f"{name}: longitude {lon} outside GB bounding box"


if __name__ == "__main__":
    tests = [
        test_strips_parenthetical_suffix,
        test_strips_generic_venue_words,
        test_strips_leading_great,
        test_plain_name_unchanged,
        test_name_variants_of_same_course_normalise_identically,
        test_all_59_real_gb_courses_present,
        test_every_coordinate_is_within_gb_bounding_box,
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
