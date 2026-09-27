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


def test_aviationstack_search_success(monkeypatch):
    """Test live flight lookup via Aviationstack API mock."""
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.setenv("AVIATIONSTACK_API_KEY", "test-aviation-key")
    clear_transport_cache()

    mock_aviation_data = {
        "pagination": {"limit": 5, "offset": 0, "count": 2, "total": 2},
        "data": [
            {
                "flight_date": "2026-10-15",
                "flight_status": "scheduled",
                "departure": {
                    "airport": "Indira Gandhi International",
                    "iata": "DEL",
                    "scheduled": "2026-10-15T09:30:00+00:00",
                },
                "arrival": {
                    "airport": "Chhatrapati Shivaji International",
                    "iata": "BOM",
                    "scheduled": "2026-10-15T11:45:00+00:00",
                },
                "airline": {"name": "IndiGo", "iata": "6E"},
                "flight": {"number": "395", "iata": "6E395"},
            },
            {
                "flight_date": "2026-10-15",
                "flight_status": "scheduled",
                "departure": {
                    "airport": "Indira Gandhi International",
                    "iata": "DEL",
                    "scheduled": "2026-10-15T14:00:00+00:00",
                },
                "arrival": {
                    "airport": "Chhatrapati Shivaji International",
                    "iata": "BOM",
                    "scheduled": "2026-10-15T16:10:00+00:00",
                },
                "airline": {"name": "Air India", "iata": "AI"},
                "flight": {"number": "805", "iata": "AI805"},
            },
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_aviation_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = search_transport("DEL", "BOM", travel_date="2026-10-15", mode="FLIGHT")

        assert res.provider_used == "aviationstack"
        assert res.is_fallback is True
        assert res.is_estimated is True
        assert len(res.options) == 2
        assert res.options[0].carrier == "IndiGo"
        assert res.options[0].transport_code == "6E395"
        assert res.options[0].departure_time == "09:30"
        assert res.options[0].arrival_time == "11:45"
        assert res.options[0].duration_minutes == 135
        assert res.options[1].carrier == "Air India"
        assert res.options[1].transport_code == "AI805"


def test_aviationstack_missing_key_falls_back(monkeypatch):
    """Test that missing AVIATIONSTACK_API_KEY gracefully cascades without crashing."""
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)
    clear_transport_cache()

    with patch("src.tools.transport.search_web", return_value=None):
        res = search_transport("DEL", "BOM", travel_date="2026-10-15", mode="FLIGHT")
        assert res.provider_used == "physics-heuristic"


# ---------------------------------------------------------------------------
# SerpApi Google Flights Tests
# ---------------------------------------------------------------------------


def test_serpapi_flights_success(monkeypatch):
    """Test successful live Tier-0 SerpApi Google Flights API call via mock HTTP."""
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)
    monkeypatch.setenv("SERPAPI_KEY", "serp-mock-key-123")
    clear_transport_cache()

    mock_serp_data = {
        "best_flights": [
            {
                "flights": [
                    {
                        "airline": "IndiGo",
                        "flight_number": "6E202",
                        "departure_airport": {"time": "2026-10-15 07:15"},
                        "arrival_airport": {"time": "2026-10-15 09:25"},
                    }
                ],
                "total_duration": 130,
                "price": 5800.0,
            }
        ],
        "other_flights": [
            {
                "flights": [
                    {
                        "airline": "Air India",
                        "flight_number": "AI805",
                        "departure_airport": {"time": "2026-10-15 14:00"},
                        "arrival_airport": {"time": "2026-10-15 16:10"},
                    }
                ],
                "total_duration": 130,
                "price": 6200.0,
            }
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_serp_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = search_transport("DEL", "BOM", travel_date="2026-10-15", mode="FLIGHT")

    assert res.provider_used == "serpapi-google-flights"
    assert res.is_fallback is False
    assert res.is_estimated is False
    assert len(res.options) == 2
    assert res.options[0].carrier == "IndiGo"
    assert res.options[0].transport_code == "6E202"
    assert res.options[0].departure_time == "07:15"
    assert res.options[0].arrival_time == "09:25"
    assert res.options[0].price_inr == 5800.0
    assert res.options[1].carrier == "Air India"
    assert res.options[1].transport_code == "AI805"


def test_serpapi_flights_missing_key_falls_through(monkeypatch):
    """Test that missing SERPAPI_KEY gracefully skips SerpApi and uses next provider."""
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-mock-key-123")
    clear_transport_cache()

    mock_sky_data = {
        "data": {
            "itineraries": [
                {
                    "price": {"raw": 5500.0},
                    "legs": [
                        {
                            "durationInMinutes": 120,
                            "departure": "06:00",
                            "arrival": "08:00",
                            "carriers": {"marketing": [{"name": "IndiGo"}]},
                            "segments": [{"flightNumber": "6E-100"}],
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

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = search_transport("DEL", "BOM", travel_date="2026-10-15", mode="FLIGHT")

    # SerpApi was skipped (no key), Sky Scraper succeeded
    assert res.provider_used == "sky-scraper"


def test_serpapi_flights_empty_result_cascades(monkeypatch):
    """Test that an empty SerpApi response falls through to next provider in cascade."""
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)
    monkeypatch.setenv("SERPAPI_KEY", "serp-mock-key-123")
    clear_transport_cache()

    # SerpApi returns 200 but no flight groups
    mock_serp_empty = {"best_flights": [], "other_flights": []}
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_serp_empty).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        with patch("src.tools.transport.search_web", return_value=None):
            res = search_transport("DEL", "BOM", travel_date="2026-10-15", mode="FLIGHT")

    # Cascades to physics heuristic after all APIs fail
    assert res.provider_used == "physics-heuristic"


# ---------------------------------------------------------------------------
# Seasonal Multiplier Tests
# ---------------------------------------------------------------------------


def test_seasonal_multiplier_peak_months():
    """Test that peak months return a 1.35 multiplier."""
    from src.tools.transport import _get_seasonal_multiplier

    # Jan, Apr, May, Oct, Dec are peak
    for month in ("2026-01-15", "2026-04-01", "2026-05-20", "2026-10-10", "2026-12-25"):
        mult = _get_seasonal_multiplier(month)
        assert mult == 1.35, f"Expected 1.35 for {month}, got {mult}"


def test_seasonal_multiplier_shoulder_months():
    """Test that shoulder months return a 1.15 multiplier."""
    from src.tools.transport import _get_seasonal_multiplier

    # Mar, Jun, Sep, Nov are shoulder
    for month in ("2026-03-10", "2026-06-05", "2026-09-18", "2026-11-22"):
        mult = _get_seasonal_multiplier(month)
        assert mult == 1.15, f"Expected 1.15 for {month}, got {mult}"


def test_seasonal_multiplier_offpeak_months():
    """Test that off-peak months return a 1.00 multiplier."""
    from src.tools.transport import _get_seasonal_multiplier

    # Feb, Jul, Aug are off-peak
    for month in ("2026-02-14", "2026-07-04", "2026-08-30"):
        mult = _get_seasonal_multiplier(month)
        assert mult == 1.00, f"Expected 1.00 for {month}, got {mult}"


def test_seasonal_multiplier_invalid_date_returns_one():
    """Test that a malformed date string returns a safe default of 1.0."""
    from src.tools.transport import _get_seasonal_multiplier

    assert _get_seasonal_multiplier("") == 1.0
    assert _get_seasonal_multiplier("invalid-date") == 1.0
    assert _get_seasonal_multiplier("2026") == 1.0


def test_physics_heuristic_applies_seasonal_multiplier(monkeypatch):
    """Test that the physics engine applies the seasonal multiplier to estimated fares.

    Patches the haversine helper to return a large distance (3000km) so the computed
    fare is well above the ₹2800 minimum floor in both peak and off-peak months,
    making the seasonal difference numerically detectable.
    """
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    clear_transport_cache()

    # Patch haversine to return 3000km so physics fare = 3000 * 5.80 * mult = 17400 / 18630
    with patch("src.tools.transport._haversine_distance_km", return_value=3000.0):
        with patch("src.tools.transport.search_web", return_value=None):
            # October is peak (1.35 multiplier): 3000 * 5.80 * 1.35 = 23490
            res_peak = search_transport("DEL", "BOM", travel_date="2026-10-15", mode="FLIGHT")
            clear_transport_cache()
            # February is off-peak (1.00 multiplier): 3000 * 5.80 * 1.00 = 17400
            res_offpeak = search_transport("DEL", "BOM", travel_date="2026-02-15", mode="FLIGHT")

    peak_flight = next(o for o in res_peak.options if o.mode == "FLIGHT")
    offpeak_flight = next(o for o in res_offpeak.options if o.mode == "FLIGHT")

    # Peak fares must be strictly higher than off-peak fares (same route, different multiplier)
    assert peak_flight.price_inr > offpeak_flight.price_inr, (
        f"Expected peak {peak_flight.price_inr} > off-peak {offpeak_flight.price_inr}"
    )
    # Verify the ratio is approximately correct (1.35 / 1.00 = 35% premium)
    assert abs(peak_flight.price_inr / offpeak_flight.price_inr - 1.35) < 0.01


# ---------------------------------------------------------------------------
# Google Flights Deep Link Tests
# ---------------------------------------------------------------------------


def test_google_flights_deep_link_format():
    """Test that _make_google_flights_deep_link produces a correct Google Travel URL."""
    from src.tools.transport import _make_google_flights_deep_link

    url = _make_google_flights_deep_link("DEL", "BOM", "2026-10-15")
    assert url.startswith("https://www.google.com/travel/flights/search")
    assert "DEL" in url
    assert "BOM" in url


def test_physics_heuristic_flight_has_deep_link(monkeypatch):
    """Test that physics-heuristic FLIGHT segments carry a valid Google Flights deep link."""
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    clear_transport_cache()

    with patch("src.tools.transport.search_web", return_value=None):
        res = search_transport("DEL", "BOM", travel_date="2026-10-15", mode="FLIGHT")

    flight = next(o for o in res.options if o.mode == "FLIGHT")
    assert flight.booking_url is not None
    assert "google.com/travel/flights" in flight.booking_url
    # Must NOT be the old placeholder URL
    assert "safarnama.local" not in flight.booking_url


def test_serpapi_flights_booking_url_is_google_flights(monkeypatch):
    """Test that SerpApi flight segments carry a Google Flights deep link when no book_url."""
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)
    monkeypatch.setenv("SERPAPI_KEY", "serp-mock-key-123")
    clear_transport_cache()

    # SerpApi response with no booking_token or book_url
    mock_serp_data = {
        "best_flights": [
            {
                "flights": [
                    {
                        "airline": "IndiGo",
                        "flight_number": "6E300",
                        "departure_airport": {"time": "2026-10-15 08:00"},
                        "arrival_airport": {"time": "2026-10-15 10:30"},
                    }
                ],
                "total_duration": 150,
                "price": 5200.0,
                # No booking_token or book_url field
            }
        ],
        "other_flights": [],
    }

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(mock_serp_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = search_transport("DEL", "BOM", travel_date="2026-10-15", mode="FLIGHT")

    assert res.provider_used == "serpapi-google-flights"
    flight = res.options[0]
    assert flight.booking_url is not None
    assert "google.com/travel/flights" in flight.booking_url


# ---------------------------------------------------------------------------
# Updated get_transport_status test
# ---------------------------------------------------------------------------


def test_get_transport_status_includes_serpapi(monkeypatch):
    """Test that get_transport_status includes serpapi_configured key."""
    monkeypatch.setenv("SERPAPI_KEY", "test-serp-key")
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapid-key")
    monkeypatch.setenv("AVIATIONSTACK_API_KEY", "test-aviation-key")

    status = get_transport_status()

    assert "serpapi_configured" in status
    assert status["serpapi_configured"] is True
    assert status["rapidapi_configured"] is True
    assert status["aviationstack_configured"] is True
    assert status["transport_rest_available"] is True
    assert status["web_search_available"] is True


def test_get_transport_status_serpapi_fallback_serper_key(monkeypatch):
    """Test that SERPER_API_KEY is accepted as the serpapi credential."""
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.setenv("SERPER_API_KEY", "serper-mock-key")
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("AVIATIONSTACK_API_KEY", raising=False)

    status = get_transport_status()

    assert status["serpapi_configured"] is True
    assert status["rapidapi_configured"] is False
    assert status["aviationstack_configured"] is False
