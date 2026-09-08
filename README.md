# Silent Edge Zero

£0-first AI horse racing probability & market intelligence engine. GB racing, Phase 1.

Not a tipster. Answers: where does our calculated win probability materially
diverge from the market's implied probability, and is that divergence real
enough to warrant attention? Most races should end in PASS.

**Start here:** `docs/BUILD_LOG.md` — current state and exactly what to do next.

## Quick start

```bash
./db/setup_local_postgres.sh       # fresh container only: starts Postgres, creates a local role
python3 db/init_db.py              # creates + schemas the local Postgres DB (idempotent)
python3 scripts/collect_weather.py # live, free, no signup — proves the pipeline works today
python3 -m pytest tests/ -v        # every test, all real, none skipped
```

## Docs

- `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` — how it's built and why
- `docs/FREE_DATA_SOURCES.md` — every data source, honestly rated LIVE/BLOCKED, with exactly what unblocks each
- `docs/FUTURE_PAID_UPGRADES.md` — what we'd buy later, and the evidence bar required first
- `docs/RESEARCH_LAB.md` — every modelling hypothesis, tested or not
- `docs/BUILD_LOG.md` — session-by-session log so an autonomous continuation always knows where it left off

## What's blocking full functionality right now

Three free account signups, all yours to do (can't be done on your behalf):
1. **The Racing API** (theracingapi.com) — highest priority, unlocks racecards/results/odds
2. **Kaggle** (kaggle.com) — free account + API token, unlocks historical bootstrap data
3. **Betfair Developer Program** (developer.betfair.com) — free Delayed App Key, unlocks market prices

See `docs/FREE_DATA_SOURCES.md` for exact steps on each.
