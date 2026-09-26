"""Phase 12 — LangGraph Orchestration: Multi-Agent Workflow Engine.

Constructs and compiles the complete Safarnama StateGraph:
- Connects Intake, Visa (conditional), Logistics & Experience (parallel),
  Budget Engine, and Optimizer nodes.
- Preserves deterministic Python calculations and hard quality guardrails.
- Provides run_planning_graph() for end-to-end execution.
- Provides replan_workflow() for selective re-planning with maximum reuse
  of unaffected artifacts (Architecture Section 12).
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.graph.edges import (
    determine_affected_components,
    route_after_visa,
    route_optimizer_outcome,
    route_scope,
)
from src.graph.state import PlanGraphState, create_initial_state
from src.nodes.budget_node import budget_node, process_budget
from src.nodes.experience_node import experience_node, process_experience
from src.nodes.intake_node import intake_node
from src.nodes.logistics_node import logistics_node, process_logistics
from src.nodes.optimizer_node import (
    create_replanning_proposal,
    optimizer_node,
    process_optimizer,
)
from src.nodes.visa_node import process_visa, visa_node

log = logging.getLogger(__name__)


def _wrap_safe_node(node_fn: Any, name: str):
    """Wrap a planning node to catch fatal exceptions and record structured errors."""

    def safe_executor(state: PlanGraphState) -> dict[str, Any]:
        try:
            return node_fn(state)
        except Exception as exc:
            log.error("Fatal error in planning node '%s': %s", name, exc, exc_info=True)
            return {
                "errors": [f"Node '{name}' execution failed: {exc}"],
                "plan_status": "FAILED",
            }

    safe_executor.__name__ = f"safe_{name}"
    return safe_executor


def build_planning_graph() -> CompiledStateGraph:
    """Construct and compile the primary Safarnama LangGraph StateGraph.

    Topology:
        START
          ↓
        intake
          ↓ (conditional scope routing)
          ├── Domestic ─────────────┐
          │                         │
          └── International → visa  │
                                    │
                                    ▼
                            Parallel planning
                            ┌───────────────┐
                            │               │
                            ▼               ▼
                        logistics       experience
                            │               │
                            └───────┬───────┘
                                    ▼
                                 budget (Deterministic Budget Engine)
                                    │
                                    ▼
                                optimizer
                                    │
                                   END

    Returns:
        CompiledStateGraph ready for synchronous or asynchronous invocation.
    """
    builder = StateGraph(PlanGraphState)

    # 1. Register specialized planning nodes
    builder.add_node("intake", _wrap_safe_node(intake_node, "intake"))
    builder.add_node("visa", _wrap_safe_node(visa_node, "visa"))
    builder.add_node("logistics", _wrap_safe_node(logistics_node, "logistics"))
    builder.add_node("experience", _wrap_safe_node(experience_node, "experience"))
    builder.add_node("budget", _wrap_safe_node(budget_node, "budget"))
    builder.add_node("optimizer", _wrap_safe_node(optimizer_node, "optimizer"))

    # 2. Add edges and conditional routing
    builder.add_edge(START, "intake")

    # Scope routing from Intake:
    # International -> Visa
    # Domestic -> Parallel fan-out to ['logistics', 'experience']
    builder.add_conditional_edges(
        "intake",
        route_scope,
        ["visa", "logistics", "experience", END],
    )

    # Post-Visa fan-out:
    # Visa -> Parallel fan-out to ['logistics', 'experience']
    builder.add_conditional_edges(
        "visa",
        route_after_visa,
        ["logistics", "experience", END],
    )

    # Parallel branches converge at the deterministic Budget Engine
    builder.add_edge("logistics", "budget")
    builder.add_edge("experience", "budget")

    # Budget Engine deterministically feeds the Optimizer
    builder.add_edge("budget", "optimizer")

    # Optimizer concludes the core workflow
    builder.add_edge("optimizer", END)

    app = builder.compile()
    log.info("Safarnama planning StateGraph successfully compiled.")
    return app


_COMPILED_GRAPH: CompiledStateGraph | None = None


def get_planning_graph() -> CompiledStateGraph:
    """Retrieve or lazily compile the singleton planning graph instance."""
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_planning_graph()
    return _COMPILED_GRAPH


def run_planning_graph(
    initial_input: dict[str, Any] | PlanGraphState,
) -> PlanGraphState:
    """Execute the complete Safarnama planning workflow end-to-end.

    Args:
        initial_input: User request dictionary or partially populated PlanGraphState.

    Returns:
        Final PlanGraphState containing all generated plans, financial breakdown,
        optimization verdict, warnings, and status.
    """
    if not isinstance(initial_input, dict):
        raise TypeError(f"Expected dictionary or PlanGraphState, got: {type(initial_input)}")

    # Ensure PlanGraphState structure
    if "request" not in initial_input and "trip_context" not in initial_input:
        state = create_initial_state(request=initial_input)
    else:
        state = create_initial_state(
            request=initial_input.get("request") or initial_input,
            trip_context=initial_input.get("trip_context"),
        )
        # Preserve existing keys if provided
        for k, v in initial_input.items():
            if v is not None:
                state[k] = v

    graph = get_planning_graph()
    final_output = graph.invoke(state)

    # Update terminal status
    status = route_optimizer_outcome(final_output)
    if final_output.get("errors"):
        final_output["plan_status"] = "FAILED"
    elif status == "USER_DECISION_REQUIRED":
        final_output["plan_status"] = "NEEDS_USER_DECISION"
    elif status == "INFEASIBLE":
        final_output["plan_status"] = "INFEASIBLE"
    else:
        final_output["plan_status"] = "COMPLETED"

    return final_output


def replan_workflow(
    current_state: PlanGraphState,
    proposal_type: str,
    target_value: Any = None,
) -> PlanGraphState:
    """Iteratively re-plan affected components while preserving unaffected work.

    Follows Architecture Section 12:
    - Analyzes the re-planning proposal.
    - Selectively reruns only affected planning nodes.
    - Reuses existing route, visa, logistics, and experience artifacts wherever valid.
    - Re-evaluates budget breakdown and optimization outcome deterministically.

    Args:
        current_state: Existing PlanGraphState from a previous planning execution.
        proposal_type: One of 'INCREASE_BUDGET', 'REDUCE_DURATION',
                       'ADJUST_TRAVEL_STYLE', 'REMOVE_DESTINATION'.
        target_value: Optional target parameter value (e.g., new budget amount or style).

    Returns:
        Updated PlanGraphState with new plans and re-planning provenance metadata.
    """
    context = current_state.get("trip_context")
    if not context:
        raise ValueError("Cannot re-plan without an existing 'trip_context' in state.")

    # 1. Update TripContext deterministically
    updated_context = create_replanning_proposal(context, proposal_type, target_value)

    # 2. Determine component impact
    affected = determine_affected_components(proposal_type)

    # 3. Selectively rerun or reuse components
    # Visa
    if affected["visa"] and updated_context.scope.value.upper() == "INTERNATIONAL":
        log.info("Re-planning: Rerunning Visa Node for updated destination context.")
        updated_visa = process_visa(updated_context)
    else:
        log.info("Re-planning: Reusing unaffected VisaVerdict.")
        updated_visa = current_state.get("visa_verdict")

    # Logistics
    if affected["logistics"]:
        log.info("Re-planning: Rerunning Logistics Node.")
        updated_logistics = process_logistics(
            # pyrefly: ignore [unexpected-keyword]
            state_or_context=updated_context,
            # pyrefly: ignore [unexpected-keyword]
            visa_verdict=updated_visa,
        )
    else:
        log.info("Re-planning: Reusing unaffected LogisticsPlan.")
        updated_logistics = current_state.get("logistics_plan")

    # Experience
    if affected["experience"]:
        log.info("Re-planning: Rerunning Experience Node.")
        updated_experience = process_experience(
            # pyrefly: ignore [unexpected-keyword]
            state_or_context=updated_context,
            logistics_plan=updated_logistics,
        )
    else:
        log.info("Re-planning: Reusing unaffected ExperiencePlan.")
        updated_experience = current_state.get("experience_plan")

    # Budget Engine (always recomputes deterministically)
    log.info("Re-planning: Deterministically recalculating BudgetBreakdown.")
    updated_budget = process_budget(
        state_or_context=updated_context,
        logistics_plan=updated_logistics,
        experience_plan=updated_experience,
        visa_verdict=updated_visa,
    )

    # Optimizer Node (always re-evaluates)
    log.info("Re-planning: Deterministically re-evaluating Optimizer.")
    opt_output = process_optimizer(
        state_or_context=updated_context,
        budget_breakdown=updated_budget,
        logistics_plan=updated_logistics,
        experience_plan=updated_experience,
        visa_verdict=updated_visa,
    )

    # Assemble updated state
    new_state: PlanGraphState = dict(current_state)  # type: ignore
    new_state["trip_context"] = updated_context
    new_state["visa_verdict"] = updated_visa
    new_state["logistics_plan"] = opt_output.logistics_plan or updated_logistics
    new_state["experience_plan"] = opt_output.experience_plan or updated_experience
    new_state["budget_breakdown"] = opt_output.budget_breakdown or updated_budget
    new_state["optimization_result"] = opt_output.optimization_result
    new_state["replan_requested"] = True
    new_state["replan_proposal"] = {
        "proposal_type": proposal_type,
        "target_value": target_value,
        "reused_components": [k for k, v in affected.items() if not v],
        "rerun_components": [k for k, v in affected.items() if v],
    }

    status = route_optimizer_outcome(new_state)
    if status == "USER_DECISION_REQUIRED":
        new_state["plan_status"] = "NEEDS_USER_DECISION"
    elif status == "INFEASIBLE":
        new_state["plan_status"] = "INFEASIBLE"
    else:
        new_state["plan_status"] = "REPLANNED"

    return new_state
