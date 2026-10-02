# Safarnama Frontend — Batch 3 Plan

**Batch:** 3 — Planning Progress & Trip Overview  
**Screens:**  
- Screen 8: Trip Planning Progress  
- Screen 9: Trip Overview  
**Previous Batch:** Batch 2 (Wizard Setup & Preferences: Travel Style, Budget, Review & Confirm)  
**Next Batch:** Batch 4 (Itinerary & Timeline: Day-by-Day Itinerary, Day Detail Timeline, Destination Details, Transport Details)  
**Stitch Project:** Safarnama (`projects/12901504223215830628`)  
**Design Reference Screens:**  
- Screen 8 Stitch ID: `0dfa100bc4f3426a97fed4293a89ac1a` (`Safarnama — Trip Planning Progress`)  
- Screen 9 Stitch ID: `4f5013a45060434197b913e2a825a76c` (`Safarnama — Trip Overview (Your Safarnama is Ready)`)  

---

## 1. Batch Summary

Batch 3 transitions Safarnama from a draft wizard into an interactive journey platform. It covers two pivotal milestone screens:
1. **Screen 8 (Trip Planning Progress):** The live multi-agent execution view that receives and renders real-time streaming Server-Sent Events (SSE) from the backend planning graph (`/api/v1/plan/stream`), displaying milestone stages, telemetry, progress metrics, and corridor layout.
2. **Screen 9 (Trip Overview):** The synthesized editorial dossier that presents the completed `FinalItinerary` deliverable: hero waypoint showcase, executive summary narrative ("Curator's Note"), rhythm index, interactive route corridor, snapshot matrix, budget leeway breakdown, highlights gallery, microclimate context, and navigation actions leading to Batch 4.

This batch establishes the data-fetching and persistence boundary for generated itineraries, integrating smoothly with Batch 2's review confirmation and setting up the state contract required by Batch 4's deep itinerary views.

---

## 2. Screen-by-Screen Implementation Plan

### Screen 8: Trip Planning Progress
- **Route:** `/planner/progress`
- **Purpose & Layout (Stitch Screen `0dfa100bc4f3426a97fed4293a89ac1a`):**
  - **Top Active Blueprint Banner:**
    - Active corridor summary: Origin (`DEL`) → Destinations (`Osaka → Kyoto → Kanazawa`).
    - Dates, duration (`10 Days`), seasonal highlight badge ("Peak Maple Foliage Window"), party summary (`2 Explorers (Couple) · Balanced Rhythm`), and target budget cap.
    - Pulsing run badge: `Batch #SF-8492` or dynamic run ID.
  - **Left Column (7 cols on lg): Primary Progress Stage Engine:**
    - Eyebrow with icon (`memory`): `Continuous Synthesis Protocol`.
    - Heading: *"Safarnama is synthesizing your bespoke journey"*.
    - Subtitle explaining mindful orchestration of route, lodging buffers, microclimates, and rail connections.
    - **Vertical Stage Timeline (7 stages):**
      1. *Understanding your trip* (`intake` stage)
      2. *Checking travel logistics* (`logistics` / `visa` / `date_optimizer` stage)
      3. *Finding experiences* (`experience` stage)
      4. *Checking weather* (`date_optimizer` / seasonal microclimates stage)
      5. *Calculating budget* (`budget` stage)
      6. *Optimizing your journey* (`optimizer` stage)
      7. *Your Safarnama is ready* (`synthesizer` / `complete` stage)
    - **Stage Item Visual States:**
      - **Completed:** Green/Secondary circle with checkmark (`check`), duration elapsed (e.g. `0.4s`), concise summary text.
      - **Active/In-Progress:** Primary-container circle with spinning indicator (`refresh`), pulsing "Live" tag, expanded contextual detail card (e.g., microclimate notes, rail schedule locks).
      - **Upcoming/Pending:** Surface-container muted dot, 65% opacity.
      - **Error/Halted:** Error container alert, retry button, cancel option.
    - **Linear Engine Progress Bar:** Percentage readout (`progress-val`), estimated seconds remaining, animated track with `transition-all duration-700`.
  - **Right Column (5 cols on lg): Journey Route Visualizer & Engine Telemetry:**
    - **Transit & Route Alignment Card:** Vertical corridor progression displaying airport departure (`DEL`), night stays with night badges (`2N Osaka`, `4N Kyoto`, `3N Kanazawa`), transit connectors (`flight`, `train` / `Thunderbird`), and active telemetry pulse.
    - **Data & Calibration Architecture Card:** Verified badges for live timetables, seasonal intelligence, and FX rates.
    - **Editorial Philosophy Excerpt:** Quotation card from Safarnama Editorial Desk.
    - **Bottom Actions:** "Cancel and return to review" link with `arrow_back` icon.
- **SSE Stream Lifecycle & Mapping:**
  - On mount, initiates connection to `/api/v1/plan/stream` via `POST` fetch reader (or mock streaming controller when in development/offline mode).
  - Handles incoming SSE events:
    - `planning_started` → sets status to `in_progress`, starts elapsed timer.
    - `intake_completed` → marks Stage 1 complete.
    - `date_optimization_completed` → marks date/weather checks underway or completed.
    - `visa_completed` → stores visa summary if applicable.
    - `logistics_completed` → marks logistics stage complete, populates transit legs & hotel summary.
    - `experience_completed` → marks experiences stage complete, displays daily plans count.
    - `budget_calculated` → marks budget calculation complete, displays total & variance status.
    - `optimization_completed` → marks optimization complete.
    - `synthesizer_started` → prepares final dossier.
    - `planning_completed` → receives payload `data.itinerary` (`FinalItinerary`), sets progress to 100%, writes itinerary to state/storage, and auto-navigates (or provides "Open Dossier" button) to `/trip/overview`.
    - `warning` → records non-fatal advisories.
    - `error` → displays error card, pauses progress, enables retry or return.
- **Validation:**
  - Prevent launching stream if wizard draft is invalid (redirect to `/planner/review`).
  - Abort stream cleanly via `AbortController` if user leaves page or clicks "Cancel".

---

### Screen 9: Trip Overview
- **Route:** `/trip/overview`
- **Purpose & Layout (Stitch Screen `4f5013a45060434197b913e2a825a76c`):**
  - **1. Top Journey Header & Dossier Meta:**
    - Dossier marker & run ID (`#SF-8492` or `itinerary.trip_id`).
    - Status pill: "Synthesis Complete • Ready for Departure" with green pulsing dot.
    - Main display title: *"Your Safarnama is ready."*
    - Narrative subtitle: Executive summary extracted from `FinalItinerary.summary`.
    - Metadata pill bar: Origin, route sequence, date range & duration (`10D / 9N`), party description (`2 Explorers (Couple)`), and active pace description.
  - **2. Prominent Travel Hero Dossier Showcase:**
    - Wide 21:9 / 16:9 cinematic cover image featuring destination waypoint (e.g. Kyoto dawn path).
    - Top-right seasonal badge (e.g. "Autumn Foliage Peak Season (Kōyō)").
    - Bottom narrative overlay: Waypoint title, confirmed stay highlight, verified reservation badge.
  - **3. Journey Summary Narrative & Philosophy (Curator's Note & Rhythm Index):**
    - Two-column grid (8 cols / 4 cols):
      - *Left:* "Curator's Note" blockquote with italicized editorial perspective, plus thematic interest chips (Culture & Heritage, Food & Culinary, etc.).
      - *Right:* "Pacing & Rhythm Index" card with percentage bars for Cultural Immersiveness (e.g. 94%) and Transit Leisure Margin (e.g. 88%), plus senior curator verification badge.
  - **4. Interactive Route Corridor (The Journey Sequence):**
    - 3-column responsive grid displaying cards for each destination stop:
      - Number badge (`01`, `02`, `03`), city name, subtitle tag.
      - Night pill (`2 Nights`, `4 Nights`).
      - Destination image with hover zoom.
      - Short experiential narrative.
      - Footer rail/transit connector banner (e.g. `Tokaido Shinkansen · 15 min bullet rail`).
  - **5. Trip Snapshot Matrix:**
    - 6-card grid with thematic icons:
      1. *Destinations:* Stop count & total distance.
      2. *Experiences:* Activity moments count (temples, culinary walks, master sessions).
      3. *Accommodation:* Stays count & accommodation style.
      4. *Transport:* Transit pass & flight corridor.
      5. *Estimated Outlay:* Grand total in INR and buffer status against user budget.
      6. *Weather Outlook:* Temperature range & climatic condition summary.
  - **6. Budget Snapshot & Leeway Breakdown:**
    - Alignment banner: Net variance status (e.g. `₹17,600 (4.6%) under your ₹3,80,000 budget cap`).
    - Comparison metric columns: Target Budget Cap, Estimated Expedition Total, Net Contingency Cushion.
    - Multi-segment stacked distribution bar (Stays 39%, Rail 26%, Cultural 14%, Dining 13%, Contingency 8%).
    - Category legend with color dots and currency values.
    - Transparent FX / seasonal note.
  - **7. Highlights of the Journey (Visual Gallery Cards):**
    - 3 featured highlight cards with imagery, day badges (e.g. `Kyoto • Day 4`), headline title, and descriptive narrative.
  - **8. Microclimate & Seasonal Context:**
    - City-by-city weather cards showing icons, temperatures, and specific travel advice (e.g., foliage hue index, drizzle recommendation).
  - **9. Primary Action Bar & Controls:**
    - Primary CTA: **"View Full Itinerary"** (links to Batch 4 `/trip/itinerary`).
    - Secondary CTAs:
      - **"Optimize Trip"** (`/trip/optimize` or modal trigger for Phase 16 trade-offs).
      - **"Edit Route & Preferences"** (returns to wizard `/planner/trip-details` preserving current draft).
      - **"Export & Share Dossier"** (opens native share / copies link).
    - Sync/Autosave notice: confirmation that dossier is saved locally/to account.
  - **10. Data Source Transparency Legend:**
    - Tag pills: `[User-Provided]`, `[Live: Timetables & FX]`, `[Estimated: Dining & Transfers]`, `[Static: Curated Access]`.
- **Validation:**
  - Requires an active `FinalItinerary` in state or storage.
  - If loaded directly without an itinerary, displays fallback sample dossier or a friendly empty-state redirecting to `/planner/review`.

---

## 3. Routes and Navigation

### Route Definitions
| Route | Screen | Step / Role | Access Condition |
| :--- | :--- | :--- | :--- |
| `/planner/progress` | Screen 8: Trip Planning Progress | Active streaming client | Reached from Review confirmation |
| `/trip/overview` | Screen 9: Trip Overview | Synthesized dossier summary | Reached after stream completion |

### Navigation Flow Map
```text
[Wizard Step 5: ReviewScreen] (/planner/review)
        │
        ▼ (User clicks "Confirm trip details")
[Screen 8: ProgressScreen] (/planner/progress)
   ├─── "Cancel and return" ───► Back to /planner/review (draft preserved)
   └─── Stream completes (planning_completed)
        │
        ▼ (Auto-transition or CTA)
[Screen 9: OverviewScreen] (/trip/overview)
   ├─── "View Full Itinerary" ────────► Batch 4 (/trip/itinerary)
   ├─── "Edit Route & Preferences" ──► Wizard Step 1 (/planner/trip-details)
   └─── "Optimize Trip" ──────────────► Future Optimization Flow (/trip/optimize)
```

### Browser History & Deep Linking
- Browser URL updates via `window.history.pushState` to support clean back/forward navigation.
- If user refreshes `/planner/progress` mid-stream, prompt confirmation or safely re-connect.
- If user refreshes `/trip/overview`, load saved itinerary from `localStorage` (`safarnama.itinerary.v1`).

---

## 4. State and Data Flow

### Data Flow Diagram
```text
[TripPlanningContext Draft]
 (tripDetails, destinations, preferences, budget)
        │
        ▼ (buildPlanRequestDraft)
[PlanRequest Payload]
        │
        ▼ (POST /api/v1/plan/stream)
[FastAPI Backend / SSE Stream]
        │
        ▼ (PlanningEvent stream: intake -> logistics -> experience -> budget -> optimizer -> synthesizer)
[Progress State Handler] ───► UI Milestone Updates in Screen 8
        │
        ▼ (planning_completed event with FinalItinerary)
[Itinerary State & LocalStorage] (safarnama.itinerary.v1)
        │
        ▼
[Screen 9: Trip Overview] ───► Reads FinalItinerary & renders dossier
```

### State Additions & Storage Model
1. **Planning Execution State (`PlanRunState`):**
   - `status`: `'idle' | 'streaming' | 'completed' | 'error'`
   - `currentStage`: `'intake' | 'date_optimizer' | 'visa' | 'logistics' | 'experience' | 'budget' | 'optimizer' | 'synthesizer' | 'complete'`
   - `progressPercent`: number (`0` to `100`)
   - `elapsedSeconds`: number
   - `events`: `PlanningEvent[]`
   - `error`: `string | null`
2. **Synthesized Dossier State (`ItineraryState`):**
   - `currentItinerary`: `FinalItinerary | null`
   - Persisted key: `safarnama.itinerary.v1` in `window.localStorage`
   - Fallback fixture: Pre-configured Kyoto/Osaka/Kanazawa sample itinerary matching Stitch designs when running in offline or mock mode.

---

## 5. Components to Reuse and Adapt

### Reused from Batch 1 & 2
- **`PlannerHeader` / App Nav:** Reused at top with logo, wordmark, and profile avatar.
- **`PlannerFooter`:** Reused for bottom platform links.
- **`useTripPlanning`:** Consumed to extract active `tripDetails`, `destinations`, `preferences`, and `budget`.
- **`buildPlanRequestDraft` (`frontend/src/data/planRequest.ts`):** Formats wizard state into standard `PlanRequest` schema for API submission.
- **Location & Destination Helpers (`frontend/src/data/destinationsRegistry.ts`):** Source of curated fallback imagery, scenic transit connectors, and regional coordinates.

### Components to Adapt
- **`App.tsx`:**
  - Add `'progress'` (`/planner/progress`) and `'overview'` (`/trip/overview`) to `Route` union and `routePaths` dictionary.
  - Wire route rendering for both new screens.
- **`ReviewScreen.tsx`:**
  - In `confirm()`, replace the static placeholder alert with navigation callback `onConfirmPlan()` targeting `/planner/progress`.

---

## 6. Components to Create

### New Screen Components
1. **`frontend/src/screens/TripPlanningProgressScreen.tsx`:**
   - Full implementation of Screen 8 matching Stitch design `0dfa100bc4f3426a97fed4293a89ac1a`.
   - Embeds timeline stages, linear progress bar, route alignment visualizer, and live telemetry card.
2. **`frontend/src/screens/TripOverviewScreen.tsx`:**
   - Full implementation of Screen 9 matching Stitch design `4f5013a45060434197b913e2a825a76c`.
   - Embeds dossier header, hero waypoint showcase, curator note, route corridor sequence, snapshot matrix, budget distribution bar, highlights gallery, and action bar.

### New Modular Sub-Components
3. **`frontend/src/components/progress/StageTimeline.tsx`:**
   - Vertical milestone list rendering completed, active, and upcoming stages with timestamps and contextual detail cards.
4. **`frontend/src/components/progress/RouteAlignmentVisualizer.tsx`:**
   - Mini corridor layout showing stops, night badges, transit leg icons, and active telemetry pulse.
5. **`frontend/src/components/overview/DossierHeroShowcase.tsx`:**
   - Cinematic hero cover with seasonal badge, waypoint caption, and host confirmation badge.
6. **`frontend/src/components/overview/CuratorNoteCard.tsx`:**
   - Narrative quote block with thematic tags and rhythm index indicators.
7. **`frontend/src/components/overview/RouteCorridorCards.tsx`:**
   - Multi-card sequential presentation of anchor hubs with image, nights, description, and transit badge.
8. **`frontend/src/components/overview/SnapshotMatrix.tsx`:**
   - 6-card summary grid (Destinations, Experiences, Stays, Transport, Outlay, Weather).
9. **`frontend/src/components/overview/BudgetLeewayBar.tsx`:**
   - Multi-segment stacked distribution progress bar with category color codes and net variance banner.
10. **`frontend/src/components/overview/HighlightsGallery.tsx`:**
    - 3-column curated experience moment cards with day badges.

### New Services & Fixtures
11. **`frontend/src/services/planningStreamService.ts`:**
    - Client for handling SSE stream from `/api/v1/plan/stream` with `fetch` and `ReadableStreamDefaultReader` supporting JSON event parsing and cancellation.
    - Includes offline/mock streaming simulator with realistic delays (3-5s total) for testing without active backend.
12. **`frontend/src/data/sampleItinerary.ts`:**
    - Rich, valid `FinalItinerary` fixture matching the Hokuriku Corridor (Osaka → Kyoto → Kanazawa) design for fallback and offline viewing.

---

## 7. Backend, Data, and Service Dependencies

### Existing Backend Contracts Consumed
- **Endpoint:** `POST /api/v1/plan/stream` (defined in `src/api/routes.py:424` and `src/graph/streaming.py`).
- **Request Payload:** `PlanRequest` (`origin`, `destinations`, `start_date`, `end_date`, `duration_days`, `budget_inr`, `travel_style`, `pace`, `num_travelers`, `must_visits`, `activity_preferences`).
- **Stream Format:** Standard SSE (`event: <name>\ndata: <JSON>\n\n`).
- **SSE Events:**
  - `planning_started` (`stage: "intake"`)
  - `intake_completed` (`stage: "intake"`)
  - `date_optimization_started` & `date_optimization_completed` (`stage: "date_optimizer"`)
  - `visa_started` & `visa_completed` (`stage: "visa"`)
  - `logistics_started` & `logistics_completed` (`stage: "logistics"`)
  - `experience_started` & `experience_completed` (`stage: "experience"`)
  - `budget_started` & `budget_calculated` (`stage: "budget"`)
  - `optimization_started` & `optimization_completed` (`stage: "optimizer"`)
  - `synthesizer_started` (`stage: "synthesizer"`)
  - `planning_completed` (`stage: "complete"`, contains `data.itinerary` conforming to `FinalItinerary`)
  - `warning` & `error`

### Data Boundaries & Constraints
- **NO INVENTED APIS:** Client strictly consumes existing `/api/v1/plan/stream`. No new endpoints required.
- **OFFLINE / DEV RESILIENCE:** If the local backend is not running or the stream errors, the frontend gracefully supports a mock simulation toggle or sample fixture so the user is never stuck on a broken spinner.
- **NO CREDENTIAL INVENTIONS:** All booking indicators in the design (e.g. "Direct Host Reservation Confirmed") are presented as informational editorial previews generated by the engine, not live transactional bookings.

---

## 8. Validation Requirements

1. **Pre-Stream Validation:**
   - Before allowing entry into `/planner/progress`, verify draft validity using `validateTripDraft()`.
   - If invalid, navigate back to `/planner/review` with section error alerts.
2. **Stream Integrity Validation:**
   - Validate incoming SSE payloads; disregard malformed chunks.
   - Guard against premature stream disconnection. If aborted, show an explicit retry card.
   - Ensure `planning_completed` event contains a valid itinerary structure with non-empty `trip_id` and days.
3. **Overview Display Validation:**
   - Ensure numerical calculations (budget variance, percentages) handle zero/undefined safely.
   - Format currencies with `Intl.NumberFormat('en-IN')` (INR).
   - If optional fields (e.g. `visa_verdict`, `date_options`) are null or domestic bypass, adjust or hide corresponding badges gracefully.

---

## 9. Forward and Backward Navigation

### Backward Navigation
- **From Screen 8 (Progress):**
  - "Cancel and return to review": Aborts the active fetch stream, clears the running status, and navigates back to `/planner/review`. All user inputs remain intact in `TripPlanningContext`.
- **From Screen 9 (Overview):**
  - "Edit Route & Preferences": Navigates back to `/planner/trip-details` (Step 1) or `/planner/review` (Step 5) with draft preserved, allowing the traveler to adjust and re-synthesize.

### Forward Navigation
- **From Screen 8 (Progress):**
  - Automatically transitions to `/trip/overview` on `planning_completed` (with optional 500ms celebratory pause), or enables a prominent "Open Dossier" button.
- **From Screen 9 (Overview):**
  - Primary CTA **"View Full Itinerary"** directs traveler forward to Batch 4's Day-by-Day Itinerary route (`/trip/itinerary`).
  - Secondary CTA **"Optimize Trip"** routes to `/trip/optimize` (or opens modal if handled locally).

---

## 10. Previous-Batch Integration (Batch 2 Handoff)

- **Existing State:** Batch 2 finished with `ReviewScreen.tsx` which validates all user inputs and displays a placeholder message: *"Planning will be available in Batch 3. No plan has been submitted."*
- **Integration Action:**
  - Replace the placeholder message in `ReviewScreen.tsx` with a proper callback `onConfirmPlan`.
  - In `App.tsx`, wire `onConfirmPlan` to `navigate('progress')`.
  - Pass the current validated draft through `buildPlanRequestDraft(tripDetails, destinations, preferences, budget)` to initiate the stream.
  - Ensure all 5 wizard steps remain fully accessible for editing from both Progress and Overview screens.

---

## 11. State and Data Required by Next Batch (Batch 4)

Batch 4 will implement:
- Screen 10: Day-by-Day Itinerary
- Screen 11: Day Detail & Activity Timeline
- Screen 12: Destination Details
- Screen 13: Transport / Route Details

**Requirements delivered by Batch 3 to Batch 4:**
1. **`FinalItinerary` Contract in Context:**
   - Fully populated `FinalItinerary` object available in `useTripPlanning()` or a dedicated context hook.
   - `experience_plan.days`: Array of `DayPlan` objects with `day_number`, `date`, `city`, `theme`, `activities` (`ActivitySlot[]`), `meals` (`DayMeal[]`), and `weather_forecast`.
   - `logistics_plan.transport_legs`: Inter-city and intermodal transit legs with operator, departure/arrival times, and costs.
   - `logistics_plan.hotel_stays`: Lodging recommendations with check-in/out dates and neighborhoods.
2. **Route Addressability:**
   - Batch 4 expects `/trip/itinerary` to be routable directly with an active itinerary in memory or loaded from `localStorage`.
   - Batch 3 will provide sample fallback data so Batch 4 development can proceed independently if needed.

---

## 12. Responsive Behavior

| Breakpoint | Screen 8: Trip Planning Progress | Screen 9: Trip Overview |
| :--- | :--- | :--- |
| **Desktop (≥ 1024px)** | 2-column layout: 7-col stage timeline on left, 5-col corridor visualizer on right. Sticky telemetry cards. | Full editorial presentation: 21:9 hero image, 8/4 split curator block, 3-column route corridor, 3-column highlights, 6-col snapshot matrix. |
| **Tablet (768px – 1023px)** | Stacked layout: Stage engine first, followed by corridor visualizer. Linear progress bar spans full width. | Hero scales to 16:9. Curator note and rhythm index stack. Corridor cards display 2 per row with wrap. Snapshot matrix in 2 columns. |
| **Mobile (< 768px)** | Single-column linear layout. Milestone timeline tightens padding. Corridor visualizer simplifies to compact vertical stop pills. | Hero banner compacts (height ~260px). Route cards stack vertically (1 per row). Stacked budget bar wraps legend gracefully. Sticky bottom action bar for primary CTA. |

---

## 13. Accessibility Requirements (WCAG 2.1 AA)

- **Live Region for Real-Time SSE:**
  - Progress updates and stage transitions must use `aria-live="polite"` and `role="status"` so screen reader users are informed of milestone completions without auditory flooding.
- **Progress Bar Semantics:**
  - The linear progress bar must have `role="progressbar"`, `aria-valuenow={progress}`, `aria-valuemin="0"`, `aria-valuemax="100"`, and `aria-label="Trip synthesis progress"`.
- **Keyboard Navigation & Focus:**
  - All interactive buttons ("Cancel and return", "View Full Itinerary", "Optimize Trip", "Export") must have visible focus rings (`focus-visible:outline-primary`) and min touch target size of 44×44px.
- **Semantic Structure:**
  - Single `<h1>` per screen ("Safarnama is synthesizing your bespoke journey" on Progress; "Your Safarnama is ready." on Overview).
  - Proper heading hierarchy (`<h2>` for Corridor Layout, Snapshot Matrix, Budget Breakdown, Highlights).
- **Color Contrast:**
  - Text on colored badges and gradient overlays must meet 4.5:1 contrast ratio against background surfaces.

---

## 14. Verification Plan

1. **Review Confirmation Handoff:**
   - Complete wizard steps 1–5, click "Confirm trip details" on Review screen, and verify immediate navigation to `/planner/progress`.
2. **SSE Streaming Lifecycle:**
   - Verify connection initiation to `/api/v1/plan/stream`.
   - Verify sequential stage transitions: intake → logistics → experience → budget → optimizer → complete.
   - Verify active stage indicators (spinning icon, live pill, expanded contextual detail card).
   - Verify cancellation: clicking "Cancel and return to review" cleanly aborts stream and restores review screen.
   - Test offline/mock mode fallback when backend server is unavailable.
3. **Dossier Synthesis & Rendering:**
   - Verify transition from progress to `/trip/overview` upon `planning_completed`.
   - Verify all 10 dossier sections render correctly with accurate data from `FinalItinerary`.
   - Verify budget breakdown calculations, variance status pill, and percentage distribution bar.
   - Verify route cards display correct nights, images, and transit connectors.
4. **State Persistence & Refresh:**
   - Reload `/trip/overview` and verify dossier rehydrates from `localStorage` without blank screen or navigation error.
5. **Batch 4 Forward Handoff:**
   - Click "View Full Itinerary" and verify navigation trigger to `/trip/itinerary`.
6. **Automated Testing Suite:**
   - Run `pnpm test` in `frontend/` with new test suites:
     - `TripPlanningProgressScreen.test.tsx`: Validates stage transitions, progress updates, and abort behavior.
     - `TripOverviewScreen.test.tsx`: Validates dossier rendering, currency formatting, and CTA clicks.
     - `planningStreamService.test.ts`: Validates SSE event parsing and mock fallback behavior.
   - Run `pnpm build` and `pnpm lint` to confirm zero TypeScript or lint errors.

---

## 15. Risks and Unknowns

1. **Backend SSE Availability in Local Environments:**
   - *Risk:* If the backend Python server (`uvicorn`) is not running during frontend development or testing, stream connection will fail immediately.
   - *Mitigation:* Implement a dedicated mock streaming service (`planningStreamService`) that transparently falls back to simulated sequential events and a fixture `FinalItinerary` when the backend is unreachable.
2. **Event Payload Variance:**
   - *Risk:* The backend `FinalItinerary` may have optional fields (`visa_verdict` is `None` for domestic trips, `date_options` is `None` for exact dates).
   - *Mitigation:* Safely guard all accessors in `TripOverviewScreen` with optional chaining and fallback presentation.
3. **Itinerary Data Volume & Local Storage Limits:**
   - *Risk:* Very long multi-destination itineraries with large descriptions could exceed storage thresholds if images are embedded as data URLs.
   - *Mitigation:* Store only clean JSON metadata and image URLs, avoiding heavy base64 blobs.
4. **Batch 4 Route Non-Existence:**
   - *Risk:* Clicking "View Full Itinerary" will target `/trip/itinerary`, which is not yet built in Batch 3.
   - *Mitigation:* Define the route in `App.tsx` with a graceful boundary notice or placeholder screen until Batch 4 is implemented.
