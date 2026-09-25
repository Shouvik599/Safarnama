"""Deterministic places, attractions, and dining search tool with multi-tier API resilience.

Provides structured point of interest data (attractions, historical monuments, museums,
restaurants, cafes) with ratings, reviews, GPS coordinates, price tiers, and maps URLs.

Fallback Cascade:
1. Test Fixture: data/fixtures/mock_places.json (if use_fixture=True or
   SAFARNAMA_USE_FIXTURES=true)
2. In-Memory Cache: 1-hour TTL per (destination, category, query, max_results) search
3. Live Tier 1: SerpApi Google Maps Engine (SERPAPI_KEY / SERPER_API_KEY)
4. Live Tier 2: OpenStreetMap Nominatim & Overpass POI API (Keyless open-access place search)
5. Live Tier 3: Live Web Search Tool Fallback: search_web() for live attraction/dining snippets
6. Tier 4: Offline Category Heuristic Baseline (Guarantees zero-crash resilience)
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from src.models.places import PlaceItem, PlacesSearchResult
from src.tools.static_data import get_airport_coordinates, get_country
from src.tools.web_search import search_web

load_dotenv()

log = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).parent.parent.parent / "data" / "fixtures" / "mock_places.json"
CACHE_TTL_SECONDS = 3600  # 1 hour
DEFAULT_TIMEOUT_SECONDS = 12.0


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class PlaceError(Exception):
    """Base exception for place search errors."""


class InvalidDestinationError(PlaceError, ValueError):
    """Raised when destination string is empty or invalid."""


class PlaceAPIError(PlaceError):
    """Raised when all place search providers fail and offline fallback is disabled."""


# ---------------------------------------------------------------------------
# In-Memory Cache Store
# ---------------------------------------------------------------------------


class PlacesCache:
    """Thread-safe in-memory cache store for places search results."""

    def __init__(self, ttl_seconds: float = CACHE_TTL_SECONDS) -> None:
        self._cache: dict[str, tuple[float, PlacesSearchResult]] = {}
        self.ttl_seconds = ttl_seconds

    def _make_key(
        self, destination: str, category: str, query: str | None, max_results: int
    ) -> str:
        q_str = query.strip().lower() if query else "NONE"
        return f"{destination.strip().upper()}:{category.strip().upper()}:{q_str}:{max_results}"

    def get(
        self, destination: str, category: str, query: str | None, max_results: int
    ) -> PlacesSearchResult | None:
        key = self._make_key(destination, category, query, max_results)
        if key in self._cache:
            created_at, result = self._cache[key]
            if time.time() - created_at < self.ttl_seconds:
                return result
            del self._cache[key]
        return None

    def set(
        self,
        destination: str,
        category: str,
        query: str | None,
        max_results: int,
        result: PlacesSearchResult,
    ) -> None:
        key = self._make_key(destination, category, query, max_results)
        self._cache[key] = (time.time(), result)

    def clear(self) -> None:
        self._cache.clear()


_PLACES_CACHE = PlacesCache()


def clear_places_cache() -> None:
    """Clear the in-memory places search cache."""
    _PLACES_CACHE.clear()


# ---------------------------------------------------------------------------
# Provider Implementation 1: Local Offline Fixture
# ---------------------------------------------------------------------------


def _search_fixture(
    destination: str,
    category: str = "ALL",
    query: str | None = None,
    max_results: int = 5,
    is_fallback_trigger: bool = True,
) -> PlacesSearchResult:
    """Retrieve places options from local mock fixture file."""
    clean_dest = destination.strip().upper()
    req_cat = category.strip().upper() if category else "ALL"

    if not FIXTURE_PATH.exists():
        log.warning("Places fixture file not found at %s", FIXTURE_PATH)
        return _estimate_category_heuristic(clean_dest, req_cat, query, max_results)

    try:
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            data = json.load(f)

        dests_map: dict = data.get("destinations", {})
        dest_data = dests_map.get(clean_dest)

        if not dest_data:
            dest_data = data.get("default_fallback", {})

        raw_items = dest_data.get("items", [])
        items: list[PlaceItem] = []

        for item in raw_items:
            item_cat = item.get("category", "ATTRACTION").upper()
            if req_cat != "ALL" and item_cat != req_cat:
                continue

            if query and query.strip().lower() not in item.get("name", "").lower():
                continue

            items.append(
                PlaceItem(
                    place_id=item.get("place_id", f"PLC-{hash(clean_dest) % 899 + 100}"),
                    name=item.get("name", f"Central Landmark {clean_dest.title()}"),
                    destination=clean_dest,
                    category=item_cat,
                    rating=float(item.get("rating", 4.5)),
                    reviews_count=int(item.get("reviews_count", 1200)),
                    price_level=item.get("price_level", "Free"),
                    estimated_cost_inr=float(item.get("estimated_cost_inr", 0.0)),
                    address=item.get("address", f"City Center, {clean_dest.title()}"),
                    latitude=item.get("latitude"),
                    longitude=item.get("longitude"),
                    description=item.get("description"),
                    open_hours=item.get("open_hours", "09:00 - 18:00"),
                    thumbnail_url=item.get("thumbnail_url"),
                    maps_url=item.get("maps_url", f"https://safarnama.local/places/{clean_dest.lower()}"),
                    provider="fixture",
                )
            )

        if not items:
            return _estimate_category_heuristic(clean_dest, req_cat, query, max_results)

        return PlacesSearchResult(
            destination=clean_dest,
            category_requested=req_cat,
            query=query,
            items=items[:max_results],
            provider_used="fixture",
            total_found=len(items[:max_results]),
            is_fallback=is_fallback_trigger,
            is_estimated=True,
            timestamp=datetime.now(UTC).isoformat(),
        )
    except Exception as exc:
        log.error("Failed to parse places fixture: %s", exc)
        return _estimate_category_heuristic(clean_dest, req_cat, query, max_results)


# ---------------------------------------------------------------------------
# Provider Implementation 2: Category Heuristic Baseline
# ---------------------------------------------------------------------------


def _resolve_city_coords(location_str: str) -> tuple[float, float]:
    """Resolve latitude & longitude for a city name or IATA code."""
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

    return 28.6139, 77.2090  # Default Delhi reference coordinates


def _estimate_category_heuristic(
    destination: str,
    category: str = "ALL",
    query: str | None = None,
    max_results: int = 5,
) -> PlacesSearchResult:
    """Generate realistic category-heuristic place options when external APIs are offline."""
    clean_dest = destination.strip().upper()
    req_cat = category.strip().upper() if category else "ALL"
    lat, lon = _resolve_city_coords(clean_dest)
    dest_title = clean_dest.title()

    items: list[PlaceItem] = []

    # 1. Sightseeing Attraction
    if req_cat in ("ALL", "ATTRACTION"):
        items.append(
            PlaceItem(
                place_id=f"PLC-EST-ATT-{hash(clean_dest) % 899 + 100}",
                name=f"{dest_title} Central Heritage Monument & Square",
                destination=clean_dest,
                category="ATTRACTION",
                rating=4.6,
                reviews_count=12400,
                price_level="Free",
                estimated_cost_inr=0.0,
                address=f"Historic District, {dest_title}",
                latitude=lat + 0.002,
                longitude=lon + 0.002,
                description=f"Iconic monument and public heritage square in {dest_title}.",
                open_hours="08:00 - 20:00",
                thumbnail_url=f"https://images.safarnama.local/places/{clean_dest.lower()}_monument.jpg",
                maps_url=f"https://safarnama.local/places/{clean_dest.lower()}",
                provider="category-heuristic",
            )
        )
        items.append(
            PlaceItem(
                place_id=f"PLC-EST-MUS-{hash(clean_dest) % 899 + 200}",
                name=f"National Museum of Art & Culture {dest_title}",
                destination=clean_dest,
                category="ATTRACTION",
                rating=4.5,
                reviews_count=8500,
                price_level="$",
                estimated_cost_inr=450.0,
                address=f"Cultural Avenue, {dest_title}",
                latitude=lat - 0.003,
                longitude=lon + 0.004,
                description=f"Premier art museum showcasing {dest_title}'s history.",
                open_hours="09:30 - 17:30",
                thumbnail_url=f"https://images.safarnama.local/places/{clean_dest.lower()}_museum.jpg",
                maps_url=f"https://safarnama.local/places/{clean_dest.lower()}",
                provider="category-heuristic",
            )
        )

    # 2. Restaurant
    if req_cat in ("ALL", "RESTAURANT"):
        items.append(
            PlaceItem(
                place_id=f"PLC-EST-RES-{hash(clean_dest) % 899 + 300}",
                name=f"The Grand Imperial Dining Room - {dest_title}",
                destination=clean_dest,
                category="RESTAURANT",
                rating=4.4,
                reviews_count=4200,
                price_level="$$",
                estimated_cost_inr=1250.0,
                address=f"Gourmet Street, {dest_title}",
                latitude=lat + 0.005,
                longitude=lon - 0.002,
                description="Highly rated multi-cuisine restaurant serving local dishes.",
                open_hours="12:00 - 23:00",
                thumbnail_url=f"https://images.safarnama.local/places/{clean_dest.lower()}_restaurant.jpg",
                maps_url=f"https://safarnama.local/places/{clean_dest.lower()}",
                provider="category-heuristic",
            )
        )

    # 3. Cafe
    if req_cat in ("ALL", "CAFE"):
        items.append(
            PlaceItem(
                place_id=f"PLC-EST-CAF-{hash(clean_dest) % 899 + 400}",
                name=f"Artisan Roastery & Bakery Cafe {dest_title}",
                destination=clean_dest,
                category="CAFE",
                rating=4.5,
                reviews_count=2800,
                price_level="$",
                estimated_cost_inr=450.0,
                address=f"Creative Quarter, {dest_title}",
                latitude=lat - 0.001,
                longitude=lon - 0.003,
                description="Cozy artisan coffee shop serving specialty brews and pastries.",
                open_hours="07:30 - 21:00",
                thumbnail_url=f"https://images.safarnama.local/places/{clean_dest.lower()}_cafe.jpg",
                maps_url=f"https://safarnama.local/places/{clean_dest.lower()}",
                provider="category-heuristic",
            )
        )

    return PlacesSearchResult(
        destination=clean_dest,
        category_requested=req_cat,
        query=query,
        items=items[:max_results],
        provider_used="category-heuristic",
        total_found=len(items[:max_results]),
        is_fallback=True,
        is_estimated=True,
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Provider Implementation 3: Live Tier 1 - SerpApi Google Maps
# ---------------------------------------------------------------------------


def _search_serpapi_google_maps(
    destination: str,
    category: str = "ALL",
    query: str | None = None,
    max_results: int = 5,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> PlacesSearchResult | None:
    """Execute live place & dining search via SerpApi Google Maps Engine."""
    api_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPER_API_KEY")
    if not api_key:
        return None

    clean_dest = destination.strip().upper()
    req_cat = category.strip().upper() if category else "ALL"

    search_q = query or f"top attractions in {clean_dest}"
    if req_cat == "RESTAURANT":
        search_q = query or f"best restaurants in {clean_dest}"
    elif req_cat == "CAFE":
        search_q = query or f"best cafes in {clean_dest}"

    params = {
        "engine": "google_maps",
        "q": search_q,
        "type": "search",
        "api_key": api_key,
    }

    url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Safarnama/0.1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                local_res = body.get("local_results", body.get("place_results", []))

                if isinstance(local_res, dict):
                    local_res = [local_res]

                items: list[PlaceItem] = []
                for p in local_res[:max_results]:
                    name = p.get("title") or p.get("name") or f"{clean_dest.title()} Venue"
                    raw_type = str(p.get("type") or "").upper()

                    cat = "ATTRACTION"
                    if "RESTAURANT" in raw_type or "FOOD" in raw_type or "DINING" in raw_type:
                        cat = "RESTAURANT"
                    elif "CAFE" in raw_type or "COFFEE" in raw_type or "BAKERY" in raw_type:
                        cat = "CAFE"
                    elif req_cat in ("ATTRACTION", "RESTAURANT", "CAFE"):
                        cat = req_cat

                    coords = p.get("gps_coordinates", {})
                    lat = coords.get("latitude")
                    lon = coords.get("longitude")

                    price_lvl = p.get("price") or ("$$" if cat == "RESTAURANT" else "Free")
                    est_cost = 0.0
                    if cat == "RESTAURANT":
                        est_cost = 1200.0 if "$$$" in str(price_lvl) else 650.0
                    elif cat == "CAFE":
                        est_cost = 350.0
                    elif cat == "ATTRACTION" and price_lvl != "Free":
                        est_cost = 500.0

                    fallback_pid = f"PLC-SERP-{hash(name) % 899 + 100}"
                    pid = p.get("data_id") or p.get("place_id") or fallback_pid
                    place_id_raw = str(pid)
                    items.append(
                        PlaceItem(
                            place_id=place_id_raw,
                            name=name,
                            destination=clean_dest,
                            category=cat,
                            rating=float(p.get("rating") or 4.5),
                            reviews_count=int(p.get("reviews") or 450),
                            price_level=price_lvl,
                            estimated_cost_inr=est_cost,
                            address=p.get("address") or f"{clean_dest.title()} City Center",
                            latitude=lat,
                            longitude=lon,
                            description=p.get("description") or p.get("type"),
                            open_hours=p.get("open_state") or p.get("hours"),
                            thumbnail_url=p.get("thumbnail"),
                            maps_url=p.get("link") or p.get("google_maps_link"),
                            provider="serpapi-google-maps",
                        )
                    )

                if items:
                    log.info("Fetched %d places from SerpApi Google Maps API", len(items))
                    return PlacesSearchResult(
                        destination=clean_dest,
                        category_requested=req_cat,
                        query=query,
                        items=items,
                        provider_used="serpapi-google-maps",
                        total_found=len(items),
                        is_fallback=False,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("SerpApi Google Maps request failed for %s: %s", clean_dest, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 4: Live Tier 2 - OpenStreetMap Nominatim POI (Keyless)
# ---------------------------------------------------------------------------


def _search_nominatim_osm(
    destination: str,
    category: str = "ALL",
    query: str | None = None,
    max_results: int = 5,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> PlacesSearchResult | None:
    """Execute live keyless places search via OpenStreetMap Nominatim API."""
    clean_dest = destination.strip().upper()
    req_cat = category.strip().upper() if category else "ALL"

    q_term = query or "attractions"
    if req_cat == "RESTAURANT":
        q_term = query or "restaurants"
    elif req_cat == "CAFE":
        q_term = query or "cafes"

    enc_q = urllib.parse.quote(f"{q_term} in {clean_dest}")
    url = f"https://nominatim.openstreetmap.org/search?q={enc_q}&format=json&limit={max_results}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safarnama/0.1.0",
                "Accept-Language": "en",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                places = json.loads(resp.read().decode("utf-8"))
                if not places or not isinstance(places, list):
                    return None

                items: list[PlaceItem] = []
                for idx, p in enumerate(places[:max_results]):
                    raw_name = p.get("display_name", "").split(",")[0]
                    name = raw_name.strip() if raw_name else f"{clean_dest.title()} Place"
                    lat = float(p.get("lat", 0.0))
                    lon = float(p.get("lon", 0.0))

                    cat = (
                        req_cat
                        if req_cat in ("ATTRACTION", "RESTAURANT", "CAFE")
                        else "ATTRACTION"
                    )

                    items.append(
                        PlaceItem(
                            place_id=f"PLC-OSM-{p.get('place_id', idx + 100)}",
                            name=name,
                            destination=clean_dest,
                            category=cat,
                            rating=4.4,
                            reviews_count=350,
                            price_level="$$" if cat == "RESTAURANT" else "Free",
                            estimated_cost_inr=650.0 if cat == "RESTAURANT" else 0.0,
                            address=p.get("display_name", f"{clean_dest.title()} City Center"),
                            latitude=lat,
                            longitude=lon,
                            description=f"Point of interest in {clean_dest.title()}",
                            open_hours="09:00 - 18:00",
                            thumbnail_url=None,
                            maps_url=f"https://safarnama.local/places/{clean_dest.lower()}",
                            provider="nominatim-osm",
                        )
                    )

                if items:
                    log.info("Fetched %d places from OpenStreetMap Nominatim API", len(items))
                    return PlacesSearchResult(
                        destination=clean_dest,
                        category_requested=req_cat,
                        query=query,
                        items=items,
                        provider_used="nominatim-osm",
                        total_found=len(items),
                        is_fallback=True,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("Nominatim OSM places search failed for %s: %s", clean_dest, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 5: Live Tier 3 - Web Search Tool Fallback
# ---------------------------------------------------------------------------


def _search_via_web_search(
    destination: str,
    category: str = "ALL",
    query: str | None = None,
    max_results: int = 5,
) -> PlacesSearchResult | None:
    """Execute live web search for places & dining via search_web()."""
    clean_dest = destination.strip().upper()
    req_cat = category.strip().upper() if category else "ALL"

    search_term = query or f"top {req_cat.lower()} places to visit in {clean_dest}"
    try:
        search_res = search_web(search_term, max_results=max_results)
        if search_res and search_res.results and not search_res.is_estimated:
            items: list[PlaceItem] = []
            for idx, item in enumerate(search_res.results[:max_results]):
                items.append(
                    PlaceItem(
                        place_id=f"PLC-WEB-{idx + 100}",
                        name=item.title[:50],
                        destination=clean_dest,
                        category=req_cat if req_cat != "ALL" else "ATTRACTION",
                        rating=4.5,
                        reviews_count=650,
                        price_level="Moderate",
                        estimated_cost_inr=500.0,
                        address=f"Central {clean_dest.title()}",
                        latitude=None,
                        longitude=None,
                        description=item.snippet[:150] if item.snippet else None,
                        open_hours="Flexible",
                        thumbnail_url=None,
                        maps_url=item.url,
                        provider="web-search",
                    )
                )

            log.info(
                "Fetched %d place results via search_web provider %s",
                len(items),
                search_res.provider_used,
            )
            return PlacesSearchResult(
                destination=clean_dest,
                category_requested=req_cat,
                query=query,
                items=items,
                provider_used="web-search",
                total_found=len(items),
                is_fallback=True,
                is_estimated=True,
                timestamp=datetime.now(UTC).isoformat(),
            )
    except Exception as exc:
        log.warning("Web search places fallback failed for query '%s': %s", search_term, exc)

    return None


# ---------------------------------------------------------------------------
# Public Places Search Interface
# ---------------------------------------------------------------------------


def search_places(
    destination: str,
    category: str = "ALL",
    query: str | None = None,
    max_results: int = 5,
    use_fixture: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> PlacesSearchResult:
    """Search points of interest (attractions, restaurants, cafes) for a destination.

    Args:
        destination: Target city or region name (e.g. 'Tokyo', 'Mumbai', 'Paris').
        category: Requested category filter: 'ALL', 'ATTRACTION', 'RESTAURANT', or 'CAFE'.
        query: Optional search keyword filter (e.g. 'museum', 'ramen', 'temple').
        max_results: Maximum number of place items to return (default: 5).
        use_fixture: If True, bypass live API network requests and return fixture data.
        timeout: Network timeout in seconds for live API HTTP requests.

    Returns:
        PlacesSearchResult containing validated PlaceItem records and provenance.

    Raises:
        InvalidDestinationError: If destination string is empty or blank.
    """
    if not destination or not destination.strip():
        raise InvalidDestinationError("Destination location string cannot be empty or whitespace.")

    clean_dest = destination.strip().upper()
    req_cat = category.strip().upper() if category else "ALL"
    if max_results <= 0:
        max_results = 5

    # Check environment variable triggers for fixture mode
    force_fixture = (
        use_fixture
        or os.getenv("SAFARNAMA_USE_FIXTURES", "").lower() in ("true", "1")
        or os.getenv("SAFARNAMA_TEST_MODE", "").lower() in ("true", "1")
    )

    # Check in-memory cache first
    cached_result = _PLACES_CACHE.get(clean_dest, req_cat, query, max_results)
    if cached_result is not None:
        log.debug("Returning cached places search result for %s", clean_dest)
        return cached_result

    if force_fixture:
        log.info("Fixture mode active. Serving places search from mock fixture.")
        res = _search_fixture(
            clean_dest,
            category=req_cat,
            query=query,
            max_results=max_results,
            is_fallback_trigger=True,
        )
        _PLACES_CACHE.set(clean_dest, req_cat, query, max_results, res)
        return res

    # 1. Live Tier 1: SerpApi Google Maps API
    res = _search_serpapi_google_maps(
        clean_dest, category=req_cat, query=query, max_results=max_results, timeout=timeout
    )
    if res and res.items:
        _PLACES_CACHE.set(clean_dest, req_cat, query, max_results, res)
        return res

    # 2. Live Tier 2: OpenStreetMap Nominatim API (Keyless Open Access)
    res = _search_nominatim_osm(
        clean_dest, category=req_cat, query=query, max_results=max_results, timeout=timeout
    )
    if res and res.items:
        _PLACES_CACHE.set(clean_dest, req_cat, query, max_results, res)
        return res

    # 3. Live Tier 3: Web Search Tool Fallback
    res = _search_via_web_search(
        clean_dest, category=req_cat, query=query, max_results=max_results
    )
    if res and res.items:
        _PLACES_CACHE.set(clean_dest, req_cat, query, max_results, res)
        return res

    # 4. Tier 4: Offline Category Heuristic Baseline (Guarantees zero crashes)
    log.warning(
        "All live place providers failed or unconfigured for %s. "
        "Falling back to category-heuristic places baseline.",
        clean_dest,
    )
    fallback_res = _estimate_category_heuristic(
        clean_dest, category=req_cat, query=query, max_results=max_results
    )
    _PLACES_CACHE.set(clean_dest, req_cat, query, max_results, fallback_res)
    return fallback_res


def get_places_status() -> dict[str, bool | str]:
    """Retrieve operational status of configured places API providers."""
    return {
        "serpapi_configured": bool(os.getenv("SERPAPI_KEY") or os.getenv("SERPER_API_KEY")),
        "nominatim_available": True,  # Keyless open access
        "web_search_available": True,
        "fixture_available": FIXTURE_PATH.exists(),
    }
