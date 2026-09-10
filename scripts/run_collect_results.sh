#!/bin/bash
# Real evening pipeline: collect today's real settled results from Racing
# Post, roll them into the persisted daily_summary track record, and
# republish the dashboard so it shows up-to-date numbers.
#
# Scheduled to run after racing has genuinely finished for the day (see
# com.silentedgezero.collect-results.plist) — Racing Post's per-race
# isResult flag means a race not yet settled is simply skipped and
# reported, never guessed (see scripts/collect_race_results.py).
set -e
export PATH="/Users/jonathannuttall/.nvm/versions/node/v20.19.4/bin:$PATH"
cd /Users/jonathannuttall/Projects/silent-edge-zero
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/collect_race_results.py
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/generate_daily_summary.py
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/generate_dashboard.py
cp dashboard.html site/index.html
netlify deploy --prod --dir=site
