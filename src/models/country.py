"""Pydantic domain models for country profile metadata.

Provides validated contracts for country metadata ingested from REST Countries v5
and consumed by Phase 2 static data tools (``src/tools/static_data.py``) and
downstream planning nodes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    """Geographic coordinates for a capital or reference location."""

    lat: float = Field(description="Latitude in decimal degrees.")
    lng: float = Field(description="Longitude in decimal degrees.")


class CurrencyInfo(BaseModel):
    """Currency information for a destination."""

    code: str = Field(description="ISO 4217 currency code, e.g. 'JPY', 'EUR', 'USD'.")
    name: str = Field(description="Full name of currency, e.g. 'Japanese yen'.")
    symbol: str = Field(default="", description="Currency symbol, e.g. '¥', '€', '$'.")


class LanguageInfo(BaseModel):
    """Official or recognized language in a destination."""

    code: str = Field(description="BCP-47 or ISO-639-1 language code, e.g. 'ja', 'en', 'fr'.")
    name: str = Field(description="English name of the language, e.g. 'Japanese'.")


class CountryProfile(BaseModel):
    """Canonical country profile for destination planning and metadata enrichment."""

    country_code: str = Field(
        description="ISO 3166-1 alpha-2 country code (uppercase 2 letters), e.g. 'JP'."
    )
    country_code_alpha3: str = Field(
        description="ISO 3166-1 alpha-3 country code (uppercase 3 letters), e.g. 'JPN'."
    )
    name: str = Field(description="Common English name of the country, e.g. 'Japan'.")
    official_name: str = Field(description="Official state name, e.g. 'Japan'.")
    capital: str | None = Field(
        default=None, description="Primary capital city name, e.g. 'Tokyo'."
    )
    capital_coordinates: Coordinates | None = Field(
        default=None, description="Coordinates of the primary capital."
    )
    region: str = Field(description="Global continent/region, e.g. 'Asia', 'Europe'.")
    subregion: str | None = Field(
        default=None, description="Geographic subregion, e.g. 'Eastern Asia'."
    )
    currencies: list[CurrencyInfo] = Field(
        default_factory=list, description="Currencies used in the country."
    )
    languages: list[LanguageInfo] = Field(
        default_factory=list, description="Recognized official languages."
    )
    timezones: list[str] = Field(
        default_factory=list, description="UTC timezone offsets, e.g. ['UTC+09:00']."
    )
    driving_side: str | None = Field(
        default=None, description="Road traffic driving side: 'left' or 'right'."
    )
    calling_code: str | None = Field(
        default=None, description="International telephone dialing code prefix, e.g. '+81'."
    )
    flag_emoji: str | None = Field(default=None, description="Unicode flag emoji, e.g. '🇯🇵'.")
    is_schengen: bool = Field(
        default=False, description="True if the country is a Schengen Area member state."
    )
    is_eu: bool = Field(default=False, description="True if the country is an EU member state.")
    borders: list[str] = Field(
        default_factory=list,
        description="List of neighboring country ISO 3166-1 alpha-3 codes.",
    )
    last_updated: str = Field(
        description="ISO-8601 date of the data ingestion run, e.g. '2026-09-25'."
    )
