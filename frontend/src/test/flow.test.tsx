import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import App from '../App';

describe('Safarnama Frontend — Batch 1 Connected Flow & Interactive Features', () => {
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
    expect(screen.getByText('Starting From (Origin)')).toBeInTheDocument();
    expect(screen.getByText('Going To (Destination)')).toBeInTheDocument();
    expect(screen.getByText('Step 1 of 5 • Basic Journey Details')).toBeInTheDocument();
  });

  it('supports origin airport autocomplete, quick origin chips, and traveler counters', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Check default values
    const originInput = screen.getByLabelText(/starting from \(origin\)/i) as HTMLInputElement;
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

    // Switch to domestic Ladakh circuit
    const ladakhBtn = screen.getByRole('button', { name: /ladakh pass/i });
    fireEvent.click(ladakhBtn);

    // Weather badge and Visa verdict adapt in real-time
    expect(
      screen.getByText(/Domestic Trip • ₹0 Visa \(ILP\/PAP Required\)/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Passes Open|Winter Adventure|Golden Poplars|Snowmelt/i)
    ).toBeInTheDocument();
  });

  it('seeds dynamic route stops matching selected circuit and reconciles duration with night counters', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

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

  it('supports reordering, adding suggestions, and switching circuit templates on Screen 3', () => {
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
    const addNaraBtn = screen.getByRole('button', { name: /add as day trip/i });
    fireEvent.click(addNaraBtn);

    // Now route should have 4 destinations
    expect(screen.getByText(/4 destinations added/i)).toBeInTheDocument();
    expect(screen.getAllByText('Nara').length).toBeGreaterThan(1);

    // Switch circuit template to Italy Circuit directly on Screen 3
    const italyTemplateBtn = screen.getByRole('button', { name: /italy circuit/i });
    fireEvent.click(italyTemplateBtn);

    // Route should now feature Italian stops
    expect(screen.getByText('Rome')).toBeInTheDocument();
    expect(screen.getByText('Florence')).toBeInTheDocument();
    expect(screen.getByText('Positano & Amalfi')).toBeInTheDocument();
  });

  it('stops at Batch 1 boundary when clicking Continue to Preferences', () => {
    render(<App />);

    // Navigate to Destinations
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // Click Continue to Preferences
    const continuePrefBtn = screen.getByRole('button', { name: /continue to preferences/i });
    fireEvent.click(continuePrefBtn);

    // Notice alert indicating Batch 1 scope boundary
    expect(
      screen.getByText(/Batch 1 scope complete: Step 3 \(Preferences\) will be unlocked in Batch 2!/i)
    ).toBeInTheDocument();
  });

  it('auto-populates destination and seeds matching cities when user enters Norway', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    // Type "Norway" into destination input
    const destInput = screen.getByPlaceholderText(/search city, circuit, or region/i) as HTMLInputElement;
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

    // Click quick featured chip for Rajasthan
    const rajasthanBtn = screen.getByRole('button', { name: /rajasthan royals/i });
    fireEvent.click(rajasthanBtn);

    // Verify domestic visa status
    expect(screen.getAllByText(/Domestic Trip • ₹0 Visa/i).length).toBeGreaterThan(0);

    // Continue to Destinations
    fireEvent.click(screen.getByRole('button', { name: /continue to destinations/i }));

    // Verify Rajasthan stops appear
    expect(screen.getByText('Jaipur')).toBeInTheDocument();
    expect(screen.getByText('Jodhpur')).toBeInTheDocument();
    expect(screen.getByText('Udaipur')).toBeInTheDocument();
    expect(screen.getByText('Jaisalmer')).toBeInTheDocument();
    expect(screen.queryByText('Osaka')).not.toBeInTheDocument();
  });

  it('auto-populates Indian cities, states, UTs, and international countries in destination search bar', () => {
    render(<App />);

    // Go to Trip Details
    fireEvent.click(screen.getAllByRole('button', { name: /plan my trip/i })[0]);

    const destInput = screen.getByPlaceholderText(/search city, circuit, or region/i) as HTMLInputElement;

    // 1. Search for an Indian city (e.g. Udaipur)
    fireEvent.change(destInput, { target: { value: 'Udaipur' } });
    expect(screen.getByText('Udaipur')).toBeInTheDocument();
    expect(screen.getByText(/City in Rajasthan, India/i)).toBeInTheDocument();

    // Select Udaipur from dropdown
    fireEvent.click(screen.getByText('Udaipur'));
    expect(screen.getAllByText(/Domestic Trip • ₹0 Visa/i).length).toBeGreaterThan(0);

    // 2. Search for an Indian state / UT (e.g. Himachal Pradesh)
    fireEvent.change(destInput, { target: { value: 'Himachal' } });
    expect(screen.getByText('Himachal Pradesh')).toBeInTheDocument();
    expect(screen.getByText(/Himachal Pine Valleys/i)).toBeInTheDocument();

    // 3. Search for an international sovereign country (e.g. Spain)
    fireEvent.change(destInput, { target: { value: 'Spain' } });
    expect(screen.getByText('Spain')).toBeInTheDocument();
    expect(screen.getByText(/Madrid, Europe/i)).toBeInTheDocument();
  }, 15000);
});
