"""
Trainer/jockey real strike-rate features — RL-010.

**Why this exists:** a gap analysis (2026-09-09, Jonathan asked directly
how to close the gap to the market's real 33.4% hit rate) found real,
substantial, completely unused signal sitting in the data already:
checking trainer win rates directly against the real 558K-row historical
dataset showed a genuine spread from 2.4% (Max Young) to 28.6% (Charlie
Appleby) over 300+ real races each — not noise, a real, large signal
neither model was using. Jockey win rates showed the same pattern (Paul
Townend 35.2% down to well under 10% for low-volume riders). Every
feature built so far (rating, draw, form, weight, going) describes the
HORSE; this is the first to describe the CONNECTIONS.

**Leakage discipline, same as draw_bias_history.py and going_affinity.py:**
the caller builds `build_trainer_table()`/`build_jockey_table()` from
ONLY strictly-earlier real outcomes (a walk-forward split's training
races) — see `scripts/train_model1.py::build_split_connections_tables`.

**Design choice, flagged honestly (same as every other edge feature
here):** the edge is centered on the RACE's own field mean (among
runners with a known trainer/jockey rate), not asserted as "higher rate
is always better" up front — the fitted weight's sign decides that, same
discipline as every other feature in this repo. Some of a top trainer's
real win rate is already explained by getting the better-rated horses
(so this could be partially redundant with `rating_edge`) — that's a
real, open question this feature's real backtest result will answer, not
assumed here.

A trainer/jockey needs at least `min_runs` real prior runs to get a table
entry — below that, `trainer_edge`/`jockey_edge` return 0.0 ("no
evidence"), never a rate computed from too few races to mean anything.
"""
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

DEFAULT_MIN_RUNS = 20


@dataclass(frozen=True)
class HistoricalConnectionOutcome:
    """One real, strictly-past completed run — the shape needed to build
    a trainer or jockey win-rate table. `entity_id` is whichever of
    trainer_id/jockey_id this outcome is being aggregated by (the caller
    builds one list per entity type)."""

    entity_id: int
    won: bool


def build_win_rate_table(
    outcomes: list[HistoricalConnectionOutcome], min_runs: int = DEFAULT_MIN_RUNS,
) -> dict[int, float]:
    """Real win rate per entity_id (trainer_id or jockey_id, depending on
    what the caller passed in), from real strictly-past runs only. An
    entity with fewer than `min_runs` real runs is left out of the table
    entirely — never guessed from too little evidence."""
    runs: dict[int, int] = defaultdict(int)
    wins: dict[int, int] = defaultdict(int)
    for o in outcomes:
        runs[o.entity_id] += 1
        if o.won:
            wins[o.entity_id] += 1
    return {eid: wins[eid] / runs[eid] for eid in runs if runs[eid] >= min_runs}


def connections_edges(
    runners: list[tuple[int, Optional[int], Optional[int]]],
    trainer_table: dict[int, float],
    jockey_table: dict[int, float],
) -> dict[int, dict[str, float]]:
    """`runners` is a list of (horse_id, trainer_id, jockey_id) for one
    real race. Returns {horse_id: {"trainer_edge": ..., "jockey_edge": ...}},
    each centered on the race's own field mean among runners with a KNOWN
    real rate (same "no evidence either way" convention as every other
    feature here — 0.0 for a runner whose trainer/jockey has no table
    entry, not folded into "average"; and every runner still gets both
    keys, always, same as build_race_features' other edges)."""
    trainer_rates = {hid: trainer_table[tid] for hid, tid, _ in runners if tid in trainer_table}
    jockey_rates = {hid: jockey_table[jid] for hid, _, jid in runners if jid in jockey_table}

    trainer_mean = sum(trainer_rates.values()) / len(trainer_rates) if trainer_rates else None
    jockey_mean = sum(jockey_rates.values()) / len(jockey_rates) if jockey_rates else None

    out: dict[int, dict[str, float]] = {}
    for hid, _tid, _jid in runners:
        t_edge = (trainer_rates[hid] - trainer_mean) if (hid in trainer_rates and trainer_mean is not None) else 0.0
        j_edge = (jockey_rates[hid] - jockey_mean) if (hid in jockey_rates and jockey_mean is not None) else 0.0
        out[hid] = {"trainer_edge": t_edge, "jockey_edge": j_edge}
    return out
