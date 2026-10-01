import React, { useState } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import { SAMPLE_HOKURIKU_ITINERARY, synthesizeItineraryFromDraft } from '../data/sampleItinerary';
import type { FinalItinerary } from '../types/itinerary';

interface TripOverviewScreenProps {
  onNavigateHome: () => void;
  onNavigateItinerary: () => void;
  onNavigateEditTrip: () => void;
  onNavigateOptimize?: () => void;
}

export const TripOverviewScreen: React.FC<TripOverviewScreenProps> = ({
  onNavigateHome,
  onNavigateItinerary,
  onNavigateEditTrip,
  onNavigateOptimize,
}) => {
  const { itinerary, tripDetails, destinations, preferences, budget } = useTripPlanning();
  const [shareSuccess, setShareSuccess] = useState(false);

  // Fallback to synthesized or sample itinerary if direct navigation occurred
  const activeItinerary: FinalItinerary =
    itinerary ||
    (tripDetails.destination
      ? synthesizeItineraryFromDraft(tripDetails, destinations, preferences, budget)
      : SAMPLE_HOKURIKU_ITINERARY);

  const formatInr = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Number.isFinite(amount) ? amount : 0);

  const {
    trip_id,
    title,
    summary,
    curator_note,
    cover_image,
    pace_rhythm_index,
    trip_context,
    logistics_plan,
    experience_plan,
    budget_breakdown,
    weather_context,
  } = activeItinerary;

  const handleShare = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      setShareSuccess(true);
      setTimeout(() => setShareSuccess(false), 2500);
    }
  };

  const totalStays = logistics_plan.hotel_stays.length;
  const totalDays = experience_plan.total_days || trip_context.duration_days;
  const stopsCount = trip_context.destinations.length;

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen flex flex-col antialiased">
      {/* Top Header */}
      <header className="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(41,37,33,0.04)]">
        <div className="h-20 max-w-[1280px] mx-auto px-margin-mobile lg:px-margin flex items-center justify-between gap-gutter">
          <div className="flex items-center gap-space-sm cursor-pointer" onClick={onNavigateHome}>
            <img
              alt="Safarnama Logo"
              className="h-8 w-auto object-contain"
              src="/safarnama-symbol.svg"
            />
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
            <span
              aria-current="page"
              className="px-space-md py-space-xs rounded-full transition-colors bg-surface-container-high text-primary font-bold shadow-sm"
            >
              Overview
            </span>
            <button
              type="button"
              onClick={onNavigateItinerary}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Itinerary
            </button>
          </nav>

          <div className="flex items-center gap-space-md">
            <div className="hidden lg:flex items-center gap-space-xs px-space-md py-space-xs rounded-full bg-surface-container-lowest shadow-[0_2px_8px_-2px_rgba(41,37,33,0.04)]">
              <span className="w-2 h-2 rounded-full bg-primary-container animate-pulse" />
              <span className="font-label-caption text-label-caption text-on-surface-variant uppercase tracking-wider font-semibold">
                Dossier Ready
              </span>
            </div>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Dossier Container */}
      <main className="w-full pt-20 bg-surface min-h-[calc(100vh-20rem)] flex-1 pb-space-xl">
        <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin py-space-lg w-full flex flex-col gap-space-xl">
          {/* 1. Top Journey Header & Dossier Meta */}
          <header className="flex flex-col gap-space-md">
            {/* Dossier Marker & Synthesis Pill */}
            <div className="flex flex-wrap items-center justify-between gap-space-sm pb-space-xs">
              <div className="flex items-center gap-space-xs">
                <span className="font-label-caption text-label-caption tracking-widest text-primary uppercase font-bold">
                  Safarnama Dossier
                </span>
                <span className="text-outline-variant font-label-caption text-label-caption">•</span>
                <span className="font-label-md text-label-md text-on-surface-variant font-semibold tracking-wider">
                  #{trip_id}
                </span>
              </div>
              <div className="inline-flex items-center gap-space-xs px-space-md py-1 rounded-full bg-surface-container-high shadow-sm border border-outline-variant/30">
                <span className="w-2 h-2 rounded-full bg-primary-container animate-pulse" />
                <span className="font-label-caption text-label-caption text-on-primary-container font-semibold">
                  Synthesis Complete • Ready for Departure
                </span>
              </div>
            </div>

            {/* Core Display Title & Subhead */}
            <div className="flex flex-col gap-space-xs max-w-4xl">
              <h1 className="font-display-hero text-headline-lg sm:text-display-hero text-on-surface tracking-tight font-bold">
                Your Safarnama is ready.
              </h1>
              <p className="font-body-lg text-body-lg text-on-surface-variant leading-relaxed">
                {title} — {summary}
              </p>
            </div>

            {/* Quick Metadata Bar */}
            <div className="flex flex-wrap items-center gap-space-sm pt-space-xs">
              <div className="inline-flex items-center gap-1.5 px-space-md py-1.5 rounded-full bg-surface-container-low shadow-sm border border-outline-variant/30">
                <span className="material-symbols-outlined text-[16px] text-primary" aria-hidden="true">
                  flight_takeoff
                </span>
                <span className="font-label-md text-label-md text-on-surface-variant">
                  {trip_context.origin}
                </span>
              </div>

              <div className="inline-flex items-center gap-1.5 px-space-md py-1.5 rounded-full bg-surface-container-low shadow-sm border border-outline-variant/30">
                <span className="material-symbols-outlined text-[16px] text-primary" aria-hidden="true">
                  route
                </span>
                <span className="font-label-md text-label-md text-on-surface font-semibold">
                  {trip_context.destinations.join(' ➔ ')}
                </span>
              </div>

              <div className="inline-flex items-center gap-1.5 px-space-md py-1.5 rounded-full bg-surface-container-low shadow-sm border border-outline-variant/30">
                <span className="material-symbols-outlined text-[16px] text-primary" aria-hidden="true">
                  calendar_today
                </span>
                <span className="font-label-md text-label-md text-on-surface-variant">
                  {trip_context.start_date} – {trip_context.end_date} ({totalDays}D / {Math.max(1, totalDays - 1)}N)
                </span>
              </div>

              <div className="inline-flex items-center gap-1.5 px-space-md py-1.5 rounded-full bg-surface-container-low shadow-sm border border-outline-variant/30">
                <span className="material-symbols-outlined text-[16px] text-secondary" aria-hidden="true">
                  group
                </span>
                <span className="font-label-md text-label-md text-on-surface-variant">
                  {trip_context.num_travelers} {trip_context.num_travelers === 1 ? 'Explorer' : 'Explorers'}
                </span>
              </div>

              <div className="inline-flex items-center gap-1.5 px-space-md py-1.5 rounded-full bg-surface-container-low shadow-sm border border-outline-variant/30">
                <span className="material-symbols-outlined text-[16px] text-primary" aria-hidden="true">
                  pace
                </span>
                <span className="font-label-md text-label-md text-on-surface-variant">
                  {trip_context.pace} Pace (~6h/day active)
                </span>
              </div>
            </div>
          </header>

          {/* 2. Prominent Travel Hero Dossier Showcase */}
          <section
            aria-label="Featured destination waypoint"
            className="relative w-full rounded-2xl overflow-hidden shadow-xl bg-surface-container-highest border border-outline-variant/30"
          >
            <div className="relative w-full aspect-[16/9] lg:aspect-[21/9] max-h-[520px]">
              <img
                alt={cover_image?.alt || 'Destination scenery'}
                className="w-full h-full object-cover"
                src={cover_image?.url || SAMPLE_HOKURIKU_ITINERARY.cover_image!.url}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-on-surface/90 via-on-surface/30 to-transparent" />

              {/* Floating Seasonal Badge Top-Right */}
              <div className="absolute top-space-md right-space-md">
                <div className="flex items-center gap-space-xs px-space-md py-1.5 rounded-full bg-surface/90 backdrop-blur-md shadow-md">
                  <span className="w-2.5 h-2.5 rounded-full bg-secondary" />
                  <span className="font-label-caption text-label-caption text-on-surface font-semibold tracking-wide">
                    {cover_image?.seasonal_badge || 'Optimal Seasonal Travel Window'}
                  </span>
                </div>
              </div>

              {/* Bottom Narrative Overlay Caption */}
              <div className="absolute bottom-0 inset-x-0 p-space-md lg:p-space-lg flex flex-col sm:flex-row items-start sm:items-end justify-between gap-space-md">
                <div className="flex flex-col gap-1 max-w-xl text-white">
                  <span className="font-label-caption text-label-caption uppercase tracking-widest text-primary-fixed font-bold">
                    Key Waypoint Showcase
                  </span>
                  <h2 className="font-headline-md text-headline-md text-white tracking-tight font-bold">
                    {cover_image?.waypoint_title || title}
                  </h2>
                  <p className="font-body-sm text-body-sm text-surface-variant opacity-90">
                    {cover_image?.stay_highlight || 'Curated boutique lodging with convenient hub access.'}
                  </p>
                </div>
                <div className="flex items-center gap-space-xs px-space-md py-2 rounded-xl bg-surface-container-lowest/95 backdrop-blur-md shadow-md text-on-surface">
                  <span className="material-symbols-outlined text-[20px] text-primary-container" aria-hidden="true">
                    verified
                  </span>
                  <span className="font-label-md text-label-md font-semibold">
                    Direct Host Reservation Preview
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* 3. Journey Summary Narrative & Philosophy */}
          <section className="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-stretch">
            {/* Left: Curator's Note */}
            <div className="lg:col-span-8 p-space-lg lg:p-space-xl rounded-2xl bg-surface-container-low shadow-sm border border-outline-variant/30 flex flex-col justify-between gap-space-md">
              <div className="flex flex-col gap-space-sm">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-primary text-[22px]">auto_stories</span>
                  <span className="font-label-md text-label-md text-primary uppercase font-bold tracking-wider">
                    Curator&rsquo;s Note
                  </span>
                </div>
                <blockquote className="font-body-lg text-body-lg text-on-surface italic leading-relaxed">
                  &ldquo;{curator_note || summary}&rdquo;
                </blockquote>
              </div>
              <div className="flex flex-wrap items-center gap-space-xs pt-space-xs">
                <span className="px-space-md py-1 rounded-full bg-surface-container-highest text-on-surface-variant font-label-caption text-label-caption font-semibold">
                  Culture & Heritage
                </span>
                <span className="px-space-md py-1 rounded-full bg-surface-container-highest text-on-surface-variant font-label-caption text-label-caption font-semibold">
                  Food & Culinary
                </span>
                <span className="px-space-md py-1 rounded-full bg-surface-container-highest text-on-surface-variant font-label-caption text-label-caption font-semibold">
                  Local Crafts
                </span>
                <span className="px-space-md py-1 rounded-full bg-surface-container-highest text-on-surface-variant font-label-caption text-label-caption font-semibold">
                  Unhurried Discovery
                </span>
              </div>
            </div>

            {/* Right: Pacing & Rhythm Index */}
            <div className="lg:col-span-4 p-space-lg rounded-2xl bg-surface-container shadow-sm border border-outline-variant/30 flex flex-col justify-between gap-space-md">
              <div className="flex flex-col gap-space-xs">
                <span className="font-label-caption text-label-caption uppercase tracking-wider text-secondary font-bold">
                  Curator Alignment
                </span>
                <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                  Pacing & Rhythm Index
                </h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Calibrated for contemplative balance. Active discovery hours balance restorative evening pauses.
                </p>
              </div>

              {/* Metric Indicators */}
              <div className="space-y-space-sm">
                <div>
                  <div className="flex justify-between font-label-caption text-label-caption mb-1">
                    <span className="text-on-surface">Cultural Immersiveness</span>
                    <span className="font-bold text-primary">
                      {pace_rhythm_index?.cultural_immersiveness || 92}%
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-surface-container-highest overflow-hidden">
                    <div
                      className="bg-primary h-full rounded-full"
                      style={{ width: `${pace_rhythm_index?.cultural_immersiveness || 92}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between font-label-caption text-label-caption mb-1">
                    <span className="text-on-surface">Transit Leisure Margin</span>
                    <span className="font-bold text-primary-container">
                      {pace_rhythm_index?.transit_leisure_margin || 88}%
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-surface-container-highest overflow-hidden">
                    <div
                      className="bg-primary-container h-full rounded-full"
                      style={{ width: `${pace_rhythm_index?.transit_leisure_margin || 88}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-space-xs">
                <span className="font-label-caption text-label-caption text-on-surface-variant flex items-center gap-1 font-medium">
                  <span className="material-symbols-outlined text-[15px] text-primary">verified_user</span>
                  Vetted by {pace_rhythm_index?.vetted_by || 'Senior Destination Architect'}
                </span>
              </div>
            </div>
          </section>

          {/* 4. Interactive Route Corridor (The Journey Sequence) */}
          <section className="flex flex-col gap-space-md">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-xs">
              <div>
                <span className="font-label-caption text-label-caption uppercase tracking-wider text-primary font-bold">
                  The Journey Sequence
                </span>
                <h2 className="font-headline-md text-headline-md text-on-surface font-bold">
                  Interactive Route Corridor
                </h2>
              </div>
              <span className="font-body-sm text-body-sm text-on-surface-variant">
                {stopsCount} Geographic Anchor Hubs • Coordinated Scenic Transit Legs
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
              {trip_context.destinations.map((destName, index) => {
                const stayMatch = logistics_plan.hotel_stays[index];
                const legMatch = logistics_plan.transport_legs[index];
                const nightsCount = stayMatch ? stayMatch.nights : Math.round(totalDays / stopsCount) || 2;

                return (
                  <div
                    key={destName}
                    className="flex flex-col p-space-lg rounded-2xl bg-surface-container-lowest shadow-sm hover:shadow-md transition-all border border-outline-variant/30 group"
                  >
                    <div className="flex items-center justify-between pb-space-sm">
                      <div className="flex items-center gap-space-xs">
                        <span className="w-7 h-7 rounded-full bg-primary flex items-center justify-center font-label-md text-label-md text-on-primary font-bold">
                          0{index + 1}
                        </span>
                        <div>
                          <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                            {destName}
                          </h3>
                          <span className="font-label-caption text-label-caption text-on-surface-variant">
                            {stayMatch?.neighborhood || 'Primary Waypoint'}
                          </span>
                        </div>
                      </div>
                      <span className="px-space-md py-1 rounded-full bg-surface-container text-on-surface font-label-caption text-label-caption font-semibold">
                        {nightsCount} {nightsCount === 1 ? 'Night' : 'Nights'}
                      </span>
                    </div>

                    <div className="w-full h-36 rounded-xl overflow-hidden my-space-xs bg-surface-container">
                      <img
                        alt={destName}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        src={destinations[index]?.imageUrl || cover_image?.url || SAMPLE_HOKURIKU_ITINERARY.cover_image!.url}
                      />
                    </div>

                    <p className="font-body-sm text-body-sm text-on-surface-variant pt-space-xs flex-1">
                      {destinations[index]?.role
                        ? `${destinations[index].role}. Immersive regional highlights, cultural ateliers, and verified lodging.`
                        : `Authentic discovery of ${destName} featuring unhurried morning trails and curated neighborhood dining.`}
                    </p>

                    <div className="mt-space-md pt-space-sm flex items-center justify-between text-on-surface-variant bg-surface-container-low p-space-sm rounded-xl border border-outline-variant/20">
                      <div className="flex items-center gap-1 font-label-caption text-label-caption">
                        <span className="material-symbols-outlined text-[16px] text-primary" aria-hidden="true">
                          train
                        </span>
                        <span>{legMatch?.operator || 'Scenic Regional Rail'}</span>
                      </div>
                      <span className="font-label-caption text-label-caption font-bold text-on-surface">
                        {legMatch?.duration || 'Coordinated Transit'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* 5. Trip Snapshot Matrix (6 compact cards) */}
          <section className="flex flex-col gap-space-md">
            <div>
              <span className="font-label-caption text-label-caption uppercase tracking-wider text-primary font-bold">
                Dossier Architecture
              </span>
              <h2 className="font-headline-md text-headline-md text-on-surface font-bold">
                Trip Snapshot Matrix
              </h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-gutter">
              {/* 1. Destinations */}
              <div className="p-space-lg rounded-2xl bg-surface-container-low shadow-sm border border-outline-variant/30 flex flex-col gap-space-xs">
                <div className="flex items-center gap-space-xs text-primary">
                  <span className="material-symbols-outlined text-[20px]">pin_drop</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">Destinations</span>
                </div>
                <h4 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                  {stopsCount} Cultural Hubs
                </h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  {trip_context.destinations.join(', ')} connected by curated scenic routes.
                </p>
              </div>

              {/* 2. Experiences */}
              <div className="p-space-lg rounded-2xl bg-surface-container-low shadow-sm border border-outline-variant/30 flex flex-col gap-space-xs">
                <div className="flex items-center gap-space-xs text-primary-container">
                  <span className="material-symbols-outlined text-[20px]">local_activity</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">Experiences</span>
                </div>
                <h4 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                  {experience_plan.days.length * 2 || 12} Handcrafted Moments
                </h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Private morning permits, master artisan sessions, and culinary trails.
                </p>
              </div>

              {/* 3. Accommodation */}
              <div className="p-space-lg rounded-2xl bg-surface-container-low shadow-sm border border-outline-variant/30 flex flex-col gap-space-xs">
                <div className="flex items-center gap-space-xs text-secondary">
                  <span className="material-symbols-outlined text-[20px]">bed</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">Accommodation</span>
                </div>
                <h4 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                  {totalStays} Bespoke Stays
                </h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Restored townhouses, boutique city hotels & heritage countryside ryokans.
                </p>
              </div>

              {/* 4. Transport */}
              <div className="p-space-lg rounded-2xl bg-surface-container-low shadow-sm border border-outline-variant/30 flex flex-col gap-space-xs">
                <div className="flex items-center gap-space-xs text-primary">
                  <span className="material-symbols-outlined text-[20px]">train</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">Transport</span>
                </div>
                <h4 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                  Intermodal Corridor
                </h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Regional rail passes, high-speed rail connections & direct departure corridor.
                </p>
              </div>

              {/* 5. Estimated Cost */}
              <div className="p-space-lg rounded-2xl bg-surface-container-low shadow-sm border border-outline-variant/30 flex flex-col gap-space-xs">
                <div className="flex items-center gap-space-xs text-primary-container">
                  <span className="material-symbols-outlined text-[20px]">payments</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">Estimated Outlay</span>
                </div>
                <h4 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                  {formatInr(budget_breakdown.total_with_contingency_inr)} Total
                </h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Target cap: {formatInr(budget_breakdown.variance?.user_budget_inr || trip_context.budget_inr)} • Balanced
                </p>
              </div>

              {/* 6. Weather Outlook */}
              <div className="p-space-lg rounded-2xl bg-surface-container-low shadow-sm border border-outline-variant/30 flex flex-col gap-space-xs">
                <div className="flex items-center gap-space-xs text-secondary">
                  <span className="material-symbols-outlined text-[20px]">wb_sunny</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">Weather Outlook</span>
                </div>
                <h4 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                  14°C – 22°C Climate
                </h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Crisp seasonal walking climate, dry morning temple strolls.
                </p>
              </div>
            </div>
          </section>

          {/* 6. Budget Snapshot & Leeway Breakdown */}
          <section className="p-space-lg lg:p-space-xl rounded-2xl bg-surface-container-low shadow-sm border border-outline-variant/30 flex flex-col gap-space-lg">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md">
              <div className="flex flex-col gap-1">
                <span className="font-label-caption text-label-caption uppercase tracking-wider text-primary font-bold">
                  Financial Feasibility
                </span>
                <h3 className="font-headline-md text-headline-md text-on-surface font-bold">
                  Budget Snapshot & Leeway Breakdown
                </h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Deterministic itemized calculation based on seasonal indices and live currency rates.
                </p>
              </div>

              <div className="inline-flex items-center gap-space-sm px-space-md py-2 rounded-xl bg-surface-container-highest border border-outline-variant/30">
                <span className="material-symbols-outlined text-primary text-[20px]">check_circle</span>
                <div>
                  <div className="font-label-md text-label-md text-on-surface font-bold">
                    {budget_breakdown.variance.status === 'FAVORABLE' ? 'Favorable Alignment' : 'Feasible Target Allocation'}
                  </div>
                  <div className="font-label-caption text-label-caption text-on-surface-variant">
                    {formatInr(budget_breakdown.variance.variance_inr)} buffer against your budget cap
                  </div>
                </div>
              </div>
            </div>

            {/* Comparison Metrics Header */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-gutter p-space-md rounded-xl bg-surface-container border border-outline-variant/20">
              <div>
                <span className="font-label-caption text-label-caption text-on-surface-variant">Target Budget Cap</span>
                <p className="font-headline-md text-headline-md text-on-surface font-bold">
                  {formatInr(budget_breakdown.variance.user_budget_inr)}
                </p>
              </div>
              <div>
                <span className="font-label-caption text-label-caption text-on-surface-variant">Estimated Expedition Total</span>
                <p className="font-headline-md text-headline-md text-primary font-bold">
                  {formatInr(budget_breakdown.total_with_contingency_inr)}
                </p>
              </div>
              <div>
                <span className="font-label-caption text-label-caption text-on-surface-variant">Net Contingency Cushion</span>
                <p className="font-headline-md text-headline-md text-secondary font-bold">
                  +{formatInr(budget_breakdown.contingency_inr)}
                </p>
              </div>
            </div>

            {/* Visual Distribution Multi-Segment Bar */}
            <div className="flex flex-col gap-space-xs">
              <div className="w-full h-3 rounded-full bg-surface-container-highest overflow-hidden flex">
                <div className="bg-primary h-full" style={{ width: '39%' }} title="Stays: 39%" />
                <div className="bg-primary-container h-full" style={{ width: '26%' }} title="Rail & Transit: 26%" />
                <div className="bg-secondary h-full" style={{ width: '14%' }} title="Experiences: 14%" />
                <div className="bg-secondary-container h-full" style={{ width: '13%' }} title="Dining: 13%" />
                <div className="bg-outline h-full" style={{ width: '8%' }} title="Contingency Buffer: 8%" />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-space-sm pt-space-xs">
                <div className="flex items-center gap-1.5 font-label-caption text-label-caption">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary shrink-0" />
                  <span className="text-on-surface font-medium">Stays: {formatInr(budget_breakdown.stays_inr)} (39%)</span>
                </div>
                <div className="flex items-center gap-1.5 font-label-caption text-label-caption">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary-container shrink-0" />
                  <span className="text-on-surface font-medium">Rail/Transit: {formatInr(budget_breakdown.transport_inr)} (26%)</span>
                </div>
                <div className="flex items-center gap-1.5 font-label-caption text-label-caption">
                  <span className="w-2.5 h-2.5 rounded-full bg-secondary shrink-0" />
                  <span className="text-on-surface font-medium">Experiences: {formatInr(budget_breakdown.activities_inr)} (14%)</span>
                </div>
                <div className="flex items-center gap-1.5 font-label-caption text-label-caption">
                  <span className="w-2.5 h-2.5 rounded-full bg-secondary-container shrink-0" />
                  <span className="text-on-surface font-medium">Dining: {formatInr(budget_breakdown.food_inr)} (13%)</span>
                </div>
                <div className="flex items-center gap-1.5 font-label-caption text-label-caption">
                  <span className="w-2.5 h-2.5 rounded-full bg-outline shrink-0" />
                  <span className="text-on-surface font-medium">Contingency: {formatInr(budget_breakdown.contingency_inr)} (8%)</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-space-xs text-on-surface-variant font-label-caption text-label-caption pt-space-xs">
              <span className="material-symbols-outlined text-[16px]">info</span>
              <span>Estimated totals reflect seasonal tariff indexes and currency FX buffers. Final booking rates lock upon checkout.</span>
            </div>
          </section>

          {/* 7. Highlights of the Journey (Visual Gallery Cards) */}
          {experience_plan.highlights && experience_plan.highlights.length > 0 && (
            <section className="flex flex-col gap-space-md">
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-xs">
                <div>
                  <span className="font-label-caption text-label-caption uppercase tracking-wider text-secondary font-bold">
                    Unrepeatable Moments
                  </span>
                  <h2 className="font-headline-md text-headline-md text-on-surface font-bold">
                    Highlights of the Journey
                  </h2>
                </div>
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Handcrafted specifically for your trip pacing
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
                {experience_plan.highlights.map((highlight, hIndex) => (
                  <div
                    key={`highlight-${hIndex}`}
                    className="flex flex-col rounded-2xl bg-surface-container-lowest shadow-sm overflow-hidden group hover:shadow-md transition-all border border-outline-variant/30"
                  >
                    <div className="relative w-full h-52 bg-surface-container overflow-hidden">
                      <img
                        alt={highlight.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        src={highlight.image_url}
                      />
                      <div className="absolute top-space-sm left-space-sm px-space-sm py-1 rounded-full bg-surface/90 backdrop-blur-sm font-label-caption text-label-caption font-semibold text-primary">
                        {highlight.city} • Day {highlight.day}
                      </div>
                    </div>
                    <div className="p-space-lg flex flex-col gap-space-xs">
                      <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                        {highlight.title}
                      </h3>
                      <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                        {highlight.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 8. Weather & Microclimate Context */}
          {weather_context && weather_context.length > 0 && (
            <section className="p-space-md lg:p-space-lg rounded-2xl bg-surface-container shadow-sm border border-outline-variant/30 flex flex-col gap-space-sm">
              <div className="flex flex-wrap items-center justify-between gap-space-xs">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-[20px] text-primary">thermostat</span>
                  <span className="font-label-md text-label-md text-on-surface font-bold">
                    Microclimate & Seasonal Context
                  </span>
                </div>
                <span className="font-label-caption text-label-caption text-on-surface-variant">
                  Static Seasonal Intelligence + 14-day Forecast Calibration
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
                {weather_context.map((wItem) => (
                  <div
                    key={wItem.city}
                    className="flex items-center justify-between p-space-md rounded-xl bg-surface-container-lowest shadow-sm border border-outline-variant/20"
                  >
                    <div className="flex items-center gap-space-sm">
                      <span className="material-symbols-outlined text-[24px] text-primary-container">
                        {wItem.icon}
                      </span>
                      <div>
                        <div className="font-label-md text-label-md text-on-surface font-bold">{wItem.city}</div>
                        <div className="font-label-caption text-label-caption text-on-surface-variant">
                          {wItem.note}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-headline-sm text-headline-sm text-on-surface font-bold">{wItem.temp}</div>
                      <div className="font-label-caption text-label-caption text-primary font-medium">
                        {wItem.condition}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 9. Primary Action Bar & Controls */}
          <section className="p-space-lg lg:p-space-xl rounded-2xl bg-surface-container-high shadow-md border border-outline-variant/30 flex flex-col gap-space-md">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md">
              {/* Primary Call to Action */}
              <button
                type="button"
                onClick={onNavigateItinerary}
                className="inline-flex items-center justify-center gap-space-xs px-space-xl py-space-md rounded-xl bg-primary hover:bg-primary-container text-on-primary font-label-lg text-label-lg transition-all shadow-md group cursor-pointer font-bold"
              >
                <span>View Full Itinerary</span>
                <span className="material-symbols-outlined text-[20px] group-hover:translate-x-1 transition-transform">
                  arrow_forward
                </span>
              </button>

              {/* Secondary Controls */}
              <div className="flex flex-wrap items-center gap-space-sm">
                {onNavigateOptimize && (
                  <button
                    type="button"
                    onClick={onNavigateOptimize}
                    className="inline-flex items-center gap-1.5 px-space-md py-space-sm rounded-xl bg-surface-container-lowest hover:bg-surface text-on-surface font-label-md text-label-md shadow-sm transition-colors border border-outline-variant/30 cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[18px] text-primary">auto_fix_high</span>
                    <span>Optimize Trip</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={onNavigateEditTrip}
                  className="inline-flex items-center gap-1.5 px-space-md py-space-sm rounded-xl bg-surface-container-lowest hover:bg-surface text-on-surface font-label-md text-label-md shadow-sm transition-colors border border-outline-variant/30 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px] text-on-surface-variant">edit</span>
                  <span>Edit Route & Preferences</span>
                </button>

                <button
                  type="button"
                  onClick={handleShare}
                  className="inline-flex items-center gap-1.5 px-space-md py-space-sm rounded-xl bg-surface-container-lowest hover:bg-surface text-on-surface font-label-md text-label-md shadow-sm transition-colors border border-outline-variant/30 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px] text-on-surface-variant">ios_share</span>
                  <span>{shareSuccess ? 'Link Copied!' : 'Export & Share Dossier'}</span>
                </button>
              </div>
            </div>

            {/* Autosave Notice */}
            <div className="flex items-center gap-space-xs font-label-caption text-label-caption text-on-surface-variant">
              <span className="material-symbols-outlined text-[16px] text-primary">cloud_done</span>
              <span>Dossier #{trip_id} is safely synced to your account. You can revisit and customize anytime.</span>
            </div>
          </section>

          {/* 10. Data Source Transparency Legend */}
          <footer className="pt-space-xs pb-space-lg flex flex-wrap items-center justify-center gap-space-sm font-label-caption text-label-caption text-on-surface-variant">
            <span className="px-space-md py-1 rounded-full bg-surface-container-low shadow-sm border border-outline-variant/20">
              [User-Provided: Dates & Budget]
            </span>
            <span className="px-space-md py-1 rounded-full bg-surface-container-low shadow-sm border border-outline-variant/20">
              [Live: Transit Timetables & FX]
            </span>
            <span className="px-space-md py-1 rounded-full bg-surface-container-low shadow-sm border border-outline-variant/20">
              [Estimated: Dining & Local Transfers]
            </span>
            <span className="px-space-md py-1 rounded-full bg-surface-container-low shadow-sm border border-outline-variant/20">
              [Static: Curated Access & Seasonal Trends]
            </span>
          </footer>
        </div>
      </main>

      {/* Global Footer */}
      <footer className="w-full bg-surface-container-low py-space-xl shadow-[0_-1px_6px_rgba(41,37,33,0.02)]">
        <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-gutter mb-space-xl">
            <div className="md:col-span-2 space-y-space-sm">
              <div className="flex items-center gap-space-xs">
                <img
                  alt="Safarnama Logo"
                  className="h-6 w-auto object-contain"
                  src="/safarnama-symbol.svg"
                />
                <span className="font-headline-sm text-headline-sm text-on-surface font-bold">
                  Safarnama
                </span>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant max-w-sm">
                Crafting timeless journeys across the Indian subcontinent and bespoke global circuits. Classical diaries meet thoughtful modern mobility.
              </p>
            </div>
            <div className="space-y-space-sm">
              <h4 className="font-label-lg text-label-lg text-on-surface font-semibold">Curations</h4>
              <ul className="space-y-space-xs font-body-sm text-body-sm text-on-surface-variant">
                <li><a className="hover:text-on-surface transition-colors" href="#">Royal Rajputana Circuit</a></li>
                <li><a className="hover:text-on-surface transition-colors" href="#">Western Ghats Retreats</a></li>
                <li><a className="hover:text-on-surface transition-colors" href="#">Himalayan Waypoints</a></li>
                <li><a className="hover:text-on-surface transition-colors" href="#">Silk Route Transits</a></li>
              </ul>
            </div>
            <div className="space-y-space-sm">
              <h4 className="font-label-lg text-label-lg text-on-surface font-semibold">Concierge & Support</h4>
              <ul className="space-y-space-xs font-body-sm text-body-sm text-on-surface-variant">
                <li><a className="hover:text-on-surface transition-colors" href="#">Travel Advisory & Safety</a></li>
                <li><a className="hover:text-on-surface transition-colors" href="#">Bespoke Customizer</a></li>
                <li><a className="hover:text-on-surface transition-colors" href="#">Heritage Stay Network</a></li>
                <li><a className="hover:text-on-surface transition-colors" href="#">Contact Curator</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-space-md flex flex-col md:flex-row items-center justify-between gap-space-sm font-label-caption text-label-caption text-on-surface-variant border-t border-outline-variant/30">
            <p>© 2025 Safarnama Technologies Private Limited. All rights reserved.</p>
            <div className="flex items-center gap-space-md">
              <a className="hover:text-on-surface transition-colors" href="#">Privacy Policy</a>
              <a className="hover:text-on-surface transition-colors" href="#">Terms of Service</a>
              <a className="hover:text-on-surface transition-colors" href="#">Safarnama Journal</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
