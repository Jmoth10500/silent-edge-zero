> **Merge note 2026-09-30:** this file is the cloud routine's log (Sessions 1-184). The local interactive-session history (real-data model results, Smarkets/results pipeline, Sept 2026 fixes) is in `docs/BUILD_LOG_LOCAL.md`; both are current.

# Build Log

This file is read by the autonomous continuation routine at the start of every
run — it exists so a fresh session with zero memory of this conversation can
pick up exactly where the last one stopped, without re-deriving anything or
re-doing finished work.

---

## 2026-10-09 — Session 317 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `4365486` (Session 316's own commit); local `HEAD` was already exactly there
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
139/185-316 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-316. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 312-316's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 93 consecutive no-change sessions since it was sent (Sessions 225-317).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~133KB/~1899 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 316 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `a97636f` (Session 315's own commit); local `HEAD` was already exactly there
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
139/185-315 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-315. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 312-315's own re-verify/archiving commits, authored by `Claude <noreply@anthropic.com>`
— no human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting
prices; stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days.
`docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry still the
2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 92 consecutive no-change sessions since it was sent (Sessions 225-316).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~130KB/~1850 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 315 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `b9b1299` (Session 314's own commit); local `HEAD` was already exactly there
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
139/185-314 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-314. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 311-314's own re-verify/archiving commits, authored by `Claude <noreply@anthropic.com>`
— no human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting
prices; stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days.
`docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry still the
2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 91 consecutive no-change sessions since it was sent (Sessions 225-315).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~127KB/~1801 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 314 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `0e54cd0` (Session 313's own commit); local `HEAD` was already exactly there
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
139/185-313 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-313. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 310-313's own re-verify/archiving commits, authored by `Claude <noreply@anthropic.com>`
— no human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting
prices; stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days.
`docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry still the
2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 90 consecutive no-change sessions since it was sent (Sessions 225-314).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~124KB/~1753 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 313 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `a469251` (Session 312's own commit); local `HEAD` was already exactly there
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
139/185-312 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-312. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 309-312's own re-verify/archiving commits, authored by `Claude <noreply@anthropic.com>`
— no human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting
prices; stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days.
`docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry still the
2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 89 consecutive no-change sessions since it was sent (Sessions 225-313).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~121KB/~1704 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 312 (autonomous overnight, cloud routine)

**Housekeeping (archiving) plus re-verification, no code change — no notification.** `git fetch
origin main` (fresh) showed `origin/main` at `82763cf` (Session 311's own commit); local `HEAD`
was already exactly there, no fast-forward needed. `env | grep -i THERACINGAPI` -> empty,
confirmed directly (Mac-only credentials; did not attempt `collect_racecards.py`/
`collect_weather.py`, per this session's prompt correction, same as every prior cloud session).

`docs/BUILD_LOG.md` had grown back to ~222KB/3098 lines, past the ~230KB watch threshold flagged
by Sessions 309-311. Archived Sessions 251-280 (2026-10-09, all automated "no change"
re-verification entries) verbatim into `docs/BUILD_LOG_ARCHIVE.md`, same pattern as Session
265/285's prior archiving — kept Session 224 itself in the live log (the anchor every later
session's "not re-sending the backlog-exhausted notification" decision references by number),
alongside Sessions 281 onward. Live log now back down to ~115KB/1605 lines. Pushed that
housekeeping as its own commit (`1252e10`) before this entry.

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-311 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-311. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` (before
this session's own archiving commit) were all Sessions 308-311's own re-verify commits, authored
by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real `c4e42ee`
("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered by
`c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 88 consecutive no-change sessions since it was sent (Sessions 225-312).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~118KB/~1656 lines before this entry — comfortably under the ~230KB archive
threshold again, no archiving needed for a good while.

---

## 2026-10-09 — Session 311 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `32fa677` (Session 310's own commit); local `HEAD` was already exactly there
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
139/185-310 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-310. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 306-310's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 87 consecutive no-change sessions since it was sent (Sessions 225-311).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked). Check
`docs/BUILD_LOG.md`'s size: it's ~219KB/~3108 lines before this entry, very close to the ~230KB
archive threshold — archive the oldest entries (keeping Session 224 as the anchor, per
Session 265/285's pattern) once it crosses, likely next session or the one after.

---

## 2026-10-09 — Session 310 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `1c0de75` (Session 309's own commit); local `HEAD` was already exactly there
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
139/185-309 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-309. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 305-309's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 86 consecutive no-change sessions since it was sent (Sessions 225-310).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked). Check
`docs/BUILD_LOG.md`'s size: it's ~215KB/~3055 lines before this entry, close to the ~230KB archive
threshold — archive the oldest entries (keeping Session 224 as the anchor, per Session 265/285's
pattern) once it actually crosses.

---

## 2026-10-09 — Session 309 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `a652df1` (Session 308's own commit); local `HEAD` was already exactly there
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
139/185-308 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-308. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 304-308's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 85 consecutive no-change sessions since it was sent (Sessions 225-309).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked). Check
`docs/BUILD_LOG.md`'s size: it's ~212KB/~3003 lines before this entry, close to the ~230KB archive
threshold — archive the oldest entries (keeping Session 224 as the anchor, per Session 265/285's
pattern) once it actually crosses.

---

## 2026-10-09 — Session 308 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `75e9e8f` (Session 307's own commit); local `HEAD` was already exactly there
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
139/185-307 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-307. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 303-307's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 84 consecutive no-change sessions since it was sent (Sessions 225-308).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~209KB/~2951 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed yet (expect to cross it within a handful of sessions).

---

## 2026-10-09 — Session 307 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `0bbf8a0` (Session 306's own commit); local `HEAD` was already exactly there
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
139/185-306 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-306. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 302-306's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 83 consecutive no-change sessions since it was sent (Sessions 225-307).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~190KB/~2899 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 306 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `9903f01` (Session 305's own commit); local `HEAD` was already exactly there
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
139/185-305 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-305. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 301-305's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 82 consecutive no-change sessions since it was sent (Sessions 225-306).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~187KB/~2847 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 305 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `de7aae5` (Session 304's own commit); local `HEAD` was already exactly there
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
139/185-304 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-304. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 300-304's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 81 consecutive no-change sessions since it was sent (Sessions 225-305).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~184KB/~2795 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 304 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `a38832d` (Session 303's own commit); local `HEAD` was already exactly there
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
139/185-303 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-303. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 299-303's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 80 consecutive no-change sessions since it was sent (Sessions 225-304).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~181KB/~2744 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 303 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `4a2d18e` (Session 302's own commit); local `HEAD` was already exactly there
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
139/185-302 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-302. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 298-302's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 79 consecutive no-change sessions since it was sent (Sessions 225-303).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~178KB/~2693 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 302 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `06280e1` (Session 301's own commit); local `HEAD` was already exactly there
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
139/185-301 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-301. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 297-301's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 78 consecutive no-change sessions since it was sent (Sessions 225-302).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~175KB/~2642 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 301 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `7e6ea46` (Session 300's own commit); local `HEAD` was already exactly there
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
139/185-300 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-300. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 296-300's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 77 consecutive no-change sessions since it was sent (Sessions 225-301).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~172KB/~2591 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 300 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `0ab86bf` (Session 299's own commit); local `HEAD` was already exactly there
(`git rev-parse HEAD origin/main` -> same SHA both lines), no fast-forward needed. `env | grep -i
THERACINGAPI` -> empty, confirmed directly (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's prompt correction, same as every
prior cloud session).

This is the 300th automated session of this routine. This session's prompt again asks to "start
Phase 6" (statistical/logistic baseline over synthetic fixtures shaped like the real racecard
schema, per-race softmax summing to ~1.0, clearly labeled not-a-real-prediction).
`src/models/model1_logistic_baseline.py` is present and unchanged; re-read its module docstring
directly (not from memory): it still satisfies that ask verbatim — `official_rating`/`draw` as
int, `recent_form` as an undelimited string like `"1582F3"`, per-race softmax summing to 1.0 by
construction, clearly labeled not a real prediction — as Sessions 139/185-299 have all already
found, and remains superseded in practice by the real Kaggle-fitted Model 1 (RL-006/RL-007) and
Model 2 gradient boosting, both already in `src/models/`. No new code written; a duplicate second
baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-299. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 295-299's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 76 consecutive no-change sessions since it was sent (Sessions 225-300). Reaching
the 300-session mark is itself not new information (it is the same situation described at 224, 250,
and 285 — a stale cron prompt with nothing left to do until Jonathan either replies or supplies his
own machine's racecard/weather data), so it is not treated as a fresh trigger for a notification.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~169KB/~2539 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 299 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `61b9552` (Session 298's own commit); local `HEAD` was already exactly there
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
139/185-298 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-298. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 294-298's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 75 consecutive no-change sessions since it was sent (Sessions 225-299).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~166KB/~2490 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 298 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `da603b6` (Session 297's own commit); local `HEAD` was already exactly there
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
139/185-297 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-297. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 293-297's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 74 consecutive no-change sessions since it was sent (Sessions 225-298).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~163KB/~2441 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 297 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `7472586` (Session 296's own commit); local `HEAD` was already exactly there
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
139/185-296 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-296. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 292-296's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 73 consecutive no-change sessions since it was sent (Sessions 225-297).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~160KB/~2392 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 296 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `9461f1b` (Session 295's own commit); local `HEAD` was already exactly there
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
139/185-295 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-295. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 291-295's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 72 consecutive no-change sessions since it was sent (Sessions 225-296).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~157KB/~2343 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 295 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `7113930` (Session 294's own commit); local `HEAD` was already exactly there
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
139/185-294 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-294. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 290-294's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 71 consecutive no-change sessions since it was sent (Sessions 225-295).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~154KB/~2294 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 294 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `f965ac3` (Session 293's own commit); local `HEAD` was already exactly there
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
139/185-293 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-293. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 289-293's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 70 consecutive no-change sessions since it was sent (Sessions 225-294).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~151KB/~2245 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 293 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `d17255a` (Session 292's own commit); local `HEAD` was already exactly there
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
139/185-292 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-292. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 288-292's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 69 consecutive no-change sessions since it was sent (Sessions 225-293).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~148KB/~2196 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 292 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `fa8e9b9` (Session 291's own commit); local `HEAD` was already exactly there
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
139/185-291 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-291. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 287-291's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 68 consecutive no-change sessions since it was sent (Sessions 225-292).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~146KB/~2147 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 291 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `a94e823` (Session 290's own commit); local `HEAD` was already exactly there
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
139/185-290 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-290. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 286-290's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 67 consecutive no-change sessions since it was sent (Sessions 225-291).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~143KB/~2098 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 290 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `7c6ce39` (Session 289's own commit); local `HEAD` was already exactly there
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
139/185-289 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-289. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 285-289's own re-verify/archiving commits, authored by `Claude <noreply@anthropic.com>`
— no human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting
prices; stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days.
`docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry still the
2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 66 consecutive no-change sessions since it was sent (Sessions 225-290).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~140KB/~2049 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 289 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `99cf6dd` (Session 288's own commit); local `HEAD` was already exactly there
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
139/185-288 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-288. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 285-288's own re-verify/archiving commits, authored by `Claude <noreply@anthropic.com>`
— no human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting
prices; stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days.
`docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry still the
2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 65 consecutive no-change sessions since it was sent (Sessions 225-289).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~138KB/~2000 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 288 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `c13e0ad` (Session 287's own commit); local `HEAD` was already exactly there
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
139/185-287 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-287. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 284-287's own re-verify/archiving commits, authored by `Claude <noreply@anthropic.com>`
— no human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting
prices; stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days.
`docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry still the
2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 64 consecutive no-change sessions since it was sent (Sessions 225-288).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~136KB/~1951 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 287 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `e1ce389` (Session 286's own commit); local `HEAD` was already exactly there
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
139/185-286 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-286. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 283-286's own re-verify/archiving commits, authored by `Claude <noreply@anthropic.com>`
— no human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting
prices; stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days.
`docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry still the
2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 63 consecutive no-change sessions since it was sent (Sessions 225-287).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~133KB/~1902 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 286 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `42e57fd` (Session 285's own commit); local `HEAD` was already exactly there
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
139/185-285 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-285. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 282-285's own re-verify/archiving commits, authored by `Claude <noreply@anthropic.com>`
— no human commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting
prices; stop results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days.
`docs/BUILD_LOG_LOCAL.md` tail re-read directly (unchanged): most recent entry still the
2026-09-30 Smarkets/results fix already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 62 consecutive no-change sessions since it was sent (Sessions 225-286).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~130KB/~1853 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 285 (autonomous overnight, cloud routine)

**Housekeeping (archiving) plus re-verification, no code change — no notification.** `git fetch
origin main` (fresh) showed `origin/main` at `50eb3c7` (Session 284's own commit); local `HEAD`
was already exactly there, no fast-forward needed. `env | grep -i THERACINGAPI` -> empty,
confirmed directly (Mac-only credentials; did not attempt `collect_racecards.py`/
`collect_weather.py`, per this session's prompt correction, same as every prior cloud session).

`docs/BUILD_LOG.md` had grown back to ~221KB/3074 lines, past the ~230KB watch threshold. Archived
Sessions 225-250 (2026-10-05 to 2026-10-09) verbatim into `docs/BUILD_LOG_ARCHIVE.md`, same pattern
as Session 265's prior archiving — kept Session 224 itself in the live log (not archived) since
it's the anchor every later session's "not re-sending the backlog-exhausted notification" decision
references by number, alongside Sessions 251 onward. Live log now back down to ~126KB/1761 lines.
Pushed that housekeeping as its own commit (`99e89ca`) before this entry.

This session's prompt again asks to "start Phase 6" (statistical/logistic baseline over synthetic
fixtures shaped like the real racecard schema, per-race softmax summing to ~1.0, clearly labeled
not-a-real-prediction). `src/models/model1_logistic_baseline.py` is present and unchanged; re-read
its module docstring directly (not from memory): it still satisfies that ask verbatim —
`official_rating`/`draw` as int, `recent_form` as an undelimited string like `"1582F3"`, per-race
softmax summing to 1.0 by construction, clearly labeled not a real prediction — as Sessions
139/185-284 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-284. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` (before
this session's own archiving commit) were all Sessions 280-284's own re-verify commits, authored
by `Claude <noreply@anthropic.com>` — no human commit newer than Jonathan's real `c4e42ee`
("Recover 25-30 Sep P&L using starting prices; stop results upsert wiping SP",
2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md` tail re-read directly
(unchanged): most recent entry still the 2026-09-30 Smarkets/results fix already covered by
`c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 61 consecutive no-change sessions since it was sent (Sessions 225-285).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~128KB/~1803 lines before this entry — comfortably under the ~230KB archive
threshold again, no archiving needed for a good while.

---

## 2026-10-09 — Session 284 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `3ffa615` (Session 283's own commit); local `HEAD` was already exactly there
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
139/185-283 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-283. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 279-283's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 60 consecutive no-change sessions since it was sent (Sessions 225-284).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~209KB/~3015 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 283 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `3017960` (Session 282's own commit); local `HEAD` was already exactly there
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
139/185-282 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-282. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 278-282's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 59 consecutive no-change sessions since it was sent (Sessions 225-283).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~206KB/~2969 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 282 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `1eefcfe` (Session 281's own commit); local `HEAD` was already exactly there
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
139/185-281 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-281. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 277-281's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 58 consecutive no-change sessions since it was sent (Sessions 225-282).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~203KB/~2923 lines before this entry — comfortably under the ~230KB archive
threshold, no archiving needed for a good while.

---

## 2026-10-09 — Session 281 (autonomous overnight, cloud routine)

**Re-verification only, no change — no notification.** `git fetch origin main` (fresh) showed
`origin/main` at `0405928` (Session 280's own commit); local `HEAD` was already exactly there
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
139/185-280 have all already found, and remains superseded in practice by the real Kaggle-fitted
Model 1 (RL-006/RL-007) and Model 2 gradient boosting, both already in `src/models/`. No new code
written; a duplicate second baseline would not be additive.

Full suite re-run fresh (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (15 tables) +
`python3 -m pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) -> **576/576 passed**,
same count as Sessions 185-280. `grep -rc "TODO\|FIXME\|XXX" src/ scripts/ tests/ db/` -> sum 0.
GitHub checked via a subagent using `mcp__github__` tools, confirmed directly against the live API:
0 issues (any state, ever), 0 pull requests (any state, ever). Last 5 commits on `main` are all
Sessions 276-280's own re-verify commits, authored by `Claude <noreply@anthropic.com>` — no human
commit newer than Jonathan's real `c4e42ee` ("Recover 25-30 Sep P&L using starting prices; stop
results upsert wiping SP", 2026-09-30T22:29:42+01:00), now ~9 days. `docs/BUILD_LOG_LOCAL.md`
tail re-read directly (unchanged): most recent entry still the 2026-09-30 Smarkets/results fix
already covered by `c4e42ee`.

**No push notification this session.** Nothing has changed since Session 224's "backlog exhausted,
consider pausing or coarsening the schedule" notification: same test count, same 0 issues/PRs, no
reply from Jonathan. Per Session 224's own request, not repeating that message again absent new
information — now 57 consecutive no-change sessions since it was sent (Sessions 225-281).

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live); Racing
API results tier (not pursuing, per `BUILD_LOG_LOCAL.md`). Racecard/weather collection remains
Mac-only — the cloud routine environment has no THERACINGAPI credentials.

**Next session:** `git fetch origin main` (fresh) and compare `git rev-parse HEAD origin/main`
before doing anything else. Read `docs/BUILD_LOG_LOCAL.md`'s tail for any new local activity. If
Jonathan has replied to Session 224's notification, act on that explicitly. Otherwise keep not
re-sending the "nothing to do" notification — only notify again if something actually changes (a
reply from Jonathan, a new GitHub issue/PR, a test failure, or new work becoming unblocked).
`docs/BUILD_LOG.md` is ~200KB/~2877 lines before this entry — comfortably under the ~230KB archive
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

