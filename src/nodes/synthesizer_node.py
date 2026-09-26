"""Phase 13 — First Complete Vertical Slice (Synthesizer Planning Node).

Consolidates all upstream planning outputs into the canonical FinalItinerary:
1. Validates presence and integrity of all domain artifacts (TripContext,
   LogisticsPlan, ExperiencePlan, BudgetBreakdown, OptimizationResult, VisaVerdict).
2. Generates human-readable, contextual journey titles and executive summaries
   tailored to destination, pacing, travel style, and party composition.
3. Consolidates actionable traveler advisories and warnings across all graph branches.
4. Determines final provenance and estimation flags (Rule 15).
5. Assembles immutable FinalItinerary domain contracts for downstream API and CLI consumption.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from src.models.budget import (
    BudgetBreakdown,
    OptimizationAction,
    OptimizationResult,
)
from src.models.itinerary import ExperiencePlan, FinalItinerary
from src.models.logistics import LogisticsPlan
from src.models.trip import InitialPlanningState, TravelStyle, TripContext
from src.models.visa import VisaVerdict

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SynthesizerError(Exception):
    """Base exception for itinerary synthesis errors."""


class SynthesizerValidationError(SynthesizerError):
    """Raised when required upstream state or artifacts are missing."""


# ---------------------------------------------------------------------------
# Narrative Generators
# ---------------------------------------------------------------------------


def generate_itinerary_title(context: TripContext) -> str:
    """Generate a crisp, compelling title for the journey narrative.

    Args:
        context: Validated TripContext.

    Returns:
        Formatted display title (e.g. '4-Day Scenic Goa Getaway').
    """
    days = context.dates.duration_days or len(context.destinations) * 2 or 3
    dests = ", ".join(d.title() for d in context.destinations)

    style_adjectives = {
        TravelStyle.BUDGET: "Essential",
        TravelStyle.COMFORTABLE: "Scenic",
        TravelStyle.PREMIUM: "Curated",
        TravelStyle.LUXURY: "Signature Luxury",
    }
    adj = style_adjectives.get(context.travel_style, "Memorable")

    if len(context.destinations) == 1:
        return f"{days}-Day {adj} {dests} Getaway"
    return f"{days}-Day {adj} Tour of {dests}"


def generate_itinerary_summary(
    context: TripContext,
    logistics: LogisticsPlan,
    experience: ExperiencePlan,
    budget: BudgetBreakdown,
) -> str:
    """Synthesize an executive narrative summary covering all trip pillars.

    Args:
        context: Validated TripContext.
        logistics: Generated LogisticsPlan.
        experience: Generated ExperiencePlan.
        budget: Deterministic BudgetBreakdown.

    Returns:
        Paragraph summarizing transport, stays, daily sights, dining, and budget health.
    """
    days = context.dates.duration_days or len(experience.days) or 1
    dests = ", ".join(d.title() for d in context.destinations)
    adults = context.party.adults
    kids = context.party.children
    party_desc = f"{adults} adults" + (f" and {kids} children" if kids else "")

    # Transport & lodging summary
    legs_cnt = len(logistics.transport_legs)
    hotel_names = [h.hotel_name for h in logistics.hotel_stays if h.hotel_name]
    hotel_str = hotel_names[0] if hotel_names else "curated accommodations"

    # Sights & dining summary
    must_visits = experience.must_visits_fulfilled
    sight_str = (
        f"including must-visits like {', '.join(must_visits[:3])}"
        if must_visits
        else f"covering {len(experience.days)} curated daily experiences"
    )

    # Budget summary
    user_budget = budget.variance.user_budget_inr
    proj_total = budget.total_with_contingency_inr
    variance_pct = budget.variance.variance_percentage
    status = budget.variance.status.value

    if variance_pct <= 0:
        headroom = abs(budget.variance.variance_inr)
        budget_note = (
            f"Within your allocated ₹{user_budget:,.2f} budget "
            f"(projected total ₹{proj_total:,.2f} with ₹{headroom:,.2f} headroom)"
        )
    elif variance_pct <= 5.0:
        budget_note = (
            f"Optimized to fit your ₹{user_budget:,.2f} budget "
            f"(projected total ₹{proj_total:,.2f}, {variance_pct:+.1f}% variance)"
        )
    else:
        budget_note = (
            f"Projected total ₹{proj_total:,.2f} vs allocated ₹{user_budget:,.2f} "
            f"({variance_pct:+.1f}% variance, {status})"
        )

    summary = (
        f"A customized {days}-day {context.travel_style.value.lower()} journey to {dests} "
        f"for {party_desc} traveling from {context.origin}. The itinerary features {legs_cnt} "
        f"transport segments and quality lodging at {hotel_str}. Daily scheduling is tuned to a "
        f"{context.pace.value.lower()} pace {sight_str}, paired with authentic regional culinary "
        f"spots. Financials: {budget_note}."
    )
    return summary


# ---------------------------------------------------------------------------
# Core Synthesis Function
# ---------------------------------------------------------------------------


def process_synthesizer(
    state_or_context: InitialPlanningState | TripContext | None = None,
    logistics_plan: LogisticsPlan | None = None,
    experience_plan: ExperiencePlan | None = None,
    budget_breakdown: BudgetBreakdown | None = None,
    optimization_result: OptimizationResult | None = None,
    visa_verdict: VisaVerdict | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    trip_context: TripContext | None = None,
) -> FinalItinerary:
    """Synthesize upstream domain artifacts into a validated FinalItinerary.

    Args:
        state_or_context: TripContext or InitialPlanningState.
        logistics_plan: Generated LogisticsPlan.
        experience_plan: Generated ExperiencePlan.
        budget_breakdown: Deterministic BudgetBreakdown.
        optimization_result: Optional OptimizationResult from Optimizer Node.
        visa_verdict: Optional VisaVerdict for international travel.
        warnings: Optional list of graph warnings.
        errors: Optional list of graph errors.
        trip_context: Keyword alias for state_or_context.

    Returns:
        Complete, validated FinalItinerary model.

    Raises:
        SynthesizerValidationError: If mandatory planning components are missing.
    """
    if state_or_context is None and trip_context is not None:
        state_or_context = trip_context

    if state_or_context is None:
        raise SynthesizerValidationError("TripContext or InitialPlanningState is required.")
    if logistics_plan is None:
        raise SynthesizerValidationError("LogisticsPlan is required for itinerary synthesis.")
    if experience_plan is None:
        raise SynthesizerValidationError("ExperiencePlan is required for itinerary synthesis.")
    if budget_breakdown is None:
        raise SynthesizerValidationError("BudgetBreakdown is required for itinerary synthesis.")

    context = (
        state_or_context.trip_context
        if isinstance(state_or_context, InitialPlanningState)
        else state_or_context
    )

    opt_result = optimization_result or budget_breakdown.optimization

    # 1. Deterministic Trip ID
    dest_str = "_".join(d.lower() for d in context.destinations)
    raw_hash = hashlib.md5(
        f"{context.origin}_{dest_str}_{context.dates.start_date}_{datetime.now(UTC).date()}".encode()
    ).hexdigest()[:8]
    trip_id = f"trip_{context.origin.lower()}_{dest_str}_{raw_hash}"

    # 2. Titles and Summaries
    title = generate_itinerary_title(context)
    summary = generate_itinerary_summary(context, logistics_plan, experience_plan, budget_breakdown)

    # 3. Consolidated Warnings
    combined_warnings: list[str] = []
    seen: set[str] = set()
    for w in (
        (warnings or [])
        + logistics_plan.warnings
        + experience_plan.warnings
        + budget_breakdown.warnings
        + (opt_result.trade_offs if opt_result else [])
    ):
        if w and w not in seen:
            seen.add(w)
            combined_warnings.append(w)

    # 4. Provenance tracking
    has_estimated = any(
        [
            logistics_plan.is_estimated,
            experience_plan.is_estimated,
            budget_breakdown.is_estimated,
        ]
    )

    # 5. Terminal Plan Status
    if errors:
        plan_status = "FAILED"
    elif opt_result.action == OptimizationAction.USER_DECISION_REQUIRED:
        plan_status = "NEEDS_USER_DECISION"
    elif opt_result.action == OptimizationAction.INFEASIBLE:
        plan_status = "INFEASIBLE"
    else:
        plan_status = "COMPLETED"

    return FinalItinerary(
        trip_id=trip_id,
        title=title,
        summary=summary,
        trip_context=context,
        logistics_plan=logistics_plan,
        experience_plan=experience_plan,
        budget_breakdown=budget_breakdown,
        visa_verdict=visa_verdict,
        optimization_result=opt_result,
        plan_status=plan_status,
        warnings=combined_warnings,
        is_estimated=has_estimated,
        created_at=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# LangGraph Node Interface
# ---------------------------------------------------------------------------


def synthesizer_node(state: dict[str, Any] | InitialPlanningState) -> dict[str, Any]:
    """LangGraph node interface for Phase 13 Final Itinerary Synthesizer.

    Args:
        state: Shared LangGraph state dictionary.

    Returns:
        State update dictionary containing 'final_itinerary' and 'plan_status'.
    """
    if isinstance(state, InitialPlanningState):
        context = state.trip_context
        logistics_plan = None
        experience_plan = None
        budget_breakdown = None
        opt_result = None
        visa_verdict = None
        warnings = []
        errors = []
    elif isinstance(state, dict):
        context = state.get("trip_context") or state.get("context")
        logistics_plan = state.get("logistics_plan")
        experience_plan = state.get("experience_plan")
        budget_breakdown = state.get("budget_breakdown")
        opt_result = state.get("optimization_result")
        visa_verdict = state.get("visa_verdict")
        warnings = state.get("warnings", [])
        errors = state.get("errors", [])
    else:
        raise SynthesizerValidationError(
            f"Invalid state object for synthesizer_node: {type(state)}"
        )

    itinerary = process_synthesizer(
        state_or_context=context,
        logistics_plan=logistics_plan,
        experience_plan=experience_plan,
        budget_breakdown=budget_breakdown,
        optimization_result=opt_result,
        visa_verdict=visa_verdict,
        warnings=warnings,
        errors=errors,
    )

    return {
        "final_itinerary": itinerary,
        "plan_status": itinerary.plan_status,
    }
