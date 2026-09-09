#!/bin/bash
# Daily wrapper for launchd — see ~/Library/LaunchAgents/com.silentedgezero.predict-races.plist
set -e
cd /Users/jonathannuttall/Projects/silent-edge-zero
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/predict_todays_races.py
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/generate_dashboard.py
cp dashboard.html site/index.html
/Users/jonathannuttall/.nvm/versions/node/v20.19.4/bin/netlify deploy --prod --dir=site
