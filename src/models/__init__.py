"""Pydantic domain contracts.

This package exposes all Safarnama domain models grouped by concern:

Data-layer models (Phases 1–3)
    Airport, CountryProfile, currency/language helpers,
    tool result models (transport, hotels, places, weather, web search,
    fallback estimator, visa ingestion).

Planning domain models (Phase 5)
    Trip context, itinerary, logistics plan, visa verdict, budget breakdown.
"""

# ---------------------------------------------------------------------------
# Phase 1–3 data-layer models
# ---------------------------------------------------------------------------
from src.models.airport import Airport

# Budget
from src.models.budget import (
    BudgetBreakdown,
    BudgetStatus,
    BudgetVariance,
    ContingencyConfig,
    CostBreakdown,
    OptimizationAction,
    OptimizationResult,
)
from src.models.country import Coordinates, CountryProfile, CurrencyInfo, LanguageInfo
from src.models.fallback_estimator import (
    CostCategory,
    EstimateRequest,
    FallbackEstimateResult,
    TravelTier,
)
from src.models.hotels import HotelOption, HotelSearchResult

# Itinerary
from src.models.itinerary import (
    ActivityCategory,
    ActivitySlot,
    DayMeal,
    Daypart,
    DayPlan,
    ExperiencePlan,
    PointOfInterest,
)

# Logistics
from src.models.logistics import (
    HotelStay,
    LogisticsPlan,
    TransportLeg,
)
from src.models.places import PlaceItem, PlacesSearchResult
from src.models.transport import TransportSearchResult, TransportSegment

# ---------------------------------------------------------------------------
# Phase 5 — planning domain models
# ---------------------------------------------------------------------------
# Trip context
from src.models.trip import (
    BudgetMode,
    DateMode,
    FoodImportance,
    FoodPreferences,
    InitialPlanningState,
    Pace,
    PreviousTravelEntry,
    ResolvedLocation,
    TravelScope,
    TravelStyle,
    TripBudget,
    TripContext,
    TripDates,
    TripParty,
)

# Visa planning domain
from src.models.visa import (
    BaseVisaRule,
    EnrichedVisaRecord,
    VisaCountryVerdict,
    VisaOption,
    VisaRequirementStatus,
    VisaVerdict,
)
from src.models.weather import DailyWeatherForecast, WeatherForecastResult
from src.models.web_search import SearchResultItem, WebSearchResult

__all__ = [
    # Phase 1–3 data-layer
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
    # Phase 5 — trip context
    "BudgetMode",
    "DateMode",
    "FoodImportance",
    "FoodPreferences",
    "InitialPlanningState",
    "Pace",
    "PreviousTravelEntry",
    "ResolvedLocation",
    "TravelScope",
    "TravelStyle",
    "TripBudget",
    "TripContext",
    "TripDates",
    "TripParty",
    # Phase 5 — itinerary
    "ActivityCategory",
    "ActivitySlot",
    "DayMeal",
    "DayPlan",
    "Daypart",
    "ExperiencePlan",
    "PointOfInterest",
    # Phase 5 — logistics
    "HotelStay",
    "LogisticsPlan",
    "TransportLeg",
    # Phase 5 — visa planning
    "VisaCountryVerdict",
    "VisaRequirementStatus",
    "VisaVerdict",
    # Phase 5 — budget
    "BudgetBreakdown",
    "BudgetStatus",
    "BudgetVariance",
    "ContingencyConfig",
    "CostBreakdown",
    "OptimizationAction",
    "OptimizationResult",
]
