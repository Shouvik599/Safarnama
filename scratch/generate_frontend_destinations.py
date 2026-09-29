import json
import os

countries_path = os.path.join('data', 'static', 'countries.json')
airports_path = os.path.join('data', 'static', 'airports.json')
visa_path = os.path.join('data', 'static', 'visa_rules_enriched.json')

countries = json.load(open(countries_path, encoding='utf-8'))
airports = json.load(open(airports_path, encoding='utf-8'))

# Build airport municipality map per country code
country_cities = {}
for a in airports:
    iso = a.get('iso_country')
    m = a.get('municipality')
    if iso and m and len(m) > 1 and not m.startswith('('):
        clean_m = m.split('/')[0].split('(')[0].strip()
        if clean_m and clean_m.isascii():
            country_cities.setdefault(iso, set()).add(clean_m)

print(f"Loaded {len(countries)} countries, {len(airports)} airports.")
