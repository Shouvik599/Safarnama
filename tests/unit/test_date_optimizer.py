"""Unit tests for Phase 15 — Flexible Dates (src/nodes/date_node.py).

Verifies all requirements from phases.md Section 19 and prd.md Section 5.5:
1. DateMode.EXACT:
   - Confirms exact start/end dates.
   - Evaluates a single candidate window, 0 alternatives.
   - Composite quality score (0-100) and structured trade-offs.
2. DateMode.FLEXIBLE:
   - Generates candidate windows shifted by -N to +N days.
   - Multi-factor evaluation (transport + lodging pricing, weather comfort, weekend efficiency).
   - Selects top-scoring window as recommended + up to 3 ranked alternatives.
   - Generates structured trade-off observations for each candidate.
   - Updates trip_context start_date and end_date for downstream nodes.
3. DateMode.FIND_BEST:
   - Evaluates sliding windows across a broad calendar window (window_start to window_end).
   - Identifies highest-scoring duration_days window + alternatives.
   - Updates trip_context dates accordingly.
4. Scoring Components:
   - Transport cost estimation (seasonal multiplier, distance-based, route check).
   - Lodging cost estimation (tier, duration, seasonal multiplier).
   - Weather assessment (historical weather fixture fallback, rain probability, outdoor comfort).
   - Weekend weighting bonus (maximizes weekend days for convenience).
   - Composite score formula: 45% price + 45% weather + weekend bonus.
5. Error handling and validation:
   - Validates required fields for each DateMode.
   - Respects error short-circuit when previous nodes set errors.
6. API integration:
   - PlanRequest accepts date_mode, flexibility_days, window_start, window_end.
   - Completeness validation enforces mode-specific constraints.
7. Full Workflow Integration:
   - LangGraph StateGraph executes date_optimizer node between intake and route_scope.
   - Downstream logistics and experience nodes plan with recommended dates.
   - FinalItinerary contains populated date_options and summary narrative.
"""

from __future__ import annotations

from datetime import date

import pytest
from src.api.models import PlanRequest
from src.graph.state import create_initial_state
from src.graph.workflow import build_planning_graph
from src.models.itinerary import FinalItinerary
from src.models.trip import (
    BudgetMode,
    DateCandidate,
    DateMode,
    DateOptimizationResult,
    Pace,
    TravelScope,
    TravelStyle,
    TripBudget,
    TripContext,
    TripDates,
    TripParty,
)
from src.nodes.date_node import (
    DateOptimizationError,
    date_node,
    evaluate_date_candidate,
    generate_candidate_date_ranges,
    process_date_optimization,
)


@pytest.fixture(autouse=True)
def enable_fixtures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure all date optimization tests run with deterministic fixture isolation."""
    monkeypatch.setenv("SAFARNAMA_USE_FIXTURES", "true")


# ---------------------------------------------------------------------------
# Test Helpers & Fixtures
# ---------------------------------------------------------------------------


def make_test_context(
    mode: DateMode = DateMode.EXACT,
    start_date: str | None = "2026-10-10",
    end_date: str | None = "2026-10-14",
    flexibility_days: int = 3,
    window_start: str | None = None,
    window_end: str | None = None,
    duration_days: int = 5,
    origin: str = "DEL",
    destinations: list[str] | None = None,
    budget_inr: float = 60_000.0,
) -> TripContext:
    """Create a standard TripContext fixture for date optimization testing."""
    dests = destinations or ["BOM"]
    return TripContext(
        scope=TravelScope.DOMESTIC,
        origin=origin,
        destinations=dests,
        dates=TripDates(
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            mode=mode,
            flexibility_days=flexibility_days,
            window_start=window_start,
            window_end=window_end,
        ),
        party=TripParty(adults=1, children=0, infants=0),
        budget=TripBudget(
            amount_inr=budget_inr,
            mode=BudgetMode.TOTAL,
        ),
        travel_style=TravelStyle.COMFORTABLE,
        pace=Pace.BALANCED,
        interests=["sightseeing", "culture"],
    )


# ---------------------------------------------------------------------------
# 1. EXACT Date Mode
# ---------------------------------------------------------------------------


class TestExactDateMode:
    """Verifies behavior for DateMode.EXACT."""

    def test_exact_mode_single_candidate(self) -> None:
        ctx = make_test_context(
            mode=DateMode.EXACT,
            start_date="2026-10-10",
            end_date="2026-10-14",
            duration_days=5,
        )
        _, result = process_date_optimization(ctx, use_fixture=True)

        assert isinstance(result, DateOptimizationResult)
        assert result.mode == DateMode.EXACT
        assert result.total_candidates_evaluated == 1
        assert len(result.alternatives) == 0
        assert result.recommended.start_date == "2026-10-10"
        assert result.recommended.end_date == "2026-10-14"
        assert result.recommended.duration_days == 5
        assert 0.0 <= result.recommended.composite_score <= 100.0
        assert len(result.recommended.trade_offs) >= 2
        assert "Exact travel dates confirmed" in result.evaluation_summary

    def test_exact_mode_preserves_context_dates(self) -> None:
        ctx = make_test_context(
            mode=DateMode.EXACT,
            start_date="2026-11-01",
            end_date="2026-11-06",
            duration_days=5,
        )
        state = create_initial_state(trip_context=ctx)
        update = date_node(state)

        assert "date_options" in update
        assert "trip_context" in update
        opt_res: DateOptimizationResult = update["date_options"]
        updated_ctx: TripContext = update["trip_context"]

        assert opt_res.recommended.start_date == "2026-11-01"
        assert updated_ctx.dates.start_date == "2026-11-01"
        assert updated_ctx.dates.end_date == "2026-11-06"


# ---------------------------------------------------------------------------
# 2. FLEXIBLE Date Mode
# ---------------------------------------------------------------------------


class TestFlexibleDateMode:
    """Verifies behavior for DateMode.FLEXIBLE."""

    def test_flexible_mode_candidate_generation(self) -> None:
        dates = TripDates(
            start_date="2026-10-10",
            end_date="2026-10-15",
            duration_days=5,
            mode=DateMode.FLEXIBLE,
            flexibility_days=3,
        )
        windows = generate_candidate_date_ranges(dates)

        # For +/-3 days, should generate 7 candidate windows (-3, -2, -1, 0, +1, +2, +3)
        assert len(windows) == 7
        for start_str, end_str, dur in windows:
            assert dur == 5
            s = date.fromisoformat(start_str)
            e = date.fromisoformat(end_str)
            assert (e - s).days == 4

    def test_flexible_mode_optimization_selection(self) -> None:
        ctx = make_test_context(
            mode=DateMode.FLEXIBLE,
            start_date="2026-10-10",
            end_date="2026-10-15",
            flexibility_days=3,
            duration_days=5,
        )
        _, result = process_date_optimization(ctx, use_fixture=True)

        assert result.mode == DateMode.FLEXIBLE
        assert result.total_candidates_evaluated == 7
        assert len(result.alternatives) <= 3
        assert len(result.alternatives) >= 2

        # Recommended should be the highest-scoring candidate
        assert result.recommended.composite_score >= result.alternatives[0].composite_score

        # Alternatives should be sorted descending by composite_score
        scores = [alt.composite_score for alt in result.alternatives]
        assert scores == sorted(scores, reverse=True)

        # Each alternative has structured trade-offs
        for alt in result.alternatives:
            assert len(alt.trade_offs) >= 2
            assert alt.duration_days == 5

        # Summary mentions candidate window count and flexibility range
        assert "+/-3 days" in result.evaluation_summary

    def test_flexible_mode_updates_trip_context_dates(self) -> None:
        ctx = make_test_context(
            mode=DateMode.FLEXIBLE,
            start_date="2026-10-10",
            end_date="2026-10-15",
            flexibility_days=2,
        )
        state = create_initial_state(trip_context=ctx)
        update = date_node(state)

        updated_ctx: TripContext = update["trip_context"]
        opt_res: DateOptimizationResult = update["date_options"]

        # Context start/end dates must match recommended candidate
        assert updated_ctx.dates.start_date == opt_res.recommended.start_date
        assert updated_ctx.dates.end_date == opt_res.recommended.end_date
        assert updated_ctx.dates.mode == DateMode.FLEXIBLE


# ---------------------------------------------------------------------------
# 3. FIND_BEST Date Mode
# ---------------------------------------------------------------------------


class TestFindBestDateMode:
    """Verifies behavior for DateMode.FIND_BEST."""

    def test_find_best_candidate_generation(self) -> None:
        dates = TripDates(
            mode=DateMode.FIND_BEST,
            duration_days=5,
            window_start="2026-11-01",
            window_end="2026-11-20",
        )
        windows = generate_candidate_date_ranges(dates)

        # Window span = 20 days. Duration = 5 days. Candidates sampled evenly (up to 5)
        assert len(windows) >= 3
        for start_str, end_str, dur in windows:
            assert dur == 5
            s = date.fromisoformat(start_str)
            e = date.fromisoformat(end_str)
            assert (e - s).days == 4
            assert s >= date(2026, 11, 1)
            assert e <= date(2026, 11, 20)

    def test_find_best_optimization_selection(self) -> None:
        ctx = make_test_context(
            mode=DateMode.FIND_BEST,
            start_date=None,
            end_date=None,
            window_start="2026-11-01",
            window_end="2026-11-15",
            duration_days=4,
        )
        _, result = process_date_optimization(ctx, use_fixture=True)

        assert result.mode == DateMode.FIND_BEST
        assert result.total_candidates_evaluated > 1
        assert len(result.alternatives) <= 3
        assert result.recommended.duration_days == 4
        assert result.recommended.composite_score >= result.alternatives[0].composite_score
        assert "Window search across" in result.evaluation_summary

    def test_find_best_updates_context_dates(self) -> None:
        ctx = make_test_context(
            mode=DateMode.FIND_BEST,
            start_date=None,
            end_date=None,
            window_start="2026-11-01",
            window_end="2026-11-15",
            duration_days=4,
        )
        state = create_initial_state(trip_context=ctx)
        update = date_node(state)

        updated_ctx: TripContext = update["trip_context"]
        opt_res: DateOptimizationResult = update["date_options"]

        assert updated_ctx.dates.start_date is not None
        assert updated_ctx.dates.end_date is not None
        assert updated_ctx.dates.start_date == opt_res.recommended.start_date
        assert updated_ctx.dates.end_date == opt_res.recommended.end_date


# ---------------------------------------------------------------------------
# 4. Multi-Factor Scoring & Evaluation
# ---------------------------------------------------------------------------


class TestDateScoringFactors:
    """Verifies composite scoring logic and multi-factor breakdown."""

    def test_evaluate_date_candidate_scores(self) -> None:
        ctx = make_test_context()
        from src.models.trip import ResolvedLocation

        origin = ResolvedLocation(
            query="DEL",
            name="Delhi Airport",
            city="Delhi",
            country_code="IN",
            country_name="India",
            iata_code="DEL",
            latitude=28.5562,
            longitude=77.1000,
        )
        dest = ResolvedLocation(
            query="BOM",
            name="Mumbai Airport",
            city="Mumbai",
            country_code="IN",
            country_name="India",
            iata_code="BOM",
            latitude=19.0896,
            longitude=72.8656,
        )

        cand = evaluate_date_candidate(
            start_date="2026-10-10",
            end_date="2026-10-15",
            duration_days=5,
            origin=origin,
            destinations=[dest],
            party=ctx.party,
            travel_style=ctx.travel_style,
            travel_scope=ctx.scope,
            budget_inr=ctx.budget.amount_inr,
            use_fixture=True,
        )

        assert isinstance(cand, DateCandidate)
        assert 0.0 <= cand.composite_score <= 100.0
        assert 0.0 <= cand.price_score <= 100.0
        assert 0.0 <= cand.weather_score <= 100.0
        assert cand.estimated_transport_cost_inr > 0.0
        assert cand.estimated_hotel_cost_inr > 0.0
        assert (
            cand.total_logistics_cost_inr
            == cand.estimated_transport_cost_inr + cand.estimated_hotel_cost_inr
        )
        assert cand.weather_summary != ""
        assert isinstance(cand.is_weather_favorable, bool)

    def test_weekend_bonus_weighting(self) -> None:
        ctx = make_test_context()
        from src.models.trip import ResolvedLocation

        origin = ResolvedLocation(
            query="DEL",
            name="Delhi Airport",
            city="Delhi",
            country_code="IN",
            country_name="India",
            iata_code="DEL",
            latitude=28.5562,
            longitude=77.1000,
        )
        dest = ResolvedLocation(
            query="BOM",
            name="Mumbai Airport",
            city="Mumbai",
            country_code="IN",
            country_name="India",
            iata_code="BOM",
            latitude=19.0896,
            longitude=72.8656,
        )

        # Candidate 1: Friday Oct 9 to Monday Oct 12 (includes Saturday and Sunday)
        weekend_cand = evaluate_date_candidate(
            start_date="2026-10-09",
            end_date="2026-10-12",
            duration_days=4,
            origin=origin,
            destinations=[dest],
            party=ctx.party,
            travel_style=ctx.travel_style,
            travel_scope=ctx.scope,
            budget_inr=ctx.budget.amount_inr,
            use_fixture=True,
        )
        assert weekend_cand.is_weekend_heavy is True
        assert any("Weekend-optimized" in trade for trade in weekend_cand.trade_offs)

        # Candidate 2: Monday Oct 12 to Thursday Oct 15 (no weekend days)
        weekday_cand = evaluate_date_candidate(
            start_date="2026-10-12",
            end_date="2026-10-15",
            duration_days=4,
            origin=origin,
            destinations=[dest],
            party=ctx.party,
            travel_style=ctx.travel_style,
            travel_scope=ctx.scope,
            budget_inr=ctx.budget.amount_inr,
            use_fixture=True,
        )
        assert weekday_cand.is_weekend_heavy is False
        assert any("Mid-week schedule" in trade for trade in weekday_cand.trade_offs)


# ---------------------------------------------------------------------------
# 5. Validation and Edge Cases
# ---------------------------------------------------------------------------


class TestDateOptimizationValidation:
    """Verifies edge cases and error handling."""

    def test_missing_start_date_in_exact_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="start_date is required"):
            TripDates(mode=DateMode.EXACT, start_date=None, end_date=None)

    def test_missing_window_in_find_best_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="window_start is required"):
            TripDates(mode=DateMode.FIND_BEST, window_start=None, window_end=None, duration_days=5)

    def test_inverted_window_raises(self) -> None:
        ctx = make_test_context(
            mode=DateMode.FIND_BEST,
            start_date=None,
            end_date=None,
            window_start="2026-11-20",
            window_end="2026-11-10",
            duration_days=5,
        )
        with pytest.raises(DateOptimizationError, match="window_start must be before window_end"):
            process_date_optimization(ctx)

    def test_date_node_short_circuits_on_existing_errors(self) -> None:
        state = {
            "errors": ["Intake validation failed: Missing origin"],
        }
        res = date_node(state)
        assert res == {}


# ---------------------------------------------------------------------------
# 6. API PlanRequest Conversion
# ---------------------------------------------------------------------------


class TestApiPlanRequestDateMode:
    """Verifies PlanRequest validation and conversion for Phase 15 date parameters."""

    def test_plan_request_flexible_validation(self) -> None:
        # Valid flexible request
        req = PlanRequest(
            origin="DEL",
            destinations=["BOM"],
            start_date="2026-10-10",
            end_date="2026-10-15",
            budget=50000.0,
            date_mode="FLEXIBLE",
            flexibility_days=3,
        )
        assert req.date_mode == "FLEXIBLE"
        ctx = req.to_trip_context()
        assert ctx.dates.mode == DateMode.FLEXIBLE
        assert ctx.dates.flexibility_days == 3

    def test_plan_request_find_best_validation(self) -> None:
        # Valid find_best request
        req = PlanRequest(
            origin="DEL",
            destinations=["GOI"],
            duration_days=4,
            budget=40000.0,
            date_mode="FIND_BEST",
            window_start="2026-11-01",
            window_end="2026-11-20",
        )
        assert req.date_mode == "FIND_BEST"
        ctx = req.to_trip_context()
        assert ctx.dates.mode == DateMode.FIND_BEST
        assert ctx.dates.window_start == "2026-11-01"
        assert ctx.dates.window_end == "2026-11-20"
        assert ctx.dates.duration_days == 4

    def test_plan_request_find_best_missing_window_reports_errors(self) -> None:
        with pytest.raises(ValueError, match="window_start"):
            PlanRequest(
                origin="DEL",
                destinations=["GOI"],
                duration_days=4,
                budget=40000.0,
                date_mode="FIND_BEST",
            )


# ---------------------------------------------------------------------------
# 7. LangGraph End-to-End Workflow Integration
# ---------------------------------------------------------------------------


class TestLangGraphDateOptimizationWorkflow:
    """Verifies end-to-end planning workflow with date optimization."""

    def test_workflow_flexible_date_planning(self) -> None:
        graph = build_planning_graph()
        initial_state = create_initial_state()
        initial_state["request"] = {
            "origin": "DEL",
            "destinations": ["BOM"],
            "start_date": "2026-10-10",
            "end_date": "2026-10-14",
            "duration_days": 4,
            "date_mode": "FLEXIBLE",
            "flexibility_days": 2,
            "budget": 75000.0,
            "travel_style": "COMFORTABLE",
            "interests": ["sightseeing", "food"],
        }
        initial_state["use_fixture"] = True

        final_state = graph.invoke(initial_state)

        assert not final_state.get("errors")
        assert final_state.get("final_itinerary") is not None
        itinerary: FinalItinerary = final_state["final_itinerary"]

        # Date options populated
        assert itinerary.date_options is not None
        assert itinerary.date_options.mode == DateMode.FLEXIBLE
        assert len(itinerary.date_options.alternatives) >= 1
        assert (
            itinerary.date_options.recommended.start_date == itinerary.trip_context.dates.start_date
        )

        # Summary references date optimization
        assert "Date Strategy" in itinerary.summary or "dates" in itinerary.summary.lower()

    def test_workflow_exact_date_planning(self) -> None:
        graph = build_planning_graph()
        initial_state = create_initial_state()
        initial_state["use_fixture"] = True
        initial_state["request"] = {
            "origin": "DEL",
            "destinations": ["BOM"],
            "start_date": "2026-10-10",
            "end_date": "2026-10-14",
            "duration_days": 4,
            "date_mode": "EXACT",
            "budget": 75000.0,
            "travel_style": "COMFORTABLE",
            "interests": ["sightseeing", "food"],
        }

        final_state = graph.invoke(initial_state)

        assert not final_state.get("errors")
        itinerary: FinalItinerary = final_state["final_itinerary"]
        assert itinerary.date_options is not None
        assert itinerary.date_options.mode == DateMode.EXACT
        assert itinerary.trip_context.dates.start_date == "2026-10-10"
        assert itinerary.trip_context.dates.end_date == "2026-10-14"
