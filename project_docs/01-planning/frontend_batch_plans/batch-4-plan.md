# Safarnama Frontend — Batch 4 Plan

**Batch:** 4 — Itinerary & Timeline  
**Screens:**  
- Screen 10: Day-by-Day Itinerary  
- Screen 11: Day Detail / Activity Timeline  
- Screen 12: Destination Details  
- Screen 13: Transport / Route Details  
**Previous Batch:** Batch 3 (Planning Progress & Overview: Screens 8 & 9)  
**Next Batch:** Batch 5 (Stays, Dining & Experiences: Screens 14–17)  
**Stitch Project:** Safarnama (`projects/12901504223215830628`)  
**Design Reference Screens:**  
- Screen 10 Stitch ID: `7bb4541315b84267b2b8b6d8b983f08f` (`Safarnama — Day-by-Day Itinerary (Day 03: Kyoto Historic Heart)`)  
- Screen 11 Stitch ID: `e5138e01e98e480db8f5332864e9682f` (`Safarnama — Day Detail & Activity Timeline (Day 03: Kyoto Historic Heart)`)  
- Screen 12 Stitch ID: `46caa57dd5b144519bd12907a939b87f` (`Safarnama — Destination Detail (Kyoto: Ancient Heart of Japan)`)  
- Screen 13 Stitch ID: `734b8ab575734d7d9034ffbf14bdb4bd` (`Safarnama — Transport & Route Details (Kyoto to Kanazawa)`)  

---

## 1. Batch Summary

Batch 4 expands the synthesized editorial dossier (`FinalItinerary`) into full chronological and geographic drill-down views. It implements:
1. **Screen 10 (Day-by-Day Itinerary):** The master chronological roadmap displaying all trip days on a horizontal progression rail with morning, afternoon, and evening activity cards, culinary pairings, and a practical sidecar (lodging anchor, day spend tracker, weather advice).
2. **Screen 11 (Day Detail / Activity Timeline):** The deep-dive single-day diary showcasing the featured anchor experience (with cinematic 16:9 photography and "Why Included" narrative), vital stats strip (rhythm, walking footprint, sanctuary base), chronological timeline with access guidance, and an hourly atmosphere breakdown.
3. **Screen 12 (Destination Details):** The cultural chapter anchor for a specific destination stop, featuring local kanji/script title, stop sequence badge, 6-card destination snapshot matrix, curator preference alignment note with pacing harmonizer sparkline, curated neighborhood waypoints, and local transit guidance.
4. **Screen 13 (Transport / Route Details):** The synchronized intermodal route guide for inter-city travel legs, featuring a 5-checkpoint milestone trajectory flow (hotel departure, station check-in, express train journey, terminus arrival, hotel drop), service equipment specs, seat class reservations, luggage dispatch rules, intermediate station timetable, and fare breakdown.

Batch 4 transforms the high-level dossier from Batch 3 into an actionable, navigable travel companion, setting up clear boundaries for Batch 5's dedicated stay, restaurant, and attraction detail pages.

---

## 2. Screen-by-Screen Implementation Plan

### Screen 10: Day-by-Day Itinerary
- **Route:** `/trip/itinerary` (optionally accepts `?day=X`)
- **Stitch Reference:** `7bb4541315b84267b2b8b6d8b983f08f`
- **Purpose & Layout:**
  - **Sticky Context Header:**
    - Back link to dossier: `← Dossier #SF-8492` (`/trip/overview`).
    - Breadcrumbs: `Circuit Name` • `Day X Detailed Diary`.
    - Main display title and subtitle tag: `Autumn Along the Hokuriku Corridor — Day 3 of 10 • Kyoto Historic Heart`.
    - Action controls: `Optimize Cadence` (button), `Offline Dossier` (download button), `Share` button.
    - Corridor Summary Micro-Strip: Origin ➔ Destination corridor, travel date range, traveler party cadence description.
  - **Horizontal Day-by-Day Journey Path Strip (Progression Rail):**
    - Horizontally scrolling track with connecting route line.
    - Day nodes (Day 01 to Day N):
      - Completed state: Checkmark icon with primary/surface ring.
      - Active state: Saffron container dot with pulsing halo ring (`animate-ping`), highlighted day label, date and city.
      - Upcoming state: Surface-container dot with day number and date/city preview.
    - Clicking any day instantly updates the active day view.
  - **Day Hero Narrative Theme Card:**
    - Eyebrow badge: `FOCUS ITINERARY` + Day date & geographic sector.
    - Headline: `DAY 03 — Sacred Dawn, Gion Whispers & Zen Sanctuary`.
    - Editorial narrative paragraph setting the mood and pacing for the day.
    - Bento Metric Badges (4 cards):
      1. *Active Rhythm* (e.g. `5.5 Hours`, Light-moderate).
      2. *Pacing* (e.g. `Balanced`, 2.5h Machiya rest).
      3. *Walking* (e.g. `~8,400 Steps`, Cobblestones & steps).
      4. *Microclimate* (e.g. `16°C Crisp`, Clear • 0% Rain).
  - **Main Content Grid (12 Columns: 8 cols Timeline + 4 cols Sidecar):**
    - **Left Column (8 cols): Chronological Day Periods:**
      - **Morning Period (`The Sacred Dawn` / `06:30 – 11:30`):**
        - Activity Card: Time range (`06:45 – 08:30`), category tag (`SPIRITUAL` / `HISTORY_HERITAGE`), status tags (`Uncrowded Window`, `Included in Pass`), activity title, location with pin icon, narrative description, curated access tips, transit link.
        - Link to Screen 11: "View Deep Timeline" or clicking activity card.
      - **Afternoon Period (`Artisanal Pauses & Zen Reflections` / `12:00 – 16:30`):**
        - Meal Card: Lunch pairing (`Seasonal Kaiseki Multi-Course at Gion Karyo`), cuisine, cost in INR, reservations note.
        - Activity Card: Secondary cultural or garden experience.
      - **Evening Period (`Twilight Lanterns & Canal Cadence` / `17:30 – 21:00`):**
        - Evening stroll / atmospheric experience card.
        - Dinner Card: Kappo / Izakaya pairing with cost and neighborhood.
    - **Right Column (4 cols): Practical Intelligence Sidecar:**
      - *Sanctuary Lodging Anchor Card:* Hotel name, neighborhood, check-in time, key amenities, room rate, confirmed badge.
      - *Day Budget Tracker Card:* Donut or progress bar breakdown for Day 3 expenses (Stays, Dining, Activities, Transit leeway).
      - *Seasonal Packing & Microclimate Card:* Daily temperatures, daylight hours, packing advisory (e.g. slip-on shoes for temple tatami).
      - *Next Day Teaser Card:* Preview of Day 4 with 1-click transition button.

---

### Screen 11: Day Detail / Activity Timeline
- **Route:** `/trip/day-detail` (supports query param `?day=X`, defaults to active day)
- **Stitch Reference:** `e5138e01e98e480db8f5332864e9682f`
- **Purpose & Layout:**
  - **Sub-Navigation & Breadcrumbs Bar:**
    - Back link: `← Back to Full Itinerary` (`/trip/itinerary?day=X`).
    - Breadcrumbs: `Autumn Along the Hokuriku Corridor > Day 03 (Kyoto) #SF-8492`.
    - Action buttons: `Optimize This Day`, `Modify Day`.
  - **Day Header & Narrative Dossier Banner:**
    - Overline badges: `Day 03 of 10 • Kyoto Historic Core` + `Autumn Kōyō Sanctuary`.
    - Main Headline: `Sacred Dawn, Gion Whispers & Zen Sanctuary`.
    - Date and location metadata strip with icons.
    - Editorial synopsis paragraph.
    - Curator Stamp Badge: `Curated Route Pacing: Artisanal & Meditative`.
  - **Vital Status Strip (4 Metric Tiles):**
    - *Atmosphere:* 16°C High / 8°C Low, crisp autumn, 0% rain.
    - *Pacing Rhythm:* ~5.5 hrs active time, 2.5h Hinoki bath buffer.
    - *Physical Footprint:* ~8,400 steps, 6.2 km gentle cobblestones.
    - *Sanctuary Base:* Machiya Residence Inn, Gion Shirakawa (Night 1 of 4).
  - **2-Column Main Workspace (8 cols Stream + 4 cols Sidecar):**
    - **Left Column (8 cols):**
      - **Featured Anchor Experience Showcase:**
        - Banner: `Key Focus Experience` • `06:45 – 08:30 (1h 45m Leisurely Stroll)`.
        - Cinematic 16:9 Cover Image with floating badges: `Peak Kōyō Foliage`, `Window of Utmost Quietude`, `Confirmed Route`.
        - Title & Subtitle: `Quiet Dawn Walk: Ninenzaka & Sannenzaka Slopes` — Ascent to Kiyomizu-dera via preservation alleyways before daytime tour groups.
        - Narrative Sections: *Why Included in Your Safarnama*, *Curated Insider Access Tips* (e.g., photo lighting angles, temple gate opening protocols), *Transit Connection* (walking time from machiya).
      - **Timeline of the Day (Vertical Hour-by-Hour Chronology):**
        - Connected vertical line linking Morning, Midday, Afternoon, and Evening slots.
        - Detailed entry cards with exact time windows, POI description, cost, and logistics notes.
        - Weather substitution badge (if substituted due to rain/heat, with explanation).
    - **Right Column (4 cols):**
      - *Microclimate Hourly Radar:* Temperature chart and precipitation probability through the day.
      - *Lodging Sanctuary Details:* Check-in guide, neighborhood amenities, walking map link.
      - *Day Cost Ledger:* Itemized table of activities, meals, and transit tickets in INR.
      - *Next Day Handoff Card:* Teaser for next morning's itinerary.

---

### Screen 12: Destination Details
- **Route:** `/trip/destination` (supports query param `?name=CityName`, defaults to first destination)
- **Stitch Reference:** `46caa57dd5b144519bd12907a939b87f`
- **Purpose & Layout:**
  - **Sub-Header Route Breadcrumb & Actions:**
    - Back link: `← Trip Overview` (`/trip/overview`) or `← Full Itinerary` (`/trip/itinerary`).
    - Breadcrumbs: `Autumn Along the Hokuriku Corridor / Destinations / Kyoto (4 Nights • Stop 2)`.
    - Action controls: `View in Itinerary (Days 03–06)` (routes to Screen 10) and `Add / Edit in Itinerary`.
  - **Destination Hero Banner:**
    - High-resolution cinematic banner with gradient overlay.
    - Badge: `Stop 02 of 03 • 4 Nights in Active Itinerary (Oct 20–24, 2025)`.
    - Display Title: `Kyoto` + local script kanji (`京都`).
    - Subtitle: `Kansai Region, Honshu, Japan • Ancient Imperial Capital of 1,000 Years`.
    - Editorial introductory paragraph.
    - Sanctuary lodging callout: `Anchored at Machiya Residence Inn Gion Shirakawa for Days 03 through 06`.
  - **Destination Snapshot Matrix (6 Bento Metric Cards):**
    1. *Recommended Stay:* `4–5 Nights` (Your Trip: 4 Nights).
    2. *Seasonal Context:* `Peak Kōyō` (Late Oct maple tint).
    3. *Weather Context:* `16°C / 8°C` (Crisp & dry • 0% Rain).
    4. *Currency & FX:* `Japanese Yen` (~₹0.55 INR / ¥1 JPY).
    5. *Language:* `Japanese` (English signage on JR & subways).
    6. *Time Zone:* `JST (UTC+9)` (+3.5 hrs ahead of IST).
  - **Curator's Editorial Selection Section:**
    - Blockquote: `Why Safarnama Curated Kyoto for You` (ties directly into user's chosen travel style and pace).
    - Thematic alignment tags: `Culture & Heritage (Primary)`, `Nature & Zen Landscapes`, `Artisanal Dining`.
    - Pacing Harmonizer card with active discovery gauge (e.g. 5.5 hrs/day, 68% active ratio).
  - **Curated Neighborhood Waypoints (Interactive Cards):**
    - Cards for key districts: `Higashiyama Historic Core`, `Gion Shirakawa & Pontocho`, `Arashiyama Bamboo Forest & Sagano`, `Fushimi & Southern Shrines`.
    - Photos, walking durations, recommended times of day, and curated highlights.
  - **Practical Mobility & Transit Guide:**
    - Arrival options from previous city (Bullet train / Express rail).
    - Local transportation guide: IC smart cards (Suica/Icoca), subway lines, scenic walking corridors.
  - **Next Waypoint Connector Card:**
    - Teaser card connecting to next stop (e.g. `Next Stop: Kanazawa via JR Thunderbird #17`) with a 1-click CTA to Screen 13.

---

### Screen 13: Transport / Route Details
- **Route:** `/trip/transport` (supports query param `?leg=leg-X`, defaults to active leg)
- **Stitch Reference:** `734b8ab575734d7d9034ffbf14bdb4bd`
- **Purpose & Layout:**
  - **Top Breadcrumb & Segment Status Bar:**
    - Back link: `← Back to Full Itinerary` (`/trip/itinerary`).
    - Breadcrumbs: `Autumn Along the Hokuriku Corridor / Day 07 Transit / Leg 02 of 03: Kyoto ➞ Kanazawa`.
    - Segment badges: `Segment Batch #SF-8492` + `Sync: Seat Locks Confirmed`.
  - **Editorial Route Banner:**
    - Leg indicator: `Leg 02 of 03 • Inter-City Regional Transit • Lake Biwa Passage`.
    - Big Route Title: `Kyoto (京都) ➞ Kanazawa (金沢)` with saffron direction arrow.
    - Narrative synopsis explaining the scenic transit across Lake Biwa into Ishikawa prefecture.
    - Key Route Metrics Strip (4 tiles):
      1. *Travel Date:* `Fri, Oct 24, 2025` (Autumn Foliage Peak).
      2. *Corridor Distance:* `218.4 km` (Scenic Rail Corridor).
      3. *Duration:* `2h 10m` (Express Limited Rail).
      4. *Recommended Mode:* `JR Thunderbird #17` (Car 01 Green Reserved).
    - Atmosphere card with origin photo and action buttons: `Open Corridor Map` and `Download Travel Pass`.
  - **Synchronized Corridor Milestone Flow (Interactive Trajectory Tracker):**
    - 5-Node horizontal flow with continuous track:
      1. *Node 1 (09:15 Departure):* Gion Shirakawa Machiya Inn (Bags handed to forward courier, MK Taxi 15m).
      2. *Node 2 (09:40 Station Check-in):* Kyoto Station Platform 0 (Ekiben bento pick, 25m buffer).
      3. *Node 3 (10:09 ➔ 12:19 Active Line):* JR Thunderbird #17 (Lake Biwa West Shore scenic vistas, right-side windows).
      4. *Node 4 (12:19 Terminus Arrival):* Kanazawa Station (Tsuzumi-mon gate arrival, loop bus connection).
      5. *Node 5 (12:45 Sanctuary Check-in):* Coastal Heritage Ryokan in Higashi Chaya.
  - **Transit Specifications & Service Details:**
    - Carrier: `JR West (West Japan Railway Company)`.
    - Equipment: `683 Series Limited Express EMU`.
    - Seat Reservation: `Car 01, Seats 4A & 4B (Forward Facing, Lake View)`.
    - Luggage Policy & Courier Advice: Forward luggage transfer protocol (hands-free travel).
    - Rail Pass Coverage: Validity under `JR Hokuriku Arch Pass` / `Whole Japan Rail Pass`.
  - **Timetable & Intermediate Stations:**
    - Intermediate stops: Kyoto ➔ Omi-Imazu ➔ Tsuruga ➔ Fukui ➔ Komatsu ➔ Kanazawa with arrival and departure timestamps.
  - **Fare & Pass Breakdown:**
    - Base fare and seat reservation breakdown in INR and JPY.
    - Confirmation status: `Included in Curated Pass Package`.

---

## 3. Routes & Navigation Architecture

| Route | Screen / Component | Query Parameters | Back Target | Primary Forward Target |
| :--- | :--- | :--- | :--- | :--- |
| `/trip/itinerary` | Screen 10 (`DayByDayItineraryScreen`) | `?day=1..N` | `/trip/overview` | `/trip/day-detail?day=X` |
| `/trip/day-detail` | Screen 11 (`DayDetailTimelineScreen`) | `?day=1..N` | `/trip/itinerary?day=X` | `/trip/destination` or `/trip/itinerary` |
| `/trip/destination` | Screen 12 (`DestinationDetailScreen`) | `?name=CityName` | `/trip/itinerary` or `/trip/overview` | `/trip/itinerary` or `/trip/transport` |
| `/trip/transport` | Screen 13 (`TransportDetailScreen`) | `?leg=leg-id` | `/trip/itinerary` | `/trip/destination` or `/trip/itinerary` |

### History Synchronization
All screens use standard browser History API integration (`window.history.pushState` / `popstate`) matching the existing `App.tsx` pattern, allowing standard browser back and forward button clicks to navigate seamlessly across screens without losing active state.

---

## 4. State & Data Flow

### State Consumed
1. **`TripPlanningContext`:**
   - `itinerary`: Canonical `FinalItinerary` deliverable.
   - `tripDetails`: Origin, destinations, dates, travelers, scope.
   - `destinations`: Route stop list with nights and regions.
   - `preferences`: Travel style, pace, interests, must-visits.
   - `budget`: Target INR budget and mode.
2. **Fallback Safety:**
   - If direct URL navigation occurs and context is empty, hydrate from `localStorage` (`safarnama.itinerary.v1`).
   - If `localStorage` is empty, fallback to `SAMPLE_HOKURIKU_ITINERARY` (or dynamic synthesis if draft exists), preventing 404s or blank screens during direct bookmark visits.

### State Managed Locally / Transferred
1. **`selectedDayNumber` (`number`):** Active day index (1..10), synchronized with URL `?day=X`.
2. **`selectedDestinationName` (`string`):** Active destination (e.g. `'Kyoto'`), synchronized with URL `?name=X`.
3. **`selectedLegId` (`string`):** Active transport leg (e.g. `'leg-3'`), synchronized with URL `?leg=X`.
4. **Interactive Filters:**
   - Active period filter (`ALL` | `MORNING` | `AFTERNOON` | `EVENING`).
   - Weather substitution accordion expansion.

### State Required by Next Batch (Batch 5)
- Batch 5 implements:
  - Screen 14: Hotel / Accommodation Details (consumes `HotelStay` and `DayPlan.stay`).
  - Screen 15: Restaurant / Food Experience Details (consumes `DayMeal` and `DayPlan.meals`).
  - Screen 16: Attraction / Experience Details (consumes `ActivitySlot` and `PointOfInterest`).
  - Screen 17: Map / Journey Route (consumes `trip_context.destinations` and `logistics_plan.transport_legs`).
- Batch 4 components will emit clean navigation callbacks to these routes with IDs/names ready for Batch 5 consumption.

---

## 5. Components to Reuse & Components to Create

### Components to Reuse
- **Layout & Structure:**
  - Standard fixed global header (`AppContent` header with Safarnama logo mark and route links).
  - Global footer (`Curations`, `Concierge & Support`, copyright).
- **Design Tokens & Icons:**
  - Material Symbols Outlined icons (`directions_railway`, `calendar_today`, `timer`, `directions_walk`, `location_on`, etc.).
  - Tailwind color tokens (`bg-surface`, `bg-surface-container-*`, `primary`, `secondary`, `outline-variant`).
  - Typography classes (`font-display-hero`, `font-headline-*`, `font-body-*`, `font-label-*`).
- **Data Fixtures & Synthesizer:**
  - `SAMPLE_HOKURIKU_ITINERARY` and `synthesizeItineraryFromDraft` from `frontend/src/data/sampleItinerary.ts`.

### Components to Create
1. **Screens (`frontend/src/screens/`):**
   - `DayByDayItineraryScreen.tsx` (Screen 10)
   - `DayDetailTimelineScreen.tsx` (Screen 11)
   - `DestinationDetailScreen.tsx` (Screen 12)
   - `TransportDetailScreen.tsx` (Screen 13)
2. **Modular Reusable Sub-components (`frontend/src/components/itinerary/`):**
   - `ItineraryDayRail.tsx`: Horizontally scrolling interactive day navigation track with connecting path, completed checkmarks, and active pulsing rings.
   - `DayBentoMetrics.tsx`: 4-card metric strip for active rhythm, pacing buffer, walking steps, and microclimates.
   - `ActivityTimelineCard.tsx`: Period activity card with timing, category badge, uncrowded indicators, access tips, and action links.
   - `DayMealCard.tsx`: Culinary pairing card with cuisine tags, estimated cost in INR, and neighborhood notes.
   - `TransportMilestoneFlow.tsx`: 5-node trajectory tracker for regional rail and flight transfers.
   - `DestinationSnapshotGrid.tsx`: 6-card bento grid for stay duration, season, weather, currency, language, and time zone.

---

## 6. Backend / Service / Mock Boundaries

- **Strict Boundary:** No live external APIs or invented backend capabilities.
- **Data Source:** All 4 screens read from the existing `FinalItinerary` schema in `TripPlanningContext` and `sampleItinerary.ts`.
- **Fixture Enrichment in `sampleItinerary.ts`:**
  - Extend `SAMPLE_HOKURIKU_ITINERARY` so that all 10 days are populated with high-fidelity records matching the Stitch screens (especially Day 3: Kyoto Historic Heart with Ninenzaka dawn walk, Nanzen-ji tea ritual, and Gion Shirakawa dinner).
  - Ensure `logistics_plan.transport_legs` includes complete milestone details for the Kyoto ➔ Kanazawa JR Thunderbird leg (#SF-8492).
  - Ensure `destinationDetails` for Osaka, Kyoto, and Kanazawa have full neighborhood and transit guidance data.

---

## 7. Responsive & Accessibility Architecture

### Responsive Breakpoints
- **Desktop (≥ 1024px):** 12-column grid. Left 8 cols for timeline/content, right 4 cols for sticky intelligence sidecar.
- **Tablet (768px – 1023px):** 8-column layout. Metric strips adapt to 2x2 grid; sidecar stacks below or becomes collapsible.
- **Mobile (< 768px):** Single-column stacked layout.
  - Horizontal day rails and transport trackers use `overflow-x-auto` with clean touch scrolling.
  - Zero horizontal page overflow (verified with viewport bounds).
  - Tap targets adhere to minimum 44px height for touch ergonomics.

### Accessibility (a11y)
- Landmark elements: `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`.
- Interactive day rail buttons: proper `role="tab"` or `role="button"` with `aria-selected` and `aria-label="View Day X: Date, City"`.
- Keyboard navigation: Space/Enter triggers day transitions and timeline expansions. Focus visible ring on interactive elements.
- Semantic contrast: High-contrast text on ivory and warm white surfaces complying with WCAG 2.1 AA.

---

## 8. Verification Plan

1. **Automated Unit & Integration Tests (`frontend/src/test/batch4.test.tsx`):**
   - **Test 1:** Renders Day-by-Day Itinerary (Screen 10) with progression rail and periods for active itinerary.
   - **Test 2:** Switching days in horizontal progression rail updates the hero narrative and periods.
   - **Test 3:** Navigates from Screen 10 to Day Detail (Screen 11) via "Focus Itinerary" / Activity card click and verifies featured anchor experience.
   - **Test 4:** Navigates to Destination Detail (Screen 12) from Itinerary / Overview and verifies 6-metric snapshot matrix and neighborhoods.
   - **Test 5:** Navigates to Transport Detail (Screen 13) and verifies 5-node milestone trajectory and timetable.
   - **Test 6:** Backward navigation from all screens returns safely to Itinerary or Overview preserving full state.
2. **Regression Verification:**
   - Run complete suite: `pnpm test` (`vitest run`) — all 30 existing tests (`flow.test.tsx` [25] + `batch3.test.tsx` [5]) must stay green.
3. **Build & Quality Verification:**
   - `pnpm build` (`tsc -b && vite build`): Zero TypeScript compiler errors.
   - `pnpm lint` (`oxlint`): Zero errors and zero warnings.
4. **Visual Inspection against Stitch:**
   - Verify Screen 10 against Stitch ID `7bb4541315b84267b2b8b6d8b983f08f`.
   - Verify Screen 11 against Stitch ID `e5138e01e98e480db8f5332864e9682f`.
   - Verify Screen 12 against Stitch ID `46caa57dd5b144519bd12907a939b87f`.
   - Verify Screen 13 against Stitch ID `734b8ab575734d7d9034ffbf14bdb4bd`.

---

## 9. Risks and Unknowns

1. **Dynamic Draft Synthesis Coverage:** When a user creates a custom trip (e.g. 5 days in Rajasthan or 14 days in Norway), `synthesizeItineraryFromDraft()` must generate plausible daily activity slots, meals, and transport legs so that Screens 10–13 render beautifully for any arbitrary user input, not just the static Hokuriku fixture.
2. **Navigation Query Param Parsing:** Deep-linking directly to `/trip/day-detail?day=3` or `/trip/destination?name=Kyoto` must parse cleanly in environments without react-router (using `window.location.search` / URLSearchParams).
3. **Scroll Position on Route Change:** Navigating between Full Itinerary and Day Detail must scroll to top cleanly while preserving the active day tab.

---

## 10. Implementation Status & Verification Record

- **Status:** Complete (Implemented & Backend-Integrated)
- **Screens Implemented:**
  - Screen 10: Day-by-Day Itinerary (`/trip/itinerary`)
  - Screen 11: Day Detail / Activity Timeline (`/trip/day-detail`)
  - Screen 12: Destination Details (`/trip/destination`)
  - Screen 13: Transport / Route Details (`/trip/transport`)
- **Components Created:**
  - `frontend/src/components/itinerary/ItineraryDayRail.tsx`
  - `frontend/src/components/itinerary/DayBentoMetrics.tsx`
  - `frontend/src/components/itinerary/ActivityTimelineCard.tsx`
  - `frontend/src/components/itinerary/DayMealCard.tsx`
  - `frontend/src/components/itinerary/TransportMilestoneFlow.tsx`
  - `frontend/src/components/itinerary/DestinationSnapshotGrid.tsx`
  - `frontend/src/screens/DayByDayItineraryScreen.tsx`
  - `frontend/src/screens/DayDetailTimelineScreen.tsx`
  - `frontend/src/screens/DestinationDetailScreen.tsx`
  - `frontend/src/screens/TransportDetailScreen.tsx`
  - `frontend/src/screens/Batch5HandoffScreen.tsx` (Staging handoff receiver for Batch 5)
  - `frontend/src/services/itineraryOptimizationService.ts` (Backend replan & cadence smoothing)
- **Backend Integration:**
  - Live proxy configured in `frontend/vite.config.ts` (`/api` -> `http://localhost:8000`).
  - Bug fix in `src/graph/workflow.py` (`replan_workflow`) resolving positional argument mismatch for `process_logistics` and `process_experience`.
  - Live and fallback cadence optimization connected to `POST /api/v1/plan/replan` with graceful timeout fallback.
- **Verification Performed:**
  - Automated Tests: 38/38 tests passing in Vitest (`batch4.test.tsx` [8] + `batch3.test.tsx` [5] + `flow.test.tsx` [25]).
  - Production Build: `tsc -b && vite build` passed cleanly with 0 type errors (3.69s).
  - Linter: `oxlint` passed cleanly with 0 errors and 0 warnings across all files.
  - Stitch Designs: Verified against Stitch IDs `7bb4541315b84267b2b8b6d8b983f08f`, `e5138e01e98e480db8f5332864e9682f`, `46caa57dd5b144519bd12907a939b87f`, and `734b8ab575734d7d9034ffbf14bdb4bd`.
- **Batch 3 Backward Flow & Batch 5 Forward Handoff:**
  - Backward flow verified from Screen 8 (`/planner/progress`) and Screen 9 (`/trip/overview`) directly into Screens 10–13.
  - Forward handoff mapped across all 4 Batch 5 targets (`/trip/stays`, `/trip/dining`, `/trip/experience`, `/trip/map`) with query params and dedicated `Batch5HandoffScreen`.
