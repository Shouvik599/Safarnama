# Safarnama — Project Memory

> Snapshot for resuming implementation. Do not duplicate `prd.md`, `architecture.md`, `rules.md`, or `phases.md`.

## Current Status

**Phase 5 — Domain Models complete.** Five domain model files implemented in `src/models/` with 89 new unit tests (351 total passing). All lint/format checks pass.

Do not start subsequent phases until explicitly requested.

## Current implementation phase

Phase 5 — Domain Models (Completed)

## Completed functionality

### Phase 0 (foundation)
- `uv`-managed Python project (`safarnama` 0.1.0, `requires-python >=3.11`)
- Hatchling src layout: `src/` is the importable package (`import src`)
- Empty package modules: `src.api`, `src.graph`, `src.models`, `src.nodes`, `src.prompts`, `src.tools`
- pytest + Ruff as **dev** dependencies only

### Phase 1 (static data ingestion — complete & verified)
- `scripts/fetch_airports.py` — downloads from `davidmegginson/ourairports-data` (3,244 airports)
- `scripts/fetch_visa_rules.py` — fetches dual CSVs (`passport-index-tidy.csv` + `passport-index-tidy-iso2.csv`), joins by row position, writes normalized baseline records to `data/static/visa_rules.json` (199 destinations)
- `scripts/enrich_visa_rules.py` — reads baseline from `data/static/visa_rules.json`, performs live web research via Tavily, synthesizes multi-option records via Google Gemini structured output with fallback across models on 429/503 (199/199 destinations enriched)
- `scripts/fetch_country_profiles.py` — queries REST Countries v5 across paginated batches (`limit=100`) using `REST_COUNTRIES_API_KEY`, parses 250 sovereign states into `CountryProfile` models in `data/static/countries.json`

### Phase 2 (static data access layer — complete)
- `src/models/airport.py`, `src/models/country.py`, `src/models/visa.py` — Canonical Pydantic domain models
- `src/tools/static_data.py` — High-performance runtime access layer:
  - Custom typed exception hierarchy (`StaticDataError`, `RecordNotFoundError`, `AirportNotFoundError`, `CountryNotFoundError`, `VisaRuleNotFoundError`, `InvalidLookupError`)
  - In-memory `StaticDataStore` singleton caching all 4 datasets on initial access without repeated file I/O
  - Fast O(1) query functions (`get_airport`, `get_country`, `is_schengen`, `get_ist_time_difference_hours`, `get_visa_rule`)

### Phase 3 (External Tool Layer — 100% complete)
- **Tool 1: Calculator Tool (`src/tools/calculator.py`)**: Exact decimal arithmetic, expense categorization, buffer calculations, and budget variance evaluation.
- **Tool 2: Forex Tool (`src/tools/forex.py`)**: Multi-tier currency converter (cache -> fixture -> open access -> FawazAhmed CDN -> Frankfurter -> authenticated -> ~40 offline rates).
- **Tool 3: Weather Tool (`src/tools/weather.py`)**: Multi-tier weather forecast (Open-Meteo, wttr.in, OpenWeatherMap, Climate Baseline).
- **Tool 4: Web Search Tool (`src/tools/web_search.py`)**: Multi-tier web search (Tavily, DuckDuckGo, Firecrawl, offline fixture).
- **Tool 5: Transport Tool (`src/tools/transport.py`)**: Multi-tier route search (Sky Scraper, Flights Sky, IRCTC, transport.rest, web search fallback, distance physics engine).
- **Tool 6: Hotel Tool (`src/tools/hotels.py`)**: Multi-tier hotel search (SerpApi Google Hotels, Booking.com on RapidAPI, OpenStreetMap Nominatim, web search fallback, location heuristic).
- **Tool 7: Places & Dining Tool (`src/tools/places.py`)**: Points of interest & dining adapter (SerpApi Google Maps, Nominatim OSM, web search fallback, offline category baseline).
- **Tool 8: Fallback Estimator (`src/tools/fallback_estimator.py`)**: Multi-provider LLM fallback cost estimation (Gemini, Groq, NVIDIA NIM, offline rule baseline) with isolated prompts in `src/prompts/estimator_prompts.py`.

### Phase 4 (API Layer — 100% complete)
- `src/api/models.py`: API request/response Pydantic contracts (`HealthResponse`, `ToolStatusItem`, `ToolStatusResponse`, `EstimateRequest`, `EstimateResponse`, `PlanPreviewRequest`, `PlanPreviewResponse`, `APIErrorResponse`).
- `src/api/routes.py`: FastAPI `APIRouter` with endpoints:
  - `GET /health` and `GET /api/v1/health` — Health check
  - `GET /api/v1/tools/status` — Aggregate tool status report
  - `POST /api/v1/estimate` — Quick cost estimation
  - `POST /api/v1/plan/preview` — Lightweight trip preview validating origin, destination, scope, visa, and budget breakdown
  - `GET /api/v1/stream/events` — Real-time event streaming via Server-Sent Events (SSE)
- `src/api/app.py`: FastAPI app factory (`create_app()`) with CORS middleware and global exception handlers.
- `src/api/__init__.py`: Public package exports.
- `tests/unit/test_api.py`: 10 comprehensive unit tests covering endpoints, validation error responses (422), domain exception handling (400), CORS headers, and SSE streaming.

### Phase 5 (Domain Models — 100% complete)
- **`src/models/trip.py`**: Trip context models including enums (`TravelScope`, `DateMode`, `BudgetMode`, `TravelStyle`, `Pace`, `FoodImportance`) and composites (`TripParty`, `TripDates` with cross-field mode validation, `TripBudget` with per-person multiplier, `FoodPreferences`, `PreviousTravelEntry`, `TripContext`).
- **`src/models/itinerary.py`**: Itinerary models including enums (`Daypart`, `ActivityCategory`) and composites (`PointOfInterest`, `ActivitySlot` with weather-substitution metadata, `DayMeal`, `DayPlan` with `total_day_cost_inr` property, `ExperiencePlan`).
- **`src/models/logistics.py`**: Logistics models (`TransportLeg`, `HotelStay`, `LogisticsPlan`). Domain-layer contracts separate from tool-layer transport/hotel result models.
- **`src/models/visa.py`** (extended): Added planning domain models (`VisaRequirementStatus` enum with 8 values including `DOMESTIC_BYPASS`, `VisaCountryVerdict`, `VisaVerdict` with Schengen optimization flag) to the existing data-ingestion models.
- **`src/models/budget.py`**: Budget models including enums (`BudgetStatus`, `OptimizationAction`) and composites (`CostBreakdown` with `subtotal_inr` property, `ContingencyConfig` with trip-complexity factors, `BudgetVariance` with cross-field consistency validator, `OptimizationResult`, `BudgetBreakdown`). Enforces architecture rule that LLMs may not perform arithmetic.
- **`src/models/__init__.py`** (updated): Exports all Phase 1–5 models with clear section comments.
- **`tests/unit/test_domain_models.py`**: 89 unit tests covering all five model files — valid construction, defaults, field validation, cross-field validators, enum values, properties, and invalid state rejection.

## Important files/modules

| Path | Role |
|---|---|
| `pyproject.toml` | Project metadata, dependencies (`fastapi`, `httpx`), pytest & Ruff config |
| `src/api/models.py` | API Request/Response models |
| `src/api/routes.py` | FastAPI router endpoints |
| `src/api/app.py` | FastAPI application factory, CORS & exception handlers |
| `src/api/__init__.py` | Package re-exports |
| `src/models/trip.py` | Trip context, party, dates, budget, food, preferences |
| `src/models/itinerary.py` | POIs, activity slots, day plans, experience plan |
| `src/models/logistics.py` | Transport legs, hotel stays, logistics plan |
| `src/models/visa.py` | Visa ingestion models + VisaVerdict planning domain |
| `src/models/budget.py` | Cost breakdown, contingency, variance, optimization, budget breakdown |
| `src/prompts/estimator_prompts.py` | Isolated prompt templates for LLM estimator |
| `src/prompts/visa_prompts.py` | Isolated prompt templates for visa enrichment |
| `src/tools/static_data.py` | In-memory indexed static data store |
| `src/tools/calculator.py` | Deterministic budget calculator |
| `src/tools/forex.py` | Multi-tier currency converter |
| `src/tools/weather.py` | Multi-tier weather forecast tool |
| `src/tools/web_search.py` | Multi-tier web search engine |
| `src/tools/transport.py` | Multi-tier transport route search tool |
| `src/tools/hotels.py` | Multi-tier hotel search tool |
| `src/tools/places.py` | Multi-tier points of interest and dining tool |
| `src/tools/fallback_estimator.py` | Multi-provider LLM fallback estimator tool |
| `tests/unit/test_domain_models.py` | 89 Phase 5 domain model unit tests |
| `tests/unit/test_api.py` | 10 API unit tests |
| `README.md` | Developer and AI agent entry point |

## Tests completed and their status

- `uv run pytest`: **351 passed** (262 pre-Phase 5 + 89 new domain model tests)
- `uv run ruff check src/ tests/ scripts/`: **All checks passed!**
- `uv run ruff format --check src/ tests/ scripts/`: **All files formatted**

## Decisions that should not be changed without discussion

- Use `uv` for Python deps; never pip.
- Use `pnpm` for frontend later.
- Import root is `src.*` matching `architecture.md`.
- Fixture-first / no live API calls in unit tests.
- Prompt Isolation Rule (Rule 9.3 in `rules.md`): All LLM prompt strings are strictly isolated in `src/prompts/`.
- All financial arithmetic goes through `src/tools/calculator.py` using `Decimal`.
- API routes validate all requests with Pydantic and return structured JSON errors (`APIErrorResponse`) on failures.
- Domain models in `src/models/` are frozen (`model_config = ConfigDict(frozen=True)`) — they are value objects.
- `VisaVerdict` and related planning domain models live in `src/models/visa.py` alongside the data-ingestion models rather than a separate file, to keep all visa-related types co-located.
- `BudgetVariance` cross-field validator rejects inconsistent `variance_inr` values (must equal `projected_total - user_budget` within ₹1).
- `TripDates` cross-field validator enforces required fields per `DateMode` (EXACT requires start+end; FLEXIBLE requires start+duration; FIND_BEST requires window+duration).
- Environment Variable & Configuration Synchronization (Rule 46 in `rules.md`): Whenever an environment variable is added, modified, or removed in `.env`, `.env.example`, `README.md` (Section 11), and project documentation must be updated in lockstep without committing real secrets.

## Phase 5 Completion Status

Phase 5 — Domain Models is **100% complete, fully tested, and verified**.

## Next recommended phase

**Phase 6 — Intake Functionality**:
Implement `src/nodes/intake_node.py` to validate/sanitize user input, resolve origin/destination, load coordinates, and create initial planning state from a `TripContext`. Test with domestic, international, multi-destination, and invalid-input scenarios.
