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
