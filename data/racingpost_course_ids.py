"""
Real Racing Post numeric course IDs and URL slugs, keyed by our OWN RAW
course.name (lowercased), NOT the normalised name from
data.gb_racecourse_coordinates.normalise_course_name — that normaliser
collapses 'Lingfield' and 'Lingfield (AW)' to the same 'lingfield' key,
which is real for Smarkets matching (one exchange market either way) but
WRONG here: turf Lingfield (course id 31) and Lingfield's all-weather
track (course id 393) are genuinely different Racing Post courses with
different race calendars, so collapsing them would fetch the wrong
course's races entirely.

**Real, honest limitation:** only the courses actually seen in our race
data so far are mapped. An unmapped course is skipped explicitly and
reported by scripts/collect_race_results.py — never guessed. Add new
courses here as they show up (found by fetching
https://www.racingpost.com/racecards/<course>/<date>/ and reading the
numeric id + slug out of the URL, or a Racing Post course profile page).
"""

RACINGPOST_COURSE_IDS: dict[str, tuple[str, str]] = {
    "doncaster": ("15", "doncaster"),
    "epsom": ("17", "epsom"),
    "worcester": ("101", "worcester"),
    "lingfield (aw)": ("393", "lingfield-aw"),
    "lingfield": ("31", "lingfield"),
}
