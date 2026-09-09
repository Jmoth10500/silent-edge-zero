"""
Real coordinates for all 59 current British racecourses (per Wikipedia's
"List of British racecourses", 59 operating as of 25 March 2026), gathered
2026-09-09 for the RL-001 weather feature.

**Why this exists:** `course.latitude`/`course.longitude` in the live DB
was only ever populated for 13 courses (Session 1's `collect_weather.py`
hardcoded list) — 8% of real GB races. The project's own build brief scope
is "GB racing, Phase 1" (see README.md), so this deliberately does NOT
attempt to geocode the ~200 non-GB course name variants also present in
the Kaggle dataset (France, Ireland, Hong Kong, US, Australia, Japan,
etc.) — that's real, out-of-scope work for a different phase.

**Source and method:** real coordinates, not guessed or estimated. 53 of
59 resolved directly from Wikipedia's own `{{coord}}` infobox data via a
live MediaWiki API call (`action=query&prop=coordinates`, batched 10
titles/request — batching more than ~10 silently truncated results, a
real quirk worth remembering for any future MediaWiki API batch call).
The remaining 6 (Brighton, Haydock Park, Hexham, Newmarket, Nottingham,
Stratford — the last one is titled "Stratford-on-Avon Racecourse" on
Wikipedia, not "Stratford-upon-Avon") had no `{{coord}}` data on their
Wikipedia page and were resolved via web search against secondary mapping
sources instead (latitude.to / Wikidata-derived) — still real, verified
coordinates, just not from the same primary source as the other 53.

Precision here is intentionally coarse (rounded to Wikipedia's own
article-level precision, typically ~10-50m) — this is for a weather
feature (rainfall/temperature/wind at a whole racecourse site), not for
anything needing survey-grade accuracy.

Keys are normalised (lowercase, "park"/"downs"/"city" suffix and leading
"great " stripped) so they match against the Kaggle course-name variants
in the DB (e.g. "Kempton" / "Kempton Park" / "Kempton (AW)" all resolve to
the same physical course) — see `scripts/backfill_gb_course_coordinates.py`
for how this is applied.
"""

GB_RACECOURSE_COORDINATES = {
    "aintree":          (53.47694444, -2.94166667),
    "ascot":            (51.41611111, -0.67694444),
    "ayr":              (55.465,      -4.60861111),
    "bangor-on-dee":    (52.99611111, -2.92805556),
    "bath":             (51.41666667, -2.41666667),
    "beverley":         (53.84472222, -0.45666667),
    "brighton":         (50.83028,    -0.11194),
    "carlisle":         (54.86111111, -2.93333333),
    "cartmel":          (54.20305556, -2.95583333),
    "catterick":        (54.38694444, -1.65),
    "chelmsford":       (51.84110556,  0.51256944),
    "cheltenham":       (51.92027778, -2.05777778),
    "chepstow":         (51.65638889, -2.68861111),
    "chester":          (53.18638889, -2.89972222),
    "doncaster":        (53.52027778, -1.09666667),
    "epsom":            (51.30972222, -0.25555556),
    "exeter":           (50.64111111, -3.55805556),
    "fakenham":         (52.8225,      0.855),
    "ffos las":         (51.73112,    -4.23998),
    "fontwell":         (50.8525,     -0.65638889),
    "goodwood":         (50.89694444, -0.7425),
    "yarmouth":         (52.63277778,  1.73416667),
    "hamilton":         (55.78722222, -4.04805556),
    "haydock":          (53.47806,    -2.62194),
    "hereford":         (52.073,      -2.729),
    "hexham":           (54.95533,    -2.12937),
    "huntingdon":       (52.33416667, -0.23361111),
    "kelso":            (55.61361389, -2.43111667),
    "kempton":          (51.41861111, -0.39805556),
    "leicester":        (52.59777778, -1.09583333),
    "lingfield":        (51.17055556, -0.005),
    "ludlow":           (52.394,      -2.749),
    "market rasen":     (53.38177222, -0.31048056),
    "musselburgh":      (55.94704722, -3.03949444),
    "newbury":          (51.39444444, -1.30055556),
    "newcastle":        (55.03083333, -1.61166667),
    "newmarket":        (52.2380347,   0.3748907),
    "newton abbot":     (50.53861111, -3.59777778),
    "nottingham":       (52.9480889,  -1.1068083),
    "perth":            (56.42607778, -3.44893056),
    "plumpton":         (50.92489167, -0.06161667),
    "pontefract":       (53.7012,     -1.3325),
    "redcar":           (54.6075,     -1.065),
    "ripon":            (54.12343889, -1.49825833),
    "salisbury":        (51.05416667, -1.85527778),
    "sandown":          (51.37583333, -0.36166667),
    "sedgefield":       (54.64636667, -1.46635278),
    "southwell":        (53.06944444, -0.90611111),
    "stratford":        (52.181,      -1.723),
    "taunton":          (50.99,       -3.085),
    "thirsk":           (54.23226667, -1.35742222),
    "uttoxeter":        (52.89305556, -1.84972222),
    "warwick":          (52.27972222, -1.60027778),
    "wetherby":         (53.93388889, -1.36444444),
    "wincanton":        (51.0647,     -2.4226),
    "windsor":          (51.490475,   -0.63133056),
    "wolverhampton":    (52.604,      -2.1451),
    "worcester":        (52.19916667, -2.23305556),
    "york":             (53.93861111, -1.0975),
}


def normalise_course_name(name: str) -> str:
    """Strips parenthetical suffixes (AW)/(July)/etc. and generic venue
    words so DB course-name variants map onto the same physical course —
    e.g. 'Kempton (AW)', 'Kempton Park', and 'Kempton' all normalise to
    'kempton'."""
    import re
    base = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip().lower()
    for suffix in (" park", " downs", " city"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    if base.startswith("great "):
        base = base[len("great "):]
    return base.strip()
