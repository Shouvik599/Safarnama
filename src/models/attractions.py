"""Validated static attraction records generated from cited place research."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AttractionSource(BaseModel):
    """A Tavily result snippet supporting a curated attraction record."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(min_length=1, max_length=300)
    url: HttpUrl
    snippet: str = Field(min_length=1, max_length=1600)


class CuratedAttraction(BaseModel):
    """A stable attraction identity and the evidence used to include it."""

    model_config = ConfigDict(frozen=True)

    attraction_id: str = Field(min_length=3, max_length=180)
    name: str = Field(min_length=2, max_length=180)
    city: str = Field(min_length=2, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    country: str = Field(min_length=2, max_length=120)
    country_code: str = Field(pattern=r"^[A-Z]{2}$")
    category: Literal["ATTRACTION"] = "ATTRACTION"
    description: str = Field(min_length=8, max_length=500)
    sources: list[AttractionSource] = Field(min_length=1, max_length=5)
    retrieved_at: date


class AttractionCityCoverage(BaseModel):
    """Completed city lookup, including the successful no-results case."""

    model_config = ConfigDict(frozen=True)

    city: str = Field(min_length=2, max_length=120)
    country: str = Field(min_length=2, max_length=120)
    country_code: str = Field(pattern=r"^[A-Z]{2}$")
    status: Literal["SOURCE_BACKED", "NO_RESULTS"]
    checked_at: date


class AttractionCatalog(BaseModel):
    """Versioned, incrementally generated static POI catalog."""

    schema_version: Literal[1] = 1
    entries: list[CuratedAttraction] = Field(default_factory=list)
    coverage: list[AttractionCityCoverage] = Field(default_factory=list)


class AttractionCandidate(BaseModel):
    """Gemini response candidate; source indexes refer to supplied Tavily results."""

    name: str = Field(min_length=2, max_length=180)
    description: str = Field(min_length=8, max_length=500)
    source_indexes: list[int] = Field(min_length=1, max_length=5)


class AttractionCandidateBatch(BaseModel):
    """Structured Gemini response for one city search."""

    attractions: list[AttractionCandidate] = Field(default_factory=list, max_length=8)
