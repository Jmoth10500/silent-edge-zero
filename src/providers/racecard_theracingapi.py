"""
STUB — The Racing API racecard provider.

Written against their publicly documented response shape, but UNTESTED —
no API key exists yet. See docs/FREE_DATA_SOURCES.md #3.

Do not call this in production until:
1. An API key exists (set THERACINGAPI_KEY env var)
2. This has been run once against real data and its field mapping verified
   against an actual response — the docs snippet available publicly showed
   jockey stats fields but not a full racecard payload, so the field names
   below are a best guess from their docs and MUST be checked on first call.
"""
import os
from datetime import date

import requests

from .base import RacecardProvider, RaceCard, RunnerCard

BASE_URL = "https://api.theracingapi.com/v1"  # unverified — confirm on signup


class TheRacingApiProvider(RacecardProvider):
    source_name = "theracingapi"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("THERACINGAPI_KEY")
        if not self.api_key:
            raise RuntimeError(
                "THERACINGAPI_KEY not set. This provider cannot run until you've "
                "signed up at theracingapi.com and set the key — see "
                "docs/FREE_DATA_SOURCES.md #3."
            )

    def get_racecards(self, for_date: date) -> list[RaceCard]:
        resp = requests.get(
            f"{BASE_URL}/racecards",
            params={"date": for_date.isoformat(), "region": "GB"},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # NOTE: field names below are a best-effort mapping from public docs
        # snippets, NOT verified against a real payload. First real call
        # must log the raw response and this mapping must be corrected.
        cards = []
        for race in data.get("racecards", []):
            runners = [
                RunnerCard(
                    horse_name=r.get("horse"),
                    trainer_name=r.get("trainer"),
                    jockey_name=r.get("jockey"),
                    age=r.get("age"),
                    draw=r.get("draw"),
                    weight_lbs=r.get("lbs"),
                    official_rating=r.get("ofr"),
                    recent_form=r.get("form"),
                    equipment=r.get("headgear"),
                    external_ref=r.get("horse_id"),
                )
                for r in race.get("runners", [])
            ]
            cards.append(RaceCard(
                course_name=race.get("course"),
                race_date=for_date,
                off_time=race.get("off_time"),
                race_name=race.get("race_name"),
                race_class=race.get("race_class"),
                race_type=race.get("type"),
                distance_yards=race.get("distance_y"),
                surface=race.get("surface"),
                going=race.get("going"),
                runners=runners,
                external_ref=race.get("race_id"),
            ))
        return cards
