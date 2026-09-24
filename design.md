# Design System & Visual Direction
# Safarnama

**Document status:** V1 Visual Foundation  
**Purpose:** Define the basic visual identity and design language for Safarnama without over-specifying the frontend before the product functionality is proven.

---

## 1. Design Vision

Safarnama should feel like a **modern Indian travel companion with a strong sense of place**.

The visual identity should combine:

- Indian travel heritage
- Warmth
- Discovery
- Modern usability
- Friendly technology
- Confidence without feeling corporate
- Rich visual storytelling without becoming visually crowded

The product should feel like a **digital travel journal + intelligent travel planner**, rather than a generic AI chatbot.

### Core design words

```text
Warm
Cultural
Exploratory
Modern
Friendly
Trustworthy
Human
Travel-focused
```

---

# 2. Overall Visual Direction

Selected direction:

> **Warm & cultural / Indian-inspired**

Safarnama should have a distinctly Indian travel identity while maintaining modern product-design principles.

The Indian influence should be visible through:

- Color
- Typography accents
- Decorative motifs
- Illustration style
- Travel/map symbolism
- Subtle references to Indian visual heritage

Avoid excessive ornamentation.

The design should feel contemporary first and culturally distinctive second.

---

# 3. Theme

## Primary theme

**Light theme**

The V1 interface should be designed primarily for a light background.

Reasons:

- Travel itineraries contain substantial information.
- Maps, cards, schedules and cost breakdowns benefit from high readability.
- The product should feel welcoming and energetic.
- Warm colors work naturally against a light canvas.
- Light UI is suitable for long itinerary-reading sessions.

### Future consideration

Dark mode can be introduced later.

It should not influence the V1 architecture beyond avoiding hard-coded colors that would make future theming difficult.

---

# 4. Primary Color Direction

The primary brand color will be:

## Safarnama Saffron

```text
Primary: #E87524
```

This provides an Indian cultural association while still feeling energetic and travel-oriented.

It should be used primarily for:

- Primary buttons
- Important actions
- Selected states
- Highlights
- Brand accents
- Journey/progress indicators
- Important interactive elements

It should **not** be used as the background for large amounts of text or dense content.

---

# 5. Supporting Color Palette

The initial palette should remain intentionally small.

### Primary

```text
Safarnama Saffron
#E87524
```

### Deep Heritage

```text
Deep Maroon
#7A2E2E
```

Use for:

- Strong secondary emphasis
- Heritage/cultural accents
- Occasional headings
- Special destination or experience highlights

### Warm Sand

```text
Sand
#F4E8D3
```

Use for:

- Soft section backgrounds
- Travel-story cards
- Cultural highlights
- Empty/background areas requiring warmth

### Background

```text
Ivory
#FFFDF8
```

Primary application background.

### Text

```text
Charcoal
#292521
```

Primary text color.

### Secondary Text

```text
Muted Brown-Gray
#6F6860
```

Used for supporting information and metadata.

### Border

```text
Warm Gray
#DDD6CC
```

Used for:

- Card borders
- Dividers
- Input boundaries
- Secondary UI structure

---

# 6. Semantic Colors

Functional status colors should remain distinct from the brand palette.

### Success

Use a restrained green for:

- Within-budget status
- Successful validation
- Confirmed information

### Warning

Use amber/yellow for:

- Data uncertainty
- Estimated values
- Weather warnings
- Visa information requiring verification

### Error

Use red for:

- Invalid input
- API failure
- Blocking planning problems
- Infeasible requests

### Information

Use a calm blue for:

- Informational notices
- Explanations
- Neutral planning guidance

Semantic colors must not be used decoratively when they could be interpreted as status.

---

# 7. Color Usage Principle

The interface should follow a rough visual hierarchy:

```text
Ivory / white
      ↓
Charcoal text
      ↓
Saffron interaction
      ↓
Maroon cultural emphasis
      ↓
Sand supporting surfaces
```

The interface should **not** become a collection of orange and maroon components.

The brand colors should create identity while neutral surfaces preserve readability.

---

# 8. Typography

Selected typography personality:

> **Modern + friendly**

Google Fonts are acceptable.

## Primary font

### Poppins

Use for:

- Navigation
- Buttons
- Headings
- Labels
- Short UI text
- Key numbers

Poppins provides a rounded, approachable personality that works well with the friendly travel identity.

## Reading font

### Inter

Use for:

- Long itinerary descriptions
- Supporting text
- Tables
- Detailed information
- Dense UI content

This creates a balance:

```text
Poppins
   ↓
Brand + personality

Inter
   ↓
Readability + information density
```

---

# 9. Typography Hierarchy

Initial hierarchy:

```text
Display
Large destination/trip titles

H1
Major page title

H2
Major section

H3
Card/section heading

Body
Normal content

Small
Metadata and supporting information

Caption
Secondary explanatory information
```

The exact font sizes should remain flexible during frontend implementation.

The important principle is consistent hierarchy rather than prematurely locking every pixel value.

---

# 10. Indian Visual Identity

Safarnama should have a **strong Indian travel identity**, but it should not look like a traditional government tourism portal.

### Preferred influences

- Indian textile-inspired patterns
- Journey/path motifs
- Map lines
- Postcard/stamp references
- Subtle architectural patterns
- Hand-drawn travel marks
- Regional visual accents
- Devanagari-inspired decorative details

### Avoid

- Excessive mandala decoration
- Overuse of traditional motifs
- Heavy gradients
- Generic "India tourism" stock imagery
- Excessive saffron
- Visual clutter

The cultural identity should feel **authentic and contemporary**.

---

# 11. Logo / Wordmark Direction

The wordmark should emphasize:

> **Safarnama**

Possible supporting treatment:

```text
Safarnama
सफ़रनामा
```

The Devanagari form can be used as a supporting brand element rather than replacing the primary English wordmark.

A future logo could incorporate:

- A journey/path line
- Map route
- Location pin
- Compass
- Open travel journal
- Stylized road

Avoid combining too many symbols into one logo.

---

# 12. Imagery Direction

Travel imagery is important to Safarnama.

Preferred imagery:

- Authentic destination photography
- Local food photography
- Architecture
- Landscapes
- Street scenes
- Cultural experiences
- Human-centered travel moments

Images should feel:

```text
Real
Local
Warm
Exploratory
High-quality
```

Avoid generic corporate travel imagery wherever possible.

---

# 13. Maps and Journey Visuals

Routes are an important part of the Safarnama experience.

The visual language can use:

```text
Origin
  ●
  │
  ├───────● Destination A
  │
  └────────────● Destination B
```

Potential UI concepts:

- Route lines
- Destination pins
- Journey timelines
- Country/state markers
- Transport icons
- Day-by-day route progression

These should visually communicate **journey**, not merely location.

---

# 14. Cards

Cards will likely be the primary information container.

Potential cards:

- Destination
- Hotel
- Restaurant
- Attraction
- Transport
- Visa
- Budget
- Weather
- Day itinerary

Card design should be:

- Moderately rounded
- Lightly bordered
- Spacious
- Information-focused
- Image-friendly

Avoid excessive shadows.

Use borders and subtle elevation primarily to establish hierarchy.

---

# 15. Buttons

Primary button:

```text
Safarnama Saffron
```

Primary actions may include:

- Plan my trip
- Continue
- Optimize
- Apply changes
- View itinerary

Secondary actions should use neutral or outlined styling.

Destructive actions should use the semantic error color rather than brand colors.

---

# 16. Forms

The trip-planning form is one of the most important parts of the product.

Inputs should prioritize:

- Clear labels
- Searchable controlled selections
- Visible selected values
- Helpful validation
- Minimal ambiguity
- Logical grouping

The UI should never encourage users to enter important structured information as arbitrary free text when a controlled input is available.

Examples:

```text
Origin → Searchable airport/city selector
Destination → Multi-select
Travelers → Structured count/profile inputs
Budget → Structured amount + currency
Dates → Date picker / flexible range
Travel style → Selection
Pace → Selection
```

---

# 17. Itinerary Visual Language

The itinerary should feel like a **journey narrative** rather than a spreadsheet.

Example hierarchy:

```text
DAY 01
Kolkata → Jaipur

Morning
   ↓
Amber Fort

Afternoon
   ↓
City Palace

Evening
   ↓
Local Rajasthani food experience
```

The design should emphasize:

- Day progression
- Destination
- Experiences
- Food
- Hotel
- Weather
- Important notes

Exact travel times between activities do not need to dominate the user-facing design.

---

# 18. Budget Visual Language

Budget should be visually understandable at a glance.

Possible structure:

```text
TOTAL ESTIMATE
₹78,500

Budget
₹80,000

Remaining
₹1,500
```

Then break down:

```text
Transport
Hotels
Food
Activities
Visa
Miscellaneous
Contingency
```

Use charts sparingly.

The budget interface should communicate financial status without making the product feel like an accounting application.

---

# 19. Weather Visual Language

Weather should be contextual rather than dominant.

For example:

```text
☀️ Good conditions
Outdoor itinerary unchanged
```

or:

```text
🌧️ Rain expected
Amber Fort visit retained
Outdoor activity adjusted
Indoor cultural experience added
```

Weather-driven changes should be visually distinguishable from normal itinerary decisions.

---

# 20. Estimates and Data Confidence

Safarnama will sometimes use estimated information.

Estimated information should have a consistent visual treatment.

Example:

```text
Estimated
₹2,500–₹3,500

Live hotel pricing unavailable
```

The design should make the distinction between:

- Live data
- Static baseline
- Estimated data
- User-provided information

clear without overwhelming the interface.

---

# 21. Accessibility

V1 should follow basic accessibility principles:

- Strong text/background contrast
- Do not rely on color alone to communicate status
- Visible focus states
- Readable font sizes
- Clear form labels
- Descriptive error messages
- Keyboard-friendly interactions
- Semantic HTML where applicable

The warm palette must not compromise readability.

---

# 22. Responsive Design

The design should work across:

- Desktop
- Tablet
- Mobile

The desktop experience can make greater use of:

- Multi-column layouts
- Maps
- Side summaries
- Budget panels

Mobile should prioritize:

```text
Trip overview
↓
Day itinerary
↓
Important decisions
↓
Budget
↓
Supporting details
```

Exact responsive breakpoints remain a frontend implementation decision.

---

# 23. Iconography

Icons should be:

- Simple
- Consistent
- Modern
- Recognizable
- Outline or lightweight filled style

Useful categories include:

- Flight
- Train
- Car
- Hotel
- Restaurant
- Food
- Weather
- Visa
- Budget
- Map
- Activity
- Calendar
- Travelers

Avoid mixing multiple unrelated icon styles.

---

# 24. Motion

Motion should be subtle.

Useful animations:

- Planning progress
- Route drawing
- Card appearance
- Loading states
- Expand/collapse
- Budget updates

Avoid decorative animation that slows down itinerary consumption.

The planning experience should feel active without feeling like a game.

---

# 25. AI / Planning Experience

Safarnama should not visually present itself as a generic chatbot.

The primary interface should communicate:

> **"Safarnama is planning your journey."**

rather than:

> **"Ask an AI anything."**

Planning progress can use meaningful stages:

```text
Understanding your trip
       ↓
Checking travel logistics
       ↓
Finding experiences
       ↓
Checking weather
       ↓
Calculating budget
       ↓
Optimizing your journey
       ↓
Your Safarnama is ready
```

This reinforces the product's identity as a planning engine.

---

# 26. What Is Intentionally Not Locked Yet

The following should remain flexible until the frontend implementation begins:

- Exact component library
- Exact spacing scale
- Exact font sizes
- Border radius values
- Shadow values
- Responsive breakpoints
- Navigation structure
- Dashboard layout
- Detailed itinerary layout
- Animation implementation
- Map provider
- Image provider
- Logo artwork
- Exact icon library
- Dark mode
- Advanced design tokens

These decisions should be made using the actual working product rather than guessing them prematurely.

---

# 27. Initial Design Tokens

The frontend should eventually centralize these values instead of scattering raw colors throughout components.

Example:

```text
--color-primary
--color-primary-dark
--color-maroon
--color-sand
--color-background
--color-text
--color-text-muted
--color-border
--color-success
--color-warning
--color-error
--color-info
```

Typography:

```text
--font-display
--font-heading
--font-body
--font-mono
```

Spacing, radius and shadows should similarly become tokens once the frontend implementation begins.

---

# 28. Design Principles

### 1. Culture without clutter

Indian identity should be recognizable without overwhelming the interface.

### 2. Warmth without sacrificing readability

The product should feel welcoming while remaining highly usable.

### 3. Information without visual overload

Travel planning produces a lot of information. Hierarchy matters more than decoration.

### 4. Journey over dashboard

The experience should communicate movement, discovery and narrative.

### 5. Trust through clarity

Clearly distinguish:

- Confirmed information
- Estimates
- Warnings
- User choices
- Planner decisions

### 6. Modern foundation

Cultural styling should sit on top of a clean modern UI system.

---

# 29. V1 Visual Identity Summary

| Area | Decision |
|---|---|
| Overall style | Warm, cultural, Indian-inspired |
| Theme | Light |
| Primary color | Safarnama Saffron `#E87524` |
| Secondary | Deep Maroon `#7A2E2E` |
| Supporting | Warm Sand `#F4E8D3` |
| Background | Ivory `#FFFDF8` |
| Primary text | Charcoal `#292521` |
| Typography | Modern + friendly |
| Heading/UI font | Poppins |
| Reading/body font | Inter |
| Indian influence | Strong |
| Visual density | Balanced |
| Imagery | Authentic travel photography |
| UI personality | Friendly, warm, exploratory |
| Dark mode | Future |
| Detailed component system | Future |

---

# 30. Design Evolution Rule

This document defines the **visual foundation**, not the final pixel-perfect design.

As the frontend is implemented, visual decisions may be refined based on:

- Actual itinerary density
- Mobile usability
- Accessibility testing
- Real destination imagery
- Budget presentation
- API-generated content
- User testing

Changes should preserve the core identity:

> **Modern travel technology with a distinctly Indian soul.**
