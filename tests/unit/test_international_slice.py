"""Phase 14 — International Vertical Slice Tests.

Validates the complete international vertical slice of Safarnama for Indian passport holders:
1. India -> Single International Destination (e.g. Delhi -> Bangkok, Thailand):
   - Scope resolved to INTERNATIONAL.
   - Routes through Visa planning node (never bypassed for international).
   - Validates VisaCountryVerdict and entry conditions for Indian citizens.
   - Validates international transport legs (round-trip flights) and accommodations.
   - Validates destination experiences and authentic dining.
   - Validates deterministic budget calculation incorporating visa costs.
   - Validates FinalItinerary title and executive narrative incorporating visa advisory.
2. India -> Country A -> Country B (Multi-Country Schengen: Delhi -> Paris, France -> Rome, Italy):
   - Multi-country destination resolution and sequential stay allocation.
   - Multi-country visa evaluation.
   - Schengen single uniform visa optimization (schengen_single_visa_applicable=True).
   - Multi-hop transport planning (Origin -> Dest 1 -> Dest 2 -> Origin).
   - Sequential hotel stays and day plans across multiple sovereign countries.
3. India -> Multi-Country Non-Schengen (Delhi -> Bangkok, Thailand -> Singapore):
   - Validates independent visa fee calculation when Schengen does not apply.
4. FastAPI REST API Layer (POST /api/v1/plan):
   - Accepts international requests (with explicit or auto-detected scope).
   - Returns 200 OK with PlanResponse schema and populated VisaVerdict.
   - Handles foreign origin rejection and scope conflicts gracefully.
5. Selective Re-planning:
   - Validates replan_workflow preserves unaffected international visa and logistics artifacts.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from src.api.app import app
from src.graph.workflow import replan_workflow, run_planning_graph
from src.models.itinerary import FinalItinerary
from src.models.trip import TravelScope


class TestInternationalSliceWorkflow:
    """End-to-end integration tests for the LangGraph StateGraph with international scenarios."""

    def test_single_country_international_slice_graph(self) -> None:
        """Verify India -> International Destination end-to-end planning (Delhi -> Bangkok)."""
        request_payload: dict[str, Any] = {
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

        final_state = run_planning_graph(request_payload)

        # 1. Pipeline execution status
        assert final_state["plan_status"] in ("COMPLETED", "NEEDS_USER_DECISION")
        assert not final_state.get("errors")

        # 2. Output deliverable
        itinerary = final_state.get("final_itinerary")
        assert itinerary is not None
        assert isinstance(itinerary, FinalItinerary)

        # 3. Context & Scope
        assert itinerary.trip_context.scope == TravelScope.INTERNATIONAL
        assert itinerary.trip_context.origin.lower() in ("delhi", "del")

        # 4. Visa Verdict Verification for Indian Passport Holder
        visa = itinerary.visa_verdict
        assert visa is not None
        assert visa.is_domestic_bypass is False
        assert len(visa.countries) == 1
        th_verdict = visa.countries[0]
        assert th_verdict.country_name == "Thailand"
        assert th_verdict.country_code == "TH"
        assert th_verdict.visa_fee_inr >= 0.0
        assert visa.total_visa_cost_inr >= 0.0

        # 5. Logistics Plan (International Flights & Hotel)
        logistics = itinerary.logistics_plan
        assert logistics is not None
        assert len(logistics.transport_legs) >= 2  # Outbound + Return
        outbound = logistics.transport_legs[0]
        return_leg = logistics.transport_legs[-1]
        assert outbound.mode == "FLIGHT"
        assert return_leg.mode == "FLIGHT"
        assert len(logistics.hotel_stays) >= 1
        assert logistics.hotel_stays[0].nights == 4

        # 6. Experience Plan
        experience = itinerary.experience_plan
        assert experience is not None
        assert len(experience.days) == 5
        # Every day has scheduled meals and activities
        for day in experience.days:
            assert len(day.activities) >= 1
            assert len(day.meals) >= 1

        # 7. Deterministic Financial Integrity (Zero LLM Arithmetic)
        budget = itinerary.budget_breakdown
        assert budget is not None
        cb = budget.cost_breakdown
        expected_subtotal = (
            cb.transport_inr
            + cb.accommodation_inr
            + cb.activities_inr
            + cb.food_inr
            + cb.local_transport_inr
            + cb.visa_inr
            + cb.misc_inr
        )
        assert abs(float(cb.subtotal_inr) - float(expected_subtotal)) < 0.01
        assert abs(cb.visa_inr - visa.total_visa_cost_inr) < 0.01

        # 8. Narrative Synthesis contains destination & Indian visa summary
        assert "Bangkok" in itinerary.title
        assert "Indian passport visa" in itinerary.summary
        assert "Thailand" in itinerary.summary

    def test_multi_country_schengen_slice_graph(self) -> None:
        """Verify India -> Country A -> Country B with Schengen optimization.

        Scenario: Delhi -> Paris -> Rome.
        """
        request_payload: dict[str, Any] = {
            "origin": "DEL",
            "destinations": ["Paris, France", "Rome, Italy"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-07",
            "adults": 2,
            "children": 0,
            "budget_inr": 350000.0,
            "travel_style": "COMFORTABLE",
            "pace": "BALANCED",
            # scope intentionally omitted to verify automatic scope resolution
        }

        final_state = run_planning_graph(request_payload)

        assert final_state["plan_status"] in ("COMPLETED", "NEEDS_USER_DECISION")
        assert not final_state.get("errors")

        itinerary = final_state.get("final_itinerary")
        assert itinerary is not None

        # 1. Visa Node Schengen Optimization
        visa = itinerary.visa_verdict
        assert visa is not None
        assert visa.is_domestic_bypass is False
        assert len(visa.countries) == 2
        country_codes = {c.country_code for c in visa.countries}
        assert "FR" in country_codes
        assert "IT" in country_codes
        # Both France and Italy belong to the Schengen Area -> single uniform Schengen visa
        assert visa.schengen_single_visa_applicable is True
        # Fee is charged ONCE per traveler (e.g. 2 * highest Schengen fee), NOT duplicated
        fr_fee = next(c.visa_fee_inr for c in visa.countries if c.country_code == "FR")
        it_fee = next(c.visa_fee_inr for c in visa.countries if c.country_code == "IT")
        single_highest_fee = max(fr_fee, it_fee)
        expected_visa_cost = single_highest_fee * 2
        assert abs(visa.total_visa_cost_inr - expected_visa_cost) < 0.01

        # 2. Logistics Multi-Hop Route (DEL -> Paris -> Rome -> DEL)
        logistics = itinerary.logistics_plan
        assert logistics is not None
        assert len(logistics.transport_legs) == 3
        assert len(logistics.hotel_stays) == 2

        # Stay dates must be sequential
        paris_stay = logistics.hotel_stays[0]
        rome_stay = logistics.hotel_stays[1]
        assert paris_stay.checkout_date == rome_stay.checkin_date
        assert paris_stay.nights + rome_stay.nights == 6

        # 3. Experience Plan across multiple countries
        experience = itinerary.experience_plan
        assert len(experience.days) == 7

        # 4. Synthesizer Narrative reflects multi-country and Schengen visa note
        assert "Paris" in itinerary.title or "Tour" in itinerary.title
        assert "Uniform Schengen Visa" in itinerary.summary

    def test_multi_country_non_schengen_slice_graph(self) -> None:
        """Verify India -> Country A -> Country B for Non-Schengen destinations.

        Scenario: Delhi -> Bangkok -> Singapore.
        """
        request_payload: dict[str, Any] = {
            "origin": "DEL",
            "destinations": ["Bangkok, Thailand", "Singapore"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-07",
            "adults": 2,
            "children": 0,
            "budget_inr": 250000.0,
            "travel_style": "COMFORTABLE",
            "pace": "BALANCED",
            "scope": "INTERNATIONAL",
        }

        final_state = run_planning_graph(request_payload)
        itinerary = final_state.get("final_itinerary")
        assert itinerary is not None

        visa = itinerary.visa_verdict
        assert visa is not None
        assert visa.schengen_single_visa_applicable is False
        assert len(visa.countries) == 2

        # Non-Schengen total fee = sum of individual country fees * 2 adults
        total_pp = sum(c.visa_fee_inr for c in visa.countries)
        assert abs(visa.total_visa_cost_inr - (total_pp * 2)) < 0.01


class TestInternationalSliceApi:
    """FastAPI REST API integration tests for international trip planning."""

    @classmethod
    def setup_class(cls) -> None:
        cls.client = TestClient(app)

    def test_post_plan_single_country_international(self) -> None:
        """Test POST /api/v1/plan endpoint with single-country international trip."""
        payload = {
            "origin": "Delhi",
            "destinations": ["Bangkok, Thailand"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-05",
            "budget_inr": 150000.0,
            "adults": 2,
            "children": 0,
            "travel_style": "COMFORTABLE",
            "pace": "BALANCED",
            "scope": "INTERNATIONAL",
            "activity_preferences": ["sightseeing"],
        }

        response = self.client.post("/api/v1/plan", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ("COMPLETED", "NEEDS_USER_DECISION")
        assert "itinerary" in data

        itinerary = data["itinerary"]
        assert itinerary["trip_context"]["scope"] == "INTERNATIONAL"
        assert itinerary["visa_verdict"] is not None
        assert itinerary["visa_verdict"]["is_domestic_bypass"] is False
        assert len(itinerary["visa_verdict"]["countries"]) >= 1

        # Check financial properties
        breakdown = itinerary["budget_breakdown"]
        assert breakdown["cost_breakdown"]["visa_inr"] >= 0.0
        assert breakdown["total_with_contingency_inr"] > 0.0

    def test_post_plan_multi_country_schengen_auto_scope(self) -> None:
        """Test POST /api/v1/plan with multi-country Schengen trip and auto-detected scope."""
        payload = {
            "origin": "BOM",
            "destinations": ["Paris, France", "Rome, Italy"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-07",
            "budget_inr": 350000.0,
            "adults": 2,
            "travel_style": "COMFORTABLE",
            "pace": "BALANCED",
            # scope omitted -> auto-detected as INTERNATIONAL
        }

        response = self.client.post("/api/v1/plan", json=payload)
        assert response.status_code == 200

        data = response.json()
        itinerary = data["itinerary"]
        assert itinerary["trip_context"]["scope"] == "INTERNATIONAL"
        assert itinerary["visa_verdict"]["schengen_single_visa_applicable"] is True

    def test_post_plan_foreign_origin_rejected(self) -> None:
        """Test that non-Indian departure origins are rejected with 400 Bad Request."""
        payload = {
            "origin": "Paris",
            "destinations": ["Rome"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-05",
            "budget_inr": 100000.0,
            "adults": 2,
        }

        response = self.client.post("/api/v1/plan", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "India" in data["detail"] or "departure" in data["detail"].lower()

    def test_post_plan_domestic_scope_conflict_rejected(self) -> None:
        """Test that explicit domestic scope with foreign destinations raises 400 conflict."""
        payload = {
            "origin": "Delhi",
            "destinations": ["Bangkok, Thailand"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-05",
            "budget_inr": 100000.0,
            "adults": 2,
            "scope": "DOMESTIC",  # Conflict!
        }

        response = self.client.post("/api/v1/plan", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "DOMESTIC" in data["detail"]
        assert "outside India" in data["detail"]


class TestInternationalSelectiveReplan:
    """Verify selective re-planning on an international itinerary."""

    def test_international_replan_increase_budget(self) -> None:
        """Verify increasing budget reuses international visa, logistics,
        and experience artifacts.
        """
        initial_payload = {
            "origin": "DEL",
            "destinations": ["Bangkok, Thailand"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-05",
            "adults": 2,
            "budget_inr": 150000.0,
            "travel_style": "COMFORTABLE",
            "pace": "BALANCED",
            "scope": "INTERNATIONAL",
        }

        initial_state = run_planning_graph(initial_payload)
        assert initial_state["final_itinerary"] is not None
        orig_visa = initial_state["visa_verdict"]
        orig_logistics = initial_state["logistics_plan"]
        orig_experience = initial_state["experience_plan"]

        # Re-plan with INCREASE_BUDGET
        replanned_state = replan_workflow(initial_state, "INCREASE_BUDGET", 250000.0)

        # Unaffected artifacts are preserved
        assert replanned_state["visa_verdict"] == orig_visa
        assert replanned_state["logistics_plan"] == orig_logistics
        assert replanned_state["experience_plan"] == orig_experience

        # Financial breakdown & FinalItinerary are re-synthesized
        replanned_itinerary = replanned_state["final_itinerary"]
        assert replanned_itinerary is not None
        assert replanned_itinerary.budget_breakdown.variance.user_budget_inr == 250000.0
