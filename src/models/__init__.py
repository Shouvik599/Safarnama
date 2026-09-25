"""Pydantic domain contracts."""

from src.models.airport import Airport
from src.models.country import Coordinates, CountryProfile, CurrencyInfo, LanguageInfo
from src.models.fallback_estimator import (
    CostCategory,
    EstimateRequest,
    FallbackEstimateResult,
    TravelTier,
)
from src.models.hotels import HotelOption, HotelSearchResult
from src.models.places import PlaceItem, PlacesSearchResult
from src.models.transport import TransportSearchResult, TransportSegment
from src.models.visa import BaseVisaRule, EnrichedVisaRecord, VisaOption
from src.models.weather import DailyWeatherForecast, WeatherForecastResult
from src.models.web_search import SearchResultItem, WebSearchResult

__all__ = [
    "Airport",
    "BaseVisaRule",
    "Coordinates",
    "CostCategory",
    "CountryProfile",
    "CurrencyInfo",
    "DailyWeatherForecast",
    "EnrichedVisaRecord",
    "EstimateRequest",
    "FallbackEstimateResult",
    "HotelOption",
    "HotelSearchResult",
    "LanguageInfo",
    "PlaceItem",
    "PlacesSearchResult",
    "SearchResultItem",
    "TransportSearchResult",
    "TransportSegment",
    "TravelTier",
    "VisaOption",
    "WeatherForecastResult",
    "WebSearchResult",
]
