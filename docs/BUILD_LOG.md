# Build Log

This file is read by the autonomous continuation routine at the start of every
run — it exists so a fresh session with zero memory of this conversation can
pick up exactly where the last one stopped, without re-deriving anything or
re-doing finished work.

---


**Archive note (added Session 101, 2026-09-20):** Sessions 1-90 (2026-09-08 to
2026-09-19) have been moved verbatim to `docs/BUILD_LOG_ARCHIVE.md` — this file had
grown to ~500KB, past the point Claude Code's own `Read` tool (256KB limit) could
open it in one call. This file now starts at Session 91, which is where the
"stale prompt, repeatedly satisfied, no human reply" situation began being logged in
detail; see the archive for everything before that.

## 2026-09-19 — Session 91 (autonomous overnight, cloud routine)

**75th consecutive session, same stale prompt, no change — sent a renewed push notification this
session (first since Session 50, 41 sessions ago).** `git fetch origin main` then `--unshallow`
(fresh container starts shallow) — no drift (`origin/main` == local `HEAD` == `f0ca80e`, Session
90's commit). Full history now visible: 94 commits, 85 Claude / 9 Jonathan Nuttall.
`git log --author="Jonathan Nuttall" -1` → still `e42411f` (2026-09-08, "RL-007 resolved"), now
**11 days old**, no reply. `env | grep -i THERACINGAPI` → empty (Mac-only credentials; did not
attempt `collect_racecards.py`/`collect_weather.py`, per this session's own prompt correction).
`src/models/*.py` + `racecard_theracingapi.py` line counts unchanged (0/138/361/215/138/116). No
TODO/FIXME/XXX in src/scripts/tests/db. `model1_logistic_baseline.py` docstring re-read directly:
still Phase 6 (per-race multinomial-logit/softmax baseline, synthetic fixtures shaped exactly like
the real racecard schema — `official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style
string — probabilities summing to ~1.0 per race, explicitly labeled not-a-real-prediction in its
own docstring), still satisfies this session's prompt verbatim, still superseded by real work
(Phase 7 gradient-boosting Model 2, RL-006/RL-007's real Kaggle-trained Model 1, which honestly did
not beat the de-vigged market baseline). GitHub checked directly: 0 open issues, 0 open or closed
PRs, no activity of any kind outside this routine's own commits. Full suite re-run
(`db/setup_local_postgres.sh` + `db/init_db.py` (13 tables) + `pip install -r requirements.txt` +
`pytest tests/ -q`) → **177/177 passed**.

**Sent one push notification this session.** Rationale: this schedule's stored prompt has now been
verbatim-satisfied for 75 consecutive sessions with zero human reply for 11 days, and prior
sessions (24, 50) explicitly flagged "approaching fifty or a hundred consecutive stale sessions"
as the threshold for a further notification after the first two (Sessions 19, 24) and the third
(Session 50). We are now 25 sessions past that "fifty" marker with no acknowledgement, so a fourth
notification — plainly stating the schedule is stuck and asking Jonathan to update or pause the
prompt, or to confirm he's aware and is fine leaving it as a standing health-check — is overdue
rather than noise. Did not manufacture busywork or re-touch working code to have something to
report.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new, log one short entry, skip the notification (this session's is fresh), and stop.
Trim/archive of this file (Session 50, now ~6165 lines) still needs a human call.

## 2026-09-19 — Session 92 (autonomous overnight, cloud routine)

**76th consecutive session, same stale prompt, no change — skipped notification per Session 91's
own instruction (its notification is same-day and still fresh).** `git fetch origin main` then
`--unshallow` (fresh container starts shallow) — no drift (`origin/main` == local `HEAD` ==
`42aa37a`, Session 91's commit). `git log --author="Jonathan Nuttall" -1` → still `e42411f`
(2026-09-08, "RL-007 resolved"), still 11 days old, no reply. `env | grep -i THERACINGAPI` → empty
(Mac-only credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this
session's own prompt correction). `src/models/*.py` + `racecard_theracingapi.py` line counts
unchanged (0/138/361/215/138/116). No TODO/FIXME/XXX in `src/`/`scripts/`/`tests/`/`db/`.
`model1_logistic_baseline.py` docstring re-read directly: still Phase 6 (per-race
multinomial-logit/softmax baseline, synthetic fixtures shaped exactly like the real racecard
schema — `official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style string —
probabilities summing to ~1.0 per race, explicitly labeled not-a-real-prediction in its own
docstring), still satisfies this session's prompt verbatim, still superseded by real work (Phase 7
gradient-boosting Model 2, RL-006/RL-007's real Kaggle-trained Model 1, which honestly did not beat
the de-vigged market baseline). GitHub checked directly: 0 open issues, 0 open or closed PRs, no
activity of any kind outside this routine's own commits. Full suite re-run
(`db/setup_local_postgres.sh` + `db/init_db.py` (13 tables) + `pip install -r requirements.txt` +
`pytest tests/ -q`) → **177/177 passed**.

**No push notification this session.** Session 91 sent a renewed one today (2026-09-19, the first
since Session 50) explicitly flagging the schedule as stuck and asking Jonathan to update, pause,
or confirm it as a standing health-check. Nothing has changed in the few hours since — sending a
second one the same day for the identical unresolved condition would be noise, not signal, per
Session 91's own "skip the notification (this session's is fresh)" instruction.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's been a meaningful stretch since Session 91's notification (days, not
hours) with still no reply, a further notification may be warranted — otherwise log one short
entry and stop. Trim/archive of this file (Session 50, now ~6195 lines) still needs a human call.

## 2026-09-19 — Session 93 (autonomous overnight, cloud routine)

**77th consecutive session, same stale prompt, no change — no notification (Session 91's is same-
day, still fresh).** `git fetch origin main` then `--unshallow` (fresh container starts shallow) —
`origin/main` == local `HEAD` == `a4103ba`, Session 92's commit, no drift. `git log
--author="Jonathan" -1` → still `e42411f` (2026-09-08, "RL-007 resolved"), still 11 days old, no
reply. `env | grep -i THERACINGAPI` → empty (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's own prompt correction).
`src/models/*.py` + `racecard_theracingapi.py` line counts unchanged
(0/138/361/215/138/116). `model1_logistic_baseline.py` still satisfies this session's prompt's
Phase 6 ask verbatim (per-race softmax baseline, synthetic fixtures shaped like the real racecard
schema, `official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style string, probabilities
summing to ~1.0, explicitly labeled not-a-real-prediction), still superseded by real work (Phase 7
gradient-boosting Model 2, RL-006/RL-007's real Kaggle-trained Model 1). GitHub checked directly:
0 open issues, 0 open or closed PRs, no activity of any kind outside this routine's own commits.
Full suite re-run (`db/setup_local_postgres.sh` + `db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `pytest tests/ -q`) → **177/177 passed** (note: the standalone
`pytest` shim on PATH resolves to a different interpreter than `python3` in this container and
mis-reports `ModuleNotFoundError: requests` on collection; `python3 -m pytest` runs correctly and
is what future sessions should use if they hit the same false failure).

**No push notification this session.** Session 91 sent one today (2026-09-19) explicitly flagging
the schedule as stuck and asking Jonathan to update, pause, or confirm it as a standing
health-check; nothing has changed in the hours since, so a second same-day notification would be
noise for the identical unresolved condition, per Sessions 91/92's own stated threshold.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's been a meaningful stretch (days, not hours) since Session 91's
notification with still no reply, a further notification may be warranted — otherwise log one
short entry and stop. Trim/archive of this file (Session 50, now ~6220 lines) still needs a human
call.

## 2026-09-19 — Session 94 (autonomous overnight, cloud routine)

**78th consecutive session, same stale prompt, no change — no notification (Session 91's is same-
day, still fresh).** `git fetch origin main` then `--unshallow` (fresh container starts shallow) —
`origin/main` == local `HEAD` == `f471c73`, Session 93's commit, no drift. `git log
--author="Jonathan" -1` → still `e42411f` (2026-09-08, "RL-007 resolved"), no reply. `env | grep -i
THERACINGAPI` → empty (Mac-only credentials; did not attempt `collect_racecards.py`/
`collect_weather.py`, per this session's own prompt correction). `src/models/*.py` +
`racecard_theracingapi.py` line counts unchanged (0/138/361/215/138/116).
`model1_logistic_baseline.py` still satisfies this session's prompt's Phase 6 ask verbatim
(per-race softmax baseline, synthetic fixtures shaped like the real racecard schema,
`official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style string, probabilities summing
to ~1.0, explicitly labeled not-a-real-prediction), still superseded by real work (Phase 7
gradient-boosting Model 2, RL-006/RL-007's real Kaggle-trained Model 1). GitHub checked directly
via `mcp__github__` tools: 0 open issues, 0 pull requests in any state, no activity of any kind
outside this routine's own commits. Full suite re-run (`db/setup_local_postgres.sh` +
`python3 db/init_db.py` (13 tables) + `pip install -r requirements.txt` +
`python3 -m pytest tests/ -q`) → **177/177 passed**.

**No push notification this session.** Same-day as Session 91's notification (2026-09-19), and
nothing has changed since — a second same-day notification for the identical unresolved condition
would be noise, per Sessions 91-93's own stated threshold ("days, not hours").

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's been a meaningful stretch (days, not hours) since Session 91's
notification with still no reply, a further notification may be warranted — otherwise log one
short entry and stop. Trim/archive of this file (Session 50, now ~6250 lines) still needs a human
call.

## 2026-09-19 — Session 95 (autonomous overnight, cloud routine)

**79th consecutive session, same stale prompt, no change — no notification (Session 91's is same-
day, still fresh).** `git fetch origin main` then `--unshallow` (fresh container starts shallow) —
`origin/main` == local `HEAD` == `505ae41`, Session 94's commit, no drift. `git log --all
--author="Jonathan" -1` → still `e42411f` (2026-09-08, "RL-007 resolved"), now 11 days old, no
reply. `env | grep -i THERACINGAPI` → empty (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's own prompt correction).
`src/models/*.py` + `racecard_theracingapi.py` line counts unchanged (0/138/361/215/138/116).
`model1_logistic_baseline.py` docstring re-read directly: still Phase 6 (per-race
multinomial-logit/softmax baseline, synthetic fixtures shaped exactly like the real racecard
schema — `official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style string —
probabilities summing to ~1.0 per race, explicitly labeled not-a-real-prediction), still satisfies
this session's prompt verbatim, still superseded by real work (Phase 7 gradient-boosting Model 2,
RL-006/RL-007's real Kaggle-trained Model 1, which honestly did not beat the de-vigged market
baseline). GitHub checked directly via `mcp__github__` tools: 0 open issues, 0 pull requests in
any state, no activity of any kind outside this routine's own commits. Full suite re-run
(`db/setup_local_postgres.sh` + `python3 db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) → **177/177 passed**.

**No push notification this session.** Same calendar day as Session 91's notification
(2026-09-19), and nothing has changed since — a second same-day notification for the identical
unresolved condition would be noise, per Sessions 91-94's own stated threshold ("days, not
hours").

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's been a meaningful stretch (days, not hours) since Session 91's
notification with still no reply, a further notification may be warranted — otherwise log one
short entry and stop. Trim/archive of this file (Session 50, now ~6355 lines) still needs a human
call.

## 2026-09-19 — Session 96 (autonomous overnight, cloud routine)

**80th consecutive session, same stale prompt, no change — no notification (Session 91's is same-
day, still fresh).** `git fetch origin main` then `--unshallow` (fresh container starts shallow) —
`origin/main` == local `HEAD` == `efe2202`, Session 95's commit, no drift. `git log --all
--author="Jonathan" -1` → still `e42411f` (2026-09-08, "RL-007 resolved"), now 11 days old, no
reply. `env | grep -i THERACINGAPI` → empty (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's own prompt correction).
`src/models/*.py` + `racecard_theracingapi.py` line counts unchanged (0/138/361/215/138/116).
`model1_logistic_baseline.py` still satisfies this session's prompt's Phase 6 ask verbatim
(per-race multinomial-logit/softmax baseline, synthetic fixtures shaped exactly like the real
racecard schema — `official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style string —
probabilities summing to ~1.0 per race, explicitly labeled not-a-real-prediction in its own
docstring), still superseded by real work (Phase 7 gradient-boosting Model 2, RL-006/RL-007's real
Kaggle-trained Model 1, which honestly did not beat the de-vigged market baseline). GitHub checked
directly via `mcp__github__` tools: 0 open issues, 0 pull requests in any state, no activity of any
kind outside this routine's own commits. Full suite re-run (`db/setup_local_postgres.sh` +
`python3 db/init_db.py` (13 tables) + `pip install -r requirements.txt` +
`python3 -m pytest tests/ -q`) → **177/177 passed**.

**No push notification this session.** Same calendar day as Session 91's notification
(2026-09-19), and nothing has changed since — a second same-day notification for the identical
unresolved condition would be noise, per Sessions 91-95's own stated threshold ("days, not
hours").

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's been a meaningful stretch (days, not hours) since Session 91's
notification with still no reply, a further notification may be warranted — otherwise log one
short entry and stop. Trim/archive of this file (Session 50, now ~6385 lines) still needs a human
call.

## 2026-09-19 — Session 97 (autonomous overnight, cloud routine)

**81st consecutive session, same stale prompt, no change — no notification (Session 91's is same-
day, still fresh).** `git fetch origin main` then `--unshallow` (fresh container starts shallow) —
`origin/main` == local `HEAD` == `7162d3c`, Session 96's commit, no drift. `git log --all
--author="Jonathan"` (unshallowed) → still `e42411f` (2026-09-08, "RL-007 resolved"), still 11
days old, no reply. `env | grep -i THERACINGAPI` → empty (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's own prompt correction).
`src/models/*.py` + `racecard_theracingapi.py` line counts unchanged
(0/138/361/215/138/116). `model1_logistic_baseline.py` docstring re-read directly: still Phase 6
(per-race multinomial-logit/softmax baseline, synthetic fixtures shaped exactly like the real
racecard schema — `official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style string —
probabilities summing to ~1.0 per race, explicitly labeled not-a-real-prediction), still satisfies
this session's prompt verbatim, still superseded by real work (Phase 7 gradient-boosting Model 2,
RL-006/RL-007's real Kaggle-trained Model 1, which honestly did not beat the de-vigged market
baseline). GitHub checked directly via `mcp__github__` tools: 0 open issues, 0 pull requests in
any state, no activity of any kind outside this routine's own commits. Full suite re-run
(`db/setup_local_postgres.sh` + `python3 db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) → **177/177 passed**.

**No push notification this session.** Same calendar day as Session 91's notification
(2026-09-19), and nothing has changed since — a second same-day notification for the identical
unresolved condition would be noise, per Sessions 91-96's own stated threshold ("days, not
hours").

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's been a meaningful stretch (days, not hours) since Session 91's
notification with still no reply, a further notification may be warranted — otherwise log one
short entry and stop. Trim/archive of this file (Session 50, now ~6397 lines) still needs a human
call.

## 2026-09-19 — Session 98 (autonomous overnight, cloud routine)

**82nd consecutive session, same stale prompt, no change — no notification (Session 91's is same-
day, still fresh).** `git fetch origin main` — `origin/main` == local `HEAD` == `754bfab`,
Session 97's commit, no drift. `git log --all --author="Jonathan" -1` → still `e42411f`
(2026-09-08, "RL-007 resolved"), now 11 days old, no reply. `env | grep -i THERACINGAPI` → empty
(Mac-only credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this
session's own prompt correction). `src/models/*.py` + `racecard_theracingapi.py` line counts
unchanged (0/138/361/215/138/116). `model1_logistic_baseline.py` still satisfies this session's
prompt's Phase 6 ask verbatim (per-race multinomial-logit/softmax baseline, synthetic fixtures
shaped exactly like the real racecard schema — `official_rating`/`draw` as ints, `recent_form` as
a `"1582F3"`-style string — probabilities summing to ~1.0 per race, explicitly labeled
not-a-real-prediction in its own docstring), still superseded by real work (Phase 7
gradient-boosting Model 2, RL-006/RL-007's real Kaggle-trained Model 1, which honestly did not beat
the de-vigged market baseline). GitHub checked directly via `mcp__github__` tools: 0 open issues,
0 pull requests in any state, no activity of any kind outside this routine's own commits. Full
suite re-run (`db/setup_local_postgres.sh` + `python3 db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) → **177/177 passed**.

**No push notification this session.** Same calendar day as Session 91's notification
(2026-09-19), and nothing has changed since — a second same-day notification for the identical
unresolved condition would be noise, per Sessions 91-97's own stated threshold ("days, not
hours").

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's been a meaningful stretch (days, not hours) since Session 91's
notification with still no reply, a further notification may be warranted — otherwise log one
short entry and stop. Trim/archive of this file (Session 50, now ~6428 lines) still needs a human
call.

## 2026-09-20 — Session 99 (autonomous overnight, cloud routine)

**83rd consecutive session, same stale prompt, no change — no notification (only ~1 day since
Session 91's, not yet the "days, not hours" threshold that session itself set).** Fresh container,
shallow clone as usual; `git fetch --unshallow origin` then `git fetch origin main` — no drift
(`origin/main` == local `HEAD` == `cf995e2`, Session 98's commit). `git log --all --author=
"Jonathan" -1` → still `e42411f` (2026-09-08, "RL-007 resolved"), now **12 days old**, no reply.
`env | grep -i THERACINGAPI` → empty (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's own prompt correction).
`src/models/*.py` + `racecard_theracingapi.py` line counts unchanged (0/138/361/215/138/116).
`model1_logistic_baseline.py` module docstring re-read directly: still describes the original
Phase 6 synthetic-fixture baseline (per-race multinomial-logit/softmax, `official_rating`/`draw`
as ints, `recent_form` as a `"1582F3"`-style string, probabilities summing to ~1.0 per race) as
historical record, now layered under the 2026-09-08 update describing the real Kaggle-fitted
Model 1 (RL-006/RL-007, did not beat the de-vigged market baseline) — still satisfies this
session's prompt verbatim, still superseded by that real work. GitHub checked directly via
`mcp__github__` tools: 0 open issues, 0 pull requests in any state, no activity of any kind
outside this routine's own commits. Full suite re-run (`db/setup_local_postgres.sh` +
`python3 db/init_db.py` (13 tables) + `pip install -r requirements.txt` +
`python3 -m pytest tests/ -q`) → **177/177 passed**. No TODO/FIXME/XXX in src/scripts/tests/db.

**New observation this session, worth flagging even without a notification:** this file
(`docs/BUILD_LOG.md`) is now 6466 lines / ~490KB — large enough that Claude Code's own `Read` tool
refuses to read it in one call (256KB limit) and this session had to fall back to `tail`/`grep`/
`sed` to inspect it. This is a step change from "long file" to "file some of this routine's own
tooling can no longer open directly," and it will only get worse at ~30-40 lines/session if the
prompt stays stale. Flagging concretely so whoever next reads this (human or Claude) has the
number, not just the recurring "needs a human call" note.

**No push notification this session.** Only about a day has passed since Session 91's
(2026-09-19), which already stated the situation plainly (schedule stuck, 11 days no reply at the
time, asked Jonathan to update/pause the prompt or confirm he's fine leaving it as a standing
health-check). Nothing has changed since that would change the ask. Re-notifying this soon for the
same unresolved, already-clearly-stated condition would be noise, not help.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's now been several days since Session 91's notification with still no
reply, a further notification is warranted — the BUILD_LOG.md size point above is worth including
in it, not a separate trigger on its own. Otherwise log one short entry and stop. Trim/archive of
this file still needs a human call; it is no longer just a style preference (see the size note
above).

## 2026-09-20 — Session 100 (autonomous overnight, cloud routine)

**84th consecutive session, same stale prompt, no change — no notification (only ~1 day since
Session 91's, not yet "several days").** Fresh container, shallow clone; `git fetch origin main`
then `--unshallow` — no drift (`origin/main` == local `HEAD` == `acbfeb8`, Session 99's commit).
`git log --all --author="Jonathan" -1` → still `e42411f` (2026-09-08, "RL-007 resolved"), now
**12 days old**, no reply. `env | grep -i THERACINGAPI` → empty (Mac-only credentials; did not
attempt `collect_racecards.py`/`collect_weather.py`, per this session's own prompt correction).
`src/models/*.py` + `racecard_theracingapi.py` line counts unchanged (0/138/361/215/138/116). No
TODO/FIXME/XXX in src/scripts/tests/db. Phase 6's `model1_logistic_baseline.py` (per-race
multinomial-logit/softmax baseline over synthetic fixtures shaped exactly like the real racecard
schema — `official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style string,
probabilities summing to ~1.0 per race, explicitly labeled not-a-real-prediction) still satisfies
this session's prompt verbatim, still superseded by real work (Phase 7 gradient-boosting Model 2,
RL-006/RL-007's real Kaggle-trained Model 1, which did not beat the de-vigged market baseline).
GitHub checked directly via `mcp__github__` tools: 0 open issues, 0 pull requests in any state, no
activity of any kind outside this routine's own commits. Full suite re-run
(`db/setup_local_postgres.sh` + `python3 db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) → **177/177 passed**.

**No push notification this session.** Only about a day has passed since Session 91's
(2026-09-19), which already stated the situation plainly and asked Jonathan to update/pause the
prompt or confirm he's fine leaving it as a standing health-check. Nothing has changed since that
would change the ask, and re-notifying this soon would be noise, not help.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's now been several days since Session 91's notification with still no
reply, a further notification is warranted. Otherwise log one short entry and stop. Trim/archive of
this file (now ~6540 lines / ~500KB, past the point Claude Code's own `Read` tool can open it in
one call) still needs a human call.

## 2026-09-20 — Session 101 (autonomous overnight, cloud routine)

**85th consecutive session, same stale prompt, no change.** Fresh container, shallow clone;
`git fetch origin main` then `--unshallow` — no drift (`origin/main` == local `HEAD` ==
`ebd1045`, Session 100's commit). `git log --all --author="Jonathan" -1` → still `e42411f`
(2026-09-08, "RL-007 resolved"), now **12 days old**, no reply. `env | grep -i THERACINGAPI` →
empty (Mac-only credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per
this session's own prompt correction). `src/models/*.py` + `racecard_theracingapi.py` line
counts unchanged (0/138/361/215/138/116). `model1_logistic_baseline.py` docstring re-read
directly: still Phase 6 (per-race multinomial-logit/softmax baseline, synthetic fixtures shaped
exactly like the real racecard schema — `official_rating`/`draw` as ints, `recent_form` as a
`"1582F3"`-style string — probabilities summing to ~1.0 per race, explicitly labeled
not-a-real-prediction), still satisfies this session's prompt verbatim, still superseded by real
work (Phase 7 gradient-boosting Model 2, RL-006/RL-007's real Kaggle-trained Model 1, which did
not beat the de-vigged market baseline). GitHub checked directly via `mcp__github__` tools: 0
open issues, 0 pull requests in any state, no activity of any kind outside this routine's own
commits. Full suite re-run (`db/setup_local_postgres.sh` + `python3 db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) → **177/177 passed**.

**Acted on the BUILD_LOG.md size problem Sessions 99-100 flagged, instead of deferring it
again.** The file had reached ~500KB / ~6540 lines — Claude Code's own `Read` tool (256KB limit)
could no longer open it in one call, forcing every session into `tail`/`grep`/`sed` just to read
its own state, and Session 99 explicitly called this "a step change ... it will only get worse."
Sessions 50 through 100 all deferred trimming as "needs a human call," but with no human reply in
12 days and the situation now actively degrading each session's ability to do its own job, this
reads as a reversible, low-risk maintenance fix rather than a decision that needs Jonathan's
input: nothing was deleted or rewritten. Sessions 1-90 (2026-09-08 to 2026-09-19, ~6175 lines)
were moved verbatim to the new `docs/BUILD_LOG_ARCHIVE.md`; this file now starts at Session 91
(the session that first sent a renewed stuck-schedule notification) and is ~28KB, well under the
Read limit again. All 101 session headers accounted for across both files (verified by count).
Full original text preserved in git history regardless.

**No push notification this session.** Only ~1 day has passed since Session 91's notification
(2026-09-19), which already stated the stuck-schedule situation plainly and asked Jonathan to
update/pause the prompt or confirm he's fine leaving it as a standing health-check. Nothing about
the underlying condition has changed — same prompt, same 12-day silence, same already-satisfied
Phase 6 ask. The BUILD_LOG.md archiving this session did is routine maintenance that keeps the
routine itself functional, not a new development worth a separate interruption; it's recorded
here for whoever reads this next, human or Claude, rather than pushed to Jonathan's phone.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's now been several days since Session 91's notification with still no
reply, a further notification is warranted. Otherwise log one short entry and stop. The
BUILD_LOG.md size problem is resolved for now (28KB); if this file grows back toward the 256KB
Read limit over many more stale sessions, repeat the same archive-and-pointer approach rather than
letting it become unreadable again.

## 2026-09-20 — Session 102 (autonomous overnight, cloud routine)

**86th consecutive session, same stale prompt, no change — no notification (~1 day since Session
91's, not yet "several days").** `git fetch origin main` then `--unshallow` — no drift
(`origin/main` == local `HEAD` == `30cc4bb`, Session 101's commit). `git log --all
--author="Jonathan" -1` → still `e42411f` (2026-09-08, "RL-007 resolved"), now **12 days old**, no
reply. `env | grep -i THERACINGAPI` → empty (Mac-only credentials; did not attempt
`collect_racecards.py`/`collect_weather.py`, per this session's own prompt correction).
`src/models/*.py` + `racecard_theracingapi.py` line counts unchanged (0/138/361/215/138/116). No
TODO/FIXME/XXX in src/scripts/tests/db. Phase 6's `model1_logistic_baseline.py` (per-race
multinomial-logit/softmax baseline over synthetic fixtures shaped exactly like the real racecard
schema — `official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style string,
probabilities summing to ~1.0 per race, explicitly labeled not-a-real-prediction) still satisfies
this session's prompt verbatim, still superseded by real work (Phase 7 gradient-boosting Model 2,
RL-006/RL-007's real Kaggle-trained Model 1, which did not beat the de-vigged market baseline).
GitHub checked directly via `mcp__github__` tools: 0 open issues, 0 pull requests in any state, no
activity of any kind outside this routine's own commits. Full suite re-run
(`db/setup_local_postgres.sh` + `python3 db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) → **177/177 passed**.
BUILD_LOG.md still well under the 256KB Read limit (this file only, per Session 101's archive).

**No push notification this session.** Only ~1 day since Session 91's (2026-09-19), which already
stated the stuck-schedule situation plainly and asked Jonathan to update/pause the prompt or
confirm he's fine leaving it as a standing health-check. Nothing about the underlying condition
has changed — same prompt, same 12-day silence, same already-satisfied Phase 6 ask. Sending again
this soon would be noise, not signal.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's now been several days (not ~1) since Session 91's notification with
still no reply, a further notification is warranted. Otherwise log one short entry and stop.

## 2026-09-20 — Session 103 (autonomous overnight, cloud routine)

**87th consecutive session, same stale prompt, no change — no notification (still ~1 day since
Session 91's, not yet "several days").** Fresh checks, no drift: `origin/main` == `HEAD` ==
`7705cf4` (Session 102's commit). `git log --all --author="Jonathan" -1` → still `e42411f`
(2026-09-08), now **12 days old**, no reply. `env | grep -i THERACINGAPI` → empty (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`). `src/models/` unchanged
(model0/1/2 + sweep, same as every prior session). No TODO/FIXME/XXX in src/scripts/tests/db.
Phase 6's `model1_logistic_baseline.py` still satisfies this session's prompt verbatim, still
superseded by real Phase 7 work. GitHub checked via `mcp__github__`: 0 open issues, 0 PRs in any
state, no non-routine activity. Full suite re-run (`db/setup_local_postgres.sh` +
`python3 db/init_db.py` + `python3 -m pytest tests/ -q`) → **177/177 passed**.

**No push notification.** Session 91's (2026-09-19) already stated the stuck-schedule situation
plainly; nothing has changed since. Re-notifying after ~1 day would be noise.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key; Kaggle-loaded Postgres dataset;
Racing API results tier (not pursuing); racecard surface/going field verification.

**Next session:** same checks. Notify only once it's been several days (not ~1) since Session 91's
notification with still no reply. Otherwise log one short entry and stop.

## 2026-09-20 — Session 104 (autonomous overnight, cloud routine)

**88th consecutive session, same stale prompt, no change — no notification (~1.5 days since
Session 91's, not yet "several days").** Fresh container, shallow clone; `git fetch origin main`
then `--unshallow` — no drift (`origin/main` == local `HEAD` == `4786477`, Session 103's commit).
`git log --all --author="Jonathan" -1` → still `e42411f` (2026-09-08, "RL-007 resolved"), now
**12 days old**, no reply. `env | grep -i THERACINGAPI` → empty (Mac-only credentials; did not
attempt `collect_racecards.py`/`collect_weather.py`, per this session's own prompt correction).
`src/models/*.py` line counts unchanged (0/138/361/215/138). No TODO/FIXME/XXX in
src/scripts/tests/db. `model1_logistic_baseline.py` docstring re-read directly: still Phase 6
(per-race multinomial-logit/softmax baseline over synthetic fixtures shaped exactly like the real
racecard schema — `official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style string,
probabilities summing to ~1.0 per race, explicitly labeled not-a-real-prediction), still satisfies
this session's prompt verbatim, still superseded by real work (Phase 7 gradient-boosting Model 2,
RL-006/RL-007's real Kaggle-trained Model 1, which did not beat the de-vigged market baseline).
GitHub checked directly via `mcp__github__` tools: 0 open issues, 0 pull requests in any state, no
activity of any kind outside this routine's own commits. Full suite re-run
(`db/setup_local_postgres.sh` + `python3 db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) → **177/177 passed**.

**No push notification this session.** Session 91's (2026-09-19 00:57) already stated the
stuck-schedule situation plainly and asked Jonathan to update/pause the prompt or confirm he's
fine leaving it as a standing health-check. Only ~1.5 days have passed since then, well short of
the "several days" bar set by Sessions 92-103 for re-notifying. Nothing about the underlying
condition has changed.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks. If Jonathan has replied or the prompt has changed, act on that. If
still nothing new and it's now been several days since Session 91's notification (2026-09-19
00:57) with still no reply, a further notification is warranted. Otherwise log one short entry
and stop.

## 2026-09-20 — Session 105 (autonomous overnight, cloud routine)

**89th consecutive session, same stale prompt, no change — no notification (~1 day since Session
91's, not yet "several days").** `env | grep -i THERACINGAPI` → empty (Mac-only credentials; did
not attempt `collect_racecards.py`/`collect_weather.py`, per this session's own prompt
correction). `git log --all --author="Jonathan" -1` → still `e42411f` (2026-09-08, "RL-007
resolved"), now **12 days old**, no reply.

**Found and fixed a real (if minor) repo-hygiene issue, not just a re-verification.** Local `main`
was detached-HEAD/stale at `95672d8` (Session 62!) while `origin/main` was at `c310233` (Session
104) — prior sessions had been committing and pushing from a detached HEAD state without ever
updating the local `main` branch ref itself. This had no effect on GitHub (every push landed on
`origin/main` correctly, verified by `git log` on `origin/main` matching each session's stated
commit), but left local `git branch -vv` / `git status` lying about being "up to date" before the
fetch resolved it. Fixed with `git checkout main && git fetch origin main && git merge --ff-only
origin/main` (fast-forward only, no rewrite). Future sessions: run `git checkout main` (not stay
detached) before comparing against `origin/main`, so this doesn't recur silently.

`src/models/*.py` line counts unchanged (0/138/361/215/138). No TODO/FIXME/XXX in
src/scripts/tests/db. `model1_logistic_baseline.py` module docstring re-read directly and
confirmed by hand (not just line-count diff): still Phase 6 (per-race multinomial-logit/softmax
baseline, synthetic fixtures shaped exactly like the real racecard schema — `official_rating`/
`draw` as ints, `recent_form` as a `"1582F3"`-style string, probabilities summing to ~1.0 per
race, explicitly labeled not-a-real-prediction in its own docstring) layered under the real,
walk-forward-validated Kaggle-fitted Model 1 (RL-006/RL-007, 2026-09-08, did not beat the
de-vigged market baseline on any of 18 folds) — still satisfies this session's prompt verbatim,
still superseded by that real work. GitHub checked directly via `mcp__github__` tools: 0 open
issues, 0 pull requests in any state, no activity of any kind outside this routine's own commits.
Full suite re-run (`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) → **177/177 passed**.
BUILD_LOG.md at 523 lines / well under the 256KB `Read` limit (Session 101's archive holding).

**No push notification this session.** Only ~1 day has passed since Session 91's (2026-09-19
00:57), which already stated the stuck-schedule situation plainly and asked Jonathan to
update/pause the prompt or confirm he's fine leaving it as a standing health-check. Nothing about
the underlying condition has changed — same prompt, same 12-day silence, same already-satisfied
Phase 6 ask. The local-branch-ref fix above is routine hygiene, not a development worth
interrupting Jonathan for; noted here for whoever reads this next.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks, and use `git checkout main` (not detached HEAD) before comparing
against `origin/main`, per the fix above. If Jonathan has replied or the prompt has changed, act
on that. If still nothing new and it's now been several days since Session 91's notification
(2026-09-19 00:57) with still no reply, a further notification is warranted. Otherwise log one
short entry and stop.

## 2026-09-20 — Session 106 (autonomous overnight, cloud routine)

**90th consecutive session, same stale prompt, no change — no notification (~1 day since Session
91's, not yet "several days").** Fresh checks throughout. `git checkout main` (per Session 105's
fix) then `git fetch origin main` — local `main` was 43 commits behind `origin/main` (this
container started from an older snapshot than Session 105's own checkout); fast-forwarded cleanly
to `d73adec` (Session 105's commit, includes its BUILD_LOG.md archive). Repo was shallow;
`git fetch --unshallow origin` run before trusting `git log --author` results, per the lesson
already in this file. `git log --all --author="Jonathan" -1` → still `e42411f` (2026-09-08,
"RL-007 resolved"), now **12 days old**, no reply. `env | grep -i THERACINGAPI` → empty (Mac-only
credentials; did not attempt `collect_racecards.py`/`collect_weather.py`, per this session's own
prompt correction). `src/models/*.py` line counts unchanged (0/138/361/215/138) and
`racecard_theracingapi.py` unchanged (116 lines). No TODO/FIXME/XXX in src/scripts/tests/db.
`model1_logistic_baseline.py` module docstring re-read directly and confirmed by hand: still
describes the original Phase 6 synthetic-fixture baseline (per-race multinomial-logit/softmax,
`official_rating`/`draw` as ints, `recent_form` as a `"1582F3"`-style undelimited string,
probabilities summing to ~1.0 per race, explicitly labeled not-a-real-prediction) as historical
record, layered under the 2026-09-08 update describing the real, walk-forward-validated
Kaggle-fitted Model 1 (RL-006/RL-007, ~487k real runner predictions across 18 chronological folds,
did not beat the de-vigged market baseline on any fold) — still satisfies this session's prompt's
Phase 6 ask verbatim, still superseded by that real work and by Phase 7's gradient-boosting
Model 2. GitHub checked directly via `mcp__github__` tools: 0 open issues, 0 pull requests in any
state, no activity of any kind outside this routine's own commits. Full suite re-run
(`bash db/setup_local_postgres.sh` + `python3 db/init_db.py` (13 tables) +
`pip install -r requirements.txt` + `python3 -m pytest tests/ -q`) → **177/177 passed**.
BUILD_LOG.md at ~572 lines, well under the 256KB `Read` limit (Session 101's archive holding).

**No push notification this session.** Only ~1 day has passed since Session 91's (2026-09-19
00:57), which already stated the stuck-schedule situation plainly and asked Jonathan to
update/pause the prompt or confirm he's fine leaving it as a standing health-check. Nothing about
the underlying condition has changed — same prompt, same 12-day silence, same already-satisfied
Phase 6 ask, no GitHub activity, no code drift beyond routine session commits. Sending again this
soon would be noise, not signal, per Sessions 92-105's own consistently applied "several days, not
hours/~1 day" threshold.

**Still blocked (unchanged, Mac-only):** Betfair Delayed App Key (Phase 4, untested live);
Kaggle-loaded 558K-row Postgres dataset; Racing API results tier (not pursuing); racecard
surface/going field verification (needs a live API call).

**Next session:** same checks, `git checkout main` before comparing against `origin/main`, and
`git fetch --unshallow origin` before trusting any `--author` log query (this session's container
started shallow and behind, same as most). If Jonathan has replied or the prompt has changed, act
on that. If still nothing new and it's now been several days since Session 91's notification
(2026-09-19 00:57) with still no reply, a further notification is warranted. Otherwise log one
short entry and stop.
