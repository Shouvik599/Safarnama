import json
import os
import urllib.request

from dotenv import load_dotenv

load_dotenv()
rapid_key = os.getenv("RAPIDAPI_KEY")

print("RAPIDAPI_KEY:", rapid_key[:10] + "..." if rapid_key else "NONE")

# Test Sky Scraper
url1 = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights?originSkyId=DEL&destinationSkyId=BOM&originEntityId=95673498&destinationEntityId=95673320&date=2026-10-15"
req1 = urllib.request.Request(
    url1, headers={"x-rapidapi-key": rapid_key, "x-rapidapi-host": "sky-scrapper.p.rapidapi.com"}
)
try:
    with urllib.request.urlopen(req1) as resp:
        print("Sky Scraper searchFlights Status:", resp.status)
        body = json.loads(resp.read().decode("utf-8"))
        print("Sky Scraper searchFlights Status Flag:", body.get("status"))
        itineraries = body.get("data", {}).get("itineraries", [])
        print(f"Sky Scraper searchFlights Itineraries Found: {len(itineraries)}")
        if itineraries:
            print("First Flight Price:", itineraries[0].get("price", {}).get("formatted"))
except Exception as e:
    print("Sky Scraper Error:", e)

# Test Indian Railway
url2 = "https://indian-railway-irctc.p.rapidapi.com/trainsBetweenStations?fromStationCode=NDLS&toStationCode=MMCT&dateOfJourney=2026-10-15"
req2 = urllib.request.Request(
    url2,
    headers={"x-rapidapi-key": rapid_key, "x-rapidapi-host": "indian-railway-irctc.p.rapidapi.com"},
)
try:
    with urllib.request.urlopen(req2) as resp:
        print("IRCTC Status:", resp.status)
        print("IRCTC Body:", resp.read().decode("utf-8")[:300])
except Exception as e:
    print("IRCTC Error:", e)
