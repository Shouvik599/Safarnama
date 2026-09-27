"""Phase 17 — Real-Time API Streaming: LangGraph Event Streamer.

Provides asynchronous event generators for streaming multi-agent planning progress:
- stream_planning_graph(): Streams step-by-step progress events (SSE) from the LangGraph StateGraph.
- stream_replan_workflow(): Streams selective re-planning events for traveler decision trade-offs.

Adheres to:
- Architecture Section 20 (API Streaming & SSE Contracts).
- Rule 49 (Real-time API Streaming, Progress Events & Client Information Hygiene).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from src.graph.edges import determine_affected_components, route_optimizer_outcome
from src.graph.state import PlanGraphState, create_initial_state
from src.graph.workflow import get_planning_graph
from src.models.trip import TripContext
from src.nodes.budget_node import process_budget
from src.nodes.experience_node import process_experience
from src.nodes.logistics_node import process_logistics
from src.nodes.optimizer_node import (
    create_replanning_proposal,
    process_optimizer,
)
from src.nodes.synthesizer_node import process_synthesizer
from src.nodes.visa_node import process_visa

log = logging.getLogger(__name__)


class PlanningEvent(BaseModel):
    """Server-Sent Event (SSE) model for real-time planning workflow updates (Phase 17)."""

    event: str = Field(
        ...,
        description="Event identifier (e.g., planning_started, logistics_completed).",
    )
    stage: str = Field(
        ...,
        description="Workflow stage (e.g., intake, logistics, synthesizer).",
    )
    message: str = Field(
        ...,
        description="Human-readable milestone description.",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured milestone payload or summary.",
    )
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_sse(self) -> str:
        """Format as valid SSE event message."""
        payload = self.model_dump_json()
        return f"event: {self.event}\ndata: {payload}\n\n"


# Primary planning nodes to track during LangGraph execution
_PLANNING_NODES = {
    "intake",
    "date_optimizer",
    "visa",
    "logistics",
    "experience",
    "budget",
    "optimizer",
    "synthesizer",
}


def _get_trip_duration(ctx: TripContext | None, req: dict[str, Any]) -> int:
    """Safely extract trip duration in days from TripContext or raw request dict."""
    if ctx and ctx.dates:
        if ctx.dates.duration_days is not None:
            return ctx.dates.duration_days
        if ctx.dates.start_date and ctx.dates.end_date:
            try:
                s = datetime.strptime(str(ctx.dates.start_date), "%Y-%m-%d")
                e = datetime.strptime(str(ctx.dates.end_date), "%Y-%m-%d")
                return max(1, (e - s).days)
            except Exception:
                pass
    return req.get("duration_days") or 1


def _get_trip_budget_inr(ctx: TripContext | None, req: dict[str, Any]) -> float:
    """Safely extract total budget in INR from TripContext or raw request dict."""
    if ctx and ctx.budget:
        if ctx.party:
            return float(ctx.budget.total_budget_inr(ctx.party))
        return float(ctx.budget.amount_inr)
    return float(req.get("budget_inr") or 0.0)


def _summarize_intake_output(output: dict[str, Any]) -> dict[str, Any]:
    """Extract clean client-facing metadata from intake node output."""
    context: TripContext | None = output.get("trip_context")
    scope = output.get("travel_scope")
    if not scope and context:
        scope = context.scope.value
    return {
        "travel_scope": scope or "DOMESTIC",
        "origin": output.get("origin") or (context.origin if context else ""),
        "destinations": output.get("destinations") or (context.destinations if context else []),
        "duration_days": output.get("effective_duration_days") or _get_trip_duration(context, {}),
        "total_budget_inr": output.get("total_budget_inr") or _get_trip_budget_inr(context, {}),
    }


def _summarize_date_output(output: dict[str, Any]) -> dict[str, Any]:
    """Extract clean client-facing metadata from date_optimizer node output."""
    date_res = output.get("date_options")
    if not date_res:
        return {"mode": "EXACT", "status": "Exact dates preserved"}

    rec_window = None
    if getattr(date_res, "recommended", None):
        rec_cand = date_res.recommended
        rec_window = {
            "start_date": str(rec_cand.start_date),
            "end_date": str(rec_cand.end_date),
            "composite_score": rec_cand.composite_score,
            "is_weather_favorable": rec_cand.is_weather_favorable,
        }

    return {
        "mode": (date_res.mode.value if hasattr(date_res.mode, "value") else str(date_res.mode)),
        "recommended_window": rec_window,
        "alternatives_count": len(date_res.alternatives),
        "evaluation_summary": date_res.evaluation_summary,
    }


def _summarize_visa_output(output: dict[str, Any]) -> dict[str, Any]:
    """Extract clean client-facing metadata from visa node output."""
    verdict = output.get("visa_verdict")
    if not verdict:
        return {"status": "Visa evaluation not required"}

    if verdict.is_domestic_bypass:
        return {"is_domestic_bypass": True, "status": "DOMESTIC_BYPASS"}

    countries_summary = []
    for c in verdict.countries:
        countries_summary.append(
            {
                "country_name": c.country_name,
                "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                "visa_type": c.visa_type_label,
                "fee_inr": c.visa_fee_inr,
                "is_live_verified": c.is_live_verified,
            }
        )

    return {
        "is_domestic_bypass": False,
        "countries_count": len(verdict.countries),
        "total_visa_cost_inr": verdict.total_visa_cost_inr,
        "schengen_single_visa_applicable": verdict.schengen_single_visa_applicable,
        "requires_advance_application": verdict.requires_advance_application,
        "countries": countries_summary,
    }


def _summarize_logistics_output(output: dict[str, Any]) -> dict[str, Any]:
    """Extract clean client-facing metadata from logistics node output."""
    log_plan = output.get("logistics_plan")
    if not log_plan:
        return {}

    return {
        "transport_legs_count": len(log_plan.transport_legs),
        "hotel_stays_count": len(log_plan.hotel_stays),
        "total_transport_cost_inr": log_plan.total_transport_cost_inr,
        "total_accommodation_cost_inr": log_plan.total_accommodation_cost_inr,
    }


def _summarize_experience_output(output: dict[str, Any]) -> dict[str, Any]:
    """Extract clean client-facing metadata from experience node output."""
    exp_plan = output.get("experience_plan")
    if not exp_plan:
        return {}

    total_activities = sum(len(d.activities) for d in exp_plan.days)
    total_meals = sum(len(d.meals) for d in exp_plan.days)
    return {
        "total_days": exp_plan.total_days,
        "daily_plans_count": len(exp_plan.days),
        "total_activities_count": total_activities,
        "total_meals_count": total_meals,
    }


def _summarize_budget_output(output: dict[str, Any]) -> dict[str, Any]:
    """Extract clean client-facing metadata from budget node output."""
    b_breakdown = output.get("budget_breakdown")
    if not b_breakdown:
        return {}

    variance = b_breakdown.variance
    var_status = (
        variance.status.value if hasattr(variance.status, "value") else str(variance.status)
    )
    return {
        "subtotal_inr": b_breakdown.subtotal_inr,
        "total_with_contingency_inr": b_breakdown.total_with_contingency_inr,
        "user_budget_inr": variance.user_budget_inr,
        "variance_status": var_status,
        "variance_amount_inr": variance.variance_inr,
        "variance_percentage": variance.variance_percentage,
    }


def _summarize_optimizer_output(output: dict[str, Any]) -> dict[str, Any]:
    """Extract clean client-facing metadata from optimizer node output."""
    opt_res = output.get("optimization_result")
    if not opt_res:
        return {}

    action_str = opt_res.action.value if hasattr(opt_res.action, "value") else str(opt_res.action)
    return {
        "action": action_str,
        "savings_inr": opt_res.savings_inr,
        "description": opt_res.description,
        "trade_offs_count": len(opt_res.trade_offs),
        "alternatives_count": len(opt_res.alternatives_presented),
    }


async def stream_planning_graph(
    initial_input: dict[str, Any] | PlanGraphState | TripContext,
) -> AsyncGenerator[PlanningEvent, None]:
    """Stream real-time progress events from the Safarnama LangGraph StateGraph.

    Args:
        initial_input: TripContext, PlanGraphState, or dictionary with request parameters.

    Yields:
        PlanningEvent instances representing sequential milestone updates.
    """
    # 1. State initialization
    if isinstance(initial_input, TripContext):
        state = create_initial_state(trip_context=initial_input)
    elif not isinstance(initial_input, dict):
        raise TypeError(
            f"Expected dictionary, PlanGraphState, or TripContext, got: {type(initial_input)}"
        )
    elif "request" not in initial_input and "trip_context" not in initial_input:
        state = create_initial_state(request=initial_input)
    else:
        state = create_initial_state(
            request=initial_input.get("request") or initial_input,
            trip_context=initial_input.get("trip_context"),
        )
        for k, v in initial_input.items():
            if v is not None:
                state[k] = v

    ctx: TripContext | None = state.get("trip_context")
    req = state.get("request") or {}

    # Extract initial request metadata
    origin = ctx.origin if ctx else req.get("origin", "")
    destinations = (
        ctx.destinations if ctx else (req.get("destinations") or [req.get("destination", "")])
    )
    if isinstance(destinations, str):
        destinations = [destinations]

    # Emit planning_started immediately
    yield PlanningEvent(
        event="planning_started",
        stage="init",
        message="Initiating Safarnama multi-agent planning engine",
        data={
            "origin": origin,
            "destinations": destinations,
            "budget_inr": _get_trip_budget_inr(ctx, req),
            "duration_days": _get_trip_duration(ctx, req),
        },
    )

    seen_warnings: set[str] = set()
    graph = get_planning_graph()
    final_itinerary_emitted = False

    try:
        async for event in graph.astream_events(state, version="v2"):
            event_type = event.get("event")
            name = event.get("name")

            if not name or name not in _PLANNING_NODES:
                continue

            # Handle Node Start
            if event_type == "on_chain_start":
                if name == "date_optimizer":
                    yield PlanningEvent(
                        event="date_optimization_started",
                        stage="date_optimizer",
                        message="Evaluating candidate travel dates and seasonal conditions",
                    )
                elif name == "visa":
                    yield PlanningEvent(
                        event="visa_started",
                        stage="visa",
                        message="Verifying visa rules and entry requirements for Indian passport",
                    )
                elif name == "logistics":
                    yield PlanningEvent(
                        event="logistics_started",
                        stage="logistics",
                        message="Researching transport routes and hotel accommodations",
                    )
                elif name == "experience":
                    yield PlanningEvent(
                        event="experience_started",
                        stage="experience",
                        message="Curating points of interest, daily activities, and dining spots",
                    )
                elif name == "budget":
                    yield PlanningEvent(
                        event="budget_started",
                        stage="budget",
                        message="Aggregating itemized costs and computing budget breakdown",
                    )
                elif name == "optimizer":
                    yield PlanningEvent(
                        event="optimization_started",
                        stage="optimizer",
                        message="Evaluating budget constraints and optimization feasibility",
                    )
                elif name == "synthesizer":
                    yield PlanningEvent(
                        event="synthesizer_started",
                        stage="synthesizer",
                        message="Synthesizing final comprehensive itinerary deliverable",
                    )

            # Handle Node End
            elif event_type == "on_chain_end":
                data_dict = event.get("data") or {}
                output = data_dict.get("output") or {}

                if not isinstance(output, dict):
                    continue

                # Check for node failure
                errors = output.get("errors") or []
                if errors or output.get("plan_status") == "FAILED":
                    yield PlanningEvent(
                        event="error",
                        stage=name,
                        message=f"Planning halted at stage '{name}': {'; '.join(errors)}",
                        data={"errors": errors, "plan_status": "FAILED"},
                    )
                    return

                # Check for new warnings
                node_warnings = output.get("warnings") or []
                for w in node_warnings:
                    if w not in seen_warnings:
                        seen_warnings.add(w)
                        yield PlanningEvent(
                            event="warning",
                            stage=name,
                            message=w,
                            data={"warning": w},
                        )

                # Node-specific completion events
                if name == "intake":
                    yield PlanningEvent(
                        event="intake_completed",
                        stage="intake",
                        message="Trip constraints and preferences validated",
                        data=_summarize_intake_output(output),
                    )
                elif name == "date_optimizer":
                    yield PlanningEvent(
                        event="date_optimization_completed",
                        stage="date_optimizer",
                        message="Travel dates and seasonal conditions evaluated",
                        data=_summarize_date_output(output),
                    )
                elif name == "visa":
                    yield PlanningEvent(
                        event="visa_completed",
                        stage="visa",
                        message="Visa requirements resolved",
                        data=_summarize_visa_output(output),
                    )
                elif name == "logistics":
                    yield PlanningEvent(
                        event="logistics_completed",
                        stage="logistics",
                        message="Transport routing and lodging options finalized",
                        data=_summarize_logistics_output(output),
                    )
                elif name == "experience":
                    exp_summary = _summarize_experience_output(output)
                    days_count = exp_summary.get("daily_plans_count", 0)
                    yield PlanningEvent(
                        event="experience_completed",
                        stage="experience",
                        message=f"Curated {days_count}-day activity and dining itinerary",
                        data=exp_summary,
                    )
                elif name == "budget":
                    b_summary = _summarize_budget_output(output)
                    total_inr = b_summary.get("total_with_contingency_inr", 0.0)
                    v_status = b_summary.get("variance_status", "Calculated")
                    yield PlanningEvent(
                        event="budget_calculated",
                        stage="budget",
                        message=f"Budget calculated: INR {total_inr:,.2f} ({v_status})",
                        data=b_summary,
                    )

                elif name == "optimizer":
                    opt_summary = _summarize_optimizer_output(output)
                    action = opt_summary.get("action", "NONE")
                    yield PlanningEvent(
                        event="optimization_completed",
                        stage="optimizer",
                        message=f"Budget optimization action: {action}",
                        data=opt_summary,
                    )
                elif name == "synthesizer":
                    final_itinerary = output.get("final_itinerary")
                    resolved_status = output.get("plan_status") or (
                        final_itinerary.plan_status if final_itinerary else "COMPLETED"
                    )
                    title = final_itinerary.title if final_itinerary else "Trip Itinerary"
                    summary = final_itinerary.summary if final_itinerary else ""
                    itin_data = final_itinerary.model_dump(mode="json") if final_itinerary else None

                    yield PlanningEvent(
                        event="planning_completed",
                        stage="complete",
                        message=f"Final itinerary synthesized successfully: '{title}'",
                        data={
                            "plan_status": resolved_status,
                            "title": title,
                            "summary": summary,
                            "itinerary": itin_data,
                        },
                    )
                    final_itinerary_emitted = True

    except Exception as exc:
        log.error("Unhandled exception during planning stream: %s", exc, exc_info=True)
        yield PlanningEvent(
            event="error",
            stage="stream",
            message=f"Planning stream encountered an unexpected error: {str(exc)}",
            data={"errors": [str(exc)], "plan_status": "FAILED"},
        )
        return

    # If stream ended without error and without synthesizer event for any reason
    if not final_itinerary_emitted:
        yield PlanningEvent(
            event="error",
            stage="stream",
            message="Planning stream terminated before synthesizing an itinerary",
            data={"errors": ["Workflow terminated prematurely"], "plan_status": "FAILED"},
        )


async def stream_replan_workflow(
    current_state: PlanGraphState,
    proposal_type: str,
    target_value: Any = None,
) -> AsyncGenerator[PlanningEvent, None]:
    """Stream selective re-planning execution following a traveler trade-off decision.

    Reuses unaffected components while providing progress updates for rerun components.

    Args:
        current_state: Existing PlanGraphState from previous planning execution.
        proposal_type: Type of proposal (e.g. INCREASE_BUDGET, ADJUST_TRAVEL_STYLE).
        target_value: Optional target parameter value.

    Yields:
        PlanningEvent instances representing sequential milestone updates.
    """
    context = current_state.get("trip_context")
    if not context:
        yield PlanningEvent(
            event="error",
            stage="replan",
            message="Cannot re-plan without an existing 'trip_context' in state.",
            data={"errors": ["Missing trip_context"], "plan_status": "FAILED"},
        )
        return

    # 1. Update TripContext deterministically
    try:
        updated_context = create_replanning_proposal(context, proposal_type, target_value)
    except Exception as exc:
        yield PlanningEvent(
            event="error",
            stage="replan",
            message=f"Invalid re-planning proposal: {exc}",
            data={"errors": [str(exc)], "plan_status": "FAILED"},
        )
        return

    # 2. Determine affected components
    affected = determine_affected_components(proposal_type)

    yield PlanningEvent(
        event="planning_started",
        stage="replan",
        message=f"Initiating re-planning for decision: {proposal_type}",
        data={
            "proposal_type": proposal_type,
            "target_value": target_value,
            "reused_components": [k for k, v in affected.items() if not v],
            "rerun_components": [k for k, v in affected.items() if v],
        },
    )

    # 3. Selectively rerun or reuse components
    # Visa
    if affected["visa"] and updated_context.scope.value.upper() == "INTERNATIONAL":
        yield PlanningEvent(
            event="visa_started",
            stage="visa",
            message="Re-evaluating visa regulations for updated destinations",
        )
        updated_visa = process_visa(updated_context)
        yield PlanningEvent(
            event="visa_completed",
            stage="visa",
            message="Visa regulations re-evaluated",
            data=_summarize_visa_output({"visa_verdict": updated_visa}),
        )
    else:
        updated_visa = current_state.get("visa_verdict")

    # Logistics
    if affected["logistics"]:
        yield PlanningEvent(
            event="logistics_started",
            stage="logistics",
            message="Re-planning transport routes and accommodations",
        )
        updated_logistics = process_logistics(
            state_or_context=updated_context,
            visa_verdict=updated_visa,
        )
        yield PlanningEvent(
            event="logistics_completed",
            stage="logistics",
            message="Transport routes and accommodations updated",
            data=_summarize_logistics_output({"logistics_plan": updated_logistics}),
        )
    else:
        updated_logistics = current_state.get("logistics_plan")

    # Experience
    if affected["experience"]:
        yield PlanningEvent(
            event="experience_started",
            stage="experience",
            message="Re-curating daily activities and dining options",
        )
        updated_experience = process_experience(
            state_or_context=updated_context,
            logistics_plan=updated_logistics,
        )
        yield PlanningEvent(
            event="experience_completed",
            stage="experience",
            message="Daily activities and dining options updated",
            data=_summarize_experience_output({"experience_plan": updated_experience}),
        )
    else:
        updated_experience = current_state.get("experience_plan")

    # Budget (always recalculated)
    yield PlanningEvent(
        event="budget_started",
        stage="budget",
        message="Deterministically recalculating budget breakdown",
    )
    updated_budget = process_budget(
        state_or_context=updated_context,
        logistics_plan=updated_logistics,
        experience_plan=updated_experience,
        visa_verdict=updated_visa,
    )
    yield PlanningEvent(
        event="budget_calculated",
        stage="budget",
        message=f"Recalculated budget: INR {updated_budget.total_with_contingency_inr:,.2f}",
        data=_summarize_budget_output({"budget_breakdown": updated_budget}),
    )

    # Optimizer (always re-evaluated)
    yield PlanningEvent(
        event="optimization_started",
        stage="optimizer",
        message="Re-evaluating optimization constraints",
    )
    opt_output = process_optimizer(
        state_or_context=updated_context,
        budget_breakdown=updated_budget,
        logistics_plan=updated_logistics,
        experience_plan=updated_experience,
        visa_verdict=updated_visa,
    )
    yield PlanningEvent(
        event="optimization_completed",
        stage="optimizer",
        message=f"Re-planning optimization action: {opt_output.optimization_result.action.value}",
        data=_summarize_optimizer_output({"optimization_result": opt_output.optimization_result}),
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

    status = route_optimizer_outcome(new_state)
    if status == "USER_DECISION_REQUIRED":
        plan_status = "NEEDS_USER_DECISION"
    elif status == "INFEASIBLE":
        plan_status = "INFEASIBLE"
    else:
        plan_status = "REPLANNED"

    yield PlanningEvent(
        event="synthesizer_started",
        stage="synthesizer",
        message="Synthesizing updated itinerary",
    )
    final_itinerary = process_synthesizer(
        trip_context=updated_context,
        logistics_plan=opt_output.logistics_plan or updated_logistics,
        experience_plan=opt_output.experience_plan or updated_experience,
        budget_breakdown=opt_output.budget_breakdown or updated_budget,
        visa_verdict=updated_visa,
        date_options=current_state.get("date_options"),
        optimization_result=opt_output.optimization_result,
        warnings=new_state.get("warnings") or [],
        plan_status=plan_status,
    )

    yield PlanningEvent(
        event="planning_completed",
        stage="complete",
        message=f"Updated itinerary synthesized: '{final_itinerary.title}'",
        data={
            "plan_status": plan_status,
            "title": final_itinerary.title,
            "summary": final_itinerary.summary,
            "itinerary": final_itinerary.model_dump(mode="json"),
            "replan_summary": {
                "proposal_type": proposal_type,
                "target_value": target_value,
                "reused_components": [k for k, v in affected.items() if not v],
                "rerun_components": [k for k, v in affected.items() if v],
            },
        },
    )
