"""Pydantic domain models for airport metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Airport(BaseModel):
    """Airport location and metadata record from ourairports-data."""

    iata_code: str = Field(description="3-letter IATA airport code (uppercase), e.g. 'DEL'.")
    type: str = Field(description="Airport classification, e.g. 'large_airport', 'medium_airport'.")
    name: str = Field(description="Official airport name.")
    municipality: str | None = Field(default=None, description="City or municipality served.")
    iso_country: str = Field(description="ISO 3166-1 alpha-2 country code (uppercase), e.g. 'IN'.")
    latitude_deg: float = Field(description="Geographic latitude in decimal degrees.")
    longitude_deg: float = Field(description="Geographic longitude in decimal degrees.")
