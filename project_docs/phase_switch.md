We have completed **Phase [PREVIOUS PHASE] — [PREVIOUS PHASE NAME]**.

Now proceed to:

# Phase [NEXT PHASE] — [NEXT PHASE NAME]

Before making changes:

1. Read the requirements for this phase in `phases.md`.
2. Review `memory.md` to confirm the actual current project state.
3. Inspect the implementation and tests produced by the previous phase.
4. Verify that the previous phase is actually in a usable state before building on top of it.
5. Review `rules.md` for any constraints relevant to this phase.
6. Review `architecture.md` if this phase involves architectural decisions.

Do not assume the previous phase is correct simply because it was marked complete. Verify the relevant implementation and tests.

## Scope

Implement **only this phase**.

Do not implement functionality belonging to later phases.

Reuse the existing implementation wherever appropriate. Do not rewrite working code unnecessarily or introduce speculative architecture.

## Implementation

Follow the exact requirements defined in:

* `phases.md`
* `architecture.md`
* `rules.md`
* `prd.md`

Keep the implementation:

* Modular
* Testable
* Deterministic where applicable
* Consistent with the existing architecture
* Compatible with the completed previous phases

If you discover that the current architecture or previous implementation has a problem that prevents this phase from being implemented correctly, explain the issue before making a significant architectural change.

## Verification

After implementation:

1. Run the new/updated tests for this phase.
2. Run the relevant existing tests from previous phases.
3. Run lint/format/type checks used by the project where applicable.
4. Manually verify important behavior where appropriate.
5. Fix failures caused by your changes.
6. Inspect the final diff.

Do not claim the phase is complete unless the implementation has actually been verified.

## Memory

Once the phase is genuinely complete, update `memory.md`.

Record:

* Current phase
* What was implemented
* Important files changed
* Important implementation decisions
* Tests/checks performed
* Test results
* Known limitations/issues
* Next recommended phase

Keep `memory.md` concise. Do not duplicate the project documentation or source code.

## Stop Condition

When Phase [NEXT PHASE] is complete and verified:

**STOP.**

Do not automatically start Phase [NEXT PHASE + 1].

Do not add unrelated improvements unless they are required to complete the current phase.

## Final Report

Provide:

```text
Phase: [NEXT PHASE] — [NEXT PHASE NAME]

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

Next recommended phase:
- [NEXT PHASE + 1] — [NAME]
```
