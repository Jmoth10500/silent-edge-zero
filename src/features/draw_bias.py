"""
Course/distance-specific historical draw bias — the real hypothesis flagged
in docs/RESEARCH_LAB.md RL-004, as opposed to
runner_features.py::draw_bias_features()'s deliberately neutral placeholder
(a runner's draw_percentile within THIS race's own field, no claim about
which draws actually win more anywhere). RL-004 has said since Session 2
that testing the real hypothesis "requires historical results grouped by
course+distance, which doesn't exist yet" in this repo — the 558K-row real
Kaggle-loaded dataset (Sessions 6/8/9) now provides exactly that, but it
lives only in Postgres on Jonathan's Mac, unreachable from this cloud
routine. This module is the pure computation the real data can be run
through the moment that happens — it is NOT itself a run against real data,
and nothing here is evidence about a real draw bias existing anywhere.

Leakage safety is the CALLER's responsibility, same discipline as
scripts/derive_recent_form.py: `historical_records` passed in must already
be filtered to races strictly earlier (by race_date/off_time) than the race
being predicted. This module does no date filtering and no DB access at
all — it is pure aggregation, exactly like runner_features.py.

Tested only against synthetic fixtures (tests/test_draw_bias.py) with
hand-verified win-rate arithmetic. Wiring this against the real Kaggle
history to actually test RL-004's hypothesis is the natural next Mac-only
step, not done yet.
"""
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class HistoricalDrawRecord:
    """One past runner's (course, distance, draw, field_size, finish) —
    mirrors race.course_id/distance_yards/surface + runner_snapshot.draw +
    runner_result.finishing_position joined together (see db/schema.sql).
    Caller is responsible for only including records strictly earlier than
    the race being predicted."""

    course_id: int
    distance_yards: int
    draw: int
    field_size: int
    finishing_position: Optional[int]  # None = non-runner/unknown, excluded
    surface: Optional[str] = None


def draw_percentile_bucket(draw: int, field_size: int, num_buckets: int = 3) -> Optional[int]:
    """0-based bucket index (0 = lowest/rail-side draws ... num_buckets-1 =
    widest), splitting draws 1..field_size into num_buckets equal-ish
    groups. Integer arithmetic throughout (no float rounding at bucket
    boundaries). None if field_size < num_buckets (too few runners to
    bucket meaningfully) or draw is outside the valid 1..field_size range —
    never guessed. Note: integer division means bucket sizes can be
    slightly uneven when field_size isn't a multiple of num_buckets (e.g.
    field_size=10, num_buckets=3 gives buckets of 4/3/3 draws) — accepted
    as an honest consequence of avoiding float rounding at the boundaries,
    not hidden."""
    if field_size < num_buckets or draw < 1 or draw > field_size:
        return None
    bucket = ((draw - 1) * num_buckets) // field_size
    return min(bucket, num_buckets - 1)


def compute_course_distance_draw_bias(
    historical_records: Sequence[HistoricalDrawRecord],
    course_id: int,
    distance_yards: int,
    draw: int,
    field_size: int,
    surface: Optional[str] = None,
    num_buckets: int = 3,
    min_sample_size: int = 30,
) -> Optional[dict]:
    """
    The real course/distance-specific draw bias RL-004 actually asks about
    (as opposed to runner_features.draw_bias_features()'s neutral,
    this-race-only percentile).

    Groups `historical_records` matching (course_id, distance_yards,
    surface) into `num_buckets` draw buckets, computes each bucket's win
    rate, and returns the queried draw's own bucket win rate against the
    group's overall baseline win rate — win_rate_vs_baseline is the actual
    "bias" signal, not just a raw rate that could just reflect the field
    generally being weak or strong that day.

    `surface` is optional: pass it to also split by surface (e.g. AW vs
    turf at the same course+distance) when the caller has it, or omit it to
    pool all surfaces. Either way this ties the SAME choice to both the
    historical filter and the queried draw — never mixes the two.

    Returns None (never a guessed/invented number) if:
      - this draw/field_size can't be bucketed (see draw_percentile_bucket)
      - fewer than `min_sample_size` historical runners fall into a
        bucketable group at this (course_id, distance_yards, surface) —
        too little data to say anything, real or placeholder
      - this draw's own bucket has zero historical runners within that
        group, even if the group as a whole met min_sample_size
    """
    this_bucket = draw_percentile_bucket(draw, field_size, num_buckets)
    if this_bucket is None:
        return None

    bucket_wins = [0] * num_buckets
    bucket_counts = [0] * num_buckets
    for r in historical_records:
        if (
            r.course_id != course_id
            or r.distance_yards != distance_yards
            or r.surface != surface
            or r.finishing_position is None
        ):
            continue
        b = draw_percentile_bucket(r.draw, r.field_size, num_buckets)
        if b is None:
            continue
        bucket_counts[b] += 1
        if r.finishing_position == 1:
            bucket_wins[b] += 1

    total_runners = sum(bucket_counts)
    if total_runners < min_sample_size or bucket_counts[this_bucket] == 0:
        return None

    total_wins = sum(bucket_wins)
    baseline_win_rate = total_wins / total_runners
    bucket_win_rate = bucket_wins[this_bucket] / bucket_counts[this_bucket]

    return {
        "draw_bucket": this_bucket,
        "num_buckets": num_buckets,
        "bucket_win_rate": bucket_win_rate,
        "baseline_win_rate": baseline_win_rate,
        "win_rate_vs_baseline": bucket_win_rate - baseline_win_rate,
        "bucket_sample_size": bucket_counts[this_bucket],
        "group_sample_size": total_runners,
    }
