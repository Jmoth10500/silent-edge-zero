"""
Real unit tests for src/features/weather_features.py — the RL-001 (turf-vs-
AW rainfall interaction) feature shape. All fixtures are synthetic; nothing
here is evidence a real weather effect exists (see the module's docstring
and docs/RESEARCH_LAB.md RL-001). WeatherSnapshot itself is already LIVE
(src/providers/weather_open_meteo.py) — only the surface classification and
feature-combination logic in this file are new and untested until now.
"""
from datetime import date, datetime, timezone

import pytest

from src.features.weather_features import (
    is_all_weather_surface,
    turf_rainfall_interaction,
    weather_race_features,
)
from src.providers.base import WeatherSnapshot


def make_snapshot(**overrides) -> WeatherSnapshot:
    defaults = dict(
        course_name="Lingfield Park",
        for_date=date(2026, 9, 8),
        rainfall_6h_mm=1.5,
        rainfall_24h_mm=5.2,
        temperature_c=14.0,
        wind_speed_kmh=12.0,
        wind_direction_deg=180.0,
        observed_at=datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc),
        available_at=datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc),
        source="open-meteo",
    )
    defaults.update(overrides)
    return WeatherSnapshot(**defaults)


class TestIsAllWeatherSurface:
    @pytest.mark.parametrize(
        "surface",
        [
            "AW",
            "Aw",
            "Polytrack",
            "Tapeta",
            "Fibresand",
            "Standard (AW)",
            "All Weather",
            "All-Weather",
            "standard, all-weather",
        ],
    )
    def test_recognises_all_weather_descriptors(self, surface):
        assert is_all_weather_surface(surface) is True

    @pytest.mark.parametrize(
        "surface",
        [
            "Turf",
            "Good (Turf)",
            "Good to Soft (Turf)",
            "Heavy, Turf",
        ],
    )
    def test_recognises_turf_descriptors(self, surface):
        assert is_all_weather_surface(surface) is False

    @pytest.mark.parametrize("surface", [None, "", "Good", "Good to Soft", "Standard"])
    def test_ambiguous_or_missing_is_none_not_guessed(self, surface):
        assert is_all_weather_surface(surface) is None

    def test_short_marker_is_whole_word_not_substring(self):
        # "aw" must not false-positive merely because it appears inside a
        # longer, unrelated word (there is no real such going descriptor,
        # but this pins the whole-word-token behaviour the docstring
        # promises rather than a raw substring check).
        assert is_all_weather_surface("flawed") is None


class TestTurfRainfallInteraction:
    def test_turf_passes_rainfall_through_unchanged(self):
        assert turf_rainfall_interaction("Good (Turf)", 7.3) == 7.3

    def test_all_weather_forced_to_exactly_zero(self):
        assert turf_rainfall_interaction("Polytrack", 7.3) == 0.0

    def test_all_weather_forced_to_zero_even_with_no_rainfall(self):
        assert turf_rainfall_interaction("Standard (AW)", 0.0) == 0.0

    def test_ambiguous_surface_returns_none_not_a_guess(self):
        assert turf_rainfall_interaction("Good", 7.3) is None

    def test_missing_surface_returns_none(self):
        assert turf_rainfall_interaction(None, 7.3) is None

    def test_missing_rainfall_returns_none_even_on_clear_surface(self):
        assert turf_rainfall_interaction("Turf", None) is None


class TestWeatherRaceFeatures:
    def test_no_snapshot_returns_empty_dict(self):
        assert weather_race_features(None, "Turf") == {}

    def test_full_snapshot_on_turf(self):
        snap = make_snapshot(rainfall_24h_mm=5.2, rainfall_6h_mm=1.5, wind_speed_kmh=12.0)
        features = weather_race_features(snap, "Good (Turf)")
        assert features == {
            "rainfall_24h_mm": 5.2,
            "rainfall_6h_mm": 1.5,
            "wind_speed_kmh": 12.0,
            "turf_rainfall_interaction": 5.2,
        }

    def test_full_snapshot_on_all_weather_zeroes_interaction_only(self):
        snap = make_snapshot(rainfall_24h_mm=5.2, rainfall_6h_mm=1.5, wind_speed_kmh=12.0)
        features = weather_race_features(snap, "Standard (AW)")
        # the raw rainfall readings are still reported honestly — only the
        # turf-specific interaction term is zeroed, per the module's
        # design-choice note, not the underlying weather facts themselves.
        assert features["rainfall_24h_mm"] == 5.2
        assert features["turf_rainfall_interaction"] == 0.0

    def test_ambiguous_surface_omits_interaction_key_entirely(self):
        snap = make_snapshot()
        features = weather_race_features(snap, "Good")
        assert "turf_rainfall_interaction" not in features
        assert "rainfall_24h_mm" in features  # raw weather facts still present

    def test_missing_field_is_omitted_not_imputed(self):
        snap = make_snapshot(wind_speed_kmh=None, rainfall_24h_mm=None)
        features = weather_race_features(snap, "Good (Turf)")
        assert "wind_speed_kmh" not in features
        assert "rainfall_24h_mm" not in features
        # rainfall_24h_mm missing means the interaction can't be computed
        # either, even though the surface itself is unambiguous turf.
        assert "turf_rainfall_interaction" not in features
        assert features["rainfall_6h_mm"] == 1.5
