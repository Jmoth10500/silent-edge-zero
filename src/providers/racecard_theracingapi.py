"""
The Racing API racecard provider — LIVE, verified against a real response
2026-09-08 (29 real GB races returned on first successful call).

Auth: HTTP Basic (username + password from account signup), NOT a bearer
token — confirmed from their published OpenAPI spec and a live test call.
Free tier endpoint: /v1/racecards/free — today + tomorrow, basic fields only
(no odds; odds require a paid tier — see docs/FREE_DATA_SOURCES.md #3).

Set THERACINGAPI_USERNAME and THERACINGAPI_PASSWORD (in .env, gitignored,
never commit these).
"""
import os
from datetime import date, datetime, timezone

import requests

from .base import RacecardProvider, RaceCard, RunnerCard

BASE_URL = "https://api.theracingapi.com/v1"


class TheRacingApiProvider(RacecardProvider):
    source_name = "theracingapi"

    def __init__(self, username: str | None = None, password: str | None = None):
        self.username = username or os.environ.get("THERACINGAPI_USERNAME")
        self.password = password or os.environ.get("THERACINGAPI_PASSWORD")
        if not self.username or not self.password:
            raise RuntimeError(
                "THERACINGAPI_USERNAME / THERACINGAPI_PASSWORD not set. "
                "See docs/FREE_DATA_SOURCES.md #3 for how to get these."
            )

    def get_racecards(self, for_date: date, region: str = "GB") -> list[RaceCard]:
        """for_date is only used to pick 'today' vs 'tomorrow' — the free
        endpoint doesn't take an arbitrary date, only those two relative
        days (confirmed from the real API: no date param accepted, 'day'
        param takes 'today'/'tomorrow' only)."""
        today = date.today()
        if for_date == today:
            day = "today"
        elif (for_date - today).days == 1:
            day = "tomorrow"
        else:
            raise ValueError(
                f"The free tier only supports today/tomorrow, not {for_date} "
                f"(today is {today}). Historical/future racecards need a paid tier."
            )

        resp = requests.get(
            f"{BASE_URL}/racecards/free",
            params={"day": day},
            auth=(self.username, self.password),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        ingested_at = datetime.now(timezone.utc)
        cards = []
        for race in data.get("racecards", []):
            if region and race.get("region") != region:
                continue

            runners = [
                RunnerCard(
                    horse_name=r.get("horse"),
                    trainer_name=r.get("trainer"),
                    jockey_name=r.get("jockey"),
                    age=int(r["age"]) if r.get("age", "").isdigit() else None,
                    draw=int(r["draw"]) if r.get("draw", "").isdigit() else None,
                    weight_lbs=int(r["lbs"]) if r.get("lbs", "").isdigit() else None,
                    official_rating=int(r["ofr"]) if r.get("ofr", "").isdigit() else None,
                    recent_form=r.get("form") or None,
                    equipment=r.get("headgear") or None,
                    external_ref=r.get("horse_id"),
                )
                for r in race.get("runners", [])
            ]
            # The API's own "off_time" field is ambiguous (e.g. "1:12" with no
            # AM/PM — Leicester's actual 13:12 race was returned as "1:12",
            # which a naive TIME cast would silently read as 01:12 AM).
            # off_dt is a full ISO datetime with timezone — always use that
            # to derive an unambiguous 24-hour off_time instead of trusting
            # the provider's own off_time string directly.
            off_time = race.get("off_time")
            off_dt_raw = race.get("off_dt")
            if off_dt_raw:
                try:
                    off_time = datetime.fromisoformat(off_dt_raw).strftime("%H:%M")
                except ValueError:
                    pass  # fall back to the raw (possibly ambiguous) off_time rather than crash

            distance_yards = None
            distance_f_raw = race.get("distance_f")
            if distance_f_raw:
                try:
                    distance_yards = round(float(distance_f_raw) * 220)  # 1 furlong = 220 yards
                except ValueError:
                    pass  # leave as None rather than guess at a malformed value

            cards.append(RaceCard(
                course_name=race.get("course"),
                race_date=for_date,
                off_time=off_time,
                race_name=race.get("race_name"),
                race_class=race.get("race_class") or None,
                race_type=race.get("type"),
                distance_yards=distance_yards,
                surface=race.get("surface"),
                going=race.get("going"),
                runners=runners,
                external_ref=race.get("race_id"),
            ))
        return cards
