# Safarnama — Project Memory

> Snapshot for resuming implementation. Do not duplicate `prd.md`, `architecture.md`, `rules.md`, or `phases.md`.

## Current Status

**Phase 3 in progress.** Tool 1: Deterministic Calculator, Tool 2: Forex Currency Converter, and Tool 3: Weather Forecaster complete.

Do not start subsequent tools until explicitly requested.

## Current implementation phase

Phase 3 — External Tool Layer (Calculator, Forex, and Weather Tools complete)

## Completed functionality

### Phase 0 (foundation)
- `uv`-managed Python project (`safarnama` 0.1.0, `requires-python >=3.11`)
- Hatchling src layout: `src/` is the importable package (`import src`)
- Empty package modules: `src.api`, `src.graph`, `src.models`, `src.nodes`, `src.prompts`, `src.tools`
- pytest + Ruff as **dev** dependencies only
- Placeholder dirs for Phase 1: `data/static/`, `data/fixtures/`, `scripts/`, `tests/integration/`

### Phase 1 (static data ingestion — updated & verified)
- `scripts/fetch_airports.py` — downloads from `davidmegginson/ourairports-data`
- `scripts/fetch_visa_rules.py` — fetches dual CSVs (`passport-index-tidy.csv` + `passport-index-tidy-iso2.csv`),
  joins by row position, writes normalized baseline records to `data/static/visa_rules.json`
- `scripts/enrich_visa_rules.py` — reads baseline from `data/static/visa_rules.json`, performs live web research
  via Tavily (`TAVILY_VISA_ENRICHMENT_API_KEY`), synthesizes multi-option records via Google Gemini structured
  output schema with fallback across models on 429/503, writes to `data/static/visa_rules_enriched.json`
  (199/199 destinations enriched)
- `scripts/fetch_country_profiles.py` — queries REST Countries v5 across paginated batches (`limit=100`) using
  `REST_COUNTRIES_API_KEY`, parses 250 sovereign states and territories into `CountryProfile` models, writing
  to `data/static/countries.json`
- All ingestion scripts: preserve existing JSON on network failure; exit 0/1

### Phase 2 (static data access layer — complete)
- `src/models/airport.py` — Canonical Pydantic domain model for `Airport`
- `src/models/country.py` — Canonical Pydantic domain models: `CountryProfile`, `CurrencyInfo`, `LanguageInfo`, `Coordinates`
- `src/models/visa.py` — Added `BaseVisaRule` alongside `VisaOption` and `EnrichedVisaRecord`
- `src/tools/static_data.py` — High-performance runtime access layer:
  - Custom typed exception hierarchy: `StaticDataError`, `RecordNotFoundError`, `AirportNotFoundError`,
    `CountryNotFoundError`, `VisaRuleNotFoundError`, `InvalidLookupError`
  - In-memory `StaticDataStore` singleton caching all 4 datasets on initial access without repeated file I/O:
    - 3,244 airports indexed by IATA code, city/municipality, and ISO country
    - 250 countries indexed by ISO-2, ISO-3, English name, and official name
    - 199 base visa rules and 199 enriched visa records indexed by country code and destination name
  - Query API:
    - `get_airport(iata)` / `find_airport(iata)` / `get_airport_coordinates(iata)`
    - `get_airports_by_city(city)` / `get_airports_by_country(iso_country)`
    - `get_country(query)` / `find_country(query)` / `is_schengen(query)`
    - `get_ist_time_difference_hours(query, timezone=None)` — intelligent timezone resolution using capital coordinates
      longitude approximation (`lng / 15.0`) for multi-timezone countries (e.g. France, USA, Australia, Russia)
    - `get_visa_baseline(destination_or_code)`
    - `get_enriched_visa(destination_or_code)`
    - `get_visa_rule(destination_or_code)` — returns enriched multi-option record if available, falling back to baseline
    - `reload_static_data()` — thread-safe cache invalidation and reloading
- `src/tools/__init__.py` and `src/models/__init__.py` — Clean public package exports

### Phase 3 (External Tool Layer — in progress)
- **Tool 1: Deterministic Calculator (`src/tools/calculator.py`)**:
  - Enforces the core architectural rule forbidding LLM-based arithmetic.
  - Pure deterministic decimal arithmetic with bankers-safe half-up rounding to 2 decimal places.
  - Functions: `round_currency`, `calculate_total_expenses`, `calculate_per_person_cost`, `calculate_daily_average`,
    `calculate_contingency_buffer`, `calculate_total_with_buffer`, `calculate_budget_variance`,
    `calculate_rooms_needed`, `calculate_budget_breakdown`.
  - Pydantic models: `BudgetVariance`, `BudgetBreakdown`.
  - Typed exceptions: `CalculatorError`, `InvalidAmountError`, `InvalidTravelerCountError`, `InvalidDaysError`,
    `InvalidPercentageError`.
  - Fully re-exported in `src/tools/__init__.py`.
  - 56 unit tests in `tests/unit/test_calculator.py`.
- **Tool 2: Deterministic Forex Currency Converter (`src/tools/forex.py`)**:
  - Ensures all foreign travel costs (USD, EUR, GBP, JPY, AED, THB, SGD, UZS, NOK, etc.) are converted to INR deterministically.
  - Multi-tier resilience chain:
    1. In-memory cache with 24-hour TTL to prevent redundant network requests.
    2. Fixture mode (`data/fixtures/mock_forex.json`) for 100% offline, zero-quota testing.
    3. Live Tier 1: ExchangeRate-API Open Access (`https://open.er-api.com/v6/latest/USD`).
    4. Live Tier 2: FawazAhmed Currency API (`@fawazahmed0/currency-api` via jsDelivr CDN and Cloudflare Pages mirror, 340+ currencies, zero auth).
    5. Live Tier 3: Frankfurter API (`https://api.frankfurter.dev/v1/latest?base=USD`, European Central Bank reference rates, zero auth).
    6. Live Tier 4: ExchangeRate-API Authenticated (`https://v6.exchangerate-api.com/v6/{KEY}/latest/USD` if `EXCHANGERATE_API_KEY` present).
    7. Offline baseline rates table: built-in dictionary for ~40 global currencies guaranteeing Safarnama never crashes.
  - Functions: `convert_to_inr`, `convert_currency`, `get_exchange_rate`, `get_rates_table`, `clear_forex_cache`.
  - Pydantic model: `ForexConversion` with full provenance, rate, timestamps, and `is_estimated` flag.
  - Typed exceptions: `ForexError`, `UnsupportedCurrencyError`, `ForexNetworkError`.
  - Fully re-exported in `src/tools/__init__.py`.
  - 19 unit tests in `tests/unit/test_forex.py`.
- **Tool 3: Deterministic Weather Forecaster (`src/tools/weather.py`)**:
  - Provides structured multi-day forecasts (temperatures, precipitation probability, WMO conditions, outdoor friendliness) by destination coordinates.
  - Multi-tier resilience cascade:
    1. Fixture mode (`data/fixtures/mock_weather.json`) for 100% deterministic offline unit testing.
    2. In-memory cache with 3-hour TTL per coordinate/date pair.
    3. Live Tier 1: Open-Meteo Forecast API (`https://api.open-meteo.com/v1/forecast`, zero auth, up to 16 days daily forecast).
    4. Live Tier 2: wttr.in JSON API (`https://wttr.in/{lat},{lon}?format=j1`, zero auth, global fallback).
    5. Live Tier 3: OpenWeatherMap 5-Day/3-Hour Forecast API (`https://api.openweathermap.org/data/2.5/forecast` using `OPENWEATHERMAP_API_KEY`).
    6. Tier 4: Offline Climate Baseline Heuristic (latitude + seasonal solar declination cycle physics guaranteeing Safarnama never crashes).
  - Functions: `get_weather_forecast`, `is_outdoor_friendly`, `generate_weather_summary`, `clear_weather_cache`.
  - Pydantic models: `DailyWeatherForecast`, `WeatherForecastResult` in `src/models/weather.py` (re-exported in `src.models` and `src.tools`).
  - Typed exceptions: `WeatherError`, `InvalidCoordinatesError`, `InvalidDateRangeError`, `WeatherAPIError`.
  - Fully re-exported in `src/tools/__init__.py`.
  - 17 unit tests in `tests/unit/test_weather.py`.

## Important files/modules

| Path | Role |
|---|---|
| `pyproject.toml` | Project, pytest, Ruff, uv dev group |
| `uv.lock` | Locked deps via uv (never pip) |
| `src/models/airport.py` | Canonical Pydantic model: `Airport` |
| `src/models/country.py` | Canonical Pydantic models: `CountryProfile`, `CurrencyInfo`, `LanguageInfo`, `Coordinates` |
| `src/models/visa.py` | Canonical Pydantic models: `BaseVisaRule`, `VisaOption`, `EnrichedVisaRecord` |
| `src/models/weather.py` | Canonical Pydantic models: `DailyWeatherForecast`, `WeatherForecastResult` |
| `src/models/__init__.py` | Re-exports all domain models |
| `src/tools/static_data.py` | Phase 2 in-memory static data access layer & query functions |
| `src/tools/calculator.py` | Phase 3 deterministic travel budget calculator |
| `src/tools/forex.py` | Phase 3 deterministic foreign currency converter with multi-tier live fallbacks |
| `src/tools/weather.py` | Phase 3 deterministic weather forecasting tool with multi-tier live fallbacks |
| `src/tools/__init__.py` | Re-exports static data, calculator, forex, and weather tools API |
| `scripts/fetch_airports.py` | Airport ingestion script |
| `scripts/fetch_visa_rules.py` | Visa rules ingestion — dual-CSV source |
| `scripts/enrich_visa_rules.py` | On-demand Gemini enrichment script |
| `scripts/fetch_country_profiles.py` | REST Countries v5 profile ingestion script |
| `data/static/airports.json` | Generated: 3244 large/medium airports worldwide |
| `data/static/visa_rules.json` | Generated: 199 destination rules for Indian passport |
| `data/static/visa_rules_enriched.json` | Generated: 199 enriched destination rules for Indian passport |
| `data/static/countries.json` | Generated: 250 enriched country profiles |
| `data/fixtures/mock_forex.json` | Generated: 35+ currency rates fixture for offline forex testing |
| `data/fixtures/mock_weather.json` | Generated: multi-day weather forecast fixture for offline weather testing |
| `tests/unit/test_weather.py` | 17 deterministic weather unit tests |
| `tests/unit/test_forex.py` | 19 deterministic forex unit tests |
| `tests/unit/test_calculator.py` | 56 deterministic calculator unit tests |
| `tests/unit/test_static_data.py` | 31 static data access layer unit tests |
| `tests/unit/test_fetch_airports.py` | 23 airport ingestion tests |
| `tests/unit/test_fetch_visa_rules.py` | 50 visa rules ingestion tests |
| `tests/unit/test_fetch_country_profiles.py` | 8 country profile ingestion tests |
| `tests/unit/test_enrich_visa_rules.py` | 6 visa enrichment tests |
| `tests/unit/test_project_foundation.py` | 2 Phase 0 smoke tests |
| `README.md` | Standalone developer and AI agent entry point & project guide |
| `.env.example` | Env var template incl. `GEMINI_ENRICHMENT_API_KEY`, `TAVILY_VISA_ENRICHMENT_API_KEY`, `REST_COUNTRIES_API_KEY`, `EXCHANGERATE_API_KEY`, `OPENWEATHERMAP_API_KEY` |

## Tests completed and their status

- `uv run pytest tests/ -v`: **212 passed**
- `uv run ruff check .`: **all checks passed**
- `uv run ruff format --check .`: **40 files already formatted**
- Airport ingestion script executed successfully: 3244 airports written
- Visa rules ingestion script executed successfully: 199 rules written
- Visa rules enrichment script executed successfully: 199 enriched rules written
- Country profiles ingestion script executed successfully: 250 country profiles written

## Visa rules schema (updated)

### Base record — `data/static/visa_rules.json` (from `fetch_visa_rules.py`)
Overwritten freely on each fetch run. Never modified by the enrichment script.
```json
{
  "destination": "Cape Verde",
  "country_code": "CV",
  "requirement": "VISA_ON_ARRIVAL",
  "last_updated": "2026-09-24"
}
```
Optional: `"allowed_stay_days": 30` when source value is numeric.

### Enriched record — `data/static/visa_rules_enriched.json` (from `enrich_visa_rules.py`)
Built up incrementally (one destination at a time). Never overwritten by the fetch script.
```json
{
  "destination": "Uzbekistan",
  "country_code": "UZ",
  "last_updated": "2026-09-24",
  "options": [
    {
      "visa_type": "Visa-Free Entry (30 Days)",
      "duration_days": 30,
      "cost_inr": 0.0,
      "entry_type": "CONDITIONAL_FREE",
      "entry_port_restriction": null,
      "requires_loi": false,
      "notes": "Visa-free entry regime for Indian citizens up to 30 days.",
      "source": ["https://example.com/uzbekistan-visa-free"]
    },
    {
      "visa_type": "Tourist e-Visa (30 Days Single Entry)",
      "duration_days": 30,
      "cost_inr": 1680.0,
      "entry_type": "E_VISA",
      "entry_port_restriction": null,
      "requires_loi": false,
      "notes": "Legacy single-entry tourist e-visa option.",
      "source": ["https://example.com/uzbekistan-evisa"]
    }
  ],
  "selected_option": { "...best option per selection logic..." }
}
```

### `selected_option` selection logic
`select_best_option()` picks the optimal pathway by: lowest `cost_inr` → longest `duration_days` → `requires_loi=False` preferred → first listed wins ties.

## Visa enrichment usage

```bash
# Set environment variable first
export GEMINI_ENRICHMENT_API_KEY=your_key_here

# Enrich and save to visa_rules_enriched.json
uv run python scripts/enrich_visa_rules.py --destination "Cape Verde"

# Dry-run: print without saving
uv run python scripts/enrich_visa_rules.py --destination "Japan" --dry-run
```

## Known issues or limitations

- `uv` was not previously on PATH; installed via winget (`astral-sh.uv`). New shells may need PATH refresh.
- Local interpreter is 3.14.7; project constraint remains Python 3.11+.
- `data/static/visa_rules.json` was NOT regenerated from the new source in this task
  (the user will run `uv run python scripts/fetch_visa_rules.py` to regenerate it).
  The existing file has the old schema without `country_code` / `last_updated`.
- **FRU (Bishkek) IATA change**: The upstream ourairports-data has updated Manas International
  Airport's IATA from `FRU` to `BSZ`. Phase 2's static data lookup should use `BSZ`.
- `enrich_visa_rules.py` requires `GEMINI_ENRICHMENT_API_KEY` to be set before running.
- The new `imorte/passport-index-data` repo lists data updated as of **17 February 2026**.
  The `last_updated` field in base records reflects the ingestion run date (today's date),
  not the upstream dataset's update date. Phase 2 consumers should treat this as a
  "last fetched" timestamp.
- The two parallel CSVs (tidy + iso2) are joined by **row position** — this is documented
  as a property of the source dataset but should be verified if the upstream source changes.

## Decisions that should not be changed without discussion

- Use `uv` for Python deps; never pip.
- Use `pnpm` for frontend later.
- Import root is `src.*` matching `architecture.md`.
- Fixture-first / no live API calls in unit tests.
- `ETA` is normalised to `E_VISA` (Electronic Travel Authority is functionally equivalent).
- Ingestion scripts use stdlib only — no new runtime dependencies in fetch scripts.
- Airport filter: type ∈ {large_airport, medium_airport} AND non-empty IATA AND scheduled_service == "yes".
- Existing output files are never deleted or replaced with empty content on network failure.
- `enrich_visa_rules.py` upserts only the queried destination — never loops all countries at once.
- `enrich_visa_rules.py` writes to `visa_rules_enriched.json` only; `visa_rules.json` is
  owned exclusively by `fetch_visa_rules.py`. The two files are fully decoupled.
- The enrichment script uses Tavily for web research and Google Gemini for
  native structured JSON synthesis (with automatic model fallback) to avoid
  Gemini free-tier search grounding 429 quota limits.
- `selected_option` is always determined by `select_best_option()` in the script, not the LLM,
  to ensure objective, consistent selection across all destinations.
- `VisaOption` and `EnrichedVisaRecord` live in `src/models/visa.py` and are re-exported
  from `src.models`. The script inserts the project root into `sys.path` at runtime so it
  can import `src.*` without the package being pip-installed.

## Next recommended step

**Phase 3 — External Tool Layer** (implement one tool at a time upon confirmation):
- [x] **Tool 1: Calculator Tool** (`src/tools/calculator.py`) — Deterministic budget arithmetic (complete)
- [x] **Tool 2: Forex Tool** (`src/tools/forex.py`) — Currency conversion to INR + offline baseline rates + fixture (complete)
- [x] **Tool 3: Weather Tool** (`src/tools/weather.py`) — Multi-tier forecast (Open-Meteo, wttr.in, OpenWeatherMap, Climate Baseline) + fixture (complete)
- [ ] **Tool 4: Web Search Tool** (`src/tools/web_search.py`) — Tavily Search wrapper + `data/fixtures/mock_tavily_search.json`
- [ ] **Tool 5: Transport/Flight Tool** (`src/tools/transport.py`) — Route search adapter + `data/fixtures/mock_flights.json`
- [ ] **Tool 6: Hotel Tool** (`src/tools/hotels.py`) — Real hotel discovery adapter + `data/fixtures/mock_hotels.json`
- [ ] **Tool 7: Places & Dining Tool** (`src/tools/places.py`) — Attractions & restaurants adapter + `data/fixtures/mock_places.json`
- [ ] **Tool 8: Fallback Estimator** (`src/tools/fallback_estimator.py`) — Gemini structured fallback cost estimation
