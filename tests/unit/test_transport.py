"""Unit tests for transport tool (src/tools/transport.py).

Tests multi-tier transport search cascade, provider fallbacks, fixture mode,
distance/speed physics heuristics, in-memory caching, exception handling,
and Pydantic response models.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from src.models.transport import TransportSearchResult, TransportSegment
from src.tools.transport import (
    InvalidLocationError,
    clear_transport_cache,
    get_transport_status,
    search_transport,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Ensure clean cache before and after every test."""
    clear_transport_cache()
    yield
    clear_transport_cache()


def test_invalid_location_raises_exception():
    """Test that empty or blank origin/destination raise InvalidLocationError."""
    with pytest.raises(InvalidLocationError, match="Origin location"):
        search_transport("", "BOM")

    with pytest.raises(InvalidLocationError, match="Destination location"):
        search_transport("DEL", "   ")


def test_fixture_mode_direct():
    """Test that setting use_fixture=True returns fixture results directly."""
    result = search_transport("DEL", "BOM", travel_date="2026-10-15", use_fixture=True)

    assert isinstance(result, TransportSearchResult)
    assert result.origin == "DEL"
    assert result.destination == "BOM"
    assert result.provider_used == "fixture"
    assert result.is_fallback is True
    assert len(result.options) >= 2

    first_opt = result.options[0]
    assert isinstance(first_opt, TransportSegment)
    assert first_opt.mode in ("FLIGHT", "TRAIN", "BUS")
    assert first_opt.price_inr > 0.0


def test_physics_heuristic_fallback(monkeypatch):
    """Test that missing keys and failed APIs trigger physics distance engine."""
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)

    with patch("urllib.request.urlopen", side_effect=OSError("Network down")):
        result = search_transport("DEL", "BOM", travel_date="2026-10-15")

        assert isinstance(result, TransportSearchResult)
        assert result.provider_used == "physics-heuristic"
        assert result.is_estimated is True
        assert len(result.options) >= 2
        assert any(opt.mode == "FLIGHT" for opt in result.options)
        assert any(opt.mode == "TRAIN" for opt in result.options)


def test_sky_scraper_flight_search(monkeypatch):
    """Test successful live Tier 1 Sky Scraper API call via mock HTTP."""
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-mock-key-123")

    mock_sky_data = {
        "data": {
            "itineraries": [
                {
                    "price": {"raw": 5200.0},
                    "legs": [
                        {
                            "durationInMinutes": 130,
                            "departure": "07:15",
                            "arrival": "09:25",
                            "carriers": {"marketing": [{"name": "IndiGo"}]},
                            "segments": [{"flightNumber": "6E-501"}],
                        }
                    ],
                }
            ]
        }
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_sky_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        result = search_transport("DEL", "BOM", travel_date="2026-10-15", mode="FLIGHT")

        assert result.provider_used == "sky-scraper"
        assert result.is_fallback is False
        assert len(result.options) == 1
        assert result.options[0].carrier == "IndiGo"
        assert result.options[0].price_inr == 5200.0

        # Verify request headers
        req = mock_urlopen.call_args[0][0]
        assert req.headers["X-rapidapi-key"] == "rapid-mock-key-123"
        assert req.headers["X-rapidapi-host"] == "sky-scrapper.p.rapidapi.com"


def test_indian_railways_search(monkeypatch):
    """Test successful live Indian Railways IRCTC API call via mock HTTP."""
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-mock-key-123")

    # Sky Scraper returns empty, Indian Railways succeeds
    mock_sky_empty = MagicMock()
    mock_sky_empty.status = 200
    mock_sky_empty.read.return_value = json.dumps({}).encode("utf-8")
    mock_sky_empty.__enter__.return_value = mock_sky_empty

    mock_irctc_data = {
        "data": [
            {
                "trainName": "Vande Bharat Express",
                "trainNumber": "20902",
                "departureTime": "15:00",
                "arrivalTime": "23:25",
                "durationMinutes": 505,
                "fare": 2850.0,
                "preferredClass": "CC",
            }
        ]
    }
    mock_irctc_resp = MagicMock()
    mock_irctc_resp.status = 200
    mock_irctc_resp.read.return_value = json.dumps(mock_irctc_data).encode("utf-8")
    mock_irctc_resp.__enter__.return_value = mock_irctc_resp

    def side_effect(req, timeout=8.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "sky-scrapper" in url:
            return mock_sky_empty
        if "irctc" in url:
            return mock_irctc_resp
        raise ValueError(f"Unexpected URL: {url}")

    with patch("urllib.request.urlopen", side_effect=side_effect):
        result = search_transport("NDLS", "MMCT", travel_date="2026-10-15", mode="TRAIN")

        assert result.provider_used in ("irctc1", "indian-railway-irctc")
        assert result.is_fallback is False
        assert len(result.options) == 1
        assert result.options[0].carrier == "Vande Bharat Express"
        assert result.options[0].price_inr == 2850.0


def test_indian_railways_duration_parsing_error(monkeypatch):
    """Test Indian Railways search falls back to 480 minutes when duration string is malformed."""
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-mock-key-123")

    mock_sky_empty = MagicMock()
    mock_sky_empty.status = 200
    mock_sky_empty.read.return_value = json.dumps({}).encode("utf-8")
    mock_sky_empty.__enter__.return_value = mock_sky_empty

    mock_irctc_data = {
        "data": [
            {
                "trainName": "Express Train",
                "trainNumber": "12345",
                "departureTime": "06:00",
                "arrivalTime": "14:00",
                "duration": "invalid:time",
                "fare": 500.0,
            }
        ]
    }
    mock_irctc_resp = MagicMock()
    mock_irctc_resp.status = 200
    mock_irctc_resp.read.return_value = json.dumps(mock_irctc_data).encode("utf-8")
    mock_irctc_resp.__enter__.return_value = mock_irctc_resp

    def side_effect(req, timeout=8.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "sky-scrapper" in url:
            return mock_sky_empty
        if "irctc" in url:
            return mock_irctc_resp
        raise ValueError(f"Unexpected URL: {url}")

    with patch("urllib.request.urlopen", side_effect=side_effect):
        result = search_transport("NDLS", "MMCT", travel_date="2026-10-15", mode="TRAIN")

        assert result.provider_used == "irctc1"
        assert len(result.options) == 1
        assert result.options[0].duration_minutes == 480


def test_transport_rest_search(monkeypatch):
    """Test live European train search via transport.rest open access API."""
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)

    mock_db_data = {
        "journeys": [
            {
                "departure": "2026-10-15T10:13:00+02:00",
                "arrival": "2026-10-15T11:30:00+01:00",
                "duration": 8220,
                "price": {"amount": 75.0, "currency": "EUR"},
                "legs": [
                    {
                        "tripId": "EUR-9023",
                        "line": {"name": "Eurostar"},
                    }
                ],
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_db_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = search_transport("PARIS", "LONDON", travel_date="2026-10-15", mode="TRAIN")

        assert result.provider_used == "transport.rest"
        assert result.is_fallback is True
        assert len(result.options) == 1
        assert result.options[0].carrier == "Eurostar"
        assert result.options[0].price_inr > 6000.0


def test_in_memory_cache_behavior():
    """Test that identical search queries hit the in-memory cache."""
    res1 = search_transport("DEL", "BOM", travel_date="2026-10-15", use_fixture=True)
    assert res1.provider_used == "fixture"

    res2 = search_transport("DEL", "BOM", travel_date="2026-10-15", use_fixture=True)
    assert res2 is res1

    clear_transport_cache()
    res3 = search_transport("DEL", "BOM", travel_date="2026-10-15", use_fixture=True)
    assert res3 is not res1


def test_get_transport_status(monkeypatch):
    """Test operational status reporting helper."""
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    monkeypatch.setenv("AVIATIONSTACK_API_KEY", "aviation-test")

    status = get_transport_status()

    assert status["rapidapi_configured"] is True
    assert status["aviationstack_configured"] is True
    assert status["transport_rest_available"] is True
    assert status["web_search_available"] is True
    assert status["fixture_available"] is True
