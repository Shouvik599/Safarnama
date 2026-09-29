# Safarnama — Frontend Batch Development

Implement one incremental frontend batch of Safarnama.

This is a connected application, not a collection of screen prototypes.

---

# Batch Configuration

```text
BATCH_NUMBER: [BATCH_NUMBER]

STITCH_PROJECT: [STITCH_PROJECT]

PREVIOUS_BATCH: [PREVIOUS_BATCH]

CURRENT_BATCH_SCREENS:
[SCREEN_NAMES]

NEXT_BATCH: [NEXT_BATCH]
```

These values define the scope of this execution.

Implement only `BATCH_NUMBER`.

---

# 1. Read the Batch Plan

Before coding, read:

```text
project_docs/frontend_batch_plans/batch-[BATCH_NUMBER]-plan.md
```

Treat it as the implementation plan produced by the planning phase.

Also inspect the current repository to ensure the plan still matches the actual codebase.

If the repository has changed since the plan was created, adapt to the current architecture rather than blindly following stale assumptions.

---

# 2. Repository Scope

Safarnama structure:

```text
frontend/       → frontend application
src/            → backend / AI / graph
data/           → fixtures/static data
project_docs/   → project documentation
scripts/        → scripts
tests/          → automated tests
```

For this frontend batch:

Prioritize:

```text
frontend/
project_docs/
data/
```

Inspect:

```text
src/
tests/
```

only where required for the current batch's functionality or integration.

Do not perform unrelated backend refactoring.

---

# 3. Stitch

Use Stitch MCP.

Open:

```text
[STITCH_PROJECT]
```

Inspect the designs for:

```text
[CURRENT_BATCH_SCREENS]
```

Use Stitch as the visual source of truth.

Do not create another Stitch project.

Match:

* layout
* spacing
* typography
* colors
* hierarchy
* components
* controls
* responsive behavior
* interaction affordances

---

# 4. Implement as a Vertical Slice

Do not implement static screens.

Implement:

* UI
* interactions
* application state
* validation
* routing
* navigation
* data flow
* loading/empty/error states where appropriate

The user must be able to actually complete the current flow.

---

# 5. Integrate With Previous Batch

Connect:

```text
[PREVIOUS_BATCH]
       ↓
[CURRENT_BATCH]
```

Reuse existing:

* state
* context
* routes
* components
* types
* services
* utilities
* validation

Do not create duplicate/incompatible state.

Preserve user data across:

* forward navigation
* back navigation
* editing previous screens
* returning to previous screens

---

# 6. State for Future Batches

The current batch may produce information required by:

```text
[NEXT_BATCH]
```

Store that information using the existing application state/model architecture.

Do not implement `NEXT_BATCH`.

---

# 7. Routing

Every current-batch screen must have a proper route.

Use the existing routing architecture.

Ensure:

* forward navigation
* backward navigation
* state preservation
* sensible incomplete/invalid navigation
* refresh/deep-link behavior where appropriate

Do not use temporary boolean screen switching as the primary routing mechanism.

---

# 8. Functionality

Implement the functionality identified in the batch plan.

Forms:

* accept input
* validate
* preserve values
* update state
* submit correctly

Search/select controls:

* search/filter
* select
* display selection
* edit/remove
* preserve state

Derived values must come from application state rather than hardcoded values.

Buttons must perform their intended actions.

---

# 9. Backend/Data Integration

Do not invent APIs, credentials, providers or backend functionality.

If the plan identifies existing backend functionality:

* use the existing API/service boundary
* follow existing data contracts
* do not duplicate backend logic in the frontend

If the plan identifies fixtures/mocks:

* use them appropriately
* clearly distinguish them from live data

If backend functionality is unavailable:

* implement the planned mock/provider boundary
* keep it compatible with future backend integration

Do not make unrelated changes to `src/`.

---

# 10. Reuse Existing Architecture

Before creating new code, inspect existing:

```text
frontend/src/components/
frontend/src/context/
frontend/src/types/
frontend/src/data/
frontend/src/screens/
```

Reuse existing components, context/state, types and utilities where appropriate.

Avoid:

* duplicate components
* duplicate state models
* unnecessary abstractions
* unrelated refactoring

---

# 11. Responsive + Accessibility

Verify:

* desktop
* tablet
* mobile

Also verify:

* semantic HTML
* labels
* keyboard navigation
* focus states
* accessible controls
* useful errors
* sufficient contrast
* touch-friendly controls

---

# 12. Verification

Run the application.

Verify:

```text
[PREVIOUS_BATCH]
       ↓
Current Screen 1
       ↓
Current Screen 2
       ↓
...
       ↓
Current Screen N
```

Test:

* forward navigation
* back navigation
* state persistence
* editing
* validation
* interactive controls
* relevant backend/mock integration
* responsive layouts
* runtime errors
* type/build errors
* relevant automated tests

Compare the current screens against Stitch.

Fix important discrepancies.

---

# 13. Scope

Implement only:

```text
BATCH_NUMBER
```

Do not implement future user-facing batches.

Do not perform unrelated backend refactoring.

Future-compatible infrastructure is acceptable only when required by the current batch.

---

# 14. Documentation

After successful implementation and verification, update the project's existing `memory.md`.

If the project has a specific documented location for memory, follow that location rather than creating a duplicate.

Record:

* batch completed
* screens
* routes
* state/model changes
* functionality
* components
* backend/data boundaries
* verification
* limitations
* next batch

---

# 15. Definition of Done

The batch is complete only when:

* [ ] all current screens implemented
* [ ] Stitch designs inspected
* [ ] routes work
* [ ] interactions work
* [ ] state flows correctly
* [ ] back navigation works
* [ ] validation works
* [ ] previous batch integration works
* [ ] required backend/data integration works
* [ ] responsive behavior verified
* [ ] accessibility checked
* [ ] build/type/runtime issues addressed
* [ ] visual verification completed
* [ ] relevant tests completed
* [ ] memory updated

---

# Final Response

Provide:

## Implemented

Screens, routes, components, state and functionality.

## Integration

Previous → current and current → future state flow.

## Verification

Functional, visual, responsive, accessibility and technical checks.

## Backend/Data

Live, mock, fixture or unavailable functionality.

## Limitations

Known issues.

## Documentation

Memory update.

## Next

Identify `NEXT_BATCH`.

Do not implement it.

Then stop.
