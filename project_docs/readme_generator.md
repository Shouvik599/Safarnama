Create or update the `README.md` for the existing project:

# Safarnama — Autonomous Multi-Agent Travel Planner

This project may be opened in a different IDE, handled by a different AI coding tool, or continued in a new chat. Therefore, the README must be understandable as a standalone entry point for a new developer or AI agent.

## First: Understand the Project

Before writing the README, inspect the repository and read:

1. `prd.md`
2. `architecture.md`
3. `rules.md`
4. `phases.md`
5. `design.md`
6. `memory.md`
7. The actual source code, configuration files, tests, and existing data files.

Do not assume the planned architecture is identical to the current implementation.

Use:

* `prd.md` for intended product requirements
* `architecture.md` for intended architecture
* `rules.md` for development constraints
* `phases.md` for the implementation roadmap
* `design.md` for visual direction
* `memory.md` for current project progress
* The actual repository for what is currently implemented

The README must accurately distinguish between:

* Planned functionality
* Currently implemented functionality
* Partially implemented functionality
* Future functionality

Do not claim that functionality exists merely because it is described in the documentation.

---

# README Objective

Create a professional, developer-friendly `README.md` that explains Safarnama clearly to:

1. A human developer joining the project
2. A new AI coding agent taking over the repository
3. Someone evaluating the project
4. Someone who wants to run the project locally

The README should be concise enough to remain useful, but detailed enough that a developer can understand the project without reading every source file.

---

# Required README Structure

Use the following structure where applicable.

## 1. Project Title

```text
Safarnama — Autonomous Multi-Agent Travel Planner
```

Include a short description explaining what Safarnama does.

The description should reflect the actual project rather than marketing claims.

---

## 2. Project Status

Clearly state the current implementation status.

For example:

```text
Status: In active development
Current Phase: Phase X — <phase name>
```

Use `memory.md` and the actual repository to determine this.

If a phase is incomplete, say so.

Do not present the project as production-ready unless the repository actually supports that claim.

---

## 3. What is Safarnama?

Explain:

* The problem it solves
* Who it is intended for
* What makes the planner different from a generic chatbot
* The role of structured travel constraints
* The role of tools, external data, deterministic calculations, and AI reasoning

Keep this section understandable to someone who has never seen the project.

---

## 4. Core Capabilities

Document the capabilities that are actually implemented.

Where appropriate, describe planned capabilities separately.

Potential areas include:

* Domestic travel planning
* International travel planning
* Multi-destination trips
* Traveler information
* Budget-aware planning
* Transportation
* Hotels
* Attractions
* Local food
* Weather adaptation
* Visa information
* Flexible dates
* Budget optimization
* Human-in-the-loop decisions

Do not list a capability as implemented unless the code supports it.

---

## 5. Key Product Principles

Explain the important Safarnama principles, such as:

* User constraints are explicit.
* The planner should not silently invent preferences.
* Must-visit places should not be silently removed.
* Deterministic calculations are performed outside the LLM.
* Real external data should be preferred over generated factual data.
* Estimated information must be clearly labeled.
* Visa information must not be fabricated.
* External providers are accessed through tool/provider abstractions.
* The system is built incrementally and tested phase by phase.

Only include principles supported by the project documentation.

---

## 6. Architecture Overview

Provide a concise architecture explanation.

Include an ASCII diagram where useful.

For example, conceptually:

```text
User
  ↓
API
  ↓
LangGraph Workflow
  ↓
Planning Nodes
  ↓
Tool Interfaces
  ↓
Provider APIs / Static Data
  ↓
Validated Structured Results
  ↓
Budget / Optimization
  ↓
Itinerary
```

Adapt this to the actual implementation.

Clearly distinguish implemented architecture from planned architecture where necessary.

---

## 7. Technology Stack

Document the technologies actually used by the project.

Examples may include:

* Python
* Python version
* LangGraph
* Pydantic
* FastAPI
* pytest
* Ruff
* LLM provider
* External APIs
* Frontend technology

Do not add technologies simply because they are mentioned in future plans.

Include version information where it can be reliably determined from the repository.

---

## 8. Repository Structure

Show the current repository structure.

Example:

```text
safarnama/
├── data/
├── scripts/
├── src/
├── tests/
├── static/
├── prd.md
├── architecture.md
├── rules.md
├── phases.md
├── design.md
├── memory.md
└── README.md
```

Only show files/directories that actually exist.

Briefly explain the purpose of important directories.

Do not create a fictional repository structure based solely on the planned architecture.

---

## 9. Development Phases

Give a concise overview of the phased development strategy from `phases.md`.

Explain that Safarnama is deliberately built incrementally:

```text
Foundation
   ↓
Static Data
   ↓
Tools
   ↓
API
   ↓
Domain Models
   ↓
Planning Functions
   ↓
LangGraph
   ↓
Optimization
   ↓
Complete Workflow
   ↓
Frontend
   ↓
Hardening
```

Show which phase is currently complete/in progress.

Do not duplicate the full contents of `phases.md`.

---

## 10. Current Implementation

This section is particularly important.

Use `memory.md` and the actual repository to explain:

* What has already been built
* What currently works
* What tests exist
* What remains incomplete
* What the next implementation milestone is

This should be the quickest section for a new AI agent to understand the current state.

---

## 11. Setup

Provide accurate local setup instructions based on the actual project.

Use `uv` for Python dependency management.

Do NOT use `pip`.

If a frontend exists, use `pnpm` rather than `npm`.

Include only commands that have been verified against the repository.

For example, where applicable:

```bash
uv sync
uv run pytest
uv run ruff check .
```

Do not invent commands.

---

## 12. Environment Variables

Document environment variables that the application actually requires.

Use `.env.example` as the primary reference.

For each important variable, explain briefly what it is used for.

Never include actual secrets, API keys, tokens, or credentials.

---

## 13. Running the Project

Explain how to run the currently implemented application.

Include:

* Development server
* CLI, if implemented
* API
* Frontend, if implemented
* Static data ingestion commands, if implemented

Only document commands that actually work in the current repository.

---

## 14. Testing

Explain how to run the tests.

Include relevant commands such as:

```bash
uv run pytest
```

and other verified project checks.

Briefly explain the testing philosophy:

* Unit tests
* Integration tests
* Fixture-first external API testing
* Deterministic calculation testing

Do not claim test coverage numbers unless they have actually been measured.

---

## 15. Static Data

If static datasets exist, document:

* What datasets are used
* Where they come from
* Their purpose
* Where generated files are stored
* How ingestion is performed
* Whether ingestion is manual/on-demand or automated

For Safarnama's current design, distinguish static baseline data from live verification.

---

## 16. External APIs / Providers

Document external integrations that are actually implemented.

For each provider, explain:

```text
Purpose
Interface/tool
Provider
Configuration
Fixture support
Fallback behavior
```

Do not expose credentials.

Do not document future providers as though they already exist.

---

## 17. AI / LLM Behavior

Explain the role of the LLM in the system.

Important distinctions should include:

* What the LLM is allowed to do
* What deterministic code handles
* What the fallback LLM is allowed to estimate
* What the LLM must never invent
* How structured outputs are validated

This section should make the project's anti-hallucination design clear.

---

## 18. Data and Reliability

Explain how Safarnama handles:

* External API failures
* Missing data
* Estimated values
* Static baseline data
* Live data
* Validation
* Warnings
* Errors
* Provenance where implemented

Keep this factual and implementation-oriented.

---

## 19. Budget and Calculation Rules

If implemented or sufficiently established by the architecture, explain that financial calculations are deterministic and not delegated to the LLM.

Document the major cost categories where appropriate:

* Transport
* Hotels
* Food
* Activities
* Visa
* Miscellaneous
* Contingency

Do not duplicate the full budget specification.

---

## 20. Contributing / Development Rules

Explain the project's incremental development philosophy.

For example:

```text
Read documentation
      ↓
Understand current phase
      ↓
Implement one capability
      ↓
Test
      ↓
Verify
      ↓
Update memory.md
      ↓
Move to next phase
```

Mention the important development constraints from `rules.md`, especially:

* `uv`, not `pip`
* `pnpm`, not `npm`
* Tests before declaring a feature complete
* No unnecessary rewrites
* No implementing future phases automatically

---

## 21. Working With AI Coding Agents

Include a short section explaining how another AI should work on this repository.

Tell the AI agent to read:

```text
prd.md
architecture.md
rules.md
phases.md
design.md
memory.md
```

before making significant changes.

Explain that:

* `memory.md` is the implementation handoff file.
* The AI should inspect actual code rather than trusting documentation blindly.
* It should work on one phase/task at a time.
* It should test its changes.
* It should update `memory.md`.
* It should stop after completing the requested scope.

This section should make the repository portable across:

* GitHub Copilot
* Cursor
* Claude Code
* Codex
* Other coding agents

Do not make the README dependent on a specific IDE.

---

## 22. Roadmap

Provide a concise roadmap based on `phases.md`.

Clearly distinguish:

```text
Completed
In Progress
Planned
```

Do not turn planned functionality into completed functionality.

---

## 23. Design Direction

Briefly document the current visual identity from `design.md`:

* Warm Indian-inspired aesthetic
* Light theme
* Safarnama Saffron
* Typography
* Cultural/travel identity

Do not reproduce the complete design document.

---

## 24. License

If a license already exists in the repository, document it.

If no license has been selected, do NOT invent one.

Instead state:

```text
License: Not yet specified.
```

---

# README Quality Rules

The final README must be:

* Accurate
* Developer-friendly
* IDE-independent
* AI-agent-friendly
* Easy to scan
* Professional
* Concise
* Based on the actual repository

Avoid:

* Marketing fluff
* Unsupported claims
* Fictional commands
* Fictional APIs
* Fictional files
* Duplicate documentation
* Excessive explanation
* Pretending future features are implemented

Use Markdown headings, tables, code blocks, and diagrams where they improve readability.

---

# Final Verification

Before finishing:

1. Compare the README against the actual repository.
2. Check every command documented in the README against the project configuration.
3. Check the current implementation status against `memory.md`.
4. Ensure planned features are clearly marked as planned.
5. Ensure no secrets are included.
6. Ensure the repository structure shown is accurate.
7. Ensure setup instructions use `uv` and, where applicable, `pnpm`.
8. Ensure the README does not contradict `prd.md`, `architecture.md`, `rules.md`, or `phases.md`.
9. Do not modify application code unless absolutely necessary to make the README accurate.

Finally, report:

```text
README created/updated:
- Yes

Files changed:
- README.md
- <anything else, if necessary>

Current project phase:
- ...

Implementation status reflected:
- ...

Commands verified:
- ...

Known documentation gaps:
- ...
```
