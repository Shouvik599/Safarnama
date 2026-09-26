"""Phase 12 — LangGraph Orchestration: Shared State Definition.

Defines the structured State schema (PlanGraphState) and reducer operators
for orchestrating the Safarnama multi-agent planning workflow:
- Typed domain representations (TripContext, LogisticsPlan, ExperiencePlan,
  BudgetBreakdown, VisaVerdict, OptimizationResult).
- Deterministic reducers for parallel branch outputs (warnings and errors).
- Provenance and tracking metadata for re-planning and lifecycle status.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any, TypedDict

from src.models.budget import BudgetBreakdown, OptimizationResult
from src.models.itinerary import ExperiencePlan, FinalItinerary
from src.models.logistics import LogisticsPlan
from src.models.trip import TravelScope, TripContext
from src.models.visa import VisaVerdict

log = logging.getLogger(__name__)


def merge_warnings(left: list[str] | None, right: list[str] | None) -> list[str]:
    """Reducer that merges and deduplicates warning messages across parallel graph branches.

    Args:
        left: Existing warnings accumulated in graph state.
        right: New warnings emitted by a node update.

    Returns:
        Deduplicated list preserving order of arrival.
    """
    combined: list[str] = []
    seen: set[str] = set()
    for item in (left or []) + (right or []):
        if item and item not in seen:
            seen.add(item)
            combined.append(item)
    return combined


def merge_errors(left: list[str] | None, right: list[str] | None) -> list[str]:
    """Reducer that merges and deduplicates error messages across parallel graph branches.

    Args:
        left: Existing errors accumulated in graph state.
        right: New errors emitted by a node update.

    Returns:
        Deduplicated list preserving order of arrival.
    """
    combined: list[str] = []
    seen: set[str] = set()
    for item in (left or []) + (right or []):
        if item and item not in seen:
            seen.add(item)
            combined.append(item)
    return combined


class PlanGraphState(TypedDict, total=False):
    """LangGraph shared planning state for Safarnama multi-agent workflow.

    Enforces Rule 21: Structured domain models are preferred over arbitrary
    dictionaries. Reducers are used intentionally for fields subject to parallel updates.
    """

    # Raw intake input
    request: dict[str, Any]

    # Intake & Trip Context
    trip_context: TripContext | None
    travel_scope: TravelScope | str | None
    origin: dict[str, Any] | None
    destinations: list[dict[str, Any]] | None
    route: list[str] | None
    effective_duration_days: int | None
    total_budget_inr: float | None
    daily_budget_per_person_inr: float | None

    # Intermediate / Parallel Planning Artifacts
    visa_verdict: VisaVerdict | None
    logistics_plan: LogisticsPlan | None
    experience_plan: ExperiencePlan | None

    # Financial & Optimization Artifacts
    budget_breakdown: BudgetBreakdown | None
    optimization_result: OptimizationResult | None

    # Synthesized Final Deliverable
    final_itinerary: FinalItinerary | None

    # Graph Execution Metadata
    plan_status: str
    warnings: Annotated[list[str], merge_warnings]
    errors: Annotated[list[str], merge_errors]

    # Re-planning Support
    replan_requested: bool
    replan_proposal: dict[str, Any] | None


def create_initial_state(
    request: dict[str, Any] | None = None,
    trip_context: TripContext | None = None,
) -> PlanGraphState:
    """Initialize a clean, structured PlanGraphState for LangGraph execution.

    Args:
        request: Raw user request dictionary or parameter mappings.
        trip_context: Pre-parsed TripContext domain model if available.

    Returns:
        PlanGraphState initialized with empty accumulators and initial status.
    """
    state: PlanGraphState = {
        "request": request or {},
        "trip_context": trip_context,
        "travel_scope": trip_context.scope if trip_context else None,
        "origin": None,
        "destinations": None,
        "route": None,
        "effective_duration_days": (
            trip_context.dates.duration_days if trip_context and trip_context.dates else None
        ),
        "total_budget_inr": (
            trip_context.budget.amount_inr if trip_context and trip_context.budget else None
        ),
        "daily_budget_per_person_inr": None,
        "visa_verdict": None,
        "logistics_plan": None,
        "experience_plan": None,
        "budget_breakdown": None,
        "optimization_result": None,
        "final_itinerary": None,
        "plan_status": "INITIALIZED",
        "warnings": [],
        "errors": [],
        "replan_requested": False,
        "replan_proposal": None,
    }
    return state
