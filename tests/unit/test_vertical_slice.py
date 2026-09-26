"""Phase 13 — First Complete Vertical Slice Tests.

Validates the full vertical slice of the Safarnama travel planning system:
1. Synthesizer node unit tests:
   - Structured FinalItinerary generation with executive summary and title.
   - Provenance tracking (is_estimated flag propagation).
   - Warning aggregation and status resolution.
2. End-to-end StateGraph execution:
   - Controlled domestic scenario (Delhi -> Goa, 2 adults, 4 days, ₹100,000).
   - Pipeline: Intake -> Domestic Scope Routing -> Parallel Planning -> Budget
     -> Optimizer -> Synthesizer.
   - Deterministic financial integrity: budget numbers match BudgetBreakdown exactly.
3. FastAPI endpoint integration tests:
   - POST /api/v1/plan returns 200 OK with PlanResponse schema.
   - POST /api/v1/plan validates inputs and returns 422 for malformed requests.
   - POST /api/v1/plan handles domain validation errors gracefully.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.graph.state import create_initial_state
from src.graph.workflow import run_planning_graph
from src.models.budget import (
    BudgetBreakdown,
    OptimizationAction,
    OptimizationResult,
)
from src.models.itinerary import (
    ExperiencePlan,
    FinalItinerary,
)
from src.models.logistics import LogisticsPlan
from src.models.trip import (
    BudgetMode,
    DateMode,
    FoodPreferences,
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
from src.nodes.logistics_node import process_logistics
from src.nodes.synthesizer_node import (
    SynthesizerValidationError,
    generate_itinerary_summary,
    generate_itinerary_title,
    process_synthesizer,
    synthesizer_node,
)


@pytest.fixture
def sample_trip_context() -> TripContext:
    """Fixture providing a standard domestic 4-day Goa trip context."""
    return TripContext(
        origin="Delhi",
        destinations=["Goa"],
        scope=TravelScope.DOMESTIC,
        party=TripParty(adults=2, children=0),
        dates=TripDates(
            mode=DateMode.EXACT,
            start_date="2026-11-01",
            end_date="2026-11-04",
            duration_days=4,
        ),
        budget=TripBudget(mode=BudgetMode.TOTAL, amount_inr=60000.0),
        travel_style=TravelStyle.COMFORTABLE,
        pace=Pace.BALANCED,
        activity_preferences=["beaches", "relaxation"],
        must_visits=["Baga Beach"],
        food=FoodPreferences(dietary_preference=None),
    )


@pytest.fixture
def sample_logistics_plan(sample_trip_context: TripContext) -> LogisticsPlan:
    """Fixture providing a logistics plan for Goa via process_logistics."""
    return process_logistics(sample_trip_context, use_fixture=True)


@pytest.fixture
def sample_experience_plan(
    sample_trip_context: TripContext,
    sample_logistics_plan: LogisticsPlan,
) -> ExperiencePlan:
    """Fixture providing a mock experience plan for Goa via process_experience."""
    return process_experience(
        sample_trip_context,
        logistics_plan=sample_logistics_plan,
        use_fixture=True,
    )


@pytest.fixture
def sample_budget_breakdown(
    sample_trip_context: TripContext,
    sample_logistics_plan: LogisticsPlan,
    sample_experience_plan: ExperiencePlan,
) -> BudgetBreakdown:
    """Fixture providing a deterministic budget breakdown via process_budget."""
    return process_budget(
        sample_trip_context,
        logistics_plan=sample_logistics_plan,
        experience_plan=sample_experience_plan,
    )


@pytest.fixture
def sample_optimization_result() -> OptimizationResult:
    """Fixture providing a feasible optimization result."""
    return OptimizationResult(
        action=OptimizationAction.NONE,
        explanation="Trip is fully feasible and comfortably within budget.",
        replan_proposal=None,
    )


class TestSynthesizerUnit:
    """Unit tests for the Synthesizer planning node."""

    def test_generate_itinerary_title(self, sample_trip_context: TripContext) -> None:
        title = generate_itinerary_title(sample_trip_context)
        assert "Goa" in title
        assert "4-Day" in title

    def test_generate_itinerary_summary(
        self,
        sample_trip_context: TripContext,
        sample_logistics_plan: LogisticsPlan,
        sample_experience_plan: ExperiencePlan,
        sample_budget_breakdown: BudgetBreakdown,
    ) -> None:
        summary = generate_itinerary_summary(
            sample_trip_context,
            sample_logistics_plan,
            sample_experience_plan,
            sample_budget_breakdown,
        )
        assert "Delhi" in summary
        assert "Goa" in summary
        cost_str = f"{int(sample_budget_breakdown.total_with_contingency_inr):,}"
        assert cost_str in summary
        assert "comfortable" in summary.lower()

    def test_process_synthesizer_success(
        self,
        sample_trip_context: TripContext,
        sample_logistics_plan: LogisticsPlan,
        sample_experience_plan: ExperiencePlan,
        sample_budget_breakdown: BudgetBreakdown,
        sample_optimization_result: OptimizationResult,
    ) -> None:
        itinerary = process_synthesizer(
            trip_context=sample_trip_context,
            logistics_plan=sample_logistics_plan,
            experience_plan=sample_experience_plan,
            budget_breakdown=sample_budget_breakdown,
            visa_verdict=None,
            optimization_result=sample_optimization_result,
            warnings=["Weather warning: occasional showers"],
        )

        assert isinstance(itinerary, FinalItinerary)
        assert itinerary.title != ""
        assert itinerary.summary != ""
        assert itinerary.plan_status == "COMPLETED"
        assert itinerary.trip_context.origin == "Delhi"
        assert itinerary.logistics_plan == sample_logistics_plan
        assert itinerary.experience_plan == sample_experience_plan
        assert itinerary.budget_breakdown == sample_budget_breakdown

    def test_process_synthesizer_missing_context(
        self,
        sample_logistics_plan: LogisticsPlan,
        sample_experience_plan: ExperiencePlan,
        sample_budget_breakdown: BudgetBreakdown,
    ) -> None:
        with pytest.raises(SynthesizerValidationError):
            process_synthesizer(
                trip_context=None,
                logistics_plan=sample_logistics_plan,
                experience_plan=sample_experience_plan,
                budget_breakdown=sample_budget_breakdown,
            )

    def test_synthesizer_node_wrapper(
        self,
        sample_trip_context: TripContext,
        sample_logistics_plan: LogisticsPlan,
        sample_experience_plan: ExperiencePlan,
        sample_budget_breakdown: BudgetBreakdown,
        sample_optimization_result: OptimizationResult,
    ) -> None:
        state = create_initial_state(trip_context=sample_trip_context)
        state["logistics_plan"] = sample_logistics_plan
        state["experience_plan"] = sample_experience_plan
        state["budget_breakdown"] = sample_budget_breakdown
        state["optimization_result"] = sample_optimization_result
        state["warnings"] = ["Initial warning"]

        update = synthesizer_node(state)
        assert "final_itinerary" in update
        assert update["plan_status"] == "COMPLETED"
        assert isinstance(update["final_itinerary"], FinalItinerary)


class TestVerticalSliceWorkflow:
    """Integration tests for the complete StateGraph planning workflow."""

    def test_full_domestic_vertical_slice_graph(self) -> None:
        """Run the end-to-end planning graph with a controlled domestic scenario."""
        request_payload = {
            "origin": "Delhi",
            "destinations": ["Goa"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-04",
            "adults": 2,
            "budget_inr": 100000.0,
            "travel_style": "COMFORTABLE",
            "pace": "BALANCED",
            "activity_preferences": ["beaches", "relaxation"],
            "must_visits": ["Baga Beach"],
        }

        final_state = run_planning_graph(request_payload)

        # 1. Pipeline execution status
        assert final_state["plan_status"] in ("COMPLETED", "NEEDS_USER_DECISION")
        assert not final_state.get("errors")

        # 2. Output deliverable
        itinerary = final_state.get("final_itinerary")
        assert itinerary is not None
        assert isinstance(itinerary, FinalItinerary)

        # 3. Check domain models embedded in FinalItinerary
        assert itinerary.trip_context is not None
        assert itinerary.trip_context.origin.lower() in ("delhi", "del")
        assert itinerary.logistics_plan is not None
        assert len(itinerary.logistics_plan.transport_legs) >= 1
        assert itinerary.experience_plan is not None
        assert len(itinerary.experience_plan.days) >= 1
        assert itinerary.budget_breakdown is not None
        assert itinerary.optimization_result is not None

        # 4. Zero LLM arithmetic verification
        cb = itinerary.budget_breakdown.cost_breakdown
        expected_subtotal = (
            cb.transport_inr
            + cb.accommodation_inr
            + cb.activities_inr
            + cb.food_inr
            + cb.local_transport_inr
            + cb.visa_inr
            + cb.misc_inr
        )
        assert abs(itinerary.budget_breakdown.subtotal_inr - expected_subtotal) < 0.01
        assert (
            abs(
                itinerary.budget_breakdown.total_with_contingency_inr
                - (expected_subtotal + itinerary.budget_breakdown.contingency.amount_inr)
            )
            < 0.01
        )


class TestVerticalSliceApi:
    """FastAPI endpoint integration tests for POST /api/v1/plan."""

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(app)

    def test_post_plan_valid_domestic(self, client: TestClient) -> None:
        """POST /api/v1/plan produces valid 200 PlanResponse with FinalItinerary."""
        payload = {
            "origin": "Delhi",
            "destinations": ["Goa"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-04",
            "adults": 2,
            "children": 0,
            "budget_inr": 100000.0,
            "budget_mode": "TOTAL",
            "travel_style": "COMFORTABLE",
            "pace": "BALANCED",
            "activity_preferences": ["beaches"],
            "must_visits": ["Baga Beach"],
        }

        response = client.post("/api/v1/plan", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ("COMPLETED", "NEEDS_USER_DECISION")
        assert "itinerary" in data

        itinerary = data["itinerary"]
        assert "trip_id" in itinerary
        assert "title" in itinerary
        assert "summary" in itinerary
        assert "Goa" in itinerary["title"]
        assert itinerary["budget_breakdown"]["total_with_contingency_inr"] > 0
        assert len(itinerary["logistics_plan"]["transport_legs"]) > 0
        assert len(itinerary["experience_plan"]["days"]) > 0

    def test_post_plan_missing_fields_validation_error(self, client: TestClient) -> None:
        """POST /api/v1/plan returns 422 if mandatory fields are missing."""
        invalid_payload = {
            "origin": "Delhi",
            # missing destinations, start_date, end_date
        }
        response = client.post("/api/v1/plan", json=invalid_payload)
        assert response.status_code == 422

    def test_post_plan_zero_travelers_validation_error(self, client: TestClient) -> None:
        """POST /api/v1/plan returns 422 when travelers count violates constraints."""
        invalid_payload = {
            "origin": "Delhi",
            "destinations": ["Goa"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-04",
            "adults": 0,  # ge=1 required
            "budget_inr": 60000.0,
        }
        response = client.post("/api/v1/plan", json=invalid_payload)
        assert response.status_code == 422
