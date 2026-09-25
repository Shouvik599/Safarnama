"""Pydantic domain contracts."""

from src.models.airport import Airport
from src.models.country import Coordinates, CountryProfile, CurrencyInfo, LanguageInfo
from src.models.hotels import HotelOption, HotelSearchResult
from src.models.transport import TransportSearchResult, TransportSegment
from src.models.visa import BaseVisaRule, EnrichedVisaRecord, VisaOption
from src.models.weather import DailyWeatherForecast, WeatherForecastResult
from src.models.web_search import SearchResultItem, WebSearchResult

__all__ = [
    "Airport",
    "BaseVisaRule",
    "Coordinates",
    "CountryProfile",
    "CurrencyInfo",
    "DailyWeatherForecast",
    "EnrichedVisaRecord",
    "HotelOption",
    "HotelSearchResult",
    "LanguageInfo",
    "SearchResultItem",
    "TransportSearchResult",
    "TransportSegment",
    "VisaOption",
    "WeatherForecastResult",
    "WebSearchResult",
]
