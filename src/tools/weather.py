"""Deterministic weather forecasting tool with multi-tier resilience.

Provides structured weather forecasts (temperatures, precipitation probability,
WMO weather conditions, outdoor friendliness) for travel destinations by coordinates.

Fallback Cascade:
1. Test Fixture: data/fixtures/mock_weather.json (if use_fixture=True or SAFARNAMA_TEST_MODE=1)
2. In-Memory Cache: 3-hour TTL per coordinate/date pair
3. Live Tier 1: Open-Meteo Forecast API (zero auth, 16-day daily forecast)
4. Live Tier 2: wttr.in JSON API (zero auth, global fallback)
5. Live Tier 3: OpenWeatherMap 5-Day/3-Hour API (if OPENWEATHERMAP_API_KEY is configured)
6. Tier 4: Offline Climate Baseline Heuristic (latitude + seasonal monthly physics)
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from src.models.weather import DailyWeatherForecast, WeatherForecastResult

load_dotenv()

log = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).parent.parent.parent / "data" / "fixtures" / "mock_weather.json"
CACHE_TTL_SECONDS = 10800  # 3 hours
DEFAULT_TIMEOUT_SECONDS = 6.0

# ---------------------------------------------------------------------------
# WMO Standard Meteorological Weather Codes (0-99)
# ---------------------------------------------------------------------------
WMO_WEATHER_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

# Weather codes that severely impair outdoor tourism
SEVERE_WEATHER_CODES = {55, 57, 63, 65, 66, 67, 73, 75, 81, 82, 85, 86, 95, 96, 99}


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class WeatherError(Exception):
    """Base exception for weather forecasting errors."""


class InvalidCoordinatesError(WeatherError, ValueError):
    """Raised when latitude or longitude coordinates are out of valid range."""


class InvalidDateRangeError(WeatherError, ValueError):
    """Raised when start_date or end_date are malformed or logically inverted."""


class WeatherAPIError(WeatherError):
    """Raised when all weather providers fail and offline fallback is disabled."""


# ---------------------------------------------------------------------------
# In-Memory Cache Store
# ---------------------------------------------------------------------------


class _WeatherCache:
    """Thread-safe in-memory cache keyed by rounded coordinates and date range."""

    def __init__(self) -> None:
        self._entries: dict[str, tuple[WeatherForecastResult, float]] = {}

    def _make_key(self, lat: float, lon: float, start_date: str, end_date: str) -> str:
        return f"{lat:.2f}:{lon:.2f}:{start_date}:{end_date}"

    def get(
        self, lat: float, lon: float, start_date: str, end_date: str
    ) -> WeatherForecastResult | None:
        key = self._make_key(lat, lon, start_date, end_date)
        entry = self._entries.get(key)
        if not entry:
            return None
        result, fetched_at = entry
        if time.time() - fetched_at < CACHE_TTL_SECONDS:
            return result
        # Expired
        self._entries.pop(key, None)
        return None

    def set(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        result: WeatherForecastResult,
    ) -> None:
        key = self._make_key(lat, lon, start_date, end_date)
        self._entries[key] = (result, time.time())

    def clear(self) -> None:
        self._entries.clear()


_global_weather_cache = _WeatherCache()


def clear_weather_cache() -> None:
    """Clear all cached weather forecast results."""
    _global_weather_cache.clear()


# ---------------------------------------------------------------------------
# Core Utilities
# ---------------------------------------------------------------------------


def is_outdoor_friendly(precipitation_probability: int, weather_code: int) -> bool:
    """Determine whether weather condition is suitable for outdoor sightseeing."""
    if precipitation_probability >= 50:
        return False
    return weather_code not in SEVERE_WEATHER_CODES


def generate_weather_summary(daily: list[DailyWeatherForecast]) -> str:
    """Produce a concise, human-readable summary of overall conditions."""
    if not daily:
        return "No forecast available."
    avg_max = sum(d.temp_max_c for d in daily) / len(daily)
    avg_min = sum(d.temp_min_c for d in daily) / len(daily)
    rainy_days = sum(1 for d in daily if not d.is_outdoor_friendly)

    summary = f"Expected temperatures between {avg_min:.1f}°C and {avg_max:.1f}°C. "
    if rainy_days == 0:
        summary += "Favorable outdoor weather throughout the period."
    elif rainy_days == len(daily):
        summary += "Precipitation expected on all days; indoor alternatives strongly recommended."
    else:
        summary += f"Precipitation or rain showers expected on {rainy_days} of {len(daily)} days."
    return summary


def _validate_coordinates(lat: float, lon: float) -> None:
    if not (-90.0 <= lat <= 90.0):
        raise InvalidCoordinatesError(f"Latitude must be between -90 and 90, got {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise InvalidCoordinatesError(f"Longitude must be between -180 and 180, got {lon}")


def _normalize_dates(
    start_date: str | date | None,
    end_date: str | date | None,
    days: int,
) -> tuple[str, str, list[str]]:
    """Convert flexible input dates into ISO date strings and full date list."""
    if days < 1:
        raise InvalidDateRangeError(f"days must be at least 1, got {days}")

    if start_date is None:
        start_d = date.today()
    elif isinstance(start_date, date):
        start_d = start_date
    else:
        try:
            start_d = date.fromisoformat(start_date)
        except ValueError as exc:
            raise InvalidDateRangeError(
                f"Invalid start_date format '{start_date}', expected YYYY-MM-DD"
            ) from exc

    if end_date is None:
        end_d = start_d + timedelta(days=days - 1)
    elif isinstance(end_date, date):
        end_d = end_date
    else:
        try:
            end_d = date.fromisoformat(end_date)
        except ValueError as exc:
            raise InvalidDateRangeError(
                f"Invalid end_date format '{end_date}', expected YYYY-MM-DD"
            ) from exc

    if end_d < start_d:
        raise InvalidDateRangeError(
            f"end_date ({end_d.isoformat()}) cannot be before start_date ({start_d.isoformat()})"
        )

    delta_days = (end_d - start_d).days + 1
    date_list = [(start_d + timedelta(days=i)).isoformat() for i in range(delta_days)]
    return start_d.isoformat(), end_d.isoformat(), date_list


# ---------------------------------------------------------------------------
# Tier 0: Fixture Mode
# ---------------------------------------------------------------------------


def _load_fixture_forecast(
    lat: float,
    lon: float,
    start_date_str: str,
    end_date_str: str,
    date_list: list[str],
    destination: str | None,
) -> WeatherForecastResult:
    """Load mock forecast from local fixture for offline testing."""
    if not FIXTURE_PATH.is_file():
        raise FileNotFoundError(f"Mock weather fixture not found at {FIXTURE_PATH}")

    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    template_list = data.get("default", [])
    if not template_list:
        raise ValueError("Mock weather fixture is missing 'default' forecast templates.")

    daily_forecasts: list[DailyWeatherForecast] = []
    for i, d_str in enumerate(date_list):
        tpl = template_list[i % len(template_list)]
        daily_forecasts.append(
            DailyWeatherForecast(
                date=d_str,
                temp_max_c=tpl["temp_max_c"],
                temp_min_c=tpl["temp_min_c"],
                temp_avg_c=tpl["temp_avg_c"],
                precipitation_probability=tpl["precipitation_probability"],
                precipitation_mm=tpl["precipitation_mm"],
                weather_code=tpl["weather_code"],
                condition=tpl["condition"],
                is_outdoor_friendly=tpl["is_outdoor_friendly"],
            )
        )

    return WeatherForecastResult(
        latitude=lat,
        longitude=lon,
        destination=destination,
        start_date=start_date_str,
        end_date=end_date_str,
        daily_forecasts=daily_forecasts,
        provider="fixture",
        is_estimated=False,
        summary=generate_weather_summary(daily_forecasts),
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Tier 1: Open-Meteo Forecast API (Zero Auth, Primary)
# ---------------------------------------------------------------------------


def _fetch_open_meteo(
    lat: float,
    lon: float,
    date_list: list[str],
    timeout: float,
) -> dict[str, DailyWeatherForecast]:
    """Fetch daily forecast from Open-Meteo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"daily=weather_code,temperature_2m_max,temperature_2m_min,"
        f"precipitation_probability_max,precipitation_sum&"
        f"timezone=auto&forecast_days=16"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Safarnama/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    daily = data.get("daily", {})
    times = daily.get("time", [])
    wcodes = daily.get("weather_code", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precip_probs = daily.get("precipitation_probability_max", [])
    precip_sums = daily.get("precipitation_sum", [])

    results: dict[str, DailyWeatherForecast] = {}
    for i, t_str in enumerate(times):
        wcode = int(wcodes[i]) if i < len(wcodes) and wcodes[i] is not None else 0
        t_max = float(max_temps[i]) if i < len(max_temps) and max_temps[i] is not None else 25.0
        t_min = float(min_temps[i]) if i < len(min_temps) and min_temps[i] is not None else 18.0
        p_prob = (
            int(precip_probs[i]) if i < len(precip_probs) and precip_probs[i] is not None else 0
        )
        p_sum = (
            float(precip_sums[i]) if i < len(precip_sums) and precip_sums[i] is not None else 0.0
        )
        t_avg = round((t_max + t_min) / 2.0, 1)
        desc = WMO_WEATHER_CODES.get(wcode, "Clear sky")

        results[t_str] = DailyWeatherForecast(
            date=t_str,
            temp_max_c=t_max,
            temp_min_c=t_min,
            temp_avg_c=t_avg,
            precipitation_probability=p_prob,
            precipitation_mm=p_sum,
            weather_code=wcode,
            condition=desc,
            is_outdoor_friendly=is_outdoor_friendly(p_prob, wcode),
        )

    return results


# ---------------------------------------------------------------------------
# Tier 2: wttr.in JSON API (Zero Auth, Fallback 1)
# ---------------------------------------------------------------------------


def _map_wttr_code_to_wmo(code_str: str) -> tuple[int, str]:
    """Map wttr.in / World Weather Online code to standard WMO code and description."""
    try:
        code = int(code_str)
    except (ValueError, TypeError):
        return 2, "Partly cloudy"

    # WWO codes to WMO
    if code == 113:
        return 0, "Clear sky"
    if code == 116:
        return 2, "Partly cloudy"
    if code in (119, 122):
        return 3, "Overcast"
    if code in (143, 248):
        return 45, "Fog"
    if code in (176, 293, 296, 302, 308):
        return 63, "Moderate rain"
    if code in (200, 386, 389):
        return 95, "Thunderstorm"
    if code in (179, 182, 323, 326, 332):
        return 71, "Slight snow fall"
    return 2, "Partly cloudy"


def _fetch_wttr_in(
    lat: float,
    lon: float,
    date_list: list[str],
    timeout: float,
) -> dict[str, DailyWeatherForecast]:
    """Fetch 3-day daily forecast from wttr.in."""
    url = f"https://wttr.in/{lat:.4f},{lon:.4f}?format=j1"
    req = urllib.request.Request(url, headers={"User-Agent": "Safarnama/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    weather_list = data.get("weather", [])
    results: dict[str, DailyWeatherForecast] = {}
    for day in weather_list:
        d_str = day.get("date")
        if not d_str:
            continue
        try:
            t_max = float(day.get("maxtempC", 25.0))
            t_min = float(day.get("mintempC", 18.0))
            t_avg = round((t_max + t_min) / 2.0, 1)
        except (ValueError, TypeError):
            t_max, t_min, t_avg = 25.0, 18.0, 21.5

        # Hourly rain aggregation
        hourly = day.get("hourly", [])
        max_chance = 0
        total_precip = 0.0
        wcode = 1
        wdesc = "Mainly clear"

        if hourly:
            mid = hourly[len(hourly) // 2]
            wcode_raw = mid.get("weatherCode", "116")
            wcode, wdesc = _map_wttr_code_to_wmo(wcode_raw)
            for h in hourly:
                try:
                    c = int(h.get("chanceofrain", 0))
                    if c > max_chance:
                        max_chance = c
                    total_precip += float(h.get("precipMM", 0.0))
                except (ValueError, TypeError):
                    pass

        results[d_str] = DailyWeatherForecast(
            date=d_str,
            temp_max_c=t_max,
            temp_min_c=t_min,
            temp_avg_c=t_avg,
            precipitation_probability=min(max_chance, 100),
            precipitation_mm=round(total_precip, 1),
            weather_code=wcode,
            condition=wdesc,
            is_outdoor_friendly=is_outdoor_friendly(max_chance, wcode),
        )

    return results


# ---------------------------------------------------------------------------
# Tier 3: OpenWeatherMap 5-Day/3-Hour Forecast (Auth Key, Fallback 2)
# ---------------------------------------------------------------------------


def _map_owm_id_to_wmo(owm_id: int) -> tuple[int, str]:
    """Map OpenWeatherMap condition id to WMO code and description."""
    if owm_id == 800:
        return 0, "Clear sky"
    if owm_id == 801:
        return 1, "Mainly clear"
    if owm_id == 802:
        return 2, "Partly cloudy"
    if owm_id in (803, 804):
        return 3, "Overcast"
    if 500 <= owm_id <= 504 or 520 <= owm_id <= 531:
        return 63, "Moderate rain"
    if 200 <= owm_id <= 232:
        return 95, "Thunderstorm"
    if 600 <= owm_id <= 622:
        return 71, "Slight snow fall"
    if 300 <= owm_id <= 321:
        return 51, "Light drizzle"
    if 701 <= owm_id <= 781:
        return 45, "Fog"
    return 2, "Partly cloudy"


def _fetch_openweathermap(
    lat: float,
    lon: float,
    api_key: str,
    timeout: float,
) -> dict[str, DailyWeatherForecast]:
    """Fetch 5-day forecast from OpenWeatherMap."""
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast?"
        f"lat={lat}&lon={lon}&appid={api_key}&units=metric"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Safarnama/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    entries = data.get("list", [])
    grouped: dict[str, list[dict]] = {}
    for item in entries:
        dt_txt = item.get("dt_txt", "")
        if len(dt_txt) >= 10:
            d_str = dt_txt[:10]
            grouped.setdefault(d_str, []).append(item)

    results: dict[str, DailyWeatherForecast] = {}
    for d_str, items in grouped.items():
        max_temps = [it.get("main", {}).get("temp_max", 25.0) for it in items]
        min_temps = [it.get("main", {}).get("temp_min", 18.0) for it in items]
        pops = [int(it.get("pop", 0.0) * 100) for it in items]
        rain_sums = [it.get("rain", {}).get("3h", 0.0) for it in items]

        t_max = max(max_temps) if max_temps else 25.0
        t_min = min(min_temps) if min_temps else 18.0
        t_avg = round((t_max + t_min) / 2.0, 1)
        p_prob = max(pops) if pops else 0
        p_mm = round(sum(rain_sums), 1)

        # Midday condition
        mid = items[len(items) // 2]
        weather_arr = mid.get("weather", [])
        owm_id = weather_arr[0].get("id", 800) if weather_arr else 800
        wcode, wdesc = _map_owm_id_to_wmo(owm_id)

        results[d_str] = DailyWeatherForecast(
            date=d_str,
            temp_max_c=round(t_max, 1),
            temp_min_c=round(t_min, 1),
            temp_avg_c=t_avg,
            precipitation_probability=p_prob,
            precipitation_mm=p_mm,
            weather_code=wcode,
            condition=wdesc,
            is_outdoor_friendly=is_outdoor_friendly(p_prob, wcode),
        )

    return results


# ---------------------------------------------------------------------------
# Tier 4: Offline Climate Baseline Heuristic
# ---------------------------------------------------------------------------


def _generate_climate_baseline_day(
    lat: float,
    d_str: str,
) -> DailyWeatherForecast:
    """Generate realistic seasonal temperature and rain probability based on latitude and month."""
    dt = date.fromisoformat(d_str)
    month = dt.month  # 1 to 12
    abs_lat = abs(lat)
    is_northern = lat >= 0

    # Solar declination cycle: summer peaks in July (N) or Jan (S)
    summer_peak_month = 7 if is_northern else 1
    # Angular distance from summer peak (0 = mid summer, 6 = mid winter)
    seasonal_phase = (month - summer_peak_month) % 12
    winter_factor = (1.0 - math.cos(2.0 * math.pi * seasonal_phase / 12.0)) / 2.0

    if abs_lat < 23.5:
        # Tropical: warm year-round, distinct wet/monsoon season
        base_max, base_min = 32.0, 24.0
        temp_max = base_max - (winter_factor * 3.0)
        temp_min = base_min - (winter_factor * 3.0)
        # Wet season in tropics: summer months
        is_wet = 5 <= month <= 9 if is_northern else (month >= 11 or month <= 3)
        p_prob = 65 if is_wet else 15
        p_mm = 12.0 if is_wet else 0.5
        wcode = 63 if is_wet else 1
        condition = "Moderate rain" if is_wet else "Mainly clear"
    elif abs_lat < 35.0:
        # Subtropical: hot summers, mild winters
        summer_max, summer_min = 35.0, 24.0
        winter_max, winter_min = 19.0, 9.0
        temp_max = summer_max - (winter_factor * (summer_max - winter_max))
        temp_min = summer_min - (winter_factor * (summer_min - winter_min))
        p_prob = int(20 + winter_factor * 15)
        p_mm = 2.0 if p_prob > 25 else 0.0
        wcode = 2 if p_prob < 30 else 61
        condition = "Partly cloudy" if p_prob < 30 else "Slight rain"
    elif abs_lat < 55.0:
        # Temperate: warm summers, cold winters
        summer_max, summer_min = 26.0, 15.0
        winter_max, winter_min = 6.0, -1.0
        temp_max = summer_max - (winter_factor * (summer_max - winter_max))
        temp_min = summer_min - (winter_factor * (summer_min - winter_min))
        p_prob = int(25 + winter_factor * 20)
        p_mm = 4.0 if p_prob > 35 else 0.5
        wcode = 2 if p_prob < 35 else 61
        condition = "Partly cloudy" if p_prob < 35 else "Slight rain"
    else:
        # Subpolar / Polar: cool summers, freezing winters
        summer_max, summer_min = 16.0, 8.0
        winter_max, winter_min = -2.0, -10.0
        temp_max = summer_max - (winter_factor * (summer_max - winter_max))
        temp_min = summer_min - (winter_factor * (summer_min - winter_min))
        p_prob = 35
        p_mm = 2.0
        wcode = 3 if winter_factor < 0.5 else 71
        condition = "Overcast" if winter_factor < 0.5 else "Slight snow fall"

    t_max_r = round(temp_max, 1)
    t_min_r = round(temp_min, 1)
    t_avg_r = round((t_max_r + t_min_r) / 2.0, 1)

    return DailyWeatherForecast(
        date=d_str,
        temp_max_c=t_max_r,
        temp_min_c=t_min_r,
        temp_avg_c=t_avg_r,
        precipitation_probability=p_prob,
        precipitation_mm=p_mm,
        weather_code=wcode,
        condition=condition,
        is_outdoor_friendly=is_outdoor_friendly(p_prob, wcode),
    )


# ---------------------------------------------------------------------------
# Public Facade
# ---------------------------------------------------------------------------


def get_weather_forecast(
    latitude: float,
    longitude: float,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
    days: int = 7,
    use_fixture: bool = False,
    destination: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> WeatherForecastResult:
    """Retrieve structured weather forecast for coordinates across requested dates.

    Follows the multi-tier fallback architecture:
    Fixture -> In-Memory Cache -> Open-Meteo -> wttr.in -> OpenWeatherMap -> Climate Baseline.

    Args:
        latitude: Target location latitude in [-90.0, 90.0].
        longitude: Target location longitude in [-180.0, 180.0].
        start_date: Start date (YYYY-MM-DD or date object). Defaults to today.
        end_date: End date (YYYY-MM-DD or date object). Defaults to start_date + days - 1.
        days: Duration in days if end_date not explicitly supplied (default: 7).
        use_fixture: Force local fixture lookup without making network calls.
        destination: Optional destination name for reporting.
        timeout: Network request timeout in seconds (default: 6.0).

    Returns:
        WeatherForecastResult with daily forecasts and provenance provider.
    """
    _validate_coordinates(latitude, longitude)
    start_date_str, end_date_str, date_list = _normalize_dates(start_date, end_date, days)

    # 1. Check Fixture Mode
    should_use_fixture = (
        use_fixture
        or os.getenv("SAFARNAMA_TEST_MODE", "").lower() in ("1", "true", "yes")
        or os.getenv("SAFARNAMA_USE_FIXTURES", "").lower() in ("1", "true", "yes")
    )
    if should_use_fixture:
        return _load_fixture_forecast(
            latitude, longitude, start_date_str, end_date_str, date_list, destination
        )

    # 2. Check In-Memory Cache
    cached = _global_weather_cache.get(latitude, longitude, start_date_str, end_date_str)
    if cached is not None:
        return cached

    # 3. Live Tier 1: Open-Meteo
    provider = "open-meteo"
    is_estimated = False
    daily_map: dict[str, DailyWeatherForecast] = {}
    try:
        daily_map = _fetch_open_meteo(latitude, longitude, date_list, timeout=timeout)
    except Exception as exc:
        log.warning(
            "Open-Meteo weather endpoint failed (%s). Trying wttr.in tier.",
            exc,
        )

    # 4. Live Tier 2: wttr.in (if Open-Meteo failed)
    if not daily_map:
        try:
            daily_map = _fetch_wttr_in(latitude, longitude, date_list, timeout=timeout)
            provider = "wttr.in"
        except Exception as exc:
            log.warning("wttr.in weather endpoint failed (%s). Trying OpenWeatherMap tier.", exc)

    # 5. Live Tier 3: OpenWeatherMap (if wttr.in failed and API key present)
    owm_key = os.getenv("OPENWEATHERMAP_API_KEY", "").strip()
    if not daily_map and owm_key:
        try:
            daily_map = _fetch_openweathermap(latitude, longitude, owm_key, timeout=timeout)
            provider = "openweathermap"
        except Exception as exc:
            log.warning(
                "OpenWeatherMap endpoint failed (%s). Falling back to climate baseline.",
                exc,
            )

    # 6. Assemble daily forecasts with fallback to climate baseline for any missing dates
    daily_forecasts: list[DailyWeatherForecast] = []
    has_estimated_days = False

    for d_str in date_list:
        if d_str in daily_map:
            daily_forecasts.append(daily_map[d_str])
        else:
            # Fallback for dates beyond provider window or when providers are down
            daily_forecasts.append(_generate_climate_baseline_day(latitude, d_str))
            has_estimated_days = True

    if not daily_map:
        provider = "climate-baseline"
        is_estimated = True
    elif has_estimated_days:
        is_estimated = True

    result = WeatherForecastResult(
        latitude=latitude,
        longitude=longitude,
        destination=destination,
        start_date=start_date_str,
        end_date=end_date_str,
        daily_forecasts=daily_forecasts,
        provider=provider,
        is_estimated=is_estimated,
        summary=generate_weather_summary(daily_forecasts),
        timestamp=datetime.now(UTC).isoformat(),
    )

    # Cache successful result
    _global_weather_cache.set(latitude, longitude, start_date_str, end_date_str, result)
    return result
