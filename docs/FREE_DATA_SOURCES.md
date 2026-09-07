# Free Data Sources — Silent Edge Zero

Every source used by this system is documented here before being wired into code.
Status is honest, not aspirational — "BLOCKED" means real code cannot use it yet.

Last verified: 2026-09-08 (live checks run this session, see notes per source)

---

## 1. Weather — Open-Meteo

- **URL:** https://open-meteo.com/
- **Data supplied:** hourly precipitation, temperature, wind speed/direction, historical back to 1940, UK Met Office model available
- **API availability:** REST, plain HTTP GET, JSON response
- **Auth required:** none
- **Free limits:** non-commercial use, up to 10,000 calls/day
- **Attribution:** required — CC BY 4.0, must credit Open-Meteo
- **Commercial restrictions:** free tier is non-commercial; a paid plan exists for commercial/high-volume use (documented separately in FUTURE_PAID_UPGRADES.md, not needed for V1)
- **Redistribution restrictions:** none found beyond attribution; do not represent raw feed as your own weather model
- **Terms checked:** 2026-09-08
- **Scraping permission:** N/A — official API
- **Reliability:** confirmed live this session (real HTTP 200, real forecast JSON returned for Ascot coordinates)
- **Replacement if unavailable:** UK Met Office's own DataHub free tier (requires registration); Open-Meteo's own `ukmo-api` endpoint already proxies Met Office UKV/global models
- **Status: LIVE — integrated in `src/providers/weather_open_meteo.py`**

---

## 2. Historical UK/Ireland racing results — Kaggle community dataset

- **URL:** https://www.kaggle.com/datasets/deltaromeo/horse-racing-results-ukireland-2015-2025
- **Data supplied:** UK/Ireland race results, described as covering 1988–2026 (per dataset title), community-compiled
- **API availability:** Kaggle API (`kaggle datasets download`) or web UI download
- **Auth required:** **yes — a free Kaggle account + API token (`kaggle.json`)**. This cannot be created on your behalf; account creation is something only you can do.
- **Free limits:** dataset download is free once authenticated; Kaggle API has generous rate limits, not a practical constraint here
- **Attribution:** check the dataset's own licence tab before any redistribution — community datasets vary (some CC0, some restricted); **not yet verified — do this before relying on it beyond personal backtesting**
- **Commercial restrictions:** unverified per above — treat as personal-research-only until the specific licence is checked
- **Redistribution restrictions:** unverified — same caveat
- **Terms checked:** not yet — blocked on your Kaggle login
- **Scraping permission:** N/A, official platform download
- **Reliability:** unverified — community-maintained, "quality and completeness vary" per general Kaggle dataset caveats; treat as a bootstrap/backtest aid, not a source of truth
- **Replacement if unavailable:** other Kaggle horse-racing datasets exist (jpmiller/race-data "Big Data Derby", hwaitt/horse-racing) as fallbacks
- **Status: BLOCKED — needs you to create a free Kaggle account, generate an API token at kaggle.com/settings, and drop `kaggle.json` into `~/.kaggle/`. Once done, tell me and the loader script (`scripts/load_kaggle_historical.py`, already written, untested) can run.**

---

## 3. Live daily racecards, results, odds — The Racing API

- **URL:** https://www.theracingapi.com/
- **Data supplied:** UK/Ireland/Hong Kong racecards, results, jockey/trainer stats, odds — racecards/results/odds updating every 3–10 minutes per their own docs (two pages gave slightly different numbers; verify on signup)
- **API availability:** REST, documented, rate-limited to 5 req/sec by default
- **Auth required:** yes, API key from account signup
- **Free limits:** **not confirmed.** Their pricing page did not render a visible free tier in this session's check (a "Loading plans..." placeholder and one mention of "any specified free trial period" in billing FAQ text — implies a trial exists but terms weren't visible without logging in)
- **Attribution / commercial / redistribution:** unknown until account created — check on signup
- **Terms checked:** 2026-09-08, could not fully verify without an account
- **Scraping permission:** N/A, this is the intended API — do not scrape their site directly instead
- **Reliability:** unknown, no account to test with yet
- **Replacement if unavailable:** `scraper.tech` advertises a free horse-racing API for UK/Ireland — found via search, **not independently verified, no terms reviewed, treat with real caution** until you or I can inspect its actual ToS and reliability; OurHub Racing API (GitHub: TamB10/ourhub-racing-api) is a paid alternative (~£5/mo) if a genuinely free tier doesn't pan out
- **Status: BLOCKED — needs you to sign up for an account (free or paid) to get an API key and confirm the actual free-tier terms. This is the single most valuable unblock for the whole project — it's what lets daily racecard ingestion (Phase 3) go live.**

---

## 4. Betfair Exchange — market prices (back/lay)

- **URL:** https://developer.betfair.com/
- **Data supplied:** exchange back/lay prices, market depth, market IDs, runner IDs
- **API availability:** Betfair Exchange API (Delayed App Key for development/non-live use)
- **Auth required:** yes — free Betfair account + developer application for a Delayed App Key
- **Free limits:** Delayed App Key access is free for development and for private customers; a Live App Key (real-time prices for actual betting) requires a one-off £499 activation fee — **not needed for Silent Edge Zero**, which only needs delayed/development-grade prices for shadow-mode research
- **Attribution:** check Betfair's API terms on signup
- **Commercial restrictions:** Delayed App Key explicitly for development/non-commercial-live use — fine for our research/shadow-mode purpose
- **Redistribution restrictions:** check on signup, standard exchange-data restrictions likely apply (no redistributing raw prices as a commercial feed)
- **Terms checked:** 2026-09-08, from public support docs only, not from inside a real developer account
- **Scraping permission:** N/A, use the API
- **Reliability:** not yet tested — needs account
- **Replacement if unavailable:** bookmaker-published odds via The Racing API's odds endpoint (see source 3) can substitute for a rough market-probability baseline if Betfair access stalls
- **Status: BLOCKED — needs you to create a free Betfair account and register for a Delayed App Key (developer.betfair.com). This is the Model 0 (market baseline) data source — important but not as urgent as source 3, since bookmaker odds from Racing API can serve as an interim market-probability proxy.**

---

## 5. BHA official ratings / regulatory reports

- **URL:** https://www.britishhorseracing.com/regulation/official-ratings/ratings-database/
- **Data supplied:** official ratings lookup (per-horse, searchable), quarterly/annual aggregate reports (field sizes, runners/race, prize money)
- **API availability:** none found — web pages and PDF reports only
- **Auth required:** none for browsing
- **Free limits:** N/A
- **Attribution:** standard fair-use citation of a public regulator's published figures
- **Commercial restrictions:** unclear for bulk reuse — this is a reference source, not a bulk-ingestion source, for V1
- **Redistribution restrictions:** unclear — do not bulk-scrape without checking robots.txt and terms first
- **Terms checked:** 2026-09-08, not deeply — deferred
- **Scraping permission:** **not checked — do not build an automated scraper against this yet.** Per the project's own rule, "do not scrape a site simply because scraping is technically possible." If official ratings are needed and The Racing API's own ratings/runner data (source 3) doesn't cover them adequately, this needs a deliberate, permission-checked scraping decision, not a default one.
- **Reliability:** high (it's the regulator) but access method is manual for now
- **Replacement:** The Racing API includes ratings-adjacent runner data per its docs — likely sufficient once source 3 is unblocked
- **Status: REFERENCE ONLY for V1. No automated ingestion built.**

---

## Summary — what's actually live vs blocked right now

| Source | Status | Blocker |
|---|---|---|
| Open-Meteo (weather) | **LIVE** | none — working now |
| Kaggle historical results | BLOCKED | needs your free Kaggle account + API token |
| The Racing API (racecards/results/odds) | BLOCKED | needs your account signup + API key |
| Betfair Exchange (market prices) | BLOCKED | needs your free developer account + Delayed App Key |
| BHA official ratings | Reference only | scraping permission not checked, deliberately deferred |

**The single highest-value unblock: sign up for The Racing API and send me the key.** That alone lights up racecards, results, and odds — three of the four core data feeds — in one step.
