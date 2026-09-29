import { beforeEach, describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { getContextualCitiesForDestination } from '../data/destinationsRegistry';
import { getMustVisitOptions } from '../data/mustVisitOptions';
import { buildPlanRequestDraft, validateTripDraft } from '../data/planRequest';

beforeEach(() => {
  window.history.replaceState(null, '', '/');
  window.localStorage.clear();
});

describe('Safarnama Frontend — Batch 1 Connected Flow & Interactive Features', () => {
  it('keeps multi-country contextual city results within each selected country', () => {
    const cities = getContextualCitiesForDestination([
      'Japan (Autumn Trail)',
      'Italy Circuit',
    ]);
    expect(cities.some((city) => city.name === 'Tokyo' && city.country === 'Japan')).toBe(true);
    expect(cities.some((city) => city.name === 'Rome' && city.country === 'Italy')).toBe(true);
    expect(cities.every((city) => city.country !== 'India')).toBe(true);
    expect(cities.some((city) => city.name === 'Bodri' || city.name === 'Daboh')).toBe(false);

    const domesticCityResults = getContextualCitiesForDestination('Bodri');
    expect(domesticCityResults.some((city) => city.name === 'Bodri' && city.country === 'India')).toBe(true);
  });

  it('renders Welcome screen by default with branding and CTAs', () => {
    render(<App />);

    // Branding & Header
    expect(screen.getAllByText('Safarnama').length).toBeGreaterThan(0);
    expect(screen.getByText('Travel from India to Anywhere')).toBeInTheDocument();

    // Hero title
    expect(screen.getByText('Plan your journey.')).toBeInTheDocument();
    expect(screen.getByText('Discover more.')).toBeInTheDocument();

    // Bento capabilities
    expect(screen.getByText('Smart Itinerary')).toBeInTheDocument();
    expect(screen.getByText('Routes & Transport')).toBeInTheDocument();
    expect(screen.getByText('Hotels & Experiences')).toBeInTheDocument();

    // Primary CTA buttons
    const planButtons = screen.getAllByRole('button', { name: /plan my trip/i });
    expect(planButtons.length).toBeGreaterThan(0);
  });

  it('navigates from Welcome to Trip Details when clicking "Plan My Trip"', () => {
    render(<App />);

    const planButton = screen.getAllByRole('button', { name: /plan my trip/i })[0];
    fireEvent.click(planButton);

    // Should now be on Screen 2 (Trip Details)
    expect(screen.getByText('Where are you going?')).toBeInTheDocument();
    expect(screen.getByText(/starting from \(origin/i)).toBeInTheDocument();
    expect(screen.getByText(/going to/i)).toBeInTheDocument();
    expect(screen.getByText('Step 1 of 5 • Basic Journey Details')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /domestic \(within india\)/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /international/i })).toBeInTheDocument();
  });

  it('supports origin airport autocomplete, quick origin chips, and traveler counters', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Check default values
    const originInput = screen.getByLabelText(/starting from \(origin/i) as HTMLInputElement;
    expect(originInput.value).toContain('New Delhi');

    // Click quick origin 'Mumbai (BOM)' chip
    const mumbaiBtn = screen.getByRole('button', { name: /mumbai \(bom\)/i });
    fireEvent.click(mumbaiBtn);
    expect(originInput.value).toBe('Mumbai (BOM - Chhatrapati Shivaji)');

    // Test traveler counters
    expect(screen.getByText('2', { selector: '#count-adults, span' })).toBeInTheDocument();
    const increaseButtons = screen.getAllByTitle('Increase Adults');
    fireEvent.click(increaseButtons[0]);
    expect(screen.getByText('3')).toBeInTheDocument();

    // Test party type button
    const soloBtn = screen.getByRole('button', { name: /solo/i });
    fireEvent.click(soloBtn);
    expect(screen.getByRole('button', { name: /solo/i })).toHaveClass('bg-primary-container');
  });

  it('calculates duration automatically when changing dates and toggles departure/return legs', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Check default duration
    expect(screen.getByText(/10 Days • 9 Nights/i)).toBeInTheDocument();

    // Find date pickers by aria-label
    const depInput = screen.getByLabelText(/departure date/i) as HTMLInputElement;
    const retInput = screen.getByLabelText(/return date/i) as HTMLInputElement;
    expect(depInput.value).toMatch(/^\d{4}-\d{2}-\d{2}$/);

    // Change return date to 14 days after departure
    const depParts = depInput.value.split('-').map(Number);
    const targetRet = new Date(Date.UTC(depParts[0], depParts[1] - 1, depParts[2] + 14));
    const targetRetIso = targetRet.toISOString().split('T')[0];
    fireEvent.change(retInput, { target: { value: targetRetIso } });
    expect(screen.getByText(/14 Days • 13 Nights/i)).toBeInTheDocument();

    // Toggle departure leg time
    const depLegBtn = screen.getByTitle(/click to cycle departure leg preference/i);
    expect(depLegBtn).toHaveTextContent(/morning leg/i);
    fireEvent.click(depLegBtn);
    expect(depLegBtn).toHaveTextContent(/afternoon leg/i);
    fireEvent.click(depLegBtn);
    expect(depLegBtn).toHaveTextContent(/evening leg/i);

    // Verify changing date to 2027 updates leg year immediately
    const retLegBtn = screen.getByTitle(/click to cycle return leg preference/i);
    fireEvent.change(retInput, { target: { value: '2027-01-25' } });
    expect(retLegBtn).toHaveTextContent(/2027 • evening leg/i);
  });

  it('displays real-time seasonal weather badge and visa guidance adapting to destination', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Default destination is Japan -> season badge and visa badge are present
    expect(
      screen.getByText(/Season|Serenity|Climate/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/eVisa Active • 90 Days Single Entry/i)
    ).toBeInTheDocument();

    // Switch to Domestic scope
    const domToggle = screen.getByRole('button', { name: /domestic \(within india\)/i });
    fireEvent.click(domToggle);

    // Switch to domestic Ladakh circuit
    const ladakhBtn = screen.getByRole('button', { name: /ladakh pass/i });
    fireEvent.click(ladakhBtn);

    // Weather badge and Visa verdict adapt in real-time: Ladakh requires ILP/PAP
    expect(
      screen.getByText(/Inner Line Permit \(ILP\) \/ PAP Required/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Passes Open|Winter Adventure|Golden Poplars|Snowmelt/i)
    ).toBeInTheDocument();
  });

  it('seeds dynamic route stops matching selected circuit and reconciles duration with night counters', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Switch to Domestic scope
    const domToggle = screen.getByRole('button', { name: /domestic \(within india\)/i });
    fireEvent.click(domToggle);

    // Choose Ladakh circuit
    const ladakhBtn = screen.getByRole('button', { name: /ladakh pass/i });
    fireEvent.click(ladakhBtn);

    // Continue to Destinations (Screen 3)
    const continueBtn = screen.getByRole('button', { name: /continue to destinations/i });
    fireEvent.click(continueBtn);

    // Verify Ladakh stops are dynamically seeded!
    expect(screen.getByText('Where would you like to explore?')).toBeInTheDocument();
    expect(screen.getByText('Leh')).toBeInTheDocument();
    expect(screen.getByText('Nubra Valley')).toBeInTheDocument();
    expect(screen.getByText('Pangong Tso')).toBeInTheDocument();
    expect(screen.getByText(/3 destinations added/i)).toBeInTheDocument();

    // Verify initial duration reconciliation: 3+2+3 = 8 nights for an 8-day trip
    expect(
      screen.getByText(/✓ Balanced Itinerary: All 8 nights allocated across 3 stops/i)
    ).toBeInTheDocument();

    // Increase nights on Nubra Valley (+1 night)
    const increaseNightBtns = screen.getAllByTitle('Increase nights');
    fireEvent.click(increaseNightBtns[1]); // Nubra Valley: 2 -> 3 nights (total 9 nights)

    // Duration reconciliation now warns about over-allocation
    expect(
      screen.getByText(/⚠️ Over-allocated: 9 nights assigned for a 8-night trip \(\+1 extra night\)/i)
    ).toBeInTheDocument();

    // Click "Sync Trip Duration" button to reconcile
    const syncBtn = screen.getByRole('button', { name: /sync trip duration to 9 nights/i });
    fireEvent.click(syncBtn);

    // Now reconciled!
    expect(
      screen.getByText(/✓ Balanced Itinerary: All 9 nights allocated across 3 stops/i)
    ).toBeInTheDocument();
  });

  it('supports reordering and adding suggestions on Screen 3', () => {
    render(<App />);

    // Navigate to Destinations screen
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // Reorder: Move Osaka down (so Kyoto becomes Stop 1)
    const moveDownButtons = screen.getAllByTitle('Move Stop Down');
    fireEvent.click(moveDownButtons[0]);

    // Check stops: first stop should now be Kyoto
    const stopTitles = screen.getAllByRole('heading', { level: 3 });
    expect(stopTitles[0]).toHaveTextContent('Kyoto');
    expect(stopTitles[1]).toHaveTextContent('Osaka');

    // Add a suggestion stop (e.g. Nara)
    const addNaraBtn = screen.getAllByRole('button', { name: /add as day trip/i })[0];
    fireEvent.click(addNaraBtn);

    // Now route should have 4 destinations
    expect(screen.getByText(/4 destinations added/i)).toBeInTheDocument();
    expect(screen.getAllByText('Nara').length).toBeGreaterThan(1);
  });

  it('continues from Destinations into Preferences', () => {
    render(<App />);

    // Navigate to Destinations
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // Click Continue to Preferences
    const continuePrefBtn = screen.getByRole('button', { name: /continue to preferences/i });
    fireEvent.click(continuePrefBtn);

    expect(screen.getByRole('heading', { name: /how do you want to travel/i })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/planner/preferences');
  });

  it('auto-populates destination and seeds matching cities when user enters Norway', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Type "Norway" into destination input
    const destInput = screen.getByPlaceholderText(/search.*(country|circuit|state|region)/i) as HTMLInputElement;
    fireEvent.change(destInput, { target: { value: 'Norway' } });

    // Verify autocomplete option appears and displays Schengen visa requirement
    expect(screen.getByText('Norway Fjords')).toBeInTheDocument();
    expect(screen.getAllByText(/Schengen Visa Required/i).length).toBeGreaterThan(0);

    // Click Continue to Destinations (Screen 3)
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // Verify Norway cities appear (Oslo, Flåm & Sognefjord, Bergen, Tromsø) and NOT Japan cities!
    expect(screen.getByText('Oslo')).toBeInTheDocument();
    expect(screen.getByText('Flåm & Sognefjord')).toBeInTheDocument();
    expect(screen.getByText('Bergen')).toBeInTheDocument();
    expect(screen.getByText('Tromsø')).toBeInTheDocument();
    expect(screen.queryByText('Osaka')).not.toBeInTheDocument();
    expect(screen.queryByText('Kanazawa')).not.toBeInTheDocument();
  });

  it('auto-populates domestic states & UTs (e.g. Rajasthan) with matching domestic stops', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Switch to Domestic scope
    const domToggle = screen.getByRole('button', { name: /domestic \(within india\)/i });
    fireEvent.click(domToggle);

    // Click quick featured chip for Rajasthan
    const rajasthanBtn = screen.getByRole('button', { name: /rajasthan royals/i });
    fireEvent.click(rajasthanBtn);

    // Verify regular domestic destinations completely hide the visa / passport badge
    expect(screen.queryByText(/Domestic Trip • ₹0 Visa/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Visa/i)).not.toBeInTheDocument();

    // Continue to Destinations
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // Verify Rajasthan stops appear
    expect(screen.getByText('Jaipur')).toBeInTheDocument();
    expect(screen.getByText('Jodhpur')).toBeInTheDocument();
    expect(screen.getByText('Udaipur')).toBeInTheDocument();
    expect(screen.getByText('Jaisalmer')).toBeInTheDocument();
    expect(screen.queryByText('Osaka')).not.toBeInTheDocument();
  });

  it('auto-populates Indian cities, states, UTs, and international countries partitioned by scope', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // 1. Switch to Domestic scope
    const domToggle = screen.getByRole('button', { name: /domestic \(within india\)/i });
    fireEvent.click(domToggle);

    const destInput = screen.getByPlaceholderText(/search.*(country|circuit|state|region)/i) as HTMLInputElement;

    // Search for an Indian state / UT (e.g. Himachal Pradesh)
    fireEvent.change(destInput, { target: { value: 'Himachal' } });
    expect(screen.getByText('Himachal Pradesh')).toBeInTheDocument();
    expect(screen.getByText(/Himachal Pine Valleys/i)).toBeInTheDocument();

    // 2. Switch to International scope
    const intlToggle = screen.getByRole('button', { name: /international/i });
    fireEvent.click(intlToggle);

    // Search for an international sovereign country (e.g. Spain)
    fireEvent.change(destInput, { target: { value: 'Spain' } });
    expect(screen.getAllByText('Spain').length).toBeGreaterThan(0);
    expect(screen.getByText(/Madrid, Europe/i)).toBeInTheDocument();
  }, 15000);

  it('Part A & B: strictly enforces contextual city scoping on Screen 2 and replaces Tokyo fallback', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Switch to Domestic scope
    fireEvent.click(screen.getByRole('button', { name: /domestic \(within india\)/i }));

    // Select Rajasthan
    fireEvent.click(screen.getByRole('button', { name: /rajasthan royals/i }));

    // Continue to Destinations (Screen 2)
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // Verify on Screen 2 for Rajasthan
    expect(screen.getByText(/Add Stops in Rajasthan Royals/i)).toBeInTheDocument();

    // Contextual search bar
    const searchInput = screen.getByPlaceholderText(/search cities strictly within/i);

    // Type a city outside Rajasthan (e.g. Paris or Tokyo) and click Add Stop
    fireEvent.change(searchInput, { target: { value: 'Paris' } });
    fireEvent.click(screen.getByRole('button', { name: /add stop/i }));

    // Validation alert must appear blocking cross-country noise!
    expect(
      screen.getByText(/is not located within/i)
    ).toBeInTheDocument();
    expect(screen.queryByText('Paris')).not.toBeInTheDocument();

    // Now type a valid Rajasthan city (e.g. Pushkar or Bikaner)
    fireEvent.change(searchInput, { target: { value: 'Pushkar' } });

    // Autocomplete dropdown should show Pushkar
    expect(screen.getAllByText('Pushkar').length).toBeGreaterThan(0);

    // Click "+ Add another destination to route" quick button
    // It must pick the next unadded contextual city for Rajasthan, NEVER Tokyo!
    const addAnotherBtn = screen.getByRole('button', { name: /\+ add another destination to route/i });
    fireEvent.click(addAnotherBtn);

    // Verify Tokyo is NOT added
    expect(screen.queryByText('Tokyo')).not.toBeInTheDocument();
  }, 15000);

  it('preserves accurate visa status for international destinations and prevents domestic city collisions (Pakistan, Nepal, South Korea)', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Switch to International scope
    const intlToggle = screen.getByRole('button', { name: /international/i });
    fireEvent.click(intlToggle);

    const destInput = screen.getByPlaceholderText(/search.*(country|circuit|state|region)/i) as HTMLInputElement;

    // 1. Pakistan test: Type "pakistan", choose Pakistan, ensure visa stays eVisa/VOA and NOT Domestic
    fireEvent.change(destInput, { target: { value: 'pakistan' } });
    const pakistanOption = screen.getByRole('button', { name: /pakistan/i });
    fireEvent.click(pakistanOption);

    // Input must contain Pakistan
    expect(destInput.value).toContain('Pakistan');
    // Visa badge must NOT say Domestic Trip
    expect(screen.queryByText(/Domestic Trip • ₹0 Visa/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/eVisa or Visa on Arrival Available for Indian Passports/i).length).toBeGreaterThan(0);

    // 2. Nepal test: Type "nepal", choose Nepal, ensure visa does NOT flip to UK Visitor Visa
    fireEvent.change(destInput, { target: { value: 'nepal' } });
    const nepalOption = screen.getByRole('button', { name: /nepal/i });
    fireEvent.click(nepalOption);

    expect(destInput.value).toContain('Nepal');
    expect(screen.queryByText(/UK Standard Visitor Visa Required/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/Visa Free • Freedom of Movement for Indian Citizens/i).length).toBeGreaterThan(0);

    // 3. South Korea test: Type "south korea", choose South Korea, ensure it does NOT become South Sikkim
    fireEvent.change(destInput, { target: { value: 'south korea' } });
    const skOption = screen.getByRole('button', { name: /south korea/i });
    fireEvent.click(skOption);

    expect(destInput.value).toContain('South Korea');
    expect(destInput.value).not.toContain('Sikkim');
    expect(screen.queryByText(/Domestic Trip • ₹0 Visa/i)).not.toBeInTheDocument();

    // Continue to Destinations Screen 2 to verify route stops
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));
    // Verify South Korea stops appear, not Sikkim (Gangtok/Pelling/Darjeeling)
    expect(screen.getByText('Seoul')).toBeInTheDocument();
    expect(screen.queryByText('Gangtok')).not.toBeInTheDocument();
    expect(screen.queryByText('Pelling')).not.toBeInTheDocument();
  }, 15000);

  it('prompts Smart Reconciliation Dialog on Continue when duration mismatch exists, and allows 1-click sync or fit', () => {
    render(<App />);

    // Navigate to Trip Details and then Screen 2 (Destinations)
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // By default, Japan circuit is seeded (10 nights total)
    // Add extra nights using [+] button on the first stop to create durationDiff > 0
    const plusButtons = screen.getAllByRole('button', { name: /\+/i });
    fireEvent.click(plusButtons[0]); // Osaka: 2 -> 3 nights (total 11 nights for 10-day trip)

    // Verify over-allocation banner appears
    expect(screen.getByText(/Over-allocated: 11 nights assigned/i)).toBeInTheDocument();

    // Click Continue to Preferences
    const continuePrefBtn = screen.getByRole('button', { name: /continue to preferences/i });
    fireEvent.click(continuePrefBtn);

    // Modal dialog must appear!
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Itinerary Duration Mismatch')).toBeInTheDocument();
    expect(screen.getByText(/Extend Trip to 11 Nights/i)).toBeInTheDocument();
    expect(screen.getByText(/Fit Stops to 10 Days/i)).toBeInTheDocument();

    // Test "Review & Edit Stops Manually" dismisses dialog
    const dismissBtn = screen.getByRole('button', { name: /review & edit stops manually/i });
    fireEvent.click(dismissBtn);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    // Re-click Continue to Preferences to re-open modal
    fireEvent.click(continuePrefBtn);
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    // Click "Extend Trip to 11 Nights"
    const extendBtn = screen.getByRole('button', { name: /extend trip to 11 nights/i });
    fireEvent.click(extendBtn);

    // Dialog closes and proceeds to Preferences.
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /how do you want to travel/i })).toBeInTheDocument();
  });

  it('supports multi-country destination chips, unified Schengen visa guidance, and seeds stops from both countries with cross-border transit', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Choose France from featured
    const franceBtn = screen.getByRole('button', { name: /france \(riviera\)/i });
    fireEvent.click(franceBtn);
    expect(screen.getAllByText('France').length).toBeGreaterThan(0);

    // Click Add Another Country
    const addCountryBtn = screen.getByRole('button', { name: /add another country/i });
    fireEvent.click(addCountryBtn);

    // Search and select Italy
    const destInput = screen.getByPlaceholderText(/type and select sovereign country to add/i);
    fireEvent.change(destInput, { target: { value: 'Italy' } });
    const italyOption = screen.getAllByRole('button', { name: /italy circuit/i })[0];
    fireEvent.click(italyOption);

    // Both chips must now be visible!
    expect(screen.getAllByText('France').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Italy').length).toBeGreaterThan(0);

    // Single unified Schengen visa verdict covering all 2 countries
    expect(
      screen.getByText(/Schengen Visa Required • Single Visa covers all 2 countries/i)
    ).toBeInTheDocument();

    // Continue to Destinations Screen 2
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // Verify stops from both France (Paris/Lyon) and Italy (Rome/Florence) are seeded
    expect(screen.getByText('Paris')).toBeInTheDocument();
    expect(screen.getByText('Rome')).toBeInTheDocument();

    // Cross-border scenic connection connector must be present
    expect(
      screen.getByText(/Cross-Region Scenic Connection to Rome/i)
    ).toBeInTheDocument();
  });


  it('keeps comma-containing destination names from duplicating in multi-country chips', () => {
    render(<App />);

    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);
    fireEvent.click(screen.getByRole('button', { name: /add another country/i }));

    const destinationInput = screen.getByPlaceholderText(/type and select sovereign country to add/i);
    fireEvent.change(destinationInput, { target: { value: 'Italy' } });
    fireEvent.click(screen.getAllByRole('button', { name: /italy circuit/i })[0]);

    const japanChipText = screen.getAllByRole('button', { name: /remove destination/i })[0]
      .parentElement?.textContent;
    expect(japanChipText).toContain('Kyoto, Japan');
    expect(japanChipText).not.toContain('Kyoto, Japan, Kyoto, Japan');

    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));
    expect(screen.getByText('Osaka')).toBeInTheDocument();
    expect(screen.getByText('Rome')).toBeInTheDocument();
  });
  it('supports multi-state/UT input, chip dismissal with ✕, and contextual city union on Screen 2', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Switch to Domestic scope
    fireEvent.click(screen.getByRole('button', { name: /domestic \(within india\)/i }));

    // Rajasthan is selected; click Add Another State/UT/City
    const addStateBtn = screen.getByRole('button', { name: /add another state\/ut\/city/i });
    fireEvent.click(addStateBtn);

    // Search and add Gujarat
    const destInput = screen.getByPlaceholderText(/type and select indian state, ut, or city to add/i);
    fireEvent.change(destInput, { target: { value: 'Gujarat' } });
    const gujaratOption = screen.getAllByRole('button', { name: /gujarat/i })[0];
    fireEvent.click(gujaratOption);

    // Both chips should appear
    expect(screen.getAllByText('Rajasthan').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Gujarat').length).toBeGreaterThan(0);

    // Remove the Rajasthan chip
    const removeBtns = screen.getAllByRole('button', { name: /remove destination/i });
    fireEvent.click(removeBtns[0]);

    // Only Gujarat remains as a chip
    expect(screen.getAllByRole('button', { name: /remove destination/i }).length).toBe(1);
    expect(screen.getAllByText('Gujarat').length).toBeGreaterThan(0);

    // Continue to Screen 2
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // Verify Gujarat stops are seeded
    expect(screen.getByText('Ahmedabad')).toBeInTheDocument();
  });

  it('aggregates border permit guidance when selecting multiple domestic permit regions (Ladakh & Sikkim)', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Switch to Domestic scope
    fireEvent.click(screen.getByRole('button', { name: /domestic \(within india\)/i }));

    // Select Ladakh from featured
    fireEvent.click(screen.getByRole('button', { name: /ladakh pass/i }));

    // Add Sikkim
    fireEvent.click(screen.getByRole('button', { name: /add another state\/ut\/city/i }));
    const destInput = screen.getByPlaceholderText(/type and select indian state, ut, or city to add/i);
    fireEvent.change(destInput, { target: { value: 'Sikkim' } });
    const sikkimOption = screen.getAllByRole('button', { name: /sikkim/i })[0];
    fireEvent.click(sikkimOption);

    // Both permit regions aggregated in badge
    expect(
      screen.getByText(/Inner Line Permit \(ILP\) \/ PAP Required for.*Ladakh.*Sikkim/i)
    ).toBeInTheDocument();
  });

  it('completes Batch 1 to Batch 2, preserves choices through back/forward and a remount', async () => {
    const app = render(<App />);
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));
    fireEvent.click(screen.getByRole('button', { name: /continue to preferences/i }));

    expect(screen.getByRole('heading', { name: /how do you want to travel/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('radio', { name: /premium/i }));
    fireEvent.click(screen.getByRole('radio', { name: /full days/i }));
    fireEvent.click(screen.getByRole('checkbox', { name: /scenic viewpoints/i }));
    fireEvent.change(screen.getByRole('combobox', { name: /search must-visit places/i }), {
      target: { value: 'Kyoto' },
    });
    fireEvent.click(screen.getByRole('option', { name: /Kyoto.*Route stop/i }));
    fireEvent.click(screen.getByRole('button', { name: /continue to budget/i }));

    expect(screen.getByRole('heading', { name: /what is your trip budget/i })).toBeInTheDocument();
    fireEvent.change(screen.getByRole('spinbutton', { name: /target amount in inr/i }), { target: { value: '125000' } });
    fireEvent.click(screen.getByRole('radio', { name: /per person/i }));
    fireEvent.click(screen.getByRole('button', { name: /review trip/i }));

    expect(screen.getByRole('heading', { name: /your journey, at a glance/i })).toBeInTheDocument();
    expect(screen.getByText('Osaka')).toBeInTheDocument();
    expect(screen.getAllByText('Kyoto').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/₹1,25,000/)).toBeInTheDocument();
    expect(screen.getByText(/Per person · INR/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /edit preferences/i }));
    expect((screen.getByRole('radio', { name: /premium/i }) as HTMLInputElement).checked).toBe(true);
    expect((screen.getByRole('radio', { name: /full days/i }) as HTMLInputElement).checked).toBe(true);
    expect(screen.getByText('Kyoto')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /continue to budget/i }));
    fireEvent.click(screen.getByRole('button', { name: /review trip/i }));

    window.history.back();
    await waitFor(() => expect(screen.getByRole('heading', { name: /what is your trip budget/i })).toBeInTheDocument());
    window.history.forward();
    await waitFor(() => expect(screen.getByRole('heading', { name: /your journey, at a glance/i })).toBeInTheDocument());

    app.unmount();
    render(<App />);
    expect(screen.getAllByText('Kyoto').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/₹1,25,000/)).toBeInTheDocument();
    expect(screen.getByText(/Osaka/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /confirm trip details/i }));
    expect(screen.getByRole('status')).toHaveTextContent(/validated and saved on this device/i);
    expect(screen.getByRole('status')).toHaveTextContent(/No plan has been submitted/i);
  });

  it('supports direct loading of implemented routes and rejects budgets below ₹1,000', () => {
    window.history.replaceState(null, '', '/planner/preferences');
    const app = render(<App />);
    expect(screen.getByRole('heading', { name: /how do you want to travel/i })).toBeInTheDocument();
    app.unmount();

    window.history.replaceState(null, '', '/planner/budget');
    render(<App />);
    expect(screen.getByRole('heading', { name: /what is your trip budget/i })).toBeInTheDocument();
    fireEvent.change(screen.getByRole('spinbutton', { name: /target amount in inr/i }), { target: { value: '999' } });
    fireEvent.click(screen.getByRole('button', { name: /review trip/i }));
    expect(screen.getByRole('alert')).toHaveTextContent(/at least ₹1,000/i);
    expect(window.location.pathname).toBe('/planner/budget');
  });

  it('supports keyboard activation and arrow navigation for radio-card controls', () => {
    window.history.replaceState(null, '', '/planner/preferences');
    const app = render(<App />);

    const luxury = screen.getByRole('radio', { name: /luxury/i });
    fireEvent.keyDown(luxury, { key: ' ' });
    expect((luxury as HTMLInputElement).checked).toBe(true);

    fireEvent.keyDown(luxury, { key: 'ArrowRight' });
    expect((screen.getByRole('radio', { name: /thoughtful value/i }) as HTMLInputElement).checked).toBe(true);

    app.unmount();
    window.history.replaceState(null, '', '/planner/budget');
    render(<App />);
    const perPerson = screen.getByRole('radio', { name: /per person/i });
    fireEvent.keyDown(perPerson, { key: ' ' });
    expect((perPerson as HTMLInputElement).checked).toBe(true);
  });

  it('only adds must-visits selected from current destination suggestions', () => {
    window.history.replaceState(null, '', '/planner/preferences');
    render(<App />);

    const search = screen.getByRole('combobox', { name: /search must-visit places/i });
    fireEvent.change(search, { target: { value: 'Atlantis' } });
    expect(screen.getByText(/no matching places in the selected destinations/i)).toBeInTheDocument();
    fireEvent.keyDown(search, { key: 'Enter' });
    expect(screen.getByRole('alert')).toHaveTextContent(/choose a place from the suggestions/i);
    expect(screen.queryByRole('list', { name: /must-visit places/i })).not.toBeInTheDocument();

    fireEvent.change(search, { target: { value: 'Osaka' } });
    const routeStop = screen.getByRole('option', { name: /Osaka.*Route stop/i });
    fireEvent.click(routeStop);
    expect(screen.getByRole('list', { name: /must-visit places/i })).toHaveTextContent('Osaka');
  });

  it('validates a reconciled shared draft and maps the supported backend request fields', () => {
    const details = {
      scope: 'INTERNATIONAL' as const,
      origin: 'Delhi',
      destination: 'Japan',
      destinations: ['Japan'],
      departureDate: 'Mon, Oct 5, 2026',
      returnDate: 'Thu, Oct 15, 2026',
      departureDateIso: '2026-10-05',
      returnDateIso: '2026-10-15',
      departureLegInfo: 'Morning leg',
      returnLegInfo: 'Evening leg',
      durationDays: 10,
      flexibleDates: false,
      partyType: 'couple' as const,
      adults: 2,
      children: 0,
      infants: 0,
    };
    const stops = [{
      id: 'kyoto', name: 'Kyoto', country: 'Japan', nights: 10, role: 'City', imageUrl: '',
    }];
    const preferences = {
      travelStyle: 'PREMIUM' as const,
      pace: 'PACKED' as const,
      activityPreferences: ['NATURE', 'FOOD_EXPERIENCE'] as ('NATURE' | 'FOOD_EXPERIENCE')[],
      mustVisits: ['Kyoto'],
    };
    const budget = { budgetMode: 'PER_PERSON' as const, budgetInr: 125000 };

    expect(validateTripDraft(details, stops, preferences, budget)).toEqual([]);
    expect(buildPlanRequestDraft(details, stops, preferences, budget)).toMatchObject({
      origin: 'Delhi',
      destinations: ['Kyoto'],
      start_date: '2026-10-05',
      end_date: '2026-10-15',
      budget_mode: 'PER_PERSON',
      budget_inr: 125000,
      travel_style: 'PREMIUM',
      pace: 'PACKED',
      activity_preferences: ['NATURE', 'FOOD_EXPERIENCE'],
      must_visits: ['Kyoto'],
    });
    expect(validateTripDraft({ ...details, infants: 1 }, stops, preferences, budget)[0].message)
      .toMatch(/not infants/i);
    expect(validateTripDraft(details, stops, preferences, { ...budget, budgetInr: 999 })[0].message)
      .toMatch(/₹1,000/i);
    expect(validateTripDraft(details, stops, preferences, budget, getMustVisitOptions(details, stops))).toEqual([]);
    expect(validateTripDraft(
      details,
      stops,
      { ...preferences, mustVisits: ['Atlantis'] },
      budget,
      getMustVisitOptions(details, stops)
    ).some((issue) => /must-visit places that are not available/i.test(issue.message))).toBe(true);
  });
});
