"""
Silent Edge rank vs. market rank matrix — Silent Edge Zero V2 brief,
Phase 4, Section 9. Read-only, pure functions. This is the shared
statistical backbone Section 8 (missed-winner research) is required to
use rather than counting missed winners in isolation — the brief is
explicit: "do not count winners alone... for every ranking combination
show number of qualifying runners, actual winners, observed win rate,
expected winners" computed by SUMMING individual pre-race probabilities,
never a runner-count times an arbitrary band midpoint.

**Rank definitions:** Silent Edge rank is already computed in
`src/research/race_dataset.py::load_race_dataset` (dense ranking by
`model_probability` descending, ties genuinely impossible since
probabilities are continuous floats from the model). Market rank here
uses the same dense/competition ranking by `exchange_back` ascending at a
chosen snapshot — ties ARE real and possible here (joint favourites), so
two runners can share market rank 1, with the next runner then getting
rank 3, not 2 (standard "competition ranking", the same convention sports
league tables use) — never silently broken by an arbitrary tie-break.

**Never invents an expected count:** "expected wins" for a matrix cell is
the real sum of the individual runners' own probabilities in that cell —
never `n_runners * cell_midpoint_probability`, which the brief explicitly
forbids.
"""
from typing import Optional

from scripts.generate_eod_report import VOID_RESULT_CODES


def rank_by_market(runners: list[dict], price_source: str = "at_lock") -> dict[int, Optional[int]]:
    """Real competition-ranking (ties share a rank, next rank skips) of
    every runner with a usable price at `price_source`; a runner with no
    real price at that snapshot gets None, never a guessed rank."""
    priced = [
        (r["horse"]["horse_id"], r["market"][price_source]["exchange_back"])
        for r in runners
        if r["market"].get(price_source) and r["market"][price_source]["exchange_back"] is not None
    ]
    ranks: dict[int, Optional[int]] = {r["horse"]["horse_id"]: None for r in runners}
    if not priced:
        return ranks
    sorted_prices = sorted(priced, key=lambda hp: hp[1])
    rank = 1
    prev_price = None
    for i, (horse_id, price) in enumerate(sorted_prices):
        if prev_price is not None and price != prev_price:
            rank = i + 1
        ranks[horse_id] = rank
        prev_price = price
    return ranks


def _runner_outcome_known(result: dict) -> Optional[int]:
    """Same real exclusion rule as src/research/brier_live.py::_runner_outcome
    — duplicated as a tiny pure function rather than imported, to keep this
    module's only real dependency (VOID_RESULT_CODES) explicit and minimal."""
    if result["finishing_position"] == 1:
        return 1
    if result["finishing_position"] is not None:
        return 0
    if result["result_note"] is None:
        return None
    if result["result_note"] in VOID_RESULT_CODES:
        return None
    return 0


def build_rank_observations(races: list[dict], price_source: str = "at_lock") -> list[dict]:
    """One dict per runner with a known Silent Edge rank, a known market
    rank, and a known outcome — the full eligible population the matrix is
    built from (every runner, not just missed-winner races). Also carries
    a real de-vigged `market_probability` (None when the race couldn't be
    de-vigged — fewer than 2 real priced runners, same rule as
    src/research/brier_live.py), so the matrix can report BOTH model- and
    market-expected wins per cell without a second pass over the DB."""
    from src.analysis.edge_metrics import normalized_market_probabilities

    observations = []
    for race in races:
        market_ranks = rank_by_market(race["runners"], price_source=price_source)
        odds_by_horse = {
            r["horse"]["horse_id"]: r["market"][price_source]["exchange_back"]
            for r in race["runners"]
            if r["market"].get(price_source) and r["market"][price_source]["exchange_back"] is not None
        }
        market_probs = normalized_market_probabilities(odds_by_horse)  # {} if < 2 priced runners

        for r in race["runners"]:
            se_rank = r["silent_edge"].get("model_rank")
            market_rank = market_ranks.get(r["horse"]["horse_id"])
            outcome = _runner_outcome_known(r["result"])
            if se_rank is None or market_rank is None or outcome is None:
                continue
            observations.append({
                "race_id": race["race"]["race_id"],
                "horse_id": r["horse"]["horse_id"],
                "se_rank": se_rank,
                "market_rank": market_rank,
                "se_probability": r["silent_edge"]["model_probability"],
                "market_probability": market_probs.get(r["horse"]["horse_id"]),  # None if not de-vig-able
                "outcome": outcome,
            })
    return observations


def aggregate_rank_matrix(observations: list[dict], max_rank: int = 6) -> dict:
    """Real per-cell (se_rank, market_rank) aggregation. Ranks beyond
    `max_rank` are pooled into a real `f"{max_rank}+"` bucket per axis so
    the matrix stays a manageable, real size regardless of field size —
    this is a display/aggregation grouping, not a fabricated rank.

    Each cell: n (qualifying runners), actual_wins, actual_win_rate,
    expected_wins_model (real sum of se_probability), diff_model
    (actual_wins - expected_wins_model). Market-probability expectation is
    added by the caller when de-vigged market probabilities are available
    (see missed_winners.py / the report script) — this function alone only
    has ranks and Silent Edge's own probability, per its real inputs."""
    def bucket(rank: int) -> str:
        return str(rank) if rank < max_rank else f"{max_rank}+"

    cells: dict[tuple[str, str], dict] = {}
    for obs in observations:
        key = (bucket(obs["se_rank"]), bucket(obs["market_rank"]))
        cell = cells.setdefault(key, {
            "n": 0, "actual_wins": 0, "expected_wins_model": 0.0,
            "expected_wins_market": 0.0, "n_with_market_probability": 0, "actual_wins_priced": 0,
        })
        cell["n"] += 1
        cell["actual_wins"] += obs["outcome"]
        cell["expected_wins_model"] += obs["se_probability"]
        if obs["market_probability"] is not None:
            cell["expected_wins_market"] += obs["market_probability"]
            cell["n_with_market_probability"] += 1
            cell["actual_wins_priced"] += obs["outcome"]

    out = {}
    for (se_bucket, mkt_bucket), cell in cells.items():
        n = cell["n"]
        actual = cell["actual_wins"]
        expected_model = cell["expected_wins_model"]
        has_market = cell["n_with_market_probability"] > 0
        out[f"se_rank={se_bucket},market_rank={mkt_bucket}"] = {
            "se_rank": se_bucket,
            "market_rank": mkt_bucket,
            "n": n,
            "actual_wins": actual,
            "actual_win_rate": round(actual / n, 4) if n else None,
            "expected_wins_model": round(expected_model, 2),
            "diff_actual_minus_expected_model": round(actual - expected_model, 2),
            # market expectation only meaningful over the subset of this
            # cell's runners that actually had a de-vig-able price — n_priced
            # is shown so a partial-coverage cell is never mistaken for full
            "expected_wins_market": round(cell["expected_wins_market"], 2) if has_market else None,
            "diff_actual_minus_expected_market": (
                round(cell["actual_wins_priced"] - cell["expected_wins_market"], 2) if has_market else None
            ),
            "n_with_market_probability": cell["n_with_market_probability"],
            "small_sample": n < 20,
        }
    return out
