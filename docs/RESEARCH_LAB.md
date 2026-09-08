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
- **Status: IDEA** — pipeline plumbing implemented and unit-tested against synthetic data only; no real-data run yet.

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
  (Session 5) and debutant-never-wins (Session 7) — in `tests/test_model1_logistic_baseline.py`,
  fixtures shaped exactly like the real, verified racecard schema
  (`tests/test_racecard_theracingapi.py`).
- **Training/validation period:** TBD — the real data to do this now exists (Session 6's Kaggle
  load, Jonathan's Mac) but hasn't been pointed at Model 1 yet; that's Mac-only work (needs that
  machine's local Postgres). Cannot be trained meaningfully in the cloud routine environment (no
  credentials there — see docs/BUILD_LOG.md Sessions 5 and 7).
- **Status: IDEA** — pipeline and maths implemented and unit-tested against synthetic data
  only; no real-data fit or evaluation yet, and everything above is explicitly NOT a real
  prediction until it is.

---

*New entries go at the bottom, oldest first, so the log itself is chronological.*
