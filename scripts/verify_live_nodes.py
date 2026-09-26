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


def main() -> None:
    print("\n" + "#" * 70)
    print("  SAFARNAMA LIVE EXTERNAL INTEGRATION TEST SUITE")
    print("  Validates all 5 planning stages (Visa, Logistics, Experience, Budget, Optimizer)")
    print("#" * 70)

    try:
        test_live_visa_node()
        logistics = test_live_logistics_node()
        state, experience = test_live_experience_node(logistics)
        budget = test_live_budget_node(state, logistics, experience)
        test_live_optimizer_node(state, budget, logistics, experience)

        print("\n" + "=" * 70)
        print("  ALL 5 LIVE PLANNING NODE INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70 + "\n")
    except Exception as exc:
        print(f"\n[FAIL] Live test failed with error: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
