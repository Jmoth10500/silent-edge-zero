"""Pre-prediction validation gate (spec section 3). Pure functions.

A race that fails ANY rule is quarantined: no scored prediction, a clear
'RACE UNDER REVIEW' status, the failed rules recorded. Conflicts between
races (duplicate label, shared runners) quarantine EVERY race involved,
because from the feed alone we cannot know which one is real — the real
one is re-validated and scored on a later run once the provider has
dropped the phantom (late lock is fine, a wrong lock is not).
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from src.integrity.canonical import base_race_label, horse_key, parse_division

# Rule codes (stable identifiers stored in race_validation.failed_rules)
V01_CANONICAL_ID = "V01_CANONICAL_ID_MISSING_OR_DUPLICATE"
V02_NOT_IN_LATEST_FEED = "V02_NOT_IN_LATEST_AUTHORITATIVE_FEED"
V03_MEETING_DATE = "V03_MEETING_OR_DATE_INCONSISTENT"
V04_INTERNAL_CONSISTENCY = "V04_INTERNAL_INCONSISTENCY"
V05_DUPLICATE_PROVIDER_ID = "V05_PROVIDER_ID_ON_MULTIPLE_ACTIVE_RACES"
V06_DUPLICATE_RUNNER = "V06_DUPLICATE_RUNNER_IN_RACE"
V07_RUNNER_IN_MULTIPLE_RACES = "V07_RUNNER_IN_MULTIPLE_RACES_AT_MEETING"
V08_RUNNER_COUNT = "V08_RUNNER_COUNT_IMPLAUSIBLE_OR_MISMATCHED"
V09_ABANDONED = "V09_RACE_ABANDONED_OR_CANCELLED"
V10_SNAPSHOT_TIMESTAMP = "V10_SNAPSHOT_TIMESTAMP_UNTRUSTWORTHY"
V11_STALE_OVERWRITE = "V11_STALE_SNAPSHOT_WOULD_OVERWRITE_FRESHER"
V12_DUPLICATE_RACE_LABEL = "V12_DUPLICATE_RACE_LABEL_AT_MEETING"

MIN_RUNNERS = 2
MAX_RUNNERS = 40
MAX_SNAPSHOT_AGE = timedelta(hours=36)
BAD_STATUSES = {"ABANDONED", "CANCELLED", "RETIRED", "QUARANTINED"}


@dataclass
class RaceView:
    """One race as seen in one feed snapshot."""
    race_id: int
    canonical_race_id: Optional[str]
    provider_race_id: Optional[str]
    race_date: object                      # datetime.date
    snapshot_date: object                  # date the snapshot was fetched FOR
    meeting_id: str
    course_name: str
    off_time: Optional[str]
    race_name: str
    runner_names: list
    feed_runner_count: Optional[int]       # authoritative count from the feed, if reported
    status: str = "ACTIVE"
    snapshot_at: Optional[datetime] = None
    in_latest_feed: bool = True
    superseding_snapshot_at: Optional[datetime] = None   # fresher stored snapshot, for V11
    division: Optional[str] = field(default=None)


@dataclass
class ValidationResult:
    race_id: int
    canonical_race_id: Optional[str]
    status: str                            # VALID | QUARANTINED
    failed_rules: list
    detail: dict

    @property
    def ok(self) -> bool:
        return self.status == "VALID"


def validate_races(races: list, now: datetime) -> list:
    """Validate every race of one meeting-day batch together (cross-race
    rules need the whole programme). Returns one ValidationResult per race."""
    fails: dict[int, list] = {r.race_id: [] for r in races}
    detail: dict[int, dict] = {r.race_id: {} for r in races}

    def fail(r, rule, **info):
        if rule not in fails[r.race_id]:
            fails[r.race_id].append(rule)
        detail[r.race_id].setdefault(rule, {}).update(info)

    # --- per-race rules -------------------------------------------------
    cid_count: dict[str, int] = {}
    pid_count: dict[str, int] = {}
    for r in races:
        if r.canonical_race_id:
            cid_count[r.canonical_race_id] = cid_count.get(r.canonical_race_id, 0) + 1
        if r.provider_race_id:
            pid_count[r.provider_race_id] = pid_count.get(r.provider_race_id, 0) + 1

    for r in races:
        keys = [horse_key(n) for n in r.runner_names]
        if not r.canonical_race_id or cid_count.get(r.canonical_race_id, 0) > 1:
            fail(r, V01_CANONICAL_ID)
        if not r.in_latest_feed:
            fail(r, V02_NOT_IN_LATEST_FEED)
        if r.race_date != r.snapshot_date or not r.meeting_id.startswith(str(r.race_date)):
            fail(r, V03_MEETING_DATE, race_date=str(r.race_date), snapshot_date=str(r.snapshot_date))
        div = r.division or parse_division(r.race_name)
        if not r.off_time or not r.race_name or not r.course_name:
            fail(r, V04_INTERNAL_CONSISTENCY, reason="missing off_time/race_name/course")
        elif div and div not in {"I", "II", "III", "IV", "V"}:
            fail(r, V04_INTERNAL_CONSISTENCY, reason=f"unrecognised division {div!r}")
        if r.provider_race_id and pid_count.get(r.provider_race_id, 0) > 1:
            fail(r, V05_DUPLICATE_PROVIDER_ID, provider_race_id=r.provider_race_id)
        if len(set(keys)) != len(keys) or any(not k for k in keys):
            fail(r, V06_DUPLICATE_RUNNER)
        n = len(keys)
        if n < MIN_RUNNERS or n > MAX_RUNNERS or (
                r.feed_runner_count is not None and r.feed_runner_count != n):
            fail(r, V08_RUNNER_COUNT, runners=n, feed_runner_count=r.feed_runner_count)
        if (r.status or "").upper() in BAD_STATUSES:
            fail(r, V09_ABANDONED, status=r.status)
        if r.snapshot_at is None or r.snapshot_at > now + timedelta(minutes=5) \
                or now - r.snapshot_at > MAX_SNAPSHOT_AGE:
            fail(r, V10_SNAPSHOT_TIMESTAMP, snapshot_at=str(r.snapshot_at))
        if r.superseding_snapshot_at and r.snapshot_at and r.snapshot_at < r.superseding_snapshot_at:
            fail(r, V11_STALE_OVERWRITE, snapshot_at=str(r.snapshot_at),
                 fresher=str(r.superseding_snapshot_at))

    # --- cross-race rules (per meeting) ---------------------------------
    # Only races that are LIVE in the latest authoritative feed take part: a retired phantom that
    # has already left the feed must not keep quarantining the real races it once conflicted with.
    by_meeting: dict[str, list] = {}
    for r in races:
        if r.in_latest_feed and (r.status or "").upper() not in BAD_STATUSES:
            by_meeting.setdefault(r.meeting_id, []).append(r)

    for meeting, group in by_meeting.items():
        # V07: a runner may belong to exactly one race at the meeting.
        owners: dict[str, list] = {}
        for r in group:
            for k in set(horse_key(n) for n in r.runner_names):
                owners.setdefault(k, []).append(r)
        for k, rs in owners.items():
            if len(rs) > 1:
                for r in rs:
                    fail(r, V07_RUNNER_IN_MULTIPLE_RACES,
                         horse=k, also_in=sorted({x.race_id for x in rs if x.race_id != r.race_id}))
        # V12: the same race label on two live races is only suspicious when the division marker repeats
        # ("Div I" twice cannot both be real) or the two share runners (a combined/provisional card).
        # Identical sponsor names on separate, runner-disjoint races (e.g. two qualifier heats) are legitimate.
        labels: dict[tuple, list] = {}
        for r in group:
            div = r.division or parse_division(r.race_name)
            labels.setdefault((base_race_label(r.race_name), div), []).append(r)
        for (label, div), rs in labels.items():
            if not label or len(rs) < 2:
                continue
            for r in rs:
                mine = {horse_key(n) for n in r.runner_names}
                others = [x for x in rs if x.race_id != r.race_id]
                overlapping = [x.race_id for x in others if mine & {horse_key(n) for n in x.runner_names}]
                if div is not None or overlapping:
                    fail(r, V12_DUPLICATE_RACE_LABEL, label=label, division=div,
                         also=sorted(x.race_id for x in others), sharing_runners_with=overlapping)

    return [
        ValidationResult(race_id=r.race_id, canonical_race_id=r.canonical_race_id,
                         status="QUARANTINED" if fails[r.race_id] else "VALID",
                         failed_rules=fails[r.race_id], detail=detail[r.race_id])
        for r in races
    ]


def status_label(result: ValidationResult) -> str:
    """Public wording for a quarantined race."""
    if result.ok:
        return "VALIDATED"
    return "DATA VALIDATION FAILED — RACE UNDER REVIEW (" + ", ".join(result.failed_rules) + ")"
