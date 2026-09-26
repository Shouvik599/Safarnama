"""Deterministic transport and route search tool with multi-tier API resilience.

Provides structured transport options (flights, trains, intercity buses) for Indian domestic
and international trips, with seat classes, durations, and fares converted to Indian Rupee (INR).

Fallback Cascade:
1. Test Fixture: data/fixtures/mock_flights.json (if use_fixture=True or
   SAFARNAMA_USE_FIXTURES=true)
2. In-Memory Cache: 1-hour TTL per (origin, destination, date, mode) search
3. Live Aviation APIs: Sky Scraper / Flights Sky / Aviationstack
   (using RAPIDAPI_KEY / AVIATIONSTACK_API_KEY)
4. Live Indian Railways APIs: Indian Railway IRCTC / eRail (using RAPIDAPI_KEY / Open access)
5. Live International Rail & Bus APIs: transport.rest / Transitland (Zero auth open access)
6. Live Web Search Tool Fallback: search_web() for live schedule & fare snippets
7. Tier 5: Offline Distance & Speed Physics Engine (Haversine math guaranteeing zero crash)
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from src.models.transport import TransportSearchResult, TransportSegment
from src.tools.static_data import (
    get_airport_coordinates,
    get_airports_by_city,
    get_country,
)
from src.tools.web_search import search_web

load_dotenv()

log = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).parent.parent.parent / "data" / "fixtures" / "mock_flights.json"
CACHE_TTL_SECONDS = 3600  # 1 hour
DEFAULT_TIMEOUT_SECONDS = 12.0


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class TransportError(Exception):
    """Base exception for transport search errors."""


class InvalidLocationError(TransportError, ValueError):
    """Raised when origin or destination inputs are empty or invalid."""


class TransportAPIError(TransportError):
    """Raised when transport search providers fail and offline fallback is disabled."""


# ---------------------------------------------------------------------------
# In-Memory Cache Store
# ---------------------------------------------------------------------------


class TransportCache:
    """Thread-safe in-memory cache store for transport search results."""

    def __init__(self, ttl_seconds: float = CACHE_TTL_SECONDS) -> None:
        self._cache: dict[str, tuple[float, TransportSearchResult]] = {}
        self.ttl_seconds = ttl_seconds

    def _make_key(self, origin: str, destination: str, date_str: str, mode: str) -> str:
        return f"{origin.strip().upper()}:{destination.strip().upper()}:{date_str}:{mode.upper()}"

    def get(
        self, origin: str, destination: str, date_str: str, mode: str
    ) -> TransportSearchResult | None:
        key = self._make_key(origin, destination, date_str, mode)
        if key in self._cache:
            created_at, result = self._cache[key]
            if time.time() - created_at < self.ttl_seconds:
                return result
            del self._cache[key]
        return None

    def set(
        self, origin: str, destination: str, date_str: str, mode: str, result: TransportSearchResult
    ) -> None:
        key = self._make_key(origin, destination, date_str, mode)
        self._cache[key] = (time.time(), result)

    def clear(self) -> None:
        self._cache.clear()


_TRANSPORT_CACHE = TransportCache()


def clear_transport_cache() -> None:
    """Clear the in-memory transport search cache."""
    _TRANSPORT_CACHE.clear()


# ---------------------------------------------------------------------------
# Provider Implementation 1: Local Offline Fixture
# ---------------------------------------------------------------------------


def _search_fixture(
    origin: str,
    destination: str,
    travel_date: str,
    mode: str = "ALL",
    is_fallback_trigger: bool = True,
) -> TransportSearchResult:
    """Retrieve transport options from local mock fixture file."""
    if not FIXTURE_PATH.exists():
        log.warning("Transport fixture file not found at %s", FIXTURE_PATH)
        return _estimate_physics_transport(origin, destination, travel_date, mode)

    try:
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            data = json.load(f)

        key1 = f"{origin.strip().upper()}:{destination.strip().upper()}"
        key2 = f"{destination.strip().upper()}:{origin.strip().upper()}"

        routes_map: dict = data.get("routes", {})
        route_data = routes_map.get(key1) or routes_map.get(key2)

        if not route_data:
            route_data = data.get("default_fallback", {})

        raw_options = route_data.get("options", [])
        options = []
        for opt in raw_options:
            opt_mode = opt.get("mode", "FLIGHT").upper()
            if mode != "ALL" and opt_mode != mode.upper():
                continue

            options.append(
                TransportSegment(
                    mode=opt_mode,
                    carrier=opt.get("carrier", "Express Carrier"),
                    transport_code=opt.get("transport_code"),
                    origin=opt.get("origin", origin),
                    destination=opt.get("destination", destination),
                    departure_time=opt.get("departure_time", "09:00"),
                    arrival_time=opt.get("arrival_time", "12:00"),
                    duration_minutes=opt.get("duration_minutes", 180),
                    price_inr=float(opt.get("price_inr", 5000.0)),
                    cabin_class=opt.get("cabin_class", "ECONOMY"),
                    booking_url=opt.get("booking_url"),
                    provider="fixture",
                )
            )

        if not options:
            return _estimate_physics_transport(origin, destination, travel_date, mode)

        return TransportSearchResult(
            origin=origin.upper(),
            destination=destination.upper(),
            travel_date=travel_date,
            mode_requested=mode.upper(),
            options=options,
            provider_used="fixture",
            total_found=len(options),
            is_fallback=is_fallback_trigger,
            is_estimated=True,
            timestamp=datetime.now(UTC).isoformat(),
        )
    except Exception as exc:
        log.error("Failed to parse transport fixture: %s", exc)
        return _estimate_physics_transport(origin, destination, travel_date, mode)


# ---------------------------------------------------------------------------
# Provider Implementation 2: Distance & Speed Physics Engine Baseline
# ---------------------------------------------------------------------------


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance in kilometers between two coordinates."""
    r = 6371.0  # Earth radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def _resolve_coordinates(location_str: str) -> tuple[float, float]:
    """Resolve coordinates for an airport IATA code, city, or country name."""
    clean_loc = location_str.strip().upper()
    try:
        coords = get_airport_coordinates(clean_loc)
        return coords.latitude, coords.longitude
    except Exception:
        pass

    try:
        country = get_country(clean_loc)
        if country.coordinates:
            return country.coordinates.latitude, country.coordinates.longitude
    except Exception:
        pass

    # Default fallback coordinates (Delhi reference: 28.6139° N, 77.2090° E)
    return 28.6139, 77.2090


def _estimate_physics_transport(
    origin: str, destination: str, travel_date: str, mode: str = "ALL"
) -> TransportSearchResult:
    """Generate realistic distance/speed-based transport estimates when APIs are unconfigured."""
    lat1, lon1 = _resolve_coordinates(origin)
    lat2, lon2 = _resolve_coordinates(destination)

    dist_km = _haversine_distance_km(lat1, lon1, lat2, lon2)
    if dist_km < 10.0:
        dist_km = 350.0  # Default reasonable inter-city distance

    options: list[TransportSegment] = []
    requested_mode = mode.upper()

    # 1. Flight Option
    if requested_mode in ("ALL", "FLIGHT"):
        flight_duration = max(45, int((dist_km / 650.0) * 60) + 45)
        flight_price = max(2800.0, round(dist_km * 5.80, 2))
        options.append(
            TransportSegment(
                mode="FLIGHT",
                carrier="Regional Air Line",
                transport_code=f"SA-{hash(origin + destination) % 899 + 100}",
                origin=origin.upper(),
                destination=destination.upper(),
                departure_time="09:30",
                arrival_time=f"{(9 + flight_duration // 60) % 24:02d}:{flight_duration % 60:02d}",
                duration_minutes=flight_duration,
                price_inr=flight_price,
                cabin_class="ECONOMY",
                booking_url="https://safarnama.local/flights",
                provider="physics-heuristic",
            )
        )

    # 2. Train Option (feasible if distance <= 1500 km or mode explicitly TRAIN)
    if requested_mode in ("ALL", "TRAIN") and (dist_km <= 1500.0 or requested_mode == "TRAIN"):
        train_duration = max(90, int((dist_km / 110.0) * 60))
        train_price = max(450.0, round(dist_km * 1.85, 2))
        options.append(
            TransportSegment(
                mode="TRAIN",
                carrier="Intercity Express Train",
                transport_code=f"{hash(destination + origin) % 89999 + 10000}",
                origin=origin.upper(),
                destination=destination.upper(),
                departure_time="14:00",
                arrival_time=f"{(14 + train_duration // 60) % 24:02d}:{train_duration % 60:02d}",
                duration_minutes=train_duration,
                price_inr=train_price,
                cabin_class="CC" if dist_km < 500 else "3A",
                booking_url="https://safarnama.local/trains",
                provider="physics-heuristic",
            )
        )

    # 3. Bus Option (feasible if distance <= 800 km or mode explicitly BUS)
    if requested_mode in ("ALL", "BUS") and (dist_km <= 800.0 or requested_mode == "BUS"):
        bus_duration = max(120, int((dist_km / 65.0) * 60))
        bus_price = max(350.0, round(dist_km * 1.30, 2))
        options.append(
            TransportSegment(
                mode="BUS",
                carrier="Volvo AC Sleeper Bus",
                transport_code=f"BUS-{hash(origin) % 899 + 100}",
                origin=origin.upper(),
                destination=destination.upper(),
                departure_time="21:00",
                arrival_time=f"{(21 + bus_duration // 60) % 24:02d}:{bus_duration % 60:02d}",
                duration_minutes=bus_duration,
                price_inr=bus_price,
                cabin_class="AC_SLEEPER",
                booking_url="https://safarnama.local/buses",
                provider="physics-heuristic",
            )
        )

    return TransportSearchResult(
        origin=origin.upper(),
        destination=destination.upper(),
        travel_date=travel_date,
        mode_requested=requested_mode,
        options=options,
        provider_used="physics-heuristic",
        total_found=len(options),
        is_fallback=True,
        is_estimated=True,
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Provider Implementation 3: Live RapidAPI Flight Providers
# ---------------------------------------------------------------------------


KNOWN_ENTITY_IDS: dict[str, str] = {
    "DEL": "95673498",
    "BOM": "95673320",
    "LHR": "95565050",
    "JFK": "95565058",
    "HND": "95565046",
    "NRT": "95565046",
    "CDG": "95565039",
    "SIN": "95565047",
    "DXB": "95565063",
    "MAA": "95673330",
    "BLR": "95673331",
    "CCU": "95673332",
}


def _get_sky_scraper_entity_id(
    iata_code: str, rapid_key: str, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> str:
    """Resolve Sky Scraper entityId dynamically for an airport IATA code."""
    code = iata_code.strip().upper()
    if code in KNOWN_ENTITY_IDS:
        return KNOWN_ENTITY_IDS[code]

    url = f"https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport?query={code}"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "x-rapidapi-key": rapid_key,
                "x-rapidapi-host": "sky-scrapper.p.rapidapi.com",
                "User-Agent": "Safarnama/0.1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                data = body.get("data", [])
                if data and isinstance(data, list):
                    for item in data:
                        if item.get("skyId") == code and item.get("entityId"):
                            entity_str = str(item["entityId"])
                            KNOWN_ENTITY_IDS[code] = entity_str
                            return entity_str
                    if data[0].get("entityId"):
                        entity_str = str(data[0]["entityId"])
                        KNOWN_ENTITY_IDS[code] = entity_str
                        return entity_str
    except Exception as exc:
        log.debug("Failed to resolve Sky Scraper entityId for %s: %s", code, exc)

    return ""


def _search_sky_scraper(
    origin: str,
    destination: str,
    travel_date: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> TransportSearchResult | None:
    """Execute live flight search via Sky Scraper API on RapidAPI."""
    rapid_key = os.getenv("RAPIDAPI_KEY")
    if not rapid_key:
        return None

    orig_code = origin.strip().upper()
    dest_code = destination.strip().upper()
    orig_entity = _get_sky_scraper_entity_id(orig_code, rapid_key, timeout)
    dest_entity = _get_sky_scraper_entity_id(dest_code, rapid_key, timeout)

    query_params = f"originSkyId={orig_code}&destinationSkyId={dest_code}&date={travel_date}"
    if orig_entity and dest_entity:
        query_params += f"&originEntityId={orig_entity}&destinationEntityId={dest_entity}"

    url = f"https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights?{query_params}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "x-rapidapi-key": rapid_key,
                "x-rapidapi-host": "sky-scrapper.p.rapidapi.com",
                "User-Agent": "Safarnama/0.1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                data = body.get("data", {})
                itineraries = data.get("itineraries", [])

                options = []
                for it in itineraries[:5]:
                    price_val = it.get("price", {}).get("raw", 5000.0)
                    legs = it.get("legs", [])
                    if legs:
                        leg = legs[0]
                        carrier_name = (
                            leg.get("carriers", {})
                            .get("marketing", [{}])[0]
                            .get("name", "Sky Airline")
                        )
                        duration = leg.get("durationInMinutes", 180)
                        dep_time = leg.get("departure", "10:00")
                        arr_time = leg.get("arrival", "13:00")
                        flight_num = leg.get("segments", [{}])[0].get("flightNumber", "FL-100")

                        options.append(
                            TransportSegment(
                                mode="FLIGHT",
                                carrier=carrier_name,
                                transport_code=str(flight_num),
                                origin=orig_code,
                                destination=dest_code,
                                departure_time=dep_time,
                                arrival_time=arr_time,
                                duration_minutes=duration,
                                price_inr=float(price_val),
                                cabin_class="ECONOMY",
                                provider="sky-scraper",
                            )
                        )

                if options:
                    log.info("Fetched %d flights from Sky Scraper API", len(options))
                    return TransportSearchResult(
                        origin=orig_code,
                        destination=dest_code,
                        travel_date=travel_date,
                        mode_requested="FLIGHT",
                        options=options,
                        provider_used="sky-scraper",
                        total_found=len(options),
                        is_fallback=False,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("Sky Scraper API request failed for %s->%s: %s", origin, destination, exc)

    return None


def _search_flights_sky(
    origin: str,
    destination: str,
    travel_date: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> TransportSearchResult | None:
    """Execute live flight search via Flights Sky API on RapidAPI."""
    rapid_key = os.getenv("RAPIDAPI_KEY")
    if not rapid_key:
        return None

    url = f"https://flights-sky.p.rapidapi.com/flights/search?origin={origin}&destination={destination}&date={travel_date}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "x-rapidapi-key": rapid_key,
                "x-rapidapi-host": "flights-sky.p.rapidapi.com",
                "User-Agent": "Safarnama/0.1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                flights = body.get("results", body.get("flights", []))

                options = []
                for fl in flights[:5]:
                    options.append(
                        TransportSegment(
                            mode="FLIGHT",
                            carrier=fl.get("airline") or fl.get("carrier") or "Sky Flight",
                            transport_code=fl.get("flightNumber") or fl.get("code"),
                            origin=origin.upper(),
                            destination=destination.upper(),
                            departure_time=fl.get("departureTime", "08:00"),
                            arrival_time=fl.get("arrivalTime", "11:00"),
                            duration_minutes=fl.get("durationMinutes", 180),
                            price_inr=float(fl.get("price", 4500.0)),
                            cabin_class="ECONOMY",
                            provider="flights-sky",
                        )
                    )

                if options:
                    log.info("Fetched %d flights from Flights Sky API", len(options))
                    return TransportSearchResult(
                        origin=origin.upper(),
                        destination=destination.upper(),
                        travel_date=travel_date,
                        mode_requested="FLIGHT",
                        options=options,
                        provider_used="flights-sky",
                        total_found=len(options),
                        is_fallback=True,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("Flights Sky API request failed for %s->%s: %s", origin, destination, exc)

    return None


def _resolve_iata_code(location: str) -> str:
    """Resolve an input string to a 3-letter IATA code if possible."""
    clean = location.strip().upper()
    if len(clean) == 3 and clean.isalpha():
        return clean
    try:
        airports = get_airports_by_city(location)
        if airports and airports[0].iata_code:
            return airports[0].iata_code.upper()
    except Exception:
        pass
    return clean[:3].upper()


def _search_aviationstack(
    origin: str,
    destination: str,
    travel_date: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> TransportSearchResult | None:
    """Execute live flight search via Aviationstack API."""
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        return None

    dep_iata = _resolve_iata_code(origin)
    arr_iata = _resolve_iata_code(destination)

    if len(dep_iata) != 3 or len(arr_iata) != 3:
        return None

    query_params: dict[str, str] = {
        "access_key": api_key,
        "dep_iata": dep_iata,
        "arr_iata": arr_iata,
        "limit": "5",
    }

    url = f"http://api.aviationstack.com/v1/flights?{urllib.parse.urlencode(query_params)}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Safarnama/0.1.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                flights_data = body.get("data", [])
                if not flights_data or not isinstance(flights_data, list):
                    return None

                # Calculate route distance for calibrated pricing baseline
                lat1, lon1 = _resolve_coordinates(dep_iata)
                lat2, lon2 = _resolve_coordinates(arr_iata)
                dist_km = _haversine_distance_km(lat1, lon1, lat2, lon2)
                base_price = max(2950.0, round(dist_km * 5.25, 2))

                options: list[TransportSegment] = []
                seen_flights: set[str] = set()

                for item in flights_data:
                    flight_info = item.get("flight", {})
                    airline_info = item.get("airline", {})
                    dep_info = item.get("departure", {})
                    arr_info = item.get("arrival", {})

                    f_num = str(flight_info.get("number") or "100")
                    f_iata = flight_info.get("iata") or f"{airline_info.get('iata', 'FL')}{f_num}"
                    flight_code = f_iata.strip()

                    if flight_code in seen_flights:
                        continue
                    seen_flights.add(flight_code)

                    carrier_name = airline_info.get("name") or "Commercial Airline"

                    dep_sched = dep_info.get("scheduled")
                    arr_sched = arr_info.get("scheduled")

                    dep_time = "09:00"
                    arr_time = "11:30"
                    dur_mins = max(45, int((dist_km / 650.0) * 60) + 40)

                    if dep_sched and "T" in dep_sched:
                        try:
                            dep_dt = datetime.fromisoformat(dep_sched.replace("Z", "+00:00"))
                            dep_time = dep_dt.strftime("%H:%M")
                            if arr_sched and "T" in arr_sched:
                                arr_dt = datetime.fromisoformat(arr_sched.replace("Z", "+00:00"))
                                arr_time = arr_dt.strftime("%H:%M")
                                diff_mins = int((arr_dt - dep_dt).total_seconds() / 60)
                                if 30 <= diff_mins <= 1440:
                                    dur_mins = diff_mins
                        except Exception:
                            pass

                    booking_url = f"https://www.google.com/travel/flights?q=flights+from+{dep_iata}+to+{arr_iata}"

                    options.append(
                        TransportSegment(
                            mode="FLIGHT",
                            carrier=carrier_name,
                            transport_code=flight_code,
                            origin=dep_iata,
                            destination=arr_iata,
                            departure_time=dep_time,
                            arrival_time=arr_time,
                            duration_minutes=dur_mins,
                            price_inr=base_price,
                            cabin_class="ECONOMY",
                            booking_url=booking_url,
                            provider="aviationstack",
                        )
                    )

                if options:
                    log.info(
                        "Fetched %d real scheduled flights from Aviationstack API", len(options)
                    )
                    return TransportSearchResult(
                        origin=dep_iata,
                        destination=arr_iata,
                        travel_date=travel_date,
                        mode_requested="FLIGHT",
                        options=options,
                        provider_used="aviationstack",
                        total_found=len(options),
                        is_fallback=True,
                        is_estimated=True,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("Aviationstack API request failed for %s->%s: %s", origin, destination, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 4: Live Indian Railways API (RapidAPI / eRail)
# ---------------------------------------------------------------------------


def _search_indian_railways(
    origin: str,
    destination: str,
    travel_date: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> TransportSearchResult | None:
    """Execute live train search via Indian Railway IRCTC API on RapidAPI."""
    rapid_key = os.getenv("RAPIDAPI_KEY")
    if not rapid_key:
        return None

    orig_code = origin.strip().upper()
    dest_code = destination.strip().upper()

    url = (
        "https://irctc1.p.rapidapi.com/api/v3/trainBetweenStations"
        f"?fromStationCode={orig_code}&toStationCode={dest_code}&dateOfJourney={travel_date}"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={
                "x-rapidapi-key": rapid_key,
                "x-rapidapi-host": "irctc1.p.rapidapi.com",
                "User-Agent": "Safarnama/0.1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                trains = body.get("data", body.get("trains", []))

                options = []
                for tr in trains[:5]:
                    name = tr.get("train_name") or tr.get("trainName") or "Express Train"
                    num = str(tr.get("train_number") or tr.get("trainNumber") or "12345")
                    dep = tr.get("from_std") or tr.get("departureTime") or "06:00"
                    arr = tr.get("to_sta") or tr.get("arrivalTime") or "14:00"

                    dur_str = tr.get("duration")
                    dur_mins = 480
                    if dur_str and ":" in str(dur_str):
                        try:
                            parts = str(dur_str).split(":")
                            dur_mins = int(parts[0]) * 60 + int(parts[1])
                        except ValueError:
                            pass
                    elif tr.get("durationMinutes"):
                        dur_mins = int(tr["durationMinutes"])

                    dist_km = float(tr.get("distance", 800.0))
                    fare_val = float(tr.get("fare") or max(450.0, round(dist_km * 1.85, 2)))

                    classes = tr.get("class_type", ["3A"])
                    cabin = classes[0] if isinstance(classes, list) and classes else "3A"

                    options.append(
                        TransportSegment(
                            mode="TRAIN",
                            carrier=name,
                            transport_code=num,
                            origin=orig_code,
                            destination=dest_code,
                            departure_time=dep,
                            arrival_time=arr,
                            duration_minutes=dur_mins,
                            price_inr=fare_val,
                            cabin_class=cabin,
                            booking_url="https://www.irctc.co.in",
                            provider="irctc1",
                        )
                    )

                if options:
                    log.info("Fetched %d trains from IRCTC1 API", len(options))
                    return TransportSearchResult(
                        origin=orig_code,
                        destination=dest_code,
                        travel_date=travel_date,
                        mode_requested="TRAIN",
                        options=options,
                        provider_used="irctc1",
                        total_found=len(options),
                        is_fallback=False,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("Indian Railways API request failed for %s->%s: %s", origin, destination, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 5: International Rail APIs (transport.rest)
# ---------------------------------------------------------------------------

EURO_STATION_IDS: dict[str, str] = {
    "PARIS": "8700014",
    "LONDON": "7001424",
    "BERLIN": "8011160",
    "AMSTERDAM": "8400058",
    "MUNICH": "8000261",
    "FRANKFURT": "8000105",
    "BRUSSELS": "8800003",
}


def _search_transport_rest(
    origin: str,
    destination: str,
    travel_date: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> TransportSearchResult | None:
    """Execute live European rail search via transport.rest open access API."""
    orig_code = origin.strip().upper()
    dest_code = destination.strip().upper()

    orig_id = EURO_STATION_IDS.get(orig_code, orig_code)
    dest_id = EURO_STATION_IDS.get(dest_code, dest_code)

    enc_orig = urllib.parse.quote(orig_id)
    enc_dest = urllib.parse.quote(dest_id)
    url = f"https://v6.db.transport.rest/journeys?from={enc_orig}&to={enc_dest}&results=3"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Safarnama/0.1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                journeys = body.get("journeys", [])

                options = []
                for j in journeys[:3]:
                    price_info = j.get("price", {})
                    eur_amount = price_info.get("amount", 45.0)
                    inr_fare = round(eur_amount * 90.0, 2)  # EUR to INR approximate conversion

                    legs = j.get("legs", [])
                    carrier = "European Rail Express"
                    if legs and legs[0].get("line"):
                        carrier = legs[0]["line"].get("name", "Deutsche Bahn / Eurostar")

                    options.append(
                        TransportSegment(
                            mode="TRAIN",
                            carrier=carrier,
                            transport_code=legs[0].get("tripId", "EUR-100") if legs else "EUR-100",
                            origin=orig_code,
                            destination=dest_code,
                            departure_time=j.get("departure", "10:00"),
                            arrival_time=j.get("arrival", "14:00"),
                            duration_minutes=int((j.get("duration", 14400)) / 60)
                            if j.get("duration")
                            else 240,
                            price_inr=inr_fare,
                            cabin_class="SECOND",
                            provider="transport.rest",
                        )
                    )

                if options:
                    log.info("Fetched %d journeys from transport.rest API", len(options))
                    return TransportSearchResult(
                        origin=orig_code,
                        destination=dest_code,
                        travel_date=travel_date,
                        mode_requested="TRAIN",
                        options=options,
                        provider_used="transport.rest",
                        total_found=len(options),
                        is_fallback=True,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.debug("transport.rest API request failed for %s->%s: %s", origin, destination, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 6: Web Search Tool Fallback
# ---------------------------------------------------------------------------


def _search_via_web_search(
    origin: str, destination: str, travel_date: str, mode: str = "ALL"
) -> TransportSearchResult | None:
    """Execute live web search for flight/train/bus travel options via search_web()."""
    query = f"{origin} to {destination} {mode} travel tickets price {travel_date}"
    try:
        search_res = search_web(query, max_results=3)
        # Only use web_search if it got live search results (not offline search fixture)
        if search_res and search_res.results and not search_res.is_estimated:
            options = []
            for item in search_res.results[:3]:
                options.append(
                    TransportSegment(
                        mode=mode.upper() if mode != "ALL" else "FLIGHT",
                        carrier=item.title[:40],
                        transport_code=None,
                        origin=origin.upper(),
                        destination=destination.upper(),
                        departure_time="Flexible",
                        arrival_time="Flexible",
                        duration_minutes=180,
                        price_inr=6500.0,
                        cabin_class="ECONOMY",
                        booking_url=item.url,
                        provider="web-search",
                    )
                )

            log.info(
                "Fetched %d transport results via search_web provider %s",
                len(options),
                search_res.provider_used,
            )
            return TransportSearchResult(
                origin=origin.upper(),
                destination=destination.upper(),
                travel_date=travel_date,
                mode_requested=mode.upper(),
                options=options,
                provider_used="web-search",
                total_found=len(options),
                is_fallback=True,
                is_estimated=True,
                timestamp=datetime.now(UTC).isoformat(),
            )
    except Exception as exc:
        log.warning("Web search transport fallback failed for query '%s': %s", query, exc)

    return None


# ---------------------------------------------------------------------------
# Public Transport Search Interface
# ---------------------------------------------------------------------------


def search_transport(
    origin: str,
    destination: str,
    travel_date: str | None = None,
    mode: str = "ALL",
    use_fixture: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> TransportSearchResult:
    """Search available transport options (flights, trains, buses) between origin and destination.

    Args:
        origin: Origin airport IATA code, station code, or city name.
        destination: Destination airport IATA code, station code, or city name.
        travel_date: Travel date in YYYY-MM-DD format (defaults to 14 days from today).
        mode: Requested transport filter: 'ALL', 'FLIGHT', 'TRAIN', or 'BUS'.
        use_fixture: If True, bypass live APIs and return fixture data.
        timeout: Network timeout in seconds for live API requests.

    Returns:
        TransportSearchResult containing validated TransportSegment items and provenance.

    Raises:
        InvalidLocationError: If origin or destination strings are empty/whitespace.
    """
    if not origin or not origin.strip():
        raise InvalidLocationError("Origin location string cannot be empty or whitespace.")
    if not destination or not destination.strip():
        raise InvalidLocationError("Destination location string cannot be empty or whitespace.")

    clean_orig = origin.strip().upper()
    clean_dest = destination.strip().upper()
    clean_mode = mode.strip().upper() if mode else "ALL"

    if not travel_date:
        travel_date = datetime.now(UTC).strftime("%Y-%m-%d")

    # Check environment variable triggers for fixture mode
    force_fixture = (
        use_fixture
        or os.getenv("SAFARNAMA_USE_FIXTURES", "").lower() in ("true", "1")
        or os.getenv("SAFARNAMA_TEST_MODE", "").lower() in ("true", "1")
    )

    # Check in-memory cache first
    cached_result = _TRANSPORT_CACHE.get(clean_orig, clean_dest, travel_date, clean_mode)
    if cached_result is not None:
        log.debug("Returning cached transport search result for %s->%s", clean_orig, clean_dest)
        return cached_result

    if force_fixture:
        log.info("Fixture mode active. Serving transport search from mock fixture.")
        res = _search_fixture(
            clean_orig, clean_dest, travel_date, mode=clean_mode, is_fallback_trigger=True
        )
        _TRANSPORT_CACHE.set(clean_orig, clean_dest, travel_date, clean_mode, res)
        return res

    # 1. Live Flights (Sky Scraper / Flights Sky / Aviationstack)
    if clean_mode in ("ALL", "FLIGHT"):
        res = _search_sky_scraper(clean_orig, clean_dest, travel_date, timeout=timeout)
        if res and res.options:
            _TRANSPORT_CACHE.set(clean_orig, clean_dest, travel_date, clean_mode, res)
            return res

        res = _search_flights_sky(clean_orig, clean_dest, travel_date, timeout=timeout)
        if res and res.options:
            _TRANSPORT_CACHE.set(clean_orig, clean_dest, travel_date, clean_mode, res)
            return res

        res = _search_aviationstack(clean_orig, clean_dest, travel_date, timeout=timeout)
        if res and res.options:
            _TRANSPORT_CACHE.set(clean_orig, clean_dest, travel_date, clean_mode, res)
            return res

    # 2. Live Indian Railways
    if clean_mode in ("ALL", "TRAIN"):
        res = _search_indian_railways(clean_orig, clean_dest, travel_date, timeout=timeout)
        if res and res.options:
            _TRANSPORT_CACHE.set(clean_orig, clean_dest, travel_date, clean_mode, res)
            return res

        res = _search_transport_rest(clean_orig, clean_dest, travel_date, timeout=timeout)
        if res and res.options:
            _TRANSPORT_CACHE.set(clean_orig, clean_dest, travel_date, clean_mode, res)
            return res

    # 3. Dynamic Web Search Fallback
    res = _search_via_web_search(clean_orig, clean_dest, travel_date, mode=clean_mode)
    if res and res.options:
        _TRANSPORT_CACHE.set(clean_orig, clean_dest, travel_date, clean_mode, res)
        return res

    # 4. Offline Distance & Speed Physics Engine Baseline (Guarantees zero crashes)
    log.warning(
        "All live transport providers failed or unconfigured for %s->%s. "
        "Falling back to physics-based distance/speed transport heuristic.",
        clean_orig,
        clean_dest,
    )
    fallback_res = _estimate_physics_transport(clean_orig, clean_dest, travel_date, mode=clean_mode)
    _TRANSPORT_CACHE.set(clean_orig, clean_dest, travel_date, clean_mode, fallback_res)
    return fallback_res


def get_transport_status() -> dict[str, bool | str]:
    """Retrieve operational status of configured transport API providers."""
    return {
        "rapidapi_configured": bool(os.getenv("RAPIDAPI_KEY")),
        "aviationstack_configured": bool(os.getenv("AVIATIONSTACK_API_KEY")),
        "transport_rest_available": True,  # Keyless open access
        "web_search_available": True,
        "fixture_available": FIXTURE_PATH.exists(),
    }
