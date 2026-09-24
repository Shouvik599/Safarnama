You are working on the existing **Safarnama — Autonomous Multi-Agent Travel Planner** project.

This is an existing project. You are taking over the current codebase, not starting a new implementation.

## 1. Understand the project first

Before making any changes, read these project documents from the repository:

1. `prd.md`
2. `architecture.md`
3. `rules.md`
4. `phases.md`
5. `design.md`
6. `memory.md`

Then inspect the relevant existing source code and tests.

Treat these as the project's source of truth.

In particular:

* `prd.md` → what the product should do
* `architecture.md` → how the system should be structured
* `rules.md` → implementation constraints and AI behavior rules
* `phases.md` → how the project is being built incrementally
* `design.md` → visual/design direction
* `memory.md` → current implementation state and handoff context

Do not assume that the documentation and implementation are identical. Use `memory.md` to understand the previous progress, then verify the actual repository state.

---

# 2. Current Task

### Task:

> **[REPLACE THIS SECTION WITH THE SPECIFIC TASK]**

Examples:

* Implement Phase 2 — Static Data Access Layer.
* Fix the airport ingestion test failure.
* Add validation for the visa dataset.
* Refactor the existing weather tool.
* Investigate why the API endpoint returns a 422.
* Add unit tests for the calculator.
* Review the current Phase 1 implementation without making changes.

---

# 3. Scope

Work only on the task described above.

Before coding, determine:

* Which existing files are relevant.
* Which project phase this belongs to.
* What existing functionality it depends on.
* What existing functionality could be affected.

Do NOT automatically implement future phases.

Do NOT rewrite working code simply because you would structure it differently.

Do NOT introduce speculative features.

If completing the task requires changing something outside the requested scope, explain why before making a significant architectural change.

---

# 4. Existing Implementation Takes Priority Over Assumptions

Inspect the existing implementation before creating anything.

If something already exists:

* Reuse it where appropriate.
* Improve it only when necessary.
* Preserve its public behavior unless the task requires changing it.
* Avoid duplicate implementations.

If `memory.md` says something was completed but the repository does not contain it, trust the actual repository after investigating and report the discrepancy.

---

# 5. Follow Project Rules

You MUST follow `rules.md`.

Important examples:

* Python 3.11+
* Use `uv` for Python dependencies.
* Never use `pip`.
* Frontend dependencies use `pnpm`, never `npm`.
* Use Pydantic for structured domain contracts.
* Keep deterministic calculations outside the LLM.
* Do not allow LLMs to invent factual travel entities or visa requirements.
* Use fixture-first testing for external APIs.
* Keep provider-specific logic behind tool/provider interfaces.
* Do not hide errors.
* Do not add unnecessary dependencies.
* Keep the implementation modular and testable.

If `rules.md` contains a more specific rule than a general coding convention, follow `rules.md`.

---

# 6. Before Coding

Briefly determine:

```text
Current phase:
Relevant files:
Existing implementation:
Task dependencies:
Expected changes:
Tests that should be affected:
```

Then implement the task.

Do not spend excessive time explaining the plan if the task is straightforward.

---

# 7. Implementation Rules

While working:

* Make the smallest reasonable changes.
* Follow the existing project structure.
* Preserve existing behavior outside the task.
* Use existing abstractions before creating new ones.
* Keep code readable and maintainable.
* Validate external data at boundaries.
* Add/update tests for behavior you change.
* Do not modify unrelated files.
* Do not silently change project requirements.
* Do not claim something works without verification.

If you discover an ambiguity in the requirements that materially affects implementation, stop and ask rather than inventing a requirement.

---

# 8. Testing and Verification

After implementation:

1. Run tests directly related to the change.
2. Run relevant existing tests.
3. Run lint/type/format checks used by the project where applicable.
4. Manually verify the behavior when appropriate.
5. Fix failures caused by your changes.
6. Inspect the final diff.

Do not skip tests merely because the change appears small.

If a test cannot be run, clearly state why.

---

# 9. Memory Update

If the task changes the project's implementation state, update:

`memory.md`

Keep it concise.

Record only information useful to the next AI agent, such as:

* Current phase
* Completed functionality
* Files/modules changed
* Important implementation decisions
* Tests and verification results
* Known limitations
* Current unresolved issues
* Next recommended task

Do not copy source code into `memory.md`.

Do not duplicate the contents of the project documentation.

If the task was only an investigation/review and did not change the implementation, do not unnecessarily modify `memory.md`.

---

# 10. Stop Condition

When the requested task is complete:

**STOP.**

Do not automatically continue into the next phase.

Do not implement "obvious next steps" unless they are required for the requested task.

---

# 11. Final Report

At the end, provide:

```text
Task:
<what was requested>

Implemented:
- ...

Files changed:
- ...

Tests/checks run:
- ...

Verification:
- ...

Known issues/limitations:
- ...

Memory updated:
- Yes / No

Next recommended step:
- ...
```

If something was intentionally not changed, mention it briefly.

The goal is to leave the repository in a verified, understandable state for the next AI or IDE.
