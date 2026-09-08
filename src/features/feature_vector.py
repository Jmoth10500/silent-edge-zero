"""
Combined per-runner feature vector — the actual flat shape a model's input
row will eventually take, wiring together three modules that were each
built and tested standalone:

- src/features/runner_features.py  (Sections 8 + 10: raw + race-relative
  runner features — rating, age, weight, draw, form)
- src/market/movement.py           (Section 16: price movement — opening
  price, current price, price change %, drift/shortening)

Still synthetic-fixture-only (see tests/test_feature_vector.py) — this is
plumbing, not a trained model, and produces no prediction of its own. It
exists so the eventual model has a single, tested function to call for its
input row instead of assembling three modules' outputs by hand every time.

Every rule the underlying modules already enforce carries over unchanged:
a missing input is OMITTED from that feature's keys, never imputed as a
default or zero. A runner absent from `price_history` simply has no
price-derived keys in its vector; that is not the same thing as "flat
price" and must never be treated as such downstream.
"""
from typing import Mapping, Optional, Sequence

from src.features.runner_features import (
    RunnerFeatureInput,
    draw_bias_features,
    form_score,
    relative_official_rating,
    relative_weight,
)
from src.market.movement import (
    PriceObservation,
    current_price,
    movement_classification,
    opening_price,
    price_change_pct,
)


def build_runner_feature_vectors(
    runners: Sequence[RunnerFeatureInput],
    price_history: Optional[Mapping[int, Sequence[PriceObservation]]] = None,
    recency_weighted_form: bool = True,
) -> dict[int, dict]:
    """One flat feature dict per horse_id for every runner in `runners`.

    `price_history` maps horse_id -> that runner's price observations
    (already leakage-filtered by the caller, same contract as
    src/market/movement.py). A horse_id with no entry, or an empty
    sequence, gets no price-derived keys at all.

    Returns {} for an empty `runners` sequence. Every runner in `runners`
    gets an output entry (at minimum {"horse_id": ...}), even one with no
    other known fields — this function never drops a runner, only omits
    individual missing features.
    """
    if not runners:
        return {}

    price_history = price_history or {}
    rating_features = relative_official_rating(runners)
    draw_features = draw_bias_features(runners)
    weight_features = relative_weight(runners)

    out: dict[int, dict] = {}
    for r in runners:
        vec: dict = {"horse_id": r.horse_id}

        if r.age is not None:
            vec["age"] = r.age
        if r.days_since_last_run is not None:
            vec["days_since_last_run"] = r.days_since_last_run

        fs = form_score(r.recent_form, recency_weighted=recency_weighted_form)
        if fs is not None:
            vec["form_score"] = fs

        if r.horse_id in rating_features:
            rf = rating_features[r.horse_id]
            vec["official_rating"] = rf["official_rating"]
            vec["rating_rank"] = rf["rank"]
            vec["rating_percentile"] = rf["percentile"]
            vec["rating_vs_mean"] = rf["rating_vs_mean"]

        if r.horse_id in draw_features:
            df = draw_features[r.horse_id]
            vec["draw"] = df["draw"]
            vec["field_size"] = df["field_size"]
            vec["draw_percentile"] = df["draw_percentile"]

        if r.horse_id in weight_features:
            wf = weight_features[r.horse_id]
            vec["weight_lbs"] = wf["weight_lbs"]
            vec["weight_vs_mean_lbs"] = wf["weight_vs_mean_lbs"]

        observations = price_history.get(r.horse_id, [])
        if observations:
            vec["opening_price"] = opening_price(observations)
            vec["current_price"] = current_price(observations)
            pct = price_change_pct(observations)
            if pct is not None:
                vec["price_change_pct"] = pct
            vec["movement_classification"] = movement_classification(observations)

        out[r.horse_id] = vec
    return out
