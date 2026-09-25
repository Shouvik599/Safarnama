import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from src.tools.forex import (
    OFFLINE_BASELINE_RATES,
    _fetch_live_authenticated,
    _fetch_live_fawazahmed,
    _fetch_live_frankfurter,
    _fetch_live_open_access,
)
from src.tools.transport import (
    _estimate_physics_transport,
    _search_flights_sky,
    _search_indian_railways,
    _search_transport_rest,
    _search_via_web_search,
)
from src.tools.weather import (
    _fetch_open_meteo,
    _fetch_openweathermap,
    _fetch_wttr_in,
    get_weather_forecast,
)
from src.tools.web_search import _search_duckduckgo, _search_fixture, _search_tavily

print("=================================================================")
print("RUNNING COMPREHENSIVE LIVE API DIAGNOSTIC VERIFICATION")
print("=================================================================\n")

results_summary = []


def record(tool, provider, tier, status, details):
    results_summary.append(
        {"tool": tool, "provider": provider, "tier": tier, "status": status, "details": details}
    )
    print(f"[{status}] {tool} ({tier}) -> {provider}: {details}")


# -------------------------------------------------------------
# 1. FOREX TOOL LIVE API TESTING
# -------------------------------------------------------------
print("--- 1. Testing Forex Tool Providers ---")
try:
    rates, provider, is_est, ts = _fetch_live_open_access()
    if rates and "INR" in rates:
        record(
            "Forex", "Open-ER-API", "Tier 1", "SUCCESS", f"1 USD = ₹{rates['INR']:.2f} ({provider})"
        )
    else:
        record("Forex", "Open-ER-API", "Tier 1", "FAILED", "Empty or missing INR rate")
except Exception as e:
    record("Forex", "Open-ER-API", "Tier 1", "FAILED", str(e))

try:
    rates, provider, is_est, ts = _fetch_live_fawazahmed()
    if rates and "INR" in rates:
        record(
            "Forex",
            "FawazAhmed CDN",
            "Tier 2",
            "SUCCESS",
            f"1 USD = ₹{rates['INR']:.2f} ({provider})",
        )
    else:
        record("Forex", "FawazAhmed CDN", "Tier 2", "FAILED", "Empty or missing INR rate")
except Exception as e:
    record("Forex", "FawazAhmed CDN", "Tier 2", "FAILED", str(e))

try:
    rates, provider, is_est, ts = _fetch_live_frankfurter()
    if rates and "INR" in rates:
        record(
            "Forex",
            "Frankfurter ECB",
            "Tier 3",
            "SUCCESS",
            f"1 USD = ₹{rates['INR']:.2f} ({provider})",
        )
    else:
        record("Forex", "Frankfurter ECB", "Tier 3", "FAILED", "Empty or missing INR rate")
except Exception as e:
    record("Forex", "Frankfurter ECB", "Tier 3", "FAILED", str(e))

er_key = os.getenv("EXCHANGERATE_API_KEY")
if er_key:
    try:
        rates, provider, is_est, ts = _fetch_live_authenticated(er_key)
        if rates and "INR" in rates:
            record(
                "Forex",
                "ExchangeRate-API Auth",
                "Tier 4",
                "SUCCESS",
                f"1 USD = ₹{rates['INR']:.2f} ({provider})",
            )
        else:
            record(
                "Forex", "ExchangeRate-API Auth", "Tier 4", "FAILED", "Empty or missing INR rate"
            )
    except Exception as e:
        record("Forex", "ExchangeRate-API Auth", "Tier 4", "FAILED", str(e))
else:
    record("Forex", "ExchangeRate-API Auth", "Tier 4", "SKIPPED", "EXCHANGERATE_API_KEY not set")

if "INR" in OFFLINE_BASELINE_RATES:
    record(
        "Forex",
        "Offline Rates Table",
        "Tier 5 (Offline)",
        "SUCCESS",
        f"1 USD = ₹{OFFLINE_BASELINE_RATES['INR']:.2f} (Static Baseline)",
    )

# -------------------------------------------------------------
# 2. WEATHER TOOL LIVE API TESTING
# -------------------------------------------------------------
print("\n--- 2. Testing Weather Tool Providers ---")
lat, lon = 35.6762, 139.6503  # Tokyo
date_list = ["2026-10-15", "2026-10-16", "2026-10-17"]

try:
    w1_map = _fetch_open_meteo(lat, lon, date_list, timeout=8.0)
    if w1_map:
        day0 = next(iter(w1_map.values()))
        record(
            "Weather",
            "Open-Meteo API",
            "Tier 1",
            "SUCCESS",
            f"16-day forecast available: Max {day0.temp_max_c}°C, {day0.condition}",
        )
    else:
        record("Weather", "Open-Meteo API", "Tier 1", "FAILED", "Empty response")
except Exception as e:
    record("Weather", "Open-Meteo API", "Tier 1", "FAILED", str(e))

try:
    w2_map = _fetch_wttr_in(lat, lon, date_list, timeout=8.0)
    if w2_map:
        day0 = next(iter(w2_map.values()))
        record(
            "Weather",
            "wttr.in JSON API",
            "Tier 2",
            "SUCCESS",
            f"3-day forecast available: Max {day0.temp_max_c}°C, {day0.condition}",
        )
    else:
        record("Weather", "wttr.in JSON API", "Tier 2", "FAILED", "Empty response")
except Exception as e:
    record("Weather", "wttr.in JSON API", "Tier 2", "FAILED", str(e))

owm_key = os.getenv("OPENWEATHERMAP_API_KEY")
if owm_key:
    try:
        w3_map = _fetch_openweathermap(lat, lon, owm_key, timeout=8.0)
        if w3_map:
            day0 = next(iter(w3_map.values()))
            record(
                "Weather",
                "OpenWeatherMap 5-Day",
                "Tier 3",
                "SUCCESS",
                f"6-day forecast available: Max {day0.temp_max_c}°C, {day0.condition}",
            )
        else:
            record("Weather", "OpenWeatherMap 5-Day", "Tier 3", "FAILED", "Empty response")
    except Exception as e:
        record("Weather", "OpenWeatherMap 5-Day", "Tier 3", "FAILED", str(e))
else:
    record("Weather", "OpenWeatherMap 5-Day", "Tier 3", "SKIPPED", "OPENWEATHERMAP_API_KEY not set")

try:
    w4 = get_weather_forecast(
        lat, lon, start_date=date_list[0], end_date=date_list[-1], use_fixture=True
    )
    if w4 and len(w4.daily_forecasts) > 0:
        record(
            "Weather",
            "Offline Climate Baseline",
            "Tier 4 (Offline)",
            "SUCCESS",
            f"Fixture/Climate: {w4.summary}",
        )
except Exception as e:
    record("Weather", "Offline Climate Baseline", "Tier 4 (Offline)", "FAILED", str(e))

# -------------------------------------------------------------
# 3. WEB SEARCH TOOL LIVE API TESTING
# -------------------------------------------------------------
print("\n--- 3. Testing Web Search Tool Providers ---")
query = "japan tourist visa requirements for indian citizens"

try:
    s1 = _search_tavily(query, max_results=3)
    if s1 and len(s1.results) > 0:
        record(
            "Web Search",
            "Tavily Search API",
            "Tier 1",
            "SUCCESS",
            f"Fetched {len(s1.results)} items: '{s1.results[0].title[:45]}...'",
        )
    else:
        record("Web Search", "Tavily Search API", "Tier 1", "FAILED", "Empty results or key error")
except Exception as e:
    record("Web Search", "Tavily Search API", "Tier 1", "FAILED", str(e))

try:
    s2 = _search_duckduckgo(query, max_results=3)
    if s2 and len(s2.results) > 0:
        record(
            "Web Search",
            "DuckDuckGo Open API",
            "Tier 2",
            "SUCCESS",
            f"Fetched {len(s2.results)} items: '{s2.results[0].title[:45]}...'",
        )
    else:
        record("Web Search", "DuckDuckGo Open API", "Tier 2", "FAILED", "Empty results")
except Exception as e:
    record("Web Search", "DuckDuckGo Open API", "Tier 2", "FAILED", str(e))

fc_key = os.getenv("FIRECRAWL_API_KEY")
if fc_key:
    try:
        import urllib.request

        url = "https://api.firecrawl.dev/v2/search"
        payload = json.dumps({"query": query, "limit": 3}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Authorization": f"Bearer {fc_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            web_items = data.get("data", {}).get("web", [])
            if web_items:
                record(
                    "Web Search",
                    "Firecrawl Search API",
                    "Tier 3",
                    "SUCCESS",
                    f"Fetched {len(web_items)} web results: '{web_items[0].get('title')[:45]}...'",
                )
            else:
                record(
                    "Web Search",
                    "Firecrawl Search API",
                    "Tier 3",
                    "FAILED",
                    "HTTP 200 but empty web results",
                )
    except Exception as e:
        record("Web Search", "Firecrawl Search API", "Tier 3", "FAILED", str(e))
else:
    record("Web Search", "Firecrawl Search API", "Tier 3", "SKIPPED", "FIRECRAWL_API_KEY not set")

try:
    s4 = _search_fixture(query, max_results=3)
    if s4 and len(s4.results) > 0:
        record(
            "Web Search",
            "Offline Search Fixture",
            "Tier 4 (Offline)",
            "SUCCESS",
            f"Fetched {len(s4.results)} mock items: '{s4.results[0].title[:45]}...'",
        )
except Exception as e:
    record("Web Search", "Offline Search Fixture", "Tier 4 (Offline)", "FAILED", str(e))

# -------------------------------------------------------------
# 4. TRANSPORT TOOL LIVE API TESTING
# -------------------------------------------------------------
print("\n--- 4. Testing Transport Tool Providers ---")

# Test Sky Scraper via RapidAPI directly / via tool with entity resolution
rapid_key = os.getenv("RAPIDAPI_KEY")
if rapid_key:
    try:
        import urllib.request

        url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights?originSkyId=DEL&destinationSkyId=BOM&originEntityId=95673498&destinationEntityId=95673320&date=2026-10-15"
        req = urllib.request.Request(
            url,
            headers={"x-rapidapi-key": rapid_key, "x-rapidapi-host": "sky-scrapper.p.rapidapi.com"},
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            itins = data.get("data", {}).get("itineraries", [])
            if itins:
                first_p = itins[0].get("price", {}).get("formatted", "N/A")
                record(
                    "Transport",
                    "Sky Scraper (RapidAPI Flights)",
                    "Tier 1A",
                    "SUCCESS",
                    f"Fetched {len(itins)} live flight itineraries (Lowest price: {first_p})",
                )
            else:
                record(
                    "Transport",
                    "Sky Scraper (RapidAPI Flights)",
                    "Tier 1A",
                    "FAILED",
                    "Empty itineraries array",
                )
    except Exception as e:
        record("Transport", "Sky Scraper (RapidAPI Flights)", "Tier 1A", "FAILED", str(e))
else:
    record(
        "Transport", "Sky Scraper (RapidAPI Flights)", "Tier 1A", "SKIPPED", "RAPIDAPI_KEY not set"
    )

# Test Flights Sky
try:
    t2 = _search_flights_sky("DEL", "BOM", "2026-10-15")
    if t2 and len(t2.options) > 0:
        record(
            "Transport",
            "Flights Sky (RapidAPI)",
            "Tier 1B",
            "SUCCESS",
            f"Fetched {len(t2.options)} flights: {t2.options[0].carrier} ₹{t2.options[0].price_inr}",
        )
    else:
        record(
            "Transport",
            "Flights Sky (RapidAPI)",
            "Tier 1B",
            "FAILED",
            "HTTP 404 / Invalid Endpoint (Unsubscribed sub-API)",
        )
except Exception as e:
    record("Transport", "Flights Sky (RapidAPI)", "Tier 1B", "FAILED", str(e))

# Test Indian Railways
try:
    t3 = _search_indian_railways("NDLS", "MMCT", "2026-10-15")
    if t3 and len(t3.options) > 0:
        record(
            "Transport",
            "Indian Railway IRCTC (RapidAPI)",
            "Tier 1C",
            "SUCCESS",
            f"Fetched {len(t3.options)} trains: {t3.options[0].carrier} ₹{t3.options[0].price_inr}",
        )
    else:
        record(
            "Transport",
            "Indian Railway IRCTC (RapidAPI)",
            "Tier 1C",
            "FAILED",
            "HTTP 404 / Endpoint structure changed (Unsubscribed sub-API)",
        )
except Exception as e:
    record("Transport", "Indian Railway IRCTC (RapidAPI)", "Tier 1C", "FAILED", str(e))

# Test transport.rest
try:
    t4 = _search_transport_rest("PARIS", "LONDON", "2026-10-15")
    if t4 and len(t4.options) > 0:
        record(
            "Transport",
            "transport.rest API (Euro Rail)",
            "Tier 1D",
            "SUCCESS",
            f"Fetched {len(t4.options)} journeys: {t4.options[0].carrier} ₹{t4.options[0].price_inr}",
        )
    else:
        record(
            "Transport",
            "transport.rest API (Euro Rail)",
            "Tier 1D",
            "FAILED",
            "Station ID resolution empty",
        )
except Exception as e:
    record("Transport", "transport.rest API (Euro Rail)", "Tier 1D", "FAILED", str(e))

# Test Web Search Fallback
try:
    t5 = _search_via_web_search("DEL", "BOM", "2026-10-15", mode="FLIGHT")
    if t5 and len(t5.options) > 0:
        record(
            "Transport",
            "Live Web Search Fallback",
            "Tier 2",
            "SUCCESS",
            f"Retrieved {len(t5.options)} live flight options via Tavily/DuckDuckGo web search",
        )
    else:
        record(
            "Transport",
            "Live Web Search Fallback",
            "Tier 2",
            "FAILED",
            "No web search options parsed",
        )
except Exception as e:
    record("Transport", "Live Web Search Fallback", "Tier 2", "FAILED", str(e))

# Test Distance Physics Engine
try:
    t6 = _estimate_physics_transport("DEL", "BOM", "2026-10-15")
    if t6 and len(t6.options) > 0:
        record(
            "Transport",
            "Distance Physics Engine",
            "Tier 3 (Offline)",
            "SUCCESS",
            f"Calculated {len(t6.options)} physics estimates (Air ₹{t6.options[0].price_inr:,.2f})",
        )
except Exception as e:
    record("Transport", "Distance Physics Engine", "Tier 3 (Offline)", "FAILED", str(e))

print("\n=================================================================")
print("ALL DIAGNOSTIC TESTS COMPLETE")
print("=================================================================")
