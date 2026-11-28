"""Canonical, immutable race identity and input-snapshot hashing.

Identity preference (spec section 2):
  1. authoritative provider race id            -> 'P:<provider id>'
  2. composite meeting + sequence + division   -> 'C:<date>|<course>|<seq>[|<div>]'
     (only when a provider id is genuinely unavailable)
The scheduled off-time is NEVER part of the identity: it is mutable
metadata. Pure functions only (no DB, no HTTP).
"""
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional

_COUNTRY_SUFFIX_RE = re.compile(r"\s*\([A-Za-z]{2,4}\)\s*$")
_DIV_RE = re.compile(r"\(\s*Div(?:ision)?\.?\s*(I{1,3}|IV|V|\d)\s*\)", re.IGNORECASE)
_ROMAN = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}


def horse_key(name: str) -> str:
    """Canonical horse identity used for validation: country suffix
    stripped, lower-cased, whitespace collapsed. Maps AROUND the duplicate
    `horse` rows (db/schema.sql known bug) without touching them."""
    if not name:
        return ""
    stripped = _COUNTRY_SUFFIX_RE.sub("", name)
    return re.sub(r"\s+", " ", stripped).strip().lower()


def course_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def meeting_id(race_date: date, course_name: str) -> str:
    return f"{race_date.isoformat()}|{course_key(course_name)}"


def parse_division(race_name: Optional[str]) -> Optional[str]:
    """'(Div I)' -> 'I', '(Div 2)' -> 'II'. None when the name has no division."""
    if not race_name:
        return None
    m = _DIV_RE.search(race_name)
    if not m:
        return None
    d = m.group(1).upper()
    return _ROMAN.get(d, d)


def base_race_label(race_name: Optional[str]) -> str:
    """Race name with the division marker removed, for 'same race?' checks."""
    if not race_name:
        return ""
    return re.sub(r"\s+", " ", _DIV_RE.sub("", race_name)).strip().lower()


def canonical_race_id(provider_race_id: Optional[str], race_date: date, course_name: str,
                      sequence: Optional[int] = None, division: Optional[str] = None) -> tuple[str, str]:
    """Returns (canonical_race_id, id_basis). Never derived from off-time."""
    if provider_race_id:
        return f"P:{provider_race_id}", "PROVIDER_ID"
    if sequence is None:
        raise ValueError("composite canonical id needs a race sequence when no provider race id exists")
    parts = [race_date.isoformat(), course_key(course_name), str(sequence)]
    if division:
        parts.append(division)
    return "C:" + "|".join(parts), "COMPOSITE"


def _canon_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_of(obj) -> str:
    return hashlib.sha256(_canon_json(obj).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class InputSnapshot:
    """Everything a prediction was computed from, hashed as one unit."""
    canonical_race_id: str
    meeting_id: str
    source_race_id: Optional[str]
    source_snapshot_at: Optional[str]      # ISO UTC of the feed snapshot used
    scheduled_off_time: str                # HH:MM:SS as scheduled at lock
    runner_ids: tuple
    runner_names: tuple
    model_version: str
    probabilities: tuple                   # ((horse_id, prob), ...) sorted by horse_id
    locked_at: str                         # ISO UTC

    def as_dict(self) -> dict:
        return {
            "canonical_race_id": self.canonical_race_id, "meeting_id": self.meeting_id,
            "source_race_id": self.source_race_id, "source_snapshot_at": self.source_snapshot_at,
            "scheduled_off_time": self.scheduled_off_time, "runner_ids": list(self.runner_ids),
            "runner_names": list(self.runner_names), "model_version": self.model_version,
            "probabilities": [[h, round(float(p), 10)] for h, p in self.probabilities],
            "locked_at": self.locked_at,
        }

    def sha256(self) -> str:
        return sha256_of(self.as_dict())


def build_input_snapshot(*, canonical_race_id: str, meeting: str, source_race_id: Optional[str],
                         source_snapshot_at: Optional[str], scheduled_off_time: str,
                         runners: Iterable[tuple], model_version: str,
                         probabilities: dict, locked_at: str) -> InputSnapshot:
    """`runners` is an iterable of (horse_id, horse_name); order-independent."""
    runners = sorted(set(runners), key=lambda r: (r[0], r[1]))
    return InputSnapshot(
        canonical_race_id=canonical_race_id, meeting_id=meeting, source_race_id=source_race_id,
        source_snapshot_at=source_snapshot_at, scheduled_off_time=scheduled_off_time,
        runner_ids=tuple(r[0] for r in runners), runner_names=tuple(r[1] for r in runners),
        model_version=model_version,
        probabilities=tuple(sorted(((int(h), float(p)) for h, p in probabilities.items()))),
        locked_at=locked_at,
    )
