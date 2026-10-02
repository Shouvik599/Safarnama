import { beforeEach, describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { parseSSEEvents } from '../services/planningStreamService';
import { SAMPLE_HOKURIKU_ITINERARY } from '../data/sampleItinerary';

beforeEach(() => {
  window.history.replaceState(null, '', '/');
  window.localStorage.clear();
  vi.restoreAllMocks();
});

describe('Safarnama Frontend — Batch 3 Planning Progress & Trip Overview', () => {
  it('parses SSE event chunks cleanly into PlanningEvent domain objects', () => {
    const sampleChunk =
      'event: planning_started\ndata: {"stage":"intake","message":"Deconstructing traveler profile"}\n\nevent: budget_calculated\ndata: {"stage":"budget","message":"Budget calculated: INR 362400"}\n\n';

    const events = parseSSEEvents(sampleChunk);
    expect(events.length).toBe(2);
    expect(events[0].event).toBe('planning_started');
    expect(events[0].stage).toBe('intake');
    expect(events[0].message).toBe('Deconstructing traveler profile');
    expect(events[1].event).toBe('budget_calculated');
    expect(events[1].stage).toBe('budget');
  });

  it('navigates from Review Screen (Step 5) to Progress Screen when confirming details', async () => {
    window.history.replaceState(null, '', '/planner/review');
    render(<App />);

    expect(screen.getByText('Your journey, at a glance')).toBeInTheDocument();
    const confirmButton = screen.getByRole('button', { name: /confirm trip details/i });
    expect(confirmButton).toBeInTheDocument();

    fireEvent.click(confirmButton);

    const startPlanningBtn = screen.getByRole('button', { name: /start live planning journey/i });
    expect(startPlanningBtn).toBeInTheDocument();
    fireEvent.click(startPlanningBtn);

    // Should now transition to Progress screen
    await waitFor(() => {
      expect(screen.getByText(/Safarnama is synthesizing your bespoke journey/i)).toBeInTheDocument();
    });

    expect(window.location.pathname).toBe('/planner/progress');
    expect(screen.getByText(/Continuous Synthesis Protocol/i)).toBeInTheDocument();
    expect(screen.getByText(/Understanding your trip/i)).toBeInTheDocument();
    expect(screen.getByText(/Transit & Route Alignment/i)).toBeInTheDocument();
  });

  it('allows canceling synthesis and returning to review with draft inputs preserved', async () => {
    window.history.replaceState(null, '', '/planner/progress');
    render(<App />);

    expect(screen.getByText(/Safarnama is synthesizing your bespoke journey/i)).toBeInTheDocument();
    const cancelButton = screen.getByRole('button', { name: /cancel and return to review/i });
    expect(cancelButton).toBeInTheDocument();

    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.getByText('Your journey, at a glance')).toBeInTheDocument();
    });
    expect(window.location.pathname).toBe('/planner/review');
  });

  it('renders Trip Overview dossier with hero showcase, curator note, and route corridor', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/overview');
    render(<App />);

    // Header & Dossier Meta
    expect(screen.getByText(/Your Safarnama is ready/i)).toBeInTheDocument();
    expect(screen.getByText(/Autumn Along the Hokuriku Corridor/i)).toBeInTheDocument();
    expect(screen.getByText(/Synthesis Complete • Ready for Departure/i)).toBeInTheDocument();
    expect(screen.getAllByText(/SF-8492/i).length).toBeGreaterThanOrEqual(1);

    // Curator's Note & Rhythm Index
    expect(screen.getByText(/Curator’s Note/i)).toBeInTheDocument();
    expect(screen.getByText(/Cultural Immersiveness/i)).toBeInTheDocument();
    expect(screen.getByText('94%')).toBeInTheDocument();
    expect(screen.getByText(/Transit Leisure Margin/i)).toBeInTheDocument();
    expect(screen.getByText('88%')).toBeInTheDocument();

    // Route Corridor
    expect(screen.getByText(/Interactive Route Corridor/i)).toBeInTheDocument();
    expect(screen.getAllByText('Osaka').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Kyoto').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Kanazawa').length).toBeGreaterThanOrEqual(1);

    // Snapshot Matrix
    expect(screen.getByText(/Trip Snapshot Matrix/i)).toBeInTheDocument();
    expect(screen.getByText(/3 Cultural Hubs/i)).toBeInTheDocument();
    expect(screen.getByText(/3 Bespoke Stays/i)).toBeInTheDocument();
    expect(screen.getByText(/Intermodal Corridor/i)).toBeInTheDocument();

    // Budget Breakdown
    expect(screen.getByText(/Budget Snapshot & Leeway Breakdown/i)).toBeInTheDocument();
    expect(screen.getByText(/Favorable Alignment/i)).toBeInTheDocument();

    // Highlights
    expect(screen.getByText(/Highlights of the Journey/i)).toBeInTheDocument();
    expect(screen.getByText(/Private Dawn Tea at Nanzen-ji Sub-temple/i)).toBeInTheDocument();

    // Action Controls
    const viewItineraryBtn = screen.getByRole('button', { name: /view full itinerary/i });
    expect(viewItineraryBtn).toBeInTheDocument();
    fireEvent.click(viewItineraryBtn);

    // Navigates to Day-by-Day Itinerary
    await waitFor(() => {
      expect(screen.getByText(/Journey Progression Rail/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Day 03/i).length).toBeGreaterThanOrEqual(1);
    });
    expect(window.location.pathname).toBe('/trip/itinerary');
  });

  it('supports editing route & preferences from Overview screen returning to Step 1', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/overview');
    render(<App />);

    const editBtn = screen.getByRole('button', { name: /edit route & preferences/i });
    expect(editBtn).toBeInTheDocument();
    fireEvent.click(editBtn);

    await waitFor(() => {
      expect(screen.getByText('Where are you going?')).toBeInTheDocument();
    });
    expect(window.location.pathname).toBe('/planner/trip-details');
  });
});
