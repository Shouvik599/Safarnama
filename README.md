# Safarnama — Autonomous Multi-Agent Travel Planner

> A constraint-aware, multi-agent travel planning system designed for Indian travelers planning domestic and international trips, combining deterministic calculations, verified static datasets, external travel tools, and structured AI reasoning.

---

## 1. Project Status

```text
Status: In Active Development
Current Phase: Phase 18 — Frontend (Batch 3 Complete)
Current Milestone: Phase 3 (8/8 Tools Complete), Phase 4 (FastAPI Layer & SSE Streaming Complete), Phase 5 (Domain Models Complete), Phase 6 (Intake Complete), Phase 7 (Visa Complete), Phase 8 (Logistics Complete), Phase 9 (Experience Complete), Phase 10 (Budget Engine Complete), Phase 11 (Optimizer Complete), Phase 12 (LangGraph Orchestration Complete), Phase 13 (First Complete Vertical Slice Complete), Phase 14 (International Vertical Slice Complete), Transport Layer Enhancements (SerpApi Google Flights, Seasonal Multipliers, Deep Linking Complete), Phase 15 (Flexible Dates Complete), Phase 16 (Budget Conflict & Human Decision Flow, Selective Re-planning & API Complete), Phase 17 (API Streaming — Real-time LangGraph SSE Event Emission & Endpoints Complete), Phase 18 (Frontend Batch 1 & 2: Welcome, Trip Details, Destinations, Preferences, Budget, Review & Confirm with Interactive Controls, Static Destination Auto-Population, Dynamic Route Seeding, URL-Addressable Routes & Device-Local Draft Persistence; Batch 3: Trip Planning Progress `/planner/progress` SSE Lifecycle & Trip Overview Dossier `/trip/overview` Complete)
Test Suite: 587 Python unit tests + 30 Frontend unit/flow tests passing (100% offline, zero network reliance in tests)
Code Quality: 100% compliant with Ruff and Oxlint
```

Safarnama is being built in small, verified, test-driven phases. The project has completed static data ingestion, static data access layer, the external tool layer (all 8 tools), the FastAPI API layer, the core domain models, the intake planning node, the date optimization node, the visa planning node, the logistics planning node, the experience planning node, the deterministic budget engine, the optimizer planning node, the LangGraph StateGraph orchestration workflow, complete domestic and international vertical slices (`POST /api/v1/plan`), flexible date optimization (`DateMode.FLEXIBLE`, `FIND_BEST`), human-in-the-loop budget conflict resolution with selective re-planning (`replan_workflow` and `POST /api/v1/plan/replan`), real-time planning progress streaming via Server-Sent Events (`src/graph/streaming.py` and `POST /api/v1/plan/stream`, `GET /api/v1/plan/stream`, `POST /api/v1/plan/replan/stream`), **Frontend Batch 1** (`frontend/`: Welcome, Trip Details, and Destinations with full interactive controls, static destination auto-population across all 250 countries and 36 Indian states/UTs, and dynamic route seeding), **Frontend Batch 2** (Preferences, Budget, Review & Confirm screens with URL-addressable routes, device-local draft validation, and backend-shaped `PlanRequestDraft` mapper), and **Frontend Batch 3** (Trip Planning Progress `/planner/progress` consuming the live `POST /api/v1/plan/stream` SSE synthesis engine, plus the synthesized Trip Overview Dossier `/trip/overview` with device-local `FinalItinerary` persistence).

| Phase        | Description                                                                                             | Status       |
| --------------| ---------------------------------------------------------------------------------------------------------| --------------|
| **Phase 0**  | Project Foundation & Packaging                                                                          | **Complete** |
| **Phase 1**  | Static Data Ingestion (Airports, Countries, Visa Rules)                                                 | **Complete** |
| **Phase 2**  | Static Data Access Layer & In-Memory Store                                                              | **Complete** |
| **Phase 3**  | External Tool Layer (Calculator, Forex, Weather, Search, Transport, Hotels, Places, Estimator)          | **Complete** |
| **Phase 4**  | API Foundation (FastAPI endpoints, validation & SSE streaming)                                          | **Complete** |
| **Phase 5**  | Domain Models (Trip context, Itinerary, Logistics, Visa verdict, Budget schemas)                        | **Complete** |
| **Phase 6**  | Intake Functionality (Sanitization, Origin/Destination Resolution, Scope Reconciliation, Initial State) | **Complete** |
| **Phase 7**  | Visa Functionality (Static Baseline + Live Verification, Schengen Optimization, Verdict Synthesizer)    | **Complete** |
| **Phase 8**  | Logistics Functionality (Transport Legs & Hotel Stays Planning)                                         | **Complete** |
| **Phase 9**  | Experience Functionality (Attractions, Dining, Weather-Aware Pacing)                                    | **Complete** |
| **Phase 10** | Deterministic Budget Engine (Category summation, buffer, variances)                                     | **Complete** |
| **Phase 11** | Optimizer Functionality (Budget trade-offs, constraint satisfaction)                                    | **Complete** |
| **Phase 12** | LangGraph Orchestration (StateGraph, parallel nodes, state reduction)                                   | **Complete** |
| **Phase 13** | First Complete Vertical Slice (End-to-end domestic itinerary generation)                                | **Complete** |
| **Phase 14** | International Vertical Slice (End-to-end international with visa integration)                           | **Complete** |
| **Phase 15** | Flexible Dates (Candidate date window optimization, multi-factor scoring)                                | **Complete** |
| **Phase 16** | Budget Conflict & Human Decision Flow (Interactive trade-off resolution, re-planning API)               | **Complete** |
| **Phase 17** | API Streaming (Real-time SSE event emission from LangGraph & dual POST/GET endpoints)                   | **Complete** |
| **Phase 18** | Frontend (Batches 1–3: Welcome, Trip Details, Destinations, Preferences, Budget, Review & Confirm, Planning Progress, Trip Overview) | **Batch 3 Complete** |
| **Phase 19** | End-to-End Test Matrix (Full regression and test scenarios)                                             | Planned      |
| **Phase 20** | Production Hardening (Observability, rate limits, deployment)                                           | Planned      |


---

## 2. What is Safarnama?

Planning a multi-day trip requires synthesizing fragmented information: flight logistics, accommodation options, daily activities, weather forecasts, culinary spots, visa regulations, and budget ceilings. 

Generic conversational AI chatbots fail at this task because they:
- Hallucinate flight routes, hotel prices, and non-existent places.
- Fabricate visa rules and entry requirements for Indian passport holders.
- Perform broken floating-point arithmetic and silently alter budget ceilings.
- Silently drop user constraints or must-visit places.

**Safarnama** (सफ़रनामा — *travelogue/journey narrative*) is an **autonomous planning engine**, not a free-form chatbot. It treats user input as hard planning constraints. It enforces an architectural boundary:
- **Deterministic Python code** performs all mathematical additions, budget variances, per-person splits, and currency conversions.
- **Structured Tool Interfaces** retrieve live and verified travel facts.
- **Static Datasets** provide instant baseline knowledge (3,244 commercial airports, 250 country profiles, 199 Indian passport visa regulations).
- **AI / LLMs** are restricted to reasoning over validated candidate data, synthesizing day-by-day narratives, and evaluating user preference trade-offs.

---

## 3. Core Capabilities

### Currently Implemented Capabilities

- **Global Airport Directory**: 3,244 commercial passenger airports worldwide loaded into memory and indexed by IATA code, city, and ISO country code (`src/models/airport.py`, `src/tools/static_data.py`).
- **Country Intelligence & Profiles**: 250 sovereign countries and territories indexed by ISO-2, ISO-3, and English names, including currencies, languages, capitals, Schengen membership, driving sides, and coordinates (`src/models/country.py`).
- **Indian Passport Visa Regulations**:
  - Baseline rules for 199 international destinations categorized into standardized regimes (`VISA_FREE`, `VISA_ON_ARRIVAL`, `E_VISA`, `STICKER_VISA_REQUIRED`).
  - Enriched multi-option tourist pathways for 199 destinations with exact visa fees in INR, stay limits, application requirements, and source references (`src/models/visa.py`).
- **High-Performance In-Memory Query Layer**: Fast, zero-disk-I/O cached lookups with custom typed exceptions and intelligent IST time difference calculations (`src/tools/static_data.py`).
- **Deterministic Budget Calculator**:
  - Exact financial arithmetic via Python `Decimal` with `ROUND_HALF_UP` rounding to 2 decimal places.
  - Expense category summation (transport, hotels, food, activities, visa, misc, contingency buffer).
  - Per-person splits, daily averages, and room requirement calculations.
  - Budget variance analysis categorizing outcomes as `UNDER_BUDGET`, `EXACT`, or `OVER_BUDGET` (`src/tools/calculator.py`).
- **Deterministic Forex Currency Converter**:
  - Multi-tier conversion to INR: In-Memory Cache (24h TTL) $\rightarrow$ Fixture Mode $\rightarrow$ Live Open-Access Tier $\rightarrow$ Live Authenticated Tier $\rightarrow$ Built-in Offline Baseline Table (~40 global currencies).
  - Explicit provenance and reliability tracking with `is_estimated` flags (`src/tools/forex.py`).
- **External Travel Tools Suite (8/8 Complete)**:
  - **Weather Tool (`src/tools/weather.py`)**: Multi-tier forecasts (Open-Meteo, wttr.in, OpenWeatherMap, Climate Baseline) with weather hazard detection.
  - **Web Search Tool (`src/tools/web_search.py`)**: Multi-tier travel search (Tavily, DuckDuckGo, Firecrawl, offline fixture).
  - **Transport Tool (`src/tools/transport.py`)**: Multi-tier route & flight search:
    - **Tier-0 Live Flights (SerpApi Google Flights)**: Live flight schedules, real INR market fares, carrier codes, and direct booking links powered by `SERPAPI_KEY`.
    - **Tier-1/2 Live APIs**: RapidAPI Sky Scraper & Flights Sky, followed by Aviationstack route-based flight schedule queries.
    - **Rail Services**: Indian Railways IRCTC API (domestic) and `transport.rest` (European rail).
    - **Deterministic Seasonal Multiplier**: Calendar-month demand heuristic (peak holiday ×1.35, shoulder ×1.15, off-peak ×1.00) applied to distance-based physics and schedule baseline flight estimates.
    - **Universal Google Flights Deep Linking**: Canonical live Google Flights search URLs (`google.com/travel/flights/search`) generated across all flight candidates and fallbacks for instant, zero-friction verification.
  - **Hotel Tool (`src/tools/hotels.py`)**: Multi-tier lodging search (SerpApi Google Hotels, Booking.com, Nominatim OSM, web search fallback, location heuristic).
  - **Places & Dining Tool (`src/tools/places.py`)**: Points of interest and dining search (SerpApi Google Maps, Nominatim OSM, web search fallback, category baseline).
  - **Fallback Estimator (`src/tools/fallback_estimator.py`)**: Multi-provider LLM fallback cost estimation (Gemini, Groq, NVIDIA NIM, offline rule baseline) with isolated prompts in `src/prompts/estimator_prompts.py`.
- **FastAPI REST API Layer (`src/api/`)**:
  - Application factory with CORS middleware and global typed error handling.
  - Endpoints: `GET /health`, `GET /api/v1/tools/status`, `POST /api/v1/estimate`, `POST /api/v1/plan/preview`, `GET /api/v1/stream/events` (SSE streaming).
- **Domain Modeling Layer (`src/models/`)**:
  - Immutable, frozen Pydantic v2 domain schemas (`TripContext`, `TripDates`, `TripParty`, `TripBudget`, `FoodPreferences`, `ExperiencePlan`, `DayPlan`, `ActivitySlot`, `PointOfInterest`, `LogisticsPlan`, `TransportLeg`, `HotelStay`, `VisaVerdict`, `BudgetBreakdown`, `BudgetVariance`).
  - Strict cross-field validations enforcing mode-dependent date constraints and mathematical variance equality.
- **Intake Functionality & Geographic Resolution (`src/nodes/intake_node.py`)**:
  - Input validation and sanitization for domestic and international trip requests.
  - Multi-tier geographic resolution: tourist hub & regional aliases, IATA airport codes, country profiles, and city/municipality indexed search.
  - Strict Indian origin enforcement and domestic vs. international scope reconciliation.
  - Date normalization (EXACT, FLEXIBLE, FIND_BEST modes), per-person budget splitting, and initial planning state assembly (`InitialPlanningState`).
- **Visa Planning & Policy Synthesis (`src/nodes/visa_node.py`)**:
  - Multi-tier entry policy evaluation combining static enriched datasets (199 destinations) and live web search verification.
  - Semantic structured LLM policy reconciliation (`LiveVisaPolicyAnalysis`) with zero regex, date-aware expiration checking for temporary waivers, and rejection of foreign nationality exemptions.
  - Automatic domestic bypass with zero cost and empty country verdicts for all-India itineraries.
  - Schengen single uniform visa optimization preventing redundant fees across multi-country European itineraries.
  - Accurate party headcount scaling on visa costs (`party.total_travelers`).
  - Strict anti-hallucination compliance (never invents visa rules; falls back to verified static baselines).
- **Logistics Planning & Route Execution (`src/nodes/logistics_node.py`)**:
  - Deterministic round-trip and multi-destination transport leg planning (flight, rail, road) connecting origin, intermediate stops, and return.
  - Multi-tier accommodation planning selecting optimal hotels based on travel style (`BUDGET`, `COMFORTABLE`, `PREMIUM`, `LUXURY`).
  - Party-aware room estimation heuristic (`estimate_rooms_required`) accurately sizing room requirements for adults and children.
  - Sequential stay duration and checkin/checkout date allocation across multi-destination itineraries.
  - Deterministic financial arithmetic scaling per-person transport fares across traveler party size and hotel costs across rooms and nights.
  - Booking URL preservation and non-crashing fallback synthesis (`is_estimated=True`, `physics-heuristic`, `location-heuristic`).
- **Experience Planning & Pacing Engine (`src/nodes/experience_node.py`)**:
  - Pacing calibration: Schedules activities per day tailored to user pace preference (`RELAXED`: 1, `BALANCED`: 2, `PACKED`: 3 activity slots per day across MORNING, AFTERNOON, and EVENING dayparts).
  - Authentic dining recommendations: Selects authentic breakfast, lunch, and dinner venues per day from `search_places` with meal-type appropriate budget tiers.
  - Weather-responsive indoor substitution: Evaluates daily meteorological forecasts, detects adverse outdoor conditions (rain, storms), and seamlessly substitutes outdoor attractions with indoor cultural venues (museums, galleries) with user-facing explanation notes and substitution tracking.
  - Must-visit fulfillment tracking: Prioritizes user must-visit sights, tracks fulfillment, and issues clear feasibility warnings if constraints prevent inclusion.
  - Logistics integration: Automatically associates hotel stay details and booking URLs from `LogisticsPlan` into daily itinerary schedules.
  - Party size cost scaling: Deterministically scales attraction tickets, dining expenses, and local transit across party headcount.
  - Resilient execution: Zero crashes on places/weather tool exceptions with graceful category-heuristic fallbacks.
- **Deterministic Budget Engine (`src/nodes/budget_node.py`)**:
  - Exact financial arithmetic with zero LLM math: Aggregates itemized costs across transport, accommodation, food, activities, visa, and miscellaneous daily expenses via `Decimal` calculations.
  - Complexity-calibrated contingency buffer: Dynamically calculates buffer (3%–20%) factoring domestic vs. international, multi-country stops, fallback pricing presence, and date flexibility.
  - 5-tier budget status classification: `EXACT`, `UNDER_BUDGET`, `MINOR_OVER` (≤5%), `SIGNIFICANT_OVER` (5%–15%), and `INFEASIBLE` (>15%).
- **Optimizer Planning Engine (`src/nodes/optimizer_node.py`)**:
  - Tiered optimization strategy: Automatic minor adjustments (hotel saver rate, dining adjustment) for ≤5% overage; user-visible trade-offs and alternatives for 5%–15%; cost-driver analysis and 4 structured alternatives for >15% infeasibility.
  - Strict preservation of hard quality guardrails: Must-visit sights cannot be silently omitted, dietary preferences cannot be violated, pace cannot be violated, and no unreasonable lodging downgrades.
- **LangGraph Multi-Agent Architecture (`src/graph/`)**:
  - Unified `StateGraph(PlanGraphState)` orchestrating `intake`, conditional `route_scope`, `visa`, parallel `logistics` and `experience` fan-out with deterministic state reduction (`merge_warnings`, `merge_errors`), `budget` convergence, and `optimizer` re-planning.
  - Selective re-planning engine (`replan_workflow`) isolating affected components and maximizing reuse of unaffected upstream artifacts.
- **First Complete Vertical Slice (`src/nodes/synthesizer_node.py`, `src/api/routes.py`)**:
  - Unified `FinalItinerary` synthesizer combining travel context, logistics, daily daypart activities, authentic dining, deterministic budget breakdown, and optimization notes into a cohesive travelogue narrative.
  - End-to-end `POST /api/v1/plan` API endpoint executing the full LangGraph workflow and returning validated plans.
- **International Vertical Slice (`src/nodes/visa_node.py`, `src/nodes/synthesizer_node.py`, `src/api/models.py`)**:
  - End-to-end planning slice for Indian passport holders traveling abroad: routes through `visa_node` with live policy analysis and static baseline fallback.
  - Schengen optimization: Single uniform visa application advisory and fee consolidation for multi-destination trips within the Schengen Area.
  - Multi-hop international transport legs and sequential hotel stays across foreign destinations.
  - Deterministic visa cost summation and integration into `BudgetBreakdown`, contingency buffer, and `FinalItinerary`.
  - Executive summary and traveler advisories dynamically enriched with Indian passport visa requirements, processing times, and advance notice rules.
- **Date Optimization & Flexible Planning Engine (`src/nodes/date_node.py`, `src/models/trip.py`)**:
  - 3 date operational modes: `DateMode.EXACT` (confirms dates with quality score), `DateMode.FLEXIBLE` (±N days shift optimization), and `DateMode.FIND_BEST` (sliding window sampling across calendar window).
  - Multi-factor evaluation balancing logistics pricing (transport + accommodation with seasonal demand multipliers), weather friendliness (rain probability and temperature comfort), and calendar convenience (+10 pt weekend weighting bonus).
  - Composite quality score on a 0–100 scale (`0.45 * price_score + 0.45 * weather_score + weekend_bonus`).
  - Transparent trade-offs: Surfaces estimated logistics costs, weather summaries, and leave/crowd observations across top recommendation and 2–3 ranked alternatives.
  - Downstream graph integration: Updates `trip_context` dates so downstream nodes plan on concrete optimal dates while preserving alternatives in `FinalItinerary.date_options`.
- **Warm Indian-Inspired Web Frontend (`frontend/`, Vite / React / TypeScript / Tailwind CSS / pnpm)**:
  - **Screen 1 (Welcome / Landing Screen)**: Editorial hero, flat-lay aesthetics, 6-card bento architecture, popular preview routes, and primary navigation.
  - **Screen 2 (Trip Details) & Scope Partitioning**:
    - **Scope Toggle**: Interactive toggle between `[ 🇮🇳 Domestic (Within India) ]` and `[ ✈️ International ]`.
    - **Dynamic Origin Routing**: Domestic travel allows selection from all 4,198 Indian cities, towns, and rail hubs from `india_places.json` + airports for train, cab, self-drive, or domestic flights; International travel strictly restricts departure origin to Indian commercial airports with valid IATA designations (`INDIAN_ORIGIN_AIRPORTS`, e.g. DEL, BOM, BLR, CCU, MAA, HYD) for immigration.
    - **Partitioned Destination Search**: Domestic queries search across Indian States, Union Territories, and regional circuits; International queries search across 250 sovereign countries (`generated_countries.json`) and global circuits.
    - **Real-Time Contextual Intelligence**: Adapting seasonal weather badges and Indian passport visa guidance.
  - **Screen 3 (Destinations & Route Sequence) & Strict Contextual Scoping**:
    - **Strict Contextual Scoping**: Search autocomplete returns the city union for all selected states or sovereign countries (`getContextualCitiesForDestination`). International destinations resolve before exact domestic city fallback, preventing cross-country/cross-state noise and incidental substring collisions. Multi-country chips normalize each selected destination independently, preserving comma-containing names.
    - **Responsive Route Editing**: Route stop cards and category controls stay within the mobile viewport; category filters scroll within their container.
    - **Real-Time Autocomplete Dropdown**: Rich dropdown rendering City Name, Region tag, Prominence badge (`★ Popular Stop` vs `Scenic Gateway`), and imagery.
    - **Dynamic Route Seeding & Scenic Transit Connectors**: Newly added stops receive realistic night allocation (default 2 nights), tailored roles, and dynamic scenic transit connectors (`generateScenicTransitConnector`, e.g. Fjord Ferry in Norway, Shinkansen in Japan, Intercity Heritage Express in Rajasthan).
    - **Contextual Add Button**: `+ Add another destination to route` dynamically picks the next unadded popular city from the contextual list rather than defaulting to Tokyo.
    - **Duration Reconciliation Engine**: Reconciles total stop nights against target duration with one-click return date synchronization.
  - **Screen 4 (Travel Preferences)**:
    - Backend-aligned travel style (`BUDGET`, `COMFORTABLE`, `PREMIUM`, `LUXURY`) and pace (`RELAXED`, `BALANCED`, `PACKED`) selection.
    - Unique supported experience interests selection.
    - Source-backed named attractions for active route cities (Tavily + Gemini structured extraction catalog).
    - Saved values that no longer match after trip edits are flagged and block continuation until corrected.
  - **Screen 5 (Budget)**:
    - INR target with `TOTAL`/`PER_PERSON` mode and ₹1,000 minimum.
    - No live pricing or invented provider API.
  - **Screen 6 (Review & Confirm)**:
    - Ordered stops/nights, origin/destination, travelers/dates, preferences, budget, section edit routes, full-draft validation, and backend-shaped `PlanRequestDraft` mapper.
    - Infant counts surfaced as unsupported by the current request contract instead of dropped.
    - Confirmation validates the full draft and launches the Batch 3 planning flow at `/planner/progress`.
  - **Screen 8: Trip Planning Progress (`/planner/progress`)**:
    - Continuous synthesis engine: 7-stage vertical timeline (*Understanding your trip*, *Checking travel logistics*, *Finding experiences*, *Checking weather*, *Calculating budget*, *Optimizing your journey*, *Your Safarnama is ready*) with live indicators, completed checks, elapsed run timer, and stage telemetry tags.
    - Blueprint banner with origin/destination corridor progression, seasonal highlight badge, party description, duration, and dossier run badge (`#SF-8492`).
    - Route alignment & telemetry visualizer: waypoint stays with night counts, scenic transit connectors, verified data tags, and editorial philosophy excerpt.
    - SSE consumer connecting to `POST /api/v1/plan/stream` with realistic simulation fallback (`simulatePlanningStream`) for development, offline, and hermetic testing environments, plus clean abort/cancel returning to review with draft inputs preserved.
  - **Screen 9: Trip Overview Dossier (`/trip/overview`)**:
    - Dossier header and meta (run tag, departure readiness pulse, editorial title, summary, and quick metadata pills), cinematic 21:9 hero showcase, Curator's Note, and Pacing & Rhythm Index gauges (*Cultural Immersiveness* 94%, *Transit Leisure Margin* 88%).
    - Interactive 3-column route corridor with stop numbers, night counts, scenic rail tags, and waypoint imagery.
    - Trip snapshot matrix (6 cards), budget leeway breakdown (Stays 39%, Transit 26%, Experiences 14%, Dining 13%, Contingency 8%), highlights gallery, and regional microclimate/packing forecast cards.
    - Navigation & actions: *View Full Itinerary* → `/trip/itinerary` (Batch 4 boundary), *Edit Route & Preferences* (returns to Step 1 preserving inputs), and *Export & Share Dossier* (clipboard sync).
  - **URL-Addressable Routes & Persistence**: History API routes for all 8 screens (6 wizard screens, `/planner/progress`, `/trip/overview`) with back/forward synchronization; versioned browser-local storage restores draft across direct loads, refreshes, and navigation.
  - **Itinerary State & Device-Local Persistence**: Canonical `FinalItinerary` domain types (`FinalItinerary`, `DayPlan`, `ActivitySlot`, `DayMeal`, `HotelStay`, `TransportLeg`, `BudgetBreakdown`, `PlanningEvent`, `PlanRunState`) in `frontend/src/types/itinerary.ts`; `TripPlanningContext` extended with `itinerary`, `planRunState`, and `clearPlan`; localStorage key `safarnama.itinerary.v1` preserves generated itineraries across refreshes, direct URL re-entry, and navigation; `synthesizeItineraryFromDraft()` provides a dynamic offline synthesizer.
- **Dual Verification Testing Architecture**:
  - **Hermetic Offline Test Harness**: 587+ backend unit tests running completely offline (`SAFARNAMA_USE_FIXTURES=true`) + 30 frontend Vitest component & flow tests (`flow.test.tsx` [25] + `batch3.test.tsx` [5]).
  - **Live Network Integration Verification**: Automated 8-stage live verification suite (`scripts/verify_live_nodes.py`) validating real-world API connectivity, authentication, live schema compatibility, and graceful fallbacks across all planning nodes.

### Planned Capabilities (Future Phases)

- **Frontend Batch 4** (Day-by-Day Itinerary `/trip/itinerary`, Day Detail / Activity Timeline, Destination Details, Transport Details) — *Phase 18 Continued*
- **End-to-End Test Matrix & Hardening** — *Phases 19–20*

---

## 4. Key Product Principles

1. **User Constraints Are Rigid**: User choices (dates, budget ceilings, travel party, must-visit locations) are hard constraints. The system never silently drops or alters them.
2. **Deterministic Financial Arithmetic**: Financial additions, multiplications, variances, and currency conversions are never delegated to an LLM.
3. **Verified Data Over Generated Facts**: The engine relies on verified static data and live tool outputs rather than LLM memory for factual travel entities.
4. **Transparent Provenance**: When exact live costs are unavailable and fallback estimation is required, values are explicitly tagged with `is_estimated=True`.
5. **No Fabricated Visa Information**: International visa pathways must be backed by verified datasets or authoritative sources.
6. **Provider Abstraction**: All external APIs (Forex, Weather, Search, Flights, Hotels) are wrapped behind stable internal interfaces and supported by offline fixtures.
7. **Incremental Verification**: Every component is tested, linted, and verified before dependent modules are implemented.

---

## 5. Architecture Overview

### High-Level Planned Architecture

```text
                           USER REQUEST
                                │
                                ▼
                       ┌─────────────────┐
                       │  FastAPI / CLI  │
                       │ (Request Intake)│
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Intake Node   │
                       │(Validate Scope) │
                       └────────┬────────┘
                                │
                       ┌────────┴────────┐
                       │                 │
                INTERNATIONAL         DOMESTIC
                       │                 │
                       ▼                 │
                ┌──────────────┐         │
                │  Visa Node   │         │
                │(Static + Live│         │
                │ Verification)│         │
                └──────┬───────┘         │
                       │                 │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │Parallel Planning│
                       └────────┬────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
       ┌──────────────────┐          ┌───────────────────┐
       │  Logistics Node  │          │  Experience Node  │
       │ (Transport/Stay) │          │(Activities/Dining)│
       └────────┬─────────┘          └─────────┬─────────┘
                │                              │
                └───────────────┬──────────────┘
                                ▼
                       ┌─────────────────┐
                       │ Optimizer Node  │
                       │ (Deterministic  │
                       │  Budget Engine) │
                       └────────┬────────┘
                                │
                       ┌────────┴────────┐
                       │                 │
                   FEASIBLE           CONFLICT
                       │                 │
                       ▼                 ▼
                ┌──────────────┐  ┌──────────────┐
                │Final Itinery │  │Trade-off Plan│
                └──────────────┘  └──────────────┘
`

### Current Implementation vs Planned Components

```text
IMPLEMENTED & VERIFIED (Phases 0–17 + Frontend Batch 1–3)
┌─────────────────────────────────────────────────────────────┐
│ src/api/                                                    │
│ - FastAPI endpoints, CORS & SSE streaming                   │
│ - POST /api/v1/plan, /plan/replan, /plan/stream (SSE)        │
│ - Request/Response Pydantic models                          │
├─────────────────────────────────────────────────────────────┤
│ src/models/                                                 │
│ - trip, itinerary, logistics, visa, budget, final itinerary │
├─────────────────────────────────────────────────────────────┤
│ src/nodes/                                                  │
│ - intake_node.py (Intake/Resolution/Scope)                  │
│ - visa_node.py (Visa/Schengen/Live Verification)            │
│ - logistics_node.py (Transport/Hotels/Rooms)                │
│ - experience_node.py (Pacing/Dining/Weather)               │
│ - budget_node.py (Deterministic Engine)                     │
│ - optimizer_node.py (Tiered Optimization/Trade-offs)        │
│ - date_node.py (Flexible Date Optimization)                 │
│ - synthesizer_node.py (Final Itinerary Assembly)            │
├─────────────────────────────────────────────────────────────┤
│ src/graph/                                                  │
│ - state.py (PlanGraphState, reducers)                       │
│ - edges.py (Routing, scope, component isolation)            │
│ - workflow.py (StateGraph, replan_workflow)                 │
│ - streaming.py (Real-time SSE event emission)               │
├─────────────────────────────────────────────────────────────┤
│ src/tools/ (All 8 Tools)                                    │
│ - static_data.py, calculator.py, forex.py, weather.py      │
│ - web_search.py, transport.py, hotels.py, places.py         │
│ - fallback_estimator.py                                     │
├─────────────────────────────────────────────────────────────┤
│ frontend/ (Vite + React 19 + TypeScript + Tailwind + pnpm)  │
│ - Batch 1: Welcome, Trip Details, Destinations (Screens 1-3)│
│ - Batch 2: Preferences, Budget, Review & Confirm (Screens 4-6)│
│ - Batch 3: Planning Progress & Trip Overview (Screens 8-9)  │
│ - Draft + itinerary persistence (safarnama.itinerary.v1)     │
└─────────────────────────────────────────────────────────────┘

PLANNED (Upcoming Phases)
┌─────────────────────────────────┐
│ Frontend Batch 4                │
│ - Day-by-Day Itinerary & Timeline│
│ - Destination & Transport Details│
├─────────────────────────────────┤
│ End-to-End Test Matrix (Phase 19)│
├─────────────────────────────────┤
│ Production Hardening (Phase 20)  │
└─────────────────────────────────┘
```

---

## 6. Technology Stack

### Current Technologies

- **Python**: `>=3.11` (developed and tested with Python 3.11–3.14)
- **Package & Dependency Manager**: [`uv`](https://docs.astral.sh/uv/) (strictly required; `pip` is prohibited)
- **Build System**: `hatchling` (configured with `src` package layout)
- **Data Validation & Schemas**: [`pydantic>=2.13.5`](https://docs.pydantic.dev/) (Pydantic v2 domain models)
- **Web API Framework**: [`fastapi>=0.115.0`](https://fastapi.tiangolo.com/) & [`httpx>=0.28.1`](https://www.python-httpx.org/)
- **Environment Management**: [`python-dotenv>=1.2.3`](https://github.com/theskumar/python-dotenv)
- **AI SDK**: [`google-genai>=2.25.0`](https://github.com/googleapis/python-genai) (Google Gemini API client)
- **Testing**: [`pytest>=9.1.1`](https://docs.pytest.org/)
- **Linting & Formatting**: [`ruff>=0.16.8`](https://docs.astral.sh/ruff/)

### Additional Technologies (Now Complete)

- **Workflow Orchestration**: `langgraph` (Phase 12 — Complete)
- **Frontend**: Vite / React / TypeScript with `pnpm` (Phase 18 — Complete)

---

## 7. Repository Structure

```text
Safarnama/
├── .env.example              # Template for environment variables
├── pyproject.toml            # Project metadata, dependencies, pytest & ruff configs
├── uv.lock                   # Deterministic lockfile managed by uv
├── data/
│   ├── fixtures/             # Offline mock data for zero-network testing
│   │   ├── airports_sample.csv
│   │   ├── mock_forex.json
│   │   ├── mock_hotels.json
│   │   ├── mock_places.json
│   │   ├── mock_routes.json
│   │   ├── mock_search.json
│   │   ├── mock_weather.json
│   │   ├── visa_rules_sample.csv
│   │   └── visa_rules_sample_iso2.csv
│   └── static/               # Production static JSON datasets
│       ├── airports.json     # 3,244 commercial airports worldwide
│       ├── countries.json    # 250 enriched country profiles
│       ├── india_places.json # 36 Indian states/UTs & 4,198 cities
│       ├── visa_rules.json   # 199 base visa rules for Indian passport holders
│       └── visa_rules_enriched.json # 199 multi-option enriched visa records
├── project_docs/             # Canonical project specifications & architectural guides
│   ├── 00-product/           # Product definitions
│   │   ├── architecture.md   # Target system architecture and node specifications
│   │   ├── design.md         # Visual identity and UI design tokens
│   │   └── prd.md            # Product Requirements Document
│   ├── 01-planning/          # Implementation roadmap & frontend batches
│   │   ├── phases.md         # Granular phase-by-phase implementation roadmap
│   │   ├── frontend_batches.md        # Screen generation batch checklist
│   │   ├── frontend_batch_develop.md  # Batch execution playbook
│   │   └── frontend_batch_plans/      # Per-batch implementation plans
│   ├── 02-prompts/           # Reusable agent prompt templates
│   └── 03-reference/         # Reference material
│       ├── memory.md         # Implementation progress snapshot and handoff record
│       ├── rules.md          # Mandatory engineering and AI assistant rules
│       └── attraction_catalog.md # Source-backed attraction catalog
├── scripts/                  # On-demand static data ingestion and enrichment scripts
│   ├── enrich_visa_rules.py  # Gemini + Tavily on-demand visa rule enrichment
│   ├── fetch_airports.py     # Ingests airports from ourairports-data
│   ├── fetch_country_profiles.py # Ingests country metadata from REST Countries v5
│   ├── fetch_india_places.py # Ingests 36 Indian states/UTs & 4,198 cities from CountryStateCity
│   └── fetch_visa_rules.py   # Ingests passport visa baseline from passport-index
├── src/                      # Importable application source package (`import src.*`)
│   ├── api/                  # FastAPI routers, app factory and endpoints (Phase 4)
│   │   ├── app.py            # FastAPI app factory with CORS & exception handlers
│   │   ├── models.py         # API Request/Response schemas (Estimate, PlanPreview, etc.)
│   │   └── routes.py         # API routes (health, tools/status, estimate, preview, SSE)
│   ├── graph/                # LangGraph state, edges, workflow & SSE streaming (Phases 12 & 17)
│   ├── models/               # Canonical Pydantic v2 domain models (Phases 1–5)
│   │   ├── airport.py        # Airport model
│   │   ├── budget.py         # CostBreakdown, ContingencyConfig, BudgetVariance, BudgetBreakdown
│   │   ├── country.py        # CountryProfile, CurrencyInfo, LanguageInfo, Coordinates
│   │   ├── itinerary.py      # PointOfInterest, ActivitySlot, DayMeal, DayPlan, ExperiencePlan
│   │   ├── logistics.py      # TransportLeg, HotelStay, LogisticsPlan
│   │   ├── trip.py           # TripParty, TripDates, TripBudget, FoodPreferences, TripContext
│   │   └── visa.py           # BaseVisaRule, VisaOption, EnrichedVisaRecord, VisaVerdict
│   ├── nodes/                # LangGraph agent planning nodes (Phases 6–16)
│   │   ├── __init__.py       # Exports intake_node, visa_node, logistics_node, etc.
│   │   ├── intake_node.py    # Phase 6: Sanitization, gateway resolution, scope reconciliation
│   │   ├── logistics_node.py # Phase 8: Transport legs & hotel stays planning, room estimation
│   │   ├── visa_node.py      # Phase 7: Static baseline + live policy reconciliation & verdict
│   │   ├── budget_node.py    # Phase 10: Deterministic budget engine
│   │   ├── optimizer_node.py # Phase 11: Tiered optimization & trade-offs
│   │   ├── date_node.py      # Phase 15: Flexible date window optimization
│   │   └── synthesizer_node.py # Phase 13: Final itinerary assembly
│   ├── prompts/              # Isolated system prompts and prompt templates
│   │   ├── estimator_prompts.py # Prompts for LLM fallback estimator
│   │   └── visa_prompts.py   # Prompts for visa enrichment & live verification
│   └── tools/                # Deterministic utilities and external tool wrappers (Phase 2–3)
│       ├── calculator.py     # Tool 1: Deterministic budget calculator (Decimal)
│       ├── fallback_estimator.py # Tool 8: Multi-provider LLM cost fallback estimator
│       ├── forex.py          # Tool 2: Multi-tier currency converter (INR)
│       ├── hotels.py         # Tool 6: Multi-tier hotel & stay search
│       ├── places.py         # Tool 7: Points of interest & dining discovery
│       ├── static_data.py    # Static data access layer & in-memory store
│       ├── transport.py      # Tool 5: Multi-tier route & transport search
│       ├── weather.py        # Tool 3: Multi-tier weather forecast
│       └── web_search.py     # Tool 4: Multi-tier web search engine
├── frontend/                 # Vite + React 19 + TypeScript + Tailwind CSS web client
│   ├── src/
│   │   ├── components/       # Reusable UI components (Header, Footer, Stepper, etc.)
│   │   ├── context/          # TripPlanningContext state management
│   │   ├── data/             # Static datasets (countries, India places, attractions)
│   │   ├── screens/          # 8 screens (Welcome → Planning Progress → Trip Overview)
│   │   ├── test/             # Vitest component & flow tests (30 tests)
│   │   └── types/            # TypeScript type definitions
│   └── package.json          # pnpm-managed dependencies
└── tests/                    # Automated test suite
    ├── conftest.py           # Shared pytest fixtures
    ├── integration/          # Integration test suite (Phase 11 scaffold)
    └── unit/                 # 587 passing offline unit tests
        ├── test_api.py       # API endpoint, validation & SSE streaming tests
        ├── test_api_streaming.py # 12 Phase 17 SSE streaming tests
        ├── test_attractions.py # Attraction catalog extraction tests
        ├── test_budget_node.py # 20 Phase 10 deterministic budget engine tests
        ├── test_calculator.py
        ├── test_date_optimizer.py # 19 Phase 15 flexible date tests
        ├── test_domain_models.py # 89 tests for trip, itinerary, logistics, visa, budget
        ├── test_enrich_visa_rules.py
        ├── test_experience_node.py # 13 Phase 9 experience planning tests
        ├── test_fallback_estimator.py
        ├── test_fetch_airports.py
        ├── test_fetch_country_profiles.py
        ├── test_fetch_india_places.py # 5 Indian geographic ingestion tests
        ├── test_fetch_visa_rules.py
        ├── test_forex.py
        ├── test_graph.py     # 19 Phase 12 LangGraph orchestration tests
        ├── test_hotels.py
        ├── test_human_decision_flow.py # 15 Phase 16 re-planning tests
        ├── test_intake_node.py # 21 tests for intake node, resolution, scope enforcement
        ├── test_international_slice.py # 8 Phase 14 international slice tests
        ├── test_logistics_node.py # 22 tests for logistics planning, rooms, and routes
        ├── test_optimizer_node.py # 18 Phase 11 optimizer & guardrail tests
        ├── test_places.py
        ├── test_project_foundation.py
        ├── test_static_data.py
        ├── test_transport.py
        ├── test_vertical_slice.py # 9 Phase 13 domestic vertical slice tests
        ├── test_visa_node.py # 20 tests for visa node, semantic LLM reconciliation, static baseline
        ├── test_weather.py
        └── test_web_search.py
```

---

## 8. Development Phases & Roadmap

Safarnama uses an incremental delivery roadmap defined in `project_docs/01-planning/phases.md`. Each phase must be fully implemented, tested, and verified before the next begins.

```text
Phase 0: Project Foundation [COMPLETED]
      ↓
Phase 1: Static Data Ingestion [COMPLETED]
      ↓
Phase 2: Static Data Access Layer [COMPLETED]
      ↓
Phase 3: External Tool Layer [COMPLETED: 8/8 Tools Done]
      ↓
Phase 4: API Foundation [COMPLETED: FastAPI, Endpoints & SSE]
      ↓
Phase 5: Domain Models [COMPLETED: Trip, Itinerary, Logistics, Visa, Budget]
      ↓
Phase 6: Intake Functionality [COMPLETED: Sanitization, Resolution, Initial State]
      ↓
Phase 7: Visa Functionality [COMPLETED: Static Baseline + Semantic LLM Verification]
      ↓
Phase 8: Logistics Functionality [COMPLETED: Transport Legs & Hotel Stays Planning]
      ↓
Phase 9: Experience Functionality [COMPLETED: Attractions, Dining & Weather Pacing]
      ↓
Phase 10: Deterministic Budget Engine [COMPLETED: Aggregation, Variance & Contingency]
      ↓
Phase 11: Optimizer Functionality [COMPLETED: Tiered Optimization & Trade-offs]
      ↓
Phase 12: LangGraph Orchestration [COMPLETED: StateGraph, Parallel Nodes, Re-planning]
      ↓
Phase 13: First Complete Vertical Slice [COMPLETED: End-to-End Domestic Planning]
      ↓
Phase 14: International Vertical Slice [COMPLETED: Visa Integration & Multi-Country]
      ↓
Phase 15: Flexible Dates [COMPLETED: Candidate Window Optimization & Scoring]
      ↓
Phase 16: Budget Conflict & Human Decision Flow [COMPLETED: Interactive Re-planning]
      ↓
Phase 17: API Streaming [COMPLETED: Real-time LangGraph SSE Events]
      ↓
Phase 18: Frontend [BATCHES 1–3 COMPLETE: Welcome, Trip Details, Destinations, Preferences, Budget, Review & Confirm, Planning Progress, Trip Overview — Batch 4 Next]
      ↓
Phase 19: End-to-End Test Matrix [PLANNED]
      ↓
Phase 20: Production Hardening [PLANNED]
```

---

## 9. Current Implementation Status

### Completed Milestones

- **Phase 0 (Foundation)**: Packaging with `hatchling` and `uv`, package namespace setup, testing and linting configurations.
- **Phase 1 (Static Data Ingestion)**:
  - `scripts/fetch_airports.py`: Filters and ingests 3,244 commercial scheduled airports from OurAirports.
  - `scripts/fetch_visa_rules.py`: Joins positional dual-CSV data from Passport Index to create 199 base visa records for Indian travelers.
  - `scripts/enrich_visa_rules.py`: Live web research (Tavily) synthesized via Google Gemini structured outputs with model fallback across rate limits (199 destinations enriched).
  - `scripts/fetch_country_profiles.py`: Ingests 250 normalized country profiles via REST Countries v5.
- **Phase 2 (Static Data Access Layer)**:
  - `StaticDataStore` singleton caching all static datasets in memory.
  - Fast O(1) indexed lookup functions (`get_airport`, `get_country`, `get_visa_rule`, `is_schengen`, `get_ist_time_difference_hours`).
- **Phase 3 (External Tool Layer — 8/8 Complete)**:
  - **Tool 1: Calculator Tool (`src/tools/calculator.py`)**: Exact decimal arithmetic, expense categorization, buffer calculations, and budget variance evaluation.
  - **Tool 2: Forex Tool (`src/tools/forex.py`)**: Deterministic currency conversion to INR with 5-tier fallback and 40+ built-in offline currency rates.
  - **Tool 3: Weather Tool (`src/tools/weather.py`)**: Multi-tier weather forecast (Open-Meteo, wttr.in, OpenWeatherMap, Climate Baseline) with weather hazard detection.
  - **Tool 4: Web Search Tool (`src/tools/web_search.py`)**: Multi-tier travel search (Tavily, DuckDuckGo, Firecrawl, offline fixture).
  - **Tool 5: Transport Tool (`src/tools/transport.py`)**: Multi-tier route search (Sky Scraper, Flights Sky, IRCTC, European rail, web search fallback, distance physics engine).
  - **Tool 6: Hotel Tool (`src/tools/hotels.py`)**: Multi-tier lodging search (SerpApi Google Hotels, Booking.com, Nominatim OSM, web search fallback, location heuristic).
  - **Tool 7: Places & Dining Tool (`src/tools/places.py`)**: Points of interest and dining search (SerpApi Google Maps, Nominatim OSM, web search fallback, category baseline).
  - **Tool 8: Fallback Estimator (`src/tools/fallback_estimator.py`)**: Multi-provider LLM fallback cost estimation (Gemini, Groq, NVIDIA NIM, offline rule baseline) with isolated prompts in `src/prompts/estimator_prompts.py`.
- **Phase 4 (API Layer — Complete)**:
  - `src/api/models.py`: API request/response Pydantic models (`HealthResponse`, `ToolStatusResponse`, `EstimateRequest`, `EstimateResponse`, `PlanPreviewRequest`, `PlanPreviewResponse`, `APIErrorResponse`).
  - `src/api/routes.py`: FastAPI routes with error mapping, request validation, and SSE streaming.
  - `src/api/app.py`: FastAPI app factory (`create_app()`) with CORS middleware and global exception handling.
  - 10 comprehensive unit tests in `tests/unit/test_api.py`.
- **Phase 5 (Domain Models — Complete)**:
  - `src/models/trip.py`: Enums (`TravelScope`, `DateMode`, `BudgetMode`, `TravelStyle`, `Pace`, `FoodImportance`) and composites (`TripParty`, `TripDates`, `TripBudget`, `FoodPreferences`, `TripContext`).
  - `src/models/itinerary.py`: Enums (`Daypart`, `ActivityCategory`) and composites (`PointOfInterest`, `ActivitySlot`, `DayMeal`, `DayPlan`, `ExperiencePlan`).
  - `src/models/logistics.py`: `TransportLeg`, `HotelStay`, `LogisticsPlan` domain models.
  - `src/models/visa.py`: Extended with planning domain types (`VisaRequirementStatus`, `VisaCountryVerdict`, `VisaVerdict`).
  - `src/models/budget.py`: Enums (`BudgetStatus`, `OptimizationAction`) and composites (`CostBreakdown`, `ContingencyConfig`, `BudgetVariance`, `OptimizationResult`, `BudgetBreakdown`).
  - 89 unit tests in `tests/unit/test_domain_models.py`.
- **Phase 6 (Intake Functionality — Complete)**:
  - `src/nodes/intake_node.py`: Request sanitization and validation, alias mapping (`DOMESTIC_GATEWAY_ALIASES`, `INTERNATIONAL_GATEWAY_ALIASES`), hierarchical location resolution (`resolve_location`), strict Indian origin enforcement, domestic vs. international scope reconciliation, and initial planning state assembly (`InitialPlanningState`).
  - 21 unit tests in `tests/unit/test_intake_node.py`.
- **Phase 7 (Visa Functionality — Complete)**:
  - `src/prompts/visa_prompts.py`: Isolated prompt engineering for live visa verification and structured semantic policy reconciliation (`build_live_visa_verification_prompt`).
  - `src/models/visa.py`: Added `LiveVisaPolicyAnalysis` Pydantic model for structured, validated LLM extraction.
  - `src/nodes/visa_node.py`: Deterministic visa evaluation pipeline (`evaluate_country_visa`, `process_visa`, `visa_node`), automatic domestic bypass for all-India trips, semantic LLM policy reconciliation cascade (Gemini, Groq, NVIDIA NIM) with zero regex, date-aware expiration checking for temporary waivers, Schengen single-visa fee optimization, and total party headcount scaling.
  - 20 comprehensive unit tests in `tests/unit/test_visa_node.py`.
- **Phase 8 (Logistics Functionality — Complete)**:
  - `src/nodes/logistics_node.py`: Transport legs and accommodation planning (`logistics_node`, `process_logistics`), family-friendly room heuristics (`estimate_rooms_required`), continuous multi-city date allocations (`allocate_stay_dates`), travel style accommodation matching, per-person fare scaling across party headcount, and non-crashing fallback synthesis.
  - 22 comprehensive unit tests in `tests/unit/test_logistics_node.py`.
- **Phase 9 (Experience Functionality — Complete)**:
  - `src/nodes/experience_node.py`: Daily activity and dining planning engine (`experience_node`, `process_experience`), pacing calibration (`RELAXED`: 1, `BALANCED`: 2, `PACKED`: 3 slots/day), weather-responsive indoor substitutions with transparent traveler notes, must-visit fulfillment tracking, hotel and booking URL association from `LogisticsPlan`, and party-scaled deterministic cost aggregation.
  - 13 comprehensive unit tests in `tests/unit/test_experience_node.py`.
- **Phases 10–12 (Budget Engine, Optimizer & LangGraph Orchestration — Complete)**:
  - Deterministic `Decimal` budget engine with dynamic contingency and 5-tier variance classification (`src/nodes/budget_node.py`, 20 tests in `tests/unit/test_budget_node.py`).
  - Tiered optimizer with hard quality guardrails, trade-off alternatives, and re-planning proposals (`src/nodes/optimizer_node.py`, 18 tests in `tests/unit/test_optimizer_node.py`).
  - Compiled `StateGraph` with parallel planning branches, deterministic warning/error reducers, and selective re-planning (`src/graph/`, 19 tests in `tests/unit/test_graph.py`).
- **Phases 13–14 (Domestic & International Vertical Slices — Complete)**:
  - End-to-end `POST /api/v1/plan` itinerary synthesis into immutable `FinalItinerary`, auto scope detection, deterministic visa fee integration, and Schengen single-visa optimization (`tests/unit/test_vertical_slice.py`, `tests/unit/test_international_slice.py`).
- **Phase 15 (Flexible Dates — Complete)**:
  - `date_optimizer` node generating `EXACT`, `FLEXIBLE`, and `FIND_BEST` candidate windows with multi-factor pricing/weather/convenience scoring (`src/nodes/date_node.py`, 19 tests in `tests/unit/test_date_optimizer.py`).
- **Phase 16 (Budget Conflict & Human Decision Flow — Complete)**:
  - 4-tier budget conflict resolution with human trade-off decisions and component-isolated selective re-planning via `POST /api/v1/plan/replan` (`tests/unit/test_human_decision_flow.py`).
- **Phase 17 (API Streaming — Complete)**:
  - `src/graph/streaming.py` emitting milestone `PlanningEvent`s from LangGraph `astream_events(..., version="v2")` with `POST`/`GET /api/v1/plan/stream` endpoints (`tests/unit/test_api_streaming.py`).
- **Frontend Batch 3 (Phase 18 — Complete)**:
  - Trip Planning Progress (`/planner/progress`): 7-stage continuous synthesis timeline consuming `POST /api/v1/plan/stream` with simulation fallback, route/telemetry visualizer, elapsed timer, and cancel controls.
  - Trip Overview Dossier (`/trip/overview`): hero showcase, Curator's Note, Pacing & Rhythm Index, route corridor, snapshot matrix, budget leeway breakdown, and microclimate/packing cards.
  - State & persistence: `FinalItinerary` domain types in `frontend/src/types/itinerary.ts`, `TripPlanningContext` extensions, and `safarnama.itinerary.v1` localStorage persistence.
  - 30 frontend tests passing (`frontend/src/test/flow.test.tsx` [25] + `batch3.test.tsx` [5]).

### Immediate Next Milestone

- **Phase 18 — Frontend Batch 4**: Day-by-Day Itinerary (`/trip/itinerary`), Day Detail / Activity Timeline, Destination Details, and Transport Details (Screens 10–13).

---

## 10. Local Setup

### Prerequisites

- **Python**: Version `3.11` or higher.
- **Package Manager**: [`uv`](https://docs.astral.sh/uv/) (Astral).
  *Do not use `pip`.* If `uv` is not installed, install it via:
  ```powershell
  # Windows (PowerShell)
  winget install astral-sh.uv
  # or
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Shouvik599/Safarnama.git
   cd Safarnama
   ```

2. Synchronize virtual environment and dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Configure your local environment file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to supply API keys as needed (see [Environment Variables](#11-environment-variables)).

4. Verify the setup by running the test suite and linter:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```

---

## 11. Environment Variables

The project uses `.env` for local configuration. A documented template is provided in `.env.example`.

> **Rule 46 (Configuration Synchronization)**: Whenever an environment variable is added, modified, or removed in `.env`, `.env.example`, `README.md`, and project documentation must be updated in lockstep.

| Variable | Category | Required For | Purpose & Fallback Behavior |
|---|---|---|---|
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | 1. LLM & Fallback | Planning & Fallback | Primary Gemini planning LLM and Fallback Estimator Tier 1 (Google AI Studio). |
| `GROQ_API_KEY` | 1. LLM & Fallback | Fallback Estimator | Groq API key for ultra-fast LPU fallback cost estimation (Tier 2). If omitted, cascades to NVIDIA NIM / offline rules. |
| `NVIDIA_API_KEY` | 1. LLM & Fallback | Fallback Estimator | NVIDIA NIM key for hosted open models fallback estimation (Tier 3). If omitted, cascades to offline heuristic. |
| `FALLBACK_LLM_API_KEY` | 1. LLM & Fallback | Fallback Estimator | Optional dedicated override key for LLM cost estimations. |
| `FALLBACK_LLM_MODEL` | 1. LLM & Fallback | Fallback Estimator | Optional dedicated model override for fallback estimation (e.g., `gemini-2.5-flash`). |
| `GEMINI_ENRICHMENT_API_KEY` | 2. Visa Enrichment | Ingestion Script | Dedicated Gemini key for multi-pathway visa synthesis in `scripts/enrich_visa_rules.py`. |
| `GEMINI_ENRICHMENT_MODEL` | 2. Visa Enrichment | Ingestion Script | Optional model override for visa enrichment (default: `gemini-2.5-flash-lite`). |
| `TAVILY_VISA_ENRICHMENT_API_KEY` | 2. Visa Enrichment | Ingestion Script | Dedicated Tavily key for web research in `scripts/enrich_visa_rules.py`. |
| `TAVILY_API_KEY` | 3. Web Search | Ingestion & Runtime | General Tavily search API key used by `src/tools/web_search.py` and tool search fallbacks. |
| `FIRECRAWL_API_KEY` | 3. Web Search | Runtime Search | Optional Firecrawl Search API key (Tier 3). If omitted, Tavily, DuckDuckGo, and offline fixtures are used. |
| `SERPAPI_KEY` | 4. Travel & Lodging | Flights, Hotels & Places | Google Flights (primary Tier-0 flight provider with real fares), Google Hotels, and Google Maps search for accommodations, POIs, and dining (`src/tools/transport.py`, `src/tools/hotels.py`, `src/tools/places.py`). Fallbacks to Sky Scraper, Flights Sky, Aviationstack, Booking.com, Nominatim/OSM, and physics engine. |
| `RAPIDAPI_KEY` | 4. Travel & Lodging | Transport & Hotels | Multi-modal travel endpoints: Sky Scraper flights, Flights Sky, and Indian Railways IRCTC (`src/tools/transport.py`), Booking.com (`src/tools/hotels.py`). Fallbacks to European rail, web search, and physics engine. |
| `AVIATIONSTACK_API_KEY` | 4. Travel & Lodging | Flight Schedules | Optional live airline and flight schedule status tracking. |
| `REST_COUNTRIES_API_KEY` | 4. Travel & Lodging | Ingestion Script | Ingestion API key for REST Countries v5 in `scripts/fetch_country_profiles.py` (free 1,000 req/mo). |
| `OPENWEATHERMAP_API_KEY` | 5. Weather & Forex | Weather Tool | Optional OpenWeatherMap 5-day forecast fallback (`src/tools/weather.py`). If omitted, Open-Meteo, wttr.in, and climate baseline are used. |
| `EXCHANGERATE_API_KEY` | 5. Weather & Forex | Forex Tool | Optional ExchangeRate-API key (`src/tools/forex.py`). If omitted, open.er-api.com and offline tables are used automatically. |
| `SAFARNAMA_USE_FIXTURES` | 6. Configuration | Testing & Offline Dev | When set to `true`, forces all runtime tools to load offline mock fixtures from `data/fixtures/` with zero live network calls. |

> **Security Notice**: Never commit `.env` or real API keys to source control.

---

## 12. Running the Project

Safarnama currently provides:
1. The **FastAPI REST API Server** (`src/api/`) with interactive OpenAPI docs, health checks, tool status telemetry, cost estimation, and SSE streaming.
2. The **Immutable Domain Modeling Layer** (`src/models/`) defining contracts for trip context, itineraries, logistics, visas, and budgets.
3. The **External Travel Tools Suite** (`src/tools/`) with all 8 multi-tier adapters and offline fixtures.
4. The **Static Data Ingestion Suite** (`scripts/`) for on-demand dataset ingestion and AI-assisted visa rule enrichment.
5. The **React Web Client** (`frontend/`) implementing the 8-screen planning wizard, live `/planner/progress` SSE consumption, and the `/trip/overview` dossier.

### Starting the FastAPI Server

Launch the local development API server using `uv`:

```bash
uv run uvicorn src.api.app:app --reload --port 8000
```

Once running, explore:
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **Health Check**: `curl http://127.0.0.1:8000/health`
- **Tool Status Report**: `curl http://127.0.0.1:8000/api/v1/tools/status`
- **Real-time SSE Stream**: `curl -N http://127.0.0.1:8000/api/v1/stream/events`

### Running Ingestion Scripts

```bash
# Ingest airports (OurAirports -> data/static/airports.json)
uv run python scripts/fetch_airports.py

# Ingest baseline visa rules (Passport Index -> data/static/visa_rules.json)
uv run python scripts/fetch_visa_rules.py

# Ingest country metadata (REST Countries v5 -> data/static/countries.json)
uv run python scripts/fetch_country_profiles.py

# Enrich visa rules for a specific destination (requires GEMINI_ENRICHMENT_API_KEY & TAVILY key)
uv run python scripts/enrich_visa_rules.py --destination "Japan"

# Dry run visa enrichment without writing to disk
uv run python scripts/enrich_visa_rules.py --destination "Thailand" --dry-run
```

### Interactive Python Usage

You can import and use the domain models and tools directly in Python:

```bash
uv run python
```

```python
from datetime import date
from src.models import (
    BudgetMode,
    DateMode,
    TravelScope,
    TravelStyle,
    TripBudget,
    TripContext,
    TripDates,
    TripParty,
)
from src.tools import (
    calculate_budget_breakdown,
    convert_to_inr,
    get_airport,
    get_country,
    get_visa_rule,
    get_weather_forecast,
    search_transport,
    search_web,
)

# 1. Airport Lookup
delhi = get_airport("DEL")
print(f"Airport: {delhi.name}, City: {delhi.municipality}")

# 2. Country & Schengen Check
france = get_country("FR")
print(f"Country: {france.name}, Schengen: {france.is_schengen}")

# 3. Enriched Visa Rule
visa = get_visa_rule("UZ")
print(f"Destination: {visa.destination}, Best Option: {visa.selected_option.visa_type}")

# 4. Constructing Immutable Domain Models (Phase 5)
trip = TripContext(
    origin="BOM",
    destinations=["DXB"],
    scope=TravelScope.INTERNATIONAL,
    dates=TripDates(
        mode=DateMode.EXACT,
        start_date=date(2026, 11, 10),
        end_date=date(2026, 11, 17),
    ),
    party=TripParty(adults=2, children=0),
    budget=TripBudget(
        mode=BudgetMode.TOTAL,
        amount_inr=250000.0,
    ),
    travel_style=TravelStyle.COMFORT,
)
print(f"Trip Context: {trip.origin} -> {trip.destinations}, Party: {trip.party.total_count}")

# 5. Deterministic Budget Math
breakdown = calculate_budget_breakdown(
    user_budget=150000.0,
    expenses={"flights": 45000.0, "hotels": 35000.0, "activities": 15000.0},
    num_travelers=2,
    num_days=5,
    contingency_percent=10.0,
)
print(f"Total: ₹{breakdown.total_with_buffer}, Status: {breakdown.variance.status}")

# 6. Deterministic Forex Conversion
inr_cost = convert_to_inr(120.0, "USD")
print(
    f"Converted: ₹{inr_cost.converted_amount} (Rate: {inr_cost.exchange_rate}, Estimated: {inr_cost.is_estimated})"
)

# 7. Multi-Tier Weather Forecast
weather = get_weather_forecast(latitude=35.6762, longitude=139.6503, days=5, destination="Tokyo")
print(f"Weather: {weather.summary} (Provider: {weather.provider})")

# 8. Resilient Multi-Tier Web Search
search_res = search_web("japan visa for indian citizens", max_results=3)
print(f"Search: {search_res.total_results} results via {search_res.provider_used}")

# 9. Multi-Tier Transport & Route Search
transport_res = search_transport(origin="DEL", destination="BOM", travel_date="2026-10-15")
print(f"Transport: {transport_res.total_found} options via {transport_res.provider_used}")
```

---

## 13. Testing

Safarnama adheres to a **fixture-first testing philosophy**. All unit tests must be 100% deterministic, offline, and require zero external API keys or live network requests.

### Executing Tests

```bash
# Run the entire test suite (587 passing tests)
uv run pytest

# Run tests with verbose output
uv run pytest tests/ -v

# Run API layer test suite (10 tests)
uv run pytest tests/unit/test_api.py

# Run domain model test suite (89 tests)
uv run pytest tests/unit/test_domain_models.py

# Run intake node test suite (21 tests)
uv run pytest tests/unit/test_intake_node.py

# Run visa node test suite (20 tests)
uv run pytest tests/unit/test_visa_node.py

# Run tool-specific test suites
uv run pytest tests/unit/test_calculator.py
uv run pytest tests/unit/test_forex.py
uv run pytest tests/unit/test_weather.py
uv run pytest tests/unit/test_web_search.py
uv run pytest tests/unit/test_transport.py
uv run pytest tests/unit/test_hotels.py
uv run pytest tests/unit/test_places.py
uv run pytest tests/unit/test_fallback_estimator.py
uv run pytest tests/unit/test_static_data.py
```

### Code Style & Quality

The project enforces strict Ruff linting and formatting standards:

```bash
# Run linter checks
uv run ruff check .

# Check formatting without modifying files
uv run ruff format --check .

# Auto-format code
uv run ruff format .
```

---

## 14. Static Data Layer

Safarnama maintains four static datasets in `data/static/`:

1. `airports.json`: 3,244 commercial passenger airports filtered for `large_airport` or `medium_airport` with scheduled passenger service and an active IATA code.
2. `countries.json`: 250 sovereign countries and dependencies containing currencies, official languages, timezones, Schengen membership flags, and driving orientations.
3. `visa_rules.json`: Baseline visa requirements for Indian passport holders across 199 global destinations.
4. `visa_rules_enriched.json`: Multi-pathway visa records enriched with verified application fees (in INR), allowed stay durations, entry restrictions, and documentation requirements.

### Ingestion Behavior

- Ingestion is executed on-demand via scripts in `scripts/`.
- **Fault-Tolerant Preservation**: If a network request fails during ingestion, existing static datasets are preserved and never overwritten with partial or empty data.
- **Decoupled Architecture**: `fetch_visa_rules.py` owns `visa_rules.json`; `enrich_visa_rules.py` owns `visa_rules_enriched.json`. Neither script modifies the other's file.

---

## 15. External Integrations & Providers

Safarnama accesses external services through strict tool interfaces with fallback mechanisms:

| Provider | Purpose | Tool File | Fallback & Resilience Strategy |
|---|---|---|---|
| **Forex Providers** | Forex conversion | `src/tools/forex.py` | 24h cache $\rightarrow$ fixture mode $\rightarrow$ Open Access (`open.er-api.com`) $\rightarrow$ FawazAhmed CDN mirror $\rightarrow$ Frankfurter ECB rates $\rightarrow$ authenticated tier $\rightarrow$ offline table of ~40 currencies. |
| **Weather Providers** | Meteorological forecast | `src/tools/weather.py` | 3h cache $\rightarrow$ fixture mode $\rightarrow$ Open-Meteo 16-day forecast $\rightarrow$ wttr.in fallback $\rightarrow$ OpenWeatherMap 5-day fallback $\rightarrow$ offline seasonal climate baseline heuristic. |
| **Web Search Providers** | Travel & general search | `src/tools/web_search.py` | 1h cache $\rightarrow$ fixture mode $\rightarrow$ Tavily Search API $\rightarrow$ DuckDuckGo Open Access $\rightarrow$ Firecrawl Search API $\rightarrow$ offline search fixture. |
| **Transport Providers** | Route, flight & train search | `src/tools/transport.py` | 1h cache $\rightarrow$ fixture mode $\rightarrow$ SerpApi Google Flights (Tier 0 live fares & schedules) $\rightarrow$ Sky Scraper & Flights Sky API $\rightarrow$ Aviationstack live schedule API $\rightarrow$ Indian Railways IRCTC API $\rightarrow$ transport.rest European rail $\rightarrow$ live web search fallback $\rightarrow$ distance & speed physics engine with seasonal demand multipliers and universal Google Flights deep links. |
| **Hotel Providers** | Lodging & accommodation search | `src/tools/hotels.py` | 1h cache $\rightarrow$ fixture mode $\rightarrow$ SerpApi Google Hotels $\rightarrow$ RapidAPI Booking.com $\rightarrow$ OpenStreetMap / Nominatim $\rightarrow$ live web search fallback $\rightarrow$ deterministic location heuristic. |
| **Places & Dining Providers** | POI attractions & dining discovery | `src/tools/places.py` | 1h cache $\rightarrow$ fixture mode $\rightarrow$ SerpApi Google Maps $\rightarrow$ OpenStreetMap / Nominatim $\rightarrow$ live web search fallback $\rightarrow$ curated category heuristic. |
| **REST Countries v5** | Country metadata | `scripts/fetch_country_profiles.py` | On-demand script; outputs preserved in `data/static/countries.json`. |
| **OurAirports** | Airport directory | `scripts/fetch_airports.py` | Source CSV fetched and saved to `data/static/airports.json`. |
| **Passport Index** | Visa baseline | `scripts/fetch_visa_rules.py` | Positional join of dual CSVs saved to `data/static/visa_rules.json`. |
| **Tavily Search** | Visa research | `scripts/enrich_visa_rules.py` | Dedicated key support, fallbacks, and single-destination querying. |
| **Google Gemini** | Structured visa extraction | `scripts/enrich_visa_rules.py` | Native JSON schema enforcement with automated fallback across 4 model tiers on 429/503 errors. |

---

## 16. AI & LLM Anti-Hallucination Guardrails

Safarnama prevents LLM hallucinations through strict architectural boundaries:

```text
┌───────────────────────────────────────┬───────────────────────────────────────┐
│        WHAT THE LLM MAY DO            │      WHAT DETERMINISTIC CODE DOES     │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ • Reason over validated tool outputs  │ • All arithmetic additions and splits │
│ • Evaluate itinerary sequencing       │ • Currency conversions & forex rates  │
│ • Synthesize engaging travel narratives│ • Date math, duration & buffer math  │
│ • Suggest activity pacing & tags      │ • Pydantic contract & schema validation│
│ • Provide ballpark cost estimates     │ • Hard constraint validation          │
│   (ONLY when live data is missing     │ • O(1) in-memory dataset lookups      │
│   and tagged is_estimated=True)       │ • Fallback cascade execution          │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

### Prohibited LLM Behaviors
- **No arithmetic**: An LLM is never allowed to sum costs or compute budget variances.
- **No fabricated visa policies**: International entry requirements must come from verified static records or live verified research.
- **No invented travel entities**: The LLM may not invent airlines, non-existent flights, or fake hotels.
- **No constraint relaxation**: Must-visit destinations or user budget ceilings cannot be silently discarded.

---

## 17. Data Reliability & Provenance

To ensure users and downstream nodes can trust travel information:
- **`is_estimated` Flag**: Every financial item carries an explicit boolean flag. Confirmed quotes from tools or baseline lookups have `is_estimated=False`. Fallback calculations or rates carry `is_estimated=True`.
- **Source Attribution**: Enriched visa options and external research items store an array of source URLs.
- **Typed Exception Hierarchy**: The codebase provides granular error types (e.g., `AirportNotFoundError`, `InvalidAmountError`, `UnsupportedCurrencyError`) rather than generic `Exception` catches.

---

## 18. Budget & Calculation Rules

Financial calculations follow strict rules defined in `src/tools/calculator.py`:
- All currency values are calculated using `decimal.Decimal`.
- Rounding follows `ROUND_HALF_UP` to two decimal places.
- Budget breakdowns track distinct cost categories:
  1. `transport` (flights, trains, transfers)
  2. `accommodation` (hotels, stays)
  3. `food` (meals and dining)
  4. `activities` (entry tickets, tours)
  5. `visa` (visa application fees)
  6. `miscellaneous` (shopping, local transit)
  7. `contingency` (user-defined percentage buffer, default 10–15%)
- Variances are classified into `UNDER_BUDGET`, `EXACT`, or `OVER_BUDGET`.

---

## 19. Frontend Web Application (Batch 3 Complete)

The Safarnama web client lives in `frontend/`, constructed as an editorial travel planning interface faithfully aligned with the approved Stitch project **`Safarnama`** (`projects/12901504223215830628`).

### Architecture & Tech Stack:
- **Core Framework**: Vite 8 + React 19 + TypeScript + Tailwind CSS
- **Package Manager**: `pnpm` exclusively
- **Typography & Icons**: Google Fonts (`Plus Jakarta Sans` for geometric structural headings, `Inter` for utilitarian micro-legibility), Google Material Symbols Outlined
- **Color Identity**: Light-mode editorial canvas (`#FFFDF8`), elevated card surfaces (`#FFFFFF`), Safarnama Saffron (`#E87524`), and Deep Maroon accents (`#7A2E2E`)
- **State Management**: Centralized `TripPlanningContext` with full bidirectional state retention across navigation steps
- **Routing**: URL-addressable History API routes (`/planner/trip-details`, `/planner/destinations`, `/planner/preferences`, `/planner/budget`, `/planner/review`, `/planner/progress`, `/trip/overview`) with back/forward synchronization; `/trip/itinerary` is reserved for Batch 4 behind an explicit boundary state
- **Persistence**: Versioned browser-local storage restoring the wizard draft across direct loads, refreshes, and navigation, plus localStorage key `safarnama.itinerary.v1` preserving the generated `FinalItinerary` dossier

### Batch 1 Implemented Screens:
1. **Screen 1: Welcome / Landing Screen**
   - Brand header with official logo and primary CTAs.
   - Editorial hero section with travel journal flat-lay visual and floating journey badge indicators.
   - 6-card bento architecture showcasing smart itineraries, transport routing, stays, weather hazards, visa rules, and budget reconciliation.
   - Curated preview circuits (Ladakh Pass, Kyoto Autumn Trail, Amalfi Coast) launching directly into the planning workflow.
2. **Screen 2: Trip Details**
   - 5-step progress stepper with active glow indicator.
   - **Origin Autocomplete**: Search and select from 14 major Indian origin airports with full IATA airport codes.
   - **Destination Search**: Autocomplete across preconfigured circuits and global regions with quick inspiration chips.
   - **Interactive Date Picker**: Editorial date typography (`Sat, Oct 18` / `Tue, Oct 28`) triggering native accessible calendar dialogs (`showPicker()`) without digit clipping.
   - **Synchronized Leg Preferences**: Morning, Afternoon, and Evening leg time cycling that automatically synchronizes the year label with the selected calendar dates (e.g. selecting January 2027 immediately updates the leg button to `2027 • Evening leg`).
   - **Static Data Destination Auto-Population**: Real-time autocomplete powered by static datasets covering all 250 sovereign countries and all 36 Indian States and Union Territories with instant visa verdicts and seasonal climate summaries.
   - **Real-Time Badges**: Dynamic Seasonal Weather Quality Badge (`getSeasonDescription`) and Visa Guidance Badge (`getVisaVerdict`) adapting live as destinations and dates change.
   - **Party Dynamics**: Solo, Couple, Family, and Friends Group buttons paired with traveler counter steppers.
3. **Screen 3: Destinations & Route Sequence**
   - **Dynamic Route Seeding**: Automatically seeds stops matching any chosen domestic state/UT or international country (e.g. Norway seeds Oslo, Flåm, Bergen, Tromsø; Rajasthan seeds Jaipur, Jodhpur, Udaipur, Jaisalmer).
   - **Stop Night Steppers**: `[ - ] X nights [ + ]` counters allowing per-stop allocation.
   - **Duration Reconciliation Engine**: Real-time comparison banner alerting to differences between allocated stop nights and overall trip duration, featuring one-click synchronization.
   - **Route Sequence Timeline**: Drag-free reorder controls (up/down), stop removal, and custom destination insertion with automatic transit connector recalculation.
   - **Curated Suggestions**: Destination-filtered attractions with "+ Add Stop" and "Add as Day Trip" actions.

### Batch 2 Implemented Screens:
4. **Screen 4: Travel Preferences** (`/planner/preferences`)
   - Backend-aligned travel style (`BUDGET`, `COMFORTABLE`, `PREMIUM`, `LUXURY`) and pace (`RELAXED`, `BALANCED`, `PACKED`) selection.
   - Unique supported experience interests selection.
   - Source-backed named attractions for active route cities (Tavily + Gemini structured extraction catalog).
   - Saved values that no longer match after trip edits are flagged and block continuation until corrected.
5. **Screen 5: Budget** (`/planner/budget`)
   - INR target with `TOTAL`/`PER_PERSON` mode and ₹1,000 minimum.
   - No live pricing or invented provider API.
6. **Screen 6: Review & Confirm** (`/planner/review`)
   - Ordered stops/nights, origin/destination, travelers/dates, preferences, budget, section edit routes, full-draft validation, and backend-shaped `PlanRequestDraft` mapper.
   - Infant counts surfaced as unsupported by the current request contract instead of dropped.
   - Confirmation hands off to the Batch 3 planning flow (`/planner/progress`).

### Batch 3 Implemented Screens:
- **Screen 8: Trip Planning Progress** (`/planner/progress`)
   - 7-stage continuous synthesis timeline with live indicators, completed checks, elapsed run timer, and stage telemetry tags.
   - Real-time SSE consumer for `POST /api/v1/plan/stream` with `simulatePlanningStream` fallback for offline/dev/testing, plus clean abort/cancel preserving draft inputs.
   - Blueprint banner (corridor progression, seasonal badge, party, duration, dossier run badge), route alignment & telemetry visualizer, and `View Full Itinerary` handoff to `/trip/overview`.
- **Screen 9: Trip Overview Dossier** (`/trip/overview`)
   - Editorial dossier header (run tag, departure readiness pulse, metadata pills), cinematic 21:9 hero, Curator's Note, and Pacing & Rhythm Index gauges.
   - 3-column route corridor cards, 6-card trip snapshot matrix, budget leeway breakdown (Stays/Transit/Experiences/Dining/Contingency), highlights gallery, and regional microclimate & packing forecasts.
   - Actions: *View Full Itinerary* (`/trip/itinerary`, Batch 4 boundary), *Edit Route & Preferences* (draft-preserving), and *Export & Share Dossier*.
   - `FinalItinerary` state from `frontend/src/types/itinerary.ts` rendered via `TripPlanningContext` extensions with offline `synthesizeItineraryFromDraft()` fallback.

### Running Frontend Locally:
```bash
cd frontend
pnpm install
pnpm dev
```
The application will be live at `http://localhost:5173/`.

### Running Tests & Linting:
```bash
cd frontend
pnpm test -- --run   # 30 unit/flow tests in Vitest
pnpm build           # TypeScript typecheck & production bundle
pnpm lint            # Oxlint static analysis
```

---

## 20. Contributing & Engineering Rules

When contributing code or modifying this repository:

1. **Package Management**:
   - Use `uv add <package>` for runtime dependencies.
   - Use `uv add --dev <package>` for development dependencies.
   - **Never use `pip`**.
2. **Frontend Management**:
   - Use `pnpm` exclusively for frontend operations (never `npm` or `yarn`).
3. **Incremental Progress**:
   - Implement one capability or tool at a time.
   - Write comprehensive unit tests with offline mock fixtures.
   - Run `uv run pytest` and `uv run ruff check .` before committing.
   - Document changes in `project_docs/03-reference/memory.md`.
4. **Preserve Architectural Invariants**:
   - Never use floating-point math for currencies.
   - Keep import root as `src.*` (configured in `pyproject.toml`).
   - Do not implement future phases speculatively.

---

## 21. Instructions for AI Coding Agents

If you are an AI assistant (Claude Code, Cursor, Copilot, Codex, Antigravity) picking up this project:

1. **Read Project Documentation First**:
   Before modifying or adding code, inspect:
   - `project_docs/03-reference/memory.md` — The living implementation status and current task handoff.
   - `project_docs/00-product/prd.md` — Intended product requirements.
   - `project_docs/00-product/architecture.md` — Target system architecture.
   - `project_docs/03-reference/rules.md` — Engineering constraints and principles.
   - `project_docs/01-planning/phases.md` — Granular implementation roadmap.
   - `project_docs/00-product/design.md` — Visual guidelines and color tokens.
2. **Inspect Existing Code**:
   Do not assume documented features are implemented. Check `src/` and `tests/` directly.
3. **Follow the Active Phase**:
   Identify the current phase in `project_docs/03-reference/memory.md`. Work only on the requested task. Do not implement future phases without explicit instructions.
4. **Verify Your Work**:
   Always run:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```
5. **Update Memory**:
   Before completing your turn, update `project_docs/03-reference/memory.md` with:
   - Completed functionality
   - Test counts and results
   - Known limitations or open issues
   - Next recommended step

---

## 22. Visual & Design Identity

The visual foundation for Safarnama is detailed in `project_docs/00-product/design.md`:

- **Design Vision**: Modern Indian travel companion with a warm sense of place, blending contemporary digital travel journal aesthetics with Indian cultural warmth.
- **Theme**: Light theme canvas optimized for reading dense itineraries, schedule cards, and budget breakdowns.
- **Primary Brand Color**: **Safarnama Saffron** (`#E87524`) — energetic, warm, and distinctly travel-focused.
- **Typography & Layout**: Clean, highly readable typography designed for scan-friendly schedules, transparent cost cards, and structured trade-off comparisons.

---

## 23. License

```text
License: Not yet specified.
```
