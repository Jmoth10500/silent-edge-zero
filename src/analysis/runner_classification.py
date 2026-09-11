"""
Silent Edge Zero — Runner Value Classification (Stage 2 of the model-vs-
market upgrade, 2026-09-11).

Turns Stage 1's real per-runner edge/EV numbers (src/analysis/
edge_metrics.py) into an honest status. MOST LIKELY WINNER stays the
existing, separate concept (the model's own top pick — see
generate_dashboard.py's "TOP PICK" badge, unchanged, not touched by
this module). This answers the different question Jonathan's spec asks
for: does this runner's edge look like real, credible value, or not?

**Never auto-labels the biggest mathematical edge as a bet.** A runner
only qualifies as BEST VALUE if it passes real, configurable filters —
see ValueFilterConfig, per Jonathan's own requirement ("make all
research thresholds configurable rather than hard coded"). MODEL
WARNING uses RL-012's real, validated backtested finding (top picks
shown >=40% overstate their real win rate on genuinely held-out
validation data, not just discovery — see docs/RESEARCH_LAB.md) — a
real, checked fact, not a fabricated rule. Everything else degrades to
an honest "can't tell" (INSUFFICIENT DATA) rather than pretending
precision the real sample size (1 live settled day as of 2026-09-11)
doesn't support.
"""
from dataclasses import dataclass
from typing import Optional

RUNNER_STATUS_BEST_VALUE = "BEST VALUE"
RUNNER_STATUS_NO_EDGE = "NO EDGE"
RUNNER_STATUS_INSUFFICIENT_DATA = "INSUFFICIENT DATA"
RUNNER_STATUS_MODEL_WARNING = "MODEL WARNING"


@dataclass(frozen=True)
class ValueFilterConfig:
    """Real, configurable thresholds — nothing here is hard-coded into
    the classification logic itself. Defaults are deliberately simple
    and permissive until real live sample size justifies tightening
    them (see docs/BUILD_LOG.md's own caution against optimising
    thresholds on 1 day of data)."""
    min_edge_pts: float = 0.05              # +5 percentage points — spec's own example filter
    min_ev: float = 0.0                     # any real positive expected value
    min_model_probability: Optional[float] = None
    max_model_probability: Optional[float] = None
    overconfidence_threshold: float = 0.40  # RL-012's real, validated finding


def classify_runner_value(model_probability: float, edge: Optional[float], ev: Optional[float],
                           config: ValueFilterConfig = ValueFilterConfig()) -> str:
    """Real, honest per-runner value classification — never a guess.
    Returns one of the RUNNER_STATUS_* constants above.

    INSUFFICIENT DATA: no real market price, so no real edge/EV exists.
    NO EDGE: a real edge/EV was computed but it doesn't clear the real
      configured bar (includes model probability outside a configured
      range, and a real negative or too-small edge).
    MODEL WARNING: a real edge clears the bar, but the model's own
      stated probability falls in a band it's been shown, on real held-
      out validation data, to be overconfident in — the apparent edge
      may just be the model overstating itself, not a real opportunity.
    BEST VALUE: a real, credible, filter-passing edge."""
    if edge is None or ev is None:
        return RUNNER_STATUS_INSUFFICIENT_DATA

    if config.min_model_probability is not None and model_probability < config.min_model_probability:
        return RUNNER_STATUS_NO_EDGE
    if config.max_model_probability is not None and model_probability > config.max_model_probability:
        return RUNNER_STATUS_NO_EDGE

    if edge < config.min_edge_pts or ev < config.min_ev:
        return RUNNER_STATUS_NO_EDGE

    if model_probability >= config.overconfidence_threshold:
        return RUNNER_STATUS_MODEL_WARNING

    return RUNNER_STATUS_BEST_VALUE


def pick_race_best_value(runners: list[dict]) -> Optional[dict]:
    """Given a race's runners (each a dict carrying at least 'status'
    and 'edge'), returns the single real BEST VALUE runner — the
    strongest real edge among those that actually qualified — or None
    if no runner in this race qualifies. Never picks a MODEL WARNING or
    NO EDGE runner just because its raw edge number is bigger; only
    RUNNER_STATUS_BEST_VALUE entries are eligible at all."""
    candidates = [r for r in runners if r.get("status") == RUNNER_STATUS_BEST_VALUE]
    if not candidates:
        return None
    return max(candidates, key=lambda r: r["edge"])
