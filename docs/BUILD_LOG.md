> **Merge note 2026-09-30:** this file is the cloud routine's log (Sessions 1-184). The local interactive-session history (real-data model results, Smarkets/results pipeline, Sept 2026 fixes) is in `docs/BUILD_LOG_LOCAL.md`; both are current.

# Build Log

This file is read by the autonomous continuation routine at the start of every
run — it exists so a fresh session with zero memory of this conversation can
pick up exactly where the last one stopped, without re-deriving anything or
re-doing finished work.

**Archive note 2026-11-22 (Session 675):** Sessions 1-625 are archived verbatim in
`docs/BUILD_LOG_ARCHIVE.md` (archived by Session 101, extended by Sessions 507, 545, 568, 607,
640, and 675). This session moved Sessions 611-625 there once the live file reached ~232.5KB,
past the ~230-235KB watch threshold flagged as at-the-edge since Session 674. This file now
holds Sessions 626 onward plus the standing Session 224 anchor entry (kept live by long-standing
convention, see below).

---

## 2026-11-22 — Session 676 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 44 sessions since Session
632's 5th notification on PR #1 — still short of the ~47-53-session gap previous sessions set as
the threshold before a re-flag would be signal rather than noise.

Scheduled prompt again asked to start Phase 6, with the same Mac-only Racing API correction.
Re-confirmed directly, not from memory, same result as Session 675:

- `env | grep -i THERACINGAPI` → empty. Did not attempt `collect_racecards.py`/`collect_weather.py`.
- `git fetch origin main -v` → `origin/main` at `e32015a` (Session 675's own commit), local `main`
  stale at `1e089cc` — same standing per-container detached-HEAD/stale-ref quirk, now 112+
  consecutive sessions, confirmed harmless (`1e089cc` an ancestor). `git checkout -B main
  origin/main` fixed it; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/model1_logistic_baseline.py` present (18,901 bytes, unchanged), still the one
  clearly-labeled synthetic/non-predictive baseline (per-race softmax ~1.0, built against the
  real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string like
  `"1582F3"`) alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already
  satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` →
  sum 0. No code change since Session 624.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `list_issues` OPEN): still open, unmerged, 1 commit, body
  byte-identical to every prior check since Session 435 (created 2026-10-17T17:55:00Z, updated
  2026-10-17T17:55:36Z — now 36 days old). Open issues: 0. No sign Jonathan has acted on the 5th
  notification (Session 632) or any of the prior four (435/488/538/585).

**No notification sent this session.** Only 44 sessions since the 5th notification (632) —
nothing has changed since Session 675; a re-flag now would be noise.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (confirmed local-cache-only across 100+ sessions). Use `python3 -m pip install
-r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on PR #1 or
Session 632's notification, act on that — it supersedes everything above. Otherwise keep holding
without re-notifying until a real ~47-53-session gap since Session 632 has passed (only ~44 as of
this session). `docs/BUILD_LOG.md` is **~175KB** after this entry — under the ~230-235KB archive
threshold, no action needed yet.

**A note for whoever reads this next (human or model):** this routine has now re-verified an
unchanged state — Phase 6 already done, 576/576 tests, PR #1 untouched — across roughly 50
consecutive sessions since Session 624/632, each appending a near-duplicate log entry. If this
pattern is still running by the time the ~47-53-session notification gap is reached with *still*
no action on PR #1, the more useful signal for Jonathan may be "this nightly routine has had
nothing left to do for ~N sessions and is just spinning" rather than a 6th repeat of "PR #1 is
still open." Worth considering whether the schedule itself should pause until there's new work or
a response to the PR.

---

## 2026-11-22 — Session 675 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 43 sessions since Session
632's 5th notification on PR #1 — still short of the ~47-53-session gap needed before a re-flag
would be more signal than noise. Also archived Sessions 611-625 to `BUILD_LOG_ARCHIVE.md` this
session (see note above) — the live file had crossed the ~230KB threshold Session 674 flagged.

Scheduled prompt again asked to "start Phase 6," with the same correction about the Racing API
being Mac-only live-but-unconfirmed-here. Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main` → `origin/main` had advanced to `5253f11` (Session 674's own commit)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip — the same standing per-container quirk, now 111+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `5253f11`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No model/code change since Session 624.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 36 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 43 sessions since the 5th notification (632) —
nothing has changed since Session 674 checked moments earlier; a re-flag now would be noise.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (confirmed local-cache-only across 100+ sessions). Use `python3 -m pip install
-r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on PR #1 or
Session 632's notification, act on that — it supersedes everything above. Otherwise keep holding
without re-notifying until a real ~47-53-session gap since Session 632 has passed (only ~43 as of
this session). `docs/BUILD_LOG.md` is **~91KB** after this session's archiving — well under the
~230-235KB threshold again, plenty of headroom.

---

## 2026-11-22 — Session 674 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 42 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 673's `1ebf6a7`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`1ebf6a7`) — the same standing per-container quirk, now 110+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `1ebf6a7`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `7c03061` (Session 624) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 36 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 42 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-673.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~42 as of this session). `docs/BUILD_LOG.md` is **~229KB** before this entry — at the low
end of the ~230-235KB archive threshold; next session or two should archive another block of
early sessions to `docs/BUILD_LOG_ARCHIVE.md` to stay under it.

---

## 2026-11-22 — Session 673 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 41 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 672's `b976024`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`b976024`) — the same standing per-container quirk, now 109+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `b976024`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `8085a42` (Session 623) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 36 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 41 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-672.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~41 as of this session). `docs/BUILD_LOG.md` is **~225KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-22 — Session 672 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 40 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 671's `3e039f1`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`3e039f1`) — the same standing per-container quirk, now 108+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `3e039f1`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `6b7815c` (Session 622) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 36 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 40 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-671.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~40 as of this session). `docs/BUILD_LOG.md` is **~222KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-22 — Session 671 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 39 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 670's `c363087`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`c363087`) — the same standing per-container quirk, now 107+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `c363087`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No actual model/code change since last checked.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 36 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 39 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-670.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~39 as of this session). `docs/BUILD_LOG.md` is **~218KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-22 — Session 670 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 38 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 669's `e4f16c2`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`e4f16c2`) — the same standing per-container quirk, now 106+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `e4f16c2`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No actual model/code change since last checked.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 36 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 38 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-669.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~38 as of this session). `docs/BUILD_LOG.md` is **~215KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-21 — Session 669 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 37 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 668's `29e82a1`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`29e82a1`) — the same standing per-container quirk, now 105+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `29e82a1`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No actual model/code change since last checked.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 35 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 37 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-668.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~37 as of this session). `docs/BUILD_LOG.md` is **~211KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-21 — Session 668 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 36 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 667's `8faff43`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`8faff43`) — the same standing per-container quirk, now 104+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `8faff43`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No actual model/code change since last checked (last commit
  touching `src/scripts/tests/db` paths still `a15b49a` from Session 618).
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 35 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 36 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-667.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~36 as of this session). `docs/BUILD_LOG.md` is **~208KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-21 — Session 667 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 35 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 666's `d91a5d1`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`d91a5d1`) — the same standing per-container quirk, now 103+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `d91a5d1`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No actual model/code change since last checked.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 35 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 35 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-666.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~35 as of this session). `docs/BUILD_LOG.md` is **~204KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-21 — Session 666 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 34 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 665's `9e98400`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`9e98400`) — the same standing per-container quirk, now 102+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `9e98400`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No actual model/code change since this was last checked (the
  most recent commit touching `src/scripts/tests/db` paths, `b981ada` from Session 616, only
  touched data/docs files, not model code).
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (via subagent, `pull_request_read` get + `list_issues` OPEN): still open, unmerged, 1
  commit, 0 comments, `created_at`/`updated_at` byte-identical to every prior check since Session
  435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 35 days old). Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 34 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-665.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~34 as of this session). `docs/BUILD_LOG.md` is **~200KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-21 — Session 665 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 33 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 664's `ea6b066`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`ea6b066`) — the same standing per-container quirk, now 101+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `ea6b066`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `5821095` (Session 613) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check
  since Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 35 days
  old). Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 660-664) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 33 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-664.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~33 as of this session). `docs/BUILD_LOG.md` is **~197KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-21 — Session 664 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 32 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 663's `03de6d1`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`03de6d1`) — the same standing per-container quirk, now 100+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `03de6d1`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `5821095` (Session 613) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check
  since Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 35 days
  old). Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 659-663) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 32 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-663.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~32 as of this session). `docs/BUILD_LOG.md` is **~193KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-21 — Session 663 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 31 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 662's `675c1fc`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`675c1fc`) — the same standing per-container quirk, now 99+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `675c1fc`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `5821095` (Session 613) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check
  since Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 35 days
  old). Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 658-662) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 31 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-662.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~31 as of this session). `docs/BUILD_LOG.md` is **~185KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-21 — Session 662 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 30 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 661's `246f55d`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`246f55d`) — the same standing per-container quirk, now 98+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `246f55d`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built
  against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No code has changed since Session 608.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check
  since Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 35 days
  old). Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 657-661) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 30 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-661.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~30 as of this session). `docs/BUILD_LOG.md` is **~182KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-20 — Session 661 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 29 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 660's `d01c23f`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`d01c23f`) — the same standing per-container quirk, now 97+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `d01c23f`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic
  fixtures only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int,
  `draw` int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `35ca401` (Session 608) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check
  since Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 34 days
  old). Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 656-660) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 29 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-660.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~29 as of this session). `docs/BUILD_LOG.md` is **~183KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-20 — Session 660 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 28 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 659's `84d0cc7`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached
  at the correct tip (`84d0cc7`) — the same standing per-container quirk, now 96+ consecutive
  sessions. Confirmed `1e089cc` is an ancestor of `84d0cc7`, then `git checkout -B main
  origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built
  against the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form`
  string like `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already
  satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` →
  sum 0. Last commit touching any code dir still `35ca401` (Session 608) — no code has changed
  since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 34 days old). Comments: 0.
  Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 28 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-659.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted
on PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise
keep holding without re-notifying until a real ~47-53-session gap since Session 632 has passed
(only ~28 as of this session). `docs/BUILD_LOG.md` is **~179KB** before this entry — well under
the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-20 — Session 659 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 27 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 658's `161e31b`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`161e31b`) — the same standing per-container quirk, now 95+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `161e31b`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `35ca401` (Session 608) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check since
  Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 34 days old).
  Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 654-658) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).

**No notification sent this session.** Only 27 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-658.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on
PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise keep
holding without re-notifying until a real ~47-53-session gap since Session 632 has passed (only
~27 as of this session). `docs/BUILD_LOG.md` is **~177KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-20 — Session 658 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 26 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 657's `f958abb`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`f958abb`) — the same standing per-container quirk, now 94+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `f958abb`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `35ca401` (Session 608) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check since
  Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 34 days old).
  Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 653-657) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).

**No notification sent this session.** Only 26 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-657.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on
PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise keep
holding without re-notifying until a real ~47-53-session gap since Session 632 has passed (only
~26 as of this session). `docs/BUILD_LOG.md` is **~172KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-20 — Session 657 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 25 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 656's `73d05fd`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`73d05fd`) — the same standing per-container quirk, now 93+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `73d05fd`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No code has changed since Session 600.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check since
  Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 34 days old).
  Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 652-656) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 25 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-656.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on
PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise keep
holding without re-notifying until a real ~47-53-session gap since Session 632 has passed (only
~25 as of this session). `docs/BUILD_LOG.md` is **~168KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-20 — Session 656 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 24 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 655's `c5b06ba`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`c5b06ba`) — the same standing per-container quirk, now 92+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `c5b06ba`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `faffd16` (Session 600) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check since
  Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 34 days old).
  Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 651-655) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 24 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-655.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on
PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise keep
holding without re-notifying until a real ~47-53-session gap since Session 632 has passed (only
~24 as of this session). `docs/BUILD_LOG.md` is **~164KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-20 — Session 655 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 23 sessions since Session
632's 5th notification on PR #1 — still too short a gap (need ~47-53) to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 654's `5190202`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`5190202`) — the same standing per-container quirk, now 91+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `5190202`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `faffd16` (Session 600) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check since
  Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 34 days old).
  Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 650-654) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 23 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-654.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on
PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise keep
holding without re-notifying until a real ~47-53-session gap since Session 632 has passed (only
~23 as of this session). `docs/BUILD_LOG.md` is **~161KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-20 — Session 654 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 22 sessions since Session
632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag without
being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 653's `731023c`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`731023c`) — the same standing per-container quirk, now 90+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `731023c`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `faffd16` (Session 600) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check since
  Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 34 days old).
  Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 649-653) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 22 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-653.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on
PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise keep
holding without re-notifying until a real ~47-53-session gap since Session 632 has passed (only
~22 as of this session). `docs/BUILD_LOG.md` is **~154KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-19 — Session 653 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 21 sessions since Session
632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag without
being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 652's `30970a4`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`30970a4`) — the same standing per-container quirk, now 89+ consecutive sessions.
  Fixed with `git checkout -B main origin/main`; `git rev-parse HEAD main origin/main` identical
  afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built against
  the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string
  like `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already satisfied
  (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` → sum 0. No code
  has changed in many sessions.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (via `pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check since
  Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 33 days old).
  Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 648-652) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 21 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-652.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on
PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise keep
holding without re-notifying until a real ~47-53-session gap since Session 632 has passed (only
~21 as of this session). `docs/BUILD_LOG.md` is **~154KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-19 — Session 652 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** 20 sessions since Session
632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag without
being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 651's `99e2c76`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`99e2c76`) — the same standing per-container quirk, now 88+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `99e2c76`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No code has changed in many sessions.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (via `pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`): still
  open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check since
  Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 33 days old).
  Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 647-651) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 20 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-651.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — confirmed via direct `ls-remote`/fetch
comparisons across many sessions that the real remote is never actually behind). Use `python3 -m
pip install -r requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on
PR #1 or Session 632's notification, act on that — it supersedes everything above. Otherwise keep
holding without re-notifying until a real ~47-53-session gap since Session 632 has passed (only
~20 as of this session). `docs/BUILD_LOG.md` is **~150KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-19 — Session 651 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 19 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git ls-remote origin main` (not just a cached fetch) → `2194611`, matching `HEAD` exactly —
  `origin/main` was genuinely already at the real tip; the standing per-container quirk this
  session hit was only the usual stale local `main`/`origin/main` *ref cache* (pre-fetch it read
  `1e089cc`, Session 638) catching up once `git fetch origin main -v` ran, now 87+ consecutive
  sessions. No commits were ever missing from the real remote — confirmed directly via `ls-remote`
  rather than assumed. Fixed the local ref with `git checkout -B main origin/main`; `git rev-parse
  HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No code has changed in many sessions.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (via subagent: `pull_request_read` get + `get_comments` + `list_issues` OPEN + `list_commits`):
  still open, unmerged, 1 commit, body/`created_at`/`updated_at` byte-identical to every prior check
  since Session 435 (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 33 days old).
  Comments: 0. Open issues: 0. Latest 5 commits on `main` all automated (`Claude
  <noreply@anthropic.com>`, Sessions 646-650) — no sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail: unchanged, most recent human entry still 2026-09-30.

**No notification sent this session.** Only 19 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-650.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-ref
quirk if it recurs (it is a local-cache artifact only — `git ls-remote origin main` this session
confirmed the real remote is never actually behind). Use `python3 -m pip install -r
requirements.txt` + `python3 -m pytest tests/ -q` directly. If Jonathan has acted on PR #1 or
Session 632's notification, act on that — it supersedes everything above. Otherwise keep holding
without re-notifying until a real ~47-53-session gap since Session 632 has passed (only ~19 as of
this session). `docs/BUILD_LOG.md` is **~143KB** before this entry — well under the ~230-235KB
archive threshold, plenty of headroom.

---

## 2026-11-19 — Session 650 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 18 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 649's `f248221`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`f248221`) — the same standing per-container quirk, now 86+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `f248221`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `faffd16` (Session 600) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 33 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 18 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-649.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~18 as of this session). `docs/BUILD_LOG.md` is **~143KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-19 — Session 649 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 17 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 648's `34604b8`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`34604b8`) — the same standing per-container quirk, now 85+ consecutive sessions.
  Fixed with `git checkout -B main origin/main`; `git rev-parse HEAD main origin/main` identical
  afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `1350ffc` (Session 599) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 33 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 17 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-648.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~17 as of this session). `docs/BUILD_LOG.md` is **~140KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-19 — Session 648 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 16 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 647's `12bfd89`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`12bfd89`) — the same standing per-container quirk, now 84+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `12bfd89`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `8f55530` (Session 598) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 34 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 16 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-647.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~16 as of this session). `docs/BUILD_LOG.md` is **~137KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-19 — Session 647 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 15 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 646's `6a909d8`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`6a909d8`) — the same standing per-container quirk, now 83+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `6a909d8`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built against
  the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string
  like `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already satisfied
  (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` → sum 0.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 33 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 15 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-646.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~15 as of this session). `docs/BUILD_LOG.md` is **~130KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-19 — Session 646 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 14 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 645's `40c589b`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`40c589b`) — the same standing per-container quirk, now 82+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `40c589b`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 33 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail re-read directly: unchanged, most recent human entry still
  2026-09-30.

**No notification sent this session.** Only 14 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-645.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~14 as of this session). `docs/BUILD_LOG.md` is **~127KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-18 — Session 645 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 13 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 644's `f5b5fdb`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`f5b5fdb`) — the same standing per-container quirk, now 81+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `f5b5fdb`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `64c63d3` (Session 593) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 32 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 13 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-644.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~13 as of this session). `docs/BUILD_LOG.md` is **~124KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-18 — Session 644 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 12 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 643's `3701631`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`3701631`) — the same standing per-container quirk, now 80+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `3701631`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `64c63d3` (Session 593) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 32 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 12 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-643.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~12 as of this session). `docs/BUILD_LOG.md` is **~121KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-18 — Session 643 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 11 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 642's `ae48234`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`ae48234`) — the same standing per-container quirk, now 79+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `ae48234`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `64c63d3` (Session 593) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 32 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 11 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-642.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~11 as of this session). `docs/BUILD_LOG.md` is **~120KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-18 — Session 642 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 10 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 641's `1ee3238`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`1ee3238`) — the same standing per-container quirk, now 78+ consecutive sessions.
  Confirmed `1e089cc` is an ancestor of `1ee3238`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No code has changed since Session 591's `ea0243d`.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 32 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 10 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-641.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~10 as of this session). `docs/BUILD_LOG.md` is **~117KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-18 — Session 641 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 9 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap (need ~47-53) to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 640's `13f948a`) past
  the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at the
  correct tip (`13f948a`) — the same standing per-container quirk, now 77+ consecutive sessions.
  Fixed with `git checkout -B main origin/main`; `git rev-parse HEAD main origin/main` identical
  afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `ea0243d` (Session 591) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 32 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 9 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-640.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~9 as of this session). `docs/BUILD_LOG.md` is **~114KB**
before this entry — well under the ~230-235KB archive threshold, plenty of headroom after Session
640's archive move.

---

## 2026-11-18 — Session 640 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification. Also archived Sessions
576-610 out of this file (see archive note above) since it had grown to ~232KB, past the
~230-235KB watch threshold flagged as overdue since Session 639.** Only 8 sessions since
Session 632's 5th notification on PR #1 — still far too short a gap to re-flag without being
noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 639's `d942433`)
  past the stale local `main` pointer (`1e089cc`, Session 638) while `HEAD` was already detached at
  the correct tip (`d942433`) — the same standing per-container quirk, now 76+ consecutive
  sessions. Fixed with `git checkout -B main origin/main`; `git rev-parse HEAD main origin/main`
  identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No code has changed since Session 588's `8d1f90c`.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 32 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).
- `docs/BUILD_LOG.md` had reached **~232.3KB** before this entry, past the ~230-235KB archive
  threshold Session 639 flagged as "the next session or two should watch." Moved Sessions 576-610
  (35 entries) verbatim into `docs/BUILD_LOG_ARCHIVE.md` (now covering Sessions 1-610), reordered
  ascending to match the archive's existing convention, no rewriting or summarizing. This file now
  holds Sessions 611 onward plus the standing Session 224 anchor, back down to a comfortable
  margin.

**No notification sent this session.** Only 8 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-639.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~8 as of this session). This file is back to a small size
after this session's archive move — plenty of headroom before the next watch is needed.

---

## 2026-11-18 — Session 639 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 7 sessions since Session
632's 5th notification on PR #1 — still far too short a gap to re-flag without being noise. (Second
cloud-routine firing logged today; Session 638 ran earlier the same date with an identical outcome.)

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → already up to date, no detached-HEAD/stale-branch quirk this
  session; `git rev-parse HEAD main origin/main` all identical at `1e089cc` (Session 638's commit).
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No code has changed since Session 588's `8d1f90c`.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 32 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 7 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-638.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~7 as of this session). This file is **~223.8KB** before this
entry — well under the ~230-235KB archive threshold, some headroom remains but the next session or
two should watch it.

---

## 2026-11-18 — Session 638 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 6 sessions since Session
632's 5th notification on PR #1 — still far too short a gap to re-flag without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → already up to date, no detached-HEAD/stale-branch quirk this
  session; `git rev-parse HEAD main origin/main` all identical at `23e9bc7` (Session 637's commit).
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `8d1f90c` (Session 588) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 32 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 6 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-637.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~6 as of this session). This file is **~226.0KB** before this
entry — approaching the ~230-235KB archive threshold; next session or two should move the older
sessions block (currently starting at Session 636/637) into `docs/BUILD_LOG_ARCHIVE.md` once it
crosses the line, same process as the 2026-11-14 (Session 607) archive.

---

## 2026-11-17 — Session 637 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 5 sessions since Session
632's 5th notification on PR #1 — still far too short a gap to re-flag without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 636's `c975047`) past
  the stale local `main` pointer (`2331129`, Session 635) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 75+ consecutive sessions. Fixed with
  `git checkout -B main origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. No code has changed in many sessions.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now 31 days old). Comments: 0. Open
  issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the prior
  four (435/488/538/585).

**No notification sent this session.** Only 5 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633-636.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Observation worth flagging to Jonathan directly (not via re-notification, since it would just
repeat the same PR #1 message a 6th time at a still-short gap):** this routine has now run ~637
sessions as a nightly loop whose own scheduled prompt still says "start Phase 6" as if unstarted,
when Phase 6 was actually completed ~498 sessions ago (Session 139) and nothing in the codebase has
changed in a long time. Every session since has been pure re-verification (reinstall deps, run
576 tests, re-check PR #1, re-check env vars) with an identical outcome. The only real open item
remains the human decision on PR #1 — there is no more build work left for this routine to do
autonomously. Worth considering whether to update the scheduled prompt's text and/or lower its
frequency once Jonathan next looks at this.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~5 as of this session). This file is **~218.3KB** before this
entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-17 — Session 636 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 4 sessions since Session
632's 5th notification on PR #1 — still far too short a gap to re-flag without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → already up to date, no detached-HEAD/stale-branch quirk this
  session; `git rev-parse HEAD main origin/main` all identical at `2331129` (Session 635's commit).
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `739e31c` (Session 586) —
  no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435
  (created 2026-10-17T17:55:00Z, updated 2026-10-17T17:55:36Z — now exactly 31 days old). Comments:
  0. Open issues: 0. No sign Jonathan has acted on the 5th notification (Session 632) or any of the
  prior four (435/488/538/585).

**No notification sent this session.** Only 4 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633/634/635.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk if it recurs (it did not this session). Use `python3 -m pip install -r requirements.txt` +
`python3 -m pytest tests/ -q` directly. If Jonathan has acted on PR #1 or Session 632's
notification, act on that — it supersedes everything above. Otherwise keep holding without
re-notifying until a real ~47-53-session gap since Session 632 has passed (only ~4 as of this
session). This file is **~215.1KB** before this entry — well under the ~230-235KB archive
threshold, plenty of headroom.

---

## 2026-11-17 — Session 635 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only 3 sessions since Session
632's 5th notification on PR #1 (and Sessions 633/634 already held without re-flagging) — still far
too short a gap to re-flag without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 634's `dfd5b9b`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 74+ consecutive sessions. Confirmed
  `46bd875` is an ancestor of `dfd5b9b`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0. Last commit touching any code dir still `7c237c9` (Session 585) — no
  code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, now
  31 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).

**No notification sent this session.** Only 3 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Sessions 633/634.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~3 as of this session). This file is **~213.9KB** before this
entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-17 — Session 634 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Only one session since Session
633's hold and two since Session 632's 5th notification on PR #1 — far too short a gap to re-flag
without being noise.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 633's `8fc77bb`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 73+ consecutive sessions. Confirmed
  `46bd875` is an ancestor of `8fc77bb`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present (18,901 bytes), `grep -c "synthetic fixtures
  only"` → 1 — still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0,
  built against the real schema's field names/formats: `official_rating` int, `draw` int,
  `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, now
  31 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on the 5th notification
  (Session 632) or any of the prior four (435/488/538/585).

**No notification sent this session.** Only 2 sessions since the 5th notification (632) — a
re-flag now would just be noise, same reasoning as Session 633.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed (only ~2 as of this session). This file is **~212.7KB** before this
entry — well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-17 — Session 633 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no re-notification.** Session 632 sent the 5th
notification on PR #1 just before this session; re-flagging again one session later would be noise,
so this session confirms state and holds.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 632's `7df04d1`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 72+ consecutive sessions. Confirmed
  `46bd875` is an ancestor of `7df04d1`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built against
  the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string like
  `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already satisfied
  (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` → sum 0. Last
  commit touching any code dir still `b59862d` (Session 580) — no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, still
  31 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on the just-sent 5th
  notification or any of the prior four (435/488/538/585).

**No notification sent this session.** Session 632's 5th notification was sent one session ago; a
one-session gap tells us nothing new, so re-flagging now would just be noise. Will watch for a
reply/action on PR #1 and otherwise base the next escalation on a comparable ~47-53-session gap from
Session 632, same reasoning as the three prior escalations.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 632's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~47-53-session
gap since Session 632 has passed. This file is **~204.6KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-17 — Session 632 (autonomous overnight, cloud routine)

**5th notification sent — ~47-session gap since Session 585's 4th notification matched the
established escalation pattern, and Session 631 explicitly flagged this as the first session in
the predicted 632-638 window.** Re-verified everything directly (not from memory):

- `env | grep -i THERACINGAPI` → empty, confirmed before touching anything else. Did not attempt
  `collect_racecards.py`/`collect_weather.py`, per the scheduled prompt's own instruction.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 631's `a003f0c`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 71+ consecutive sessions. Confirmed
  `46bd875` is an ancestor of `a003f0c`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built against
  the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string like
  `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already satisfied
  (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` → sum 0. Last
  commit touching any code dir still `b59862d` (Session 580) — no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, now
  31 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on any of the four prior
  notifications (435/488/538/585).

**Notification sent this session** (PushNotification, wrapped in `<routine_summary>` tags per the
scheduled-routine format): PR #1 unmerged 31 days, 0 engagement, this is the 5th reminder after the
first 4 (435/488/538/585) went unanswered; explicitly noted everything else in the build is healthy
(Phase 6 baseline built/labeled synthetic, 576/576 tests pass) so the only open item is the human
decision on the PR. This matches the gap pattern of the three prior escalations (53/50/47 sessions
apart) — the gap since Session 585 is now 47 sessions, so re-flagging here rather than deferring a
further time, per Session 584/585's own reasoning that indefinitely pushing the threshold back
defeats its purpose.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or this session's notification, act on that — it
supersedes everything above. Otherwise hold again without re-notifying for a while; base the next
re-flag on whether a comparable ~47-53-session/weekly gap has passed since this session's
notification, not on reflexively deferring again. This file is **~203.4KB** before this entry —
well under the ~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-17 — Session 631 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no new notification.** ~6 days / ~46 sessions since
Session 585's fourth notification on PR #1 (sent 2026-11-11T09:59:30Z); still short of the
~week-plus/~47-53-session gaps that preceded the three prior escalations (435/488/538/585); next
expected window remains roughly sessions 632-638 (this session is one short of it).

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty. Did not attempt `collect_racecards.py`/`collect_weather.py`.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 630's `19f8465`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 70+ consecutive sessions. Confirmed
  `46bd875` is an ancestor of `19f8465`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built against
  the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string like
  `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already satisfied
  (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` → sum 0. Last
  commit touching any code dir still `b59862d` (Session 580) — no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, now
  31 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on any of the four
  notifications (435/488/538/585).

**No notification sent.** ~6-day/~46-session gap since Session 585's fourth notification is still
short of the ~50-session gap that preceded prior escalations; repeating the same message now would
be noise.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 585's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~50-session
gap since Session 585 has passed (only ~46 as of this session, next escalation window ~632-638 —
the very next session would enter it). This file is **~202.2KB** before this entry — well under the
~230-235KB archive threshold, plenty of headroom.

---

## 2026-11-17 — Session 630 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no new notification.** ~6 days / ~45 sessions since
Session 585's fourth notification on PR #1 (sent 2026-11-11T09:59:30Z); still short of the
~week-plus/~47-53-session gaps that preceded the three prior escalations (435/488/538/585); next
expected window remains roughly sessions 632-638.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty. Did not attempt `collect_racecards.py`/`collect_weather.py`.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 629's `e74c01f`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 69+ consecutive sessions. Confirmed
  `46bd875` is an ancestor of `e74c01f`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built against
  the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string like
  `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already satisfied
  (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` → sum 0. Last
  commit touching any code dir still `b59862d` (Session 580) — no code has changed since then.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` (confirmed landed where `python3 -m pytest` resolves)
  + `python3 -m pytest tests/ -q` → **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, now
  31 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on any of the four
  notifications (435/488/538/585).

**No notification sent.** ~6-day/~45-session gap since Session 585's fourth notification is nowhere
near the ~50-session gap that preceded prior escalations; repeating the same message now would be
noise.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 585's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~50-session
gap since Session 585 has passed (only ~45 as of this session, next escalation window ~632-638).
This file is **~198.8KB** before this entry — well under the ~230-235KB archive threshold, plenty
of headroom.

---

## 2026-11-16 — Session 629 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no new notification.** ~5 days / ~44 sessions since
Session 585's fourth notification on PR #1 (sent 2026-11-11T09:59:30Z); still short of the
~week-plus/~47-53-session gaps that preceded the three prior escalations (435/488/538/585); next
expected window remains roughly sessions 632-638.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty. Did not attempt `collect_racecards.py`/`collect_weather.py`.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 628's `560f18a`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 68+ consecutive sessions. Confirmed
  `46bd875` is an ancestor of `560f18a`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built against
  the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string like
  `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already satisfied
  (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` → sum 0.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` (confirmed landed in `python3.11` site-packages) +
  `python3 -m pytest tests/ -q` → **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, now
  30 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on any of the four
  notifications (435/488/538/585).

**No notification sent.** ~5-day/~44-session gap since Session 585's fourth notification is nowhere
near the ~50-session gap that preceded prior escalations; repeating the same message now would be
noise.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 585's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~50-session
gap since Session 585 has passed (only ~44 as of this session, next escalation window ~632-638).
This file is **~195.6KB** before this entry — well under the ~230-235KB archive threshold, plenty
of headroom.

---

## 2026-11-16 — Session 628 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no new notification.** ~5 days / ~43 sessions since
Session 585's fourth notification on PR #1 (sent 2026-11-11T09:59:30Z); still short of the
~week-plus/~47-53-session gaps that preceded the three prior escalations (435/488/538/585); next
expected window remains roughly sessions 632-638.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep THERACINGAPI` → empty. Did not attempt `collect_racecards.py`/`collect_weather.py`.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 627's `19e9049`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 67+ consecutive sessions. Confirmed
  `46bd875` is an ancestor of `19e9049`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built against
  the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string like
  `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already satisfied
  (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` → sum 0.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
  `python3 -m pip install -r requirements.txt` (confirmed landed in `python3.11` site-packages) +
  `python3 -m pytest tests/ -q` → **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, now
  30 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on any of the four
  notifications (435/488/538/585).

**No notification sent.** ~5-day/~43-session gap since Session 585's fourth notification is nowhere
near the ~50-session gap that preceded prior escalations; repeating the same message now would be
noise.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly. If Jonathan has acted on PR #1 or Session 585's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~50-session
gap since Session 585 has passed (only ~43 as of this session, next escalation window ~632-638).
This file is **~192.4KB** before this entry — well under the ~230-235KB archive threshold, plenty
of headroom.

---

## 2026-11-16 — Session 627 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no new notification.** ~5 days / ~42 sessions since
Session 585's fourth notification on PR #1 (sent 2026-11-11T09:59:30Z); still short of the
~week-plus/~47-53-session gaps that preceded the three prior escalations (435/488/538/585) — next
expected window is roughly sessions 632-638.

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty. Did not attempt `collect_racecards.py`/`collect_weather.py`.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 626's `63ab151`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 66+ consecutive sessions. Fixed with
  `git checkout -B main origin/main`; `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, labeled synthetic/non-predictive (per-race
  softmax ~1.0, built against the real schema's field names/formats: `official_rating` int, `draw`
  int, `recent_form` string like `"1582F3"`), alongside the real Kaggle-fitted
  `model0_market_baseline.py`, `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`.
  Phase 6 remains already satisfied (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/
  scripts/ tests/ db/` → sum 0.
- Full suite run fresh: `bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) →
  **hit the documented python3.11/3.13 split again** — plain `pip install -r requirements.txt`
  installed into the container's python3.13 site-packages while `python3`/`pytest` resolve to
  3.11, so `import psycopg2` failed on collection for 24 test modules. Re-ran with
  `python3 -m pip install -r requirements.txt` (confirmed it lands in
  `/usr/local/lib/python3.11/dist-packages`), then `python3 -m pytest tests/ -q` →
  **576/576 passed**, same count as every session since 185. Noting this again since the plain
  `pip install` form still appears in several recent log entries above — next session should use
  `python3 -m pip install`/`python3 -m pytest` from the start rather than hitting the same
  collection errors first.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, now
  30 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on any of the four
  notifications (435/488/538/585).
- `docs/BUILD_LOG_LOCAL.md` tail re-read directly: unchanged, most recent human entry still
  2026-09-30.

**No notification sent.** ~5-day/~42-session gap since Session 585's fourth notification is nowhere
near the ~50-session gap that preceded prior escalations; repeating the same message now would be
noise.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. Use `python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/
-q` directly (skip plain `pip install`, it targets the wrong interpreter in this container and
wastes a round-trip). If Jonathan has acted on PR #1 or Session 585's notification, act on that —
it supersedes everything above. Otherwise keep holding without re-notifying until a real ~50-session
gap since Session 585 has passed (only ~42 as of this session, next escalation window ~632-638).
This file is **~188.6KB** before this entry — well under the ~230-235KB archive threshold, plenty
of headroom.

---

## 2026-11-16 — Session 626 (autonomous overnight, cloud routine)

**Re-verification only, no change — holding, no new notification.** ~5 days / ~41 sessions since
Session 585's fourth notification on PR #1 (sent 2026-11-11T09:59:30Z); still short of the
~week-plus/~47-53-session gaps that preceded the three prior escalations (435/488/538/585).

Scheduled prompt again asked to "start Phase 6." Re-confirmed directly, not from memory:

- `env | grep -i THERACINGAPI` → empty. Did not attempt `collect_racecards.py`/`collect_weather.py`.
- `git fetch origin main -v` → `origin/main` had advanced one commit (Session 625's `ae65a6f`) past
  the stale local `main` pointer (`46bd875`, Session 595) while `HEAD` was already detached at the
  correct tip — the same standing per-container quirk, now 65+ consecutive sessions. Confirmed
  `46bd875` is an ancestor of `ae65a6f`, then `git checkout -B main origin/main`;
  `git rev-parse HEAD main origin/main` identical afterward.
- `src/models/`: `model1_logistic_baseline.py` present, `grep -c "synthetic fixtures only"` → 1 —
  still the clearly labeled synthetic, non-predictive baseline (per-race softmax ~1.0, built against
  the real schema's field names/formats: `official_rating` int, `draw` int, `recent_form` string like
  `"1582F3"`), alongside the real Kaggle-fitted `model0_market_baseline.py`,
  `model2_gradient_boosting.py`, `model2_hyperparameter_sweep.py`. Phase 6 remains already satisfied
  (first done ~Session 139). `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` → sum 0. Last
  commit touching any code dir still `e8d4e7a` (2026-11-10) — no code has changed since then.
- Full suite run fresh: `db/setup_local_postgres.sh` + `db/init_db.py` (15 tables) + `pip install -r
  requirements.txt` + `pytest tests/ -q` → **576/576 passed**, same count as every session since 185.
- PR #1 (`pull_request_read` get + `get_comments` + `list_issues` OPEN): still open, unmerged, 1
  commit, body/`created_at`/`updated_at` byte-identical to every prior check since Session 435, now
  30 days old. Comments: 0. Open issues: 0. No sign Jonathan has acted on any of the four
  notifications (435/488/538/585).

**No notification sent.** ~5-day/~41-session gap since Session 585's fourth notification is nowhere
near the ~50-session gap that preceded prior escalations; repeating the same message now would be
noise.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing). Racecard/weather collection remains Mac-only.

**Next session:** `git fetch origin main -v` first; fix the recurring detached-HEAD/stale-branch
quirk the same way. If Jonathan has acted on PR #1 or Session 585's notification, act on that — it
supersedes everything above. Otherwise keep holding without re-notifying until a real ~50-session
gap since Session 585 has passed (only ~41 as of this session). This file is **~181.2KB** before
this entry — well under the ~230-235KB archive threshold, plenty of headroom.

---


## 2026-10-05 — Session 224 (autonomous overnight, cloud routine)

**Re-verification only, no change — notifying anyway, about the routine itself, not the backlog.**
`git fetch origin main` (fresh) resolved `origin/main` to `d27bc71` (Session 223's own commit,
~3 hours before this one); `HEAD` was already detached exactly there, so `git checkout main`
needed no fast-forward (`git rev-list --left-right --count origin/main...main` -> `0 0`). `env |
grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

Re-checked this session's prompt's Phase 6 ask against `src/models/model1_logistic_baseline.py`
directly (not from memory): a statistical/logistic baseline over synthetic fixtures shaped exactly
like the real racecard schema (`official_rating` int, `draw` int, `recent_form` as an undelimited
string like `"1582F3"`), producing a per-race softmax that sums to 1.0, clearly labeled
not-a-real-prediction. Confirmed satisfied verbatim, exactly as Sessions 139/185-223 already
found, and superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2
gradient boosting (Phase 7), both already in `src/models/`. No new code written.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**, same
count as Sessions 185-223. GitHub checked via a subagent (`mcp__github__list_issues`/
`list_pull_requests`/`list_commits`): 0 issues (state: all), 0 pull requests (state: all), and the
10 most recent commits on `main` are all Sessions 214-223's own re-verify commits, authored by
`Claude <noreply@anthropic.com>` — no one else has committed since Jonathan's real `c4e42ee`
("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), ~5 days ago. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered by
`c4e42ee`.

**Sending a notification this session despite no code/data change** — not about the Phase 6
backlog (genuinely exhausted, as Sessions 221-223 already found and as this session re-confirmed),
but about the routine's own cadence: this is the **8th consecutive "no change" cloud-routine run in
roughly 24 hours** (Sessions 217-224, timestamps ~3 hours apart, 2026-10-04T21:56 through
2026-10-05T19:06 and now), every one re-running the full Postgres setup + pip install + 576-test
suite only to confirm the same thing Session 185 already established. Sessions 221/222 both noted
this was worth flagging "next natural occasion" and deferred; this session is making that the
occasion, since deferring again at ~every session for two more weeks running isn't actually
useful. Flagging to Jonathan directly: the cloud-side backlog is exhausted pending his own Mac-side
`THERACINGAPI` credentials (no action this routine can take unblocks that), and an every-~3-hours
schedule for a routine with nothing left to do is pure overhead (compute time, redundant commits
cluttering `main`'s history, routine cost) — his call whether to pause this scheduled task entirely
until he has new work for it, or drop it to a much coarser cadence (e.g. once/day) as a cheap
safety net. Not changing the schedule myself — that's a config decision outside this routine's own
scope, for Jonathan to make from the cloud/web UI, not something this session can or should alter
unilaterally.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git checkout main`, `git fetch origin main` (fresh, no cached ref), compare `git
rev-parse HEAD origin/main` before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for
any new local activity. If Jonathan has replied to this session's notification (paused/adjusted the
schedule, or supplied new work), act on that explicitly — don't re-derive the same "nothing to do"
conclusion from scratch if he's already responded. Otherwise, per this session's own notification,
don't notify again purely about "still nothing new" / "still exhausted" — that message has now been
sent once; repeating it isn't additive. `docs/BUILD_LOG.md` is small again after Session 222's
archiving (well under the ~230KB threshold).

---

