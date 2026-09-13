#!/bin/bash
# Real, coarser Netlify redeploy — hourly, not every 20 minutes.
#
# 2026-09-13: split out from scripts/run_collect_smarkets_prices.sh
# after Jonathan hit real Netlify usage warnings from deploying on every
# 20-minute odds run (~72 real deploys/day). The odds job now only
# regenerates the LOCAL dashboard.html (free); this job picks up
# whatever's accumulated since its last run and does the actual real
# deploy — ~24 deploys/day instead of ~72, while the live site still
# refreshes within the hour rather than only twice daily. See
# docs/BUILD_LOG.md's 2026-09-13 entry for the real reasoning.
set -e
export PATH="/Users/jonathannuttall/.nvm/versions/node/v20.19.4/bin:$PATH"
cd /Users/jonathannuttall/Projects/silent-edge-zero
cp dashboard.html site/index.html
netlify deploy --prod --dir=site
