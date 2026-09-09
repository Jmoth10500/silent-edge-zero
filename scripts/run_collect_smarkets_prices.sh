#!/bin/bash
# Recurring wrapper for launchd — see ~/Library/LaunchAgents/com.silentedgezero.collect-smarkets-prices.plist
set -e
cd /Users/jonathannuttall/Projects/silent-edge-zero
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/collect_smarkets_prices.py
