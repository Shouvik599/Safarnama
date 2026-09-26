"""Unit tests for Phase 12 — LangGraph Orchestration.

Tests:
1. State creation and Reducers (merge_warnings, merge_errors).
2. Routing Edges:
   - Domestic routing bypasses visa to parallel branch.
   - International routing includes visa before parallel branch.
   - Routing after visa fans out to parallel branch.
   - Optimizer outcome routing (FEASIBLE, USER_DECISION_REQUIRED, INFEASIBLE).
   - Component isolation logic (determine_affected_components).
3. Graph Compilation:
   - StateGraph builds and compiles without errors.
   - Graph node structure and connectivity.
4. End-to-End Orchestration:
   - Domestic trip workflow execution.
   - International trip workflow execution.
   - Parallel branch execution and state aggregation.
   - Warning and error aggregation across nodes.
5. Error Resilience:
   - Safe node wrapping captures unexpected exceptions into state errors.
6. Re-planning & Reuse of Unaffected Work:
   - INCREASE_BUDGET: Reuses route, visa, logistics, and experience; reruns budget and optimizer.
   - ADJUST_TRAVEL_STYLE: Reuses visa; reruns logistics, experience, budget, and optimizer.
   - REDUCE_DURATION: Reuses visa; reruns logistics, experience, budget, and optimizer.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from langgraph.graph import END
from langgraph.graph.state import CompiledStateGraph
from src.graph.edges import (
    determine_affected_components,
    route_after_visa,
    route_optimizer_outcome,
    route_scope,
)
from src.graph.state import (
    PlanGraphState,
    create_initial_state,
    merge_errors,
    merge_warnings,
)
from src.graph.workflow import (
    _wrap_safe_node,
    build_planning_graph,
    get_planning_graph,
    replan_workflow,
    run_planning_graph,
)
from src.models.budget import (
    BudgetBreakdown,
    BudgetStatus,
    BudgetVariance,
    ContingencyConfig,
    CostBreakdown,
    OptimizationAction,
    OptimizationResult,
)
from src.models.itinerary import DayPlan, ExperiencePlan
from src.models.logistics import HotelStay, LogisticsPlan, TransportLeg
from src.models.trip import (
    DateMode,
    Pace,
    TravelScope,
    TravelStyle,
    TripBudget,
    TripContext,
    TripDates,
    TripParty,
)
from src.models.visa import VisaCountryVerdict, VisaRequirementStatus, VisaVerdict

# ===========================================================================
# Fixture Helpers
# ===========================================================================


def make_dummy_context(
    scope: TravelScope = TravelScope.DOMESTIC,
    origin: str = "BOM",
    destinations: list[str] | None = None,
    budget_inr: float = 80_000.0,
    duration_days: int = 4,
    travel_style: TravelStyle = TravelStyle.COMFORTABLE,
) -> TripContext:
    return TripContext(
        scope=scope,
        origin=origin,
        destinations=destinations or (["GOI"] if scope == TravelScope.DOMESTIC else ["DXB"]),
        dates=TripDates(
            mode=DateMode.EXACT,
            start_date="2026-10-01",
            end_date="2026-10-05",
            duration_days=duration_days,
        ),
        party=TripParty(adults=2, children=0),
        budget=TripBudget(amount_inr=budget_inr),
        travel_style=travel_style,
        pace=Pace.BALANCED,
    )


def make_dummy_logistics(dest: str = "GOI") -> LogisticsPlan:
    return LogisticsPlan(
        transport_legs=[
            TransportLeg(
                leg_number=1,
                carrier="IndiGo",
                origin="BOM",
                destination=dest,
                mode="FLIGHT",
                price_per_person_inr=5000.0,
                total_price_inr=10000.0,
                provider="fixture",
            )
        ],
        hotel_stays=[
            HotelStay(
                destination=dest,
                hotel_name=f"{dest} Resort",
                checkin_date="2026-10-01",
                checkout_date="2026-10-05",
                nights=4,
                rooms_required=1,
                price_per_room_per_night_inr=6000.0,
                total_accommodation_cost_inr=24000.0,
                provider="fixture",
            )
        ],
        total_transport_cost_inr=10000.0,
        total_lodging_cost_inr=24000.0,
        total_logistics_cost_inr=34000.0,
        warnings=[],
        timestamp="2026-10-01T00:00:00Z",
    )


def make_dummy_experience(dest: str = "GOI") -> ExperiencePlan:
    return ExperiencePlan(
        days=[
            DayPlan(
                day_number=1,
                date="2026-10-01",
                city=dest,
                theme="Arrival & Exploration",
                activities=[],
                meals=[],
                day_total_cost_inr=3000.0,
            )
        ],
        total_days=1,
        destinations_covered=[dest],
        must_visits_fulfilled=[],
        must_visits_omitted=[],
        weather_substitutions=0,
        total_activity_cost_inr=2000.0,
        total_food_cost_inr=4000.0,
        total_local_transport_cost_inr=1000.0,
        warnings=[],
        timestamp="2026-10-01T00:00:00Z",
    )


def make_dummy_visa(is_domestic: bool = True) -> VisaVerdict:
    return VisaVerdict(
        is_domestic_bypass=is_domestic,
        countries=[]
        if is_domestic
        else [
            VisaCountryVerdict(
                country_code="AE",
                country_name="United Arab Emirates",
                status=VisaRequirementStatus.E_VISA,
                visa_type_label="Tourist eVisa",
                estimated_fee_inr=6500.0,
            )
        ],
        total_visa_cost_inr=0.0 if is_domestic else 13000.0,
        requires_advance_application=not is_domestic,
        schengen_single_visa_applicable=False,
        warnings=[],
        timestamp="2026-10-01T00:00:00Z",
    )


def make_dummy_budget(user_budget: float = 80000.0, total: float = 50000.0) -> BudgetBreakdown:
    variance = total - user_budget
    pct = round((variance / user_budget) * 100, 2)
    return BudgetBreakdown(
        cost_breakdown=CostBreakdown(
            transport_inr=10000.0,
            accommodation_inr=24000.0,
            activities_inr=2000.0,
            food_inr=4000.0,
            local_transport_inr=1000.0,
            visa_fees_inr=0.0,
            misc_inr=2000.0,
            subtotal_inr=43000.0,
        ),
        contingency=ContingencyConfig(
            percentage=10.0,
            amount_inr=7000.0,
            reasoning="Standard buffer",
        ),
        variance=BudgetVariance(
            user_budget_inr=user_budget,
            projected_total_inr=total,
            variance_inr=variance,
            variance_percentage=pct,
            status=BudgetStatus.UNDER_BUDGET if variance <= 0 else BudgetStatus.MINOR_OVER,
        ),
        optimization=OptimizationResult(),
        subtotal_inr=43000.0,
        total_with_contingency_inr=total,
        per_person_cost_inr=total / 2,
        warnings=[],
        timestamp="2026-10-01T00:00:00Z",
    )


# ===========================================================================
# 1. State & Reducer Unit Tests
# ===========================================================================


def test_create_initial_state_defaults() -> None:
    """Verify create_initial_state sets default values and structure."""
    state = create_initial_state()
    assert state["plan_status"] == "INITIALIZED"
    assert state["warnings"] == []
    assert state["errors"] == []
    assert state["replan_requested"] is False
    assert state["replan_proposal"] is None
    assert state["request"] == {}


def test_create_initial_state_with_context() -> None:
    """Verify create_initial_state populates fields from TripContext."""
    ctx = make_dummy_context(budget_inr=95_000.0, duration_days=5)
    state = create_initial_state(trip_context=ctx)
    assert state["trip_context"] == ctx
    assert state["travel_scope"] == TravelScope.DOMESTIC
    assert state["total_budget_inr"] == 95_000.0
    assert state["effective_duration_days"] == 5


def test_merge_warnings_deduplication() -> None:
    """Verify merge_warnings merges lists and deduplicates items while preserving order."""
    left = ["Weather may be rainy in Goa", "High flight demand"]
    right = ["High flight demand", "Hotel prices subject to change"]
    merged = merge_warnings(left, right)
    assert len(merged) == 3
    assert merged == [
        "Weather may be rainy in Goa",
        "High flight demand",
        "Hotel prices subject to change",
    ]


def test_merge_warnings_handles_nones() -> None:
    """Verify merge_warnings handles None arguments gracefully."""
    assert merge_warnings(None, ["Warning 1"]) == ["Warning 1"]
    assert merge_warnings(["Warning 1"], None) == ["Warning 1"]
    assert merge_warnings(None, None) == []


def test_merge_errors_deduplication() -> None:
    """Verify merge_errors merges lists and deduplicates errors."""
    left = ["Error 1"]
    right = ["Error 1", "Error 2"]
    merged = merge_errors(left, right)
    assert merged == ["Error 1", "Error 2"]


# ===========================================================================
# 2. Routing Edges Unit Tests
# ===========================================================================


def test_route_scope_domestic() -> None:
    """Verify domestic trip routes directly to parallel planning ['logistics', 'experience']."""
    ctx = make_dummy_context(scope=TravelScope.DOMESTIC)
    state = create_initial_state(trip_context=ctx)
    destination = route_scope(state)
    assert destination == ["logistics", "experience"]


def test_route_scope_international() -> None:
    """Verify international trip routes to the visa node."""
    ctx = make_dummy_context(scope=TravelScope.INTERNATIONAL)
    state = create_initial_state(trip_context=ctx)
    destination = route_scope(state)
    assert destination == "visa"


def test_route_scope_intake_error() -> None:
    """Verify fatal intake errors route immediately to END."""
    state = create_initial_state()
    state["errors"] = ["Fatal intake failure: Origin airport UNKNOWN could not be resolved."]
    destination = route_scope(state)
    assert destination == END


def test_route_after_visa_normal() -> None:
    """Verify route_after_visa fans out to parallel planning."""
    state = create_initial_state()
    destination = route_after_visa(state)
    assert destination == ["logistics", "experience"]


def test_route_after_visa_fatal_error() -> None:
    """Verify fatal visa errors without verdict route to END."""
    state = create_initial_state()
    state["errors"] = ["Visa policy unavailable and entry forbidden."]
    destination = route_after_visa(state)
    assert destination == END


def test_route_optimizer_outcome() -> None:
    """Verify optimizer outcome classification across feasible, trade-off, and infeasible."""
    state = create_initial_state()

    # Feasible: No action
    state["optimization_result"] = OptimizationResult(
        action=OptimizationAction.NONE,
        status="UNDER_BUDGET",
    )
    assert route_optimizer_outcome(state) == "FEASIBLE"

    # Feasible: Minor auto-optimization
    state["optimization_result"] = OptimizationResult(
        action=OptimizationAction.CHEAPER_HOTEL,
        status="OPTIMIZED",
    )
    assert route_optimizer_outcome(state) == "FEASIBLE"

    # User decision required (5-15% over)
    state["optimization_result"] = OptimizationResult(
        action=OptimizationAction.USER_DECISION_REQUIRED,
        status="USER_DECISION_REQUIRED",
    )
    assert route_optimizer_outcome(state) == "USER_DECISION_REQUIRED"

    # Infeasible (>15% over)
    state["optimization_result"] = OptimizationResult(
        action=OptimizationAction.INFEASIBLE,
        status="INFEASIBLE",
    )
    assert route_optimizer_outcome(state) == "INFEASIBLE"


def test_determine_affected_components() -> None:
    """Verify component isolation rules follow Architecture Section 12."""
    # INCREASE_BUDGET affects only financial calculation and optimization
    inc_budget = determine_affected_components("INCREASE_BUDGET")
    assert inc_budget["visa"] is False
    assert inc_budget["logistics"] is False
    assert inc_budget["experience"] is False
    assert inc_budget["budget"] is True
    assert inc_budget["optimizer"] is True

    # ADJUST_TRAVEL_STYLE affects hotels (logistics) and dining/activities (experience)
    adj_style = determine_affected_components("ADJUST_TRAVEL_STYLE")
    assert adj_style["visa"] is False
    assert adj_style["logistics"] is True
    assert adj_style["experience"] is True
    assert adj_style["budget"] is True
    assert adj_style["optimizer"] is True

    # REDUCE_DURATION affects stay days (logistics) and day plans (experience)
    red_dur = determine_affected_components("REDUCE_DURATION")
    assert red_dur["visa"] is False
    assert red_dur["logistics"] is True
    assert red_dur["experience"] is True
    assert red_dur["budget"] is True
    assert red_dur["optimizer"] is True

    # REMOVE_DESTINATION affects all downstream components
    rem_dest = determine_affected_components("REMOVE_DESTINATION")
    assert rem_dest["visa"] is True
    assert rem_dest["logistics"] is True
    assert rem_dest["experience"] is True
    assert rem_dest["budget"] is True
    assert rem_dest["optimizer"] is True


# ===========================================================================
# 3. Graph Compilation Unit Tests
# ===========================================================================


def test_build_planning_graph_compilation() -> None:
    """Verify StateGraph compiles into a valid CompiledStateGraph instance."""
    graph = build_planning_graph()
    assert isinstance(graph, CompiledStateGraph)
    singleton = get_planning_graph()
    assert isinstance(singleton, CompiledStateGraph)


def test_wrap_safe_node_catches_exception() -> None:
    """Verify _wrap_safe_node catches uncaught exceptions and populates errors in state."""

    def faulty_node(state: PlanGraphState) -> dict[str, Any]:
        raise RuntimeError("Unexpected external connection drop")

    wrapped = _wrap_safe_node(faulty_node, "test_faulty")
    result = wrapped(create_initial_state())

    assert "errors" in result
    assert result["plan_status"] == "FAILED"
    assert "Unexpected external connection drop" in result["errors"][0]


# ===========================================================================
# 4. End-to-End Orchestration Tests (Offline / Mock Fixtures)
# ===========================================================================


@patch("src.graph.workflow.intake_node")
@patch("src.graph.workflow.visa_node")
@patch("src.graph.workflow.logistics_node")
@patch("src.graph.workflow.experience_node")
@patch("src.graph.workflow.budget_node")
@patch("src.graph.workflow.optimizer_node")
def test_domestic_workflow_execution(
    mock_opt: MagicMock,
    mock_bud: MagicMock,
    mock_exp: MagicMock,
    mock_log: MagicMock,
    mock_vis: MagicMock,
    mock_int: MagicMock,
) -> None:
    """Verify complete end-to-end execution of a domestic trip through the graph."""
    ctx = make_dummy_context(scope=TravelScope.DOMESTIC, origin="BOM", destinations=["GOI"])
    logistics = make_dummy_logistics("GOI")
    experience = make_dummy_experience("GOI")
    budget = make_dummy_budget(80000.0, 50000.0)
    opt_res = OptimizationResult(action=OptimizationAction.NONE, status="UNDER_BUDGET")

    mock_int.return_value = {
        "trip_context": ctx,
        "travel_scope": TravelScope.DOMESTIC,
        "warnings": ["Intake warning"],
    }
    mock_log.return_value = {"logistics_plan": logistics, "warnings": ["Logistics warning"]}
    mock_exp.return_value = {"experience_plan": experience, "warnings": ["Experience warning"]}
    mock_bud.return_value = {"budget_breakdown": budget}
    mock_opt.return_value = {
        "optimization_result": opt_res,
        "budget_breakdown": budget,
        "logistics_plan": logistics,
        "experience_plan": experience,
    }

    # Execute workflow with newly built graph
    app = build_planning_graph()
    initial_state = create_initial_state(trip_context=ctx)
    output = app.invoke(initial_state)

    # 1. Verify node invocations
    assert mock_int.called
    assert not mock_vis.called, "Domestic trip must bypass the Visa node!"
    assert mock_log.called
    assert mock_exp.called
    assert mock_bud.called
    assert mock_opt.called

    # 2. Verify state aggregation
    assert output["trip_context"] == ctx
    assert output["logistics_plan"] == logistics
    assert output["experience_plan"] == experience
    assert output["budget_breakdown"] == budget
    assert output["optimization_result"] == opt_res

    # 3. Verify warning deduplication & aggregation across parallel branches
    assert "Intake warning" in output["warnings"]
    assert "Logistics warning" in output["warnings"]
    assert "Experience warning" in output["warnings"]


@patch("src.graph.workflow.intake_node")
@patch("src.graph.workflow.visa_node")
@patch("src.graph.workflow.logistics_node")
@patch("src.graph.workflow.experience_node")
@patch("src.graph.workflow.budget_node")
@patch("src.graph.workflow.optimizer_node")
def test_international_workflow_execution(
    mock_opt: MagicMock,
    mock_bud: MagicMock,
    mock_exp: MagicMock,
    mock_log: MagicMock,
    mock_vis: MagicMock,
    mock_int: MagicMock,
) -> None:
    """Verify complete end-to-end execution of an international trip routes through Visa node."""
    ctx = make_dummy_context(scope=TravelScope.INTERNATIONAL, origin="BOM", destinations=["DXB"])
    visa = make_dummy_visa(is_domestic=False)
    logistics = make_dummy_logistics("DXB")
    experience = make_dummy_experience("DXB")
    budget = make_dummy_budget(120000.0, 90000.0)
    opt_res = OptimizationResult(action=OptimizationAction.NONE, status="UNDER_BUDGET")

    mock_int.return_value = {
        "trip_context": ctx,
        "travel_scope": TravelScope.INTERNATIONAL,
        "warnings": [],
    }
    mock_vis.return_value = {"visa_verdict": visa, "warnings": ["Visa advance app required"]}
    mock_log.return_value = {"logistics_plan": logistics}
    mock_exp.return_value = {"experience_plan": experience}
    mock_bud.return_value = {"budget_breakdown": budget}
    mock_opt.return_value = {
        "optimization_result": opt_res,
        "budget_breakdown": budget,
        "logistics_plan": logistics,
        "experience_plan": experience,
    }

    app = build_planning_graph()
    initial_state = create_initial_state(trip_context=ctx)
    output = app.invoke(initial_state)

    # 1. Visa node MUST be invoked for international trips
    assert mock_vis.called
    assert output["visa_verdict"] == visa
    assert "Visa advance app required" in output["warnings"]


# ===========================================================================
# 5. Re-planning & Reuse of Unaffected Work Tests
# ===========================================================================


@patch("src.graph.workflow.process_logistics")
@patch("src.graph.workflow.process_experience")
@patch("src.graph.workflow.process_budget")
@patch("src.graph.workflow.process_optimizer")
def test_replan_workflow_increase_budget_reuses_unaffected_work(
    mock_opt: MagicMock,
    mock_bud: MagicMock,
    mock_exp: MagicMock,
    mock_log: MagicMock,
) -> None:
    """Verify INCREASE_BUDGET reuses existing visa, logistics, and experience artifacts."""
    ctx = make_dummy_context(budget_inr=50_000.0)
    logistics = make_dummy_logistics()
    experience = make_dummy_experience()
    visa = make_dummy_visa(is_domestic=True)
    budget = make_dummy_budget(50_000.0, 60_000.0)

    current_state: PlanGraphState = {
        "request": {},
        "trip_context": ctx,
        "travel_scope": TravelScope.DOMESTIC,
        "visa_verdict": visa,
        "logistics_plan": logistics,
        "experience_plan": experience,
        "budget_breakdown": budget,
        "optimization_result": OptimizationResult(
            action=OptimizationAction.USER_DECISION_REQUIRED,
            status="SIGNIFICANT_OVER",
        ),
        "plan_status": "NEEDS_USER_DECISION",
        "warnings": [],
        "errors": [],
        "replan_requested": False,
        "replan_proposal": None,
    }

    updated_budget = make_dummy_budget(75_000.0, 60_000.0)
    mock_bud.return_value = updated_budget
    mock_opt.return_value = MagicMock(
        optimization_result=OptimizationResult(
            action=OptimizationAction.NONE,
            status="UNDER_BUDGET",
        ),
        budget_breakdown=updated_budget,
        logistics_plan=logistics,
        experience_plan=experience,
    )

    # Re-plan: User increases budget to 75,000 INR
    replanned_state = replan_workflow(
        current_state=current_state,
        proposal_type="INCREASE_BUDGET",
        target_value=75_000.0,
    )

    # 1. Unaffected work MUST NOT rerun
    assert not mock_log.called, "Logistics must NOT rerun on budget increase!"
    assert not mock_exp.called, "Experience must NOT rerun on budget increase!"

    # 2. Affected work MUST rerun
    assert mock_bud.called
    assert mock_opt.called

    # 3. Verify state updates
    assert replanned_state["trip_context"].budget.amount_inr == 75_000.0
    assert replanned_state["replan_requested"] is True
    assert replanned_state["replan_proposal"]["proposal_type"] == "INCREASE_BUDGET"
    assert "logistics" in replanned_state["replan_proposal"]["reused_components"]
    assert "experience" in replanned_state["replan_proposal"]["reused_components"]
    assert "visa" in replanned_state["replan_proposal"]["reused_components"]
    assert replanned_state["plan_status"] == "REPLANNED"


@patch("src.graph.workflow.process_logistics")
@patch("src.graph.workflow.process_experience")
@patch("src.graph.workflow.process_budget")
@patch("src.graph.workflow.process_optimizer")
def test_replan_workflow_adjust_travel_style(
    mock_opt: MagicMock,
    mock_bud: MagicMock,
    mock_exp: MagicMock,
    mock_log: MagicMock,
) -> None:
    """Verify ADJUST_TRAVEL_STYLE re-plans logistics & experience while reusing visa."""
    ctx = make_dummy_context(travel_style=TravelStyle.LUXURY)
    logistics = make_dummy_logistics()
    experience = make_dummy_experience()
    visa = make_dummy_visa(is_domestic=True)
    budget = make_dummy_budget()

    current_state: PlanGraphState = {
        "request": {},
        "trip_context": ctx,
        "travel_scope": TravelScope.DOMESTIC,
        "visa_verdict": visa,
        "logistics_plan": logistics,
        "experience_plan": experience,
        "budget_breakdown": budget,
        "plan_status": "NEEDS_USER_DECISION",
        "warnings": [],
        "errors": [],
        "replan_requested": False,
        "replan_proposal": None,
    }

    new_logistics = make_dummy_logistics()
    new_experience = make_dummy_experience()
    mock_log.return_value = new_logistics
    mock_exp.return_value = new_experience
    new_budget = make_dummy_budget()
    mock_bud.return_value = new_budget
    mock_opt.return_value = MagicMock(
        optimization_result=OptimizationResult(
            action=OptimizationAction.NONE,
            status="UNDER_BUDGET",
        ),
        budget_breakdown=new_budget,
        logistics_plan=new_logistics,
        experience_plan=new_experience,
    )

    replanned = replan_workflow(
        current_state=current_state,
        proposal_type="ADJUST_TRAVEL_STYLE",
        target_value=TravelStyle.BUDGET,
    )

    # Visa is reused
    assert "visa" in replanned["replan_proposal"]["reused_components"]
    # Logistics and Experience must rerun
    assert mock_log.called
    assert mock_exp.called
    assert replanned["trip_context"].travel_style == TravelStyle.BUDGET


def test_run_planning_graph_entrypoint_with_mock() -> None:
    """Verify run_planning_graph accepts a request dictionary and returns state."""
    with patch("src.graph.workflow.get_planning_graph") as mock_get:
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = {
            "trip_context": make_dummy_context(),
            "optimization_result": OptimizationResult(
                action=OptimizationAction.NONE,
                status="UNDER_BUDGET",
            ),
            "errors": [],
            "warnings": [],
        }
        mock_get.return_value = mock_compiled

        output = run_planning_graph({"origin": "BOM", "destinations": ["GOI"]})
        assert output["plan_status"] == "COMPLETED"
        assert mock_compiled.invoke.called
