import json
import os

countries_path = os.path.join('data', 'static', 'countries.json')
airports_path = os.path.join('data', 'static', 'airports.json')

countries = json.load(open(countries_path, encoding='utf-8'))
airports = json.load(open(airports_path, encoding='utf-8'))

# Clean map of country -> list of municipalities
country_airports_map = {}
for a in airports:
    iso = a.get('iso_country')
    m = a.get('municipality')
    if iso and m and len(m) > 1 and not m.startswith('('):
        clean_m = m.split('/')[0].split('(')[0].strip()
        if clean_m and clean_m.isascii():
            country_airports_map.setdefault(iso, set()).add(clean_m)

# Convert sets to sorted lists
country_airports_map = {k: sorted(list(v)) for k, v in country_airports_map.items()}

# Export as JSON in frontend/src/data/generated_countries.json
output_path = os.path.join('frontend', 'src', 'data', 'generated_countries.json')
cleaned_countries = []
for c in countries:
    iso = c.get('country_code', '')
    name = c.get('name', '')
    capital = c.get('capital', '')
    cities = country_airports_map.get(iso, [])
    # make sure capital is at front of cities
    top_cities = [capital] if capital and capital.isascii() else []
    for city in cities:
        if city not in top_cities and city.lower() != (capital or '').lower():
            top_cities.append(city)
        if len(top_cities) >= 5:
            break
    
    cleaned_countries.append({
        'code': iso,
        'name': name,
        'capital': capital,
        'region': c.get('region', ''),
        'subregion': c.get('subregion', ''),
        'is_schengen': c.get('is_schengen', False),
        'top_cities': top_cities[:4]
    })

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(cleaned_countries, f, indent=2, ensure_ascii=True)

print(f"Generated {len(cleaned_countries)} cleaned countries in {output_path}")
