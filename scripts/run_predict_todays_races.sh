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
set -e
export PATH="/Users/jonathannuttall/.nvm/versions/node/v20.19.4/bin:$PATH"
cd /Users/jonathannuttall/Projects/silent-edge-zero
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/predict_todays_races.py
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/generate_dashboard.py
cp dashboard.html site/index.html
netlify deploy --prod --dir=site
