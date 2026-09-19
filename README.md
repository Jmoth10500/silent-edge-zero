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

## What's actually blocking things right now (updated 2026-09-19 — the section above was stale)

All three original signups are done. Real, current open items:
1. **Betfair Exchange** — account created, Delayed App Key issued, but login still returns `LIMITED_ACCESS`/`SUSPENDED` even after identity verification. Smarkets (no auth needed) is the live substitute for market prices.
2. **The Racing API's paid tiers** — an open decision, not a blocker: results/odds are gated behind Basic (£27.99/mo) / Standard (£59.99/mo+); horseracing.net + Smarkets cover the same need for free today.
3. **Racing TV RaceIQ** (sectional/GPS data) — researched 2026-09-19: no documented API, only a commercial contact form. Not integrated; would need a real licensing conversation, not a scraper.

See `docs/FREE_DATA_SOURCES.md` for the full, current per-source status.
