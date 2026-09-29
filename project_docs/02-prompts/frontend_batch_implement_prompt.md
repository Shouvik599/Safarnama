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

Then stop.

Do not begin the next batch.
