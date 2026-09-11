#!/bin/bash
# Daily wrapper for launchd — see ~/Library/LaunchAgents/com.silentedgezero.predict-races.plist
#
# Real bug found and fixed 2026-09-10: launchd runs this with a minimal
# PATH that doesn't include nvm's node install, so the netlify CLI
# (itself a `#!/usr/bin/env node` script) failed with "env: node: No such
# file or directory" — predictions/dashboard generation succeeded, but
# the Netlify deploy silently never ran, so the live site kept showing
# stale/empty data despite the local pipeline completing without error.
# Fixed by explicitly adding nvm's node bin directory to PATH here.
#
# 2026-09-11: also predicts tomorrow's real races (collect_racecards.py
# now fetches both days) so the dashboard's Today/Tomorrow tab always has
# real predictions ready, not just a bare racecard — see
# generate_dashboard.py's render_day_tabs.
set -e
export PATH="/Users/jonathannuttall/.nvm/versions/node/v20.19.4/bin:$PATH"
cd /Users/jonathannuttall/Projects/silent-edge-zero
PY=/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
TODAY=$(date +%Y-%m-%d)
TOMORROW=$(date -v+1d +%Y-%m-%d)
$PY scripts/predict_todays_races.py "$TODAY"
$PY scripts/predict_todays_races.py "$TOMORROW"
$PY scripts/generate_dashboard.py "$TODAY"
cp dashboard.html site/index.html
netlify deploy --prod --dir=site
