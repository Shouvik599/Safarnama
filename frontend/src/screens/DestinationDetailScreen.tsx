import React, { useState } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import {
  SAMPLE_HOKURIKU_ITINERARY,
  getDestinationDetail,
  synthesizeItineraryFromDraft,
} from '../data/sampleItinerary';
import type { FinalItinerary, DestinationDetail } from '../types/itinerary';
import { DestinationSnapshotGrid } from '../components/itinerary/DestinationSnapshotGrid';

interface DestinationDetailScreenProps {
  destinationName?: string;
  onNavigateHome: () => void;
  onNavigateOverview: () => void;
  onNavigateItinerary: (dayNumber?: number) => void;
  onNavigateTransport: (legId?: string) => void;
  onNavigateEditTrip: () => void;
  // Batch 5 handoff callbacks
  onNavigateStay?: (hotelName?: string) => void;
  onNavigateDining?: (mealTitle?: string) => void;
  onNavigateExperience?: (poiName?: string) => void;
  onNavigateMap?: () => void;
}

export const DestinationDetailScreen: React.FC<DestinationDetailScreenProps> = ({
  destinationName = 'Kyoto',
  onNavigateHome,
  onNavigateOverview,
  onNavigateItinerary,
  onNavigateTransport,
  onNavigateEditTrip,
  onNavigateStay,
  onNavigateDining,
  onNavigateExperience,
  onNavigateMap,
}) => {
  const { itinerary, tripDetails, destinations, preferences, budget } = useTripPlanning();

  const activeItinerary: FinalItinerary =
    itinerary ||
    (tripDetails.destination
      ? synthesizeItineraryFromDraft(tripDetails, destinations, preferences, budget)
      : SAMPLE_HOKURIKU_ITINERARY);

  // Active destination
  const activeDestName =
    destinationName ||
    activeItinerary.trip_context.destinations[1] ||
    activeItinerary.trip_context.destinations[0] ||
    'Kyoto';

  const [currentCity, setCurrentCity] = useState<string>(activeDestName);
  const detail: DestinationDetail = getDestinationDetail(currentCity, activeItinerary);

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
              onClick={() => onNavigateItinerary(3)}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Itinerary
            </button>
          </nav>

          <div className="flex items-center gap-space-sm">
            <button
              type="button"
              onClick={() => (onNavigateMap ? onNavigateMap() : onNavigateTransport('leg-3'))}
              className="px-space-md py-2 rounded-xl bg-surface-container-low text-secondary hover:bg-surface-container border border-outline-variant/30 font-label-sm text-label-sm font-bold flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">map</span>
              <span className="hidden sm:inline">Route Map</span>
            </button>
            <button
              type="button"
              onClick={() => onNavigateItinerary(3)}
              className="px-space-md py-2 rounded-xl bg-surface-container-low text-primary hover:bg-surface-container border border-outline-variant/30 font-label-sm text-label-sm font-bold flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">calendar_today</span>
              <span className="hidden sm:inline">View in Itinerary</span>
            </button>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-[1280px] w-full mx-auto px-margin-mobile lg:px-margin pt-28 pb-space-2xl flex flex-col gap-space-lg">
        {/* 2. Sub-Header Route Breadcrumbs & Actions */}
        <div className="flex flex-wrap items-center justify-between gap-space-sm">
          <div className="flex items-center gap-space-xs text-on-surface-variant font-label-sm text-label-sm">
            <button
              type="button"
              onClick={onNavigateOverview}
              className="flex items-center gap-1 text-primary hover:underline font-bold cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_back</span>
              <span>Trip Overview</span>
            </button>
            <span className="text-outline-variant">•</span>
            <span>Destinations</span>
            <span className="text-outline-variant">•</span>
            <span className="text-on-surface font-semibold">
              {detail.name} ({detail.nights} Nights • Stop {detail.stop_number} of {detail.total_stops})
            </span>
          </div>

          {/* Quick Destination Switcher if multi-destination */}
          <div className="flex items-center gap-1.5 bg-surface-container-low p-1 rounded-xl border border-outline-variant/30">
            {activeItinerary.trip_context.destinations.map((dName) => (
              <button
                key={dName}
                type="button"
                onClick={() => setCurrentCity(dName)}
                className={`px-space-md py-1 rounded-lg font-label-caption text-label-caption font-bold transition-all cursor-pointer ${
                  currentCity.toLowerCase() === dName.toLowerCase()
                    ? 'bg-primary text-on-primary shadow-xs'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                {dName}
              </button>
            ))}
          </div>
        </div>

        {/* 3. Destination Hero Banner */}
        <section className="relative rounded-3xl overflow-hidden shadow-md border border-outline-variant/30 bg-surface-container">
          <div className="relative w-full h-[360px] md:h-[440px]">
            <img
              src={detail.hero_image}
              alt={detail.name}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/45 to-black/20" />

            <div className="absolute inset-0 p-space-xl md:p-space-2xl flex flex-col justify-end text-white">
              <div className="flex flex-wrap items-center gap-space-xs mb-space-xs">
                <span className="px-space-md py-1 rounded-full bg-primary text-on-primary font-label-caption text-label-caption font-bold uppercase tracking-wider shadow-sm">
                  Stop 0{detail.stop_number} of 0{detail.total_stops} • {detail.nights} Nights in Active Itinerary
                </span>
                <span className="px-space-md py-1 rounded-full bg-white/20 backdrop-blur-md text-[12px] font-semibold">
                  {detail.stay_dates}
                </span>
              </div>

              <div className="flex items-baseline gap-space-md">
                <h1 className="font-headline-lg text-[36px] md:text-[54px] font-bold tracking-tight">
                  {detail.name}
                </h1>
                <span className="font-display-hero text-[30px] md:text-[44px] text-white/70 font-light select-none">
                  {detail.native_script}
                </span>
              </div>

              <p className="font-body-md text-[15px] md:text-[17px] text-white/90 max-w-3xl mt-1 leading-relaxed">
                {detail.region}, {detail.country} • {detail.editorial_intro}
              </p>

              {/* Sanctuary Lodging Callout Strip */}
              <div className="mt-space-md p-space-md rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex flex-wrap items-center justify-between gap-space-sm max-w-3xl">
                <div className="flex items-center gap-space-xs text-white">
                  <span className="material-symbols-outlined text-[20px] text-primary">hotel</span>
                  <span className="font-body-sm text-[13px] md:text-[14px]">
                    {detail.sanctuary_lodging_callout}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => onNavigateItinerary(3)}
                  className="px-space-md py-1 rounded-xl bg-white text-on-surface font-label-sm text-label-sm font-bold hover:bg-white/90 transition-colors shadow-xs cursor-pointer flex-shrink-0"
                >
                  View Itinerary Days
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* 4. Destination Snapshot Matrix (6 Bento Cards) */}
        <section className="flex flex-col gap-space-md">
          <div>
            <span className="font-label-caption text-label-caption uppercase tracking-wider text-primary font-bold">
              Destination Intelligence
            </span>
            <h2 className="font-headline-md text-headline-md text-on-surface font-bold">
              Snapshot & Regional Vitality Matrix
            </h2>
          </div>

          <DestinationSnapshotGrid snapshot={detail.snapshot} />
        </section>

        {/* 5. Curator's Editorial Selection Section */}
        <section className="p-space-xl rounded-3xl bg-surface-container-low border border-outline-variant/30 flex flex-col md:flex-row items-stretch gap-space-xl">
          <div className="flex-1 flex flex-col justify-between gap-space-md">
            <div>
              <span className="font-label-caption text-label-caption uppercase tracking-wider text-primary font-bold">
                Curator Editorial
              </span>
              <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface mt-0.5">
                Why Safarnama Curated {detail.name} for Your Journey
              </h3>
              <blockquote className="mt-space-sm p-space-md rounded-2xl bg-surface-container-lowest border-l-4 border-primary text-on-surface font-body-md text-body-md italic leading-relaxed shadow-xs">
                "{detail.curator_selection.quote}"
              </blockquote>
            </div>

            <div className="flex flex-wrap gap-2">
              {detail.curator_selection.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-space-md py-1 rounded-full bg-surface-container text-on-surface-variant font-label-caption text-label-caption font-semibold flex items-center gap-1"
                >
                  <span className="material-symbols-outlined text-[14px] text-primary">check_circle</span>
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Pacing Harmonizer Card */}
          <div className="w-full md:w-80 p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-on-surface-variant mb-space-xs">
                <span className="font-label-caption text-label-caption uppercase font-bold">
                  Pacing Harmonizer
                </span>
                <span className="material-symbols-outlined text-[18px] text-primary">speed</span>
              </div>
              <h4 className="font-headline-sm text-[16px] font-bold text-on-surface">
                {detail.curator_selection.active_discovery_hours}h Daily Discovery
              </h4>
              <p className="font-body-sm text-[13px] text-on-surface-variant mt-1">
                Optimized ratio between active walking exploration and restorative machiya tea pauses.
              </p>
            </div>

            <div className="mt-space-md space-y-2">
              <div className="flex items-center justify-between font-label-caption text-label-caption">
                <span className="text-primary font-bold">Active Exploration ({detail.curator_selection.active_ratio_percent}%)</span>
                <span className="text-secondary font-bold">Leisure Margin ({detail.curator_selection.leisure_ratio_percent}%)</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-surface-container overflow-hidden flex">
                <div
                  className="bg-primary h-full"
                  style={{ width: `${detail.curator_selection.active_ratio_percent}%` }}
                />
                <div
                  className="bg-secondary h-full"
                  style={{ width: `${detail.curator_selection.leisure_ratio_percent}%` }}
                />
              </div>
            </div>
          </div>
        </section>

        {/* 6. Curated Neighborhood Waypoints */}
        <section className="flex flex-col gap-space-md">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-label-caption text-label-caption uppercase tracking-wider text-primary font-bold">
                Neighborhood Micro-Districts
              </span>
              <h2 className="font-headline-md text-headline-md text-on-surface font-bold">
                Curated Waypoints Across {detail.name}
              </h2>
            </div>
            <span className="font-label-caption text-label-caption text-on-surface-variant font-medium">
              {detail.neighborhoods.length} Districts Mapped
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter">
            {detail.neighborhoods.map((nh) => (
              <div
                key={nh.id}
                className="flex flex-col rounded-2xl bg-surface-container-lowest border border-outline-variant/30 overflow-hidden shadow-xs hover:shadow-md transition-all group"
              >
                <div className="relative w-full h-44 bg-surface-container overflow-hidden">
                  <img
                    src={nh.image_url}
                    alt={nh.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute bottom-2 left-2 flex items-center gap-1.5">
                    <span className="px-2.5 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-white font-label-caption text-[11px] font-bold">
                      {nh.recommended_time}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full bg-primary/80 backdrop-blur-md text-white font-label-caption text-[11px] font-semibold">
                      {nh.duration}
                    </span>
                  </div>
                </div>

                <div className="p-space-lg flex flex-col flex-1 justify-between gap-space-sm">
                  <div>
                    <div className="flex items-center justify-between">
                      <h4 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                        {nh.name}
                      </h4>
                      {nh.native_name && (
                        <span className="font-label-sm text-label-sm text-on-surface-variant font-medium">
                          {nh.native_name}
                        </span>
                      )}
                    </div>
                    <p className="font-body-sm text-body-sm text-on-surface-variant mt-1 leading-relaxed">
                      {nh.description}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 pt-space-xs border-t border-outline-variant/15">
                    <div className="flex flex-wrap gap-1.5">
                      {nh.highlights.map((hl) => (
                        <button
                          key={hl}
                          type="button"
                          onClick={() => onNavigateExperience?.(hl)}
                          className="px-2 py-0.5 rounded-md bg-surface-container hover:bg-primary/10 hover:text-primary text-on-surface font-label-caption text-[11px] font-medium transition-colors cursor-pointer"
                        >
                          {hl}
                        </button>
                      ))}
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => onNavigateStay?.(nh.name)}
                        className="text-primary hover:underline font-label-caption text-[11px] font-bold cursor-pointer"
                      >
                        Find Stays
                      </button>
                      <span className="text-outline-variant">•</span>
                      <button
                        type="button"
                        onClick={() => onNavigateDining?.(`${nh.name} Dining`)}
                        className="text-secondary hover:underline font-label-caption text-[11px] font-bold cursor-pointer"
                      >
                        Dining
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 7. Practical Mobility & Transit Guide */}
        <section className="p-space-xl rounded-3xl bg-surface-container-lowest border border-outline-variant/30 flex flex-col gap-space-md shadow-xs">
          <div className="flex items-center gap-space-xs">
            <span className="material-symbols-outlined text-[24px] text-primary">directions_subway</span>
            <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
              Practical Mobility & Local Transit Guidance
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md font-body-sm text-body-sm">
            <div className="p-space-md rounded-2xl bg-surface-container-low flex flex-col gap-1">
              <span className="font-label-sm text-label-sm font-bold text-primary flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">train</span>
                Arrival Protocol
              </span>
              <p className="text-on-surface-variant leading-relaxed">
                {detail.mobility_guide.arrival_overview}
              </p>
            </div>

            <div className="p-space-md rounded-2xl bg-surface-container-low flex flex-col gap-1">
              <span className="font-label-sm text-label-sm font-bold text-secondary flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">contactless</span>
                Local Smart Cards & Lines
              </span>
              <p className="text-on-surface-variant leading-relaxed">
                {detail.mobility_guide.local_transit}
              </p>
            </div>

            <div className="p-space-md rounded-2xl bg-surface-container-low flex flex-col gap-1">
              <span className="font-label-sm text-label-sm font-bold text-on-surface flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">directions_walk</span>
                Footwear & Walking Advice
              </span>
              <p className="text-on-surface-variant leading-relaxed">
                {detail.mobility_guide.walking_notes}
              </p>
            </div>
          </div>
        </section>

        {/* 8. Next Stop Connector Card */}
        {detail.next_stop && (
          <section className="p-space-xl rounded-3xl bg-primary/10 border border-primary/30 flex flex-wrap items-center justify-between gap-space-md">
            <div className="flex items-center gap-space-md">
              <div className="w-12 h-12 rounded-2xl bg-primary text-on-primary flex items-center justify-center shadow-sm">
                <span className="material-symbols-outlined text-[28px]">directions_railway</span>
              </div>
              <div>
                <span className="font-label-caption text-label-caption uppercase font-bold text-primary">
                  Next Destination Segment
                </span>
                <h4 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                  {detail.next_stop.destination} via {detail.next_stop.service_name}
                </h4>
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Duration: {detail.next_stop.duration} • Lake Biwa scenic western passage
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onNavigateTransport(detail.next_stop?.leg_id || 'leg-3')}
              className="px-space-xl py-space-sm rounded-xl bg-primary text-on-primary font-label-md text-label-md font-bold hover:bg-primary/90 transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
            >
              <span>Examine Transport Leg</span>
              <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
            </button>
          </section>
        )}
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
            <button type="button" onClick={onNavigateOverview} className="hover:text-primary transition-colors cursor-pointer">
              Overview
            </button>
            <button type="button" onClick={() => onNavigateItinerary(3)} className="hover:text-primary transition-colors cursor-pointer">
              Itinerary
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
