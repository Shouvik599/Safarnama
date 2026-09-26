# Implementation Phases
# Safarnama

**Document status:** V1 Incremental Delivery Plan  
**Purpose:** Break Safarnama into small, verifiable implementation phases so the project is built deliberately rather than attempting the complete application in one pass.

---

## 1. Why We Are Building in Phases

Safarnama is a multi-component system involving:

- Static datasets
- Data ingestion
- External APIs
- Tool wrappers
- Pydantic models
- LLMs
- LangGraph
- Budget calculation
- Optimization
- FastAPI
- Streaming
- Frontend
- Tests

Trying to implement all of these simultaneously would make it difficult to determine:

- Which component is broken.
- Whether an API integration is reliable.
- Whether data contracts are correct.
- Whether the LangGraph state is correct.
- Whether budget calculations are trustworthy.
- Whether the final itinerary is actually complete.

Therefore, the project will be built as a sequence of **small, independently verifiable milestones**.

The guiding principle is:

> **Build one capability → test it completely → verify its output → only then build on top of it.**

The objective is not to reach a full-looking application quickly.

The objective is to reach a **working application with reliable foundations**.

---

# 2. Phase Completion Rule

A phase is not considered complete merely because its code exists.

Each phase must have:

1. Implementation conforming to domain contracts
2. Hermetic unit tests running 100% offline with zero external network reliance
3. Live network integration verification (`use_fixture=False`, `live_search_enabled=True`) for all planning nodes and tools connecting to external APIs (validating real endpoint responses, provider schemas, and fallback behavior)
4. Manual verification where useful
5. Clear inputs and outputs
6. Comprehensive error handling and non-crashing resilience
7. Documentation synchronized across `rules.md`, `phases.md`, `architecture.md`, `README.md`, and `memory.md`
8. A working result that the next phase can safely depend on

Do not proceed to the next major phase if the current foundation is unstable or lacks verified live and offline testing.

---

# 3. Development Strategy

The project will follow this progression:

```text
PHASE 0: Project Foundation
      ↓
PHASE 1: Static Data Ingestion
      ↓
PHASE 2: Static Data Access Layer
      ↓
PHASE 3: External Tool Layer
      ↓
PHASE 4: API Foundation
      ↓
PHASE 5: Domain Models
      ↓
PHASE 6: Intake Functionality
      ↓
PHASE 7: Visa Functionality
      ↓
PHASE 8: Logistics Functionality
      ↓
PHASE 9: Experience Functionality
      ↓
PHASE 10: Deterministic Budget Engine
      ↓
PHASE 11: Optimizer Functionality
      ↓
PHASE 12: LangGraph Orchestration
      ↓
PHASE 13: First Complete Vertical Slice
      ↓
PHASE 14: International Vertical Slice
      ↓
PHASE 15: Flexible Dates
      ↓
PHASE 16: Budget Conflict & Human Decision Flow
      ↓
PHASE 17: API Streaming
      ↓
PHASE 18: Frontend
      ↓
PHASE 19: End-to-End Test Matrix
      ↓
PHASE 20: Production Hardening
```

The order may be adjusted if implementation experience shows a better dependency order, but the principle of incremental verification remains mandatory.

---

# 4. Phase 0 — Project Foundation

## Objective

Create the smallest valid Python project and development environment.

## Build

- Repository structure
- `pyproject.toml`
- Python 3.11+
- `uv` configuration
- Ruff configuration
- pytest configuration
- `.gitignore`
- `.env.example`
- Basic package initialization

Do not implement travel-planning logic yet.

## Verification

Confirm:

```bash
uv run python --version
uv run pytest
```

and basic imports work.

## Exit criteria

- Project can be installed with `uv`.
- Tests execute.
- Ruff executes.
- No dependency requires `pip`.
- Repository structure is ready for Phase 1.

---

# 5. Phase 1 — Static Data Ingestion

## Objective

Make the two foundational ingestion scripts work correctly before building agents or the application workflow.

This is the **first major implementation target**.

## 5.1 Airport ingestion

Implement:

```text
scripts/fetch_airports.py
```

Source:

`davidmegginson/ourairports-data`

Input:

`airports.csv`

Output:

```text
data/static/airports.json
```

Extract relevant:

- IATA code
- Airport type
- Municipality/city
- ISO country
- Latitude
- Longitude

Filter according to the project requirements.

## 5.2 Visa ingestion

Implement:

```text
scripts/fetch_visa_rules.py
```

Source:

`imorte/passport-index-data`

Input:

Passport Index CSV dataset.

Output:

```text
data/static/visa_rules.json
```

Filter for Indian passport (`IND`) and normalize baseline destination entry rules.

## 5.3 Country profile ingestion

Implement:

```text
scripts/fetch_country_profiles.py
```

Source:

`REST Countries v5 API` (https://restcountries.com)

Output:

```text
data/static/countries.json
```

Extract and normalize:
- ISO-2 and ISO-3 country codes
- Common and official English names
- Capital cities and geographic coordinates
- Currencies (code, name, symbol)
- Languages
- Timezones (UTC offsets)
- Driving side (left/right)
- Dialing calling code
- Flag emojis
- Schengen Area & EU membership status
- Border countries

## 5.4 Ingestion behavior

The scripts are **on-demand** in V1.

Run with:

```bash
uv run python scripts/fetch_airports.py
uv run python scripts/fetch_visa_rules.py
uv run python scripts/fetch_country_profiles.py
```

Do not depend on a scheduled runtime ingestion process.

## Verification

Test:

- Source retrieval
- CSV / API payload parsing
- Required columns / fields
- Filtering
- Transformation
- JSON output
- JSON validity
- Required records
- Re-running ingestion safely
- Existing output preservation when refresh cannot be completed

## Exit criteria

We can reliably produce valid:

```text
data/static/airports.json
data/static/visa_rules.json
data/static/visa_rules_enriched.json
data/static/countries.json
```

and tests confirm that expected records resolve.

---

# 6. Phase 2 — Static Data Access Layer

## Objective

Create the runtime interface through which application components consume static datasets.

Implement:

```text
src/tools/static_data.py
```

Responsibilities:

- Load static JSON
- Build in-memory indexes
- Resolve IATA codes
- Resolve cities
- Resolve countries
- Retrieve coordinates
- Retrieve visa baseline rules
- Provide predictable errors for missing records

The application should not repeatedly open JSON files for every lookup.

## Tests

Test examples such as:

- `DEL`
- `CCU`
- `BGO`
- `TAS`
- `FRU`

and representative visa destinations.

Test:

- Valid lookup
- Missing lookup
- Invalid input
- Dataset loading
- Dataset structure

## Exit criteria

The application can reliably query the static datasets through one tested interface.

---

# 7. Phase 3 — External Tool Layer

## Objective

Build and validate external integrations **before connecting them to LangGraph agents**.

This phase is intentionally tool-first.

Each tool should work independently.

---

## 7.1 Weather Tool

Implement:

```text
src/tools/weather.py
```

Responsibilities:

- Accept coordinates (latitude, longitude)
- Accept requested dates (start date, end date, or duration in days)
- Query weather providers with multi-tier fallback cascade:
  1. Test Fixture: `data/fixtures/mock_weather.json` (offline testing)
  2. In-Memory Cache: 3-hour TTL per coordinate/date pair
  3. Live Tier 1: Open-Meteo Forecast API (`https://api.open-meteo.com/v1/forecast`, zero auth, up to 16 days daily forecast)
  4. Live Tier 2: wttr.in JSON API (`https://wttr.in/{lat},{lon}?format=j1`, zero auth, global fallback)
  5. Live Tier 3: OpenWeatherMap 5-Day/3-Hour Forecast API (`https://api.openweathermap.org/data/2.5/forecast` using `OPENWEATHERMAP_API_KEY`)
  6. Tier 4: Offline Climate Baseline Heuristic (latitude + seasonal monthly solar physics ensuring Safarnama never crashes)
- Return structured weather data (`DailyWeatherForecast`, `WeatherForecastResult`)
- Compute outdoor friendliness (`is_outdoor_friendly`) and summary string
- Support fixture mode: `data/fixtures/mock_weather.json`
- Respect network timeouts (default: 6.0s)
- Provide cache management (`clear_weather_cache`)

Test with:

```text
data/fixtures/mock_weather.json
```

Verify:

- Rain probability and precipitation mm
- Maximum, minimum, and average temperatures
- Standard meteorological WMO weather codes (0-99)
- Date handling (ISO strings and date objects)
- Fixture fallback and environment variable trigger (`SAFARNAMA_TEST_MODE`)
- Multi-tier live provider fallback cascade
- Offline climate baseline heuristic
- Coordinates and date validation error handling

---

## 7.2 Web Search Tool

Implement:

```text
src/tools/web_search.py
```

Responsibilities:

- Execute web search queries for travel research, visa rules, attractions, hotels, and flight advice
- Query web search providers with multi-tier fallback cascade:
  1. Test Fixture: `data/fixtures/mock_web_search.json` (or `mock_tavily_search.json` for offline testing)
  2. In-Memory Cache: 1-hour TTL per query string / result limit
  3. Live Tier 1: Tavily Search API (`POST https://api.tavily.com/search` using `TAVILY_API_KEY`)
  4. Live Tier 2: DuckDuckGo Search (Keyless open-access instant answer API / HTTP fallback)
  5. Live Tier 3: Firecrawl Search API (`POST https://api.firecrawl.dev/v2/search` using `FIRECRAWL_API_KEY`)
  6. Tier 4: Offline Search Fixture (Guarantees zero-crash resilience when offline/unconfigured)
- Return structured search result models (`SearchResultItem`, `WebSearchResult` in `src/models/web_search.py`)
- Support fixture mode: `data/fixtures/mock_web_search.json`
- Preserve title, URL snippet/markdown, and provider provenance metadata
- Provide cache management (`clear_web_search_cache`) and status reporting (`get_web_search_status`)

---

## 7.3 Transport/Flight Tool

Implement:

```text
src/tools/transport.py
```

Responsibilities:

- Search available transport options (flights, trains, buses) for domestic and international travel
- Query transport providers with multi-tier fallback cascade:
  1. Test Fixture: `data/fixtures/mock_flights.json` (offline testing)
  2. In-Memory Cache: 1-hour TTL per `(origin, destination, date, mode)` search
  3. Live Aviation APIs: Sky Scraper / Flights Sky / Aviationstack (`RAPIDAPI_KEY` / `AVIATIONSTACK_API_KEY`)
  4. Live Indian Railways APIs: Indian Railway IRCTC / eRail (`RAPIDAPI_KEY` / open access)
  5. Live International Rail & Bus APIs: `transport.rest` / Transitland (Zero-auth open access)
  6. Live Web Search Tool Fallback: `search_web()` for live route & ticket pricing snippets
  7. Tier 5: Offline Distance & Speed Physics Engine (Haversine math guaranteeing zero-crash operation)
- Return structured transport models (`TransportSegment`, `TransportSearchResult` in `src/models/transport.py`)
- Support fixture mode: `data/fixtures/mock_flights.json`
- Convert all fares to Indian Rupee (INR) deterministically
- Preserve carrier, code, class, URL, and provider provenance metadata
- Provide cache management (`clear_transport_cache`) and status reporting (`get_transport_status`)

---

## 7.4 Hotel Tool

Responsibilities:

- Search hotel/place data
- Normalize results
- Return validated hotel options
- Provide booking link when available
- Return pricing when available
- Support fixture mode

The tool discovers real hotels.

The fallback LLM may estimate a price when allowed, but must not invent a hotel.

---

## 7.5 Places/Restaurant Tool

Responsibilities:

- Find attractions
- Find restaurants/food places
- Return real place information
- Preserve location/rating/category data where available
- Support fixture mode

Food recommendations should use this tool for actual restaurants.

---

## 7.6 Forex / Currency Converter Tool

Implement:

```text
src/tools/forex.py
```

Responsibilities:

- Convert amounts between foreign currencies and Indian Rupee (INR)
- Ensure all downstream costs presented to travelers are expressed in INR
- Query forex providers with multi-tier fallback cascade:
  1. Test Fixture: `data/fixtures/mock_forex.json` (offline testing)
  2. In-Memory Cache: 24-hour TTL
  3. Live Tier 1: ExchangeRate-API Open Access (`https://open.er-api.com/v6/latest/USD`, zero auth)
  4. Live Tier 2: FawazAhmed Currency API (`@fawazahmed0/currency-api` via jsDelivr CDN and Cloudflare Pages mirror, 340+ currencies, zero auth)
  5. Live Tier 3: Frankfurter API (`https://api.frankfurter.dev/v1/latest?base=USD`, ECB reference rates, zero auth)
  6. Live Tier 4: ExchangeRate-API Authenticated (`https://v6.exchangerate-api.com/v6/{KEY}/latest/USD` if `EXCHANGERATE_API_KEY` present)
  7. Tier 5: Built-in Offline Baseline Rates Table (`OFFLINE_BASELINE_RATES` for ~40 global currencies)
- Support fixture mode: `data/fixtures/mock_forex.json`
- Preserve conversion rate, provider, `is_estimated` flag, and timestamp metadata for pricing auditability
- Provide cache management (`clear_forex_cache`)

---

## 7.7 Deterministic Calculator Tool

Implement:

```text
src/tools/calculator.py
```

Responsibilities:

- Provide deterministic arithmetic for travel budget aggregation
- Strictly enforce the architectural rule prohibiting LLM-based arithmetic
- Calculate total expenses, per-person allocations, daily averages, and contingency buffers
- Ensure rounding consistency (e.g. 2 decimal places for financial calculations)
- Test edge cases (zero values, single vs multi-traveler splits, buffer percentages)

---

## 7.8 Fallback Estimator

Implement a dedicated fallback component for estimation-only behavior (`src/tools/fallback_estimator.py`).

It may estimate:

- Hotel cost
- Transport cost
- Food cost
- Activity cost
- Miscellaneous travel costs
- Total budget baseline

It may not invent:

- Hotels
- Restaurants
- Flights
- Attractions
- Booking links
- Visa requirements

Every estimate must carry a clear estimated status (`is_estimated=True`).

Multi-provider LLM Fallback Cascade:
1. **Test Fixture Mode**: `data/fixtures/mock_fallback_estimates.json`
2. **In-Memory Cache**: 24-hour TTL
3. **Live Tier 1**: Google Gemini API (`gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`)
4. **Live Tier 2**: Groq API (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`)
5. **Live Tier 3**: NVIDIA NIM API (`meta/llama-3.3-70b-instruct`, `meta/llama-3.1-8b-instruct`, `mistralai/mistral-7b-instruct-v0.3`)
6. **Tier 4**: Offline Rule-Based Mathematical Baseline (`_estimate_heuristic_baseline`)

---

## 7.9 Tool Exit Criteria

Before moving to planning nodes, every required tool must:

- Have a defined interface.
- Return validated structured data.
- Handle failure.
- Support fixture testing.
- Have appropriate tests.
- Respect provider boundaries.
- Preserve provenance.

---

# 8. Phase 4 — API Foundation

## Objective

Create a working FastAPI service **before connecting the complete planning workflow**.

Implement:

```text
src/api/app.py
src/api/routes.py
```

Initially expose a simple planning/test endpoint.

The API should prove:

```text
HTTP request
   ↓
Pydantic validation
   ↓
Application service
   ↓
Structured response
```

Do not immediately connect every agent.

## Test

Verify:

- Valid request
- Invalid request
- Validation errors
- API response schema
- Error responses
- CORS configuration
- Basic streaming mechanism if selected for the endpoint

## Exit criteria

A client can call the API and receive a valid structured response without requiring the full planner.

---

# 9. Phase 5 — Domain Models

## Objective

Create reliable domain contracts before building complex planning nodes.

Implement:

```text
src/models/
├── trip.py
├── itinerary.py
├── logistics.py
├── visa.py
└── budget.py
```

Define and test:

- Trip context
- Party details
- Travel scope
- Date modes
- Duration
- Budget modes
- Travel style
- Pace
- Activity preferences
- Food preferences
- Must-visits
- Visa information
- Logistics
- Hotels
- Activities
- Day plans
- Budget breakdown

## Important

Do not attempt to solve orchestration in the models.

Models define contracts.

## Exit criteria

Invalid states are rejected and valid domain objects can be created reliably.

---

# 10. Phase 6 — Intake Functionality

## Objective

Build the first real planning capability.

Implement:

```text
src/nodes/intake_node.py
```

Responsibilities:

- Validate/sanitize user input
- Resolve scope
- Resolve origin
- Resolve destinations
- Resolve gateway information
- Load coordinates
- Create initial state

Do not yet build the complete itinerary.

## Test scenarios

At minimum:

- Domestic single destination
- Domestic multiple states
- International single country
- International multiple countries
- Invalid origin
- Invalid destination
- Invalid traveler count
- Invalid budget

## Exit criteria

A valid user request can be converted into a reliable planning state.

---

# 11. Phase 7 — Visa Functionality

## Objective

Build and verify international visa planning independently.

Implement:

```text
src/nodes/visa_node.py
```

Workflow:

```text
Static baseline
      +
Live verification/search
      ↓
Structured policy interpretation
      ↓
Validated visa verdict
```

Test:

- Domestic bypass
- International invocation
- Static baseline
- Live policy override
- Multiple countries
- Structured output validation
- Failure/warning behavior

The fallback LLM must not fabricate visa requirements.

## Exit criteria

International trips can produce a reliable visa result before being connected to the complete planner.

---

# 12. Phase 8 — Logistics Functionality

## Objective

Build transportation and accommodation planning independently.

Implement:

```text
src/nodes/logistics_node.py
```

Responsibilities:

- Determine appropriate transport
- Search available options
- Select suitable hotel
- Estimate room requirements
- Produce structured logistics data

The node must consider:

- Budget
- Travel style
- Travelers
- Route
- Availability
- Practicality

## Verification

Test:

- Single destination
- Multi-destination
- Adults + children
- Different travel styles
- Provider failure
- Fallback estimates
- Hotel booking links
- Budget-sensitive alternatives

## Exit criteria

The logistics node can independently produce valid structured logistics.

---

# 13. Phase 9 — Experience Functionality

## Objective

Build attractions, food, and weather-aware itinerary planning.

Implement:

```text
src/nodes/experience_node.py
```

Responsibilities:

- Select attractions
- Respect activity preferences
- Respect must-visits
- Select local food experiences
- Find real restaurants
- Apply weather adjustments
- Group activities geographically
- Respect pace
- Produce day-level experiences

## Weather behavior

If weather makes an outdoor activity unsuitable:

```text
Original activity
      ↓
Weather evaluation
      ↓
Alternative activity
      ↓
Updated itinerary
      ↓
User-visible explanation
```

## Exit criteria

The experience node can independently produce a coherent experience plan.

---

# 14. Phase 10 — Deterministic Budget Engine

## Objective

Build the financial engine before connecting optimization loops.

Implement:

```text
src/tools/calculator.py
```

and:

```text
src/models/budget.py
```

The calculator handles:

- Transportation
- Lodging
- Activities
- Visa fees
- Food
- Miscellaneous
- Dynamic contingency
- Total
- Variance
- Budget status

The LLM must never perform these calculations.

## Tests

Test:

- Total trip budget
- Per-person budget
- Adults + children
- Visa fee multiplication
- Food daily estimate
- Miscellaneous
- Contingency
- Under budget
- ≤5% over
- 5–15% over
- >15% over
- Floating-point/rounding behavior

## Exit criteria

The budget engine is independently trusted before optimization is added.

---

# 15. Phase 11 — Optimizer Functionality

## Objective

Implement budget-aware optimization without yet building the complete graph.

Responsibilities:

- Detect budget conflict
- Perform permitted minor optimizations
- Preserve hard quality guardrails
- Generate meaningful alternatives
- Determine when user intervention is required
- Support re-planning of affected components

Optimization rules:

```text
≤5% over
    ↓
Automatic minor optimization

5–15% over
    ↓
User-visible trade-off

>15% over
    ↓
Explain infeasibility + alternatives
```

## Exit criteria

The optimizer can be tested using fixed logistics/experience inputs without requiring the complete LangGraph workflow.

---

# 16. Phase 12 — LangGraph Orchestration

## Objective

Only after individual components work should they be connected into the main graph.

Implement:

```text
src/graph/
├── state.py
├── edges.py
└── workflow.py
```

Connect:

```text
START
  ↓
Intake
  ↓
Scope routing
  ├── Domestic ─────────────┐
  │                         │
  └── International → Visa │
                            │
                            ▼
                    Parallel planning
                    ┌───────────────┐
                    │               │
                    ▼               ▼
                Logistics       Experience
                    │               │
                    └───────┬───────┘
                            ▼
                        Optimizer
                            │
                            ▼
                      Final result /
                       re-planning
```

## Verification

Test:

- Domestic routing
- International routing
- Parallel branch behavior
- State aggregation
- Warnings
- Errors
- Budget optimization
- Re-planning
- Reuse of unaffected work

---

# 17. Phase 13 — First Complete Vertical Slice

## Objective

Build one complete, reliable end-to-end scenario.

Do **not** attempt every possible travel scenario yet.

Start with one controlled scenario such as:

> Indian traveler → one domestic destination → fixed dates → fixed budget → balanced pace.

The complete path should work:

```text
API
 ↓
Intake
 ↓
Logistics
 ↓
Experience
 ↓
Budget
 ↓
Final itinerary
```

Verify the complete response.

## Exit criteria

A real end-to-end trip can be planned successfully without relying on untested components.

---

# 18. Phase 14 — International Vertical Slice

Add:

- Indian passport context
- Visa node
- Live visa verification
- Multi-country support
- International logistics
- International food/activity planning
- Visa budget

Start with one country before expanding to multi-country complexity.

Then test:

```text
India → International destination
```

followed by:

```text
India → Country A → Country B
```

---

# 19. Phase 15 — Flexible Dates

Add support for:

- Exact dates
- Flexible date window
- Best dates within a window

For optimized date selection, evaluate:

- Live pricing
- Availability
- Weather
- Route feasibility
- Overall experience quality

Return:

- Recommended dates
- 2–3 alternatives
- Trade-offs

This phase should be added after the basic itinerary workflow is reliable.

---

# 20. Phase 16 — Budget Conflict and Human Decision Flow

Add the complete human-in-the-loop behavior.

Test scenarios such as:

```text
Budget sufficient
       ↓
Normal plan
```

```text
≤5% over
       ↓
Automatic minor optimization
```

```text
5–15% over
       ↓
Present trade-offs
       ↓
User decision
```

```text
>15% over
       ↓
Realistic budget
+
Alternative paths
       ↓
User decision
```

Also test changing the budget and ensuring unaffected work is reused.

---

# 21. Phase 17 — API Streaming

Once the workflow is reliable, expose useful progress through the API.

Potential events:

```text
planning_started
intake_completed
visa_started
visa_completed
logistics_started
logistics_completed
experience_started
experience_completed
budget_calculated
optimization_started
optimization_completed
planning_completed
warning
error
```

Do not expose internal implementation details unnecessarily.

The client should receive meaningful planning progress.

---

# 22. Phase 18 — Frontend

Only after the backend workflow is stable should the frontend become a major focus.

The frontend should support:

- Trip input
- Destination selection
- Date selection
- Duration
- Budget
- Traveler details
- Travel style
- Pace
- Activities
- Food preferences
- Must-visits
- Planning progress
- Itinerary display
- Budget summary
- Visa information
- Warnings/estimates

Frontend dependencies must use:

```bash
pnpm
```

not npm.

---

# 23. Phase 19 — End-to-End Test Matrix

After the main workflow exists, expand testing systematically.

## Domestic

- Single city
- Multiple cities
- Multiple states
- Different budgets
- Different travel styles
- Different paces

## International

- Single country
- Multiple countries
- Visa required
- Visa-free baseline
- Recent policy change
- Multiple visa options

## Budget

- Under budget
- ≤5% over
- 5–15% over
- >15% over
- Impossible budget
- User budget change

## Dates

- Exact
- Flexible duration
- Flexible date window
- Date optimization

## Weather

- Good weather
- High rain probability
- Low-confidence long-range forecast
- Weather substitution

## Data failures

- Primary API unavailable
- Alternate provider unavailable
- Fallback LLM estimation
- Static dataset usage
- Missing optional information

---

# 24. Phase 20 — Production Hardening

Only after functional behavior is established.

Focus on:

- Configuration
- Logging
- Error reporting
- Timeouts
- Retry strategy
- API rate limits
- Security
- Secret management
- Performance
- Observability
- Documentation
- Deployment

Do not prematurely optimize production infrastructure before the core planning workflow is reliable.

---

# 25. Phase Dependency Map

```text
Foundation
    │
    ▼
Static Data
    │
    ▼
Static Data Tools
    │
    ├───────────────┐
    ▼               ▼
External Tools   Domain Models
    │               │
    └───────┬───────┘
            ▼
       Individual Nodes
            │
            ▼
       LangGraph
            │
            ▼
     Budget + Optimizer
            │
            ▼
   Complete Backend Flow
            │
      ┌─────┴─────┐
      ▼           ▼
 International   Flexible Dates
      │           │
      └─────┬─────┘
            ▼
       API Streaming
            │
            ▼
         Frontend
            │
            ▼
       End-to-End Tests
            │
            ▼
     Production Hardening
```

---

# 26. Definition of Done

A feature is considered done only when:

- The implementation works.
- Its interface is defined.
- Inputs are validated.
- Outputs are validated.
- Errors are handled.
- Tests exist.
- Fixture behavior exists where external APIs are involved.
- The feature does not violate `rules.md`.
- Documentation remains consistent.
- Existing functionality continues to work.

A feature is **not done** merely because the code compiles.

---

# 27. AI Agent Working Rules for Phases

When an AI agent is asked to implement a phase:

### It should

1. Read `prd.md`.
2. Read `architecture.md`.
3. Read `rules.md`.
4. Read this `phases.md`.
5. Identify the current phase.
6. Inspect existing implementation.
7. Implement only the requested phase.
8. Run relevant tests.
9. Fix failures caused by its changes.
10. Report what was implemented and verified.

### It should not

- Implement later phases automatically.
- Rewrite unrelated files.
- Add speculative features.
- Replace working components without reason.
- Skip tests to save time.
- Hide errors.
- Claim functionality works without verification.
- Build a vague "complete" version covering every feature superficially.

---

# 28. Phase Reporting Format

At the end of each phase, the implementation agent should report:

```text
Phase: <name>

Implemented:
- ...

Files changed:
- ...

Tests run:
- ...

Tests passed:
- ...

Known limitations:
- ...

Next recommended phase:
- ...
```

This makes progress measurable and prevents the project from becoming a collection of partially working components.

---

# 29. First Implementation Milestone

The first implementation milestone is deliberately narrow:

> **Get the static-data ingestion tools working correctly.**

Specifically:

```text
fetch_airports.py
fetch_visa_rules.py
```

Then verify:

```text
airports.json
visa_rules.json
```

before building:

- Agents
- LangGraph
- API workflow
- Frontend

This gives Safarnama a reliable data foundation before application complexity is introduced.

---

# 30. Guiding Principle

The project should never optimize for:

> "How quickly can we generate the whole application?"

It should optimize for:

> **"How reliably can we build and verify one layer before depending on it?"**

A small, verified working system is more valuable than a large implementation where every component is only partially functional.

Safarnama should therefore grow as:

```text
Reliable tool
      ↓
Reliable component
      ↓
Reliable node
      ↓
Reliable workflow
      ↓
Reliable API
      ↓
Reliable product
```
