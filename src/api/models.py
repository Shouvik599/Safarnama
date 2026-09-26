"""API Request and Response Models for Safarnama FastAPI Service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from src.models.itinerary import FinalItinerary
from src.models.trip import (
    BudgetMode,
    DateMode,
    FoodPreferences,
    Pace,
    TravelScope,
    TravelStyle,
    TripBudget,
    TripContext,
    TripDates,
    TripParty,
)


class HealthResponse(BaseModel):
    """Health check status response model."""

    status: str = "ok"
    version: str = "0.1.0"
    service: str = "Safarnama API"
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ToolStatusItem(BaseModel):
    """Individual tool capability status model."""

    tool: str
    status: str  # e.g., "available", "configured", "fixture_mode"
    provider: str
    details: dict[str, Any] | None = None


class ToolStatusResponse(BaseModel):
    """Aggregate tool layer status response model."""

    status: str = "ok"
    tools: dict[str, ToolStatusItem]
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class EstimateRequest(BaseModel):
    """Request model for quick cost estimation endpoint."""

    destination: str = Field(..., min_length=2, description="Target destination or country")
    category: str = Field(
        default="hotel",
        description="Cost category: hotel, transport, food, activity, misc",
    )
    hotel_stars: int | None = Field(default=3, ge=1, le=5)
    nights: int | None = Field(default=1, ge=1)
    travelers: int | None = Field(default=1, ge=1)
    budget_tier: str | None = Field(default="moderate", description="budget, moderate, luxury")


class EstimateResponse(BaseModel):
    """Response model for cost estimation endpoint."""

    destination: str
    category: str
    estimated_cost_inr: float
    is_estimated: bool = True
    confidence: float = 0.8
    explanation: str
    provider: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PlanPreviewRequest(BaseModel):
    """Request model for lightweight trip plan preview endpoint."""

    origin: str = Field(
        ..., min_length=2, description="Origin city or IATA airport code (e.g. DEL, Mumbai)"
    )
    destination: str = Field(
        ..., min_length=2, description="Destination city or country (e.g. Japan, France, Goa)"
    )
    duration_days: int = Field(default=5, ge=1, le=60)
    num_travelers: int = Field(default=2, ge=1, le=20)
    budget_inr: float = Field(default=100000.0, ge=1000.0)
    travel_style: str | None = Field(default="balanced")


class PlanPreviewResponse(BaseModel):
    """Response model for trip plan preview endpoint."""

    status: str = "preview"
    origin_airport: dict[str, Any] | None = None
    destination_country: dict[str, Any] | None = None
    travel_scope: str = Field(..., description="DOMESTIC or INTERNATIONAL")
    visa_summary: dict[str, Any] | None = None
    estimated_baseline_cost_inr: float
    budget_variance: dict[str, Any]
    weather_preview: dict[str, Any] | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class APIErrorResponse(BaseModel):
    """Standardized API error response model."""

    detail: str
    error_type: str
    status_code: int
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PlanRequest(BaseModel):
    """Request model for end-to-end trip planning endpoint (POST /api/v1/plan)."""

    trip_context: TripContext | None = None

    origin: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Starting Indian city or airport code (e.g. 'Delhi', 'DEL', 'Mumbai').",
    )
    destinations: list[str] | None = Field(
        default=None,
        min_length=1,
        description="List of destination cities or regions (e.g. ['Goa']).",
    )
    start_date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Trip departure date (YYYY-MM-DD).",
    )
    end_date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Trip return date (YYYY-MM-DD).",
    )
    duration_days: int | None = Field(
        default=None,
        ge=1,
        le=60,
        description="Trip duration in days (inferred from dates if omitted).",
    )
    adults: int = Field(default=2, ge=1, le=50, description="Number of adult travelers.")
    children: int = Field(default=0, ge=0, le=20, description="Number of child travelers.")
    budget_inr: float = Field(
        default=60000.0,
        ge=1000.0,
        description="Total trip budget in Indian Rupees (INR).",
    )
    budget_mode: str = Field(
        default="TOTAL",
        description="Budget allocation mode: 'TOTAL' or 'PER_PERSON'.",
    )
    travel_style: str = Field(
        default="COMFORTABLE",
        description="Travel comfort style: 'BUDGET', 'COMFORTABLE', 'PREMIUM', 'LUXURY'.",
    )
    pace: str = Field(
        default="BALANCED",
        description="Itinerary activity pace: 'RELAXED', 'BALANCED', 'PACKED'.",
    )
    activity_preferences: list[str] = Field(
        default_factory=list,
        description="Preferred activity tags, e.g. ['beaches', 'culture'].",
    )
    must_visits: list[str] = Field(
        default_factory=list,
        description="Mandatory places or attractions to include.",
    )
    dietary_preference: str | None = Field(
        default=None,
        description="Dietary requirements (e.g. 'vegetarian', 'vegan', 'halal').",
    )
    scope: str | None = Field(
        default=None,
        description=(
            "Travel scope: 'DOMESTIC' or 'INTERNATIONAL'. "
            "If omitted, auto-detected from destinations."
        ),
    )

    @model_validator(mode="after")
    def validate_request_completeness(self) -> PlanRequest:
        if self.trip_context is not None:
            return self
        if not self.origin:
            raise ValueError("'origin' is required when 'trip_context' is not supplied.")
        if not self.destinations:
            raise ValueError("'destinations' is required when 'trip_context' is not supplied.")
        if not self.start_date:
            raise ValueError("'start_date' is required when 'trip_context' is not supplied.")
        if not self.end_date:
            raise ValueError("'end_date' is required when 'trip_context' is not supplied.")
        return self

    def to_trip_context(self) -> TripContext:
        """Convert validated request into canonical TripContext domain model."""
        if self.trip_context is not None:
            return self.trip_context

        party = TripParty(adults=self.adults, children=self.children)
        dates = TripDates(
            mode=DateMode.EXACT,
            start_date=self.start_date,
            end_date=self.end_date,
            duration_days=self.duration_days,
        )
        b_mode = (
            BudgetMode.PER_PERSON if self.budget_mode.upper() == "PER_PERSON" else BudgetMode.TOTAL
        )
        budget = TripBudget(mode=b_mode, amount_inr=self.budget_inr)
        food = FoodPreferences(dietary_preference=self.dietary_preference)
        t_style = TravelStyle(self.travel_style.upper())
        t_pace = Pace(self.pace.upper())

        if self.scope:
            t_scope = TravelScope(self.scope.upper())
        else:
            is_intl = False
            try:
                from src.nodes.intake_node import resolve_location

                for dest in self.destinations or []:
                    dest_clean = dest.strip()
                    loc = resolve_location(dest_clean, is_origin=False)
                    if loc.country_code != "IN":
                        is_intl = True
                        break
            except Exception:
                pass
            t_scope = TravelScope.INTERNATIONAL if is_intl else TravelScope.DOMESTIC

        return TripContext(
            origin=self.origin or "",
            destinations=self.destinations or [],
            scope=t_scope,
            party=party,
            dates=dates,
            budget=budget,
            travel_style=t_style,
            pace=t_pace,
            activity_preferences=self.activity_preferences,
            must_visits=self.must_visits,
            food=food,
        )


class PlanResponse(BaseModel):
    """Response model for the primary trip planning endpoint."""

    status: str = Field(
        ...,
        description="Plan execution status (e.g. COMPLETED, NEEDS_USER_DECISION, INFEASIBLE).",
    )
    itinerary: FinalItinerary = Field(
        ...,
        description="Synthesized end-to-end trip itinerary artifact.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Aggregated planning warnings across all nodes.",
    )
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
