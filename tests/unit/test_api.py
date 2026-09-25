"""Unit tests for Phase 4 — API Layer (FastAPI endpoints, validation & responses)."""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture
def client() -> TestClient:
    """TestClient fixture for FastAPI application testing."""
    return TestClient(app)


def test_root_welcome(client: TestClient) -> None:
    """Verify root endpoint returns welcome payload."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Safarnama API" in data["message"]
    assert data["version"] == "0.1.0"
    assert data["health"] == "/api/v1/health"


def test_health_endpoint(client: TestClient) -> None:
    """Verify health check endpoint returns status ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Safarnama API"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_tools_status_endpoint(client: TestClient) -> None:
    """Verify tools status aggregator endpoint returns capability report."""
    response = client.get("/api/v1/tools/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    tools = data["tools"]
    assert "static_data" in tools
    assert "forex" in tools
    assert "web_search" in tools
    assert "transport" in tools
    assert "hotels" in tools
    assert "places" in tools
    assert "fallback_estimator" in tools
    assert tools["static_data"]["status"] == "available"
    assert tools["forex"]["status"] == "available"


def test_estimate_endpoint_valid(client: TestClient) -> None:
    """Verify estimate endpoint returns valid cost estimate response."""
    payload = {
        "destination": "Japan",
        "category": "hotel",
        "hotel_stars": 4,
        "nights": 3,
        "travelers": 2,
        "budget_tier": "moderate",
    }
    response = client.post("/api/v1/estimate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["destination"].upper() == "JAPAN"
    assert data["category"].lower() == "hotel"
    assert data["estimated_cost_inr"] > 0
    assert data["is_estimated"] is True
    assert "provider" in data
    assert "timestamp" in data


def test_estimate_endpoint_validation_error(client: TestClient) -> None:
    """Verify estimate endpoint returns 422 for invalid request parameters."""
    # Invalid star rating > 5 and empty destination
    payload = {
        "destination": "",
        "category": "hotel",
        "hotel_stars": 10,
    }
    response = client.post("/api/v1/estimate", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["status_code"] == 422
    assert data["error_type"] == "RequestValidationError"
    assert "Validation Error" in data["detail"]


def test_plan_preview_domestic(client: TestClient) -> None:
    """Verify plan preview endpoint returns structured domestic trip preview."""
    payload = {
        "origin": "DEL",
        "destination": "Goa",
        "duration_days": 4,
        "num_travelers": 2,
        "budget_inr": 40000.0,
        "travel_style": "balanced",
    }
    response = client.post("/api/v1/plan/preview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "preview"
    assert data["travel_scope"] == "DOMESTIC"
    assert data["origin_airport"]["iata"] == "DEL"
    assert data["estimated_baseline_cost_inr"] > 0
    assert "budget_variance" in data
    assert data["budget_variance"]["status"] in [
        "UNDER_BUDGET",
        "EXACT",
        "OVER_BUDGET",
    ]


def test_plan_preview_international(client: TestClient) -> None:
    """Verify plan preview endpoint returns structured international trip preview with visa info."""
    payload = {
        "origin": "BOM",
        "destination": "Uzbekistan",
        "duration_days": 5,
        "num_travelers": 1,
        "budget_inr": 80000.0,
        "travel_style": "budget",
    }
    response = client.post("/api/v1/plan/preview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "preview"
    assert data["travel_scope"] == "INTERNATIONAL"
    assert data["origin_airport"]["iata"] == "BOM"
    assert data["destination_country"]["iso2"] == "UZ"
    assert data["visa_summary"] is not None
    assert data["visa_summary"]["destination"] == "Uzbekistan"


def test_plan_preview_validation_error(client: TestClient) -> None:
    """Verify plan preview endpoint returns 422 for negative budget or duration."""
    payload = {
        "origin": "DEL",
        "destination": "France",
        "duration_days": -1,
        "budget_inr": -500.0,
    }
    response = client.post("/api/v1/plan/preview", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["status_code"] == 422
    assert data["error_type"] == "RequestValidationError"


def test_stream_events_endpoint(client: TestClient) -> None:
    """Verify Server-Sent Events (SSE) streaming endpoint."""
    response = client.get("/api/v1/stream/events")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    content = response.text
    assert "data: " in content
    assert "Initiating Safarnama planning engine" in content
    assert "Plan preview generated successfully" in content


def test_cors_middleware_headers(client: TestClient) -> None:
    """Verify CORS headers are present on API responses."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in [
        "*",
        "http://localhost:3000",
    ]
