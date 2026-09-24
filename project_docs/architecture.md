# Architecture Document
# Safarnama — Autonomous Multi-Agent Travel Planner

**Document status:** V1 Architecture Definition  
**Project:** Safarnama  
**Runtime:** Python 3.11+  
**Primary orchestration:** LangGraph  
**Validation/contracts:** Pydantic v2  
**API/service:** FastAPI  
**Development approach:** Incremental, test-driven, tool-first

---

## 1. Architecture Purpose

Safarnama is a constraint-aware, multi-agent travel planning system for Indian travelers.

The architecture separates:

1. **User request and API handling**
2. **Validated planning state**
3. **LangGraph orchestration**
4. **Specialized planning nodes**
5. **External data tools/providers**
6. **Static datasets**
7. **Deterministic calculation**
8. **Fallback estimation**
9. **Testing and offline fixtures**

The system should not be implemented as one large LLM workflow.

Each responsibility should remain independently testable and replaceable.

The central architectural principle is:

> **LLMs reason over structured information; tools retrieve information; deterministic Python performs calculations; Pydantic validates contracts; LangGraph controls execution.**

---

# 2. High-Level Application Flow

The overall planning flow is:

```text
                         USER
                           │
                           ▼
                 ┌──────────────────┐
                 │  FastAPI / CLI   │
                 │ Request Intake   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   Intake Node    │
                 │ Validate/resolve │
                 │ scope + origin   │
                 └────────┬─────────┘
                          │
                 ┌────────┴─────────┐
                 │                  │
          INTERNATIONAL          DOMESTIC
                 │                  │
                 ▼                  │
          ┌──────────────┐          │
          │  Visa Node   │          │
          │ Static +     │          │
          │ Live Verify  │          │
          └──────┬───────┘          │
                 │                  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Parallel Planning│
                 └───────┬──────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
      ┌───────────────┐      ┌────────────────┐
      │ Logistics     │      │ Experience     │
      │ Node          │      │ Node           │
      │               │      │                │
      │ Transport     │      │ Attractions    │
      │ Hotels        │      │ Food           │
      │ Route data    │      │ Weather        │
      └───────┬───────┘      └───────┬────────┘
              │                      │
              └──────────┬───────────┘
                         ▼
                 ┌──────────────────┐
                 │ Optimizer Node   │
                 │ Deterministic    │
                 │ Budget Engine    │
                 └────────┬─────────┘
                          │
                 ┌────────┴─────────┐
                 │                  │
             FEASIBLE          CONFLICT
                 │                  │
                 ▼                  ▼
              OUTPUT          Optimization /
                              User decision
                                   │
                                   ▼
                            Re-plan affected
                              components
                                   │
                                   └──────► OUTPUT
```

The graph is responsible for **orchestration and routing**, not for implementing every business operation itself.

---

# 3. Request Lifecycle

## Step 1 — User submits trip requirements

The request contains structured information such as:

- Origin
- Destination(s)
- Domestic/international scope
- Adults
- Children
- Travel dates or flexible date window
- Duration or flexible duration
- Budget mode
- Budget amount
- Travel style
- Pace
- Activity preferences
- Must-visit places
- Food importance
- Dietary preferences
- Allergies
- Foods to avoid
- Previous international travel information

The API layer validates the request before passing it into the planning graph.

---

## Step 2 — Intake Node

The intake node:

- Sanitizes the request.
- Normalizes structured fields.
- Determines travel scope.
- Resolves origin against the static airport dataset.
- Resolves relevant destination gateway/city information.
- Retrieves coordinates required by downstream tools.
- Creates the initial planning state.

The intake node should not perform itinerary planning.

---

## Step 3 — Scope Routing

The graph determines whether visa planning is required.

```text
DOMESTIC
   │
   └──────────────► Parallel Planning

INTERNATIONAL
   │
   ▼
Visa Node
   │
   └──────────────► Parallel Planning
```

Domestic trips bypass visa processing.

International trips enter the visa workflow before joining the main planning branch.

---

# 4. Visa Architecture

The visa node combines a static baseline with live verification.

```text
             Visa Request
                  │
          ┌───────┴────────┐
          ▼                ▼
   Static Visa Rules   Live Search
          │                │
          └───────┬────────┘
                  ▼
          Visa Reconciliation
                  │
                  ▼
          Structured Verdict
```

## Static baseline

`data/static/visa_rules.json`

The baseline is derived from the Passport Index dataset for Indian passports.

## Live verification

The system uses a live search tool to identify recent policy changes.

The LLM may reconcile structured policy information into a Pydantic visa result, but it must not be treated as the authoritative source by itself.

## Visa fallback restriction

The fallback LLM must **not** invent:

- Visa requirements
- Eligibility rules
- Required documents
- Application procedures
- Entry restrictions
- Other authoritative visa facts

If reliable visa information cannot be obtained, the system should report the information gap rather than fabricate requirements.

---

# 5. Parallel Planning Layer

After intake and required visa processing, the system runs the major planning branches.

## Logistics Node

Responsible for:

- Main transportation
- Intercity transportation
- Accommodation discovery
- Hotel selection
- Route-related logistics
- Cost inputs for the budget engine

Transportation is planner-controlled.

Hotels are selected automatically using available live hotel/place data.

The node should use tools rather than directly embedding provider-specific API logic.

---

## Experience Node

Responsible for:

- Attractions
- Activities
- Food experiences
- Restaurant/place discovery
- Weather-aware itinerary planning
- Geographic grouping of activities
- Day-level pacing
- Local experience selection

The experience node combines curated knowledge with live place information.

Weather can cause automatic itinerary adjustments.

Example:

```text
Rain forecast
    ↓
Outdoor activity unsuitable
    ↓
Find suitable indoor alternative
    ↓
Preserve activity category / route quality
    ↓
Mark weather-driven change in output
```

---

# 6. Tool Architecture

Agents/nodes should not directly depend on individual API providers.

The preferred dependency direction is:

```text
Node / Agent
     │
     ▼
Tool Interface
     │
     ▼
Provider Adapter
     │
     ▼
External API
```

This makes providers replaceable.

Potential tool categories include:

```text
src/tools/
├── calculator.py
├── static_data.py
├── weather.py
├── web_search.py
├── forex.py
├── flights.py              # future/provider-specific implementation
├── hotels.py               # future/provider-specific implementation
├── places.py               # future/provider-specific implementation
└── fallback_estimator.py   # dedicated fallback LLM
```

The initial repository structure does not need every future tool implemented immediately.

---

# 7. Tool Fallback Strategy

Live data retrieval follows this conceptual chain:

```text
Primary Provider
      │
      ├── success ───────────────► Structured result
      │
      ▼
Alternate Provider
      │
      ├── success ───────────────► Structured result
      │
      ▼
Fallback LLM
      │
      ├── estimate possible ─────► Explicitly labeled estimate
      │
      ▼
Unavailable
      │
      └──────────────────────────► Warning / omit
```

The fallback LLM is **estimation-only**.

It may estimate numerical information such as:

- Hotel cost
- Transport cost
- Food cost
- Activity cost
- Other travel cost assumptions

It cannot invent concrete entities.

For example:

```text
Allowed:
"Typical 3-star hotel cost is estimated at ₹7,000/night."

Not allowed:
"XYZ Hotel costs ₹7,000/night."
```

unless the hotel was actually discovered through a trusted place/hotel tool.

Every fallback estimate must be explicitly marked:

> **Estimated — live data unavailable**

### 7.1 Forex Tool Multi-Tier Fallback Cascade

The currency conversion tool (`src/tools/forex.py`) implements a 7-tier resilience chain ensuring all foreign amounts convert to INR deterministically:

1. **Test Fixture**: `data/fixtures/mock_forex.json` (active when `use_fixture=True` or `SAFARNAMA_TEST_MODE=1`).
2. **In-Memory Cache**: 24-hour TTL per currency pair, avoiding redundant external network calls.
3. **Live Tier 1 (Open Access)**: ExchangeRate-API open access (`https://open.er-api.com/v6/latest/USD`, keyless).
4. **Live Tier 2 (CDN Mirror)**: FawazAhmed Currency API (`@fawazahmed0/currency-api` via jsDelivr CDN and Cloudflare Pages mirror, keyless, 340+ currencies).
5. **Live Tier 3 (ECB Rates)**: Frankfurter API (`https://api.frankfurter.dev/v1/latest?base=USD`, keyless European Central Bank reference rates).
6. **Live Tier 4 (Authenticated API)**: ExchangeRate-API authenticated endpoint (`https://v6.exchangerate-api.com/v6/{KEY}/latest/USD` when `EXCHANGERATE_API_KEY` is configured).
7. **Tier 5 (Offline Baseline)**: Built-in `OFFLINE_BASELINE_RATES` table for ~40 major travel currencies, guaranteeing the application never crashes during complete internet blackouts.

### 7.2 Weather Tool Multi-Tier Fallback Cascade

The weather forecasting tool (`src/tools/weather.py`) implements a 6-tier resilience chain providing structured meteorological forecasts and outdoor friendliness ratings:

1. **Test Fixture**: `data/fixtures/mock_weather.json` (active when `use_fixture=True` or `SAFARNAMA_TEST_MODE=1`).
2. **In-Memory Cache**: 3-hour TTL per coordinate/date pair.
3. **Live Tier 1 (Primary)**: Open-Meteo Forecast API (`https://api.open-meteo.com/v1/forecast`, keyless, up to 16 days daily forecast).
4. **Live Tier 2 (Fallback 1)**: wttr.in JSON API (`https://wttr.in/{lat},{lon}?format=j1`, keyless global fallback).
5. **Live Tier 3 (Fallback 2)**: OpenWeatherMap 5-Day/3-Hour Forecast API (`https://api.openweathermap.org/data/2.5/forecast` using `OPENWEATHERMAP_API_KEY`).
6. **Tier 4 (Offline Baseline)**: Deterministic seasonal climate baseline heuristic based on destination latitude, hemisphere, and calendar month solar cycles.

---

# 8. Fixture-First Offline Architecture

Tools should support hermetic local testing.

The intended pattern is:

```text
Tool call
   │
   ▼
Fixture available?
   │
 ┌─┴─────────────┐
 │               │
YES              NO
 │               │
 ▼               ▼
Fixture        API call
```

Fixtures live under:

```text
data/fixtures/
```

Examples:

- `mock_flights.json`
- `mock_hotels.json`
- `mock_tavily_search.json`
- `mock_weather.json`

This allows:

- Offline development
- Deterministic tests
- Reduced API usage
- Faster unit tests
- Reproducible integration tests

---

# 9. Static Data Architecture

Static datasets provide fast baseline lookups.

```text
Upstream Repository
        │
        ▼
On-demand ingestion script
        │
        ▼
Validation / transformation
        │
        ▼
data/static/*.json
        │
        ▼
static_data.py
        │
        ▼
Application nodes/tools
```

## Airport dataset

Source:

`davidmegginson/ourairports-data`

Generated by:

`scripts/fetch_airports.py`

Output:

`data/static/airports.json`

Used for:

- IATA resolution
- Airport/city mapping
- Country identification
- Coordinates

## Visa dataset

Source:

`imorte/passport-index-data` & Tavily/Gemini enrichment

Generated by:

`scripts/fetch_visa_rules.py` & `scripts/enrich_visa_rules.py`

Output:

`data/static/visa_rules.json` & `data/static/visa_rules_enriched.json`

Used as the baseline and verified Indian-passport visa matrix.

## Country profile dataset

Source:

`REST Countries v5 API` (https://restcountries.com)

Generated by:

`scripts/fetch_country_profiles.py`

Output:

`data/static/countries.json`

Used for:

- Official currencies (code, name, symbol) for destination budget displays
- UTC timezones and IST offset calculations
- Schengen Area & EU membership verification for European multi-destination trips
- Capital city coordinates & country borders
- Driving side (left/right) for car rental advisories
- Calling codes and flag emojis

## Ingestion policy

V1 uses **on-demand ingestion**.

There is no required periodic ingestion runtime process.

GitHub Actions may be used later to automate ingestion, but it is not part of the current runtime requirement.

Existing static data remains usable if an upstream refresh is unavailable.

---

# 10. Budget and Optimization Architecture

The optimizer is intentionally separated from LLM reasoning.

```text
Logistics Costs ─────┐
Experience Costs ────┤
Visa Costs ──────────┤
Food Estimate ───────┤
Miscellaneous ───────┤
                     ▼
              Calculator Tool
                     │
                     ▼
             Base Trip Cost
                     │
                     ▼
          Dynamic Contingency
                     │
                     ▼
             Projected Total
                     │
                     ▼
              Budget Verdict
```

## Deterministic calculation

The LLM must not:

- Add costs
- Multiply quantities
- Calculate room totals
- Calculate visa totals
- Calculate contingency
- Calculate budget variance
- Decide whether a numeric total is under budget

All arithmetic belongs in deterministic Python tooling.

---

# 11. Budget Decision Flow

The budget system uses the following policy:

```text
Projected total
      │
      ▼
Within budget?
 ┌────┴─────┐
YES         NO
 │           │
 ▼           ▼
Continue   Overage
             │
       ┌─────┼───────────────┐
       │     │               │
      ≤5%   5–15%           >15%
       │     │               │
       ▼     ▼               ▼
 Auto      User-visible     Explain
 minor     trade-off        infeasibility
 optimize  decision         + alternatives
```

Major changes require user involvement.

Minor optimizations can include:

- Slightly cheaper appropriate hotel
- More economical transportation
- Lower-cost activity alternative
- Lower-cost food assumption

Hard quality guardrails must remain active.

---

# 12. Human-in-the-Loop Architecture

Safarnama automates planning but preserves user control over meaningful trade-offs.

User intervention is appropriate when:

- Budget needs a material increase
- Travel style must materially change
- Must-visit places conflict with feasibility
- Duration needs to change
- Destinations need to be removed
- Major activities need to be removed

The system should not silently make a major compromise.

If the user changes a constraint, the graph should reuse unaffected work where possible.

Example:

```text
Existing plan
     │
User changes budget
     │
     ▼
Determine affected components
     │
     ├── Route unchanged
     ├── Visa unchanged
     ├── Attractions unchanged
     │
     └── Recalculate:
           Hotels
           Transport
           Budget
           Optimization
```

---

# 13. Weather Architecture

Weather is an input to itinerary planning, not merely an informational display.

```text
Coordinates
    │
    ▼
Weather Tool
    │
    ▼
Forecast + confidence/context
    │
    ▼
Experience Node
    │
    ├── Suitable ─────► Keep outdoor plan
    │
    └── Significant risk
             │
             ▼
       Indoor/covered
       alternative
             │
             ▼
       Explain change
```

Long-range or low-confidence forecasts should not cause disproportionate itinerary changes.

---

# 14. Date Optimization Architecture

Three date modes are supported:

### Exact dates

```text
User dates
   ↓
Plan trip
```

### Flexible date window

```text
Date window + duration
        ↓
Find suitable trip
```

### Find best dates within a window

The planner evaluates candidate date ranges using:

- Live pricing/availability where possible
- Weather
- Attraction suitability
- Route feasibility
- Overall trip quality

The objective is **best overall trip quality**, not simply lowest cost.

The result includes:

- Recommended date range
- 2–3 alternatives
- Main trade-offs

---

# 15. Data Provenance

The architecture should preserve the origin/status of important external values.

Possible source classifications:

```text
LIVE_PROVIDER
ALTERNATE_PROVIDER
STATIC_DATASET
FIXTURE
FALLBACK_LLM_ESTIMATE
```

This allows downstream planning and final output to distinguish live values from estimates.

The user-facing result must explicitly identify fallback-LMM estimates.

---

# 16. State Architecture

LangGraph maintains a central typed state.

Conceptually:

```text
TravelPlannerState
├── trip_context
├── travel_scope
├── origin information
├── destination information
├── route
├── visa_verdict
├── logistics_plan
├── experience_plan
├── budget_breakdown
├── optimization_status
├── replanning information
├── warnings
└── execution errors
```

The exact state schema should be implemented in:

`src/graph/state.py`

Pydantic models under `src/models/` should define structured domain contracts.

LangGraph state should contain validated structured data rather than arbitrary LLM-generated strings wherever possible.

---

# 17. Pydantic Model Architecture

Pydantic v2 is used for strict validation and structured contracts.

Primary domains:

```text
models/
├── trip.py
├── itinerary.py
├── logistics.py
├── visa.py
└── budget.py
```

### Trip models

Represent:

- Trip context
- Party details
- Travel scope
- Dates
- Duration
- Budget mode
- Travel preferences

### Logistics models

Represent:

- Transport options
- Hotel options
- Logistics plan

### Itinerary models

Represent:

- POIs
- Activities
- Time/daypart slots
- Day plans
- Experience plans

### Visa models

Represent:

- Country policy
- Visa options
- Visa verdict
- Entry conditions

### Budget models

Represent:

- Cost components
- Contingency
- Projected total
- Variance
- Optimization status

---

# 18. LLM Architecture

LLMs are specialized components inside the system, not the system itself.

The primary planning LLM is used for structured reasoning where appropriate.

Requirements inherited from the project specification include:

- Structured outputs
- Pydantic validation
- Temperature 0 where deterministic structured generation is required
- No LLM arithmetic

The visa reconciliation workflow can use an LLM to reconcile static and live policy information into a structured verdict.

The fallback LLM is a separate concern and has a narrower responsibility: **numerical estimation when normal data providers cannot supply sufficient data**.

---

# 19. Prompt Architecture

Prompts are isolated from node implementation.

```text
src/prompts/
├── __init__.py
├── experience_prompts.py
└── visa_prompts.py
```

This keeps:

- Prompt text
- Node logic
- Tool calls
- State mutation

separated.

Additional prompt modules can be added as new LLM-driven responsibilities emerge.

---

# 20. API Architecture

FastAPI provides the application service layer.

```text
static UI / client
        │
        ▼
POST /plan
        │
        ▼
FastAPI route
        │
        ▼
Request validation
        │
        ▼
LangGraph workflow
        │
        ▼
Streaming events / result
```

Primary files:

```text
src/api/
├── app.py
└── routes.py
```

The API should not contain planning logic.

It translates between external requests/responses and the planning workflow.

---

# 21. CLI Architecture

`src/main.py` provides a local CLI entry point.

The CLI should invoke the same planning workflow used by the API rather than implementing a separate planning path.

```text
CLI ───────┐
           ├──► Planning Workflow
FastAPI ───┘
```

This prevents divergence between local development and service execution.

---

# 22. Frontend Architecture

V1 contains:

```text
static/
└── index.html
```

The initial UI can provide:

- Trip input
- Planning execution
- Progress/status visibility
- Final itinerary
- Budget summary
- Warnings
- Estimates

The project structure currently allows a Three.js-based interactive globe/dashboard.

The frontend remains separate from the planning engine.

---

# 23. Repository Structure

The current intended repository structure is:

```text
travel-planner/
├── .github/
│   └── workflows/
│       └── ingest_static_data.yml
├── data/
│   ├── fixtures/
│   │   ├── mock_flights.json
│   │   ├── mock_hotels.json
│   │   ├── mock_tavily_search.json
│   │   └── mock_weather.json
│   └── static/
│       ├── airports.json
│       ├── culinary_signatures.json
│       └── visa_rules.json
├── scripts/
│   ├── fetch_airports.py
│   └── fetch_visa_rules.py
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── routes.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── edges.py
│   │   ├── state.py
│   │   └── workflow.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── budget.py
│   │   ├── itinerary.py
│   │   ├── logistics.py
│   │   ├── trip.py
│   │   └── visa.py
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── experience_node.py
│   │   ├── intake_node.py
│   │   ├── logistics_node.py
│   │   ├── optimizer_node.py
│   │   └── visa_node.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── experience_prompts.py
│   │   └── visa_prompts.py
│   └── tools/
│       ├── __init__.py
│       ├── calculator.py
│       ├── forex.py
│       ├── static_data.py
│       ├── weather.py
│       └── web_search.py
├── static/
│   └── index.html
├── tests/
│   ├── conftest.py
│   ├── integration/
│   │   ├── test_api_streaming.py
│   │   └── test_full_workflow.py
│   └── unit/
│       ├── test_calculator.py
│       ├── test_edges.py
│       ├── test_nodes.py
│       ├── test_state_models.py
│       └── test_static_data.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

The structure is a starting architecture, not a requirement to implement every file immediately.

---

# 24. File and Responsibility Map

| Area | Responsibility |
|---|---|
| `.github/workflows/` | Optional automation around static-data ingestion |
| `data/fixtures/` | Offline API/test payloads |
| `data/static/` | Generated static datasets |
| `scripts/` | On-demand data ingestion |
| `src/api/` | HTTP service layer |
| `src/graph/` | LangGraph state and orchestration |
| `src/models/` | Pydantic domain contracts |
| `src/nodes/` | Specialized planning workers |
| `src/prompts/` | LLM prompt definitions |
| `src/tools/` | External integrations and deterministic utilities |
| `static/` | Initial frontend |
| `tests/unit/` | Component-level tests |
| `tests/integration/` | Cross-component/workflow tests |
| `pyproject.toml` | Dependencies and development tooling |

---

# 25. Technical Stack

## Core runtime

- Python 3.11+

## Orchestration

- LangGraph
- `StateGraph`
- Conditional routing
- Parallel execution/fan-out
- Replanning/cyclic execution where required

## Data validation

- Pydantic v2

## API

- FastAPI

## LLM

- Google Gemini through the configured LangChain Google GenAI integration for structured reasoning where required.
- Separate fallback LLM/API configuration for estimation-only fallback behavior.

The exact production model/provider configuration should remain configurable rather than embedded throughout the codebase.

## HTTP/API clients

- Python HTTP client implementation appropriate to each provider.
- Provider-specific logic should remain behind tool interfaces.

## Search

- Tavily or another configured web-search provider for live verification where required.

## Weather

- Open-Meteo or the configured weather provider.

## Testing

- pytest

## Code quality

- Ruff

## Configuration

- Environment variables
- `.env.example`

## Frontend

- Initial static HTML interface
- Three.js may be used for the planned interactive globe/dashboard

---

# 26. Dependency Rules

The architecture should maintain clear dependency direction.

### Allowed

```text
API → Graph
Graph → Nodes
Nodes → Tools / Models / Prompts
Tools → Provider adapters
Models → Validation/domain definitions
```

### Avoid

```text
API → Provider API directly
Node → raw HTTP provider logic
Calculator → LLM
Model → API client
Tool → UI
Frontend → internal node implementation
```

This keeps the application modular and testable.

---

# 27. Error and Warning Architecture

Errors should be distinguished from warnings.

### Errors

Used when execution cannot safely continue.

Examples:

- Invalid user request
- Corrupt required state
- Invalid structured provider response
- Unrecoverable workflow failure

### Warnings

Used when planning can continue but information quality is reduced.

Examples:

- Live hotel pricing unavailable
- Fallback estimate used
- Static dataset used
- Weather forecast confidence is low
- Some optional data unavailable

Warnings should be preserved in planning state and exposed appropriately in the final result.

---

# 28. Testing Architecture

Testing should happen at every layer.

## Unit tests

Validate:

- Pydantic models
- Static-data lookup
- Calculator
- Tool fallback behavior
- Graph routing
- Individual nodes

## Integration tests

Validate:

- API → graph execution
- Full domestic workflow
- Full international workflow
- Fixture-backed external tools
- Streaming behavior

## Critical scenarios

At minimum, the test suite should eventually cover:

1. Domestic trip bypasses visa.
2. International trip invokes visa processing.
3. Multiple countries are supported.
4. Multiple Indian states/UTs are supported.
5. Static airport lookup resolves valid cities/IATA codes.
6. Static visa baseline is loaded.
7. API failure uses alternate/fallback behavior.
8. Fallback LLM estimates are labeled.
9. Fallback LLM cannot create concrete entities.
10. Calculator performs all budget arithmetic.
11. Budget optimization respects hard quality guardrails.
12. Weather can modify the itinerary.
13. Flexible-date optimization can compare candidate windows.
14. User budget changes reuse unaffected planning state where possible.

---

# 29. Incremental Implementation Strategy

Safarnama will **not** be built all at once.

The implementation sequence is intentionally incremental.

## Phase 1 — Static Data Foundation

First build and validate:

- Project environment
- `fetch_airports.py`
- `fetch_visa_rules.py`
- Static JSON generation
- Static-data lookup helpers
- Unit tests

Goal:

> Prove that the application's baseline travel datasets can be generated and consumed correctly.

---

## Phase 2 — Domain Models and Deterministic Tools

Build:

- Trip models
- Itinerary models
- Logistics models
- Visa models
- Budget models
- Calculator
- Static-data utilities

Goal:

> Establish reliable contracts before adding agent behavior.

---

## Phase 3 — External Tools

Build and test:

- Weather
- Search
- Places
- Hotels
- Transport
- Visa verification
- Fallback estimation

Goal:

> Establish reliable data acquisition independently of the planning graph.

---

## Phase 4 — Individual Nodes

Build one node at a time:

1. Intake
2. Visa
3. Logistics
4. Experience
5. Optimizer

Each node should be testable independently.

---

## Phase 5 — LangGraph Workflow

Connect the validated nodes into the complete graph.

Validate:

- Routing
- Parallel execution
- State reducers
- Budget decisions
- Replanning
- Error/warning propagation

---

## Phase 6 — API and CLI

Expose the validated workflow through:

- CLI
- FastAPI
- Streaming events

---

## Phase 7 — Frontend

Connect the static UI to the API and present:

- Inputs
- Planning progress
- Route
- Itinerary
- Budget
- Visa information
- Warnings
- Estimates

---

# 30. Architecture Principles

The following principles should guide implementation decisions:

### 1. Tools over direct API calls

Nodes request capabilities through tools rather than knowing provider-specific APIs.

### 2. Structured state over free-form text

Important planning information should use validated models.

### 3. Deterministic calculations

Financial arithmetic must never depend on LLM reasoning.

### 4. Real entities from real data

The fallback LLM may estimate numerical data but must not fabricate specific travel entities.

### 5. Explicit uncertainty

Estimated or degraded data quality must be visible.

### 6. Offline testability

External tools should support fixtures.

### 7. Replaceable providers

Changing a flight, hotel, places, search, or weather provider should not require rewriting planning logic.

### 8. Incremental construction

Each layer must work before the next layer is built.

### 9. User control for major trade-offs

The planner may optimize small things automatically, but major compromises require user involvement.

### 10. Preserve reusable work

When a constraint changes, re-use unaffected results rather than rebuilding the entire plan unnecessarily.

---

# 31. Current Architecture Boundary

This document defines the intended architecture and responsibilities.

It does **not** yet define:

- Exact API providers for every travel category
- Exact API schemas
- Exact Pydantic field definitions
- Exact LangGraph state reducers
- Exact prompts
- Exact UI implementation
- Exact database/persistence strategy
- Production deployment topology
- Authentication/authorization
- Booking execution

Those decisions can be defined in subsequent project documents as implementation progresses.

The architecture is intentionally designed to accommodate those decisions without coupling the core planner to them.
