"""
Silent Edge Zero — Edge Metrics (Stage 1 of the "model vs market" upgrade,
2026-09-11, per Jonathan's real spec).

**Core reframing:** this project's live pipeline has always answered
"which horse is our model most confident in" — these are the pure,
reusable functions behind the different, more important question:
"where does our model disagree with the real market price enough that
it might mean something." Every function here is pure (no DB, no I/O),
real, and independently testable — never a hard-coded number.

**Why these are computed at DISPLAY time, not stored on `prediction`:**
`prediction` already has dormant `market_probability`/`fair_odds`/
`absolute_edge`/`expected_value` columns from an earlier planning phase,
left NULL by `predict_todays_races.py`'s own real, honest design — market
odds usually aren't available (or aren't final) at the moment a
prediction locks, and once locked, a row can never be updated (the DB's
own `trg_prevent_locked_prediction_update` trigger rejects it — see
db/schema.sql). Baking a point-in-time market read into an immutable row
would either be wrong (guessed) or would freeze a value that goes stale
the moment the market moves. The correct, real answer — same pattern
already used for the odds chip in generate_dashboard.py — is to keep the
model's own probability/ranking immutable (the actual prediction, never
touched) and recompute its relationship to the market fresh, every time,
against whatever the latest real market_snapshot says. This also means
Live Value numbers are always current, not a lock-time fossil.
"""
from typing import Optional


def model_fair_odds(model_probability: float) -> Optional[float]:
    """Real decimal fair odds implied by the model's own probability:
    1 / model_probability. None for a non-positive probability (never a
    divide-by-zero guess)."""
    if model_probability is None or model_probability <= 0:
        return None
    return 1.0 / model_probability


def raw_market_implied_probability(market_odds: Optional[float]) -> Optional[float]:
    """Real raw implied probability from one runner's own decimal odds:
    1 / odds. Includes the exchange's own overround/margin — NOT
    normalised against the rest of the field (see
    `normalized_market_probabilities` for that). None when no real price
    exists — never guessed."""
    if market_odds is None or market_odds <= 0:
        return None
    return 1.0 / market_odds


def normalized_market_probabilities(odds_by_runner: dict) -> dict:
    """Real de-vigged market probabilities: each priced runner's raw
    1/odds, renormalised so every PRICED runner's share sums to 1.0 —
    the real, standard way to strip a bookmaker/exchange's own overround
    out of raw prices. Runners with no real price are excluded entirely
    (never assigned a guessed share) — a real, honest field with fewer
    than 2 priced runners returns {} rather than a misleading single
    number, since a single quote can't be meaningfully de-vigged against
    itself."""
    priced = {h: 1.0 / o for h, o in odds_by_runner.items() if o and o > 0}
    if len(priced) < 2:
        return {}
    total = sum(priced.values())
    return {h: v / total for h, v in priced.items()}


def probability_edge(model_probability: float, normalized_market_probability: Optional[float]) -> Optional[float]:
    """Real probability-edge in percentage points (as a 0-1 fraction,
    e.g. 0.104 = +10.4pts): model_probability - normalized_market_probability.
    None when there's no real normalised market probability to compare
    against — an edge cannot be computed from nothing."""
    if normalized_market_probability is None:
        return None
    return model_probability - normalized_market_probability


def price_advantage(market_odds: Optional[float], fair_odds: Optional[float]) -> Optional[float]:
    """Real price advantage: how much better the available market price
    is than the model's own fair price, as a fraction (e.g. 0.89 = +89%).
    market_odds / fair_odds - 1. None if either real price is missing."""
    if market_odds is None or fair_odds is None or fair_odds <= 0:
        return None
    return market_odds / fair_odds - 1.0


def expected_value(model_probability: float, market_odds: Optional[float],
                    commission: float = 0.0) -> dict:
    """Real expected value of a theoretical £1 back bet at `market_odds`,
    using the model's own probability as the real win chance:
    EV = model_probability * market_odds - 1.

    `commission` (0.0-1.0, e.g. 0.02 for Smarkets' real 2% standard rate)
    is NEVER assumed — it defaults to 0.0 (no commission) and must be
    explicitly passed. Commission is only real on a WINNING bet's real
    profit (not on stake return or a loss), matching how a real exchange
    actually charges it: net_profit_if_win = (market_odds - 1) * (1 - commission).

    Returns {"gross_ev": ..., "net_ev": ..., "commission": ...} — gross
    and net are identical when commission is 0.0. None values throughout
    when market_odds is missing — never guessed."""
    if market_odds is None or market_odds <= 0:
        return {"gross_ev": None, "net_ev": None, "commission": commission}
    if not (0.0 <= commission < 1.0):
        raise ValueError(f"commission must be in [0.0, 1.0), got {commission}")

    gross_profit_if_win = market_odds - 1.0
    gross_ev = model_probability * gross_profit_if_win - (1.0 - model_probability) * 1.0

    net_profit_if_win = gross_profit_if_win * (1.0 - commission)
    net_ev = model_probability * net_profit_if_win - (1.0 - model_probability) * 1.0

    return {"gross_ev": gross_ev, "net_ev": net_ev, "commission": commission}


def model_agreement_label(prob_a: Optional[float], prob_b: Optional[float],
                           strong_threshold: float = 0.03, moderate_threshold: float = 0.08) -> Optional[str]:
    """Real classification of how closely two models' probabilities agree
    for the same runner, by absolute difference:
    <= strong_threshold -> "Strong Agreement"
    <= moderate_threshold -> "Moderate Agreement"
    otherwise -> "Disagreement"
    None when either real probability is missing. Thresholds are real
    parameters, not hard-coded inside the function — callers (and,
    eventually, a settings layer) choose them explicitly."""
    if prob_a is None or prob_b is None:
        return None
    diff = abs(prob_a - prob_b)
    if diff <= strong_threshold:
        return "Strong Agreement"
    if diff <= moderate_threshold:
        return "Moderate Agreement"
    return "Disagreement"
