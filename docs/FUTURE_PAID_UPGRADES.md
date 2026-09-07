# Future Paid Upgrades

Rule: **data must earn the right to be purchased.** Nothing here gets bought
until the free/current version has been tested and shown to be a genuine
limiting factor, with evidence, not a hunch.

| Upgrade | Cost (as found 2026-09-08, verify before buying) | What it adds | Can it be tested first? | Minimum evidence needed |
|---|---|---|---|---|
| The Racing API — paid tier | Usage-scaled, exact pricing not visible without account | Higher rate limits, possibly deeper ratings/stats fields | Yes — start on whatever free/trial tier exists first | Hitting rate limits regularly on the free tier, with a queue of unmet requests logged |
| Betfair Live App Key | £499 one-off activation | Real-time (non-delayed) exchange prices for actual live betting | Delayed App Key already covers shadow-mode research | Only relevant once Silent Edge moves past shadow mode toward real execution — not before |
| Betfair Historical Data (paid tiers) | Priced per dataset/month on historicdata.betfair.com | Full price ladder + volume, vs free tier's last-traded-price-per-minute only | Yes — free tier is enough to prototype the market-movement features (Section 16) first | Free tier's coarser data demonstrably limits a specific feature's predictive power in backtests |
| Timeform / Total Performance Data | Not yet priced — enterprise racing data providers | Proprietary ratings, sectional times | Build Silent Edge's own rating (Section 9) first | Our own rating underperforms and a documented feature-ablation test (Section 38) shows a Timeform-style input would plausibly close the gap |
| OurHub Racing API | ~£5/month | Alternative racecard/prediction source if The Racing API's free tier proves insufficient | Yes, cheap enough to trial directly | The Racing API free tier turns out not to exist or to be too limited |

Nothing above is committed to. This file exists so a future purchase decision has to explicitly reference the evidence bar it needs to clear first.
