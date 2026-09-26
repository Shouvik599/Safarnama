"""Unit tests for Phase 9 — Experience Functionality (Experience Planning Node).

Tests:
1. Daily activity scheduling and pacing calibration (RELAXED vs BALANCED vs PACKED).
2. Must-visit sights prioritization and fulfillment tracking.
3. Dining recommendations (breakfast, lunch, dinner) from places tool.
4. Weather evaluation and indoor activity substitution for adverse forecast conditions.
5. Multi-destination daily itinerary distribution across cities.
6. Hotel stay and booking URL association from LogisticsPlan.
7. Party size scaling on activity and food costs.
8. Provider failure resilience with zero crashes when places or weather tools error.
9. LangGraph node interface contract (experience_node).
10. Input validation and error handling on invalid states.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from src.models.itinerary import ExperiencePlan
from src.models.logistics import HotelStay, LogisticsPlan
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
from src.models.weather import DailyWeatherForecast, WeatherForecastResult
from src.nodes.experience_node import (
    ExperiencePlanningError,
    experience_node,
    process_experience,
)
from src.nodes.intake_node import process_intake
from src.tools.places import PlaceError
from src.tools.weather import WeatherError

# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------


def make_context(
    origin: str,
    destinations: list[str],
    scope: TravelScope = TravelScope.DOMESTIC,
    adults: int = 2,
    children: int = 0,
    pace: Pace = Pace.BALANCED,
    must_visit: list[str] | None = None,
    duration_days: int = 5,
    start_date: str = "2026-10-15",
) -> TripContext:
    """Create a valid TripContext for experience testing."""
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = (start_dt + timedelta(days=duration_days - 1)).strftime("%Y-%m-%d")
    return TripContext(
        origin=origin,
        destinations=destinations,
        scope=scope,
        party=TripParty(adults=adults, children=children),
        dates=TripDates(
            mode=DateMode.EXACT,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
        ),
        budget=TripBudget(mode=BudgetMode.TOTAL, amount_inr=80000.0),
        travel_style=TravelStyle.COMFORTABLE,
        pace=pace,
        must_visits=must_visit or [],
    )


# ---------------------------------------------------------------------------
# Pacing Calibration Tests
# ---------------------------------------------------------------------------


def test_experience_pacing_relaxed():
    """Verify RELAXED pace schedules 1 activity per day."""
    ctx = make_context("DEL", ["BOM"], pace=Pace.RELAXED, duration_days=3)
    state = process_intake(ctx)

    plan = process_experience(state, use_fixture=True)

    assert isinstance(plan, ExperiencePlan)
    assert plan.total_days == 3
    for day in plan.days:
        assert len(day.activities) == 1


def test_experience_pacing_balanced():
    """Verify BALANCED pace schedules 2 activities per day."""
    ctx = make_context("DEL", ["BOM"], pace=Pace.BALANCED, duration_days=3)
    state = process_intake(ctx)

    plan = process_experience(state, use_fixture=True)

    assert plan.total_days == 3
    for day in plan.days:
        assert len(day.activities) == 2


def test_experience_pacing_packed():
    """Verify PACKED pace schedules 3 activities per day."""
    ctx = make_context("DEL", ["BOM"], pace=Pace.PACKED, duration_days=3)
    state = process_intake(ctx)

    plan = process_experience(state, use_fixture=True)

    assert plan.total_days == 3
    for day in plan.days:
        assert len(day.activities) == 3


# ---------------------------------------------------------------------------
# Must-Visit Sights Prioritization Tests
# ---------------------------------------------------------------------------


def test_experience_must_visit_fulfillment():
    """Verify must-visit sights requested by traveler are scheduled and tracked."""
    ctx = make_context(
        "DEL",
        ["BOM"],
        must_visit=["Gateway of India"],
        duration_days=4,
    )
    state = process_intake(ctx)

    plan = process_experience(state, use_fixture=True)

    assert "Gateway of India" in plan.must_visits_fulfilled
    assert "Gateway of India" not in plan.must_visits_omitted

    # At least one activity slot must feature the Gateway of India
    all_poi_names = [slot.poi.name for d in plan.days for slot in d.activities]
    assert any("Gateway of India" in name for name in all_poi_names)


# ---------------------------------------------------------------------------
# Dining Recommendations Tests
# ---------------------------------------------------------------------------


def test_experience_dining_recommendations():
    """Verify each day contains breakfast, lunch, and dinner recommendations."""
    ctx = make_context("DEL", ["BOM"], duration_days=3)
    state = process_intake(ctx)

    plan = process_experience(state, use_fixture=True)

    for day in plan.days:
        assert len(day.meals) == 3
        meal_types = [m.meal_type for m in day.meals]
        assert "breakfast" in meal_types
        assert "lunch" in meal_types
        assert "dinner" in meal_types

        # Food cost is calculated and positive
        assert day.food_cost_inr > 0


# ---------------------------------------------------------------------------
# Weather Evaluation & Activity Substitution Tests
# ---------------------------------------------------------------------------


def test_experience_weather_indoor_substitution():
    """Verify adverse rainy forecast triggers indoor substitution for outdoor activities."""
    ctx = make_context("DEL", ["BOM"], duration_days=2)
    state = process_intake(ctx)

    # Mock adverse weather: 85% rain, thunderstorm, not outdoor friendly
    mock_rainy_forecast = DailyWeatherForecast(
        date="2026-10-15",
        temp_max_c=24.0,
        temp_min_c=20.0,
        temp_avg_c=22.0,
        precipitation_probability=85,
        precipitation_mm=45.0,
        weather_code=65,
        condition="Heavy rain",
        is_outdoor_friendly=False,
    )
    mock_weather_res = WeatherForecastResult(
        destination="Mumbai",
        latitude=19.0886,
        longitude=72.8679,
        start_date="2026-10-15",
        end_date="2026-10-16",
        daily_forecasts=[mock_rainy_forecast],
        provider="fixture",
        is_estimated=True,
        summary="Heavy rain forecast",
        timestamp="2026-09-26T00:00:00Z",
    )

    with patch(
        "src.nodes.experience_node.get_weather_forecast",
        return_value=mock_weather_res,
    ):
        plan = process_experience(state, use_fixture=True)

    # Should have triggered at least one weather substitution
    assert plan.weather_substitutions > 0

    # Look for substituted activity slot
    substituted_slots = [
        slot for day in plan.days for slot in day.activities if slot.is_weather_substituted
    ]
    assert len(substituted_slots) > 0
    sub_slot = substituted_slots[0]
    assert sub_slot.substituted_for is not None
    assert sub_slot.weather_note is not None
    assert "rain" in sub_slot.weather_note.lower()


# ---------------------------------------------------------------------------
# Multi-Destination Itinerary Distribution Tests
# ---------------------------------------------------------------------------


def test_experience_multi_destination_distribution():
    """Verify days are sequentially assigned across multi-destination route."""
    ctx = make_context("DEL", ["Jaipur", "Udaipur"], duration_days=6)
    state = process_intake(ctx)

    plan = process_experience(state, use_fixture=True)

    assert plan.total_days == 6
    cities_in_plan = [d.city for d in plan.days]
    assert "Jaipur" in cities_in_plan
    assert "Udaipur" in cities_in_plan
    assert plan.destinations_covered == ["Jaipur", "Udaipur"]


# ---------------------------------------------------------------------------
# Hotel Association from LogisticsPlan Tests
# ---------------------------------------------------------------------------


def test_experience_hotel_association_from_logistics():
    """Verify DayPlans inherit hotel names and booking URLs from LogisticsPlan."""
    ctx = make_context("DEL", ["BOM"], duration_days=3)
    state = process_intake(ctx)

    mock_hotel_stay = HotelStay(
        destination="Mumbai",
        hotel_name="The Taj Mahal Palace Mumbai",
        star_rating=5,
        user_rating=9.3,
        checkin_date="2026-10-15",
        checkout_date="2026-10-18",
        nights=3,
        rooms_required=1,
        price_per_room_per_night_inr=24500.0,
        total_accommodation_cost_inr=73500.0,
        booking_url="https://safarnama.local/hotels/taj-mahal-palace",
        provider="fixture",
        is_estimated=False,
    )
    mock_logistics = LogisticsPlan(
        transport_legs=[],
        hotel_stays=[mock_hotel_stay],
        total_transport_cost_inr=0.0,
        total_accommodation_cost_inr=73500.0,
        timestamp="2026-09-26T00:00:00Z",
    )

    plan = process_experience(state, logistics_plan=mock_logistics, use_fixture=True)

    # Days 1 and 2 should have Taj Mahal Palace associated
    assert plan.days[0].hotel_name == "The Taj Mahal Palace Mumbai"
    assert plan.days[0].hotel_booking_url == "https://safarnama.local/hotels/taj-mahal-palace"
    assert plan.days[1].hotel_name == "The Taj Mahal Palace Mumbai"
    # Final day (departure day) has None hotel_name
    assert plan.days[2].hotel_name is None


# ---------------------------------------------------------------------------
# Party Size Scaling Tests
# ---------------------------------------------------------------------------


def test_experience_party_cost_scaling():
    """Verify activity and food costs scale deterministically by traveler party size."""
    ctx_solo = make_context("DEL", ["BOM"], adults=1, children=0, duration_days=2)
    ctx_family = make_context("DEL", ["BOM"], adults=2, children=2, duration_days=2)

    state_solo = process_intake(ctx_solo)
    state_family = process_intake(ctx_family)

    plan_solo = process_experience(state_solo, use_fixture=True)
    plan_family = process_experience(state_family, use_fixture=True)

    # Family has 4 travelers, solo has 1 -> food and activity costs scale 4x
    assert plan_family.total_food_cost_inr == pytest.approx(
        plan_solo.total_food_cost_inr * 4, rel=1e-2
    )
    assert plan_family.total_activity_cost_inr == pytest.approx(
        plan_solo.total_activity_cost_inr * 4, rel=1e-2
    )


# ---------------------------------------------------------------------------
# Provider Failure Resilience Tests
# ---------------------------------------------------------------------------


def test_experience_provider_failure_resilience():
    """Verify experience node does not crash when places and weather tools raise errors."""
    ctx = make_context("DEL", ["BOM"], duration_days=2)
    state = process_intake(ctx)

    with (
        patch("src.nodes.experience_node.search_places", side_effect=PlaceError("Places API down")),
        patch(
            "src.nodes.experience_node.get_weather_forecast",
            side_effect=WeatherError("Weather API down"),
        ),
    ):
        plan = process_experience(state, use_fixture=False)

    assert isinstance(plan, ExperiencePlan)
    assert plan.total_days == 2
    assert len(plan.days) == 2
    # Activities and meals synthesized via fallback heuristics
    for day in plan.days:
        assert len(day.activities) > 0
        assert len(day.meals) == 3


# ---------------------------------------------------------------------------
# LangGraph Node Interface Tests
# ---------------------------------------------------------------------------


def test_experience_node_langgraph_interface():
    """Verify experience_node returns a dictionary containing 'experience_plan'."""
    ctx = make_context("DEL", ["BOM"])
    state = process_intake(ctx)

    result = experience_node(state)
    assert isinstance(result, dict)
    assert "experience_plan" in result
    assert isinstance(result["experience_plan"], ExperiencePlan)


def test_experience_node_from_dict_state_with_logistics():
    """Verify experience_node handles state dictionary containing logistics_plan."""
    ctx = make_context("DEL", ["BOM"])
    state = process_intake(ctx)

    state_dict = {
        "trip_context": ctx,
        "origin": state.origin,
        "destinations": state.destinations,
        "effective_duration_days": state.effective_duration_days,
        "travel_scope": state.travel_scope,
        "logistics_plan": {
            "transport_legs": [],
            "hotel_stays": [
                {
                    "destination": "Mumbai",
                    "hotel_name": "Trident Nariman Point",
                    "star_rating": 5,
                    "checkin_date": "2026-10-15",
                    "checkout_date": "2026-10-20",
                    "nights": 5,
                    "rooms_required": 1,
                    "price_per_room_per_night_inr": 13800.0,
                    "total_accommodation_cost_inr": 69000.0,
                    "provider": "fixture",
                }
            ],
            "total_transport_cost_inr": 0.0,
            "total_accommodation_cost_inr": 69000.0,
            "timestamp": "2026-09-26T00:00:00Z",
        },
    }

    result = experience_node(state_dict)
    assert "experience_plan" in result
    plan = result["experience_plan"]
    assert plan.days[0].hotel_name == "Trident Nariman Point"


def test_experience_invalid_state_type():
    """Verify invalid state raises ExperiencePlanningError."""
    with pytest.raises(ExperiencePlanningError):
        process_experience(99999)  # type: ignore[arg-type]
