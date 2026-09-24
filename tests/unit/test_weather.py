"""Unit tests for deterministic weather forecasting tool (src/tools/weather.py)."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from src.models.weather import DailyWeatherForecast, WeatherForecastResult
from src.tools.weather import (
    InvalidCoordinatesError,
    InvalidDateRangeError,
    _generate_climate_baseline_day,
    _map_owm_id_to_wmo,
    _map_wttr_code_to_wmo,
    clear_weather_cache,
    generate_weather_summary,
    get_weather_forecast,
    is_outdoor_friendly,
)


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    """Ensure in-memory cache is pristine for every test."""
    clear_weather_cache()


# ---------------------------------------------------------------------------
# Tier 0: Fixture Mode
# ---------------------------------------------------------------------------


def test_fixture_mode_returns_mock_forecast() -> None:
    """Fixture mode returns deterministic forecasts without network calls."""
    res = get_weather_forecast(
        latitude=35.6762,
        longitude=139.6503,
        start_date="2026-10-01",
        end_date="2026-10-07",
        use_fixture=True,
        destination="Tokyo, Japan",
    )

    assert isinstance(res, WeatherForecastResult)
    assert res.provider == "fixture"
    assert res.is_estimated is False
    assert res.destination == "Tokyo, Japan"
    assert res.start_date == "2026-10-01"
    assert res.end_date == "2026-10-07"
    assert len(res.daily_forecasts) == 7

    day0 = res.daily_forecasts[0]
    assert day0.date == "2026-10-01"
    assert day0.temp_max_c == 28.5
    assert day0.precipitation_probability == 10
    assert day0.weather_code == 1
    assert day0.condition == "Mainly clear"
    assert day0.is_outdoor_friendly is True

    # Check rainy day in fixture
    day2 = res.daily_forecasts[2]
    assert day2.precipitation_probability == 85
    assert day2.weather_code == 63
    assert day2.condition == "Moderate rain"
    assert day2.is_outdoor_friendly is False


def test_fixture_mode_honors_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """SAFARNAMA_TEST_MODE forces fixture mode automatically."""
    monkeypatch.setenv("SAFARNAMA_TEST_MODE", "1")
    res = get_weather_forecast(latitude=48.8566, longitude=2.3522, days=3)
    assert res.provider == "fixture"
    assert len(res.daily_forecasts) == 3


# ---------------------------------------------------------------------------
# Tier 1: Open-Meteo
# ---------------------------------------------------------------------------


def test_open_meteo_success() -> None:
    """Open-Meteo tier succeeds and parses forecast metrics cleanly."""
    mock_daily = {
        "2026-10-01": DailyWeatherForecast(
            date="2026-10-01",
            temp_max_c=25.0,
            temp_min_c=15.0,
            temp_avg_c=20.0,
            precipitation_probability=15,
            precipitation_mm=0.0,
            weather_code=0,
            condition="Clear sky",
            is_outdoor_friendly=True,
        ),
        "2026-10-02": DailyWeatherForecast(
            date="2026-10-02",
            temp_max_c=22.0,
            temp_min_c=14.0,
            temp_avg_c=18.0,
            precipitation_probability=65,
            precipitation_mm=8.5,
            weather_code=61,
            condition="Slight rain",
            is_outdoor_friendly=False,
        ),
    }

    with patch("src.tools.weather._fetch_open_meteo", return_value=mock_daily):
        res = get_weather_forecast(
            latitude=28.6139,
            longitude=77.2090,
            start_date="2026-10-01",
            end_date="2026-10-02",
            use_fixture=False,
        )
        assert res.provider == "open-meteo"
        assert res.is_estimated is False
        assert len(res.daily_forecasts) == 2
        assert res.daily_forecasts[0].condition == "Clear sky"
        assert res.daily_forecasts[1].condition == "Slight rain"
        assert res.daily_forecasts[1].is_outdoor_friendly is False


# ---------------------------------------------------------------------------
# Tier 2: wttr.in Fallback
# ---------------------------------------------------------------------------


def test_fallback_to_wttr_when_open_meteo_fails() -> None:
    """When Open-Meteo encounters an error, wttr.in provides the forecast."""
    mock_wttr = {
        "2026-10-01": DailyWeatherForecast(
            date="2026-10-01",
            temp_max_c=27.0,
            temp_min_c=18.0,
            temp_avg_c=22.5,
            precipitation_probability=20,
            precipitation_mm=0.0,
            weather_code=2,
            condition="Partly cloudy",
            is_outdoor_friendly=True,
        )
    }

    with (
        patch("src.tools.weather._fetch_open_meteo", side_effect=RuntimeError("Rate limited")),
        patch("src.tools.weather._fetch_wttr_in", return_value=mock_wttr),
    ):
        res = get_weather_forecast(
            latitude=13.7563,
            longitude=100.5018,
            start_date="2026-10-01",
            end_date="2026-10-01",
            use_fixture=False,
        )
        assert res.provider == "wttr.in"
        assert res.is_estimated is False
        assert len(res.daily_forecasts) == 1
        assert res.daily_forecasts[0].weather_code == 2


# ---------------------------------------------------------------------------
# Tier 3: OpenWeatherMap Fallback
# ---------------------------------------------------------------------------


def test_fallback_to_openweathermap_when_open_meteo_and_wttr_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When Open-Meteo and wttr.in fail, OpenWeatherMap is queried using API key."""
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "test_mock_key_123")
    mock_owm = {
        "2026-10-01": DailyWeatherForecast(
            date="2026-10-01",
            temp_max_c=31.0,
            temp_min_c=22.0,
            temp_avg_c=26.5,
            precipitation_probability=10,
            precipitation_mm=0.0,
            weather_code=0,
            condition="Clear sky",
            is_outdoor_friendly=True,
        )
    }

    with (
        patch("src.tools.weather._fetch_open_meteo", side_effect=RuntimeError("503 Gateway")),
        patch("src.tools.weather._fetch_wttr_in", side_effect=RuntimeError("Timeout")),
        patch("src.tools.weather._fetch_openweathermap", return_value=mock_owm),
    ):
        res = get_weather_forecast(
            latitude=25.2048,
            longitude=55.2708,
            start_date="2026-10-01",
            end_date="2026-10-01",
            use_fixture=False,
        )
        assert res.provider == "openweathermap"
        assert res.is_estimated is False
        assert res.daily_forecasts[0].temp_max_c == 31.0


# ---------------------------------------------------------------------------
# Tier 4: Offline Climate Baseline Fallback
# ---------------------------------------------------------------------------


def test_fallback_to_climate_baseline_when_all_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """When all live endpoints fail, offline climate baseline estimates are returned."""
    monkeypatch.delenv("OPENWEATHERMAP_API_KEY", raising=False)
    with (
        patch("src.tools.weather._fetch_open_meteo", side_effect=Exception("No internet")),
        patch("src.tools.weather._fetch_wttr_in", side_effect=Exception("No internet")),
    ):
        res = get_weather_forecast(
            latitude=41.2995,
            longitude=69.2401,
            start_date="2026-10-01",
            end_date="2026-10-03",
            use_fixture=False,
            destination="Tashkent, Uzbekistan",
        )
        assert res.provider == "climate-baseline"
        assert res.is_estimated is True
        assert len(res.daily_forecasts) == 3
        for day in res.daily_forecasts:
            assert isinstance(day.temp_max_c, float)
            assert isinstance(day.temp_min_c, float)
            assert day.temp_max_c > day.temp_min_c
            assert 0 <= day.precipitation_probability <= 100


# ---------------------------------------------------------------------------
# In-Memory Cache
# ---------------------------------------------------------------------------


def test_in_memory_cache_prevents_duplicate_calls() -> None:
    """Repeated calls for the same coordinates and dates use the memory cache."""
    mock_fn = MagicMock(
        return_value={
            "2026-10-01": DailyWeatherForecast(
                date="2026-10-01",
                temp_max_c=25.0,
                temp_min_c=18.0,
                temp_avg_c=21.5,
                precipitation_probability=10,
                precipitation_mm=0.0,
                weather_code=0,
                condition="Clear sky",
                is_outdoor_friendly=True,
            )
        }
    )

    with patch("src.tools.weather._fetch_open_meteo", mock_fn):
        res1 = get_weather_forecast(
            latitude=35.0,
            longitude=139.0,
            start_date="2026-10-01",
            end_date="2026-10-01",
            use_fixture=False,
        )
        res2 = get_weather_forecast(
            latitude=35.0,
            longitude=139.0,
            start_date="2026-10-01",
            end_date="2026-10-01",
            use_fixture=False,
        )
        assert mock_fn.call_count == 1
        assert res1.timestamp == res2.timestamp


# ---------------------------------------------------------------------------
# Input Validation & Date Ranges
# ---------------------------------------------------------------------------


def test_invalid_latitude_raises_error() -> None:
    """Latitudes outside [-90, 90] trigger InvalidCoordinatesError."""
    with pytest.raises(InvalidCoordinatesError, match="Latitude"):
        get_weather_forecast(latitude=95.0, longitude=0.0)


def test_invalid_longitude_raises_error() -> None:
    """Longitudes outside [-180, 180] trigger InvalidCoordinatesError."""
    with pytest.raises(InvalidCoordinatesError, match="Longitude"):
        get_weather_forecast(latitude=0.0, longitude=195.0)


def test_end_date_before_start_date_raises_error() -> None:
    """End date earlier than start date triggers InvalidDateRangeError."""
    with pytest.raises(InvalidDateRangeError, match="cannot be before"):
        get_weather_forecast(
            latitude=0.0,
            longitude=0.0,
            start_date="2026-10-10",
            end_date="2026-10-05",
        )


def test_invalid_date_format_raises_error() -> None:
    """Non-ISO date string triggers InvalidDateRangeError."""
    with pytest.raises(InvalidDateRangeError, match="Invalid start_date"):
        get_weather_forecast(latitude=0.0, longitude=0.0, start_date="October 1st")


def test_date_objects_handled_properly() -> None:
    """datetime.date objects are accepted in place of strings."""
    today = date.today()
    in_three_days = today + timedelta(days=2)
    res = get_weather_forecast(
        latitude=0.0,
        longitude=0.0,
        start_date=today,
        end_date=in_three_days,
        use_fixture=True,
    )
    assert res.start_date == today.isoformat()
    assert res.end_date == in_three_days.isoformat()
    assert len(res.daily_forecasts) == 3


def test_days_parameter_defaults() -> None:
    """When end_date is omitted, days parameter governs forecast length."""
    res = get_weather_forecast(
        latitude=0.0,
        longitude=0.0,
        start_date="2026-11-01",
        days=5,
        use_fixture=True,
    )
    assert len(res.daily_forecasts) == 5
    assert res.end_date == "2026-11-05"


# ---------------------------------------------------------------------------
# Code Mappings & Utilities
# ---------------------------------------------------------------------------


def test_is_outdoor_friendly_logic() -> None:
    """Outdoor friendliness respects both rain probability and severe codes."""
    assert is_outdoor_friendly(precipitation_probability=10, weather_code=0) is True
    assert is_outdoor_friendly(precipitation_probability=49, weather_code=2) is True
    # Probability >= 50
    assert is_outdoor_friendly(precipitation_probability=50, weather_code=1) is False
    assert is_outdoor_friendly(precipitation_probability=75, weather_code=2) is False
    # Severe codes even if probability low
    assert is_outdoor_friendly(precipitation_probability=30, weather_code=95) is False
    assert is_outdoor_friendly(precipitation_probability=20, weather_code=65) is False


def test_generate_weather_summary() -> None:
    """generate_weather_summary computes expected range and outdoor advisories."""
    forecasts = [
        DailyWeatherForecast(
            date="2026-10-01",
            temp_max_c=28.0,
            temp_min_c=18.0,
            temp_avg_c=23.0,
            precipitation_probability=10,
            precipitation_mm=0.0,
            weather_code=0,
            condition="Clear sky",
            is_outdoor_friendly=True,
        ),
        DailyWeatherForecast(
            date="2026-10-02",
            temp_max_c=24.0,
            temp_min_c=16.0,
            temp_avg_c=20.0,
            precipitation_probability=80,
            precipitation_mm=12.0,
            weather_code=63,
            condition="Moderate rain",
            is_outdoor_friendly=False,
        ),
    ]
    summary = generate_weather_summary(forecasts)
    assert "Expected temperatures between 17.0°C and 26.0°C" in summary
    assert "Precipitation or rain showers expected on 1 of 2 days" in summary


def test_wmo_code_mappings() -> None:
    """Mapping functions map diverse third-party weather identifiers to standard WMO codes."""
    wmo_code, desc = _map_wttr_code_to_wmo("113")
    assert wmo_code == 0
    assert desc == "Clear sky"

    wmo_code, desc = _map_wttr_code_to_wmo("389")
    assert wmo_code == 95
    assert desc == "Thunderstorm"

    owm_code, o_desc = _map_owm_id_to_wmo(800)
    assert owm_code == 0
    assert o_desc == "Clear sky"

    owm_code, o_desc = _map_owm_id_to_wmo(501)
    assert owm_code == 63
    assert o_desc == "Moderate rain"


def test_climate_baseline_seasons() -> None:
    """Climate baseline respects hemispheres and summer/winter extremes."""
    # Tokyo (35° N) in July (summer) vs January (winter)
    tokyo_summer = _generate_climate_baseline_day(35.68, "2026-07-15")
    tokyo_winter = _generate_climate_baseline_day(35.68, "2026-01-15")
    assert tokyo_summer.temp_max_c > tokyo_winter.temp_max_c
    assert tokyo_summer.temp_max_c > 24.0
    assert tokyo_winter.temp_max_c < 20.0

    # Sydney (-33° S) in January (summer) vs July (winter)
    sydney_summer = _generate_climate_baseline_day(-33.86, "2026-01-15")
    sydney_winter = _generate_climate_baseline_day(-33.86, "2026-07-15")
    assert sydney_summer.temp_max_c > sydney_winter.temp_max_c
