# Safarnama — Autonomous Multi-Agent Travel Planner

> A constraint-aware, multi-agent travel planning system designed for Indian travelers planning domestic and international trips, combining deterministic calculations, verified static datasets, external travel tools, and structured AI reasoning.

---

## 1. Project Status

```text
Status: In Active Development
Current Phase: Phase 3 — External Tool Layer (In Progress)
Current Milestone: Tool 1 (Calculator) & Tool 2 (Forex) complete; Tools 3–8 pending
Test Suite: 193 unit tests passing (100% offline, zero network reliance in tests)
Code Quality: 100% compliant with Ruff linting and formatting
```

Safarnama is being built in small, verified, test-driven phases. The project is currently in the external tool development stage. **It is not yet production-ready**, nor is the end-to-end multi-agent orchestration or frontend interface implemented.

| Phase | Description | Status |
|---|---|---|
| **Phase 0** | Project Foundation & Packaging | **Complete** |
| **Phase 1** | Static Data Ingestion (Airports, Countries, Visa Rules) | **Complete** |
| **Phase 2** | Static Data Access Layer & In-Memory Store | **Complete** |
| **Phase 3** | External Tool Layer (Calculator, Forex, Weather, Search, Places) | **In Progress** (Tools 1 & 2 done) |
| **Phase 4** | API Layer (FastAPI endpoints & contracts) | Planned |
| **Phase 5** | Domain Models (Travel state, Itinerary, Budget schemas) | Planned |
| **Phase 6** | Individual Planning Functions | Planned |
| **Phase 7** | LangGraph Orchestration & Multi-Agent Graph | Planned |
| **Phase 8** | Budget Engine & Optimization | Planned |
| **Phase 9** | Complete Planning Workflow & Verification | Planned |
| **Phase 10** | Web Frontend (Vite / React) | Planned |
| **Phase 11** | Integration, Streaming & Hardening | Planned |

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

- **Global Airport Directory**: 3,244 commercial passenger airports worldwide loaded into memory and indexed by IATA code, city, and ISO country code.
- **Country Intelligence & Profiles**: 250 sovereign countries and territories indexed by ISO-2, ISO-3, and English names, including currencies, languages, capitals, Schengen membership, driving sides, and coordinates.
- **Indian Passport Visa Regulations**:
  - Baseline rules for 199 international destinations categorized into standardized regimes (`VISA_FREE`, `VISA_ON_ARRIVAL`, `E_VISA`, `STICKER_VISA_REQUIRED`).
  - Enriched multi-option tourist pathways for 199 destinations with exact visa fees in INR, stay limits, application requirements, and source references.
- **High-Performance In-Memory Query Layer**: Fast, zero-disk-I/O cached lookups with custom typed exceptions and intelligent IST time difference calculations.
- **Deterministic Budget Calculator**:
  - Exact financial arithmetic via Python `Decimal` with `ROUND_HALF_UP` rounding to 2 decimal places.
  - Expense category summation (transport, hotels, food, activities, visa, misc, contingency buffer).
  - Per-person splits, daily averages, and room requirement calculations.
  - Budget variance analysis categorizing outcomes as `UNDER_BUDGET`, `EXACT`, or `OVER_BUDGET`.
- **Deterministic Forex Currency Converter**:
  - Multi-tier conversion to INR: In-Memory Cache (24h TTL) $\rightarrow$ Fixture Mode $\rightarrow$ Live Open-Access Tier $\rightarrow$ Live Authenticated Tier $\rightarrow$ Built-in Offline Baseline Table (~40 global currencies).
  - Explicit provenance and reliability tracking with `is_estimated` flags.
- **100% Offline Test Harness**: Comprehensive test suite with zero live API calls during unit testing.

### Planned Capabilities (Future Phases)

- **Weather-Aware Planning Tool** (Open-Meteo integration) — *Phase 3*
- **Live Travel Research Tool** (Tavily search wrapper) — *Phase 3*
- **Flight & Route Adapter** — *Phase 3*
- **Hotel Discovery Adapter** — *Phase 3*
- **Attractions & Dining Discovery Adapter** — *Phase 3*
- **LLM Fallback Estimator** (Gemini structured cost estimation when live pricing is missing) — *Phase 3*
- **LangGraph Multi-Agent Architecture** (Intake, Visa, Logistics, Experience, Optimizer nodes) — *Phase 7*
- **FastAPI Backend Server & SSE Streaming** — *Phase 4 & 11*
- **Warm Indian-Inspired Web Frontend** (Vite / React) — *Phase 10*

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
```

### Current Implementation vs Planned Components

```text
IMPLEMENTED & VERIFIED                     PLANNED (Upcoming Phases)
┌─────────────────────────────────┐        ┌───────────────────────────────┐
│ src/tools/static_data.py        │        │ src/api/                      │
│ - In-Memory Singleton Store     │        │ - FastAPI endpoints & models  │
│ - 3,244 Airports (IATA/City)    │        ├───────────────────────────────┤
│ - 250 Countries (ISO/Time/Bloc) │        │ src/graph/ & src/nodes/       │
│ - 199 Visa Rules & Enriched     │        │ - LangGraph state & nodes     │
├─────────────────────────────────┤        ├───────────────────────────────┤
│ src/tools/calculator.py         │        │ src/tools/ (Pending)          │
│ - Decimal Arithmetic            │        │ - weather.py (Open-Meteo)     │
│ - Category Sum & Buffer         │        │ - web_search.py (Tavily)      │
│ - Budget Variance Analysis      │        │ - transport.py (Routes)       │
├─────────────────────────────────┤        │ - hotels.py (Accommodations)  │
│ src/tools/forex.py              │        │ - places.py (Attractions/Food)│
│ - Multi-tier Currency Engine    │        │ - fallback_estimator.py (LLM) │
│ - 40+ Offline Rates + Live Tiers│        ├───────────────────────────────┤
│ - INR Conversion with Provenance│        │ Frontend                      │
└─────────────────────────────────┘        │ - Vite / React / pnpm UI      │
                                           └───────────────────────────────┘
```

---

## 6. Technology Stack

### Current Technologies

- **Python**: `>=3.11` (developed and tested with Python 3.11–3.14)
- **Package & Dependency Manager**: [`uv`](https://docs.astral.sh/uv/) (strictly required; `pip` is prohibited)
- **Build System**: `hatchling` (configured with `src` package layout)
- **Data Validation & Schemas**: [`pydantic>=2.13.5`](https://docs.pydantic.dev/) (Pydantic v2 domain models)
- **Environment Management**: [`python-dotenv>=1.2.3`](https://github.com/theskumar/python-dotenv)
- **AI SDK**: [`google-genai>=2.25.0`](https://github.com/googleapis/python-genai) (Google Gemini API client)
- **Testing**: [`pytest>=9.1.1`](https://docs.pytest.org/)
- **Linting & Formatting**: [`ruff>=0.16.8`](https://docs.astral.sh/ruff/)

### Planned Technologies (Future Phases)

- **Workflow Orchestration**: `langgraph` (Phase 7)
- **Web API Framework**: `fastapi` & `uvicorn` (Phase 4)
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
│   ├── api/                  # FastAPI routers and endpoints (Phase 4 scaffold)
│   ├── graph/                # LangGraph state graph definitions (Phase 7 scaffold)
│   ├── models/               # Canonical Pydantic domain models
│   │   ├── airport.py        # Airport model
│   │   ├── country.py        # CountryProfile, CurrencyInfo, LanguageInfo, Coordinates
│   │   └── visa.py           # BaseVisaRule, VisaOption, EnrichedVisaRecord
│   ├── nodes/                # LangGraph agent planning nodes (Phase 7 scaffold)
│   ├── prompts/              # System prompts and prompt templates (Phase 7 scaffold)
│   └── tools/                # Deterministic utilities and external tool wrappers
│       ├── calculator.py     # Phase 3 Tool 1: Deterministic budget calculator
│       ├── forex.py          # Phase 3 Tool 2: Multi-tier currency converter
│       └── static_data.py    # Phase 2: In-memory indexed static data store
└── tests/                    # Automated test suite
    ├── conftest.py           # Shared pytest fixtures
    ├── integration/          # Integration test suite (Phase 11 scaffold)
    └── unit/                 # 193 passing offline unit tests
        ├── test_calculator.py
        ├── test_enrich_visa_rules.py
        ├── test_fetch_airports.py
        ├── test_fetch_country_profiles.py
        ├── test_fetch_visa_rules.py
        ├── test_forex.py
        ├── test_project_foundation.py
        └── test_static_data.py
```

---

## 8. Development Phases & Roadmap

Safarnama uses an incremental delivery roadmap defined in `project_docs/phases.md`. Each phase must be fully implemented, tested, and verified before the next begins.

```text
Phase 0: Foundation [COMPLETED]
      ↓
Phase 1: Static Data Ingestion [COMPLETED]
      ↓
Phase 2: Static Data Tools [COMPLETED]
      ↓
Phase 3: External Tool Layer [IN PROGRESS: Tools 1 & 2 done; Tools 3–8 pending]
      ↓
Phase 4: API Layer [PLANNED]
      ↓
Phase 5: Domain Models [PLANNED]
      ↓
Phase 6: Planning Functions [PLANNED]
      ↓
Phase 7: LangGraph Orchestration [PLANNED]
      ↓
Phase 8: Budget Optimization [PLANNED]
      ↓
Phase 9: Complete Planning Workflow [PLANNED]
      ↓
Phase 10: Web Frontend [PLANNED]
      ↓
Phase 11: Integration & Hardening [PLANNED]
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
- **Phase 3 (External Tool Layer — Active)**:
  - **Tool 1: Calculator Tool (`src/tools/calculator.py`)**: Exact decimal arithmetic, expense categorization, buffer calculations, and budget variance evaluation. 56 unit tests.
  - **Tool 2: Forex Tool (`src/tools/forex.py`)**: Deterministic currency conversion to INR with 5-tier fallback and 40+ built-in offline currency rates. 17 unit tests.

### Immediate Next Milestone

- **Phase 3, Tool 3: Weather Tool (`src/tools/weather.py`)**: Implement Open-Meteo weather forecast wrapper with offline fixtures (`data/fixtures/mock_weather.json`), historical climate fallback, and unit tests.

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

| Variable | Required For | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | Runtime Planning | Primary Gemini planning LLM key (Google AI Studio). |
| `FALLBACK_LLM_API_KEY` | Runtime Planning | Dedicated key for fallback cost estimations when live tools lack pricing. |
| `FALLBACK_LLM_MODEL` | Runtime Planning | Model name for fallback estimations (e.g., `gemini-2.5-flash`). |
| `GEMINI_ENRICHMENT_API_KEY` | Ingestion Script | Key used by `scripts/enrich_visa_rules.py` for structured visa synthesis. |
| `GEMINI_ENRICHMENT_MODEL` | Ingestion Script | Optional model override (default: `gemini-2.5-flash-lite`). |
| `TAVILY_VISA_ENRICHMENT_API_KEY` | Ingestion Script | Dedicated Tavily key for web research in `scripts/enrich_visa_rules.py`. |
| `TAVILY_API_KEY` | Ingestion / Runtime | General Tavily search API key. |
| `REST_COUNTRIES_API_KEY` | Ingestion Script | API key for REST Countries v5 ingestion (`scripts/fetch_country_profiles.py`). |
| `EXCHANGERATE_API_KEY` | Forex Tool | Optional key for ExchangeRate-API. If omitted, open tier and offline rates are used. |
| `SAFARNAMA_USE_FIXTURES` | Testing / Dev | When set to `true`, forces tools to load mock fixtures from `data/fixtures/`. |

> **Security Notice**: Never commit `.env` or real API keys to source control.

---

## 12. Running the Project

Because the project is currently in Phase 3, the runtime consists of static data ingestion scripts, the deterministic tool layer, and automated tests.

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

### Interactive Usage of Implemented Tools

You can explore the implemented tools in Python:

```bash
uv run python
```

```python
from src.tools import (
    get_airport,
    get_country,
    get_visa_rule,
    calculate_budget_breakdown,
    convert_to_inr,
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

# 4. Deterministic Budget Math
breakdown = calculate_budget_breakdown(
    user_budget=150000.0,
    expenses={"flights": 45000.0, "hotels": 35000.0, "activities": 15000.0},
    num_travelers=2,
    num_days=5,
    contingency_percent=10.0,
)
print(f"Total: ₹{breakdown.total_with_buffer}, Status: {breakdown.variance.status}")

# 5. Deterministic Forex Conversion
inr_cost = convert_to_inr(120.0, "USD")
print(f"Converted: ₹{inr_cost.amount_inr} (Rate: {inr_cost.rate_used}, Estimated: {inr_cost.is_estimated})")
```

---

## 13. Testing

Safarnama adheres to a **fixture-first testing philosophy**. All unit tests must be 100% deterministic, offline, and require zero external API keys or live network requests.

### Executing Tests

```bash
# Run all unit tests
uv run pytest

# Run tests with verbose output
uv run pytest tests/ -v

# Run specific tool test suites
uv run pytest tests/unit/test_calculator.py
uv run pytest tests/unit/test_forex.py
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
| **ExchangeRate-API** | Forex conversion | `src/tools/forex.py` | 24h cache $\rightarrow$ fixture mode $\rightarrow$ open tier (`open.er-api.com`) $\rightarrow$ authenticated tier $\rightarrow$ offline table of ~40 currencies. |
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
