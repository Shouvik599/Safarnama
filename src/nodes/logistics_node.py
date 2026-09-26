"""Phase 8 — Logistics Functionality (Logistics Planning Node).

Plans transportation and accommodations for Safarnama itineraries:
1. Determines appropriate transport modes (flight, rail, road) based on route and travel style.
2. Estimates hotel room requirements from party composition (adults + children headcount).
3. Distributes stay durations and dates sequentially across multi-destination itineraries.
4. Searches transport options and selects optimal legs matching travel style and budget.
5. Searches hotel properties and selects accommodations matching preferences and budget.
6. Calculates exact, deterministic party-wide costs for transport and lodging.
7. Preserves booking URLs, provider provenance, and fallback flags.
8. Produces validated, immutable LogisticsPlan domain models conforming to domain contracts.

Architectural Constraints:
- All cost calculations are strictly deterministic in Python math (Rule 36).
- Supports 100% offline fixture-first execution without network reliance.
- Handles provider failures gracefully without crashing.
"""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime, timedelta
from typing import Any

from src.models.logistics import HotelStay, LogisticsPlan, TransportLeg
from src.models.trip import (
    InitialPlanningState,
    ResolvedLocation,
    TravelScope,
    TravelStyle,
    TripContext,
    TripParty,
)
from src.nodes.intake_node import process_intake
from src.tools.hotels import HotelError, search_hotels
from src.tools.transport import TransportError, search_transport

log = logging.getLogger(__name__)

# Default heuristic cost baselines (INR)
DEFAULT_HEURISTIC_FLIGHT_DOMESTIC_INR = 4500.0
DEFAULT_HEURISTIC_FLIGHT_INTL_INR = 22000.0
DEFAULT_HEURISTIC_TRAIN_DOMESTIC_INR = 1850.0

DEFAULT_HEURISTIC_HOTEL_BUDGET_INR = 2500.0
DEFAULT_HEURISTIC_HOTEL_COMFORT_INR = 5500.0
DEFAULT_HEURISTIC_HOTEL_PREMIUM_INR = 11000.0
DEFAULT_HEURISTIC_HOTEL_LUXURY_INR = 24000.0


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class LogisticsError(Exception):
    """Base exception for logistics planning errors."""


class LogisticsPlanningError(LogisticsError, ValueError):
    """Raised when logistics planning cannot proceed due to missing or invalid state."""


# ---------------------------------------------------------------------------
# Party & Room Allocation Heuristics
# ---------------------------------------------------------------------------


def estimate_rooms_required(party: TripParty | None) -> int:
    """Estimate hotel rooms required based on traveler party composition.

    Rules:
    - 1 adult alone -> 1 room.
    - 2 adults -> 1 room.
    - 1 adult + 1 child -> 1 room.
    - 2 adults + 1 young child -> 1 room (family sharing).
    - 2 adults + 2 children -> 2 rooms.
    - Standard occupancy assumes max 2 individuals per room for larger groups.

    Args:
        party: TripParty composition or None (defaults to 1 room).

    Returns:
        Integer number of rooms required (ge=1).
    """
    if party is None or party.total_travelers <= 1:
        return 1

    adults = party.adults
    children = party.children

    # Solo adult with 1 child
    if adults == 1 and children <= 1:
        return 1

    # Couple with 1 child sharing bed/room
    if adults == 2 and children <= 1:
        return 1

    # Couple with 2 children -> 2 rooms
    if adults == 2 and children == 2:
        return 2

    # General group: capacity ~2 persons per room
    total_persons = adults + children
    return max(1, math.ceil(total_persons / 2))


# ---------------------------------------------------------------------------
# Date & Stay Allocation
# ---------------------------------------------------------------------------


def allocate_stay_dates(
    start_date: str | None,
    duration_days: int,
    destinations: list[ResolvedLocation],
) -> list[tuple[ResolvedLocation, str, str, int]]:
    """Distribute trip duration sequentially across destinations.

    Args:
        start_date: Starting date in YYYY-MM-DD format, or None (defaults to +14 days).
        duration_days: Total trip duration in days (ge=1).
        destinations: List of resolved destination locations in visit order.

    Returns:
        List of tuples: (destination, checkin_date, checkout_date, nights).
    """
    if not destinations:
        return []

    # Parse or default start date
    today = datetime.now(UTC).date()
    if start_date:
        try:
            base_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            base_date = today + timedelta(days=14)
    else:
        base_date = today + timedelta(days=14)

    n_dest = len(destinations)
    # Total nights: typically duration_days - 1 for a round trip, with minimum of 1 per destination
    total_nights = max(n_dest, duration_days - 1 if duration_days > 1 else 1)

    base_nights = total_nights // n_dest
    remainder = total_nights % n_dest

    allocations: list[tuple[ResolvedLocation, str, str, int]] = []
    current_checkin = base_date

    for i, dest in enumerate(destinations):
        nights = base_nights + (1 if i < remainder else 0)
        nights = max(1, nights)  # Guarantee at least 1 night
        checkout = current_checkin + timedelta(days=nights)

        allocations.append(
            (
                dest,
                current_checkin.strftime("%Y-%m-%d"),
                checkout.strftime("%Y-%m-%d"),
                nights,
            )
        )
        current_checkin = checkout

    return allocations


# ---------------------------------------------------------------------------
# Helper: Normalize Travel Style
# ---------------------------------------------------------------------------


def _normalize_travel_style(style: TravelStyle | str | None) -> TravelStyle:
    """Normalize string or enum input into canonical TravelStyle."""
    if isinstance(style, TravelStyle):
        return style
    if isinstance(style, str):
        cleaned = style.strip().upper()
        if cleaned in ("BUDGET", "BACKPACKER", "ECONOMY"):
            return TravelStyle.BUDGET
        if cleaned in ("COMFORTABLE", "MID_RANGE", "STANDARD"):
            return TravelStyle.COMFORTABLE
        if cleaned in ("PREMIUM", "SUPERIOR"):
            return TravelStyle.PREMIUM
        if cleaned in ("LUXURY", "DELUXE", "FIRST_CLASS"):
            return TravelStyle.LUXURY
    return TravelStyle.COMFORTABLE


# ---------------------------------------------------------------------------
# Transport Planning
# ---------------------------------------------------------------------------


def plan_transport_legs(
    origin: ResolvedLocation,
    destinations: list[ResolvedLocation],
    stay_allocations: list[tuple[ResolvedLocation, str, str, int]],
    party: TripParty,
    travel_style: TravelStyle = TravelStyle.COMFORTABLE,
    travel_scope: TravelScope = TravelScope.DOMESTIC,
    use_fixture: bool = False,
) -> tuple[list[TransportLeg], list[str]]:
    """Plan all transport legs for the complete round-trip route.

    Route structure:
    Leg 1: Origin -> Destination 1 (Departure Date = Checkin Date 1)
    Leg 2..N: Destination i -> Destination i+1 (Travel Date = Checkout Date i)
    Leg N+1: Destination N -> Origin (Return Date = Checkout Date N)

    Args:
        origin: Resolved departure hub in India.
        destinations: List of resolved destinations.
        stay_allocations: Precomputed stay date tuples for each destination.
        party: Traveler party headcount details.
        travel_style: Travel comfort preference.
        travel_scope: DOMESTIC or INTERNATIONAL.
        use_fixture: Whether to force offline mock fixtures.

    Returns:
        Tuple of (list of TransportLeg, list of non-fatal warning strings).
    """
    legs: list[TransportLeg] = []
    warnings: list[str] = []
    party_size = party.total_travelers if party else 1

    # Assemble sequential route hops: (leg_number, hop_origin, hop_destination, travel_date)
    hops: list[tuple[int, ResolvedLocation, ResolvedLocation, str]] = []

    # Outbound leg
    first_dest, first_checkin, _, _ = stay_allocations[0]
    hops.append((1, origin, first_dest, first_checkin))

    # Inter-destination legs
    for idx in range(len(destinations) - 1):
        from_dest, _, checkout_d, _ = stay_allocations[idx]
        to_dest, _, _, _ = stay_allocations[idx + 1]
        hops.append((idx + 2, from_dest, to_dest, checkout_d))

    # Return leg
    last_dest, _, last_checkout, _ = stay_allocations[-1]
    hops.append((len(hops) + 1, last_dest, origin, last_checkout))

    for leg_num, from_loc, to_loc, leg_date in hops:
        from_code = from_loc.iata_code or from_loc.city or from_loc.name
        to_code = to_loc.iata_code or to_loc.city or to_loc.name

        # Determine mode preference
        is_domestic_hop = from_loc.country_code == "IN" and to_loc.country_code == "IN"
        if not is_domestic_hop or travel_style == TravelStyle.LUXURY:
            mode_filter = "FLIGHT"
        elif travel_style == TravelStyle.BUDGET:
            mode_filter = "ALL"  # Allow trains if available and cheaper
        else:
            mode_filter = "ALL"

        selected_option = None
        is_leg_estimated = False
        provider_name = "physics-heuristic"

        try:
            search_res = search_transport(
                origin=from_code,
                destination=to_code,
                travel_date=leg_date,
                mode=mode_filter,
                use_fixture=use_fixture,
            )

            if search_res and search_res.options:
                is_leg_estimated = search_res.is_estimated
                provider_name = search_res.provider_used

                options = list(search_res.options)
                if travel_style == TravelStyle.BUDGET:
                    # Prefer lowest fare
                    options.sort(key=lambda opt: opt.price_inr)
                    selected_option = options[0]
                elif travel_style == TravelStyle.LUXURY:
                    # Prefer premium class or shortest flight
                    premium_opts = [
                        o for o in options if o.cabin_class.upper() in ("BUSINESS", "FIRST", "1A")
                    ]
                    if premium_opts:
                        premium_opts.sort(key=lambda o: o.duration_minutes)
                        selected_option = premium_opts[0]
                    else:
                        options.sort(key=lambda o: o.duration_minutes)
                        selected_option = options[0]
                else:
                    # Balanced: fastest among reasonable fares
                    options.sort(key=lambda o: (o.duration_minutes, o.price_inr))
                    selected_option = options[0]

        except (TransportError, Exception) as exc:
            log.warning("Transport search error on %s->%s: %s", from_code, to_code, exc)
            warnings.append(
                f"Transport search unavailable for {from_code} -> {to_code}; "
                "fallback estimate applied."
            )

        # Fallback synthesis if no option found
        if selected_option is None:
            is_leg_estimated = True
            provider_name = "physics-heuristic"
            if is_domestic_hop and travel_style == TravelStyle.BUDGET:
                carrier = "Indian Railways"
                mode = "TRAIN"
                code = "12001"
                cabin = "3A"
                price_pp = DEFAULT_HEURISTIC_TRAIN_DOMESTIC_INR
                duration = 360
            elif is_domestic_hop:
                carrier = "IndiGo / Air India"
                mode = "FLIGHT"
                code = "6E-100"
                cabin = "ECONOMY"
                price_pp = DEFAULT_HEURISTIC_FLIGHT_DOMESTIC_INR
                duration = 135
            else:
                carrier = "International Air Partner"
                mode = "FLIGHT"
                code = "IN-901"
                cabin = "BUSINESS" if travel_style == TravelStyle.LUXURY else "ECONOMY"
                price_pp = (
                    DEFAULT_HEURISTIC_FLIGHT_INTL_INR * 2.2
                    if travel_style == TravelStyle.LUXURY
                    else DEFAULT_HEURISTIC_FLIGHT_INTL_INR
                )
                duration = 420

            dep_time = f"{leg_date} 09:00"
            arr_time = f"{leg_date} 13:00"
            booking_url = None
        else:
            carrier = selected_option.carrier
            mode = selected_option.mode
            code = selected_option.transport_code
            cabin = selected_option.cabin_class
            price_pp = selected_option.price_inr
            duration = selected_option.duration_minutes
            booking_url = selected_option.booking_url
            dep_time = selected_option.departure_time
            arr_time = selected_option.arrival_time
            if not is_leg_estimated and selected_option.provider in (
                "physics-heuristic",
                "fixture",
                "web-search",
            ):
                is_leg_estimated = True

            # If time is purely HH:MM, prefix with travel_date
            if dep_time and "T" not in dep_time and " " not in dep_time:
                dep_time = f"{leg_date} {dep_time}"
            if arr_time and "T" not in arr_time and " " not in arr_time:
                arr_time = f"{leg_date} {arr_time}"

        price_per_person = round(float(price_pp), 2)
        total_price = round(price_per_person * party_size, 2)

        leg = TransportLeg(
            leg_number=leg_num,
            mode=mode,
            carrier=carrier,
            transport_code=code,
            origin=from_code,
            destination=to_code,
            departure_datetime=dep_time,
            arrival_datetime=arr_time,
            duration_minutes=duration,
            cabin_class=cabin,
            price_per_person_inr=price_per_person,
            total_price_inr=total_price,
            booking_url=booking_url,
            provider=provider_name,
            is_estimated=is_leg_estimated,
            notes=f"Planned for {party_size} traveler{'s' if party_size > 1 else ''}.",
        )
        legs.append(leg)

    return legs, warnings


# ---------------------------------------------------------------------------
# Accommodation Planning
# ---------------------------------------------------------------------------


def plan_hotel_stays(
    destinations: list[ResolvedLocation],
    stay_allocations: list[tuple[ResolvedLocation, str, str, int]],
    party: TripParty,
    rooms_required: int,
    travel_style: TravelStyle = TravelStyle.COMFORTABLE,
    use_fixture: bool = False,
) -> tuple[list[HotelStay], list[str]]:
    """Plan hotel stays for all destinations.

    Args:
        destinations: List of resolved destinations.
        stay_allocations: Precomputed stay date tuples for each destination.
        party: Traveler party details.
        rooms_required: Estimated number of rooms required.
        travel_style: User's travel comfort preference.
        use_fixture: Whether to force offline mock fixtures.

    Returns:
        Tuple of (list of HotelStay, list of non-fatal warning strings).
    """
    stays: list[HotelStay] = []
    warnings: list[str] = []
    guests_count = party.total_travelers if party else 2

    # Target star rating based on travel style
    if travel_style == TravelStyle.BUDGET:
        target_stars = 3
        heuristic_rate = DEFAULT_HEURISTIC_HOTEL_BUDGET_INR
    elif travel_style == TravelStyle.LUXURY:
        target_stars = 5
        heuristic_rate = DEFAULT_HEURISTIC_HOTEL_LUXURY_INR
    elif travel_style == TravelStyle.PREMIUM:
        target_stars = 4
        heuristic_rate = DEFAULT_HEURISTIC_HOTEL_PREMIUM_INR
    else:
        target_stars = 3
        heuristic_rate = DEFAULT_HEURISTIC_HOTEL_COMFORT_INR

    for dest, checkin_d, checkout_d, nights in stay_allocations:
        dest_query = dest.city or dest.name or dest.iata_code or "Destination"
        selected_hotel = None
        is_stay_estimated = False
        provider_name = "location-heuristic"

        try:
            # Query hotel search tool
            hotel_res = search_hotels(
                destination=dest_query,
                checkin_date=checkin_d,
                checkout_date=checkout_d,
                nights=nights,
                guests=guests_count,
                star_rating=target_stars,
                use_fixture=use_fixture,
            )

            # If no options found at target star rating, retry without star filter
            if not hotel_res or not hotel_res.options:
                hotel_res = search_hotels(
                    destination=dest_query,
                    checkin_date=checkin_d,
                    checkout_date=checkout_d,
                    nights=nights,
                    guests=guests_count,
                    star_rating=None,
                    use_fixture=use_fixture,
                )

            if hotel_res and hotel_res.options:
                is_stay_estimated = hotel_res.is_estimated
                provider_name = hotel_res.provider_used
                opts = list(hotel_res.options)

                if travel_style == TravelStyle.BUDGET:
                    # Lowest nightly rate
                    opts.sort(key=lambda h: h.price_per_night_inr)
                    selected_hotel = opts[0]
                elif travel_style == TravelStyle.LUXURY:
                    # Highest stars and guest reviews
                    opts.sort(
                        key=lambda h: (h.star_rating or 0, h.user_rating or 0.0),
                        reverse=True,
                    )
                    selected_hotel = opts[0]
                else:
                    # Balanced: high guest rating with reasonable price
                    opts.sort(
                        key=lambda h: (h.user_rating or 7.0) - (h.price_per_night_inr / 20000.0),
                        reverse=True,
                    )
                    selected_hotel = opts[0]

        except (HotelError, Exception) as exc:
            log.warning("Hotel search error for destination '%s': %s", dest_query, exc)
            warnings.append(
                f"Hotel search unavailable for {dest_query}; fallback lodging estimate applied."
            )

        # Fallback synthesis if no option found
        if selected_hotel is None:
            is_stay_estimated = True
            provider_name = "location-heuristic"
            hotel_name = f"{dest_query} Central Stay"
            star_rating = target_stars
            user_rating = 8.0
            price_per_night = heuristic_rate
            amenities = ["Free Wi-Fi", "Air Conditioning", "24-Hour Front Desk"]
            address = f"City Center, {dest_query}"
            booking_url = None
        else:
            hotel_name = selected_hotel.name
            star_rating = selected_hotel.star_rating
            user_rating = selected_hotel.user_rating
            price_per_night = selected_hotel.price_per_night_inr
            amenities = selected_hotel.amenities
            address = selected_hotel.address
            booking_url = selected_hotel.booking_url
            if not is_stay_estimated and selected_hotel.provider in (
                "location-heuristic",
                "fixture",
                "web-search",
            ):
                is_stay_estimated = True

        price_per_room = round(float(price_per_night), 2)
        total_stay_cost = round(price_per_room * nights * rooms_required, 2)

        stay = HotelStay(
            destination=dest_query,
            hotel_name=hotel_name,
            star_rating=star_rating,
            user_rating=user_rating,
            checkin_date=checkin_d,
            checkout_date=checkout_d,
            nights=nights,
            rooms_required=rooms_required,
            price_per_room_per_night_inr=price_per_room,
            total_accommodation_cost_inr=total_stay_cost,
            amenities=amenities,
            address=address,
            booking_url=booking_url,
            provider=provider_name,
            is_estimated=is_stay_estimated,
            notes=f"Booked for {rooms_required} room{'s' if rooms_required > 1 else ''}.",
        )
        stays.append(stay)

    return stays, warnings


# ---------------------------------------------------------------------------
# Public Processing Interface
# ---------------------------------------------------------------------------


def process_logistics(
    state: InitialPlanningState | TripContext | dict[str, Any],
    use_fixture: bool = False,
) -> LogisticsPlan:
    """Execute complete logistics planning for transport legs and hotel stays.

    Accepts:
    1. An ``InitialPlanningState`` domain model from the intake node.
    2. A ``TripContext`` domain model (automatically resolved via intake).
    3. A state dictionary from the LangGraph workflow.

    Args:
        state: Initial planning state or context.
        use_fixture: Force offline mock fixture evaluation.

    Returns:
        Validated, immutable ``LogisticsPlan`` domain model.

    Raises:
        LogisticsPlanningError: If state lacks destinations or required context.
    """
    # 1. Normalize input state
    if isinstance(state, InitialPlanningState):
        planning_state = state
        context = state.trip_context
        origin = state.origin
        destinations = state.destinations
        duration_days = state.effective_duration_days
        total_budget = state.total_budget_inr
        scope = state.travel_scope
    elif isinstance(state, TripContext):
        planning_state = process_intake(state)
        context = planning_state.trip_context
        origin = planning_state.origin
        destinations = planning_state.destinations
        duration_days = planning_state.effective_duration_days
        total_budget = planning_state.total_budget_inr
        scope = planning_state.travel_scope
    elif isinstance(state, dict):
        if "trip_context" in state and isinstance(state["trip_context"], TripContext):
            context = state["trip_context"]
        elif "trip_context" in state and isinstance(state["trip_context"], dict):
            context = TripContext.model_validate(state["trip_context"])
        elif "origin" in state and "destinations" in state and "trip_context" not in state:
            context = TripContext.model_validate(state)
        else:
            context = TripContext.model_validate(state)

        # Check if resolved locations are already present
        has_resolved = (
            "origin" in state
            and "destinations" in state
            and isinstance(state["destinations"], list)
        )
        if has_resolved:
            try:
                origin = (
                    state["origin"]
                    if isinstance(state["origin"], ResolvedLocation)
                    else ResolvedLocation.model_validate(state["origin"])
                )
                destinations = [
                    d if isinstance(d, ResolvedLocation) else ResolvedLocation.model_validate(d)
                    for d in state["destinations"]
                ]
                duration_days = int(state.get("effective_duration_days", 5))
                total_budget = float(state.get("total_budget_inr", 50000.0))
                scope = TravelScope(state.get("travel_scope", TravelScope.DOMESTIC))
            except Exception:
                planning_state = process_intake(context)
                origin = planning_state.origin
                destinations = planning_state.destinations
                duration_days = planning_state.effective_duration_days
                total_budget = planning_state.total_budget_inr
                scope = planning_state.travel_scope
        else:
            planning_state = process_intake(context)
            origin = planning_state.origin
            destinations = planning_state.destinations
            duration_days = planning_state.effective_duration_days
            total_budget = planning_state.total_budget_inr
            scope = planning_state.travel_scope
    else:
        raise LogisticsPlanningError(
            f"Unsupported input type for logistics planning: {type(state).__name__}"
        )

    if not destinations:
        raise LogisticsPlanningError("At least one destination is required for logistics planning.")

    # 2. Extract configuration
    party = context.party
    travel_style = _normalize_travel_style(context.travel_style)
    start_date = context.dates.start_date

    plan_warnings: list[str] = []

    # 3. Estimate rooms required
    rooms_required = estimate_rooms_required(party)
    if rooms_required > 1:
        plan_warnings.append(
            f"Party of {party.adults} adult(s) and {party.children} child(ren) "
            f"allocated {rooms_required} rooms."
        )

    # 4. Allocate stay dates across destinations
    stay_allocations = allocate_stay_dates(
        start_date=start_date,
        duration_days=duration_days,
        destinations=destinations,
    )

    # 5. Plan transport legs
    transport_legs, transport_warnings = plan_transport_legs(
        origin=origin,
        destinations=destinations,
        stay_allocations=stay_allocations,
        party=party,
        travel_style=travel_style,
        travel_scope=scope,
        use_fixture=use_fixture,
    )
    plan_warnings.extend(transport_warnings)

    # 6. Plan hotel stays
    hotel_stays, hotel_warnings = plan_hotel_stays(
        destinations=destinations,
        stay_allocations=stay_allocations,
        party=party,
        rooms_required=rooms_required,
        travel_style=travel_style,
        use_fixture=use_fixture,
    )
    plan_warnings.extend(hotel_warnings)

    # 7. Aggregate financial totals deterministically
    total_transport_cost = round(sum(leg.total_price_inr for leg in transport_legs), 2)
    total_accommodation_cost = round(
        sum(stay.total_accommodation_cost_inr for stay in hotel_stays), 2
    )

    # 8. Check budget feasibility warnings
    combined_logistics_cost = total_transport_cost + total_accommodation_cost
    if total_budget > 0 and combined_logistics_cost > total_budget:
        plan_warnings.append(
            f"Total logistics cost (₹{combined_logistics_cost:,.2f}) exceeds "
            f"total trip budget (₹{total_budget:,.2f}). "
            "Optimizer adjustment or budget increase recommended."
        )

    # 9. Format human-readable route summary
    # e.g. "Delhi → Mumbai (FLIGHT) → Delhi (FLIGHT)"
    route_parts = [origin.city or origin.name]
    for leg in transport_legs:
        route_parts.append(f"({leg.mode}) → {leg.destination}")
    route_summary = " ".join(route_parts)

    is_any_estimated = any(leg.is_estimated for leg in transport_legs) or any(
        stay.is_estimated for stay in hotel_stays
    )

    return LogisticsPlan(
        transport_legs=transport_legs,
        hotel_stays=hotel_stays,
        total_transport_cost_inr=total_transport_cost,
        total_accommodation_cost_inr=total_accommodation_cost,
        route_summary=route_summary,
        warnings=plan_warnings,
        is_estimated=is_any_estimated,
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# LangGraph Node Interface
# ---------------------------------------------------------------------------


def logistics_node(
    state: dict[str, Any] | InitialPlanningState,
) -> dict[str, Any]:
    """LangGraph node function for logistics planning.

    Args:
        state: State dictionary or InitialPlanningState from the graph.

    Returns:
        State update dictionary containing the generated 'logistics_plan'.
    """
    plan = process_logistics(state)
    return {
        "logistics_plan": plan,
    }
