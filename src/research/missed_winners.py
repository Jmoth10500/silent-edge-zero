"""
"Who did we both miss?" — Silent Edge Zero V2 brief, Phase 4, Section 8.
Read-only, pure functions. Descriptive investigation ONLY, per the brief's
own explicit warning: "looking exclusively at missed-winner races creates
a selected dataset... use that subset for descriptive investigation only.
Test whether discovered characteristics actually outperform expectations
across ALL eligible races." This module never claims a finding is
validated — it produces the descriptive detail plus points every summary
back at src/research/ranking_matrix.py's full-population expected-vs-
actual figures for the SAME rank cells, so a reader never mistakes "this
happened a lot in the missed-winner subset" for "this rank combination is
underpriced across all races" without checking the full population too.

A "missed winner" race is exactly four-way category D from
src/research/market_vs_model.py (both Silent Edge's top pick and the
market favourite lost) — reusing that classification rather than
re-deriving a second, possibly inconsistent definition of "both wrong".
"""
from src.research.market_vs_model import classify_races
from src.research.ranking_matrix import build_rank_observations, rank_by_market


def find_missed_winner_races(races: list[dict], price_source: str = "at_lock") -> list[dict]:
    """Real detail record for every eligible category-D race: the actual
    winner's Silent Edge rank/probability, market rank/probability
    (de-vigged where possible), starting price, field size, race type,
    trainer, jockey, going, distance — every field `None` rather than
    guessed if genuinely unavailable (e.g. SP is not populated by the
    primary results source, see race_dataset.py's module docstring)."""
    from src.analysis.edge_metrics import normalized_market_probabilities

    classified = classify_races(races, price_source=price_source)
    d_race_ids = {c["race_id"] for c in classified if c["category"] == "D"}

    out = []
    for race in races:
        if race["race"]["race_id"] not in d_race_ids:
            continue
        runners = race["runners"]
        winner_runners = [r for r in runners if r["result"]["finishing_position"] == 1]
        if len(winner_runners) != 1:
            continue  # a real dead heat inside an otherwise-D race — skip rather than guess which one "the" winner is
        winner = winner_runners[0]

        market_ranks = rank_by_market(runners, price_source=price_source)
        odds_by_horse = {
            r["horse"]["horse_id"]: r["market"][price_source]["exchange_back"]
            for r in runners
            if r["market"].get(price_source) and r["market"][price_source]["exchange_back"] is not None
        }
        market_probs = normalized_market_probabilities(odds_by_horse)

        winner_horse_id = winner["horse"]["horse_id"]
        out.append({
            "race_id": race["race"]["race_id"],
            "date": race["race"]["date"],
            "course": race["race"]["course"],
            "race_type": race["race"].get("race_type"),
            "distance_yards": race["race"].get("distance_yards"),
            "going": race["race"].get("going"),
            "field_size_declared": race["race"].get("field_size_declared"),
            "winner_horse_id": winner_horse_id,
            "winner_horse_name": winner["horse"].get("name"),
            "winner_trainer": winner["horse"].get("trainer"),
            "winner_jockey": winner["horse"].get("jockey"),
            "winner_se_rank": winner["silent_edge"].get("model_rank"),
            "winner_market_rank": market_ranks.get(winner_horse_id),
            "winner_se_probability": winner["silent_edge"]["model_probability"],
            "winner_market_probability": market_probs.get(winner_horse_id),
            "winner_probability_difference": (
                winner["silent_edge"]["model_probability"] - market_probs[winner_horse_id]
                if market_probs.get(winner_horse_id) is not None else None
            ),
            "winner_starting_price": winner["result"]["starting_price"],
        })
    return out


def summarise_missed_winner_rank_combinations(missed_races: list[dict]) -> dict:
    """Real counts of how often the missed winner came from each
    (se_rank, market_rank) combination — descriptive only. Every entry is
    paired with a note pointing at ranking_matrix's full-population figure
    for the same cell, since a raw count here says nothing about whether
    that cell is actually mispriced across all races (brief's own warning,
    module docstring)."""
    from collections import Counter

    combo_counts = Counter(
        (r["winner_se_rank"], r["winner_market_rank"]) for r in missed_races
        if r["winner_se_rank"] is not None and r["winner_market_rank"] is not None
    )
    n_total = len(missed_races)
    out = {}
    for (se_rank, market_rank), n in combo_counts.most_common():
        out[f"se_rank={se_rank},market_rank={market_rank}"] = {
            "se_rank": se_rank,
            "market_rank": market_rank,
            "n_missed_winners_from_this_combo": n,
            "share_of_all_missed_winners": round(n / n_total, 4) if n_total else None,
            "note": "descriptive only — cross-check against the full-population expected/actual "
                    "figure for this rank combination (src/research/ranking_matrix.py) before "
                    "treating this as a real, exploitable pattern",
        }
    return out


def cross_check_against_full_population(missed_summary: dict, races: list[dict], price_source: str = "at_lock",
                                          max_rank: int = 6) -> dict:
    """For every rank combination that shows up in the missed-winner
    descriptive summary, attach the REAL full-population cell from
    ranking_matrix (all races, not just the missed-winner subset) — this
    is the actual test the brief requires ("test whether discovered
    characteristics actually outperform expectations across ALL eligible
    races"), not a second independent computation that could drift out of
    sync with it."""
    from src.research.ranking_matrix import aggregate_rank_matrix

    full_observations = build_rank_observations(races, price_source=price_source)
    full_matrix = aggregate_rank_matrix(full_observations, max_rank=max_rank)

    def bucket(rank: int) -> str:
        return str(rank) if rank < max_rank else f"{max_rank}+"

    out = {}
    for key, entry in missed_summary.items():
        se_bucket = bucket(entry["se_rank"])
        mkt_bucket = bucket(entry["market_rank"])
        full_key = f"se_rank={se_bucket},market_rank={mkt_bucket}"
        out[key] = {**entry, "full_population_cell": full_matrix.get(full_key)}
    return out


def missed_winner_probability_bands(missed_races: list[dict], band_width: float = 0.05) -> dict:
    """Real grouping of missed-winner races (category D — see
    find_missed_winner_races) by the actual winner's ORIGINAL locked
    Silent Edge probability — brief Section 7, "What probability did SEN
    give the actual winner?". Purely descriptive, per this module's own
    docstring: never compared against expectation here (that comparison
    lives in the full-population probability-band chart,
    src/research/probability_bands.py, which uses ALL eligible runners,
    not just missed winners — the two must never be conflated, per the
    brief's own repeated warning against drawing conclusions from a
    selected sample alone).

    `band_width` supports the requested 5-point/10-point toggle (0.05 or
    0.10). Bands with zero real observations are included with n=0 —
    never omitted, so "no missed winners in this band" is visible as a
    real zero, not a gap a reader might mistake for missing data.

    **Real, honest population note (found live 2026-09-20, Jonathan's own
    audit):** `n_winners` here counts every real missed winner regardless
    of whether the winning horse itself had a market price — a winner can
    lack its own price even when the race overall had enough OTHER priced
    runners to be de-vig-able. `probability_band_analysis`'s ALL-RUNNERS
    population additionally requires the SPECIFIC runner to be priced.
    This means `n_winners` is NOT a strict subset of that population's
    actual-win count for the same band — comparing the two bare numbers
    directly is a real, previously undisclosed trap. `n_winners_priced`
    (a real subset of the ALL-RUNNERS population, since it applies the
    SAME per-runner pricing requirement) is provided specifically to make
    a valid, disclosed comparison possible; `n_winners_unpriced` is the
    named, counted gap, never silently absorbed into the total."""
    def band_key(p: float) -> str:
        lo = min(int(p / band_width) * band_width, 1 - band_width)
        hi = lo + band_width
        return f"{lo:.0%}-{hi:.0%}"

    # Real, evenly-spaced, non-overlapping band boundaries covering 0-100%.
    n_bands = int(round(1.0 / band_width))
    all_keys = [band_key(i * band_width) for i in range(n_bands)]

    grouped: dict[str, list[dict]] = {k: [] for k in all_keys}
    for race in missed_races:
        p = race["winner_se_probability"]
        grouped.setdefault(band_key(p), []).append(race)

    total_winners = len(missed_races)
    out = {}
    for key in all_keys:
        races = grouped.get(key, [])
        n = len(races)
        priced = [r for r in races if r["winner_market_probability"] is not None]
        market_probs = [r["winner_market_probability"] for r in priced]
        out[key] = {
            "band": key,
            "n_winners": n,
            "n_winners_priced": len(priced),
            "n_winners_unpriced": n - len(priced),
            "share_of_all_missed_winners": round(n / total_winners, 4) if total_winners else None,
            "avg_se_probability": round(sum(r["winner_se_probability"] for r in races) / n, 4) if n else None,
            "avg_market_probability": round(sum(market_probs) / len(market_probs), 4) if market_probs else None,
            "n_races": n,  # one winner per race here (dead heats already excluded upstream)
            "races": races,
        }
    return out
