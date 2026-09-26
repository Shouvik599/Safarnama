"""Domain models for trip context and planning inputs.

Represents the canonical, validated trip planning request:

- ``TravelScope`` — domestic vs. international classification
- ``DateMode`` — exact, flexible window, or best-date-search
- ``BudgetMode`` — total trip vs. per-person budget
- ``TravelStyle`` — budget / comfortable / premium / luxury
- ``Pace`` — relaxed / balanced / packed
- ``FoodImportance`` — how strongly food shapes the itinerary
- ``TripParty`` — adults + children traveler group
- ``TripDates`` — travel date contract covering all three date modes
- ``TripBudget`` — validated budget specification
- ``FoodPreferences`` — dietary, allergy, and experience configuration
- ``TripContext`` — top-level aggregate of the full planning input

These models define the contract between the API layer and the planning
graph (LangGraph nodes). They do not contain orchestration logic.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class TravelScope(StrEnum):
    """Whether the trip is domestic (within India) or international."""

    DOMESTIC = "DOMESTIC"
    INTERNATIONAL = "INTERNATIONAL"


class DateMode(StrEnum):
    """How the user has specified travel dates.

    EXACT        — precise start and end dates provided.
    FLEXIBLE     — a preferred start date with an allowed shift window.
    FIND_BEST    — a broader date window within which the planner selects
                   optimal dates balancing price, weather, and availability.
    """

    EXACT = "EXACT"
    FLEXIBLE = "FLEXIBLE"
    FIND_BEST = "FIND_BEST"


class BudgetMode(StrEnum):
    """Whether the budget figure represents the whole trip or per person."""

    TOTAL = "TOTAL"
    PER_PERSON = "PER_PERSON"


class TravelStyle(StrEnum):
    """Broad quality/comfort preference affecting accommodation and transport choices."""

    BUDGET = "BUDGET"
    COMFORTABLE = "COMFORTABLE"
    PREMIUM = "PREMIUM"
    LUXURY = "LUXURY"


class Pace(StrEnum):
    """Day-level activity density preference.

    RELAXED  — 1–3 major activities/day, longer meals, more free time.
    BALANCED — 3–5 activities/day with reasonable breathing room.
    PACKED   — maximise sightseeing; minimal downtime.
    """

    RELAXED = "RELAXED"
    BALANCED = "BALANCED"
    PACKED = "PACKED"


class FoodImportance(StrEnum):
    """How strongly food experiences shape route and schedule decisions.

    LOW    — basic food coverage; restaurants are secondary to attractions.
    MEDIUM — a good mix of notable local food and sightseeing.
    HIGH   — food experiences may drive route/scheduling choices.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ---------------------------------------------------------------------------
# Party
# ---------------------------------------------------------------------------


class TripParty(BaseModel):
    """Traveler group composition."""

    model_config = ConfigDict(frozen=True)

    adults: Annotated[int, Field(ge=1, le=50, description="Number of adult travelers (≥1).")]
    children: Annotated[
        int, Field(default=0, ge=0, le=20, description="Number of child travelers (0–20).")
    ]

    @property
    def total_travelers(self) -> int:
        """Total headcount including children."""
        return self.adults + self.children


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------


class TripDates(BaseModel):
    """Travel date specification covering all three date modes.

    Field requirements by mode:

    EXACT
        ``start_date`` and ``end_date`` must both be present.
        ``duration_days`` is derived automatically if omitted.

    FLEXIBLE
        ``start_date`` must be present.
        ``duration_days`` must be specified.
        ``flexibility_days`` optionally indicates how many days the start
        date may shift (default 0 = no shift allowed).

    FIND_BEST
        ``window_start`` and ``window_end`` must both be present.
        ``duration_days`` must be specified.
    """

    model_config = ConfigDict(frozen=True)

    mode: DateMode = Field(description="Date specification mode (EXACT / FLEXIBLE / FIND_BEST).")

    # EXACT / FLEXIBLE
    start_date: str | None = Field(
        default=None,
        description="Trip start date in YYYY-MM-DD format (required for EXACT and FLEXIBLE modes).",
    )
    end_date: str | None = Field(
        default=None,
        description="Trip end date in YYYY-MM-DD format (required for EXACT mode).",
    )

    # FIND_BEST
    window_start: str | None = Field(
        default=None,
        description="Earliest acceptable start date in YYYY-MM-DD format (FIND_BEST mode).",
    )
    window_end: str | None = Field(
        default=None,
        description="Latest acceptable end date in YYYY-MM-DD format (FIND_BEST mode).",
    )

    # Duration
    duration_days: int | None = Field(
        default=None,
        ge=1,
        le=90,
        description=(
            "Trip length in days. Required for FLEXIBLE and FIND_BEST modes. "
            "For EXACT mode this is derived from start/end dates when omitted."
        ),
    )

    # Flexibility (FLEXIBLE mode)
    flexibility_days: int = Field(
        default=0,
        ge=0,
        le=14,
        description=(
            "For FLEXIBLE mode: how many days the start date may shift "
            "to optimise price, weather, or availability."
        ),
    )

    @model_validator(mode="after")
    def _validate_date_fields(self) -> TripDates:
        if self.mode == DateMode.EXACT:
            if not self.start_date:
                raise ValueError("start_date is required for EXACT date mode.")
            if not self.end_date:
                raise ValueError("end_date is required for EXACT date mode.")
        elif self.mode == DateMode.FLEXIBLE:
            if not self.start_date:
                raise ValueError("start_date is required for FLEXIBLE date mode.")
            if self.duration_days is None:
                raise ValueError("duration_days is required for FLEXIBLE date mode.")
        elif self.mode == DateMode.FIND_BEST:
            if not self.window_start:
                raise ValueError("window_start is required for FIND_BEST date mode.")
            if not self.window_end:
                raise ValueError("window_end is required for FIND_BEST date mode.")
            if self.duration_days is None:
                raise ValueError("duration_days is required for FIND_BEST date mode.")
        return self


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------


class TripBudget(BaseModel):
    """Budget specification for the trip."""

    model_config = ConfigDict(frozen=True)

    mode: BudgetMode = Field(
        default=BudgetMode.TOTAL,
        description="Whether the amount is for the whole trip (TOTAL) or per-person (PER_PERSON).",
    )
    amount_inr: Annotated[
        float,
        Field(
            ge=1000.0,
            description=(
                "Budget amount in Indian Rupees (INR). "
                "Must be ≥ ₹1,000. Covers all-inclusive costs "
                "(transport, accommodation, food, visa, activities, misc)."
            ),
        ),
    ]

    def total_budget_inr(self, party: TripParty) -> float:
        """Return the total trip budget normalised to INR for the full party.

        If ``mode`` is ``PER_PERSON``, multiplies by total traveler count.
        """
        if self.mode == BudgetMode.PER_PERSON:
            return self.amount_inr * party.total_travelers
        return self.amount_inr


# ---------------------------------------------------------------------------
# Food preferences
# ---------------------------------------------------------------------------


class FoodPreferences(BaseModel):
    """Food-related preferences that influence restaurant selection and itinerary shaping."""

    model_config = ConfigDict(frozen=True)

    importance: FoodImportance = Field(
        default=FoodImportance.MEDIUM,
        description="How strongly food drives scheduling and route decisions.",
    )
    dietary_preference: str | None = Field(
        default=None,
        description=(
            "Primary dietary regime, e.g. 'vegetarian', 'vegan', 'halal', "
            "'jain', 'kosher', or None for no restriction."
        ),
    )
    allergies: list[str] = Field(
        default_factory=list,
        description=(
            "List of food allergens to avoid, e.g. ['nuts', 'shellfish', 'gluten']. "
            "Treated as a constraint. Note: cross-contamination must be confirmed "
            "with the establishment directly."
        ),
    )
    foods_to_avoid: list[str] = Field(
        default_factory=list,
        description=(
            "Foods or ingredients the traveler prefers to avoid (non-allergy preference), "
            "e.g. ['pork', 'raw fish']."
        ),
    )
    desired_experiences: list[str] = Field(
        default_factory=list,
        description=(
            "Specific food experiences the traveler wants to include, "
            "e.g. ['street food', 'fine dining', 'cooking class', 'local market']."
        ),
    )


# ---------------------------------------------------------------------------
# Previous international travel (visa context)
# ---------------------------------------------------------------------------


class PreviousTravelEntry(BaseModel):
    """A single previously visited country entry used as visa context.

    This information is contextual and does not replace current visa verification.
    """

    model_config = ConfigDict(frozen=True)

    country_code: str = Field(
        description="ISO 3166-1 alpha-2 country code of the previously visited country."
    )
    country_name: str | None = Field(default=None, description="Optional human-readable name.")
    travel_year: int | None = Field(
        default=None,
        ge=1990,
        description="Approximate year of travel.",
    )
    visa_type: str | None = Field(
        default=None,
        description="Visa type used for that visit, e.g. 'Tourist', 'Business', 'Student'.",
    )
    visa_still_valid: bool | None = Field(
        default=None,
        description="Whether the visa from that visit is believed to still be valid.",
    )


# ---------------------------------------------------------------------------
# Top-level trip context
# ---------------------------------------------------------------------------


class TripContext(BaseModel):
    """Full trip planning input — the canonical entry contract for the planning graph.

    Aggregates all user-specified constraints and preferences validated before
    being passed to the LangGraph intake node.

    Constraints
    -----------
    - ``scope`` must be DOMESTIC or INTERNATIONAL.
    - Mixed domestic + international in a single request is not supported in V1.
    - ``destinations`` must contain at least one entry.
    - For DOMESTIC trips, destinations are Indian state/UT names or city names.
    - For INTERNATIONAL trips, destinations are country names or ISO-2 codes.
    """

    model_config = ConfigDict(frozen=True)

    # Identity
    origin: Annotated[
        str,
        Field(
            min_length=2,
            max_length=100,
            description=(
                "Starting city or IATA airport code in India "
                "(e.g. 'Delhi', 'DEL', 'Mumbai', 'BOM')."
            ),
        ),
    ]
    destinations: Annotated[
        list[str],
        Field(
            min_length=1,
            description=(
                "One or more destination names. "
                "For DOMESTIC: Indian state/UT or city names. "
                "For INTERNATIONAL: country names or ISO-2 codes."
            ),
        ),
    ]
    scope: TravelScope = Field(
        description="DOMESTIC for trips within India; INTERNATIONAL for trips outside India."
    )

    # Party
    party: TripParty = Field(description="Traveler group (adults + optional children).")

    # Dates
    dates: TripDates = Field(description="Travel date specification (exact, flexible, or window).")

    # Budget
    budget: TripBudget = Field(description="Budget specification in INR.")

    # Preferences
    travel_style: TravelStyle = Field(
        default=TravelStyle.COMFORTABLE,
        description="Broad accommodation/transport quality preference.",
    )
    pace: Pace = Field(
        default=Pace.BALANCED,
        description="Day-level activity density (RELAXED / BALANCED / PACKED).",
    )
    activity_preferences: list[str] = Field(
        default_factory=list,
        description=(
            "Activity category preferences, e.g. ['history', 'nature', 'food experiences', "
            "'adventure', 'beaches', 'museums', 'architecture', 'nightlife', 'shopping']."
        ),
    )
    must_visits: list[str] = Field(
        default_factory=list,
        description=(
            "Specific attractions or places that are high-priority for the traveler. "
            "May be omitted only if fulfilling them is genuinely infeasible within constraints."
        ),
    )
    food: FoodPreferences = Field(
        default_factory=FoodPreferences,
        description=(
            "Food preferences including importance, dietary needs, and desired experiences."
        ),
    )

    # International context
    previous_travel: list[PreviousTravelEntry] = Field(
        default_factory=list,
        description=(
            "Previously visited countries (contextual visa information). "
            "Only relevant for INTERNATIONAL trips."
        ),
    )

    @model_validator(mode="after")
    def _validate_scope_constraints(self) -> TripContext:
        # At least one destination always required (enforced by min_length=1 above)
        # For domestic trips, previous_travel is irrelevant but not an error.
        return self


# ---------------------------------------------------------------------------
# Intake & Planning State Models
# ---------------------------------------------------------------------------


class ResolvedLocation(BaseModel):
    """Geographically and statically resolved location or passenger gateway.

    Produced by the intake node to normalize origins and destinations
    with canonical coordinates, gateway airport, and country metadata.
    """

    model_config = ConfigDict(frozen=True)

    query: str = Field(description="Original user-specified location string.")
    name: str = Field(description="Canonical resolved name of the airport, city, or country.")
    city: str | None = Field(default=None, description="City or municipality if known.")
    country_code: str = Field(description="ISO 3166-1 alpha-2 country code.")
    country_name: str | None = Field(default=None, description="Full English country name.")
    iata_code: str | None = Field(
        default=None,
        description="Primary commercial passenger airport IATA code if available.",
    )
    latitude: float = Field(description="Latitude coordinate.")
    longitude: float = Field(description="Longitude coordinate.")
    is_schengen: bool = Field(
        default=False,
        description="Whether location is within the Schengen Area.",
    )
    ist_offset_hours: float = Field(
        default=0.0,
        description="Timezone difference in hours relative to IST.",
    )


class InitialPlanningState(BaseModel):
    """The canonical initial state created by the intake node.

    Conforms to the TravelPlannerState contract in architecture.md (Section 16).
    """

    model_config = ConfigDict(frozen=True)

    trip_context: TripContext = Field(description="Validated user trip context.")
    travel_scope: TravelScope = Field(
        description="Resolved travel scope (DOMESTIC or INTERNATIONAL)."
    )
    origin: ResolvedLocation = Field(description="Resolved departure airport/location.")
    destinations: list[ResolvedLocation] = Field(
        min_length=1,
        description="Resolved destination locations/gateways in visit order.",
    )
    route: list[str] = Field(
        min_length=2,
        description="Sequence of airport/city waypoint codes from origin back to origin.",
    )
    effective_duration_days: int = Field(
        ge=1,
        description="Calculated duration of the trip in days.",
    )
    total_budget_inr: float = Field(
        gt=0,
        description="Total budget in INR for the entire party.",
    )
    daily_budget_per_person_inr: float = Field(
        gt=0,
        description="Daily budget ceiling per person in INR.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings or advisory notices.",
    )
