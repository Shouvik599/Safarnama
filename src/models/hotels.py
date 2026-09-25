"""Pydantic domain models for hotel and accommodation search functionality.

Provides structured, validated contracts for individual hotel options
and aggregated hotel search results consumed by Phase 3 tools,
Logistics planning nodes, and itinerary optimizers.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HotelOption(BaseModel):
    """Structured model for a single hotel/accommodation option."""

    hotel_id: str = Field(description="Unique identifier for the property.")
    name: str = Field(description="Name of the hotel or accommodation property.")
    destination: str = Field(description="City or region where the hotel is located.")
    star_rating: int | None = Field(
        default=None, ge=1, le=5, description="Star classification rating (1 to 5 stars)."
    )
    user_rating: float | None = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Guest review score (e.g. 8.5 out of 10 or 4.4 out of 5).",
    )
    reviews_count: int | None = Field(
        default=None, ge=0, description="Total number of guest reviews."
    )
    address: str = Field(description="Street address or vicinity location string.")
    latitude: float | None = Field(default=None, description="GPS latitude coordinate.")
    longitude: float | None = Field(default=None, description="GPS longitude coordinate.")
    price_per_night_inr: float = Field(
        ge=0.0, description="Nightly room rate in Indian Rupee (INR)."
    )
    total_price_inr: float | None = Field(
        default=None, ge=0.0, description="Total stay price for all requested nights."
    )
    amenities: list[str] = Field(
        default_factory=list,
        description="List of available amenities (e.g. ['Wi-Fi', 'Pool', 'Breakfast']).",
    )
    room_type: str = Field(
        default="Standard Room", description="Room category description."
    )
    thumbnail_url: str | None = Field(
        default=None, description="URL to main property image or thumbnail."
    )
    booking_url: str | None = Field(
        default=None, description="Direct booking or reservation link."
    )
    provider: str = Field(
        description=(
            "Provenance provider: 'serpapi-google-hotels', 'booking-com', "
            "'tripadvisor', 'nominatim-osm', 'web-search', 'fixture', or 'location-heuristic'."
        )
    )


class HotelSearchResult(BaseModel):
    """Aggregated hotel search result across multi-tier providers."""

    destination: str = Field(description="Query destination city or region.")
    checkin_date: str = Field(description="Requested check-in date in YYYY-MM-DD format.")
    checkout_date: str = Field(description="Requested check-out date in YYYY-MM-DD format.")
    nights: int = Field(ge=1, description="Total number of stay nights.")
    guests: int = Field(default=2, ge=1, description="Number of adult guests.")
    options: list[HotelOption] = Field(
        default_factory=list, description="List of validated hotel options."
    )
    provider_used: str = Field(
        description="Name of the backend provider that successfully answered the request."
    )
    total_found: int = Field(default=0, description="Total number of hotel options returned.")
    is_fallback: bool = Field(
        default=False,
        description="True if a secondary fallback provider, web search, or fixture was used.",
    )
    is_estimated: bool = Field(
        default=False,
        description="True if derived from location heuristic baseline.",
    )
    timestamp: str = Field(description="ISO 8601 timestamp when this search was executed.")
