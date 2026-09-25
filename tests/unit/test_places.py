"""Unit tests for places and dining search tool (src/tools/places.py).

Tests multi-tier places search cascade, provider fallbacks, fixture mode,
category heuristics, in-memory caching, exception handling,
and Pydantic response models.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from src.models.places import PlaceItem, PlacesSearchResult
from src.tools.places import (
    InvalidDestinationError,
    clear_places_cache,
    get_places_status,
    search_places,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Ensure clean cache before and after every test."""
    clear_places_cache()
    yield
    clear_places_cache()


def test_invalid_destination_raises_exception():
    """Test that empty or blank destination string raises InvalidDestinationError."""
    with pytest.raises(InvalidDestinationError, match="Destination location"):
        search_places("")

    with pytest.raises(InvalidDestinationError, match="Destination location"):
        search_places("   ")


def test_fixture_mode_direct():
    """Test that setting use_fixture=True returns fixture results directly."""
    result = search_places("Tokyo", category="ATTRACTION", use_fixture=True)

    assert isinstance(result, PlacesSearchResult)
    assert result.destination == "TOKYO"
    assert result.category_requested == "ATTRACTION"
    assert result.provider_used == "fixture"
    assert result.is_fallback is True
    assert len(result.items) >= 1

    first_item = result.items[0]
    assert isinstance(first_item, PlaceItem)
    assert first_item.category == "ATTRACTION"
    assert first_item.name == "Senso-ji Temple"


def test_category_heuristic_fallback(monkeypatch):
    """Test that missing keys and failed APIs trigger category heuristic baseline."""
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with patch("urllib.request.urlopen", side_effect=ValueError("API Offline")):
        result = search_places("Mumbai", category="ALL")

        assert isinstance(result, PlacesSearchResult)
        assert result.destination == "MUMBAI"
        assert result.provider_used == "category-heuristic"
        assert result.is_estimated is True
        assert len(result.items) >= 2

        categories = [item.category for item in result.items]
        assert "ATTRACTION" in categories
        assert "RESTAURANT" in categories or "CAFE" in categories


def test_serpapi_google_maps_search(monkeypatch):
    """Test successful SerpApi Google Maps API call via mock HTTP."""
    monkeypatch.setenv("SERPAPI_KEY", "serp-mock-key-123")

    mock_serp_data = {
        "local_results": [
            {
                "title": "Ichiran Ramen",
                "type": "Ramen restaurant",
                "rating": 4.6,
                "reviews": 9800,
                "price": "$$",
                "address": "Shinjuku, Tokyo",
                "gps_coordinates": {"latitude": 35.6905, "longitude": 139.7018},
                "open_state": "Open 24 hours",
                "link": "https://maps.google.com/ichiran"
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_serp_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = search_places("Tokyo", category="RESTAURANT")

        assert isinstance(result, PlacesSearchResult)
        assert result.provider_used == "serpapi-google-maps"
        assert result.is_fallback is False
        assert len(result.items) == 1

        item = result.items[0]
        assert item.name == "Ichiran Ramen"
        assert item.category == "RESTAURANT"
        assert item.rating == 4.6


def test_nominatim_osm_search(monkeypatch):
    """Test keyless OpenStreetMap Nominatim places search via mock HTTP."""
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SERPER_API_KEY", raising=False)

    mock_osm_data = [
        {
            "place_id": 901,
            "display_name": "Louvre Museum, Paris, France",
            "lat": "48.8606",
            "lon": "2.3376"
        }
    ]
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_osm_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = search_places("Paris", category="ATTRACTION")

        assert isinstance(result, PlacesSearchResult)
        assert result.provider_used == "nominatim-osm"
        assert result.is_fallback is True
        assert len(result.items) == 1

        item = result.items[0]
        assert item.name == "Louvre Museum"
        assert item.latitude == 48.8606


def test_in_memory_caching():
    """Test that repeated search calls query in-memory cache."""
    res1 = search_places("Tokyo", category="ALL", use_fixture=True)
    res2 = search_places("Tokyo", category="ALL", use_fixture=True)

    assert res1 == res2
    assert res1.timestamp == res2.timestamp


def test_get_places_status():
    """Test retrieving operational status dictionary of places providers."""
    status = get_places_status()
    assert isinstance(status, dict)
    assert "serpapi_configured" in status
    assert "nominatim_available" in status
    assert status["nominatim_available"] is True
    assert status["fixture_available"] is True
