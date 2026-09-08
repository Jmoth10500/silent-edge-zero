#!/bin/bash
# Daily wrapper for launchd — see ~/Library/LaunchAgents/com.silentedgezero.collect-racecards.plist
set -e
cd /Users/jonathannuttall/Projects/silent-edge-zero
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/collect_racecards.py
