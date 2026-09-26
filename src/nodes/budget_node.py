"""Phase 10 — Deterministic Budget Engine (Budget Planning Node).

Calculates comprehensive, deterministic financial breakdowns and budget variance:
1. Aggregates itemized trip expenses across all spend categories:
   - Transport (flights, trains, buses) from LogisticsPlan.
   - Accommodation (hotel stays) from LogisticsPlan.
   - Activities & attractions from ExperiencePlan.
   - Food and dining experiences from ExperiencePlan.
   - In-destination local transit from ExperiencePlan.
   - Visa and entry fees from VisaVerdict.
   - Realistic miscellaneous costs (insurance, eSIM, incidentals) from deterministic rules.
2. Dynamically calculates contingency buffers based on trip scope, destination country count,
   pricing estimation uncertainty, and date flexibility.
3. Computes exact budget variance (projected total vs. user budget ceiling) and classifies
   the outcome into actionable status tiers: UNDER_BUDGET, EXACT, MINOR_OVER,
   SIGNIFICANT_OVER, and INFEASIBLE.
4. Deterministically computes per-person expense shares and tracks provenance/estimation flags.
5. Produces immutable, frozen BudgetBreakdown domain models conforming to domain contracts.

Architectural Constraints:
- 100% deterministic calculation; LLMs must NEVER perform arithmetic (Rule 10, Rule 27).
- All arithmetic operations execute via src/tools/calculator.py using Python Decimal.
- Internal consistency: variance_inr strictly matches (projected_total - user_budget) within ₹1.
- Zero external network reliance in unit tests.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from src.models.budget import (
    BudgetBreakdown,
    BudgetStatus,
    BudgetVariance,
    ContingencyConfig,
    CostBreakdown,
    OptimizationResult,
)
from src.models.itinerary import ExperiencePlan
from src.models.logistics import LogisticsPlan
from src.models.trip import (
    DateMode,
    InitialPlanningState,
    TravelScope,
    TripContext,
    TripParty,
)
from src.models.visa import VisaVerdict
from src.tools.calculator import (
    calculate_dynamic_contingency,
    calculate_miscellaneous_expenses,
    calculate_per_person_cost,
    classify_detailed_budget_status,
    round_currency,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class BudgetError(Exception):
    """Base exception for budget planning and calculation errors."""


class BudgetValidationError(BudgetError, ValueError):
    """Raised when budget inputs, states, or constraints are invalid."""


class BudgetCalculationError(BudgetError, RuntimeError):
    """Raised when deterministic budget calculation encounters an unrecoverable error."""


# ---------------------------------------------------------------------------
# Budget Planning Engine
# ---------------------------------------------------------------------------


def process_budget(
    state_or_context: InitialPlanningState | TripContext | dict[str, Any],
    logistics_plan: LogisticsPlan | None = None,
    experience_plan: ExperiencePlan | None = None,
    visa_verdict: VisaVerdict | None = None,
    misc_inr: float | None = None,
    custom_contingency_pct: float | None = None,
) -> BudgetBreakdown:
    """Calculate the deterministic budget breakdown and variance for a trip.

    Args:
        state_or_context: Planning state dictionary, InitialPlanningState, or TripContext.
        logistics_plan: Optional LogisticsPlan containing transport and accommodation costs.
        experience_plan: Optional ExperiencePlan containing activities, food, and transit costs.
        visa_verdict: Optional VisaVerdict containing visa fees and advance application metadata.
        misc_inr: Optional explicit miscellaneous expense override in INR.
        custom_contingency_pct: Optional custom contingency percentage override (e.g. 10.0 for 10%).

    Returns:
        Validated, immutable BudgetBreakdown domain model.

    Raises:
        BudgetValidationError: If context or required planning parameters are missing or invalid.
    """
    context: TripContext
    if isinstance(state_or_context, InitialPlanningState):
        context = state_or_context.trip_context
    elif isinstance(state_or_context, TripContext):
        context = state_or_context
    elif isinstance(state_or_context, dict):
        if "initial_state" in state_or_context and isinstance(
            state_or_context["initial_state"], InitialPlanningState
        ):
            context = state_or_context["initial_state"].trip_context
        elif "context" in state_or_context and isinstance(state_or_context["context"], TripContext):
            context = state_or_context["context"]
        elif "trip_context" in state_or_context and isinstance(
            state_or_context["trip_context"], TripContext
        ):
            context = state_or_context["trip_context"]
        else:
            raise BudgetValidationError(
                "State dictionary must contain 'initial_state', 'context', or 'trip_context'"
            )

        # Pull plans from state if not passed explicitly
        if logistics_plan is None:
            logistics_plan = state_or_context.get("logistics_plan")
        if experience_plan is None:
            experience_plan = state_or_context.get("experience_plan")
        if visa_verdict is None:
            visa_verdict = state_or_context.get("visa_verdict")
    else:
        raise BudgetValidationError(
            f"Unsupported state_or_context type: {type(state_or_context).__name__}"
        )

    party: TripParty = context.party
    total_travelers: int = party.total_travelers
    duration_days: int = max(1, context.dates.duration_days or 1)
    is_international: bool = context.scope == TravelScope.INTERNATIONAL
    country_count: int = max(1, len(context.destinations))

    warnings: list[str] = []

    # 1. Transport & Accommodation (Logistics)
    transport_inr = 0.0
    accommodation_inr = 0.0
    has_estimated_logistics = False

    if logistics_plan is not None:
        transport_inr = round_currency(logistics_plan.total_transport_cost_inr)
        accommodation_inr = round_currency(logistics_plan.total_accommodation_cost_inr)
        has_estimated_logistics = logistics_plan.is_estimated
    else:
        warnings.append(
            "Logistics plan omitted — transport and accommodation costs defaulted to ₹0"
        )

    # 2. Activities, Food & Local Transit (Experience)
    activities_inr = 0.0
    food_inr = 0.0
    local_transport_inr = 0.0
    has_estimated_experience = False

    if experience_plan is not None:
        activities_inr = round_currency(experience_plan.total_activity_cost_inr)
        food_inr = round_currency(experience_plan.total_food_cost_inr)
        local_transport_inr = round_currency(experience_plan.total_local_transport_cost_inr)
        has_estimated_experience = experience_plan.is_estimated
    else:
        warnings.append(
            "Experience plan omitted — activities, food, and local transit costs defaulted to ₹0"
        )

    # 3. Visa Fees (Visa)
    visa_inr = 0.0
    has_estimated_visa = False

    if is_international:
        if visa_verdict is not None:
            visa_inr = round_currency(visa_verdict.total_visa_cost_inr)
            has_estimated_visa = any(
                getattr(cv, "is_estimated", False) or getattr(cv, "confidence", "") == "LOW"
                for cv in visa_verdict.countries
            )
            if visa_verdict.requires_advance_application:
                warnings.append(
                    "Advance visa application required; ensure processing fees and appointment "
                    "logistics are accounted for"
                )
        else:
            warnings.append("International trip without visa verdict — visa costs defaulted to ₹0")
    else:
        visa_inr = 0.0

    # 4. Miscellaneous Costs
    if misc_inr is not None:
        computed_misc_inr = round_currency(misc_inr)
    else:
        computed_misc_inr = calculate_miscellaneous_expenses(
            is_international=is_international,
            total_travelers=total_travelers,
            duration_days=duration_days,
            adults=party.adults,
        )

    # 5. Composite Estimation Flag
    has_estimated_components = (
        has_estimated_logistics or has_estimated_experience or has_estimated_visa
    )
    if has_estimated_components:
        warnings.append(
            "One or more cost components relied on fallback estimation — verify actual live "
            "booking rates before final confirmation"
        )

    # 6. Itemized Cost Breakdown
    cost_breakdown = CostBreakdown(
        transport_inr=transport_inr,
        accommodation_inr=accommodation_inr,
        local_transport_inr=local_transport_inr,
        activities_inr=activities_inr,
        food_inr=food_inr,
        visa_inr=visa_inr,
        misc_inr=computed_misc_inr,
        has_estimated_components=has_estimated_components,
    )
    subtotal_inr = round_currency(cost_breakdown.subtotal_inr)

    # 7. Dynamic Contingency Buffer
    has_flexible_dates = context.dates.mode in (DateMode.FLEXIBLE, DateMode.FIND_BEST)

    if custom_contingency_pct is not None:
        contingency_pct = float(round_currency(custom_contingency_pct))
        contingency_amt = round_currency(subtotal_inr * (contingency_pct / 100.0))
        contingency_reasoning = f"User custom contingency buffer override ({contingency_pct:.1f}%)"
    else:
        contingency_pct, contingency_amt, contingency_reasoning = calculate_dynamic_contingency(
            subtotal=subtotal_inr,
            is_international=is_international,
            country_count=country_count,
            has_estimated_prices=has_estimated_components,
            has_flexible_dates=has_flexible_dates,
        )

    contingency = ContingencyConfig(
        percentage=contingency_pct,
        amount_inr=contingency_amt,
        reasoning=contingency_reasoning,
        is_international=is_international,
        country_count=country_count,
        has_estimated_prices=has_estimated_components,
        has_flexible_dates=has_flexible_dates,
    )

    # 8. Projected Total Cost
    projected_total_inr = round_currency(subtotal_inr + contingency.amount_inr)

    # 9. Budget Variance & Status Classification
    user_budget_inr = round_currency(context.budget.total_budget_inr(party))
    variance_inr = round_currency(projected_total_inr - user_budget_inr)

    if user_budget_inr > 0.0:
        variance_percentage = round_currency((variance_inr / user_budget_inr) * 100.0)
    else:
        variance_percentage = 0.0 if projected_total_inr == 0.0 else 100.0

    status_str = classify_detailed_budget_status(variance_inr, variance_percentage)
    status_enum = BudgetStatus(status_str)

    # Add actionable budget warnings matching status tiers
    if status_enum == BudgetStatus.MINOR_OVER:
        warnings.append(
            f"Projected cost exceeds user budget by {variance_percentage:.1f}% (<=5%) — "
            "eligible for automatic minor optimization in Phase 11"
        )
    elif status_enum == BudgetStatus.SIGNIFICANT_OVER:
        warnings.append(
            f"Projected cost exceeds user budget by {variance_percentage:.1f}% (5–15%) — "
            "user-visible trade-off decision required"
        )
    elif status_enum == BudgetStatus.INFEASIBLE:
        warnings.append(
            f"Projected cost exceeds user budget by {variance_percentage:.1f}% (>15%) — "
            "trip parameters are financially infeasible under current budget ceiling"
        )

    variance = BudgetVariance(
        user_budget_inr=user_budget_inr,
        projected_total_inr=projected_total_inr,
        variance_inr=variance_inr,
        variance_percentage=variance_percentage,
        status=status_enum,
    )

    # 10. Per-Person Cost
    per_person_cost_inr = calculate_per_person_cost(projected_total_inr, total_travelers)

    # 11. Top-Level Budget Breakdown Assembly
    breakdown = BudgetBreakdown(
        cost_breakdown=cost_breakdown,
        contingency=contingency,
        variance=variance,
        optimization=OptimizationResult(),
        subtotal_inr=subtotal_inr,
        total_with_contingency_inr=projected_total_inr,
        per_person_cost_inr=per_person_cost_inr,
        warnings=warnings,
        is_estimated=has_estimated_components,
        timestamp=datetime.now(UTC).isoformat(),
    )

    log.info(
        "Budget calculated: Subtotal=₹%0.2f, Buffer=₹%0.2f (%0.1f%%), Total=₹%0.2f, Status=%s",
        subtotal_inr,
        contingency_amt,
        contingency_pct,
        projected_total_inr,
        status_enum.value,
    )

    return breakdown


# ---------------------------------------------------------------------------
# LangGraph Node Interface
# ---------------------------------------------------------------------------


def budget_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node function for Phase 10 Deterministic Budget Engine.

    Accepts the shared state dictionary containing intake, logistics, experience,
    and visa verdicts, computes the complete deterministic BudgetBreakdown,
    and returns a state update dictionary.

    Args:
        state: LangGraph state dictionary.

    Returns:
        State update dictionary containing {"budget_breakdown": breakdown}.
    """
    breakdown = process_budget(state)
    return {"budget_breakdown": breakdown}
