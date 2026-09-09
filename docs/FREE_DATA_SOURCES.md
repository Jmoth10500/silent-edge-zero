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
- **Status: LIVE — real account created, real data loaded 2026-09-08.**
- **Auth method (newer/simpler than expected):** a single API token, not the old username+key `kaggle.json`. Set via `KAGGLE_API_TOKEN` env var or saved to `~/.kaggle/access_token`. Confirmed working.
- **Data supplied, confirmed by actually opening the download:** far more than just results — `form_2015-present/raceform.csv` (the main file, 1,851,285 rows, 2015-01-01 to 2026-05-27, 37 columns: date, course, race_id, off, race_name, type, class, pattern, dist, going, ran, pos, draw, sp, jockey, trainer, or/rpr/ts ratings, sire/dam/damsire, owner, race comment), plus `archive_1988-2004/`, `archive_2005-2014/`, `betfair/`, `BHA_ratings/`, `daily_racecards/`, `recent_form_html/` — only `raceform.csv` has been loaded so far, the rest are there if needed later.
- **Licence CONFIRMED: Community Data License Agreement – Sharing – Version 1.0** (shown directly in the Kaggle CLI download output, not a guess). CDLA-Sharing is share-alike: any *redistributed derivative dataset* must carry the same licence. Internal research/backtesting use — which is all this project does with it — is unrestricted.
- **Loaded into the database:** `scripts/load_kaggle_historical.py` — real script, run successfully. Loaded from 2023-01-01 onward (configurable start date; full file goes back to 2015-01-01, re-run with an earlier date to backfill more): **558,370 runner results, 57,267 races, across 1,241 distinct racing days**, stored as `runner_result` + `runner_snapshot` rows with `observed_at`/`available_at` set to each race's real off-time (not "today" — this is genuine backdated historical data, correctly timestamped so the leakage tests still mean something).
- **Real data-quality issue found and fixed:** the CSV's "missing value" marker isn't consistent — sometimes an en-dash (`–`), sometimes a plain hyphen (`-`), sometimes empty. A naive `float()` call crashed on row ~1.2M. Fixed with a `safe_float`/`safe_int` helper that treats any unparseable value as `None`, never a guess.
- **Reliability:** good in practice — real winners, real starting prices (fractional odds like `11/4F` correctly converted to decimal), spot-checked against several real races.
- **Replacement if unavailable:** other Kaggle horse-racing datasets exist (jpmiller/race-data "Big Data Derby", hwaitt/horse-racing) as fallbacks
- **Status: LIVE — real account created, real token issued, real data loaded 2026-09-08 (Session 6). This section's own closing status line had gone stale since before Session 6 and still said BLOCKED / described the OLD (pre-real) auth method (`kaggle.json`, superseded by the single-token method documented above) — corrected 2026-09-09 (Session 19) to match this section's own body text three lines up, which already had it right. Same class of top-vs-body drift Session 17 found and fixed in the summary table below; this one was inside a section body, not the table, so that pass missed it.**

---

## 3. Live daily racecards, results, odds — The Racing API

- **URL:** https://www.theracingapi.com/
- **Free tier CONFIRMED LIVE 2026-09-08** — real account created, real credentials tested against the real API.
- **What the pricing page claims vs what the API actually enforces (these disagree — trust the API, not the marketing copy):**
  - Pricing page lists "Results for all races on daily racecards (basic data)" under Free.
  - The real OpenAPI spec (and a live call) shows `/v1/results`, `/v1/results/today`, and `/v1/racecards/summaries` **all require Basic Plan (£27.99/mo)** — confirmed live: `/v1/results/today` with real free-tier credentials returned `{"detail":"Basic Plan required"}`.
  - **Conclusion: results are NOT actually free, despite the pricing page.** Only `/v1/racecards/free` (pre-race data, today/tomorrow) and `/v1/courses` are genuinely free.
- **Free tier confirmed working:** `/v1/racecards/free?day=today` — HTTP Basic Auth (username+password, not a bearer token). Returns real UK/Ireland/France racecards. Live-tested 2026-09-08: 29 real GB races, 248 runners, fields verified against the real `RacecardBasic`/`RunnerBasic` schema (not guessed).
- **Free tier does NOT include:** results (see above — this contradicts the pricing page), odds (Standard tier, £59.99/mo+), historical results-per-horse, horse/jockey/trainer search, analysis endpoints.
- **Paid tiers:** Basic £27.99/mo (adds results + historical), Standard £59.99/mo (adds odds), Pro £99.99/mo. See `FUTURE_PAID_UPGRADES.md` — none justified yet; results specifically might be worth revisiting once Phase 6 needs real outcomes to validate against and Kaggle's historical dataset proves insufficient.
- **API availability:** REST, documented, rate-limited to 5 req/sec by default
- **Auth:** HTTP Basic (username + password pair, from account dashboard → API Keys) — confirmed from the real OpenAPI spec at `raw.githubusercontent.com/APIs-guru/openapi-directory/.../theracingapi.com/1.0.0/openapi.yaml`
- **Attribution / commercial / redistribution:** ToS link present on signup, full text not yet reviewed — personal/research use only in scope right now
- **Terms checked:** 2026-09-08, pricing page + live API behaviour; full ToS text still not read
- **Reliability:** good — worked first call, real data, no errors
- **Real bug found and fixed:** the API's own `off_time` field is ambiguous (e.g. `"1:12"`, no AM/PM) — use `off_dt` (full ISO datetime) instead. See `src/providers/racecard_theracingapi.py` and its regression test.
- **Practical implication for the build:** Phase 3 (daily collector, pre-race snapshots) is genuinely live. Phase 4 (market baseline) is still blocked — no odds on any tier below Standard. **Phase 6 validation (comparing predictions to real outcomes) is also still blocked** — results aren't free either, despite what the pricing page says. Kaggle's historical dataset is the real path to real outcomes for now, not this API.
- **Status: LIVE for racecards. BLOCKED for results/odds — same as before, just via a different (paid) tier than the pricing page implied.**

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
- **Provider stub:** `src/providers/odds_betfair.py` — written 2026-09-09 (cloud routine) against the public JSON-RPC docs (listMarketCatalogue for runner names, listMarketBook for best back/lay prices), 8 tests in `tests/test_odds_betfair.py` against a docs-shaped fixture (NOT a real captured response). Genuinely untested against a live account, same status racecard_theracingapi.py carried before Session 4 verified it live — do not trust the field mapping until a real call confirms it. Also documents, rather than solves, a real gap: auth needs a session token from a *separate* login step (identitysso.betfair.com) this provider doesn't perform, and Betfair marketIds live in a different ID space from Racing API race IDs with no reconciliation built yet.
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
| Kaggle historical results | **LIVE** — 558,370 real results loaded (2023–2026) | none — done |
| The Racing API — racecards (free tier) | **LIVE** — real account, real credentials tested, real races pulled since Session 4 (2026-09-08); Mac-only, daily-automated (Session 5) | none — done, but only runnable on Jonathan's Mac (`.env` credentials not present in this cloud routine) |
| The Racing API — results | BLOCKED | needs paid Basic tier (£27.99/mo) — not pursued, Kaggle's historical dataset covers this need for free (Session 6) |
| The Racing API — odds | BLOCKED | needs paid Standard tier (£59.99/mo+) or Betfair instead |
| Betfair Exchange (market prices) | BLOCKED | needs your free developer account + Delayed App Key. Provider stub + race-identity reconciliation logic both written and unit-tested (Sessions 14–15), neither live-verified |
| BHA official ratings | Reference only | scraping permission not checked, deliberately deferred |

**This table previously (incorrectly) showed The Racing API as fully BLOCKED — stale since before Session 4 confirmed racecards LIVE. Corrected 2026-09-09 (Session 17) to match this file's own body text above, which already had it right.** The one real remaining unblock left on Jonathan: a free Betfair developer account + Delayed App Key, for real market prices (Phase 4). Kaggle now covers historical outcomes, so Racing API's paid results tier is not being pursued.
