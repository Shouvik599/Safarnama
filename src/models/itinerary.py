"""Domain models for itinerary planning output.

Defines the structured contracts for day-level and activity-level itinerary data
produced by the Experience Node and consumed by the Optimizer and final result formatter.

Model hierarchy
---------------
``Daypart``
    Time-of-day label for scheduling (MORNING / AFTERNOON / EVENING).

``ActivityCategory``
    Broad classification for activities and POIs.

``PointOfInterest``
    A single attraction, landmark, or place the traveler will visit.

``ActivitySlot``
    A scheduled activity anchored to a daypart, including weather-substitution metadata.

``DayMeal``
    A single meal recommendation with optional restaurant reference.

``DayPlan``
    One calendar day's complete itinerary (activities + meals + weather + hotel + costs).

``ExperiencePlan``
    Aggregate of all day plans covering the full trip duration.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Daypart(StrEnum):
    """Coarse time-of-day slot for scheduling activities.

    Itinerary uses dayparts rather than exact clock times per product spec.
    """

    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"


class ActivityCategory(StrEnum):
    """Broad classification for a point of interest or activity."""

    HISTORY_HERITAGE = "HISTORY_HERITAGE"
    MUSEUM = "MUSEUM"
    ARCHITECTURE = "ARCHITECTURE"
    NATURE = "NATURE"
    MOUNTAIN = "MOUNTAIN"
    BEACH = "BEACH"
    ADVENTURE = "ADVENTURE"
    WILDLIFE = "WILDLIFE"
    SHOPPING = "SHOPPING"
    NIGHTLIFE = "NIGHTLIFE"
    PHOTOGRAPHY = "PHOTOGRAPHY"
    SPIRITUAL = "SPIRITUAL"
    ART_CULTURE = "ART_CULTURE"
    LOCAL_EXPERIENCE = "LOCAL_EXPERIENCE"
    FOOD_EXPERIENCE = "FOOD_EXPERIENCE"
    RELAXATION = "RELAXATION"
    FAMILY_KIDS = "FAMILY_KIDS"
    SPORTS = "SPORTS"
    TRANSIT = "TRANSIT"
    OTHER = "OTHER"


# ---------------------------------------------------------------------------
# Point of interest
# ---------------------------------------------------------------------------


class PointOfInterest(BaseModel):
    """A single attraction, landmark, or place included in the itinerary.

    May originate from the live places tool, static curated knowledge, or
    a must-visit specified by the traveler.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Name of the attraction, landmark, or place.")
    category: ActivityCategory = Field(
        default=ActivityCategory.OTHER,
        description="Broad activity category classification.",
    )
    city: str = Field(description="City or locality where this POI is located.")
    country: str | None = Field(default=None, description="Country (for international trips).")
    address: str | None = Field(default=None, description="Street address or vicinity.")
    latitude: float | None = Field(default=None, description="GPS latitude coordinate.")
    longitude: float | None = Field(default=None, description="GPS longitude coordinate.")
    description: str | None = Field(default=None, description="Brief summary of the POI.")
    estimated_duration_minutes: int | None = Field(
        default=None,
        ge=5,
        description="Approximate visit duration in minutes.",
    )
    estimated_cost_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated entrance fee or participation cost per person in INR (0.0 if free).",
    )
    is_must_visit: bool = Field(
        default=False,
        description="True if this POI was explicitly requested by the traveler as a must-visit.",
    )
    maps_url: str | None = Field(default=None, description="Optional maps or booking URL.")
    provider: str = Field(
        default="curated",
        description=(
            "Data source: 'serpapi-google-maps', 'overpass-osm', 'nominatim-osm', "
            "'web-search', 'fixture', 'category-heuristic', or 'curated'."
        ),
    )


# ---------------------------------------------------------------------------
# Activity slot
# ---------------------------------------------------------------------------


class ActivitySlot(BaseModel):
    """A scheduled activity anchored to a daypart, with optional weather substitution.

    When weather makes the original activity unsuitable, ``substituted_for``
    records what was originally planned and ``weather_note`` explains the change.
    """

    model_config = ConfigDict(frozen=True)

    daypart: Daypart = Field(description="Time-of-day slot (MORNING / AFTERNOON / EVENING).")
    poi: PointOfInterest = Field(description="The point of interest being visited.")
    notes: str | None = Field(
        default=None,
        description="Optional scheduling note (e.g. 'Book tickets in advance').",
    )
    # Weather adjustment
    is_weather_substituted: bool = Field(
        default=False,
        description="True if this activity replaced an outdoor activity due to weather risk.",
    )
    substituted_for: str | None = Field(
        default=None,
        description=(
            "Name of the original outdoor activity that was replaced due to weather. "
            "None if no substitution occurred."
        ),
    )
    weather_note: str | None = Field(
        default=None,
        description=(
            "Explanation of the weather condition that triggered the substitution, "
            "e.g. 'High rain probability (80%) forecast — replaced outdoor hike'."
        ),
    )


# ---------------------------------------------------------------------------
# Meal recommendation
# ---------------------------------------------------------------------------


class DayMeal(BaseModel):
    """A single meal recommendation for one daypart slot.

    Restaurant details come from the live places tool where available.
    """

    model_config = ConfigDict(frozen=True)

    daypart: Daypart = Field(description="Meal slot (typically MORNING/AFTERNOON/EVENING).")
    meal_type: str = Field(
        description="Meal classification, e.g. 'breakfast', 'lunch', 'dinner', 'snack'."
    )
    restaurant_name: str | None = Field(
        default=None,
        description=(
            "Name of the recommended restaurant or food venue. "
            "Must come from a real places/tool result; not LLM-invented."
        ),
    )
    cuisine: str | None = Field(
        default=None,
        description="Cuisine type, e.g. 'South Indian', 'Italian', 'Street Food'.",
    )
    estimated_cost_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated per-person meal cost in INR.",
    )
    address: str | None = Field(default=None, description="Restaurant address or vicinity.")
    maps_url: str | None = Field(default=None, description="Optional maps link.")
    is_estimated: bool = Field(
        default=False,
        description="True if cost is a heuristic estimate rather than from a live pricing source.",
    )
    notes: str | None = Field(
        default=None,
        description="Dietary or recommendation note, e.g. 'Famous for biryani'.",
    )


# ---------------------------------------------------------------------------
# Day plan
# ---------------------------------------------------------------------------


class DayPlan(BaseModel):
    """Complete plan for one calendar day of the trip.

    Combines scheduled activity slots, meal recommendations, accommodation,
    and day-level cost totals. Uses dayparts rather than exact clock times.
    """

    model_config = ConfigDict(frozen=True)

    day_number: Annotated[int, Field(ge=1, description="1-indexed day number within the trip.")]
    date: str | None = Field(
        default=None, description="Calendar date for this day in YYYY-MM-DD format, if known."
    )
    city: str = Field(description="Primary city or destination for this day.")
    country: str | None = Field(default=None, description="Country for this day (international).")

    # Activities
    activities: list[ActivitySlot] = Field(
        default_factory=list,
        description="Scheduled activity slots in daypart order.",
    )

    # Meals
    meals: list[DayMeal] = Field(
        default_factory=list,
        description="Meal recommendations for the day.",
    )

    # Accommodation
    hotel_name: str | None = Field(
        default=None, description="Name of accommodation for this night (None on last day)."
    )
    hotel_booking_url: str | None = Field(
        default=None, description="Booking/reservation URL for the accommodation."
    )

    # Weather
    weather_summary: str | None = Field(
        default=None,
        description=(
            "Brief weather forecast summary for the day, "
            "e.g. 'Partly cloudy, 25°C. Outdoor activities suitable.'."
        ),
    )
    is_outdoor_friendly: bool = Field(
        default=True,
        description="True if forecast conditions are generally suitable for outdoor sightseeing.",
    )

    # Day-level costs (INR)
    activity_cost_inr: float = Field(
        default=0.0, ge=0.0, description="Total estimated activity/attraction costs for the day."
    )
    food_cost_inr: float = Field(
        default=0.0, ge=0.0, description="Estimated food/dining cost for the day."
    )
    local_transport_cost_inr: float = Field(
        default=0.0, ge=0.0, description="Estimated local transport (taxi/metro) cost for the day."
    )

    # Notes
    notes: str | None = Field(
        default=None,
        description="Important practical notes for this day, e.g. 'Closed on Mondays'.",
    )

    @property
    def total_day_cost_inr(self) -> float:
        """Sum of activity, food, and local transport costs for the day."""
        return self.activity_cost_inr + self.food_cost_inr + self.local_transport_cost_inr


# ---------------------------------------------------------------------------
# Experience plan
# ---------------------------------------------------------------------------


class ExperiencePlan(BaseModel):
    """Aggregated experience plan covering the full trip duration.

    Produced by the Experience Node and consumed by the Optimizer and
    final itinerary formatter.
    """

    model_config = ConfigDict(frozen=True)

    days: list[DayPlan] = Field(
        default_factory=list,
        description="Day-level plans in chronological order.",
    )
    total_days: Annotated[
        int, Field(ge=0, description="Total number of planned days (must equal len(days)).")
    ]
    destinations_covered: list[str] = Field(
        default_factory=list,
        description="Ordered list of cities/destinations covered across all days.",
    )
    must_visits_fulfilled: list[str] = Field(
        default_factory=list,
        description="Names of must-visit POIs that were successfully included.",
    )
    must_visits_omitted: list[str] = Field(
        default_factory=list,
        description=(
            "Names of must-visit POIs that could NOT be included, "
            "with reasons carried in ``warnings``."
        ),
    )
    weather_substitutions: int = Field(
        default=0,
        ge=0,
        description="Total number of weather-driven activity substitutions across all days.",
    )
    # Aggregate cost totals (INR)
    total_activity_cost_inr: float = Field(
        default=0.0, ge=0.0, description="Sum of all activity/attraction costs in INR."
    )
    total_food_cost_inr: float = Field(
        default=0.0, ge=0.0, description="Sum of all daily food cost estimates in INR."
    )
    total_local_transport_cost_inr: float = Field(
        default=0.0, ge=0.0, description="Sum of local transport estimates for all days."
    )
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Non-fatal issues encountered during experience planning, "
            "e.g. reduced data quality, skipped must-visits, weather uncertainty."
        ),
    )
    is_estimated: bool = Field(
        default=False,
        description="True if any cost component relied on fallback estimation.",
    )
    timestamp: str = Field(
        description="ISO 8601 timestamp when this experience plan was generated."
    )
