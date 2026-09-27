# Antigravity — Safarnama Batch Implementation

You are implementing **one incremental batch of the Safarnama frontend**.

This is a **connected production-oriented application**, not a collection of independent screen prototypes.

The implementation must use the existing Stitch project:

**Stitch project: `Safarnama`**

Use the **Stitch MCP** to inspect the relevant designs before implementing anything.

---

## 1. Determine the Current Batch

The current task is:

**Batch: `[BATCH_NUMBER]`**

**Screens in this batch:**

`[SCREEN_NUMBERS_AND_NAMES]`

The previous batches have already been implemented in the same application.

Your responsibility is to:

1. Inspect the existing repository.
2. Inspect the existing `Safarnama` Stitch project.
3. Inspect the designs belonging to the current batch.
4. Inspect the already implemented application and previous batches.
5. Implement **only this batch**.
6. Integrate this batch into the existing application.
7. Implement the actual functionality that can reasonably be implemented at this stage.
8. Add proper routing/navigation.
9. Verify both the UI and the functionality.
10. Update project memory/documentation.
11. Stop after this batch is complete and verified.

Do **not** implement future batches.

---

# 2. IMPORTANT: This Is a Vertical Slice, Not a UI Mockup

Do NOT treat the Stitch designs as static screens that only need to look correct.

For every screen in the current batch, determine:

* What information the user enters or views
* What controls are interactive
* What state needs to be maintained
* What happens when the user submits/confirms/continues
* What happens when the user goes back
* What data needs to be passed to the next screen
* What existing application state needs to be consumed
* What existing state needs to be updated
* What route should represent the screen
* What validation is required
* What loading/empty/error states are appropriate
* What functionality can be implemented now without a backend
* What functionality must remain mocked because the corresponding backend/provider does not yet exist

The result should be a **working application flow**, not merely visually accurate pages.

---

# 3. Stitch Project — Source of Truth

Use the existing Stitch project:

**`Safarnama`**

Do NOT:

* create a new Stitch project
* create a separate project for this batch
* treat the batch as a standalone prototype
* redesign screens unnecessarily
* replace the Stitch visual direction with your own design

First inspect the relevant Stitch designs.

Use Stitch as the primary visual reference for:

* layout
* hierarchy
* spacing
* typography
* colors
* components
* cards
* controls
* responsive behavior
* visual relationships
* interaction affordances

If something is not explicitly represented in Stitch but is required for functionality, implement it in a way that remains visually consistent with the existing Safarnama design system.

---

# 4. Inspect the Existing Application Before Coding

Before modifying code, inspect:

* repository structure
* existing routes
* existing pages/screens
* existing components
* existing state management
* existing hooks
* existing utilities
* existing design tokens
* existing types/models
* existing mock/fixture data
* existing API/provider abstractions
* existing validation
* existing tests
* existing documentation
* `memory.md`
* relevant project architecture/design/rules documents

Do not duplicate functionality that already exists.

Prefer extending existing components and abstractions over creating parallel implementations.

---

# 5. Understand Previous Batches

Previous batches are part of the same application.

Inspect how the existing application currently flows into and out of the current batch.

For example:

```text
Previous Batch
     ↓
Current Batch
     ↓
Next logical application state
```

The current batch must integrate with the existing application rather than resetting or bypassing it.

If a previous screen collects data required by the current batch:

* consume that data
* preserve that data
* do not create a second incompatible version of the same state

If the current batch produces data required by future screens:

* model and store that data cleanly
* expose it through the appropriate application state/model
* do not implement future screens just to consume it

---

# 6. Implement Proper Routing

Every implemented screen should have a real application route.

Do not rely solely on:

* manually toggling components
* temporary boolean state
* hardcoded screen switching
* prototype-only navigation

Use the application's existing routing architecture.

If no routing architecture exists yet, establish a lightweight, scalable routing structure consistent with the project architecture.

For each current-batch screen:

* define a stable route
* support forward navigation
* support backward navigation where appropriate
* preserve user-entered state
* support refresh/deep-link behavior where practical
* ensure invalid/incomplete navigation is handled sensibly

The user should be able to navigate through the actual application rather than through a developer-only demo state.

---

# 7. Implement Actual Functionality

For each current-batch screen, implement as much real functionality as the current architecture supports.

Examples:

### Forms

If a screen contains a form:

* make fields functional
* maintain controlled state
* validate inputs
* display validation errors
* preserve entered values
* enable/disable actions appropriately
* submit the form into application state
* navigate to the correct next route

### Search / Selection

If the design contains searchable selections:

* implement search/filter behavior
* allow selection
* visibly show selected values
* support removal/change where appropriate
* preserve selections across navigation

### Multi-step flows

If the batch is part of a planner flow:

```text
Step A
  ↓
Step B
  ↓
Step C
```

the user should actually be able to complete the flow.

Do not simply make buttons navigate to visually unrelated screens.

### Derived information

If information can be derived deterministically from user input, implement it.

For example:

```text
destination selection
        ↓
application state
        ↓
summary / validation / next step
```

Avoid hardcoding values that should be derived from state.

---

# 8. Backend / External Data Boundary

Do not invent APIs, providers, credentials, or backend services.

If the required backend/provider does not yet exist:

* use the existing mock/fixture/provider abstraction if available
* otherwise introduce a clean mock/service boundary
* keep the interface compatible with the future real implementation
* clearly distinguish mock/fixture data from real/live data

The frontend should still behave realistically.

For example:

```text
UI
 ↓
Application state
 ↓
Service/provider abstraction
 ↓
Mock implementation
```

rather than:

```text
Button
 ↓
hardcoded screen transition
```

Do not pretend mock data is live data.

---

# 9. State Management

Use the project's existing state-management approach.

Maintain a coherent Safarnama trip/planning state.

Do not create isolated state copies for every screen when the data represents the same user journey.

For example:

```text
Trip
 ├── origin
 ├── destinations
 ├── travelers
 ├── budget
 ├── dates
 ├── travelStyle
 ├── pace
 └── preferences
```

The exact model must follow the existing architecture and project documentation.

State should survive:

* moving forward
* moving backward
* editing previous inputs
* returning to a previous step

Avoid unnecessary global state when local state is sufficient.

---

# 10. Validation and Error Handling

Implement appropriate validation for the current batch.

Handle:

* missing required information
* invalid values
* contradictory selections
* empty states
* loading states
* recoverable errors
* unavailable/mock data states

Do not allow the UI to appear functional while silently losing user input.

Errors should be understandable to users and visually consistent with Safarnama.

---

# 11. Reuse Existing Components

Before creating a new component, check whether an existing component can be reused.

Create reusable components when the pattern is genuinely shared.

Examples:

* AppShell
* Header
* PageContainer
* StepIndicator
* FormField
* SearchableSelect
* MultiSelect
* DestinationChip
* PrimaryButton
* SecondaryButton
* Card
* EmptyState
* ErrorState

Do not prematurely build an enormous design system.

Build only the reusable foundations required by the current and immediately connected flow.

---

# 12. Visual Fidelity

Match the Stitch designs closely.

Verify:

* spacing
* alignment
* typography
* colors
* borders
* radii
* cards
* icons
* button hierarchy
* form appearance
* visual density
* responsive layout

Do not introduce unrelated visual styles.

Safarnama should continue to feel like one coherent product.

---

# 13. Responsive Behavior

Implement responsive behavior for:

* desktop
* tablet
* mobile

Do not simply shrink the desktop layout.

Check:

* navigation
* forms
* cards
* buttons
* long destination names
* selected-value chips
* scrolling
* content hierarchy
* touch targets

The application should remain usable on smaller screens.

---

# 14. Accessibility

Implement appropriate:

* semantic HTML
* labels
* keyboard navigation
* visible focus states
* accessible buttons
* accessible form controls
* error messaging
* sufficient contrast
* non-color-only status communication

Follow the existing project's accessibility conventions.

---

# 15. Functional Testing

Do not stop after confirming that the screens render.

Test the actual user flow.

At minimum, verify:

### Navigation

```text
Previous screen
      ↓
Current Screen A
      ↓
Current Screen B
      ↓
Current Screen C
```

and verify backward navigation.

### State

Enter realistic test data and verify:

```text
Screen A
  ↓
Screen B
  ↓
Back
  ↓
Screen A still contains the entered data
```

### Validation

Verify:

* required fields
* invalid input
* incomplete steps
* valid submission

### Interaction

Verify every important interactive control:

* buttons
* inputs
* dropdowns
* search
* selection
* remove/edit actions
* toggles
* navigation

### Integration

Verify that the current batch works with the already implemented previous batches.

Do not test the batch in isolation.

---

# 16. Visual Verification Against Stitch

After implementation:

1. Run the application.
2. Navigate to every screen in the current batch.
3. Compare each screen against the corresponding Stitch design.
4. Fix obvious differences.
5. Check desktop and mobile layouts.
6. Re-test interactions after visual fixes.

The goal is:

**Stitch design ≈ implemented UI + real interaction**

not:

**Stitch design ≈ static screenshot**

---

# 17. Do Not Implement Future Batches

Only implement:

**Batch `[BATCH_NUMBER]`**

Do NOT implement:

* screens belonging to future batches
* future dashboard functionality
* future itinerary functionality
* future budget functionality
* future optimization functionality
* future profile/settings functionality

unless a tiny underlying abstraction is genuinely required by the current batch.

It is acceptable to create:

* future-compatible data models
* reusable primitives
* service interfaces
* route placeholders only when architecturally necessary

But do not build future user-facing functionality.

---

# 18. Documentation / Memory

After successful implementation, update:

`memory.md`

Record:

* current batch completed
* screens implemented
* routes added
* reusable components added
* state/models added
* functionality implemented
* mock/provider boundaries
* important architectural decisions
* verification performed
* known limitations
* next batch to implement

Do not rewrite unrelated project history.

Keep the memory concise and chronological.

---

# 19. Definition of Done

The batch is complete only when all of the following are true:

### Design

* [ ] All current-batch Stitch screens inspected
* [ ] UI implemented according to Stitch
* [ ] Responsive behavior implemented

### Architecture

* [ ] Existing architecture respected
* [ ] Existing components reused where appropriate
* [ ] No unnecessary duplicate abstractions
* [ ] State integrated with existing application state

### Routing

* [ ] Real routes implemented
* [ ] Forward navigation works
* [ ] Back navigation works
* [ ] State is preserved

### Functionality

* [ ] Interactive controls actually work
* [ ] Forms actually submit
* [ ] Validation works
* [ ] Selections/searches work where applicable
* [ ] Data flows between screens
* [ ] Mock/provider boundaries are explicit where backend is unavailable

### Integration

* [ ] Previous batch → current batch works
* [ ] Current batch produces usable application state
* [ ] No existing functionality was broken

### Quality

* [ ] Desktop verified
* [ ] Mobile verified
* [ ] Accessibility checked
* [ ] Console/runtime errors addressed
* [ ] Functional flow tested
* [ ] Visual comparison against Stitch performed

### Documentation

* [ ] `memory.md` updated
* [ ] Current batch status recorded
* [ ] Next batch identified

---

# 20. Important Constraints

Do NOT:

* create a new Stitch project
* redesign the product independently of Stitch
* build the entire application at once
* implement future batches
* create fake backend APIs
* claim mock data is live data
* hardcode navigation as a substitute for application routing
* create disconnected screen prototypes
* discard existing application state
* duplicate existing components unnecessarily
* stop at "the page renders"

The objective is a **working vertical slice of the real Safarnama application**.

---

# 21. Final Report

When finished, provide a concise implementation report containing:

### Implemented

* screens
* routes
* components
* state/models
* functionality

### Integration

* previous batch integration
* navigation flow
* state persistence

### Verification

* functional testing
* responsive testing
* Stitch visual verification
* accessibility checks

### Limitations

* mock data
* unavailable backend/provider functionality
* known issues

### Documentation

* `memory.md` updated

### Next

Identify the next batch, but **do not implement it**.

Then stop.
