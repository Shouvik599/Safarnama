"""Phase 17 — Unit & API Tests: Real-time LangGraph API Streaming (SSE).

Verifies:
1. Asynchronous event generator stream_planning_graph across domestic and international scopes.
2. Sequential lifecycle of planning events (planning_started, intake_completed, visa, logistics,
   experience, budget, optimization, planning_completed).
3. Selective event streaming during iterative re-planning (stream_replan_workflow).
4. FastAPI endpoints: POST /plan/stream, GET /plan/stream, POST /plan/replan/stream.
5. Error and warning event handling without leaking internal LangChain traces.
6. Strict offline execution using fixtures.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.api.models import PlanningEvent, PlanRequest
from src.graph.streaming import (
    _summarize_budget_output,
    _summarize_date_output,
    _summarize_experience_output,
    _summarize_intake_output,
    _summarize_logistics_output,
    _summarize_optimizer_output,
    _summarize_visa_output,
    stream_planning_graph,
    stream_replan_workflow,
)
from src.graph.workflow import run_planning_graph


@pytest.fixture(autouse=True)
def setup_fixtures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests run strictly offline using deterministic fixtures."""
    monkeypatch.setenv("SAFARNAMA_USE_FIXTURES", "true")


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


def parse_sse_events(raw_text: str) -> list[dict[str, str]]:
    """Parse raw SSE text into a list of event dictionaries with 'event' and 'data'."""
    events = []
    current_event = None
    current_data = []

    for line in raw_text.splitlines():
        if line.startswith("event: "):
            current_event = line[len("event: ") :].strip()
        elif line.startswith("data: "):
            current_data.append(line[len("data: ") :].strip())
        elif line == "":
            if current_event or current_data:
                events.append(
                    {
                        "event": current_event or "message",
                        "data": "\n".join(current_data),
                    }
                )
                current_event = None
                current_data = []

    if current_event or current_data:
        events.append(
            {
                "event": current_event or "message",
                "data": "\n".join(current_data),
            }
        )
    return events


def test_planning_event_model_and_sse_serialization() -> None:
    """Verify PlanningEvent domain model serialization to valid SSE wire format."""
    ev = PlanningEvent(
        event="logistics_completed",
        stage="logistics",
        message="Transport routes and hotels finalized",
        data={"transport_legs_count": 2, "hotel_stays_count": 1},
    )

    sse_text = ev.to_sse()
    assert sse_text.startswith("event: logistics_completed\n")
    assert "data: {" in sse_text
    assert sse_text.endswith("\n\n")

    lines = [line for line in sse_text.splitlines() if line]
    assert len(lines) == 2
    assert lines[0] == "event: logistics_completed"
    parsed_payload = json.loads(lines[1].replace("data: ", ""))
    assert parsed_payload["event"] == "logistics_completed"
    assert parsed_payload["stage"] == "logistics"
    assert parsed_payload["data"]["transport_legs_count"] == 2


def test_stream_planning_graph_domestic_lifecycle() -> None:
    """Verify complete domestic event stream from planning_started to planning_completed."""

    async def _run():
        req = {
            "origin": "DEL",
            "destinations": ["Goa"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-04",
            "duration_days": 3,
            "budget_inr": 35000.0,
        }

        events: list[PlanningEvent] = []
        async for ev in stream_planning_graph(req):
            events.append(ev)

        event_names = [e.event for e in events]

        # Verify key lifecycle milestone events are present
        assert "planning_started" in event_names
        assert "intake_completed" in event_names
        assert "date_optimization_started" in event_names
        assert "date_optimization_completed" in event_names
        assert "experience_started" in event_names
        assert "logistics_started" in event_names
        assert "logistics_completed" in event_names
        assert "experience_completed" in event_names
        assert "budget_started" in event_names
        assert "budget_calculated" in event_names
        assert "optimization_started" in event_names
        assert "optimization_completed" in event_names
        assert "synthesizer_started" in event_names
        assert "planning_completed" in event_names

        # Domestic trips must not emit visa_started
        assert "visa_started" not in event_names

        # First event must be planning_started
        assert events[0].event == "planning_started"
        assert events[0].stage == "init"
        assert events[0].data["origin"] == "DEL"
        assert events[0].data["destinations"] == ["Goa"]

        # Final event must be planning_completed containing synthesized itinerary
        completed_ev = events[-1]
        assert completed_ev.event == "planning_completed"
        assert completed_ev.stage == "complete"
        assert "itinerary" in completed_ev.data
        assert completed_ev.data["itinerary"]["title"] is not None
        assert completed_ev.data["plan_status"] in (
            "COMPLETED",
            "INFEASIBLE",
            "NEEDS_USER_DECISION",
        )

    asyncio.run(_run())


def test_stream_planning_graph_international_visa_events() -> None:
    """Verify international planning streams visa_started and visa_completed events."""

    async def _run():
        req = {
            "origin": "BOM",
            "destinations": ["France"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-05",
            "duration_days": 4,
            "budget_inr": 150000.0,
        }

        events: list[PlanningEvent] = []
        async for ev in stream_planning_graph(req):
            events.append(ev)

        event_names = [e.event for e in events]

        assert "visa_started" in event_names
        assert "visa_completed" in event_names

        visa_completed = next(e for e in events if e.event == "visa_completed")
        assert visa_completed.stage == "visa"
        assert visa_completed.data["is_domestic_bypass"] is False
        assert visa_completed.data["countries_count"] >= 1
        assert "countries" in visa_completed.data

    asyncio.run(_run())


def test_stream_planning_graph_flexible_date_summary() -> None:
    """Verify flexible date options are broadcast cleanly in date_optimization_completed."""

    async def _run():
        plan_req = PlanRequest(
            origin="DEL",
            destinations=["Goa"],
            start_date="2026-11-01",
            duration_days=3,
            budget_inr=40000.0,
            date_mode="flexible",
            flexibility_days=3,
        )
        context = plan_req.to_trip_context()

        events: list[PlanningEvent] = []
        async for ev in stream_planning_graph(context):
            events.append(ev)

        date_ev = next(e for e in events if e.event == "date_optimization_completed")
        assert date_ev.data["mode"] == "FLEXIBLE"
        assert date_ev.data["recommended_window"] is not None
        assert "start_date" in date_ev.data["recommended_window"]
        assert "composite_score" in date_ev.data["recommended_window"]

    asyncio.run(_run())


def test_stream_planning_graph_error_event_on_failure() -> None:
    """Verify an error event is broadcast and stream terminates if a node fails."""

    async def _run():
        req = {
            "origin": "DEL",
            "destinations": ["Goa"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-04",
            "duration_days": 3,
            "budget_inr": 35000.0,
        }

        with patch(
            "src.nodes.budget_node.process_budget",
            side_effect=RuntimeError("Currency API dead"),
        ):
            events: list[PlanningEvent] = []
            async for ev in stream_planning_graph(req):
                events.append(ev)

        event_names = [e.event for e in events]
        assert "error" in event_names

        error_ev = next(e for e in events if e.event == "error")
        assert error_ev.data["plan_status"] == "FAILED"
        assert "planning_completed" not in event_names

    asyncio.run(_run())


def test_stream_replan_workflow_events() -> None:
    """Verify stream_replan_workflow broadcasts events for re-planning and reuses components."""

    async def _run():
        req = {
            "origin": "DEL",
            "destinations": ["Goa"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-04",
            "duration_days": 3,
            "budget_inr": 35000.0,
        }
        base_state = run_planning_graph(req)

        events: list[PlanningEvent] = []
        async for ev in stream_replan_workflow(
            current_state=base_state,
            proposal_type="INCREASE_BUDGET",
            target_value=120000.0,
        ):
            events.append(ev)

        event_names = [e.event for e in events]

        assert events[0].event == "planning_started"
        assert events[0].stage == "replan"
        assert "reused_components" in events[0].data
        assert "logistics" in events[0].data["reused_components"]
        assert "experience" in events[0].data["reused_components"]

        # Logistics and Experience should not be rerun for pure budget increases
        assert "logistics_started" not in event_names
        assert "experience_started" not in event_names

        # Budget, optimizer, and synthesizer must run
        assert "budget_started" in event_names
        assert "budget_calculated" in event_names
        assert "optimization_started" in event_names
        assert "optimization_completed" in event_names
        assert "synthesizer_started" in event_names
        assert "planning_completed" in event_names

        final_ev = events[-1]
        assert final_ev.event == "planning_completed"
        assert final_ev.data["plan_status"] in ("COMPLETED", "REPLANNED")
        assert "replan_summary" in final_ev.data

    asyncio.run(_run())


def test_api_post_plan_stream_endpoint(client: TestClient) -> None:
    """Verify POST /api/v1/plan/stream returns SSE stream with valid milestone events."""
    payload = {
        "origin": "DEL",
        "destinations": ["Goa"],
        "start_date": "2026-11-01",
        "end_date": "2026-11-04",
        "duration_days": 3,
        "budget_inr": 35000.0,
    }

    response = client.post("/api/v1/plan/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert response.headers.get("Cache-Control") == "no-cache"

    events = parse_sse_events(response.text)
    event_names = [e["event"] for e in events]

    assert "planning_started" in event_names
    assert "intake_completed" in event_names
    assert "budget_calculated" in event_names
    assert "optimization_completed" in event_names
    assert "planning_completed" in event_names

    # Verify JSON parseability of payload
    completed = next(e for e in events if e["event"] == "planning_completed")
    data = json.loads(completed["data"])
    assert "title" in data["data"]
    assert "itinerary" in data["data"]


def test_api_get_plan_stream_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/plan/stream provides browser EventSource compatibility."""
    url = (
        "/api/v1/plan/stream"
        "?origin=DEL&destination=Goa&start_date=2026-11-01&end_date=2026-11-04"
        "&duration_days=3&budget_inr=35000"
    )
    response = client.get(url)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = parse_sse_events(response.text)
    event_names = [e["event"] for e in events]

    assert "planning_started" in event_names
    assert "planning_completed" in event_names


def test_api_post_replan_stream_endpoint(client: TestClient) -> None:
    """Verify POST /api/v1/plan/replan/stream streams re-planning milestones."""
    # First plan synchronously to obtain a base itinerary
    plan_resp = client.post(
        "/api/v1/plan",
        json={
            "origin": "DEL",
            "destinations": ["Goa"],
            "start_date": "2026-11-01",
            "end_date": "2026-11-04",
            "duration_days": 3,
            "budget_inr": 35000.0,
        },
    )
    assert plan_resp.status_code == 200
    itinerary = plan_resp.json()["itinerary"]

    # Submit re-planning decision via SSE
    replan_payload = {
        "proposal_type": "INCREASE_BUDGET",
        "target_value": 115000.0,
        "itinerary": itinerary,
    }
    response = client.post("/api/v1/plan/replan/stream", json=replan_payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = parse_sse_events(response.text)
    event_names = [e["event"] for e in events]

    assert "planning_started" in event_names
    assert "budget_calculated" in event_names
    assert "planning_completed" in event_names

    completed = next(e for e in events if e["event"] == "planning_completed")
    data = json.loads(completed["data"])
    assert data["data"]["replan_summary"]["proposal_type"] == "INCREASE_BUDGET"


def test_api_post_plan_stream_validation_error(client: TestClient) -> None:
    """Verify POST /api/v1/plan/stream returns 422 for unparseable input."""
    response = client.post("/api/v1/plan/stream", json={"origin": "DEL"})
    assert response.status_code == 422


def test_api_post_replan_stream_missing_context(client: TestClient) -> None:
    """Verify POST /api/v1/plan/replan/stream returns 400 when missing itinerary and context."""
    response = client.post(
        "/api/v1/plan/replan/stream",
        json={"proposal_type": "INCREASE_BUDGET", "target_value": 50000.0},
    )
    assert response.status_code == 400
    assert "Either 'itinerary' or 'trip_context' must be provided" in response.json()["detail"]


def test_summarize_helper_functions_empty_inputs() -> None:
    """Verify summary helper functions handle None and empty outputs gracefully."""
    assert _summarize_intake_output({})["travel_scope"] == "DOMESTIC"
    assert _summarize_date_output({})["mode"] == "EXACT"
    assert _summarize_visa_output({})["status"] == "Visa evaluation not required"
    assert _summarize_logistics_output({}) == {}
    assert _summarize_experience_output({}) == {}
    assert _summarize_budget_output({}) == {}
    assert _summarize_optimizer_output({}) == {}
