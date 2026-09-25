"""API Request and Response Models for Safarnama FastAPI Service."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


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
