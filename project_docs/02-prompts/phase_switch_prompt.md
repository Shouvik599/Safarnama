We have completed **Phase [PREVIOUS PHASE] — [PREVIOUS PHASE NAME]**.

Now proceed to:

**Phase [NEXT PHASE] — [NEXT PHASE NAME]**

## 1. Establish Current Context

Before making changes, determine the actual current project state.

Read:

* `memory.md`
* `phases.md`
* `rules.md`
* `architecture.md`
* `prd.md`
* `README.md`
* `design.md` where relevant

Then inspect the existing implementation and tests from the previous phase.

### Context rule

Use the sources available to you according to this priority:

1. **Decisions explicitly made in the current conversation**, if this is the same chat.
2. **`memory.md`**, which records the latest project handoff state.
3. **The actual code, tests, and configuration in the repository.**
4. **Project documentation** (`prd.md`, `architecture.md`, `phases.md`, `rules.md`, `design.md`, `README.md`).

If this is a new chat or a different IDE, do **not** assume you have any context from the previous AI/session. Reconstruct the current state from the repository and `memory.md`.

Do not assume documentation or `memory.md` is perfectly accurate. Verify important claims against the actual implementation.

---

## 2. Documentation Synchronization

Before implementing the phase, identify any project decisions that are:

* New
* Changed
* Missing
* Outdated
* Contradictory

This includes decisions made in the current conversation, if available.

Update the appropriate documentation:

* `prd.md`
* `architecture.md`
* `phases.md`
* `rules.md`
* `design.md`
* `README.md`

Do not invent requirements or make undocumented design decisions.

If documentation conflicts with an explicitly agreed newer decision, update the affected documentation so there is one consistent source of truth.

---

## 3. Phase Scope

Implement **only Phase [NEXT PHASE]**.

Do not implement later phases or unrelated improvements.

Reuse existing work.

Do not rewrite working code unnecessarily.

Do not introduce speculative architecture.

If a problem in an earlier phase prevents this phase from being implemented correctly, investigate it and make only the necessary correction.

---

## 4. Implementation Requirements

Follow:

* `phases.md`
* `architecture.md`
* `rules.md`
* `prd.md`

Keep the implementation:

* Modular
* Testable
* Maintainable
* Deterministic where applicable
* Consistent with the existing architecture

---

## 5. Verification

After implementation:

1. Run tests for this phase.
2. Run relevant existing tests.
3. Run applicable lint/format/type checks.
4. Manually verify important behavior where appropriate.
5. Fix failures caused by your changes.
6. Inspect the final diff.
7. Verify that documentation matches the resulting implementation.

Do not claim completion without verification.

---

## 6. Update Project Memory

Once the phase is genuinely complete, update `memory.md` with:

* Current phase
* Completed work
* Files changed
* Important implementation decisions
* Tests/checks and results
* Known issues/limitations
* Documentation updates
* Next recommended phase

Keep `memory.md` concise. It is a **handoff/context file**, not a copy of the documentation or source code.

---

## 7. Stop

When Phase [NEXT PHASE] is complete, verified, and documentation is synchronized:

**STOP.**

Do not automatically start the next phase.

---

## Final Report

```text
Phase: [NEXT PHASE] — [NEXT PHASE NAME]

Implemented:
- ...

Files changed:
- ...

Documentation synchronized:
- prd.md: Yes/No
- architecture.md: Yes/No
- phases.md: Yes/No
- rules.md: Yes/No
- design.md: Yes/No
- README.md: Yes/No
- memory.md: Yes/No

Tests/checks run:
- ...

Verification:
- ...

Known issues/limitations:
- ...

Next recommended phase:
- [NEXT PHASE + 1] — [NAME]
```
