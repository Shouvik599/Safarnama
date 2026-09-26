# Safarnama — Autonomous Multi-Agent Travel Planner

> A constraint-aware, multi-agent travel planning system designed for Indian travelers planning domestic and international trips, combining deterministic calculations, verified static datasets, external travel tools, and structured AI reasoning.

---

## 1. Project Status

```text
Status: In Active Development
Current Phase: Phase 8 — Logistics Functionality (Complete)
Current Milestone: Phase 3 (8/8 Tools Complete), Phase 4 (FastAPI Layer & SSE Streaming Complete), Phase 5 (Domain Models Complete), Phase 6 (Intake Complete), Phase 7 (Visa Complete), Phase 8 (Logistics Functionality Complete)
Test Suite: 414 unit tests passing (100% offline, zero network reliance in tests)
Code Quality: 100% compliant with Ruff linting and formatting
```

Safarnama is being built in small, verified, test-driven phases. The project has completed static data ingestion, static data access layer, the external tool layer (all 8 tools), the FastAPI API layer, the core domain models, the intake planning node, the visa planning node, and the logistics planning node. **It is not yet production-ready**, nor is the end-to-end multi-agent orchestration or frontend interface implemented.

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Project Foundation & Packaging | **Complete** |
| **Phase 1** | Static Data Ingestion (Airports, Countries, Visa Rules) | **Complete** |
| **Phase 2** | Static Data Access Layer & In-Memory Store | **Complete** |
| **Phase 3** | External Tool Layer (Calculator, Forex, Weather, Search, Transport, Hotels, Places, Estimator) | **Complete** |
| **Phase 4** | API Foundation (FastAPI endpoints, validation & SSE streaming) | **Complete** |
| **Phase 5** | Domain Models (Trip context, Itinerary, Logistics, Visa verdict, Budget schemas) | **Complete** |
| **Phase 6** | Intake Functionality (Sanitization, Origin/Destination Resolution, Scope Reconciliation, Initial State) | **Complete** |
| **Phase 7** | Visa Functionality (Static Baseline + Live Verification, Schengen Optimization, Verdict Synthesizer) | **Complete** |
| **Phase 8** | Logistics Functionality (Transport Legs & Hotel Stays Planning) | **Complete** |
| **Phase 9** | Experience Functionality (Attractions, Dining, Weather-Aware Pacing) | Planned |
| **Phase 10** | Deterministic Budget Engine (Category summation, buffer, variances) | Planned |
| **Phase 11** | Optimizer Functionality (Budget trade-offs, constraint satisfaction) | Planned |
| **Phase 12** | LangGraph Orchestration (StateGraph, parallel nodes, state reduction) | Planned |
| **Phase 13** | First Complete Vertical Slice (End-to-end domestic itinerary generation) | Planned |
| **Phase 14** | International Vertical Slice (End-to-end international with visa integration) | Planned |
| **Phase 15** | Flexible Dates (Candidate date window optimization) | Planned |
| **Phase 16** | Budget Conflict & Human Decision Flow (Interactive trade-off resolution) | Planned |
| **Phase 17** | API Streaming (Real-time SSE event emission from LangGraph) | Planned |
| **Phase 18** | Frontend (Interactive web user interface) | Planned |
| **Phase 19** | End-to-End Test Matrix (Full regression and test scenarios) | Planned |
| **Phase 20** | Production Hardening (Observability, rate limits, deployment) | Planned |

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
  - **Transport Tool (`src/tools/transport.py`)**: Multi-tier route search (Sky Scraper, Flights Sky, IRCTC rail, European rail, web search fallback, distance physics engine).
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
- **100% Offline Test Harness**: 427 unit tests running completely offline with zero network reliance or live API key dependencies.

### Planned Capabilities (Future Phases)

- **Deterministic Budget Engine** (Category summation, buffer, variances) — *Phase 10*
- **Optimizer Functionality** (Budget trade-offs, constraint satisfaction) — *Phase 11*
- **LangGraph Multi-Agent Architecture** (StateGraph, conditional routing, state reduction) — *Phase 12*
- **First Complete Vertical Slice** (End-to-end domestic itinerary generation) — *Phase 13*
- **International Vertical Slice** (End-to-end international with visa integration) — *Phase 14*
- **Flexible Dates Optimization** (Candidate date window optimization) — *Phase 15*
- **Budget Conflict & Human Decision Flow** (Interactive trade-off resolution) — *Phase 16*
- **API Streaming Engine** (Real-time SSE event emission from LangGraph) — *Phase 17*
- **Warm Indian-Inspired Web Frontend** (Vite / React / TypeScript / pnpm) — *Phase 18*
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
IMPLEMENTED & VERIFIED (Phases 0–7)            PLANNED (Upcoming Phases)
┌─────────────────────────────────┐        ┌───────────────────────────────┐
│ src/api/                        │        │ src/nodes/                    │
│ - FastAPI endpoints, CORS & SSE │        │ - logistics_node.py           │
│ - Request/Response Pydantic     │        │ - experience_node.py          │
├─────────────────────────────────┤        │ - optimizer_node.py           │
│ src/models/                     │        ├───────────────────────────────┤
│ - trip, itinerary, logistics    │        │ src/graph/                    │
│ - visa, budget, static models   │        │ - LangGraph StateGraph        │
├─────────────────────────────────┤        │ - State transitions & routing │
│ src/nodes/                      │        ├───────────────────────────────┤
│ - intake_node.py (Intake/Res)   │        │ Frontend                      │
│ - visa_node.py (Visa/Schengen)  │        │ - Vite / React / pnpm UI      │
├─────────────────────────────────┤        └───────────────────────────────┘
│ src/tools/ (All 8 Tools)        │
│ - static_data.py (3 datasets)   │
│ - calculator.py (Decimal math)  │
│ - forex.py (Multi-tier INR)     │
│ - weather.py (Forecasts)        │
│ - web_search.py (Search)        │
│ - transport.py (Routes)         │
│ - hotels.py (Accommodations)    │
│ - places.py (Attractions/Food)  │
│ - fallback_estimator.py (LLM)   │
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

### Planned Technologies (Future Phases)

- **Workflow Orchestration**: `langgraph` (Phase 7)
- **Frontend**: Vite / React / TypeScript with `pnpm` (Phase 10)

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
│       ├── visa_rules.json   # 199 base visa rules for Indian passport holders
│       └── visa_rules_enriched.json # 199 multi-option enriched visa records
├── project_docs/             # Canonical project specifications & architectural guides
│   ├── architecture.md       # Target system architecture and node specifications
│   ├── design.md             # Visual identity and UI design tokens
│   ├── instructions.md       # Master project setup & guidelines
│   ├── memory.md             # Implementation progress snapshot and handoff record
│   ├── phases.md             # Granular phase-by-phase implementation roadmap
│   ├── prd.md                # Product Requirements Document
│   └── rules.md              # Mandatory engineering and AI assistant rules
├── scripts/                  # On-demand static data ingestion and enrichment scripts
│   ├── enrich_visa_rules.py  # Gemini + Tavily on-demand visa rule enrichment
│   ├── fetch_airports.py     # Ingests airports from ourairports-data
│   ├── fetch_country_profiles.py # Ingests country metadata from REST Countries v5
│   └── fetch_visa_rules.py   # Ingests passport visa baseline from passport-index
├── src/                      # Importable application source package (`import src.*`)
│   ├── api/                  # FastAPI routers, app factory and endpoints (Phase 4)
│   │   ├── app.py            # FastAPI app factory with CORS & exception handlers
│   │   ├── models.py         # API Request/Response schemas (Estimate, PlanPreview, etc.)
│   │   └── routes.py         # API routes (health, tools/status, estimate, preview, SSE)
│   ├── graph/                # LangGraph state graph definitions (Phase 7 scaffold)
│   ├── models/               # Canonical Pydantic v2 domain models (Phases 1–5)
│   │   ├── airport.py        # Airport model
│   │   ├── budget.py         # CostBreakdown, ContingencyConfig, BudgetVariance, BudgetBreakdown
│   │   ├── country.py        # CountryProfile, CurrencyInfo, LanguageInfo, Coordinates
│   │   ├── itinerary.py      # PointOfInterest, ActivitySlot, DayMeal, DayPlan, ExperiencePlan
│   │   ├── logistics.py      # TransportLeg, HotelStay, LogisticsPlan
│   │   ├── trip.py           # TripParty, TripDates, TripBudget, FoodPreferences, TripContext
│   │   └── visa.py           # BaseVisaRule, VisaOption, EnrichedVisaRecord, VisaVerdict
│   ├── nodes/                # LangGraph agent planning nodes (Phases 6–8)
│   │   ├── __init__.py       # Exports intake_node, visa_node, logistics_node, etc.
│   │   ├── intake_node.py    # Phase 6: Sanitization, gateway resolution, scope reconciliation
│   │   ├── logistics_node.py # Phase 8: Transport legs & hotel stays planning, room estimation
│   │   └── visa_node.py      # Phase 7: Static baseline + live policy reconciliation & verdict
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
└── tests/                    # Automated test suite
    ├── conftest.py           # Shared pytest fixtures
    ├── integration/          # Integration test suite (Phase 11 scaffold)
    └── unit/                 # 414 passing offline unit tests
        ├── test_api.py       # API endpoint, validation & SSE streaming tests
        ├── test_calculator.py
        ├── test_domain_models.py # 89 tests for trip, itinerary, logistics, visa, budget
        ├── test_enrich_visa_rules.py
        ├── test_fallback_estimator.py
        ├── test_fetch_airports.py
        ├── test_fetch_country_profiles.py
        ├── test_fetch_visa_rules.py
        ├── test_forex.py
        ├── test_hotels.py
        ├── test_intake_node.py # 21 tests for intake node, resolution, scope enforcement
        ├── test_logistics_node.py # 22 tests for logistics planning, rooms, and routes
        ├── test_places.py
        ├── test_project_foundation.py
        ├── test_static_data.py
        ├── test_transport.py
        ├── test_visa_node.py # 20 tests for visa node, semantic LLM reconciliation, static baseline
        ├── test_weather.py
        └── test_web_search.py
```

---

## 8. Development Phases & Roadmap

Safarnama uses an incremental delivery roadmap defined in `project_docs/phases.md`. Each phase must be fully implemented, tested, and verified before the next begins.

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
Phase 10: Deterministic Budget Engine [NEXT PHASE: Aggregation, Variance & Contingency]
      ↓
Phase 11: Optimizer Functionality [PLANNED]
      ↓
Phase 12: LangGraph Orchestration [PLANNED]
      ↓
Phase 13: First Complete Vertical Slice [PLANNED]
      ↓
Phase 14: International Vertical Slice [PLANNED]
      ↓
Phase 15: Flexible Dates [PLANNED]
      ↓
Phase 16: Budget Conflict & Human Decision Flow [PLANNED]
      ↓
Phase 17: API Streaming [PLANNED]
      ↓
Phase 18: Frontend [PLANNED]
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

### Immediate Next Milestone

- **Phase 10 — Deterministic Budget Engine**: Implement `src/nodes/budget_node.py` to aggregate logistics, experience, and visa cost breakdowns, evaluate contingency buffer configurations, and compute mathematical budget variances without LLM arithmetic.

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
| `SERPAPI_KEY` | 4. Travel & Lodging | Hotels & Places | Google Hotels and Google Maps search for accommodations, POIs, and dining (`src/tools/hotels.py`, `src/tools/places.py`). Fallbacks to Nominatim/OSM. |
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
# Run the entire test suite (392 passing tests)
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
| **Transport Providers** | Route, flight & train search | `src/tools/transport.py` | 1h cache $\rightarrow$ fixture mode $\rightarrow$ Sky Scraper & Flights Sky API $\rightarrow$ Indian Railways IRCTC API $\rightarrow$ transport.rest European rail $\rightarrow$ live web search fallback $\rightarrow$ distance & speed physics engine. |
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

## 19. Contributing & Engineering Rules

When contributing code or modifying this repository:

1. **Package Management**:
   - Use `uv add <package>` for runtime dependencies.
   - Use `uv add --dev <package>` for development dependencies.
   - **Never use `pip`**.
2. **Frontend Management**:
   - When the frontend is created in Phase 10, use `pnpm` exclusively (never `npm` or `yarn`).
3. **Incremental Progress**:
   - Implement one capability or tool at a time.
   - Write comprehensive unit tests with offline mock fixtures.
   - Run `uv run pytest` and `uv run ruff check .` before committing.
   - Document changes in `project_docs/memory.md`.
4. **Preserve Architectural Invariants**:
   - Never use floating-point math for currencies.
   - Keep import root as `src.*` (configured in `pyproject.toml`).
   - Do not implement future phases speculatively.

---

## 20. Instructions for AI Coding Agents

If you are an AI assistant (Claude Code, Cursor, Copilot, Codex, Antigravity) picking up this project:

1. **Read Project Documentation First**:
   Before modifying or adding code, inspect:
   - `project_docs/memory.md` — The living implementation status and current task handoff.
   - `project_docs/prd.md` — Intended product requirements.
   - `project_docs/architecture.md` — Target system architecture.
   - `project_docs/rules.md` — Engineering constraints and principles.
   - `project_docs/phases.md` — Granular implementation roadmap.
   - `project_docs/design.md` — Visual guidelines and color tokens.
2. **Inspect Existing Code**:
   Do not assume documented features are implemented. Check `src/` and `tests/` directly.
3. **Follow the Active Phase**:
   Identify the current phase in `project_docs/memory.md`. Work only on the requested task. Do not implement future phases without explicit instructions.
4. **Verify Your Work**:
   Always run:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```
5. **Update Memory**:
   Before completing your turn, update `project_docs/memory.md` with:
   - Completed functionality
   - Test counts and results
   - Known limitations or open issues
   - Next recommended step

---

## 21. Visual & Design Identity

The visual foundation for Safarnama is detailed in `project_docs/design.md`:

- **Design Vision**: Modern Indian travel companion with a warm sense of place, blending contemporary digital travel journal aesthetics with Indian cultural warmth.
- **Theme**: Light theme canvas optimized for reading dense itineraries, schedule cards, and budget breakdowns.
- **Primary Brand Color**: **Safarnama Saffron** (`#E87524`) — energetic, warm, and distinctly travel-focused.
- **Typography & Layout**: Clean, highly readable typography designed for scan-friendly schedules, transparent cost cards, and structured trade-off comparisons.

---

## 22. License

```text
License: Not yet specified.
```
