# Research Lab

Every modelling hypothesis, tracked honestly. Most will fail — that's expected (Section 39).

Status values: IDEA / TESTING / FAILED / PROMISING / VALIDATED / PRODUCTION

---

## RL-001: Weather materially improves prediction accuracy on AW vs turf

- **Hypothesis:** All-weather (AW) surfaces are less weather-sensitive than turf; a weather-interaction feature should show near-zero effect on AW races and a real effect on turf, particularly on going-adjacent features (rainfall correlating with turf going changes).
- **Why it might work:** turf going is directly driven by rainfall; AW surfaces are engineered to be more consistent.
- **Implementation:** `src/features/weather_features.py` (2026-09-08, autonomous overnight session) — `is_all_weather_surface()` classifies a caller-supplied surface/going string as AW/turf/ambiguous (never guessed on an unrecognised string), `turf_rainfall_interaction()` is the actual RL-001 feature (24h rainfall passed through on turf, forced to exactly 0.0 on AW, `None` when either input can't be classified), `weather_race_features()` combines a `WeatherSnapshot` (already LIVE, `src/providers/weather_open_meteo.py`, no key needed) with a surface string into a flat feature dict, same "omit missing, never impute" rule as `feature_vector.py`. Pure computation, no HTTP/DB access — the caller supplies both the snapshot and the surface string, same discipline as `draw_bias.py`'s caller-supplied historical records.
- **Design choice flagged for review, not proven:** forcing the interaction to exactly 0.0 on AW bakes the hypothesis in as a fixed assumption rather than letting a fitted model discover a per-surface effect itself — there's no real data yet to compare the two approaches.
- **Real gap this exposed:** `src/providers/racecard_theracingapi.py` has no verified surface/going field mapping at all yet — `weather_features.py`'s surface classifier is written against known real GB/IRE going descriptions (e.g. `"Standard (AW)"`, `"Good to Soft (Turf)"`) but nothing in this repo yet supplies that string from a live racecard. Confirming the real field name/format (same "verify against a live response before writing a parser" discipline used for `off_time`/`off_dt` and results) is needed before this feature can run on anything but a manually-supplied surface string.
- **Training/validation period:** TBD, needs real racecard history (with a verified surface field) + real weather + real results, all joined, before RL-001's actual hypothesis can be tested.
- **Status: TESTING (partial)** — the feature computation is built and unit-tested (`tests/test_weather_features.py`, 2026-09-08) against synthetic surface strings and a synthetic `WeatherSnapshot`; the real hypothesis (does rainfall genuinely predict turf outcomes more than AW ones) is still completely untested, and is now blocked on two things, not one: real (weather, result) history AND a verified racecard surface field.

## RL-002: Overround-removal method choice (proportional vs power vs Shin) materially changes calibration

- **Hypothesis:** Shin's method, by modelling favourite-longshot bias explicitly, should produce better-calibrated market-probability baselines than proportional scaling, particularly at the long-odds end of the field.
- **Why it might work:** proportional scaling assumes overround is spread evenly across all runners, which doesn't match observed bookmaker behaviour (shorter-priced runners typically carry proportionally less margin).
- **Implementation:** `src/market/probability.py` — all three methods built and unit-tested (2026-09-08).
- **Training/validation period:** needs real historical odds + results to actually benchmark against — the current tests only confirm the methods are mathematically correct (sum to 1, favourite gets highest probability), not which is more accurate.
- **Status: TESTING (partial)** — implementation done and correct, empirical benchmark blocked on real odds history (needs The Racing API or Betfair access).

## RL-003: Recency-weighted form score vs simple average finishing position

- **Hypothesis:** weighting a horse's most recent runs more heavily (linear weights, most recent = highest) predicts better than a flat average of the same runs.
- **Why it might work:** form is not static — a horse improving or declining recently is more informative than an old good/bad run buried in a longer form string.
- **Implementation:** `src/features/runner_features.py::form_score(recency_weighted=True)` — both the weighted and unweighted variants are implemented so they can be compared directly once real results exist.
- **Design choice flagged for review:** non-completion codes (F/P/U/O/R/S/B) are scored as a fixed penalty (12 — worse than any real finishing position) rather than dropped from the form string. This is a reasonable default, not a validated one — worth checking whether a fall vs a pulled-up run should really carry the same weight once real data can distinguish them.
- **Training/validation period:** TBD, needs real racecard + result history first.
- **Status: IDEA** — implemented and unit-tested against synthetic form strings only (2026-09-08); no real predictive comparison yet.

## RL-004: Draw percentile as a neutral geometric feature vs a track-specific bias feature

- **Hypothesis:** a raw draw_percentile (0 = rail, 1 = widest, based only on the field present) is a weaker feature than a track+distance-specific historical draw bias, but is a reasonable and honest placeholder until real per-course historical data exists.
- **Why it might work / why it's a placeholder:** genuine draw bias is course- and distance-specific (e.g. a low draw can be a major advantage at one course/distance and irrelevant at another) — that requires historical results grouped by course+distance, which the real 558K-row Kaggle-loaded dataset (Sessions 6/8/9) now genuinely provides, but that data lives only on Jonathan's Mac.
- **Implementation (placeholder, in the model's actual feature set):** `src/features/runner_features.py::draw_bias_features()` — deliberately does NOT claim any bias direction, just the neutral positional fact.
- **Implementation (the real hypothesis itself, new this session):** `src/features/draw_bias.py::compute_course_distance_draw_bias()` — buckets historical (course, distance, surface, draw) runners into `num_buckets` draw groups and returns the queried draw's own bucket win rate against the group's overall baseline win rate (the actual "bias" signal), gated by `min_sample_size` so a sparse course/distance/surface combination honestly returns `None` rather than a noisy number. Leakage safety is the CALLER's responsibility (same discipline as `scripts/derive_recent_form.py`) — the module itself does no date filtering and no DB access, pure aggregation only. Tested with hand-verified win-rate arithmetic against synthetic fixtures (`tests/test_draw_bias.py`, 13 tests) — **not yet run against the real Kaggle history**, so RL-004's actual hypothesis is still untested, only its computation is now built and correct.
- **Training/validation period:** TBD — needs the real Kaggle-loaded (course, distance, draw, finishing_position) rows, Mac-only, plus deciding whether to wire the result into Model 1/2's feature vector as a sixth feature or keep it as a standalone diagnostic first.
- **Status: TESTING (partial)** — the real computation is built and unit-tested; the hypothesis itself (does a genuine course/distance draw bias exist and does it help) is still open, exactly as before, just no longer blocked on missing plumbing.

## RL-005: Market baseline (Model 0) as the bar every real model must clear

- **Hypothesis:** the de-vigged market-implied probability (src/market/probability.py), used directly as a "prediction" with no fitting at all, is already a strong baseline — real money is priced into it. Any trained model built later (Phase 6+) that can't beat Model 0's Brier score / log loss on the same walk-forward test windows isn't adding information the market didn't already have.
- **Why it might work / why it's the right null hypothesis:** bookmaker/exchange odds already aggregate a lot of public information (form, ratings, weather, etc.) through pricing behaviour. A model that can't beat this baseline is, at best, redundant with the market.
- **Implementation:** `src/models/model0_market_baseline.py::predict_race_probabilities` (wraps the existing overround-removal methods) + `evaluate_market_baseline_walk_forward` (wires it through the walk-forward split harness and calibration scoring end-to-end). Tested with hand-verified Brier scores against synthetic zero-overround odds (2026-09-08) — see `tests/test_model0_market_baseline.py`.
- **Design choice flagged for review:** which of the three overround-removal methods (proportional/power/Shin, see RL-002) Model 0 should default to is still unresolved — same blocker as RL-002, needs real odds history to benchmark.
- **Training/validation period:** TBD — Model 0 has no training step by design, but its *evaluation* needs real (race_date, odds, winner) rows, which needs The Racing API or Betfair access (both blocked, see FREE_DATA_SOURCES.md).
- **Real result (2026-09-08, `scripts/train_model1.py`, real Kaggle-sourced starting prices as odds, power de-vig method):** confirmed as the bar to clear. Pooled Brier=0.0795, log loss=0.2738 across 18 walk-forward folds (2023-06 to 2026-06), ~484k real runner predictions. Beat Model 1 on every single fold, no exceptions.
- **Status: VALIDATED as a real, working baseline.** Whether power is the *best* de-vig method (vs. proportional/Shin) is still open — see RL-002.

## RL-006: Model 1 — a fitted, per-race logistic/softmax baseline over race-relative features

- **Hypothesis:** a simple multinomial logit (softmax) over five race-relative runner
  features — official rating vs. field mean, draw percentile vs. 0.5, recency-weighted form
  score vs. field mean, weight vs. field mean, and a missing-rating indicator (added Session
  7, see below) — fit by gradient ascent on observed winners, should beat Model 0's market
  baseline once it can be trained on real (racecard, result) pairs, by using the same
  information a market-derived probability implicitly prices in but making it explicit and
  auditable per feature.
- **Why it might work / why it's still just an idea:** the first four features are exactly the
  ones `src/features/runner_features.py` (Sections 8/10) already computes and tests; wiring
  them into a per-race softmax is the standard "conditional logit" formulation for a discrete
  choice among race entrants, so the probability-per-race-sums-to-1.0 property comes for free
  rather than needing a second normalisation pass. This is genuinely untested against real
  outcomes, though — The Racing API still only returns racecards (results need its paid Basic
  tier, not pursued — Session 5 interactive) and this cloud routine cannot reach it at all (no
  credentials here). Session 6 (interactive, Jonathan's Mac) *did* load 558,370 real historical
  runner results via Kaggle into the local database on that machine — the first real (racecard-
  shaped, result) pairs anywhere in this project — but that data and DB state live only on
  Jonathan's Mac; this cloud routine has no Kaggle credentials either and cannot reach or
  reproduce it (confirmed again Session 7, `env | grep -iE "racing|kaggle|betfair"` empty), so
  nothing here is evidence the features or their sign actually predict winners. Training Model 1
  against that real Kaggle data is Mac-only work for a future interactive session.
- **Design choice flagged for review (Session 5) and partially addressed (Session 7):** every
  feature is deliberately UNDIRECTED (centered on the race's own mean, sign decided by the
  fitted weight, not asserted up front) — same discipline as RL-004's draw_percentile. A runner
  missing an underlying field still gets 0.0 for that one feature ("no evidence either way") for
  draw/form/weight. For official_rating specifically, Session 7 added a fifth feature,
  `no_rating_flag` (1.0 when official_rating is missing, 0.0 otherwise, its own separately
  fitted weight), so a debutant-shaped runner (no rating at all) is no longer indistinguishable
  from a genuinely average-rated one — the model can now learn whether missingness itself
  carries signal, rather than that possibility being silently foreclosed by defaulting to 0.0.
  Still synthetic-only: a convergence test confirms gradient ascent recovers the sign of an
  *injected* debutant-never-wins pattern, which proves the maths works, not that real debutants
  actually underperform.
- **Implementation:** `src/models/model1_logistic_baseline.py::build_race_features`,
  `predict_race_probabilities`, `fit_logistic_baseline` (pure-Python batch gradient ascent, no
  numpy/scikit-learn — see the module docstring for why). Tested with hand-verified
  single-gradient-step calculations and two convergence checks — rating-determines-the-winner
  (Session 5) and debutant-never-wins (Session 7, cloud) — in
  `tests/test_model1_logistic_baseline.py`, fixtures shaped exactly like the real, verified
  racecard schema (`tests/test_racecard_theracingapi.py`).
- **Real result (2026-09-08, Session 8 interactive, `scripts/train_model1.py`, walk-forward,
  min_train_days=180, test_window_days=60, iterations=150, real Kaggle-sourced results 2023-06
  to 2026-06):** Model 1 lost to Model 0 (market baseline, RL-005) on Brier score and log loss
  on every single one of 18 out-of-sample folds — pooled Brier=0.0896 vs. Model 0's 0.0795, log
  loss=0.3199 vs. 0.2738, across ~487k real runner predictions. This is genuinely the first
  time this hypothesis has been tested against a real outcome, and the hypothesis (Model 1
  beats the market) did NOT hold. Calibration is good, though (predicted probability tracks
  actual win rate closely in every bin with meaningful volume, e.g. predicted 0.074 vs. actual
  0.074 on 284,519 predictions) — the model is honest, just not (yet) as informative as the
  market. This run used the 4-feature model from before Session 7's `no_rating_flag` addition
  landed on `origin/main`; re-running with all 5 features is a natural next step.
- **Confound resolved (2026-09-08, same session):** `scripts/derive_recent_form.py` built a
  real, leakage-safe `recent_form`/`days_since_last_run` for 481,186 of 558,866 runner_snapshot
  rows (the remainder are each horse's first appearance in the dataset — left NULL honestly,
  not guessed), by walking each horse's own prior rows in date order and using only its
  strictly-earlier races. Spot-checked against a real horse's full race history — form strings
  (e.g. `431258U`) and non-completion codes (UR, PU) matched the real result sequence exactly.
- **Real result, re-run with the full 5-feature model (`no_rating_flag` merged +
  real form) — the clean, complete test of this hypothesis:** pooled Brier=0.0875,
  log loss=0.3093 across the same 18 folds, ~487k predictions — a genuine improvement over the
  3-working-feature run (0.0896), narrowing the gap to Model 0 from 0.0101 to 0.0080. Still did
  NOT beat the market baseline (0.0795) on any fold. Calibration held up and gained resolution
  (more predictions now land in the 0.2–0.7 bins where form/rating actually differentiate
  runners), still tracking actual outcomes closely bin-by-bin.
- **Status: TESTING — clean, complete result in (no more open feature confounds). Model 1
  in its current 5-feature shape does NOT beat the market**, though it's closer than the
  incomplete first attempt. This is now a fair conclusion, not one waiting on missing data.
  Next real step for RL-006 is a genuinely different model (Model 2, gradient boosting per
  the build brief's Phase 7) or richer features (course/distance-specific draw bias per
  RL-004, weather per RL-001) rather than re-testing this same feature shape again.

## RL-007: Kaggle CSV has no form/days-since-last-run field — must be derived, not loaded

- **Finding, not a hypothesis:** `data/kaggle_historical/.../raceform.csv` has no
  `recent_form` or `days_since_last_run` column (confirmed by reading the raw header,
  2026-09-08) — `scripts/load_kaggle_historical.py` never populated
  `runner_snapshot.recent_form` because there was never a source column to read it from, not
  because of a loader bug. The CSV does have per-horse rows across many dates (`horse`,
  `date`, `pos`, `or`, `rpr`, `ts`), so a real form feature is derivable — for each runner,
  look up that same horse's own prior rows with `date` strictly before the current race's date
  and build a form string / recency-weighted score from their finishing positions — but this
  is a real data-engineering task, not a config flip. See RL-006 for why this matters now (it's
  the likely reason Model 1 underperformed its first real test).
- **Resolved (2026-09-08, same session):** `scripts/derive_recent_form.py` — a one-shot
  backfill, not part of the live daily collector — built exactly this, leakage-safe by
  construction (only strictly-earlier races per horse), for 481,186 of 558,866 rows. Spot-check
  against a real horse's full history confirmed correctness, including non-completion codes.
  See RL-006 for the resulting real re-run.
- **Status: DONE.**

## RL-008: Model 2 — gradient-boosted trees over the same features, a different model class

- **Hypothesis:** RL-006 concluded that Model 1's linear conditional-logit could not beat the
  market baseline even with a clean, confound-free 5-feature set, and that further tuning of
  that same feature shape was unlikely to close the gap. A model class capable of
  nonlinearities and feature interactions — gradient-boosted decision trees — over the SAME
  5 features might capture structure a linear score cannot (e.g. "rating only matters when
  draw is also favourable"), and should be tested before concluding this feature family is
  exhausted.
- **Why it might work / why it's still just an idea:** this is genuinely untested against real
  outcomes — the same status Model 1 had before Sessions 8/9 trained it on real Kaggle data.
  This cloud routine has no THERACINGAPI_* or Kaggle credentials (confirmed again this
  session, `env | grep THERACINGAPI` empty) and cannot reach or reproduce the real 558K-row
  historical dataset that lives only in Postgres on Jonathan's Mac.
- **Design choice flagged for review:** Model 2 is a per-runner INDEPENDENT binary classifier
  (P(win) per runner, sklearn's HistGradientBoostingClassifier), not a true joint per-race
  model the way Model 1's softmax is — raw outputs are renormalised to sum to 1.0 per race
  after the fact (`_renormalize` in `src/models/model2_gradient_boosting.py`). This is a
  simpler normalisation than a genuinely joint tree model would need (it can't represent "if
  runner A is strong, runner B's chances fall by more than proportionally" the way a joint
  softmax can) — worth revisiting (e.g. a learning-to-rank formulation) if Model 2 shows
  promise but its ceiling looks capped by this simplification.
- **Also flagged:** unlike this repo's other numerical work (the market de-vig bisection
  solvers, Model 1's own gradient ascent), Model 2 uses scikit-learn rather than a from-scratch
  implementation — see the module docstring for why (a correct, efficient boosted-tree
  implementation is a different scale of surface area than either of those). `requirements.txt`
  has scikit-learn uncommented for the first time this session; no other Phase 6+ dependency is
  needed yet.
- **Implementation:** `src/models/model2_gradient_boosting.py::fit_gradient_boosting_baseline`,
  `predict_race_probabilities`, `_renormalize`. Reuses Model 1's own
  `build_race_features`/`FEATURE_NAMES` unchanged, deliberately — isolating "different model
  class" as the one variable under test, not also changing what the model can see. Tested with
  renormalisation edge cases (all-zero, empty, negative-total fallback to uniform — hand
  verified) and a signal-recovery convergence check (highest-rated runner always wins in
  training -> fitted model rates that runner-shape highest on a held-out race), same discipline
  as Model 1's own convergence tests, in `tests/test_model2_gradient_boosting.py`, fixtures
  shaped exactly like the real, verified racecard schema (`tests/test_racecard_theracingapi.py`).
- **Not yet run:** `scripts/train_model2.py` (added this session, mirrors
  `scripts/train_model1.py`'s shape exactly — real Kaggle-sourced load query, walk-forward
  splits, Model 0/1/2 scored side by side on the same folds) is ready to run but has not been —
  that needs Jonathan's Mac (the real DB). Until that real run happens, nothing here is evidence
  Model 2 predicts real racing any better (or worse) than Model 1 did.
- **Hyperparameter-stability check (2026-09-09, cloud routine, Session 13):**
  `src/models/model2_hyperparameter_sweep.py::sweep_gradient_boosting_hyperparameters` fits
  Model 2 once per combination in a `max_depth` x `learning_rate` x `max_iter` grid against the
  same "highest-rated runner always wins" synthetic fixture
  `test_model2_gradient_boosting.py` already uses, and checks the fitted model still ranks that
  runner-shape highest on a held-out race for every combination. **Result: stable across all 12
  combinations tested** (`max_depth` in {2,3,4}, `learning_rate` in {0.1,0.3}, `max_iter` in
  {30,60}) — every combination recovered the injected signal, none rated it below uniform.
  This is NOT a real hyperparameter benchmark (still no real outcomes to tune against) — it only
  answers the narrower question flagged since Session 10: is the fitting procedure itself
  fragile to reasonable setting changes? No, not on this synthetic signal. `scripts/train_model2.py`
  can trust its current default kwargs (or a small grid drawn from this same range) without first
  discovering instability on Jonathan's Mac. `tests/test_model2_hyperparameter_sweep.py` — 9
  tests: cartesian-product correctness (every combination present, none skipped/duplicated),
  input validation (empty grid, empty grid-value list, empty training set, a requested winner
  absent from the held-out race), the real 12-combination stability assertion above, and
  `summarize_sweep()`'s roll-up stats (pass rate, min/max/mean predicted probability) checked
  against hand-built all-pass and mixed-pass/fail result lists.
- **Status: IDEA — implementation and pipeline plumbing done and unit-tested against synthetic
  fixtures only (2026-09-08, cloud routine); hyperparameter-fitting stability now also confirmed
  on the same synthetic signal (2026-09-09, cloud routine). No real-data run yet — that's still
  Mac-only.**

---

*New entries go at the bottom, oldest first, so the log itself is chronological.*
