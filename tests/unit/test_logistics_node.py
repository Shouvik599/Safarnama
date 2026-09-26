"""Unit tests for Phase 8 — Logistics Functionality (Logistics Planning Node).

Tests:
1. Room requirement estimation heuristic for various party compositions (adults + children).
2. Date and stay duration allocation across multi-destination itineraries.
3. Domestic single destination planning (DEL -> BOM -> DEL).
4. Multi-destination itinerary planning (DEL -> Jaipur -> Udaipur -> DEL) with date alignment.
5. Travel style sensitivity: BUDGET vs LUXURY transport and hotel selections.
6. Traveler headcount cost scaling for party members on transport legs.
7. Room count and nights mathematical consistency on hotel stays.
8. Provider failure and graceful fallback handling with zero crashes.
9. Booking URL preservation on transport and hotel records.
10. Budget feasibility warning generation when costs exceed total budget ceiling.
11. LangGraph node interface contract (logistics_node).
12. Error handling on empty destinations or invalid state types.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from src.models.logistics import LogisticsPlan
from src.models.trip import (
    BudgetMode,
    DateMode,
    Pace,
    ResolvedLocation,
    TravelScope,
    TravelStyle,
    TripBudget,
    TripContext,
    TripDates,
    TripParty,
)
from src.nodes.intake_node import process_intake
from src.nodes.logistics_node import (
    LogisticsPlanningError,
    allocate_stay_dates,
    estimate_rooms_required,
    logistics_node,
    process_logistics,
)
from src.tools.hotels import HotelError
from src.tools.transport import TransportError

# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------


def make_context(
    origin: str,
    destinations: list[str],
    scope: TravelScope = TravelScope.DOMESTIC,
    adults: int = 2,
    children: int = 0,
    travel_style: TravelStyle = TravelStyle.COMFORTABLE,
    start_date: str = "2026-10-15",
    duration_days: int = 5,
    budget_amount_inr: float = 80000.0,
) -> TripContext:
    """Create a valid TripContext for logistics testing."""
    end_date = "2026-10-20" if start_date == "2026-10-15" and duration_days == 5 else None
    mode = DateMode.EXACT if end_date else DateMode.FLEXIBLE

    return TripContext(
        origin=origin,
        destinations=destinations,
        scope=scope,
        party=TripParty(adults=adults, children=children),
        dates=TripDates(
            mode=mode,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
        ),
        budget=TripBudget(mode=BudgetMode.TOTAL, amount_inr=budget_amount_inr),
        travel_style=travel_style,
        pace=Pace.BALANCED,
    )


# ---------------------------------------------------------------------------
# Room Requirement Estimation Tests
# ---------------------------------------------------------------------------


def test_estimate_rooms_required_single_adult():
    party = TripParty(adults=1, children=0)
    assert estimate_rooms_required(party) == 1


def test_estimate_rooms_required_couple():
    party = TripParty(adults=2, children=0)
    assert estimate_rooms_required(party) == 1


def test_estimate_rooms_required_couple_with_one_child():
    # 2 adults + 1 child share 1 room
    party = TripParty(adults=2, children=1)
    assert estimate_rooms_required(party) == 1


def test_estimate_rooms_required_solo_with_one_child():
    # 1 adult + 1 child share 1 room
    party = TripParty(adults=1, children=1)
    assert estimate_rooms_required(party) == 1


def test_estimate_rooms_required_couple_with_two_children():
    # 2 adults + 2 children require 2 rooms
    party = TripParty(adults=2, children=2)
    assert estimate_rooms_required(party) == 2


def test_estimate_rooms_required_three_adults():
    party = TripParty(adults=3, children=0)
    assert estimate_rooms_required(party) == 2


def test_estimate_rooms_required_four_adults():
    party = TripParty(adults=4, children=0)
    assert estimate_rooms_required(party) == 2


def test_estimate_rooms_required_five_adults():
    party = TripParty(adults=5, children=0)
    assert estimate_rooms_required(party) == 3


def test_estimate_rooms_required_none_party():
    assert estimate_rooms_required(None) == 1


# ---------------------------------------------------------------------------
# Stay Date Allocation Tests
# ---------------------------------------------------------------------------


def test_allocate_stay_dates_single_destination():
    dest = ResolvedLocation(
        query="BOM",
        name="Mumbai Airport",
        iata_code="BOM",
        city="Mumbai",
        country_code="IN",
        country_name="India",
        latitude=19.0886,
        longitude=72.8679,
    )
    allocations = allocate_stay_dates(
        start_date="2026-11-01",
        duration_days=5,
        destinations=[dest],
    )
    assert len(allocations) == 1
    d, checkin, checkout, nights = allocations[0]
    assert d.city == "Mumbai"
    assert checkin == "2026-11-01"
    assert checkout == "2026-11-05"
    assert nights == 4


def test_allocate_stay_dates_multi_destination():
    dest1 = ResolvedLocation(
        query="Jaipur",
        name="Jaipur Airport",
        iata_code="JAI",
        city="Jaipur",
        country_code="IN",
        country_name="India",
        latitude=26.8242,
        longitude=75.8122,
    )
    dest2 = ResolvedLocation(
        query="Udaipur",
        name="Udaipur Airport",
        iata_code="UDR",
        city="Udaipur",
        country_code="IN",
        country_name="India",
        latitude=24.6178,
        longitude=73.8961,
    )
    allocations = allocate_stay_dates(
        start_date="2026-11-01",
        duration_days=6,
        destinations=[dest1, dest2],
    )
    assert len(allocations) == 2
    # 5 total nights split between 2 destinations: 3 and 2
    d1, in1, out1, n1 = allocations[0]
    d2, in2, out2, n2 = allocations[1]
    assert in1 == "2026-11-01"
    assert out1 == "2026-11-04"
    assert n1 == 3
    # Destination 2 starts when Destination 1 checks out
    assert in2 == out1
    assert out2 == "2026-11-06"
    assert n2 == 2


# ---------------------------------------------------------------------------
# Single Destination Logistics Planning Tests
# ---------------------------------------------------------------------------


def test_process_logistics_single_destination_domestic():
    """Verify single domestic destination produces round-trip legs and 1 hotel stay."""
    ctx = make_context("DEL", ["BOM"], adults=2, children=0)
    state = process_intake(ctx)

    plan = process_logistics(state, use_fixture=True)

    assert isinstance(plan, LogisticsPlan)
    assert len(plan.transport_legs) == 2
    # Outbound leg
    leg1 = plan.transport_legs[0]
    assert leg1.leg_number == 1
    assert leg1.origin.upper() in ("DEL", "DELHI")
    assert leg1.destination.upper() in ("BOM", "MUMBAI")
    assert leg1.price_per_person_inr > 0
    # Scaled to 2 travelers
    assert leg1.total_price_inr == round(leg1.price_per_person_inr * 2, 2)

    # Return leg
    leg2 = plan.transport_legs[1]
    assert leg2.leg_number == 2
    assert leg2.origin.upper() in ("BOM", "MUMBAI")
    assert leg2.destination.upper() in ("DEL", "DELHI")

    # Hotel stays
    assert len(plan.hotel_stays) == 1
    stay = plan.hotel_stays[0]
    assert "MUMBAI" in stay.destination.upper()
    assert stay.nights == 5
    assert stay.rooms_required == 1
    assert stay.price_per_room_per_night_inr > 0
    assert stay.total_accommodation_cost_inr == round(
        stay.price_per_room_per_night_inr * stay.nights * stay.rooms_required, 2
    )

    # Aggregate math
    assert plan.total_transport_cost_inr == round(leg1.total_price_inr + leg2.total_price_inr, 2)
    assert plan.total_accommodation_cost_inr == stay.total_accommodation_cost_inr
    assert plan.route_summary is not None
    assert plan.timestamp is not None


# ---------------------------------------------------------------------------
# Multi-Destination Logistics Planning Tests
# ---------------------------------------------------------------------------


def test_process_logistics_multi_destination():
    """Verify multi-destination route: Origin -> Dest 1 -> Dest 2 -> Origin."""
    ctx = make_context("DEL", ["Jaipur", "Udaipur"], adults=2, duration_days=6)
    state = process_intake(ctx)

    plan = process_logistics(state, use_fixture=True)

    # 3 transport legs: DEL->Jaipur, Jaipur->Udaipur, Udaipur->DEL
    assert len(plan.transport_legs) == 3
    assert plan.transport_legs[0].leg_number == 1
    assert plan.transport_legs[1].leg_number == 2
    assert plan.transport_legs[2].leg_number == 3

    # 2 hotel stays: Jaipur and Udaipur
    assert len(plan.hotel_stays) == 2
    stay1 = plan.hotel_stays[0]
    stay2 = plan.hotel_stays[1]

    # Date continuity: checkout of stay1 is checkin of stay2
    assert stay1.checkout_date == stay2.checkin_date
    # Return leg departs on checkout date of stay2
    assert plan.transport_legs[2].departure_datetime.startswith(stay2.checkout_date)

    # Costs are positive and deterministic
    assert plan.total_transport_cost_inr > 0
    assert plan.total_accommodation_cost_inr > 0


# ---------------------------------------------------------------------------
# Party Size & Room Count Scaling Tests
# ---------------------------------------------------------------------------


def test_process_logistics_party_scaling_with_children():
    """Verify party of 2 adults + 2 children requires 2 rooms and scales transport fares by 4."""
    ctx = make_context("DEL", ["BOM"], adults=2, children=2)
    state = process_intake(ctx)

    plan = process_logistics(state, use_fixture=True)

    # Total headcount is 4
    for leg in plan.transport_legs:
        assert leg.total_price_inr == round(leg.price_per_person_inr * 4, 2)

    # Hotel rooms required is 2
    stay = plan.hotel_stays[0]
    assert stay.rooms_required == 2
    assert stay.total_accommodation_cost_inr == round(
        stay.price_per_room_per_night_inr * stay.nights * 2, 2
    )


# ---------------------------------------------------------------------------
# Travel Style Sensitivity Tests
# ---------------------------------------------------------------------------


def test_process_logistics_travel_style_budget_vs_luxury():
    """Verify budget style selects lower cost or standard options compared to luxury style."""
    ctx_budget = make_context(
        "DEL", ["BOM"], travel_style=TravelStyle.BUDGET, budget_amount_inr=30000.0
    )
    ctx_luxury = make_context(
        "DEL", ["BOM"], travel_style=TravelStyle.LUXURY, budget_amount_inr=250000.0
    )

    state_budget = process_intake(ctx_budget)
    state_luxury = process_intake(ctx_luxury)

    plan_budget = process_logistics(state_budget, use_fixture=True)
    plan_luxury = process_logistics(state_luxury, use_fixture=True)

    # Luxury hotel star rating should be >= budget hotel star rating
    assert (plan_luxury.hotel_stays[0].star_rating or 5) >= (
        plan_budget.hotel_stays[0].star_rating or 3
    )

    # Total costs for luxury should exceed or equal budget
    assert plan_luxury.total_accommodation_cost_inr >= plan_budget.total_accommodation_cost_inr


# ---------------------------------------------------------------------------
# Provider Failure & Fallback Tests
# ---------------------------------------------------------------------------


def test_process_logistics_provider_failure_resilience():
    """Verify logistics planning does not crash when underlying search tools fail."""
    ctx = make_context("DEL", ["BOM"], adults=1)
    state = process_intake(ctx)

    with (
        patch(
            "src.nodes.logistics_node.search_transport",
            side_effect=TransportError("Network timeout"),
        ),
        patch(
            "src.nodes.logistics_node.search_hotels",
            side_effect=HotelError("API down"),
        ),
    ):
        plan = process_logistics(state, use_fixture=False)

    assert isinstance(plan, LogisticsPlan)
    assert len(plan.transport_legs) == 2
    assert len(plan.hotel_stays) == 1
    assert plan.is_estimated is True
    # Non-fatal warnings recorded
    assert any("fallback" in w.lower() or "unavailable" in w.lower() for w in plan.warnings)


# ---------------------------------------------------------------------------
# Booking URL Preservation Tests
# ---------------------------------------------------------------------------


def test_process_logistics_preserves_booking_urls():
    """Verify booking URLs from fixtures/tools are populated in output models."""
    ctx = make_context("DEL", ["BOM"], adults=1)
    state = process_intake(ctx)

    plan = process_logistics(state, use_fixture=True)

    # At least one transport leg or hotel stay should contain a valid booking URL in fixture mode
    has_transport_url = any(leg.booking_url is not None for leg in plan.transport_legs)
    has_hotel_url = any(stay.booking_url is not None for stay in plan.hotel_stays)
    assert has_transport_url or has_hotel_url


# ---------------------------------------------------------------------------
# Budget Feasibility Warning Tests
# ---------------------------------------------------------------------------


def test_process_logistics_budget_feasibility_warning():
    """Verify a warning is added when logistics costs exceed user budget."""
    # Ultra-low budget of ₹1,000 for a 5-day trip to Mumbai
    ctx = make_context("DEL", ["BOM"], budget_amount_inr=1000.0)
    state = process_intake(ctx)

    plan = process_logistics(state, use_fixture=True)

    # Should flag a budget warning
    assert any("exceeds total trip budget" in w.lower() for w in plan.warnings)


# ---------------------------------------------------------------------------
# State Processing & LangGraph Interface Tests
# ---------------------------------------------------------------------------


def test_process_logistics_from_trip_context_directly():
    """Verify process_logistics can accept a raw TripContext and internally invoke intake."""
    ctx = make_context("DEL", ["BOM"])
    plan = process_logistics(ctx, use_fixture=True)
    assert isinstance(plan, LogisticsPlan)
    assert len(plan.transport_legs) == 2


def test_process_logistics_from_dict_state():
    """Verify process_logistics can accept a dictionary state."""
    ctx = make_context("DEL", ["BOM"])
    state = process_intake(ctx)
    state_dict = {
        "trip_context": ctx,
        "origin": state.origin,
        "destinations": state.destinations,
        "effective_duration_days": state.effective_duration_days,
        "total_budget_inr": state.total_budget_inr,
        "travel_scope": state.travel_scope,
    }
    plan = process_logistics(state_dict, use_fixture=True)
    assert isinstance(plan, LogisticsPlan)
    assert len(plan.transport_legs) == 2


def test_logistics_node_langgraph_interface():
    """Verify logistics_node returns a dictionary with 'logistics_plan'."""
    ctx = make_context("DEL", ["BOM"])
    state = process_intake(ctx)

    result = logistics_node(state)
    assert isinstance(result, dict)
    assert "logistics_plan" in result
    assert isinstance(result["logistics_plan"], LogisticsPlan)


def test_process_logistics_invalid_input_error():
    """Verify invalid state inputs raise LogisticsPlanningError."""
    with pytest.raises(LogisticsPlanningError):
        process_logistics(12345)  # type: ignore[arg-type]
