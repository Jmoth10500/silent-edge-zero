"""
Research Lab hypothesis tracker — Silent Edge Zero V2 brief, Section 22.
File-based (one JSON file per hypothesis under data/hypotheses/), not a
new DB table — this is genuinely exploratory record-keeping, not
relational data the prediction pipeline needs to query, and keeping it out
of the DB means it carries zero migration/freeze risk to anything else in
this project.

**Immutability discipline, same principle as `prediction.locked_at`
(db/schema.sql's trigger), enforced here in application code rather than a
DB trigger:** once a hypothesis is created, its `name`, `description`,
`rule_definition`, `created_at`, and `historical_evidence` are frozen —
`update_prospective_results` can only ever ADD to `prospective_results`
(a list, one entry per evaluation run, each itself immutable once
appended), never edit or delete anything already there. "Never change
historical rules after seeing results" (brief Section 22) is enforced by
raising, not silently allowing, an attempt to touch a protected field.

**Never referenced by the live prediction pipeline.** No file in this
module is anywhere near FROZEN_FILES in scripts/check_model_freeze.py, and
nothing here is ever imported by scripts/predict_todays_races.py or the
model/feature modules.
"""
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

HYPOTHESES_DIR = Path(__file__).parent.parent.parent / "data" / "hypotheses"

_PROTECTED_FIELDS = {"name", "slug", "description", "rule_definition", "created_at", "historical_evidence", "source_finding"}


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise ValueError(f"cannot derive a real slug from hypothesis name {name!r}")
    return slug


def create_hypothesis(name: str, description: str, rule_definition: str, source_finding: str,
                       historical_evidence: dict, prospective_test_start_date: Optional[date] = None) -> str:
    """Creates a new hypothesis file. Refuses to overwrite an existing one
    with the same slug — a revised hypothesis is a NEW hypothesis (with a
    new name/slug), never a silent edit of an old one's frozen fields,
    same discipline as a new `model_version` row rather than mutating an
    old one. Returns the slug."""
    HYPOTHESES_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slugify(name)
    path = HYPOTHESES_DIR / f"{slug}.json"
    if path.exists():
        raise FileExistsError(
            f"hypothesis '{slug}' already exists at {path} — a revised hypothesis must get a new "
            f"name, never overwrite an existing one's frozen historical record"
        )

    record = {
        "slug": slug,
        "name": name,
        "description": description,
        "rule_definition": rule_definition,
        "source_finding": source_finding,
        "historical_evidence": historical_evidence,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prospective_test_start_date": str(prospective_test_start_date) if prospective_test_start_date else None,
        "status": "descriptive" if prospective_test_start_date is None else "awaiting_prospective_test",
        "prospective_results": [],
    }
    path.write_text(json.dumps(record, indent=2, default=str))
    return slug


def load_hypothesis(slug: str) -> dict:
    path = HYPOTHESES_DIR / f"{slug}.json"
    if not path.exists():
        raise FileNotFoundError(f"no hypothesis '{slug}' at {path}")
    return json.loads(path.read_text())


def list_hypotheses() -> list[dict]:
    if not HYPOTHESES_DIR.exists():
        return []
    return [json.loads(p.read_text()) for p in sorted(HYPOTHESES_DIR.glob("*.json"))]


def append_prospective_result(slug: str, evaluation: dict, new_status: Optional[str] = None) -> None:
    """Appends one real evaluation-run result to `prospective_results` —
    never edits or removes a prior entry. Raises if `evaluation` tries to
    smuggle a change to any protected historical field via its own keys
    (defensive — a caller should never be passing those anyway)."""
    bad_keys = set(evaluation) & _PROTECTED_FIELDS
    if bad_keys:
        raise ValueError(f"refusing to record a prospective result touching protected field(s): {bad_keys}")

    record = load_hypothesis(slug)
    evaluation = {**evaluation, "recorded_at": datetime.now(timezone.utc).isoformat()}
    record["prospective_results"].append(evaluation)
    if new_status is not None:
        if new_status not in ("awaiting_prospective_test", "prospective_supported", "prospective_rejected", "descriptive"):
            raise ValueError(f"unrecognised status {new_status!r}")
        record["status"] = new_status

    path = HYPOTHESES_DIR / f"{slug}.json"
    path.write_text(json.dumps(record, indent=2, default=str))
