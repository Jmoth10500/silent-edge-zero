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
    "chester": ("13", "chester"),
    "salisbury": ("52", "salisbury"),
    "sandown": ("54", "sandown"),
    "bath": ("5", "bath"),
    "musselburgh": ("16", "musselburgh"),
    "ayr": ("3", "ayr"),
    "newbury": ("36", "newbury"),
    "newton abbot": ("39", "newton-abbot"),
    "wolverhampton (aw)": ("513", "wolverhampton-aw"),
    "ffos las": ("1212", "ffos-las"),
    "hamilton": ("22", "hamilton"),
    "leicester": ("30", "leicester"),
    "perth": ("41", "perth"),
    "redcar": ("47", "redcar"),
    "goodwood": ("21", "goodwood"),
    "kempton (aw)": ("1079", "kempton-aw"),
}
