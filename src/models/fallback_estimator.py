"""Domain contracts for the LLM Fallback Estimator tool.

Provides structured data models for requesting and receiving numerical
cost estimations when live API tools return incomplete cost figures.
"""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class CostCategory(StrEnum):
    """Cost estimation category classification."""

    HOTEL = "HOTEL"
    TRANSPORT = "TRANSPORT"
    FOOD = "FOOD"
    ACTIVITY = "ACTIVITY"
    MISC = "MISC"
    TOTAL_BUDGET = "TOTAL_BUDGET"


class TravelTier(StrEnum):
    """Travel budget tier classification."""

    BUDGET = "BUDGET"
    MID_RANGE = "MID_RANGE"
    LUXURY = "LUXURY"


class EstimateRequest(BaseModel):
    """Input contract for requesting a cost estimation."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    destination: Annotated[
        str, Field(min_length=1, description="Target destination city or region name")
    ]
    category: Annotated[CostCategory | str, Field(description="Cost category to estimate")]
    tier: Annotated[
        TravelTier | str,
        Field(default="MID_RANGE", description="Budget tier: BUDGET, MID_RANGE, or LUXURY"),
    ]
    duration_days: Annotated[int, Field(default=1, ge=1, description="Trip duration in days")]
    num_travelers: Annotated[int, Field(default=1, ge=1, description="Number of travelers")]
    currency: Annotated[str, Field(default="INR", description="Target currency ISO code")]
    context_notes: Annotated[
        str | None,
        Field(default=None, description="Optional context notes (e.g. '3-star hotel')"),
    ]


class FallbackEstimateResult(BaseModel):
    """Output contract containing structured numerical cost estimation and provenance."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    destination: str
    category: str
    tier: str
    estimated_cost_inr: Annotated[
        float, Field(ge=0.0, description="Point estimate of total cost in INR")
    ]
    min_cost_inr: Annotated[float, Field(ge=0.0, description="Minimum estimated cost range in INR")]
    max_cost_inr: Annotated[float, Field(ge=0.0, description="Maximum estimated cost range in INR")]
    currency: str = "INR"
    confidence_score: Annotated[
        float, Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    ]
    reasoning: Annotated[
        str, Field(min_length=1, description="Explanation/assumptions behind cost estimate")
    ]
    provider_used: str
    model_used: str
    is_fallback: bool = True
    is_estimated: bool = True
    timestamp: str
