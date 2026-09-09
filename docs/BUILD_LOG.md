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

## 2026-09-08 — Session 10 (autonomous overnight, cloud routine)

**Confirmed the credential boundary first, as instructed:** `env | grep THERACINGAPI` returned
nothing in this container. This cloud routine still does not have
`THERACINGAPI_USERNAME`/`THERACINGAPI_PASSWORD` — checked again per the ground rules, did not
assume otherwise, did not attempt `scripts/collect_racecards.py` or
`scripts/collect_weather.py`. The real 558K-row Kaggle-loaded dataset from Sessions 6/8/9 is
also still Mac-only (this container's Postgres was freshly bootstrapped empty via
`db/setup_local_postgres.sh && python3 db/init_db.py`, as every prior autonomous session has
needed — no real data lives here).

**This session's scheduled prompt asked for Phase 6 (a synthetic-fixture logistic baseline) —
that work is already done, real-data-tested, and superseded** (Model 1,
`src/models/model1_logistic_baseline.py`, built Session 5, extended Session 7, real-trained
Sessions 8–9: it lost to the market baseline on Brier/log loss, see RL-006). Per this file's own
instruction to "read BUILD_LOG.md first, it has the exact current state... follow it," picked up
the actual next item Session 9 left open instead of duplicating finished work: **Phase 7 — Model
2, a genuinely different model class (gradient-boosted trees) over the same features**, exactly
as RL-006 and Session 9's "suggested next step" named.

**What's genuinely done and verified this session (all real code, all with real passing
tests — 93/93 tests pass via `python3 -m pytest tests/ -v`, up from 81):**
- `src/models/model2_gradient_boosting.py` — **Model 2**, a per-runner binary classifier
  (`sklearn.ensemble.HistGradientBoostingClassifier`, P(this runner wins) fit on one row per
  (race, runner)) over the exact same 5 race-relative features Model 1 uses
  (`build_race_features`/`FEATURE_NAMES`, reused unchanged from
  `src/models/model1_logistic_baseline.py`) — deliberately the same features, so the one
  variable under test is the model class, not the information available to it. Since each
  runner's raw probability comes from an independent binary classification rather than a joint
  per-race softmax, `predict_race_probabilities` renormalises the raw outputs to sum to 1.0 per
  race (`_renormalize`, with an all-zero/negative-total fallback to uniform rather than dividing
  by zero). Unlike Model 0/1, `model=None` raises `ValueError` rather than falling back to a
  meaningful "untrained" prediction — an unfitted classifier can't produce one. **This is still
  NOT a real prediction** — labelled as such in the module docstring, every relevant test
  docstring, `docs/RESEARCH_LAB.md` RL-008, and here — no real (racecard, result) pair is
  reachable from this cloud routine.
- **`requirements.txt`: scikit-learn uncommented for the first time** (Phase 7 dependency,
  anticipated since Phase 1's comment block). Unlike this repo's other numerical work (the
  market de-vig bisection solvers, Model 1's own pure-Python gradient ascent), a correct
  gradient-boosted tree implementation is a different scale of surface area — using the same
  free, open-source, well-tested library the industry uses is the responsible choice here, not
  a shortcut; explained in the module docstring. No other Phase 6+ dependency
  (catboost/xgboost/lightgbm/pandas/polars) was needed or added.
- `tests/test_model2_gradient_boosting.py` — 12 real tests: `_renormalize` edge cases (normal
  case sums to 1.0 and preserves relative order, all-zero and negative-total both fall back to
  exact uniform, empty input returns empty — pulled out as its own pure function specifically so
  these degenerate cases could be tested directly without forcing a real classifier into them),
  fit/predict error handling (empty race list, winner not among runners, empty race, `model=None`
  all raise `ValueError`), and a signal-recovery convergence check (same style as Model 1's
  `test_fit_recovers_rating_signal_sign`: 25 synthetic races where the highest-rated runner
  always wins -> the fitted boosted-tree classifier rates that same runner-shape highest on a
  held-out race of the identical shape). Fixtures use the same real, verified schema shapes as
  every other test in this repo (`tests/test_racecard_theracingapi.py`).
- `scripts/train_model2.py` — **new, NOT YET RUN** (Mac-only, needs the real Kaggle-loaded DB
  that lives only on Jonathan's Mac). Mirrors `scripts/train_model1.py`'s exact shape (same
  `load_races` query, same walk-forward loop) but scores Model 0, Model 1, and Model 2 side by
  side on the same chronological folds for a real three-way comparison the moment someone runs
  it there — same "build the plumbing ready to fire the moment real data is reachable" pattern
  this repo has used since Model 0 was scaffolded against synthetic odds. Verified only that it
  parses and imports cleanly in this environment (no DB here to actually run it against).
- `docs/RESEARCH_LAB.md` — new entry RL-008 (Model 2, status IDEA, explicit about the
  independent-binary-classifier-plus-renormalisation simplification vs. a true joint model, and
  that nothing here is evidence about real racing yet).
- `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` — directory listing updated: `model2_gradient_boosting.py`
  and its test file added; `scripts/` section corrected to reflect every script's real
  Mac-only/cloud-buildable status accurately (several entries had gone stale — `collect_weather.py`
  wasn't marked Mac-only, `load_kaggle_historical.py` still said "written but untested" when
  Session 6 actually ran it to completion, `train_model1.py` was missing entirely); ML stack line
  updated now that scikit-learn is genuinely in use, not just anticipated.
- Full test suite re-run and confirmed green after every change: `./db/setup_local_postgres.sh
  && python3 db/init_db.py` (fresh container, as every prior autonomous session has needed) then
  `python3 -m pytest tests/ -v` → **93/93 passed**, including the DB-backed `tests/test_leakage.py`
  tests against a freshly bootstrapped local Postgres in this container. `pip install pytest
  psycopg2-binary python-dotenv requests scikit-learn` was needed first (fresh container has none
  of `requirements.txt` pre-installed, matching every prior session's experience).

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — for real market prices (Phase 4)
2. Kaggle account credentials in THIS cloud environment — the real 558K-row dataset exists but
   only on Jonathan's Mac; this routine cannot reach or reproduce it
3. Racing API results — still needs their Basic tier; not pursuing, Kaggle covers this need

**What the next session should do, in priority order:**
1. **Check for new credentials/results as always** — `env | grep -iE "racing|kaggle|betfair"`,
   recent commits, this file. If still cloud-only, don't re-derive that, move on.
2. **Running `scripts/train_model2.py` against the real Kaggle-loaded DB is the single
   highest-leverage next step**, and it's Mac-only (same reason `train_model1.py` needed to be):
   this is the first point Model 2 could honestly be compared to Model 0/Model 1 on real
   outcomes rather than a synthetic convergence check. Update `docs/RESEARCH_LAB.md` RL-008 and
   this file with the real result, whichever way it goes — a loss is real information (see
   RL-006's own honest write-up), not a failed session.
3. If still cloud-only and blocked on real data: there is very little synthetic-only plumbing
   left worth building blind for Model 2 specifically. Worth considering instead: (a) a
   hyperparameter sweep (`max_depth`/`learning_rate`/`max_iter`) on the SAME synthetic
   rating-signal fixture, to confirm the fitting is reasonably stable across settings before a
   real run burns Mac time on a bad default — still not a real benchmark; (b) revisit RL-008's
   flagged independent-binary-classifier simplification (a genuinely joint/ranking formulation)
   as a Model 2b variant; (c) an `odds_betfair.py` provider stub against Betfair's public
   Exchange API docs, still flagged as not written since Session 5; (d) course/distance-specific
   draw bias (RL-004) or weather (RL-001) as a genuinely new Model 1/2 feature, not yet touched
   by any session.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session — add a new dated section above this
   instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not attempt `scripts/collect_racecards.py`, `scripts/collect_weather.py`,
  `scripts/load_kaggle_historical.py`, `scripts/derive_recent_form.py`, `scripts/train_model1.py`,
  or `scripts/train_model2.py` from this cloud routine environment — no credentials/real DB here,
  confirmed again this session, will fail or run against an empty database
- Do not present Model 2's synthetic-fixture test results as evidence it predicts real racing
- Do not skip re-running the full test suite before committing — all 93 tests must actually
  pass, not just the new ones

---

## 2026-09-08 — Session 11 (autonomous overnight, cloud routine)

**Confirmed the credential boundary first, per this session's explicit instructions:**
`env | grep THERACINGAPI` returned nothing in this container — empty, as flagged. Only
`CCR_ENABLE_TRACING=true` is set. This cloud routine still does not have
`THERACINGAPI_USERNAME`/`THERACINGAPI_PASSWORD`, does not have Kaggle credentials, and cannot
reach the real 558K-row Kaggle-loaded historical dataset (that lives only in Postgres on
Jonathan's Mac). Did **not** attempt `scripts/collect_racecards.py` or
`scripts/collect_weather.py` here, per the explicit instruction. Racecard/weather collection
stays **Mac-only** — unconfirmed otherwise in this file, so not assumed.

**This session's scheduled prompt asked for Phase 6 (a synthetic-fixture statistical/logistic
baseline).** Per this file's own standing instruction ("read BUILD_LOG.md first... follow it"),
checked current state before starting: Phase 6 (Model 1,
`src/models/model1_logistic_baseline.py`) was built Session 5, real-trained Sessions 8–9 (lost
to the market baseline, see RL-006), and **Phase 7 (Model 2, gradient boosting) is also already
done** (`src/models/model2_gradient_boosting.py`, Session 10, RL-008) — `git log` at the start
of this session was already at `de23e44 "Phase 7: Model 2, gradient-boosted trees..."`, matching
Session 10's own entry exactly. Rather than duplicate finished work, picked up Session 10's own
"what the next session should do" list, item 3(d): **course/distance-specific draw bias
(RL-004)**, flagged as "not yet touched by any session" and the most concrete real gap in the
feature set that's genuinely buildable without real data access.

**What's genuinely done and verified this session (all real code, all with real passing
tests — 106/106 tests pass via `python3 -m pytest tests/ -v`, up from 93):**
- `src/features/draw_bias.py` — **new module**, the real hypothesis RL-004 has flagged since
  Session 2 as blocked ("requires historical results grouped by course+distance, which doesn't
  exist yet"), as opposed to `runner_features.py::draw_bias_features()`'s deliberately neutral
  this-race-only placeholder. `draw_percentile_bucket()` splits draws 1..field_size into
  `num_buckets` groups using pure integer arithmetic (no float rounding at bucket boundaries —
  deliberately, after confirming a float version would have hit exact `x.0` boundary ambiguity).
  `compute_course_distance_draw_bias()` takes caller-supplied historical (course, distance,
  surface, draw, finishing_position) records — already leakage-filtered by the caller, same
  discipline as `scripts/derive_recent_form.py`, this module does no date filtering and no DB
  access at all — buckets them, and returns the queried draw's own bucket win rate against the
  group's overall baseline win rate (`win_rate_vs_baseline`, the actual bias signal, not just a
  raw rate that could reflect the field being generally weak/strong). Returns `None` (never
  guessed) when the draw/field can't be bucketed, when a course+distance+surface combination has
  fewer than `min_sample_size` historical runners, or when the queried draw's own bucket happens
  to have zero historical runners even though the group overall met the threshold.
- `tests/test_draw_bias.py` — 13 real tests: exact bucket-boundary tables hand-worked for two
  field sizes (including an uneven 10-runner/3-bucket case where bucket sizes come out 4/3/3, not
  equal — checked and accepted honestly, not hidden), hand-verified win-rate-vs-baseline
  arithmetic (2/9 for a favoured bucket, -1/9 for an unfavoured one, against a 10-race synthetic
  fixture where draw 2 always wins), and every `None`-return path exercised individually
  (unbucketable draw, sample size below threshold, course/surface mismatch, a bucket with zero
  historical runners despite the group meeting the sample-size floor, and non-runner rows
  correctly excluded from the sample rather than counted as losses). One test failure caught and
  fixed during this session, not shipped: the first draft's hand-calculated expected buckets for
  the uneven-field-size case were arithmetically wrong (worked out `(d-1)*3//10` incorrectly by
  hand) — pytest caught it immediately, recomputed by hand carefully, fixed the test, not the
  (correct) code.
- `docs/RESEARCH_LAB.md` RL-004 — updated: now documents both the neutral placeholder
  (`runner_features.py`) and the real computation (`draw_bias.py`) side by side, status moved
  from IDEA to **TESTING (partial)** — the computation is built and unit-tested, but RL-004's
  actual hypothesis (does a genuine course/distance draw bias exist and does it help a model) is
  still untested against real data, only no longer blocked on missing plumbing.
- `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` — directory listing updated: `draw_bias.py` and
  `test_draw_bias.py` added.
- Full test suite re-run and confirmed green after every change: `./db/setup_local_postgres.sh
  && python3 db/init_db.py` (fresh container, as every prior autonomous session has needed) then
  `python3 -m pytest tests/ -v` → **106/106 passed**, including the DB-backed
  `tests/test_leakage.py` tests against a freshly bootstrapped local Postgres in this container.
  `pip install pytest psycopg2-binary python-dotenv requests scikit-learn` needed a couple of
  retries this session (one `ReadTimeoutError` fetching a wheel from `files.pythonhosted.org` on
  the first attempt) — not a credentials or environment problem, just transient network flake;
  succeeded on retry with a longer timeout.

**Deliberately NOT done this session, and why:** did not write a DB-writing backfill script
(the way `scripts/derive_recent_form.py` backfills `runner_snapshot` columns) for draw bias.
Unlike recent-form, there's no natural single column to store a course/distance/draw-bucket win
rate against on `runner_snapshot` — it's a derived, query-time aggregate over *other* rows, not
a fact about the row itself — and inventing a new table/column for it without validating the
computation against real data first felt like schema commitment ahead of evidence. The cleaner
next step (below) is to call `compute_course_distance_draw_bias()` from within
`scripts/train_model1.py`/`train_model2.py` at train time, the same place feature vectors are
already assembled, no schema change needed.

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — for real market prices (Phase 4)
2. Kaggle account credentials in THIS cloud environment — the real 558K-row dataset exists but
   only on Jonathan's Mac; this routine cannot reach or reproduce it
3. Racing API results — still needs their Basic tier; not pursuing, Kaggle covers this need

**What the next session should do, in priority order:**
1. **Check for new credentials as always** — `env | grep -iE "racing|kaggle|betfair"`, recent
   commits, this file. If still cloud-only, don't re-derive that, move on.
2. **The single highest-leverage next step is genuinely testing RL-004 and RL-008 against real
   data**, both Mac-only: (a) run `scripts/train_model2.py` against the real Kaggle-loaded DB
   (Session 10's own item 2, still not done — Model 2 has never been compared to Model 0/1 on
   real outcomes); (b) wire `src/features/draw_bias.py::compute_course_distance_draw_bias()` into
   a real (course_id, distance_yards, surface, draw, finishing_position) query over the Kaggle
   data, leakage-filtered per race the same way `train_model1.py`/`derive_recent_form.py` already
   do it, and see whether `win_rate_vs_baseline` is (a) real signal or (b) noise once real sample
   sizes and `min_sample_size` gating are applied — this is the first point RL-004's actual
   hypothesis (not just its plumbing) could be tested.
3. If still cloud-only and blocked on real data: there is very little synthetic-only plumbing
   left worth building blind for either Model 2 or draw bias specifically. Worth considering
   instead: (a) a hyperparameter sweep for Model 2 on a synthetic fixture (Session 10's item 3a,
   still not done); (b) RL-001 (weather) as a genuinely new feature, still completely untouched
   by any session; (c) an `odds_betfair.py` provider stub, still flagged as not written since
   Session 5.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session — add a new dated section above this
   instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result data, or any model's training data, to "demo" anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not attempt `scripts/collect_racecards.py`, `scripts/collect_weather.py`,
  `scripts/load_kaggle_historical.py`, `scripts/derive_recent_form.py`, `scripts/train_model1.py`,
  or `scripts/train_model2.py` from this cloud routine environment — no credentials/real DB here,
  confirmed again this session, will fail or run against an empty database
- Do not present `draw_bias.py`'s synthetic-fixture test results as evidence a real course/
  distance draw bias exists — the hypothesis itself is still untested
- Do not skip re-running the full test suite before committing — all 106 tests must actually
  pass, not just the new ones

---

## 2026-09-08 — Session 12 (autonomous overnight, cloud routine)

**Confirmed the credential boundary first, per this session's explicit instructions:**
`env | grep -iE "racing|kaggle|betfair"` returned nothing in this container — only
`CCR_ENABLE_TRACING=true` is set. This cloud routine still does not have
`THERACINGAPI_USERNAME`/`THERACINGAPI_PASSWORD` or Kaggle credentials, and cannot reach the real
558K-row Kaggle-loaded dataset (Postgres on Jonathan's Mac only). Did **not** attempt
`scripts/collect_racecards.py`, `scripts/collect_weather.py`, `scripts/load_kaggle_historical.py`,
`scripts/derive_recent_form.py`, `scripts/train_model1.py`, or `scripts/train_model2.py` here.
Racecard/weather collection and the real historical dataset stay **Mac-only** — unconfirmed
otherwise in this file, so not assumed.

**This session's scheduled prompt asked for Phase 6 (a synthetic-fixture statistical/logistic
baseline model).** That work is not new: `src/models/model1_logistic_baseline.py` was built
Session 5, extended Session 7, and real-data trained/validated Sessions 8–9 (it lost to the
market baseline — RL-006). Phase 7 (Model 2, gradient boosting) is also already done (Session
10, RL-008), and RL-004's real draw-bias computation was already built Session 11. `git log` at
the start of this session was already at `b2cf41d` ("RL-004: real course/distance draw-bias
computation"), matching Session 11's own entry exactly. Per this file's own standing instruction
("read BUILD_LOG.md first... follow it"), did not duplicate any of this finished work. Instead
picked up Session 11's own "what the next session should do" item 3(b): **RL-001 (weather
interaction feature), flagged as "still completely untouched by any session" since Session 2.**

**What's genuinely done and verified this session (all real code, all with real passing
tests — 136/136 tests pass via `python3 -m pytest tests/ -v`, up from 106):**
- `src/features/weather_features.py` — **new module**, RL-001's actual feature (as opposed to
  just the hypothesis being logged). `is_all_weather_surface()` classifies a caller-supplied
  surface/going string as AW (`True`), turf (`False`), or ambiguous/missing (`None`, never
  guessed) — whole-word token matching for short markers (AW/Polytrack/Tapeta/Fibresand) so an
  unrelated word merely containing "aw" doesn't false-positive, plus direct phrase matching for
  "all weather"/"all-weather". `turf_rainfall_interaction()` is the RL-001 feature itself: 24h
  rainfall passed through unchanged on turf, forced to exactly 0.0 on AW (a design choice flagged
  for review in the module docstring and RL-004-style in `docs/RESEARCH_LAB.md`, not proven —
  there's no real data yet to check whether a fitted per-surface weight would do better than
  hard-zeroing it), `None` when either input can't be classified. `weather_race_features()`
  combines a `WeatherSnapshot` (already LIVE since Session 1 via
  `src/providers/weather_open_meteo.py`, no API key needed) with a surface string into a flat
  feature dict, same "omit missing, never impute" discipline as `feature_vector.py`. Pure
  computation throughout — no HTTP calls, no DB access, leakage safety and surface-string
  sourcing are the caller's responsibility, same pattern as `draw_bias.py`.
- **Real gap surfaced, not hidden:** `src/providers/racecard_theracingapi.py` has no verified
  surface/going field mapping at all — this module's surface classifier is written against known
  real GB/IRE going descriptions (`"Standard (AW)"`, `"Good to Soft (Turf)"`) but nothing in this
  repo yet supplies that string from a live racecard response. Documented in RL-001 as a second,
  separate blocker alongside the missing real (weather, result) history — confirming the real
  field name/format needs the same "verify against a live response before writing a parser"
  discipline Session 4 used for `off_time`/`off_dt`, and is genuinely Mac-only work (needs a live
  API call).
- `tests/test_weather_features.py` — 29 real tests: parametrised truth tables for
  `is_all_weather_surface()` covering every recognised AW marker, every turf phrasing, and every
  ambiguous/missing case (including a dedicated whole-word-vs-substring regression case),
  `turf_rainfall_interaction()`'s four input combinations (turf+rain, AW+rain, ambiguous+rain,
  clear-surface+missing-rain), and `weather_race_features()`'s merge behaviour (no snapshot →
  `{}`, full snapshot on turf vs AW, ambiguous surface omits only the interaction key while still
  reporting raw weather facts, and a missing individual field is omitted rather than imputed).
- `docs/RESEARCH_LAB.md` RL-001 — status moved from IDEA to **TESTING (partial)**: the
  computation is built and unit-tested, the actual hypothesis (does rainfall genuinely predict
  turf outcomes more than AW) is still completely untested, and is now explicitly blocked on two
  separate things rather than one vague "needs real data" — real (weather, surface, result)
  history AND a verified racecard surface field.
- `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` — directory listing updated: `weather_features.py` and
  `test_weather_features.py` added.
- Full test suite re-run and confirmed green after every change: `./db/setup_local_postgres.sh
  && python3 db/init_db.py` (fresh container, as every prior autonomous session has needed) then
  `python3 -m pytest tests/ -v` → **136/136 passed**, including the DB-backed `tests/test_leakage.py`
  tests against a freshly bootstrapped local Postgres in this container. `pip install pytest
  psycopg2-binary python-dotenv requests scikit-learn` succeeded cleanly this session, no retries
  needed.

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — for real market prices (Phase 4)
2. Kaggle account credentials in THIS cloud environment — the real 558K-row dataset exists but
   only on Jonathan's Mac; this routine cannot reach or reproduce it
3. Racing API results — still needs their Basic tier; not pursuing, Kaggle covers this need
4. A verified racecard surface/going field — new this session, genuinely Mac-only (needs a live
   API call, same discipline Session 4 used for `off_time`)

**What the next session should do, in priority order:**
1. **Check for new credentials as always** — `env | grep -iE "racing|kaggle|betfair"`, recent
   commits, this file. If still cloud-only, don't re-derive that, move on.
2. **The single highest-leverage next steps are all Mac-only and unchanged from Session 11's own
   list, plus one new item:** (a) run `scripts/train_model2.py` against the real Kaggle-loaded DB
   (still not done since Session 10 built it); (b) wire `src/features/draw_bias.py` into a real
   query over the Kaggle data to actually test RL-004's hypothesis; (c) **new:** verify
   `/v1/racecards/free`'s real response for a surface/going field with a live call (the same
   discipline Session 4 used for `off_time`) so `src/features/weather_features.py` can eventually
   be wired to a real racecard instead of only a manually-supplied surface string.
3. If still cloud-only and blocked on real data: there is very little synthetic-only plumbing
   left worth building blind. Worth considering: (a) a hyperparameter sweep for Model 2 on a
   synthetic fixture (Session 10's item 3a, still not done); (b) an `odds_betfair.py` provider
   stub, still flagged as not written since Session 5; (c) re-read
   `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md`'s full section list for any other synthetic-only
   section not yet touched — after RL-001/002/003/004/006/007/008 this list is getting short, be
   honest in the next summary if genuinely nothing useful remains rather than inventing work.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session — add a new dated section above this
   instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/weather data, or any model's training data, to "demo"
  anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not attempt `scripts/collect_racecards.py`, `scripts/collect_weather.py`,
  `scripts/load_kaggle_historical.py`, `scripts/derive_recent_form.py`, `scripts/train_model1.py`,
  or `scripts/train_model2.py` from this cloud routine environment — no credentials/real DB here,
  confirmed again this session, will fail or run against an empty database
- Do not present `weather_features.py`'s synthetic-fixture test results as evidence a real
  turf/AW rainfall effect exists — RL-001's hypothesis itself is still completely untested
- Do not invent or guess a racecard surface/going field mapping — verify it live on Jonathan's
  Mac first, same discipline used for `off_time`/`off_dt`
- Do not skip re-running the full test suite before committing — all 136 tests must actually
  pass, not just the new ones

---

## 2026-09-09 — Session 13 (autonomous overnight, cloud routine)

**Confirmed the credential boundary first, per this session's explicit instructions:**
`env | grep THERACINGAPI` returned nothing in this container — empty, exactly as the
instructions said to expect. Only `CCR_ENABLE_TRACING=true` is set. This cloud routine still
does not have `THERACINGAPI_USERNAME`/`THERACINGAPI_PASSWORD` or Kaggle credentials, and cannot
reach the real 558K-row Kaggle-loaded dataset (Postgres on Jonathan's Mac only). Did **not**
attempt `scripts/collect_racecards.py`, `scripts/collect_weather.py`,
`scripts/load_kaggle_historical.py`, `scripts/derive_recent_form.py`, `scripts/train_model1.py`,
or `scripts/train_model2.py` here. Racecard/weather collection and the real historical dataset
stay **Mac-only** — unconfirmed otherwise in this file, so not assumed.

**This session's scheduled prompt asked for Phase 6 (a synthetic-fixture statistical/logistic
baseline model, built against the real racecard schema).** That work is not new, for the fourth
session running: `src/models/model1_logistic_baseline.py` was built Session 5, extended Session
7, and real-data trained/validated Sessions 8–9 (it lost to the market baseline — RL-006).
Phase 7 (Model 2, gradient boosting) is also already done (Session 10, RL-008). `git log` at the
true start of this session (`origin/main`, after fetching — see environment note below) was
already at `e0dbfec` ("RL-001: real weather turf/AW rainfall interaction feature"), matching
Session 12's own entry exactly. Per this file's own standing instruction ("read BUILD_LOG.md
first... follow it"), did not duplicate any of this finished work. Instead picked up Session
12's own "what the next session should do" item 3(a): **a hyperparameter sweep for Model 2 on a
synthetic fixture, flagged as still not done since Session 10.**

**Environment note (worth flagging, not a data problem):** this container's local `main` ref
was stale on first checkout — `git checkout -B main origin/main` before fetching landed on
`4935d67` (Session 6's commit), seven commits behind the real `origin/main` tip. Running
`git fetch origin main` first, then re-running the same checkout, landed correctly on `e0dbfec`.
Same class of issue Session 3 hit with a stale local ref in a fresh container — worth a future
session always running `git fetch origin main` before trusting a bare `origin/main` ref in a
freshly cloned container, not just after seeing a suspiciously old HEAD.

**Real (if minor) bug found and fixed, unrelated to credentials:** `tests/test_racecard_theracingapi.py`
had 4 failing tests on a clean run — `provider.get_racecards(date(2026, 9, 8), ...)` was hardcoded
against the real capture date, but `TheRacingApiProvider.get_racecards` validates its `for_date`
argument against the real `date.today()` (the free tier only accepts "today"/"tomorrow"). Once
the real calendar date rolled past 2026-09-08 (today is 2026-09-09), every one of those 4 tests
started raising `ValueError` instead of testing what they meant to test. Fixed by calling
`provider.get_racecards(date.today(), region="GB")` instead of the hardcoded literal — none of
the assertions depend on the actual calendar value, only on fields mapped from the fixture
response body, so this doesn't weaken the tests at all, it just stops them from silently rotting
one calendar day at a time. Worth a future session's attention if this pattern shows up
elsewhere: search for other hardcoded `date(2026, ...)` literals passed to date-validating code.

**What's genuinely done and verified this session (all real code, all with real passing
tests — 145/145 tests pass via `python3 -m pytest tests/ -v`, up from 136 + the
test_racecard_theracingapi.py fix above):**
- `src/models/model2_hyperparameter_sweep.py` — **new module**. `sweep_gradient_boosting_hyperparameters()`
  fits `src/models/model2_gradient_boosting.py::fit_gradient_boosting_baseline` once per
  combination in the cartesian product of a caller-supplied hyperparameter grid (e.g.
  `max_depth`/`learning_rate`/`max_iter`), predicts on the same held-out race each time, and
  records whether the expected winner came out top-ranked and with what probability.
  `summarize_sweep()` rolls a list of results up into pass-rate/min/max/mean-probability summary
  stats. This directly answers the question flagged as open since Session 10 and repeated,
  still undone, in Sessions 11 and 12: is Model 2's fitting procedure itself stable across
  reasonable hyperparameter choices, or fragile in a way that would only be discovered after
  burning real wall-clock time on Jonathan's Mac running `scripts/train_model2.py` against the
  real Kaggle data? **Real result (on the synthetic fixture): stable across all 12 combinations
  tested** (`max_depth` in {2,3,4} x `learning_rate` in {0.1,0.3} x `max_iter` in {30,60}) — every
  combination correctly ranked the injected always-wins runner-shape highest on a held-out race,
  none fell to or below uniform. **This is explicitly NOT a real hyperparameter benchmark** — no
  real outcomes exist yet to tune against — only a check that the fitting mechanics themselves
  aren't an accident of the current default kwargs. Labelled as such in the module docstring,
  `docs/RESEARCH_LAB.md` RL-008, and here.
- `tests/test_model2_hyperparameter_sweep.py` — 9 real tests: input validation (empty grid,
  empty grid-value list, empty training set, a requested expected-winner absent from the
  held-out race — all `ValueError`), cartesian-product correctness (a 2x3x1 grid produces
  exactly 6 distinct combinations, none skipped or duplicated, checked against the literal
  parameter tuples expected), the real 12-combination stability assertion described above, and
  `summarize_sweep()`'s roll-up arithmetic hand-verified against both an all-pass and a
  mixed-pass/fail hand-built result list.
- `docs/RESEARCH_LAB.md` RL-008 — updated with the real sweep result and its honest scope
  (stability check, not a benchmark).
- `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` — directory listing updated: `model2_hyperparameter_sweep.py`
  and its test file added.
- Full test suite re-run and confirmed green after every change: `./db/setup_local_postgres.sh
  && python3 db/init_db.py` (fresh container, as every prior autonomous session has needed) then
  `python3 -m pytest tests/ -v` → **145/145 passed**, including the DB-backed `tests/test_leakage.py`
  tests against a freshly bootstrapped local Postgres in this container, and the
  `test_racecard_theracingapi.py` date fix above. `pip install pytest psycopg2-binary
  python-dotenv requests scikit-learn` succeeded cleanly this session, no retries needed.

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — for real market prices (Phase 4)
2. Kaggle account credentials in THIS cloud environment — the real 558K-row dataset exists but
   only on Jonathan's Mac; this routine cannot reach or reproduce it
3. Racing API results — still needs their Basic tier; not pursuing, Kaggle covers this need
4. A verified racecard surface/going field — genuinely Mac-only (needs a live API call, same
   discipline Session 4 used for `off_time`), unchanged since Session 12

**What the next session should do, in priority order:**
1. **Check for new credentials as always** — `env | grep -iE "racing|kaggle|betfair"`, recent
   commits, this file. **Also run `git fetch origin main` before trusting a bare `origin/main`
   ref** — this session's environment note above explains why. If still cloud-only, don't
   re-derive that, move on.
2. **The single highest-leverage next steps are all Mac-only and unchanged from Session
   11/12's own list:** (a) run `scripts/train_model2.py` against the real Kaggle-loaded DB
   (still not done since Session 10 built it — this session's hyperparameter-stability result
   means it can be run with confidence in the default kwargs); (b) wire
   `src/features/draw_bias.py` into a real query over the Kaggle data to actually test RL-004's
   hypothesis; (c) verify `/v1/racecards/free`'s real response for a surface/going field with a
   live call so `src/features/weather_features.py` can eventually be wired to a real racecard.
3. If still cloud-only and blocked on real data: **there is genuinely very little synthetic-only
   plumbing left worth building blind at this point** — four consecutive autonomous sessions
   (10, 11, 12, 13) have each found and closed one more remaining gap (Model 2, draw bias,
   weather, Model 2 hyperparameter stability), and the honest state now is that nearly
   everything buildable without real data access has been built and tested. Worth considering
   if truly nothing else surfaces: (a) an `odds_betfair.py` provider stub against Betfair's
   public Exchange API docs, still flagged as not written since Session 5 — this remains the
   one clearly-still-open synthetic-only item; (b) re-read this file's full history for any
   flagged-but-unaddressed design choice (e.g. RL-001's "force AW rainfall to exactly 0.0 vs a
   fitted per-surface weight" — still just a flagged design choice, not a task) before inventing
   new work for its own sake.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session — add a new dated section above this
   instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/weather data, or any model's training data, to "demo"
  anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not attempt `scripts/collect_racecards.py`, `scripts/collect_weather.py`,
  `scripts/load_kaggle_historical.py`, `scripts/derive_recent_form.py`, `scripts/train_model1.py`,
  or `scripts/train_model2.py` from this cloud routine environment — no credentials/real DB here,
  confirmed again this session, will fail or run against an empty database
- Do not present `model2_hyperparameter_sweep.py`'s synthetic-fixture stability result as
  evidence about which hyperparameters are best for real racing — it only shows the fitting
  procedure itself isn't fragile, nothing about real predictive accuracy
- Do not skip re-running the full test suite before committing — all 145 tests must actually
  pass, not just the new ones

---

## 2026-09-09 — Session 14 (autonomous overnight, cloud routine)

**Confirmed the credential boundary first, per this session's explicit instructions:**
`env | grep THERACINGAPI` returned nothing in this container — empty, exactly as expected. Only
`CCR_ENABLE_TRACING=true` is set. This cloud routine still does not have
`THERACINGAPI_USERNAME`/`THERACINGAPI_PASSWORD` or Kaggle credentials, and cannot reach the real
558K-row Kaggle-loaded dataset (Postgres on Jonathan's Mac only). Did **not** attempt
`scripts/collect_racecards.py`, `scripts/collect_weather.py`, `scripts/load_kaggle_historical.py`,
`scripts/derive_recent_form.py`, `scripts/train_model1.py`, or `scripts/train_model2.py` here.
Racecard/weather collection and the real historical dataset stay **Mac-only** — unconfirmed
otherwise in this file, so not assumed. `git fetch origin main` first confirmed the local ref
was already at `origin/main`'s tip (`8c83a46`, Session 13's own commit) — no stale-ref issue this
time.

**This session's scheduled prompt asked for Phase 6 (a synthetic-fixture statistical/logistic
baseline model).** That work is not new, for the fifth session running:
`src/models/model1_logistic_baseline.py` was built Session 5, extended Session 7, real-data
trained/validated Sessions 8–9 (it lost to the market baseline — RL-006), and Phase 7 (Model 2,
gradient boosting) is also already done (Session 10, RL-008) with a hyperparameter-stability
check added Session 13. Per this file's own standing instruction ("read BUILD_LOG.md first...
follow it"), did not duplicate any of this finished work. Instead picked up Session 13's own
"what the next session should do" item 3(a) — the one item every session since Session 5 has
flagged as "the one clearly-still-open synthetic-only item": **an `odds_betfair.py` provider
stub against Betfair's public Exchange API docs.**

**What's genuinely done and verified this session (all real code, all with real passing
tests — 153/153 tests pass via `python3 -m pytest tests/ -v`, up from 145):**
- `src/providers/odds_betfair.py` — **new**, implements `OddsProvider` (already defined in
  `src/providers/base.py` since Session 1, never previously implemented). Written against
  Betfair's public Betting API docs (JSON-RPC method names/params/response shapes:
  `listMarketCatalogue` for runner names, `listMarketBook` with `EX_BEST_OFFERS` for best back/lay
  prices — a market's runner NAMES and its PRICES come back from two separate calls, keyed only
  by `selectionId`, so `get_odds()` merges them and skips any selectionId present in the price
  book but absent from the name catalogue rather than fabricating a name). **This is a STUB,
  genuinely untested against a real account** — same honest status `racecard_theracingapi.py`
  carried before Session 4 verified it live — because there is no Betfair Delayed App Key to test
  against (still BLOCKED, `docs/FREE_DATA_SOURCES.md` #4). Labelled as such in the module
  docstring, `docs/FREE_DATA_SOURCES.md`, `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md`, and here — do
  not trust any field mapping below until a live call actually confirms it, the same discipline
  Session 4 used to catch the real `off_time`/`off_dt` ambiguity bug.
- **Two real, honestly-documented gaps surfaced, not solved (deliberately, same discipline as
  `weather_features.py`'s unmapped surface field from Session 12):** (1) Betfair auth needs a
  session token from a *separate* login step (Betfair's identity service,
  identitysso.betfair.com) that this provider does not perform — a session token expires and
  re-authenticating is either an interactive login or a client-certificate setup, which is
  Jonathan's call to make, not something to build blind against undocumented specifics; (2)
  Betfair identifies a race by its own `marketId` (e.g. `"1.170258175"`), a completely different
  ID space from The Racing API's `race_id` (e.g. `"rac_32297295303"`) — there is no
  course-name/off-time reconciliation logic anywhere in this repo yet to map one provider's race
  identity to the other's, and wiring this provider into the rest of the pipeline needs that step
  first. Both documented in the module docstring rather than papered over with a guess.
- `tests/test_odds_betfair.py` — 8 real tests, against a fixture shaped from Betfair's publicly
  documented response format (explicitly NOT a real captured response, unlike
  `test_racecard_theracingapi.py`'s fixture — flagged in the test file's own docstring): missing
  credentials raises `RuntimeError`; runner names and prices correctly merged by `selectionId`
  across the two separate calls; the best (first-rung) back/lay price is used, not just any rung;
  an empty price ladder (no current liquidity on one side) returns `None`, not `0` or a crash; a
  `selectionId` present in the price book but absent from the name catalogue is skipped entirely,
  never given a fabricated name; a JSON-RPC top-level `"error"` key (the documented way Betfair
  signals a failure on an otherwise-200 HTTP response) raises `RuntimeError` rather than being
  silently swallowed as an empty result; the `_best_price` helper's edge cases (`None`, empty
  list, single/multiple rungs) tested directly; `observed_at` is a real, timezone-aware UTC
  datetime captured at call time.
- `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` — directory listing updated: the old aspirational
  "`(odds_betfair.py — NOT YET WRITTEN...)`" placeholder line replaced with the real file's actual
  status; `test_odds_betfair.py` added to the test listing.
- `docs/FREE_DATA_SOURCES.md` #4 (Betfair) — updated with the new stub's real status and the two
  gaps above, without changing the underlying BLOCKED status (still needs Jonathan's account).
- Full test suite re-run and confirmed green after every change: `./db/setup_local_postgres.sh &&
  python3 db/init_db.py` (fresh container, as every prior autonomous session has needed) then
  `python3 -m pytest tests/ -v` → **153/153 passed**, including the DB-backed `tests/test_leakage.py`
  tests against a freshly bootstrapped local Postgres in this container. `pip install pytest
  psycopg2-binary python-dotenv requests scikit-learn` succeeded cleanly this session, no retries
  needed.

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — for real market prices (Phase 4); the provider code now exists but
   is genuinely untested against a live account
2. Kaggle account credentials in THIS cloud environment — the real 558K-row dataset exists but
   only on Jonathan's Mac; this routine cannot reach or reproduce it
3. Racing API results — still needs their Basic tier; not pursuing, Kaggle covers this need
4. A verified racecard surface/going field — genuinely Mac-only (needs a live API call), unchanged
   since Session 12
5. **New this session:** a Betfair marketId ↔ Racing API race_id reconciliation step (needed
   before `odds_betfair.py` can be wired into the rest of the pipeline even once real credentials
   exist) — not a Jonathan-signup blocker, a genuinely-not-yet-built piece of plumbing

**What the next session should do, in priority order:**
1. **Check for new credentials as always** — `env | grep -iE "racing|kaggle|betfair"`, recent
   commits, this file. **Also run `git fetch origin main` before trusting a bare `origin/main`
   ref** (Session 13's note, still good practice). If still cloud-only, don't re-derive that,
   move on.
2. **The single highest-leverage next steps are all Mac-only and unchanged from Sessions
   11/12/13's own list:** (a) run `scripts/train_model2.py` against the real Kaggle-loaded DB
   (still not done since Session 10 built it); (b) wire `src/features/draw_bias.py` into a real
   query over the Kaggle data to actually test RL-004's hypothesis; (c) verify
   `/v1/racecards/free`'s real response for a surface/going field with a live call so
   `src/features/weather_features.py` can eventually be wired to a real racecard.
3. If still cloud-only and blocked on real data: **genuinely very little synthetic-only plumbing
   remains.** Five consecutive autonomous sessions (10–14) have each closed one more remaining gap
   (Model 2, draw bias, weather, Model 2 hyperparameter stability, the Betfair odds stub). What's
   left, if truly nothing else surfaces: (a) the race-identity reconciliation step flagged as
   blocker 5 above — a pure function matching (course_name, off_time) across two providers'
   racecards, buildable and testable against synthetic fixtures shaped like both providers' real
   schemas without needing either provider's live credentials; (b) revisit any flagged-but-still-
   just-flagged design choice from earlier sessions (e.g. RL-001's "force AW rainfall to exactly
   0.0 vs. a fitted per-surface weight") before inventing new work for its own sake; (c) be honest
   in the next summary if nothing genuinely useful remains rather than manufacturing scaffolding.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session — add a new dated section above this
   instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/weather data, or any model's training data, to "demo"
  anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not attempt `scripts/collect_racecards.py`, `scripts/collect_weather.py`,
  `scripts/load_kaggle_historical.py`, `scripts/derive_recent_form.py`, `scripts/train_model1.py`,
  or `scripts/train_model2.py` from this cloud routine environment — no credentials/real DB here,
  confirmed again this session, will fail or run against an empty database
- Do not present `odds_betfair.py`'s docs-shaped fixture test results as evidence its field
  mapping is correct against a real Betfair account — that has not been checked, unlike
  `racecard_theracingapi.py`'s real captured-response fixture
- Do not implement Betfair's login/session-token flow speculatively — it needs Jonathan's account
  and a real decision (password login vs. certificate), not a guess
- Do not skip re-running the full test suite before committing — all 153 tests must actually
  pass, not just the new ones

---

## 2026-09-09 — Session 15 (autonomous overnight, cloud routine)

**Confirmed the credential boundary first, per this session's explicit instructions:**
`env | grep THERACINGAPI` returned nothing in this container — empty, exactly as the
instructions said to expect. Only `CCR_ENABLE_TRACING=true` is set. This cloud routine still
does not have `THERACINGAPI_USERNAME`/`THERACINGAPI_PASSWORD` or Kaggle/Betfair credentials, and
cannot reach the real 558K-row Kaggle-loaded dataset (Postgres on Jonathan's Mac only). Did
**not** attempt `scripts/collect_racecards.py`, `scripts/collect_weather.py`,
`scripts/load_kaggle_historical.py`, `scripts/derive_recent_form.py`, `scripts/train_model1.py`,
or `scripts/train_model2.py` here. Racecard/weather collection and the real historical dataset
stay **Mac-only** — unconfirmed otherwise in this file, so not assumed. `git fetch origin main`
first (Session 13/14's own advice, still good practice) confirmed this container's local `main`
ref was stale — a bare `git branch -vv` showed it 9 commits behind `origin/main` even though
`HEAD` itself was already correctly detached at `origin/main`'s real tip (`42ed93e`, Session 14's
own commit). Fixed with `git checkout -B main origin/main` before starting, same class of issue
Sessions 3/13 hit before.

**This session's scheduled prompt asked for Phase 6 (a synthetic-fixture statistical/logistic
baseline model).** That work is not new, for the sixth session running:
`src/models/model1_logistic_baseline.py` was built Session 5, extended Session 7, real-data
trained/validated Sessions 8–9 (it lost to the market baseline — RL-006), and Phase 7 (Model 2,
gradient boosting) is also already done (Session 10, RL-008) with a hyperparameter-stability
check added Session 13. Per this file's own standing instruction ("read BUILD_LOG.md first...
follow it"), did not duplicate any of this finished work. Instead picked up Session 14's own
"what the next session should do" item 3(a) — the one concrete, genuinely-not-yet-built piece of
plumbing it flagged: **the race-identity reconciliation step (Betfair marketId ↔ Racing API
race_id)**, buildable and testable against synthetic fixtures without needing either provider's
live credentials.

**What's genuinely done and verified this session (all real code, all with real passing
tests — 170/170 tests pass via `python3 -m pytest tests/ -v`, up from 153):**
- `src/reconciliation/race_identity.py` — **new module**, `reconcile_race_identities()`. Matches
  each Racing API `RaceCard` (real schema, `src/providers/base.py`/`racecard_theracingapi.py`) to
  at most one Betfair market (`BetfairMarketIdentity`, a new minimal dataclass —
  `market_id`/`venue`/`market_start_time` — written against Betfair's public
  `listMarketCatalogue` docs, same "not yet live-verified" status the rest of `odds_betfair.py`
  carries) by normalized course name (`normalize_course_name()`: case/punctuation/whitespace-
  insensitive, strips only "Racecourse" and AW/"All Weather" qualifiers, deliberately does NOT
  fuzzy-match genuinely different course spellings) plus closest off-time within a configurable
  tolerance (default 5 minutes). Greedy nearest-in-time-first assignment so a race is never
  stolen from its true match by a coarser candidate processed earlier. Pure computation only — no
  HTTP, no DB access, same pattern as `draw_bias.py`/`weather_features.py`; leakage/timezone
  alignment stays the caller's explicit responsibility, documented as gap #1 in the module
  docstring (Racing API's `off_time` has no timezone attached; Betfair's `marketStartTime` is
  documented UTC; nothing has confirmed live whether the two line up — this function does a
  naive wall-clock comparison, not a real conversion, so a genuine mismatch fails safe by
  matching nothing rather than matching wrong).
- `tests/test_race_identity.py` — 17 real tests: course-name normalization truth table (case/
  punctuation/whitespace/"Racecourse"/AW-qualifier variants all collapse together; the
  deliberate "Newmarket (July)" vs "Newmarket July Course" non-match case, proving this doesn't
  over-fuzzy-match), exact/within-tolerance/at-the-boundary time matches, a beyond-tolerance
  non-match, a different-course-same-time non-match, two multi-candidate greedy-assignment cases
  (closest-in-time pairing wins regardless of input list order; a closer racecard wins a shared
  market over a farther one, correctly leaving the loser unmatched rather than guessed), a
  tz-aware `market_start_time` handled without crashing, and defensive/input-validation cases
  (negative tolerance rejected, unparseable `off_time` left unmatched not crashed, empty inputs
  return an empty result). **One real bug caught by these tests before being shipped:** the first
  draft's "all weather"/"all-weather" stripping only checked each whitespace-split TOKEN against
  a suffix list, so the two-word phrase "all weather" (post-punctuation-strip, from either
  "All Weather" or "All-Weather") never matched — a single token can't equal a two-word string.
  `pytest` caught it immediately (`test_normalize_strips_aw_qualifiers` failed on
  `"Kempton - All Weather"` specifically, not the other AW variants), fixed with a phrase-level
  regex strip before the per-token filter runs, not shipped uncaught — same "found and fixed
  live, not glossed over" discipline as `draw_bias.py`'s Session 11 bucket-boundary bug.
- `src/providers/odds_betfair.py` docstring updated: the "no reconciliation logic anywhere in
  this repo yet" line (Session 14) now correctly points at this new module and its status
  (matching LOGIC done and tested; the underlying course-name/clock-alignment ASSUMPTION still
  completely untested; not yet wired into this provider or any real pipeline).
- `docs/RESEARCH_LAB.md` — new entry RL-009: explicit about the implementation-vs-hypothesis
  split (same discipline as RL-004/RL-008) — the matching logic being correct is a separate claim
  from the matching assumption being true, and only the first is shown here.
- `docs/SILENT_EDGE_ZERO_ARCHITECTURE.md` — directory listing updated: `reconciliation/` module
  and `test_race_identity.py` added; the stale "no reconciliation logic built yet" line under
  `odds_betfair.py` corrected to point at the new module.
- Full test suite re-run and confirmed green after every change: `./db/setup_local_postgres.sh
  && python3 db/init_db.py` (fresh container, as every prior autonomous session has needed) then
  `python3 -m pytest tests/ -v` → **170/170 passed**, including the DB-backed `tests/test_leakage.py`
  tests against a freshly bootstrapped local Postgres in this container. `pip install pytest
  psycopg2-binary python-dotenv requests scikit-learn` succeeded cleanly this session, no retries
  needed.

**What this changes for future sessions:** this closes blocker 5 from Session 14's own list (the
race-identity reconciliation gap). It does NOT unblock Betfair odds in any real sense — the
Delayed App Key is still the actual blocker, unchanged — and the matching function's own
underlying assumption (does course-name spelling and clock actually line up between the two
providers on a real capture) is still completely untested; that needs live Betfair credentials
the same as everything else in `odds_betfair.py`.

**What's still blocked (unchanged):**
1. Betfair Delayed App Key — for real market prices (Phase 4); the provider code and the
   race-identity matching logic now both exist but neither is tested against a live account
2. Kaggle account credentials in THIS cloud environment — the real 558K-row dataset exists but
   only on Jonathan's Mac; this routine cannot reach or reproduce it
3. Racing API results — still needs their Basic tier; not pursuing, Kaggle covers this need
4. A verified racecard surface/going field — genuinely Mac-only (needs a live API call), unchanged
   since Session 12

**What the next session should do, in priority order:**
1. **Check for new credentials as always** — `env | grep -iE "racing|kaggle|betfair"`, recent
   commits, this file. **Also run `git fetch origin main` before trusting a bare `origin/main`
   ref** — this session hit the same stale-local-ref issue Sessions 3/13 already documented;
   `git checkout -B main origin/main` after fetching is the fix, don't re-diagnose it.
2. **The single highest-leverage next steps are all Mac-only and unchanged from Sessions
   11–14's own list:** (a) run `scripts/train_model2.py` against the real Kaggle-loaded DB
   (still not done since Session 10 built it — five sessions running now); (b) wire
   `src/features/draw_bias.py` into a real query over the Kaggle data to actually test RL-004's
   hypothesis; (c) verify `/v1/racecards/free`'s real response for a surface/going field with a
   live call so `src/features/weather_features.py` can eventually be wired to a real racecard.
3. If still cloud-only and blocked on real data: **genuinely very little synthetic-only plumbing
   remains at this point.** Six consecutive autonomous sessions (10–15) have each closed one more
   remaining gap (Model 2, draw bias, weather, Model 2 hyperparameter stability, the Betfair odds
   stub, race-identity reconciliation). Be honest in the next summary if nothing genuinely useful
   surfaces rather than manufacturing scaffolding for its own sake — consider explicitly whether
   the honest report is "there is nothing left to build blind; the project now needs Jonathan's
   Mac time (Model 2's real run, draw bias's real test, or a surface-field live check) more than
   another autonomous session" rather than inventing a seventh synthetic-only task.
4. Keep using `db/setup_local_postgres.sh` at the start of any session that touches the DB.
5. Keep this file updated at the end of every session — add a new dated section above this
   instruction, don't overwrite prior sessions' entries.

**Do NOT do, even if it seems like faster progress (still applies):**
- Do not fabricate racecard/odds/result/weather data, or any model's training data, to "demo"
  anything
- Do not create accounts on Jonathan's behalf (Betfair)
- Do not attempt `scripts/collect_racecards.py`, `scripts/collect_weather.py`,
  `scripts/load_kaggle_historical.py`, `scripts/derive_recent_form.py`, `scripts/train_model1.py`,
  or `scripts/train_model2.py` from this cloud routine environment — no credentials/real DB here,
  confirmed again this session, will fail or run against an empty database
- Do not present `race_identity.py`'s synthetic-fixture test results as evidence the matching
  actually works against real course-name spellings/clocks from both providers — that assumption
  is still completely untested, only the matching LOGIC is proven correct
- Do not skip re-running the full test suite before committing — all 170 tests must actually
  pass, not just the new ones
