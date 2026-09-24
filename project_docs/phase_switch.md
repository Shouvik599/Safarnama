We have completed **Phase [PREVIOUS PHASE] — [PREVIOUS PHASE NAME]**.

Now proceed to:

**Phase [NEXT PHASE] — [NEXT PHASE NAME]**

Before making changes:

1. Read the requirements for this phase in `phases.md`.
2. Review `memory.md` to confirm the actual current project state.
3. Inspect the implementation and tests from the previous phase.
4. Review `rules.md` and `architecture.md` for relevant constraints.
5. Review `prd.md` and `README.md` for the current documented product state.
6. Consider **all decisions and requirements we have discussed in this conversation**, including decisions that may not yet be reflected in the project documentation.

Do not assume the documentation is fully up to date. The current conversation may contain newer decisions.

### Documentation Synchronization

Before implementing the phase, identify any decisions we have made during this conversation that are missing, outdated, or inconsistent in:

* `prd.md`
* `architecture.md`
* `phases.md`
* `README.md`
* `rules.md`
* `design.md` where relevant

Update the appropriate documentation files so they reflect the **latest agreed project decisions**.

Do not invent new requirements. Only document decisions that were actually established.

If a new decision conflicts with an existing document, update the affected document rather than leaving contradictory information.

### Scope

Implement **only Phase [NEXT PHASE]**.

Do not implement later phases or unrelated improvements.

Reuse existing work and avoid unnecessary rewrites or speculative architecture.

### Verification

After implementation:

1. Run the new/updated tests for this phase.
2. Run relevant existing tests.
3. Run applicable lint/format/type checks.
4. Manually verify important behavior where appropriate.
5. Fix failures caused by your changes.
6. Inspect the final diff.
7. Verify that the documentation accurately describes the resulting implementation.

Do not claim the phase is complete without verification.

### Memory

Once the phase is genuinely complete, update `memory.md` with:

* Current phase
* Completed work
* Files changed
* Important implementation decisions
* Tests/checks and results
* Known issues/limitations
* Documentation updates made
* Next recommended phase

Keep `memory.md` concise.

### Stop Condition

When Phase [NEXT PHASE] is complete, verified, and the documentation is synchronized:

**STOP.**

Do not automatically start the next phase.

### Final Report

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
