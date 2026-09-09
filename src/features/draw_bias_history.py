"""
Course+distance-specific historical draw bias — RL-004's real
implementation, now that real historical results exist (558K+ real
Kaggle-sourced runner results, Session 6, 2026-09-08).

RL-004 deliberately left `runner_features.py::draw_bias_features()` as a
NEUTRAL positional fact only (draw_percentile: 0.0=rail, 1.0=widest), with
no claim about which side of the field actually wins more, because that
needs real historical results grouped by course+distance — which didn't
exist yet at the time. This module is that missing piece: it does NOT
replace `draw_bias_features()` (that neutral feature is still real and
still used), it adds a SEPARATE, genuinely biased-on-purpose feature next
to it.

**Leakage discipline, same as everywhere else in this repo:** the caller
is responsible for building `build_draw_bias_table()` from ONLY
strictly-earlier results than whatever race is being predicted — e.g. only
a walk-forward split's training-fold outcomes, never the full dataset
including the future. This module has no DB access and no notion of
"today"; it just aggregates whatever `HistoricalRaceOutcome` rows it's
given. See `scripts/train_model1.py`/`scripts/train_model2.py` for the
leakage-safe real caller: the table is rebuilt fresh from each split's
training races only.

**Design choices, flagged honestly (this is a first real attempt, not a
validated method):**
- Courses+distances are grouped into `distance_band`-width buckets
  (default 220 yards = 1 furlong) so races of near-identical trip pool
  together for real sample size, without conflating e.g. a 5f sprint with
  a 12f staying race at the same course. The band width is a reasonable
  starting choice, not tuned.
- Draw position is bucketed into LOW/MID/HIGH thirds of the field (by
  percentile, same 0.0=rail/1.0=widest scale as `draw_percentile` in
  runner_features.py) rather than compared as a raw draw number, so it's
  comparable across different field sizes.
- A (course, distance_band, tercile) bucket only produces a real number
  once it has at least `min_sample_size` historical runs — below that,
  `draw_bias_edge()` returns 0.0 ("no evidence"), the same honest
  no-evidence-either-way convention every other feature in this repo
  already follows for missing data, rather than reporting a bias estimate
  built on too few races to mean anything.
"""
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class HistoricalRaceOutcome:
    """One real, strictly-past runner-result row, exactly the shape needed
    to compute a course+distance draw-bias table. The caller builds these
    from real (race, runner_snapshot, runner_result) joins — see
    scripts/train_model1.py::load_races for the equivalent real query this
    reuses course_id/distance_yards/draw from."""

    course_id: int
    distance_yards: int
    draw: int
    field_size: int
    won: bool


DEFAULT_DISTANCE_BAND_YARDS = 220  # 1 furlong
DEFAULT_MIN_SAMPLE_SIZE = 30


def distance_band(distance_yards: int, band_width: int = DEFAULT_DISTANCE_BAND_YARDS) -> int:
    """Round down to the nearest band_width so nearby trips at the same
    course pool together. Not a validated band width — a reasonable
    starting default, see module docstring."""
    return (distance_yards // band_width) * band_width


def draw_tercile(draw: int, field_size: int) -> str:
    """LOW / MID / HIGH third of the field by draw percentile (0.0=rail,
    1.0=widest — same scale as runner_features.py's draw_percentile).
    field_size <= 1 has no meaningful spread, so it's always MID."""
    if field_size <= 1:
        return "MID"
    percentile = (draw - 1) / (field_size - 1)
    if percentile < 1 / 3:
        return "LOW"
    elif percentile < 2 / 3:
        return "MID"
    return "HIGH"


DrawBiasTable = dict  # {(course_id, distance_band, tercile): win_rate}


def build_draw_bias_table(
    outcomes: Sequence[HistoricalRaceOutcome],
    min_sample_size: int = DEFAULT_MIN_SAMPLE_SIZE,
    band_width: int = DEFAULT_DISTANCE_BAND_YARDS,
) -> DrawBiasTable:
    """Aggregates real (course, distance_band, tercile) -> win_rate from
    `outcomes`. Buckets with fewer than `min_sample_size` real runs are
    left out entirely (not returned with a low-confidence estimate) — see
    module docstring. Empty `outcomes` returns an empty table, which
    `draw_bias_edge()` treats the same as "no data for this bucket": 0.0.
    """
    counts: dict[tuple, list[int]] = defaultdict(lambda: [0, 0])  # [wins, runs]
    for o in outcomes:
        key = (o.course_id, distance_band(o.distance_yards, band_width), draw_tercile(o.draw, o.field_size))
        counts[key][1] += 1
        if o.won:
            counts[key][0] += 1

    return {
        key: wins / runs
        for key, (wins, runs) in counts.items()
        if runs >= min_sample_size
    }


def draw_bias_edge(
    table: DrawBiasTable,
    course_id: Optional[int],
    distance_yards: Optional[int],
    draw: Optional[int],
    field_size: Optional[int],
    band_width: int = DEFAULT_DISTANCE_BAND_YARDS,
) -> float:
    """This runner's historical course+distance draw-tercile win rate,
    minus the naive uniform expectation (1/field_size) — positive means
    "this draw position has historically won MORE than its fair share at
    this course/distance", negative means less. Returns 0.0 ("no
    evidence") whenever any input is missing, field_size is 0, or the
    relevant bucket has no table entry (insufficient real sample size) —
    same convention as every other feature in this repo, never a guess.
    """
    if course_id is None or distance_yards is None or draw is None or not field_size:
        return 0.0
    key = (course_id, distance_band(distance_yards, band_width), draw_tercile(draw, field_size))
    tercile_rate = table.get(key)
    if tercile_rate is None:
        return 0.0
    return tercile_rate - (1.0 / field_size)
