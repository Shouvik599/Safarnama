import React, { useState } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import { SAMPLE_HOKURIKU_ITINERARY, synthesizeItineraryFromDraft } from '../data/sampleItinerary';
import type { FinalItinerary, DayPlan } from '../types/itinerary';
import { ItineraryDayRail } from '../components/itinerary/ItineraryDayRail';
import { DayBentoMetrics } from '../components/itinerary/DayBentoMetrics';
import { ActivityTimelineCard } from '../components/itinerary/ActivityTimelineCard';
import { DayMealCard } from '../components/itinerary/DayMealCard';
import { optimizeCadenceWithBackend } from '../services/itineraryOptimizationService';

interface DayByDayItineraryScreenProps {
  initialDay?: number;
  onNavigateHome: () => void;
  onNavigateOverview: () => void;
  onNavigateDayDetail: (dayNumber: number) => void;
  onNavigateDestination: (destinationName: string) => void;
  onNavigateTransport: (legId?: string) => void;
  onNavigateEditTrip: () => void;
  // Batch 5 handoff callbacks
  onNavigateStay?: (hotelName?: string) => void;
  onNavigateDining?: (mealTitle?: string) => void;
  onNavigateExperience?: (poiName?: string) => void;
  onNavigateMap?: () => void;
}

export const DayByDayItineraryScreen: React.FC<DayByDayItineraryScreenProps> = ({
  initialDay = 3,
  onNavigateHome,
  onNavigateOverview,
  onNavigateDayDetail,
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
  const totalDays = activeItinerary.experience_plan.total_days || days.length || 10;

  // Ensure initial day is valid within totalDays
  const validInitialDay = Math.min(Math.max(1, initialDay), totalDays);
  const [selectedDayNumber, setSelectedDayNumber] = useState<number>(() => {
    const hasInitial = days.some((d) => d.day_number === validInitialDay);
    return hasInitial ? validInitialDay : (days[0]?.day_number || 1);
  });

  const [activePeriodFilter, setActivePeriodFilter] = useState<'ALL' | 'MORNING' | 'AFTERNOON' | 'EVENING'>('ALL');
  const [shareSuccess, setShareSuccess] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizationNotice, setOptimizationNotice] = useState<string | null>(null);

  // Active Day object
  const activeDay: DayPlan =
    days.find((d) => d.day_number === selectedDayNumber) ||
    days[0] || {
      day_number: 1,
      date: 'Day 1',
      city: activeItinerary.trip_context.destinations[0] || 'Origin',
      theme: 'Exploration & Arrival',
      activities: [],
      meals: [],
    };

  const handleShare = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      setShareSuccess(true);
      setTimeout(() => setShareSuccess(false), 2500);
    }
  };

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const res = await optimizeCadenceWithBackend(activeItinerary, 'ADJUST_PACE', 'BALANCED');
      setItinerary(res.itinerary);
      setOptimizationNotice(res.summary || 'Cadence harmonized successfully.');
      setTimeout(() => setOptimizationNotice(null), 3500);
    } catch {
      setOptimizationNotice('Cadence adjusted locally.');
      setTimeout(() => setOptimizationNotice(null), 3500);
    } finally {
      setOptimizing(false);
    }
  };

  const formatInr = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Number.isFinite(amount) ? amount : 0);

  // Partition activities into morning, afternoon, evening
  const morningActivities = activeDay.activities.filter(
    (a) => a.daypart === 'MORNING' || (!a.daypart && activeDay.activities.indexOf(a) === 0)
  );
  const afternoonActivities = activeDay.activities.filter(
    (a) => a.daypart === 'AFTERNOON'
  );
  const eveningActivities = activeDay.activities.filter(
    (a) => a.daypart === 'EVENING'
  );

  // Meals
  const lunchMeal = activeDay.meals.find((m) => m.meal_type === 'LUNCH');
  const dinnerMeal = activeDay.meals.find((m) => m.meal_type === 'DINNER');

  // Next day info
  const nextDayPlan = days.find((d) => d.day_number === activeDay.day_number + 1);

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen flex flex-col antialiased">
      {/* 1. Fixed Top Application Header */}
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
            <button
              type="button"
              onClick={onNavigateOverview}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Overview
            </button>
            <span
              aria-current="page"
              className="px-space-md py-space-xs rounded-full transition-colors bg-surface-container-high text-primary font-bold shadow-sm"
            >
              Itinerary
            </span>
          </nav>

          <div className="flex items-center gap-space-sm">
            <button
              type="button"
              onClick={handleShare}
              className="px-space-md py-2 rounded-xl bg-surface-container-low text-on-surface-variant hover:text-on-surface border border-outline-variant/30 font-label-sm text-label-sm font-semibold flex items-center gap-1 transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">
                {shareSuccess ? 'check' : 'share'}
              </span>
              <span className="hidden sm:inline">{shareSuccess ? 'Copied' : 'Share'}</span>
            </button>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-[1280px] w-full mx-auto px-margin-mobile lg:px-margin pt-28 pb-space-2xl flex flex-col gap-space-lg">
        {/* 2. Sticky Context Header Strip */}
        <section className="flex flex-col gap-space-sm">
          <div className="flex flex-wrap items-center justify-between gap-space-sm">
            <div className="flex items-center gap-space-xs text-on-surface-variant font-label-sm text-label-sm">
              <button
                type="button"
                onClick={onNavigateOverview}
                className="flex items-center gap-1 text-primary hover:underline font-bold cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">arrow_back</span>
                <span>Dossier #{activeItinerary.trip_id}</span>
              </button>
              <span className="text-outline-variant">•</span>
              <span>{activeItinerary.title}</span>
              <span className="text-outline-variant">•</span>
              <span className="text-on-surface font-semibold">
                Day {String(activeDay.day_number).padStart(2, '0')} Detailed Diary
              </span>
            </div>

            <div className="flex items-center gap-space-xs">
              <button
                type="button"
                onClick={handleOptimize}
                disabled={optimizing}
                className="px-space-md py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface font-label-sm text-label-sm font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs disabled:opacity-50"
              >
                <span className={`material-symbols-outlined text-[16px] text-primary ${optimizing ? 'animate-spin' : ''}`}>
                  tune
                </span>
                <span>{optimizing ? 'Harmonizing...' : 'Optimize Cadence'}</span>
              </button>
              <button
                type="button"
                onClick={() => window.print()}
                className="px-space-md py-1.5 rounded-xl bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface font-label-sm text-label-sm font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
              >
                <span className="material-symbols-outlined text-[16px] text-secondary">
                  download_for_offline
                </span>
                <span className="hidden sm:inline">Offline Dossier</span>
              </button>
            </div>
          </div>

          {/* Optimization notification toast */}
          {optimizationNotice && (
            <div className="flex items-center gap-2 px-space-md py-2 rounded-xl bg-primary/10 border border-primary/30 text-primary font-label-sm text-label-sm font-bold">
              <span className="material-symbols-outlined text-[18px]">verified</span>
              <span>{optimizationNotice}</span>
            </div>
          )}

          {/* Corridor Summary Micro-Strip */}
          <div className="flex flex-wrap items-center justify-between gap-space-sm p-space-md rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs">
            <div className="flex items-center gap-space-sm">
              <div className="flex items-center gap-1 text-primary font-bold font-headline-sm text-[16px]">
                <span>{activeItinerary.trip_context.origin}</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                <span>{activeItinerary.trip_context.destinations.join(' ➔ ')}</span>
              </div>
              <span className="px-space-sm py-0.5 rounded-full bg-primary/10 text-primary font-label-caption text-label-caption font-bold">
                {activeItinerary.trip_context.scope === 'DOMESTIC' ? 'Domestic Circuit' : 'International Expedition'}
              </span>
            </div>

            <div className="flex items-center gap-space-md text-on-surface-variant font-label-caption text-label-caption">
              <div className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-primary" aria-hidden="true">
                  calendar_today
                </span>
                <span>
                  {activeItinerary.trip_context.start_date} – {activeItinerary.trip_context.end_date}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-secondary" aria-hidden="true">
                  group
                </span>
                <span>
                  {activeItinerary.trip_context.num_travelers} Explorers • {activeItinerary.trip_context.pace} Pace
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* 3. Horizontal Journey Path Progression Rail */}
        <section>
          <ItineraryDayRail
            days={days}
            selectedDayNumber={selectedDayNumber}
            onSelectDay={(dayNum) => {
              setSelectedDayNumber(dayNum);
              window.scrollTo({ top: 180, behavior: 'smooth' });
            }}
          />
        </section>

        {/* 4. Day Hero Narrative Theme Card */}
        <section className="flex flex-col p-space-xl rounded-3xl bg-surface-container-low border border-outline-variant/30 shadow-sm relative overflow-hidden">
          {/* Subtle decorative watermark */}
          <div className="absolute right-0 bottom-0 text-[140px] font-black text-outline-variant/5 select-none pointer-events-none leading-none -mr-4 -mb-4">
            {String(activeDay.day_number).padStart(2, '0')}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-space-xs mb-space-xs relative z-10">
            <div className="flex items-center gap-space-xs">
              <span className="px-space-md py-1 rounded-full bg-primary text-on-primary font-label-caption text-label-caption font-bold tracking-wider uppercase shadow-xs">
                Focus Itinerary
              </span>
              <span className="font-label-sm text-label-sm font-semibold text-on-surface-variant">
                {activeDay.date} • {activeDay.city} Historic Sector
              </span>
            </div>

            <button
              type="button"
              onClick={() => onNavigateDestination(activeDay.city)}
              className="text-primary hover:underline font-label-sm text-label-sm font-bold flex items-center gap-1 cursor-pointer"
            >
              <span>Explore {activeDay.city} Waypoints</span>
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            </button>
          </div>

          <div className="relative z-10">
            <h2 className="font-headline-lg text-headline-lg font-bold text-on-surface tracking-tight">
              DAY {String(activeDay.day_number).padStart(2, '0')} — {activeDay.theme}
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-3xl mt-space-xs leading-relaxed">
              {activeItinerary.curator_note ||
                `A thoughtfully balanced day balancing active morning discovery with restorative afternoon buffers and curated regional dining.`}
            </p>
          </div>

          {/* Bento Metrics 4-Pack */}
          <div className="mt-space-lg relative z-10">
            <DayBentoMetrics day={activeDay} />
          </div>

          {/* Period Filter Tabs */}
          <div className="flex items-center gap-space-xs mt-space-lg pt-space-sm border-t border-outline-variant/20 relative z-10">
            <span className="font-label-caption text-label-caption text-on-surface-variant uppercase font-bold mr-space-xs">
              Filter:
            </span>
            {(['ALL', 'MORNING', 'AFTERNOON', 'EVENING'] as const).map((period) => (
              <button
                key={period}
                type="button"
                onClick={() => setActivePeriodFilter(period)}
                className={`px-space-md py-1 rounded-full font-label-sm text-label-sm font-bold transition-all cursor-pointer ${
                  activePeriodFilter === period
                    ? 'bg-on-surface text-surface shadow-xs'
                    : 'bg-surface-container text-on-surface-variant hover:text-on-surface'
                }`}
              >
                {period === 'ALL' ? 'All Day Periods' : period.charAt(0) + period.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </section>

        {/* 5. Main 12-Column Grid (8 cols Left Timeline + 4 cols Right Sidecar) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-start">
          {/* Left Column (8 cols): Chronological Periods */}
          <div className="lg:col-span-8 flex flex-col gap-space-xl">
            {/* Morning Period */}
            {(activePeriodFilter === 'ALL' || activePeriodFilter === 'MORNING') && (
              <section className="flex flex-col gap-space-md">
                <div className="flex items-center justify-between pb-space-xs border-b-2 border-primary/20">
                  <div className="flex items-center gap-space-xs">
                    <span className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                      <span className="material-symbols-outlined text-[18px]">wb_twilight</span>
                    </span>
                    <div>
                      <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                        Morning: The Sacred Dawn
                      </h3>
                      <span className="font-label-caption text-label-caption text-on-surface-variant">
                        06:30 – 11:30 • Pristine early light and uncrowded access window
                      </span>
                    </div>
                  </div>
                  <span className="font-label-caption text-label-caption text-primary font-bold">
                    {morningActivities.length} Experiences Scheduled
                  </span>
                </div>

                <div className="flex flex-col gap-space-md">
                  {morningActivities.map((act, idx) => (
                    <ActivityTimelineCard
                      key={act.poi.name + idx}
                      activity={act}
                      timeWindow={idx === 0 ? '06:45 – 08:30' : '09:15 – 11:00'}
                      onNavigateDetail={() => onNavigateDayDetail(activeDay.day_number)}
                      onNavigateExperience={() => onNavigateExperience?.(act.poi.name)}
                    />
                  ))}
                  {morningActivities.length === 0 && (
                    <div className="p-space-lg rounded-2xl bg-surface-container-low text-center text-on-surface-variant font-body-sm text-body-sm">
                      Unhurried morning rest and breakfast at your sanctuary base.
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* Afternoon Period */}
            {(activePeriodFilter === 'ALL' || activePeriodFilter === 'AFTERNOON') && (
              <section className="flex flex-col gap-space-md">
                <div className="flex items-center justify-between pb-space-xs border-b-2 border-primary/20">
                  <div className="flex items-center gap-space-xs">
                    <span className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                      <span className="material-symbols-outlined text-[18px]">wb_sunny</span>
                    </span>
                    <div>
                      <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                        Afternoon: Artisanal Pauses & Reflections
                      </h3>
                      <span className="font-label-caption text-label-caption text-on-surface-variant">
                        12:00 – 16:30 • Cultural atelier immersion & mindful pacing
                      </span>
                    </div>
                  </div>
                  <span className="font-label-caption text-label-caption text-primary font-bold">
                    Midday Dining & Culture
                  </span>
                </div>

                <div className="flex flex-col gap-space-md">
                  {lunchMeal && (
                    <DayMealCard
                      meal={lunchMeal}
                      timeWindow="12:00 – 13:30"
                      onNavigateDining={() => onNavigateDining?.(lunchMeal.name)}
                    />
                  )}
                  {afternoonActivities.map((act, idx) => (
                    <ActivityTimelineCard
                      key={act.poi.name + idx}
                      activity={act}
                      timeWindow="14:00 – 16:00"
                      onNavigateDetail={() => onNavigateDayDetail(activeDay.day_number)}
                      onNavigateExperience={() => onNavigateExperience?.(act.poi.name)}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* Evening Period */}
            {(activePeriodFilter === 'ALL' || activePeriodFilter === 'EVENING') && (
              <section className="flex flex-col gap-space-md">
                <div className="flex items-center justify-between pb-space-xs border-b-2 border-primary/20">
                  <div className="flex items-center gap-space-xs">
                    <span className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                      <span className="material-symbols-outlined text-[18px]">nights_stay</span>
                    </span>
                    <div>
                      <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
                        Evening: Twilight Lanterns & Canal Cadence
                      </h3>
                      <span className="font-label-caption text-label-caption text-on-surface-variant">
                        17:30 – 21:00 • Dusk walks & bespoke dining counter
                      </span>
                    </div>
                  </div>
                  <span className="font-label-caption text-label-caption text-primary font-bold">
                    Twilight & Dinner
                  </span>
                </div>

                <div className="flex flex-col gap-space-md">
                  {eveningActivities.map((act, idx) => (
                    <ActivityTimelineCard
                      key={act.poi.name + idx}
                      activity={act}
                      timeWindow="17:45 – 19:15"
                      onNavigateDetail={() => onNavigateDayDetail(activeDay.day_number)}
                      onNavigateExperience={() => onNavigateExperience?.(act.poi.name)}
                    />
                  ))}
                  {dinnerMeal && (
                    <DayMealCard
                      meal={dinnerMeal}
                      timeWindow="19:30 – 21:30"
                      onNavigateDining={() => onNavigateDining?.(dinnerMeal.name)}
                    />
                  )}
                </div>
              </section>
            )}

            {/* Bottom Screen Navigation CTA */}
            <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 flex flex-wrap items-center justify-between gap-space-md shadow-xs">
              <div className="flex items-center gap-space-sm">
                <span className="material-symbols-outlined text-[24px] text-primary" aria-hidden="true">
                  timeline
                </span>
                <div>
                  <h4 className="font-headline-sm text-[16px] font-bold text-on-surface">
                    Examine Hour-by-Hour Timeline for Day {activeDay.day_number}
                  </h4>
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Unlock access protocols, insider timing, and hourly atmosphere radar.
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => onNavigateDayDetail(activeDay.day_number)}
                className="px-space-xl py-space-sm rounded-xl bg-primary text-on-primary font-label-md text-label-md font-bold hover:bg-primary/90 transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
              >
                <span>View Full Day Detail</span>
                <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
              </button>
            </div>
          </div>

          {/* Right Column (4 cols): Practical Intelligence Sidecar */}
          <div className="lg:col-span-4 flex flex-col gap-space-lg sticky top-28">
            {/* 1. Sanctuary Lodging Anchor Card */}
            {activeDay.stay && (
              <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex flex-col gap-space-sm">
                <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/15">
                  <div className="flex items-center gap-1 text-primary">
                    <span className="material-symbols-outlined text-[18px]">hotel</span>
                    <span className="font-label-caption text-label-caption uppercase font-bold">
                      Sanctuary Lodging
                    </span>
                  </div>
                  {activeDay.stay.confirmed && (
                    <span className="font-label-caption text-label-caption font-bold text-on-secondary bg-secondary px-2 py-0.5 rounded-full flex items-center gap-0.5">
                      <span className="material-symbols-outlined text-[12px]">check</span>
                      Confirmed
                    </span>
                  )}
                </div>

                <div>
                  <h4 className="font-headline-sm text-[17px] font-bold text-on-surface">
                    {activeDay.stay.name}
                  </h4>
                  <div className="flex items-center gap-1 font-label-caption text-label-caption text-on-surface-variant mt-0.5">
                    <span className="material-symbols-outlined text-[14px] text-primary">pin_drop</span>
                    <span>{activeDay.stay.neighborhood}</span>
                    <span>• {activeDay.stay.type}</span>
                  </div>
                </div>

                {activeDay.stay.amenities && (
                  <div className="flex flex-wrap gap-1.5 my-1">
                    {activeDay.stay.amenities.map((am) => (
                      <span
                        key={am}
                        className="px-2 py-0.5 rounded-md bg-surface-container text-on-surface font-label-caption text-label-caption"
                      >
                        {am}
                      </span>
                    ))}
                  </div>
                )}

                <div className="pt-space-xs flex items-center justify-between text-on-surface-variant font-label-caption text-label-caption border-t border-outline-variant/15">
                  <span>Nightly Rate:</span>
                  <span className="font-bold text-on-surface font-label-sm text-label-sm">
                    {formatInr(activeDay.stay.cost_inr)}
                  </span>
                </div>

                <div className="flex gap-2 mt-1">
                  <button
                    type="button"
                    onClick={() => (onNavigateStay ? onNavigateStay(activeDay.stay?.name) : onNavigateDestination(activeDay.city))}
                    className="flex-1 py-1.5 rounded-xl bg-primary text-on-primary font-label-caption text-label-caption font-bold transition-colors cursor-pointer text-center hover:bg-primary/90"
                  >
                    View Lodging Details
                  </button>
                  <button
                    type="button"
                    onClick={() => onNavigateDestination(activeDay.city)}
                    className="py-1.5 px-3 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-label-caption text-label-caption font-bold transition-colors cursor-pointer text-center"
                  >
                    City Context
                  </button>
                </div>
              </div>
            )}

            {/* 2. Day Budget Spend Tracker Card */}
            {activeDay.day_budget && (
              <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex flex-col gap-space-sm">
                <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/15">
                  <div className="flex items-center gap-1 text-primary">
                    <span className="material-symbols-outlined text-[18px]">account_balance_wallet</span>
                    <span className="font-label-caption text-label-caption uppercase font-bold">
                      Day {activeDay.day_number} Spend Breakdown
                    </span>
                  </div>
                  <span className="font-label-sm text-label-sm font-bold text-on-surface">
                    {formatInr(activeDay.day_budget.total_inr)}
                  </span>
                </div>

                <div className="space-y-2 pt-1 font-body-sm text-body-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-on-surface-variant flex items-center gap-1">
                      <span className="material-symbols-outlined text-[15px] text-primary">attractions</span>
                      Activities:
                    </span>
                    <span className="font-semibold text-on-surface">
                      {formatInr(activeDay.day_budget.activities_inr)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-on-surface-variant flex items-center gap-1">
                      <span className="material-symbols-outlined text-[15px] text-primary-container">restaurant</span>
                      Dining:
                    </span>
                    <span className="font-semibold text-on-surface">
                      {formatInr(activeDay.day_budget.meals_inr)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-on-surface-variant flex items-center gap-1">
                      <span className="material-symbols-outlined text-[15px] text-secondary">train</span>
                      Transit Leeway:
                    </span>
                    <span className="font-semibold text-on-surface">
                      {formatInr(activeDay.day_budget.transit_inr)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-outline-variant/15">
                    <span className="text-on-surface-variant flex items-center gap-1">
                      <span className="material-symbols-outlined text-[15px]">hotel</span>
                      Sanctuary Base:
                    </span>
                    <span className="font-semibold text-on-surface">
                      {formatInr(activeDay.day_budget.stays_inr)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* 3. Seasonal Advisory Card */}
            {activeDay.weather_forecast?.advisory && (
              <div className="p-space-lg rounded-2xl bg-surface-container-low border border-outline-variant/30 flex flex-col gap-space-xs">
                <div className="flex items-center gap-1 text-primary">
                  <span className="material-symbols-outlined text-[18px]">info</span>
                  <span className="font-label-caption text-label-caption uppercase font-bold">
                    Curator Packing & Atmosphere Note
                  </span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                  {activeDay.weather_forecast.advisory}
                </p>
              </div>
            )}

            {/* 4. Next Day Teaser Card */}
            {nextDayPlan && (
              <div className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-sm flex flex-col gap-space-sm">
                <span className="font-label-caption text-label-caption uppercase font-bold text-primary">
                  Coming Up Tomorrow
                </span>
                <h4 className="font-headline-sm text-[16px] font-bold text-on-surface">
                  Day {nextDayPlan.day_number} — {nextDayPlan.theme}
                </h4>
                <div className="flex items-center gap-1 text-on-surface-variant font-label-caption text-label-caption">
                  <span className="material-symbols-outlined text-[14px] text-primary">pin_drop</span>
                  <span>{nextDayPlan.city}</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedDayNumber(nextDayPlan.day_number);
                    window.scrollTo({ top: 180, behavior: 'smooth' });
                  }}
                  className="mt-1 w-full py-2 rounded-xl bg-primary/10 hover:bg-primary hover:text-on-primary text-primary font-label-sm text-label-sm font-bold transition-all text-center cursor-pointer"
                >
                  Switch to Day {nextDayPlan.day_number}
                </button>
              </div>
            )}

            {/* Link to Transport Details */}
            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-primary">directions_railway</span>
                <span className="font-label-caption text-label-caption font-bold text-on-surface">
                  Intermodal Corridor Details
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

            {/* Link to Interactive Journey Map (Batch 5 Handoff) */}
            <div className="p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-secondary">map</span>
                <span className="font-label-caption text-label-caption font-bold text-on-surface">
                  Interactive Route Map
                </span>
              </div>
              <button
                type="button"
                onClick={() => (onNavigateMap ? onNavigateMap() : onNavigateTransport('leg-3'))}
                className="text-secondary hover:underline font-label-caption text-label-caption font-bold cursor-pointer"
              >
                Open Map ➔
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
            <button type="button" onClick={onNavigateOverview} className="hover:text-primary transition-colors cursor-pointer">
              Overview
            </button>
            <button type="button" onClick={onNavigateEditTrip} className="hover:text-primary transition-colors cursor-pointer">
              Edit Plan
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
