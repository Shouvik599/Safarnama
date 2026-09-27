"""Unit tests for Phase 16 — Budget Conflict and Human Decision Flow.

Verifies all requirements from phases.md Section 20 and architecture.md Section 11-12:
1. Scenario 1: Budget sufficient (UNDER_BUDGET / EXACT) -> Normal plan, COMPLETED.
2. Scenario 2: <=5% over (MINOR_OVER) -> Automatic minor optimization applied,
   recalculates deterministically, brings costs within budget, guardrails respected.
3. Scenario 3: 5%–15% over (SIGNIFICANT_OVER) -> Halts automatic mutation, sets
   NEEDS_USER_DECISION, presents structured trade-offs and alternatives.
4. Scenario 3 User Decision: Traveler chooses trade-off (e.g. INCREASE_BUDGET or
   ADJUST_TRAVEL_STYLE), replan_workflow resolves conflict to REPLANNED / COMPLETED.
5. Scenario 4: >15% over (INFEASIBLE) -> Halts mutation, sets INFEASIBLE, isolates top
   cost drivers with percentages, calculates realistic minimum budget and alternative paths.
6. Scenario 4 User Decision: Traveler accepts realistic budget or reduces duration,
   replan_workflow re-evaluates.
7. Unaffected Work Reuse: Verifies that budget changes reuse visa, logistics, and experience
   artifacts without rerun; style changes reuse visa; destination removals rerun downstream.
8. Date Alignment on Duration Shortening: EXACT mode properly recalculates end_date.
9. API Layer Integration: POST /api/v1/plan/replan endpoint validates requests,
   extracts state from FinalItinerary, runs replan_workflow, and returns ReplanResponse.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.graph.state import PlanGraphState
from src.graph.workflow import replan_workflow
from src.models.budget import (
    BudgetBreakdown,
    BudgetStatus,
    BudgetVariance,
    ContingencyConfig,
    CostBreakdown,
    OptimizationAction,
    OptimizationResult,
)
from src.models.itinerary import (
    ActivitySlot,
    DayMeal,
    Daypart,
    DayPlan,
    ExperiencePlan,
    FinalItinerary,
    PointOfInterest,
)
from src.models.logistics import HotelStay, LogisticsPlan, TransportLeg
from src.models.trip import (
    BudgetMode,
    DateMode,
    Pace,
    TravelScope,
    TravelStyle,
    TripBudget,
    TripContext,
    TripDates,
    TripParty,
)
from src.nodes.optimizer_node import (
    OptimizerValidationError,
    create_replanning_proposal,
    process_optimizer,
)
from src.nodes.synthesizer_node import process_synthesizer

# ---------------------------------------------------------------------------
# Scoped Fixtures & Test Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def force_fixture_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure all tests run hermetically offline using fixtures."""
    monkeypatch.setenv("SAFARNAMA_USE_FIXTURES", "true")


def make_context(
    scope: TravelScope = TravelScope.DOMESTIC,
    destinations: list[str] | None = None,
    budget_inr: float = 100_000.0,
    travel_style: TravelStyle = TravelStyle.COMFORTABLE,
    duration_days: int = 5,
    date_mode: DateMode = DateMode.EXACT,
    start_date: str = "2026-10-15",
    end_date: str = "2026-10-20",
) -> TripContext:
    """Helper to construct a valid TripContext."""
    return TripContext(
        origin="Delhi",
        destinations=destinations or ["Goa"],
        scope=scope,
        party=TripParty(adults=2, children=0),
        dates=TripDates(
            mode=date_mode,
            start_date=start_date,
            end_date=end_date if date_mode == DateMode.EXACT else None,
            duration_days=duration_days,
        ),
        budget=TripBudget(amount_inr=budget_inr, mode=BudgetMode.TOTAL),
        travel_style=travel_style,
        pace=Pace.BALANCED,
    )


def make_breakdown(
    user_budget: float,
    subtotal: float,
    contingency_pct: float = 10.0,
    transport: float = 20_000.0,
    accommodation: float = 30_000.0,
    activities: float = 10_000.0,
    food: float = 15_000.0,
    local_transport: float = 5_000.0,
    visa: float = 0.0,
    misc: float = 2_000.0,
) -> BudgetBreakdown:
    """Helper to construct a deterministic BudgetBreakdown."""
    contingency_amt = round(subtotal * (contingency_pct / 100.0), 2)
    projected = round(subtotal + contingency_amt, 2)
    variance_inr = round(projected - user_budget, 2)
    variance_pct = round((variance_inr / user_budget) * 100.0, 2) if user_budget > 0 else 0.0

    if abs(variance_inr) <= 1.0:
        status = BudgetStatus.EXACT
    elif variance_inr < 0:
        status = BudgetStatus.UNDER_BUDGET
    elif variance_pct <= 5.0:
        status = BudgetStatus.MINOR_OVER
    elif variance_pct <= 15.0:
        status = BudgetStatus.SIGNIFICANT_OVER
    else:
        status = BudgetStatus.INFEASIBLE

    return BudgetBreakdown(
        cost_breakdown=CostBreakdown(
            transport_inr=transport,
            accommodation_inr=accommodation,
            local_transport_inr=local_transport,
            activities_inr=activities,
            food_inr=food,
            visa_inr=visa,
            misc_inr=misc,
            has_estimated_components=False,
        ),
        contingency=ContingencyConfig(
            percentage=contingency_pct,
            amount_inr=contingency_amt,
            reasoning=f"{contingency_pct}% standard buffer",
            is_international=False,
            country_count=1,
            has_estimated_prices=False,
            has_flexible_dates=False,
        ),
        variance=BudgetVariance(
            user_budget_inr=user_budget,
            projected_total_inr=projected,
            variance_inr=variance_inr,
            variance_percentage=variance_pct,
            status=status,
        ),
        optimization=OptimizationResult(),
        subtotal_inr=subtotal,
        total_with_contingency_inr=projected,
        per_person_cost_inr=round(projected / 2, 2),
        warnings=[],
        is_estimated=False,
        timestamp="2026-10-15T10:00:00Z",
    )


def make_logistics(nights: int = 4, hotel_rate: float = 5_000.0) -> LogisticsPlan:
    """Helper to construct a valid LogisticsPlan."""
    return LogisticsPlan(
        transport_legs=[
            TransportLeg(
                leg_number=1,
                mode="FLIGHT",
                carrier="IndiGo",
                origin="DEL",
                destination="GOI",
                price_per_person_inr=7_500.0,
                total_price_inr=15_000.0,
                provider="fixture",
            )
        ],
        hotel_stays=[
            HotelStay(
                destination="Goa",
                hotel_name="Resort Stay",
                checkin_date="2026-10-15",
                checkout_date="2026-10-19",
                nights=nights,
                rooms_required=1,
                price_per_room_per_night_inr=hotel_rate,
                total_accommodation_cost_inr=hotel_rate * nights,
                star_rating=4,
                provider="fixture",
            )
        ],
        total_transport_cost_inr=15_000.0,
        total_accommodation_cost_inr=hotel_rate * nights,
        warnings=[],
        is_estimated=False,
        timestamp="2026-10-15T10:00:00Z",
    )


def make_experience() -> ExperiencePlan:
    """Helper to construct a valid ExperiencePlan."""
    return ExperiencePlan(
        days=[
            DayPlan(
                day_number=1,
                date="2026-10-15",
                city="Goa",
                activities=[
                    ActivitySlot(
                        daypart="MORNING",
                        poi=PointOfInterest(name="Calangute Beach", city="Goa", category="BEACH"),
                        cost_inr=0.0,
                    )
                ],
                meals=[
                    DayMeal(
                        daypart=Daypart.AFTERNOON,
                        meal_type="LUNCH",
                        restaurant_name="Local Bistro",
                        estimated_cost_inr=500.0,
                    )
                ],
            )
        ],
        total_activity_cost_inr=2_000.0,
        total_food_cost_inr=8_000.0,
        total_local_transport_cost_inr=3_000.0,
        total_days=1,
        warnings=[],
        is_estimated=False,
        timestamp="2026-10-15T10:00:00Z",
    )


def make_itinerary(
    ctx: TripContext,
    breakdown: BudgetBreakdown,
    logistics: LogisticsPlan | None = None,
    experience: ExperiencePlan | None = None,
    opt_result: OptimizationResult | None = None,
    plan_status: str | None = None,
) -> FinalItinerary:
    """Helper to assemble a valid FinalItinerary."""
    log_plan = logistics or make_logistics()
    exp_plan = experience or make_experience()
    opt = opt_result or OptimizationResult()
    return process_synthesizer(
        trip_context=ctx,
        logistics_plan=log_plan,
        experience_plan=exp_plan,
        budget_breakdown=breakdown,
        optimization_result=opt,
        plan_status=plan_status,
    )


# ===========================================================================
# 1. Scenario 1: Budget Sufficient (Normal Plan)
# ===========================================================================


def test_scenario_1_budget_sufficient_normal_plan() -> None:
    """Scenario 1: When budget is sufficient, optimizer takes no action and returns COMPLETED."""
    ctx = make_context(budget_inr=100_000.0)
    # Subtotal 70,000 + 10% contingency = 77,000 <= 100,000
    breakdown = make_breakdown(user_budget=100_000.0, subtotal=70_000.0)
    logistics = make_logistics()
    experience = make_experience()

    output = process_optimizer(ctx, breakdown, logistics, experience)

    assert output.optimization_result.action == OptimizationAction.NONE
    assert output.optimization_result.savings_inr == 0.0
    assert output.optimization_result.guardrails_respected is True

    itin = make_itinerary(
        ctx, output.budget_breakdown, logistics, experience, output.optimization_result
    )
    assert itin.plan_status == "COMPLETED"
    assert "allocated" in itin.summary and "headroom" in itin.summary


# ===========================================================================
# 2. Scenario 2: <=5% Over (Automatic Minor Optimization)
# ===========================================================================


def test_scenario_2_minor_overage_auto_optimization() -> None:
    """Scenario 2: When budget is <=5% over, optimizer executes minor savings automatically."""
    # User budget 100,000. Subtotal 93,000 + 10% contingency = 102,300 (+2.3% over)
    ctx = make_context(budget_inr=100_000.0)
    breakdown = make_breakdown(
        user_budget=100_000.0,
        subtotal=93_000.0,
        accommodation=40_000.0,
        food=20_000.0,
    )
    logistics = make_logistics(hotel_rate=10_000.0)
    experience = make_experience()

    output = process_optimizer(ctx, breakdown, logistics, experience)

    # Must automatically apply minor optimization
    assert output.optimization_result.action in (
        OptimizationAction.CHEAPER_HOTEL,
        OptimizationAction.LOWER_FOOD_BUDGET,
        OptimizationAction.MULTIPLE_MINOR,
    )
    assert output.optimization_result.savings_inr > 0.0
    assert output.optimization_result.guardrails_respected is True

    # Recalculated total must be within or at user budget
    recalculated = output.budget_breakdown
    assert recalculated.total_with_contingency_inr <= 100_000.0
    assert recalculated.variance.variance_inr <= 1.0

    itin = make_itinerary(
        ctx, recalculated, output.logistics_plan, output.experience_plan, output.optimization_result
    )
    assert itin.plan_status == "COMPLETED"


# ===========================================================================
# 3. Scenario 3: 5%–15% Over (Trade-offs & User Decision Required)
# ===========================================================================


def test_scenario_3_significant_overage_presents_tradeoffs() -> None:
    """Scenario 3: When budget is 5%-15% over, mutation halts and user decision is required."""
    # User budget 100,000. Subtotal 100,000 + 10% contingency = 110,000 (+10.0% over)
    ctx = make_context(budget_inr=100_000.0)
    breakdown = make_breakdown(
        user_budget=100_000.0,
        subtotal=100_000.0,
        accommodation=50_000.0,
        food=20_000.0,
    )
    logistics = make_logistics(hotel_rate=12_500.0)
    experience = make_experience()

    output = process_optimizer(ctx, breakdown, logistics, experience)

    # Halts automated changes
    assert output.optimization_result.action == OptimizationAction.USER_DECISION_REQUIRED
    assert output.optimization_result.savings_inr == 0.0
    assert len(output.optimization_result.trade_offs) > 0
    assert len(output.optimization_result.alternatives_presented) > 0
    assert output.optimization_result.guardrails_respected is True

    itin = make_itinerary(
        ctx, output.budget_breakdown, logistics, experience, output.optimization_result
    )
    assert itin.plan_status == "NEEDS_USER_DECISION"


def test_scenario_3_user_decision_increase_budget_resolves_conflict() -> None:
    """Scenario 3 Flow: Traveler accepts alternative to INCREASE_BUDGET, resolving conflict."""
    ctx = make_context(budget_inr=100_000.0)
    breakdown = make_breakdown(user_budget=100_000.0, subtotal=100_000.0)
    logistics = make_logistics()
    experience = make_experience()

    initial_opt = process_optimizer(ctx, breakdown, logistics, experience)
    assert initial_opt.optimization_result.action == OptimizationAction.USER_DECISION_REQUIRED

    # Starting state before user decision
    current_state: PlanGraphState = {
        "request": {},
        "trip_context": ctx,
        "travel_scope": TravelScope.DOMESTIC,
        "visa_verdict": None,
        "logistics_plan": logistics,
        "experience_plan": experience,
        "budget_breakdown": breakdown,
        "optimization_result": initial_opt.optimization_result,
        "plan_status": "NEEDS_USER_DECISION",
        "warnings": [],
        "errors": [],
        "replan_requested": False,
        "replan_proposal": None,
    }

    # Traveler decision: increase budget to 115,000 INR
    replanned_state = replan_workflow(
        current_state=current_state,
        proposal_type="INCREASE_BUDGET",
        target_value=115_000.0,
    )

    # Workflow successfully re-planned
    assert replanned_state["plan_status"] == "REPLANNED"
    assert replanned_state["trip_context"].budget.amount_inr == 115_000.0
    assert replanned_state["optimization_result"].action == OptimizationAction.NONE
    assert replanned_state["final_itinerary"].plan_status == "REPLANNED"
    assert replanned_state["replan_proposal"]["proposal_type"] == "INCREASE_BUDGET"
    assert "logistics" in replanned_state["replan_proposal"]["reused_components"]
    assert "experience" in replanned_state["replan_proposal"]["reused_components"]


# ===========================================================================
# 4. Scenario 4: >15% Over (Infeasible Explanation + Alternatives)
# ===========================================================================


def test_scenario_4_infeasible_budget_top_drivers_and_alternatives() -> None:
    """Scenario 4: When budget is >15% over, explains infeasibility and isolates cost drivers."""
    # User budget 50,000. Subtotal 90,000 + 10% contingency = 99,000 (+98.0% over)
    ctx = make_context(budget_inr=50_000.0)
    breakdown = make_breakdown(
        user_budget=50_000.0,
        subtotal=90_000.0,
        transport=35_000.0,
        accommodation=35_000.0,
    )
    logistics = make_logistics()
    experience = make_experience()

    output = process_optimizer(ctx, breakdown, logistics, experience)

    assert output.optimization_result.action == OptimizationAction.INFEASIBLE
    assert output.optimization_result.savings_inr == 0.0
    # Description isolates primary cost drivers
    desc = output.optimization_result.description
    assert "substantially above budget" in desc
    assert "Primary cost drivers" in desc
    # Alternatives include increasing budget, shortening trip, changing style
    alts = output.optimization_result.alternatives_presented
    assert any("Increase budget" in a for a in alts)
    assert any("Shorten trip" in a for a in alts)
    assert any("travel style" in a for a in alts)

    itin = make_itinerary(
        ctx, output.budget_breakdown, logistics, experience, output.optimization_result
    )
    assert itin.plan_status == "INFEASIBLE"


def test_scenario_4_user_decision_accept_realistic_budget() -> None:
    """Scenario 4 Flow: Traveler accepts realistic minimum budget required."""
    ctx = make_context(budget_inr=50_000.0)
    breakdown = make_breakdown(user_budget=50_000.0, subtotal=90_000.0)
    logistics = make_logistics()
    experience = make_experience()

    current_state: PlanGraphState = {
        "request": {},
        "trip_context": ctx,
        "travel_scope": TravelScope.DOMESTIC,
        "visa_verdict": None,
        "logistics_plan": logistics,
        "experience_plan": experience,
        "budget_breakdown": breakdown,
        "optimization_result": OptimizationResult(action=OptimizationAction.INFEASIBLE),
        "plan_status": "INFEASIBLE",
        "warnings": [],
        "errors": [],
        "replan_requested": False,
        "replan_proposal": None,
    }

    # Traveler approves realistic budget of 100,000 INR
    replanned_state = replan_workflow(
        current_state=current_state,
        proposal_type="ACCEPT_REALISTIC_BUDGET",
        target_value=100_000.0,
    )

    assert replanned_state["plan_status"] == "REPLANNED"
    assert replanned_state["trip_context"].budget.amount_inr == 100_000.0
    assert replanned_state["optimization_result"].action == OptimizationAction.NONE


# ===========================================================================
# 5. Unaffected Work Reuse & Component Isolation Tests
# ===========================================================================


@patch("src.graph.workflow.process_logistics")
@patch("src.graph.workflow.process_experience")
@patch("src.graph.workflow.process_budget")
@patch("src.graph.workflow.process_optimizer")
def test_unaffected_work_reuse_on_budget_change(
    mock_opt: MagicMock,
    mock_bud: MagicMock,
    mock_exp: MagicMock,
    mock_log: MagicMock,
) -> None:
    """Verify that changing budget does NOT re-query or rerun logistics, experience, or visa."""
    ctx = make_context(budget_inr=80_000.0)
    logistics = make_logistics()
    experience = make_experience()
    breakdown = make_breakdown(user_budget=80_000.0, subtotal=90_000.0)

    current_state: PlanGraphState = {
        "trip_context": ctx,
        "visa_verdict": None,
        "logistics_plan": logistics,
        "experience_plan": experience,
        "budget_breakdown": breakdown,
        "optimization_result": OptimizationResult(action=OptimizationAction.USER_DECISION_REQUIRED),
        "plan_status": "NEEDS_USER_DECISION",
        "warnings": [],
        "errors": [],
    }

    updated_budget = make_breakdown(user_budget=105_000.0, subtotal=90_000.0)
    mock_bud.return_value = updated_budget
    mock_opt.return_value = MagicMock(
        optimization_result=OptimizationResult(action=OptimizationAction.NONE),
        budget_breakdown=updated_budget,
        logistics_plan=logistics,
        experience_plan=experience,
    )

    replanned = replan_workflow(current_state, "INCREASE_BUDGET", 105_000.0)

    # Strictly verify zero external or node reruns for unaffected components
    assert not mock_log.called, "Logistics must NOT rerun when only budget changes!"
    assert not mock_exp.called, "Experience must NOT rerun when only budget changes!"
    assert mock_bud.called, "Budget calculation must run."
    assert mock_opt.called, "Optimizer must evaluate the updated budget."
    assert replanned["replan_proposal"]["reused_components"] == ["visa", "logistics", "experience"]
    assert replanned["replan_proposal"]["rerun_components"] == ["budget", "optimizer"]


@patch("src.graph.workflow.process_logistics")
@patch("src.graph.workflow.process_experience")
@patch("src.graph.workflow.process_budget")
@patch("src.graph.workflow.process_optimizer")
def test_component_isolation_on_style_change(
    mock_opt: MagicMock,
    mock_bud: MagicMock,
    mock_exp: MagicMock,
    mock_log: MagicMock,
) -> None:
    """Verify that changing travel style reruns logistics and experience while reusing visa."""
    ctx = make_context(travel_style=TravelStyle.LUXURY)
    logistics = make_logistics()
    experience = make_experience()
    breakdown = make_breakdown(user_budget=100_000.0, subtotal=120_000.0)

    current_state: PlanGraphState = {
        "trip_context": ctx,
        "visa_verdict": None,
        "logistics_plan": logistics,
        "experience_plan": experience,
        "budget_breakdown": breakdown,
        "optimization_result": OptimizationResult(action=OptimizationAction.USER_DECISION_REQUIRED),
        "plan_status": "NEEDS_USER_DECISION",
        "warnings": [],
        "errors": [],
    }

    mock_log.return_value = make_logistics(hotel_rate=3_000.0)
    mock_exp.return_value = make_experience()
    new_budget = make_breakdown(user_budget=100_000.0, subtotal=75_000.0)
    mock_bud.return_value = new_budget
    mock_opt.return_value = MagicMock(
        optimization_result=OptimizationResult(action=OptimizationAction.NONE),
        budget_breakdown=new_budget,
        logistics_plan=mock_log.return_value,
        experience_plan=mock_exp.return_value,
    )

    replanned = replan_workflow(current_state, "ADJUST_TRAVEL_STYLE", TravelStyle.BUDGET)

    assert mock_log.called, "Logistics must rerun to fetch budget hotel tier."
    assert mock_exp.called, "Experience must rerun to calibrate dining costs."
    assert replanned["trip_context"].travel_style == TravelStyle.BUDGET
    assert "visa" in replanned["replan_proposal"]["reused_components"]


def test_reduce_duration_proposal_exact_dates_adjusts_end_date() -> None:
    """Verify REDUCE_DURATION on EXACT dates aligns both duration_days and end_date."""
    ctx = make_context(
        date_mode=DateMode.EXACT,
        start_date="2026-10-15",
        end_date="2026-10-20",
        duration_days=5,
    )

    updated = create_replanning_proposal(ctx, "REDUCE_DURATION", 4)
    assert updated.dates.duration_days == 4
    assert updated.dates.start_date == "2026-10-15"
    assert updated.dates.end_date == "2026-10-19"


def test_adjust_pace_proposal() -> None:
    """Verify ADJUST_PACE updates the traveler pace correctly."""
    ctx = make_context()
    assert ctx.pace == Pace.BALANCED

    updated = create_replanning_proposal(ctx, "ADJUST_PACE", "RELAXED")
    assert updated.pace == Pace.RELAXED


def test_remove_destination_proposal() -> None:
    """Verify REMOVE_DESTINATION removes the designated destination."""
    ctx = make_context(destinations=["Paris", "Rome"])
    updated = create_replanning_proposal(ctx, "REMOVE_DESTINATION", "Rome")
    assert updated.destinations == ["Paris"]


def test_invalid_replanning_proposals_raise_validation_error() -> None:
    """Verify invalid re-planning parameters raise clear OptimizerValidationError."""
    ctx = make_context()

    with pytest.raises(OptimizerValidationError, match="Valid positive budget amount required"):
        create_replanning_proposal(ctx, "INCREASE_BUDGET", -500.0)

    with pytest.raises(OptimizerValidationError, match="duration cannot be less than 1 day"):
        create_replanning_proposal(ctx, "REDUCE_DURATION", 0)

    with pytest.raises(OptimizerValidationError, match="Unknown travel style"):
        create_replanning_proposal(ctx, "ADJUST_TRAVEL_STYLE", "INVALID_STYLE")

    with pytest.raises(OptimizerValidationError, match="Cannot remove the only destination"):
        create_replanning_proposal(ctx, "REMOVE_DESTINATION", "Goa")

    with pytest.raises(OptimizerValidationError, match="Unsupported re-planning proposal type"):
        create_replanning_proposal(ctx, "UNKNOWN_ACTION", "value")


# ===========================================================================
# 6. API Re-planning Endpoint Tests (POST /api/v1/plan/replan)
# ===========================================================================


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client fixture."""
    app = create_app()
    return TestClient(app)


def test_api_replan_with_itinerary_increase_budget(client: TestClient) -> None:
    """Verify POST /api/v1/plan/replan succeeds when passed a previous FinalItinerary."""
    ctx = make_context(budget_inr=80_000.0)
    breakdown = make_breakdown(user_budget=80_000.0, subtotal=90_000.0)
    opt_result = OptimizationResult(
        action=OptimizationAction.USER_DECISION_REQUIRED,
        trade_offs=["Accommodation cost high"],
        alternatives_presented=["Increase budget by ₹19,000"],
    )
    itin = make_itinerary(ctx, breakdown, opt_result=opt_result, plan_status="NEEDS_USER_DECISION")

    payload = {
        "proposal_type": "INCREASE_BUDGET",
        "target_value": 110_000.0,
        "itinerary": itin.model_dump(),
    }

    response = client.post("/api/v1/plan/replan", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "REPLANNED"
    assert data["itinerary"]["plan_status"] == "REPLANNED"
    assert data["itinerary"]["trip_context"]["budget"]["amount_inr"] == 110_000.0
    assert data["replan_summary"]["proposal_type"] == "INCREASE_BUDGET"
    assert "logistics" in data["replan_summary"]["reused_components"]


def test_api_replan_accept_realistic_budget_auto_derives_value(client: TestClient) -> None:
    """Verify ACCEPT_REALISTIC_BUDGET auto-extracts projected_total if target_value is omitted."""
    ctx = make_context(budget_inr=50_000.0)
    breakdown = make_breakdown(user_budget=50_000.0, subtotal=90_000.0)  # total with 10% is 99,000
    opt_result = OptimizationResult(action=OptimizationAction.INFEASIBLE)
    itin = make_itinerary(ctx, breakdown, opt_result=opt_result, plan_status="INFEASIBLE")

    payload = {
        "proposal_type": "ACCEPT_REALISTIC_BUDGET",
        "itinerary": itin.model_dump(),
    }

    response = client.post("/api/v1/plan/replan", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "REPLANNED"
    assert data["itinerary"]["trip_context"]["budget"]["amount_inr"] == 99_000.0


def test_api_replan_validation_failures(client: TestClient) -> None:
    """Verify API error handling on malformed re-planning requests."""
    # 1. Missing both itinerary and trip_context
    resp1 = client.post(
        "/api/v1/plan/replan", json={"proposal_type": "INCREASE_BUDGET", "target_value": 100_000}
    )
    assert resp1.status_code == 400
    assert "Either 'itinerary' or 'trip_context' must be provided" in resp1.json()["detail"]

    # 2. Invalid target value (negative budget)
    ctx = make_context(budget_inr=50_000.0)
    breakdown = make_breakdown(user_budget=50_000.0, subtotal=70_000.0)
    itin = make_itinerary(ctx, breakdown)
    resp2 = client.post(
        "/api/v1/plan/replan",
        json={
            "proposal_type": "INCREASE_BUDGET",
            "target_value": -100.0,
            "itinerary": itin.model_dump(),
        },
    )
    assert resp2.status_code == 400
    assert "Valid positive budget amount required" in resp2.json()["detail"]

    # 3. Unknown proposal type
    resp3 = client.post(
        "/api/v1/plan/replan",
        json={
            "proposal_type": "MAGIC_DISCOUNT",
            "itinerary": itin.model_dump(),
        },
    )
    assert resp3.status_code == 400
    assert "Unsupported re-planning proposal type" in resp3.json()["detail"]
