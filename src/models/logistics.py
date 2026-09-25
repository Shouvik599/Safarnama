"""Domain models for logistics planning output.

Defines the structured contracts for transportation and accommodation data
produced by the Logistics Node and consumed by the Optimizer and final
itinerary formatter.

Model hierarchy
---------------
``TransportLeg``
    A single transport segment in the planned route (extends ``TransportSegment``
    semantics but stays in the domain layer, independent of the tool layer).

``HotelStay``
    A planned accommodation stay at one destination for a set of nights.

``LogisticsPlan``
    Aggregate of all transport legs and hotel stays covering the full trip.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Transport leg (domain layer)
# ---------------------------------------------------------------------------


class TransportLeg(BaseModel):
    """One transport segment in the planned trip route.

    Represents a concrete booked/recommended transport option that the
    Logistics Node has selected from available tool results. Carries
    provenance so the final itinerary can label live vs. estimated fares.
    """

    model_config = ConfigDict(frozen=True)

    leg_number: Annotated[
        int, Field(ge=1, description="Sequential leg index within the overall route (1-indexed).")
    ]
    mode: str = Field(description="Transport mode: 'FLIGHT', 'TRAIN', 'BUS', or 'OTHER'.")
    carrier: str = Field(
        description="Operator name, e.g. 'IndiGo', 'Vande Bharat Express', 'Eurostar'."
    )
    transport_code: str | None = Field(
        default=None,
        description="Flight number, train number, or service code (e.g. '6E-204', '20901').",
    )
    origin: str = Field(description="Origin location label (city, IATA code, or station code).")
    destination: str = Field(
        description="Destination location label (city, IATA code, or station code)."
    )
    departure_datetime: str | None = Field(
        default=None,
        description="Scheduled departure as ISO 8601 datetime or YYYY-MM-DD HH:MM string.",
    )
    arrival_datetime: str | None = Field(
        default=None,
        description="Scheduled arrival as ISO 8601 datetime or YYYY-MM-DD HH:MM string.",
    )
    duration_minutes: int | None = Field(
        default=None,
        ge=0,
        description="Total journey duration in minutes.",
    )
    cabin_class: str = Field(
        default="ECONOMY",
        description="Travel class, e.g. 'ECONOMY', 'BUSINESS', '3A', '2A', '1A', 'CC'.",
    )
    price_per_person_inr: float = Field(
        ge=0.0, description="Per-person ticket cost in Indian Rupees (INR)."
    )
    total_price_inr: float = Field(
        ge=0.0, description="Total cost for all travelers on this leg in INR."
    )
    booking_url: str | None = Field(
        default=None, description="Optional direct booking or provider URL."
    )
    provider: str = Field(
        description=(
            "Data source for this leg: 'sky-scraper', 'flights-sky', 'aviationstack', "
            "'indian-railway-irctc', 'erail', 'transport.rest', 'transitland', "
            "'web-search', 'fixture', or 'physics-heuristic'."
        )
    )
    is_estimated: bool = Field(
        default=False,
        description="True if the price was derived from an offline heuristic or LLM estimate.",
    )
    notes: str | None = Field(
        default=None,
        description="Practical notes, e.g. 'Book 30 days in advance for best fares'.",
    )


# ---------------------------------------------------------------------------
# Hotel stay (domain layer)
# ---------------------------------------------------------------------------


class HotelStay(BaseModel):
    """A planned accommodation stay at one destination.

    Selected by the Logistics Node from live hotel search results.
    """

    model_config = ConfigDict(frozen=True)

    destination: str = Field(description="City or locality where this hotel is located.")
    hotel_name: str = Field(description="Name of the selected hotel or accommodation.")
    star_rating: int | None = Field(
        default=None, ge=1, le=5, description="Star classification (1–5 stars)."
    )
    user_rating: float | None = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Guest review score (e.g. 8.5/10 or 4.4/5).",
    )
    checkin_date: str = Field(description="Check-in date in YYYY-MM-DD format.")
    checkout_date: str = Field(description="Check-out date in YYYY-MM-DD format.")
    nights: Annotated[int, Field(ge=1, description="Number of nights.")]
    rooms_required: Annotated[int, Field(ge=1, description="Number of rooms booked.")]
    price_per_room_per_night_inr: float = Field(ge=0.0, description="Nightly per-room cost in INR.")
    total_accommodation_cost_inr: float = Field(
        ge=0.0,
        description="Total accommodation cost: price_per_room_per_night × nights × rooms.",
    )
    amenities: list[str] = Field(
        default_factory=list,
        description="Available amenities, e.g. ['Wi-Fi', 'Pool', 'Breakfast'].",
    )
    address: str | None = Field(default=None, description="Hotel address or vicinity.")
    booking_url: str | None = Field(default=None, description="Direct booking/reservation link.")
    provider: str = Field(
        description=(
            "Data source: 'serpapi-google-hotels', 'booking-com', 'tripadvisor', "
            "'nominatim-osm', 'web-search', 'fixture', or 'location-heuristic'."
        )
    )
    is_estimated: bool = Field(
        default=False,
        description="True if pricing was derived from a location heuristic or LLM estimate.",
    )
    notes: str | None = Field(default=None, description="Optional booking or location notes.")


# ---------------------------------------------------------------------------
# Logistics plan (aggregate)
# ---------------------------------------------------------------------------


class LogisticsPlan(BaseModel):
    """Aggregate logistics plan for the complete trip.

    Produced by the Logistics Node and consumed by the Optimizer.
    Contains all transport legs and hotel stays, plus aggregate cost totals.
    """

    model_config = ConfigDict(frozen=True)

    transport_legs: list[TransportLeg] = Field(
        default_factory=list,
        description=(
            "Ordered list of transport segments covering the full route "
            "(origin → destinations → return if applicable)."
        ),
    )
    hotel_stays: list[HotelStay] = Field(
        default_factory=list,
        description="Accommodation stays in chronological order, one entry per destination.",
    )

    # Aggregate cost totals (INR)
    total_transport_cost_inr: float = Field(
        default=0.0, ge=0.0, description="Sum of all transport leg costs for all travelers."
    )
    total_accommodation_cost_inr: float = Field(
        default=0.0, ge=0.0, description="Sum of all hotel stay costs."
    )

    # Plan metadata
    route_summary: str | None = Field(
        default=None,
        description=(
            "Human-readable route description, e.g. 'Delhi → Goa (flight) → Delhi (flight)'."
        ),
    )
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Non-fatal logistics warnings, e.g. 'Hotel price estimated — live data unavailable', "
            "'No direct train found; physics-heuristic used for duration'."
        ),
    )
    is_estimated: bool = Field(
        default=False,
        description="True if any cost component relied on fallback estimation.",
    )
    timestamp: str = Field(description="ISO 8601 timestamp when this logistics plan was generated.")
