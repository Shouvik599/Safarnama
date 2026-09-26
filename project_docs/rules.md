# AI Development Rules
# Safarnama

**Document status:** V1 Engineering Rules  
**Purpose:** Define mandatory boundaries for AI-assisted development and implementation of Safarnama.

---

## 1. Core Principle

Safarnama must be built as a **modular, deterministic, testable travel-planning system**, not as a single LLM-driven application.

The AI/developer implementing this project must:

- Follow `prd.md` for product requirements.
- Follow `architecture.md` for system boundaries and component responsibilities.
- Preserve established product decisions unless the user explicitly changes them.
- Build incrementally rather than implementing the entire system at once.
- Ask before making a major architectural change.
- Prefer simple, explicit implementations over unnecessary abstractions.

---

# 2. Source-of-Truth Hierarchy

When implementing the project, use this priority:

1. **Current user instructions**
2. **`prd.md`**
3. **`architecture.md`**
4. **`rules.md`**
5. Existing implementation/code
6. General engineering conventions

If an existing specification conflicts with a later decision captured in these documents, the newer project decision takes precedence.

Do not silently reintroduce behavior that the product requirements explicitly changed.

---

# 3. Implementation Strategy

## 3.1 Build incrementally

Do not build the entire application in one pass.

The intended sequence is:

```text
Static Data
    ↓
Models + Deterministic Tools
    ↓
External Tools
    ↓
Individual Nodes
    ↓
LangGraph Workflow
    ↓
API / CLI
    ↓
Frontend
    ↓
Integration / Hardening
```

Each stage should be runnable and testable before the next stage is introduced.

## 3.2 Do not prematurely implement future functionality

If a feature is marked as future scope, do not implement it merely because it would be convenient.

Examples:

- Actual travel booking
- Arbitrary natural-language itinerary modification
- Detailed individual traveler profiles
- Automated periodic dataset ingestion
- Additional providers not required by the current phase

Create extension points where appropriate, but do not build unnecessary functionality.

---

# 4. Package and Library Management

## 4.1 Python package installation — mandatory `uv`

**Never use `pip` to install Python dependencies.**

Use `uv` for all Python dependency management.

Examples:

```bash
uv init
uv add pydantic
uv add langgraph
uv add fastapi
uv add pytest
```

For development dependencies, use the appropriate `uv` development-dependency mechanism.

Do not use:

```bash
pip install ...
pip3 install ...
```

unless the user explicitly overrides this rule.

## 4.2 Python execution

Prefer:

```bash
uv run ...
```

for project commands.

Examples:

```bash
uv run pytest
uv run python scripts/fetch_airports.py
uv run python scripts/fetch_visa_rules.py
```

Avoid relying on an unmanaged global Python environment.

## 4.3 Frontend package management — mandatory `pnpm`

For frontend dependencies and scripts, use **pnpm**, not npm.

Use:

```bash
pnpm install
pnpm add <package>
pnpm dev
pnpm build
```

Do not use:

```bash
npm install
npm i
npm run ...
```

unless explicitly instructed by the user.

Do not introduce another package manager without approval.

---

# 5. Python Version

The project targets:

**Python 3.11+**

Code should remain compatible with the project's declared Python version.

Do not introduce language features requiring a newer Python version without explicitly updating the project requirement.

---

# 6. Required Core Libraries

The architecture is based around:

- **LangGraph** — workflow orchestration
- **Pydantic v2** — data validation and structured contracts
- **FastAPI** — HTTP/API layer
- **pytest** — testing
- **Ruff** — linting/formatting
- **Google Gemini integration** — structured LLM reasoning where required
- **Open-Meteo, wttr.in, and OpenWeatherMap** — multi-tier weather data
- **ExchangeRate-API, FawazAhmed CDN, and Frankfurter** — multi-tier currency conversion
- **Tavily or configured search provider** — live search/verification where required

Provider-specific libraries should only be added when the corresponding integration is actually being implemented.

Do not add libraries speculatively.

---

# 7. Library Selection Rules

Before adding a dependency:

1. Check whether the Python standard library is sufficient.
2. Check whether an already-installed project dependency provides the capability.
3. Prefer a well-maintained, focused library.
4. Avoid duplicate libraries solving the same problem.
5. Add the smallest dependency that satisfies the requirement.
6. Update `pyproject.toml` through `uv`.
7. Add tests for behavior that depends on the new library.

Do not add a framework merely to solve a small utility problem.

---

# 8. Libraries and Approaches to Avoid

Avoid:

- `pip` for dependency installation
- `npm` for frontend package management
- Multiple overlapping HTTP clients without a reason
- Heavy frameworks for simple functionality
- Global mutable state
- Unstructured dictionaries where a Pydantic model is appropriate
- Direct provider API calls from LangGraph nodes
- LLM-based arithmetic
- Hidden network calls inside tests
- Hard-coded secrets
- Hard-coded provider credentials
- Copying large third-party libraries into the repository

If a library is proposed that materially changes the architecture, ask before introducing it.

---

# 9. LLM Rules

LLMs are reasoning components, not the application's source of truth for every piece of information.

## 9.1 LLMs may

Use LLMs for:

- Structured reasoning
- Itinerary composition
- Experience interpretation
- Policy reconciliation where explicitly designed
- Transforming retrieved information into validated structured outputs
- Estimation through the dedicated fallback LLM within its restricted scope

## 9.2 LLMs must not

LLMs must not:

- Perform financial arithmetic
- Add/subtract/multiply/divide trip costs
- Calculate contingency
- Calculate budget variance
- Calculate room requirements
- Perform currency arithmetic
- Decide numerical budget status based on mental arithmetic
- Invent live travel entities
- Invent hotels
- Invent restaurants
- Invent flights
- Invent booking links
- Invent visa requirements
- Invent visa eligibility
- Invent application procedures
- Treat generated knowledge as current live provider data

## 9.3 Prompt Isolation Rule

**All LLM prompt strings must be isolated in `src/prompts/` modules.**

Do NOT hardcode system prompts, user prompts, or instruction strings inline inside tool adapters (`src/tools/`), ingestion scripts (`scripts/`), or graph planning nodes (`src/planning/`).

Each domain or component using LLM prompts must import prompt builder functions from its dedicated file in `src/prompts/` (e.g., `estimator_prompts.py`, `visa_prompts.py`, `experience_prompts.py`).

---

# 10. Deterministic Calculation Rule

All financial arithmetic must go through the calculator layer.

Use:

```text
LLM / provider data
       ↓
Validated numeric inputs
       ↓
src/tools/calculator.py
       ↓
Budget result
```

Never:

```text
LLM
 ↓
"Total cost is ₹1,23,500"
```

without deterministic calculation.

The LLM can reason about trade-offs, but the calculator determines the numbers.

---

# 11. Fallback LLM Rules

Safarnama may use a **separate fallback LLM/model and API key** when normal data providers cannot provide sufficient numerical travel data.

The fallback LLM is **estimation-only**.

## Allowed

It may estimate:

- Hotel prices
- Transport prices
- Food costs
- Activity costs
- Miscellaneous travel costs

## Forbidden

It must not generate:

- Specific hotels
- Specific restaurants
- Specific flights
- Specific attractions
- Booking links
- Fake provider records
- Visa requirements
- Visa eligibility
- Visa documentation requirements
- Visa application procedures

Example:

Allowed:

> Estimated 3★ hotel cost: ₹7,000–₹10,000/night.

Not allowed:

> XYZ Hotel costs ₹8,500/night.

unless `XYZ Hotel` was actually returned by a trusted hotel/place provider.

Every fallback-LLM estimate must carry an explicit provenance/status indicating that it is estimated.

---

# 12. External Data Rules

Real-world travel entities should come from tools/providers.

The architectural direction is:

```text
Node
 ↓
Tool
 ↓
Provider adapter
 ↓
External API
```

Do not place provider-specific HTTP requests directly inside planning nodes.

This allows providers to be replaced without rewriting the planning logic.

---

# 13. Provider Fallback Order

For data that supports provider fallback:

```text
Primary provider
      ↓ failure / insufficient result
Alternate provider
      ↓ failure / insufficient result
Fallback LLM estimate
      ↓ impossible
Warning + omit
```

The fallback LLM should only be used where its restricted estimation role is appropriate.

Do not use it to fabricate missing entities.

---

# 14. Static Dataset Rules

Static data is generated by ingestion scripts and consumed by the application.

Current datasets:

```text
data/static/
├── airports.json
├── culinary_signatures.json
└── visa_rules.json
```

Ingestion scripts:

```text
scripts/
├── fetch_airports.py
└── fetch_visa_rules.py
```

## 14.1 Ingestion is on-demand

V1 does **not** require periodic runtime ingestion.

Run ingestion explicitly when needed.

Example:

```bash
uv run python scripts/fetch_airports.py
uv run python scripts/fetch_visa_rules.py
```

GitHub Actions may automate this later, but periodic automation is not a current runtime requirement.

## 14.2 Preserve existing data

If an upstream refresh is unavailable:

- Do not delete the existing dataset.
- Do not replace known-good data with an empty file.
- Keep the existing dataset usable.
- Log/report the refresh issue where appropriate.

---

# 15. Fixture Rules

External API wrappers must support offline fixtures for testability.

Fixtures live under:

```text
data/fixtures/
```

Tests should prefer fixtures rather than real network requests.

The project should not consume API credits during ordinary unit tests.

Examples:

```text
mock_flights.json
mock_forex.json
mock_hotels.json
mock_tavily_search.json
mock_weather.json
```

A test that requires the network must be explicitly identified as an integration/external test rather than silently making network requests.

---

# 16. Error Handling

Errors must be handled deliberately.

## 16.1 Never silently swallow errors

Avoid:

```python
try:
    ...
except Exception:
    pass
```

Do not suppress an error without recording or handling it.

## 16.2 Distinguish errors from warnings

### Error

The system cannot safely continue.

Examples:

- Invalid user input
- Corrupt required state
- Invalid required model
- Unrecoverable workflow failure

### Warning

The system can continue with reduced information quality.

Examples:

- Live price unavailable
- Fallback estimate used
- Static data used
- Low-confidence weather information
- Optional provider unavailable

Warnings should be retained in application state.

---

# 17. Error Recovery

When an external dependency fails:

1. Determine whether an alternate provider exists.
2. Use a fixture when running in fixture/test mode.
3. Use the fallback LLM only if the failure is within its allowed estimation scope.
4. Otherwise continue without the optional component where safe.
5. Add a warning.
6. Never fabricate the missing information.

For required information where safe continuation is impossible, return a structured error.

---

# 18. Validation Rules

Validate external data at the boundary where it enters the application.

Use Pydantic models for structured domain data.

Do not allow raw provider dictionaries to propagate through the entire graph when a validated domain model is appropriate.

Preferred flow:

```text
External API
    ↓
Provider response
    ↓
Validation
    ↓
Domain model
    ↓
Graph state
```

Invalid external responses should be rejected or handled through fallback logic.

---

# 19. LangGraph Rules

LangGraph is responsible for orchestration.

Nodes should have focused responsibilities.

Avoid creating one giant node that:

- Searches APIs
- Performs calculations
- Generates prompts
- Mutates unrelated state
- Handles every error
- Builds the final response

Instead use separate components.

The graph should make routing decisions explicit.

Conditional routing should be implemented in graph edges rather than hidden inside arbitrary node behavior wherever practical.

---

# 20. Node Rules

Each node should:

1. Accept known state.
2. Perform its defined responsibility.
3. Use tools where external data is required.
4. Validate outputs.
5. Update only the state fields it owns.
6. Preserve warnings/errors.
7. Avoid unrelated side effects.

Examples:

### Intake node

Responsible for normalization and resolution.

Not responsible for hotel search.

### Logistics node

Responsible for transportation and accommodation.

Not responsible for final budget arithmetic.

### Experience node

Responsible for attractions, food, weather-aware experiences.

Not responsible for financial reconciliation.

### Optimizer node

Responsible for budget evaluation and optimization orchestration.

It must use deterministic calculator output.

---

# 21. State Rules

Graph state should remain structured.

Prefer:

```python
TripContext
LogisticsPlan
ExperiencePlan
BudgetBreakdown
VisaVerdict
```

over large arbitrary dictionaries.

Use reducers intentionally for fields that need aggregation.

Do not allow unrelated nodes to mutate arbitrary state fields.

---

# 22. Pydantic Rules

Use Pydantic v2 for domain contracts.

Models should:

- Validate required fields.
- Constrain enumerated values.
- Validate numeric ranges.
- Reject clearly invalid data.
- Provide meaningful validation errors.

Avoid duplicating the same validation logic in multiple nodes.

Validation belongs at the model/boundary where possible.

---

# 23. API Rules

FastAPI routes should be thin.

A route should primarily:

1. Receive request.
2. Validate request.
3. Invoke the planning workflow.
4. Stream/return structured results.
5. Translate expected application errors into appropriate API responses.

Business logic should not live inside `routes.py`.

Do not call external travel APIs directly from FastAPI routes.

---

# 24. CLI Rules

The CLI must use the same workflow as the API.

Avoid maintaining separate planning implementations for:

```text
CLI
API
```

Both should call the same graph/workflow layer.

---

# 25. Frontend Rules

The frontend is a client of the backend planning system.

It should not contain:

- Travel-planning business logic
- Budget arithmetic
- Visa decision logic
- Provider API credentials
- Provider API calls requiring secrets

Frontend package management must use **pnpm**.

Do not commit API keys into frontend source code.

---

# 26. Secrets and Configuration

Never hard-code:

- API keys
- Tokens
- Passwords
- Private URLs containing credentials
- Provider secrets

Use environment variables.

Document required variables in:

```text
.env.example
```

The actual `.env` file must not be committed.

---

# 27. Logging Rules

Logs should help diagnose failures without leaking secrets.

Do not log:

- API keys
- Authorization headers
- Passwords
- Sensitive credentials

Useful log information includes:

- Node started/completed
- Tool/provider used
- Fallback invoked
- Warning generated
- Workflow failure
- Dataset ingestion result

Avoid excessive logging of complete provider payloads.

---

# 28. Testing Rules

Every meaningful component should have tests.

Minimum expectations:

- New calculator behavior → calculator tests
- New model → model validation tests
- New node → isolated node tests
- New graph routing → edge/workflow tests
- New provider tool → mocked/fixture tests
- New API behavior → API integration tests

Tests should be deterministic.

Avoid tests that depend on:

- Current weather
- Live prices
- Random external search results
- Provider availability

unless the test is explicitly an external integration test.

## 28.1 Dual Verification: Hermetic Offline & Live Network Testing

For all planning and tool functionalities that interact with external services (including Visa, Logistics, Experience, and future planning nodes):

1. **Hermetic Offline Test Suite (`uv run pytest`)**:
   - Must run 100% offline using fixtures and mocks (`SAFARNAMA_USE_FIXTURES=true`).
   - Must be fast, reproducible, and run in CI/CD without network or API key dependencies.
2. **Live Network Integration Test (`scripts/verify_live_nodes.py` or dedicated live runners)**:
   - Must execute in live network mode (`use_fixture=False`, `live_search_enabled=True`) against real external endpoints (e.g. Open-Meteo, Tavily, Gemini, RapidAPI, SerpApi, Nominatim).
   - Validates live API connectivity, API key authentication, real provider schema adherence, real-world pricing/policies, latency, and graceful error resilience.
   - Every planning functionality milestone MUST include both hermetic unit tests and live external verification before completion sign-off.

---

# 29. Test-Driven Development Preference

For new core functionality:

```text
Requirement
    ↓
Test
    ↓
Implementation
    ↓
Test passes
    ↓
Refactor
```

Do not write a large implementation first and postpone all testing until the end.

---

# 30. Formatting and Code Quality

Use Ruff for Python linting/formatting according to project configuration.

Code should favor:

- Clear names
- Small functions
- Explicit types
- Focused modules
- Minimal duplication
- Readable control flow

Do not optimize for cleverness.

Premature optimization is discouraged unless performance is an explicit requirement.

---

# 31. Performance Rules

Static datasets are intended to support fast local lookups.

Load/index static datasets appropriately rather than repeatedly reading the same JSON file for every lookup.

Do not add a database merely to solve a lookup problem that can be handled efficiently by the current static-data design.

Network calls should have sensible timeouts.

Avoid unnecessary duplicate API calls.

Reuse valid state/results during replanning where possible.

---

# 32. Network Rules

External calls should:

- Use timeouts.
- Handle non-success responses.
- Validate returned data.
- Have appropriate fallback behavior.
- Avoid unnecessary retries.
- Never block indefinitely.

Do not make network requests from import-time code.

---

# 33. Data Provenance Rules

Where practical, retain information about the origin of important values.

Possible statuses:

```text
LIVE_PROVIDER
ALTERNATE_PROVIDER
STATIC_DATASET
FIXTURE
FALLBACK_LLM_ESTIMATE
```

Do not represent fallback estimates as live prices.

User-facing output must explicitly label fallback-LLM estimates.

---

# 34. Financial Safety Rules

Budget values are estimates unless explicitly sourced as exact/current provider values.

The system must not present estimated costs as guaranteed prices.

All final arithmetic must come from deterministic code.

The optimizer must respect the hard quality guardrails defined in `prd.md`.

---

# 35. Visa Safety Rules

Visa information is higher-risk than ordinary travel estimates.

Never fabricate:

- Visa requirements
- Eligibility
- Required documents
- Application procedure
- Entry conditions

Static visa data is a baseline.

Current policy should be live-verified where required. Live policy reconciliation must use structured semantic LLM analysis rather than brittle regex or substring pattern matching, strictly rejecting foreign nationality exemptions, unconfirmed proposals, and waivers expired relative to planned travel dates.

If reliable information is unavailable, clearly report the limitation.

---

# 36. AI Decision Boundaries

The AI may decide:

- Which available experiences fit the user's preferences.
- How to structure an itinerary.
- How to explain trade-offs.
- Which valid planning option better satisfies qualitative preferences.

The AI must not independently override:

- Explicit user constraints without an approved product rule.
- Deterministic budget calculations.
- Validated model constraints.
- Hard quality guardrails.
- Visa safety restrictions.
- Provider data provenance.

---

# 37. Do Not Hallucinate

When required information is unavailable:

**Do not make up an answer merely to complete the itinerary.**

Instead:

1. Try the configured fallback.
2. If estimation is allowed, generate a clearly labeled estimate.
3. If estimation is not allowed, warn the user.
4. Continue only if the missing information is non-critical.
5. Otherwise report that the plan cannot be safely completed.

An incomplete but honest result is preferable to fabricated travel information.

---

# 38. Do Not Over-Engineer

Do not introduce:

- Microservices
- Message queues
- Databases
- Kubernetes
- Complex caching systems
- Additional orchestration frameworks

unless a concrete project requirement demonstrates the need.

V1 should remain a modular Python application with clear boundaries.

---

# 39. Do Not Rewrite Working Components Unnecessarily

When modifying the project:

- Preserve working behavior.
- Make the smallest change that satisfies the requirement.
- Avoid broad refactors unless requested.
- Update tests when behavior changes.
- Do not rewrite unrelated modules.

If a refactor is beneficial but not necessary, mention it separately rather than silently performing it.

---

# 40. Documentation Rules

When implementation changes architecture or behavior:

- Update the relevant documentation.
- Keep `prd.md` focused on product requirements.
- Keep `architecture.md` focused on system structure.
- Keep `rules.md` focused on engineering/AI boundaries.

Do not duplicate large sections unnecessarily between documents.

---

# 41. Change Management

Before making a change that affects:

- Product behavior
- Core architecture
- Technology stack
- Data contracts
- Budget rules
- Visa handling
- User interaction model

the AI should identify the impact and ask for confirmation when the change is not already authorized by the project documents.

Small implementation details do not require confirmation.

---

# 42. Current Build Rule

At the beginning of the implementation phase, **do not build the complete application**.

The first implementation target is the static-data foundation:

```text
scripts/fetch_airports.py
scripts/fetch_visa_rules.py
data/static/
tests/unit/test_static_data.py
```

Once that foundation works, move to the next phase.

---

# 43. Final AI Checklist

Before completing any implementation task, verify:

- [ ] Did I follow `prd.md`?
- [ ] Did I follow `architecture.md`?
- [ ] Did I follow these rules?
- [ ] Did I use `uv` for Python dependencies?
- [ ] Did I use `pnpm` for frontend dependencies?
- [ ] Did I avoid hard-coded secrets?
- [ ] Did I keep business logic out of API routes?
- [ ] Did I keep provider logic inside tools/adapters?
- [ ] Did I keep arithmetic deterministic?
- [ ] Did I avoid hallucinating real travel entities?
- [ ] Did I respect fallback-LLM restrictions?
- [ ] Did I validate external data?
- [ ] Did I handle errors explicitly?
- [ ] Did I add/update appropriate tests?
- [ ] Did I avoid unnecessary changes?
- [ ] Did I build only the requested phase?
- [ ] Did I place all new Pydantic models inside `src/models/`?
- [ ] Did I update `.env.example`, `README.md`, and project docs whenever `.env` variables changed?

---

# 44. Guiding Rule

When uncertain, prefer:

> **Explicit over implicit.  
> Validated over assumed.  
> Deterministic over generated.  
> Real data over hallucination.  
> Modular over coupled.  
> Tested over unverified.  
> Incremental over all-at-once.**

---

# 45. Pydantic Model Location

All Pydantic models **must** be defined inside `src/models/`.

Do not define Pydantic models inline inside scripts, tools, nodes, or any other module.

## 45.1 Required structure

```text
src/
  models/
    __init__.py   ← re-exports all public models
    visa.py       ← VisaOption, EnrichedVisaRecord
    <domain>.py   ← one file per domain (airports, itinerary, budget, …)
```

## 45.2 Re-export from `__init__.py`

Every model defined in `src/models/<domain>.py` must be re-exported from
`src/models/__init__.py` so callers can use the short import form:

```python
# Correct
from src.models import VisaOption, EnrichedVisaRecord

# Also acceptable for internal use
from src.models.visa import VisaOption
```

## 45.3 Scripts and tools importing models

Scripts under `scripts/` that need to import `src.models.*` must insert the
project root into `sys.path` at the top of the file:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.visa import EnrichedVisaRecord, VisaOption  # noqa: E402
```

## 45.4 Enforcement

- If a new Pydantic `BaseModel` subclass is created anywhere outside `src/models/`,
  move it to the appropriate `src/models/<domain>.py` file before completing the task.
- Never duplicate a model definition across multiple files — import it instead.

---

# 46. Environment Variable & Configuration Synchronization

Whenever any environment variable is added, modified, renamed, or removed in `.env`:

## 46.1 Update `.env.example` Immediately
- `.env.example` must mirror the exact section layout, variable names, category headers, and comments of `.env`.
- **Never commit real secrets or production API keys to `.env.example`**. Values must be empty (`VAR=`) or documented non-sensitive default values (e.g., `SAFARNAMA_USE_FIXTURES=false`).
- Include helpful comments indicating what the variable is used for and where a developer can register for free API credentials.

## 46.2 Update `README.md`
- Section 11 of `README.md` (Environment Variables) must be kept strictly synchronized with `.env.example`.
- Document every environment variable in the table, including its category, whether it is required or optional, its runtime/ingestion role, and its fallback behavior when omitted.

## 46.3 Update Project Documentation
- Any architecture or tooling specifications in `project_docs/architecture.md`, `project_docs/rules.md`, and `project_docs/memory.md` that discuss provider integration or environment configuration must be updated in lockstep.
- An implementation task or phase is **not complete** if environment variables were introduced or altered without updating `.env.example`, `README.md`, and the project docs.

