#!/usr/bin/env python3
"""
Create the silent_edge_zero database (if it doesn't exist) and apply schema.sql.
Idempotent — safe to run repeatedly. Uses the local Homebrew Postgres already
running on this machine (zero-cost, no new infrastructure).
"""
import subprocess
import sys
from pathlib import Path

DB_NAME = "silent_edge_zero"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def main():
    exists = run(["psql", "-lqt"]).stdout
    if DB_NAME in exists:
        print(f"Database '{DB_NAME}' already exists.")
    else:
        r = run(["createdb", DB_NAME])
        if r.returncode != 0:
            print("Failed to create database:", r.stderr, file=sys.stderr)
            sys.exit(1)
        print(f"Created database '{DB_NAME}'.")

    r = run(["psql", "-d", DB_NAME, "-f", str(SCHEMA_PATH)])
    print(r.stdout)
    if r.returncode != 0:
        print("Schema apply had errors:", r.stderr, file=sys.stderr)
        sys.exit(1)
    print("Schema applied successfully.")

    # sanity check: list tables
    r = run(["psql", "-d", DB_NAME, "-c", "\\dt"])
    print(r.stdout)


if __name__ == "__main__":
    main()
