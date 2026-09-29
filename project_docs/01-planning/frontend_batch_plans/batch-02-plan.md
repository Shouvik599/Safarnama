# Safarnama Frontend — Batch 2 Plan

**Batch:** 2 — Preferences, budget, and review  
**Previous batch:** Batch 1 (Welcome, Trip Details, Destinations)  
**Next batch:** Batch 3  
**Stitch project:** Safarnama (`projects/12901504223215830628`)

## Batch Summary

Batch 2 contains three screens: Travel Style & Pace, Budget, and Review & Confirm. Destinations is complete in Batch 1 and is outside this batch's screen implementation scope. Its only remaining work is integration: connect its existing Continue action to the new Preferences route and verify that route/night state survives navigation. Keep one shared draft; do not implement Batch 3 Planning Progress or Trip Overview.

The updated three-screen list is authoritative. Stitch has corresponding Step 3 Travel Preferences, Step 4 Budget, and Step 5 Review designs. The Step 2 Destinations design corresponds to the already-developed Batch 1 screen and is referenced only for flow integration.

## Screen-by-Screen Plan

### 5. Trip Planner — Travel Style & Pace
- **Route:** `/planner/preferences` (new screen; existing wizard calls it Preferences).
- **Purpose/UI:** Match Stitch Step 3 with one travel-style choice, one pace choice, selectable experience interests, and specific must-visit places selected from destination-scoped autocomplete. Planning priorities are included only where the existing contract supports them.
- **State:** Add and retain `travelStyle`, `pace`, `activityPreferences`, and `mustVisits` in the shared draft; map supported values to `PlanRequest.travel_style`, `pace`, `activity_preferences`, and `must_visits` when Batch 3 submits the plan.
- **Validation:** Require one supported travel style (`BUDGET`, `COMFORTABLE`, `PREMIUM`, `LUXURY`) and pace (`RELAXED`, `BALANCED`, `PACKED`); interests must be unique supported values; must-visits must match a route stop or curated place from the selected destinations. Do not accept arbitrary free-text places or claim specific activity-count guarantees until Stitch descriptions are aligned with backend pace behavior.
- **Navigation:** Back to Destinations; forward to Budget with selections preserved.

### 6. Trip Planner — Budget
- **Route:** `/planner/budget`.
- **Purpose/UI:** Match Stitch Step 4's all-inclusive target budget, total/per-person toggle, currency/amount presentation, and transparency/estimate area. Currency entry is INR in the existing backend contract.
- **State:** Add `budgetMode` and `budgetInr` to the shared draft; map to `budget_mode` and `budget_inr` in `PlanRequest`. Existing traveler and date values remain sourced from Batch 1 state.
- **Validation:** Require a finite INR amount of at least ₹1,000 and a selected mode; total/per-person conversion is backend-owned. Do not calculate a misleading category allocation in the browser.
- **Design boundary:** Stitch includes tier benchmarks, expense allocations, splurge pillars, and strict/flexible/experience-first choices. `TripBudget` models only amount and `TOTAL`/`PER_PERSON`; no contract/provider represents those extra controls. Omit/defer them or show only clearly non-binding information. `/api/v1/plan/preview` is generic heuristic output, not the designed personalized allocation.
- **Navigation:** Back to Travel Style & Pace; forward to Review & Confirm.

### 7. Trip Planner — Review & Confirm
- **Route:** `/planner/review`.
- **Purpose/UI:** Match Stitch Step 5 with a scannable summary of origin/destination and ordered stops/nights, travelers and dates, preferences, budget/mode, and warnings. Provide section-level edit links and a final confirmation action.
- **State:** Read-only projection of the shared draft; edits return to the owning route and must preserve all other sections. Confirm hands the complete validated request to the Batch 3 Progress flow; it does not synthesize a plan in this batch.
- **Validation:** Before confirmation, require valid origin/destination, non-empty reconciled route, supported party values, valid dates, budget >= ₹1,000, and required preferences. Show section-specific errors and link to the owning screen; never silently normalize user choices.
- **Navigation:** Back to Budget; edit links to Destinations, Preferences, or Batch 1 Trip Details. Confirm targets Batch 3's `/planner/progress` handoff. Until Batch 3 exists, use an explicit boundary state rather than submitting and leaving users without progress/result handling.

## Routes and Navigation

There is no URL router today: `App.tsx` switches among three screens with local state. Preserve Welcome (`/`), Trip Details (`/planner/trip-details`), and the existing Destinations screen (`/planner/destinations`); add URL-addressable routes for Preferences (`/planner/preferences`), Budget (`/planner/budget`), and Review (`/planner/review`). These are proposed URLs. Connect the existing Destinations Continue callback to Preferences; do not recreate its route editor or add a new Destinations screen. Use a route layer rather than expanding the boolean screen switch; no routing dependency is currently installed, so select the smallest suitable option.

Forward flow: Welcome → Trip Details → existing Destinations → Travel Style & Pace → Budget → Review & Confirm → Batch 3 Progress. Back/edit actions return to the previous or owning route without losing draft data. Do not create a Progress route/screen in Batch 2. Direct route loads and refresh must not silently reset a draft; the provider is currently in-memory only. If local/session persistence is added, do not describe it as account/cloud autosave.

## State and Data Flow

- **Batch 1 state consumed:** `scope`, `origin`, `destination`/`destinations`, ordered route stops and nights, traveler counts/type, dates, duration, and `flexibleDates`.
- **Existing state owner:** `TripPlanningProvider` remains the single draft owner. Keep destinations in its current `RouteStop[]`; add typed preferences and budget fields to the shared trip state. Per-screen state is transient UI only.
- **Batch 2 state created/updated:** `travelStyle`, `pace`, supported `activityPreferences`/`mustVisits`, `budgetMode`, and `budgetInr`. Review presents these together with the existing Batch 1 request data.
- **Batch 3 handoff:** Keep the full validated draft/request available for `/api/v1/plan/stream` and preserve it through planning. Batch 3 owns SSE lifecycle, warnings/errors, `planning_completed.data.itinerary`, and final result state; do not implement those behaviors or result screens here.

## Components To Reuse / Create

- **Reuse:** Existing `DestinationsScreen` as a prior-batch screen (no reimplementation), its route/duration helpers, `TripPlanningProvider`/`useTripPlanning`, `PlannerHeader`, `PlannerFooter`, and `ProgressStepper`.
- **Adapt:** Pass the existing `onContinueToPreferences` callback from application navigation so the screen's current duration reconciliation leads into Preferences. Update header/stepper navigation to link implemented steps and allow back/edit navigation. Keep current route-night reconciliation as the authority.
- **Create:** Preferences input controls/state, budget input/state, read-only Review & Confirm summary, URL route definitions, and focused tests. The new screens consume shared state; no API/SSE progress client is required until Batch 3.
- **Must-visit source:** Reuse current ordered route stops and each selected destination's curated stops/suggestions. Keep the backend `must_visits` string list contract; reject unmatched values, and flag saved values that become out of-scope after editing trip destinations. Do not invent a places API or fabricate candidates.

## Backend and Data Dependencies

- **FRONTEND_ONLY:** Preferences, budget entry, review summary, form validation, and navigation are frontend responsibilities. Destination editing/reconciliation remain completed Batch 1 functionality.
- **EXISTING_BACKEND CONTRACT (future submission):** `PlanRequest` supports adult/child party, dates, budget mode/INR amount, travel style, pace, activity preferences, and must-visits. Batch 2 should shape state to this contract but not add or invent API fields.
- **EXISTING_BACKEND, limited:** `/api/v1/plan/preview` returns a heuristic baseline; `/api/v1/estimate` is a generic estimate. Neither provides Stitch's personalized tier benchmarks or category allocations. No planning call is needed before the Review confirmation handoff.
- **EXISTING_FIXTURE:** Provider fixtures under `data/fixtures/` are backend test inputs, not direct browser pricing data. No dedicated frontend fixtures/mocks exist.
- **NOT_YET_AVAILABLE:** Budget splurge/allocation/flexibility fields in the planning model; frontend API configuration/client; account/cloud draft storage; mobile/tablet Stitch designs. Do not treat static destination data or provider fixtures as live prices.

## Batch 1 Integration

Destinations route editing, suggestions, contextual city validation, and stop-night reconciliation are complete in Batch 1 and remain out of Batch 2 implementation scope. One integration item remains: application navigation currently renders `DestinationsScreen` without its optional `onContinueToPreferences` callback, so Continue shows the Batch 1 boundary alert. Supply the callback to navigate to Travel Style & Pace after reconciliation. Preserve its existing route/night data in the shared provider; Preferences and Budget extend that draft, and Review reads it. No other Destinations feature work is planned.

## Verification Plan

1. Test the connected flow Welcome → Trip Details → existing Destinations → Preferences → Budget → Review, including the existing duration reconciliation and the Continue callback transition; confirm route/night values survive navigation and back/edit actions.
2. Test preferences selection/state mapping; destination-scoped must-visit suggestions, rejection of unmatched text, stale-value validation, and request mapping; budget total/per-person mode and minimum; review summaries, section edit links, invalid-section errors, and confirmation handoff. Use no live API call in frontend unit tests.
3. Verify direct URL loads and browser back/forward for existing and new routes; refresh behavior must not silently reset a draft or claim cloud autosave.
4. Run `pnpm test`, `pnpm build`, and `pnpm lint` in `frontend/`; visually inspect desktop, tablet, and narrow mobile layouts (including 390 px) for overflow and control fit.
5. Keyboard/accessibility-check semantic labels/grouping, visible focus, named controls, review error announcements, and touch target usability.

## Risks and Unknowns

- Destinations is already developed; only its navigation callback/route connection remains. Do not expand Batch 2 into destination feature changes.
- The current frontend has no URL router and only in-memory draft state; route wiring and refresh/deep-link persistence need an explicit implementation decision. Do not claim account/cloud autosave.
- Stitch's budget benchmarks, allocations, splurge pillars, and flexibility controls lack matching domain fields or a dedicated pricing provider; don't present them as enforced planner behavior.
- Stitch offers desktop-only screens; mobile/tablet behavior needs implementation-time layout and accessibility review.
- The current `Pace` descriptions and Stitch's activity-count copy are not fully aligned; use backend enum contracts and confirm labels before promising counts.
- Review confirmation depends on Batch 3's Progress route. Define the handoff contract now, but do not implement the progress view, SSE lifecycle, or overview in Batch 2.
