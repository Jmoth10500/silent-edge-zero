#!/usr/bin/env bash
# One-time-per-container local Postgres bootstrap for Silent Edge Zero.
#
# This project's DB code (db/init_db.py, tests/test_leakage.py) connects
# with psycopg2.connect(dbname=...) and no explicit user/password — that
# relies on Unix "peer" auth, which requires a Postgres role matching
# whatever OS user runs the code. On Jonathan's own machine (Homebrew
# Postgres) that role already exists. In a fresh ephemeral container
# (e.g. an autonomous cloud session) it usually doesn't, and Postgres
# itself may not even be started yet — this script fixes both, and is
# safe to re-run (every step is idempotent).
#
# Needs to run as a user that can `sudo -u postgres` (root, in this
# project's cloud sessions). Zero new infrastructure, zero cost — same
# local Postgres 16 install, just making sure it's up and the calling
# OS user can reach it.
set -euo pipefail

CURRENT_OS_USER="$(whoami)"

if command -v service >/dev/null 2>&1; then
    service postgresql status >/dev/null 2>&1 || service postgresql start
fi

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${CURRENT_OS_USER}'" | grep -q 1; then
    sudo -u postgres createuser -s "${CURRENT_OS_USER}"
    echo "Created superuser Postgres role '${CURRENT_OS_USER}' (peer auth for local dev/test only)."
else
    echo "Postgres role '${CURRENT_OS_USER}' already exists."
fi

echo "Postgres is up and '${CURRENT_OS_USER}' can connect. Run 'python3 db/init_db.py' next."
