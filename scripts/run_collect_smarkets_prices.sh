#!/bin/bash
# Recurring wrapper for launchd — see ~/Library/LaunchAgents/com.silentedgezero.collect-smarkets-prices.plist
#
# 2026-09-11: also regenerates and redeploys the dashboard, same as
# run_predict_todays_races.sh / run_collect_results.sh — real gap found:
# this collects fresh odds every 20 minutes, but until this change the
# live site only picked up fresh odds twice a day (01:15 predictions,
# 21:30 results), so real intraday odds movement sat in the DB all day
# without ever reaching the page Jonathan actually looks at. Needs the
# same nvm PATH fix as the other wrappers (netlify CLI is a
# `#!/usr/bin/env node` script; launchd's PATH doesn't include nvm).
set -e
export PATH="/Users/jonathannuttall/.nvm/versions/node/v20.19.4/bin:$PATH"
cd /Users/jonathannuttall/Projects/silent-edge-zero
PY=/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
TODAY=$(date +%Y-%m-%d)
$PY scripts/collect_smarkets_prices.py "$TODAY"
$PY scripts/generate_dashboard.py "$TODAY"
cp dashboard.html site/index.html
netlify deploy --prod --dir=site
