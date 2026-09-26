"""Phase 12 — LangGraph Orchestration: Conditional Routing and Graph Edges.

Implements explicit graph routing logic (Rule 19, Architecture Section 2 & 12):
1. Scope Routing (Domestic vs International):
   - Domestic trips bypass visa evaluation and fan out directly to parallel planning.
   - International trips route through the Visa Node before fan-out.
2. Parallel Planning Fan-out & Join:
   - Logistics and Experience nodes execute concurrently.
   - Outputs converge deterministically at the Budget Engine.
3. Post-Optimizer Decision Routing:
   - Evaluates optimization action and determines terminal status.
4. Component Isolation for Re-planning:
   - Analyzes user trade-off proposals to rerun only affected planning nodes,
     reusing unaffected work where possible (Architecture Section 12).
"""

from __future__ import annotations

import logging

from langgraph.graph import END

from src.graph.state import PlanGraphState
from src.models.budget import OptimizationAction
from src.models.trip import TravelScope

log = logging.getLogger(__name__)


def route_scope(state: PlanGraphState) -> str | list[str]:
    """Determine downstream branch following Intake node execution.

    Args:
        state: Current PlanGraphState.

    Returns:
        'visa' for international itineraries,
        ['logistics', 'experience'] for domestic itineraries (parallel fan-out),
        END if fatal errors aborted intake.
    """
    if state.get("errors"):
        log.warning("Intake node reported fatal errors; terminating workflow at END.")
        return END

    context = state.get("trip_context")
    scope = state.get("travel_scope")

    is_international = False
    if context and hasattr(context, "scope"):
        is_international = context.scope == TravelScope.INTERNATIONAL
    elif scope:
        if isinstance(scope, TravelScope):
            is_international = scope == TravelScope.INTERNATIONAL
        elif isinstance(scope, str):
            is_international = scope.upper() == "INTERNATIONAL"

    if is_international:
        log.info("Routing scope: INTERNATIONAL -> routing to 'visa' node.")
        return "visa"

    log.info("Routing scope: DOMESTIC -> fanning out to ['logistics', 'experience'].")
    return ["logistics", "experience"]


def route_after_visa(state: PlanGraphState) -> str | list[str]:
    """Determine downstream routing following Visa node execution.

    Args:
        state: Current PlanGraphState.

    Returns:
        ['logistics', 'experience'] for parallel planning fan-out,
        or END if visa processing reported fatal errors.
    """
    if state.get("errors"):
        log.warning("Visa node encountered fatal errors; routing to END.")
        return END

    log.info("Visa node complete -> fanning out to ['logistics', 'experience'].")
    return ["logistics", "experience"]


def route_optimizer_outcome(state: PlanGraphState) -> str:
    """Classify the terminal status following Optimizer node execution.

    Args:
        state: Current PlanGraphState.

    Returns:
        One of 'FEASIBLE', 'USER_DECISION_REQUIRED', 'INFEASIBLE', or 'ERROR'.
    """
    if state.get("errors"):
        return "ERROR"

    opt_result = state.get("optimization_result")
    if not opt_result:
        return "FEASIBLE"

    action = opt_result.action
    if action in (
        OptimizationAction.NONE,
        OptimizationAction.CHEAPER_HOTEL,
        OptimizationAction.LOWER_FOOD_BUDGET,
        OptimizationAction.CHEAPER_ACTIVITIES,
        OptimizationAction.CHEAPER_TRANSPORT,
        OptimizationAction.MULTIPLE_MINOR,
    ):
        return "FEASIBLE"

    if action == OptimizationAction.USER_DECISION_REQUIRED:
        return "USER_DECISION_REQUIRED"

    if action == OptimizationAction.INFEASIBLE:
        return "INFEASIBLE"

    return "FEASIBLE"


def determine_affected_components(proposal_type: str) -> dict[str, bool]:
    """Determine which planning nodes must rerun for a given re-planning proposal.

    Follows Architecture Section 12 (Re-planning & Reusing Unaffected Work):
    - INCREASE_BUDGET:
        Route, Visa, Transport, Hotels, Experience are unaffected.
        Only Budget Engine and Optimizer must re-evaluate.
    - ADJUST_TRAVEL_STYLE:
        Visa and base Route are unaffected.
        Logistics (hotels tier), Experience (dining tier), Budget, and Optimizer rerun.
    - REDUCE_DURATION:
        Visa is unaffected.
        Logistics (nights), Experience (day count), Budget, and Optimizer rerun.
    - REMOVE_DESTINATION:
        All downstream components (Visa, Logistics, Experience, Budget, Optimizer) rerun.

    Args:
        proposal_type: String identifier ('INCREASE_BUDGET', 'ADJUST_TRAVEL_STYLE', etc.).

    Returns:
        Mapping of component names to boolean flags indicating if they must rerun.
    """
    pt = proposal_type.upper().strip()

    if pt == "INCREASE_BUDGET":
        return {
            "visa": False,
            "logistics": False,
            "experience": False,
            "budget": True,
            "optimizer": True,
        }

    if pt == "ADJUST_TRAVEL_STYLE":
        return {
            "visa": False,
            "logistics": True,
            "experience": True,
            "budget": True,
            "optimizer": True,
        }

    if pt == "REDUCE_DURATION":
        return {
            "visa": False,
            "logistics": True,
            "experience": True,
            "budget": True,
            "optimizer": True,
        }

    if pt == "REMOVE_DESTINATION":
        return {
            "visa": True,
            "logistics": True,
            "experience": True,
            "budget": True,
            "optimizer": True,
        }

    # Default fallback: conservative rerun
    return {
        "visa": True,
        "logistics": True,
        "experience": True,
        "budget": True,
        "optimizer": True,
    }
