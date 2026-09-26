"""Phase 11 — Optimizer Functionality (Optimizer Planning Node).

Evaluates budget variance and executes tiered optimization policies:
1. Detects budget conflicts across 4 discrete outcome tiers:
   - UNDER_BUDGET / EXACT: No cost reductions required (Action: NONE). Notes headroom if applicable.
   - MINOR_OVER (<= 5% over): Automatically executes minor optimizations without sacrificing
     hard quality guardrails (Action: CHEAPER_HOTEL, LOWER_FOOD_BUDGET, CHEAPER_ACTIVITIES,
     CHEAPER_TRANSPORT, or MULTIPLE_MINOR).
   - SIGNIFICANT_OVER (5%–15% over): Halts automatic mutation; formulates explicit,
     user-visible trade-offs and alternatives requiring traveler decision
     (Action: USER_DECISION_REQUIRED).
   - INFEASIBLE (> 15% over): Explains substantial cost discrepancy, isolates major cost drivers,
     and presents structured alternatives (Action: INFEASIBLE).
2. Hard Quality Guardrails Enforcement:
   - Must-visit sights cannot be silently removed or omitted.
   - Dietary/allergy constraints must not be violated.
   - Trip pacing (RELAXED, BALANCED, PACKED) must not be materially distorted.
   - No unreasonable hotel downgrades (e.g. dropping luxury down to 1-star hostel).
   - No excessive travel time added merely to cut costs.
   - No replacing major cultural experiences with unrelated low-cost activities.
3. Deterministic Financial Recalculation:
   - All adjusted costs, subtotals, dynamic contingency, and budget variances are computed
     deterministically using Python Decimal via src/tools/calculator.py (Rule 18, Rule 34).
   - LLMs must NEVER perform arithmetic.
4. Re-planning Support:
   - Generates structured re-planning proposals (INCREASE_BUDGET, REDUCE_DURATION,
     ADJUST_TRAVEL_STYLE, REMOVE_DESTINATION) for downstream interactive workflows.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.models.budget import (
    BudgetBreakdown,
    BudgetStatus,
    ContingencyConfig,
    CostBreakdown,
    OptimizationAction,
    OptimizationResult,
)
from src.models.budget import (
    BudgetVariance as DomainBudgetVariance,
)
from src.models.itinerary import DayMeal, DayPlan, ExperiencePlan
from src.models.logistics import HotelStay, LogisticsPlan
from src.models.trip import (
    DateMode,
    InitialPlanningState,
    TravelScope,
    TravelStyle,
    TripContext,
)
from src.models.visa import VisaVerdict
from src.tools.calculator import (
    calculate_dynamic_contingency,
    calculate_per_person_cost,
    calculate_total_expenses,
    classify_detailed_budget_status,
    round_currency,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Typed Exceptions
# ---------------------------------------------------------------------------


class OptimizerError(Exception):
    """Base exception for all optimizer node errors."""


class OptimizerValidationError(OptimizerError):
    """Raised when required input parameters or budget state are missing or invalid."""


class OptimizerPlanningError(OptimizerError):
    """Raised when an internal error occurs during optimization calculation."""


# ---------------------------------------------------------------------------
# Output Domain Contract
# ---------------------------------------------------------------------------


class OptimizerOutput(BaseModel):
    """Consolidated result returned by the Optimizer Planning Node."""

    model_config = ConfigDict(frozen=True)

    optimization_result: OptimizationResult = Field(
        description="The optimization action taken or recommended, with trade-offs."
    )
    budget_breakdown: BudgetBreakdown = Field(
        description="Updated BudgetBreakdown reflecting applied savings (or original if unchanged)."
    )
    logistics_plan: LogisticsPlan | None = Field(
        default=None,
        description="Updated LogisticsPlan with adjusted hotel/transport rates if modified.",
    )
    experience_plan: ExperiencePlan | None = Field(
        default=None,
        description="Updated ExperiencePlan with adjusted meal/activity costs if modified.",
    )


# ---------------------------------------------------------------------------
# Core Optimization Logic
# ---------------------------------------------------------------------------


def process_optimizer(
    state_or_context: InitialPlanningState | TripContext | None,
    budget_breakdown: BudgetBreakdown | None,
    logistics_plan: LogisticsPlan | None = None,
    experience_plan: ExperiencePlan | None = None,
    visa_verdict: VisaVerdict | None = None,
) -> OptimizerOutput:
    """Evaluate budget variance and apply tiered optimization policies.

    Args:
        state_or_context: TripContext or InitialPlanningState containing travel requirements.
        budget_breakdown: Current deterministic budget breakdown from BudgetEngine.
        logistics_plan: Optional LogisticsPlan containing transport legs and hotel stays.
        experience_plan: Optional ExperiencePlan containing daily itinerary and dining.
        visa_verdict: Optional VisaVerdict containing visa regulations and fees.

    Returns:
        OptimizerOutput with optimization result, updated budget, and updated plans.

    Raises:
        OptimizerValidationError: If context or budget_breakdown is missing.
    """
    if state_or_context is None:
        raise OptimizerValidationError("TripContext or InitialPlanningState is required.")
    if budget_breakdown is None:
        raise OptimizerValidationError("BudgetBreakdown is required for optimization.")

    context = (
        state_or_context.trip_context
        if isinstance(state_or_context, InitialPlanningState)
        else state_or_context
    )

    variance = budget_breakdown.variance
    variance_pct = variance.variance_percentage
    variance_inr = variance.variance_inr
    user_budget = variance.user_budget_inr
    projected_total = variance.projected_total_inr

    log.info(
        "Optimizer running: user_budget=₹%.2f, projected=₹%.2f, variance=₹%.2f (%.2f%%, status=%s)",
        user_budget,
        projected_total,
        variance_inr,
        variance_pct,
        variance.status.value,
    )

    # -----------------------------------------------------------------------
    # Tier 1: UNDER_BUDGET or EXACT (<= 0 or within ₹1 tolerance)
    # -----------------------------------------------------------------------
    if variance.status in (BudgetStatus.UNDER_BUDGET, BudgetStatus.EXACT) or variance_inr <= 0.0:
        return _handle_within_budget(context, budget_breakdown, logistics_plan, experience_plan)

    # -----------------------------------------------------------------------
    # Tier 2: MINOR_OVER (0 < variance_pct <= 5.0%)
    # Automatic minor optimization permitted; obey hard quality guardrails.
    # -----------------------------------------------------------------------
    if variance_pct <= 5.0:
        return _handle_minor_overage(
            context=context,
            budget_breakdown=budget_breakdown,
            logistics_plan=logistics_plan,
            experience_plan=experience_plan,
            visa_verdict=visa_verdict,
        )

    # -----------------------------------------------------------------------
    # Tier 3: SIGNIFICANT_OVER (5.0% < variance_pct <= 15.0%)
    # Present user with trade-offs before making meaningful changes.
    # -----------------------------------------------------------------------
    if variance_pct <= 15.0:
        return _handle_significant_overage(
            context=context,
            budget_breakdown=budget_breakdown,
            logistics_plan=logistics_plan,
            experience_plan=experience_plan,
        )

    # -----------------------------------------------------------------------
    # Tier 4: INFEASIBLE (> 15.0% over budget)
    # Explain infeasibility, highlight primary cost drivers, present alternatives.
    # -----------------------------------------------------------------------
    return _handle_infeasible_budget(
        context=context,
        budget_breakdown=budget_breakdown,
        logistics_plan=logistics_plan,
        experience_plan=experience_plan,
    )


# ---------------------------------------------------------------------------
# Tier Handler: Within Budget
# ---------------------------------------------------------------------------


def _handle_within_budget(
    context: TripContext,
    budget_breakdown: BudgetBreakdown,
    logistics_plan: LogisticsPlan | None,
    experience_plan: ExperiencePlan | None,
) -> OptimizerOutput:
    """Handle trips that are already under budget or exact."""
    variance = budget_breakdown.variance
    surplus_inr = abs(variance.variance_inr)

    trade_offs: list[str] = []
    if variance.variance_percentage < -15.0 and surplus_inr >= 5000:
        trade_offs.append(
            f"Available budget headroom of ₹{surplus_inr:,.2f} permits potential room upgrades "
            f"or premium dining experiences if desired."
        )

    result = OptimizationResult(
        action=OptimizationAction.NONE,
        savings_inr=0.0,
        description="Trip is within allocated budget. No cost reductions needed.",
        trade_offs=trade_offs,
        alternatives_presented=[],
        guardrails_respected=True,
    )

    updated_breakdown = budget_breakdown.model_copy(update={"optimization": result})
    return OptimizerOutput(
        optimization_result=result,
        budget_breakdown=updated_breakdown,
        logistics_plan=logistics_plan,
        experience_plan=experience_plan,
    )


# ---------------------------------------------------------------------------
# Tier Handler: Minor Over-Budget (<= 5%)
# ---------------------------------------------------------------------------


def _handle_minor_overage(
    context: TripContext,
    budget_breakdown: BudgetBreakdown,
    logistics_plan: LogisticsPlan | None,
    experience_plan: ExperiencePlan | None,
    visa_verdict: VisaVerdict | None,
) -> OptimizerOutput:
    """Execute automatic minor optimizations without violating hard quality guardrails."""
    variance = budget_breakdown.variance
    target_savings = variance.variance_inr  # e.g. ₹3,500

    current_costs = budget_breakdown.cost_breakdown
    current_hotels = current_costs.accommodation_inr
    current_food = current_costs.food_inr

    # Strategy 1: Hotel Saver Rate Optimization (if hotel cost covers target savings)
    # A standard saver rate (e.g. 8%–15% room rate reduction) without dropping style tier
    if logistics_plan and logistics_plan.hotel_stays and current_hotels > 0:
        # Check if an achievable hotel saver discount (up to 15%) covers target savings
        max_hotel_saver = current_hotels * 0.15
        if max_hotel_saver >= target_savings:
            return _optimize_hotel_stays(
                context=context,
                budget_breakdown=budget_breakdown,
                logistics_plan=logistics_plan,
                experience_plan=experience_plan,
                visa_verdict=visa_verdict,
                target_savings=target_savings,
            )

    # Strategy 2: Dining Assumption Optimization (if dining alone covers target savings)
    # Mix casual authentic eateries/bistros, saving 10%-15% while keeping all dietary preferences
    if experience_plan and experience_plan.days and current_food > 0:
        max_food_saver = current_food * 0.15
        if max_food_saver >= target_savings:
            return _optimize_dining_costs(
                context=context,
                budget_breakdown=budget_breakdown,
                logistics_plan=logistics_plan,
                experience_plan=experience_plan,
                visa_verdict=visa_verdict,
                target_savings=target_savings,
            )

    # Strategy 3: Multi-minor Optimization
    # Proportional small reductions across hotel (~5-8%) and dining (~5-8%)
    return _optimize_multi_minor(
        context=context,
        budget_breakdown=budget_breakdown,
        logistics_plan=logistics_plan,
        experience_plan=experience_plan,
        visa_verdict=visa_verdict,
        target_savings=target_savings,
    )


def _optimize_hotel_stays(
    context: TripContext,
    budget_breakdown: BudgetBreakdown,
    logistics_plan: LogisticsPlan,
    experience_plan: ExperiencePlan | None,
    visa_verdict: VisaVerdict | None,
    target_savings: float,
) -> OptimizerOutput:
    """Apply hotel saver rate optimization."""
    current_hotels = budget_breakdown.cost_breakdown.accommodation_inr
    discount_ratio = min(0.15, max(0.05, (target_savings * 1.05) / current_hotels))

    updated_stays: list[HotelStay] = []
    for stay in logistics_plan.hotel_stays:
        new_rate = round_currency(stay.price_per_room_per_night_inr * (1.0 - discount_ratio))
        new_total = round_currency(new_rate * stay.nights * stay.rooms_required)
        updated_stays.append(
            stay.model_copy(
                update={
                    "price_per_room_per_night_inr": new_rate,
                    "total_accommodation_cost_inr": new_total,
                    "notes": f"Saver Rate applied ({int(discount_ratio * 100)}% savings)",
                }
            )
        )

    new_accomm_cost = round_currency(sum(s.total_accommodation_cost_inr for s in updated_stays))
    updated_logistics = logistics_plan.model_copy(
        update={
            "hotel_stays": updated_stays,
            "total_accommodation_cost_inr": new_accomm_cost,
            "total_logistics_cost_inr": round_currency(
                logistics_plan.total_transport_cost_inr + new_accomm_cost
            ),
        }
    )

    recomputed = _recompute_budget_breakdown(
        context=context,
        original_breakdown=budget_breakdown,
        logistics_plan=updated_logistics,
        experience_plan=experience_plan,
        visa_verdict=visa_verdict,
    )

    achieved_savings = round_currency(
        budget_breakdown.variance.projected_total_inr - recomputed.variance.projected_total_inr
    )
    result = OptimizationResult(
        action=OptimizationAction.CHEAPER_HOTEL,
        savings_inr=achieved_savings,
        description=(
            f"Automatically selected standard saver room rates at hotel(s), "
            f"reducing accommodation expenses by ₹{achieved_savings:,.2f} "
            f"without changing hotel star tier."
        ),
        trade_offs=["Selected standard saver room rates instead of flexible/deluxe packages."],
        alternatives_presented=[],
        guardrails_respected=True,
    )

    final_breakdown = recomputed.model_copy(update={"optimization": result})
    return OptimizerOutput(
        optimization_result=result,
        budget_breakdown=final_breakdown,
        logistics_plan=updated_logistics,
        experience_plan=experience_plan,
    )


def _optimize_dining_costs(
    context: TripContext,
    budget_breakdown: BudgetBreakdown,
    logistics_plan: LogisticsPlan | None,
    experience_plan: ExperiencePlan,
    visa_verdict: VisaVerdict | None,
    target_savings: float,
) -> OptimizerOutput:
    """Apply dining assumption optimization preserving all dietary preferences."""
    current_food = budget_breakdown.cost_breakdown.food_inr
    discount_ratio = min(0.15, max(0.05, (target_savings * 1.05) / current_food))

    updated_days: list[DayPlan] = []
    for day in experience_plan.days:
        updated_meals: list[DayMeal] = []
        for meal in day.meals:
            new_cost = round_currency(meal.estimated_cost_inr * (1.0 - discount_ratio))
            updated_meals.append(meal.model_copy(update={"estimated_cost_inr": new_cost}))
        updated_days.append(day.model_copy(update={"meals": updated_meals}))

    total_travelers = context.party.total_travelers
    new_food_total = round_currency(
        sum(m.estimated_cost_inr for d in updated_days for m in d.meals) * total_travelers
    )

    updated_experience = experience_plan.model_copy(
        update={
            "days": updated_days,
            "total_food_cost_inr": new_food_total,
        }
    )

    recomputed = _recompute_budget_breakdown(
        context=context,
        original_breakdown=budget_breakdown,
        logistics_plan=logistics_plan,
        experience_plan=updated_experience,
        visa_verdict=visa_verdict,
    )

    achieved_savings = round_currency(
        budget_breakdown.variance.projected_total_inr - recomputed.variance.projected_total_inr
    )
    result = OptimizationResult(
        action=OptimizationAction.LOWER_FOOD_BUDGET,
        savings_inr=achieved_savings,
        description=(
            f"Adjusted dining allocations to incorporate authentic local cafes and casual dining, "
            f"saving ₹{achieved_savings:,.2f} while preserving all dietary requirements."
        ),
        trade_offs=[
            "Assumed casual authentic eateries and local cafes for select meals instead of dining."
        ],
        alternatives_presented=[],
        guardrails_respected=True,
    )

    final_breakdown = recomputed.model_copy(update={"optimization": result})
    return OptimizerOutput(
        optimization_result=result,
        budget_breakdown=final_breakdown,
        logistics_plan=logistics_plan,
        experience_plan=updated_experience,
    )


def _optimize_multi_minor(
    context: TripContext,
    budget_breakdown: BudgetBreakdown,
    logistics_plan: LogisticsPlan | None,
    experience_plan: ExperiencePlan | None,
    visa_verdict: VisaVerdict | None,
    target_savings: float,
) -> OptimizerOutput:
    """Apply proportional minor adjustments across hotel and dining."""
    updated_logistics = logistics_plan
    updated_experience = experience_plan

    current_hotels = budget_breakdown.cost_breakdown.accommodation_inr
    current_food = budget_breakdown.cost_breakdown.food_inr

    # Proportional split between hotel and food
    combined_base = current_hotels + current_food
    if combined_base > 0:
        ratio = min(0.12, max(0.04, (target_savings * 1.05) / combined_base))
    else:
        ratio = 0.05

    trade_offs: list[str] = []

    if logistics_plan and logistics_plan.hotel_stays:
        updated_stays: list[HotelStay] = []
        for stay in logistics_plan.hotel_stays:
            new_rate = round_currency(stay.price_per_room_per_night_inr * (1.0 - ratio))
            new_total = round_currency(new_rate * stay.nights * stay.rooms_required)
            updated_stays.append(
                stay.model_copy(
                    update={
                        "price_per_room_per_night_inr": new_rate,
                        "total_accommodation_cost_inr": new_total,
                        "notes": f"Saver Rate applied ({int(ratio * 100)}% savings)",
                    }
                )
            )
        new_accomm = round_currency(sum(s.total_accommodation_cost_inr for s in updated_stays))
        updated_logistics = logistics_plan.model_copy(
            update={
                "hotel_stays": updated_stays,
                "total_accommodation_cost_inr": new_accomm,
                "total_logistics_cost_inr": round_currency(
                    logistics_plan.total_transport_cost_inr + new_accomm
                ),
            }
        )
        trade_offs.append("Selected standard saver room rates at hotel(s).")

    if experience_plan and experience_plan.days:
        updated_days: list[DayPlan] = []
        for day in experience_plan.days:
            updated_meals: list[DayMeal] = []
            for meal in day.meals:
                new_cost = round_currency(meal.estimated_cost_inr * (1.0 - ratio))
                updated_meals.append(meal.model_copy(update={"estimated_cost_inr": new_cost}))
            updated_days.append(day.model_copy(update={"meals": updated_meals}))

        total_travelers = context.party.total_travelers
        new_food_total = round_currency(
            sum(m.estimated_cost_inr for d in updated_days for m in d.meals) * total_travelers
        )
        updated_experience = experience_plan.model_copy(
            update={
                "days": updated_days,
                "total_food_cost_inr": new_food_total,
            }
        )
        trade_offs.append("Balanced dining with casual local bistros and cafes.")

    recomputed = _recompute_budget_breakdown(
        context=context,
        original_breakdown=budget_breakdown,
        logistics_plan=updated_logistics,
        experience_plan=updated_experience,
        visa_verdict=visa_verdict,
    )

    achieved_savings = round_currency(
        budget_breakdown.variance.projected_total_inr - recomputed.variance.projected_total_inr
    )
    result = OptimizationResult(
        action=OptimizationAction.MULTIPLE_MINOR,
        savings_inr=achieved_savings,
        description=(
            f"Applied balanced minor optimizations across hotel saver rates and casual dining, "
            f"saving ₹{achieved_savings:,.2f} without impacting must-visit sights or trip pacing."
        ),
        trade_offs=trade_offs,
        alternatives_presented=[],
        guardrails_respected=True,
    )

    final_breakdown = recomputed.model_copy(update={"optimization": result})
    return OptimizerOutput(
        optimization_result=result,
        budget_breakdown=final_breakdown,
        logistics_plan=updated_logistics,
        experience_plan=updated_experience,
    )


# ---------------------------------------------------------------------------
# Tier Handler: Significant Overage (5%–15%)
# ---------------------------------------------------------------------------


def _handle_significant_overage(
    context: TripContext,
    budget_breakdown: BudgetBreakdown,
    logistics_plan: LogisticsPlan | None,
    experience_plan: ExperiencePlan | None,
) -> OptimizerOutput:
    """Formulate actionable trade-offs and alternatives requiring traveler decision."""
    variance = budget_breakdown.variance
    overage = variance.variance_inr
    pct = variance.variance_percentage
    costs = budget_breakdown.cost_breakdown

    trade_offs: list[str] = []
    alternatives: list[str] = [
        f"Increase budget by ₹{overage:,.2f} to proceed without altering hotels or experiences."
    ]

    # Calculate potential lodging savings (e.g. step down 1 hotel tier ~25% savings)
    if costs.accommodation_inr > 0:
        est_hotel_savings = round_currency(costs.accommodation_inr * 0.25)
        trade_offs.append(
            f"Hotel tier adjustment: Switching to 3-star lodging saves ~₹{est_hotel_savings:,.2f}."
        )
        alternatives.append(
            f"Approve hotel tier adjustment (estimated savings: ~₹{est_hotel_savings:,.2f})."
        )

    # Calculate potential dining/activities savings (~20% savings)
    if (costs.food_inr + costs.activities_inr) > 0:
        est_experience_savings = round_currency((costs.food_inr + costs.activities_inr) * 0.20)
        trade_offs.append(
            f"Dining: Shifting to casual street food saves ~₹{est_experience_savings:,.2f}."
        )
        alternatives.append(
            f"Adjust dining budget (estimated savings: ~₹{est_experience_savings:,.2f})."
        )

    # Duration reduction
    duration_days = context.dates.duration_days or 5
    if duration_days > 2:
        alternatives.append(
            f"Reduce trip duration by 1 day (from {duration_days} to {duration_days - 1} days)."
        )

    result = OptimizationResult(
        action=OptimizationAction.USER_DECISION_REQUIRED,
        savings_inr=0.0,
        description=(
            f"Projected trip cost exceeds allocated budget by ₹{overage:,.2f} ({pct:.1f}% over). "
            f"Confirmation is required before making meaningful itinerary or lodging changes."
        ),
        trade_offs=trade_offs,
        alternatives_presented=alternatives,
        guardrails_respected=True,
    )

    updated_breakdown = budget_breakdown.model_copy(update={"optimization": result})
    return OptimizerOutput(
        optimization_result=result,
        budget_breakdown=updated_breakdown,
        logistics_plan=logistics_plan,
        experience_plan=experience_plan,
    )


# ---------------------------------------------------------------------------
# Tier Handler: Infeasible (> 15%)
# ---------------------------------------------------------------------------


def _handle_infeasible_budget(
    context: TripContext,
    budget_breakdown: BudgetBreakdown,
    logistics_plan: LogisticsPlan | None,
    experience_plan: ExperiencePlan | None,
) -> OptimizerOutput:
    """Explain infeasibility, highlight primary cost drivers, and present alternatives."""
    variance = budget_breakdown.variance
    user_budget = variance.user_budget_inr
    projected = variance.projected_total_inr
    overage = variance.variance_inr
    pct = variance.variance_percentage
    costs = budget_breakdown.cost_breakdown

    # Identify primary cost drivers
    category_shares = [
        ("Transport", costs.transport_inr),
        ("Accommodation", costs.accommodation_inr),
        ("Dining", costs.food_inr),
        ("Activities", costs.activities_inr),
        ("Visa Fees", costs.visa_inr),
        ("Miscellaneous", costs.misc_inr),
    ]
    category_shares.sort(key=lambda x: x[1], reverse=True)
    top_drivers = [
        f"{name}: ₹{amount:,.2f} ({amount / costs.subtotal_inr * 100:.1f}%)"
        for name, amount in category_shares[:3]
        if amount > 0 and costs.subtotal_inr > 0
    ]

    duration_days = context.dates.duration_days or 5
    style = context.travel_style

    alternatives: list[str] = [
        f"Increase budget to at least ₹{projected:,.2f} (including dynamic contingency).",
        f"Shorten trip duration from {duration_days} days to {max(1, duration_days - 2)} days.",
        f"Adjust travel style from {style.value} to a more budget-friendly tier.",
    ]
    if len(context.destinations) > 1:
        alternatives.append(
            f"Focus on a single destination instead of {len(context.destinations)} destinations."
        )
    if costs.transport_inr > 0:
        alternatives.append("Replace flights with premium train routes where feasible.")

    trade_offs = [
        f"Major cost drivers consuming the budget: {', '.join(top_drivers)}.",
        "Attempting to force this itinerary into budget would violate core quality guardrails.",
    ]

    result = OptimizationResult(
        action=OptimizationAction.INFEASIBLE,
        savings_inr=0.0,
        description=(
            f"The trip to {', '.join(context.destinations)} is substantially above budget "
            f"(projected ₹{projected:,.2f} vs allocated ₹{user_budget:,.2f}, an overage of "
            f"₹{overage:,.2f} or +{pct:.1f}%). Primary cost drivers: {', '.join(top_drivers)}."
        ),
        trade_offs=trade_offs,
        alternatives_presented=alternatives,
        guardrails_respected=True,
    )

    updated_breakdown = budget_breakdown.model_copy(update={"optimization": result})
    return OptimizerOutput(
        optimization_result=result,
        budget_breakdown=updated_breakdown,
        logistics_plan=logistics_plan,
        experience_plan=experience_plan,
    )


# ---------------------------------------------------------------------------
# Recomputation Helper
# ---------------------------------------------------------------------------


def _recompute_budget_breakdown(
    context: TripContext,
    original_breakdown: BudgetBreakdown,
    logistics_plan: LogisticsPlan | None,
    experience_plan: ExperiencePlan | None,
    visa_verdict: VisaVerdict | None,
) -> BudgetBreakdown:
    """Recompute budget breakdown deterministically using updated plan costs."""
    orig_costs = original_breakdown.cost_breakdown

    transport_cost = (
        logistics_plan.total_transport_cost_inr if logistics_plan else orig_costs.transport_inr
    )
    accommodation_cost = (
        logistics_plan.total_accommodation_cost_inr
        if logistics_plan
        else orig_costs.accommodation_inr
    )
    activities_cost = (
        experience_plan.total_activity_cost_inr if experience_plan else orig_costs.activities_inr
    )
    food_cost = experience_plan.total_food_cost_inr if experience_plan else orig_costs.food_inr
    local_transport_cost = (
        experience_plan.total_local_transport_cost_inr
        if experience_plan
        else orig_costs.local_transport_inr
    )
    visa_cost = (
        visa_verdict.total_visa_cost_inr
        if visa_verdict is not None
        else (orig_costs.visa_inr if context.scope == TravelScope.INTERNATIONAL else 0.0)
    )
    misc_cost = orig_costs.misc_inr

    subtotal = calculate_total_expenses(
        [
            transport_cost,
            accommodation_cost,
            activities_cost,
            food_cost,
            local_transport_cost,
            visa_cost,
            misc_cost,
        ]
    )

    has_estimated = (
        (logistics_plan.is_estimated if logistics_plan else False)
        or orig_costs.has_estimated_components
        or (visa_verdict.is_estimated if visa_verdict else False)
    )

    cost_breakdown = CostBreakdown(
        transport_inr=transport_cost,
        accommodation_inr=accommodation_cost,
        local_transport_inr=local_transport_cost,
        activities_inr=activities_cost,
        food_inr=food_cost,
        visa_inr=visa_cost,
        misc_inr=misc_cost,
        has_estimated_components=has_estimated,
    )

    contingency_pct, contingency_amt, contingency_reasoning = calculate_dynamic_contingency(
        subtotal=subtotal,
        is_international=(context.scope == TravelScope.INTERNATIONAL),
        country_count=max(1, len(context.destinations)),
        has_estimated_prices=has_estimated,
        has_flexible_dates=(context.dates.mode != DateMode.EXACT),
    )

    contingency_config = ContingencyConfig(
        percentage=contingency_pct,
        amount_inr=contingency_amt,
        reasoning=contingency_reasoning,
        is_international=(context.scope == TravelScope.INTERNATIONAL),
        country_count=max(1, len(context.destinations)),
        has_estimated_prices=has_estimated,
        has_flexible_dates=(context.dates.mode != DateMode.EXACT),
    )

    dec_subtotal = Decimal(str(subtotal))
    dec_contingency = Decimal(str(contingency_amt))
    dec_projected = dec_subtotal + dec_contingency
    projected_total = float(dec_projected.quantize(Decimal("0.01")))

    user_budget = original_breakdown.variance.user_budget_inr
    dec_budget = Decimal(str(user_budget))
    variance_dec = dec_projected - dec_budget

    if dec_budget > Decimal("0.00"):
        pct_dec = (variance_dec / dec_budget) * Decimal("100")
    else:
        pct_dec = Decimal("100.00") if dec_projected > 0 else Decimal("0.00")

    variance_inr = float(variance_dec.quantize(Decimal("0.01")))
    variance_pct = float(pct_dec.quantize(Decimal("0.01")))

    status_str = classify_detailed_budget_status(user_budget, projected_total)
    status = BudgetStatus(status_str)

    budget_variance = DomainBudgetVariance(
        user_budget_inr=user_budget,
        projected_total_inr=projected_total,
        variance_inr=variance_inr,
        variance_percentage=variance_pct,
        status=status,
    )

    per_person = calculate_per_person_cost(projected_total, context.party.total_travelers)

    return BudgetBreakdown(
        cost_breakdown=cost_breakdown,
        contingency=contingency_config,
        variance=budget_variance,
        optimization=OptimizationResult(),
        subtotal_inr=subtotal,
        total_with_contingency_inr=projected_total,
        per_person_cost_inr=per_person,
        warnings=original_breakdown.warnings,
        is_estimated=has_estimated,
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Re-planning Proposal Helper
# ---------------------------------------------------------------------------


def create_replanning_proposal(
    context: TripContext,
    proposal_type: str,
    target_value: Any = None,
) -> TripContext:
    """Create a modified TripContext to support iterative re-planning workflows.

    Args:
        context: Current TripContext.
        proposal_type: One of 'INCREASE_BUDGET', 'REDUCE_DURATION',
            'ADJUST_TRAVEL_STYLE', 'REMOVE_DESTINATION'.
        target_value: Specific new value for the targeted parameter.

    Returns:
        Updated TripContext ready for re-planning.

    Raises:
        OptimizerValidationError: If proposal_type or target_value is invalid.
    """
    pt = proposal_type.upper().strip()

    if pt == "INCREASE_BUDGET":
        if target_value is None or float(target_value) <= 0:
            raise OptimizerValidationError(
                f"Valid positive budget amount required, got: {target_value!r}"
            )
        new_budget = context.budget.model_copy(update={"amount_inr": float(target_value)})
        return context.model_copy(update={"budget": new_budget})

    if pt == "REDUCE_DURATION":
        current_days = context.dates.duration_days or 5
        new_days = int(target_value) if target_value is not None else max(1, current_days - 1)
        if new_days < 1:
            raise OptimizerValidationError("Trip duration cannot be less than 1 day.")
        new_dates = context.dates.model_copy(update={"duration_days": new_days})
        return context.model_copy(update={"dates": new_dates})

    if pt == "ADJUST_TRAVEL_STYLE":
        if isinstance(target_value, TravelStyle):
            new_style = target_value
        elif isinstance(target_value, str):
            try:
                new_style = TravelStyle(target_value.upper())
            except ValueError as exc:
                raise OptimizerValidationError(f"Unknown travel style: {target_value!r}") from exc
        else:
            new_style = TravelStyle.BUDGET

        return context.model_copy(update={"travel_style": new_style})

    if pt == "REMOVE_DESTINATION":
        if not target_value and len(context.destinations) > 1:
            new_destinations = context.destinations[:-1]
        elif isinstance(target_value, str) and target_value in context.destinations:
            new_destinations = [d for d in context.destinations if d != target_value]
            if not new_destinations:
                raise OptimizerValidationError("Cannot remove the only destination from a trip.")
        else:
            raise OptimizerValidationError(
                f"Cannot remove destination {target_value!r} from {context.destinations}"
            )
        return context.model_copy(update={"destinations": new_destinations})

    raise OptimizerValidationError(f"Unsupported re-planning proposal type: {proposal_type!r}")


# ---------------------------------------------------------------------------
# LangGraph Node Interface
# ---------------------------------------------------------------------------


def optimizer_node(state: dict[str, Any] | InitialPlanningState) -> dict[str, Any]:
    """LangGraph node interface for Phase 11 — Optimizer Functionality.

    Extracts context, budget breakdown, logistics plan, experience plan, and visa verdict
    from graph state, executes tiered optimization, and returns state updates.

    Args:
        state: LangGraph state dictionary or InitialPlanningState.

    Returns:
        Dictionary with 'optimization_result', 'budget_breakdown', 'logistics_plan',
        and 'experience_plan'.
    """
    if isinstance(state, InitialPlanningState):
        context = state.trip_context
        budget_breakdown = None
        logistics_plan = None
        experience_plan = None
        visa_verdict = None
    elif isinstance(state, dict):
        context = state.get("trip_context") or state.get("context")
        budget_breakdown = state.get("budget_breakdown")
        logistics_plan = state.get("logistics_plan")
        experience_plan = state.get("experience_plan")
        visa_verdict = state.get("visa_verdict")
    else:
        raise OptimizerValidationError(f"Invalid state object for optimizer_node: {type(state)}")

    output = process_optimizer(
        state_or_context=context,
        budget_breakdown=budget_breakdown,
        logistics_plan=logistics_plan,
        experience_plan=experience_plan,
        visa_verdict=visa_verdict,
    )

    return {
        "optimization_result": output.optimization_result,
        "budget_breakdown": output.budget_breakdown,
        "logistics_plan": output.logistics_plan,
        "experience_plan": output.experience_plan,
    }
