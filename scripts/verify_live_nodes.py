"""Live external integration verification for Safarnama planning nodes.

Tests all 3 external-facing planning nodes against live APIs:
1. Visa Node (process_visa with live Tavily web search + Gemini LLM policy analysis)
2. Logistics Node (process_logistics with live transport + hotel search APIs)
3. Experience Node (process_experience with live Open-Meteo weather + live places/dining)

Usage:
    uv run python scripts/verify_live_nodes.py
"""

from __future__ import annotations

import sys
import time

from dotenv import load_dotenv
from src.graph import replan_workflow, run_planning_graph
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
from src.nodes.budget_node import process_budget
from src.nodes.experience_node import process_experience
from src.nodes.intake_node import process_intake
from src.nodes.logistics_node import process_logistics
from src.nodes.optimizer_node import process_optimizer
from src.nodes.visa_node import process_visa

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()


def print_banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_live_visa_node() -> None:
    print_banner("1. LIVE TEST: Visa Planning Node (Phase 7)")
    print("Destination: Thailand (BKK) for Indian Passport Holder")
    print("Calling live web search (Tavily) + live Gemini semantic policy extraction...")

    ctx = TripContext(
        origin="DEL",
        destinations=["BKK"],
        scope=TravelScope.INTERNATIONAL,
        party=TripParty(adults=2, children=0),
        dates=TripDates(
            mode=DateMode.EXACT,
            start_date="2026-11-10",
            end_date="2026-11-17",
            duration_days=8,
        ),
        budget=TripBudget(mode=BudgetMode.TOTAL, amount_inr=150000.0),
        travel_style=TravelStyle.COMFORTABLE,
        pace=Pace.BALANCED,
    )
    state = process_intake(ctx)

    t0 = time.perf_counter()
    verdict = process_visa(state, live_search_enabled=True)
    elapsed = time.perf_counter() - t0

    print(f"\n[OK] Visa Verdict generated in {elapsed:.2f}s:")
    print(f"  - Total Visa Cost (2 travelers): INR {verdict.total_visa_cost_inr:,.2f}")
    print(f"  - Advance Application Required: {verdict.requires_advance_application}")
    print(f"  - Schengen Single Visa: {verdict.schengen_single_visa_applicable}")
    print(f"  - Country Verdicts ({len(verdict.countries)}):")
    for cv in verdict.countries:
        print(f"    * {cv.country_name} ({cv.country_code}):")
        print(f"        Status: {cv.status.value}")
        print(f"        Per-person fee: INR {cv.visa_fee_inr:,.2f}")
        print(f"        Max Stay Days: {cv.permitted_stay_days}")
        if cv.warnings:
            print(f"        Warnings: {cv.warnings}")

    assert verdict is not None
    assert len(verdict.countries) >= 1
    assert verdict.total_visa_cost_inr >= 0


def test_live_logistics_node() -> None:
    print_banner("2. LIVE TEST: Logistics Planning Node (Phase 8)")
    print("Route: New Delhi (DEL) -> Mumbai (BOM) -> New Delhi (DEL)")
    print("Calling live flight/transport search + live hotel search...")

    ctx = TripContext(
        origin="DEL",
        destinations=["BOM"],
        scope=TravelScope.DOMESTIC,
        party=TripParty(adults=2, children=1),
        dates=TripDates(
            mode=DateMode.EXACT,
            start_date="2026-10-15",
            end_date="2026-10-19",
            duration_days=5,
        ),
        budget=TripBudget(mode=BudgetMode.TOTAL, amount_inr=85000.0),
        travel_style=TravelStyle.COMFORTABLE,
        pace=Pace.BALANCED,
    )
    state = process_intake(ctx)

    t0 = time.perf_counter()
    logistics = process_logistics(state, use_fixture=False)
    elapsed = time.perf_counter() - t0

    tot_logistics = logistics.total_transport_cost_inr + logistics.total_accommodation_cost_inr
    print(f"\n[OK] Logistics Plan generated in {elapsed:.2f}s:")
    print(f"  - Total Transport Cost: INR {logistics.total_transport_cost_inr:,.2f}")
    print(f"  - Total Accommodation Cost: INR {logistics.total_accommodation_cost_inr:,.2f}")
    print(f"  - Total Logistics Cost: INR {tot_logistics:,.2f}")

    print(f"\n  - Transport Legs ({len(logistics.transport_legs)}):")
    for leg in logistics.transport_legs:
        carrier = leg.carrier or "N/A"
        print(f"    * {leg.origin} -> {leg.destination} ({leg.mode}) via {carrier}:")
        dur_str = f"{(leg.duration_minutes / 60):.1f}h" if leg.duration_minutes else "N/A"
        print(
            f"        Fare: INR {leg.price_per_person_inr:,.2f} "
            f"(Total: INR {leg.total_price_inr:,.2f})"
        )
        print(
            f"        Duration: {dur_str} | "
            f"Provider: {leg.provider} (Estimated: {leg.is_estimated})"
        )

    print(f"\n  - Hotel Stays ({len(logistics.hotel_stays)}):")
    for stay in logistics.hotel_stays:
        print(f"    * {stay.hotel_name} in {stay.destination} ({stay.star_rating}-star):")
        print(f"        Nights: {stay.nights}, Rooms: {stay.rooms_required}")
        print(f"        Rate/room/night: INR {stay.price_per_room_per_night_inr:,.2f}")
        print(f"        Total stay cost: INR {stay.total_accommodation_cost_inr:,.2f}")
        print(f"        Provider: {stay.provider} (Estimated: {stay.is_estimated})")
        if stay.booking_url:
            print(f"        Booking URL: {stay.booking_url}")

    assert logistics is not None
    assert len(logistics.transport_legs) >= 2
    assert len(logistics.hotel_stays) >= 1
    return logistics


def test_live_experience_node(logistics_plan=None) -> None:
    print_banner("3. LIVE TEST: Experience Planning Node (Phase 9)")
    print("Destination: Mumbai (BOM)")
    print("Calling live Open-Meteo weather API + live Places & Dining search...")

    ctx = TripContext(
        origin="DEL",
        destinations=["BOM"],
        scope=TravelScope.DOMESTIC,
        party=TripParty(adults=2, children=1),
        dates=TripDates(
            mode=DateMode.EXACT,
            start_date="2026-10-15",
            end_date="2026-10-19",
            duration_days=5,
        ),
        budget=TripBudget(mode=BudgetMode.TOTAL, amount_inr=85000.0),
        travel_style=TravelStyle.COMFORTABLE,
        pace=Pace.BALANCED,
        must_visits=["Gateway of India", "Marine Drive"],
    )
    state = process_intake(ctx)

    t0 = time.perf_counter()
    experience = process_experience(state, logistics_plan=logistics_plan, use_fixture=False)
    elapsed = time.perf_counter() - t0

    print(f"\n[OK] Experience Plan generated in {elapsed:.2f}s:")
    print(f"  - Total Days: {experience.total_days}")
    print(f"  - Total Activity Cost: INR {experience.total_activity_cost_inr:,.2f}")
    print(f"  - Total Food Cost: INR {experience.total_food_cost_inr:,.2f}")
    print(f"  - Total Local Transit Cost: INR {experience.total_local_transport_cost_inr:,.2f}")
    print(f"  - Weather Substitutions Count: {experience.weather_substitutions}")
    print(f"  - Must-Visits Fulfilled: {experience.must_visits_fulfilled}")

    print(f"\n  - Sample Day Plan (Day 1 in {experience.days[0].city}):")
    day1 = experience.days[0]
    print(f"    Date: {day1.date} | Weather: {day1.weather_summary}")
    print(f"    Hotel: {day1.hotel_name or 'N/A'}")
    print("    Activities:")
    for act in day1.activities:
        sub_tag = f" [SUBSTITUTED for {act.substituted_for}]" if act.is_weather_substituted else ""
        party_cost = act.poi.estimated_cost_inr * 3
        print(
            f"      - [{act.daypart.value}] {act.poi.name} "
            f"({act.poi.category.value}){sub_tag} - INR {party_cost:,.2f} party cost"
        )
        if act.poi.maps_url:
            print(f"        Maps URL: {act.poi.maps_url}")
    print("    Dining:")
    for meal in day1.meals:
        venue = meal.restaurant_name or "Local Cafe"
        cuisine = meal.cuisine or "Regional Specialities"
        print(
            f"      - [{meal.meal_type.title()}] {venue} - "
            f"INR {meal.estimated_cost_inr:,.2f} ({cuisine})"
        )
        if meal.maps_url:
            print(f"        Maps URL: {meal.maps_url}")

    assert experience is not None
    assert experience.total_days == 5
    assert len(experience.days) == 5
    assert len(experience.days[0].meals) == 3
    return state, experience


def test_live_budget_node(state, logistics, experience) -> None:
    print_banner("4. LIVE TEST: Deterministic Budget Engine (Phase 10)")
    print("Aggregating live logistics, live experience, and domestic zero-visa breakdown...")

    t0 = time.perf_counter()
    budget = process_budget(
        state_or_context=state,
        logistics_plan=logistics,
        experience_plan=experience,
    )
    elapsed = time.perf_counter() - t0

    print(f"\n[OK] Budget Breakdown generated in {elapsed:.4f}s:")
    cb = budget.cost_breakdown
    print(f"  - Transport:        INR {cb.transport_inr:,.2f}")
    print(f"  - Accommodation:    INR {cb.accommodation_inr:,.2f}")
    print(f"  - Activities:       INR {cb.activities_inr:,.2f}")
    print(f"  - Food & Dining:    INR {cb.food_inr:,.2f}")
    print(f"  - Local Transit:    INR {cb.local_transport_inr:,.2f}")
    print(f"  - Visa Fees:        INR {cb.visa_inr:,.2f}")
    print(f"  - Miscellaneous:    INR {cb.misc_inr:,.2f}")
    print("  -------------------------------------------")
    print(f"  - Subtotal:         INR {budget.subtotal_inr:,.2f}")
    print(
        f"  - Contingency:      INR {budget.contingency.amount_inr:,.2f} "
        f"({budget.contingency.percentage:.1f}%)"
    )
    print(f"  - Projected Total:  INR {budget.total_with_contingency_inr:,.2f}")
    print(f"  - User Budget:      INR {budget.variance.user_budget_inr:,.2f}")
    print(
        f"  - Budget Variance:  INR {budget.variance.variance_inr:,.2f} "
        f"({budget.variance.variance_percentage:+.1f}%)"
    )
    print(f"  - Health Status:    {budget.variance.status.value}")
    print(f"  - Cost Per Person:  INR {budget.per_person_cost_inr:,.2f} (3 travelers)")
    if budget.warnings:
        print("  - Actionable Warnings:")
        for w in budget.warnings:
            print(f"    * {w}")

    assert budget is not None
    assert budget.subtotal_inr > 0.0
    assert budget.total_with_contingency_inr >= budget.subtotal_inr
    assert budget.per_person_cost_inr > 0.0
    return budget


def test_live_optimizer_node(state, budget, logistics, experience) -> None:
    print_banner("5. LIVE TEST: Optimizer Functionality (Phase 11)")
    print(f"Evaluating budget status ({budget.variance.status.value}) with real live plans...")

    t0 = time.perf_counter()
    output = process_optimizer(
        state_or_context=state,
        budget_breakdown=budget,
        logistics_plan=logistics,
        experience_plan=experience,
    )
    elapsed = time.perf_counter() - t0

    res = output.optimization_result
    print(f"\n[OK] Optimization Result generated in {elapsed:.4f}s:")
    print(f"  - Action Taken:       {res.action.value}")
    print(f"  - Achieved Savings:   INR {res.savings_inr:,.2f}")
    print(f"  - Guardrails Kept:    {res.guardrails_respected}")
    print(f"  - Description:        {res.description}")
    if res.trade_offs:
        print("  - Actionable Trade-offs:")
        for to in res.trade_offs:
            print(f"    * {to}")
    if res.alternatives_presented:
        print("  - Alternatives Presented:")
        for alt in res.alternatives_presented:
            print(f"    * {alt}")

    assert output is not None
    assert output.optimization_result.guardrails_respected is True
    assert output.budget_breakdown is not None


def test_live_langgraph_orchestration() -> None:
    print_banner("6. LIVE TEST: LangGraph Orchestration (Phase 12)")
    print("Executing full autonomous StateGraph workflow with live APIs...")

    trip_request = {
        "origin": "DEL",
        "destinations": ["GOI"],
        "scope": "DOMESTIC",
        "dates": {
            "mode": "EXACT",
            "start_date": "2026-10-15",
            "end_date": "2026-10-18",
            "duration_days": 3,
        },
        "party": {"adults": 2, "children": 0},
        "budget": {"amount_inr": 60000.0, "mode": "TOTAL"},
        "travel_style": "COMFORTABLE",
        "pace": "BALANCED",
        "activity_preferences": ["BEACH", "HISTORICAL"],
    }

    t0 = time.perf_counter()
    graph_output = run_planning_graph(trip_request)
    elapsed = time.perf_counter() - t0

    print(f"\n[OK] Full LangGraph StateGraph executed in {elapsed:.4f}s:")
    print(f"  - Terminal Plan Status:   {graph_output.get('plan_status')}")
    print(f"  - Scope Routed:           {graph_output.get('travel_scope')}")
    print(f"  - Logistics Plan Legs:    {len(graph_output['logistics_plan'].transport_legs)}")
    print(f"  - Logistics Hotel:        {graph_output['logistics_plan'].hotel_stays[0].hotel_name}")
    print(f"  - Experience Days:        {len(graph_output['experience_plan'].days)}")
    total_inr = graph_output["budget_breakdown"].total_with_contingency_inr
    print(f"  - Budget Projected Total: INR {total_inr:,.2f}")
    print(f"  - Optimization Action:    {graph_output['optimization_result'].action.value}")
    print(f"  - Total Warnings Caught:  {len(graph_output.get('warnings', []))}")

    assert graph_output.get("trip_context") is not None
    assert graph_output.get("logistics_plan") is not None
    assert graph_output.get("experience_plan") is not None
    assert graph_output.get("budget_breakdown") is not None
    assert graph_output.get("optimization_result") is not None

    print("\nTesting Selective Re-planning with Reuse of Unaffected Work...")
    t_replan = time.perf_counter()
    replanned = replan_workflow(
        current_state=graph_output,
        proposal_type="INCREASE_BUDGET",
        target_value=90000.0,
    )
    elapsed_replan = time.perf_counter() - t_replan

    print(f"[OK] Re-planning completed in {elapsed_replan:.4f}s:")
    print(f"  - Re-planning Proposal:   {replanned['replan_proposal']['proposal_type']}")
    print(f"  - Reused Components:      {replanned['replan_proposal']['reused_components']}")
    print(f"  - Rerun Components:       {replanned['replan_proposal']['rerun_components']}")
    print(f"  - New Status:             {replanned.get('plan_status')}")

    assert replanned["replan_requested"] is True
    assert "logistics" in replanned["replan_proposal"]["reused_components"]
    assert "experience" in replanned["replan_proposal"]["reused_components"]
    assert replanned["trip_context"].budget.amount_inr == 90000.0


def test_live_vertical_slice() -> None:
    print_banner("7. LIVE TEST: End-to-End Vertical Slice (API & Synthesizer - Phase 13)")
    print("Controlled Scenario: Delhi -> Goa, 2 adults, 4 days, Comfortable, ₹100,000 budget")
    print("Executing POST /api/v1/plan via FastAPI service...")

    from fastapi.testclient import TestClient
    from src.api.app import app

    client = TestClient(app)
    payload = {
        "origin": "Delhi",
        "destinations": ["Goa"],
        "start_date": "2026-11-01",
        "end_date": "2026-11-04",
        "adults": 2,
        "children": 0,
        "budget_inr": 100000.0,
        "travel_style": "COMFORTABLE",
        "pace": "BALANCED",
        "activity_preferences": ["beaches", "relaxation"],
        "must_visits": ["Baga Beach"],
    }

    t0 = time.perf_counter()
    resp = client.post("/api/v1/plan", json=payload)
    elapsed = time.perf_counter() - t0

    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}: {resp.text}"
    data = resp.json()
    itinerary = data["itinerary"]

    print(f"\n[OK] Vertical Slice API response received in {elapsed:.4f}s:")
    print(f"  - Status:            {data['status']}")
    print(f"  - Title:             {itinerary['title']}")
    print(f"  - Trip ID:           {itinerary['trip_id']}")
    print(f"  - Transport Legs:    {len(itinerary['logistics_plan']['transport_legs'])}")
    print(f"  - Hotel Stays:       {len(itinerary['logistics_plan']['hotel_stays'])}")
    print(f"  - Experience Days:   {len(itinerary['experience_plan']['days'])}")
    total_proj = itinerary["budget_breakdown"]["total_with_contingency_inr"]
    print(f"  - Projected Total:   INR {total_proj:,.2f}")
    print(f"  - Estimated Flag:    {itinerary['is_estimated']}")
    print(f"  - Summary:           {itinerary['summary'][:150]}...")

    assert itinerary["title"]
    assert itinerary["summary"]
    assert total_proj > 0


def test_live_international_vertical_slice() -> None:
    print_banner("8. LIVE TEST: International Vertical Slice (API & Live Visa - Phase 14)")
    print(
        "Controlled Scenario: Delhi -> Bangkok, Thailand, 2 adults, 4 days, "
        "Comfortable, ₹150,000 budget"
    )
    print("Executing POST /api/v1/plan via FastAPI service...")

    from fastapi.testclient import TestClient
    from src.api.app import app

    client = TestClient(app)
    payload = {
        "origin": "Delhi",
        "destinations": ["Bangkok, Thailand"],
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "adults": 2,
        "children": 0,
        "budget_inr": 150000.0,
        "travel_style": "COMFORTABLE",
        "pace": "BALANCED",
        "scope": "INTERNATIONAL",
        "activity_preferences": ["temples", "street food", "culture"],
    }

    t0 = time.perf_counter()
    resp = client.post("/api/v1/plan", json=payload)
    elapsed = time.perf_counter() - t0

    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}: {resp.text}"
    data = resp.json()
    itinerary = data["itinerary"]

    print(f"\n[OK] International Vertical Slice API response received in {elapsed:.4f}s:")
    print(f"  - Status:            {data['status']}")
    print(f"  - Title:             {itinerary['title']}")
    print(f"  - Trip ID:           {itinerary['trip_id']}")
    print(f"  - Scope:             {itinerary['trip_context']['scope']}")
    visa = itinerary["visa_verdict"]
    print(f"  - Visa Bypass:       {visa['is_domestic_bypass']}")
    print(f"  - Visa Countries:    {[c['country_name'] for c in visa['countries']]}")
    print(f"  - Total Visa Cost:   INR {visa['total_visa_cost_inr']:,.2f}")
    print(f"  - Transport Legs:    {len(itinerary['logistics_plan']['transport_legs'])}")
    print(f"  - Hotel Stays:       {len(itinerary['logistics_plan']['hotel_stays'])}")
    print(f"  - Experience Days:   {len(itinerary['experience_plan']['days'])}")
    total_proj = itinerary["budget_breakdown"]["total_with_contingency_inr"]
    print(f"  - Projected Total:   INR {total_proj:,.2f}")
    print(f"  - Summary:           {itinerary['summary'][:160]}...")

    assert itinerary["title"]
    assert itinerary["summary"]
    assert visa["is_domestic_bypass"] is False
    assert len(visa["countries"]) >= 1
    assert total_proj > 0


def main() -> None:
    print("\n" + "#" * 70)
    print("  SAFARNAMA LIVE EXTERNAL INTEGRATION TEST SUITE")
    print(
        "  Validates all 8 stages "
        "(Visa, Logistics, Experience, Budget, Optimizer, Graph, Slice, Intl Slice)"
    )
    print("#" * 70)

    try:
        test_live_visa_node()
        logistics = test_live_logistics_node()
        state, experience = test_live_experience_node(logistics)
        budget = test_live_budget_node(state, logistics, experience)
        test_live_optimizer_node(state, budget, logistics, experience)
        test_live_langgraph_orchestration()
        test_live_vertical_slice()
        test_live_international_vertical_slice()

        print("\n" + "=" * 70)
        print("  ALL 8 LIVE PLANNING INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70 + "\n")
    except Exception as exc:
        print(f"\n[FAIL] Live test failed with error: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
