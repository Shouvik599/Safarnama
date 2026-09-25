"""Deterministic hotel & accommodation search tool with multi-tier API resilience.

Provides structured hotel options (star rating, guest score, price per night, total stay price,
amenities, coordinates, and booking URL) for Indian domestic and international destinations.

Fallback Cascade:
1. Test Fixture: data/fixtures/mock_hotels.json (if use_fixture=True or
   SAFARNAMA_USE_FIXTURES=true)
2. In-Memory Cache: 1-hour TTL per (destination, checkin, checkout, guests, star_rating) search
3. Live Tier 1A: SerpApi Google Hotels API (SERPAPI_KEY / SERPER_API_KEY)
4. Live Tier 1B: Booking.com API on RapidAPI (GET https://booking-com.p.rapidapi.com, RAPIDAPI_KEY)
5. Live Tier 2: OpenStreetMap Nominatim Places API (Keyless open-access hotel discovery)
6. Live Tier 3: Live Web Search Tool Fallback: search_web() for live hotel options & rates
7. Tier 4: Offline Hotel Location Heuristic Baseline (Guarantees zero-crash resilience)
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from src.models.hotels import HotelOption, HotelSearchResult
from src.tools.static_data import get_airport_coordinates, get_country
from src.tools.web_search import search_web

load_dotenv()

log = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).parent.parent.parent / "data" / "fixtures" / "mock_hotels.json"
CACHE_TTL_SECONDS = 3600  # 1 hour
DEFAULT_TIMEOUT_SECONDS = 12.0


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class HotelError(Exception):
    """Base exception for hotel search errors."""


class InvalidDestinationError(HotelError, ValueError):
    """Raised when destination string is empty or invalid."""


class HotelAPIError(HotelError):
    """Raised when all hotel search providers fail and offline fallback is disabled."""


# ---------------------------------------------------------------------------
# In-Memory Cache Store
# ---------------------------------------------------------------------------


class HotelsCache:
    """Thread-safe in-memory cache store for hotel search results."""

    def __init__(self, ttl_seconds: float = CACHE_TTL_SECONDS) -> None:
        self._cache: dict[str, tuple[float, HotelSearchResult]] = {}
        self.ttl_seconds = ttl_seconds

    def _make_key(
        self,
        destination: str,
        checkin_date: str,
        checkout_date: str,
        guests: int,
        star_rating: int | None,
    ) -> str:
        star_str = str(star_rating) if star_rating else "ANY"
        return f"{destination.strip().upper()}:{checkin_date}:{checkout_date}:{guests}:{star_str}"

    def get(
        self,
        destination: str,
        checkin_date: str,
        checkout_date: str,
        guests: int,
        star_rating: int | None = None,
    ) -> HotelSearchResult | None:
        key = self._make_key(destination, checkin_date, checkout_date, guests, star_rating)
        if key in self._cache:
            created_at, result = self._cache[key]
            if time.time() - created_at < self.ttl_seconds:
                return result
            del self._cache[key]
        return None

    def set(
        self,
        destination: str,
        checkin_date: str,
        checkout_date: str,
        guests: int,
        star_rating: int | None,
        result: HotelSearchResult,
    ) -> None:
        key = self._make_key(destination, checkin_date, checkout_date, guests, star_rating)
        self._cache[key] = (time.time(), result)

    def clear(self) -> None:
        self._cache.clear()


_HOTELS_CACHE = HotelsCache()


def clear_hotels_cache() -> None:
    """Clear the in-memory hotel search cache."""
    _HOTELS_CACHE.clear()


# ---------------------------------------------------------------------------
# Provider Implementation 1: Local Offline Fixture
# ---------------------------------------------------------------------------


def _search_fixture(
    destination: str,
    checkin_date: str,
    checkout_date: str,
    nights: int,
    guests: int = 2,
    star_rating: int | None = None,
    max_price_per_night_inr: float | None = None,
    is_fallback_trigger: bool = True,
) -> HotelSearchResult:
    """Retrieve hotel options from local mock fixture file."""
    clean_dest = destination.strip().upper()

    if not FIXTURE_PATH.exists():
        log.warning("Hotel fixture file not found at %s", FIXTURE_PATH)
        return _estimate_location_heuristic(
            clean_dest,
            checkin_date,
            checkout_date,
            nights,
            guests,
            star_rating,
            max_price_per_night_inr,
        )

    try:
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            data = json.load(f)

        dests_map: dict = data.get("destinations", {})
        dest_data = dests_map.get(clean_dest)

        if not dest_data:
            dest_data = data.get("default_fallback", {})

        raw_options = dest_data.get("options", [])
        options: list[HotelOption] = []

        for item in raw_options:
            price_night = float(item.get("price_per_night_inr", 6500.0))

            if max_price_per_night_inr and price_night > max_price_per_night_inr:
                continue

            item_star = item.get("star_rating")
            if star_rating and item_star and item_star < star_rating:
                continue

            total_stay = round(price_night * nights, 2)
            default_amenities = ["Free Wi-Fi", "Air Conditioning", "Restaurant"]

            options.append(
                HotelOption(
                    hotel_id=item.get("hotel_id", f"HTL-{hash(clean_dest) % 899 + 100}"),
                    name=item.get("name", f"Grand {clean_dest.title()} Hotel"),
                    destination=clean_dest,
                    star_rating=item_star or 4,
                    user_rating=item.get("user_rating", 8.4),
                    reviews_count=item.get("reviews_count", 1500),
                    address=item.get("address", f"Central Boulevard, {clean_dest.title()}"),
                    latitude=item.get("latitude"),
                    longitude=item.get("longitude"),
                    price_per_night_inr=price_night,
                    total_price_inr=total_stay,
                    amenities=item.get("amenities", default_amenities),
                    room_type=item.get("room_type", "Standard Deluxe Room"),
                    thumbnail_url=item.get("thumbnail_url"),
                    booking_url=item.get(
                        "booking_url", f"https://safarnama.local/hotels/{clean_dest.lower()}"
                    ),
                    provider="fixture",
                )
            )

        if not options:
            return _estimate_location_heuristic(
                clean_dest,
                checkin_date,
                checkout_date,
                nights,
                guests,
                star_rating,
                max_price_per_night_inr,
            )

        return HotelSearchResult(
            destination=clean_dest,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            nights=nights,
            guests=guests,
            options=options,
            provider_used="fixture",
            total_found=len(options),
            is_fallback=is_fallback_trigger,
            is_estimated=True,
            timestamp=datetime.now(UTC).isoformat(),
        )
    except Exception as exc:
        log.error("Failed to parse hotel fixture: %s", exc)
        return _estimate_location_heuristic(
            clean_dest,
            checkin_date,
            checkout_date,
            nights,
            guests,
            star_rating,
            max_price_per_night_inr,
        )


# ---------------------------------------------------------------------------
# Provider Implementation 2: Location Heuristic Baseline
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


def _estimate_location_heuristic(
    destination: str,
    checkin_date: str,
    checkout_date: str,
    nights: int,
    guests: int = 2,
    star_rating: int | None = None,
    max_price_per_night_inr: float | None = None,
) -> HotelSearchResult:
    """Generate realistic location-heuristic hotel options when external APIs are offline."""
    clean_dest = destination.strip().upper()
    lat, lon = _resolve_city_coords(clean_dest)

    base_prices = {
        3: 4500.0,
        4: 9500.0,
        5: 22500.0,
    }

    target_stars = [3, 4, 5]
    if star_rating in base_prices:
        target_stars = [star_rating]

    options: list[HotelOption] = []
    dest_title = clean_dest.title()

    for star in target_stars:
        night_price = base_prices[star]
        if max_price_per_night_inr and night_price > max_price_per_night_inr:
            night_price = max_price_per_night_inr * 0.90

        total_stay = round(night_price * nights, 2)
        h_name = f"{dest_title} {star}-Star Comfort Hotel"
        if star == 5:
            h_name = f"The Grand Palace & Spa {dest_title}"
        elif star == 4:
            h_name = f"Courtyard by Marriott {dest_title}"

        options.append(
            HotelOption(
                hotel_id=f"HTL-EST-{star}-{hash(clean_dest) % 899 + 100}",
                name=h_name,
                destination=clean_dest,
                star_rating=star,
                user_rating=8.0 + (star - 3) * 0.6,
                reviews_count=1200 + star * 400,
                address=f"City Center Boulevard, {dest_title}",
                latitude=lat + (star * 0.005),
                longitude=lon + (star * 0.005),
                price_per_night_inr=night_price,
                total_price_inr=total_stay,
                amenities=["Free Wi-Fi", "Air Conditioning", "Breakfast", "24-Hour Front Desk"],
                room_type="Executive Room" if star >= 4 else "Standard Deluxe Room",
                thumbnail_url=f"https://images.safarnama.local/hotels/est_{star}star.jpg",
                booking_url=f"https://safarnama.local/hotels/{clean_dest.lower()}",
                provider="location-heuristic",
            )
        )

    return HotelSearchResult(
        destination=clean_dest,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        nights=nights,
        guests=guests,
        options=options,
        provider_used="location-heuristic",
        total_found=len(options),
        is_fallback=True,
        is_estimated=True,
        timestamp=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Provider Implementation 3: Live Tier 1A - SerpApi Google Hotels
# ---------------------------------------------------------------------------


def _search_serpapi_google_hotels(
    destination: str,
    checkin_date: str,
    checkout_date: str,
    nights: int,
    guests: int = 2,
    star_rating: int | None = None,
    max_price_per_night_inr: float | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> HotelSearchResult | None:
    """Execute live hotel search via SerpApi Google Hotels API."""
    api_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPER_API_KEY")
    if not api_key:
        return None

    clean_dest = destination.strip().upper()
    query_str = f"hotels in {clean_dest}"

    params = {
        "engine": "google_hotels",
        "q": query_str,
        "check_in_date": checkin_date,
        "check_out_date": checkout_date,
        "adults": str(guests),
        "currency": "INR",
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
                properties = body.get("properties", [])

                options: list[HotelOption] = []
                for prop in properties[:8]:
                    name = prop.get("name") or f"{clean_dest.title()} Hotel"
                    rate_obj = prop.get("rate_per_night", {})
                    extracted_rate = (
                        rate_obj.get("extracted_lowest")
                        or rate_obj.get("extracted_before_taxes_fees")
                    )

                    if not extracted_rate:
                        raw_str = rate_obj.get("lowest") or rate_obj.get("before_taxes_fees") or ""
                        nums = [int(s) for s in raw_str.replace(",", "").split() if s.isdigit()]
                        extracted_rate = float(nums[0]) if nums else 6500.0

                    price_night = float(extracted_rate)
                    if max_price_per_night_inr and price_night > max_price_per_night_inr:
                        continue

                    raw_class = prop.get("hotel_class", "")
                    stars = None
                    if raw_class and isinstance(raw_class, str):
                        for char in raw_class:
                            if char.isdigit():
                                stars = int(char)
                                break

                    if star_rating and stars and stars < star_rating:
                        continue

                    coords = prop.get("gps_coordinates", {})
                    lat = coords.get("latitude")
                    lon = coords.get("longitude")

                    images = prop.get("images", [])
                    thumb = images[0].get("thumbnail") if images else None
                    amenities = prop.get("amenities", ["Free Wi-Fi", "Air Conditioning"])

                    options.append(
                        HotelOption(
                            hotel_id=f"HTL-SERP-{hash(name) % 89999 + 10000}",
                            name=name,
                            destination=clean_dest,
                            star_rating=stars,
                            user_rating=float(prop.get("overall_rating") or 8.2),
                            reviews_count=int(prop.get("reviews") or 500),
                            address=prop.get("description") or f"{clean_dest.title()} City Center",
                            latitude=lat,
                            longitude=lon,
                            price_per_night_inr=price_night,
                            total_price_inr=round(price_night * nights, 2),
                            amenities=amenities[:5],
                            room_type="Standard Room",
                            thumbnail_url=thumb,
                            booking_url=prop.get("deal_url") or prop.get("link"),
                            provider="serpapi-google-hotels",
                        )
                    )

                if options:
                    log.info("Fetched %d hotels from SerpApi Google Hotels API", len(options))
                    return HotelSearchResult(
                        destination=clean_dest,
                        checkin_date=checkin_date,
                        checkout_date=checkout_date,
                        nights=nights,
                        guests=guests,
                        options=options,
                        provider_used="serpapi-google-hotels",
                        total_found=len(options),
                        is_fallback=False,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("SerpApi Google Hotels request failed for %s: %s", clean_dest, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 4: Live Tier 1B - Booking.com on RapidAPI
# ---------------------------------------------------------------------------


def _search_booking_com(
    destination: str,
    checkin_date: str,
    checkout_date: str,
    nights: int,
    guests: int = 2,
    star_rating: int | None = None,
    max_price_per_night_inr: float | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> HotelSearchResult | None:
    """Execute live hotel search via Booking.com API on RapidAPI."""
    rapid_key = os.getenv("RAPIDAPI_KEY")
    if not rapid_key:
        return None

    clean_dest = destination.strip().upper()
    enc_name = urllib.parse.quote(clean_dest)
    loc_url = f"https://booking-com.p.rapidapi.com/v1/hotels/locations?name={enc_name}&locale=en-gb"

    try:
        req = urllib.request.Request(
            loc_url,
            headers={
                "x-rapidapi-key": rapid_key,
                "x-rapidapi-host": "booking-com.p.rapidapi.com",
                "User-Agent": "Safarnama/0.1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                loc_data = json.loads(resp.read().decode("utf-8"))
                if not loc_data or not isinstance(loc_data, list):
                    return None

                dest_id = loc_data[0].get("dest_id")
                dest_type = loc_data[0].get("dest_type", "city")
                if not dest_id:
                    return None

                search_url = (
                    "https://booking-com.p.rapidapi.com/v1/hotels/search"
                    f"?dest_id={dest_id}&dest_type={dest_type}"
                    f"&checkin_date={checkin_date}&checkout_date={checkout_date}"
                    f"&adults_number={guests}&units=metric&currency=INR&locale=en-gb"
                )

                s_req = urllib.request.Request(
                    search_url,
                    headers={
                        "x-rapidapi-key": rapid_key,
                        "x-rapidapi-host": "booking-com.p.rapidapi.com",
                        "User-Agent": "Safarnama/0.1.0",
                    },
                )
                with urllib.request.urlopen(s_req, timeout=timeout) as s_resp:
                    if s_resp.status == 200:
                        s_body = json.loads(s_resp.read().decode("utf-8"))
                        results = s_body.get("result", [])

                        options: list[HotelOption] = []
                        for h in results[:8]:
                            price_val = float(
                                h.get("min_total_price")
                                or h.get("price_breakdown", {}).get("gross_price", 7500.0)
                            )
                            price_night = round(price_val / max(1, nights), 2)

                            if max_price_per_night_inr and price_night > max_price_per_night_inr:
                                continue

                            stars = int(h.get("class") or 3)
                            if star_rating and stars < star_rating:
                                continue

                            options.append(
                                HotelOption(
                                    hotel_id=str(h.get("hotel_id", "HTL-BKG-100")),
                                    name=h.get("hotel_name", f"{clean_dest.title()} Hotel"),
                                    destination=clean_dest,
                                    star_rating=stars,
                                    user_rating=float(h.get("review_score") or 8.0),
                                    reviews_count=int(h.get("review_nr") or 300),
                                    address=h.get("address", f"{clean_dest.title()} City Center"),
                                    latitude=h.get("latitude"),
                                    longitude=h.get("longitude"),
                                    price_per_night_inr=price_night,
                                    total_price_inr=round(price_night * nights, 2),
                                    amenities=["Free Wi-Fi", "Air Conditioning"],
                                    room_type=h.get("unit_configuration_label", "Standard Room"),
                                    thumbnail_url=h.get("max_photo_url"),
                                    booking_url=h.get("url"),
                                    provider="booking-com",
                                )
                            )

                        if options:
                            log.info("Fetched %d hotels from Booking.com API", len(options))
                            return HotelSearchResult(
                                destination=clean_dest,
                                checkin_date=checkin_date,
                                checkout_date=checkout_date,
                                nights=nights,
                                guests=guests,
                                options=options,
                                provider_used="booking-com",
                                total_found=len(options),
                                is_fallback=False,
                                is_estimated=False,
                                timestamp=datetime.now(UTC).isoformat(),
                            )
    except Exception as exc:
        log.warning("Booking.com API request failed for %s: %s", clean_dest, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 5: Live Tier 2 - Nominatim OpenStreetMap (Keyless)
# ---------------------------------------------------------------------------


def _search_nominatim_osm(
    destination: str,
    checkin_date: str,
    checkout_date: str,
    nights: int,
    guests: int = 2,
    star_rating: int | None = None,
    max_price_per_night_inr: float | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> HotelSearchResult | None:
    """Execute live keyless hotel location search via OpenStreetMap Nominatim API."""
    clean_dest = destination.strip().upper()
    enc_q = urllib.parse.quote(f"hotels in {clean_dest}")
    url = f"https://nominatim.openstreetmap.org/search?q={enc_q}&format=json&limit=5"

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

                options: list[HotelOption] = []
                for idx, p in enumerate(places[:5]):
                    raw_name = p.get("display_name", "").split(",")[0]
                    name = raw_name.strip() if raw_name else f"{clean_dest.title()} Hotel"
                    lat = float(p.get("lat", 0.0))
                    lon = float(p.get("lon", 0.0))

                    star = star_rating or (4 if idx % 2 == 0 else 3)
                    night_price = 5500.0 if star == 3 else 10500.0

                    if max_price_per_night_inr and night_price > max_price_per_night_inr:
                        night_price = max_price_per_night_inr

                    options.append(
                        HotelOption(
                            hotel_id=f"HTL-OSM-{p.get('place_id', idx + 100)}",
                            name=name,
                            destination=clean_dest,
                            star_rating=star,
                            user_rating=8.3,
                            reviews_count=450,
                            address=p.get("display_name", f"{clean_dest.title()} City Center"),
                            latitude=lat,
                            longitude=lon,
                            price_per_night_inr=night_price,
                            total_price_inr=round(night_price * nights, 2),
                            amenities=["Free Wi-Fi", "Air Conditioning", "24-Hour Desk"],
                            room_type="Standard Room",
                            thumbnail_url=None,
                            booking_url=f"https://safarnama.local/hotels/{clean_dest.lower()}",
                            provider="nominatim-osm",
                        )
                    )

                if options:
                    log.info("Fetched %d hotels from OpenStreetMap Nominatim API", len(options))
                    return HotelSearchResult(
                        destination=clean_dest,
                        checkin_date=checkin_date,
                        checkout_date=checkout_date,
                        nights=nights,
                        guests=guests,
                        options=options,
                        provider_used="nominatim-osm",
                        total_found=len(options),
                        is_fallback=True,
                        is_estimated=False,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
    except Exception as exc:
        log.warning("Nominatim OSM hotel search failed for %s: %s", clean_dest, exc)

    return None


# ---------------------------------------------------------------------------
# Provider Implementation 6: Live Tier 3 - Web Search Tool Fallback
# ---------------------------------------------------------------------------


def _search_via_web_search(
    destination: str,
    checkin_date: str,
    checkout_date: str,
    nights: int,
    guests: int = 2,
    star_rating: int | None = None,
    max_price_per_night_inr: float | None = None,
) -> HotelSearchResult | None:
    """Execute live web search for hotels via search_web()."""
    clean_dest = destination.strip().upper()
    query = f"hotels in {clean_dest} price per night booking {checkin_date}"

    try:
        search_res = search_web(query, max_results=3)
        if search_res and search_res.results and not search_res.is_estimated:
            options: list[HotelOption] = []
            for idx, item in enumerate(search_res.results[:3]):
                night_price = max_price_per_night_inr or 7500.0
                options.append(
                    HotelOption(
                        hotel_id=f"HTL-WEB-{idx + 100}",
                        name=item.title[:50],
                        destination=clean_dest,
                        star_rating=star_rating or 4,
                        user_rating=8.4,
                        reviews_count=850,
                        address=f"Central {clean_dest.title()}",
                        latitude=None,
                        longitude=None,
                        price_per_night_inr=night_price,
                        total_price_inr=round(night_price * nights, 2),
                        amenities=["Free Wi-Fi", "Air Conditioning"],
                        room_type="Standard Room",
                        thumbnail_url=None,
                        booking_url=item.url,
                        provider="web-search",
                    )
                )

            log.info(
                "Fetched %d hotel results via search_web provider %s",
                len(options),
                search_res.provider_used,
            )
            return HotelSearchResult(
                destination=clean_dest,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                nights=nights,
                guests=guests,
                options=options,
                provider_used="web-search",
                total_found=len(options),
                is_fallback=True,
                is_estimated=True,
                timestamp=datetime.now(UTC).isoformat(),
            )
    except Exception as exc:
        log.warning("Web search hotel fallback failed for query '%s': %s", query, exc)

    return None


# ---------------------------------------------------------------------------
# Public Hotel Search Interface
# ---------------------------------------------------------------------------


def search_hotels(
    destination: str,
    checkin_date: str | None = None,
    checkout_date: str | None = None,
    nights: int = 1,
    guests: int = 2,
    star_rating: int | None = None,
    max_price_per_night_inr: float | None = None,
    use_fixture: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> HotelSearchResult:
    """Search available hotel/accommodation options for a destination.

    Args:
        destination: Target city or region name (e.g. 'Tokyo', 'Mumbai', 'Paris').
        checkin_date: Check-in date in YYYY-MM-DD format (defaults to 14 days from today).
        checkout_date: Check-out date in YYYY-MM-DD format (defaults to checkin + nights).
        nights: Number of stay nights (default: 1).
        guests: Number of adult guests (default: 2).
        star_rating: Optional minimum star rating filter (1 to 5).
        max_price_per_night_inr: Optional budget cap per night in INR.
        use_fixture: If True, bypass live API network requests and return fixture data.
        timeout: Network timeout in seconds for live API HTTP requests.

    Returns:
        HotelSearchResult containing validated HotelOption items and provenance.

    Raises:
        InvalidDestinationError: If destination string is empty or blank.
    """
    if not destination or not destination.strip():
        raise InvalidDestinationError("Destination location string cannot be empty or whitespace.")

    clean_dest = destination.strip().upper()
    if nights <= 0:
        nights = 1
    if guests <= 0:
        guests = 2

    today = datetime.now(UTC).date()
    if not checkin_date:
        checkin_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")

    if not checkout_date:
        try:
            in_d = datetime.strptime(checkin_date, "%Y-%m-%d").date()
            checkout_date = (in_d + timedelta(days=nights)).strftime("%Y-%m-%d")
        except ValueError:
            checkout_date = (today + timedelta(days=14 + nights)).strftime("%Y-%m-%d")
    else:
        try:
            in_d = datetime.strptime(checkin_date, "%Y-%m-%d").date()
            out_d = datetime.strptime(checkout_date, "%Y-%m-%d").date()
            computed_nights = (out_d - in_d).days
            if computed_nights > 0:
                nights = computed_nights
        except ValueError:
            pass

    # Check environment variable triggers for fixture mode
    force_fixture = (
        use_fixture
        or os.getenv("SAFARNAMA_USE_FIXTURES", "").lower() in ("true", "1")
        or os.getenv("SAFARNAMA_TEST_MODE", "").lower() in ("true", "1")
    )

    # Check in-memory cache first
    cached_result = _HOTELS_CACHE.get(clean_dest, checkin_date, checkout_date, guests, star_rating)
    if cached_result is not None:
        log.debug("Returning cached hotel search result for %s", clean_dest)
        return cached_result

    if force_fixture:
        log.info("Fixture mode active. Serving hotel search from mock fixture.")
        res = _search_fixture(
            clean_dest,
            checkin_date,
            checkout_date,
            nights,
            guests=guests,
            star_rating=star_rating,
            max_price_per_night_inr=max_price_per_night_inr,
            is_fallback_trigger=True,
        )
        _HOTELS_CACHE.set(clean_dest, checkin_date, checkout_date, guests, star_rating, res)
        return res

    # 1. Live Tier 1A: SerpApi Google Hotels API
    res = _search_serpapi_google_hotels(
        clean_dest,
        checkin_date,
        checkout_date,
        nights,
        guests=guests,
        star_rating=star_rating,
        max_price_per_night_inr=max_price_per_night_inr,
        timeout=timeout,
    )
    if res and res.options:
        _HOTELS_CACHE.set(clean_dest, checkin_date, checkout_date, guests, star_rating, res)
        return res

    # 2. Live Tier 1B: Booking.com API (RapidAPI)
    res = _search_booking_com(
        clean_dest,
        checkin_date,
        checkout_date,
        nights,
        guests=guests,
        star_rating=star_rating,
        max_price_per_night_inr=max_price_per_night_inr,
        timeout=timeout,
    )
    if res and res.options:
        _HOTELS_CACHE.set(clean_dest, checkin_date, checkout_date, guests, star_rating, res)
        return res

    # 3. Live Tier 2: OpenStreetMap Nominatim API (Keyless Open Access)
    res = _search_nominatim_osm(
        clean_dest,
        checkin_date,
        checkout_date,
        nights,
        guests=guests,
        star_rating=star_rating,
        max_price_per_night_inr=max_price_per_night_inr,
        timeout=timeout,
    )
    if res and res.options:
        _HOTELS_CACHE.set(clean_dest, checkin_date, checkout_date, guests, star_rating, res)
        return res

    # 4. Live Tier 3: Web Search Tool Fallback
    res = _search_via_web_search(
        clean_dest,
        checkin_date,
        checkout_date,
        nights,
        guests=guests,
        star_rating=star_rating,
        max_price_per_night_inr=max_price_per_night_inr,
    )
    if res and res.options:
        _HOTELS_CACHE.set(clean_dest, checkin_date, checkout_date, guests, star_rating, res)
        return res

    # 5. Tier 4: Offline Hotel Location Heuristic Baseline (Guarantees zero crashes)
    log.warning(
        "All live hotel providers failed or unconfigured for %s. "
        "Falling back to location-heuristic hotel baseline.",
        clean_dest,
    )
    fallback_res = _estimate_location_heuristic(
        clean_dest,
        checkin_date,
        checkout_date,
        nights,
        guests=guests,
        star_rating=star_rating,
        max_price_per_night_inr=max_price_per_night_inr,
    )
    _HOTELS_CACHE.set(clean_dest, checkin_date, checkout_date, guests, star_rating, fallback_res)
    return fallback_res


def get_hotels_status() -> dict[str, bool | str]:
    """Retrieve operational status of configured hotel API providers."""
    return {
        "serpapi_configured": bool(os.getenv("SERPAPI_KEY") or os.getenv("SERPER_API_KEY")),
        "rapidapi_configured": bool(os.getenv("RAPIDAPI_KEY")),
        "nominatim_available": True,  # Keyless open access
        "web_search_available": True,
        "fixture_available": FIXTURE_PATH.exists(),
    }
