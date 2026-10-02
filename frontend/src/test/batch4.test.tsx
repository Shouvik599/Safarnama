import { beforeEach, describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { SAMPLE_HOKURIKU_ITINERARY } from '../data/sampleItinerary';

beforeEach(() => {
  window.history.replaceState(null, '', '/');
  window.localStorage.clear();
  vi.restoreAllMocks();
});

describe('Safarnama Frontend — Batch 4 Itinerary & Timeline Screens', () => {
  it('renders Day-by-Day Itinerary (Screen 10) with progression rail, bento metrics, and periods', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/itinerary?day=3');
    render(<App />);

    // Breadcrumb and dossier context
    expect(screen.getAllByText(/Dossier #SF-8492/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Autumn Along the Hokuriku Corridor/i)).toBeInTheDocument();
    expect(screen.getByText(/Journey Progression Rail/i)).toBeInTheDocument();

    // Progression rail days
    expect(screen.getByRole('tab', { name: /^Day 1:/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /^Day 3:/i })).toBeInTheDocument();

    // Day 3 Hero Headline and Bento Metrics
    expect(screen.getByText(/DAY 03 — Sacred Dawn, Gion Whispers & Zen Sanctuary/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Rhythm/i)).toBeInTheDocument();
    expect(screen.getByText(/Pacing Buffer/i)).toBeInTheDocument();
    expect(screen.getByText(/Walking Footprint/i)).toBeInTheDocument();
    expect(screen.getByText(/Microclimate/i)).toBeInTheDocument();

    // Period sections and cards
    expect(screen.getByText(/Morning: The Sacred Dawn/i)).toBeInTheDocument();
    expect(screen.getByText(/Quiet Dawn Walk: Ninenzaka & Sannenzaka Slopes/i)).toBeInTheDocument();
    expect(screen.getByText(/Private Dawn Tea Ritual at Nanzen-ji Sub-temple/i)).toBeInTheDocument();
    expect(screen.getByText(/Afternoon: Artisanal Pauses & Reflections/i)).toBeInTheDocument();
    expect(screen.getByText(/Seasonal Kaiseki Multi-Course/i)).toBeInTheDocument();
    expect(screen.getByText(/Evening: Twilight Lanterns & Canal Cadence/i)).toBeInTheDocument();

    // Practical Sidecar
    expect(screen.getAllByText(/Sanctuary Lodging/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Restored Gion Machiya Sanctuary/i)).toBeInTheDocument();
    expect(screen.getByText(/Day 3 Spend Breakdown/i)).toBeInTheDocument();
  });

  it('switches active day via Progression Rail in Screen 10 and updates content', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/itinerary?day=3');
    render(<App />);

    expect(screen.getByText(/DAY 03 — Sacred Dawn, Gion Whispers & Zen Sanctuary/i)).toBeInTheDocument();

    // Click Day 1 in the progression rail using exact label
    const day1Tab = screen.getByRole('tab', { name: /^Day 1:/i });
    fireEvent.click(day1Tab);

    // Hero title updates to Day 1
    await waitFor(() => {
      expect(screen.getByText(/DAY 01 — Arrival & Gastronomic Introduction/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Kuromon Market & Namba Orientation/i)).toBeInTheDocument();

    // Click Day 8 (Kanazawa)
    const day8Tab = screen.getByRole('tab', { name: /^Day 8:/i });
    fireEvent.click(day8Tab);

    await waitFor(() => {
      expect(screen.getByText(/DAY 08 — Kenroku-en Gardens & Ancient Artisanal Chaya Guilds/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Kenroku-en Gardens Dawn Walk/i)).toBeInTheDocument();
    expect(screen.getByText(/Gold Leaf Gilding Workshop in Higashi Chaya/i)).toBeInTheDocument();
  });

  it('navigates from Screen 10 to Day Detail / Timeline (Screen 11) with featured experience and radar', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/itinerary?day=3');
    render(<App />);

    const viewFullDayBtn = screen.getByRole('button', { name: /view full day detail/i });
    fireEvent.click(viewFullDayBtn);

    // Should transition to /trip/day-detail?day=3
    await waitFor(() => {
      expect(screen.getByText(/Back to Full Itinerary/i)).toBeInTheDocument();
    });
    expect(window.location.pathname).toBe('/trip/day-detail');

    // Header & vital status strip
    expect(screen.getByText(/Day 03 of 10 • Kyoto Historic Core/i)).toBeInTheDocument();
    expect(screen.getByText(/Curated Route Pacing: Artisanal & Meditative/i)).toBeInTheDocument();
    expect(screen.getByText(/Physical Footprint/i)).toBeInTheDocument();
    expect(screen.getByText(/~8,400 Steps/i)).toBeInTheDocument();

    // Featured Anchor Experience Showcase
    expect(screen.getByText(/Key Focus Experience/i)).toBeInTheDocument();
    expect(screen.getByText(/Why Included in Your Safarnama/i)).toBeInTheDocument();
    expect(screen.getByText(/Curated Insider Access Tips/i)).toBeInTheDocument();

    // Hourly Atmosphere Radar
    expect(screen.getByText(/Atmosphere Radar/i)).toBeInTheDocument();
    expect(screen.getByText(/06:00/i)).toBeInTheDocument();
    expect(screen.getByText(/12:00/i)).toBeInTheDocument();

    // Hour-by-Hour Chronological Flow
    expect(screen.getByText(/Hour-by-Hour Chronological Flow/i)).toBeInTheDocument();

    // Navigating back returns to Full Itinerary
    const backBtn = screen.getByRole('button', { name: /back to full itinerary/i });
    fireEvent.click(backBtn);

    await waitFor(() => {
      expect(screen.getByText(/Journey Progression Rail/i)).toBeInTheDocument();
    });
    expect(window.location.pathname).toBe('/trip/itinerary');
  });

  it('renders Destination Detail (Screen 12) with snapshot matrix, curator note, and neighborhoods', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/destination?name=Kyoto');
    render(<App />);

    // Destination Title & Kanji
    expect(screen.getByRole('heading', { level: 1, name: 'Kyoto' })).toBeInTheDocument();
    expect(screen.getByText('京都')).toBeInTheDocument();
    expect(screen.getByText(/Stop 02 of 03 • 4 Nights in Active Itinerary/i)).toBeInTheDocument();

    // 6-Card Snapshot Matrix
    expect(screen.getByText(/Snapshot & Regional Vitality Matrix/i)).toBeInTheDocument();
    expect(screen.getByText(/Recommended Stay/i)).toBeInTheDocument();
    expect(screen.getByText(/4–5 Nights \(Your Trip: 4 Nights\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Seasonal Window/i)).toBeInTheDocument();
    expect(screen.getByText(/Peak Kōyō \(Late Oct Maple Tint\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Currency & Exchange/i)).toBeInTheDocument();
    expect(screen.getByText(/Japanese Yen/i)).toBeInTheDocument();

    // Curator Editorial & Pacing Harmonizer
    expect(screen.getByText(/Why Safarnama Curated Kyoto for Your Journey/i)).toBeInTheDocument();
    expect(screen.getByText(/Pacing Harmonizer/i)).toBeInTheDocument();
    expect(screen.getByText(/5.5h Daily Discovery/i)).toBeInTheDocument();

    // Neighborhood Waypoints
    expect(screen.getByText(/Curated Waypoints Across Kyoto/i)).toBeInTheDocument();
    expect(screen.getByText(/Higashiyama Historic Core/i)).toBeInTheDocument();
    expect(screen.getByText(/Gion Shirakawa & Pontocho/i)).toBeInTheDocument();
    expect(screen.getByText(/Arashiyama & Sagano Grove/i)).toBeInTheDocument();

    // Mobility & Next Stop Connector
    expect(screen.getByText(/Practical Mobility & Local Transit Guidance/i)).toBeInTheDocument();
    expect(screen.getByText(/Next Destination Segment/i)).toBeInTheDocument();
    expect(screen.getByText(/Kanazawa via JR Thunderbird #17/i)).toBeInTheDocument();

    // Clicking Next Transport takes user to Screen 13
    const examineTransportBtn = screen.getByRole('button', { name: /examine transport leg/i });
    fireEvent.click(examineTransportBtn);

    await waitFor(() => {
      expect(screen.getByText(/Rolling Stock & Service Specifications/i)).toBeInTheDocument();
    });
    expect(window.location.pathname).toBe('/trip/transport');
  });

  it('renders Transport & Route Details (Screen 13) with 5-node milestone flow, specs, and timetable', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/transport?leg=leg-3');
    render(<App />);

    // Route title & service
    expect(screen.getAllByText(/Kyoto Station/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Kanazawa Station/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/JR Thunderbird #17/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/2h 10m scenic lakeside/i)).toBeInTheDocument();

    // Synchronized Corridor Milestone Flow
    expect(screen.getByText(/Synchronized Corridor Milestone Flow/i)).toBeInTheDocument();
    expect(screen.getByText(/Checkpoint 01/i)).toBeInTheDocument();
    expect(screen.getByText(/Sanctuary Departure/i)).toBeInTheDocument();
    expect(screen.getByText(/Station Check-in & Bento Pick/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Express Corridor/i)).toBeInTheDocument();
    expect(screen.getByText(/Terminus Arrival/i)).toBeInTheDocument();

    // Specifications & Baggage
    expect(screen.getByText(/Rolling Stock & Service Specifications/i)).toBeInTheDocument();
    expect(screen.getAllByText(/JR West \(West Japan Railway Company\)/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/683 Series Limited Express EMU/i)).toBeInTheDocument();
    expect(screen.getByText(/Hands-Free Baggage Protocol/i)).toBeInTheDocument();
    expect(screen.getByText(/Covered under JR Hokuriku Arch Pass/i)).toBeInTheDocument();

    // Timetable & Intermediate Stations
    expect(screen.getByText(/Timetable & Station Sequence/i)).toBeInTheDocument();
    expect(screen.getByText(/Omi-Imazu/i)).toBeInTheDocument();
    expect(screen.getByText(/Tsuruga/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Fukui/i).length).toBeGreaterThanOrEqual(1);

    // Fare & Seat Breakdown
    expect(screen.getByText(/Fare & Seat Breakdown/i)).toBeInTheDocument();
    expect(screen.getByText(/Base Fare Ticket:/i)).toBeInTheDocument();
    expect(screen.getByText(/Reserved Green Seat:/i)).toBeInTheDocument();

    // Download Pass button interaction
    const downloadBtn = screen.getByRole('button', { name: /download travel pass/i });
    fireEvent.click(downloadBtn);
    expect(screen.getByText(/Digital Travel Pass & JR Seat Reservation voucher downloaded/i)).toBeInTheDocument();
  });

  it('integrates seamlessly with Batch 3 Trip Overview destination card clicks', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/overview');
    render(<App />);

    // Click Kyoto destination card
    const kyotoHeader = screen.getByRole('heading', { level: 3, name: 'Kyoto' });
    fireEvent.click(kyotoHeader);

    // Navigates to Screen 12
    await waitFor(() => {
      expect(screen.getByText('京都')).toBeInTheDocument();
    });
    expect(window.location.pathname).toBe('/trip/destination');
  });

  it('triggers cadence optimization and updates pacing rhythm indicators', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/itinerary?day=3');
    render(<App />);

    const optimizeBtn = screen.getByRole('button', { name: /optimize cadence/i });
    fireEvent.click(optimizeBtn);

    await waitFor(() => {
      expect(screen.getByText(/Cadence harmonized/i)).toBeInTheDocument();
    });
  });

  it('navigates to Batch 5 Stays handoff screen from Itinerary Lodging and returns safely', async () => {
    window.localStorage.setItem('safarnama.itinerary.v1', JSON.stringify(SAMPLE_HOKURIKU_ITINERARY));
    window.history.replaceState(null, '', '/trip/itinerary?day=3');
    render(<App />);

    const lodgingBtn = screen.getByRole('button', { name: /view lodging details/i });
    fireEvent.click(lodgingBtn);

    // Navigates to /trip/stays
    await waitFor(() => {
      expect(screen.getByText(/Sanctuary Stays & Historic Ryokan Lodging/i)).toBeInTheDocument();
    });
    expect(window.location.pathname).toBe('/trip/stays');

    // Return back to Itinerary
    const returnBtn = screen.getByRole('button', { name: /return to day 3 itinerary/i });
    fireEvent.click(returnBtn);

    await waitFor(() => {
      expect(screen.getByText(/DAY 03 — Sacred Dawn, Gion Whispers & Zen Sanctuary/i)).toBeInTheDocument();
    });
    expect(window.location.pathname).toBe('/trip/itinerary');
  });
});

