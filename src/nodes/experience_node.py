"""Phase 9 — Experience Functionality (Experience Planning Node).

Plans attractions, cultural activities, dining experiences, and weather-aware pacing:
1. Distributes itinerary days across resolved destinations.
2. Selects points of interest (attractions, landmarks, cultural spots) matching user preferences.
3. Prioritizes explicitly requested must-visit sights (context.must_visit).
4. Discovers real dining spots and recommends authentic regional meals for breakfast, lunch, dinner.
5. Evaluates meteorological conditions via the weather tool and applies indoor substitutions
   for outdoor activities when adverse weather (rain, storms, extreme temperatures) is forecast.
6. Calibrates activity density and dayparts to match requested pace (RELAXED, BALANCED, PACKED).
7. Associates overnight accommodations and booking URLs from LogisticsPlan where available.
8. Calculates deterministic day-level and trip-wide activity, food, and local transit costs.
9. Produces validated, immutable ExperiencePlan domain models conforming to domain contracts.

Architectural Constraints:
- 100% deterministic calculation of day-level and trip-wide expenses (Rule 36).
- Supports 100% offline fixture-first execution without network reliance.
- Handles search tool errors or empty place discoveries gracefully with zero crashes.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from src.models.itinerary import (
    ActivityCategory,
    ActivitySlot,
    DayMeal,
    Daypart,
    DayPlan,
    ExperiencePlan,
    PointOfInterest,
)
from src.models.logistics import LogisticsPlan
from src.models.places import PlaceItem
from src.models.trip import (
    InitialPlanningState,
    Pace,
    ResolvedLocation,
    TravelScope,
    TripContext,
    TripParty,
)
from src.nodes.intake_node import process_intake
from src.tools.places import PlaceError, search_places
from src.tools.weather import DailyWeatherForecast, WeatherError, get_weather_forecast

log = logging.getLogger(__name__)

# Default heuristic costs (per person in INR)
DEFAULT_ATTRACTION_COST_DOMESTIC_INR = 250.0
DEFAULT_ATTRACTION_COST_INTL_INR = 1800.0

DEFAULT_MEAL_COST_BREAKFAST_INR = 200.0
DEFAULT_MEAL_COST_LUNCH_INR = 500.0
DEFAULT_MEAL_COST_DINNER_INR = 800.0

DEFAULT_LOCAL_TRANSIT_PER_DAY_DOMESTIC_INR = 500.0
DEFAULT_LOCAL_TRANSIT_PER_DAY_INTL_INR = 1800.0

# Keywords for classifying places into ActivityCategory
OUTDOOR_KEYWORDS = {
    "garden",
    "park",
    "beach",
    "mountain",
    "hike",
    "trail",
    "lake",
    "waterfall",
    "wildlife",
    "safari",
    "outdoor",
    "fort",
    "viewpoint",
    "ghat",
    "monument",
    "arch",
    "sea",
    "promenade",
    "waterfront",
    "plaza",
    "square",
    "pier",
    "bridge",
    "harbor",
    "harbour",
    "lookout",
    "boardwalk",
}

INDOOR_KEYWORDS = {
    "museum",
    "gallery",
    "palace",
    "temple",
    "church",
    "mosque",
    "shrine",
    "mall",
    "market",
    "bazaar",
    "theatre",
    "theater",
    "aquarium",
    "indoor",
}


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class ExperienceError(Exception):
    """Base exception for experience node planning errors."""


class ExperiencePlanningError(ExperienceError, ValueError):
    """Raised when experience planning cannot proceed due to missing or invalid inputs."""


# ---------------------------------------------------------------------------
# Helpers: Activity Classification & Weather Suitability
# ---------------------------------------------------------------------------


def _classify_activity_category(name: str, desc: str | None = None) -> ActivityCategory:
    """Infer broad ActivityCategory from attraction title and description."""
    text = f"{name} {desc or ''}".lower()

    if any(k in text for k in ("museum", "gallery", "exhibit")):
        return ActivityCategory.MUSEUM
    if any(k in text for k in ("temple", "shrine", "mosque", "church", "cathedral", "spiritual")):
        return ActivityCategory.SPIRITUAL
    if any(k in text for k in ("park", "garden", "lake", "nature", "river", "botanic")):
        return ActivityCategory.NATURE
    if any(k in text for k in ("fort", "monument", "ruins", "historical", "palace", "heritage")):
        return ActivityCategory.HISTORY_HERITAGE
    if any(k in text for k in ("beach", "coast", "cove", "sea")):
        return ActivityCategory.BEACH
    if any(k in text for k in ("bazaar", "market", "shopping", "mall")):
        return ActivityCategory.SHOPPING
    if any(k in text for k in ("safari", "wildlife", "zoo", "sanctuary")):
        return ActivityCategory.WILDLIFE
    if any(k in text for k in ("adventure", "trek", "hike", "rafting", "climbing")):
        return ActivityCategory.ADVENTURE
    return ActivityCategory.LOCAL_EXPERIENCE


def _is_outdoor_poi(poi: PointOfInterest) -> bool:
    """Determine if a point of interest is predominantly an outdoor activity."""
    if poi.category in (
        ActivityCategory.NATURE,
        ActivityCategory.BEACH,
        ActivityCategory.ADVENTURE,
        ActivityCategory.WILDLIFE,
    ):
        return True
    text = f"{poi.name} {poi.description or ''}".lower()
    return any(k in text for k in OUTDOOR_KEYWORDS)


# ---------------------------------------------------------------------------
# POI & Dining Discovery
# ---------------------------------------------------------------------------


def _fetch_destination_pois(
    dest: ResolvedLocation,
    must_visits: list[str],
    is_international: bool,
    use_fixture: bool = False,
) -> list[PointOfInterest]:
    """Retrieve POIs from places tool, incorporating user must-visit preferences."""
    dest_name = dest.city or dest.name or dest.iata_code or "Destination"
    pois: list[PointOfInterest] = []
    seen_names: set[str] = set()

    # 1. Fetch live or fixture attractions
    try:
        res = search_places(
            destination=dest_name,
            category="ATTRACTION",
            max_results=8,
            use_fixture=use_fixture,
        )
        if res and res.items:
            for item in res.items:
                cat = _classify_activity_category(item.name, item.description)
                poi = PointOfInterest(
                    name=item.name,
                    category=cat,
                    city=dest_name,
                    country=dest.country_name,
                    address=item.address,
                    latitude=item.latitude,
                    longitude=item.longitude,
                    description=item.description,
                    estimated_duration_minutes=90,
                    estimated_cost_inr=item.estimated_cost_inr,
                    is_must_visit=False,
                    maps_url=item.maps_url,
                    provider=item.provider,
                )
                pois.append(poi)
                seen_names.add(item.name.strip().lower())
    except (PlaceError, Exception) as exc:
        log.warning("Places search error for attractions in %s: %s", dest_name, exc)

    # 2. Add fallback POIs if search returned empty
    if not pois:
        default_cost = (
            DEFAULT_ATTRACTION_COST_INTL_INR
            if is_international
            else DEFAULT_ATTRACTION_COST_DOMESTIC_INR
        )
        fallback_poi1 = PointOfInterest(
            name=f"{dest_name} Heritage Monument",
            category=ActivityCategory.HISTORY_HERITAGE,
            city=dest_name,
            country=dest.country_name,
            address=f"Central District, {dest_name}",
            latitude=dest.latitude,
            longitude=dest.longitude,
            description=f"Iconic historical monument and cultural landmark of {dest_name}.",
            estimated_duration_minutes=90,
            estimated_cost_inr=default_cost,
            is_must_visit=False,
            provider="category-heuristic",
        )
        fallback_poi2 = PointOfInterest(
            name=f"{dest_name} Cultural Museum",
            category=ActivityCategory.MUSEUM,
            city=dest_name,
            country=dest.country_name,
            address=f"Museum Road, {dest_name}",
            latitude=dest.latitude,
            longitude=dest.longitude,
            description=f"Preserving the art, history, and craftsmanship of {dest_name}.",
            estimated_duration_minutes=120,
            estimated_cost_inr=default_cost * 0.8,
            is_must_visit=False,
            provider="category-heuristic",
        )
        fallback_poi3 = PointOfInterest(
            name=f"{dest_name} Public Gardens & Promenade",
            category=ActivityCategory.NATURE,
            city=dest_name,
            country=dest.country_name,
            address=f"Green Valley Park, {dest_name}",
            latitude=dest.latitude,
            longitude=dest.longitude,
            description=f"Scenic green public park and botanical garden in {dest_name}.",
            estimated_duration_minutes=75,
            estimated_cost_inr=0.0,
            is_must_visit=False,
            provider="category-heuristic",
        )
        pois.extend([fallback_poi1, fallback_poi2, fallback_poi3])

    # 3. Prioritize must-visits specified by the user
    for mv in must_visits:
        mv_clean = mv.strip().lower()
        # Check if already present in discovered POIs
        matched = False
        for i, p in enumerate(pois):
            if mv_clean in p.name.lower() or p.name.lower() in mv_clean:
                # Mark as must-visit and move to front
                updated = p.model_copy(update={"is_must_visit": True})
                pois[i] = updated
                matched = True
                break
        if not matched:
            # Inject must-visit as a high-priority POI
            mv_poi = PointOfInterest(
                name=mv.strip(),
                category=ActivityCategory.LOCAL_EXPERIENCE,
                city=dest_name,
                country=dest.country_name,
                address=f"{mv.strip()}, {dest_name}",
                latitude=dest.latitude,
                longitude=dest.longitude,
                description=f"Prominent point of interest requested by traveler: {mv.strip()}.",
                estimated_duration_minutes=90,
                estimated_cost_inr=DEFAULT_ATTRACTION_COST_DOMESTIC_INR,
                is_must_visit=True,
                provider="curated",
            )
            pois.insert(0, mv_poi)
            seen_names.add(mv_clean)

    return pois


def _fetch_destination_dining(
    dest: ResolvedLocation,
    use_fixture: bool = False,
) -> tuple[list[PlaceItem], list[PlaceItem]]:
    """Retrieve restaurants and cafes for a destination."""
    dest_name = dest.city or dest.name or dest.iata_code or "Destination"
    restaurants: list[PlaceItem] = []
    cafes: list[PlaceItem] = []

    try:
        res_rest = search_places(
            destination=dest_name,
            category="RESTAURANT",
            max_results=6,
            use_fixture=use_fixture,
        )
        if res_rest and res_rest.items:
            restaurants = list(res_rest.items)
    except Exception as exc:
        log.warning("Places search error for restaurants in %s: %s", dest_name, exc)

    try:
        res_cafe = search_places(
            destination=dest_name,
            category="CAFE",
            max_results=4,
            use_fixture=use_fixture,
        )
        if res_cafe and res_cafe.items:
            cafes = list(res_cafe.items)
    except Exception as exc:
        log.warning("Places search error for cafes in %s: %s", dest_name, exc)

    return restaurants, cafes


# ---------------------------------------------------------------------------
# Weather Forecast Lookup
# ---------------------------------------------------------------------------


def _fetch_destination_weather(
    dest: ResolvedLocation,
    start_date: str | None,
    duration_days: int,
    use_fixture: bool = False,
) -> dict[str, DailyWeatherForecast]:
    """Retrieve daily meteorological forecasts for a destination."""
    forecast_map: dict[str, DailyWeatherForecast] = {}
    try:
        wf_res = get_weather_forecast(
            latitude=dest.latitude,
            longitude=dest.longitude,
            start_date=start_date,
            days=max(1, duration_days),
            use_fixture=use_fixture,
            destination=dest.city or dest.name,
        )
        if wf_res and wf_res.daily_forecasts:
            for df in wf_res.daily_forecasts:
                forecast_map[df.date] = df
    except (WeatherError, Exception) as exc:
        log.warning("Weather tool error for destination %s: %s", dest.name, exc)

    return forecast_map


# ---------------------------------------------------------------------------
# Public Processing Interface
# ---------------------------------------------------------------------------


def process_experience(
    state: InitialPlanningState | TripContext | dict[str, Any],
    logistics_plan: LogisticsPlan | None = None,
    use_fixture: bool = False,
) -> ExperiencePlan:
    """Execute complete experience planning for attractions, dining, and weather adaptation.

    Accepts:
    1. An ``InitialPlanningState`` domain model from intake.
    2. A ``TripContext`` domain model (automatically resolved via intake).
    3. A state dictionary from the LangGraph workflow.

    Args:
        state: Planning state or trip context.
        logistics_plan: Optional LogisticsPlan containing hotel stays.
        use_fixture: Force offline mock fixture evaluation.

    Returns:
        Validated, immutable ``ExperiencePlan`` domain model.

    Raises:
        ExperiencePlanningError: If state lacks destinations or required context.
    """
    # 1. Normalize input state
    if isinstance(state, InitialPlanningState):
        context = state.trip_context
        destinations = state.destinations
        duration_days = state.effective_duration_days
        scope = state.travel_scope
    elif isinstance(state, TripContext):
        intake_state = process_intake(state)
        context = intake_state.trip_context
        destinations = intake_state.destinations
        duration_days = intake_state.effective_duration_days
        scope = intake_state.travel_scope
    elif isinstance(state, dict):
        if "trip_context" in state and isinstance(state["trip_context"], TripContext):
            context = state["trip_context"]
        elif "trip_context" in state and isinstance(state["trip_context"], dict):
            context = TripContext.model_validate(state["trip_context"])
        else:
            context = TripContext.model_validate(state)

        # Extract resolved destinations if present
        if (
            "destinations" in state
            and isinstance(state["destinations"], list)
            and len(state["destinations"]) > 0
        ):
            try:
                destinations = [
                    d if isinstance(d, ResolvedLocation) else ResolvedLocation.model_validate(d)
                    for d in state["destinations"]
                ]
                duration_days = int(state.get("effective_duration_days", 5))
                scope = TravelScope(state.get("travel_scope", TravelScope.DOMESTIC))
            except Exception:
                intake_state = process_intake(context)
                destinations = intake_state.destinations
                duration_days = intake_state.effective_duration_days
                scope = intake_state.travel_scope
        else:
            intake_state = process_intake(context)
            destinations = intake_state.destinations
            duration_days = intake_state.effective_duration_days
            scope = intake_state.travel_scope

        # Check if logistics plan is in state dict
        if logistics_plan is None and "logistics_plan" in state:
            lp_raw = state["logistics_plan"]
            if isinstance(lp_raw, LogisticsPlan):
                logistics_plan = lp_raw
            elif isinstance(lp_raw, dict):
                try:
                    logistics_plan = LogisticsPlan.model_validate(lp_raw)
                except Exception:
                    logistics_plan = None
    else:
        raise ExperiencePlanningError(
            f"Unsupported input type for experience planning: {type(state).__name__}"
        )

    if not destinations:
        raise ExperiencePlanningError(
            "At least one destination is required for experience planning."
        )

    # 2. Extract context parameters
    party = context.party or TripParty(adults=2, children=0)
    party_size = party.total_travelers
    pace = context.pace or Pace.BALANCED
    must_visits = list(getattr(context, "must_visits", getattr(context, "must_visit", [])))
    start_date_str = context.dates.start_date
    is_intl = scope == TravelScope.INTERNATIONAL

    # Determine base calendar start date
    today = datetime.now(UTC).date()
    if start_date_str:
        try:
            base_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            base_date = today + timedelta(days=14)
    else:
        base_date = today + timedelta(days=14)

    # 3. Distribute trip days across destinations
    n_dest = len(destinations)
    base_days_per_dest = duration_days // n_dest
    rem_days = duration_days % n_dest

    day_destination_map: list[ResolvedLocation] = []
    for i, d in enumerate(destinations):
        count = base_days_per_dest + (1 if i < rem_days else 0)
        count = max(1, count)
        for _ in range(count):
            day_destination_map.append(d)

    # Truncate or extend to match duration_days exactly
    day_destination_map = day_destination_map[:duration_days]
    while len(day_destination_map) < duration_days:
        day_destination_map.append(destinations[-1])

    # 4. Map hotel stays from logistics_plan by destination city
    hotel_by_city: dict[str, tuple[str, str | None]] = {}
    if logistics_plan and logistics_plan.hotel_stays:
        for stay in logistics_plan.hotel_stays:
            city_key = stay.destination.strip().lower()
            hotel_by_city[city_key] = (stay.hotel_name, stay.booking_url)

    # 5. Pre-fetch POIs, dining, and weather for all destinations
    dest_pois: dict[str, list[PointOfInterest]] = {}
    dest_dining: dict[str, tuple[list[PlaceItem], list[PlaceItem]]] = {}
    dest_weather: dict[str, dict[str, DailyWeatherForecast]] = {}

    for d in destinations:
        key = d.city or d.name or d.iata_code or "Destination"
        dest_pois[key] = _fetch_destination_pois(d, must_visits, is_intl, use_fixture=use_fixture)
        dest_dining[key] = _fetch_destination_dining(d, use_fixture=use_fixture)
        dest_weather[key] = _fetch_destination_weather(
            d, base_date.strftime("%Y-%m-%d"), duration_days, use_fixture=use_fixture
        )

    # 6. Build DayPlan for each day
    day_plans: list[DayPlan] = []
    must_visits_fulfilled: set[str] = set()
    total_weather_substitutions = 0
    warnings: list[str] = []

    # Number of activity slots per day based on Pace
    if pace == Pace.RELAXED:
        slots_per_day = 1
    elif pace == Pace.PACKED:
        slots_per_day = 3
    else:
        slots_per_day = 2

    # Pointers to track used POIs and restaurants per destination
    poi_idx_map: dict[str, int] = {k: 0 for k in dest_pois}
    rest_idx_map: dict[str, int] = {k: 0 for k in dest_pois}
    cafe_idx_map: dict[str, int] = {k: 0 for k in dest_pois}

    for day_num in range(1, duration_days + 1):
        day_date = base_date + timedelta(days=day_num - 1)
        day_date_str = day_date.strftime("%Y-%m-%d")

        current_dest = day_destination_map[day_num - 1]
        dest_key = current_dest.city or current_dest.name or current_dest.iata_code or "Destination"
        pois_available = dest_pois.get(dest_key, [])
        restaurants_available, cafes_available = dest_dining.get(dest_key, ([], []))
        weather_forecasts = dest_weather.get(dest_key, {})

        day_forecast = weather_forecasts.get(day_date_str)
        is_outdoor = day_forecast.is_outdoor_friendly if day_forecast else True
        weather_suitability = (
            "Outdoor activities suitable."
            if is_outdoor
            else "Precipitation expected; indoor activities recommended."
        )
        weather_summary = (
            f"{day_forecast.condition}, {day_forecast.temp_max_c:.0f}°C / "
            f"{day_forecast.temp_min_c:.0f}°C. {weather_suitability}"
            if day_forecast
            else "Pleasant travel weather expected."
        )

        # A. Schedule activities for the day
        activities: list[ActivitySlot] = []
        dayparts = [Daypart.MORNING, Daypart.AFTERNOON, Daypart.EVENING]

        for s_idx in range(slots_per_day):
            dp = dayparts[s_idx % len(dayparts)]
            p_idx = poi_idx_map[dest_key]

            # Pick next POI (cycle if pool exhausted)
            selected_poi = pois_available[p_idx % len(pois_available)]
            poi_idx_map[dest_key] = p_idx + 1

            if selected_poi.is_must_visit:
                must_visits_fulfilled.add(selected_poi.name.strip())

            # Check weather substitution: if weather is bad and POI is outdoor
            if not is_outdoor and _is_outdoor_poi(selected_poi):
                # Search for an indoor alternative from POI pool
                indoor_alt = None
                for candidate in pois_available:
                    if not _is_outdoor_poi(candidate) and candidate.name != selected_poi.name:
                        indoor_alt = candidate
                        break

                if not indoor_alt:
                    # Synthesize indoor alternative
                    indoor_alt = PointOfInterest(
                        name=f"{dest_key} Art Gallery & Cultural Center",
                        category=ActivityCategory.MUSEUM,
                        city=dest_key,
                        country=current_dest.country_name,
                        address=f"Arts Quarter, {dest_key}",
                        latitude=current_dest.latitude,
                        longitude=current_dest.longitude,
                        description=(
                            "Indoor museum and cultural center ideal for weather protection."
                        ),
                        estimated_duration_minutes=90,
                        estimated_cost_inr=selected_poi.estimated_cost_inr,
                        provider="category-heuristic",
                    )

                prob = day_forecast.precipitation_probability if day_forecast else 70
                weather_note = (
                    f"Rain forecast ({prob}% probability) "
                    f"— replaced outdoor {selected_poi.name} with indoor {indoor_alt.name}."
                )
                slot = ActivitySlot(
                    daypart=dp,
                    poi=indoor_alt,
                    notes=f"Indoor activity suited for weather conditions in {dest_key}.",
                    is_weather_substituted=True,
                    substituted_for=selected_poi.name,
                    weather_note=weather_note,
                )
                total_weather_substitutions += 1
            else:
                slot = ActivitySlot(
                    daypart=dp,
                    poi=selected_poi,
                    notes=f"Explore {selected_poi.name} at a {pace.lower()} pace.",
                    is_weather_substituted=False,
                )

            activities.append(slot)

        # B. Schedule meals for the day
        meals: list[DayMeal] = []

        # Breakfast / Cafe
        c_idx = cafe_idx_map[dest_key]
        cafe_item = cafes_available[c_idx % len(cafes_available)] if cafes_available else None
        cafe_idx_map[dest_key] = c_idx + 1

        b_name = cafe_item.name if cafe_item else f"Local Cafe & Bakery, {dest_key}"
        b_cost = cafe_item.estimated_cost_inr if cafe_item else DEFAULT_MEAL_COST_BREAKFAST_INR
        b_maps = cafe_item.maps_url if cafe_item else None
        meals.append(
            DayMeal(
                daypart=Daypart.MORNING,
                meal_type="breakfast",
                restaurant_name=b_name,
                cuisine="Local Morning Fare",
                estimated_cost_inr=round(float(b_cost), 2),
                address=cafe_item.address if cafe_item else f"City Center, {dest_key}",
                maps_url=b_maps,
                is_estimated=cafe_item is None
                or cafe_item.provider in ("category-heuristic", "fixture"),
                notes="Light breakfast and fresh brew before starting sightseeing.",
            )
        )

        # Lunch
        r_idx = rest_idx_map[dest_key]
        lunch_item = (
            restaurants_available[r_idx % len(restaurants_available)]
            if restaurants_available
            else None
        )
        rest_idx_map[dest_key] = r_idx + 1

        l_name = lunch_item.name if lunch_item else f"Heritage Restaurant, {dest_key}"
        l_cost = lunch_item.estimated_cost_inr if lunch_item else DEFAULT_MEAL_COST_LUNCH_INR
        l_maps = lunch_item.maps_url if lunch_item else None
        meals.append(
            DayMeal(
                daypart=Daypart.AFTERNOON,
                meal_type="lunch",
                restaurant_name=l_name,
                cuisine="Regional Specialties",
                estimated_cost_inr=round(float(l_cost), 2),
                address=lunch_item.address if lunch_item else f"Central Market, {dest_key}",
                maps_url=l_maps,
                is_estimated=lunch_item is None
                or lunch_item.provider in ("category-heuristic", "fixture"),
                notes="Midday meal highlighting authentic regional flavors.",
            )
        )

        # Dinner
        r_idx2 = rest_idx_map[dest_key]
        dinner_item = (
            restaurants_available[r_idx2 % len(restaurants_available)]
            if restaurants_available
            else None
        )
        rest_idx_map[dest_key] = r_idx2 + 1

        d_name = dinner_item.name if dinner_item else f"Bistro & Dining Room, {dest_key}"
        d_cost = dinner_item.estimated_cost_inr if dinner_item else DEFAULT_MEAL_COST_DINNER_INR
        d_maps = dinner_item.maps_url if dinner_item else None
        meals.append(
            DayMeal(
                daypart=Daypart.EVENING,
                meal_type="dinner",
                restaurant_name=d_name,
                cuisine="Fine Regional & Indian Dining",
                estimated_cost_inr=round(float(d_cost), 2),
                address=dinner_item.address if dinner_item else f"Old Town, {dest_key}",
                maps_url=d_maps,
                is_estimated=dinner_item is None
                or dinner_item.provider in ("category-heuristic", "fixture"),
                notes="Evening dining and leisurely relaxation.",
            )
        )

        # C. Hotel association (from logistics plan if provided)
        hotel_info = hotel_by_city.get(dest_key.strip().lower())
        h_name = hotel_info[0] if hotel_info and day_num < duration_days else None
        h_url = hotel_info[1] if hotel_info and day_num < duration_days else None

        # D. Calculate day-level costs
        day_activity_cost = round(
            sum(slot.poi.estimated_cost_inr for slot in activities) * party_size, 2
        )
        day_food_cost = round(sum(m.estimated_cost_inr for m in meals) * party_size, 2)
        day_transit_cost = (
            DEFAULT_LOCAL_TRANSIT_PER_DAY_INTL_INR
            if is_intl
            else DEFAULT_LOCAL_TRANSIT_PER_DAY_DOMESTIC_INR
        )

        day_plan = DayPlan(
            day_number=day_num,
            date=day_date_str,
            city=dest_key,
            country=current_dest.country_name,
            activities=activities,
            meals=meals,
            hotel_name=h_name,
            hotel_booking_url=h_url,
            weather_summary=weather_summary,
            is_outdoor_friendly=is_outdoor,
            activity_cost_inr=day_activity_cost,
            food_cost_inr=day_food_cost,
            local_transport_cost_inr=day_transit_cost,
            notes=f"Day {day_num} in {dest_key} with {pace.lower()} activity schedule.",
        )
        day_plans.append(day_plan)

    # 7. Evaluate must-visit fulfillment
    must_visits_omitted = [mv for mv in must_visits if mv.strip() not in must_visits_fulfilled]
    if must_visits_omitted:
        omitted_str = ", ".join(must_visits_omitted)
        warnings.append(
            f"Could not safely schedule must-visit places due to duration/pacing: {omitted_str}."
        )

    # 8. Aggregate trip-wide cost totals
    total_activity_cost = round(sum(dp.activity_cost_inr for dp in day_plans), 2)
    total_food_cost = round(sum(dp.food_cost_inr for dp in day_plans), 2)
    total_local_transit_cost = round(sum(dp.local_transport_cost_inr for dp in day_plans), 2)

    destinations_covered = list(dict.fromkeys(dp.city for dp in day_plans))

    is_any_estimated = any(
        slot.poi.provider in ("category-heuristic", "fixture", "web-search")
        for dp in day_plans
        for slot in dp.activities
    ) or any(meal.is_estimated for dp in day_plans for meal in dp.meals)

    return ExperiencePlan(
        days=day_plans,
        total_days=len(day_plans),
        destinations_covered=destinations_covered,
        must_visits_fulfilled=sorted(must_visits_fulfilled),
        must_visits_omitted=sorted(must_visits_omitted),
        weather_substitutions=total_weather_substitutions,
        total_activity_cost_inr=total_activity_cost,
        total_food_cost_inr=total_food_cost,
        total_local_transport_cost_inr=total_local_transit_cost,
        warnings=warnings,
        is_estimated=is_any_estimated,
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# LangGraph Node Interface
# ---------------------------------------------------------------------------


def experience_node(
    state: dict[str, Any] | InitialPlanningState,
) -> dict[str, Any]:
    """LangGraph node function for experience planning.

    Args:
        state: State dictionary or InitialPlanningState from the graph.

    Returns:
        State update dictionary containing the generated 'experience_plan'.
    """
    plan = process_experience(state)
    return {
        "experience_plan": plan,
    }
