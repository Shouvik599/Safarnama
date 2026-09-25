"""Pydantic domain models for places, attractions, and dining search functionality.

Provides structured, validated contracts for individual points of interest (sightseeing
attractions, museums, restaurants, cafes) and aggregated search results consumed by Phase 3 tools,
Logistics planning nodes, and itinerary optimizers.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlaceItem(BaseModel):
    """Structured model for a single point of interest (attraction or dining spot)."""

    place_id: str = Field(description="Unique identifier for the location or place.")
    name: str = Field(description="Name of the attraction, landmark, restaurant, or cafe.")
    destination: str = Field(description="City or region where the place is located.")
    category: str = Field(
        description="Category classification: 'ATTRACTION', 'RESTAURANT', or 'CAFE'."
    )
    rating: float | None = Field(
        default=None, ge=0.0, le=5.0, description="Average review score (0.0 to 5.0 stars)."
    )
    reviews_count: int | None = Field(
        default=None, ge=0, description="Total number of user reviews."
    )
    price_level: str | None = Field(
        default=None,
        description="Price indicator string (e.g. '$', '$$', '$$$', 'Free', 'Moderate').",
    )
    estimated_cost_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated entrance fee or average meal cost per person in INR.",
    )
    address: str = Field(description="Street address or location vicinity string.")
    latitude: float | None = Field(default=None, description="GPS latitude coordinate.")
    longitude: float | None = Field(default=None, description="GPS longitude coordinate.")
    description: str | None = Field(
        default=None, description="Brief summary or highlight description of the venue."
    )
    open_hours: str | None = Field(
        default=None, description="Opening hours status (e.g. 'Open now', '09:00 - 18:00')."
    )
    thumbnail_url: str | None = Field(
        default=None, description="URL to main place image or thumbnail."
    )
    maps_url: str | None = Field(
        default=None, description="Direct Google Maps or location web link."
    )
    provider: str = Field(
        description=(
            "Provenance provider: 'serpapi-google-maps', 'overpass-osm', 'nominatim-osm', "
            "'web-search', 'fixture', or 'category-heuristic'."
        )
    )


class PlacesSearchResult(BaseModel):
    """Aggregated places and dining search result across multi-tier providers."""

    destination: str = Field(description="Query destination city or region.")
    category_requested: str = Field(
        default="ALL",
        description="Requested category filter: 'ALL', 'ATTRACTION', 'RESTAURANT', or 'CAFE'.",
    )
    query: str | None = Field(default=None, description="Optional search query keyword.")
    items: list[PlaceItem] = Field(
        default_factory=list, description="List of validated PlaceItem records."
    )
    provider_used: str = Field(
        description="Name of the backend provider that successfully answered the request."
    )
    total_found: int = Field(default=0, description="Total number of places returned.")
    is_fallback: bool = Field(
        default=False,
        description="True if a secondary fallback provider, web search, or fixture was used.",
    )
    is_estimated: bool = Field(
        default=False,
        description="True if derived from category heuristic baseline.",
    )
    timestamp: str = Field(description="ISO 8601 timestamp when this search was executed.")
