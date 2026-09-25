"""Pydantic domain models for transport and route search functionality.

Provides structured, validated contracts for individual transport segments (flights,
trains, buses) and aggregated route search results consumed by Phase 3 tools,
Logistics planning nodes, and itinerary optimizers.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TransportSegment(BaseModel):
    """Structured segment for a single transport option (flight, train, or bus)."""

    mode: str = Field(description="Mode of transportation: 'FLIGHT', 'TRAIN', or 'BUS'.")
    carrier: str = Field(
        description="Operator/Carrier name (e.g. 'IndiGo', 'Vande Bharat Express', 'Eurostar')."
    )
    transport_code: str | None = Field(
        default=None, description="Flight or Train identifier code (e.g. '6E-204', '20901')."
    )
    origin: str = Field(description="Origin airport IATA code, railway station code, or city name.")
    destination: str = Field(
        description="Destination airport IATA code, railway station code, or city name."
    )
    departure_time: str = Field(description="Scheduled departure time or ISO timestamp.")
    arrival_time: str = Field(description="Scheduled arrival time or ISO timestamp.")
    duration_minutes: int = Field(ge=0, description="Total journey duration in minutes.")
    price_inr: float = Field(ge=0.0, description="Ticket fare converted to Indian Rupee (INR).")
    cabin_class: str = Field(
        default="ECONOMY",
        description="Travel class (e.g. 'ECONOMY', 'BUSINESS', '3A', '2A', '1A', 'CC').",
    )
    booking_url: str | None = Field(
        default=None, description="Optional direct booking or provider URL."
    )
    provider: str = Field(
        description=(
            "Provenance provider: 'sky-scraper', 'flights-sky', 'aviationstack', "
            "'indian-railway-irctc', 'erail', 'transport.rest', 'transitland', "
            "'web-search', 'fixture', or 'physics-heuristic'."
        )
    )


class TransportSearchResult(BaseModel):
    """Aggregated transport search result across multi-tier providers."""

    origin: str = Field(description="Query origin location.")
    destination: str = Field(description="Query destination location.")
    travel_date: str = Field(description="Requested travel date in YYYY-MM-DD format.")
    mode_requested: str = Field(
        default="ALL",
        description="Requested mode filter: 'ALL', 'FLIGHT', 'TRAIN', or 'BUS'.",
    )
    options: list[TransportSegment] = Field(
        default_factory=list, description="List of validated transport segments."
    )
    provider_used: str = Field(
        description="Name of the backend provider that successfully answered the request."
    )
    total_found: int = Field(default=0, description="Total number of transport options returned.")
    is_fallback: bool = Field(
        default=False,
        description="True if a secondary fallback provider, web search, or fixture was used.",
    )
    is_estimated: bool = Field(
        default=False,
        description="True if derived from offline distance & speed physics heuristic.",
    )
    timestamp: str = Field(description="ISO 8601 timestamp when this search was executed.")
