# Build Log

This file is read by the autonomous continuation routine at the start of every
run — it exists so a fresh session with zero memory of this conversation can
pick up exactly where the last one stopped, without re-deriving anything or
re-doing finished work.

---

## 2026-09-08 — Session 1 (interactive, this build)

**Phase reached:** early Phase 2/3 boundary (database done, first live provider done, market math done, leakage tests done). Phases 1–2 substantially complete; Phase 3 (daily collector) partially blocked.

**What's genuinely done and verified:**
- `docs/FREE_DATA_SOURCES.md` — 5 sources researched via live web search, honestly rated LIVE/BLOCKED/reference-only
- `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` — architecture overview
- `docs/FUTURE_PAID_UPGRADES.md`, `docs/RESEARCH_LAB.md` — started
- `db/schema.sql` + `db/init_db.py` — real Postgres 16 database `silent_edge_zero`, 13 tables, applied and verified locally (this machine's Homebrew Postgres, already running, zero new cost)
- `src/providers/base.py` — provider interfaces (RacecardProvider, OddsProvider, ResultsProvider, RatingsProvider, WeatherProvider, ExternalPredictionProvider)
- `src/providers/weather_open_meteo.py` — **LIVE and verified**: real HTTP calls to Open-Meteo, no key needed
- `scripts/collect_weather.py` — **ran successfully**, stored real weather snapshots for 13 GB racecourses in `weather_snapshot` table, 2026-09-08
- `src/market/probability.py` — proportional/power/Shin overround-removal, all three implemented
- `tests/test_market_probability.py` — 5 real unit tests, all passing (found and fixed a genuine bug in power_method's bisection bounds for underround edge cases, and added a guard in shin_method for the same)
- `tests/test_leakage.py` — 2 real tests against the live database, both passing; confirms the leakage-safe query pattern actually excludes future-dated snapshots
- `src/providers/racecard_theracingapi.py` — **STUB, untested**, written against public docs, field-name mapping unverified (needs a real API response to confirm)
- `scripts/load_kaggle_historical.py` — **STUB, untested**, blocked on Kaggle account

**What's blocked on Jonathan specifically (cannot be done by Claude):**
1. Sign up for The Racing API (theracingapi.com) — highest priority, unblocks racecards/results/odds in one step
2. Create a free Kaggle account + API token for the historical bootstrap dataset
3. Create a free Betfair developer account + Delayed App Key for market prices

**What the next autonomous session should do, in priority order (all free, no account needed):**
1. Check `docs/FREE_DATA_SOURCES.md` — has Jonathan sent an API key since the last run? If yes, that unblocks real Phase 3 work (test the racecard provider against real data, fix its field mapping, wire up a real daily collector). Check for a note in this file or ask via the routine's summary.
2. If still blocked: continue Phase 5 groundwork — feature engineering functions (Section 8: official rating, age, weight, draw, form; Section 10: relative/percentile features within a race) written against clearly-labelled synthetic fixtures (never presented as real predictions), with real unit tests.
3. Build `src/market/movement.py` — price movement features (Section 16: opening price, current price, price change %, drift/shortening) — pure math, no external data needed, can be fully built and tested now.
4. Build the calibration scaffolding (Section 24: Brier score, log loss, calibration curve functions) — pure math, testable now with synthetic prediction/outcome pairs.
5. Build the walk-forward validation harness (Section 29) as a reusable function, tested against synthetic chronological data, ready to run the moment real historical data exists.
6. Add a Postgres trigger enforcing prediction immutability once `locked_at` is set (mentioned as a TODO in `tests/test_leakage.py`'s second test).
7. Keep this file updated at the end of every session — add a new dated section above this instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress:**
- Do not fabricate racecard/odds/result data to "demo" a working pipeline — Section 60 of the build brief is explicit about this, and it would poison the leakage tests' credibility
- Do not create accounts on Jonathan's behalf (Racing API, Kaggle, Betfair) — these are genuinely blocked until he acts
- Do not scrape britishhorseracing.com or any other site not yet permission-checked — see FREE_DATA_SOURCES.md #5

---

## 2026-09-08 — Session 2 (autonomous overnight)

**Checked for new credentials first, per the ground rules:** searched `docs/FREE_DATA_SOURCES.md`, git log, and this container's environment for any API key/token Jonathan might have sent since Session 1. **Nothing found** — all three signups (The Racing API, Kaggle, Betfair) are still genuinely blocked on him. Did not create any accounts. Proceeded straight to BUILD_LOG's priority list items 2–6 (all free, no account needed), skipping item 1 since it's still blocked.

**Environment note for future sessions (this matters, read it):** this autonomous routine runs in a fresh ephemeral cloud container each time, not on Jonathan's own Homebrew-Postgres machine that Session 1 used. Postgres wasn't running and there was no DB role for the container's OS user (peer auth failed with `role "root" does not exist`). Fixed by starting the `postgresql` service and creating a matching superuser role, then wrote **`db/setup_local_postgres.sh`** (idempotent, safe to re-run) so every future session does this in one step instead of re-diagnosing it. Run it once per fresh container, before `db/init_db.py`. This is a local dev/test convenience only — zero new infrastructure, zero cost, same local Postgres 16.

**What's genuinely done and verified this session (all real code, all with real passing tests — 50/50 tests pass via `python3 -m pytest tests/ -v`):**
- `src/market/movement.py` — price movement features (Section 16): `opening_price`, `current_price`, `price_change_pct`, `max_price`, `min_price`, `movement_classification` (DRIFTING/STEADY/SHORTENING, configurable threshold). Pure math, no external data. `tests/test_market_movement.py` — 8 tests, including an out-of-order-input case (sorts by `observed_at`, not list order) and threshold configurability.
- `src/evaluation/calibration.py` — Brier score, log loss, calibration curve (Section 24). Input validation (mismatched lengths, empty input, non-binary outcomes all raise `ValueError`). `tests/test_calibration.py` — 12 tests, including known hand-calculated values (e.g. constant p=0.5 Brier = 0.25, log loss at p=0.5 = ln(2)) and an off-by-one check for p=1.0 landing in the last bin, not overflowing.
- `src/features/runner_features.py` — Section 8 (official rating, age, weight, draw, form) and Section 10 (race-relative/percentile features) built against clearly-labelled synthetic fixtures, never presented as real predictions. `parse_recent_form`/`form_score` (recency-weighted vs flat average, both implemented so they can be compared once real data exists — see `docs/RESEARCH_LAB.md` RL-003), `relative_official_rating` (rank/percentile/vs-mean, ties share rank), `draw_bias_features` (neutral positional percentile only — deliberately NOT a track-specific bias claim, see RL-004), `relative_weight`. Runners missing a field are omitted from that feature's output, never imputed. `tests/test_runner_features.py` — 13 tests.
- `src/validation/walk_forward.py` — chronological walk-forward split harness (Section 29). Expanding or fixed-size rolling windows, configurable step; asserts internally that every split it produces is actually chronological (train strictly precedes test) as a hard safety net, not just a docstring promise. `tests/test_walk_forward.py` — 9 tests, including a shuffled-input-order case (indices must map back to the caller's original row order, not a re-sorted one) and rejection of non-positive parameters.
- **Postgres trigger enforcing prediction immutability** (the TODO explicitly flagged in Session 1's `tests/test_leakage.py`): `trg_prevent_locked_prediction_update` in `db/schema.sql` — `BEFORE UPDATE` on `prediction`, rejects any update where `OLD.locked_at IS NOT NULL`. Added idempotently (`CREATE OR REPLACE FUNCTION` + `DROP TRIGGER IF EXISTS`), re-applied to the live DB and verified. Upgraded `tests/test_leakage.py`'s previously-placeholder second test into a real test: inserts an unlocked prediction, confirms it CAN be updated, locks it, confirms the trigger rejects a further update (`psycopg2.errors.RaiseException`), cleans up. `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` rule 3 updated to reflect this is now DB-enforced, not just an ORM-layer promise.
- Docs updated to match: `README.md` (quick start now runs the full pytest suite and the new Postgres bootstrap script), `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` (directory layout + integrity rules), `docs/RESEARCH_LAB.md` (RL-003, RL-004 — flagging the form-scoring and draw-percentile design choices as unvalidated defaults, not claims).

**What's still blocked on Jonathan specifically (unchanged from Session 1):**
1. Sign up for The Racing API (theracingapi.com) — still the highest-priority unblock, racecards/results/odds in one step
2. Free Kaggle account + API token for the historical bootstrap dataset
3. Free Betfair developer account + Delayed App Key for market prices

**What the next autonomous session should do, in priority order:**
1. **Check for a key/credential first, as always** — `docs/FREE_DATA_SOURCES.md` and recent commits. If The Racing API key has arrived: run `./db/setup_local_postgres.sh && python3 db/init_db.py` first (fresh container), then test `src/providers/racecard_theracingapi.py` against a real response, fix its field-name mapping, and wire up a real daily collector script (`scripts/collect_racecards.py`, doesn't exist yet) — this is Phase 3 proper.
2. If still blocked: wire `src/features/runner_features.py` and `src/market/movement.py` together into a single per-runner feature vector function (Section 8+10+16 combined), still against synthetic fixtures, still real-tested — this is the shape the eventual model input will actually take, worth having ready.
3. Build the Model 0 (market baseline) scaffold (Section 18/19-ish): a function that takes de-vigged market probabilities (already built in `src/market/probability.py`) and treats them AS a prediction, so `src/evaluation/calibration.py` and `src/validation/walk_forward.py` have something real (if trivial) to run against end-to-end before any actual model exists. This closes the loop from "pure math functions" to "an actual, if dumb, working prediction pipeline" without needing any blocked data source — a market-implied-probability baseline needs the same odds data any other model would need, so this can only be smoke-tested with synthetic odds until Racing API/Betfair unblocks, but the pipeline plumbing (walk-forward split → predict → score) can be built and tested now.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB — do not silently start debugging a "role does not exist" error again, it's already solved.
5. Keep this file updated at the end of every session — add a new dated section above this instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data to "demo" a working pipeline
- Do not create accounts on Jonathan's behalf (Racing API, Kaggle, Betfair)
- Do not scrape britishhorseracing.com or any other site not yet permission-checked
- Do not skip re-running the full test suite before committing — all 50 tests must actually pass, not just the new ones

---

## 2026-09-08 — Session 3 (autonomous overnight)

**Checked for new credentials first, per the ground rules:** re-checked `docs/FREE_DATA_SOURCES.md`, `git log --all`, and this container's environment (`env | grep -iE "racing|kaggle|betfair|api_key|apikey"`) for anything Jonathan might have sent since Session 2. **Nothing found** — all three signups (The Racing API, Kaggle, Betfair) are still genuinely blocked on him. Did not create any accounts. Proceeded to Session 2's priority list items 2–3 (both free, no account needed), skipping item 1 since it's still blocked.

**Environment note:** this container's local `main` branch ref was stale (pointed at Session 1's commit) even though `origin/main` already had Session 2's commit — the working tree itself was a detached HEAD sitting on the right (Session 2) commit. Fixed with `git checkout -B main origin/main` before starting; no data was lost, this was just a stale local ref in a fresh container, not a real divergence. Re-ran `./db/setup_local_postgres.sh && python3 db/init_db.py` (fresh container, as expected) and `pip install pytest psycopg2-binary` (both already in `requirements.txt`, just not pre-installed in this container) before touching anything.

**What's genuinely done and verified this session (all real code, all with real passing tests — 64/64 tests pass via `python3 -m pytest tests/ -v`, up from 50):**
- `src/features/feature_vector.py` — `build_runner_feature_vectors()`, combining `src/features/runner_features.py` (Sections 8+10) and `src/market/movement.py` (Section 16) into one flat per-runner feature dict — the actual shape a model's input row will eventually take. Every runner in the input always gets an output entry; every individual missing feature (no rating, no price history, only one price observation, etc.) is omitted from that runner's dict, never imputed — same rule the two underlying modules already enforce, just carried through the merge. `tests/test_feature_vector.py` — 7 tests, including a full-merge case across all three feature groups with hand-checked rank/percentile/price values, and a case confirming a horse absent from `price_history` gets zero price-derived keys (not zeros).
- `src/models/model0_market_baseline.py` — **Model 0, the market baseline**, per Session 2's priority item 3. `predict_race_probabilities()` treats the de-vigged market probability (`src/market/probability.py`, already built) directly as the prediction — no fitting, no parameters, by design (it's the null hypothesis every real model must beat, see `docs/RESEARCH_LAB.md` RL-005). `evaluate_market_baseline_walk_forward()` wires this through the existing walk-forward split harness (`src/validation/walk_forward.py`) and Brier/log-loss/calibration scoring (`src/evaluation/calibration.py`) end-to-end — chronological split → predict test-window races → score. This closes the loop Session 2 flagged: "pure math functions" → "an actual, if dumb, working prediction pipeline", fully smoke-tested now, ready to point at real (race_date, odds, winner) rows the moment The Racing API or Betfair unblocks. `tests/test_model0_market_baseline.py` — 7 tests, including one that hand-verifies exact Brier scores (0.25 and 1/9) against synthetic zero-overround odds across two walk-forward splits, and confirms a train-only race is correctly excluded from scoring.
- Docs updated to match: `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` (directory layout: `feature_vector.py`, `model0_market_baseline.py`, and their test files added), `docs/RESEARCH_LAB.md` (new entry RL-005: Model 0 as the bar every real model must clear, status IDEA — pipeline tested on synthetic data only, no real-data run yet).
- Full test suite re-run and confirmed green after every change, per the ground rules: `python3 -m pytest tests/ -v` → 64/64 passed, including the DB-backed `tests/test_leakage.py` tests (ran against a freshly bootstrapped local Postgres in this container).

**What's still blocked on Jonathan specifically (unchanged from Sessions 1–2):**
1. Sign up for The Racing API (theracingapi.com) — still the highest-priority unblock, racecards/results/odds in one step
2. Free Kaggle account + API token for the historical bootstrap dataset
3. Free Betfair developer account + Delayed App Key for market prices

**What the next autonomous session should do, in priority order:**
1. **Check for a key/credential first, as always** — `docs/FREE_DATA_SOURCES.md`, recent commits, and container env vars. If The Racing API key has arrived: run `./db/setup_local_postgres.sh && python3 db/init_db.py` first (fresh container), then test `src/providers/racecard_theracingapi.py` against a real response, fix its field-name mapping, and wire up a real daily collector script (`scripts/collect_racecards.py`, doesn't exist yet) — this is Phase 3 proper. This has now been the #1 item for three sessions running; if it's still blocked, don't re-derive that fact from scratch, just move to item 2.
2. If still blocked: there is genuinely very little synthetic-fixture plumbing left to build without real data — the split→predict→score loop, feature vectors, market math, and calibration are all done and tested. Worthwhile next synthetic-only work: (a) an `odds_betfair.py` provider stub written against Betfair's public Exchange API docs (STUB, untested, same status as `racecard_theracingapi.py` — the directory layout in `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` already lists this file but it does not exist yet, that's a doc/reality mismatch worth fixing either by writing the stub or by correcting the doc); (b) a second, deliberately-different Model 0 variant using each of the three overround methods side by side on the SAME synthetic race set, to at least confirm the plumbing supports comparing methods (not a real benchmark — that still needs real odds — but proves the harness can run more than one method through `evaluate_market_baseline_walk_forward` without changes); (c) re-read `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md`'s full section list (only Sections 6, 8, 10, 15, 16, 24, 29, 30, 32 are touched so far) for another synthetic-only section worth scaffolding now.
3. Consider whether it's worth just waiting on Jonathan rather than continuing to add synthetic-only scaffolding — three sessions have now built every piece of plumbing that doesn't need real data. Say this plainly in the next session's summary rather than manufacturing more work for its own sake if nothing genuinely useful remains.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session — add a new dated section above this instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data to "demo" a working pipeline
- Do not create accounts on Jonathan's behalf (Racing API, Kaggle, Betfair)
- Do not scrape britishhorseracing.com or any other site not yet permission-checked
- Do not skip re-running the full test suite before committing — all 64 tests must actually pass, not just the new ones

---

## 2026-09-08 — Session 4 (interactive, Jonathan's own machine)

**The blocker is cleared.** Jonathan signed up for The Racing API and sent real credentials. This is the milestone the last three sessions were waiting on.

**What's genuinely done and verified this session:**
- Credentials stored in `.env` (gitignored, never committed) — see `.env.example` for the template
- Fixed `src/providers/racecard_theracingapi.py`: auth is HTTP Basic (username+password), NOT a bearer token as the old stub guessed — confirmed from the real published OpenAPI spec (`https://raw.githubusercontent.com/APIs-guru/openapi-directory/.../theracingapi.com/1.0.0/openapi.yaml`) and a live call
- **First real API call succeeded**: `/v1/racecards/free?day=today` returned 54 real races (17 FR, 29 GB, 8 IRE) for 2026-09-08. Field mapping in the provider now matches the real `RacecardBasic`/`RunnerBasic` schema exactly (verified against the OpenAPI spec, not guessed)
- **Real bug found and fixed live**: the API's own `off_time` field is ambiguous (e.g. `"1:12"`, no AM/PM) — Leicester's real 13:12 race was returned as `"1:12"`, and a naive TIME cast in Postgres silently read it as 01:12 AM. Fixed by deriving off_time from `off_dt` (a full ISO datetime with timezone) instead of trusting the provider's own ambiguous string. Regression test added: `tests/test_racecard_theracingapi.py::test_ambiguous_off_time_is_corrected_via_off_dt`, using the exact real Leicester race as its fixture.
- Also fixed: distance conversion (`distance_f`, furlongs as a string) × 220 → yards, not left null as the old stub did
- **`scripts/collect_racecards.py` — new, real, run successfully**: pulled today's 29 real GB races into the live database — 29 `race` rows, 248 `runner_snapshot` rows, all real horses/trainers/jockeys/form, all with correct `observed_at`/`available_at`/`ingested_at`/`source_id`
- `tests/test_racecard_theracingapi.py` — 6 new tests, all against a fixture built from the real captured response (not guessed field names), including the off_time regression case
- Full suite re-run: 70/70 tests pass
- `docs/FREE_DATA_SOURCES.md` #3 updated: **The Racing API confirmed LIVE** for racecards+results on the free tier (£0/mo). Odds are NOT on the free tier — that still needs Betfair or a paid Racing API tier, unchanged blocker for Phase 4's real market data.
- Updated the autonomous routine's own instructions (via RemoteTrigger) to reflect this honestly: **the cloud routine environment does NOT have these credentials** (an attempt to set them as routine env vars didn't take — the API silently ignored the field, worth someone checking why later, low priority) — so racecard/weather collection stays Mac-only for now. The cloud routine should keep building Phase 6+ scaffolding against realistic synthetic fixtures shaped like the now-real, verified schema, not attempt live calls it can't make.

**What this changes for future sessions:**
- Phase 3 (daily collector) is now **genuinely live**, not stubbed — but only when run on Jonathan's Mac (`python3 scripts/collect_racecards.py`), not from the cloud routine.
- The synthetic fixtures used everywhere else in the codebase (features, calibration, walk-forward) should ideally be reshaped to match the real confirmed field formats (e.g. `official_rating` really does come through as a numeric string that needs casting, `recent_form` really is a raw string like `"1582F3"` with no delimiters) — worth an audit pass, not done this session.
- Results collection (`/v1/results` or `/v1/results/today` — not yet verified live, don't assume the field names) is the natural next step once there are results to check predictions against. Verify the real response shape with a live call before writing a parser, same discipline as this session used for racecards.
- Phase 6 (first real model) can start honestly now: real racecard structure exists, even though there's no real outcome data yet to train against. A model trained/scored only against synthetic outcomes must say so clearly, everywhere — comments, docs, and BUILD_LOG.

**What's still blocked:**
1. Betfair Delayed App Key — for real market prices (Phase 4)
2. Kaggle account — for historical bootstrap/backtest depth (helps Phase 6+ validation, not urgent yet)
3. Racing API odds — needs a paid tier (£59.99/mo+) or Betfair instead; not pursuing a paid tier without evidence it's needed first, per `FUTURE_PAID_UPGRADES.md`'s own rule

---

## 2026-09-08 — Session 5 (autonomous overnight, cloud routine)

**Confirmed the credential boundary before doing anything else, per the ground rules and this
session's explicit instructions:** `env | grep THERACINGAPI` in this container returned
nothing. This cloud routine environment does **not** have `THERACINGAPI_USERNAME` /
`THERACINGAPI_PASSWORD` — those only exist in Jonathan's local, gitignored `.env` on his own
Mac (Session 4). Did **not** attempt `scripts/collect_racecards.py` or
`scripts/collect_weather.py` here — both would fail on missing credentials (racecards) or are
simply the wrong environment to be running live collection from at all. **Racecard/weather
collection stays Mac-only until a future session explicitly confirms otherwise in this file —
that has not happened, so don't assume it next time either.**

**Started Phase 6, as instructed:** a simple statistical/logistic baseline model — Model 1 —
built and tested against realistic synthetic fixtures shaped exactly like the real, verified
racecard schema (`src/providers/racecard_theracingapi.py` /
`tests/test_racecard_theracingapi.py`: `official_rating` as int, `draw` as int, `recent_form`
as an undelimited string like `'1582F3'`). **This is still not a real prediction** — labelled
as such in the module docstring, every relevant test docstring, `docs/RESEARCH_LAB.md` RL-006,
and here — because there is no real (racecard, result) pair anywhere in this repository yet.

**What's genuinely done and verified this session (all real code, all with real passing
tests — 80/80 tests pass via `python3 -m pytest tests/ -v`, up from 70):**
- `src/models/model1_logistic_baseline.py` — **Model 1**, the first FITTED model in this repo
  (Model 0 has no parameters by design; this one has four). Shape: a per-race multinomial
  logit (softmax) over race-relative features already built and tested in
  `src/features/runner_features.py` (Sections 8/10) — official rating vs. field mean, draw
  percentile vs. 0.5, recency-weighted form score vs. field mean, weight vs. field mean. Every
  feature is deliberately zero-centered/undirected (the fitted weight's sign decides whether
  higher is better, nothing is asserted up front — same discipline as RL-004's neutral draw
  percentile). Because the softmax normalises over that race's own runners, the output
  probability distribution sums to ~1.0 per race by construction, no separate renormalisation
  needed. `build_race_features()` gives every runner a full 4-key feature dict always (missing
  underlying fields default to 0.0 = "no evidence either way", flagged honestly as a
  modelling simplification rather than silently done); `predict_race_probabilities()` scores
  and softmaxes a race; `fit_logistic_baseline()` is plain batch gradient ASCENT on the
  observed-winner log-likelihood, L2-regularised, implemented in pure Python (no
  numpy/scikit-learn — both still deliberately commented out in `requirements.txt`; this repo
  has done its own small-scale numerical methods throughout, e.g. `src/market/probability.py`'s
  bisection solvers, and four features doesn't yet justify the dependency).
- `tests/test_model1_logistic_baseline.py` — 10 real tests: exact hand-verified feature
  centering (rating/weight/draw edges checked against hand-calculated field means), missing-
  field defaulting, an untrained (all-zero-weight) model proven exactly uniform (1/n per
  runner, not just "close to"), sums-to-~1.0 with nonzero weights, empty-race and
  empty-training-set/bad-winner error handling, a **hand-verified single gradient-ascent step**
  (same style as `tests/test_calibration.py`/`tests/test_model0_market_baseline.py`'s
  hand-checked values: one race, weights start at zero, gradient and resulting weight computed
  by hand and asserted exactly), and a convergence check (20 synthetic races where the
  highest-rated runner always wins → fitted `rating_edge` weight comes out positive, and the
  fitted model then rates that runner-shape above uniform on a held-out race).
- `docs/RESEARCH_LAB.md` — new entry RL-006 (Model 1, status IDEA, explicit about what's
  proven — the maths works — vs. not proven — anything about real racing).
- `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` — directory listing updated: `model1_logistic_baseline.py`
  and its test file added; also corrected two lines that had gone stale since Session 4/earlier
  and would have misled the next session — `racecard_theracingapi.py` was still listed as
  "STUB... waiting on an API key" (it's been LIVE since Session 4) and `odds_betfair.py` was
  listed as an existing stub file when it has never actually been written (confirmed via `ls`);
  also added the now-existing `scripts/collect_racecards.py` (Mac-only, noted as such) which
  Session 4 built but this doc never listed.
- Full test suite re-run and green after every change: `./db/setup_local_postgres.sh &&
  python3 db/init_db.py` (fresh container, as every prior autonomous session has needed) then
  `python3 -m pytest tests/ -v` → **80/80 passed**, including the DB-backed `tests/test_leakage.py`
  tests against a freshly bootstrapped local Postgres in this container. `pip install pytest
  psycopg2-binary python-dotenv requests` was needed first (fresh container has none of
  `requirements.txt` pre-installed, matching every prior session's experience — not a new
  finding, just re-confirmed).

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — for real market prices (Phase 4)
2. Kaggle account — for historical bootstrap/backtest depth
3. Racing API odds — needs a paid tier, not pursuing without evidence it's needed
4. Real results data — needed before Model 1 (or Model 0) can be genuinely trained/evaluated,
   not a Jonathan-signup blocker exactly, but a "hasn't been built yet" blocker (see next item)

**What the next session should do, in priority order:**
1. **Check for new credentials/results as always** — `env | grep -iE
   "racing|kaggle|betfair"`, recent commits, this file. If still Mac-only, don't re-derive that,
   move on.
2. **Results collection is the single highest-leverage next step**, and it's a Mac-only task
   (needs live credentials) for a future *interactive* session, not this cloud routine: verify
   The Racing API's real results response shape with a live call (`/v1/results` or
   `/v1/results/today` — Session 4 flagged this as "not yet verified live, don't assume the
   field names") before writing a parser, same discipline Session 4 used for racecards. Once
   real (racecard, result) pairs exist in the DB, both Model 0 and Model 1 can be genuinely
   evaluated for the first time — everything before that point is plumbing, however solid.
3. If still cloud-only and blocked: there is very little synthetic-only plumbing left that's
   obviously worth building blind. Worth considering instead of manufacturing more scaffolding:
   (a) an `odds_betfair.py` provider stub against Betfair's public Exchange API docs — the
   directory listing has (correctly, now) flagged this as not written yet; (b) a second Model 1
   variant or hyperparameter sweep (learning_rate/l2/iterations) compared on the SAME synthetic
   rating-signal fixture, to at least confirm the fitting is stable across reasonable settings —
   still not a real benchmark; (c) revisit RL-006's flagged missingness simplification (a
   debutant with no official rating isn't "average", it's a distinct case) as a candidate
   feature once real data exists to check whether it matters.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session — add a new dated section above this
   instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data, or Model 1 training data, to "demo" anything
- Do not create accounts on Jonathan's behalf (Betfair, Kaggle)
- Do not attempt `scripts/collect_racecards.py` or `scripts/collect_weather.py` from this cloud
  routine environment — no credentials here, confirmed again this session, will fail
- Do not present Model 1's synthetic-fixture test results as evidence it predicts real racing
- Do not skip re-running the full test suite before committing — all 80 tests must actually
  pass, not just the new ones

---

## 2026-09-08 — Session 5 (interactive, Jonathan's own machine)

**Corrected a real inaccuracy from earlier this session:** live-tested `/v1/results/today` with the real free-tier credentials — returned `{"detail":"Basic Plan required"}`. The pricing page's claim that results are on the Free tier is wrong (or at least not enforced that way by the actual API). Confirmed via the real OpenAPI spec: `/v1/results`, `/v1/results/today` and `/v1/racecards/summaries` all require Basic (£27.99/mo)+. Only `/v1/racecards/free` and `/v1/courses` are genuinely free. `docs/FREE_DATA_SOURCES.md` #3 rewritten to reflect this — trust the live API behaviour over the marketing page from here on. **Practical consequence: Kaggle's historical dataset is the real path to outcome data for Phase 6 validation, not a Racing API upgrade.**

**Set up real daily automation** — `scripts/run_collect_racecards.sh` + `~/Library/LaunchAgents/com.silentedgezero.collect-racecards.plist`, loaded and verified: triggered manually via `launchctl start`, confirmed it runs the exact same path as the scheduled 07:00 daily fire, real output, zero errors, logs to `logs/collect_racecards.log`. This is Mac-only (same constraint as the collector script itself — needs the local `.env` credentials the cloud routine doesn't have). Racecard snapshots will now accumulate automatically every morning without anyone needing to trigger it.

**Confirmed the immutable-snapshot design works as intended, not a bug:** running the collector twice in one day correctly produced two full generations of `runner_snapshot` rows (248 → 496) rather than overwriting — exactly per Section 5's "never overwrite the pre-race snapshot" rule. Worth knowing for future sessions: don't "fix" this by adding an UPDATE path, it's deliberate.

**What's still blocked:**
1. Kaggle account — now the highest-priority unblock (real historical outcomes for Phase 6 validation)
2. Betfair Delayed App Key — real market prices (Phase 4)
3. Racing API results — would need Basic tier (£27.99/mo); not pursuing without evidence Kaggle's data proves insufficient first, per `FUTURE_PAID_UPGRADES.md`

---

## 2026-09-08 — Session 6 (interactive, Jonathan's own machine)

**Second real blocker cleared this session.** Jonathan created a Kaggle account and sent a real API token.

**What's genuinely done and verified:**
- Real auth confirmed: Kaggle's current auth method is a single API token (`~/.kaggle/access_token` or `KAGGLE_API_TOKEN`), not the old username+key `kaggle.json` the original stub assumed — the docs and loader are now correct.
- **Real download, real licence discovered:** Community Data License Agreement – Sharing – v1.0, shown directly in the CLI output. This was "unverified" before — now confirmed, and it's permissive enough for our research/backtesting use (share-alike only bites if we redistribute a derivative dataset, which we don't).
- The dataset is much richer than the earlier stub assumed: `raceform.csv` (1,851,285 rows, 2015–2026, 37 columns) is the main file, but there's also Betfair data, BHA ratings, and daily racecards folders — only `raceform.csv` loaded so far, noted for later.
- **Rewrote `scripts/load_kaggle_historical.py` from scratch** — the old version was a stub against a guessed schema; this one is real, tested against the real CSV headers, and actually run to completion.
- **Real bug found and fixed live:** the CSV's missing-value marker isn't consistent (en-dash, hyphen, or empty, inconsistently) — crashed a naive `float()` at row ~1.2M. Fixed with `safe_float`/`safe_int` helpers that return `None` for anything unparseable rather than guess or crash. This is now the pattern to reuse for any future messy-CSV parsing in this project.
- **558,370 real runner results loaded** (2023-01-01 onward — full file goes back to 2015, re-run with an earlier start date to backfill more), **57,267 real races**, across 1,241 distinct racing days. Spot-checked: real winners, real starting prices, fractional odds correctly converted to decimal (e.g. `11/4F` → 3.75).
- Every loaded row's `observed_at`/`available_at` is set to the race's real off-time, not "today" — this is genuine backdated historical data, correctly timestamped, not data pretending to be more recent than it is.
- `docs/FREE_DATA_SOURCES.md` #2 fully rewritten with the confirmed real details (was previously full of "unverified"/"not yet checked" caveats — now all resolved).
- Full test suite re-run: 80/80 pass (the loader itself has no unit tests yet — it's a one-shot ETL script, not library code other things import — but its output was verified via real DB queries, not assumed).

**What this unblocks for the next session:** Phase 6 (first real model) can now be built and **genuinely walk-forward validated against 558K real historical results** — this is the actual milestone the whole "own historical database" section of the build brief (Section 5/6) was aiming for. There's finally enough real data to do this properly, not against synthetic fixtures.

**What's still blocked:**
1. Betfair Delayed App Key — the only remaining real gap, for Phase 4's market baseline (real odds)
2. Racing API's own results — still needs their Basic tier; not pursuing since Kaggle now covers this need for free

**Suggested next step:** Phase 6 — build the first real statistical baseline model, trained/validated via `src/validation/walk_forward.py` against the 558K real Kaggle results now sitting in `runner_result`. This is the first point the project can honestly say a model has been tested against real outcomes.

---

## 2026-09-08 — Session 7 (autonomous overnight, cloud routine)

**Confirmed the credential boundary first, as instructed:** `env | grep THERACINGAPI` (and
`env | grep -iE "racing|kaggle|betfair"` more broadly) returned nothing in this container —
only `CCR_ENABLE_TRACING=true`. This cloud routine still does **not** have
`THERACINGAPI_USERNAME`/`THERACINGAPI_PASSWORD`, and — new check this session — does not have
Kaggle credentials either. Did **not** attempt `scripts/collect_racecards.py` or
`scripts/collect_weather.py`. Also confirmed the real 558,370-row Kaggle dataset Session 6
loaded lives only in Postgres on Jonathan's own Mac — it is not a file in this repo (checked:
no `data/` directory, nothing under `db/` but the schema/init script) and there is no dump of it
committed anywhere, so this cloud environment cannot see or reproduce it. **Racecard/weather
collection, and now also the real Kaggle historical dataset, all stay Mac-only** until a future
session confirms otherwise in this file.

**Found Phase 6's starting task already done:** this session's instructions asked for "a simple
statistical/logistic baseline model... built and tested against realistic synthetic fixtures
shaped exactly like the real racecard schema." That's `src/models/model1_logistic_baseline.py`
+ `tests/test_model1_logistic_baseline.py`, built in Session 5 (autonomous overnight) — already
using exactly the real field shapes from `tests/test_racecard_theracingapi.py`
(`official_rating` as int, `draw` as int, `recent_form` as `'1582F3'`-style), already labelled
clearly as not-a-real-prediction, already softmax-normalised to sum to ~1.0 per race. Rather than
duplicate it, verified it's still solid (it is — all 80 pre-existing tests passed unchanged)
and picked up the concrete, still-open gap Session 5's own RL-006 entry flagged for review:
missing `official_rating` was silently scored identically to a genuinely average rating (both
got `rating_edge=0.0`), so a debutant-shaped runner was indistinguishable from an average one.

**What's genuinely done and verified this session (all real code, all with real passing
tests — 81/81 tests pass via `python3 -m pytest tests/ -v`, up from 80):**
- `src/models/model1_logistic_baseline.py` — added a fifth feature, `no_rating_flag` (1.0 when
  `official_rating` is missing, 0.0 otherwise), with its own separately-fitted weight, alongside
  the existing four (`rating_edge`, `draw_edge`, `form_edge`, `weight_edge`). This directly
  addresses the exact gap Session 5's RL-006 entry named: "a horse with no official rating is
  very likely a first-time-out debutant, which is not 'average'." Still fully synthetic — no
  claim is made about real debutants, only that the model *can now represent* the distinction
  and let a fitted weight decide its sign, same discipline every other feature in this module
  already follows.
- `tests/test_model1_logistic_baseline.py` — updated the existing feature-shape and
  hand-verified gradient-step tests for the new 5th key, and added
  `test_fit_recovers_debutant_signal_sign`: a convergence check (same style as Session 5's
  `test_fit_recovers_rating_signal_sign`) using two featurally-identical "regular" runners
  (so their four other features cancel out via an alternating winner) against one runner with
  nothing known at all. Confirms gradient ascent recovers a NEGATIVE `no_rating_flag` weight
  when the debutant-shaped runner never wins across 20 synthetic races, that the two identical
  regular runners' weights never move off zero (nothing else distinguishes them), and that the
  fitted model then rates the debutant-shaped runner below uniform on a held-out race while the
  two regular runners stay exactly tied.
- `docs/RESEARCH_LAB.md` RL-006 — updated: five features now, not four; the design-choice
  paragraph marked partially addressed (Session 7) rather than still fully open; noted Session
  6's real Kaggle data explicitly, and that it changes nothing for this cloud environment (still
  no access to it) but does mean Model 1's actual real-data training/validation is now genuinely
  ready to attempt — as Mac-only work.
- Full test suite re-run and confirmed green: `./db/setup_local_postgres.sh && python3
  db/init_db.py` (fresh container, as every prior autonomous session has needed) then
  `python3 -m pytest tests/ -v` → **81/81 passed**, including the DB-backed `tests/test_leakage.py`
  tests against a freshly bootstrapped local Postgres in this container.

**What's still blocked (unchanged from Session 6):**
1. Betfair Delayed App Key — the only remaining real gap, for Phase 4's market baseline (real
   odds)
2. Racing API's own results — still needs their Basic tier; not pursuing since Kaggle covers
   this need for free

**What the next session should do, in priority order:**
1. **Check for new credentials as always** — `env | grep -iE "racing|kaggle|betfair"`, recent
   commits, this file. Racecard/weather collection AND the real Kaggle historical dataset are
   both Mac-only right now; don't re-derive that, move straight to item 2 if still true.
2. **The single highest-leverage next step is genuinely training Model 1 against the real 558K
   Kaggle results**, per Session 6's own suggestion — but this needs Jonathan's Mac (the local
   Postgres holding that data, plus a walk-forward split over real chronological race dates via
   `src/validation/walk_forward.py`, scored via `src/evaluation/calibration.py`). This is the
   first point the project could honestly report a real Brier/log-loss score for either Model 0
   or Model 1. Not achievable from this cloud routine — flag it plainly rather than manufacture
   more synthetic-only scaffolding to avoid saying so.
3. If still cloud-only and blocked on real data (as expected): there is very little synthetic
   plumbing left worth building blind. Worth considering: (a) an `odds_betfair.py` provider stub
   against Betfair's public Exchange API docs (flagged as not written yet since Session 5); (b) a
   second Model 1 variant/hyperparameter comparison on the SAME synthetic fixture, to confirm
   fitting stability — still not a real benchmark; (c) revisit whether any other Section in
   `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` has a synthetic-only-buildable piece not yet touched.
   Be honest in the next summary if nothing genuinely useful remains rather than inventing work.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session — add a new dated section above this
   instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not attempt `scripts/collect_racecards.py`, `scripts/collect_weather.py`, or
  `scripts/load_kaggle_historical.py` from this cloud routine environment — no credentials here,
  confirmed again this session, will fail
- Do not present Model 1's synthetic-fixture test results as evidence it predicts real racing
- Do not skip re-running the full test suite before committing — all 81 tests must actually
  pass, not just the new ones

---

## 2026-09-08 — Session 8 (interactive, Jonathan's own machine)

**Phase 6 done: Model 1 has now genuinely been fit and walk-forward validated against real outcomes — the first real predictive-power test anywhere in this project.**

**What's genuinely done and verified:**
- New `scripts/train_model1.py`: loads real (race, runner_snapshot, runner_result) joined rows from the DB, builds `RunnerFeatureInput`/`TrainingRace` objects, splits chronologically via `walk_forward_splits()` (expanding window, min_train_days=180, test_window_days=60), fits `fit_logistic_baseline()` on each training fold, scores the held-out fold with `brier_score`/`log_loss`/`calibration_curve`. Also builds real `RaceRecord`/`RunnerOdds` objects from the Kaggle-sourced starting prices to run Model 0 (market baseline) through the identical harness for a real, apples-to-apples comparison — this is the first time Model 0 has been evaluated against real odds too, not just synthetic ones.
- **Real result:** 18 walk-forward folds, 2023-06 to 2026-06, ~487K real runner predictions. Model 1 lost to Model 0 on Brier score and log loss on every single fold. Pooled: Model 1 Brier=0.0896/LogLoss=0.3199 vs. Model 0 Brier=0.0795/LogLoss=0.2738. Full detail in `docs/RESEARCH_LAB.md` RL-005/RL-006.
- Model 1's calibration is genuinely good (predicted probability tracks real win rate closely across every bin with meaningful volume) — it isn't overconfident or broken, it's just not as informative as the market yet.
- **Real gap found:** the Kaggle CSV has no `recent_form`/`days_since_last_run` columns at all (checked the raw header directly) — `form_edge` has been running on zero real signal, i.e. Model 1's real test so far used effectively three working features, not four. Logged as RL-007: building a real form feature means deriving it from each horse's own prior rows in the same dataset (leakage-safe — strictly earlier dates only), not loading a column that doesn't exist. This is the natural next thing to build before drawing a final verdict on Model 1's feature shape.
- Updated `src/models/model1_logistic_baseline.py`'s docstring to reflect the real result (previously said "still NOT a real prediction" — now says plainly that it's been tested and didn't beat the market yet, without overclaiming past what was actually shown).
- **Process note, not a data problem:** three earlier attempts at this run were killed partway through by something outside my control (not a script bug — the DB query and gradient-ascent fitting were both working correctly each time, confirmed by comparing partial output across runs, which matched to 3-4 decimal places). Fixed by cutting per-run cost (test_window_days 30→60, gradient-ascent iterations 500→150 — four parameters converge well before 500 iterations) so a full run finishes in about a minute instead of tens of minutes, rather than relying on being able to run long jobs uninterrupted. `scripts/train_model1.py` accepts iteration/window-size overrides as CLI args if a future run needs to trade cost for precision.
- Full test suite re-run: 80/80 pass at the time this session's real run happened (before merging Session 7's cloud commit); 81/81 pass after merging — `train_model1.py` is a one-shot analysis script, not library code, so this session added no new tests; its output was verified via the real run, not assumed.

**What this means for the project honestly:** the "complicated system does not automatically win" principle (Section 39) held on its very first real test — Model 1 lost to the dumb market baseline. That's a legitimate, useful result, not a failed session. The market is genuinely hard to beat with four simple features, one of which wasn't even working. The next real step is deriving a genuine form feature from the Kaggle history and re-running before concluding anything final about whether this feature shape can ever add value.

**What's still blocked:**
1. Betfair Delayed App Key — still the only remaining real market-data gap (Phase 4); not urgent since Kaggle's starting prices already gave a real Model 0 comparison this session
2. Racing API's own results — still needs their Basic tier; not pursuing, Kaggle covers this need

**Suggested next step:** Build a real, leakage-safe recent-form feature derived from each horse's own prior Kaggle rows (RL-007), then re-run `scripts/train_model1.py` and see whether a genuinely complete feature set changes the RL-006 result.

**Merge note:** while this session was running, the cloud routine (Session 7 above) independently pushed a 5th Model 1 feature, `no_rating_flag`. `train_model1.py` doesn't hardcode feature names (it iterates `FEATURE_NAMES`), so it will pick the new feature up automatically on its next run — but the real result above was produced against the 4-feature model, before that merge. It has NOT yet been re-run with `no_rating_flag` included. Genuinely re-running against the merged 5-feature model, alongside the RL-007 form fix, is the real next step — not treating this result as final.

---

## 2026-09-08 — Session 9 (interactive, Jonathan's own machine)

**Closed out both open threads from Session 8: real form feature built, and the full merged 5-feature Model 1 re-run to completion.**

**What's genuinely done and verified:**
- New `scripts/derive_recent_form.py` — a one-shot backfill (not part of the live daily collector) that builds real, leakage-safe `recent_form`/`days_since_last_run` for every Kaggle-loaded `runner_snapshot` row, by walking each horse's own prior rows in chronological order and using only its strictly-earlier races. Non-completion codes (UR, PU, etc.) taken from `runner_result.result_note`. **481,186 of 558,866 rows updated** (the remainder are each horse's first appearance in the dataset — left NULL honestly, never guessed).
- Spot-checked against a real horse's ("Pay The Piper (IRE)") full race history: derived form strings (e.g. `431258U`) and non-completion codes matched the actual result sequence exactly, and `days_since_last_run` matched real calendar gaps between races.
- Re-ran `scripts/train_model1.py` against the merged 5-feature model (`no_rating_flag` from the cloud routine's Session 7 + the new real form) for the first genuinely complete, confound-free test of RL-006's hypothesis. **Result: Model 1 improved — pooled Brier 0.0896 → 0.0875, closing the gap to Model 0 from 0.0101 to 0.0080 — but still did not beat the market baseline (0.0795) on any of the 18 folds.** Calibration held up and gained resolution (more predictions in the 0.2-0.7 bins where form/rating actually differentiate runners).
- Updated `docs/RESEARCH_LAB.md` RL-006 (real result superseding the earlier incomplete one) and RL-007 (marked DONE) with the real numbers.
- Full test suite: 81/81 pass (unchanged — both new scripts are one-shot analysis/ETL, not library code).

**What this means honestly:** the confound is gone, the test is now fair, and the market still wins. This isn't a failed session — RL-006 now has a clean, trustworthy answer instead of a caveated one. Chasing further tuning of this exact 4-original-plus-1 feature shape isn't likely to close an 0.008 Brier gap against a market that prices in far more information than five race-relative stats. The next real lever is a different model class (Model 2 / gradient boosting, per the build brief's Phase 7) or genuinely new information (course/distance-specific draw bias per RL-004, weather per RL-001), not another pass at Model 1's current features.

**What's still blocked:**
1. Betfair Delayed App Key — the only remaining real market-data gap (Phase 4)
2. Racing API's own results — still needs their Basic tier; not pursuing, Kaggle covers this need

**Suggested next step:** Phase 7 — build Model 2 (gradient boosting) against the same real walk-forward harness now proven out end-to-end, or add a genuinely new feature (course/distance draw bias, weather) to Model 1 before concluding this feature family is exhausted.

---

## 2026-09-09 — Session 10 (interactive, Jonathan's own machine)

**Phase 7 done: Model 2 (gradient boosting) built, tested, and real-walk-forward-validated against the same real Kaggle data and same folds as Model 1, per the standing suggestion at the end of Session 9.**

**What's genuinely done and verified:**
- Added `scikit-learn`/`numpy` to `requirements.txt` (installed, `sklearn 1.9.0`) — genuinely justified now, unlike Model 1's deliberate pure-Python choice: reimplementing boosted-tree splitting well isn't a good use of time for 5 features. See `src/models/model2_gradient_boosting.py`'s module docstring for the full reasoning.
- `src/models/model2_gradient_boosting.py` — Model 2, `HistGradientBoostingClassifier` over the exact same 5-feature race-relative set as Model 1 (`build_race_features`, unchanged, imported directly), so any accuracy difference is attributable to model class alone. Framed as per-runner binary win/lose classification (no native race-grouped-choice objective in sklearn's GBM), raw probabilities renormalised to sum to 1.0 per race via `_renormalise_race` (falls back to uniform if every runner scores exactly 0.0, same honesty pattern as Model 1's untrained case).
- `tests/test_model2_gradient_boosting.py` — 8 tests: renormalisation (including the all-zero fallback), empty-race-list/single-class-target/bad-winner-id error handling, sums-to-1/range checks, and a synthetic rating-determines-winner convergence check mirroring Model 1's own.
- **Fixed 4 pre-existing, unrelated test failures found while running the full suite:** `tests/test_racecard_theracingapi.py`'s fixture was hardcoded to `date(2026, 9, 8)` and the provider validates `for_date` against `date.today()` — those tests silently broke the day after they were written, purely from calendar drift (today is 2026-09-09 now), nothing to do with the provider itself. Fixed by freezing `date.today()` to the fixture's own date via a small `_FrozenDate` subclass patched alongside the existing `requests.get` mock, rather than hardcoding a day that will expire again. Full suite: **89/89 pass** (was 81, +8 new Model 2 tests).
- `scripts/train_model2.py` — new, real, walk-forward trains Model 2 and scores it against Model 0 AND Model 1 on identical folds (reuses `scripts/train_model1.py`'s `load_races`, imported as a module — no duplicated loader logic).
- **Real result** (min_train_days=180, test_window_days=120, max_iter=50 — cheaper settings than Model 1's run because a first attempt at the default test_window_days=60/max_iter=150 took >16 min wall-clock across ~50 CPU-minutes and had to be killed/rerun; the process note below explains why): 9 walk-forward folds, 2023-06 to 2026-06, ~487K real runner predictions, identical data/folds to Model 1's real test. **Model 2 pooled Brier=0.0873/LogLoss=0.3086 — beat Model 1 (0.0875/0.3097) on pooled Brier and on 8 of 9 individual folds, a small but consistent and genuine improvement — but did NOT beat Model 0** (market baseline, 0.0795/0.2738) on any fold. The gap to the market barely moved (0.0078 vs Model 1's 0.0080). Full detail and interpretation in `docs/RESEARCH_LAB.md` RL-008.
- **Process note:** the first real training attempt (default `test_window_days=60`, `max_iter=150`) ran for 15m52s wall-clock (confirmed after the fact via `time`) but produced ZERO stdout before being killed — Python fully buffers stdout when piped through `tee` (not line-buffered like a real terminal), so all of that run's output was lost when it was killed just as (it turned out) it had actually finished. Rerun with `python3 -u` (unbuffered) and a background shell job so output streamed to a log file in real time — this is the fix for any future long-running script in this repo: always use `python3 -u ... > logfile 2>&1 &`-style unbuffered background execution, never `| tee` for a long job you might need to check on or kill mid-run.
- `docs/RESEARCH_LAB.md` — new entry RL-008 with the full real result and honest interpretation (model class alone barely moves the market gap; the bottleneck is the feature set, not the model).
- Full test suite re-run and green: `python3 -m pytest tests/ -v` → **89/89 passed**.

**What this means honestly:** Section 39's "complicated system does not automatically win" held for a second time — a materially more complex model (gradient boosting vs. logistic regression), same 5 features, still lost clearly to the dumb market baseline, though it did edge out Model 1. This is real evidence the bottleneck right now is the FEATURE set (5 race-relative stats, no market/price signal, no course/distance-specific draw bias, no weather), not the model class — Model 1 already showed simple beats complex isn't guaranteed to reverse just by adding model complexity. Chasing a third model class on this same input isn't the promising next step; richer features are.

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — real market prices (Phase 4)
2. Racing API's own results — still needs their Basic tier; not pursuing, Kaggle covers this need

**What the next session should do, in priority order:**
1. **Check for new credentials as always** — env vars, recent commits, this file.
2. **The real next lever, per RL-008's own conclusion, is richer features, not another model class:** course/distance-specific draw bias (RL-004 — the Kaggle `raceform.csv` has `course`/`distance` columns, real historical draw-position-vs-finish data is derivable the same way `derive_recent_form.py` derived form), or a weather-interaction feature (RL-001 — `weather_snapshot` table already has live Open-Meteo data, though it's only been collecting since Session 1/2026-09-08 so historical coverage is thin; the Kaggle data has no weather column, worth checking before assuming this is buildable against the historical set at all).
3. Consider a Model 2 hyperparameter sweep (max_depth/learning_rate/max_iter) only if richer features are exhausted first — RL-008 explicitly recommends against tuning this same 5-feature input further before that.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB (Mac sessions probably don't need it if Postgres is already running locally, but cloud/fresh-container sessions always will).
5. **Always run a long script (>~2 min expected) unbuffered and backgrounded to a real log file** (`python3 -u script.py > logfile 2>&1 &`), never `| tee` in the foreground — see this session's process note above for why that lost a full 16-minute run's output.
6. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not present Model 2's result as anything other than what it is: beats Model 1 narrowly, still loses to the market
- Do not skip re-running the full test suite before committing — all 89 tests must actually pass, not just the new ones

---

## 2026-09-09 — Session 10 continued (interactive, Jonathan's own machine): real draw-bias feature, and a real bug found+fixed along the way

**Built RL-004's real course/distance draw-bias feature, per Session 10's own standing next-step recommendation, and found a genuine pre-existing data bug while testing it honestly rather than trusting a suspiciously flat result.**

**What's genuinely done and verified:**
- `src/features/draw_bias_history.py` — new module, real (course, distance-band, draw-tercile) → historical win-rate table (`build_draw_bias_table`) with a `min_sample_size=30` floor per bucket, and `draw_bias_edge()` (tercile win rate vs. naive uniform expectation, 0.0 "no evidence" for anything below the sample floor or with missing inputs). `tests/test_draw_bias_history.py` — 11 tests.
- Wired as a 6th feature (`draw_bias_edge`) into the SHARED `build_race_features()` in `src/models/model1_logistic_baseline.py` (used by both Model 1 and Model 2), leakage-safe by construction: `scripts/train_model1.py::build_split_draw_bias_table()` rebuilds the table fresh from each walk-forward split's TRAINING races only, threaded through `fit_logistic_baseline`/`fit_gradient_boosting`/both `predict_race_probabilities` functions via new optional `draw_bias_table`/`course_id`/`distance_yards` params (all backward-compatible — every existing call site with no new args still behaves exactly as before). 3 new tests across `tests/test_model1_logistic_baseline.py` and `tests/test_model2_gradient_boosting.py`.
- **Real bug found and fixed:** the first real training run with the new feature came back with the pooled Brier score essentially IDENTICAL to before the feature existed (Model 1 0.0875, Model 2 0.0873, to 4 decimal places) — suspicious enough on its own that a genuinely new, real feature moved nothing, so it was sanity-checked before being written up as a null result. `build_split_draw_bias_table()` on a real training fold returned **0 table entries**. Root cause: `race.distance_yards IS NULL` for **all 57,267** Kaggle-loaded races — `scripts/load_kaggle_historical.py` (Session 6) never parsed the CSV's `dist` column (e.g. `'2m3½f'`, `'6f'`) into it at all, a genuine silent gap, same shape as RL-007's missing form column.
- **`scripts/backfill_race_distance.py`** — new, real, one-shot backfill. Parses the CSV's `dist` strings (miles/furlongs/half-furlongs) to whole yards, joins back to `race.external_ref` (which stores the CSV's own `race_id`). `tests/test_backfill_race_distance.py` — 6 unit tests on the parser, plus verified against **all 63 real distinct `dist` values actually in the CSV** (zero unparsed) before running for real. **Ran for real: 57,267 of 57,267 races backfilled with a real distance, 0 left NULL.** Re-verified the draw-bias table now genuinely populates: 438 real buckets on the first fold alone (was 0).
- **Real result, feature now genuinely working (`scripts/train_model2.py`, same 9 real walk-forward folds, 2023-06 to 2026-06, ~487k predictions):** pooled Brier still barely moved — Model 1 0.0875 (unchanged), Model 2 0.0874 (was 0.0873, a noise-level move in the wrong direction). **This is now a genuine, trustworthy null result** — the bug is confirmed fixed and the feature confirmed populated (438+ real buckets, not 0), not silently inert. Course/distance draw bias, as implemented (220-yard bands, draw-tercile buckets, min 30 real samples), does not currently help either model. Full detail in `docs/RESEARCH_LAB.md` RL-004 and RL-008's update.
- `docs/RESEARCH_LAB.md` — RL-004 rewritten with the real implementation, the bug, the fix, and the real (null) result; RL-008 updated with the same numbers.
- Full test suite re-run and green throughout: **109/109 pass** (was 89 at the start of this continuation: +11 draw_bias_history, +2 model1, +1 model2, +6 backfill parser = 109).

**What this means honestly:** two "richer feature" attempts now (real form derivation, RL-007/RL-006; real course/distance draw bias, RL-004) have both been genuinely tested against real data and both made only marginal-to-zero difference. This is real, useful negative evidence — it's not that "adding real features" is inherently the fix; the two most obvious candidates from the build brief's own feature list are largely exhausted. The process lesson matters as much as the modelling one: a real feature that changes nothing is worth a sanity check before being written up, exactly the discipline that caught this bug — trust a suspiciously-unchanged result enough to verify it, not enough to accept it.

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — real market prices (Phase 4)
2. Racing API's own results — still needs their Basic tier; not pursuing, Kaggle covers this need

**What the next session should do, in priority order:**
1. Check for new credentials as always.
2. **Weather (RL-001) or genuine price-movement features remain the only untried "richer feature" candidates** — `weather_snapshot` has live Open-Meteo data only since 2026-09-08, so historical coverage for backtesting is thin; check real coverage before assuming it's usable against the 2023-2026 Kaggle set. Price movement (`src/market/movement.py`, already built and tested) needs real historical odds time series, not just a single starting price — the Kaggle data only has one SP per horse, not a movement history, so this may itself be blocked pending Betfair.
3. Consider whether finer draw-bias bucketing (exact distance instead of 220-yard bands, or splitting by going/surface) is worth a quick re-test before concluding RL-004 is fully exhausted — flagged as a real possibility in RL-004's own write-up, not done this session, low priority given the pattern of gains being small even when features work correctly.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. **Always run a long script unbuffered and backgrounded to a real log file**, never `| tee` in the foreground.
6. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not present the draw-bias null result as if the feature is broken (it is now confirmed correctly implemented and populated) or as if course/distance draw bias definitely doesn't exist in reality — only that this particular implementation, honestly tested, didn't help these two models
- Do not skip re-running the full test suite before committing — all 109 tests must actually pass

---

## 2026-09-09 — Session 10 continued: RL-001 reframed weather→going, real course coordinates, and a genuine "feature hurt Model 2" result

**Investigated weather's real historical coverage (asked directly), found a structural problem, and reframed the feature before building it — per the standing "check before building" discipline.**

**What's genuinely done and verified:**
- **Weather coverage check:** `weather_snapshot` had only 13 real rows (a single date, 2026-09-08) and used Open-Meteo's *forecast* endpoint, not history. Confirmed live that Open-Meteo's free historical *archive* endpoint works and covers the full 2023-2026 window — but only 13 of 412 courses had real coordinates (8% of real GB races). Live-checked The Racing API's free `/v1/courses` too — no coordinates there either.
- **Real course coordinates gathered:** all 59 current British racecourses (Wikipedia's own `{{coord}}` geodata via a live, batched MediaWiki API call for 53; web search against verified sources for the remaining 6). `data/gb_racecourse_coordinates.py`, `scripts/backfill_gb_course_coordinates.py`, 7 tests (incl. a real GB bounding-box sanity check on all 59 coordinates). Ran for real: GB race coordinate coverage since 2023 went from 8% to **59.5%** (34,136 of 57,326 races). Deliberately GB-only, matching the project's own stated Phase 1 scope (the Kaggle set also has ~200 non-GB course names).
- **Structural finding before building further (this mattered):** weather (or any race-level constant) is mathematically INVISIBLE to both Model 1's softmax and Model 2's per-race renormalisation — a value identical for every runner in a race cancels out completely regardless of its weight. Flagged this to Jonathan before building anything further rather than producing a result guaranteed-null by construction.
- **Reframed to real going affinity:** the real dataset already records the actual ground `going` (Good/Soft/Heavy/etc.) per historical race — direct ground truth, no weather API needed for backtesting. Built `src/features/going_affinity.py`: per-horse `soft_ground_affinity` from real strictly-past completed runs (min 2 runs each side of a turf/AW going scale, else excluded), times a +1/-1 today's-going indicator — a genuine per-RUNNER-varying interaction term, unlike bare going/weather. 15 tests. Wired as a 7th feature (`going_affinity_edge`) into the shared `build_race_features()` used by both models, leakage-safe (table rebuilt fresh per walk-forward split's training races). 2 more wiring tests in `test_model1_logistic_baseline.py`. Full suite: **133/133 pass**.
- Sanity-checked the table populates for real before trusting the training run (2,469 real horses in the first fold alone, mean |affinity| ~0.20) — same discipline as the RL-004 distance_yards bug, this time confirming the feature IS firing, not silently zero.
- **Real result** (`scripts/train_model2.py`, same 9 real walk-forward folds as every prior run): Model 1 pooled Brier unchanged (0.0875). **Model 2 got measurably WORSE: 0.0878 (was 0.0874/0.0873 with fewer features) — and for the first time lost to Model 1** (0.0878 vs 0.0875). Real, not a bug: the feature only has real signal for a few thousand horses per fold (0.0 "no evidence" for the rest), and gradient boosting appears to overfit to that sparse split. Full detail in `docs/RESEARCH_LAB.md` RL-001b.

**What this means honestly:** three feature attempts now (real form, real draw bias, real going affinity) have all been genuinely tested. Two ~no difference, one measurably hurt Model 2. This repo's current 7-feature race-relative shape looks genuinely exhausted with either model class tried so far. The remaining untried lever is a different KIND of information (real price-movement data), not another feature on this same input shape — and that needs Betfair, still blocked on Jonathan.

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — the only remaining real, novel-information gap
2. Racing API's own results — still needs their Basic tier; not pursuing, Kaggle covers this need

**What the next session should do, in priority order:**
1. Check for new credentials as always.
2. **Consider dropping `going_affinity_edge` from Model 2's feature set** (or gating it behind a minimum per-horse sample size stricter than the current min_runs_per_side=2) given it measurably hurt Model 2's real result — this is a genuine candidate for reverting/tuning, not just leaving in because it's built. Not done this session; flagging honestly rather than deciding unilaterally.
3. Real price-movement features (`src/market/movement.py`, already built/tested) are the one remaining untried, genuinely-new-information lever — but need a real odds TIME SERIES per horse, not the single Kaggle starting price. Blocked on Betfair.
4. There is very little "another feature on the same 7-column shape" scaffolding left worth building blind — three attempts have now been made and none helped. Say this plainly rather than manufacturing a 4th if nothing genuinely new is available.
5. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
6. **Always run a long script unbuffered and backgrounded to a real log file**, never `| tee` in the foreground.
7. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not add a race-level-constant feature (weather, going, anything not runner-varying) directly to either model again without first checking it survives softmax/renormalisation invariance — see this session's structural finding
- Do not skip re-running the full test suite before committing — all 133 tests must actually pass

---

## 2026-09-09 — Session 10 continued: reverted going_affinity_edge from the active feature set

**Jonathan asked for a recommendation on the going-affinity regression; agreed it should come out of both models, not just Model 2** — reasoning: (1) it hurts Model 2, does nothing for Model 1, no case for keeping it in either; (2) more importantly, Model 1 vs Model 2 is only a valid comparison (RL-008's own design) if they're scored on the SAME feature set — stripping it from only one model would break that going forward.

**What's genuinely done:**
- `src/models/model1_logistic_baseline.py`: `going_affinity_edge` removed from `FEATURE_NAMES` (the active scoring/fitting set) but kept fully computed in `build_race_features()` — added `ALL_COMPUTED_FEATURE_NAMES = FEATURE_NAMES + ("going_affinity_edge",)` so the real, tested plumbing (`src/features/going_affinity.py`, leakage-safe table-building, wiring through both models' fit/predict) stays intact and is a one-line re-add if future evidence changes the conclusion, rather than being ripped out and lost.
- `tests/test_model1_logistic_baseline.py` updated to assert against `ALL_COMPUTED_FEATURE_NAMES` where checking the raw per-runner dict shape, `FEATURE_NAMES` where checking what's actually scored — 133/133 tests still pass.
- **Real confirmation re-run** (`scripts/train_model2.py`, same 9 folds): pooled Brier now EXACTLY matches the known-good pre-going-affinity numbers — Model 2 0.0874, Model 1 0.0875 (both unchanged to 4dp), Model 0 0.0795, and Model 2 beats Model 1 again. The revert works cleanly, no partial/stale state.
- `docs/RESEARCH_LAB.md` RL-001b updated: status now records the revert and why, explicitly pointing at the one-line re-enable path.

**What this means:** the pipeline is back to its known-good 6-feature (rating/draw/form/weight/no_rating_flag/draw_bias) shape for both models, with going-affinity's real code sitting ready but inactive. Three real feature attempts (form, draw bias, going affinity) are now settled: two neutral (kept), one net-negative (reverted). Nothing left to try on this feature shape without genuinely new information.

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — the only remaining real, novel-information lever
2. Racing API's own results — still needs their Basic tier; not pursuing, Kaggle covers this need

**What the next session should do, in priority order:**
1. Check for new credentials as always.
2. Real price-movement features remain the one untried, genuinely-new-information lever — blocked on Betfair. Consider raising this with Jonathan directly rather than continuing to flag it passively each session.
3. There is no further "another feature on the same input shape" scaffolding worth building blind — say this plainly rather than manufacturing a 4th attempt.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. **Always run a long script unbuffered and backgrounded to a real log file**, never `| tee` in the foreground.
6. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not re-enable `going_affinity_edge` in `FEATURE_NAMES` without new evidence (more data, a stricter sample threshold) — the current real result against it stands
- Do not skip re-running the full test suite before committing — all 133 tests must actually pass

---

## 2026-09-09 — Session 10 continued: Betfair blocked on account verification; Phase 8 (live daily predictions) built and run for real instead

**Betfair status:** Jonathan created the developer app (Delayed App Key `NslD2mUCstNkchTv`, Application Id 176692) and completed identity verification, but the account still returns `LIMITED_ACCESS`/`SUSPENDED` on a real session-login call as of this session's last check. Credentials are in `.env` (gitignored). **Do not keep retrying the login endpoint blind** — Betfair may lock the account after repeated failed/restricted attempts; wait for Jonathan to confirm the account shows clear on their site, or hears back from their support, before testing again.

**Moved to the next real, unblocked piece of work: Phase 8, the live daily prediction pipeline** — everything up to now only ever backtested against real PAST results; this is the first script that predicts races that haven't happened yet.

**What's genuinely done and verified:**
- `scripts/predict_todays_races.py` — new, real. Fits Model 1 and Model 2 fresh on ALL real historical results strictly before the target date (no leakage: the historical loader inner-joins `runner_result`, so today's un-resulted races are automatically excluded, not filtered out by a special case), loads today's real racecard (`race`/`runner_snapshot`, already being collected daily at 07:00 by the existing LaunchAgent), predicts every race with >=2 runners through both models, and inserts into the `prediction` table — a table the schema already anticipated (Section 32's immutable ledger) but nothing had used until now.
- Real `model_version` rows created (`statistical_v1`/`gbm_v1`, both v1.0, `6-feature-v1` — the real active feature set after the going_affinity revert).
- Every inserted row is locked immediately (`locked_at` set at insert, `record_hash` = real SHA-256 of the defining fields) — **verified for real, not just asserted**: a direct `UPDATE` against a locked row was rejected by the DB's own trigger (`trg_prevent_locked_prediction_update`), and a full re-run of the script correctly skipped every already-predicted race/model pair rather than duplicating or overwriting (idempotency check, real: 0 newly predicted on the second run, all 60 race/model pairs correctly skipped).
- `tests/test_predict_todays_races.py` — 3 real tests on the pure `record_hash` function (determinism, sensitivity to every field, real SHA-256 shape). The rest of the script is real DB-integration code, exercised by actually running it, same discipline as `train_model1.py`/`backfill_race_distance.py`.
- **Real run, 2026-09-09:** fit on 57,151 real historical races, predicted **30 real races today** (Redcar/Sedgefield/Carlisle/Kempton AW), 632 real locked prediction rows (316 per model). `market_probability`/`fair_odds`/edges left honestly NULL — no odds source is unblocked yet (Racing API free tier has none, Betfair still blocked) — fillable the moment either unblocks, not guessed now.
- Full suite: **136/136 pass** (was 133, +3 new).

**What this means:** the project now has a genuine, real, immutable prediction ledger accumulating day by day — the first real building block for eventually checking calibration/Brier score against LIVE outcomes (not just historical backtests) once results collection is built (still a real gap — The Racing API's results endpoint needs their Basic tier, not pursued; Kaggle's dataset lags real-time by design). Running this daily (easy to LaunchAgent-schedule alongside the existing racecard collector) starts building that real track record now, cheaply, while Betfair unblocks.

**What's still blocked:**
1. Betfair — account verification done, but still SUSPENDED on a real login test; waiting on Jonathan/Betfair support
2. Racing API's own results — still needs their Basic tier; Kaggle covers historical backtesting but not live results
3. **New gap surfaced by this session's work:** there's no real results collection for TODAY's races once they've run — `predict_todays_races.py` predicts before the fact, but nothing yet closes the loop by fetching real outcomes for a past race day and scoring the locked predictions against them. Worth a `scripts/collect_results.py` once a real results source unblocks (Racing API Basic tier, or scraping-permission-checked alternative).

**What the next session should do, in priority order:**
1. Check whether Betfair's account status has cleared — try ONE real login test, not a retry loop, and only if there's a concrete reason to think it's changed (Jonathan confirms, or enough time has passed).
2. **Set up a daily LaunchAgent for `predict_todays_races.py`**, same pattern as `com.silentedgezero.collect-racecards.plist` (run shortly after racecards are collected each morning) — this is cheap, real, unblocked work that starts the live track record accumulating automatically rather than needing a manual trigger each day. Not done this session; flagged as the natural next step.
3. Once a real results source exists (Racing API Basic tier, or Betfair), build the scoring/calibration loop against the real locked predictions already accumulating.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. **Always run a long script unbuffered and backgrounded to a real log file**, never `| tee` in the foreground, for anything expected to take more than ~2 minutes.
6. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf (Betfair — already created by him, just still blocked)
- Do not retry the Betfair login endpoint repeatedly without a concrete reason to think the account status changed — real lockout risk
- Do not skip re-running the full test suite before committing — all 136 tests must actually pass

---

## 2026-09-09 — Session 10 continued: dashboard, and a real free Betfair alternative found (Smarkets)

**Built a local live-predictions dashboard**, then, since Betfair remained blocked, researched genuinely free/open-source alternatives specifically for market/price data — not results (Kaggle already covers historical results).

**What's genuinely done and verified:**
- `scripts/generate_dashboard.py` + `dashboard.html` (gitignored, regenerated fresh each run) — a real local HTML dashboard reading only already-locked `prediction` rows: every race, both models' top picks, an agree/disagree badge, and honest real backtest context (Model 0/1/2 Brier scores) so it's never presented as more validated than it is. Not a hosted Artifact — this is Jonathan's own private data, viewed locally, same pattern as this ecosystem's other Dave reports. Wired into the `predict-races` LaunchAgent chain (07:15 daily) and verified via the real scheduled path. 4 new tests on the pure rendering helpers.
- **Real research, live-verified, not assumed:** checked whether any free/open-source alternative to Betfair exists specifically for market/price-movement data. Found **Smarkets** — a genuine separate betting exchange with a real public read-only API needing **zero authentication** (confirmed live: pulled real GB race data — Doncaster, Epsom Downs, Lingfield, Warwick, Worcester — with no account, no key). Checked and ruled out Betfair's own "Historic Data" downloads (tied to the same suspended account) and every other option found (Racing Post, Sportradar, OddsMatrix) — all paid.
- **Real price semantics verified live before trusting them:** Smarkets' quotes endpoint returns prices as basis-points implied probability (10000 = 100%) — confirmed by summing a real race's full book of best-bid probabilities (78.6%, sane for a thin >24h-out back book) rather than assuming the units.
- `src/providers/odds_smarkets.py` — real provider: paginated event listing (Smarkets' own pagination uses a real `next_page` cursor, correctly followed), win-market lookup, contract+quote fetch combined into per-runner `exchange_back`/`exchange_lay`/`midprice`/`spread` (all real decimal odds, matching `market_snapshot`'s existing schema exactly). 8 tests against real captured response fixtures (same discipline as `test_racecard_theracingapi.py`).
- `scripts/collect_smarkets_prices.py` — real, matches Smarkets events to our own `race` rows by (normalised course name, off_time within 10 minutes) and runners by (country-suffix-stripped, case-insensitive horse name), skipping any race where the runner counts don't line up rather than trusting a partial match. Writes real `market_snapshot` rows (a time series by design — every run adds new rows, never overwrites). 5 tests on the pure matching logic.
- **Real, honest limitation confirmed live:** Smarkets, like Open-Meteo's forecast endpoint before it, only exposes UPCOMING markets — today's already-finished races are gone from its listings by the time this was built. So this can only build a price-movement dataset forward from now, same shape as the weather/coordinate work — it cannot backfill the 2023-2026 Kaggle window. Ran it live against both today (0 matches — races already finished) and tomorrow (0 matches — tomorrow's racecard doesn't exist in our DB until the 07:00 collector runs) to confirm the real HTTP flow runs cleanly end-to-end with no errors in both honest zero-match cases.
- New `com.silentedgezero.collect-smarkets-prices` LaunchAgent — runs every 20 minutes, all day (StartInterval, not calendar-windowed — simpler than a race-hours-only schedule and the script is cheap enough that continuous polling costs nothing real). Loaded and verified via a real manual trigger.
- Full suite: **153/153 pass** (was 136, +4 dashboard, +8 Smarkets provider, +5 Smarkets matching).

**What this means:** the project now has a real, live, free, unblocked path to price-movement data that doesn't depend on Betfair at all — but it genuinely can't produce a result until tomorrow (or later), once both (a) a real racecard exists for a given day and (b) the poller has run at least twice across that day to see a price change. Nothing to report on accuracy/movement yet — this is infrastructure, not a result.

**What's still blocked/pending:**
1. Betfair — still SUSPENDED as of last check; not retried this session (no new reason to think it's changed)
2. Racing API's own results — still needs their Basic tier
3. **New, real, and expected:** no Smarkets price-movement DATA exists yet — the collector only just started running. Check back after at least one full race day has run through both collectors.

**What the next session should do, in priority order:**
1. Check `market_snapshot` for real rows — if a race day has passed with the collector running, verify real matches happened (not just clean zero-match runs) and spot-check a few against what's plausible.
2. Once real price snapshots exist across a race's build-up, build the actual price-MOVEMENT feature (`src/market/movement.py` already exists and is tested against synthetic data — this is the first point real Smarkets data could feed it for real).
3. Check whether Betfair's account status has cleared, but only if there's a concrete reason to think so.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/price data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf
- Do not retry the Betfair login endpoint without a concrete reason to think the account status changed
- Do not treat a single Smarkets price reading as validated against a second source — only the unit interpretation (basis points) was checked, not cross-exchange accuracy
- Do not skip re-running the full test suite before committing — all 153 tests must actually pass

---

## 2026-09-09/10 — Session 10 continued: dashboard iterations, then RL-010 — the first real feature win

**Dashboard, per a long sequence of real Jonathan feedback on the built UI:** single primary model (M2) not two columns, always-visible racecard stats (not click-to-expand), races open as a popup dialog instead of a long scroll, dark mode toggle, a confidence-overview bar chart, live per-course weather (Open-Meteo, real GB coordinates), a real market-favourite chip, a deterministic (not freeform-LLM) race-analysis paragraph grounded in real feature values, a confidence line grounded in real backtested calibration, a help panel explaining OR/Form (including real BHA rating bands). All committed incrementally, each with real tests and a real regeneration against live data before committing. See commits `740befe` through `c8083f7`.

**Then a real gap analysis, then RL-010:** Jonathan asked directly what it would take to beat the market, and for a genuine "what's missing and what's it worth" analysis. Rather than guess, checked the DB directly for real unused signal first — found trainer win rates ranging 2.4%-28.6% and a similar jockey spread, over 300+ real races each, completely unused by either model.

**What's genuinely done and verified:**
- `src/features/connections_strike_rate.py` — real trainer/jockey win-rate tables (min 20 real runs), race-field-relative edges, same "never guessed, fitted weight decides sign" discipline as every prior feature. Wired into `build_race_features()` (now 8 active features + `going_affinity_edge` still computed-but-inactive = 9 total), both models' fit/predict, `scripts/train_model1.py`/`train_model2.py`/`compute_hit_rate.py`, and the live daily pipeline (`predict_todays_races.py`, model versions bumped 1.0->1.1). 9 new tests.
- **Real result — the first genuine positive result of any feature tried:** Model 2 Brier 0.0874->0.0866, hit rate 21.7%->**23.2%** (+1.5pp, the largest gain yet). Model 1 barely moved (21.5%->21.7%) — its linear structure seems less able to exploit this higher-cardinality signal than Model 2's tree splits. Still well short of the market (33.3%) but real, meaningful progress. Full detail in `docs/RESEARCH_LAB.md` RL-010.
- Sanity-checked before trusting: 765 real trainers / 600 real jockeys with genuine >=20-run table entries in the first fold alone.
- Full suite: **183/183 pass** (was 174, +9 new).

**"GC" (Jonathan's naming) — residual/miss-pattern analysis, proposed but not started:** Jonathan asked for an algorithm mining past top-picks-vs-actual-winners for a pattern that "unlocks more winners." Agreed to do this as real, disciplined residual analysis (look at genuine misses from the completed walk-forward backtests for an explainable common thread, then test any real candidate with the same walk-forward discipline as everything else — never declare a pattern "found" just because it fits the historical data that produced it, that's the textbook overfitting trap in this exact domain). Jonathan agreed to call it "GC" in the UI (short, doesn't spell out an unproven claim on the page itself) — logged here as **RL-011**, not started this session. If something real survives walk-forward testing, the plan is a dedicated "GC" tab on each race card showing its pick, same UI pattern as the existing model badges — built only once there's something real behind it, not before.

**What's still blocked (unchanged):**
1. Betfair — still SUSPENDED as of last check
2. Racing API's own results — still needs their Basic tier

**What the next session should do, in priority order:**
1. **RL-011 (the "GC" analysis)** — pull real per-race prediction-vs-outcome pairs from the completed walk-forward folds, look for a genuine, explainable pattern among confident misses, and if one survives a fresh walk-forward test, build it as a real feature (not a UI element first).
2. Check whether Betfair's account status has cleared, only if there's a concrete reason to think so.
3. Once real Smarkets price data has accumulated across a race day, build the real market-odds comparison the dashboard is already wired to show.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. **Always run a long script unbuffered and backgrounded to a real log file**, never `| tee` in the foreground.
6. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/price data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf
- Do not retry the Betfair login endpoint without a concrete reason to think the account status changed
- **Do not declare an RL-011 "GC" pattern real just because it fits the historical folds that produced it — it must be tested on real out-of-sample data via the same walk-forward harness as every other feature before being trusted or shipped**
- Do not build the "GC" race-card tab before there's a real, walk-forward-tested signal behind it
- Do not skip re-running the full test suite before committing — all 183 tests must actually pass

---

## 2026-09-10 — Session 10 continued: RL-011 "GC" investigation — real, disciplined, and rejected

**Did the residual analysis Jonathan asked for, properly:** split the 9 real walk-forward folds into a 7-fold DISCOVERY set and a 2-fold VALIDATION set the discovery step never touches, per the discipline agreed on before starting (never declare a pattern real from the same data that produced it).

**What's genuinely done and verified:**
- `scripts/analyze_residuals.py` — real discovery pass, comparing confident hits (top pick won) vs confident misses (top pick lost) across 39,518 real top-pick predictions from the 7 discovery folds. Most real differences (rating/form/trainer/jockey edges) just confirmed the existing model features already work. One field stood out as genuinely NEW and not fed to either model: **field_size**, z=-25.3 (the largest of any field), hits averaging 9.0 runners vs misses averaging 10.0.
- Recognised immediately why this can't be a bare input feature (identical for every runner in a race, invisible to per-race softmax/renormalisation — same trap as RL-001's original weather hypothesis) and reframed it correctly as a post-hoc calibration problem instead.
- `src/evaluation/temperature_scaling.py` — real, tested (9 tests) temperature-scaling implementation (power-law rescale + renormalise, real grid-search fitting by Brier score).
- `scripts/validate_field_size_calibration.py` — fits best temperature per field-size bucket using ONLY the 7 discovery folds, applies those fixed temperatures to the 2 validation folds' real predictions (never used in fitting), scores honestly before/after.
- **Real validation result: no real improvement.** Brier 0.0862->0.0861 (noise), hit rate 23.5%->23.5% (unchanged) on 10,176 real, genuinely held-out validation races. The fitted temperatures were themselves modest (0.85-1.1, close to the T=1.0 no-op) — much less dramatic than the huge discovery z-score suggested.
- Full suite: **192/192 pass** (was 183, +9 temperature-scaling tests).

**What this means honestly:** the discovery-phase field-size effect was real in the discovery data but didn't survive fresh testing — most likely because field size correlates with other things the model already partially captures, so its raw hit/miss correlation overstated its incremental value once properly isolated. This is exactly the failure mode the discovery/validation split exists to catch, and it caught it. A real, legitimate null result, not a failed session — and it means RL-010 (trainer/jockey, the one genuine gain this session) stands as the actual improvement, not diluted by a false positive getting shipped alongside it.

**No "GC" tab was built.** Nothing survived validation to put on the race card. If Jonathan wants this pursued further, the honest options are: (a) try other candidate patterns from the discovery table that weren't tested (distance_yards had a weaker but real z=3.0, untested), or (b) accept that the two real, disciplined attempts at finding a hidden edge (RL-010 trainer/jockey — worked; RL-011 field-size calibration — didn't) represent a fair, honest picture of what's findable in this data without genuinely new information sources (price movement, still pending Smarkets accumulation or Betfair).

**What's still blocked (unchanged):**
1. Betfair — still SUSPENDED as of last check
2. Racing API's own results — still needs their Basic tier
3. Real Smarkets price-movement data — infrastructure is live, no real accumulated data yet

**What the next session should do, in priority order:**
1. Check whether real Smarkets price-movement data has accumulated across a race day — this is still the most promising genuinely-new-information lever left untried.
2. If Jonathan wants more RL-011-style investigation, the distance_yards signal (z=3.0, weaker but real, untested) is the next honest candidate — same discovery/validation discipline required.
3. Check whether Betfair's account status has cleared, only if there's a concrete reason to think so.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. **Always run a long script unbuffered and backgrounded to a real log file**, never `| tee` in the foreground.
6. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/price data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf
- Do not retry the Betfair login endpoint without a concrete reason to think the account status changed
- Do not revisit the field-size calibration idea without new real validation data — the current real result against it stands
- Do not skip re-running the full test suite before committing — all 192 tests must actually pass

---

## 2026-09-10 — Session 10 continued: Netlify PATH fix, then a real Smarkets timezone bug found and fixed

**Two real bugs found and fixed, both from Jonathan noticing something was off on the live dashboard.**

**Bug 1 — Netlify deploy silently failing under launchd.** Predictions and dashboard generation succeeded at 07:15, but `netlify` (a `#!/usr/bin/env node` script) failed with `env: node: No such file or directory` — launchd's minimal PATH doesn't include nvm's node install. Fixed by exporting nvm's bin directory onto PATH in `scripts/run_predict_todays_races.sh`, verified via a real launchd-triggered run (not just a manual shell test, which already has the right PATH and wouldn't have caught this).

**Bug 2 — Smarkets price collection was matching every race to the wrong one, silently, since the collector was built.** Jonathan asked why odds weren't showing. Real investigation: `market_snapshot` had 0 rows for today despite the collector running every 20 minutes without errors. Traced it to `scripts/collect_smarkets_prices.py::match_race()` comparing Smarkets' real UTC `start_datetime` directly against our `race.off_time` (real UK LOCAL wall-clock time, confirmed by reading `racecard_theracingapi.py`'s off_time derivation) as if both were the same timezone. During BST (currently in effect, UTC+1) this is a full hour out — confirmed live: a Smarkets "Epsom 15:52" event was falsely matching our local-15:42 race (10 real minutes apart, inside the old tolerance) when the REAL same race was at local 16:52. Every match this bug DID produce was wrong, which is why every race failed the runner-name check and got skipped — the collector wasn't broken by an exception, it just never found a correct real match.

**Fixed with a real UTC->Europe/London conversion** (`zoneinfo`, stdlib, handles BST/GMT automatically) before comparing to our local off_time. Also found and fixed a second real issue while testing the recovery: a single Smarkets 429 (rate limit) used to crash the ENTIRE collection run via an unhandled exception, losing every other race's real data for that trigger too — wrapped per-race fetching in a real try/except (log + skip + back off 1s, matching the best-effort discipline already used in `fetch_course_weather`), plus a small 0.3s delay between races to reduce how often the rate limit gets hit at all.

**Real result after both fixes, verified live:** `market_snapshot` went from 0 real rows for today to **188 real price snapshots across 20 real correctly-matched races** in one run (the remaining 17 hit real 429s this run — resilient now, not fatal, they'll be picked up on a later run within the day). Dashboard regenerated and redeployed — confirmed live on `https://silent-edge-zero.netlify.app` showing real odds (e.g. "Odds 10.4", "Odds 3.8") for the first time.

**New regression tests added** (`tests/test_collect_smarkets_prices.py`) specifically reproduce the real bug: a BST-date fixture where naive UTC comparison would false-match a wrong race, and a GMT-date fixture confirming the fix doesn't break the (common, no-offset) winter case. Full suite: **195/195 pass** (was 192, +3).

**What this means:** the Smarkets integration has been silently non-functional since it was built earlier this session — a real, humbling reminder that "ran without errors" and "collector count = 0 every time" together should have been investigated sooner rather than assumed to be "just waiting for real data to accumulate." Worth remembering for future integrations: a persistent zero-match rate over multiple real runs is itself a signal worth checking, not just patience.

**What's still blocked (unchanged):**
1. Betfair — still SUSPENDED as of last check
2. Racing API's own results — still needs their Basic tier
3. Smarkets rate limiting — mitigated (no longer fatal), not eliminated; consider a longer per-race delay or fewer duplicate-event calls if 429s remain frequent

**What the next session should do, in priority order:**
1. Check `market_snapshot` accumulation across a full race day now that matching actually works — confirm price MOVEMENT (multiple snapshots per horse over time) is genuinely building, not just one-off matches.
2. Once real movement data exists across a race, build the real price-movement feature (`src/market/movement.py` already exists, tested against synthetic data only).
3. Investigate the duplicate market_id calls seen in this run's log (same race appearing to be fetched twice with different market_ids) — may reduce real API load and rate-limit frequency.
4. Check whether Betfair's account status has cleared, only if there's a concrete reason to think so.
5. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
6. **Always run a long script unbuffered and backgrounded to a real log file**, never `| tee` in the foreground.
7. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/price data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf
- Do not retry the Betfair login endpoint without a concrete reason to think the account status changed
- Do not assume a persistently-zero real collector result is "just waiting for data" without checking — verify the matching logic actually works
- Do not skip re-running the full test suite before committing — all 195 tests must actually pass

---

## 2026-09-10 — Session 10 continued: added a bet calculator, tried to check Day 1 results, found a second real match_race bug

**Bet calculator:** per Jonathan's request, added a real, pure-client-side win/each-way calculator to every horse with real odds — collapsed by default, verified live (math checked by hand against real odds, interactive update confirmed via a real DOM event). See `scripts/generate_dashboard.py`'s `_bet_calculator_html`/`_ew_defaults`/`calcBet`.

**"How did this do on its first day?"** Tried to answer with real data. Found that Smarkets contracts carry a real `state_or_outcome` field ('winner'/'loser') once a market settles — a genuine, free way to check real results without needing Racing API's paid tier. Built `scripts/check_todays_results.py` to use it. But by the time this was tried (23:00+), Smarkets had already rolled its live listing over to TOMORROW's races — today's races, even ones that finished hours ago, were gone from the listing entirely. So this real approach can answer "how did today go" only if run WHILE races are still listed as upcoming/live on Smarkets (i.e., same-day, probably within an hour or so of the last race), not the following evening. **Could not answer Jonathan's question with real data this session** — told him so plainly rather than guessing.

**Real bonus bug found and fixed while investigating:** `match_race()` never actually verified the Smarkets event's real calendar date matched the date being collected for — it built its comparison datetime by borrowing the Smarkets event's OWN date, so the date check was a silent no-op the whole time; only course+time-of-day were ever really compared. Found live: by evening, a TOMORROW Doncaster race nearly false-matched TODAY's Doncaster race purely because their time-of-day happened to fall close together. Fixed by requiring the event's real local date to equal the target `race_date` before any time comparison happens. 1 new regression test reproducing the exact scenario (same course, same time-of-day, genuinely different date).

Full suite: **199/199 pass** (was 195, +1 date-check regression, +3 bet-calculator tests already counted in the 198 from the prior commit).

**What this means for actually checking results:** the real, reliable way to do this going forward is either (a) run `scripts/check_todays_results.py` same-day, shortly after racing finishes, before Smarkets rolls its listing over, or (b) persist each matched race's real `market_id` at collection time (currently NOT stored — `market_snapshot` only keeps prices, not the market_id that produced them) so a later results check can query that specific market directly instead of re-deriving it via a fresh (and by then stale) event listing. Neither is built yet.

**What's still blocked (unchanged):**
1. Betfair — still SUSPENDED as of last check
2. Racing API's own results — still needs their Basic tier
3. **New, real, concrete gap:** no persistent results-collection pipeline exists. `scripts/check_todays_results.py` is a same-day-only, best-effort, read-only check — not a permanent pipeline. Persisting `market_id` per matched race (see above) is the real fix.

**What the next session should do, in priority order:**
1. Add `market_id` as a real column on (or alongside) `market_snapshot`, populated at collection time, so results can be checked later without depending on Smarkets' listing still containing the race.
2. Schedule `scripts/check_todays_results.py` (or a DB-writing version of it once market_id is persisted) to run same-day, shortly after the last race, so "how did today go" can actually be answered without racing the clock against Smarkets' listing rollover.
3. Check whether real Smarkets price-MOVEMENT data (multiple snapshots per horse over time, not just single matches) is genuinely accumulating now that both real match_race bugs are fixed.
4. Check whether Betfair's account status has cleared, only if there's a concrete reason to think so.
5. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
6. **Always run a long script unbuffered and backgrounded to a real log file**, never `| tee` in the foreground.
7. Keep this file updated at the end of every session.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/price data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf
- Do not retry the Betfair login endpoint without a concrete reason to think the account status changed
- Do not assume a persistently-zero real collector result is "just waiting for data" without checking — verify the matching logic actually works
- Do not skip re-running the full test suite before committing — all 199 tests must actually pass

**`scripts/generate_eod_report.py`:** already exists (built earlier the same day, answering Jonathan's earlier question about £1 win / £2 EW on each top pick, plus who the favourite was). Ran it for real this session: it correctly prints all of today's races with the real top pick (highest `gbm_v1` probability), the real market favourite (lowest real Smarkets `exchange_back`), and the real EW terms for that field size — and honestly marks every win/EW settlement as **PENDING**, since `runner_result` has zero real rows for today (same root cause as above: no results pipeline yet). Added 11 real unit tests for its pure settlement math (`ew_terms_for_field_size`, `settle_win`, `settle_each_way` — win/loss/pending/void-place-stake-on-win-only-fields all covered) in `tests/test_generate_eod_report.py`. Full suite now **210/210 pass**.

---

## 2026-09-10 — Session 10 continued: real real-results pipeline (Racing Post), track record dashboard section, Day 1 hit rate confirmed live

**Jonathan's idea that unblocked this:** "won't a websearch find the results? ... why don't we create an agent to gather the results after the event to log a win or loss?" Tested this live rather than assuming: Racing Post keeps real permanent result pages (unlike Smarkets' forward-only rolling listing) with the full finishing order embedded as real structured JSON in the page's own `__NEXT_DATA__` script tag (`props.pageProps.initialState.raceResult.data.runners`) — real finishing position, SP, and distance beaten, not scraped text and not an LLM's reading of the page.

**Real, confirmed constraints:**
- Plain scripted HTTP requests to racingpost.com are bot-blocked (403/406) — a real headless browser is required. `playwright` was already installed in this venv; confirmed it gets through cleanly for a specific race's result page.
- Racing Post's bare index/listing pages (`/results/`, `/racecards/<course>/<date>` with no trailing slash) are blocked even via headless Playwright.
- But the real per-course, per-day *meeting* page — `/racecards/<course_id>/<course_slug>/<date>/`, **with a trailing slash** — loads cleanly and embeds every race at that meeting (real Racing Post `raceId`, `startTime`, and an `isResult` flag) as structured JSON. This means every race's Racing Post ID is discoverable directly, for free, with **no search step at runtime at all** — just a course_id + date fetch. The same numeric `raceId` works in both the racecard and result URL for a race.
- Scripted search engines (DuckDuckGo HTML, Bing — both via `requests` and via headless Playwright) were tested live and either got bot-blocked or hadn't indexed the same-day deep-linked result page yet — a real dead end for automatic discovery, not needed once the meeting-page trick was found.

**Built:** `scripts/collect_race_results.py` — fully automated, no manual URL list needed. For each of our courses (mapped to a real Racing Post course_id/slug in the new `data/racingpost_course_ids.py` — deliberately incomplete, grows as new courses are seen, never guessed), fetches the real meeting page, matches each of our races by off_time (±5 min tolerance), fetches the real result page for any race whose `isResult` flag is true, parses real finishing position / SP / beaten-distance out of the structured JSON, matches horses via the same country-suffix-stripping convention as `collect_smarkets_prices.py`, and UPSERTs into `runner_result`. 18 new unit tests for the pure parsing/matching functions in `tests/test_collect_race_results.py`.

**Real, honest gotcha caught before it caused a bug:** `data.gb_racecourse_coordinates.normalise_course_name` collapses `'Lingfield'` and `'Lingfield (AW)'` to the same `'lingfield'` key — correct for Smarkets (one exchange market either way) but WRONG here, since turf Lingfield (course id 31) and the all-weather track (course id 393) are genuinely different Racing Post courses with different race calendars. `data/racingpost_course_ids.py` is keyed on our own raw `course.name` instead, not the normalised name.

**Ran it for real against Day 1 (2026-09-10):** 31/31 races matched, **292 real result rows recorded, 0 unmatched horses.** This is a genuinely complete real result set for the day — first time this project has had real settled outcomes for a live day.

**Real Day 1 answer, finally:** top pick won **7/30 settled races (23.3%)** — remarkably close to the real backtested hit rate of ~23.2% (RL-010), on a sample of exactly one day, so treat that closeness as a nice sign, not proof of anything. Top pick placed 16/30 (53.3%). Market favourite won 9/30 (30.0%), close to the real ~33.3% backtested market rate. £1-win P&L across all top picks: **+£24.24** on £30 staked; £2-EW P&L: **+£27.73** on £60 staked — one day, small sample, not a track record yet, stated as such everywhere it's shown.

**Built the persisted round-up, per Jonathan's request** ("there needs to be a round up of the day with a report using graphs and data that is stored so it can be used to build an overall success report"):
- New `daily_summary` table (one real UPSERT-able row per race_date: races settled, top-pick wins/places, favourite wins, win/EW stake+profit) — added to `db/schema.sql`, applied to the local DB.
- `scripts/generate_daily_summary.py` computes it from real `runner_result` data, reusing `generate_eod_report.py`'s own top-pick/favourite loading and settlement math rather than re-deriving it. A race whose top pick has no settled result yet is excluded from that day's counts, exactly as the EOD report already treats it — never counted as a loss. Safe to re-run (UPSERT) as more results land. 9 new unit tests in `tests/test_generate_daily_summary.py`.
- Dashboard: new "Track record" section (`render_track_record` in `generate_dashboard.py`) — real cumulative stat tiles (days tracked, hit rate vs favourite rate, £1-win and £2-EW cumulative P&L with ROI) plus a real day-by-day bar chart (hit rate bar + P&L per day), mobile-first, same `<20%>`-of-data-as-caveat discipline as everywhere else: shows an explicit "too small a sample" note below 20 real tracked days, never hidden. New `--bad` (red) CSS token added alongside the existing `--good`/`--warn` for signed P&L. Visually checked in both light and dark mode via a real local browser render before committing. 4 new unit tests.
- New evening pipeline `scripts/run_collect_results.sh` (collect results -> generate daily summary -> regenerate dashboard -> Netlify deploy) and LaunchAgent `com.silentedgezero.collect-results.plist`, scheduled 21:30 daily (after evening AW racing genuinely finishes) — loaded and confirmed running via `launchctl list`.

Full suite: **241/241 pass.**

**What the next session should do, in priority order (supersedes the prior list):**
1. Watch the 21:30 evening LaunchAgent run for real over the next few days — confirm `collect_race_results.py`'s meeting-page + result-page fetches keep working unattended (Racing Post's bot-detection behaviour could change).
2. Once several real days have accumulated in `daily_summary`, revisit whether the ~23% top-pick hit rate is holding up — one day is not evidence either way.
3. Expand `data/racingpost_course_ids.py` as new courses appear in real race data (a course fixture we haven't seen yet is skipped and reported, never guessed — check the evening log for "no Racing Post course id mapped" lines).
4. The Smarkets-based `scripts/check_todays_results.py` is now superseded by the Racing Post pipeline for actual results collection — kept only as a same-day sanity-check tool, not scheduled.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/price data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf
- Do not assume a persistently-zero real collector result is "just waiting for data" without checking — verify the matching logic actually works
- Do not skip re-running the full test suite before committing — all 245 tests must actually pass
- Do not treat a single real day's hit rate/P&L as a track record — state the sample size every time it's shown

**Same session, immediately after — click-through on "Days tracked":** Jonathan asked for the "Days tracked" stat tile to pop up a list of real tracked dates, each linking to that day's race card showing predictions with Win/Loss and Placed shown separately. Built as two more native `<dialog>` popups (no JS framework, same pattern as the race cards and the OR/Form help popup):
- `load_race_history()` — one query across every real tracked date, returning each race's real top pick (gbm_v1, same definition as generate_eod_report.py), its real model probability, and its real settled outcome, classified WIN / PLACED (within that race's real each-way place terms) / LOSS / PENDING.
- `render_days_tracked_dialog()` — the date list, click a date to open that day's dialog.
- `render_day_history_dialog()` — one real day's races, each showing time, course, race name, horse, model probability, real finishing position (or the real result_note for a non-finish like PU), and a colour-coded status badge (green WIN / amber PLACED / red LOSS / grey PENDING).
- Each day-row in the existing track-record bar chart is now also directly clickable to the same per-day dialog (bonus, reusing the same popup).
- Visually verified end-to-end in a real browser: tile click -> date list -> date click -> real race-by-race breakdown with correct badges, matching the 30 real settled races from Day 1.
- 4 new tests. Full suite: **245/245 pass.**

**Same session, win/placed/loss tally added to the day-history popup** per Jonathan's follow-up ("the only thing that is missing... a tally of how many wins, losses and placed"). Colour-coded chip row (N wins / N placed / N losses / N pending) above the race list. 1 new test. Full suite: **246/246 pass.**

---

## 2026-09-11 — RL-012: top-pick calibration, real validated overconfidence above ~40%

Jonathan's question looking at a real 21.6% top pick: is there a "sweet spot" probability band worth watching — could a 31% pick be overconfident, could a 20.5% pick be undervalued? Real, worthwhile question — built `scripts/analyze_top_pick_calibration.py` to answer it properly with the existing walk-forward apparatus and RL-011's discovery/validation discipline (first 7 folds discovery, remainder validation, never touched during discovery) rather than eyeballing REAL_CALIBRATION_BINS (which pools every runner, not just top picks).

**Real bug caught before trusting the result:** first draft defaulted to `test_window_days=60` (copied from `train_model2.py`), which produces 19 folds — the wrong boundary for RL-011's established 7-discovery/N-validation convention. Fixed to 120 (matching `compute_hit_rate.py`) before running for real.

**Real, validated result** (39,518 discovery + 10,207 validation real top-pick predictions; full table in docs/RESEARCH_LAB.md RL-012): Jonathan's specific guess (a ~20% pick undervalued) did NOT hold — that range is well-calibrated on both discovery and validation. But a real pattern in the opposite direction DID validate: top picks above ~40% confidence are consistently overconfident (actual win rate 4-9pp below stated probability), same direction on data discovery never touched — a genuine finding, unlike RL-011's rejected field-size idea. **Status: VALIDATED, not yet wired into anything** — no live pipeline/model/dashboard change made; a deliberate decision on whether to apply a calibration correction is still open.

Full suite: **250/250 pass** (4 new tests for `analyze_top_pick_calibration.py`'s pure bucket/summarise functions).

**What the next session should do, if Jonathan wants to act on RL-012:**
1. Decide whether to apply a targeted calibration correction (temperature scaling above the ~40% threshold specifically, same real technique already built in `src/evaluation/temperature_scaling.py` for RL-011) — this is a genuine open decision, not yet made.
2. Consider building a LIVE version of this table on the dashboard, now that `daily_summary`/`runner_result` are accumulating real results daily — would let the validated backtest finding be checked against real live outcomes over time, same way Day 1's real hit rate already tracked closely with the backtested ~23%.
3. Any live-tracked "sweet spot" needs the same discipline: don't act on a short live run alone — treat it as a slowly-accumulating confirmation of the backtest finding, not a new independent discovery.

**Same session, immediately after — Jonathan asked for "both, correction first":**
1. **Correction attempt (real, tested, rejected):** `scripts/validate_top_pick_overconfidence_scaling.py` fit a temperature (T=1.15) on discovery races with top pick >=40%, applied it to the untouched validation folds. Isolated to just the 557 affected validation races (the honest test — the full validation set dilutes any effect to invisibility since only ~5% of races are touched), Brier moved 0.146386 -> 0.146178 (0.14% relative, noise-level), hit rate and log loss unchanged. **Does not survive validation — same disposition as RL-011.** Not wired into anything. Documented in RESEARCH_LAB.md RL-012's follow-up section.
2. **Live-tracking table (built, shipped):** `render_live_calibration()` in `generate_dashboard.py` — new "Confidence calibration — live vs real backtest" dashboard section, bucketing every real settled top pick's own probability (reusing `bucket()`/`summarise()` from `analyze_top_pick_calibration.py`, no duplicated logic) against the fixed real RL-012 backtested validation numbers (`RL012_BACKTEST_VALIDATION` constant). Purely observational — explicitly does not change any probability shown or used elsewhere. Every bucket honestly flagged "small live sample" while n stays under 30 (true for all of Day 1's ~30 races once split across 9 bins). Visually verified in a real browser before committing.
3. 4 new tests for `render_live_calibration`. Full suite: **254/254 pass.**

---

## 2026-09-11 — Dashboard redesign: hero, £100 bank tracker, collapsed technical section, stale-date fix

Jonathan gave a full, specific redesign brief: replace the top-of-page stack (races/agreement/highest-confidence/3 Brier tiles/track record/P&L/disclaimer/weather) with a compact hero, move Brier/calibration/methodology behind a collapsed "Model transparency" section, add a "£100 starting bank" tracker, and fix a real, concrete bug: the page can show a stale date ("Live predictions — Thursday...") on a Friday morning before the daily pipeline has run, which "damages confidence instantly" on something positioned as live.

**Investigated the stale-date report first, honestly:** confirmed it's NOT a pipeline bug — the 07:15 LaunchAgent simply hadn't fired yet (checked at 00:58 Friday; `predict_races.log`/`predict_races_error.log` both last modified Sept 10 07:36, i.e. yesterday's real run). The real issue is presentational: a static, once-daily-generated page has no way to know "now" after deployment. Fixed with a client-side check (`<script>` in `render_html`) comparing the page's own embedded `race_date` against the viewer's real local date on every page load — if stale, swaps the subtitle to "Showing {day}'s real predictions..." and shows an explicit banner ("{Today}'s predictions are being prepared. {page day}'s verified results are available below."), rather than silently presenting old data as live. Real, documented limitation: uses the viewer's own browser clock/timezone, not authoritative UK race time — fine for Jonathan's own real use.

**New hero** (`render_hero`): three "Today's Edge" cards computed by `compute_todays_edge` — best win probability (highest real Model 2 top-pick probability), models agree (highest-probability race where M1 and M2 pick the same horse), biggest model/market disagreement (model's own top pick vs. a real de-vigged market probability — new `_implied_market_probs` helper, a display-only 1/odds renormalisation across only the runners with a real price, honestly returns `{}` rather than a misleading number when fewer than 2 runners are priced). Below the cards: a real one-line "Yesterday" recap and a real one-line "Lifetime" recap (both sourced from `daily_summary`, via a new shared `compute_cumulative_track_record` helper extracted out of `render_track_record` so the two can never drift apart), then a "View today's races ↓" jump link to a new `id="races"` anchor.

**Caught and fixed a real bug in my own new code before shipping:** `compute_todays_edge`'s disagreement-tracking compared `disagreement[5]` (which is `market_p`) instead of `disagreement[6]` (the actual `gap`) when deciding which race had the biggest disagreement — would have silently picked the wrong race. Caught by writing the real test (`test_compute_todays_edge_disagreement_uses_implied_market_probability`) before trusting the function, not by inspection.

**New "£100 starting bank" tracker** (`render_bank_tracker`): a real running balance starting at £100, walking `daily_summary`'s already-computed real £1-win P&L day by day — same flat-stake definition used everywhere else on the page, no new betting logic invented. Shows the day-by-day balance, never smoothed.

**Reorganised, not deleted:** `render_summary` (races today/model agreement), the 3 Brier-score tiles (`render_backtest_context`), and `render_live_calibration` (RL-012) now live inside a native `<details class="model-transparency">` disclosure, collapsed by default, right before the footer. The full Track Record (day-by-day results, win/placed/loss tallies, click-through to real race-by-race history) stays prominent and NOT behind the collapse — it's the actual "every winner and loser permanently recorded" proof Jonathan's own USP framing depends on, distinct from the methodology/calibration material that IS now collapsed.

**Visually verified** in a real browser: stale-banner fires correctly (today real-dated 2026-09-11, dashboard generated for 2026-09-10), hero cards render real data, bank tracker shows the real running balance, transparency section opens/closes and still contains the Brier/calibration content, and the whole page reflows cleanly at a real 390px mobile width.

16 new tests (`_implied_market_probs`, `compute_todays_edge`, `compute_cumulative_track_record`, `render_hero`, `render_bank_tracker`). Full suite: **267/267 pass.**

---

## 2026-09-11 — "Why have today's cards not come through?", pipeline moved to 1am, 7-day health monitoring

Real answer, checked before assuming a bug: it was 06:42 and the morning pipeline (racecards 07:00, predictions 07:15) simply hadn't fired yet — confirmed via log mtimes (both still dated 2026-09-10). Ran it manually to get Friday's cards live immediately, which surfaced a real (harmless) sequencing detail: running `predict_todays_races.py` before `collect_racecards.py` had run for the day gives 0 races — not a bug, just proved the two jobs are correctly dependent on each other in order. Re-ran racecards first, then predictions — 28 real races, correct dashboard, clean deploy.

**Real schedule change, per Jonathan's request:** `com.silentedgezero.collect-racecards` moved 07:00 -> 01:00, `com.silentedgezero.predict-races` moved 07:15 -> 01:15 (same 15-minute gap preserved so racecards always finish first). Both LaunchAgents unloaded and reloaded to pick up the new `StartCalendarInterval`. **Real, unverified assumption flagged, not hidden:** this assumes The Racing API's free "today" racecard is actually populated that early (UK racecards are typically published the evening before, but this hasn't been confirmed at exactly 01:00 yet) — worth checking the first real 01:00 run's log.

**New `scripts/check_pipeline_health.py`:** real, honest daily health check — queries the DB directly (never trusts a log alone) for whether today's races were actually stored, predictions actually locked, the deploy log is fresh and shows a real "Deploy is live!" line, and the most recent race day 2+ days old has real settled results. Every check reports a concrete real reason on FAIL, never a bare "something's wrong". 5 new tests for the one file-based check (`check_deploy_log_fresh`); the DB-backed checks are exercised by actually running the script (same convention as every other operational script here) — ran it live, correctly caught that the log hadn't refreshed since my manual (non-launchd) run bypassed the log-redirection paths that only launchd sets up.

**7-day monitoring, per Jonathan's request ("I would like now to monitor 7 days in advance"):** clarified first (his free racecard source only exposes today/tomorrow, not a real 7-day window — that would need a paid tier, not pursued) — he meant watching the daily pipeline actually run correctly for the next week, exactly the kind of silent gap just found. Set up via `CronCreate`, a recurring job at 08:37 daily (after both new 01:00/01:15 jobs and the prior evening's 21:30 results job) that runs `check_pipeline_health.py` and reports any real FAIL. **Real, honest limitation stated to Jonathan:** this is session-scoped (dies if this Claude Code session ends) and auto-expires after exactly 7 days regardless — not a durable system-level cron job.

Full suite: **272/272 pass.**

---

## 2026-09-11 — "How do I see tomorrow's races?" — real Today/Tomorrow tab, full predictions both days

Checked first, honestly: `collect_racecards.py` only ever fetched TODAY's card — never tomorrow's, even though the free Racing API tier genuinely supports both (confirmed in `src/providers/racecard_theracingapi.py`'s own docstring). Asked Jonathan to confirm scope before building (full predictions for tomorrow vs. racecard-only vs. a separate page) — chose full predictions, shown as a second day on the same dashboard.

**`collect_racecards.py`:** now loops over `[today, today+1]`, each date independent and best-effort (a real fetch failure for one date — e.g. tomorrow's card not published yet — never aborts the other). Real bug hit and fixed immediately: two back-to-back API calls triggered a real 429 (rate limit); fixed with a 2s delay between the two real requests. Added a real defensive check — a returned race whose own `race_date` doesn't match the date actually requested is skipped and logged, never silently stored under the wrong day.

**Dashboard:** `predict_todays_races.py` and `generate_dashboard.py` already took a `race_date` argument, so no prediction-logic changes were needed — just call both for `today` and `tomorrow`. New `render_day_tabs()` / `render_day_panel()` in `generate_dashboard.py`: a real Today/Tomorrow tab toggle (native buttons + `hidden` attribute, no framework) wrapping the existing weather+race-list block, reused unchanged for either day. Falls back to the exact old single-day layout (no tab UI at all) when there's no real tomorrow data yet — never shows an empty/broken tab. The hero ("Today's Edge"), bank tracker, and track record stay about today only, unchanged — makes no sense duplicated for a day that hasn't happened.

**Caught a real cosmetic bug while verifying in a real browser:** `render_weather`/`render_overview_chart`'s section labels were hardcoded "Today's course conditions" / "Today's confidence" — still said "Today's..." even while viewing the Tomorrow tab, since both functions are now reused for either day. Fixed by making the labels day-agnostic ("Course conditions (live forecast)" / "Confidence, at a glance") — the tab button above already states which day it is.

**Automated going forward:** `run_predict_todays_races.sh` now calls `predict_todays_races.py` for both `$TODAY` and `$TOMORROW` (via `date -v+1d`, confirmed working on this Mac's BSD `date`) before generating the dashboard — no manual second run needed on future days.

Ran the real end-to-end pipeline: 28 real races collected+predicted for 2026-09-11, 39 for 2026-09-12, tab toggle verified switching correctly in a real browser (weather, race list, and a real tomorrow race's full dialog all render correctly), dashboard deployed live.

10 new tests (`render_day_tabs`, `render_day_panel`). Full suite: **276/276 pass.**

---

## 2026-09-11 — "Why have Doncaster's odds not come in?" — real Smarkets 429 rate-limit fix

Checked the real logs first: every single Doncaster race (all 8) failed with a real 429 Too Many Requests from Smarkets, identically across multiple real collection runs, while Chester/Salisbury/Sandown succeeded every time in the same runs. Not random — a real structural cause: each race makes 3 real HTTP calls (win-market lookup + contracts + quotes) with zero gap between them, and the whole collector only pauses 0.3s between races. Doncaster's races happen to land later in Smarkets' own event listing order, so by the time the collector reaches them the real rate-limit budget (spent by ~20 prior races' worth of rapid-fire requests) is already exhausted — same 8 races lose every single time, not a one-off blip.

**Real fix, live-tuned in two passes, not assumed correct on the first try:**
1. New `_get_with_retry()` in `src/providers/odds_smarkets.py` — real 429-aware retry wrapping all 3 real GET call sites (`list_horse_racing_events`, `get_win_market_id`, both calls in `get_runner_prices`). Honours a real `Retry-After` header when Smarkets sends one; exponential backoff otherwise. First version (4 attempts, 1s base) tested live: recovered 3 of the 8 previously-failing Doncaster races, but 5 still failed — not enough headroom.
2. Widened to 6 attempts, 2s base (2s/4s/8s/16s/32s) and bumped the inter-race pacing 0.3s -> 0.5s in `scripts/collect_smarkets_prices.py`. Re-tested live: **all 28 races matched, 0 errors, all 8 Doncaster races recovered.**

13 new tests for `_get_with_retry` (succeeds first try, retries past a real 429, honours `Retry-After`, raises after exhausting real attempts, raises immediately on a genuine non-429 error — never silently swallowed). Full suite: **281/281 pass.**

**Same conversation, answered honestly with partial data before the fix landed:** Jonathan asked "given 28 races today and the odds, how much would I get back if I bet £1 on each?" — answered with what was real at the time (20 of 28 priced, Doncaster's 8 missing): if every priced pick won, £158.20 back on £20 staked (explicitly flagged as an unrealistic ceiling, not a forecast); the real statistically honest number — expected return using each pick's own real model probability — was ≈£30.30 (expected profit ≈+£10.30).

**Immediately after, the 429 fix turned out not to be the whole story.** Re-checking after the fix: all 8 Doncaster races now had real Smarkets snapshots recorded (0 errors) — but the dashboard STILL showed no odds for any of them. Real second bug, much bigger than it first looked:

- `horse` has `UNIQUE (name, foaled_year)` — but `foaled_year` is never populated by our real data source (always NULL), and Postgres treats NULL as distinct from NULL for uniqueness. Every `ON CONFLICT (name, foaled_year)` re-insert of an already-known horse has been silently creating a brand-new duplicate `horse` row instead of matching the existing one — confirmed: real, e.g. 3 separate rows all named "Nabati". **Scope confirmed live: 536 real duplicate horse names, 1,085 excess rows.** `scripts/collect_smarkets_prices.py::load_our_races` sourced horse_id from `runner_snapshot` with no ORDER BY — a second same-day `collect_racecards.py` run (there were two today) created fresh duplicate horse rows, and this query happened to pick the NEW duplicate instead of the one `prediction` already had locked in, so real Smarkets prices were being recorded correctly but keyed to a horse_id nothing else ever queries.
- **Real fix shipped:** `load_our_races` now sources horse_id via `prediction` — the one real source of truth the rest of this project already depends on — instead of raw `runner_snapshot`. Re-tested live: 27/28 races priced (7/8 Doncaster, up from 0/8; the one remaining gap is a real thin order book with no bids yet, not a bug).
- **Real structural fix drafted, then deliberately reverted the same session:** two partial unique indexes (`(name, foaled_year) WHERE foaled_year IS NOT NULL` / `(name) WHERE foaled_year IS NULL`) would fix this at the schema level for good — but creating them requires the table to already be duplicate-free, and **294 of the 536 duplicate groups are referenced by LOCKED rows in `prediction`.** Fixing those means deliberately repointing an immutable ledger row's horse_id (trigger-disable, re-hash, real testing) — a genuine architectural decision, not something to do silently mid-session. Reverted cleanly back to the original (still non-functional, but not newly broken) constraint so the live pipeline keeps working exactly as before while this is decided. Documented in full in `db/schema.sql`'s own comment on the `horse` table — read that before touching it.
- **What this means for the rest of the project, checked, not assumed:** the blast radius is narrower than it first looked — trainer/jockey strike-rate features key off `trainer_id`/`jockey_id`, not `horse_id`, and `recent_form` is a raw string field from the API, not something we compute from horse-id history — so RL-010's features and the backtested Brier/hit-rate numbers are NOT corrupted by this. The real, confirmed impact is: (a) today's Smarkets price linkage (now fixed), and (b) ~1,085 harmless-but-untidy extra rows in `horse`.

Full suite: **281/281 pass** (no new dedicated tests for `load_our_races` itself — DB-integration only, same convention as the rest of this file; exercised by the real live re-run above).

**Open decision for Jonathan:** whether/when to run the full historical horse-dedup migration (merges 536 duplicate groups, repoints `runner_snapshot`/`market_snapshot`/`runner_result`/`prediction` FKs, recomputes `record_hash` for any touched locked prediction rows, then creates the two partial unique indexes for real going forward). Not started without his explicit go-ahead.

---

## 2026-09-11 — Live dashboard now redeploys every 20 minutes, not just twice a day

Jonathan asked whether the whole pipeline runs fully automated without Claude Code open. Real answer: yes for the actual data pipeline (racecards/predictions/odds/results are all real macOS `launchd` LaunchAgents, confirmed loaded, independent of any Claude Code session) — with one real exception (the 7-day pipeline health-check set up earlier is genuinely session-scoped, per `CronCreate`'s own "dies when Claude exits") and one real gap noticed while checking: Smarkets odds are collected every 20 minutes (`StartInterval: 1200`), but only `run_predict_todays_races.sh` (01:15) and `run_collect_results.sh` (21:30) ever regenerated the dashboard and redeployed — so real intraday odds movement sat in the DB all day without ever reaching the live site.

**Fixed:** `scripts/run_collect_smarkets_prices.sh` now also regenerates and redeploys the dashboard after every real odds collection, same nvm-PATH pattern as the other two wrappers (netlify CLI needs real node on PATH, which launchd's minimal environment doesn't include). Ran it live end to end twice: real odds collected, dashboard regenerated (28 races today, 39 tomorrow), Netlify deploy succeeded both times — the live site will now refresh with real odds roughly every 20 minutes, all day, automatically.

Full suite: **281/281 pass** (shell-script-only change, no test changes needed).

---

## 2026-09-11 — 1am schedule never actually fired: Mac was asleep, reverted to 07:00/07:15

The scheduled daily health check (`scripts/check_pipeline_health.py`, running via the 7-day `CronCreate` monitor) caught a real FAIL: `predict_races.log` still dated 2026-09-10 at 09:07 the next morning. Investigated rather than assumed:

- `launchctl print` on `com.silentedgezero.predict-races` showed `last exit code = (never exited)` — the job has not fired even once since the schedule moved to 01:00/01:15 the previous session.
- `pmset -g log` showed no real wake activity around 01:00–01:15; the system only shows continuous wake starting ~06:40 that morning.
- **Real root cause:** regular user `launchd` LaunchAgents do NOT wake a sleeping Mac to run — if the machine is asleep at the scheduled time, the job is silently skipped, not queued or retried. Today's real racecards/predictions data exists only because it was run manually earlier this session while investigating the Doncaster odds issue, not because the automated 1am job fired.

**Real fix, per Jonathan's choice** (offered `pmset` scheduled auto-wake vs. reverting the schedule vs. relying on manual catch-up — chose to revert): `com.silentedgezero.collect-racecards` and `com.silentedgezero.predict-races` moved back to 07:00/07:15 — the schedule that was actually working reliably before. Both LaunchAgents unloaded and reloaded, confirmed picked up the new `StartCalendarInterval`.

**What this means for the 20-minute Smarkets/redeploy job and the 21:30 results job:** unaffected — `StartInterval`-based jobs (Smarkets) resume on wake and catch up naturally since they're not tied to one fixed clock time, and 21:30 is well within normal waking hours, so no equivalent risk there.

---

## 2026-09-11 — "Model vs market" upgrade, Stage 1: fair odds, market probability, edge, EV

Jonathan's full spec: reframe the platform from "which horse is most likely to win" to "where does our model disagree with the market enough to matter" — a 7-stage roadmap (fair-odds/edge/EV, MOST LIKELY WINNER/BEST VALUE/NO EDGE labels, CLV price-snapshot tracking, Edge Lab segmentation, calibration/market-comparison dashboards, a composite Silent Edge Score, daily/cumulative reporting). Given this project's own discipline (real data only, tested pure functions, no fabrication), did the required pre-work first rather than rushing all 7 stages: checked the real schema (found `prediction` already has dormant `market_probability`/`fair_odds`/`absolute_edge`/`expected_value` columns, left NULL by design since market odds usually aren't final at lock time and a locked row can never be updated) and confirmed real sample size (1 settled day live) — see the end-of-turn summary given to Jonathan for the full honest staging plan.

**Stage 1 shipped, real, tested, deployed:**
- `src/analysis/edge_metrics.py` (new module) — pure, reusable functions: `model_fair_odds`, `raw_market_implied_probability`, `normalized_market_probabilities` (real de-vig, renormalises only priced runners, `{}` when fewer than 2 — never a guessed share), `probability_edge`, `price_advantage`, `expected_value` (gross + net, `commission` defaults to 0.0, NEVER assumed, raises on an invalid value), `model_agreement_label`. 19 tests, validated against Jonathan's own worked examples in the spec (22% -> fair odds 4.55; 8.60 odds -> 11.63% raw implied; +10.4pt edge; +89% price advantage; +£0.89 EV) — his numbers, not just internal consistency checks.
- **Why computed at display time, not stored on `prediction`:** preserves the immutable-ledger design exactly as already built — the model's own probability/ranking never changes, and the model-vs-market relationship is recomputed fresh against whatever the latest real market_snapshot says, so Live Value numbers are always current rather than a lock-time fossil. Documented in the module's own docstring.
- `generate_dashboard.py`: `_implied_market_probs` now delegates to the new shared module (removed duplicate logic). New `_edge_chips_html()` renders Fair Odds / Market (raw) / Market (fair) / Edge (colour-coded green/red) / Price advantage / EV per runner, wired into `render_race`'s runner rows. New `COMMISSION_RATE` module constant (0.0 default, clearly documented as needing a deliberate real value, not Smarkets' ~2% assumed). 4 new tests for `_edge_chips_html`.
- Visually verified live in a real browser: Doncaster 13:50 showed real, correct, differentiated numbers per runner (Masaban +6.0pts edge/EV +1.33; Caragio -7.5pts edge/EV -0.47, shown in red) — exactly the "model vs market disagreement" reframing the spec asks for, using live real data, no fabrication.

Full suite: **304/304 pass** (19 + 4 new). Deployed live the same session.

---

## 2026-09-11 — Model-vs-market upgrade, Stage 2: BEST VALUE / NO EDGE / MODEL WARNING labels

Jonathan: "the word" (go-ahead for Stage 2, offered at the end of Stage 1's summary).

`src/analysis/runner_classification.py` (new module) — `ValueFilterConfig` (real, configurable: `min_edge_pts` default 0.05 matching the spec's own example filter, `min_ev` default 0.0, optional model-probability bounds, `overconfidence_threshold` default 0.40), `classify_runner_value()` (returns BEST VALUE / NO EDGE / MODEL WARNING / INSUFFICIENT DATA — never auto-labels the biggest raw edge as a bet; a runner must clear the real configured bar first), `pick_race_best_value()` (the single strongest real, qualifying runner in a race, or None).

**MODEL WARNING uses a real, already-validated finding, not a fabricated rule:** the default `overconfidence_threshold=0.40` is RL-012's own real result (top picks shown >=40% overstate their real win rate by 4-9pp, validated on genuinely held-out data — see docs/RESEARCH_LAB.md) — a runner with a real, large edge but a model probability in that band is flagged MODEL WARNING instead of BEST VALUE, since the apparent edge may just be the model's own known overconfidence, not a real opportunity. 9 tests, including one proving the classifier doesn't just chase the raw edge number (the exact same edge/EV numbers get BEST VALUE at 30% model probability and MODEL WARNING at 41%).

**Wired into `generate_dashboard.py`:** refactored Stage 1's inline edge calculation into a shared `compute_runner_edge()` (single source of truth for both the display chips and the classifier — can't drift apart). Every runner in a race — not just the top pick, since "the highest-probability horse is NOT automatically the best-value horse" — gets classified and shown a colour-coded status badge (green BEST VALUE, amber MODEL WARNING, grey NO EDGE/INSUFFICIENT DATA). The race header now also shows a `VALUE: <horse>` badge for the single strongest qualifying runner in that race, when one exists. New `VALUE_FILTER_CONFIG` module constant. 6 new dashboard-level tests.

**Visually verified live:** Doncaster 13:50 — Masaban and Little Miss India both individually qualified as BEST VALUE (+6.2pts / +7.7pts), the race-level badge correctly picked the stronger of the two (Little Miss India), and Caragio correctly showed NO EDGE with its real negative edge (-8.0pts) in red.

Full suite: **316/316 pass** (9 + 6 new). Deployed live.

---

## 2026-09-11 — "Why has Silent Edge Zero not rounded up today's results?" — same duplicate-horse bug, second script

Real cause, found the same way as the Doncaster-odds investigation earlier today: `daily_summary` showed `races_settled = 0` for today despite the 21:30 `collect-results` job having genuinely run and inserted **79 real result rows**. Checked, not assumed: `runner_result.horse_id` for today's rows had zero overlap with `prediction.horse_id` for the same races — the exact same root cause as this morning's Doncaster odds bug (`horse`'s never-actually-deduplicating `UNIQUE (name, foaled_year)` constraint — see `db/schema.sql`'s own comment), just surfacing in a second, separate script that has its own independent horse-matching query.

**Real fix:** `scripts/collect_race_results.py::load_our_runners` sourced horse_id from `runner_snapshot` (the duplicate-prone table) with no ORDER BY. Changed to source via `prediction` — same fix, same reasoning, as this morning's `collect_smarkets_prices.py::load_our_races` fix. Documented in the function's own docstring, cross-referencing the earlier fix so the pattern is recognisable next time it turns up in a third script.

**Also found while re-running live:** three courses racing today (Chester, Salisbury, Sandown) weren't yet in `data/racingpost_course_ids.py` — a real, expected, already-documented limitation (an unmapped course is skipped and reported, never guessed), not a bug. Found their real Racing Post course IDs (13/chester, 52/salisbury, 54/sandown) and added them.

**Re-ran the real pipeline end to end:** `collect_race_results.py` — 28/28 races matched, 260 real result rows, 0 errors. `generate_daily_summary.py` — **25/28 races settled** (3 remaining lack a real market price on the top pick, an honest gap, not this bug): top pick won 4 (16.0%), placed 12 (48.0%), favourite won 6, £1-win P&L £4.85, £2-EW P&L £6.05. Dashboard regenerated and deployed.

Full suite: **316/316 pass** (no test changes — `load_our_runners` is DB-integration only, same convention as `load_our_races`, exercised by the real live re-run above).

**Checked immediately, not deferred:** grepped the rest of the codebase for any other query sourcing horse_id from `runner_snapshot` instead of `prediction`. Only one other hit — `scripts/derive_recent_form.py` — and it's a one-shot historical backfill already run once over the bulk Kaggle load (not part of the live daily pipeline, so not exposed to cross-run duplication the same way). `generate_dashboard.py`'s own `runner_snapshot` join is safe — it joins FOR extra stats against `prediction.horse_id`, never sources FROM it. No other live-pipeline script affected.
