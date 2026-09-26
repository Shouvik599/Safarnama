"""Phase 6 — Intake Functionality (Intake Node).

The entry planning node of Safarnama:
1. Validates and sanitizes user trip input (TripContext).
2. Resolves origin departure hub against static airport and geographical data.
3. Resolves each destination to a canonical passenger gateway, country, and coordinates.
4. Validates and reconciles travel scope (DOMESTIC vs INTERNATIONAL).
5. Computes normalized planning parameters (effective duration, total & per-person budgets).
6. Assembles the InitialPlanningState / TravelPlannerState dictionary.

Architectural Constraints:
- Does NOT perform itinerary, hotel, or activity planning.
- All operations are 100% deterministic and offline, relying on static data.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from src.models.trip import (
    DateMode,
    InitialPlanningState,
    ResolvedLocation,
    TravelScope,
    TripContext,
)
from src.tools.static_data import (
    find_airport,
    find_country,
    get_airports_by_city,
    get_ist_time_difference_hours,
    is_schengen,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class IntakeError(Exception):
    """Base exception for intake node processing errors."""


class IntakeValidationError(IntakeError, ValueError):
    """Raised when user input violates planning constraints or cannot be resolved."""


class IntakeScopeConflictError(IntakeError, ValueError):
    """Raised when user-specified travel scope contradicts geographical destinations."""


# ---------------------------------------------------------------------------
# Known Tourist & Region Gateway Mappings
# ---------------------------------------------------------------------------

# Common aliases for Indian tourist destinations, states, and major hubs
DOMESTIC_GATEWAY_ALIASES: dict[str, dict[str, Any]] = {
    "goa": {
        "iata_code": "GOI",
        "name": "Dabolim Airport / Goa",
        "city": "Goa",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 15.3808,
        "longitude": 73.8314,
    },
    "north goa": {
        "iata_code": "GOX",
        "name": "Manohar International Airport (Mopa) / North Goa",
        "city": "Mopa",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 15.7667,
        "longitude": 73.8667,
    },
    "kerala": {
        "iata_code": "COK",
        "name": "Cochin International Airport / Kerala Gateway",
        "city": "Kochi",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 10.1520,
        "longitude": 76.4019,
    },
    "rajasthan": {
        "iata_code": "JAI",
        "name": "Jaipur International Airport / Rajasthan Gateway",
        "city": "Jaipur",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 26.8242,
        "longitude": 75.8122,
    },
    "delhi": {
        "iata_code": "DEL",
        "name": "Indira Gandhi International Airport",
        "city": "New Delhi",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 28.5562,
        "longitude": 77.1000,
    },
    "new delhi": {
        "iata_code": "DEL",
        "name": "Indira Gandhi International Airport",
        "city": "New Delhi",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 28.5562,
        "longitude": 77.1000,
    },
    "mumbai": {
        "iata_code": "BOM",
        "name": "Chhatrapati Shivaji Maharaj International Airport",
        "city": "Mumbai",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 19.0896,
        "longitude": 72.8656,
    },
    "bombay": {
        "iata_code": "BOM",
        "name": "Chhatrapati Shivaji Maharaj International Airport",
        "city": "Mumbai",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 19.0896,
        "longitude": 72.8656,
    },
    "bangalore": {
        "iata_code": "BLR",
        "name": "Kempegowda International Airport",
        "city": "Bengaluru",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 13.1986,
        "longitude": 77.7066,
    },
    "bengaluru": {
        "iata_code": "BLR",
        "name": "Kempegowda International Airport",
        "city": "Bengaluru",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 13.1986,
        "longitude": 77.7066,
    },
    "kolkata": {
        "iata_code": "CCU",
        "name": "Netaji Subhash Chandra Bose International Airport",
        "city": "Kolkata",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 22.6547,
        "longitude": 88.4467,
    },
    "calcutta": {
        "iata_code": "CCU",
        "name": "Netaji Subhash Chandra Bose International Airport",
        "city": "Kolkata",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 22.6547,
        "longitude": 88.4467,
    },
    "chennai": {
        "iata_code": "MAA",
        "name": "Chennai International Airport",
        "city": "Chennai",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 12.9941,
        "longitude": 80.1709,
    },
    "madras": {
        "iata_code": "MAA",
        "name": "Chennai International Airport",
        "city": "Chennai",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 12.9941,
        "longitude": 80.1709,
    },
    "hyderabad": {
        "iata_code": "HYD",
        "name": "Rajiv Gandhi International Airport",
        "city": "Hyderabad",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 17.2403,
        "longitude": 78.4294,
    },
    "jaipur": {
        "iata_code": "JAI",
        "name": "Jaipur International Airport",
        "city": "Jaipur",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 26.8242,
        "longitude": 75.8122,
    },
    "manali": {
        "iata_code": "KUU",
        "name": "Kullu Manali Airport / Manali Gateway",
        "city": "Kullu",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 31.8763,
        "longitude": 77.1544,
    },
    "kullu": {
        "iata_code": "KUU",
        "name": "Kullu Manali Airport",
        "city": "Kullu",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 31.8763,
        "longitude": 77.1544,
    },
    "shimla": {
        "iata_code": "SLV",
        "name": "Shimla Airport",
        "city": "Shimla",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 31.0818,
        "longitude": 77.0681,
    },
    "ladakh": {
        "iata_code": "IXL",
        "name": "Kushok Bakula Rimpochee Airport / Ladakh Gateway",
        "city": "Leh",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 34.1359,
        "longitude": 77.5465,
    },
    "leh": {
        "iata_code": "IXL",
        "name": "Kushok Bakula Rimpochee Airport",
        "city": "Leh",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 34.1359,
        "longitude": 77.5465,
    },
    "srinagar": {
        "iata_code": "SXR",
        "name": "Srinagar International Airport",
        "city": "Srinagar",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 33.9871,
        "longitude": 74.7744,
    },
    "kashmir": {
        "iata_code": "SXR",
        "name": "Srinagar International Airport / Kashmir Gateway",
        "city": "Srinagar",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 33.9871,
        "longitude": 74.7744,
    },
    "varanasi": {
        "iata_code": "VNS",
        "name": "Lal Bahadur Shastri International Airport",
        "city": "Varanasi",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 25.4524,
        "longitude": 82.8593,
    },
    "agra": {
        "iata_code": "AGR",
        "name": "Agra Airport / Taj Mahal Gateway",
        "city": "Agra",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 27.1558,
        "longitude": 77.9609,
    },
    "amritsar": {
        "iata_code": "ATQ",
        "name": "Sri Guru Ram Dass Jee International Airport",
        "city": "Amritsar",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 31.7096,
        "longitude": 74.7973,
    },
    "udaipur": {
        "iata_code": "UDR",
        "name": "Maharana Pratap Airport",
        "city": "Udaipur",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 24.6177,
        "longitude": 73.8961,
    },
    "andaman": {
        "iata_code": "IXZ",
        "name": "Veer Savarkar International Airport / Andaman Gateway",
        "city": "Port Blair",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 11.6412,
        "longitude": 92.7297,
    },
    "port blair": {
        "iata_code": "IXZ",
        "name": "Veer Savarkar International Airport",
        "city": "Port Blair",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 11.6412,
        "longitude": 92.7297,
    },
    "kochi": {
        "iata_code": "COK",
        "name": "Cochin International Airport",
        "city": "Kochi",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 10.1520,
        "longitude": 76.4019,
    },
    "ahmedabad": {
        "iata_code": "AMD",
        "name": "Sardar Vallabhbhai Patel International Airport",
        "city": "Ahmedabad",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 23.0772,
        "longitude": 72.6347,
    },
    "pune": {
        "iata_code": "PNQ",
        "name": "Pune Airport",
        "city": "Pune",
        "country_code": "IN",
        "country_name": "India",
        "latitude": 18.5821,
        "longitude": 73.9197,
    },
}

# Common international hubs frequented by Indian travelers
INTERNATIONAL_GATEWAY_ALIASES: dict[str, dict[str, Any]] = {
    "dubai": {
        "iata_code": "DXB",
        "name": "Dubai International Airport",
        "city": "Dubai",
        "country_code": "AE",
        "country_name": "United Arab Emirates",
        "latitude": 25.2532,
        "longitude": 55.3657,
        "is_schengen": False,
    },
    "abu dhabi": {
        "iata_code": "AUH",
        "name": "Zayed International Airport",
        "city": "Abu Dhabi",
        "country_code": "AE",
        "country_name": "United Arab Emirates",
        "latitude": 24.4330,
        "longitude": 54.6511,
        "is_schengen": False,
    },
    "paris": {
        "iata_code": "CDG",
        "name": "Charles de Gaulle Airport",
        "city": "Paris",
        "country_code": "FR",
        "country_name": "France",
        "latitude": 49.0097,
        "longitude": 2.5479,
        "is_schengen": True,
    },
    "london": {
        "iata_code": "LHR",
        "name": "Heathrow Airport",
        "city": "London",
        "country_code": "GB",
        "country_name": "United Kingdom",
        "latitude": 51.4700,
        "longitude": -0.4543,
        "is_schengen": False,
    },
    "tokyo": {
        "iata_code": "HND",
        "name": "Tokyo Haneda Airport",
        "city": "Tokyo",
        "country_code": "JP",
        "country_name": "Japan",
        "latitude": 35.5494,
        "longitude": 139.7798,
        "is_schengen": False,
    },
    "singapore": {
        "iata_code": "SIN",
        "name": "Singapore Changi Airport",
        "city": "Singapore",
        "country_code": "SG",
        "country_name": "Singapore",
        "latitude": 1.3644,
        "longitude": 103.9915,
        "is_schengen": False,
    },
    "bangkok": {
        "iata_code": "BKK",
        "name": "Suvarnabhumi Airport",
        "city": "Bangkok",
        "country_code": "TH",
        "country_name": "Thailand",
        "latitude": 13.6900,
        "longitude": 100.7501,
        "is_schengen": False,
    },
    "amsterdam": {
        "iata_code": "AMS",
        "name": "Amsterdam Airport Schiphol",
        "city": "Amsterdam",
        "country_code": "NL",
        "country_name": "Netherlands",
        "latitude": 52.3105,
        "longitude": 4.7683,
        "is_schengen": True,
    },
    "bali": {
        "iata_code": "DPS",
        "name": "Ngurah Rai International Airport",
        "city": "Denpasar / Bali",
        "country_code": "ID",
        "country_name": "Indonesia",
        "latitude": -8.7482,
        "longitude": 115.1672,
        "is_schengen": False,
    },
    "rome": {
        "iata_code": "FCO",
        "name": "Leonardo da Vinci–Fiumicino Airport",
        "city": "Rome",
        "country_code": "IT",
        "country_name": "Italy",
        "latitude": 41.8003,
        "longitude": 12.2389,
        "is_schengen": True,
    },
    "berlin": {
        "iata_code": "BER",
        "name": "Berlin Brandenburg Airport",
        "city": "Berlin",
        "country_code": "DE",
        "country_name": "Germany",
        "latitude": 52.3667,
        "longitude": 13.5033,
        "is_schengen": True,
    },
    "zurich": {
        "iata_code": "ZRH",
        "name": "Zurich Airport",
        "city": "Zurich",
        "country_code": "CH",
        "country_name": "Switzerland",
        "latitude": 47.4582,
        "longitude": 8.5555,
        "is_schengen": True,
    },
}


# ---------------------------------------------------------------------------
# Entity Resolution
# ---------------------------------------------------------------------------


def resolve_location(query: str, *, is_origin: bool = False) -> ResolvedLocation:
    """Resolve a location query string to a canonical passenger gateway.

    Resolution strategy:
    1. Check alias dictionaries (common cities, states, and global hubs).
    2. Check exact airport IATA code (e.g. 'DEL', 'BOM', 'DXB').
    3. Check municipality/city via get_airports_by_city.
    4. Check country profile via find_country (e.g. 'France', 'TH', 'Japan').

    Args:
        query: Location query string (airport IATA, city name, state, or country).
        is_origin: True if resolving departure origin (must be within India).

    Returns:
        ResolvedLocation with coordinates, country code, and gateway information.

    Raises:
        IntakeValidationError: If the location cannot be resolved, or if origin
                               is outside India.
    """
    raw_query = query.strip()
    if not raw_query:
        raise IntakeValidationError("Location query cannot be empty.")

    clean_lower = raw_query.lower()

    # 1. Alias lookup (Domestic)
    if clean_lower in DOMESTIC_GATEWAY_ALIASES:
        data = DOMESTIC_GATEWAY_ALIASES[clean_lower]
        return ResolvedLocation(
            query=raw_query,
            name=data["name"],
            city=data.get("city"),
            country_code=data["country_code"],
            country_name=data.get("country_name", "India"),
            iata_code=data["iata_code"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            is_schengen=False,
            ist_offset_hours=0.0,
        )

    # 1b. Alias lookup (International - destination only)
    if not is_origin and clean_lower in INTERNATIONAL_GATEWAY_ALIASES:
        data = INTERNATIONAL_GATEWAY_ALIASES[clean_lower]
        offset = get_ist_time_difference_hours(data["country_code"]) or 0.0
        return ResolvedLocation(
            query=raw_query,
            name=data["name"],
            city=data.get("city"),
            country_code=data["country_code"],
            country_name=data.get("country_name"),
            iata_code=data["iata_code"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            is_schengen=data.get("is_schengen", False),
            ist_offset_hours=round(offset, 2),
        )

    # 2. Exact IATA lookup (3-letter code)
    if len(raw_query) == 3 and raw_query.isalpha():
        airport = find_airport(raw_query.upper())
        if airport is not None:
            if is_origin and airport.iso_country != "IN":
                raise IntakeValidationError(
                    f"Origin airport '{raw_query.upper()}' is located in {airport.iso_country}. "
                    "Safarnama travel planner departures must originate within India."
                )

            schengen_flag = (
                is_schengen(airport.iso_country) if airport.iso_country != "IN" else False
            )
            offset = (
                get_ist_time_difference_hours(airport.iso_country)
                if airport.iso_country != "IN"
                else 0.0
            )

            country_rec = find_country(airport.iso_country)
            country_name = country_rec.name if country_rec else airport.iso_country

            return ResolvedLocation(
                query=raw_query,
                name=airport.name,
                city=airport.municipality,
                country_code=airport.iso_country,
                country_name=country_name,
                iata_code=airport.iata_code,
                latitude=airport.latitude_deg,
                longitude=airport.longitude_deg,
                is_schengen=schengen_flag,
                ist_offset_hours=round(offset or 0.0, 2),
            )

    # 3. Country Profile Lookup (e.g. 'France', 'Japan', 'TH')
    if not is_origin:
        country = find_country(raw_query)
        if country is not None:
            schengen_flag = country.is_schengen
            offset = get_ist_time_difference_hours(country.country_code) or 0.0

            # Try to associate with a known capital gateway
            capital_iata = None
            lat = 0.0
            lng = 0.0
            if country.capital_coordinates:
                lat = country.capital_coordinates.lat
                lng = country.capital_coordinates.lng

            if country.capital:
                capital_airports = get_airports_by_city(country.capital)
                if capital_airports:
                    capital_iata = capital_airports[0].iata_code
                    lat = capital_airports[0].latitude_deg
                    lng = capital_airports[0].longitude_deg

            return ResolvedLocation(
                query=raw_query,
                name=country.name,
                city=country.capital,
                country_code=country.country_code,
                country_name=country.name,
                iata_code=capital_iata,
                latitude=lat,
                longitude=lng,
                is_schengen=schengen_flag,
                ist_offset_hours=round(offset, 2),
            )

    # 4. Municipality / City Search
    city_airports = get_airports_by_city(raw_query)
    if city_airports:
        # Prioritize commercial passenger airports in India if origin
        if is_origin:
            indian_airports = [a for a in city_airports if a.iso_country == "IN"]
            if not indian_airports:
                raise IntakeValidationError(
                    f"City '{raw_query}' is located outside India. "
                    "Origin must be a location within India."
                )
            selected_airport = indian_airports[0]
        else:
            selected_airport = city_airports[0]

        schengen_flag = (
            is_schengen(selected_airport.iso_country)
            if selected_airport.iso_country != "IN"
            else False
        )
        offset = (
            get_ist_time_difference_hours(selected_airport.iso_country)
            if selected_airport.iso_country != "IN"
            else 0.0
        )

        country_rec = find_country(selected_airport.iso_country)
        country_name = country_rec.name if country_rec else selected_airport.iso_country

        return ResolvedLocation(
            query=raw_query,
            name=selected_airport.name,
            city=selected_airport.municipality or raw_query,
            country_code=selected_airport.iso_country,
            country_name=country_name,
            iata_code=selected_airport.iata_code,
            latitude=selected_airport.latitude_deg,
            longitude=selected_airport.longitude_deg,
            is_schengen=schengen_flag,
            ist_offset_hours=round(offset or 0.0, 2),
        )

    # If unresolved
    if is_origin:
        raise IntakeValidationError(
            f"Could not resolve departure origin '{raw_query}' "
            "to a commercial airport or city in India."
        )
    raise IntakeValidationError(
        f"Could not resolve destination '{raw_query}' to a recognized airport, city, or country."
    )


# ---------------------------------------------------------------------------
# Core Intake Processing
# ---------------------------------------------------------------------------


def process_intake(context: TripContext) -> InitialPlanningState:
    """Process and normalize a TripContext into an InitialPlanningState.

    Performs:
    1. Origin resolution within India.
    2. Destination resolution to canonical gateways and coordinates.
    3. Scope reconciliation and consistency checking.
    4. Duration and budget normalization.
    5. Route waypoint construction.

    Args:
        context: Validated TripContext domain model.

    Returns:
        InitialPlanningState ready for graph orchestration.

    Raises:
        IntakeValidationError: If inputs are invalid or unresolvable.
        IntakeScopeConflictError: If user scope contradicts destination locations.
    """
    warnings: list[str] = []

    # 1. Resolve Origin
    resolved_origin = resolve_location(context.origin, is_origin=True)

    # 2. Resolve Destinations
    resolved_destinations: list[ResolvedLocation] = []
    for dest_str in context.destinations:
        resolved_dest = resolve_location(dest_str, is_origin=False)
        resolved_destinations.append(resolved_dest)

    # 3. Scope Reconciliation
    all_destinations_domestic = all(d.country_code == "IN" for d in resolved_destinations)

    if all_destinations_domestic:
        if context.scope == TravelScope.INTERNATIONAL:
            raise IntakeScopeConflictError(
                "Travel scope is marked INTERNATIONAL, but all resolved destinations "
                f"({', '.join(d.name for d in resolved_destinations)}) are within India."
            )
        resolved_scope = TravelScope.DOMESTIC
    else:
        if context.scope == TravelScope.DOMESTIC:
            non_domestic = [d for d in resolved_destinations if d.country_code != "IN"]
            conflict_names = ", ".join(
                f"{d.name} ({d.country_name or d.country_code})" for d in non_domestic
            )
            raise IntakeScopeConflictError(
                "Travel scope is marked DOMESTIC, but destination(s) "
                f"[{conflict_names}] are outside India."
            )
        resolved_scope = TravelScope.INTERNATIONAL

    # 4. Effective Duration Calculation
    dates = context.dates
    if dates.mode == DateMode.EXACT:
        if dates.start_date and dates.end_date:
            try:
                d1 = datetime.strptime(dates.start_date, "%Y-%m-%d").date()
                d2 = datetime.strptime(dates.end_date, "%Y-%m-%d").date()
                duration_days = (d2 - d1).days + 1
            except ValueError:
                duration_days = dates.duration_days or 1
        else:
            duration_days = dates.duration_days or 1
    else:
        duration_days = dates.duration_days or 1

    if duration_days < 1:
        raise IntakeValidationError(
            f"Calculated trip duration must be >= 1 day (got {duration_days})."
        )

    if dates.mode == DateMode.FLEXIBLE:
        warnings.append(
            f"Dates are flexible (+/-{dates.flexibility_days} days). "
            f"Target duration is {duration_days} days starting around {dates.start_date}."
        )
    elif dates.mode == DateMode.FIND_BEST:
        warnings.append(
            f"Search window set from {dates.window_start} to {dates.window_end} "
            f"for an optimal {duration_days}-day trip."
        )

    # 5. Budget Normalization
    total_travelers = context.party.total_travelers
    total_budget_inr = context.budget.total_budget_inr(context.party)
    daily_budget_per_person = total_budget_inr / (total_travelers * duration_days)

    # 6. Waypoint Route Assembly
    origin_code = resolved_origin.iata_code or resolved_origin.city or resolved_origin.name
    destination_codes = [d.iata_code or d.city or d.name for d in resolved_destinations]
    route = [origin_code] + destination_codes + [origin_code]

    # Advisory notice for international trips
    if resolved_scope == TravelScope.INTERNATIONAL:
        schengen_destinations = [d for d in resolved_destinations if d.is_schengen]
        if schengen_destinations:
            names = ", ".join(d.country_name or d.country_code for d in schengen_destinations)
            warnings.append(
                f"Destinations [{names}] belong to the Schengen Area. "
                "A single uniform Schengen visa applies."
            )

    return InitialPlanningState(
        trip_context=context,
        travel_scope=resolved_scope,
        origin=resolved_origin,
        destinations=resolved_destinations,
        route=route,
        effective_duration_days=duration_days,
        total_budget_inr=round(total_budget_inr, 2),
        daily_budget_per_person_inr=round(daily_budget_per_person, 2),
        warnings=warnings,
    )


def intake_node(state: TripContext | dict[str, Any]) -> dict[str, Any]:
    """Execute the Intake planning step (LangGraph Node Interface).

    Accepts either:
    1. A ``TripContext`` domain model directly.
    2. A dictionary containing a ``"trip_context"`` key or raw trip parameters.

    Returns:
        A dictionary representation conforming to ``TravelPlannerState`` (Section 16).
    """
    if isinstance(state, TripContext):
        context = state
    elif isinstance(state, dict):
        if state.get("trip_context") is not None:
            tc = state["trip_context"]
            context = tc if isinstance(tc, TripContext) else TripContext.model_validate(tc)
        elif state.get("request") is not None:
            req = state["request"]
            context = req if isinstance(req, TripContext) else TripContext.model_validate(req)
        else:
            context = TripContext.model_validate(state)
    else:
        raise IntakeValidationError(f"Invalid input type for intake_node: {type(state).__name__}")

    initial_state = process_intake(context)

    return {
        "trip_context": initial_state.trip_context,
        "travel_scope": initial_state.travel_scope,
        "origin": initial_state.origin.model_dump(),
        "destinations": [d.model_dump() for d in initial_state.destinations],
        "route": initial_state.route,
        "effective_duration_days": initial_state.effective_duration_days,
        "total_budget_inr": initial_state.total_budget_inr,
        "daily_budget_per_person_inr": initial_state.daily_budget_per_person_inr,
        "warnings": initial_state.warnings,
        "errors": [],
        # Placeholders for downstream nodes
        "visa_verdict": None,
        "logistics_plan": None,
        "experience_plan": None,
        "budget_breakdown": None,
        "optimization_status": None,
    }
