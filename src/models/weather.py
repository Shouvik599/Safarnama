"""Pydantic domain models for weather forecast data.

Provides structured, validated contracts for daily weather forecasts and aggregated
forecast results consumed by Phase 3 tools, Experience nodes, and itinerary planners.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DailyWeatherForecast(BaseModel):
    """Structured weather forecast for a single calendar day."""

    date: str = Field(description="Forecast date in ISO 8601 format (YYYY-MM-DD).")
    temp_max_c: float = Field(description="Maximum expected temperature in Celsius.")
    temp_min_c: float = Field(description="Minimum expected temperature in Celsius.")
    temp_avg_c: float = Field(description="Average expected temperature in Celsius.")
    precipitation_probability: int = Field(
        ge=0, le=100, description="Probability of precipitation as a percentage (0 to 100)."
    )
    precipitation_mm: float = Field(
        ge=0.0, description="Total expected liquid precipitation/rainfall in millimeters."
    )
    weather_code: int = Field(
        description="WMO standard meteorological weather interpretation code (0-99)."
    )
    condition: str = Field(
        description="Human-readable description of weather (e.g. 'Clear sky', 'Moderate rain')."
    )
    is_outdoor_friendly: bool = Field(
        description=(
            "True if condition is suitable for outdoor sightseeing "
            "(precipitation probability < 50% and no severe weather)."
        )
    )


class WeatherForecastResult(BaseModel):
    """Aggregated multi-day weather forecast result for a destination."""

    latitude: float = Field(ge=-90.0, le=90.0, description="Target location latitude.")
    longitude: float = Field(ge=-180.0, le=180.0, description="Target location longitude.")
    destination: str | None = Field(
        default=None, description="Optional city or destination label (e.g. 'Tokyo, Japan')."
    )
    start_date: str = Field(description="Start date of the forecast window (YYYY-MM-DD).")
    end_date: str = Field(description="End date of the forecast window (YYYY-MM-DD).")
    daily_forecasts: list[DailyWeatherForecast] = Field(
        default_factory=list, description="Ordered daily forecasts across the date range."
    )
    provider: str = Field(
        description=(
            "Provenance provider: 'fixture', 'open-meteo', 'wttr.in', "
            "'openweathermap', or 'climate-baseline'."
        )
    )
    is_estimated: bool = Field(
        description="True if derived from historical/seasonal climate baseline heuristic."
    )
    summary: str = Field(
        description="Concise human-readable summary of expected conditions for the travel window."
    )
    timestamp: str = Field(
        description="ISO 8601 timestamp when this forecast was generated or retrieved."
    )
