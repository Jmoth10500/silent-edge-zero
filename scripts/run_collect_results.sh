#!/bin/bash
# Real evening pipeline: collect today's real settled results, roll them
# into the persisted daily_summary track record, and republish the
# dashboard so it shows up-to-date numbers.
#
# 2026-09-13: horseracing.net promoted to PRIMARY results source —
# genuinely verified live (9/9 spot-check, then 398/398 real results at
# full scale, see docs/BUILD_LOG.md) after Racing Post's own
# meeting-page discovery route became unreliable for a finished race
# day, even same-evening. scripts/collect_race_results.py (Racing Post)
# still runs second as a real, harmless cross-check/fallback — both
# scripts UPSERT (ON CONFLICT DO UPDATE) into runner_result, so running
# both in sequence never duplicates or conflicts; whichever source
# actually has a race's real result fills it in.
#
# Scheduled to run after racing has genuinely finished for the day (see
# com.silentedgezero.collect-results.plist).
set -e
export PATH="/Users/jonathannuttall/.nvm/versions/node/v20.19.4/bin:$PATH"
cd /Users/jonathannuttall/Projects/silent-edge-zero
PY=/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
TODAY=$(date +%Y-%m-%d)
$PY scripts/import_horseracingnet_results.py "$TODAY"
$PY scripts/collect_race_results.py "$TODAY"
$PY scripts/generate_daily_summary.py "$TODAY"
$PY scripts/integrity_report.py "$TODAY"
$PY scripts/generate_dashboard.py
cp dashboard.html site/index.html
# Research Intelligence: regenerated nightly (was manual -> stale since 21 Sep). It refuses to
# publish if its own reconciliation fails; in that case the old page stays and the failure is logged.
if $PY scripts/generate_research_dashboard.py; then
  cp research_dashboard.html site/research_dashboard.html
else
  echo "research dashboard NOT updated: generation/reconciliation failed" >&2
fi
# No Netlify deploy here since 2026-09-30: the site is published once a day
# by scripts/run_deploy_site.sh (06:00). Everything stays local until then.
