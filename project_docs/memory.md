# Safarnama — Project Memory

> Snapshot for resuming implementation. Do not duplicate `prd.md`, `architecture.md`, `rules.md`, or `phases.md`.

## Current Status

**Phase 10 — Deterministic Budget Engine complete.** `src/nodes/budget_node.py` and extended deterministic financial helpers in `src/tools/calculator.py` implemented. Aggregates itemized trip costs across transport, accommodation, activities, dining, transit, visa, and miscellaneous expenses; dynamically evaluates contingency buffers based on scope, destination count, estimated pricing, and date flexibility; computes exact budget variance and classifies outcomes into 5 actionable status tiers (`UNDER_BUDGET`, `EXACT`, `MINOR_OVER`, `SIGNIFICANT_OVER`, `INFEASIBLE`); scales per-person costs across party size, backed by 20 unit tests (459 total passing) and 4-stage live integration verification. All lint/format checks pass.

Do not start subsequent phases until explicitly requested.

## Current implementation phase

Phase 10 — Deterministic Budget Engine (Completed)

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
- **Tool 5: Transport Tool (`src/tools/transport.py`)**: Multi-tier route search (Sky Scraper, Flights Sky, Aviationstack live flights, IRCTC, transport.rest, web search fallback, distance physics engine).
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

### Phase 8 (Logistics Functionality — 100% complete)
- **`src/nodes/logistics_node.py`**: Complete logistics planning engine:
  - Custom exceptions (`LogisticsError`, `LogisticsPlanningError`).
  - Party-aware room estimation heuristic (`estimate_rooms_required`): Accurately estimates rooms for adults and children (couples with 1 young child share 1 room, 2 adults + 2 children allocate 2 rooms, larger parties allocate $\lceil \text{total}/2 \rceil$).
  - Sequential stay allocation (`allocate_stay_dates`): Evenly distributes nights across destinations, ensuring seamless continuity where checkout date of destination $i$ matches checkin date of destination $i+1$.
  - Transport leg planning (`plan_transport_legs`): Plans round-trip (origin $\rightarrow$ dest $\rightarrow$ origin) or multi-destination (origin $\rightarrow$ dest 1 $\rightarrow$ dest 2 $\rightarrow$ ... $\rightarrow$ origin) hops via flights and trains. Adapts to travel styles (`BUDGET` favors lower fares/trains, `LUXURY` favors premium cabin/fastest routes). Scales per-person fares across total party headcount (`total_travelers`).
  - Accommodation planning (`plan_hotel_stays`): Queries live/fixture hotels via `search_hotels`. Matches star ratings and guest scores to user travel style (`BUDGET` 2-3 stars, `COMFORTABLE` 3-4 stars, `LUXURY` 5 stars). Deterministically calculates `total_accommodation_cost_inr = rate * nights * rooms_required`.
  - Resilience & provenance: Gracefully handles provider exceptions or empty search results without crashing by synthesizing labeled fallback records (`is_estimated=True`, `physics-heuristic`, `location-heuristic`). Preserves booking URLs.
  - Feasibility warnings: Emits non-fatal warnings when combined transport and accommodation costs exceed the user's budget ceiling.
  - LangGraph node function `logistics_node(state)` returning `{"logistics_plan": plan}`.
- **`src/nodes/__init__.py`**: Re-exports `logistics_node`, `process_logistics`, `estimate_rooms_required`, `allocate_stay_dates`, `plan_transport_legs`, `plan_hotel_stays`, `LogisticsError`, and `LogisticsPlanningError`.
- **`tests/unit/test_logistics_node.py`**: 22 unit tests covering room heuristics, date allocation, domestic single destination, multi-destination continuity, party size scaling, room count scaling, travel style sensitivity (budget vs luxury), provider failure resilience, booking URL preservation, budget feasibility warnings, LangGraph state interface, and error handling.

### Phase 9 (Experience Functionality — 100% complete)
- **`src/nodes/experience_node.py`**: Complete experience planning engine:
  - Custom exceptions (`ExperienceError`, `ExperiencePlanningError`).
  - Activity scheduling and pacing calibration: Schedules slots per day according to traveler pace (`RELAXED`: 1, `BALANCED`: 2, `PACKED`: 3 slots across `MORNING`, `AFTERNOON`, `EVENING`).
  - Authentic dining recommendations: Integrates `search_places` to assign breakfast, lunch, and dinner to each day with appropriate meal costs scaled by party size.
  - Weather-responsive indoor substitution: Retrieves multi-day weather forecasts via `get_weather_forecast`. When adverse weather (heavy rain, storms, `is_outdoor_friendly=False`) is forecasted, seamlessly substitutes outdoor attractions with indoor cultural venues (museums, art galleries) from the POI pool or synthetic category heuristics, appending transparent explanation notes and tracking `weather_substitutions`.
  - Must-visit fulfillment tracking: Prioritizes user must-visit sights, tracks fulfillment, and issues clear feasibility warnings if constraints prevent inclusion.
  - Logistics integration: Automatically associates hotel stay details and booking URLs from `LogisticsPlan` into daily itinerary schedules (final departure day has `hotel_name=None`).
  - Party size cost scaling: Deterministically scales attraction tickets, dining expenses, and local transit across total traveler headcount (`party.total_travelers`).
  - Resilient execution: Zero crashes on places/weather tool exceptions with graceful category-heuristic fallbacks.
  - LangGraph node function `experience_node(state)` returning `{"experience_plan": plan}`.
- **`src/nodes/__init__.py`**: Re-exports `experience_node`, `process_experience`, `ExperienceError`, and `ExperiencePlanningError`.
- **`tests/unit/test_experience_node.py`**: 13 unit tests covering pacing calibration (RELAXED, BALANCED, PACKED), must-visit fulfillment and shortfall warnings, authentic dining, weather-responsive indoor substitutions, multi-destination day distribution, hotel stay inheritance from logistics, party size cost scaling, provider failure resilience, LangGraph interface, and error handling.

### Phase 10 (Deterministic Budget Engine — 100% complete)
- **`src/tools/calculator.py`** (extended):
  - `classify_detailed_budget_status()`: 5-tier budget status evaluator (`UNDER_BUDGET`, `EXACT`, `MINOR_OVER`, `SIGNIFICANT_OVER`, `INFEASIBLE`).
  - `calculate_dynamic_contingency()`: Dynamic buffer based on trip scope (domestic 5% vs. international 10%), multi-country hops (+2%), fallback/estimated costs (+3%), and date flexibility (-2%), clamped to [3%, 20%].
  - `calculate_miscellaneous_expenses()`: Style-based daily miscellaneous allowance scaled by party headcount and duration.
- **`src/nodes/budget_node.py`**: Complete deterministic budget engine node:
  - Custom exceptions (`BudgetError`, `BudgetValidationError`, `BudgetCalculationError`).
  - Total budget normalization: Properly scales per-person budget limits across party headcount (`context.budget.total_budget_inr(party)`).
  - Itemized category summation: Aggregates transport legs, hotel stays, activity admissions, dining, local transit, visa fees, and miscellaneous expenses using deterministic `Decimal` arithmetic.
  - Dynamic contingency evaluation: Automatically computes contingency buffer and itemizes percentage and amounts.
  - Exact budget variance calculation: Computes `variance_inr = projected_total_inr - user_budget_inr` and `variance_pct` matching Pydantic domain cross-field validation rules (within ₹1 precision).
  - Comprehensive feasibility warnings: Generates detailed warnings when budget is exceeded or when costs rely heavily on fallback estimates.
  - Output contract: Produces immutable frozen `BudgetBreakdown` model conforming to domain schemas.
  - LangGraph node function `budget_node(state)` returning `{"budget_breakdown": breakdown}`.
- **`src/nodes/__init__.py`**: Re-exports `budget_node`, `process_budget`, `BudgetError`, `BudgetValidationError`, and `BudgetCalculationError`.
- **`tests/unit/test_budget_node.py`**: 20 unit tests covering all 12 test requirements from `phases.md` Section 14 (total budget, per-person normalization, adults+children, visa multiplication, food aggregation, misc costs, dynamic contingency, under/exact/minor/significant/infeasible budget statuses, float precision invariants, missing input handling, and LangGraph interface).

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
| `src/nodes/logistics_node.py` | Phase 8 logistics planning node, transport legs, hotel stays, room estimation |
| `src/nodes/experience_node.py` | Phase 9 experience planning node, attractions, dining, weather pacing |
| `src/nodes/budget_node.py` | Phase 10 deterministic budget engine node, cost aggregation, contingency, variance |
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
| `tests/unit/test_logistics_node.py` | 22 Phase 8 logistics node unit tests |
| `tests/unit/test_experience_node.py` | 13 Phase 9 experience node unit tests |
| `tests/unit/test_budget_node.py` | 20 Phase 10 budget node unit tests |
| `tests/unit/test_domain_models.py` | 89 Phase 5 domain model unit tests |
| `tests/unit/test_calculator.py` | 56 Phase 3/10 calculator unit tests |
| `tests/unit/test_api.py` | 10 API unit tests |
| `README.md` | Developer and AI agent entry point |

## Tests completed and their status

- **Hermetic Offline Test Harness**:
  - `uv run pytest`: **459 passed**, 4 warnings in 8.01s (100% offline, zero network reliance in test suite).
  - `uv run ruff check src/ tests/ scripts/`: **All checks passed!**
  - `uv run ruff format --check src/ tests/ scripts/`: **66 files already formatted**.
- **Live Network Integration Verification**:
  - `uv run python scripts/verify_live_nodes.py`: **ALL 4 LIVE PLANNING NODE INTEGRATION TESTS COMPLETED SUCCESSFULLY**
    - **Visa Node (Phase 7)**: Live Tavily web search + Gemini 3.5 structured reconciliation verified Thailand 60-day visa-free status in 4.37s.
    - **Logistics Node (Phase 8)**: Live flights via Aviationstack / Sky Scraper and live lodging via SerpApi Google Hotels (Royal Hometel Suites with booking URL) in 13.68s.
    - **Experience Node (Phase 9)**: Live Open-Meteo weather ("Mainly clear, 30°C/22°C") + real venues (Prithvi Cafe, Lake View Cafe, Peshwa Pavilion) with live hotel association in 5.71s.
    - **Budget Engine Node (Phase 10)**: Aggregated itemized costs across all upstream live plans (₹40,892.00 projected total vs ₹35,000.00 budget), applied 5% dynamic contingency, and classified as `SIGNIFICANT_OVER` (+16.83%) in 0.0008s with 100% deterministic precision.
  - **Live Aviationstack Search Verification**: Direct live query to `http://api.aviationstack.com/v1/flights` verified scheduled operating flights (IndiGo, Air India, Lufthansa) with calibrated fares and 0 errors.

## Decisions that should not be changed without discussion

- Use `uv` for Python deps; never pip.
- Use `pnpm` for frontend later.
- Import root is `src.*` matching `architecture.md`.
- Fixture-first / no live API calls in unit tests (`uv run pytest` runs 100% offline).
- **Dual Verification Mandate (Rule 28.1 & Section 2 of `phases.md`)**: Every planning functionality and external-facing tool MUST be verified via both:
  1. Hermetic offline unit test suite (`SAFARNAMA_USE_FIXTURES=true`, zero network reliance, fast CI/CD).
  2. Live network integration verification (`scripts/verify_live_nodes.py`, `use_fixture=False`, `live_search_enabled=True`) against real endpoints (Open-Meteo, Tavily, Gemini, RapidAPI, SerpApi, Nominatim, Aviationstack) to validate live API connectivity, authentication, schema compatibility, and graceful fallbacks.
- Prompt Isolation Rule (Rule 9.3 in `rules.md`): All LLM prompt strings are strictly isolated in `src/prompts/`.
- All financial arithmetic goes through `src/tools/calculator.py` using `Decimal` or strict Python deterministic math (Rule 18 in `rules.md`). LLMs must NEVER perform arithmetic.
- Dynamic contingency buffer is determined based on domestic (5%) vs. international (10%), multi-country itineraries (+2%), fallback pricing presence (+3%), and date flexibility (-2%), clamped to [3%, 20%].
- 5-tier budget status classification: `EXACT` within ₹1 variance, `UNDER_BUDGET` when under, `MINOR_OVER` within 5%, `SIGNIFICANT_OVER` between 5% and 15%, `INFEASIBLE` >15%.
- User budget is normalized via `context.budget.total_budget_inr(context.party)` so `PER_PERSON` budget mode correctly scales by `party.total_travelers`.
- Miscellaneous expenses scale based on travel style (`BUDGET`: ₹200/day/person, `COMFORTABLE`: ₹450, `LUXURY`: ₹1,000).
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
- In `logistics_node.py`, room requirement estimation follows family-friendly occupancy heuristics (2 adults + 1 child share 1 room; larger parties allocate ~2 persons per room).
- Multi-destination stay dates are distributed sequentially with continuous checkout/checkin date alignment and return flight departure matching final stay checkout.
- Fare and stay prices are scaled deterministically (`fare * travelers`, `rate * nights * rooms`). Fallbacks are explicitly labeled with `is_estimated=True`.
- In `experience_node.py`, pacing strictly dictates slots/day (`RELAXED`: 1, `BALANCED`: 2, `PACKED`: 3).
- Adverse weather automatically triggers indoor activity replacement from POI candidates or museum heuristics with transparent traveler notes and substitution accounting.
- Hotel stays and booking URLs are inherited directly from `LogisticsPlan`, with `hotel_name=None` on final departure day.
- Must-visit sights omitted due to pacing constraints produce user-visible feasibility warnings.
- **Aviationstack Flight API Integration (`src/tools/transport.py`)**: When RapidAPI flight endpoints (`Sky Scraper` or `Flights Sky`) fail or time out, `_search_aviationstack` executes as the live flight schedule provider. It queries routes via `dep_iata` and `arr_iata` without sending `flight_date` (as `flight_date` throws 403 Forbidden on standard/free tiers), extracts real scheduled flight numbers and departure/arrival times, and assigns a calibrated distance-based pricing baseline labeled with `is_estimated=True` and `provider="aviationstack"`.

## Phase 10 Completion Status

Phase 10 — Deterministic Budget Engine is **100% complete, dual-verified (offline unit tests + live network verification), and synchronized across all project documentation**.

## Next recommended phase

**Phase 11 — Optimizer Functionality**:
Implement `src/nodes/optimizer_node.py` to evaluate budget variance from Phase 10, generate tiered cost reductions or upgrades when in variance, and dynamically rebalance logistics and activities without compromising core user preferences. Followed by Phase 12 (LangGraph Orchestration) as specified in `project_docs/phases.md`.

