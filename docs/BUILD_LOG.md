> **Merge note 2026-09-30:** this file is the cloud routine's log (Sessions 1-184). The local interactive-session history (real-data model results, Smarkets/results pipeline, Sept 2026 fixes) is in `docs/BUILD_LOG_LOCAL.md`; both are current.

# Build Log

This file is read by the autonomous continuation routine at the start of every
run — it exists so a fresh session with zero memory of this conversation can
pick up exactly where the last one stopped, without re-deriving anything or
re-doing finished work.

---

## 2026-10-13 — Session 357 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `8d7040b` (Session 356's own commit); local `HEAD` was already sitting exactly
there — no divergence, no stale-ref message this time. `env | grep -i THERACINGAPI` -> empty,
confirmed directly (Mac-only credentials; did not attempt `collect_racecards.py`/
`collect_weather.py`, per this session's prompt correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Read `src/models/model1_logistic_baseline.py`'s module docstring directly
(not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-356 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-356. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged, still 1149
lines): most recent entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's
real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~13 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 132 consecutive no-change sessions since it was sent (Sessions 225-357).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~134KB/~1789 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-13 — Session 356 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `229e4b0` (Session 355's own commit); local `HEAD` was already sitting exactly
there — no divergence. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt
correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Read `src/models/model1_logistic_baseline.py`'s module docstring directly
(not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-355 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-355. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged, still 1149
lines): most recent entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's
real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~13 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 131 consecutive no-change sessions since it was sent (Sessions 225-356).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~132KB/~1766 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-13 — Session 355 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `9853d0c` (Session 354's own commit); local `HEAD` was already sitting exactly
there — no divergence. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt
correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged: it still
satisfies that ask verbatim — `official_rating`/`draw` as int, `recent_form` as an undelimited
string like `"1582F3"`, per-race softmax summing to 1.0 by construction, clearly labeled not a real
prediction — as Sessions 139/185-354 have all already found, and remains superseded in practice by
the real Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in
`src/models/`. No new code written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-354. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged, still 1149
lines): most recent entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's
real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~13 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 130 consecutive no-change sessions since it was sent (Sessions 225-355).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~130KB/~1734 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-13 — Session 354 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `9921a3e` (Session 353's own commit); local `HEAD` was already sitting exactly
there — no divergence. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt
correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Re-read `src/models/model1_logistic_baseline.py`'s module docstring
directly (not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-353 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-353. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged, still 1149
lines): most recent entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's
real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~13 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 129 consecutive no-change sessions since it was sent (Sessions 225-354).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~128KB/~1711 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-13 — Session 353 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `68403ff` (Session 352's own commit); local `HEAD` was already sitting exactly
there — no divergence. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt
correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Re-read `src/models/model1_logistic_baseline.py`'s module docstring
directly (not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-352 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-352. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged, still 1149
lines): most recent entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's
real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~13 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 128 consecutive no-change sessions since it was sent (Sessions 225-353).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~126KB/~1687 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-13 — Session 352 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `253fc8c` (Session 351's own commit); local `HEAD` was already sitting exactly
there — no divergence. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt
correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Re-read `src/models/model1_logistic_baseline.py`'s module docstring
directly (not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-351 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-351. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent
entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's real `c4e42ee`
("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~13 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 127 consecutive no-change sessions since it was sent (Sessions 225-352).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~123KB/~1644 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-13 — Session 351 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `c0b1cf7` (Session 350's own commit); local `HEAD` was already sitting exactly
there — no divergence, no stale-ref message this time. `env | grep -i THERACINGAPI` -> empty,
confirmed directly (Mac-only credentials; did not attempt `collect_racecards.py`/
`collect_weather.py`, per this session's prompt correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Re-read `src/models/model1_logistic_baseline.py`'s module docstring
directly (not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-350 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-350. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged, still 1149
lines): most recent entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's
real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~13 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 126 consecutive no-change sessions since it was sent (Sessions 225-351).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~121KB/~1618 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-13 — Session 350 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `0aeb8f3` (Session 349's own commit); local `HEAD` was already sitting exactly
there (fetch reported the same recurring "forced update" ref-staleness message on the local `main`
branch ref — container-reuse artifact, not real divergence, as Sessions 336+ have documented).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Re-read `src/models/model1_logistic_baseline.py`'s module docstring
directly (not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-349 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-349. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent
entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's real `c4e42ee`
("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~13 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 125 consecutive no-change sessions since it was sent (Sessions 225-350).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~119KB/~1590 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-12 — Session 349 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `c14026e` (Session 348's own commit); local `HEAD` was already sitting exactly
there (fetch reported the same recurring "forced update" ref-staleness message on the local `main`
branch ref — container-reuse artifact, not real divergence, as Sessions 336+ have documented).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Re-read `src/models/model1_logistic_baseline.py`'s module docstring
directly (not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-348 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-348. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent
entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's real `c4e42ee`
("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~12 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 124 consecutive no-change sessions since it was sent (Sessions 225-349).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~116KB/~1541 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-12 — Session 348 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `bb0f7eb` (Session 347's own commit); local `HEAD` was already sitting exactly
there (fetch reported the same recurring "forced update" ref-staleness message on the local `main`
branch ref — container-reuse artifact, not real divergence, as Sessions 336+ have documented).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Re-read `src/models/model1_logistic_baseline.py`'s module docstring
directly (not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-347 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-347. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent
entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's real `c4e42ee`
("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~12 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 123 consecutive no-change sessions since it was sent (Sessions 225-348).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~112KB/~1494 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-12 — Session 347 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `27afa4a` (Session 346's own commit); local `HEAD` was already sitting exactly
there — fetch again reported the same recurring "forced update" ref-staleness message on the local
`main` branch ref (container-reuse artifact, not real divergence, as Sessions 336+ have documented).
Repo confirmed still a shallow clone (depth 50). `env | grep -i THERACINGAPI` -> empty, confirmed
directly (Mac-only credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per
this session's prompt correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Read `src/models/model1_logistic_baseline.py`'s module docstring directly
(not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as int,
`recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-346 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-346. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (open), 0 pull
requests (any state). Last 5 commits on `origin/main` are all Sessions 342-346's own re-verify
commits, authored by `Claude <noreply@anthropic.com>`. `docs/BUILD_LOG_LOCAL.md` tail re-read
directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered
by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 122 consecutive no-change sessions since it was sent (Sessions 225-347).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~106KB/~1412 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-12 — Session 346 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `d323bcb` (Session 345's own commit); local detached `HEAD` was already sitting
exactly there, no fast-forward needed — fetch again reported the same recurring "forced update"
ref-staleness message on the local `main` branch ref. Checked directly this time: the repo is a
shallow clone (`git rev-parse --is-shallow-repository` -> `true`, only 50 commits reachable from
`origin/main`), which is why `c4e42ee` (Jonathan's last real commit, now well past 50 commits back)
no longer resolves locally for an ancestry check — a clone-depth artifact, not real divergence or
history loss; HEAD matching `origin/main` exactly is sufficient confirmation on its own.
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Read `src/models/model1_logistic_baseline.py` directly (not from memory):
it still satisfies that ask verbatim — `official_rating`/`draw` as int, `recent_form` as an
undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by construction, clearly
labeled not a real prediction — as Sessions 139/185-345 have all already found, and remains
superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient
boosting, both already in `src/models/`. No new code written; a duplicate second baseline would
not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-345. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). Last 5 commits on `origin/main` are all Sessions 341-345's own re-verify
commits, authored by `Claude <noreply@anthropic.com>`. `docs/BUILD_LOG_LOCAL.md` tail re-read
directly (unchanged, still 1149 lines): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 121 consecutive no-change sessions since it was sent (Sessions 225-346).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked). Note:
this container's clone of the repo is shallow (depth 50) — an ancestry check against a commit older
than 50 commits back (e.g. `c4e42ee`) will fail to resolve locally; that's expected and not a sign
of real divergence, so don't re-investigate it as a bug. `docs/BUILD_LOG.md` is ~104KB/~1390 lines
before this entry — comfortably under the ~230KB archive threshold, no archiving needed for a good
while.

---

## 2026-10-12 — Session 345 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `bd082da` (Session 344's own commit); local detached `HEAD` was already sitting
exactly there, no fast-forward needed — fetch again reported the same recurring "forced update"
container-reuse ref-staleness artifact on the local `main` branch ref that prior sessions have
documented, not real divergence. `env | grep THERACINGAPI` -> empty, confirmed directly (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt
correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged: it still
satisfies that ask verbatim — `official_rating`/`draw` as int, `recent_form` as an undelimited
string like `"1582F3"`, per-race softmax summing to 1.0 by construction, clearly labeled not a real
prediction — as Sessions 139/185-344 have all already found, and remains superseded in practice by
the real Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in
`src/models/`. No new code written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-344. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (open), 0 pull
requests (any state). Last 5 commits on `origin/main` are all Sessions 340-344's own re-verify
commits, authored by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real
`c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~12 days (confirmed `c4e42ee` is still an ancestor of
`origin/main`). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry
still the 2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 120 consecutive no-change sessions since it was sent (Sessions 225-345).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~100KB/~1341 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-12 — Session 344 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `3556957` (Session 343's own commit); local detached `HEAD` was already sitting
exactly there (fetch reported the same recurring "forced update" container-reuse ref-staleness
artifact on the local `main` branch ref prior sessions have documented — not real divergence).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). Re-read `src/models/model1_logistic_baseline.py`'s module docstring
directly (not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as
int, `recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-343 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-343. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). Last 5 commits on `origin/main` are all Sessions 339-343's own re-verify
commits, authored by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real
`c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~12 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged, still 1149 lines): most recent entry still the 2026-09-30 Smarkets/results fix already
covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 119 consecutive no-change sessions since it was sent (Sessions 225-344).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~96KB/~1285 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-12 — Session 343 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `f4239d3` (Session 342's own commit); local detached `HEAD` was already sitting
exactly there (fetch reported the same recurring "forced update" container-reuse ref-staleness
artifact on the local `main` branch ref prior sessions have documented — not real divergence).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged, as
Sessions 139/185-342 have all already found, and remains superseded in practice by the real
Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in
`src/models/`. No new code written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-342. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). Last 15 commits on `origin/main` are all Sessions 328-342's own
re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human commit newer than
Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping
SP", 2026-09-30T22:29:42+01:00), now ~12 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged, still 1149 lines): most recent entry still the 2026-09-30 Smarkets/results fix already
covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 118 consecutive no-change sessions since it was sent (Sessions 225-343).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~93KB/~1244 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-12 — Session 342 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `6a37d08` (Session 341's own commit); local detached `HEAD` was already sitting
exactly there (fetch reported the same recurring "forced update" container-reuse ref-staleness
artifact on the local `main` branch ref prior sessions have documented — not real divergence).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged, as
Sessions 139/185-341 have all already found, and remains superseded in practice by the real
Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in
`src/models/`. No new code written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-341. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). Latest commit on `origin/main` is Session 341's own re-verify commit,
authored by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real
`c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~12 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered by
`c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 117 consecutive no-change sessions since it was sent (Sessions 225-342).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~90KB/~1198 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-11 — Session 341 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `9e35783` (Session 340's own commit); local detached `HEAD` was already sitting
exactly there (fetch reported the same recurring "forced update" container-reuse ref-staleness
artifact on the local `main` branch ref prior sessions have documented — not real divergence).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged, as
Sessions 139/185-340 have all already found, and remains superseded in practice by the real
Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in
`src/models/`. No new code written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-340. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). Last 5 commits on `origin/main` are all Sessions 336-340's own re-verify
commits, authored by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real
`c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~11 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered by
`c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 116 consecutive no-change sessions since it was sent (Sessions 225-341).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is comfortably under the ~230KB archive threshold, no archiving needed for a
good while.

---

## 2026-10-11 — Session 340 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `4f37608` (Session 339's own commit); local `HEAD` was already sitting exactly
there, no fast-forward needed (fetch reported a forced update on the local `main` branch ref, the
same recurring container-reuse artifact prior sessions have documented — not real divergence).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged, as
Sessions 139/185-339 have all already found, and remains superseded in practice by the real
Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in
`src/models/`. No new code written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-339. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Latest commit on `main` is Session
339's own re-verify commit, authored by `Claude <noreply@anthropic.com>` — no human commit newer
than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert
wiping SP", 2026-09-30T22:29:42+01:00), now ~11 days. `docs/BUILD_LOG_LOCAL.md` tail re-read
directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered
by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 115 consecutive no-change sessions since it was sent (Sessions 225-340).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~82KB/~1103 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-11 — Session 339 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `f1c4c07` (Session 338's own archiving commit); local detached `HEAD` was already
sitting exactly there, no fast-forward needed. Confirmed `f1c4c07` is just Session 338's own
`docs/BUILD_LOG.md`/`docs/BUILD_LOG_ARCHIVE.md` archiving commit (`git show --stat`), not new human
activity. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not
attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as
every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged, as
Sessions 139/185-338 have all already found, and remains superseded in practice by the real
Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in
`src/models/`. No new code written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-338. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most
recent entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's real
`c4e42ee`, now ~11 days old with no newer human commit on `origin/main`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 114 consecutive no-change sessions since it was sent (Sessions 225-339).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely stale again on container
reuse — try `git checkout -B main origin/main` first and fall back to detached-HEAD work if
denied. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If Jonathan has replied
to Session 224's notification, act on that explicitly. Otherwise keep not re-sending the "nothing
to do" notification — only notify again if something actually changes (a reply from Jonathan, a
new GitHub issue/PR, a test failure, or new work becoming unblocked). `docs/BUILD_LOG.md` stays a
manageable size after Session 338's archiving — no archiving needed for a good while.

---

## 2026-10-11 — Session 338 (autonomous overnight, cloud routine)

**Re-verification: no code/data change, but did the housekeeping Session 337 flagged — no push
notification (nothing for Jonathan to act on).** `git fetch origin main` (fresh) showed
`origin/main` at `528f19f` (Session 337's own commit); local detached `HEAD` was already sitting
exactly there, no fast-forward needed. The local `main` branch ref was stale again (still Session
225's `21c0e11`), the same recurring container-reuse artifact every prior session has documented —
worked from detached HEAD, sufficient for verification, committing, and pushing. `env | grep -i
THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged, as
Sessions 139/185-337 have all already found, and remains superseded in practice by the real
Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in
`src/models/`. No new code written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-337. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (any state), 0
pull requests (any state). `docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most
recent entry still the 2026-09-30 Smarkets/results fix already covered by Jonathan's real
`c4e42ee`, now ~11 days old with no newer human commit on `origin/main`.

**Housekeeping done this session (the one piece of real work available):** Session 337 flagged
`docs/BUILD_LOG.md` at ~218KB/~2965 lines, approaching the ~230KB archive threshold. Archived
Sessions 281-320 (40 sessions, all identical automated re-verification runs, verbatim, no rewriting
or summarizing) into `docs/BUILD_LOG_ARCHIVE.md`, following the same pattern Sessions 159/193/222/
265/285/312 already used. The live log now holds only Sessions 321-337 plus the Session 224 anchor
entry (kept live rather than archived, since later sessions' "Next session" notes keep referring
back to its notification about the routine's own cadence) — back down to a manageable size.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 113 consecutive no-change sessions since it was sent (Sessions 225-338).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely stale again on container
reuse — try `git checkout -B main origin/main` first and fall back to detached-HEAD work if
denied. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If Jonathan has replied
to Session 224's notification, act on that explicitly. Otherwise keep not re-sending the "nothing
to do" notification — only notify again if something actually changes (a reply from Jonathan, a
new GitHub issue/PR, a test failure, or new work becoming unblocked). `docs/BUILD_LOG.md` is back
down to a small size after this session's archiving — no archiving needed for a good while.

---

## 2026-10-11 — Session 337 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `9e92ad0` (Session 336's own commit); local detached `HEAD` was already sitting
exactly there. The local `main` branch ref was stale again (still Session 225's `21c0e11`, "ahead
57, behind 50" — same recurring container-reuse artifact every prior session has documented, not
real divergence); `git checkout -B main origin/main` was denied by the auto-mode classifier this
run, so worked from detached HEAD instead (sufficient for verification, committing, and pushing).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged, as
Sessions 139/185-336 have all already found, and remains superseded in practice by the real
Kaggle-fitted Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in
`src/models/`. No new code written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-336. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (open), 0 pull
requests (any state). Last 5 commits on `origin/main` are all Sessions 332-336's own re-verify
commits, authored by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real
`c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~11 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered by
`c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 112 consecutive no-change sessions since it was sent (Sessions 225-337).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely stale again on container
reuse — try `git checkout -B main origin/main` first and fall back to detached-HEAD work if
denied. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If Jonathan has replied
to Session 224's notification, act on that explicitly. Otherwise keep not re-sending the "nothing
to do" notification — only notify again if something actually changes (a reply from Jonathan, a
new GitHub issue/PR, a test failure, or new work becoming unblocked). Given 112 consecutive
no-change sessions, this routine's schedule firing multiple times per night with nothing to do is
worth Jonathan's attention — Session 224 raised this and it remains unresolved.
`docs/BUILD_LOG.md` is ~218KB/~2965 lines before this entry — approaching the ~230KB archive
threshold; the next session or two should archive older entries (e.g. Sessions ~225-300) into a
dated archive file to keep this file manageable.

---

## 2026-10-11 — Session 336 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `12a2885` (Session 335's own commit); local detached `HEAD` was already sitting
exactly there, no fast-forward needed. The local `main` branch ref was stale (pointing at Session
225's old `21c0e11`, "ahead 57, behind 50" against `origin/main` — the same recurring
container-reuse artifact prior sessions have documented, not real divergence); resolved by
`git checkout main && git reset --hard origin/main`, which only moves the local branch pointer to
match the already-fetched, already-current remote — no content lost, working tree was clean
throughout. `env | grep THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not
attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as
every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-335 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-335. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 331-335's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~11 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 111 consecutive no-change sessions since it was sent (Sessions 225-336).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~214KB/~2919 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-11 — Session 335 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `11c0d1c` (Session 334's own commit); local detached `HEAD` was already sitting
exactly there, no fast-forward needed. The local `main` branch ref was stale again (still Session
225's `21c0e11`, "ahead 57, behind 50" — same recurring container-reuse artifact prior sessions
documented, not real divergence). Worked from detached HEAD, same as Session 334. `env | grep -i
THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-334 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive. (Note for whoever next edits this
routine's stored prompt: the "start Phase 6" instruction has now been a no-op for 150+ consecutive
sessions since it first shipped — the prompt text itself is stale and could be updated to stop
asking for already-completed work.)

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-334. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 10 commits on `origin/main` are
all Sessions 325-334's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no
human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices;
stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~11 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged, still 1149 lines): most recent entry still the 2026-09-30
Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 111 consecutive no-change sessions since it was sent (Sessions 225-335).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely stale again on container
reuse — try `git checkout -B main origin/main` first and fall back to detached-HEAD work if
denied; if it looks like `main`/`origin/main` have "diverged" with no common ancestor, that is this
same stale-ref artifact, not real history loss — confirm with `git merge-base --is-ancestor
c4e42ee origin/main` before concluding anything is actually wrong. Read `docs/BUILD_LOG_LOCAL.md`'s
tail for any new local activity. If Jonathan has replied to Session 224's notification, act on that
explicitly. Otherwise keep not re-sending the "nothing to do" notification — only notify again if
something actually changes (a reply from Jonathan, a new GitHub issue/PR, a test failure, or new
work becoming unblocked). Given 111 consecutive no-change sessions, consider whether this routine's
schedule should be coarsened (fewer, less frequent runs) rather than continuing to re-verify an
unchanged repo every night — Session 224 raised this and it remains worth Jonathan's attention.
`docs/BUILD_LOG.md` is ~204KB/~2818 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-11 — Session 334 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `315fd65` (Session 333's own commit); local detached `HEAD` was already sitting
exactly there, no fast-forward needed. The local `main` branch ref was stale again (still Session
225's `21c0e11`, "ahead 57, behind 50" — same recurring container-reuse artifact prior sessions
documented, not real divergence); confirmed directly via `git merge-base --is-ancestor c4e42ee
origin/main` before concluding anything, since the only quick way to compare `main`/`origin/main`
otherwise would mislead. Worked from detached HEAD, same as Session 333. `env | grep -i
THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-333 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-333. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 15 commits on `origin/main` are
all Sessions 319-333's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no
human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices;
stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~11 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged, still 1149 lines): most recent entry still the 2026-09-30
Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 110 consecutive no-change sessions since it was sent (Sessions 225-334).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely stale again on container
reuse — try `git checkout -B main origin/main` first and fall back to detached-HEAD work if
denied; if it looks like `main`/`origin/main` have "diverged" with no common ancestor, that is this
same stale-ref artifact, not real history loss — confirm with `git merge-base --is-ancestor
c4e42ee origin/main` before concluding anything is actually wrong. Read `docs/BUILD_LOG_LOCAL.md`'s
tail for any new local activity. If Jonathan has replied to Session 224's notification, act on that
explicitly. Otherwise keep not re-sending the "nothing to do" notification — only notify again if
something actually changes (a reply from Jonathan, a new GitHub issue/PR, a test failure, or new
work becoming unblocked). Given 110 consecutive no-change sessions, consider whether this routine's
schedule should be coarsened (fewer, less frequent runs) rather than continuing to re-verify an
unchanged repo every night — Session 224 raised this and it remains worth Jonathan's attention.
`docs/BUILD_LOG.md` is ~199KB/~2758 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-10 — Session 333 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `4ed5f09` (Session 332's own commit); local detached `HEAD` was already sitting
exactly there, no fast-forward needed. The local `main` branch ref had gone stale again (still
pointing at Session 225's `21c0e11`, the same recurring container-reuse artifact prior sessions
documented) — `git checkout -B main origin/main` was denied this run (same denial pattern as
Sessions 324/326-328), so worked from detached HEAD instead, same as those sessions; `origin/main`'s
own history is a normal, unbroken chain — confirmed directly via `git merge-base --is-ancestor
c4e42ee origin/main` before concluding anything, since `main`/`origin/main` initially looked
unrelated (`git merge-base main origin/main` returned nothing) purely because of the stale local
branch ref, not real data loss. `env | grep -i THERACINGAPI` -> empty, confirmed directly
(Mac-only credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this
session's prompt correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-332 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-332. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 10 commits on `main` are all
Sessions 323-332's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~10 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged, still 1149 lines): most recent entry still the 2026-09-30
Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 109 consecutive no-change sessions since it was sent (Sessions 225-333).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely stale again on container
reuse — try `git checkout -B main origin/main` first and fall back to detached-HEAD work if
denied; if it looks like `main`/`origin/main` have "diverged" with no common ancestor, that is this
same stale-ref artifact, not real history loss — confirm with `git merge-base --is-ancestor
c4e42ee origin/main` before concluding anything is actually wrong. Read `docs/BUILD_LOG_LOCAL.md`'s
tail for any new local activity. If Jonathan has replied to Session 224's notification, act on that
explicitly. Otherwise keep not re-sending the "nothing to do" notification — only notify again if
something actually changes (a reply from Jonathan, a new GitHub issue/PR, a test failure, or new
work becoming unblocked). `docs/BUILD_LOG.md` is ~193KB/~2700 lines before this entry —
comfortably under the ~230KB archive threshold, no archiving needed for a good while.

---

## 2026-10-10 — Session 332 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `d157507` (Session 331's own commit); local `HEAD` was already detached and
sitting exactly there. The local `main` branch ref had gone stale again (still pointing at Session
225's `21c0e11`, same recurring container-reuse artifact Sessions 324-331 documented) —
`git checkout -B main origin/main` was permitted this run and fixed it cleanly, same as Session
331. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not
attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as
every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-331 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-331. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (open), 0 pull
requests (any state). Last 5 commits on `main` are all Sessions 327-331's own re-verify commits,
authored by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real
`c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~10 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged, still 1149 lines): most recent entry still the 2026-09-30 Smarkets/results fix already
covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 108 consecutive no-change sessions since it was sent (Sessions 225-332).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely stale again on container
reuse — `git checkout -B main origin/main` has now worked cleanly for two sessions running (330,
331) after being denied several times before that; try it first and fall back to detached-HEAD
work only if denied. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If Jonathan
has replied to Session 224's notification, act on that explicitly. Otherwise keep not re-sending
the "nothing to do" notification — only notify again if something actually changes (a reply from
Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked). `docs/BUILD_LOG.md`
is ~190KB/~2645 lines before this entry — comfortably under the ~230KB archive threshold, no
archiving needed for a good while.

---

## 2026-10-10 — Session 331 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `ab2346e` (Session 330's own commit); local `HEAD` was already detached and
sitting exactly there. This time `git checkout -B main origin/main` was NOT denied (unlike Sessions
326-328's attempts) — ran it and it cleanly fixed the stale `main` branch ref (previously stuck at
Session 225's `21c0e11`), so `main` now tracks `origin/main` properly again for the first time since
that staleness appeared. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt
correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-330 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-330. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (open), 0 pull
requests (any state). Last 20 commits on `main` are all Sessions 311-330's own re-verify commits,
authored by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real `c4e42ee`
("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~10 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged, still 1149 lines): most recent entry still the 2026-09-30 Smarkets/results fix already
covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 107 consecutive no-change sessions since it was sent (Sessions 225-331).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The `main` branch ref was fixed this session (`git checkout -B main
origin/main` succeeded, no longer denied) — if it's gone stale again, the same command should work;
if denied, detached-HEAD work is a fine fallback as in prior sessions. Read
`docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If Jonathan has replied to Session
224's notification, act on that explicitly. Otherwise keep not re-sending the "nothing to do"
notification — only notify again if something actually changes (a reply from Jonathan, a new
GitHub issue/PR, a test failure, or new work becoming unblocked). `docs/BUILD_LOG.md` is
~187KB/~2592 lines before this entry — comfortably under the ~230KB archive threshold, no
archiving needed for a good while.

---

## 2026-10-10 — Session 330 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `835d63a` (Session 329's own commit); local `HEAD` was already detached and
sitting exactly there (`git rev-parse HEAD origin/main` -> same SHA both lines) — the fetch still
reported `main -> origin/main (forced update)` for the local branch ref, the same recurring
container-reuse ref-staleness artifact Sessions 324-329 documented (local `main` branch ref lagging
behind detached `HEAD`; `origin/main`'s own history is a normal, unbroken chain, not a real
force-push). Worked from detached HEAD as before. `env | grep -i THERACINGAPI` -> empty, confirmed
directly (Mac-only credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per
this session's prompt correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-329 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-329. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (open), 0 pull requests (any state). Last 5 commits on `main` are all Sessions 325-329's
own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human commit newer than
Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping
SP", 2026-09-30T22:29:42+01:00), now ~10 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged, still 1149 lines): most recent entry still the 2026-09-30 Smarkets/results fix already
covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 106 consecutive no-change sessions since it was sent (Sessions 225-330).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely still stale — if a plain
`git checkout -B main origin/main` is permitted in that session's context, use it to fix it
properly; detached-HEAD work (as this session did) is a fine fallback if it's denied again. Read
`docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If Jonathan has replied to Session
224's notification, act on that explicitly. Otherwise keep not re-sending the "nothing to do"
notification — only notify again if something actually changes (a reply from Jonathan, a new
GitHub issue/PR, a test failure, or new work becoming unblocked). `docs/BUILD_LOG.md` is
~183KB/~2536 lines before this entry — comfortably under the ~230KB archive threshold, no
archiving needed for a good while.

---

## 2026-10-10 — Session 329 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `93f7e11` (Session 328's own commit); local `HEAD` was already detached and
sitting exactly there (`git rev-parse HEAD origin/main` -> same SHA both lines) — the fetch still
reported `main -> origin/main (forced update)` for the local branch ref, the same recurring
container-reuse ref-staleness artifact Sessions 324-328 documented (local `main` branch ref lagging
behind detached `HEAD`; `origin/main`'s own history is a normal, unbroken chain, not a real
force-push). Worked from detached HEAD as before. `env | grep -i THERACINGAPI` -> empty, confirmed
directly (Mac-only credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per
this session's prompt correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-328 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-328. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (open), 0 pull
requests (any state). Last 20 commits on `main` are all Sessions 310-328's own re-verify/archiving
commits, authored by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real
`c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~10 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged, still 1149 lines): most recent entry still the 2026-09-30 Smarkets/results fix already
covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 105 consecutive no-change sessions since it was sent (Sessions 225-329).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely still stale — if a plain
`git checkout -B main origin/main` is permitted in that session's context, use it to fix it
properly; detached-HEAD work (as this session did) is a fine fallback if it's denied again. Read
`docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If Jonathan has replied to Session
224's notification, act on that explicitly. Otherwise keep not re-sending the "nothing to do"
notification — only notify again if something actually changes (a reply from Jonathan, a new
GitHub issue/PR, a test failure, or new work becoming unblocked). `docs/BUILD_LOG.md` is
~179KB/~2480 lines before this entry — comfortably under the ~230KB archive threshold, no
archiving needed for a good while.

---

## 2026-10-10 — Session 328 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `be35b67` (Session 327's own commit); local `HEAD` was already detached and
sitting exactly there (`git rev-parse HEAD origin/main` -> same SHA both lines). Same recurring
container-reuse ref-staleness artifact Sessions 324-327 documented: local `main` branch ref still
points at Session 225's `21c0e11` (fetch itself reported `main -> origin/main (forced update)` for
that ref, which is just this staleness being corrected locally, not a real force-push on GitHub —
`origin/main`'s own history is the normal, unbroken chain). `git checkout -B main origin/main` was
again denied by the auto-mode permission classifier as an "irreversible local destruction" risk;
did not fight the denial, worked from detached HEAD instead (sufficient for verification,
committing, and pushing). `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's
prompt correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-327 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-327. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (open and closed), 0 pull requests (open and closed). Last 10 commits on `main` are all
Sessions 318-327's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~10 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged, still 1149 lines): most recent entry still the 2026-09-30
Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 104 consecutive no-change sessions since it was sent (Sessions 225-328).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely still stale (pointing at
Session 225's `21c0e11`) — if a plain `git checkout -B main origin/main` is permitted in that
session's context, use it to fix it properly; detached-HEAD work (as this session did) is a fine
fallback if it's denied again. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~176KB/~2423 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-10 — Session 327 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `d4d9c3e` (Session 326's own commit); local `HEAD` was already detached and
sitting exactly there (`git rev-parse HEAD origin/main` -> same SHA both lines). Same recurring
container-reuse ref-staleness artifact Sessions 324-326 documented: local `main` branch ref still
points at Session 225's `21c0e11`. `git checkout -B main origin/main` was again denied by the
auto-mode permission classifier as an "irreversible local destruction" risk; did not fight the
denial, worked from detached HEAD instead (sufficient for verification, committing, and pushing).
`env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-326 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-326. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (open and
closed), 0 pull requests (open and closed). Last 9 commits on `main` are all Sessions 318-326's own
re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human commit newer than
Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping
SP", 2026-09-30T22:29:42+01:00), now ~10 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered by
`c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 103 consecutive no-change sessions since it was sent (Sessions 225-327).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely still stale (pointing at
Session 225's `21c0e11`) — if a plain `git checkout -B main origin/main` is permitted in that
session's context, use it to fix it properly; detached-HEAD work (as this session did) is a fine
fallback if it's denied again. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~173KB/~2367 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-10 — Session 326 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `8a14d9d` (Session 325's own commit); local `HEAD` was already detached and
sitting exactly there. Hit the same recurring container-reuse ref-staleness artifact Sessions
324-325 documented: local `main` branch ref still pointed at Session 225's `21c0e11` (this repo's
shallow clone means `git merge-base` can't prove the two share history, but `origin/main`'s own
log shows the normal, unbroken Session 225->325 commit chain, so there is no real divergence).
This time `git checkout -B main origin/main` was denied by the auto-mode permission classifier as
an "irreversible local destruction" risk; did not fight the denial. Worked from detached HEAD
instead (sufficient for verification, committing, and pushing) rather than attempting a bypass —
leaving the stale `main` ref for a future session, or Jonathan, to tidy with that same command if
desired. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not
attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as
every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-325 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-325. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked directly against the live API with `mcp__github__` tools: 0 issues (open and
closed), 0 pull requests (open and closed). Last 8 commits on `main` are all Sessions 318-325's own
re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human commit newer than
Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping
SP", 2026-09-30T22:29:42+01:00), now ~10 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered by
`c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 102 consecutive no-change sessions since it was sent (Sessions 225-326).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. The local `main` branch ref is very likely still stale (pointing at
Session 225's `21c0e11`) — if a plain `git checkout -B main origin/main` is permitted in that
session's context, use it to fix it properly; detached-HEAD work (as this session did) is a fine
fallback if it's denied again. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~170KB/~2308 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 325 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `ce22498` (Session 324's own commit). Hit the exact same container-reuse ref-
staleness artifact Session 324 documented: local `main` ref still pointed at Session 225's
`21c0e11` with `HEAD` detached and already sitting at `ce22498` (no real divergence — `git log
origin/main` showed the normal, unbroken commit chain). Fixed the same way, `git checkout -B main
origin/main`. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only credentials;
did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt correction,
same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-324 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-324. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 320-324's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 101 consecutive no-change sessions since it was sent (Sessions 225-325).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. If the local `main` ref is stale again (detached HEAD already at the
right commit, `main` pointing at an old SHA), re-fix with `git checkout -B main origin/main` as
Sessions 324-325 both did — this looks like a recurring container-reuse artifact, not a one-off.
Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If Jonathan has replied to
Session 224's notification, act on that explicitly. Otherwise keep not re-sending the "nothing to
do" notification — only notify again if something actually changes (a reply from Jonathan, a new
GitHub issue/PR, a test failure, or new work becoming unblocked). `docs/BUILD_LOG.md` is
~165KB/~2253 lines before this entry — comfortably under the ~230KB archive threshold, no
archiving needed for a good while.

---

## 2026-10-09 — Session 324 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `507e28f` (Session 323's own commit). The local checkout's `main` branch ref had
gone stale (still pointing at Session 225's `21c0e11`, with `HEAD` itself detached and already
sitting at `507e28f` — a container-reuse artifact, not an actual force-push on GitHub; confirmed
via `git log origin/main` showing the normal, unbroken Session 225->323 chain). Fixed with
`git checkout -B main origin/main` so `main` tracks `origin/main` cleanly again; no content divergence,
no fast-forward needed. `env | grep -i THERACINGAPI` -> empty, confirmed directly (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's prompt
correction, same as every prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-323 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-323. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 319-323's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 100 consecutive no-change sessions since it was sent (Sessions 225-324).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~158KB/~2201 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 323 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `86af0b6` (Session 322's own commit); local `HEAD` was already exactly there
(`git rev-parse HEAD origin/main` -> same SHA both lines), no fast-forward needed. `env | grep -i
THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-322 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-322. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 318-322's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 99 consecutive no-change sessions since it was sent (Sessions 225-323).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~151KB/~2193 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 322 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `66901d5` (Session 321's own commit); local `HEAD` was already exactly there
(`git rev-parse HEAD origin/main` -> same SHA both lines), no fast-forward needed. `env | grep -i
THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-321 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-321. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 317-321's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 98 consecutive no-change sessions since it was sent (Sessions 225-322).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~148KB/~2144 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 321 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `572698a` (Session 320's own commit); local `HEAD` was already exactly there
(`git rev-parse HEAD origin/main` -> same SHA both lines), no fast-forward needed. `env | grep -i
THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-320 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-320. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 316-320's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 97 consecutive no-change sessions since it was sent (Sessions 225-321).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~145KB/~2095 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

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

