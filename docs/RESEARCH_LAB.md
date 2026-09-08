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

---

*New entries go at the bottom, oldest first, so the log itself is chronological.*
