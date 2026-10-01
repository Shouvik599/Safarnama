## Batch Configuration

```text
BATCH_NUMBER: [N]
STITCH_PROJECT: Safarnama
PREVIOUS_BATCH: Batch [N-1]
NEXT_BATCH: Batch [N+1]

CURRENT_BATCH_SCREENS:
[Paste the finalized screen list for this batch]
```

## Implementation Plan

First read:

```text
project_docs/01-planning/frontend_batch_plans/batch-[N]-plan.md
```

Validate the plan against the current repository before coding.

If the plan conflicts with the actual repository state, follow the existing repository architecture and make the smallest necessary adjustment. Do not silently invent unrelated functionality.

## Scope

Implement **ONLY Batch [N]**.

The implementation must be a **working vertical slice**, not static UI.

Implement:

- Stitch-accurate UI
- Real interactions
- Application state
- Proper routes
- Forward navigation
- Backward navigation
- State persistence
- Validation
- Required derived values
- Relevant mock/API/service integration
- Responsive behavior
- Accessibility
- Integration with the previous batch

## Existing Project

Inspect the current repository before making changes.

Reuse existing:

- Components
- State/context
- Types/models
- Routes
- Utilities
- Services
- Styling/design tokens
- Testing patterns

Do not create duplicate state or parallel implementations when an existing mechanism can be extended.

## Backend / Data Boundary

Do not invent:

- APIs
- Credentials
- Providers
- Live data
- Backend capabilities

If a required backend capability does not exist, use an existing mock/fixture/service boundary where appropriate.

If a new abstraction is genuinely required, create the smallest appropriate abstraction and avoid unrelated backend changes.

## Stitch

Use the existing **Safarnama** Stitch project.

Inspect the relevant designs for this batch and implement them in the existing frontend.

Do not create a separate Stitch project.

Prioritize:

- Layout
- Spacing
- Typography
- Colors
- Component structure
- States
- Interaction behavior
- Responsive behavior

Do not introduce unrelated visual redesigns.

## Navigation and State

Verify the complete flow:

```text
Previous Batch
      ↓
Current Batch Screen 1
      ↓
Current Batch Screen 2
      ↓
...
      ↓
Current Batch Final Screen
      ↓
Next Batch entry point
```

Verify that:

- Forward navigation works.
- Back navigation works.
- Previously entered values remain available.
- Editing earlier values updates dependent state correctly.
- Validation prevents invalid progression.
- Refresh/re-entry behavior follows the existing application architecture.
- The state produced by this batch is usable by the next batch.

## Verification

Run the application and verify the previous-batch → current-batch flow.

Verify every screen in the current batch.

Check:

- Forward navigation
- Backward navigation
- State persistence
- Editing previous inputs
- Validation
- Interactive controls
- Derived values
- Empty/default states
- Error states where applicable
- Responsive desktop behavior
- Responsive mobile behavior
- Keyboard accessibility
- Focus behavior
- Runtime errors
- Build errors
- Type errors
- Relevant automated tests

Compare the implemented screens against the corresponding designs in the **Safarnama** Stitch project and fix important visual discrepancies.

## Scope Control

Do NOT:

- Implement the next batch.
- Implement future user-facing screens.
- Rewrite unrelated architecture.
- Replace working existing components unnecessarily.
- Add speculative features.
- Create duplicate state systems.
- Create unrelated backend functionality.

If a future-batch dependency is necessary, create only the smallest state/interface needed to support it.

## Project Documentation

After implementation and successful verification, update the existing project memory/documentation with:

- Batch completion status
- Important implementation decisions
- New routes
- New state/data structures
- Important reusable components
- Verification performed
- Known limitations
- Relevant information needed by the next batch

Do not create unnecessary documentation files.

## Definition of Done

Batch [N] is complete only when:

- All current-batch screens are implemented.
- They are integrated with the previous batch.
- Required interactions work.
- State flows correctly.
- Validation works.
- Navigation works in both directions.
- Responsive behavior is verified.
- Accessibility basics are verified.
- Relevant tests pass.
- The application builds/runs successfully.
- Important visual discrepancies against Stitch are resolved.
- Project memory/documentation is updated.
- No next-batch user-facing functionality has been implemented.

## Final Report

After successful verification, provide a concise report containing:

1. Screens implemented.
2. Routes added/changed.
3. State/data changes.
4. Components created/reused.
5. Backend/mock/service changes.
6. Tests and verification performed.
7. Stitch visual verification status.
8. Documentation/memory updated.
9. Known limitations or follow-up items.

# Project Documentation & Memory Update

After implementation and **only after successful verification**, update the existing project documentation and memory.

The documentation update is a required part of completing the batch. Do not merely mention documentation updates in the final report — **actually modify the relevant existing Markdown files in the repository.**

## 1. Update `memory.md`

Locate the project's existing `memory.md`.

Update it to reflect the completed Batch [N] implementation.

Preserve all existing project history and structure. Do not replace or recreate the memory file.

Record:

* Batch [N] completion status
* Screens implemented
* Routes added or changed
* State/data structures introduced or extended
* Important implementation decisions
* Important reusable components
* Integration with Batch [N-1]
* State/data contract required by Batch [N+1]
* Verification and testing performed
* Known limitations
* Important decisions or constraints that future batches must preserve

If `memory.md` already contains a batch/status section, update that section rather than creating a duplicate section.

Do not remove information from previous batches unless it is demonstrably obsolete.

---

## 2. Update Relevant Project Documentation

Inspect the existing documentation structure before making changes.

Update the relevant existing documentation under:

```text
project_docs/
```

Possible relevant documentation may include existing files covering:

* Architecture
* Frontend architecture
* Routes
* State management
* Data models
* Design decisions
* Screen implementation status
* Batch progress
* Project phases
* Frontend implementation notes
* Data/state contracts

Only update documentation that is genuinely relevant to the Batch [N] implementation.

**Do not create unnecessary documentation files.**

Prefer updating existing documents over creating new ones.

---

## 3. Update the Batch [N] Plan / Status

Read:

```text
project_docs/01-planning/frontend_batch_plans/batch-[N]-plan.md
```

If the existing plan contains a completion/status section, update it to reflect the actual implementation status.

Do not rewrite the original implementation plan unnecessarily.

If implementation required a deviation from the plan because of the actual repository architecture, document the deviation clearly:

* What was different
* Why the adjustment was necessary
* What implementation decision was made instead

Do not silently overwrite the original plan.

---

## 4. Record Batch [N+1] Handoff Information

Document only the information that Batch [N+1] genuinely needs from Batch [N].

This may include:

* Routes available to Batch [N+1]
* State produced by Batch [N]
* Data structures/types that Batch [N+1] can consume
* Existing reusable components
* Navigation entry points
* Important assumptions
* Known limitations
* Dependencies that Batch [N+1] must be aware of

Do **not** implement Batch [N+1] functionality.

The documentation should make it possible for the next batch to understand the current state without relying on undocumented assumptions.

---

## 5. Preserve Project Memory Continuity

When updating documentation:

* Preserve terminology already established by the project.
* Preserve existing architecture decisions.
* Do not introduce a competing architecture description.
* Do not create duplicate sources of truth.
* Do not document speculative functionality as implemented.
* Do not document future screens as completed.
* Do not claim APIs, services, or integrations that do not actually exist.
* Clearly distinguish implemented functionality from planned/future functionality.

Use the following conceptual status where appropriate:

```text
Implemented
Planned
Known Limitation
Future Dependency
```

---

## 6. Verify Documentation Against the Repository

Before finishing the batch, verify that the updated documentation matches the actual implementation.

Check that:

* Documented routes actually exist.
* Documented state structures actually exist.
* Documented components actually exist.
* Documented services actually exist.
* Documented Batch [N] screens are actually implemented.
* Batch [N+1] handoff information reflects the real application state.
* No future functionality is incorrectly described as complete.

Do not claim a documentation update was completed unless the corresponding file was actually modified.

---

## 7. Final Documentation Record

In the final implementation report, explicitly list the documentation files that were actually updated.

For example:

```text
Documentation updated:
- memory.md
- project_docs/...
- project_docs/01-planning/frontend_batch_plans/batch-[N]-plan.md
```

Only list files that were genuinely modified.

The documentation update is part of the **Definition of Done** for the batch.

Use these skills as required:
design-taste-frontend ~\.agents\skills\design-taste-frontend
huashu-design         ~\.agents\skills\huashu-design
impeccable            ~\.agents\skills\impeccable
ui-ux-pro-max         ~\.agents\skills\ui-ux-pro-max


Then stop.

Do not begin the next batch.
