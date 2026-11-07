# Data integrity layer (2026-10-17)

Purpose: make Silent Edge a defensible *prospective experiment*. The prediction models are untouched
(`scripts/check_model_freeze.py` passes; 7,552 frozen locks verified). Everything here repairs the data
*around* the models. Schema: `db/migrations/001_integrity.sql` (additive; `db/schema.sql` is not edited
because lines 207-269 are hash-frozen). Code: `src/integrity/`.

## Layers
| Layer | Tables | Rule |
|---|---|---|
| Raw immutable | `race_feed_snapshot`, `prediction_lock`, `market_price_snapshot`, `market_snapshot`, `race_validation`, `correction_ledger`, `integrity_alert`, `canonical_race_alias` | `UPDATE`/`DELETE` rejected by trigger |
| Validated / eligible | `canonical_race`, `race_integrity` (view `excluded_race`) | classification + `include_in_metrics`; originals never altered |
| Derived | `bet_settlement`, `metric_snapshot`, `daily_summary` | re-computable from the layers above |
| Presentation | `dashboard.html`, `research_dashboard.html`, `data_health.html` (internal, not deployed) | read only from `src/integrity/metrics.py` |

## Canonical race identity
* `canonical_race_id` = `P:<provider race id>` (authoritative Racing API id). Composite
  `C:<date>|<course>|<sequence>[|<division>]` only if no provider id exists. **Off-time is never part of identity.**
* Identity columns are immutable (trigger). Off-time / status / last-seen are mutable metadata; reschedules
  `UPDATE` the same `race` row and append to `canonical_race_time_history`.
* If the provider re-issues the id of the same race (same course/date/time slot, ≥80% runner overlap) the new id
  is recorded in `canonical_race_alias`, not as a second race.
* Ingestion (`scripts/collect_racecards.py` → `src/integrity/store.py::ingest_racecards`): stores the raw feed
  payload + SHA-256; reuses existing `horse` rows by exact name (stops the NULL-`foaled_year` duplicate bug growing);
  rewrites a race's runner rows only when its runner set actually changed; **retires** (never deletes) races absent
  from the newest *complete* feed (a snapshot with <50% of the previous race count cannot retire anything);
  a snapshot older than one already stored is kept but never applied.

## Validation gate (before any scoring)
`scripts/run_gated_predictions.py` wraps the frozen scorer: runs `run_gate`, hands the scorer only VALID races with
their *current, de-duplicated* runners, and writes a `prediction_lock` for every new lock. Rules (`src/integrity/validation.py`):
V01 canonical id present/unique · V02 in latest feed · V03 date/meeting consistent · V04 internal consistency ·
V05 provider id unique among live races · V06 no duplicate runner · V07 runner in only one race at the meeting ·
V08 runner count 2-40 and equals the feed · V09 not abandoned/retired · V10 trustworthy snapshot time ·
V11 stale snapshot can't overwrite fresher · V12 repeated label (repeated division marker, or shared runners).
Cross-race conflicts quarantine **every** race involved (the feed alone can't say which is real); the real one is
re-validated and scored on a later run once the provider drops the phantom. Failures are appended to
`race_validation` with the failed rules and the raw payload, and shown publicly as *DATA VALIDATION FAILED / RACE UNDER REVIEW*.

## Prediction immutability
`prediction` keeps its frozen trigger. `prediction_lock` (one per race+model) stores canonical/meeting/provider ids,
feed snapshot id + timestamp, scheduled time at lock, runner ids + names, model version, probabilities, lock time and a
SHA-256 of the whole input. 2,364 pre-existing locks were back-filled with `provenance = LEGACY_RECONSTRUCTED`
(no feed snapshot existed then; we do not pretend otherwise). Old probabilities are never regenerated.

## Market snapshots and prices
* Primary: Smarkets (`market_snapshot`, now append-only). `price_observation` view unions it with `market_price_snapshot`
  (explicit NULL+reason rows and approved-fallback rows).
* **Lock-window price** = last valid (`price_quality='ok'`, 1.01 ≤ price ≤ 1000) exchange snapshot in
  `[off-30min, off-60s]`. Anything after that is never a pre-off price. A valid exchange price earlier in the day is
  `EXCHANGE_OTHER`, never called lock-time. (Predictions are locked the morning *before*, so "lock-time" market means the
  lock window before the off, not the prediction timestamp; constants in `src/integrity/market.py`.)
* **Fallback is gap-filling only** (`src/integrity/gapfill.py`, `scripts/market_gap_fill.py`): one race at a time, only
  for a validated race, only inside the lock window, only if the primary snapshot is missing, never at/after the off,
  never overwriting a primary price, never historical (>3h after the off → skipped), stamped with *our* clock, tagged
  `source_type`/`is_fallback`. `APPROVED_FALLBACK_SOURCES` ships **empty** → outcome is NULL + reason
  `PRIMARY_UNAVAILABLE_NO_APPROVED_FALLBACK`. Adding a source = owner approval + one entry + a fetcher.
* Smarkets is currently behind a Cloudflare 403 (since ~15 Oct). We do not bypass bot protection.

## Settlement
`src/integrity/settlement.py`. Status taxonomy WIN / PLACED / FINISHED_UNPLACED / FELL / PULLED_UP / UNSEATED /
REFUSED / RAN_OUT / BROUGHT_DOWN / CARRIED_OUT / DISQUALIFIED / VOID / NON_RUNNER / ABANDONED / UNKNOWN_PENDING.
F/PU/UR/BD/RR/RO/DSQ/SU/REF/CO/U/FELL **lose**; only NR/WD/VOID/ABD refund; an unmapped code stays UNKNOWN_PENDING (alerted).
Each bet in `bet_settlement` records price, `settlement_price_type` (`EXCHANGE_LOCK` / `EXCHANGE_OTHER` / `SP` / `NO_PRICE`),
price timestamp/source, stake, gross, commission (0 by default, so figures stay comparable with history), net.
Reporting always shows: A exchange-lock · A2 exchange-other · B SP · C **MIXED / NON-HOMOGENEOUS**.

## Metrics layer and reconciliation
`src/integrity/metrics.py` is the only place public numbers are defined. Every `Metric` carries numerator, denominator,
definition, exclusions, sample dates; `metric_snapshot` stores each run with a dataset version hash.
Identities asserted on every report (`reconcile`): raw = valid + excluded · valid = settled + pending ·
settled = genuine runner + void · genuine = lock + other + SP + no-price · staked(mixed) = lock + other + SP · no orphans.
A failure is a CRITICAL alert and a non-zero exit.

## Research eligibility
Research page regenerates nightly (`run_collect_results.sh`), refuses to publish if its own 19-check reconciliation fails,
excludes `excluded_race`, uses the lock-window price as its market reference (`race_dataset.attach_market_data`:
`at_lock`; the old "first snapshot after prediction lock" is kept as `first_after_lock`), and prints sample start/end, n,
coverage, exclusions and refresh time, with a "valid through <date> only" banner whenever the eligible sample is stale.
Data Integrity Status = worst of the legacy audit and `collect_alerts()`; it cannot be set by hand.

## Audit / correction process
`scripts/integrity_migrate.py` (idempotent): schema → canonical back-fill → lock reconstruction → classification
(`VALID`, `INVALID_DUPLICATE`, `INVALID_RACE_ID`, `MISSING_RESULT`, `MISSING_MARKET`, `NON_RUNNER`, `OTHER`) → settlement →
reconciliation. Each classification change appends to `correction_ledger` (before/after/reason/run id). Nothing is deleted;
excluded races stay in `race`/`prediction`/`runner_result`. Pre-repair dump: `backups/pre_integrity_20261017.dump`.
Phantom rule: a larger race at the same meeting containing ≥50% (min 2) of another race's runners = superseded provisional card.

## 16 Oct root cause
Identity was `UNIQUE(course, date, off_time)`; `external_ref` stored but unused; ingest was additive and never retired
races. The 15 Oct "tomorrow" fetch contained entries-stage cards alongside the declared ones; both were scored and locked at
07:49. On 16 Oct the provider dropped the entries-stage cards (Redcar 13:55, Haydock 14:12, Haydock 16:32) but the rows and
locks stayed, and results were later attached to Redcar 13:55 by horse-name matching. Same pattern on 13 Sep, 18 Sep, 26 Sep,
30 Sep, 5 Oct and 8 Oct (9 phantom races in total), plus Ayr 18 Sep locked on a 190-runner entries field.

## Runbook
* `python3 scripts/integrity_report.py [date]` → status, alerts, reconciliation, `logs/integrity_status.json`, `data_health.html`
* `python3 scripts/integrity_migrate.py [--dry-run]` → re-classify / re-settle
* Tests: `python3 -m pytest tests/test_integrity_pure.py tests/test_integrity_db.py` (DB tests roll back)
