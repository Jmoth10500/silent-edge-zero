"""
Weather-derived race features — the real hypothesis flagged in
docs/RESEARCH_LAB.md RL-001 since Session 1 (autonomous overnight): all-
weather (AW) surfaces should be less rainfall-sensitive than turf, so a
feature that lets a model treat rainfall differently by surface should show
a near-zero effect on AW races and a real effect on turf if the hypothesis
holds.

This module is pure computation over a caller-supplied WeatherSnapshot
(src/providers/base.py, already LIVE via src/providers/weather_open_meteo.py,
no API key needed) and a caller-supplied surface string — it makes no HTTP
calls and touches no DB itself, same discipline as
src/features/draw_bias.py and src/features/runner_features.py (leakage
safety, DB access, etc. are the caller's responsibility, not this module's).

RL-001's actual hypothesis (does rainfall genuinely predict turf outcomes
more than AW ones) is NOT tested here and can't be from this cloud routine:
that needs real (weather, surface/going, result) triples, and surface/going
isn't even a verified field on the racecard provider yet
(src/providers/racecard_theracingapi.py has no confirmed mapping for it —
see that module's docstring history). This file only builds the feature
SHAPE a model could consume once that data exists, tested against
synthetic fixtures — the same "build the plumbing now, prove the
hypothesis later" pattern every prior session has used for RL-002/RL-004.

Design choice flagged for review, not proven: forcing the interaction term
to exactly 0.0 on AW surfaces bakes RL-001's hypothesis in as a fixed
assumption rather than letting a fitted model discover it. The alternative
— passing rainfall through unmodified on every surface and letting a
model learn a per-surface weight itself — wasn't chosen here because there
is no real (weather, surface, result) data yet to compare the two
approaches against. Recorded honestly as an open question, not resolved.
"""
import re
from typing import Optional

from src.providers.base import WeatherSnapshot

# No real racecard field maps to a surface/going string yet (see module
# docstring) — this module must define its own vocabulary ahead of a
# verified live field, same situation src/features/draw_bias.py is in with
# its caller-supplied `surface` parameter. Written against known real GB/IRE
# going/surface descriptions (e.g. "Standard (AW)", "Good to Soft (Turf)").
_AW_TOKENS = frozenset({"aw", "polytrack", "tapeta", "fibresand"})
_AW_PHRASES = ("all weather", "all-weather")


def is_all_weather_surface(surface: Optional[str]) -> Optional[bool]:
    """
    True if `surface` looks like an all-weather descriptor, False if it
    looks like turf, None if `surface` is missing or doesn't clearly say
    either — never guessed.

    Matches on whole word tokens (split on non-letters) for the short
    markers (AW/Polytrack/Tapeta/Fibresand) rather than raw substrings, so
    an unrelated word merely containing "aw" doesn't false-positive; the
    two-word "all weather" / "all-weather" phrases are checked directly
    since they're not single tokens.
    """
    if not surface:
        return None
    s = surface.strip().lower()
    tokens = set(re.split(r"[^a-z]+", s))
    if tokens & _AW_TOKENS or any(phrase in s for phrase in _AW_PHRASES):
        return True
    if "turf" in tokens:
        return False
    return None


def turf_rainfall_interaction(surface: Optional[str], rainfall_24h_mm: Optional[float]) -> Optional[float]:
    """
    The RL-001 feature itself: 24h rainfall on turf, forced to exactly 0.0
    on AW (see the module docstring's design-choice note), None when the
    surface can't be classified either way or rainfall is missing — never
    guessed at either end.
    """
    is_aw = is_all_weather_surface(surface)
    if is_aw is None or rainfall_24h_mm is None:
        return None
    return 0.0 if is_aw else rainfall_24h_mm


def weather_race_features(snapshot: Optional[WeatherSnapshot], surface: Optional[str]) -> dict:
    """
    Combine a WeatherSnapshot with a race's surface into a flat feature
    dict — same "omit missing, never impute" discipline as
    src/features/feature_vector.py. Returns {} if there's no snapshot at
    all (e.g. weather wasn't collected for this course/date).
    """
    if snapshot is None:
        return {}
    features: dict = {}
    if snapshot.rainfall_24h_mm is not None:
        features["rainfall_24h_mm"] = snapshot.rainfall_24h_mm
    if snapshot.rainfall_6h_mm is not None:
        features["rainfall_6h_mm"] = snapshot.rainfall_6h_mm
    if snapshot.wind_speed_kmh is not None:
        features["wind_speed_kmh"] = snapshot.wind_speed_kmh
    interaction = turf_rainfall_interaction(surface, snapshot.rainfall_24h_mm)
    if interaction is not None:
        features["turf_rainfall_interaction"] = interaction
    return features
