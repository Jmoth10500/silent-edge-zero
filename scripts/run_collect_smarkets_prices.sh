#!/bin/bash
# Recurring wrapper for launchd — see ~/Library/LaunchAgents/com.silentedgezero.collect-smarkets-prices.plist
#
# 2026-09-11: added a Netlify redeploy here too (real gap: odds refresh
# every 20 min but the live site only picked up fresh odds twice a day).
#
# 2026-09-13: REVERTED the redeploy — real problem found: deploying on
# every 20-minute run means ~72 real Netlify deploys/day (up from ~3/day
# before), and Jonathan hit real Netlify usage warnings from it. This
# job now only regenerates the LOCAL dashboard.html (free, no Netlify
# involvement) — a separate, much coarser job
# (scripts/run_redeploy_dashboard.sh, hourly) picks up whatever's
# accumulated and does the actual real deploy, cutting deploy volume
# ~3x while still keeping the live site reasonably current through the
# day. See docs/BUILD_LOG.md's 2026-09-13 entry.
set -e
cd /Users/jonathannuttall/Projects/silent-edge-zero
PY=/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
TODAY=$(date +%Y-%m-%d)
$PY scripts/collect_smarkets_prices.py "$TODAY"
$PY scripts/generate_dashboard.py "$TODAY"
