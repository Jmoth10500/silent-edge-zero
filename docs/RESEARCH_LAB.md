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

## RL-001b: Real implementation — per-horse going affinity (reframed from weather)

- **Reframe, 2026-09-09:** RL-001's original hypothesis was about weather
  (rainfall) affecting turf vs all-weather races differently. Investigating
  it surfaced two things worth recording: (1) `weather_snapshot` had only
  13 real rows (a single day) and only 8% of real GB races since 2023 had
  a course with known coordinates — fixed as real groundwork (see below),
  but (2) the more important finding: weather can only ever act as an
  INTERACTION with a per-runner attribute, never a main effect, in either
  model here — every runner in a race experiences identical weather, and
  a feature identical across all runners in a race is mathematically
  invariant under both Model 1's softmax and Model 2's per-race
  renormalisation (it cancels out completely, regardless of its fitted
  weight). And the real dataset already records the actual GROUND GOING
  per historical race (`race.going`, e.g. 'Good To Soft', ~57K real rows)
  — direct ground truth, not a noisy weather proxy, needing no API calls.
  So RL-001 was rebuilt as a genuine per-horse going-affinity interaction
  feature instead of a weather one.
- **Course-coordinate groundwork (still real, still committed, just not
  load-bearing for this particular feature):** gathered real coordinates
  for all 59 current British racecourses (Wikipedia's own geodata,
  verified live via the MediaWiki API, 6 resolved via web search where
  Wikipedia had no `{{coord}}` data) — `data/gb_racecourse_coordinates.py`,
  `scripts/backfill_gb_course_coordinates.py`. Real GB race coverage with
  a known course coordinate went from 8% to 59.5%. This remains useful
  groundwork for a live/future-facing weather feature (going isn't
  finalised until close to race time, so a live system still needs a
  weather-based going FORECAST) — just not needed for backtesting against
  historical results, where the real going is already known.
- **Implementation:** `src/features/going_affinity.py` —
  `build_going_affinity_table()` computes each horse's own
  `(avg finish percentile on the soft/slow side of its going scale) -
  (avg finish percentile on the fast/firm side)` from real, strictly-past
  completed runs (min 2 real runs on EACH side, else excluded — never
  guessed). Turf and all-weather going use separate, non-comparable
  ordinal scales (sourced from standard UK/Irish racing terminology, not
  empirically validated — same honesty flag as RL-004's draw-percentile
  placeholder). `going_interaction_edge()` = the horse's own affinity times
  a +1/-1 indicator of whether TODAY's going is soft-side or fast-side —
  this is what makes it a genuine per-runner-varying feature despite
  `going` itself being race-constant. Wired as a 7th feature into the
  shared `build_race_features()`, leakage-safe by construction (the table
  is rebuilt fresh per walk-forward split from training races only, using
  every runner's real finishing position, not just the winner). 15 new
  tests in `tests/test_going_affinity.py`, plus 2 wiring tests in
  `tests/test_model1_logistic_baseline.py`.
- **Real result (2026-09-09, `scripts/train_model2.py`, same 9 real
  walk-forward folds, 2023-06 to 2026-06, ~487k predictions):** Model 1
  pooled Brier UNCHANGED at 0.0875. **Model 2 got slightly WORSE: 0.0878
  (was 0.0874 with 6 features, 0.0873 with 5) — and for the first time,
  Model 2 no longer beats Model 1** (0.0878 vs 0.0875). Sanity-checked
  before trusting this (same discipline as the RL-004 distance_yards bug):
  the affinity table genuinely populates (2,469 real horses in the first
  fold alone, mean |affinity| ~0.20, so this isn't another silent-zero
  bug) — the feature is real and firing, it's just not helping, and for
  Model 2 it appears to be adding noise the gradient-boosted trees
  overfit to (a feature with real signal for only ~2,500 of many more
  horses per fold, versus 0.0 "no evidence" for the rest, is exactly the
  kind of sparse, high-variance split a boosted tree can latch onto
  spuriously).
- **What this means honestly:** three feature attempts now (real form,
  RL-007; real draw bias, RL-004; real going affinity, RL-001b) have been
  genuinely tested. Two made ~no difference, one made Model 2 measurably
  worse. This is a real, informative negative result, not a failed
  session — it suggests this repo's current 7-feature race-relative shape,
  built from 5 simple runner attributes plus two interaction terms, is
  genuinely exhausted as a source of edge over the market with either
  model class tried so far. The remaining untried lever is a different
  kind of information entirely (real price-movement data, needs Betfair —
  still blocked on Jonathan's signup), not another feature on this same
  input shape.
- **Reverted from the active feature set (2026-09-09, same session):**
  since it made no difference to Model 1 and measurably hurt Model 2,
  `going_affinity_edge` was removed from `FEATURE_NAMES` (what either
  model actually trains/scores on) — confirmed via a real re-run that
  this restores both models to their known-good pre-going numbers exactly
  (Model 2 0.0874, Model 1 0.0875, unchanged). The computation itself
  stays real and tested (`src/features/going_affinity.py`,
  `build_race_features`'s `ALL_COMPUTED_FEATURE_NAMES`) — a one-line
  re-add to `FEATURE_NAMES` if future evidence changes this conclusion
  (e.g. a stricter `min_runs_per_side`, or more real data reducing the
  sparsity Model 2 appears to have overfit to).
- **Status: TESTING — clean, complete, genuinely tested result, reverted
  from active use.** Real going affinity does not help Model 1 and
  measurably hurts Model 2 on this feature set as implemented. Not
  recommending this feature be re-enabled without further evidence it
  helps once genuinely new information (price movement) is also in play.

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
- **Implementation:** `src/features/runner_features.py::draw_bias_features()` — deliberately does NOT claim any bias direction, just the neutral positional fact. The real, biased-on-purpose version is `src/features/draw_bias_history.py` (built 2026-09-09, see below) — a SEPARATE feature, not a replacement.
- **Real implementation (2026-09-09, Session 10):** `src/features/draw_bias_history.py::build_draw_bias_table()`/`draw_bias_edge()` — course+distance-banded (220-yard/1-furlong bands), draw-tercile (LOW/MID/HIGH third of field) historical win rate vs. the naive uniform expectation, with a `min_sample_size=30` floor per bucket (below that, returns 0.0 "no evidence", never a low-confidence guess). Wired as a 6th feature (`draw_bias_edge`) into both Model 1 and Model 2's shared `build_race_features()`, leakage-safe by construction: the table is rebuilt fresh from each walk-forward split's TRAINING races only (`scripts/train_model1.py::build_split_draw_bias_table`), never the test fold or full dataset.
- **Real bug found and fixed along the way:** the first real run of this feature came back with the pooled Brier score essentially unchanged from before the feature existed — suspicious enough to sanity-check rather than accept. `build_split_draw_bias_table()` was returning ZERO table entries: `race.distance_yards` was NULL for all 57,267 Kaggle-loaded races, because `scripts/load_kaggle_historical.py` (Session 6) never parsed the CSV's `dist` column (e.g. `'2m3½f'`) into it — a real, silent data-engineering gap, same shape as RL-007's missing form column. Fixed with `scripts/backfill_race_distance.py` — a real parser (6 unit tests, verified against all 63 real distinct `dist` strings in the CSV, zero unparsed) that backfilled all 57,267 races with real distances. Confirmed fixed by re-checking the table: 438 real (course, distance, tercile) buckets populated on the first fold alone, not 0.
- **Real result, feature genuinely working this time (2026-09-09, `scripts/train_model2.py`, same 9 real walk-forward folds, 2023-06 to 2026-06, ~487k predictions):** pooled Brier virtually unchanged — Model 1: 0.0875 (same as without the feature), Model 2: 0.0874 (was 0.0873 without it, a noise-level difference in the wrong direction). **The draw-bias feature, correctly computed against real data, did NOT meaningfully improve either model.** This is now a genuine, trustworthy null result (the bug is confirmed fixed and the feature confirmed populated, not silently inert) rather than the false null the buggy first run produced.
- **What this means honestly:** either genuine course/distance draw bias is weaker in this real dataset than expected, the 220-yard-band/tercile bucketing is too coarse to capture it, or five/six race-relative features generally aren't the bottleneck this repo hoped (consistent with RL-008's own conclusion). Worth one more look with finer buckets (e.g. by exact distance rather than banded, or by going/surface too) before concluding draw bias itself is a dead end here — but not a priority next step given how small the earlier feature-completeness gains (RL-006/RL-007's form fix) already were relative to the market gap.
- **Status: TESTING — clean, complete, genuinely tested result** (after fixing the distance_yards bug that produced a false null first). Real course+distance draw bias, as implemented, does not currently move the needle for Model 1 or Model 2.

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

## RL-008: Model 2 — gradient boosting over the same feature set as Model 1

- **Hypothesis:** a genuinely different model class (gradient-boosted trees,
  `HistGradientBoostingClassifier`) over the SAME race-relative feature set
  as Model 1 (rating/draw/form/weight edges + no_rating_flag) should beat
  Model 1, since tree ensembles can capture nonlinear interactions a linear
  softmax cannot — and the real question this repo cares about (RL-006):
  can either fitted model beat the market baseline (Model 0)?
- **Why scikit-learn here, unlike Model 1:** reimplementing boosted-tree
  splitting well in pure Python is a real project of its own, not a good
  use of time the way Model 1's 4-5 parameter logistic regression was.
  scikit-learn is free/open-source and was already anticipated in
  `requirements.txt` since Phase 6 — see `src/models/model2_gradient_boosting.py`'s
  module docstring for the full reasoning.
- **Implementation:** `src/models/model2_gradient_boosting.py` — reuses
  `model1_logistic_baseline.build_race_features` unchanged (same 5 features,
  so any accuracy difference is attributable to model class, not feature
  engineering), framed as per-runner binary win/lose classification with
  raw probabilities renormalised to sum to 1.0 per race (no native
  race-grouped-choice objective in `HistGradientBoostingClassifier`).
  `tests/test_model2_gradient_boosting.py` — 8 tests: renormalisation edge
  cases (including an all-zero fallback to uniform), empty/single-class/
  bad-winner error handling, and a synthetic rating-determines-winner
  convergence check, mirroring Model 1's own test discipline.
- **Real result (2026-09-09, `scripts/train_model2.py`, walk-forward,
  min_train_days=180, test_window_days=120, max_iter=50, real Kaggle-sourced
  results 2023-06 to 2026-06, 9 folds, ~487k real runner predictions,
  identical folds/data to Model 1's own real test):** pooled Brier=0.0873,
  log loss=0.3086. **Beat Model 1 (Brier 0.0875, LogLoss 0.3097) on pooled
  Brier score, and on 8 of 9 individual folds** — a small but consistent
  edge from the different model class over the identical feature set,
  confirming the RL-008 hypothesis's first half. **Did NOT beat Model 0**
  (the de-vigged market baseline, Brier 0.0795, LogLoss 0.2738) on Brier
  score on any fold — the gap to the market (0.0078) is essentially
  unchanged from Model 1's own gap (0.0080), i.e. changing model class
  barely moved the needle against the market, even though it did help
  slightly against Model 1. Calibration is reasonable through the
  well-populated 0.0-0.3 bins (which cover >99% of the real predictions);
  the 0.5+ bins have too little volume (n<150 combined) to say anything
  about calibration there.
- **What this means honestly:** the "complicated system does not
  automatically win" principle (Section 39) held again — a materially more
  complex model, same information, still lost to the market. This is
  further evidence the bottleneck here is the FEATURE set (only 5
  race-relative stats, no market/price data, no course/distance-specific
  draw bias, no weather), not the model class Model 1 already exhausted
  with a simpler, cheaper model. Chasing a third model class on this same
  5-feature input isn't a promising next step; richer features (RL-001,
  RL-004) or genuinely new information (price movement, Betfair once
  unblocked) are.
- **Status: TESTING — clean, complete result.** Model 2 beats Model 1
  narrowly, both still lose clearly to Model 0. Not pursuing model-class
  tuning (hyperparameter sweep) further against this same feature set — see
  reasoning above.
- **Update 2026-09-09, same session — re-run with the new `draw_bias_edge`
  6th feature (RL-004) once its real distance_yards bug was fixed:** pooled
  Brier barely moved — Model 1 0.0875 (unchanged), Model 2 0.0874 (was
  0.0873, noise-level). See RL-004 for the full story (a real bug briefly
  produced a false null before the fix). This reinforces RL-008's original
  conclusion: the bottleneck is genuinely the feature set/its current
  shape, not model class, and the two most obvious "richer feature"
  candidates tried so far (real form, RL-007; real draw bias, RL-004) both
  made only marginal-to-zero difference once genuinely tested. Weather
  (RL-001) and price-movement features remain untried.

## RL-009: "How likely is this app to pick the winning horse?" — real top-pick hit rate

- **Why this is a different question from RL-008's Brier scores:** Brier
  score measures calibration (is a 20% prediction right ~20% of the time
  across many races), not "how often is the single highest-probability
  pick actually the winner". Jonathan asked the hit-rate question
  directly (2026-09-09); this is the real answer, computed on the exact
  same real walk-forward folds/data every other backtest in this repo
  uses — no new data, a different real metric on it.
- **Implementation:** `scripts/compute_hit_rate.py` — for every real test
  race in every walk-forward fold, takes each model's single highest-
  probability runner and checks whether it was the real winner. Also
  reports the honest "no information at all" floor: the average of
  `1/field_size` across real races (what a uniformly random pick would
  score, given real GB field sizes).
- **Real result (2026-09-09, same 9 walk-forward folds, 2023-06 to
  2026-06, ~49-50k real races per model):**

  | | Hit rate |
  |---|---|
  | No-info baseline (random pick) | 11.8% |
  | Model 0 (market favourite) | 33.4% |
  | Model 1 (statistical) | 21.5% |
  | Model 2 (gradient boosting) | 21.7% |

- **What this means in plain terms:** both real models pick the actual
  winner roughly 1 in 5 races (21-22%) — almost double the no-information
  floor (11.8%), so they are genuinely finding real signal, not noise.
  But simply backing the market's own favourite wins 1 in 3 races (33.4%)
  — the market is still clearly the best single predictor here, consistent
  with every Brier-score result in RL-005 through RL-008. This is the
  most honest, plain-language answer to "how good is this at picking
  winners": better than guessing, worse than just following the crowd.
- **Status: real, complete.** Not pursued further this session — same
  conclusion as RL-008, the current feature set is exhausted; a materially
  better hit rate needs either genuinely new information (price movement,
  now unblocked via Smarkets — RL-010 candidate once real data
  accumulates) or accepting the market as the practical baseline.

## RL-010: Trainer/jockey real strike-rate features — the first genuine improvement

- **Origin:** Jonathan asked for a real gap analysis on closing the gap
  from the RL-009 hit rate (21.7%) to the market's 33.4%. Before proposing
  anything, the DB was checked directly for real, already-collected,
  completely unused signal — and found a large one: real trainer win
  rates over 300+ real races each ranged from **2.4% (Max Young) to 28.6%
  (Charlie Appleby)**; jockeys showed the same real spread (Paul Townend
  35.2% down to low single digits for low-volume riders). Neither model
  used trainer or jockey identity at all before this.
- **Implementation:** `src/features/connections_strike_rate.py` —
  `build_win_rate_table()` computes a real win rate per trainer_id/
  jockey_id from strictly-earlier real runs (min 20 real runs to get a
  table entry, else excluded — never guessed from too little evidence).
  `connections_edges()` centers each runner's real rate on the race's own
  field mean among runners with a KNOWN rate, same "fitted weight decides
  the sign" discipline as every other edge feature here (RL-004's
  precedent) even though the real-world direction is obvious. Wired as
  a 7th/8th feature pair (`trainer_edge`, `jockey_edge`) into the shared
  `build_race_features()`, leakage-safe (tables rebuilt fresh per
  walk-forward split's training races only — `build_split_connections_tables()`
  in `scripts/train_model1.py`). Also wired into the live daily pipeline
  (`scripts/predict_todays_races.py`, model versions bumped to 1.1). 9 new
  tests (`tests/test_connections_strike_rate.py` + 2 wiring tests in
  `test_model1_logistic_baseline.py`).
- **Real result, sanity-checked before trusting (765 real trainers,
  600 real jockeys with real >=20-run table entries in the first fold
  alone — genuinely populated, not a silent-zero bug):**

  | | Brier (Model 2) | Brier (Model 1) | Hit rate (Model 2) | Hit rate (Model 1) |
  |---|---|---|---|---|
  | Before (RL-008 feature set) | 0.0874 | 0.0875 | 21.7% | 21.5% |
  | With trainer/jockey (RL-010) | **0.0866** | 0.0875 (flat) | **23.2%** | 21.7% (flat) |

  **This is the first feature attempt in this project's history that
  produced a genuine, real improvement** — not marginal-to-zero (form,
  draw bias) and not negative (going affinity). Model 2's real hit rate
  moved +1.5 percentage points, the single largest gain of any feature
  tried. Model 1 barely moved — the logistic model's linear structure
  appears less able to exploit this signal than Model 2's tree splits,
  consistent with trainer/jockey identity being a higher-cardinality,
  more interaction-heavy signal than the earlier race-relative edges.
- **Real calibration note (same backtest):** Model 2's calibration curve
  now extends further into high-confidence bins with more real data
  (up to predicted 0.8-0.9), but shows some real overconfidence at the
  top end (predicted 0.641 vs actual 0.541 at [0.6-0.7), n=196; predicted
  0.817 vs actual 0.600 at [0.8-0.9), n=5 — too small a sample to trust
  alone, flagged honestly rather than presented as solid).
- **What this means honestly:** still short of the market (33.3% vs
  23.2%) — this doesn't change RL-009's practical conclusion that
  outright beating the market with free public data is unlikely. But it's
  real, meaningful progress, and confirms the gap-analysis approach
  (check what real, already-collected data is sitting unused before
  building anything new) was the right one. Some of trainer/jockey's real
  win-rate spread likely correlates with getting better-rated horses
  (partially redundant with `rating_edge`) — the fact it still moved the
  needle this much suggests real, additional signal beyond what rating
  already captures.
- **Status: TESTING — real, genuine, positive result. Kept in the active
  feature set for both models** (unlike RL-001b's going-affinity, which
  was reverted). Natural next step: the "GC" residual/miss-pattern
  analysis Jonathan proposed next (RL-011) — look at where the model's
  confident picks were real misses across these walk-forward folds for a
  genuine, explainable common thread, then test any real candidate the
  same walk-forward way, never just declared from the pattern-finding
  step alone.

---

*New entries go at the bottom, oldest first, so the log itself is chronological.*
