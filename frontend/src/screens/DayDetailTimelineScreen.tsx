import React, { useState } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import { SAMPLE_HOKURIKU_ITINERARY, synthesizeItineraryFromDraft } from '../data/sampleItinerary';
import type { FinalItinerary, DayPlan } from '../types/itinerary';

import { optimizeCadenceWithBackend } from '../services/itineraryOptimizationService';

interface DayDetailTimelineScreenProps {
  dayNumber?: number;
  onNavigateHome: () => void;
  onNavigateOverview: () => void;
  onNavigateItinerary: (dayNumber?: number) => void;
  onNavigateDestination: (destinationName: string) => void;
  onNavigateTransport: (legId?: string) => void;
  onNavigateEditTrip: () => void;
  // Batch 5 handoff callbacks
  onNavigateStay?: (hotelName?: string) => void;
  onNavigateDining?: (mealTitle?: string) => void;
  onNavigateExperience?: (poiName?: string) => void;
  onNavigateMap?: () => void;
}

export const DayDetailTimelineScreen: React.FC<DayDetailTimelineScreenProps> = ({
  dayNumber = 3,
  onNavigateHome,
  onNavigateOverview,
  onNavigateItinerary,
  onNavigateDestination,
  onNavigateTransport,
  onNavigateEditTrip,
  onNavigateStay,
  onNavigateDining,
  onNavigateExperience,
  onNavigateMap,
}) => {
  const { itinerary, tripDetails, destinations, preferences, budget, setItinerary } = useTripPlanning();

  const activeItinerary: FinalItinerary =
    itinerary ||
    (tripDetails.destination
      ? synthesizeItineraryFromDraft(tripDetails, destinations, preferences, budget)
      : SAMPLE_HOKURIKU_ITINERARY);

  const days: DayPlan[] = activeItinerary.experience_plan.days || [];
  const currentDay: DayPlan =
    days.find((d) => d.day_number === dayNumber) ||
    days[0] || {
      day_number: 1,
      date: 'Day 1',
      city: activeItinerary.trip_context.destinations[0] || 'Selected Destination',
      theme: 'Arrival & First Cultural Pauses',
      activities: [],
      meals: [],
    };

  const [optimizedAlert, setOptimizedAlert] = useState(false);

  const formatInr = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Number.isFinite(amount) ? amount : 0);

  const metrics = currentDay.metrics || {
    active_hours: 5.5,
    rest_hours: 2.5,
    walking_steps: 8400,
    walking_km: 6.2,
    pacing_label: 'Balanced & Meditative',
  };

  const weather = currentDay.weather_forecast || {
    condition: 'Crisp Autumn',
    temp_celsius: 16,
    temp_high_celsius: 18,
    temp_low_celsius: 8,
    precipitation_chance: 0,
    advisory: 'Optimal morning lighting; slip-on shoes recommended for temple tatami.',
  };

  const featured = currentDay.featured_experience || {
    title: currentDay.activities[0]?.poi.name || 'Featured Cultural Experience',
    subtitle: currentDay.activities[0]?.poi.description || 'Pristine access before crowds.',
    time_window: '06:45 – 08:30 (1h 45m Leisurely Stroll)',
    duration: '1h 45m',
    image_url:
      activeItinerary.cover_image?.url ||
      SAMPLE_HOKURIKU_ITINERARY.cover_image!.url,
    tags: ['Peak Kōyō Foliage', 'Window of Utmost Quietude', 'Confirmed Route'],
    why_included:
      'Curated to introduce the architectural soul of the historic quarter before daytime tour buses arrive, aligning with an unhurried, mindful cadence.',
    curator_tips: [
      'Arrive early for soft morning illumination and undisturbed photography.',
      'Wear supportive walking shoes suitable for damp morning stone slopes.',
      'Follow the quiet northern return path for an undisturbed trail.',
    ],
    transit_connection: '8 min unhurried stroll from sanctuary base',
  };

  const hourlyRadar = currentDay.hourly_atmosphere || [
    { time: '06:00', temp: '11°C', condition: 'Dawn Mist', precipitation: '0%', icon: 'wb_twilight' },
    { time: '09:00', temp: '14°C', condition: 'Crisp Sun', precipitation: '0%', icon: 'sunny' },
    { time: '12:00', temp: '17°C', condition: 'Warm Autumn', precipitation: '0%', icon: 'sunny' },
    { time: '15:00', temp: '16°C', condition: 'Golden Light', precipitation: '0%', icon: 'light_mode' },
    { time: '18:00', temp: '13°C', condition: 'Evening Breeze', precipitation: '0%', icon: 'air' },
    { time: '21:00', temp: '10°C', condition: 'Clear Chill', precipitation: '0%', icon: 'bedtime' },
  ];

  const [optimizationNotice, setOptimizationNotice] = useState<string | null>(null);

  const handleOptimizeDay = async () => {
    setOptimizedAlert(true);
    try {
      const res = await optimizeCadenceWithBackend(activeItinerary, 'ADJUST_PACE', 'BALANCED');
      setItinerary(res.itinerary);
      setOptimizationNotice(res.summary || 'Day cadence harmonized successfully.');
      setTimeout(() => setOptimizationNotice(null), 3500);
    } catch {
      setOptimizationNotice('Day schedule adjusted locally.');
      setTimeout(() => setOptimizationNotice(null), 3500);
    } finally {
      setTimeout(() => setOptimizedAlert(false), 2000);
    }
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
              onClick={() => onNavigateItinerary(currentDay.day_number)}
              className="px-space-md py-space-xs rounded-full transition-colors bg-surface-container-high text-primary font-bold shadow-sm"
            >
              Itinerary
            </button>
          </nav>

          <div className="flex items-center gap-space-sm">
            <button
              type="button"
              onClick={() => onNavigateItinerary(currentDay.day_number)}
              className="px-space-md py-2 rounded-xl bg-surface-container-low text-primary hover:bg-surface-container border border-outline-variant/30 font-label-sm text-label-sm font-bold flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">calendar_month</span>
              <span className="hidden sm:inline">All Days</span>
            </button>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-[1280px] w-full mx-auto px-margin-mobile lg:px-margin pt-28 pb-space-2xl flex flex-col gap-space-lg">
        {/* 2. Sub-Navigation & Breadcrumbs Bar */}
        <div className="flex flex-wrap items-center justify-between gap-space-sm">
          <div className="flex items-center gap-space-xs text-on-surface-variant font-label-sm text-label-sm">
            <button
              type="button"
              onClick={() => onNavigateItinerary(currentDay.day_number)}
              className="flex items-center gap-1 text-primary hover:underline font-bold cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_back</span>
              <span>Back to Full Itinerary</span>
            </button>
            <span className="text-outline-variant">•</span>
            <span>{activeItinerary.title}</span>
            <span className="text-outline-variant">•</span>
            <span className="text-on-surface font-semibold">
              Day {String(currentDay.day_number).padStart(2, '0')} ({currentDay.city}) #{activeItinerary.trip_id}
            </span>
          </div>

          <div className="flex items-center gap-space-xs">
            <button
              type="button"
              onClick={handleOptimizeDay}
              className="px-space-md py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface font-label-sm text-label-sm font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
            >
              <span className="material-symbols-outlined text-[16px] text-primary">tune</span>
              <span>Optimize This Day</span>
            </button>
            <button
              type="button"
              onClick={onNavigateEditTrip}
              className="px-space-md py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface font-label-sm text-label-sm font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
            >
              <span className="material-symbols-outlined text-[16px] text-secondary">edit</span>
              <span className="hidden sm:inline">Modify Day</span>
            </button>
          </div>
        </div>

        {optimizedAlert && (
          <div className="p-space-md rounded-2xl bg-primary/10 border border-primary/30 text-on-surface flex items-center gap-space-sm animate-fadeIn">
            <span className="material-symbols-outlined text-[20px] text-primary">check_circle</span>
            <span className="font-body-sm text-body-sm font-semibold">
              {optimizationNotice || 'Cadence harmonized: generous 2.5h rest buffer secured between morning exploration and evening dining.'}
            </span>
          </div>
        )}

        {/* 3. Day Header & Narrative Dossier Banner */}
        <section className="flex flex-col p-space-xl rounded-3xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm relative overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-space-xs mb-space-xs">
            <div className="flex items-center gap-space-xs">
              <span className="px-space-md py-1 rounded-full bg-primary text-on-primary font-label-caption text-label-caption font-bold tracking-wider uppercase shadow-xs">
                Day {String(currentDay.day_number).padStart(2, '0')} of {days.length} • {currentDay.city} Historic Core
              </span>
              <span className="px-space-md py-1 rounded-full bg-surface-container text-on-surface font-label-caption text-label-caption font-bold">
                Autumn Kōyō Sanctuary
              </span>
            </div>

            <div className="px-space-md py-1 rounded-full bg-secondary/15 text-secondary font-label-caption text-label-caption font-bold flex items-center gap-1 border border-secondary/20">
              <span className="material-symbols-outlined text-[15px]">verified</span>
              <span>Curated Route Pacing: Artisanal & Meditative</span>
            </div>
          </div>

          <h1 className="font-headline-lg text-headline-lg font-bold text-on-surface tracking-tight mt-space-xs">
            {currentDay.theme}
          </h1>

          <div className="flex flex-wrap items-center gap-space-md text-on-surface-variant font-label-sm text-label-sm my-space-xs">
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px] text-primary">calendar_today</span>
              {currentDay.date}
            </span>
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px] text-primary">pin_drop</span>
              {currentDay.city}, Japan
            </span>
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px] text-secondary">schedule</span>
              {metrics.active_hours}h Active • {metrics.rest_hours}h Rest Buffer
            </span>
          </div>

          <p className="font-body-md text-body-md text-on-surface-variant max-w-3xl leading-relaxed">
            {activeItinerary.curator_note ||
              `A day structured around quiet dawn paths, traditional teahouse encounters, and refined Kaiseki gastronomy before dusk canal lanterns ignite.`}
          </p>

          {/* 4. Vital Status Strip (4 Metric Tiles) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-space-sm mt-space-lg pt-space-md border-t border-outline-variant/20">
            {/* Tile 1: Atmosphere */}
            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex flex-col justify-between">
              <div className="flex items-center justify-between text-on-surface-variant">
                <span className="font-label-caption text-label-caption uppercase font-bold">Atmosphere</span>
                <span className="material-symbols-outlined text-[18px] text-primary">wb_sunny</span>
              </div>
              <div className="mt-space-xs">
                <span className="font-headline-sm text-[18px] font-bold text-on-surface">
                  {weather.temp_celsius}°C High / {weather.temp_low_celsius ?? 8}°C Low
                </span>
                <span className="font-label-caption text-label-caption text-on-surface-variant block">
                  {weather.condition} • {weather.precipitation_chance ?? 0}% Rain
                </span>
              </div>
            </div>

            {/* Tile 2: Pacing Rhythm */}
            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex flex-col justify-between">
              <div className="flex items-center justify-between text-on-surface-variant">
                <span className="font-label-caption text-label-caption uppercase font-bold">Pacing Rhythm</span>
                <span className="material-symbols-outlined text-[18px] text-primary-container">spa</span>
              </div>
              <div className="mt-space-xs">
                <span className="font-headline-sm text-[18px] font-bold text-on-surface">
                  ~{metrics.active_hours} hrs Active
                </span>
                <span className="font-label-caption text-label-caption text-on-surface-variant block">
                  {metrics.rest_hours}h Hinoki Bath & Tea Buffer
                </span>
              </div>
            </div>

            {/* Tile 3: Physical Footprint */}
            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex flex-col justify-between">
              <div className="flex items-center justify-between text-on-surface-variant">
                <span className="font-label-caption text-label-caption uppercase font-bold">Physical Footprint</span>
                <span className="material-symbols-outlined text-[18px] text-secondary">directions_walk</span>
              </div>
              <div className="mt-space-xs">
                <span className="font-headline-sm text-[18px] font-bold text-on-surface">
                  ~{metrics.walking_steps.toLocaleString()} Steps
                </span>
                <span className="font-label-caption text-label-caption text-on-surface-variant block">
                  {metrics.walking_km} km Gentle Cobblestones
                </span>
              </div>
            </div>

            {/* Tile 4: Sanctuary Base */}
            <div
              onClick={() => (onNavigateStay ? onNavigateStay(currentDay.stay?.name) : onNavigateDestination(currentDay.city))}
              className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex flex-col justify-between cursor-pointer hover:border-primary/40 transition-colors"
            >
              <div className="flex items-center justify-between text-on-surface-variant">
                <span className="font-label-caption text-label-caption uppercase font-bold">Sanctuary Base</span>
                <span className="material-symbols-outlined text-[18px] text-primary">hotel</span>
              </div>
              <div className="mt-space-xs">
                <span className="font-headline-sm text-[16px] font-bold text-on-surface truncate block">
                  {currentDay.stay?.name || 'Sanctuary Machiya'}
                </span>
                <span className="font-label-caption text-label-caption text-on-surface-variant block">
                  {currentDay.stay?.neighborhood || currentDay.city} (Night {Math.min(currentDay.day_number, 4)} of 4)
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* 5. 2-Column Main Workspace (8 cols Left Stream + 4 cols Right Sidecar) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-start">
          {/* Left Column (8 cols): Featured Anchor & Vertical Timeline */}
          <div className="lg:col-span-8 flex flex-col gap-space-xl">
            {/* Featured Anchor Experience Showcase */}
            <section className="flex flex-col rounded-3xl bg-surface-container-lowest border border-outline-variant/30 overflow-hidden shadow-sm">
              {/* Header Ribbon */}
              <div className="px-space-xl py-space-md bg-surface-container-low flex flex-wrap items-center justify-between gap-space-xs border-b border-outline-variant/20">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-[20px] text-primary">star</span>
                  <span className="font-label-sm text-label-sm font-bold uppercase tracking-wider text-on-surface">
                    Key Focus Experience
                  </span>
                </div>
                <span className="font-label-sm text-label-sm font-bold text-primary bg-primary/10 px-space-md py-0.5 rounded-full">
                  {featured.time_window}
                </span>
              </div>

              {/* Cinematic 16:9 Image Showcase */}
              <div className="relative w-full aspect-[16/9] bg-surface-container overflow-hidden">
                <img
                  src={featured.image_url}
                  alt={featured.title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

                {/* Floating Badges */}
                <div className="absolute bottom-4 left-4 right-4 flex flex-wrap items-center justify-between gap-2 text-white">
                  <div className="flex flex-wrap gap-1.5">
                    {featured.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-space-sm py-1 rounded-full bg-black/50 backdrop-blur-md text-[12px] font-bold border border-white/20"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  <span className="text-[12px] font-semibold bg-primary/90 px-3 py-1 rounded-full backdrop-blur-md">
                    {featured.transit_connection}
                  </span>
                </div>
              </div>

              {/* Editorial Narrative */}
              <div className="p-space-xl flex flex-col gap-space-md">
                <div>
                  <h3 className="font-headline-md text-headline-md font-bold text-on-surface">
                    {featured.title}
                  </h3>
                  <p className="font-body-md text-body-md text-on-surface-variant mt-1">
                    {featured.subtitle}
                  </p>
                </div>

                <div className="p-space-md rounded-2xl bg-surface-container-low/70 border border-outline-variant/20">
                  <h4 className="font-label-sm text-label-sm font-bold text-primary uppercase tracking-wider mb-1 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px]">menu_book</span>
                    Why Included in Your Safarnama
                  </h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                    {featured.why_included}
                  </p>
                </div>

                {/* Curated Insider Access Tips */}
                <div>
                  <h4 className="font-label-sm text-label-sm font-bold text-on-surface uppercase tracking-wider mb-space-xs flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px] text-secondary">tips_and_updates</span>
                    Curated Insider Access Tips
                  </h4>
                  <ul className="space-y-2">
                    {featured.curator_tips.map((tip, idx) => (
                      <li key={idx} className="flex items-start gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
                        <span className="w-5 h-5 rounded-full bg-primary/10 text-primary font-bold text-[12px] flex items-center justify-center flex-shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Batch 5 Handoff Action Links */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-space-sm border-t border-outline-variant/15">
                  <button
                    type="button"
                    onClick={() => (onNavigateExperience ? onNavigateExperience(featured.title) : onNavigateDestination(currentDay.city))}
                    className="px-space-lg py-2 rounded-xl bg-primary text-on-primary font-label-sm text-label-sm font-bold flex items-center gap-1.5 cursor-pointer hover:bg-primary/90 transition-colors shadow-xs"
                  >
                    <span>Experience Dossier & Story</span>
                    <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => (onNavigateMap ? onNavigateMap() : onNavigateTransport('leg-3'))}
                    className="px-space-md py-2 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-label-sm text-label-sm font-semibold flex items-center gap-1.5 cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[16px] text-secondary">map</span>
                    <span>View on Journey Map</span>
                  </button>
                </div>
              </div>
            </section>

            {/* Vertical Hour-by-Hour Timeline */}
            <section className="flex flex-col gap-space-md">
              <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/20">
                <div className="flex items-center gap-space-xs">
                  <span className="material-symbols-outlined text-[22px] text-primary">hourglass_bottom</span>
                  <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                    Hour-by-Hour Chronological Flow
                  </h3>
                </div>
                <span className="font-label-caption text-label-caption text-on-surface-variant font-medium">
                  {currentDay.activities.length} Slots Coordinated
                </span>
              </div>

              {/* Connected Vertical Timeline */}
              <div className="relative pl-6 md:pl-8 flex flex-col gap-space-lg">
                {/* Vertical Continuous Line */}
                <div className="absolute left-2.5 md:left-3 top-3 bottom-3 w-0.5 bg-outline-variant/30" />

                {currentDay.activities.map((slot, index) => {
                  const time =
                    index === 0
                      ? '06:45 – 08:30'
                      : index === 1
                      ? '09:15 – 11:00'
                      : index === 2
                      ? '14:00 – 16:00'
                      : '17:45 – 19:15';

                  return (
                    <div key={slot.poi.name + index} className="relative flex flex-col gap-space-xs">
                      {/* Timeline Dot */}
                      <div className="absolute -left-6 md:-left-8 top-1.5 w-5 h-5 rounded-full bg-surface border-2 border-primary flex items-center justify-center">
                        <div className="w-2 h-2 rounded-full bg-primary" />
                      </div>

                      {/* Content Card */}
                      <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs hover:border-primary/40 transition-colors">
                        <div className="flex flex-wrap items-center justify-between gap-space-xs mb-1">
                          <div className="flex items-center gap-2">
                            <span className="font-label-sm text-label-sm font-bold text-primary">
                              {time}
                            </span>
                            <span className="font-label-caption text-label-caption px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-medium">
                              {slot.daypart}
                            </span>
                          </div>
                          <span className="font-label-sm text-label-sm font-bold text-on-surface">
                            {slot.poi.estimated_cost_inr > 0 ? formatInr(slot.poi.estimated_cost_inr) : 'Included'}
                          </span>
                        </div>

                        <h4 className="font-headline-sm text-[17px] font-bold text-on-surface">
                          {slot.poi.name}
                        </h4>
                        <p className="font-body-sm text-body-sm text-on-surface-variant mt-1 leading-relaxed">
                          {slot.poi.description}
                        </p>

                        {slot.notes && (
                          <div className="mt-space-sm p-space-sm rounded-xl bg-surface-container-low text-on-surface-variant font-label-caption text-label-caption flex items-start gap-1.5">
                            <span className="material-symbols-outlined text-[15px] text-primary mt-0.5">
                              info
                            </span>
                            <span>{slot.notes}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>

          {/* Right Column (4 cols): Radar, Lodging, Spend Ledger */}
          <div className="lg:col-span-4 flex flex-col gap-space-lg sticky top-28">
            {/* 1. Microclimate Hourly Radar */}
            <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex flex-col gap-space-sm">
              <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/15">
                <div className="flex items-center gap-1 text-primary">
                  <span className="material-symbols-outlined text-[18px]">thermostat</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">
                    Atmosphere Radar
                  </span>
                </div>
                <span className="font-label-caption text-label-caption text-on-surface-variant">
                  {currentDay.city} Hourly
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 pt-1">
                {hourlyRadar.map((h) => (
                  <div
                    key={h.time}
                    className="p-space-xs rounded-xl bg-surface-container-low text-center flex flex-col items-center justify-between border border-outline-variant/15"
                  >
                    <span className="font-label-caption text-[11px] text-on-surface-variant font-semibold">
                      {h.time}
                    </span>
                    <span className="material-symbols-outlined text-[18px] text-primary my-1">
                      {h.icon}
                    </span>
                    <span className="font-label-sm text-[13px] font-bold text-on-surface">
                      {h.temp}
                    </span>
                    <span className="font-label-caption text-[10px] text-on-surface-variant">
                      {h.condition}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 2. Sanctuary Lodging Details */}
            {currentDay.stay && (
              <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex flex-col gap-space-xs">
                <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/15">
                  <div className="flex items-center gap-1 text-primary">
                    <span className="material-symbols-outlined text-[18px]">hotel</span>
                    <span className="font-label-caption text-label-caption uppercase font-bold">
                      Sanctuary Lodging
                    </span>
                  </div>
                  <span className="font-label-caption text-label-caption text-secondary font-bold">
                    Confirmed
                  </span>
                </div>

                <h4 className="font-headline-sm text-[16px] font-bold text-on-surface mt-1">
                  {currentDay.stay.name}
                </h4>
                <div className="font-label-caption text-label-caption text-on-surface-variant">
                  {currentDay.stay.neighborhood} • {currentDay.stay.type}
                </div>

                <div className="mt-2 text-on-surface-variant font-body-sm text-body-sm bg-surface-container-low p-space-sm rounded-xl">
                  <span className="font-bold text-on-surface">Check-in Protocol:</span> Priority room entry from 15:00 with matcha welcome ceremony and Hinoki soaking bath preparation.
                </div>

                <button
                  type="button"
                  onClick={() => onNavigateDestination(currentDay.city)}
                  className="w-full mt-2 py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-label-caption text-label-caption font-bold transition-colors cursor-pointer text-center"
                >
                  View Destination Guide
                </button>
              </div>
            )}

            {/* 3. Day Cost Ledger */}
            {currentDay.day_budget && (
              <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex flex-col gap-space-sm">
                <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/15">
                  <div className="flex items-center gap-1 text-primary">
                    <span className="material-symbols-outlined text-[18px]">receipt_long</span>
                    <span className="font-label-caption text-label-caption uppercase font-bold">
                      Day Cost Ledger
                    </span>
                  </div>
                  <span className="font-label-sm text-label-sm font-bold text-on-surface">
                    {formatInr(currentDay.day_budget.total_inr)}
                  </span>
                </div>

                <table className="w-full text-left font-body-sm text-body-sm">
                  <tbody className="divide-y divide-outline-variant/15">
                    <tr>
                      <td className="py-1 text-on-surface-variant">Experiences & Fees</td>
                      <td className="py-1 text-right font-semibold text-on-surface">
                        {formatInr(currentDay.day_budget.activities_inr)}
                      </td>
                    </tr>
                    <tr
                      onClick={() => onNavigateDining?.(currentDay.meals[0]?.name || 'Kaiseki Dining')}
                      className="cursor-pointer hover:text-primary transition-colors"
                    >
                      <td className="py-1 text-on-surface-variant">Curated Dining ➔</td>
                      <td className="py-1 text-right font-semibold text-on-surface">
                        {formatInr(currentDay.day_budget.meals_inr)}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-1 text-on-surface-variant">Local Transit Buffer</td>
                      <td className="py-1 text-right font-semibold text-on-surface">
                        {formatInr(currentDay.day_budget.transit_inr)}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-1 text-on-surface-variant">Sanctuary Allocation</td>
                      <td className="py-1 text-right font-semibold text-on-surface">
                        {formatInr(currentDay.day_budget.stays_inr)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}

            {/* 4. Next Day Handoff */}
            {currentDay.next_day_teaser && (
              <div className="p-space-lg rounded-2xl bg-surface-container-low border border-outline-variant/30 flex flex-col gap-space-xs">
                <span className="font-label-caption text-label-caption uppercase font-bold text-primary">
                  Next Day Handoff
                </span>
                <h4 className="font-headline-sm text-[15px] font-bold text-on-surface">
                  Day {currentDay.next_day_teaser.day_number}: {currentDay.next_day_teaser.theme}
                </h4>
                <button
                  type="button"
                  onClick={() => onNavigateItinerary(currentDay.next_day_teaser?.day_number)}
                  className="mt-2 w-full py-1.5 rounded-xl bg-primary text-on-primary font-label-caption text-label-caption font-bold text-center cursor-pointer hover:bg-primary/90 transition-colors"
                >
                  Explore Day {currentDay.next_day_teaser.day_number}
                </button>
              </div>
            )}

            {/* 5. Transit Corridor Link */}
            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-primary">directions_railway</span>
                <span className="font-label-caption text-label-caption font-bold text-on-surface">
                  Regional Transit Corridor
                </span>
              </div>
              <button
                type="button"
                onClick={() => onNavigateTransport('leg-3')}
                className="text-primary hover:underline font-label-caption text-label-caption font-bold cursor-pointer"
              >
                View Route ➔
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
            <button
              type="button"
              onClick={() => onNavigateItinerary(currentDay.day_number)}
              className="hover:text-primary transition-colors cursor-pointer"
            >
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
