"""
Provider interfaces (build brief Section 51 — "Data Source Redundancy").

The rest of the system requests a RACECARD, not a SpecificProviderRacecard.
This means a provider (e.g. The Racing API) can be replaced without touching
anything downstream. Each concrete provider lives in its own file and must
implement one of these interfaces.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class WeatherSnapshot:
    course_name: str
    for_date: date
    rainfall_6h_mm: Optional[float]
    rainfall_24h_mm: Optional[float]
    temperature_c: Optional[float]
    wind_speed_kmh: Optional[float]
    wind_direction_deg: Optional[float]
    observed_at: datetime
    available_at: datetime
    source: str


class WeatherProvider(ABC):
    @abstractmethod
    def get_snapshot(self, course_name: str, latitude: float, longitude: float, for_date: date) -> WeatherSnapshot:
        ...


@dataclass
class RunnerCard:
    horse_name: str
    trainer_name: Optional[str]
    jockey_name: Optional[str]
    age: Optional[int]
    draw: Optional[int]
    weight_lbs: Optional[int]
    official_rating: Optional[int]
    recent_form: Optional[str]
    equipment: Optional[str]
    external_ref: Optional[str]


@dataclass
class RaceCard:
    course_name: str
    race_date: date
    off_time: str
    race_name: str
    race_class: Optional[str]
    race_type: Optional[str]
    distance_yards: Optional[int]
    surface: Optional[str]
    going: Optional[str]
    runners: list[RunnerCard]
    external_ref: Optional[str]


class RacecardProvider(ABC):
    @abstractmethod
    def get_racecards(self, for_date: date) -> list[RaceCard]:
        ...


@dataclass
class RunnerResult:
    horse_name: str
    finishing_position: Optional[int]
    distance_beaten: Optional[float]
    starting_price: Optional[float]
    bsp: Optional[float]
    result_note: Optional[str]


class ResultsProvider(ABC):
    @abstractmethod
    def get_results(self, for_date: date) -> dict[str, list[RunnerResult]]:
        """Returns {race_external_ref: [RunnerResult, ...]}"""
        ...


@dataclass
class OddsSnapshot:
    horse_name: str
    bookmaker_odds: Optional[float]
    exchange_back: Optional[float]
    exchange_lay: Optional[float]
    observed_at: datetime


class OddsProvider(ABC):
    @abstractmethod
    def get_odds(self, race_external_ref: str) -> list[OddsSnapshot]:
        ...


class RatingsProvider(ABC):
    @abstractmethod
    def get_rating(self, horse_name: str) -> Optional[int]:
        ...


class ExternalPredictionProvider(ABC):
    """For consuming a free third-party model's predictions as EXTERNAL_MODEL_X
    evidence (Section 18) — never presented as our own prediction."""
    @abstractmethod
    def get_predictions(self, race_external_ref: str) -> dict[str, float]:
        """Returns {horse_name: probability}"""
        ...
