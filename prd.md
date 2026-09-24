# Product Requirements Document (PRD)
# Safarnama — Autonomous Multi-Agent Travel Planner

**Document status:** V1 Product Definition  
**Primary audience:** Product/engineering team  
**Scope:** Requirements and product behavior; implementation details are intentionally deferred.

**Project name:** Safarnama  
**Meaning:** “Safarnama” (सफ़रनामा) — a travelogue/journey narrative; the name represents the product's goal of turning travel constraints and preferences into a coherent journey plan.

---

## 1. Product Overview

**Safarnama** is a travel-planning application that creates personalized, budget-aware itineraries for Indian travelers planning domestic or international trips.

The application accepts structured travel preferences and constraints, researches relevant travel information through specialized tools, and produces a practical day-by-day itinerary covering:

- Route and destinations
- Transportation
- Accommodation
- Attractions and activities
- Local food and restaurants
- Weather-aware scheduling
- Visa and entry requirements for international travel
- Estimated total trip cost
- Budget optimization and trade-offs

The system is intended to behave as a **planning engine**, not merely as a conversational travel chatbot. User-provided choices act as constraints for the planning system rather than assumptions for an LLM to infer.

The system will use multiple specialized agents/nodes and tools. Deterministic calculations and validation are separated from LLM reasoning.

---

## 2. Problem Statement

Planning a multi-day trip requires combining information from many sources:

- Transport options and prices
- Hotels and accommodation
- Attractions and activities
- Local food
- Weather
- Visa requirements
- Entry conditions
- Travel time and route efficiency
- Budget constraints

A conventional search experience makes the traveler manually collect and reconcile this information.

Safarnama aims to provide a single planning workflow that combines these concerns, produces a coherent itinerary, and makes budget trade-offs explicit.

For international travel, the system should also provide enough visa-related information that the user does not need to perform a separate visa research workflow for basic trip planning.

---

## 3. Product Goals

### Primary goals

1. Generate complete, personalized travel itineraries.
2. Support Indian domestic and international travel.
3. Treat the user's budget as a major planning constraint.
4. Optimize the itinerary without silently making major compromises.
5. Include authentic local food recommendations and where to try them.
6. Select hotels and activities automatically using available travel/place data.
7. Adapt the itinerary to weather conditions.
8. Provide visa information for Indian passport holders on international trips.
9. Clearly distinguish live information from estimates.
10. Keep the architecture modular so travel-data providers can be replaced later.
11. Build the product incrementally and validate each layer before adding the next.

### Non-goals for V1

- Booking flights, hotels, or activities directly.
- Arbitrary natural-language itinerary modification.
- Mixed domestic + international trips.
- User-specific traveler profiles with detailed personal attributes.
- Treating an LLM as an authoritative source for live travel entities.
- Using an LLM for arithmetic or final budget calculations.

---

## 4. Target Audience

### Primary audience

**Indian travelers planning domestic or international leisure trips**, particularly travelers who want a complete itinerary without manually researching every component.

Typical users may be:

- Solo travelers
- Couples
- Families
- Groups of adults
- Groups containing adults and children
- Travelers planning domestic multi-state trips
- Travelers planning international multi-country trips
- Travelers who want to stay within a defined budget
- Travelers who want food and cultural experiences included in their itinerary

### Initial geographic scope

- User/passport context: Indian passport holders
- Domestic travel: India
- International travel: destinations outside India
- V1 does not support a mixed domestic + international trip in one planning request.

---

## 5. User Inputs

Safarnama uses structured inputs so that user choices constrain the planning process.

### 5.1 Origin

Required.

The user selects a starting Indian city/airport from a searchable controlled list.

The origin does not have to be the user's home city.

Example:

> Origin: Delhi

even if the traveler normally lives elsewhere.

### 5.2 Destination

Required.

The user can select:

- One or more countries for international travel.
- One or more Indian states/UTs for domestic travel.

Destinations come from controlled searchable lists.

The planner determines the internal city/region route automatically.

### 5.3 Travel scope

The system determines/records:

- Domestic
- International

Mixed domestic + international trips are outside V1 scope.

### 5.4 Travelers

V1 supports:

- Number of adults
- Number of children

The architecture should remain extensible to individual traveler profiles later.

### 5.5 Travel dates

The user can choose any of:

1. **Exact dates**
2. **Flexible date window**
3. **Find suitable dates within a window**

For date optimization, the planner balances:

- Cost
- Weather
- Attraction suitability
- Route feasibility
- Availability
- Overall trip quality

It should present the recommended date range plus 2–3 alternatives and their main trade-offs.

### 5.6 Trip duration

The user can provide:

- A fixed number of days, or
- Flexible duration

For exact dates, duration is derived from the dates.

For flexible duration, the planner determines a suitable duration based on trip constraints.

### 5.7 Budget

The user can specify either:

- Total trip budget, or
- Per-person budget

The budget is **all-inclusive**.

It covers:

- Main transportation
- Accommodation
- Local transportation
- Activities/attractions
- Food
- Visa fees
- Mandatory trip-related costs
- Miscellaneous estimated costs

Discretionary shopping is not included by default.

### 5.8 Travel style

User-selectable:

- Budget
- Comfortable
- Premium
- Luxury

Travel style is a strong preference rather than an absolute constraint.

If the requested style conflicts with the budget, the system explains the trade-off before making a meaningful downgrade.

### 5.9 Activity preferences

Users can select multiple categories, including:

- History & heritage
- Museums
- Architecture
- Nature
- Mountains
- Beaches
- Adventure
- Wildlife
- Shopping
- Nightlife
- Photography
- Spiritual/religious sites
- Art & culture
- Local experiences
- Food experiences
- Relaxation
- Family/kids
- Sports
- Other/custom

The planner chooses the specific attractions and activities.

### 5.10 Must-visit places

The user can explicitly identify must-visit attractions/places.

Must-visits have high priority but are not treated as absolute if the requested combination becomes infeasible.

If fulfilling all must-visits creates a significant budget or schedule conflict, the system explains the trade-off and asks the user rather than silently removing them.

### 5.11 Pace

Simple user-facing choices:

- **Relaxed** — approximately 1–3 major activities/day, more free time and longer meals.
- **Balanced** — approximately 3–5 activities/day with reasonable free time.
- **Packed** — maximize sightseeing with less free time.

### 5.12 Food preferences

Food is configurable by importance:

- Low
- Medium
- High

The user can also specify:

- Dietary preference
- Allergies
- Foods to avoid
- Desired food experiences

Food importance affects itinerary planning.

At high importance, the planner may shape route/scheduling around notable food experiences.

Allergy restrictions are treated as constraints, but recommendations should not claim absolute safety because ingredients and cross-contamination must ultimately be confirmed with the establishment.

### 5.13 Previous international travel

For international travel, V1 captures previous countries visited.

The default input is a simple country list, with optional structured details such as:

- Travel year/date
- Visa type
- Issue date
- Expiry date
- Whether the visa may still be valid

Previous travel/visa history is contextual information and does not replace current visa verification.

---

## 6. Core Product Features

### 6.1 Automatic route planning

The planner automatically determines the internal route across selected destinations.

There is no mandatory route-approval step.

The final result shows the route chosen and relevant reasoning.

### 6.2 Transportation planning

Transportation is planner-controlled.

The planner selects appropriate transportation based on:

- Budget
- Travel time
- Route efficiency
- Traveler count
- Travel style
- Pace
- Availability
- Overall itinerary quality

The user does not need to select the transport mode manually.

### 6.3 Hotel planning

The planner automatically selects suitable hotels using available live hotel/place data.

Selection can consider:

- Budget
- Travel style
- Location
- Route efficiency
- Ratings/reputation
- Amenities
- Traveler/room requirements
- Availability
- Pricing

V1 provides hotel recommendations and booking links.

V1 does not perform hotel booking.

### 6.4 Activity planning

The planner automatically selects specific attractions and experiences based on the user's:

- Destination
- Activity preferences
- Must-visits
- Pace
- Budget
- Travel style
- Weather
- Route efficiency

The activity system uses a hybrid information approach:

- Curated/static knowledge for relevant experiences and regional context.
- Live places data for current place details.

### 6.5 Food planning

The planner recommends local food and actual places to try it.

Restaurant/place selection primarily uses live places data.

Selection dynamically balances:

- Authenticity/local reputation
- Ratings/reviews
- Price
- Location
- Food importance
- Dietary restrictions
- Opening/availability information
- Route efficiency

Food cost is modeled as a **daily estimated food budget**, not as exact menu-level pricing.

### 6.6 Weather-aware itinerary

Weather influences the itinerary automatically.

When significant weather risk exists, the planner can replace or adjust outdoor activities with appropriate alternatives.

The final itinerary explains weather-driven changes.

Long-range forecasts should be treated according to their confidence; weak forecasts should not cause disproportionate itinerary changes.

### 6.7 International visa planning

For international travel by Indian passport holders, the system provides visa/entry information including, where reliably available:

- Visa type
- Cost
- Processing time
- Required documents
- Application process
- Where/how to apply
- Entry requirements
- Relevant restrictions or conditions

Visa information uses:

1. Static baseline visa rules.
2. Live verification/search for current policy changes.

The fallback LLM is **not permitted to invent or estimate visa requirements**.

### 6.8 Destination country profiles and intelligence

For international destinations, the system enriches the planning context with verified country-level metadata:

- Official currencies (code, name, symbol) for local pricing and budget representation.
- Local timezones and time offsets relative to Indian Standard Time (IST, UTC+05:30).
- Regional bloc memberships (specifically Schengen Area status to prevent redundant visa planning for multi-country European travel).
- Official languages and native names.
- Driving orientation (left/right traffic) for self-drive and car rental advisories.
- Country flag emoji and calling code prefixes.

Metadata is backed by static normalized profiles (`data/static/countries.json`) derived from REST Countries v5.

### 6.9 Budget planning

The budget engine produces an itemized trip estimate covering:

- Main transportation
- Accommodation
- Local transport
- Activities
- Visa
- Food
- Miscellaneous costs
- Contingency

All arithmetic is deterministic and performed outside the LLM.

### 6.9 Dynamic contingency

The contingency percentage is dynamic rather than a fixed 10%.

It can depend on:

- Domestic/international scope
- Number of countries
- Number of transport legs
- Date flexibility
- Price uncertainty
- Data availability
- Visa/logistics uncertainty
- Other trip complexity

The contingency applies to the complete estimated trip cost.

### 6.10 Budget optimization

Budget intervention follows these rules:

- **≤5% over budget:** minor optimizations may be performed automatically.
- **5–15% over:** present the user with trade-offs before making meaningful changes.
- **>15% over:** explain that the requested combination is substantially above budget and present alternatives.

Minor optimizations may include:

- Cheaper but appropriate hotel
- More economical transport with limited impact
- Lower-cost activity alternatives
- Lower-cost food assumptions

Automatic optimization must obey hard quality guardrails.

### 6.11 Quality guardrails

Budget optimization must not:

- Remove a must-visit silently.
- Violate dietary/allergy constraints.
- Materially violate the selected pace.
- Make unreasonable hotel downgrades.
- Add excessive travel time merely to reduce cost.
- Replace major experiences with unrelated low-cost activities.
- Materially damage the intended travel style without user involvement.

### 6.12 Infeasible budget handling

If no acceptable itinerary can satisfy the user's budget and quality constraints:

1. Explain that the requested combination is not feasible within the current budget.
2. Show the realistic estimated budget.
3. Explain major cost drivers.
4. Present possible trade-offs, such as:
   - Increase budget
   - Reduce duration
   - Remove a destination
   - Lower travel style
   - Change transport expectations
   - Reduce activities
5. Let the user choose.

If the user changes the budget, the system should reuse valid work and re-plan only affected components.

---

## 7. Data and Tool Architecture Requirements

The product will use specialized tools/adapters rather than assuming one API provides all travel data.

Conceptually:

`Agent/Node → Tool interface → External provider`

Potential tool categories include:

- Flight/transport
- Hotels
- Places/attractions
- Restaurants
- Weather
- Visa/live search
- Currency
- Calculator
- Static data

Providers should be replaceable without changing the core planning logic.

### 7.1 Tool fallback strategy

For live travel data:

1. Primary provider/tool
2. Alternate provider/tool
3. Dedicated fallback LLM for estimation
4. Omit the component and warn if an acceptable estimate cannot be produced

### 7.2 Fallback LLM

A separate LLM/model and API key may be used solely as a fallback estimation service.

It may estimate:

- Hotel prices
- Transport prices
- Food costs
- Activity costs
- Other missing numerical travel costs

It must **not invent specific entities**, including:

- Hotels
- Restaurants
- Flights
- Attractions
- Booking links

It must also not invent visa requirements or authoritative visa facts.

Every fallback-LLM-generated estimate must be explicitly labeled:

> **Estimated — live data unavailable**

### 7.3 Fixtures and offline testability

API wrappers should support fixture-based operation for development and testing.

Fixtures allow the application to operate without external API calls and help preserve API credits.

---

## 8. Static Data

The project uses periodically refreshable upstream datasets, but V1 ingestion is **on-demand**, not automatically scheduled.

### Airport dataset

Source:

`davidmegginson/ourairports-data`

Target source file:

`airports.csv`

Generated dataset:

`data/static/airports.json`

The ingestion extracts:

- IATA codes
- Relevant airport types
- Municipality/city
- ISO country
- Latitude
- Longitude

The coordinates support downstream weather and travel calculations.

### Visa baseline dataset

Source:

`ilyankou/passport-index-dataset`

Generated dataset:

`data/static/visa_rules.json`

The baseline is filtered for Indian passports and maps destination countries to baseline entry requirements.

The static dataset is a **baseline**, not the sole authoritative source for current visa policy.

### Static-data ingestion

The ingestion scripts are manually/on-demand executable in V1.

If a refresh is unavailable, existing known-good static data can continue to be used.

---

## 9. Itinerary Output Requirements

The final output has two levels.

### 9.1 Trip overview

Should include:

- Trip dates
- Duration
- Route
- Destinations/cities
- Total estimated cost
- Budget status
- Hotels
- Main transportation
- Major experiences
- Visa summary when applicable
- Important warnings/estimates

### 9.2 Detailed day-by-day itinerary

Each day should use **dayparts/time ranges**, not exact clock times.

Example structure:

- Morning
- Afternoon
- Evening

Each day can include:

- Activities
- Attractions
- Food/restaurant recommendations
- Hotel
- Relevant costs
- Daily food estimate
- Weather adjustments
- Important notes

The user-facing itinerary does **not** need to display detailed travel times between every activity, although the planner uses travel time internally for route optimization.

---

## 10. Human-in-the-Loop Principles

The product should automate planning while preserving user control over meaningful trade-offs.

The system can make small optimizations automatically.

The system should involve the user when a change materially affects:

- Budget
- Travel style
- Must-visit places
- Trip duration
- Destinations
- Major experiences

The system should not silently make major compromises merely to satisfy a numeric budget.

---

## 11. International Travel Scope

V1 is designed around Indian passport holders.

International planning must account for:

- Multiple countries
- Country-specific visa requirements
- Visa costs
- Visa processing times
- Entry conditions
- Multi-country logistics
- Cross-border transportation
- Destination-specific weather
- Country-specific food and experiences

The architecture must support more than one international destination in a single trip.

---

## 12. Domestic Travel Scope

Domestic planning supports multiple Indian states/UTs.

The user can select multiple states/UTs, and the planner determines the internal route across relevant cities/regions.

The same general planning system applies:

- Transport
- Hotels
- Activities
- Food
- Weather
- Budget
- Optimization

Visa processing is bypassed for domestic trips.

---

## 13. User Experience Principles

The user-facing experience should be simple even though the internal planning system is sophisticated.

Principles:

1. Prefer structured choices over excessive configuration.
2. Do not expose internal agent complexity unnecessarily.
3. Explain meaningful decisions and trade-offs.
4. Clearly label estimates.
5. Avoid false precision.
6. Respect explicit user constraints.
7. Do not silently remove important experiences.
8. Provide useful alternatives when constraints conflict.
9. Keep the itinerary practical rather than maximizing the number of attractions.

---

## 14. Planning Priorities

When multiple planning objectives conflict, the planner should prioritize:

1. Must-see attractions
2. Minimize unnecessary travel
3. Authentic local experiences
4. Local food
5. Comfortable pace
6. Variety
7. Number of attractions

The goal is a coherent and enjoyable itinerary rather than the maximum possible number of attractions.

---

## 15. Success Criteria

The product should be considered successful when it can reliably:

- Accept a structured trip request.
- Distinguish domestic and international planning.
- Resolve origins/destinations using controlled data.
- Plan single- and multi-destination trips.
- Produce a coherent route and day-by-day itinerary.
- Select hotels and activities using appropriate live data.
- Recommend local food and restaurants.
- Incorporate weather into scheduling.
- Provide current visa verification for international trips.
- Calculate costs deterministically.
- Respect the user's budget and quality guardrails.
- Explain unavoidable budget conflicts.
- Use fallback estimates without fabricating concrete travel entities.
- Clearly label estimates.
- Continue operating with fixture/static data when live APIs are unavailable.
- Reuse unaffected planning work when the user changes a major constraint such as budget.
- Be testable offline.

---

## 16. V1 Boundaries and Future Extensions

The architecture should allow future additions without requiring a fundamental redesign.

Potential future capabilities include:

- Individual traveler profiles
- Rich natural-language itinerary modifications
- Actual booking integrations
- More traveler nationalities
- Additional travel providers
- Automated static-data refresh
- More sophisticated price forecasting
- Additional transportation modes/providers
- More granular traveler-specific pricing
- Additional planning objectives

These are not required for the initial implementation.

---

## 17. Product Definition Summary

Safarnama is a **constraint-aware, multi-agent travel planning system for Indian travelers**.

Its central promise is:

> **Give the planner your destination, dates, duration, travelers, budget, pace, interests, food preferences, and must-visits; it will assemble a practical itinerary, research the required travel information, manage the budget, adapt to weather, and explain important trade-offs without silently compromising the trip.**

The system is deliberately designed so that:

- LLMs handle reasoning and structured planning.
- Tools retrieve real-world data.
- Static datasets provide fast baseline information.
- A dedicated fallback LLM provides clearly labeled estimates when data retrieval fails.
- Deterministic code performs all financial calculations.
- User control is preserved when meaningful trade-offs are required.
