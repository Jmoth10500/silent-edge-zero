#!/usr/bin/env python3
"""
One-off (or deliberately re-run) generator for the model-freeze manifest and
locked-predictions snapshot that scripts/check_model_freeze.py verifies
against. See that script's docstring for why both exist.

Re-running this script MOVES the freeze point forward — only do that after
an explicit, separate conversation confirming the frozen files were meant
to change (e.g. a genuinely new, deliberate model version). Never re-run it
just to make a failing check pass.

Usage: python3 scripts/generate_model_freeze_manifest.py
"""
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json

import psycopg2

from scripts.check_model_freeze import (
    FROZEN_FILES,
    MANIFEST_PATH,
    REPO_ROOT,
    SNAPSHOT_PATH,
    current_git_commit,
    sha256_file,
    sha256_schema_ddl_range,
)


def main():
    files = {rel: sha256_file(REPO_ROOT / rel) for rel in FROZEN_FILES}
    files["db/schema.sql#model_version+prediction+trigger"] = sha256_schema_ddl_range()

    manifest = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "frozen_at_commit": current_git_commit(),
        "files": files,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n")
    print(f"Wrote manifest: {MANIFEST_PATH} ({len(files)} entries)")

    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()
    cur.execute(
        "SELECT id, model_probability, locked_at, record_hash FROM prediction "
        "WHERE locked_at IS NOT NULL ORDER BY id"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    with open(SNAPSHOT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "model_probability", "locked_at", "record_hash"])
        writer.writerows(rows)
    print(f"Wrote snapshot: {SNAPSHOT_PATH} ({len(rows)} locked prediction rows)")


if __name__ == "__main__":
    main()
