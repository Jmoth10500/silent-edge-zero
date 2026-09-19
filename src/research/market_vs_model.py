"""
Market favourite vs. Silent Edge top pick — Silent Edge Zero V2 brief,
Phase 2 (Sections 5-7). Pure, read-only analysis over the canonical
dataset from src/research/race_dataset.py — never recomputes a
probability, never touches `prediction`.

**Two distinct favourites, deliberately not conflated (Section 5):**
- The *lock-time market favourite* — lowest `exchange_back` among runners'
  `market.at_lock` snapshot (nearest real snapshot at/after
  `prediction.locked_at`). This is the fair comparison against Silent
  Edge's own locked pick, since both were "knowable" at the same moment.
- The *starting-price (SP) favourite* — lowest `result.starting_price`.
  A genuinely different question ("who did the market end up backing
  most") that must never be silently substituted for the lock-time one.

**Joint favourites are real and handled explicitly** — `determine_favourites`
returns every horse tied at the lowest price, not an arbitrary single
pick. A race with more than one lock-time favourite is not "unresolved"
for the four-way classification (Section 6) — it just means "the market
favourite won" is true if the winner is any one of them.

**Four-way classification (Section 6):** because a race has exactly one
winner (dead heats aside), a race can only ever land in BOTH_CORRECT if
Silent Edge's top pick and (one of) the market favourite(s) are the same
horse and it won — two independently "correct" but different picks is not
possible in a single-winner race. `classify_race_outcome` documents this
directly rather than trying to derive it cleverly. Dead heats and races
with no usable favourite data are flagged (`"UNRESOLVED"`), never forced
into a category the brief says to reconcile exactly against the eligible
count.
"""
from typing import Optional


def determine_favourites(runners: list[dict], price_source: str = "at_lock") -> list[int]:
    """Real horse_id(s) tied for the lowest exchange_back under
    `runner["market"][price_source]` (default 'at_lock'; pass 'latest' or
    'closing' for the other two). Ignores runners with no real price at
    that snapshot rather than guessing. Returns [] if no runner in the
    race has a usable price — never invents a favourite (brief Section 5)."""
    priced = [
        (r["horse"]["horse_id"], r["market"][price_source]["exchange_back"])
        for r in runners
        if r["market"].get(price_source) and r["market"][price_source]["exchange_back"] is not None
    ]
    if not priced:
        return []
    best_price = min(p for _, p in priced)
    return [hid for hid, p in priced if p == best_price]


def determine_sp_favourites(runners: list[dict]) -> list[int]:
    """Real horse_id(s) tied for the lowest official starting_price. []
    if no runner has a real SP recorded (starting_price is only populated
    by the Racing Post cross-check today, not the primary horseracing.net
    source — see src/research/race_dataset.py's module docstring)."""
    priced = [
        (r["horse"]["horse_id"], r["result"]["starting_price"])
        for r in runners if r["result"]["starting_price"] is not None
    ]
    if not priced:
        return []
    best_price = min(p for _, p in priced)
    return [hid for hid, p in priced if p == best_price]


def classify_race_outcome(top_pick_horse_id: Optional[int], favourite_horse_ids: list[int],
                           winner_horse_ids: list[int]) -> dict:
    """Real four-way classification for one race. `winner_horse_ids` is a
    list to accommodate a genuine dead heat (more than one horse sharing
    finishing_position 1) — treated as UNRESOLVED for this classification
    rather than arbitrarily picking one, per the brief's own instruction to
    flag rather than force an impossible-to-uniquely-classify race.

    Returns {"category": "A"|"B"|"C"|"D"|"UNRESOLVED", "reason": str}.
    """
    if not winner_horse_ids:
        return {"category": "UNRESOLVED", "reason": "race not settled / no real winner recorded"}
    if len(winner_horse_ids) > 1:
        return {"category": "UNRESOLVED", "reason": "real dead heat — more than one recorded winner"}
    if top_pick_horse_id is None:
        return {"category": "UNRESOLVED", "reason": "no Silent Edge top pick available"}
    if not favourite_horse_ids:
        return {"category": "UNRESOLVED", "reason": "no usable market favourite data at this snapshot"}

    winner = winner_horse_ids[0]
    se_correct = top_pick_horse_id == winner
    market_correct = winner in favourite_horse_ids

    if se_correct and market_correct:
        return {"category": "A", "reason": "Silent Edge and the market favourite were the same horse, and it won"}
    if se_correct and not market_correct:
        return {"category": "B", "reason": "Silent Edge's top pick won; the market favourite did not"}
    if market_correct and not se_correct:
        return {"category": "C", "reason": "the market favourite won; Silent Edge's top pick did not"}
    return {"category": "D", "reason": "neither Silent Edge's top pick nor the market favourite won"}


def classify_races(races: list[dict], price_source: str = "at_lock") -> list[dict]:
    """Applies classify_race_outcome to every race in `races` (as returned
    by race_dataset.load_race_dataset + attach_market_data), returning one
    result dict per race with race identifying info attached. Races that
    are still pending settlement are still included, classified
    UNRESOLVED — callers filtering to only fully-classified races should
    check `category != "UNRESOLVED"` themselves, since the brief requires
    the eligible-race count and the UNRESOLVED count to be visible
    separately, never silently dropped (Section 6: "all standard category
    totals must reconcile exactly with the eligible race count")."""
    out = []
    for race in races:
        runners = race["runners"]
        favourites = determine_favourites(runners, price_source=price_source)
        winners = [r["horse"]["horse_id"] for r in runners if r["result"]["finishing_position"] == 1]
        result = classify_race_outcome(race.get("top_pick_horse_id"), favourites, winners)
        result.update({
            "race_id": race["race"]["race_id"],
            "date": race["race"]["date"],
            "course": race["race"]["course"],
            "off_time": race["race"]["off_time"],
            "top_pick_horse_id": race.get("top_pick_horse_id"),
            "favourite_horse_ids": favourites,
            "winner_horse_ids": winners,
            "price_source": price_source,
        })
        out.append(result)
    return out


def summarise_classification(classified: list[dict]) -> dict:
    """Real aggregate counts (Section 6/7) — eligible races are every race
    NOT classified UNRESOLVED; totals below reconcile exactly against that
    count, and the UNRESOLVED count/reasons are reported alongside, never
    hidden."""
    eligible = [c for c in classified if c["category"] != "UNRESOLVED"]
    unresolved = [c for c in classified if c["category"] == "UNRESOLVED"]

    counts = {cat: sum(1 for c in eligible if c["category"] == cat) for cat in ("A", "B", "C", "D")}
    n_eligible = len(eligible)

    unresolved_reasons: dict[str, int] = {}
    for c in unresolved:
        unresolved_reasons[c["reason"]] = unresolved_reasons.get(c["reason"], 0) + 1

    se_wins = counts["A"] + counts["B"]
    market_wins = counts["A"] + counts["C"]

    # Model-vs-market AGREEMENT (Silent Edge's top pick IS one of the market
    # favourites) is a pre-race property, entirely independent of who won —
    # deliberately computed from top_pick_horse_id/favourite_horse_ids
    # directly, never inferred from the four-way win/loss categories (the
    # brief explicitly warns these two agreement notions must stay
    # separate; A+D is NOT the agreement count, since D includes races
    # where they agreed on a loser AND races where they picked different
    # losers).
    agree_races = [c for c in eligible if c["top_pick_horse_id"] in c["favourite_horse_ids"]]
    n_agree = len(agree_races)

    return {
        "n_races_total": len(classified),
        "n_eligible": n_eligible,
        "n_unresolved": len(unresolved),
        "unresolved_reasons": unresolved_reasons,
        "four_way": counts,
        "silent_edge_win_rate": round(se_wins / n_eligible, 4) if n_eligible else None,
        "market_favourite_win_rate": round(market_wins / n_eligible, 4) if n_eligible else None,
        "win_rate_difference": round((se_wins - market_wins) / n_eligible, 4) if n_eligible else None,
        "model_market_agreement_rate": round(n_agree / n_eligible, 4) if n_eligible else None,
        "n_agree": n_agree,
    }
