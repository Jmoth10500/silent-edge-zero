#!/bin/bash
# Hourly silent-failure check — see scripts/health_check.py
cd /Users/jonathannuttall/Projects/silent-edge-zero
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/health_check.py
exit 0
