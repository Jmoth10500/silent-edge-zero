# Scientific Audit + Live Brier Dashboard — pre-implementation report

Requested by Jonathan 2026-09-16. This document is the required output of
that request's Section 26 ("Before implementation give me...") — written
**before any audit-layer code exists**. Nothing described here has been
built yet. Git tag `SILENT_EDGE_MODEL_FROZEN_BASELINE` marks the commit
this plan was written against (`fee865f`, 2026-09-15).

---

## 1. SILENT EDGE MODEL FREEZE MANIFEST

Every file in the live prediction path — generates a probability, ranks
runners, combines Model 1/Model 2, assigns the top pick, or enforces
immutability. **None of these will be edited by the audit/dashboard work.**
SHA-256 recorded now; re-checked after implementation (Section "Regression
methodology" below) — any mismatch is a failed implementation.

| File | Purpose | SHA-256 |
|---|---|---|
| `scripts/predict_todays_races.py` | Orchestrator: fits Model 1 + Model 2 daily, writes+locks `prediction` rows, computes `record_hash` | `35db1d9468d0d7feb243ee629b3f97b6567902105be94932230092b52c93bb10` |
| `scripts/train_model1.py` | `load_races()` (shared data loader), Model 1's walk-forward split-table builders (draw bias, going affinity, connections strike rate) | `14ccca04505e2281f99fdffa5960f22c0fda9ab7ccf1a06b52e55b6b15d1da38` |
| `scripts/train_model2.py` | Model 2 training/backtest driver — **this is where the static `BACKTEST_CONTEXT` numbers on the dashboard (Brier 0.0795/0.0875/0.0866) come from**, not live-computed | `5408ad6291b2fdf46e042f37b4c743dda27761969674962268a517e39f72dd32` |
| `src/models/model1_logistic_baseline.py` | Model 1 (fitted logistic regression) — weights, prediction function | `594f5d4cd8885acd1da167cce74095375bf4099881a6d9170c97a131209c57d7` |
| `src/models/model2_gradient_boosting.py` | Model 2 (gradient boosting) — the live, primary model (`gbm_v1`) | `eea489f9af90491a84e60ec7ac33ee1b74809ff19b2cc68a53a3d69b3bd6e923` |
| `src/models/model0_market_baseline.py` | Market-only baseline (de-vigged odds as the "prediction") — reference model, not live-deployed | `5c9c7f17ed1eae0e644c337b203bbc5510bffa840bed404d9de75c3709a1ed68` |
| `src/features/feature_vector.py` | Assembles the feature vector fed to Model 1/2 | `f9caa441969fd4145a171eef8b3efe89c1c740d2ded7352ac3c1c9b64334cb28` |
| `src/features/runner_features.py` | Per-runner raw feature input shape | `c78f35a7cf1d57ea10fa8741afe9c6c531b4966f1bb92880acf9e6cefae3ad70` |
| `src/features/connections_strike_rate.py` | Trainer/jockey strike-rate feature (leakage-safe, train-only fit) | `f0403be5b7ff0ef82ff3d23c94ba8e4d8d7a02ccb0b906c8623f611481c1ead1` |
| `src/features/draw_bias_history.py` | Draw-bias feature (leakage-safe, train-only fit) | `a641fda17e9fe8ad8bd689395cce6f89463a3524192faf8f4da9600b2dec7e7d` |
| `src/features/going_affinity.py` | Going-affinity feature (leakage-safe, train-only fit) | `610d1f4ee1ea2a042a42c0467997030d21d6d675d5b60b6d0ff4663ff8632284` |
| `src/market/probability.py` | De-vig methods (proportional/power/shin) — feeds Model 0 and `market_probability`, never the model's own probability | `448bb3799e1fa35cfbd77ff644f348d0c2c4172d382662ecee228fc37471c00f` |
| `src/market/movement.py` | Market-movement feature helper | `e86451221010645e925194ab264d7d2e927f8d832c373ce0f27f8b7c05d632f7` |
| `src/evaluation/calibration.py` | `brier_score`/`log_loss`/`calibration_curve` — the exact scoring formula (see Section 2) | `eea54c6a103724600bc291e2ee9077f36aaafd6f236f9c1b32aee22670dc6140` |
| `src/evaluation/temperature_scaling.py` | RL-012's calibration-correction research — **NOT in the live path**, its own correction failed validation and was never deployed (docs/RESEARCH_LAB.md) | `12fe6b01257078f13b6122f2a831e463ff7ae7dc16cc8d3e5abc4d298bbe1e3c` |
| `src/validation/walk_forward.py` | Chronological walk-forward split logic (backtesting only, not live) | `0153ac46d7b225413240404c2cd45df69f32aeda456739f43d316bd3cb1296d3` |
| `src/analysis/edge_metrics.py` | Stage 1 (2026-09-11) dashboard-only derived edge/EV math — reads locked predictions + live market, never writes | `87c6bd381f207bffdddb616f4c9e7df1a83e286e48aa1c400bc742188c45c0af` |
| `src/analysis/runner_classification.py` | Stage 2 BEST VALUE/NO EDGE display labels — same, derived/display-only | `3627e4003ed87a4893ecfd8f84341994f527e5212230269b4f3ab4bd145b439a` |
| `db/schema.sql` | `prediction` table + `trg_prevent_locked_prediction_update` trigger (DB-enforced immutability) | `6aa2da51ee1cbea374793d5b2a84d794f20f6c6100a37b7df59fe9f46d6cfb6f` |

**Live model version in production:** `gbm_v1` (Model 2, gradient boosting) is what the dashboard shows as the primary pick; `statistical_v1` (Model 1) is stored alongside every day but only shown as a small secondary note.

**Git tag:** `SILENT_EDGE_MODEL_FROZEN_BASELINE` → commit `fee865f`.

**Regression methodology** (Section 23 of the request): the files above will be re-hashed after implementation — every hash must match **exactly** (0 bytes changed). This is a stronger guarantee than sampling a handful of races and comparing probabilities, since it proves *no line of model code was touched at all*, not just that a sample happened not to change. On top of that: `prediction` rows are already immutable at the database level (`trg_prevent_locked_prediction_update` rejects any UPDATE once `locked_at` is set) — the audit layer physically cannot alter a locked prediction even if it tried, and the audit code will contain zero UPDATE/DELETE statements against `prediction`, `runner_snapshot`, or `model_version`. The full existing test suite (currently 335/335) will also be re-run and must still pass with no existing test's assertions changed.

---

## 2. Current Brier calculation methodology (must be preserved, not reinvented)

`src/evaluation/calibration.py::brier_score(predicted_probs, outcomes)`:

```
brier = mean((p_i - y_i)^2)  over every (runner, race) pair
```

- **Binary, per-runner, across ALL runners** — not multiclass, not just the winner/top-pick. Every runner in every race contributes one `(p, y)` pair, `y=1` for the actual winner, `y=0` for everyone else in that race.
- **Not normalised beyond whatever probability set is passed in** — the function itself does no de-vigging; that happens upstream (see below).
- **Non-runners**: excluded entirely from the runner set before scoring (`scripts/train_model1.py`'s `_NON_RUNNER_NOTES = {"NR", "WD"}` — a non-runner contributes no `(p, y)` pair at all, not a `y=0` pair). A real non-finish (PU/F/UR/etc.) **is** kept in the runner set with `y=0` — it ran and didn't win, a real loss, same as yesterday's fix to `generate_eod_report.py`/`generate_daily_summary.py`.
- **Dead heats**: not currently handled anywhere in this formula or its callers — no real dead heat has been hit in the data yet (confirmed: 0 rows in `runner_result` with more than one `finishing_position=1` for the same race, per today's query). This is a genuine gap, documented in Section "Open questions" below, not silently assumed.
- **The static numbers shown today** (`Market: ~0.0795`, `Model 2: ~0.0866`, in `scripts/generate_dashboard.py`'s `BACKTEST_CONTEXT`) come from `scripts/train_model2.py`'s **historical walk-forward backtest** (RL-008, 9 folds, ~487k real predictions, 2023-06 to 2026-06) — hardcoded into the dashboard, **not recomputed live**. The market probability behind that number uses `src/market/probability.py::power_method` (Shin-style redistribution of overround), fed by `runner_result.starting_price` (SP) — a **historical, single, post-hoc price**, not a live exchange feed.
- **This is a different data source and (for the market side) a different de-vig method than the live "Edge" chips already on the dashboard**, which use `src/analysis/edge_metrics.py::normalized_market_probabilities` — **proportional** de-vig (simple rescale to sum=1), fed by live `market_snapshot.exchange_back` (Smarkets). These two market-probability pipelines have never been reconciled and **are not directly comparable today**.

## 3. Current result-settlement methodology

- `runner_result.finishing_position` (INT, NULL if non-runner/non-finish) + `runner_result.result_note` (TEXT — 'PU', 'F', 'NR', etc.) — real codes seen live in this DB right now: `PU, F, UR, BD, RR, RO, DSQ, SU, NR, REF, CO, VOID, FELL` (queried directly today).
- As of yesterday's fix (2026-09-15, see `docs/BUILD_LOG.md`): `NR`/`VOID` = void (stake refunded, £0 P&L, counted as settled). Any other code = the horse ran and didn't finish = a genuine loss, full stake, counted as settled. `finishing_position IS NULL AND result_note IS NULL` = genuinely still pending (no result row/data yet).
- This settlement logic lives in **`scripts/generate_eod_report.py`** (`VOID_RESULT_CODES`, `settle_win`, `settle_each_way`) and is reused by `scripts/generate_daily_summary.py`. The dashboard's day-history view (`scripts/generate_dashboard.py::load_race_history`) assigns a status of `WIN`/`PLACED`/`LOSS`/`PENDING`/`NR` per the same distinction.
- **None of this is inside the frozen model-file list above** — it operates entirely downstream of `prediction`, on `runner_result` only. The audit layer's classification work (Sections 2–5 of the request) extends this same real, already-tested logic; it does not compete with or duplicate it.

## 4. Where NR/PU/F/UR/etc. are classified today

- `scripts/train_model1.py::_NON_RUNNER_NOTES` — training-time only, excludes NR/WD from the Model 1/2 *training* feature set (a withdrawn horse was never a real data point to learn from).
- `scripts/generate_eod_report.py::VOID_RESULT_CODES` — settlement-time, P&L/void-vs-loss (yesterday's fix).
- `scripts/generate_dashboard.py::load_race_history` — display-time status badge (yesterday's fix).
- `src/providers/horseracingnet_results.py::parse_finish_text` / `scripts/collect_race_results.py::parse_outcome_code` — ingestion-time, turn a source's raw text/code into `(finishing_position, result_note)`.

No single canonical, reusable "classify this result_note" function exists yet — the same `{"NR", "VOID"}` / "everything else is a real non-finish" distinction is currently duplicated (by value, not by import) across `generate_eod_report.py` and (implicitly) `train_model1.py`'s slightly different `{"NR", "WD"}` set. **Proposed fix in Section 8 below**: a single shared classification module the audit layer, `generate_eod_report.py`, and `generate_daily_summary.py` all import from — read-only, additive, doesn't change any existing behaviour, just deduplicates it.

## 5. Current source of market probabilities

Two, genuinely different, both real:

1. **Live**: `market_snapshot` table, populated every ~20 minutes by `scripts/collect_smarkets_prices.py` from the Smarkets exchange (`exchange_back`/`exchange_lay`/`midprice`). This is what today's live Edge/EV chips use, de-vigged via `edge_metrics.py::normalized_market_probabilities` (proportional method).
2. **Historical backtest**: `runner_result.starting_price` — only populated for the pre-2026-05-27 Kaggle bootstrap data. **Every live-collected result since 2026-09-12 has `starting_price = NULL`** (both `collect_race_results.py` and `import_horseracingnet_results.py` document this honestly — neither source currently gives us SP or BSP). This means `train_model2.py`'s backtest Brier numbers cannot be recomputed on live 2026-09+ data as-is — there simply is no `starting_price` for those races. The live audit layer's market-vs-model comparison **must use `market_snapshot`, not `starting_price`**, for anything after 2026-05-27.

## 6. Current market timestamp used

- **Backtest** (`train_model2.py`): a single, undated "starting price" per historical runner — effectively "closing" in spirit (SP is set at the off), but there's no separate "at prediction time" market snapshot in that historical dataset at all — Model 0/backtest Brier has only ever compared against one timestamp.
- **Live** (dashboard Edge chips): whatever the most recent `market_snapshot` row is at *page-render* time — **not** pinned to `prediction.locked_at`, and **not** a defined "closing" snapshot either. It is simply "latest available," which drifts as the day goes on and Jonathan happens to load the page.
- **Real, live data availability** for a proper lock-vs-closing split: `market_snapshot.observed_at` is a real timestamp on every row, and `prediction.locked_at` is a real timestamp on every locked prediction. Both already exist — building "market probability at lock" (nearest `market_snapshot` at/after `locked_at`) and "closing market" (latest `market_snapshot` with `observed_at` before that race's `off_time`) needs **no new data collection**, just two new queries over data already being captured.

## 7. Database structure holding predictions and results

(Full detail: `db/schema.sql`.)

- `prediction` — one immutable row per (race, horse, model_version), `model_probability`, `locked_at`, `record_hash`. DB-trigger-enforced immutable once locked.
- `runner_result` — one row per (race, horse), `finishing_position`, `result_note`, `starting_price` (historical only, see Section 5), `source_id`.
- `market_snapshot` — many rows per (race, horse) over the day, `exchange_back`/`exchange_lay`/`midprice`, `observed_at`.
- `race` / `course` / `horse` / `model_version` — reference/dimension tables.
- `daily_summary` — one row per date, persisted aggregate (yesterday's fix corrected its settlement counting).

Current real scale (queried today, 2026-09-16): **263 real races** with locked `gbm_v1` predictions since 2026-09-09 (app went live), **174 already settled**, **200 with at least some real `market_snapshot` coverage**. This is the honest starting sample size for the new live dashboard — genuinely small, which is exactly why Sections 16/17/26 of the request (uncertainty, milestones, "EARLY" language) matter and will be followed, not glossed over.

## 8. Proposed new audit tables/modules (additive only)

**New DB tables** (all `CREATE TABLE IF NOT EXISTS`, no `ALTER` on any existing table, no new columns on `prediction`/`runner_result`):

- `audit_result_classification` — one row per audited `runner_result` (race_id, horse_id), storing `original_status`, `audited_status`, `audit_reason`, `audit_timestamp`, `integrity_status` (PASS/WARNING/FAIL). This is the append-only audit trail the request explicitly requires (Section 4/20) — corrections are *recorded*, never overwrite `runner_result` itself.
- `market_probability_snapshot_link` (or similar) — resolves, per (race, horse), which real `market_snapshot` row counts as "at lock" and which counts as "closing," computed once and cached rather than re-queried on every page load. Purely derived; can be dropped and rebuilt from `market_snapshot`+`prediction` at any time with zero data loss.
- `daily_scientific_snapshot` — one row per date (Section 19): paired sample size, live Brier (model/market), Brier gap, rolling windows, hit rates, P&L, audit warning/failure counts. Same append-only, never-retroactively-changed discipline as `daily_summary` already follows.
- `audit_correction_log` — human-readable log entries for Section 20, generated from `audit_result_classification` rows where `original_status != audited_status`.

**New modules** (all read-only against `prediction`/`runner_result`/`market_snapshot`):

- `src/analysis/result_classification.py` — the single shared "classify this result_note" function proposed in Section 4, used by the audit layer AND (optionally, as a non-behaviour-changing refactor) by `generate_eod_report.py` going forward.
- `src/analysis/live_brier.py` — pure functions: paired-sample construction (model prob + market prob + outcome, only where both exist), live Brier/gap/rolling-window computation, calibration-by-band, bootstrap CI. Reuses `src/evaluation/calibration.py::brier_score` unchanged — does not redefine it.
- `scripts/audit_race_results.py` — the integrity-audit pass (Section 3): scans `runner_result`, flags anomalies, writes `audit_result_classification` rows. Run on-demand or as a new, separate daily job — never inside `predict_todays_races.py`.
- `scripts/generate_scientific_snapshot.py` — the Section 19 daily-snapshot writer, same UPSERT-once-settled pattern as `generate_daily_summary.py`.
- `scripts/generate_dashboard.py` — **extended**, not rewritten: a new `render_scientific_audit_section()` (or a separate page) added alongside existing renderers. The existing renderers (`render_race`, `render_summary`, `render_track_record`, etc.) are untouched.

## 9. Confirmation that no prediction logic needs to change

Confirmed. Every one of the 19 files in the freeze manifest (Section 1) is read-only input to this work. The audit/dashboard layer's entire job is to **read** `prediction` (already locked, already immutable), **read** `runner_result` and `market_snapshot`, and **write** to brand-new, additive tables. There is no scientific-audit or Brier-dashboard requirement anywhere in this brief that requires changing a probability, a ranking, a weight, or a threshold — every one of Sections 2–25 is explicitly framed as measurement/reporting of the existing, unchanged model. **No prediction logic needs to change to build this.**

---

## Open questions for Jonathan (flagging honestly rather than guessing)

1. **Dead heats**: no real one has occurred in this dataset yet, so there's no real precedent to follow. Standard practice splits `y` between the tied winners (e.g. 0.5/0.5) rather than 1/0 — I'd propose that as the rule *if and when* one occurs, clearly documented, not silently assumed. Flag only, no action needed now.
2. **`starting_price` is NULL for all live (2026-09-12+) results** — the live market Brier comparison will use `market_snapshot` (Smarkets), not SP/BSP, for anything after the Kaggle bootstrap cutoff. This means the live dashboard's market-probability pipeline is genuinely different from the backtest's (Section 2) — I'll present them as clearly separate, non-interchangeable numbers, per the brief's own Section 7 instruction, rather than trying to force them into one figure.
3. **De-vig method for the live market comparison**: propose using `power_method` (matching the historical backtest exactly, for genuine comparability) as the primary LIVE figure, and keep today's dashboard Edge chips on their existing `proportional` method untouched (separate, already-shipped feature, not part of this brief). Both will be clearly labelled by method so nothing is silently mixed.
4. **Sample size is currently small** (174 settled, 200 with market data) — every headline number on the new dashboard will carry its real `n`, and "Evidence level" will read EARLY until a real milestone (Section 17) is reached. I will not soften this.

---

## Implementation plan

Given the size of this brief (26 sections), building it in ordered, independently-shippable, independently-testable slices — each slice runs the full test suite + a fresh file-hash check against the freeze manifest before moving to the next:

**Slice 1 — Data integrity audit (Sections 2–5, 18, 20)**
`src/analysis/result_classification.py` (shared classifier) + `scripts/audit_race_results.py` + `audit_result_classification`/`audit_correction_log` tables. Run once against all 174 real settled races. Deliverable: real PASS/WARNING/FAIL counts, real correction log (if any), before touching a single metric.

**Slice 2 — Paired sample construction + live Brier core (Sections 6–11)**
`src/analysis/live_brier.py` (paired records, live Brier, cumulative chart data, rolling windows, Brier gap). No UI yet — proven against real data via tests + a printed report, same discipline as `generate_eod_report.py`.

**Slice 3 — Calibration-by-band + winner-vs-probability separation (Sections 12–14)**
Bucket analysis, "which bands are hurting Brier," the explicit Winner Identification vs Probability Accuracy split.

**Slice 4 — Economic performance section (Section 15)**
Reuses yesterday's already-fixed `settle_win`/`settle_each_way` unchanged — just a new, separately-labelled presentation, not new settlement math.

**Slice 5 — Uncertainty (Section 16)**
Bootstrap CI on the Brier gap and hit-rate difference. Pure stats, no new data dependency.

**Slice 6 — Daily snapshot + milestones (Sections 17, 19)**
`generate_scientific_snapshot.py`, `daily_scientific_snapshot` table, sample-size milestone tracker.

**Slice 7 — Dashboard UI (Sections 6, 24, 25)**
New "SCIENTIFIC AUDIT" nav section + "LIVE BRIER" page in `generate_dashboard.py`, restrained research-lab language throughout, summary card at the top.

**Slice 8 — Shadow research layer (Section 22)**
Clearly-labelled hypothetical-recalibration exploration, explicitly never fed back into `prediction`.

Each slice ends with: full test suite run, freeze-manifest re-hash, and a short written note of what changed/what was found — same discipline as every other piece of work this project.

**I have not started Slice 1.** Confirming the plan above (or adjusting it) is the next step before any code is written, per the brief's own Section 26 instruction.
