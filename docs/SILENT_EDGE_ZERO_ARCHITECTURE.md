# Silent Edge Zero — Architecture

**Status:** Phase 1–2 in progress. Built 2026-09-08 overnight session, continuing autonomously.
**Core rule:** £0 monthly operating cost. Every dependency below is free or has a documented free tier — see `FREE_DATA_SOURCES.md`.

## Philosophy (from the build brief, kept here so future-me doesn't drift)

Not "which horse wins" — **where does our probability diverge from the market's, and is that divergence real?**
Model probability vs market-implied probability. Edge only means something when it survives calibration and walk-forward validation. Most races should end in PASS.

## Stack (all free/open-source)

- **Database:** PostgreSQL 16 (already running locally via Homebrew, zero setup cost)
- **Language:** Python 3.11 (already on this machine)
- **ML:** scikit-learn, CatBoost/XGBoost/LightGBM (added when Phase 6–7 starts, not yet needed)
- **API layer:** FastAPI (added when Phase 11 dashboard starts)
- **Provider abstraction:** every external data source sits behind an interface (`RacecardProvider`, `OddsProvider`, `ResultsProvider`, `RatingsProvider`, `WeatherProvider`) so a provider can be swapped without touching the rest of the system — see `src/providers/`

## Directory layout

```
silent-edge-zero/
  docs/
    FREE_DATA_SOURCES.md       — every data source, honestly rated LIVE/BLOCKED
    SILENT_EDGE_ZERO_ARCHITECTURE.md   — this file
    FUTURE_PAID_UPGRADES.md    — what we'd buy later, and what evidence would justify it
    RESEARCH_LAB.md            — every modelling hypothesis, tested or not
    BUILD_LOG.md               — running log for the autonomous overnight build, so each
                                  continuation session knows exactly where it left off
  db/
    schema.sql                 — canonical Postgres schema (Phase 2)
    init_db.py                 — creates the database + applies schema, idempotent
  src/
    providers/
      base.py                  — abstract interfaces (RacecardProvider etc.)
      weather_open_meteo.py    — LIVE: real Open-Meteo integration
      racecard_theracingapi.py — LIVE since 2026-09-08 (Session 4): real HTTP Basic auth,
                                  field mapping verified against a real response. Only
                                  runnable on Jonathan's own machine (has the credentials
                                  in a local .env) — the cloud routine environment does not
                                  have THERACINGAPI_USERNAME/PASSWORD and never assumes it does.
      (odds_betfair.py         — NOT YET WRITTEN, waiting on a Betfair Delayed App Key —
                                  this line is aspirational, the file does not exist yet)
    market/
      probability.py           — overround removal: proportional, power, Shin methods
      movement.py               — price movement features: opening/current price,
                                  price change %, drift/shorten classification (Section 16)
    features/
      runner_features.py        — per-runner raw features (rating, age, weight, draw,
                                  form) and race-relative/percentile features (Section 8/10)
      feature_vector.py         — combines runner_features.py (Sections 8+10) and
                                  market/movement.py (Section 16) into a single flat
                                  per-runner feature dict — the actual model-input row shape
    evaluation/
      calibration.py            — Brier score, log loss, calibration curve (Section 24)
    validation/
      walk_forward.py           — chronological walk-forward split harness (Section 29)
    models/
      model0_market_baseline.py — Model 0: the de-vigged market probability treated AS the
                                  prediction, plus the walk-forward-split -> predict -> score
                                  pipeline wiring (Sections 18/19, 24, 29 end-to-end)
      model1_logistic_baseline.py — Model 1: first FITTED model, a per-race softmax/
                                  multinomial-logit over race-relative rating/draw/form/
                                  weight features (Section 8/10 features -> Section 6-ish
                                  first model), trained by pure-Python gradient ascent.
                                  Synthetic-fixture-only — see RESEARCH_LAB.md RL-006.
  scripts/
    collect_racecards.py       — LIVE since 2026-09-08 (Session 4): pulls real GB racecards
                                  from The Racing API into the DB. Mac-only (needs
                                  THERACINGAPI_USERNAME/PASSWORD, not present in the cloud
                                  routine environment) — do not attempt this from the cloud.
    collect_weather.py         — runs the live weather provider, stores snapshots
    load_kaggle_historical.py  — bootstraps historical DB from the Kaggle dataset,
                                  written but untested — needs your Kaggle credentials
  tests/
    test_leakage.py            — enforces observed_at/available_at ordering (Section 6/30)
                                  and the DB-level prediction-immutability trigger (Section 32)
    test_market_probability.py — checks overround-removal methods sum to ~1.0
    test_market_movement.py    — price movement feature tests
    test_runner_features.py    — per-runner and race-relative feature tests (synthetic fixtures)
    test_feature_vector.py     — combined feature-vector tests (synthetic fixtures)
    test_calibration.py        — Brier/log-loss/calibration-curve tests (synthetic predictions)
    test_walk_forward.py       — walk-forward split harness tests (synthetic chronological data)
    test_model0_market_baseline.py — Model 0 + end-to-end split/predict/score pipeline tests,
                                  with hand-verified Brier scores against known synthetic odds
    test_model1_logistic_baseline.py — Model 1 tests: hand-verified single gradient-ascent
                                  step, uniform-output check for the untrained (zero-weight)
                                  model, and a signal-recovery convergence check — all
                                  against synthetic fixtures shaped like the real racecard
                                  schema (official_rating/draw as int, recent_form as
                                  '1582F3'-style undelimited string)
    test_racecard_theracingapi.py — LIVE provider tests against a real captured API response
                                  fixture (Session 4) — includes the ambiguous off_time
                                  regression case
```

## Data integrity rules enforced in code, not just policy

1. **Every row gets `observed_at`, `available_at`, `ingested_at`, `source`.** A model must never be able to see data whose `available_at` is after the prediction's timestamp — enforced by a query-time filter in `db/schema.sql`'s views, tested in `tests/test_leakage.py`.
2. **PRE_RACE_SNAPSHOT and POST_RACE_RESULT are separate tables, never merged in place.** A snapshot is never overwritten.
3. **Predictions are immutable once locked.** Enforced by a Postgres trigger (`trg_prevent_locked_prediction_update` in `db/schema.sql`), not just ORM discipline — any UPDATE against a row with `locked_at` set is rejected by the database itself, tested in `tests/test_leakage.py`. The only legitimate way to change a locked prediction is to INSERT a new row under a new model_version.
4. **No random train/test splits.** Anything under `tests/` or `scripts/` that evaluates a model must use chronological (walk-forward) splits — this is a code-review rule until an automated check exists.

## What's genuinely working right now (2026-09-08)

- PostgreSQL schema designed and applied (Race, Runner, Horse, Trainer, Jockey, MarketSnapshot, Prediction, Result, DataSource — see `db/schema.sql`)
- Live weather ingestion via Open-Meteo, tested against a real racecourse coordinate, zero signup
- Market probability math (overround removal — proportional/power/Shin) implemented and unit-tested against known odds sets
- Provider interfaces defined so racecard/odds providers plug in the moment API keys exist

## What's blocked on you, specifically

See `FREE_DATA_SOURCES.md` — three signups (The Racing API, Betfair Delayed App Key, Kaggle) unlock the actual racing data. None of these can be done on your behalf — they're account creations. The Racing API signup is the single highest-leverage one: it unblocks racecards, results, and odds in one step.

## What the autonomous build continues doing while blocked

Everything that doesn't need real racing data yet:
- Finish the DB schema's indexes and constraints
- Build out the feature-engineering code against schema-valid synthetic fixtures (clearly labeled as fixtures, never presented as real predictions)
- Build the market-probability and calibration math further (Section 15, 24)
- Build the leakage/time-travel test harness (Section 6, 30)
- Write the walk-forward validation scaffold (Section 29)
- Keep `BUILD_LOG.md` updated so the next autonomous session picks up exactly here
