# Safarnama — Project Memory

> Snapshot for resuming implementation. Do not duplicate `prd.md`, `architecture.md`, `rules.md`, or `phases.md`.

## Current Status

**Phase 7 — Visa Functionality complete (including Option 1 Semantic LLM Policy Reconciliation).** `src/nodes/visa_node.py` implemented with semantic LLM policy reconciliation (`LiveVisaPolicyAnalysis`, zero regex, date expiration checks, foreign nationality rejection), Schengen single-visa optimization, party scaling, and domestic bypass, backed by 20 unit tests (392 total passing). All lint/format checks pass.

Do not start subsequent phases until explicitly requested.

## Current implementation phase

Phase 7 — Visa Functionality (Completed)

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

### Phase 6 (Intake Functionality — 100% complete)
- **`src/models/trip.py`** (extended): Added `ResolvedLocation` (geocoded gateway, country, Schengen flag, timezone offset) and `InitialPlanningState` (immutable planning state container with route sequence, normalized budgets, and duration).
- **`src/models/__init__.py`** (updated): Re-exported `ResolvedLocation` and `InitialPlanningState`.
- **`src/nodes/intake_node.py`**: Complete intake processing engine with:
  - Custom exceptions (`IntakeError`, `IntakeValidationError`, `IntakeScopeConflictError`).
  - Alias mappings for Indian tourist hubs/states (`DOMESTIC_GATEWAY_ALIASES`) and international regions (`INTERNATIONAL_GATEWAY_ALIASES`).
  - Hierarchical resolution pipeline (`resolve_location`): Aliases -> IATA / airport codes -> Country profiles (for destinations) -> City / municipality search -> Fallback error.
  - Strict Indian origin enforcement (must resolve to an airport or city in India).
  - Scope auto-detection and conflict enforcement (`TravelScope.DOMESTIC` vs `INTERNATIONAL`).
  - Date normalization (calculates duration for EXACT, FLEXIBLE, FIND_BEST modes) and budget split calculations (per-person multiplier).
  - LangGraph node function `intake_node(state)` returning state update dictionary.
- **`src/nodes/__init__.py`**: Re-exports `intake_node`, `process_intake`, `resolve_location`, and exceptions.
- **`tests/unit/test_intake_node.py`**: 21 unit tests covering domestic single/multi-destination, international single/multi-country, Schengen advisory, flexible dates, per-person budgets, invalid origins, foreign origins, and scope conflict exceptions.

### Phase 7 (Visa Functionality — 100% complete)
- **`src/prompts/visa_prompts.py`** (extended): Added `build_live_visa_verification_prompt()` isolating prompt construction for structured semantic reconciliation.
- **`src/models/visa.py`** (extended): Added `LiveVisaPolicyAnalysis` Pydantic model for validated LLM extraction.
- **`src/nodes/visa_node.py`**: Complete international visa evaluation and synthesis node:
  - Custom exceptions (`VisaError`, `VisaProcessingError`).
  - Strict Indian passport holder context.
  - Automatic domestic trip bypass (`is_domestic_bypass=True`, ₹0 visa cost, empty countries list).
  - Multi-tier resolution: static enriched records (`data/static/visa_rules_enriched.json`), static baseline rules, and live search verification via `search_web`.
  - Resilience & Safety: Fallback LLM and system never fabricate visa rules (Rule 35); graceful fallback to verified static baseline on live network failures.
  - **Option 1 Semantic LLM Policy Reconciliation**: Eliminated regex and keyword searching (`"visa-free" in snippets`). Reconciles search snippets via LLM structured analysis (`LiveVisaPolicyAnalysis`):
    - Rejects foreign nationality rules (e.g. EU/US visa-free policies).
    - Distinguishes confirmed decrees from speculative/pending proposals.
    - Compares planned travel date against temporary waiver expiration dates (`waiver_end_date`).
    - Multi-provider cascade: Google Gemini -> Groq -> NVIDIA NIM.
  - Schengen single uniform visa optimization: Multiple Schengen destinations are covered by a single visa fee per traveler rather than duplicating fees across member states.
  - Traveler party scaling: Accurately multiplies per-person visa fees across traveler headcount (`party.total_travelers`).
  - Output contract: Produces immutable frozen `VisaCountryVerdict` and `VisaVerdict` models conforming to domain schemas.
  - LangGraph node function `visa_node(state)` returning `{"visa_verdict": verdict}`.
- **`src/nodes/__init__.py`**: Re-exports `visa_node`, `process_visa`, `evaluate_country_visa`, `VisaError`, and `VisaProcessingError`.
- **`tests/unit/test_visa_node.py`**: 20 unit tests covering domestic bypass, single international countries, static baseline retrieval, live policy overrides, semantic waiver confirmation, foreign nationality rejection, speculative proposal rejection, expired waiver rejection, network error fallback, LLM unavailable fallback, multi-country summing, Schengen optimization, party scaling, advance application flag, and safety on unknown destinations.

## Important files/modules

| Path | Role |
|---|---|
| `pyproject.toml` | Project metadata, dependencies (`fastapi`, `httpx`), pytest & Ruff config |
| `src/api/models.py` | API Request/Response models |
| `src/api/routes.py` | FastAPI router endpoints |
| `src/api/app.py` | FastAPI application factory, CORS & exception handlers |
| `src/api/__init__.py` | Package re-exports |
| `src/models/trip.py` | Trip context, party, dates, budget, food, preferences, ResolvedLocation, InitialPlanningState |
| `src/models/itinerary.py` | POIs, activity slots, day plans, experience plan |
| `src/models/logistics.py` | Transport legs, hotel stays, logistics plan |
| `src/models/visa.py` | Visa ingestion models + VisaVerdict planning domain |
| `src/models/budget.py` | Cost breakdown, contingency, variance, optimization, budget breakdown |
| `src/nodes/intake_node.py` | Phase 6 intake node, geographic resolution, scope reconciliation, planning state generator |
| `src/nodes/visa_node.py` | Phase 7 visa planning node, live verification, Schengen optimization, domestic bypass |
| `src/nodes/__init__.py` | Node exports |
| `src/prompts/estimator_prompts.py` | Isolated prompt templates for LLM estimator |
| `src/prompts/visa_prompts.py` | Isolated prompt templates for visa enrichment and verification |
| `src/tools/static_data.py` | In-memory indexed static data store |
| `src/tools/calculator.py` | Deterministic budget calculator |
| `src/tools/forex.py` | Multi-tier currency converter |
| `src/tools/weather.py` | Multi-tier weather forecast tool |
| `src/tools/web_search.py` | Multi-tier web search engine |
| `src/tools/transport.py` | Multi-tier transport route search tool |
| `src/tools/hotels.py` | Multi-tier hotel search tool |
| `src/tools/places.py` | Multi-tier points of interest and dining tool |
| `src/tools/fallback_estimator.py` | Multi-provider LLM fallback estimator tool |
| `tests/unit/test_intake_node.py` | 21 Phase 6 intake node unit tests |
| `tests/unit/test_visa_node.py` | 20 Phase 7 visa node unit tests |
| `tests/unit/test_domain_models.py` | 89 Phase 5 domain model unit tests |
| `tests/unit/test_api.py` | 10 API unit tests |
| `README.md` | Developer and AI agent entry point |

## Tests completed and their status

- `uv run pytest`: **392 passed** (372 pre-Phase 7 + 20 visa node tests)
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
- In `resolve_location()`, destination country profile lookup (`find_country()`) takes precedence over municipality substring search to prevent country names (e.g. France) from falsely matching foreign towns with substrings (e.g. Fort Frances, CA).
- Departure origin must strictly resolve to a passenger airport or municipality located in India (`iso_country == "IN"`).
- In `visa_node.py`, domestic trips automatically bypass visa processing returning `is_domestic_bypass=True`, ₹0 cost, and empty countries list.
- Multi-destination itineraries within the Schengen Area trigger `schengen_single_visa_applicable=True` and charge the uniform Schengen visa fee once per traveler (instead of duplicating fees per country).
- Destination country deduplication ensures multiple city stops in the same nation (e.g. Rome + Milan) evaluate the country visa rule once.
- Zero regex in live policy reconciliation (Option 1): Live policy updates are verified via LLM structured analysis (`LiveVisaPolicyAnalysis`) with strict validation against foreign nationalities, speculative proposals, and expired waiver end dates vs planned travel dates.
- Live search or LLM failures fall back gracefully to the verified static baseline without raising unhandled network errors.

## Phase 7 Completion Status

Phase 7 — Visa Functionality (including Option 1) is **100% complete, fully tested, and verified**.

## Next recommended phase

**Phase 8 — Logistics Functionality**:
Implement `src/nodes/logistics_node.py` to plan transportation (flight/rail legs) and accommodations (hotel stays) for the itinerary using `src/tools/transport.py` and `src/tools/hotels.py`, generating validated `LogisticsPlan` models.
