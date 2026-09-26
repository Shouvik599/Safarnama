"""Unit tests for Phase 6 — Intake Functionality (src/nodes/intake_node.py).

Tests:
1. Domestic single destination (DEL -> BOM).
2. Domestic multiple destinations (BLR -> Delhi -> Goa -> Jaipur).
3. International single country (BOM -> DXB / United Arab Emirates).
4. International multiple countries (DEL -> France -> Netherlands with Schengen detection).
5. Invalid origin (non-existent code, or origin outside India).
6. Invalid destination (unresolvable place).
7. Invalid traveler count (0 adults rejected by Pydantic).
8. Invalid budget (0 or negative budget rejected by Pydantic).
9. Scope conflict detection (DOMESTIC with international destination & vice versa).
10. DateMode handling (EXACT, FLEXIBLE, FIND_BEST).
11. BudgetMode handling (TOTAL vs PER_PERSON).
12. LangGraph node invocation formats (TripContext, dict with trip_context, raw dict).
13. Custom exceptions and error recovery.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.models.trip import (
    BudgetMode,
    DateMode,
    InitialPlanningState,
    Pace,
    TravelScope,
    TravelStyle,
    TripBudget,
    TripContext,
    TripDates,
    TripParty,
)
from src.nodes.intake_node import (
    IntakeScopeConflictError,
    IntakeValidationError,
    intake_node,
    process_intake,
    resolve_location,
)

# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------


def make_context(
    *,
    origin: str = "DEL",
    destinations: list[str] | None = None,
    scope: TravelScope = TravelScope.DOMESTIC,
    start_date: str = "2026-11-10",
    end_date: str = "2026-11-15",
    mode: DateMode = DateMode.EXACT,
    duration_days: int | None = None,
    adults: int = 2,
    children: int = 0,
    budget_amount: float = 100000.0,
    budget_mode: BudgetMode = BudgetMode.TOTAL,
) -> TripContext:
    """Helper to construct a valid TripContext for testing."""
    if destinations is None:
        destinations = ["BOM"]

    dates = TripDates(
        mode=mode,
        start_date=start_date,
        end_date=end_date if mode == DateMode.EXACT else None,
        duration_days=duration_days,
        window_start=start_date if mode == DateMode.FIND_BEST else None,
        window_end=end_date if mode == DateMode.FIND_BEST else None,
    )
    party = TripParty(adults=adults, children=children)
    budget = TripBudget(mode=budget_mode, amount_inr=budget_amount)

    return TripContext(
        origin=origin,
        destinations=destinations,
        scope=scope,
        party=party,
        dates=dates,
        budget=budget,
        travel_style=TravelStyle.COMFORTABLE,
        pace=Pace.BALANCED,
    )


# ---------------------------------------------------------------------------
# 1. Domestic Trips
# ---------------------------------------------------------------------------


def test_domestic_single_destination_del_to_bom() -> None:
    """Domestic single destination resolves correctly with coordinates and gateways."""
    context = make_context(origin="DEL", destinations=["BOM"], scope=TravelScope.DOMESTIC)
    state = process_intake(context)

    assert isinstance(state, InitialPlanningState)
    assert state.travel_scope == TravelScope.DOMESTIC
    assert state.origin.iata_code == "DEL"
    assert state.origin.country_code == "IN"
    assert state.origin.latitude > 20.0
    assert state.origin.longitude > 70.0

    assert len(state.destinations) == 1
    dest = state.destinations[0]
    assert dest.iata_code == "BOM"
    assert dest.country_code == "IN"
    assert dest.is_schengen is False
    assert dest.ist_offset_hours == 0.0

    assert state.effective_duration_days == 6  # 2026-11-10 to 2026-11-15 inclusive
    assert state.total_budget_inr == 100000.0
    assert state.daily_budget_per_person_inr == round(100000.0 / (2 * 6), 2)
    assert state.route == ["DEL", "BOM", "DEL"]


def test_domestic_multiple_states_and_cities() -> None:
    """Domestic multiple destinations using city and state alias names."""
    context = make_context(
        origin="BLR",
        destinations=["Delhi", "Goa", "Jaipur"],
        scope=TravelScope.DOMESTIC,
        start_date="2026-12-01",
        end_date="2026-12-10",
    )
    state = process_intake(context)

    assert state.travel_scope == TravelScope.DOMESTIC
    assert state.origin.iata_code == "BLR"
    assert len(state.destinations) == 3

    assert state.destinations[0].iata_code == "DEL"
    assert state.destinations[1].iata_code in ("GOI", "GOX")
    assert state.destinations[2].iata_code == "JAI"

    for dest in state.destinations:
        assert dest.country_code == "IN"
        assert dest.is_schengen is False

    assert state.route == ["BLR", "DEL", state.destinations[1].iata_code, "JAI", "BLR"]
    assert state.effective_duration_days == 10


# ---------------------------------------------------------------------------
# 2. International Trips
# ---------------------------------------------------------------------------


def test_international_single_country_bom_to_dxb() -> None:
    """International trip to Dubai resolves country code, gateway, and IST offset."""
    context = make_context(
        origin="BOM",
        destinations=["Dubai"],
        scope=TravelScope.INTERNATIONAL,
        budget_amount=250000.0,
    )
    state = process_intake(context)

    assert state.travel_scope == TravelScope.INTERNATIONAL
    assert state.origin.iata_code == "BOM"
    assert len(state.destinations) == 1

    dest = state.destinations[0]
    assert dest.country_code == "AE"
    assert dest.iata_code == "DXB"
    assert dest.is_schengen is False
    assert dest.ist_offset_hours < 0.0  # UAE is UTC+4, IST is UTC+5.5 -> negative offset


def test_international_multiple_countries_with_schengen() -> None:
    """International trip across Schengen countries attaches Schengen advisory."""
    context = make_context(
        origin="DEL",
        destinations=["France", "Netherlands"],
        scope=TravelScope.INTERNATIONAL,
        start_date="2026-09-01",
        end_date="2026-09-12",
        budget_amount=400000.0,
    )
    state = process_intake(context)

    assert state.travel_scope == TravelScope.INTERNATIONAL
    assert len(state.destinations) == 2
    assert state.destinations[0].country_code == "FR"
    assert state.destinations[0].is_schengen is True
    assert state.destinations[1].country_code == "NL"
    assert state.destinations[1].is_schengen is True

    # Schengen single visa notice must be emitted in warnings
    assert any("Schengen" in w for w in state.warnings)


# ---------------------------------------------------------------------------
# 3. Invalid Inputs & Scope Conflict Handling
# ---------------------------------------------------------------------------


def test_invalid_origin_non_existent_code() -> None:
    """Non-existent origin airport code raises IntakeValidationError."""
    context = make_context(origin="XYZ99", destinations=["BOM"])
    with pytest.raises(IntakeValidationError, match="Could not resolve departure origin"):
        process_intake(context)


def test_invalid_origin_outside_india() -> None:
    """Departure origin located outside India is rejected."""
    context = make_context(origin="LHR", destinations=["BOM"], scope=TravelScope.INTERNATIONAL)
    with pytest.raises(IntakeValidationError, match="must originate within India"):
        process_intake(context)


def test_invalid_destination_unresolvable() -> None:
    """Unresolvable destination query raises IntakeValidationError."""
    context = make_context(origin="DEL", destinations=["FakeCityDoesNotExist999"])
    with pytest.raises(IntakeValidationError, match="Could not resolve destination"):
        process_intake(context)


def test_invalid_party_zero_adults_rejected() -> None:
    """Pydantic rejects traveler party with 0 adults."""
    with pytest.raises(ValidationError):
        TripParty(adults=0, children=2)


def test_invalid_budget_negative_or_zero_rejected() -> None:
    """Pydantic rejects zero or negative budget."""
    with pytest.raises(ValidationError):
        TripBudget(mode=BudgetMode.TOTAL, amount_inr=0.0)

    with pytest.raises(ValidationError):
        TripBudget(mode=BudgetMode.TOTAL, amount_inr=-5000.0)


def test_scope_conflict_domestic_with_international_destination() -> None:
    """User specifying DOMESTIC for an international destination raises IntakeScopeConflictError."""
    context = make_context(
        origin="DEL",
        destinations=["Paris"],
        scope=TravelScope.DOMESTIC,
    )
    with pytest.raises(IntakeScopeConflictError, match="marked DOMESTIC, but destination"):
        process_intake(context)


def test_scope_conflict_international_with_all_domestic_destinations() -> None:
    """User specifying INTERNATIONAL for domestic destinations raises IntakeScopeConflictError."""
    context = make_context(
        origin="DEL",
        destinations=["BOM", "Goa"],
        scope=TravelScope.INTERNATIONAL,
    )
    with pytest.raises(
        IntakeScopeConflictError, match="marked INTERNATIONAL, but all resolved destinations"
    ):
        process_intake(context)


# ---------------------------------------------------------------------------
# 4. Date Modes & Budget Modes
# ---------------------------------------------------------------------------


def test_flexible_date_mode_generates_warning() -> None:
    """Flexible date mode preserves target duration and issues advisory warning."""
    context = make_context(
        origin="DEL",
        destinations=["BOM"],
        mode=DateMode.FLEXIBLE,
        start_date="2026-11-15",
        duration_days=7,
    )
    state = process_intake(context)

    assert state.effective_duration_days == 7
    assert any("flexible" in w.lower() for w in state.warnings)


def test_find_best_date_mode_generates_warning() -> None:
    """Find-best date mode preserves search window and issues advisory warning."""
    context = make_context(
        origin="DEL",
        destinations=["BOM"],
        mode=DateMode.FIND_BEST,
        start_date="2026-10-01",
        end_date="2026-10-31",
        duration_days=5,
    )
    state = process_intake(context)

    assert state.effective_duration_days == 5
    assert any("search window" in w.lower() for w in state.warnings)


def test_budget_mode_per_person_multiplies_by_party() -> None:
    """Per-person budget correctly calculates total party budget."""
    context = make_context(
        origin="DEL",
        destinations=["BOM"],
        adults=3,
        children=1,
        budget_mode=BudgetMode.PER_PERSON,
        budget_amount=20000.0,
        start_date="2026-11-10",
        end_date="2026-11-14",  # 5 days
    )
    state = process_intake(context)

    # 4 travelers * 20,000 = 80,000 INR total
    assert state.total_budget_inr == 80000.0
    # 80,000 / (4 travelers * 5 days) = 4,000 per person per day
    assert state.daily_budget_per_person_inr == 4000.0


# ---------------------------------------------------------------------------
# 5. LangGraph Node Interface
# ---------------------------------------------------------------------------


def test_intake_node_accepts_trip_context_object() -> None:
    """intake_node accepts a TripContext instance directly."""
    context = make_context(origin="DEL", destinations=["BOM"])
    result = intake_node(context)

    assert isinstance(result, dict)
    assert result["travel_scope"] == TravelScope.DOMESTIC
    assert result["origin"]["iata_code"] == "DEL"
    assert result["destinations"][0]["iata_code"] == "BOM"
    assert result["visa_verdict"] is None
    assert result["logistics_plan"] is None
    assert result["budget_breakdown"] is None


def test_intake_node_accepts_dict_with_trip_context_key() -> None:
    """intake_node accepts {'trip_context': TripContext} dictionary."""
    context = make_context(origin="DEL", destinations=["BOM"])
    result = intake_node({"trip_context": context})

    assert isinstance(result, dict)
    assert result["travel_scope"] == TravelScope.DOMESTIC
    assert result["origin"]["iata_code"] == "DEL"


def test_intake_node_accepts_raw_dict() -> None:
    """intake_node accepts a raw dictionary representation of trip parameters."""
    raw_dict = {
        "origin": "DEL",
        "destinations": ["BOM"],
        "scope": "DOMESTIC",
        "party": {"adults": 2, "children": 0},
        "dates": {
            "mode": "EXACT",
            "start_date": "2026-11-10",
            "end_date": "2026-11-15",
        },
        "budget": {"mode": "TOTAL", "amount_inr": 75000.0},
    }
    result = intake_node(raw_dict)

    assert isinstance(result, dict)
    assert result["travel_scope"] == TravelScope.DOMESTIC
    assert result["total_budget_inr"] == 75000.0


def test_intake_node_rejects_invalid_type() -> None:
    """intake_node raises IntakeValidationError for invalid input types."""
    with pytest.raises(IntakeValidationError, match="Invalid input type"):
        intake_node(12345)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 6. Entity Resolver Helpers
# ---------------------------------------------------------------------------


def test_resolve_location_empty_string_raises() -> None:
    """resolve_location raises IntakeValidationError on empty query."""
    with pytest.raises(IntakeValidationError, match="cannot be empty"):
        resolve_location("   ")


def test_resolve_location_handles_country_name() -> None:
    """resolve_location resolves sovereign country by English name."""
    res = resolve_location("Japan", is_origin=False)
    assert res.country_code == "JP"
    assert res.country_name == "Japan"
    assert res.is_schengen is False
    assert res.latitude > 0.0


def test_resolve_location_handles_city_without_iata_fallback() -> None:
    """resolve_location resolves domestic city names via alias or static database."""
    res = resolve_location("Kochi", is_origin=False)
    assert res.country_code == "IN"
    assert res.iata_code == "COK"
    assert res.latitude > 0.0
