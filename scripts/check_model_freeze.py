#!/usr/bin/env python3
"""
Model-freeze regression guard — Silent Edge Zero V2 brief, Phase 0.

The live prediction pipeline (scripts/predict_todays_races.py) refits both
models from scratch on the full historical dataset every run — there is no
persisted weight file anywhere in this repo (confirmed: no pickle/joblib,
no models/ or artifacts/ dir). So "freezing the model" means freezing the
CODE that produces predictions, not a weight file, and a live before/after
diff of predictions is not by itself a valid regression test — new results
landing legitimately shifts tomorrow's freshly-fit weights even with zero
code changes.

This script checks two independent things:

1. CODE HASH CHECK — every file in FROZEN_FILES must still match the
   SHA-256 recorded in data/model_freeze_manifest.json. A mismatch means
   someone edited a file that produces predictions, rankings, or top
   picks — this must never happen without a separate, explicit
   conversation (see docs/BUILD_LOG.md / the Research V2 brief).

2. LOCKED-PREDICTION SNAPSHOT CHECK — a CSV snapshot of already-locked
   `prediction` rows (id, model_probability, locked_at, record_hash) taken
   at freeze time must still match the live DB exactly. The DB trigger
   trg_prevent_locked_prediction_update (db/schema.sql) should already make
   this impossible, but this is belt-and-braces: it would catch a trigger
   being dropped/bypassed, a migration touching prediction directly, etc.

For the DB-embedded prediction/model_version/trigger DDL (db/schema.sql
lines 207-269 at freeze time), the manifest stores a hash of that specific
line range, not the whole file — the rest of schema.sql (e.g.
market_snapshot) is legitimately edited by later research-layer work.

Usage:
    python3 scripts/generate_model_freeze_manifest.py   # (re)create the manifest + snapshot, once
    python3 scripts/check_model_freeze.py                # verify — exit 0 pass, exit 1 fail
"""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

REPO_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "model_freeze_manifest.json"
SNAPSHOT_PATH = REPO_ROOT / "data" / "model_freeze_locked_predictions_snapshot.csv"

FROZEN_FILES = [
    "scripts/predict_todays_races.py",
    "scripts/train_model1.py",
    "scripts/train_model2.py",
    "src/models/__init__.py",
    "src/models/model0_market_baseline.py",
    "src/models/model1_logistic_baseline.py",
    "src/models/model2_gradient_boosting.py",
    "src/features/__init__.py",
    "src/features/connections_strike_rate.py",
    "src/features/draw_bias_history.py",
    "src/features/feature_vector.py",
    "src/features/going_affinity.py",
    "src/features/runner_features.py",
]

# db/schema.sql content markers bounding the model_version/prediction table
# DDL and the locked-row immutability trigger. Deliberately content-based,
# not line-number-based: an unrelated edit earlier in the file (e.g. Phase
# 1 adding a market_snapshot column) shifts every later line number, which
# would make a line-range hash fail for a reason that has nothing to do
# with the frozen block actually changing.
SCHEMA_DDL_START_MARKER = "CREATE TABLE IF NOT EXISTS model_version ("
SCHEMA_DDL_END_MARKER = "EXECUTE FUNCTION prevent_locked_prediction_update();"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_schema_ddl_range() -> str:
    text = (REPO_ROOT / "db" / "schema.sql").read_text()
    start = text.index(SCHEMA_DDL_START_MARKER)
    end = text.index(SCHEMA_DDL_END_MARKER) + len(SCHEMA_DDL_END_MARKER)
    return hashlib.sha256(text[start:end].encode()).hexdigest()


def current_git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()


def check_code_hashes() -> list[str]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    failures = []
    for rel_path, expected_hash in manifest["files"].items():
        if rel_path == "db/schema.sql#model_version+prediction+trigger":
            actual = sha256_schema_ddl_range()
        else:
            actual = sha256_file(REPO_ROOT / rel_path)
        if actual != expected_hash:
            failures.append(f"HASH MISMATCH: {rel_path} has changed since the freeze manifest was recorded")
    return failures


def check_locked_predictions() -> list[str]:
    if not SNAPSHOT_PATH.exists():
        return [f"MISSING SNAPSHOT: {SNAPSHOT_PATH} not found — run generate_model_freeze_manifest.py first"]

    with open(SNAPSHOT_PATH) as f:
        snapshot_rows = {row["id"]: row for row in csv.DictReader(f)}

    if not snapshot_rows:
        return []

    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()
    cur.execute(
        "SELECT id, model_probability, locked_at, record_hash FROM prediction WHERE id = ANY(%s)",
        (list(map(int, snapshot_rows.keys())),),
    )
    live_rows = {
        str(pid): {"model_probability": str(prob), "locked_at": str(locked_at), "record_hash": record_hash}
        for pid, prob, locked_at, record_hash in cur
    }
    cur.close()
    conn.close()

    failures = []
    for pid, snap in snapshot_rows.items():
        live = live_rows.get(pid)
        if live is None:
            failures.append(f"LOCKED PREDICTION {pid} MISSING from live DB — was it deleted?")
            continue
        for field in ("record_hash",):
            if snap[field] != live[field]:
                failures.append(
                    f"LOCKED PREDICTION {pid} CHANGED: {field} was {snap[field]!r}, now {live[field]!r}"
                )
    return failures


def main():
    if not MANIFEST_PATH.exists():
        print(f"No freeze manifest at {MANIFEST_PATH} — run scripts/generate_model_freeze_manifest.py first.")
        sys.exit(1)

    failures = check_code_hashes() + check_locked_predictions()

    if failures:
        print("MODEL FREEZE CHECK: FAIL")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    manifest = json.loads(MANIFEST_PATH.read_text())
    with open(SNAPSHOT_PATH) as f:
        n_snapshot_rows = sum(1 for _ in csv.DictReader(f))
    print(f"MODEL FREEZE CHECK: PASS ({len(manifest['files'])} files hashed, "
          f"{n_snapshot_rows} locked predictions verified unchanged)")
    print(f"  Frozen at commit {manifest['frozen_at_commit'][:12]} on {manifest['frozen_at']}")
    print(f"  Current commit  {current_git_commit()[:12]}")
    sys.exit(0)


if __name__ == "__main__":
    main()
