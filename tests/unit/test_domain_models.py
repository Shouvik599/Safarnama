"""Unit tests for Phase 5 — Domain Models.

Tests cover all five new domain model files:
  - src/models/trip.py
  - src/models/itinerary.py
  - src/models/logistics.py
  - src/models/visa.py  (VisaVerdict additions)
  - src/models/budget.py

Each model is tested for:
  - Valid construction with required fields
  - Default values
  - Field-level validation (type, range, length)
  - Cross-field validators (model_validator)
  - Enum membership and string values
  - Property helpers
  - Invalid states are rejected

No external network calls are made.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
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
    ActivityCategory,
    ActivitySlot,
    Daypart,
    DayPlan,
    ExperiencePlan,
    PointOfInterest,
)
from src.models.logistics import HotelStay, LogisticsPlan, TransportLeg
from src.models.trip import (
    BudgetMode,
    DateMode,
    FoodImportance,
    FoodPreferences,
    Pace,
    PreviousTravelEntry,
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

# =============================================================================
# Trip models — TripParty
# =============================================================================


class TestTripParty:
    def test_valid_adults_only(self) -> None:
        party = TripParty(adults=2)
        assert party.adults == 2
        assert party.children == 0
        assert party.total_travelers == 2

    def test_valid_adults_and_children(self) -> None:
        party = TripParty(adults=2, children=3)
        assert party.total_travelers == 5

    def test_zero_adults_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TripParty(adults=0)

    def test_negative_adults_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TripParty(adults=-1)

    def test_negative_children_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TripParty(adults=1, children=-1)

    def test_too_many_adults_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TripParty(adults=51)

    def test_too_many_children_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TripParty(adults=1, children=21)

    def test_single_traveler(self) -> None:
        party = TripParty(adults=1)
        assert party.total_travelers == 1


# =============================================================================
# Trip models — DateMode and TripDates
# =============================================================================


class TestDateMode:
    def test_all_values_defined(self) -> None:
        assert DateMode.EXACT == "EXACT"
        assert DateMode.FLEXIBLE == "FLEXIBLE"
        assert DateMode.FIND_BEST == "FIND_BEST"


class TestTripDates:
    def test_exact_dates_valid(self) -> None:
        dates = TripDates(
            mode=DateMode.EXACT,
            start_date="2026-12-01",
            end_date="2026-12-08",
        )
        assert dates.mode == DateMode.EXACT
        assert dates.start_date == "2026-12-01"
        assert dates.end_date == "2026-12-08"

    def test_exact_dates_missing_start_rejected(self) -> None:
        with pytest.raises(ValidationError, match="start_date"):
            TripDates(mode=DateMode.EXACT, end_date="2026-12-08")

    def test_exact_dates_missing_end_rejected(self) -> None:
        with pytest.raises(ValidationError, match="end_date"):
            TripDates(mode=DateMode.EXACT, start_date="2026-12-01")

    def test_flexible_valid(self) -> None:
        dates = TripDates(
            mode=DateMode.FLEXIBLE,
            start_date="2026-12-01",
            duration_days=7,
            flexibility_days=3,
        )
        assert dates.duration_days == 7
        assert dates.flexibility_days == 3

    def test_flexible_missing_start_rejected(self) -> None:
        with pytest.raises(ValidationError, match="start_date"):
            TripDates(mode=DateMode.FLEXIBLE, duration_days=7)

    def test_flexible_missing_duration_rejected(self) -> None:
        with pytest.raises(ValidationError, match="duration_days"):
            TripDates(mode=DateMode.FLEXIBLE, start_date="2026-12-01")

    def test_find_best_valid(self) -> None:
        dates = TripDates(
            mode=DateMode.FIND_BEST,
            window_start="2026-12-01",
            window_end="2026-12-31",
            duration_days=7,
        )
        assert dates.window_start == "2026-12-01"
        assert dates.window_end == "2026-12-31"

    def test_find_best_missing_window_start_rejected(self) -> None:
        with pytest.raises(ValidationError, match="window_start"):
            TripDates(
                mode=DateMode.FIND_BEST,
                window_end="2026-12-31",
                duration_days=7,
            )

    def test_find_best_missing_window_end_rejected(self) -> None:
        with pytest.raises(ValidationError, match="window_end"):
            TripDates(
                mode=DateMode.FIND_BEST,
                window_start="2026-12-01",
                duration_days=7,
            )

    def test_find_best_missing_duration_rejected(self) -> None:
        with pytest.raises(ValidationError, match="duration_days"):
            TripDates(
                mode=DateMode.FIND_BEST,
                window_start="2026-12-01",
                window_end="2026-12-31",
            )

    def test_duration_too_large_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TripDates(
                mode=DateMode.EXACT,
                start_date="2026-12-01",
                end_date="2027-12-01",
                duration_days=91,
            )

    def test_flexibility_days_default_zero(self) -> None:
        dates = TripDates(
            mode=DateMode.FLEXIBLE,
            start_date="2026-12-01",
            duration_days=5,
        )
        assert dates.flexibility_days == 0


# =============================================================================
# Trip models — TripBudget
# =============================================================================


class TestTripBudget:
    def test_total_budget(self) -> None:
        budget = TripBudget(mode=BudgetMode.TOTAL, amount_inr=100_000.0)
        party = TripParty(adults=2)
        assert budget.total_budget_inr(party) == 100_000.0

    def test_per_person_budget_multiplies_by_total_travelers(self) -> None:
        budget = TripBudget(mode=BudgetMode.PER_PERSON, amount_inr=50_000.0)
        party = TripParty(adults=2, children=1)
        assert budget.total_budget_inr(party) == 150_000.0

    def test_amount_too_low_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TripBudget(amount_inr=500.0)

    def test_default_mode_is_total(self) -> None:
        budget = TripBudget(amount_inr=80_000.0)
        assert budget.mode == BudgetMode.TOTAL


# =============================================================================
# Trip models — FoodPreferences
# =============================================================================


class TestFoodPreferences:
    def test_defaults(self) -> None:
        prefs = FoodPreferences()
        assert prefs.importance == FoodImportance.MEDIUM
        assert prefs.dietary_preference is None
        assert prefs.allergies == []
        assert prefs.foods_to_avoid == []
        assert prefs.desired_experiences == []

    def test_full_configuration(self) -> None:
        prefs = FoodPreferences(
            importance=FoodImportance.HIGH,
            dietary_preference="vegetarian",
            allergies=["nuts", "shellfish"],
            foods_to_avoid=["pork"],
            desired_experiences=["street food", "cooking class"],
        )
        assert prefs.importance == FoodImportance.HIGH
        assert "nuts" in prefs.allergies
        assert "pork" in prefs.foods_to_avoid


# =============================================================================
# Trip models — TripContext
# =============================================================================


def _make_valid_trip_context(
    scope: TravelScope = TravelScope.DOMESTIC,
    destinations: list[str] | None = None,
) -> TripContext:
    """Helper: build a minimal valid TripContext."""
    if destinations is None:
        destinations = ["Goa"] if scope == TravelScope.DOMESTIC else ["Japan"]
    return TripContext(
        origin="DEL",
        destinations=destinations,
        scope=scope,
        party=TripParty(adults=2),
        dates=TripDates(
            mode=DateMode.EXACT,
            start_date="2026-12-01",
            end_date="2026-12-08",
        ),
        budget=TripBudget(amount_inr=80_000.0),
    )


class TestTripContext:
    def test_domestic_trip_valid(self) -> None:
        ctx = _make_valid_trip_context(TravelScope.DOMESTIC)
        assert ctx.scope == TravelScope.DOMESTIC
        assert ctx.origin == "DEL"
        assert ctx.destinations == ["Goa"]

    def test_international_trip_valid(self) -> None:
        ctx = _make_valid_trip_context(TravelScope.INTERNATIONAL, ["Japan"])
        assert ctx.scope == TravelScope.INTERNATIONAL
        assert "Japan" in ctx.destinations

    def test_multi_destination(self) -> None:
        ctx = _make_valid_trip_context(TravelScope.INTERNATIONAL, ["France", "Spain", "Italy"])
        assert len(ctx.destinations) == 3

    def test_empty_destinations_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TripContext(
                origin="DEL",
                destinations=[],
                scope=TravelScope.DOMESTIC,
                party=TripParty(adults=2),
                dates=TripDates(
                    mode=DateMode.EXACT,
                    start_date="2026-12-01",
                    end_date="2026-12-08",
                ),
                budget=TripBudget(amount_inr=50_000.0),
            )

    def test_origin_too_short_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TripContext(
                origin="D",
                destinations=["Goa"],
                scope=TravelScope.DOMESTIC,
                party=TripParty(adults=1),
                dates=TripDates(
                    mode=DateMode.EXACT,
                    start_date="2026-12-01",
                    end_date="2026-12-05",
                ),
                budget=TripBudget(amount_inr=30_000.0),
            )

    def test_defaults_applied(self) -> None:
        ctx = _make_valid_trip_context()
        assert ctx.travel_style == TravelStyle.COMFORTABLE
        assert ctx.pace == Pace.BALANCED
        assert ctx.activity_preferences == []
        assert ctx.must_visits == []
        assert ctx.previous_travel == []

    def test_previous_travel_entry(self) -> None:
        ctx = _make_valid_trip_context(TravelScope.INTERNATIONAL, ["France"])
        entry = PreviousTravelEntry(
            country_code="TH",
            country_name="Thailand",
            travel_year=2023,
            visa_type="Tourist",
        )
        ctx2 = ctx.model_copy(update={"previous_travel": [entry]})
        assert len(ctx2.previous_travel) == 1
        assert ctx2.previous_travel[0].country_code == "TH"

    def test_must_visits_list(self) -> None:
        ctx = _make_valid_trip_context()
        ctx2 = ctx.model_copy(update={"must_visits": ["Taj Mahal", "Qutub Minar"]})
        assert len(ctx2.must_visits) == 2

    def test_travel_style_enum_values(self) -> None:
        for style in TravelStyle:
            ctx = _make_valid_trip_context()
            ctx2 = ctx.model_copy(update={"travel_style": style})
            assert ctx2.travel_style == style

    def test_pace_enum_values(self) -> None:
        for pace in Pace:
            ctx = _make_valid_trip_context()
            ctx2 = ctx.model_copy(update={"pace": pace})
            assert ctx2.pace == pace


# =============================================================================
# Itinerary models — PointOfInterest
# =============================================================================


class TestPointOfInterest:
    def test_minimal_valid(self) -> None:
        poi = PointOfInterest(
            name="Taj Mahal",
            city="Agra",
        )
        assert poi.name == "Taj Mahal"
        assert poi.city == "Agra"
        assert poi.is_must_visit is False
        assert poi.estimated_cost_inr == 0.0
        assert poi.category == ActivityCategory.OTHER

    def test_with_category_and_cost(self) -> None:
        poi = PointOfInterest(
            name="Louvre Museum",
            city="Paris",
            country="France",
            category=ActivityCategory.MUSEUM,
            estimated_cost_inr=2000.0,
            is_must_visit=True,
        )
        assert poi.category == ActivityCategory.MUSEUM
        assert poi.is_must_visit is True
        assert poi.estimated_cost_inr == 2000.0

    def test_negative_cost_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PointOfInterest(name="Test", city="Paris", estimated_cost_inr=-100.0)

    def test_duration_below_minimum_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PointOfInterest(name="Test", city="Paris", estimated_duration_minutes=4)


# =============================================================================
# Itinerary models — ActivitySlot
# =============================================================================


class TestActivitySlot:
    def _make_poi(self) -> PointOfInterest:
        return PointOfInterest(name="Red Fort", city="Delhi")

    def test_valid_slot(self) -> None:
        slot = ActivitySlot(daypart=Daypart.MORNING, poi=self._make_poi())
        assert slot.daypart == Daypart.MORNING
        assert slot.is_weather_substituted is False

    def test_weather_substituted_slot(self) -> None:
        slot = ActivitySlot(
            daypart=Daypart.AFTERNOON,
            poi=self._make_poi(),
            is_weather_substituted=True,
            substituted_for="Outdoor trek",
            weather_note="80% rain probability — replaced outdoor hike",
        )
        assert slot.is_weather_substituted is True
        assert slot.substituted_for == "Outdoor trek"


# =============================================================================
# Itinerary models — DayPlan
# =============================================================================


class TestDayPlan:
    def test_minimal_valid_day_plan(self) -> None:
        day = DayPlan(day_number=1, city="Delhi")
        assert day.day_number == 1
        assert day.city == "Delhi"
        assert day.activities == []
        assert day.meals == []

    def test_total_day_cost_property(self) -> None:
        day = DayPlan(
            day_number=2,
            city="Jaipur",
            activity_cost_inr=1500.0,
            food_cost_inr=800.0,
            local_transport_cost_inr=300.0,
        )
        assert day.total_day_cost_inr == pytest.approx(2600.0)

    def test_day_number_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DayPlan(day_number=0, city="Delhi")

    def test_negative_costs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DayPlan(day_number=1, city="Delhi", activity_cost_inr=-100.0)


# =============================================================================
# Itinerary models — ExperiencePlan
# =============================================================================


class TestExperiencePlan:
    def test_minimal_valid(self) -> None:
        plan = ExperiencePlan(total_days=3, timestamp="2026-09-26T00:00:00Z")
        assert plan.total_days == 3
        assert plan.days == []
        assert plan.weather_substitutions == 0
        assert plan.is_estimated is False

    def test_with_days(self) -> None:
        day1 = DayPlan(day_number=1, city="Delhi")
        day2 = DayPlan(day_number=2, city="Agra")
        plan = ExperiencePlan(
            total_days=2,
            days=[day1, day2],
            destinations_covered=["Delhi", "Agra"],
            timestamp="2026-09-26T00:00:00Z",
        )
        assert len(plan.days) == 2
        assert "Delhi" in plan.destinations_covered


# =============================================================================
# Logistics models — TransportLeg
# =============================================================================


class TestTransportLeg:
    def test_valid_flight_leg(self) -> None:
        leg = TransportLeg(
            leg_number=1,
            mode="FLIGHT",
            carrier="IndiGo",
            origin="DEL",
            destination="GOI",
            price_per_person_inr=5000.0,
            total_price_inr=10000.0,
            provider="fixture",
        )
        assert leg.leg_number == 1
        assert leg.mode == "FLIGHT"
        assert leg.total_price_inr == 10000.0
        assert leg.is_estimated is False

    def test_leg_number_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransportLeg(
                leg_number=0,
                mode="FLIGHT",
                carrier="IndiGo",
                origin="DEL",
                destination="GOI",
                price_per_person_inr=5000.0,
                total_price_inr=10000.0,
                provider="fixture",
            )

    def test_negative_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransportLeg(
                leg_number=1,
                mode="FLIGHT",
                carrier="IndiGo",
                origin="DEL",
                destination="GOI",
                price_per_person_inr=-100.0,
                total_price_inr=-200.0,
                provider="fixture",
            )

    def test_estimated_leg(self) -> None:
        leg = TransportLeg(
            leg_number=1,
            mode="BUS",
            carrier="State Bus",
            origin="Jaipur",
            destination="Jodhpur",
            price_per_person_inr=300.0,
            total_price_inr=600.0,
            provider="physics-heuristic",
            is_estimated=True,
        )
        assert leg.is_estimated is True


# =============================================================================
# Logistics models — HotelStay
# =============================================================================


class TestHotelStay:
    def test_valid_hotel_stay(self) -> None:
        stay = HotelStay(
            destination="Goa",
            hotel_name="Sunset Beach Resort",
            checkin_date="2026-12-01",
            checkout_date="2026-12-05",
            nights=4,
            rooms_required=1,
            price_per_room_per_night_inr=3500.0,
            total_accommodation_cost_inr=14000.0,
            provider="serpapi-google-hotels",
        )
        assert stay.nights == 4
        assert stay.total_accommodation_cost_inr == 14000.0
        assert stay.is_estimated is False

    def test_zero_nights_rejected(self) -> None:
        with pytest.raises(ValidationError):
            HotelStay(
                destination="Goa",
                hotel_name="Test Hotel",
                checkin_date="2026-12-01",
                checkout_date="2026-12-01",
                nights=0,
                rooms_required=1,
                price_per_room_per_night_inr=3000.0,
                total_accommodation_cost_inr=0.0,
                provider="fixture",
            )

    def test_star_rating_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            HotelStay(
                destination="Goa",
                hotel_name="Test Hotel",
                checkin_date="2026-12-01",
                checkout_date="2026-12-03",
                nights=2,
                rooms_required=1,
                price_per_room_per_night_inr=3000.0,
                total_accommodation_cost_inr=6000.0,
                provider="fixture",
                star_rating=6,
            )


# =============================================================================
# Logistics models — LogisticsPlan
# =============================================================================


class TestLogisticsPlan:
    def test_empty_plan_valid(self) -> None:
        plan = LogisticsPlan(timestamp="2026-09-26T00:00:00Z")
        assert plan.transport_legs == []
        assert plan.hotel_stays == []
        assert plan.total_transport_cost_inr == 0.0
        assert plan.total_accommodation_cost_inr == 0.0

    def test_plan_with_legs_and_stays(self) -> None:
        leg = TransportLeg(
            leg_number=1,
            mode="FLIGHT",
            carrier="IndiGo",
            origin="DEL",
            destination="GOI",
            price_per_person_inr=5000.0,
            total_price_inr=10000.0,
            provider="fixture",
        )
        stay = HotelStay(
            destination="Goa",
            hotel_name="Beach Hotel",
            checkin_date="2026-12-01",
            checkout_date="2026-12-05",
            nights=4,
            rooms_required=1,
            price_per_room_per_night_inr=3000.0,
            total_accommodation_cost_inr=12000.0,
            provider="fixture",
        )
        plan = LogisticsPlan(
            transport_legs=[leg],
            hotel_stays=[stay],
            total_transport_cost_inr=10000.0,
            total_accommodation_cost_inr=12000.0,
            timestamp="2026-09-26T00:00:00Z",
        )
        assert len(plan.transport_legs) == 1
        assert len(plan.hotel_stays) == 1
        assert plan.total_transport_cost_inr == 10000.0


# =============================================================================
# Visa models — VisaRequirementStatus
# =============================================================================


class TestVisaRequirementStatus:
    def test_all_statuses_defined(self) -> None:
        expected = {
            "VISA_FREE",
            "VISA_ON_ARRIVAL",
            "E_VISA",
            "STICKER_VISA_REQUIRED",
            "CONDITIONAL_FREE",
            "RESTRICTED",
            "UNKNOWN",
            "DOMESTIC_BYPASS",
        }
        actual = {s.value for s in VisaRequirementStatus}
        assert expected == actual


# =============================================================================
# Visa models — VisaCountryVerdict
# =============================================================================


class TestVisaCountryVerdict:
    def test_visa_free_verdict(self) -> None:
        verdict = VisaCountryVerdict(
            country_name="Thailand",
            country_code="TH",
            status=VisaRequirementStatus.VISA_FREE,
            permitted_stay_days=30,
            visa_fee_inr=0.0,
        )
        assert verdict.status == VisaRequirementStatus.VISA_FREE
        assert verdict.visa_fee_inr == 0.0
        assert verdict.is_live_verified is False

    def test_evisa_verdict_with_documents(self) -> None:
        verdict = VisaCountryVerdict(
            country_name="Uzbekistan",
            country_code="UZ",
            status=VisaRequirementStatus.E_VISA,
            visa_type_label="Tourist e-Visa",
            permitted_stay_days=30,
            visa_fee_inr=2000.0,
            required_documents=["Passport", "Hotel booking", "Return ticket"],
            application_process="Apply at e-visa.gov.uz 7 days before travel",
            processing_time_days="3–5 business days",
            data_source="LIVE_VERIFIED",
            is_live_verified=True,
        )
        assert verdict.visa_fee_inr == 2000.0
        assert verdict.is_live_verified is True
        assert len(verdict.required_documents) == 3

    def test_negative_visa_fee_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VisaCountryVerdict(
                country_name="Test",
                country_code="TT",
                status=VisaRequirementStatus.E_VISA,
                visa_fee_inr=-100.0,
            )

    def test_permitted_stay_days_below_minimum_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VisaCountryVerdict(
                country_name="Test",
                country_code="TT",
                status=VisaRequirementStatus.VISA_FREE,
                permitted_stay_days=0,
            )

    def test_default_confidence_medium(self) -> None:
        verdict = VisaCountryVerdict(
            country_name="France",
            country_code="FR",
            status=VisaRequirementStatus.STICKER_VISA_REQUIRED,
        )
        assert verdict.confidence == "MEDIUM"


# =============================================================================
# Visa models — VisaVerdict
# =============================================================================


class TestVisaVerdict:
    def test_domestic_bypass(self) -> None:
        verdict = VisaVerdict(
            is_domestic_bypass=True,
            timestamp="2026-09-26T00:00:00Z",
        )
        assert verdict.is_domestic_bypass is True
        assert verdict.countries == []
        assert verdict.total_visa_cost_inr == 0.0

    def test_international_verdict(self) -> None:
        country_verdict = VisaCountryVerdict(
            country_name="Japan",
            country_code="JP",
            status=VisaRequirementStatus.STICKER_VISA_REQUIRED,
            visa_fee_inr=6500.0,
        )
        verdict = VisaVerdict(
            is_domestic_bypass=False,
            countries=[country_verdict],
            total_visa_cost_inr=6500.0,
            requires_advance_application=True,
            timestamp="2026-09-26T00:00:00Z",
        )
        assert len(verdict.countries) == 1
        assert verdict.requires_advance_application is True

    def test_multi_country_schengen(self) -> None:
        france = VisaCountryVerdict(
            country_name="France",
            country_code="FR",
            status=VisaRequirementStatus.STICKER_VISA_REQUIRED,
        )
        spain = VisaCountryVerdict(
            country_name="Spain",
            country_code="ES",
            status=VisaRequirementStatus.STICKER_VISA_REQUIRED,
        )
        verdict = VisaVerdict(
            countries=[france, spain],
            schengen_single_visa_applicable=True,
            timestamp="2026-09-26T00:00:00Z",
        )
        assert verdict.schengen_single_visa_applicable is True
        assert len(verdict.countries) == 2


# =============================================================================
# Budget models — BudgetStatus
# =============================================================================


class TestBudgetStatus:
    def test_all_statuses_defined(self) -> None:
        expected = {"UNDER_BUDGET", "EXACT", "MINOR_OVER", "SIGNIFICANT_OVER", "INFEASIBLE"}
        actual = {s.value for s in BudgetStatus}
        assert expected == actual


# =============================================================================
# Budget models — CostBreakdown
# =============================================================================


class TestCostBreakdown:
    def test_all_zero_defaults(self) -> None:
        breakdown = CostBreakdown()
        assert breakdown.subtotal_inr == 0.0
        assert breakdown.has_estimated_components is False

    def test_subtotal_property(self) -> None:
        breakdown = CostBreakdown(
            transport_inr=15000.0,
            accommodation_inr=12000.0,
            local_transport_inr=1500.0,
            activities_inr=3000.0,
            food_inr=4000.0,
            visa_inr=0.0,
            misc_inr=2000.0,
        )
        assert breakdown.subtotal_inr == pytest.approx(37500.0)

    def test_negative_transport_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CostBreakdown(transport_inr=-1000.0)

    def test_has_estimated_flag(self) -> None:
        breakdown = CostBreakdown(
            transport_inr=5000.0,
            accommodation_inr=3000.0,
            has_estimated_components=True,
        )
        assert breakdown.has_estimated_components is True


# =============================================================================
# Budget models — ContingencyConfig
# =============================================================================


class TestContingencyConfig:
    def test_valid_contingency(self) -> None:
        cfg = ContingencyConfig(
            percentage=12.0,
            amount_inr=4500.0,
            is_international=True,
            country_count=2,
        )
        assert cfg.percentage == 12.0
        assert cfg.amount_inr == 4500.0

    def test_percentage_above_50_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ContingencyConfig(percentage=51.0, amount_inr=1000.0)

    def test_percentage_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ContingencyConfig(percentage=-1.0, amount_inr=0.0)

    def test_negative_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ContingencyConfig(percentage=10.0, amount_inr=-500.0)


# =============================================================================
# Budget models — BudgetVariance
# =============================================================================


class TestBudgetVariance:
    def test_under_budget_variance(self) -> None:
        variance = BudgetVariance(
            user_budget_inr=100_000.0,
            projected_total_inr=85_000.0,
            variance_inr=-15_000.0,
            variance_percentage=-15.0,
            status=BudgetStatus.UNDER_BUDGET,
        )
        assert variance.status == BudgetStatus.UNDER_BUDGET
        assert variance.variance_inr == pytest.approx(-15_000.0)

    def test_over_budget_variance(self) -> None:
        variance = BudgetVariance(
            user_budget_inr=100_000.0,
            projected_total_inr=110_000.0,
            variance_inr=10_000.0,
            variance_percentage=10.0,
            status=BudgetStatus.SIGNIFICANT_OVER,
        )
        assert variance.status == BudgetStatus.SIGNIFICANT_OVER

    def test_inconsistent_variance_rejected(self) -> None:
        """variance_inr must equal projected_total_inr - user_budget_inr (within ₹1)."""
        with pytest.raises(ValidationError, match="inconsistent"):
            BudgetVariance(
                user_budget_inr=100_000.0,
                projected_total_inr=110_000.0,
                variance_inr=5_000.0,  # Wrong! Should be 10_000
                variance_percentage=10.0,
                status=BudgetStatus.SIGNIFICANT_OVER,
            )

    def test_exact_budget(self) -> None:
        variance = BudgetVariance(
            user_budget_inr=100_000.0,
            projected_total_inr=100_000.0,
            variance_inr=0.0,
            variance_percentage=0.0,
            status=BudgetStatus.EXACT,
        )
        assert variance.status == BudgetStatus.EXACT


# =============================================================================
# Budget models — OptimizationResult
# =============================================================================


class TestOptimizationResult:
    def test_no_action_default(self) -> None:
        result = OptimizationResult()
        assert result.action == OptimizationAction.NONE
        assert result.savings_inr == 0.0
        assert result.guardrails_respected is True

    def test_hotel_optimization(self) -> None:
        result = OptimizationResult(
            action=OptimizationAction.CHEAPER_HOTEL,
            savings_inr=4200.0,
            description="Switched to 3-star hotel",
            trade_offs=["Hotel is 3km from city centre"],
        )
        assert result.savings_inr == pytest.approx(4200.0)
        assert len(result.trade_offs) == 1


# =============================================================================
# Budget models — BudgetBreakdown
# =============================================================================


class TestBudgetBreakdown:
    def _make_valid_breakdown(self) -> BudgetBreakdown:
        return BudgetBreakdown(
            cost_breakdown=CostBreakdown(
                transport_inr=15000.0,
                accommodation_inr=12000.0,
                food_inr=4000.0,
                activities_inr=3000.0,
                misc_inr=2000.0,
            ),
            contingency=ContingencyConfig(
                percentage=10.0,
                amount_inr=3600.0,
            ),
            variance=BudgetVariance(
                user_budget_inr=40_000.0,
                projected_total_inr=39_600.0,
                variance_inr=-400.0,
                variance_percentage=-1.0,
                status=BudgetStatus.UNDER_BUDGET,
            ),
            subtotal_inr=36_000.0,
            total_with_contingency_inr=39_600.0,
            per_person_cost_inr=19_800.0,
            timestamp="2026-09-26T00:00:00Z",
        )

    def test_valid_breakdown(self) -> None:
        breakdown = self._make_valid_breakdown()
        assert breakdown.subtotal_inr == 36_000.0
        assert breakdown.total_with_contingency_inr == 39_600.0
        assert breakdown.variance.status == BudgetStatus.UNDER_BUDGET
        assert breakdown.is_estimated is False

    def test_negative_subtotal_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BudgetBreakdown(
                cost_breakdown=CostBreakdown(),
                contingency=ContingencyConfig(percentage=10.0, amount_inr=0.0),
                variance=BudgetVariance(
                    user_budget_inr=10_000.0,
                    projected_total_inr=0.0,
                    variance_inr=-10_000.0,
                    variance_percentage=-100.0,
                    status=BudgetStatus.UNDER_BUDGET,
                ),
                subtotal_inr=-1.0,
                total_with_contingency_inr=0.0,
                per_person_cost_inr=0.0,
                timestamp="2026-09-26T00:00:00Z",
            )

    def test_warnings_list(self) -> None:
        breakdown = self._make_valid_breakdown()
        updated = breakdown.model_copy(
            update={"warnings": ["Hotel pricing estimated", "Visa fee is approximate"]}
        )
        assert len(updated.warnings) == 2


# =============================================================================
# Integration: enums are StrEnum (serializable)
# =============================================================================


class TestEnumSerialization:
    """Verify that all Phase 5 enums serialize correctly as plain strings."""

    def test_travel_scope_serialization(self) -> None:
        ctx = _make_valid_trip_context()
        data = ctx.model_dump()
        assert data["scope"] == "DOMESTIC"

    def test_budget_status_serialization(self) -> None:
        variance = BudgetVariance(
            user_budget_inr=100_000.0,
            projected_total_inr=85_000.0,
            variance_inr=-15_000.0,
            variance_percentage=-15.0,
            status=BudgetStatus.UNDER_BUDGET,
        )
        data = variance.model_dump()
        assert data["status"] == "UNDER_BUDGET"

    def test_visa_status_serialization(self) -> None:
        verdict = VisaCountryVerdict(
            country_name="Thailand",
            country_code="TH",
            status=VisaRequirementStatus.VISA_FREE,
        )
        data = verdict.model_dump()
        assert data["status"] == "VISA_FREE"

    def test_daypart_serialization(self) -> None:
        slot = ActivitySlot(
            daypart=Daypart.MORNING,
            poi=PointOfInterest(name="Taj Mahal", city="Agra"),
        )
        data = slot.model_dump()
        assert data["daypart"] == "MORNING"
