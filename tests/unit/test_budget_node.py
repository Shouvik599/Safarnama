"""Unit tests for Phase 10 — Deterministic Budget Engine (src/nodes/budget_node.py).

Verifies all requirements from phases.md:
1. Total trip budget calculation & aggregation
2. Per-person budget mode normalization & splitting
3. Adult + children traveler party scaling
4. Visa fee multiplication (domestic bypass ₹0, international, Schengen)
5. Food daily estimate aggregation from ExperiencePlan
6. Deterministic miscellaneous costs calculation (domestic vs international)
7. Dynamic contingency calculation & reasoning
8. Under budget scenario (status == UNDER_BUDGET)
9. Exact budget scenario (status == EXACT within ₹1)
10. Minor over budget scenario <=5% (status == MINOR_OVER)
11. Significant over budget scenario 5–15% (status == SIGNIFICANT_OVER)
12. Infeasible scenario >15% (status == INFEASIBLE)
13. Floating-point precision and rounding invariants
14. Missing planning components & warning accumulation
15. LangGraph node function budget_node(state) interface
16. Error handling and validation (BudgetValidationError)
"""

from __future__ import annotations

import pytest
from src.models.budget import (
    BudgetBreakdown,
    BudgetStatus,
)
from src.models.itinerary import DayPlan, ExperiencePlan
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
from src.models.visa import (
    VisaCountryVerdict,
    VisaRequirementStatus,
    VisaVerdict,
)
from src.nodes.budget_node import (
    BudgetValidationError,
    budget_node,
    process_budget,
)
from src.nodes.intake_node import process_intake

# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------


def make_test_context(
    scope: TravelScope = TravelScope.DOMESTIC,
    budget_mode: BudgetMode = BudgetMode.TOTAL,
    budget_amount: float = 100_000.0,
    per_person_inr: float | None = None,
    adults: int = 2,
    children: int = 0,
    duration_days: int = 5,
    destinations: list[str] | None = None,
    date_mode: DateMode = DateMode.EXACT,
) -> TripContext:
    """Helper to generate consistent TripContext objects."""
    dests = destinations or (["BOM"] if scope == TravelScope.DOMESTIC else ["DXB"])
    dates = (
        TripDates(
            mode=DateMode.EXACT,
            start_date="2026-10-15",
            end_date="2026-10-19",
            duration_days=duration_days,
        )
        if date_mode == DateMode.EXACT
        else TripDates(
            mode=DateMode.FLEXIBLE,
            start_date="2026-10-01",
            duration_days=duration_days,
        )
    )
    budget = (
        TripBudget(mode=BudgetMode.TOTAL, amount_inr=budget_amount)
        if budget_mode == BudgetMode.TOTAL
        else TripBudget(
            mode=BudgetMode.PER_PERSON,
            amount_inr=per_person_inr or (budget_amount / (adults + children)),
        )
    )
    return TripContext(
        origin="DEL",
        destinations=dests,
        scope=scope,
        party=TripParty(adults=adults, children=children),
        dates=dates,
        budget=budget,
        travel_style=TravelStyle.COMFORTABLE,
        pace=Pace.BALANCED,
    )


def make_test_logistics(
    transport_cost: float = 20_000.0,
    hotel_cost: float = 24_000.0,
    is_estimated: bool = False,
) -> LogisticsPlan:
    """Helper to generate a valid LogisticsPlan."""
    return LogisticsPlan(
        transport_legs=[
            TransportLeg(
                leg_number=1,
                carrier="IndiGo",
                origin="DEL",
                destination="BOM",
                mode="FLIGHT",
                departure_datetime="2026-10-15T09:00:00",
                arrival_datetime="2026-10-15T11:15:00",
                duration_minutes=135,
                price_per_person_inr=transport_cost / 4.0,
                total_price_inr=transport_cost / 2.0,
                is_estimated=is_estimated,
                provider="mock-flights",
            ),
            TransportLeg(
                leg_number=2,
                carrier="IndiGo",
                origin="BOM",
                destination="DEL",
                mode="FLIGHT",
                departure_datetime="2026-10-19T18:00:00",
                arrival_datetime="2026-10-19T20:15:00",
                duration_minutes=135,
                price_per_person_inr=transport_cost / 4.0,
                total_price_inr=transport_cost / 2.0,
                is_estimated=is_estimated,
                provider="mock-flights",
            ),
        ],
        hotel_stays=[
            HotelStay(
                destination="BOM",
                hotel_name="Grand Hotel",
                checkin_date="2026-10-15",
                checkout_date="2026-10-19",
                nights=4,
                rooms_required=1,
                price_per_room_per_night_inr=hotel_cost / 4.0,
                total_accommodation_cost_inr=hotel_cost,
                is_estimated=is_estimated,
                provider="mock-hotels",
            )
        ],
        total_transport_cost_inr=transport_cost,
        total_accommodation_cost_inr=hotel_cost,
        is_estimated=is_estimated,
        timestamp="2026-09-26T12:00:00Z",
    )


def make_test_experience(
    activity_cost: float = 6_000.0,
    food_cost: float = 12_000.0,
    transit_cost: float = 3_000.0,
    is_estimated: bool = False,
) -> ExperiencePlan:
    """Helper to generate a valid ExperiencePlan."""
    days = [
        DayPlan(
            day_number=i + 1,
            city="BOM",
            activity_cost_inr=activity_cost / 4.0,
            food_cost_inr=food_cost / 4.0,
            local_transport_cost_inr=transit_cost / 4.0,
        )
        for i in range(4)
    ]
    return ExperiencePlan(
        days=days,
        total_days=4,
        destinations_covered=["BOM"],
        must_visits_fulfilled=["Gateway of India"],
        total_activity_cost_inr=activity_cost,
        total_food_cost_inr=food_cost,
        total_local_transport_cost_inr=transit_cost,
        is_estimated=is_estimated,
        timestamp="2026-09-26T12:00:00Z",
    )


def make_test_visa(
    fee_per_person: float = 3_500.0,
    travelers: int = 2,
    is_domestic: bool = False,
    advance_app: bool = False,
) -> VisaVerdict:
    """Helper to generate a valid VisaVerdict."""
    if is_domestic:
        return VisaVerdict(
            is_domestic_bypass=True,
            total_visa_cost_inr=0.0,
            requires_advance_application=False,
            timestamp="2026-09-26T12:00:00Z",
        )
    return VisaVerdict(
        is_domestic_bypass=False,
        countries=[
            VisaCountryVerdict(
                country_code="AE",
                country_name="United Arab Emirates",
                status=VisaRequirementStatus.E_VISA,
                visa_fee_inr=fee_per_person,
                permitted_stay_days=30,
            )
        ],
        total_visa_cost_inr=fee_per_person * travelers,
        requires_advance_application=advance_app,
        timestamp="2026-09-26T12:00:00Z",
    )


# ===========================================================================
# 1. Total Trip Budget & Itemized Breakdown
# ===========================================================================


def test_budget_engine_total_trip_budget_aggregation() -> None:
    """Verify exact category summation across transport, lodging, activities, food, and misc."""
    ctx = make_test_context(budget_amount=100_000.0)
    logistics = make_test_logistics(transport_cost=20_000.0, hotel_cost=24_000.0)
    experience = make_test_experience(
        activity_cost=6_000.0, food_cost=12_000.0, transit_cost=3_000.0
    )
    visa = make_test_visa(is_domestic=True)

    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=logistics,
        experience_plan=experience,
        visa_verdict=visa,
        misc_inr=2_000.0,
    )

    cb = breakdown.cost_breakdown
    assert cb.transport_inr == 20_000.0
    assert cb.accommodation_inr == 24_000.0
    assert cb.activities_inr == 6_000.0
    assert cb.food_inr == 12_000.0
    assert cb.local_transport_inr == 3_000.0
    assert cb.visa_inr == 0.0
    assert cb.misc_inr == 2_000.0

    expected_subtotal = 20_000.0 + 24_000.0 + 6_000.0 + 12_000.0 + 3_000.0 + 0.0 + 2_000.0
    assert cb.subtotal_inr == expected_subtotal
    assert breakdown.subtotal_inr == expected_subtotal
    assert (
        breakdown.total_with_contingency_inr
        == breakdown.subtotal_inr + breakdown.contingency.amount_inr
    )


# ===========================================================================
# 2. Per-Person Budget Mode
# ===========================================================================


def test_budget_engine_per_person_budget_normalization() -> None:
    """Verify that when user specifies per-person budget, total and per-person cost align."""
    # 2 adults, ₹40,000 per person -> ₹80,000 total budget
    ctx = make_test_context(
        budget_mode=BudgetMode.PER_PERSON,
        per_person_inr=40_000.0,
        adults=2,
        children=0,
    )
    # Using process_intake ensures state normalization
    state = process_intake(ctx)

    logistics = make_test_logistics(transport_cost=20_000.0, hotel_cost=20_000.0)
    experience = make_test_experience(
        activity_cost=5_000.0, food_cost=10_000.0, transit_cost=2_000.0
    )

    breakdown = process_budget(
        state_or_context=state,
        logistics_plan=logistics,
        experience_plan=experience,
        misc_inr=2_000.0,
    )

    assert breakdown.variance.user_budget_inr == 80_000.0
    assert breakdown.per_person_cost_inr == round(breakdown.total_with_contingency_inr / 2.0, 2)


# ===========================================================================
# 3. Adults + Children Scaling
# ===========================================================================


def test_budget_engine_adults_and_children_scaling() -> None:
    """Verify that parties with adults and children divide total cost across all travelers."""
    ctx = make_test_context(adults=2, children=2, budget_amount=150_000.0)  # 4 travelers total
    logistics = make_test_logistics(transport_cost=40_000.0, hotel_cost=36_000.0)
    experience = make_test_experience(
        activity_cost=8_000.0, food_cost=16_000.0, transit_cost=4_000.0
    )

    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=logistics,
        experience_plan=experience,
        misc_inr=4_000.0,
    )

    total_travelers = 4
    assert breakdown.per_person_cost_inr == round(
        breakdown.total_with_contingency_inr / total_travelers, 2
    )


# ===========================================================================
# 4. Visa Fee Multiplication
# ===========================================================================


def test_budget_engine_visa_fee_multiplication_international() -> None:
    """Verify that visa fee is correctly incorporated for all travelers in international scope."""
    ctx = make_test_context(
        scope=TravelScope.INTERNATIONAL,
        adults=3,
        children=0,
        budget_amount=250_000.0,
    )
    # Fee: ₹4,000 per person * 3 travelers = ₹12,000
    visa = make_test_visa(fee_per_person=4_000.0, travelers=3, is_domestic=False, advance_app=True)

    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(),
        experience_plan=make_test_experience(),
        visa_verdict=visa,
        misc_inr=5_000.0,
    )

    assert breakdown.cost_breakdown.visa_inr == 12_000.0
    assert any("Advance visa application required" in w for w in breakdown.warnings)


def test_budget_engine_domestic_visa_bypass_zero() -> None:
    """Verify domestic trips have ₹0 visa cost."""
    ctx = make_test_context(scope=TravelScope.DOMESTIC)
    visa = make_test_visa(is_domestic=True)

    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(),
        experience_plan=make_test_experience(),
        visa_verdict=visa,
    )

    assert breakdown.cost_breakdown.visa_inr == 0.0


# ===========================================================================
# 5. Food Daily Estimate Aggregation
# ===========================================================================


def test_budget_engine_food_cost_aggregation() -> None:
    """Verify food costs from ExperiencePlan days are properly summed into the cost breakdown."""
    ctx = make_test_context()
    experience = make_test_experience(food_cost=15_450.75)

    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(),
        experience_plan=experience,
    )

    assert breakdown.cost_breakdown.food_inr == 15_450.75


# ===========================================================================
# 6. Miscellaneous Expenses
# ===========================================================================


def test_budget_engine_deterministic_misc_costs_domestic() -> None:
    """Verify domestic misc expenses calculate ₹200/traveler/day when not overridden."""
    # 2 travelers, 5 days -> 2 * 5 * 200 = ₹2,000
    ctx = make_test_context(
        scope=TravelScope.DOMESTIC,
        adults=2,
        children=0,
        duration_days=5,
    )
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(),
        experience_plan=make_test_experience(),
    )
    assert breakdown.cost_breakdown.misc_inr == 2_000.0


def test_budget_engine_deterministic_misc_costs_international() -> None:
    """Verify international misc costs include insurance, eSIM, and daily cash buffer."""
    # 2 adults, 7 days
    # Insurance: 2 * ₹1,200 = ₹2,400
    # eSIM: 2 * ₹1,200 = ₹2,400
    # Incidentals: 2 * 7 * ₹350 = ₹4,900
    # Total: ₹9,700
    ctx = make_test_context(
        scope=TravelScope.INTERNATIONAL,
        adults=2,
        children=0,
        duration_days=7,
    )
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(),
        experience_plan=make_test_experience(),
    )
    assert breakdown.cost_breakdown.misc_inr == 9_700.0


# ===========================================================================
# 7. Dynamic Contingency Buffer
# ===========================================================================


def test_budget_engine_dynamic_contingency_domestic_simple() -> None:
    """Verify base domestic contingency is 5.0%."""
    ctx = make_test_context(scope=TravelScope.DOMESTIC, date_mode=DateMode.EXACT)
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(is_estimated=False),
        experience_plan=make_test_experience(is_estimated=False),
        misc_inr=2_000.0,
    )
    assert breakdown.contingency.percentage == 5.0
    assert breakdown.contingency.is_international is False
    assert breakdown.contingency.amount_inr == round(breakdown.subtotal_inr * 0.05, 2)


def test_budget_engine_dynamic_contingency_international_multi_country_estimated() -> None:
    """Verify international multi-country with estimated prices scales contingency percentage."""
    # International base: 10%
    # 2 countries (+2%)
    # Estimated prices (+3%)
    # Flexible dates (+2%)
    # Total: 17%
    ctx = make_test_context(
        scope=TravelScope.INTERNATIONAL,
        destinations=["DXB", "DOH"],
        date_mode=DateMode.FLEXIBLE,
    )
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(is_estimated=True),
        experience_plan=make_test_experience(is_estimated=True),
        misc_inr=3_000.0,
    )
    assert breakdown.contingency.percentage == 17.0
    assert breakdown.contingency.is_international is True
    assert breakdown.contingency.country_count == 2
    assert breakdown.contingency.has_estimated_prices is True
    assert breakdown.contingency.has_flexible_dates is True
    assert breakdown.contingency.amount_inr == round(breakdown.subtotal_inr * 0.17, 2)


# ===========================================================================
# 8. Under Budget Scenario (UNDER_BUDGET)
# ===========================================================================


def test_budget_engine_status_under_budget() -> None:
    """Verify status is UNDER_BUDGET when total cost is strictly below user budget."""
    ctx = make_test_context(budget_amount=150_000.0)
    # Total subtotal ~ ₹65,000, + 5% buffer = ₹68,250
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(transport_cost=20_000.0, hotel_cost=20_000.0),
        experience_plan=make_test_experience(
            activity_cost=5_000.0, food_cost=10_000.0, transit_cost=2_000.0
        ),
        misc_inr=2_000.0,
    )
    assert breakdown.variance.status == BudgetStatus.UNDER_BUDGET
    assert breakdown.variance.variance_inr < 0.0
    assert breakdown.variance.variance_percentage < 0.0


# ===========================================================================
# 9. Exact Budget Scenario (EXACT)
# ===========================================================================


def test_budget_engine_status_exact_within_one_rupee() -> None:
    """Verify status is EXACT when projected total equals budget within ₹1.00 tolerance."""
    # Subtotal ₹90,000, 10% buffer = ₹9,000, projected total = ₹99,000
    ctx = make_test_context(budget_amount=99_000.0)
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(transport_cost=40_000.0, hotel_cost=30_000.0),
        experience_plan=make_test_experience(
            activity_cost=10_000.0, food_cost=8_000.0, transit_cost=0.0
        ),
        misc_inr=2_000.0,
        custom_contingency_pct=10.0,
    )
    assert breakdown.total_with_contingency_inr == 99_000.0
    assert breakdown.variance.status == BudgetStatus.EXACT
    assert abs(breakdown.variance.variance_inr) <= 1.0


# ===========================================================================
# 10. Minor Over Budget Scenario (MINOR_OVER: <=5%)
# ===========================================================================


def test_budget_engine_status_minor_over_within_five_percent() -> None:
    """Verify status is MINOR_OVER when projected total is between 0% and 5% over budget."""
    # Projected total = ₹104,000, User budget = ₹100,000 -> 4.0% over budget
    ctx = make_test_context(budget_amount=100_000.0)
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(transport_cost=40_000.0, hotel_cost=40_000.0),
        experience_plan=make_test_experience(
            activity_cost=5_000.0, food_cost=10_000.0, transit_cost=0.0
        ),
        misc_inr=4_000.0,  # Subtotal = 99,000
        custom_contingency_pct=5.0,  # 99,000 * 5.0% = 4,950 -> Total = 103,950 (3.95% over)
    )
    assert breakdown.total_with_contingency_inr == 103_950.0
    assert breakdown.variance.variance_percentage == 3.95
    assert breakdown.variance.status == BudgetStatus.MINOR_OVER
    assert any("minor optimization" in w for w in breakdown.warnings)


# ===========================================================================
# 11. Significant Over Budget Scenario (SIGNIFICANT_OVER: 5–15%)
# ===========================================================================


def test_budget_engine_status_significant_over_five_to_fifteen_percent() -> None:
    """Verify status is SIGNIFICANT_OVER when projected total is between 5% and 15% over budget."""
    # Projected total = ₹110,000, User budget = ₹100,000 -> 10.0% over budget
    ctx = make_test_context(budget_amount=100_000.0)
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(transport_cost=40_000.0, hotel_cost=40_000.0),
        experience_plan=make_test_experience(
            activity_cost=10_000.0, food_cost=10_000.0, transit_cost=0.0
        ),
        misc_inr=0.0,  # Subtotal = 100,000
        custom_contingency_pct=10.0,  # Buffer = 10,000 -> Total = 110,000
    )
    assert breakdown.total_with_contingency_inr == 110_000.0
    assert breakdown.variance.variance_percentage == 10.0
    assert breakdown.variance.status == BudgetStatus.SIGNIFICANT_OVER
    assert any("trade-off decision required" in w for w in breakdown.warnings)


# ===========================================================================
# 12. Infeasible Scenario (INFEASIBLE: >15%)
# ===========================================================================


def test_budget_engine_status_infeasible_above_fifteen_percent() -> None:
    """Verify status is INFEASIBLE when projected total is >15% over user budget."""
    # Projected total = ₹132,000, User budget = ₹100,000 -> 32.0% over budget
    ctx = make_test_context(budget_amount=100_000.0)
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(transport_cost=50_000.0, hotel_cost=50_000.0),
        experience_plan=make_test_experience(
            activity_cost=10_000.0, food_cost=10_000.0, transit_cost=0.0
        ),
        misc_inr=0.0,  # Subtotal = 120,000
        custom_contingency_pct=10.0,  # Buffer = 12,000 -> Total = 132,000
    )
    assert breakdown.total_with_contingency_inr == 132_000.0
    assert breakdown.variance.variance_percentage == 32.0
    assert breakdown.variance.status == BudgetStatus.INFEASIBLE
    assert any("financially infeasible" in w for w in breakdown.warnings)


# ===========================================================================
# 13. Floating-Point Precision & Rounding Invariants
# ===========================================================================


def test_budget_engine_floating_point_precision_invariants() -> None:
    """Verify exact decimal rounding with no floating point inaccuracy."""
    # Test values with complex decimal fractions
    ctx = make_test_context(budget_amount=77_777.77)
    breakdown = process_budget(
        state_or_context=ctx,
        logistics_plan=make_test_logistics(transport_cost=12_345.67, hotel_cost=23_456.78),
        experience_plan=make_test_experience(
            activity_cost=3_456.78,
            food_cost=4_567.89,
            transit_cost=1_234.56,
        ),
        misc_inr=987.65,
        custom_contingency_pct=7.25,
    )
    # Subtotal: 12345.67 + 23456.78 + 3456.78 + 4567.89 + 1234.56 + 0.0 + 987.65 = 46049.33
    assert breakdown.subtotal_inr == 46_049.33
    # Contingency buffer: 46049.33 * 0.0725 = 3338.576425 -> 3338.58
    assert breakdown.contingency.amount_inr == 3_338.58
    # Projected total: 46049.33 + 3338.58 = 49387.91
    assert breakdown.total_with_contingency_inr == 49_387.91
    # Variance check internal consistency
    assert breakdown.variance.variance_inr == round(49_387.91 - 77_777.77, 2)


# ===========================================================================
# 14. Missing Component Handling & Warning Accumulation
# ===========================================================================


def test_budget_engine_missing_logistics_and_experience_plans() -> None:
    """Verify budget engine handles missing planning components gracefully with warnings."""
    ctx = make_test_context()
    breakdown = process_budget(state_or_context=ctx)

    assert breakdown.cost_breakdown.transport_inr == 0.0
    assert breakdown.cost_breakdown.accommodation_inr == 0.0
    assert breakdown.cost_breakdown.activities_inr == 0.0
    assert breakdown.cost_breakdown.food_inr == 0.0
    assert breakdown.cost_breakdown.local_transport_inr == 0.0
    assert any("Logistics plan omitted" in w for w in breakdown.warnings)
    assert any("Experience plan omitted" in w for w in breakdown.warnings)


# ===========================================================================
# 15. LangGraph Node Interface
# ===========================================================================


def test_budget_node_langgraph_state_dict_interface() -> None:
    """Verify budget_node successfully reads state dictionary and returns state update."""
    ctx = make_test_context(budget_amount=120_000.0)
    init_state = process_intake(ctx)
    logistics = make_test_logistics()
    experience = make_test_experience()
    visa = make_test_visa(is_domestic=True)

    state = {
        "initial_state": init_state,
        "logistics_plan": logistics,
        "experience_plan": experience,
        "visa_verdict": visa,
    }

    result = budget_node(state)
    assert isinstance(result, dict)
    assert "budget_breakdown" in result
    bb = result["budget_breakdown"]
    assert isinstance(bb, BudgetBreakdown)
    assert bb.subtotal_inr > 0.0
    assert bb.variance.status in (BudgetStatus.UNDER_BUDGET, BudgetStatus.EXACT)


# ===========================================================================
# 16. Validation & Error Handling
# ===========================================================================


def test_budget_engine_invalid_input_type_raises() -> None:
    """Verify BudgetValidationError is raised when unsupported state argument is provided."""
    with pytest.raises(BudgetValidationError, match="Unsupported state_or_context type"):
        process_budget(state_or_context="invalid-string-input")


def test_budget_engine_empty_dict_raises() -> None:
    """Verify BudgetValidationError is raised when state dict lacks context or initial_state."""
    with pytest.raises(BudgetValidationError, match="State dictionary must contain"):
        process_budget(state_or_context={})
