"""Domain models for trip budget breakdown and optimization status.

Implements the financial contracts used by the deterministic Budget Engine and
Optimizer Node. All arithmetic happens in ``src/tools/calculator.py`` using
Python ``Decimal``; these models hold the results.

Model hierarchy
---------------
``BudgetStatus``
    Enum: UNDER_BUDGET / EXACT / MINOR_OVER / SIGNIFICANT_OVER / INFEASIBLE.

``OptimizationAction``
    Enum representing which type of automatic optimization was applied.

``CostBreakdown``
    Itemized trip cost across all categories (transport, accommodation, food, etc.).

``ContingencyConfig``
    Dynamic contingency parameters and final computed amount.

``BudgetVariance``
    Comparison of projected total vs. user budget with an actionable status.

``OptimizationResult``
    Record of what automatic optimization was attempted/applied.

``BudgetBreakdown``
    Top-level aggregate produced by the Budget Engine covering cost breakdown,
    contingency, variance, and optimization result.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class BudgetStatus(StrEnum):
    """Outcome of comparing projected trip cost to user budget.

    UNDER_BUDGET
        Projected cost is at or below the user's budget.
    EXACT
        Projected cost equals the budget (within ₹1 rounding tolerance).
    MINOR_OVER
        Projected cost is 0–5 % over budget. Minor automatic optimization may apply.
    SIGNIFICANT_OVER
        Projected cost is 5–15 % over budget. User-visible trade-off presentation required.
    INFEASIBLE
        Projected cost is >15 % over budget. Explain infeasibility; present alternatives.
    """

    UNDER_BUDGET = "UNDER_BUDGET"
    EXACT = "EXACT"
    MINOR_OVER = "MINOR_OVER"
    SIGNIFICANT_OVER = "SIGNIFICANT_OVER"
    INFEASIBLE = "INFEASIBLE"


class OptimizationAction(StrEnum):
    """Type of budget optimization that was applied or recommended."""

    NONE = "NONE"
    CHEAPER_HOTEL = "CHEAPER_HOTEL"
    CHEAPER_TRANSPORT = "CHEAPER_TRANSPORT"
    CHEAPER_ACTIVITIES = "CHEAPER_ACTIVITIES"
    LOWER_FOOD_BUDGET = "LOWER_FOOD_BUDGET"
    MULTIPLE_MINOR = "MULTIPLE_MINOR"
    USER_DECISION_REQUIRED = "USER_DECISION_REQUIRED"
    INFEASIBLE = "INFEASIBLE"


# ---------------------------------------------------------------------------
# Cost breakdown
# ---------------------------------------------------------------------------


class CostBreakdown(BaseModel):
    """Itemized trip cost across all spend categories in INR.

    All values are the deterministic totals computed by ``src/tools/calculator.py``.
    The LLM must not set or modify any field in this model.
    """

    model_config = ConfigDict(frozen=True)

    # Main cost components (INR)
    transport_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Total main transport cost (flights/trains/buses) for all travelers in INR.",
    )
    accommodation_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Total accommodation cost (hotel stays) for all nights in INR.",
    )
    local_transport_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Total in-destination local transport cost (taxis, metro, auto) in INR.",
    )
    activities_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Total attractions and activities cost for all travelers in INR.",
    )
    food_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Total estimated food/dining cost for all travelers across all days in INR.",
    )
    visa_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Total visa fees for all travelers in INR (0.0 for domestic trips).",
    )
    misc_inr: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Miscellaneous estimated costs (travel insurance, SIM cards, tips, etc.) in INR."
        ),
    )

    # Provenance flags
    has_estimated_components: bool = Field(
        default=False,
        description=(
            "True if any cost component relied on fallback estimation "
            "(e.g. LLM estimate or physics heuristic)."
        ),
    )

    @property
    def subtotal_inr(self) -> float:
        """Sum of all itemized costs before contingency."""
        return (
            self.transport_inr
            + self.accommodation_inr
            + self.local_transport_inr
            + self.activities_inr
            + self.food_inr
            + self.visa_inr
            + self.misc_inr
        )


# ---------------------------------------------------------------------------
# Contingency configuration
# ---------------------------------------------------------------------------


class ContingencyConfig(BaseModel):
    """Dynamic contingency parameters used by the budget engine.

    The contingency percentage is not a fixed 10% — it depends on trip
    complexity, scope, data quality, and uncertainty factors.
    """

    model_config = ConfigDict(frozen=True)

    percentage: float = Field(
        ge=0.0,
        le=50.0,
        description=(
            "Applied contingency percentage (e.g. 10.0 for 10%). "
            "Ranges from ~5% (simple domestic) to ~20%+ (complex multi-country international)."
        ),
    )
    amount_inr: float = Field(
        ge=0.0, description="Contingency amount in INR (subtotal × percentage / 100)."
    )
    reasoning: str | None = Field(
        default=None,
        description=(
            "Brief explanation of why this percentage was chosen, "
            "e.g. 'International 2-country trip with estimated hotel pricing (+15%)'."
        ),
    )

    # Factors that influenced the percentage
    is_international: bool = Field(default=False, description="Trip has international scope.")
    country_count: int = Field(default=1, ge=1, description="Number of destination countries.")
    has_estimated_prices: bool = Field(
        default=False, description="True if any price components are estimated."
    )
    has_flexible_dates: bool = Field(
        default=False, description="True if dates are flexible or best-date-search mode."
    )


# ---------------------------------------------------------------------------
# Budget variance
# ---------------------------------------------------------------------------


class BudgetVariance(BaseModel):
    """Comparison of projected total cost to the user's requested budget.

    Computed deterministically by the budget engine; not by the LLM.
    """

    model_config = ConfigDict(frozen=True)

    user_budget_inr: float = Field(ge=0.0, description="User's total budget in INR.")
    projected_total_inr: float = Field(
        ge=0.0,
        description="Projected total cost including contingency.",
    )
    variance_inr: float = Field(
        description=(
            "Difference: projected_total_inr − user_budget_inr. "
            "Negative means under budget; positive means over."
        )
    )
    variance_percentage: float = Field(
        description=(
            "Variance as a percentage of user_budget_inr. "
            "Negative = under budget; positive = over budget."
        )
    )
    status: BudgetStatus = Field(description="Actionable budget status classification.")

    @model_validator(mode="after")
    def _validate_consistency(self) -> BudgetVariance:
        # Verify variance calculation is internally consistent (within ₹1 tolerance)
        expected_variance = self.projected_total_inr - self.user_budget_inr
        if abs(expected_variance - self.variance_inr) > 1.0:
            raise ValueError(
                f"variance_inr {self.variance_inr:.2f} is inconsistent with "
                f"projected_total_inr {self.projected_total_inr:.2f} - "
                f"user_budget_inr {self.user_budget_inr:.2f} = {expected_variance:.2f}"
            )
        return self


# ---------------------------------------------------------------------------
# Optimization result
# ---------------------------------------------------------------------------


class OptimizationResult(BaseModel):
    """Record of what budget optimization was applied (if any).

    The Optimizer Node populates this after evaluating the BudgetVariance.
    Hard quality guardrails from ``rules.md`` must not be violated by any
    automatic optimization.
    """

    model_config = ConfigDict(frozen=True)

    action: OptimizationAction = Field(
        default=OptimizationAction.NONE,
        description="The primary optimization action taken or recommended.",
    )
    savings_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="Cost reduction achieved by automatic optimization in INR.",
    )
    description: str | None = Field(
        default=None,
        description=(
            "Human-readable description of what was changed, "
            "e.g. 'Switched to 3-star hotel saving ₹4,200 per night'."
        ),
    )
    trade_offs: list[str] = Field(
        default_factory=list,
        description=(
            "List of meaningful trade-offs the user should be aware of, "
            "e.g. 'Hotel is further from city centre', 'Economy class instead of Business'."
        ),
    )
    alternatives_presented: list[str] = Field(
        default_factory=list,
        description=(
            "Alternative plan options presented to the user for SIGNIFICANT_OVER or INFEASIBLE "
            "scenarios, e.g. ['Reduce trip by 2 days', 'Remove one destination', 'Budget hotels']."
        ),
    )
    guardrails_respected: bool = Field(
        default=True,
        description=(
            "True if all hard quality guardrails were maintained during optimization. "
            "Must-visits were not silently removed; pace was not materially violated."
        ),
    )


# ---------------------------------------------------------------------------
# Top-level budget breakdown
# ---------------------------------------------------------------------------


class BudgetBreakdown(BaseModel):
    """Complete budget result for the trip produced by the Budget Engine.

    Aggregates cost breakdown, contingency, variance, and optimization
    result into a single domain object carried in the LangGraph state.

    All arithmetic must have been performed by ``src/tools/calculator.py``
    using deterministic ``Decimal`` arithmetic, not by any LLM.
    """

    model_config = ConfigDict(frozen=True)

    cost_breakdown: CostBreakdown = Field(description="Itemized costs across all spend categories.")
    contingency: ContingencyConfig = Field(
        description="Contingency configuration and computed amount."
    )
    variance: BudgetVariance = Field(
        description="Comparison of projected total to user budget with actionable status."
    )
    optimization: OptimizationResult = Field(
        default_factory=OptimizationResult,
        description="Record of any budget optimization applied or recommended.",
    )

    # Convenience summary fields (derived, not calculated here)
    subtotal_inr: float = Field(
        ge=0.0,
        description=(
            "Sum of all cost components before contingency (equals cost_breakdown.subtotal_inr)."
        ),
    )
    total_with_contingency_inr: float = Field(
        ge=0.0,
        description=(
            "Final projected total including contingency (equals variance.projected_total_inr)."
        ),
    )
    per_person_cost_inr: float = Field(
        ge=0.0,
        description="Projected total divided by total traveler count.",
    )

    # Provenance
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Budget-level warnings, e.g. 'Visa fee estimated — verify before booking', "
            "'Hotel pricing based on heuristic'."
        ),
    )
    is_estimated: bool = Field(
        default=False,
        description="True if any cost component relied on fallback estimation.",
    )
    timestamp: str = Field(description="ISO 8601 timestamp when this budget was calculated.")
