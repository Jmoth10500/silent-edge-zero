# Research Lab

Every modelling hypothesis, tracked honestly. Most will fail — that's expected (Section 39).

Status values: IDEA / TESTING / FAILED / PROMISING / VALIDATED / PRODUCTION

---

## RL-001: Weather materially improves prediction accuracy on AW vs turf

- **Hypothesis:** All-weather (AW) surfaces are less weather-sensitive than turf; a weather-interaction feature should show near-zero effect on AW races and a real effect on turf, particularly on going-adjacent features (rainfall correlating with turf going changes).
- **Why it might work:** turf going is directly driven by rainfall; AW surfaces are engineered to be more consistent.
- **Implementation:** not yet — needs Phase 5 (feature engineering) built first.
- **Training/validation period:** TBD, needs real racecard history first.
- **Status: IDEA** — logged now so it isn't lost, tested once real data exists.

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
- **Why it might work / why it's a placeholder:** genuine draw bias is course- and distance-specific (e.g. a low draw can be a major advantage at one course/distance and irrelevant at another) — that requires historical results grouped by course+distance, which doesn't exist yet.
- **Implementation:** `src/features/runner_features.py::draw_bias_features()` — deliberately does NOT claim any bias direction, just the neutral positional fact.
- **Training/validation period:** TBD — needs real historical results per course+distance (Phase 5+, once The Racing API or Kaggle data lands).
- **Status: IDEA** — flagged so the next session doesn't mistake the neutral placeholder for a validated bias model.

## RL-005: Market baseline (Model 0) as the bar every real model must clear

- **Hypothesis:** the de-vigged market-implied probability (src/market/probability.py), used directly as a "prediction" with no fitting at all, is already a strong baseline — real money is priced into it. Any trained model built later (Phase 6+) that can't beat Model 0's Brier score / log loss on the same walk-forward test windows isn't adding information the market didn't already have.
- **Why it might work / why it's the right null hypothesis:** bookmaker/exchange odds already aggregate a lot of public information (form, ratings, weather, etc.) through pricing behaviour. A model that can't beat this baseline is, at best, redundant with the market.
- **Implementation:** `src/models/model0_market_baseline.py::predict_race_probabilities` (wraps the existing overround-removal methods) + `evaluate_market_baseline_walk_forward` (wires it through the walk-forward split harness and calibration scoring end-to-end). Tested with hand-verified Brier scores against synthetic zero-overround odds (2026-09-08) — see `tests/test_model0_market_baseline.py`.
- **Design choice flagged for review:** which of the three overround-removal methods (proportional/power/Shin, see RL-002) Model 0 should default to is still unresolved — same blocker as RL-002, needs real odds history to benchmark.
- **Training/validation period:** TBD — Model 0 has no training step by design, but its *evaluation* needs real (race_date, odds, winner) rows, which needs The Racing API or Betfair access (both blocked, see FREE_DATA_SOURCES.md).
- **Real result (2026-09-08, `scripts/train_model1.py`, real Kaggle-sourced starting prices as odds, power de-vig method):** confirmed as the bar to clear. Pooled Brier=0.0795, log loss=0.2738 across 18 walk-forward folds (2023-06 to 2026-06), ~484k real runner predictions. Beat Model 1 on every single fold, no exceptions.
- **Status: VALIDATED as a real, working baseline.** Whether power is the *best* de-vig method (vs. proportional/Shin) is still open — see RL-002.

## RL-006: Model 1 — a fitted, per-race logistic/softmax baseline over race-relative features

- **Hypothesis:** a simple multinomial logit (softmax) over just four race-relative runner
  features — official rating vs. field mean, draw percentile vs. 0.5, recency-weighted form
  score vs. field mean, weight vs. field mean — fit by gradient ascent on observed winners,
  should beat Model 0's market baseline once it can be trained on real (racecard, result)
  pairs, by using the same information a market-derived probability implicitly prices in but
  making it explicit and auditable per feature.
- **Why it might work / why it's still just an idea:** the four features are exactly the ones
  `src/features/runner_features.py` (Sections 8/10) already computes and tests; wiring them
  into a per-race softmax is the standard "conditional logit" formulation for a discrete
  choice among race entrants, so the probability-per-race-sums-to-1.0 property comes for free
  rather than needing a second normalisation pass. This is genuinely untested against real
  outcomes, though — there is still no real (racecard, result) pair anywhere in this repo (The
  Racing API only returns racecards so far — Session 4 — and results collection hasn't been
  built), so nothing here is evidence the features or their sign actually predict winners.
- **Design choice flagged for review:** every feature is deliberately UNDIRECTED (centered on
  the race's own mean, sign decided by the fitted weight, not asserted up front) — same
  discipline as RL-004's draw_percentile. A runner missing an underlying field (no rating, no
  parseable form, ...) gets 0.0 for that one feature ("no evidence either way"), which is a
  modelling simplification worth revisiting once there's enough real data to check whether
  missingness itself carries signal (e.g. a horse with no official rating is very likely a
  first-time-out debutant, which is not "average").
- **Implementation:** `src/models/model1_logistic_baseline.py::build_race_features`,
  `predict_race_probabilities`, `fit_logistic_baseline` (pure-Python batch gradient ascent, no
  numpy/scikit-learn — see the module docstring for why). Tested with a hand-verified
  single-gradient-step calculation and a synthetic rating-determines-the-winner convergence
  check (`tests/test_model1_logistic_baseline.py`, 2026-09-08) — fixtures shaped exactly like
  the real, verified racecard schema (`tests/test_racecard_theracingapi.py`).
- **Training/validation period:** TBD — needs real (racecard, result) pairs, which needs
  results collection to be built (the natural next step per Session 4's notes) and run on
  Jonathan's Mac, same as racecards. Cannot be trained meaningfully in the cloud routine
  environment (no credentials there — see docs/BUILD_LOG.md Session 5).
- **Real result (2026-09-08, `scripts/train_model1.py`, walk-forward, min_train_days=180,
  test_window_days=60, iterations=150, real Kaggle-sourced results 2023-06 to 2026-06):**
  Model 1 lost to Model 0 (market baseline, RL-005) on Brier score and log loss on every
  single one of 18 out-of-sample folds — pooled Brier=0.0896 vs. Model 0's 0.0795, log
  loss=0.3199 vs. 0.2738, across ~487k real runner predictions. This is genuinely the first
  time this hypothesis has been tested against a real outcome, and the hypothesis (Model 1
  beats the market) did NOT hold. Calibration is good, though (predicted probability tracks
  actual win rate closely in every bin with meaningful volume, e.g. predicted 0.074 vs. actual
  0.074 on 284,519 predictions) — the model is honest, just not (yet) as informative as the
  market.
- **Known real confound, not yet controlled for:** `form_edge` has had zero real signal this
  whole run — the Kaggle CSV has no `recent_form`/`days_since_last_run` columns at all (checked
  directly against the raw file's header, 2026-09-08), so every runner's form_edge defaulted to
  0.0. A real form feature would need to be *derived* from each horse's own prior rows in this
  same dataset (build a per-horse chronological result history, leakage-safe — only races
  strictly before the current one), which hasn't been built yet. Re-running this evaluation
  with a real form feature is the natural next step before drawing a final verdict on whether
  Model 1's four-feature shape can ever beat the market — right now it's running on
  effectively three features, not four.
- **Status: TESTING — real result in, currently FAILED to beat the market baseline, but not
  a clean test of the original hypothesis yet** (missing form signal). Next: derive real form
  from the Kaggle history and re-run before concluding Model 1's feature set is insufficient.

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
- **Status: IDEA** — logged so the next session builds this rather than re-discovering the
  gap.

---

*New entries go at the bottom, oldest first, so the log itself is chronological.*
