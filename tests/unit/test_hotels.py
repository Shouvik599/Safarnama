"""Unit tests for hotel search tool (src/tools/hotels.py).

Tests multi-tier hotel search cascade, provider fallbacks, fixture mode,
location heuristics, in-memory caching, exception handling,
and Pydantic response models.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from src.models.hotels import HotelOption, HotelSearchResult
from src.tools.hotels import (
    InvalidDestinationError,
    clear_hotels_cache,
    get_hotels_status,
    search_hotels,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Ensure clean cache before and after every test."""
    clear_hotels_cache()
    yield
    clear_hotels_cache()


def test_invalid_destination_raises_exception():
    """Test that empty or blank destination string raises InvalidDestinationError."""
    with pytest.raises(InvalidDestinationError, match="Destination location"):
        search_hotels("")

    with pytest.raises(InvalidDestinationError, match="Destination location"):
        search_hotels("   ")


def test_fixture_mode_direct():
    """Test that setting use_fixture=True returns fixture results directly."""
    result = search_hotels("Tokyo", checkin_date="2026-10-15", nights=2, use_fixture=True)

    assert isinstance(result, HotelSearchResult)
    assert result.destination == "TOKYO"
    assert result.nights == 2
    assert result.provider_used == "fixture"
    assert result.is_fallback is True
    assert len(result.options) >= 2

    first_opt = result.options[0]
    assert isinstance(first_opt, HotelOption)
    assert first_opt.price_per_night_inr > 0.0
    assert first_opt.total_price_inr == round(first_opt.price_per_night_inr * 2, 2)


def test_location_heuristic_fallback(monkeypatch):
    """Test that missing keys and failed APIs trigger location heuristic baseline."""
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    # Patch urllib to fail
    with patch("urllib.request.urlopen", side_effect=ValueError("API Offline")):
        result = search_hotels("Mumbai", checkin_date="2026-10-15", nights=3)

        assert isinstance(result, HotelSearchResult)
        assert result.destination == "MUMBAI"
        assert result.nights == 3
        assert result.provider_used == "location-heuristic"
        assert result.is_estimated is True
        assert len(result.options) >= 2

        opt = result.options[0]
        assert opt.total_price_inr == round(opt.price_per_night_inr * 3, 2)


def test_serpapi_google_hotels_search(monkeypatch):
    """Test successful SerpApi Google Hotels API call via mock HTTP."""
    monkeypatch.setenv("SERPAPI_KEY", "serp-mock-key-123")

    mock_serp_data = {
        "properties": [
            {
                "name": "Tokyo Grand Palace",
                "hotel_class": "4-star hotel",
                "overall_rating": 8.8,
                "reviews": 1420,
                "rate_per_night": {"extracted_lowest": 12500.0, "lowest": "₹12,500"},
                "gps_coordinates": {"latitude": 35.6895, "longitude": 139.6917},
                "amenities": ["Free Wi-Fi", "Pool", "Restaurant"],
                "images": [{"thumbnail": "https://images.local/thumb.jpg"}],
                "deal_url": "https://booking.com/hotel/tokyo-grand",
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_serp_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = search_hotels("Tokyo", checkin_date="2026-10-15", nights=2)

        assert isinstance(result, HotelSearchResult)
        assert result.provider_used == "serpapi-google-hotels"
        assert result.is_fallback is False
        assert len(result.options) == 1

        opt = result.options[0]
        assert opt.name == "Tokyo Grand Palace"
        assert opt.price_per_night_inr == 12500.0
        assert opt.total_price_inr == 25000.0
        assert opt.star_rating == 4


def test_booking_com_search(monkeypatch):
    """Test successful Booking.com API call via mock HTTP."""
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-mock-key-123")

    mock_loc_data = [{"dest_id": "1001", "dest_type": "city", "name": "Paris"}]
    mock_search_data = {
        "result": [
            {
                "hotel_id": "9991",
                "hotel_name": "Novotel Paris",
                "class": 4,
                "review_score": 8.6,
                "review_nr": 850,
                "min_total_price": 16000.0,
                "address": "Paris City Center",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "url": "https://booking.com/paris-novotel",
            }
        ]
    }

    mock_loc_resp = MagicMock()
    mock_loc_resp.status = 200
    mock_loc_resp.read.return_value = json.dumps(mock_loc_data).encode("utf-8")
    mock_loc_resp.__enter__.return_value = mock_loc_resp

    mock_s_resp = MagicMock()
    mock_s_resp.status = 200
    mock_s_resp.read.return_value = json.dumps(mock_search_data).encode("utf-8")
    mock_s_resp.__enter__.return_value = mock_s_resp

    def side_effect(req, timeout=12.0):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "locations" in url:
            return mock_loc_resp
        return mock_s_resp

    with patch("urllib.request.urlopen", side_effect=side_effect):
        result = search_hotels("Paris", checkin_date="2026-10-15", nights=2)

        assert isinstance(result, HotelSearchResult)
        assert result.provider_used == "booking-com"
        assert result.is_fallback is False
        assert len(result.options) == 1

        opt = result.options[0]
        assert opt.name == "Novotel Paris"
        assert opt.price_per_night_inr == 8000.0
        assert opt.total_price_inr == 16000.0


def test_nominatim_osm_search(monkeypatch):
    """Test live keyless OpenStreetMap Nominatim hotel search via mock HTTP."""
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)

    mock_osm_data = [
        {
            "place_id": 501,
            "display_name": "Hotel Metropolis, Rome, Italy",
            "lat": "41.9028",
            "lon": "12.4964",
        }
    ]
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_osm_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = search_hotels("Rome", checkin_date="2026-10-15", nights=1)

        assert isinstance(result, HotelSearchResult)
        assert result.provider_used == "nominatim-osm"
        assert result.is_fallback is True
        assert len(result.options) == 1

        opt = result.options[0]
        assert opt.name == "Hotel Metropolis"
        assert opt.latitude == 41.9028
        assert opt.longitude == 12.4964


def test_in_memory_caching():
    """Test that repeated search calls query in-memory cache."""
    res1 = search_hotels("Tokyo", checkin_date="2026-10-15", nights=2, use_fixture=True)
    res2 = search_hotels("Tokyo", checkin_date="2026-10-15", nights=2, use_fixture=True)

    assert res1 == res2
    assert res1.timestamp == res2.timestamp


def test_get_hotels_status():
    """Test retrieving operational status dictionary of hotel providers."""
    status = get_hotels_status()
    assert isinstance(status, dict)
    assert "serpapi_configured" in status
    assert "rapidapi_configured" in status
    assert "nominatim_available" in status
    assert status["nominatim_available"] is True
    assert status["fixture_available"] is True


def test_date_parsing_fallback_invalid_checkin_no_checkout():
    """Test date parsing fallback when checkin_date is invalid and checkout_date is not provided."""
    result = search_hotels("Tokyo", checkin_date="invalid-date-format", nights=3, use_fixture=True)

    assert isinstance(result, HotelSearchResult)
    assert result.nights == 3
    assert result.checkout_date is not None
    assert len(result.options) >= 1


def test_date_parsing_fallback_invalid_dates_with_checkout():
    """Test date parsing fallback when checkin/checkout date is invalid but checkout is given."""
    # Test invalid checkout_date string
    result1 = search_hotels(
        "Tokyo", checkin_date="2026-10-15", checkout_date="invalid-date", nights=3, use_fixture=True
    )
    assert isinstance(result1, HotelSearchResult)
    assert result1.nights == 3

    # Test invalid checkin_date string with a checkout_date string
    result2 = search_hotels(
        "Tokyo", checkin_date="invalid-date", checkout_date="2026-10-20", nights=4, use_fixture=True
    )
    assert isinstance(result2, HotelSearchResult)
    assert result2.nights == 4
