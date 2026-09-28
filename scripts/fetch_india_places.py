"""Phase 1 — Ingestion of Indian States, UTs, and Cities.

Fetches the complete hierarchy of Indian administrative divisions:
1. 28 States + 8 Union Territories with standard ISO 3166-2 codes, coordinates,
   and administrative types from ``api.countrystatecity.in``.
2. Complete list of all ~4,200 Indian cities and settlements categorized by state.
3. Curated prominence tagging for iconic Indian tourist destinations, hill stations,
   cultural heritage hubs, and spiritual circuits.

Outputs:
- ``data/static/india_places.json`` (Backend deterministic access layer)
- ``frontend/src/data/india_places.json`` (Frontend autocomplete & route resolver)
- Refreshes ``frontend/src/data/indian_states_uts.json`` with enriched cities.

Usage::

    # Default run with embedded/configured API key:
    python scripts/fetch_india_places.py

    # Override key or specify limit for testing:
    python scripts/fetch_india_places.py --api-key <YOUR_KEY>
    python scripts/fetch_india_places.py --limit 3 --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Logging & Paths
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("fetch_india_places")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_OUTPUT_PATH = PROJECT_ROOT / "data" / "static" / "india_places.json"
FRONTEND_OUTPUT_PATH = PROJECT_ROOT / "frontend" / "src" / "data" / "india_places.json"
FRONTEND_STATES_PATH = PROJECT_ROOT / "frontend" / "src" / "data" / "indian_states_uts.json"

DEFAULT_API_KEY = "53a77eb3c476d68bf975a21b6cbb802007f139a216e31548df3d1ed70baa9b36"
API_BASE_URL = "https://api.countrystatecity.in/v1/countries/IN"

# ---------------------------------------------------------------------------
# Prominent Indian Tourist Hubs (Tagged as is_popular for Priority Ranking)
# ---------------------------------------------------------------------------

POPULAR_INDIAN_DESTINATIONS: set[str] = {
    # Rajasthan
    "Jaipur", "Udaipur", "Jodhpur", "Jaisalmer", "Pushkar", "Mount Abu",
    "Bikaner", "Ranthambore", "Ajmer", "Chittorgarh", "Alwar", "Kumbhalgarh",
    # Himachal Pradesh
    "Manali", "Shimla", "Dharamshala", "McLeod Ganj", "Kullu", "Kasauli",
    "Dalhousie", "Spiti", "Kaza", "Bir", "Billing",
    # Uttarakhand
    "Rishikesh", "Haridwar", "Nainital", "Mussoorie", "Dehradun", "Auli",
    "Jim Corbett", "Kedarnath", "Badrinath", "Almora", "Ranikhet",
    # Jammu & Kashmir / Ladakh
    "Srinagar", "Gulmarg", "Pahalgam", "Sonamarg", "Leh", "Nubra", "Kargil",
    # Goa
    "Panaji", "Calangute", "Baga", "Candolim", "Margao", "Vasco da Gama",
    "Anjuna", "Arambol", "Palolem",
    # Kerala
    "Kochi", "Cochin", "Munnar", "Alleppey", "Alappuzha", "Wayanad", "Varkala",
    "Kovalam", "Thekkady", "Kumarakom", "Thrissur", "Thiruvananthapuram",
    # Tamil Nadu
    "Ooty", "Udhagamandalam", "Kodaikanal", "Madurai", "Rameswaram", "Chennai",
    "Mahabalipuram", "Kanyakumari", "Coimbatore", "Thanjavur",
    # Karnataka
    "Bengaluru", "Bangalore", "Mysuru", "Mysore", "Hampi", "Coorg", "Madikeri",
    "Gokarna", "Chikmagalur", "Badami", "Mangaluru", "Mangalore",
    # Maharashtra
    "Mumbai", "Pune", "Lonavala", "Khandala", "Mahabaleshwar", "Alibaug",
    "Nashik", "Shirdi", "Aurangabad", "Chhatrapati Sambhajinagar", "Panchgani",
    # Uttar Pradesh
    "Varanasi", "Agra", "Prayagraj", "Allahabad", "Lucknow", "Ayodhya",
    "Mathura", "Vrindavan", "Sarnath",
    # West Bengal
    "Kolkata", "Darjeeling", "Kalimpong", "Siliguri", "Digha", "Sundarbans",
    # Sikkim & Northeast
    "Gangtok", "Pelling", "Lachung", "Shillong", "Cherrapunji", "Sohra",
    "Tawang", "Kaziranga", "Guwahati", "Majuli", "Ziro",
    # Madhya Pradesh
    "Khajuraho", "Bhopal", "Indore", "Ujjain", "Gwalior", "Orchha",
    "Pachmarhi", "Bandhavgarh", "Kanha",
    # Gujarat
    "Ahmedabad", "Rann of Kutch", "Bhuj", "Gir", "Somnath", "Dwarka", "Vadodara",
    # Odisha
    "Puri", "Bhubaneswar", "Konark", "Cuttack",
    # Punjab & Haryana & UTs
    "Amritsar", "Chandigarh", "Puducherry", "Pondicherry", "Port Blair", "Havelock",
    "Delhi", "New Delhi",
}


# ---------------------------------------------------------------------------
# API Client with Retries & Exponential Backoff
# ---------------------------------------------------------------------------

def fetch_json_with_retries(
    url: str,
    api_key: str,
    max_retries: int = 4,
    base_backoff: float = 0.5,
    timeout: float = 20.0,
) -> Any:
    """Perform an authenticated HTTP GET request with exponential backoff retries."""
    headers = {
        "X-CSCAPI-KEY": api_key,
        "User-Agent": "Safarnama-Travel-Engine/1.0",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    raw_bytes = response.read()
                    return json.loads(raw_bytes.decode("utf-8"))
                raise urllib.error.HTTPError(
                    url, response.status, f"Unexpected HTTP status {response.status}", response.headers, None
                )
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if attempt == max_retries:
                log.error("Failed fetching %s after %d attempts: %s", url, max_retries, exc)
                raise
            delay = base_backoff * (2 ** (attempt - 1))
            log.warning("Attempt %d for %s failed (%s); retrying in %.2fs...", attempt, url, exc, delay)
            time.sleep(delay)


# ---------------------------------------------------------------------------
# Core Ingestion Logic
# ---------------------------------------------------------------------------

def fetch_india_states_and_cities(
    api_key: str,
    limit_states: int | None = None,
    delay_between_requests: float = 0.05,
) -> dict[str, Any]:
    """Fetch all 36 Indian states/UTs and their respective cities from the API."""
    states_url = f"{API_BASE_URL}/states"
    log.info("Fetching Indian states and union territories from %s...", states_url)
    states_raw = fetch_json_with_retries(states_url, api_key)

    if not isinstance(states_raw, list):
        raise ValueError(f"Expected list from {states_url}, got {type(states_raw)}")

    log.info("Retrieved %d states/UTs from API.", len(states_raw))

    if limit_states:
        states_raw = states_raw[:limit_states]
        log.info("Limiting processing to first %d states.", limit_states)

    processed_states: list[dict[str, Any]] = []
    all_flat_cities: list[dict[str, Any]] = []
    popular_cities_list: list[dict[str, Any]] = []

    for idx, s in enumerate(states_raw, start=1):
        state_name: str = s.get("name", "").strip()
        state_code: str = s.get("iso2", "").strip()
        state_id: str = state_name.lower().replace(" ", "-").replace("&", "and")

        # Determine administrative type
        is_ut = any(
            ut in state_name.lower()
            for ut in [
                "andaman", "chandigarh", "dadra", "daman", "delhi", "jammu and kashmir",
                "ladakh", "lakshadweep", "puducherry",
            ]
        )
        state_type = "UT" if is_ut else "STATE"

        log.info("[%d/%d] Fetching cities for %s (%s)...", idx, len(states_raw), state_name, state_code)
        cities_url = f"{API_BASE_URL}/states/{state_code}/cities"

        try:
            cities_raw = fetch_json_with_retries(cities_url, api_key)
            if not isinstance(cities_raw, list):
                cities_raw = []
        except Exception as exc:
            log.warning("Could not fetch cities for %s (%s): %s", state_name, state_code, exc)
            cities_raw = []

        time.sleep(delay_between_requests)

        # Process and clean cities
        state_city_names: list[str] = []
        state_popular_cities: list[str] = []

        for c in cities_raw:
            c_name: str = c.get("name", "").strip()
            if not c_name:
                continue

            state_city_names.append(c_name)

            # Check if this city is a recognized popular travel hub
            is_popular = (
                c_name in POPULAR_INDIAN_DESTINATIONS
                or any(p.lower() == c_name.lower() for p in POPULAR_INDIAN_DESTINATIONS)
            )

            city_record = {
                "id": f"in-{c_name.lower().replace(' ', '-')}",
                "name": c_name,
                "state_name": state_name,
                "state_code": state_code,
                "state_id": state_id,
                "scope": "DOMESTIC",
                "is_popular": is_popular,
            }

            all_flat_cities.append(city_record)

            if is_popular:
                state_popular_cities.append(c_name)
                popular_cities_list.append(city_record)

        # Fallback if no cities tagged as popular: take top 3 cities or capital
        if not state_popular_cities and state_city_names:
            state_popular_cities = state_city_names[:3]

        processed_states.append({
            "id": state_id,
            "name": state_name,
            "code": state_code,
            "type": state_type,
            "latitude": float(s.get("latitude") or 0.0),
            "longitude": float(s.get("longitude") or 0.0),
            "total_cities": len(state_city_names),
            "popular_cities": state_popular_cities,
            "cities": state_city_names,
        })

    # Sort popular cities and total cities
    all_flat_cities.sort(key=lambda x: (not x["is_popular"], x["name"]))
    popular_cities_list.sort(key=lambda x: x["name"])

    catalog = {
        "metadata": {
            "source": "api.countrystatecity.in",
            "country": "India",
            "country_code": "IN",
            "total_states": len(processed_states),
            "total_cities": len(all_flat_cities),
            "total_popular_destinations": len(popular_cities_list),
            "ingested_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "states": processed_states,
        "popular_destinations": popular_cities_list,
        "cities": all_flat_cities,
    }

    return catalog


def enrich_frontend_states_registry(catalog: dict[str, Any]) -> None:
    """Enrich frontend/src/data/indian_states_uts.json with expanded cities."""
    if not FRONTEND_STATES_PATH.exists():
        log.warning("%s not found, skipping frontend states registry update.", FRONTEND_STATES_PATH)
        return

    try:
        with open(FRONTEND_STATES_PATH, "r", encoding="utf-8") as f:
            existing_states = json.load(f)

        state_city_map = {s["id"]: s for s in catalog["states"]}

        for s in existing_states:
            s_id = s.get("id")
            if s_id in state_city_map:
                api_state = state_city_map[s_id]
                existing_top = s.get("top_cities", [])
                api_popular = api_state.get("popular_cities", [])
                api_all = api_state.get("cities", [])

                # Merge preserving order: existing curated top first, then api popular, then remaining cities
                merged = list(existing_top)
                for c in api_popular + api_all:
                    if c not in merged:
                        merged.append(c)

                s["top_cities"] = merged[:15]  # Rich top 15 cities per state

        with open(FRONTEND_STATES_PATH, "w", encoding="utf-8") as f:
            json.dump(existing_states, f, indent=2, ensure_ascii=False)
        log.info("Successfully refreshed %s with enriched cities.", FRONTEND_STATES_PATH)
    except Exception as exc:
        log.warning("Could not enrich %s: %s", FRONTEND_STATES_PATH, exc)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest Indian states, union territories, and cities from api.countrystatecity.in."
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("CSC_API_KEY") or os.getenv("COUNTRYSTATECITY_API_KEY") or DEFAULT_API_KEY,
        help="API Key for api.countrystatecity.in",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of states to process (useful for testing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate without writing files to disk",
    )
    args = parser.parse_args()

    if not args.api_key:
        log.error("No API key provided. Set CSC_API_KEY environment variable or pass --api-key.")
        sys.exit(1)

    log.info("Starting Indian states, UTs, and cities ingestion...")
    catalog = fetch_india_states_and_cities(api_key=args.api_key, limit_states=args.limit)

    log.info(
        "Ingestion completed: %d states/UTs, %d total cities, %d popular destinations.",
        len(catalog["states"]),
        len(catalog["cities"]),
        len(catalog["popular_destinations"]),
    )

    if args.dry_run:
        log.info("Dry-run enabled. Output files not written.")
        print(json.dumps(catalog["metadata"], indent=2))
        return

    # Ensure output directories exist
    BACKEND_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write backend and frontend static JSON files
    with open(BACKEND_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    log.info("Wrote backend dataset: %s", BACKEND_OUTPUT_PATH)

    with open(FRONTEND_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    log.info("Wrote frontend dataset: %s", FRONTEND_OUTPUT_PATH)

    # Refresh indian_states_uts.json with enriched cities list
    enrich_frontend_states_registry(catalog)

    log.info("All Indian geographic data successfully fetched and synchronized!")


if __name__ == "__main__":
    main()
