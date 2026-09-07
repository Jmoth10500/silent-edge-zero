"""
LIVE weather provider — Open-Meteo, no API key, no signup.
See docs/FREE_DATA_SOURCES.md #1.

Attribution required per CC BY 4.0: data (c) Open-Meteo.com, non-commercial use.
"""
from datetime import date, datetime, timezone
from typing import Optional

import requests

from .base import WeatherProvider, WeatherSnapshot

BASE_URL = "https://api.open-meteo.com/v1/forecast"


class OpenMeteoWeatherProvider(WeatherProvider):
    source_name = "open-meteo"

    def get_snapshot(self, course_name: str, latitude: float, longitude: float, for_date: date) -> WeatherSnapshot:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "precipitation,temperature_2m,wind_speed_10m,wind_direction_10m",
            "start_date": for_date.isoformat(),
            "end_date": for_date.isoformat(),
            "timezone": "Europe/London",
        }
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        hourly = data["hourly"]
        times = hourly["time"]
        precip = hourly["precipitation"]
        temp = hourly["temperature_2m"]
        wind_speed = hourly["wind_speed_10m"]
        wind_dir = hourly["wind_direction_10m"]

        now_hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
        idx = times.index(now_hour) if now_hour in times else len(times) - 1

        rainfall_6h = sum(v for v in precip[max(0, idx - 6):idx + 1] if v is not None)
        rainfall_24h = sum(v for v in precip[max(0, idx - 24):idx + 1] if v is not None)

        return WeatherSnapshot(
            course_name=course_name,
            for_date=for_date,
            rainfall_6h_mm=round(rainfall_6h, 2),
            rainfall_24h_mm=round(rainfall_24h, 2),
            temperature_c=temp[idx] if idx < len(temp) else None,
            wind_speed_kmh=wind_speed[idx] if idx < len(wind_speed) else None,
            wind_direction_deg=wind_dir[idx] if idx < len(wind_dir) else None,
            observed_at=datetime.now(timezone.utc),
            available_at=datetime.now(timezone.utc),
            source=self.source_name,
        )
