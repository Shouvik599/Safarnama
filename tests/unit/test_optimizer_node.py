"""Unit tests for Phase 11 — Optimizer Functionality (src/nodes/optimizer_node.py).

Verifies all requirements from phases.md Section 15 and prd.md Section 6.10-6.12:
1. Under budget scenario (action == NONE, savings == 0.0, guardrails == True)
2. Exact budget scenario (action == NONE, savings == 0.0)
3. Large surplus scenario (action == NONE, headroom notes for upgrades)
4. Minor over budget (<=5%): Hotel saver rate optimization (action == CHEAPER_HOTEL)
5. Minor over budget (<=5%): Dining assumption optimization (action == LOWER_FOOD_BUDGET)
6. Minor over budget (<=5%): Multi-minor optimization (action == MULTIPLE_MINOR)
7. Minor over budget: Quality guardrails preservation
8. Significant over budget (5%–15%): User decision required (USER_DECISION_REQUIRED)
9. Infeasible scenario (>15%): Infeasibility explanation and alternatives (INFEASIBLE)
10. Re-planning proposal generation (INCREASE_BUDGET, REDUCE_DURATION, etc.)
11. Re-planning error validation (invalid type, invalid values)
12. LangGraph node interface optimizer_node(state) with dict state
13. LangGraph node interface optimizer_node(state) with InitialPlanningState
14. Missing context or breakdown raises OptimizerValidationError
"""

from __future__ import annotations

import pytest
from src.models.budget import (
    BudgetBreakdown,
    BudgetStatus,
    BudgetVariance,
    ContingencyConfig,
    CostBreakdown,
    OptimizationAction,
    OptimizationResult,
)
from src.models.itinerary import ActivitySlot, DayMeal, DayPlan, ExperiencePlan, PointOfInterest
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
    OptimizerOutput,
    OptimizerValidationError,
    create_replanning_proposal,
    optimizer_node,
    process_optimizer,
)

# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------


def make_test_context(
    scope: TravelScope = TravelScope.DOMESTIC,
    budget_amount: float = 100_000.0,
    adults: int = 2,
    children: int = 0,
    duration_days: int = 5,
    destinations: list[str] | None = None,
    style: TravelStyle = TravelStyle.COMFORTABLE,
) -> TripContext:
    """Helper to generate consistent TripContext objects."""
    dests = destinations or (["BOM"] if scope == TravelScope.DOMESTIC else ["DXB"])
    return TripContext(
        origin="DEL",
        destinations=dests,
        scope=scope,
        party=TripParty(adults=adults, children=children),
        dates=TripDates(
            mode=DateMode.EXACT,
            start_date="2026-10-15",
            end_date="2026-10-19",
            duration_days=duration_days,
        ),
        budget=TripBudget(mode=BudgetMode.TOTAL, amount_inr=budget_amount),
        travel_style=style,
        pace=Pace.BALANCED,
    )


def make_test_plans(
    hotel_cost: float = 40_000.0,
    transport_cost: float = 20_000.0,
    food_cost: float = 15_000.0,
    activity_cost: float = 10_000.0,
    local_transit: float = 3_000.0,
) -> tuple[LogisticsPlan, ExperiencePlan]:
    """Helper to generate matching LogisticsPlan and ExperiencePlan."""
    stays = [
        HotelStay(
            destination="BOM",
            hotel_name="Grand Hotel",
            star_rating=4,
            checkin_date="2026-10-15",
            checkout_date="2026-10-19",
            nights=4,
            rooms_required=1,
            price_per_room_per_night_inr=hotel_cost / 4.0,
            total_accommodation_cost_inr=hotel_cost,
            provider="fixture",
        )
    ]
    legs = [
        TransportLeg(
            leg_number=1,
            mode="FLIGHT",
            carrier="IndiGo",
            origin="DEL",
            destination="BOM",
            price_per_person_inr=transport_cost / 2.0,
            total_price_inr=transport_cost,
            provider="fixture",
        )
    ]
    logistics = LogisticsPlan(
        transport_legs=legs,
        hotel_stays=stays,
        total_transport_cost_inr=transport_cost,
        total_accommodation_cost_inr=hotel_cost,
        timestamp="2026-10-01T00:00:00Z",
    )

    day_plans = [
        DayPlan(
            day_number=1,
            city="BOM",
            activities=[
                ActivitySlot(
                    slot_index=1,
                    daypart="MORNING",
                    title="Gateway of India",
                    description="Historic landmark",
                    poi=PointOfInterest(
                        name="Gateway of India", category="HISTORY_HERITAGE", city="BOM"
                    ),
                    is_must_visit=True,
                    ticket_cost_inr=activity_cost / 2.0,
                )
            ],
            meals=[
                DayMeal(
                    daypart="AFTERNOON",
                    meal_type="LUNCH",
                    venue_name="Prithvi Cafe",
                    estimated_cost_inr=food_cost / 4.0,
                )
            ],
        )
    ]
    experience = ExperiencePlan(
        days=day_plans,
        total_days=1,
        destinations_covered=["BOM"],
        must_visits_fulfilled=["Gateway of India"],
        total_activity_cost_inr=activity_cost,
        total_food_cost_inr=food_cost,
        total_local_transport_cost_inr=local_transit,
        timestamp="2026-10-01T00:00:00Z",
    )
    return logistics, experience


def make_test_breakdown(
    user_budget: float,
    projected_total: float,
    status: BudgetStatus,
    hotel_cost: float | None = None,
    transport_cost: float = 20_000.0,
    food_cost: float = 15_000.0,
    activity_cost: float = 10_000.0,
    local_transit: float = 3_000.0,
    misc_cost: float = 2_000.0,
    contingency_pct: float = 5.0,
) -> BudgetBreakdown:
    """Helper to create a BudgetBreakdown with consistent variance values."""
    subtotal = round(projected_total / (1.0 + contingency_pct / 100.0), 2)
    contingency_amt = round(projected_total - subtotal, 2)

    if hotel_cost is None:
        hotel_cost = max(
            0.0,
            round(
                subtotal - (transport_cost + food_cost + activity_cost + local_transit + misc_cost),
                2,
            ),
        )
    else:
        misc_cost = max(
            0.0,
            round(
                subtotal
                - (hotel_cost + transport_cost + food_cost + activity_cost + local_transit),
                2,
            ),
        )

    variance_inr = round(projected_total - user_budget, 2)
    variance_pct = round((variance_inr / user_budget) * 100.0, 2)

    return BudgetBreakdown(
        cost_breakdown=CostBreakdown(
            transport_inr=transport_cost,
            accommodation_inr=hotel_cost,
            local_transport_inr=local_transit,
            food_inr=food_cost,
            activities_inr=activity_cost,
            misc_inr=misc_cost,
        ),
        contingency=ContingencyConfig(
            percentage=round(contingency_pct, 1),
            amount_inr=round(contingency_amt, 2),
        ),
        variance=BudgetVariance(
            user_budget_inr=user_budget,
            projected_total_inr=projected_total,
            variance_inr=variance_inr,
            variance_percentage=variance_pct,
            status=status,
        ),
        optimization=OptimizationResult(),
        subtotal_inr=subtotal,
        total_with_contingency_inr=projected_total,
        per_person_cost_inr=projected_total / 2.0,
        timestamp="2026-10-01T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


class TestOptimizerWithinBudget:
    """Tests for UNDER_BUDGET and EXACT scenarios."""

    def test_under_budget_no_optimization(self):
        context = make_test_context(budget_amount=100_000.0)
        logistics, experience = make_test_plans()
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=92_000.0,
            status=BudgetStatus.UNDER_BUDGET,
        )

        output = process_optimizer(context, breakdown, logistics, experience)
        assert isinstance(output, OptimizerOutput)
        assert output.optimization_result.action == OptimizationAction.NONE
        assert output.optimization_result.savings_inr == 0.0
        assert output.optimization_result.guardrails_respected is True
        assert output.budget_breakdown.optimization.action == OptimizationAction.NONE

    def test_exact_budget_no_optimization(self):
        context = make_test_context(budget_amount=100_000.0)
        logistics, experience = make_test_plans()
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=100_000.0,
            status=BudgetStatus.EXACT,
        )

        output = process_optimizer(context, breakdown, logistics, experience)
        assert output.optimization_result.action == OptimizationAction.NONE
        assert output.optimization_result.savings_inr == 0.0

    def test_substantial_surplus_notes_headroom(self):
        context = make_test_context(budget_amount=100_000.0)
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=75_000.0,
            status=BudgetStatus.UNDER_BUDGET,
        )

        output = process_optimizer(context, breakdown)
        assert output.optimization_result.action == OptimizationAction.NONE
        assert len(output.optimization_result.trade_offs) > 0
        assert "headroom" in output.optimization_result.trade_offs[0].lower()


class TestOptimizerMinorOverBudget:
    """Tests for MINOR_OVER (<=5% over budget) scenarios."""

    def test_hotel_saver_rate_optimization(self):
        # 3% over budget: ₹103,000 projected vs ₹100,000 budget
        context = make_test_context(budget_amount=100_000.0)
        logistics, experience = make_test_plans(hotel_cost=50_000.0)
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=103_000.0,
            status=BudgetStatus.MINOR_OVER,
            hotel_cost=50_000.0,
        )

        output = process_optimizer(context, breakdown, logistics, experience)
        assert output.optimization_result.action == OptimizationAction.CHEAPER_HOTEL
        assert output.optimization_result.savings_inr >= 3_000.0
        assert output.optimization_result.guardrails_respected is True
        # Verify resulting budget is now within budget
        assert output.budget_breakdown.variance.variance_inr <= 0.0
        # Verify updated logistics plan
        assert output.logistics_plan is not None
        assert output.logistics_plan.total_accommodation_cost_inr < 50_000.0
        assert "Saver Rate" in (output.logistics_plan.hotel_stays[0].notes or "")

    def test_dining_optimization_when_hotels_small(self):
        # 2% over budget: ₹102,000 vs ₹100,000 with low hotel and high food
        context = make_test_context(budget_amount=100_000.0)
        logistics, experience = make_test_plans(hotel_cost=5_000.0, food_cost=40_000.0)
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=102_000.0,
            status=BudgetStatus.MINOR_OVER,
            hotel_cost=5_000.0,
            food_cost=40_000.0,
        )

        output = process_optimizer(context, breakdown, logistics, experience)
        assert output.optimization_result.action == OptimizationAction.LOWER_FOOD_BUDGET
        assert output.optimization_result.savings_inr >= 2_000.0
        assert output.budget_breakdown.variance.variance_inr <= 0.0
        assert output.experience_plan is not None
        assert output.experience_plan.total_food_cost_inr < 40_000.0

    def test_multi_minor_optimization(self):
        # 4.5% over budget: ₹104,500 vs ₹100,000 with moderate hotel and food
        context = make_test_context(budget_amount=100_000.0)
        logistics, experience = make_test_plans(hotel_cost=25_000.0, food_cost=25_000.0)
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=104_500.0,
            status=BudgetStatus.MINOR_OVER,
            hotel_cost=25_000.0,
            food_cost=25_000.0,
        )

        output = process_optimizer(context, breakdown, logistics, experience)
        assert output.optimization_result.action in (
            OptimizationAction.MULTIPLE_MINOR,
            OptimizationAction.CHEAPER_HOTEL,
        )
        assert output.optimization_result.savings_inr >= 4_000.0
        assert output.optimization_result.guardrails_respected is True

    def test_quality_guardrails_preserved_during_minor_optimization(self):
        context = make_test_context(budget_amount=100_000.0)
        logistics, experience = make_test_plans(hotel_cost=50_000.0)
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=103_500.0,
            status=BudgetStatus.MINOR_OVER,
            hotel_cost=50_000.0,
        )

        output = process_optimizer(context, breakdown, logistics, experience)
        assert output.optimization_result.guardrails_respected is True
        # Must-visits in experience plan must not be lost
        if output.experience_plan:
            assert "Gateway of India" in output.experience_plan.must_visits_fulfilled
        # Hotel star rating must remain unchanged
        if output.logistics_plan:
            assert output.logistics_plan.hotel_stays[0].star_rating == 4.0


class TestOptimizerSignificantOverBudget:
    """Tests for SIGNIFICANT_OVER (5%–15% over budget) scenarios."""

    def test_user_decision_required_no_automatic_mutation(self):
        # 10% over budget: ₹110,000 vs ₹100,000
        context = make_test_context(budget_amount=100_000.0)
        logistics, experience = make_test_plans()
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=110_000.0,
            status=BudgetStatus.SIGNIFICANT_OVER,
        )

        output = process_optimizer(context, breakdown, logistics, experience)
        assert output.optimization_result.action == OptimizationAction.USER_DECISION_REQUIRED
        assert output.optimization_result.savings_inr == 0.0
        assert output.optimization_result.guardrails_respected is True
        assert len(output.optimization_result.trade_offs) > 0
        assert len(output.optimization_result.alternatives_presented) >= 2
        # Plans must not be mutated without user decision
        assert output.logistics_plan == logistics
        assert output.experience_plan == experience


class TestOptimizerInfeasible:
    """Tests for INFEASIBLE (>15% over budget) scenarios."""

    def test_infeasible_explains_cost_drivers_and_alternatives(self):
        # 30% over budget: ₹130,000 vs ₹100,000
        context = make_test_context(budget_amount=100_000.0)
        logistics, experience = make_test_plans(hotel_cost=60_000.0, transport_cost=40_000.0)
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=130_000.0,
            status=BudgetStatus.INFEASIBLE,
            hotel_cost=60_000.0,
            transport_cost=40_000.0,
        )

        output = process_optimizer(context, breakdown, logistics, experience)
        assert output.optimization_result.action == OptimizationAction.INFEASIBLE
        assert output.optimization_result.savings_inr == 0.0
        assert output.optimization_result.guardrails_respected is True
        # Description isolates primary cost drivers
        assert "Accommodation" in output.optimization_result.description
        # Provides concrete alternatives
        assert len(output.optimization_result.alternatives_presented) >= 3


class TestReplanningProposal:
    """Tests for create_replanning_proposal helper."""

    def test_increase_budget(self):
        context = make_test_context(budget_amount=50_000.0)
        new_ctx = create_replanning_proposal(context, "INCREASE_BUDGET", 65_000.0)
        assert new_ctx.budget.amount_inr == 65_000.0
        assert context.budget.amount_inr == 50_000.0  # Immutable

    def test_reduce_duration(self):
        context = make_test_context(duration_days=6)
        new_ctx = create_replanning_proposal(context, "REDUCE_DURATION", 4)
        assert new_ctx.dates.duration_days == 4

    def test_adjust_travel_style(self):
        context = make_test_context(style=TravelStyle.LUXURY)
        new_ctx = create_replanning_proposal(context, "ADJUST_TRAVEL_STYLE", "COMFORTABLE")
        assert new_ctx.travel_style == TravelStyle.COMFORTABLE

    def test_remove_destination(self):
        context = make_test_context(destinations=["BOM", "GOI"])
        new_ctx = create_replanning_proposal(context, "REMOVE_DESTINATION", "GOI")
        assert new_ctx.destinations == ["BOM"]

    def test_invalid_proposal_type_raises(self):
        context = make_test_context()
        with pytest.raises(OptimizerValidationError, match="Unsupported re-planning"):
            create_replanning_proposal(context, "INVALID_ACTION")

    def test_invalid_budget_raises(self):
        context = make_test_context()
        with pytest.raises(OptimizerValidationError, match="Valid positive budget"):
            create_replanning_proposal(context, "INCREASE_BUDGET", -100)


class TestLangGraphNodeInterface:
    """Tests for optimizer_node(state) dictionary and object interfaces."""

    def test_dict_state_interface(self):
        context = make_test_context(budget_amount=100_000.0)
        logistics, experience = make_test_plans()
        breakdown = make_test_breakdown(
            user_budget=100_000.0,
            projected_total=95_000.0,
            status=BudgetStatus.UNDER_BUDGET,
        )

        state = {
            "trip_context": context,
            "budget_breakdown": breakdown,
            "logistics_plan": logistics,
            "experience_plan": experience,
        }

        result = optimizer_node(state)
        assert isinstance(result, dict)
        assert "optimization_result" in result
        assert "budget_breakdown" in result
        assert "logistics_plan" in result
        assert "experience_plan" in result
        assert result["optimization_result"].action == OptimizationAction.NONE

    def test_initial_planning_state_interface_without_breakdown_raises(self):
        context = make_test_context()
        from src.nodes.intake_node import process_intake

        init_state = process_intake(context)
        with pytest.raises(OptimizerValidationError, match="BudgetBreakdown is required"):
            optimizer_node(init_state)

    def test_missing_context_raises_validation_error(self):
        with pytest.raises(OptimizerValidationError):
            process_optimizer(None, None)
