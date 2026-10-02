import React, { useState } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import {
  SAMPLE_HOKURIKU_ITINERARY,
  getTransportLegDetail,
  synthesizeItineraryFromDraft,
} from '../data/sampleItinerary';
import type { FinalItinerary, TransportLeg } from '../types/itinerary';
import { TransportMilestoneFlow } from '../components/itinerary/TransportMilestoneFlow';

interface TransportDetailScreenProps {
  legId?: string;
  onNavigateHome: () => void;
  onNavigateOverview: () => void;
  onNavigateItinerary: (dayNumber?: number) => void;
  onNavigateDestination: (destinationName: string) => void;
  onNavigateEditTrip: () => void;
  onNavigateMap?: () => void;
}

export const TransportDetailScreen: React.FC<TransportDetailScreenProps> = ({
  legId = 'leg-3',
  onNavigateHome,
  onNavigateOverview,
  onNavigateItinerary,
  onNavigateDestination,
  onNavigateEditTrip,
  onNavigateMap,
}) => {
  const { itinerary, tripDetails, destinations, preferences, budget } = useTripPlanning();

  const activeItinerary: FinalItinerary =
    itinerary ||
    (tripDetails.destination
      ? synthesizeItineraryFromDraft(tripDetails, destinations, preferences, budget)
      : SAMPLE_HOKURIKU_ITINERARY);

  const legs = activeItinerary.logistics_plan.transport_legs || [];
  const [selectedLegId, setSelectedLegId] = useState<string>(() => {
    const hasSpecified = legs.some((l) => l.id === legId);
    return hasSpecified ? legId : (legs[0]?.id || 'leg-3');
  });

  const leg: TransportLeg = getTransportLegDetail(selectedLegId, activeItinerary);

  const formatInr = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Number.isFinite(amount) ? amount : 0);

  const [downloadAlert, setDownloadAlert] = useState(false);

  const handleDownloadPass = () => {
    setDownloadAlert(true);
    setTimeout(() => setDownloadAlert(false), 2500);
  };

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen flex flex-col antialiased">
      {/* 1. Global Header */}
      <header className="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(41,37,33,0.04)]">
        <div className="h-20 max-w-[1280px] mx-auto px-margin-mobile lg:px-margin flex items-center justify-between gap-gutter">
          <div className="flex items-center gap-space-sm cursor-pointer" onClick={onNavigateHome}>
            <img alt="Safarnama Logo" className="h-8 w-auto object-contain" src="/safarnama-symbol.svg" />
            <span className="hidden sm:inline-block font-headline-sm text-headline-sm text-on-surface tracking-tight ml-space-xs font-bold">
              Safarnama
            </span>
          </div>

          <nav
            aria-label="Application navigation"
            className="hidden md:flex items-center gap-space-xs bg-surface-container-low px-space-xs py-space-xs rounded-full shadow-[0_1px_3px_-1px_rgba(41,37,33,0.03)]"
          >
            <button
              type="button"
              onClick={onNavigateHome}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Explore
            </button>
            <button
              type="button"
              onClick={onNavigateEditTrip}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Planner
            </button>
            <button
              type="button"
              onClick={onNavigateOverview}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Overview
            </button>
            <button
              type="button"
              onClick={() => onNavigateItinerary(7)}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Itinerary
            </button>
          </nav>

          <div className="flex items-center gap-space-sm">
            <button
              type="button"
              onClick={() => (onNavigateMap ? onNavigateMap() : onNavigateOverview())}
              className="px-space-md py-2 rounded-xl bg-surface-container-low text-secondary hover:bg-surface-container border border-outline-variant/30 font-label-sm text-label-sm font-bold flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">map</span>
              <span className="hidden sm:inline">Route Map</span>
            </button>
            <button
              type="button"
              onClick={() => onNavigateItinerary(7)}
              className="px-space-md py-2 rounded-xl bg-surface-container-low text-primary hover:bg-surface-container border border-outline-variant/30 font-label-sm text-label-sm font-bold flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">calendar_today</span>
              <span className="hidden sm:inline">Back to Itinerary</span>
            </button>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-[1280px] w-full mx-auto px-margin-mobile lg:px-margin pt-28 pb-space-2xl flex flex-col gap-space-lg">
        {/* 2. Top Breadcrumb & Segment Status Bar */}
        <div className="flex flex-wrap items-center justify-between gap-space-sm">
          <div className="flex items-center gap-space-xs text-on-surface-variant font-label-sm text-label-sm">
            <button
              type="button"
              onClick={() => onNavigateItinerary(7)}
              className="flex items-center gap-1 text-primary hover:underline font-bold cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_back</span>
              <span>Full Itinerary</span>
            </button>
            <span className="text-outline-variant">•</span>
            <span>Transit Corridor</span>
            <span className="text-outline-variant">•</span>
            <span className="text-on-surface font-semibold">
              {leg.origin} ➔ {leg.destination}
            </span>
          </div>

          <div className="flex items-center gap-space-xs">
            <span className="px-space-md py-1 rounded-full bg-surface-container text-on-surface-variant font-label-caption text-label-caption font-bold">
              Segment Batch #{activeItinerary.trip_id}
            </span>
            <span className="px-space-md py-1 rounded-full bg-secondary/15 text-secondary border border-secondary/20 font-label-caption text-label-caption font-bold flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">lock</span>
              Sync: Seat Locks Confirmed
            </span>
          </div>
        </div>

        {downloadAlert && (
          <div className="p-space-md rounded-2xl bg-secondary/10 border border-secondary/30 text-on-surface flex items-center gap-space-sm animate-fadeIn">
            <span className="material-symbols-outlined text-[20px] text-secondary">check_circle</span>
            <span className="font-body-sm text-body-sm font-semibold">
              Digital Travel Pass & JR Seat Reservation voucher downloaded to your device.
            </span>
          </div>
        )}

        {/* Leg Selector Bar if multiple legs exist */}
        {legs.length > 1 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            {legs.map((l, idx) => (
              <button
                key={l.id || idx}
                type="button"
                onClick={() => setSelectedLegId(l.id || `leg-${idx + 1}`)}
                className={`flex-shrink-0 flex items-center gap-2 px-space-md py-1.5 rounded-xl font-label-sm text-label-sm font-bold transition-all cursor-pointer border ${
                  selectedLegId === (l.id || `leg-${idx + 1}`)
                    ? 'bg-primary text-on-primary border-primary shadow-xs'
                    : 'bg-surface-container-low text-on-surface-variant border-outline-variant/30 hover:text-on-surface'
                }`}
              >
                <span>Leg 0{idx + 1}:</span>
                <span>{l.origin} ➔ {l.destination}</span>
              </button>
            ))}
          </div>
        )}

        {/* 3. Editorial Route Banner */}
        <section className="p-space-xl md:p-space-2xl rounded-3xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex flex-col gap-space-md">
          <div className="flex flex-wrap items-center justify-between gap-space-xs">
            <span className="px-space-md py-1 rounded-full bg-primary/10 text-primary font-label-caption text-label-caption font-bold uppercase tracking-wider">
              {leg.mode} • Scenic Regional Corridor Passage
            </span>
            <span className="font-label-sm text-label-sm text-on-surface-variant font-medium">
              Vetted Carrier: {leg.carrier}
            </span>
          </div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-md pt-space-xs">
            <div>
              <div className="flex items-center gap-space-md flex-wrap">
                <h1 className="font-headline-lg text-[32px] md:text-[44px] font-bold text-on-surface tracking-tight">
                  {leg.origin}
                </h1>
                <span className="material-symbols-outlined text-[32px] text-primary">arrow_forward</span>
                <h1 className="font-headline-lg text-[32px] md:text-[44px] font-bold text-on-surface tracking-tight">
                  {leg.destination}
                </h1>
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant max-w-3xl mt-2 leading-relaxed">
                {leg.notes ||
                  `Scenic regional transit corridor traversing picturesque shorelines and mountain valleys with seamless luggage forwarding and reserved panoramic seating.`}
              </p>
            </div>

            <div className="flex items-center gap-space-xs flex-shrink-0">
              <button
                type="button"
                onClick={handleDownloadPass}
                className="px-space-lg py-2.5 rounded-xl bg-primary text-on-primary font-label-sm text-label-sm font-bold hover:bg-primary/90 transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">confirmation_number</span>
                <span>Download Travel Pass</span>
              </button>
            </div>
          </div>

          {/* Key Route Metrics Strip (4 tiles) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-space-sm mt-space-md pt-space-md border-t border-outline-variant/20">
            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex flex-col justify-between">
              <span className="font-label-caption text-label-caption uppercase font-bold text-on-surface-variant">
                Travel Date
              </span>
              <div className="mt-1">
                <span className="font-headline-sm text-[16px] font-bold text-on-surface block">
                  {leg.travel_date || 'Fri, Oct 24, 2025'}
                </span>
                <span className="font-label-caption text-[11px] text-primary font-semibold">
                  Autumn Foliage Window
                </span>
              </div>
            </div>

            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex flex-col justify-between">
              <span className="font-label-caption text-label-caption uppercase font-bold text-on-surface-variant">
                Corridor Distance
              </span>
              <div className="mt-1">
                <span className="font-headline-sm text-[16px] font-bold text-on-surface block">
                  {leg.distance_km ? `${leg.distance_km} km` : '218.4 km'}
                </span>
                <span className="font-label-caption text-[11px] text-secondary font-semibold">
                  Scenic Track Alignment
                </span>
              </div>
            </div>

            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex flex-col justify-between">
              <span className="font-label-caption text-label-caption uppercase font-bold text-on-surface-variant">
                Transit Duration
              </span>
              <div className="mt-1">
                <span className="font-headline-sm text-[16px] font-bold text-on-surface block">
                  {leg.duration}
                </span>
                <span className="font-label-caption text-[11px] text-on-surface-variant font-medium">
                  Direct High-Speed Link
                </span>
              </div>
            </div>

            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex flex-col justify-between">
              <span className="font-label-caption text-label-caption uppercase font-bold text-on-surface-variant">
                Curated Service
              </span>
              <div className="mt-1">
                <span className="font-headline-sm text-[16px] font-bold text-on-surface truncate block">
                  {leg.service_name || 'Express Service'}
                </span>
                <span className="font-label-caption text-[11px] text-primary font-semibold truncate block">
                  {leg.seat_reservation || 'Reserved Seating'}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* 4. Synchronized Corridor Milestone Flow (5-Node Trajectory Tracker) */}
        {leg.milestones && leg.milestones.length > 0 && (
          <section>
            <TransportMilestoneFlow milestones={leg.milestones} />
          </section>
        )}

        {/* 5. Transit Specifications & Timetable Grid (2 Columns) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-start">
          {/* Left Column (7 cols): Equipment, Carrier & Luggage Policy */}
          <div className="lg:col-span-7 flex flex-col gap-space-lg">
            <div className="p-space-xl rounded-3xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex flex-col gap-space-md">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-[22px] text-primary">train</span>
                <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                  Rolling Stock & Service Specifications
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
                <div className="p-space-md rounded-2xl bg-surface-container-low">
                  <span className="font-label-caption text-label-caption uppercase font-bold text-on-surface-variant block">
                    Operating Carrier
                  </span>
                  <span className="font-headline-sm text-[16px] font-bold text-on-surface mt-0.5 block">
                    {leg.carrier || leg.operator || 'National Rail Operator'}
                  </span>
                  <span className="font-label-caption text-label-caption text-on-surface-variant mt-1 block">
                    Regional Passenger Network
                  </span>
                </div>

                <div className="p-space-md rounded-2xl bg-surface-container-low">
                  <span className="font-label-caption text-label-caption uppercase font-bold text-on-surface-variant block">
                    Equipment Class
                  </span>
                  <span className="font-headline-sm text-[16px] font-bold text-on-surface mt-0.5 block">
                    {leg.equipment || 'High-Comfort Air-Conditioned Coach'}
                  </span>
                  <span className="font-label-caption text-label-caption text-on-surface-variant mt-1 block">
                    Quiet Coach • Panoramic Windows
                  </span>
                </div>

                <div className="p-space-md rounded-2xl bg-surface-container-low sm:col-span-2">
                  <span className="font-label-caption text-label-caption uppercase font-bold text-on-surface-variant block">
                    Seat & Carriage Reservation
                  </span>
                  <span className="font-headline-sm text-[16px] font-bold text-on-surface mt-0.5 block">
                    {leg.seat_reservation || 'Car 01, Reserved Forward Facing Window'}
                  </span>
                  <span className="font-label-caption text-label-caption text-primary font-semibold mt-1 block">
                    Forward scenic lake view alignment secured
                  </span>
                </div>
              </div>

              {/* Luggage Policy & Courier Box */}
              <div className="p-space-md rounded-2xl bg-primary/5 border border-primary/20 flex flex-col gap-1">
                <div className="flex items-center gap-1.5 text-primary">
                  <span className="material-symbols-outlined text-[18px]">luggage</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">
                    Hands-Free Baggage Protocol
                  </span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                  {leg.luggage_policy ||
                    'Main suitcases forwarded directly between sanctuaries. Travel hands-free with a light daypack only.'}
                </p>
              </div>

              {/* Pass Coverage Badge */}
              <div className="p-space-md rounded-2xl bg-secondary/10 border border-secondary/20 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-secondary">verified_user</span>
                  <span className="font-label-sm text-label-sm font-bold text-on-surface">
                    {leg.pass_coverage || 'Covered under Curated Pass Package'}
                  </span>
                </div>
                <span className="font-label-caption text-label-caption text-secondary font-bold">
                  Zero Out-of-Pocket
                </span>
              </div>
            </div>
          </div>

          {/* Right Column (5 cols): Timetable & Intermediate Stations */}
          <div className="lg:col-span-5 flex flex-col gap-space-lg">
            {/* Intermediate Station Timetable */}
            {leg.intermediate_stops && leg.intermediate_stops.length > 0 && (
              <div className="p-space-xl rounded-3xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex flex-col gap-space-md">
                <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/15">
                  <div className="flex items-center gap-1 text-primary">
                    <span className="material-symbols-outlined text-[18px]">schedule</span>
                    <span className="font-label-caption text-label-caption uppercase font-bold">
                      Timetable & Station Sequence
                    </span>
                  </div>
                  <span className="font-label-caption text-label-caption text-on-surface-variant">
                    {leg.intermediate_stops.length} Station Calls
                  </span>
                </div>

                <div className="relative pl-6 flex flex-col gap-space-md">
                  <div className="absolute left-2.5 top-2 bottom-2 w-0.5 bg-outline-variant/30" />

                  {leg.intermediate_stops.map((stop, idx) => (
                    <div key={stop.station + idx} className="relative flex items-center justify-between">
                      <div className="absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full bg-surface border-2 border-primary" />
                      <div>
                        <span className="font-label-sm text-label-sm font-bold text-on-surface block">
                          {stop.station}
                        </span>
                        {stop.notes && (
                          <span className="font-label-caption text-[11px] text-on-surface-variant block">
                            {stop.notes} {stop.platform && `• ${stop.platform}`}
                          </span>
                        )}
                      </div>
                      <span className="font-label-sm text-label-sm font-bold text-primary">
                        {stop.time}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Fare & Pass Breakdown */}
            <div className="p-space-xl rounded-3xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex flex-col gap-space-sm">
              <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/15">
                <div className="flex items-center gap-1 text-primary">
                  <span className="material-symbols-outlined text-[18px]">payments</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">
                    Fare & Seat Breakdown
                  </span>
                </div>
                <span className="font-label-sm text-label-sm font-bold text-on-surface">
                  {formatInr(leg.cost_inr)}
                </span>
              </div>

              <div className="space-y-2 pt-1 font-body-sm text-body-sm">
                <div className="flex items-center justify-between">
                  <span className="text-on-surface-variant">Base Fare Ticket:</span>
                  <span className="font-semibold text-on-surface">
                    {formatInr(leg.fare_breakdown?.base_fare_inr || Math.round(leg.cost_inr * 0.6))}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-on-surface-variant">Reserved Green Seat:</span>
                  <span className="font-semibold text-on-surface">
                    {formatInr(leg.fare_breakdown?.seat_reservation_inr || Math.round(leg.cost_inr * 0.4))}
                  </span>
                </div>
                <div className="flex items-center justify-between pt-1 border-t border-outline-variant/15 font-label-caption text-label-caption">
                  <span className="text-on-surface-variant">Curated Status:</span>
                  <span className="font-bold text-secondary">
                    {leg.fare_breakdown?.status || 'Included in Package'}
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => onNavigateDestination(leg.destination)}
                className="w-full mt-2 py-2 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-label-sm text-label-sm font-bold transition-colors cursor-pointer text-center"
              >
                Explore {leg.destination} Guide
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Global Footer */}
      <footer className="w-full border-t border-outline-variant/20 bg-surface-container-lowest py-space-xl mt-space-2xl">
        <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin flex flex-col md:flex-row items-center justify-between gap-space-md">
          <div className="flex items-center gap-space-xs cursor-pointer" onClick={onNavigateHome}>
            <img alt="Safarnama Logo" className="h-6 w-auto" src="/safarnama-symbol.svg" />
            <span className="font-headline-sm text-headline-sm font-bold text-on-surface">Safarnama</span>
          </div>
          <span className="font-body-sm text-body-sm text-on-surface-variant text-center">
            Handcrafted with cultural intention. Dossier #{activeItinerary.trip_id} • All rights reserved.
          </span>
          <div className="flex items-center gap-space-md font-label-sm text-label-sm text-on-surface-variant">
            <button type="button" onClick={() => onNavigateItinerary(7)} className="hover:text-primary transition-colors cursor-pointer">
              Full Itinerary
            </button>
            <button type="button" onClick={onNavigateOverview} className="hover:text-primary transition-colors cursor-pointer">
              Overview
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
