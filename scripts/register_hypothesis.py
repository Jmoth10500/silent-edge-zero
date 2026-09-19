#!/usr/bin/env python3
"""
CLI to register a new Research Lab hypothesis (brief Section 22). Thin
wrapper over src/research/hypothesis_tracker.py::create_hypothesis — see
that module for the immutability discipline.

Usage: python3 scripts/register_hypothesis.py <json_file>
Where json_file has keys: name, description, rule_definition,
source_finding, historical_evidence, prospective_test_start_date (optional,
YYYY-MM-DD).
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.hypothesis_tracker import create_hypothesis


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    spec = json.loads(Path(sys.argv[1]).read_text())
    prospective_start = date.fromisoformat(spec["prospective_test_start_date"]) if spec.get("prospective_test_start_date") else None
    slug = create_hypothesis(
        name=spec["name"], description=spec["description"], rule_definition=spec["rule_definition"],
        source_finding=spec["source_finding"], historical_evidence=spec["historical_evidence"],
        prospective_test_start_date=prospective_start,
    )
    print(f"Registered hypothesis '{slug}' at data/hypotheses/{slug}.json")


if __name__ == "__main__":
    main()
