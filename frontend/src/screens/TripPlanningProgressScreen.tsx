import React, { useEffect, useState, useRef } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import { startPlanningStream } from '../services/planningStreamService';
import { buildPlanRequestDraft } from '../data/planRequest';
import type { FinalItinerary, PlanningEvent } from '../types/itinerary';

interface TripPlanningProgressScreenProps {
  onNavigateReview: () => void;
  onNavigateOverview: () => void;
}

interface TimelineStage {
  id: string;
  name: string;
  backendStage: string;
  defaultDescription: string;
  estimatedSeconds: number;
}

const TIMELINE_STAGES: TimelineStage[] = [
  {
    id: 'stage-1',
    name: 'Understanding your trip',
    backendStage: 'intake',
    defaultDescription: 'Deconstructing group dynamic, party rhythm profile, and arrival window.',
    estimatedSeconds: 1,
  },
  {
    id: 'stage-2',
    name: 'Checking travel logistics',
    backendStage: 'logistics',
    defaultDescription: 'Mapped high-speed rail legs, transit connectors, and forward luggage leeway.',
    estimatedSeconds: 2,
  },
  {
    id: 'stage-3',
    name: 'Finding experiences',
    backendStage: 'experience',
    defaultDescription: 'Matched local artisan guilds, private ceremonies, and uncrowded morning hours.',
    estimatedSeconds: 3,
  },
  {
    id: 'stage-4',
    name: 'Checking weather',
    backendStage: 'date_optimizer',
    defaultDescription: 'Analyzing regional microclimate models and seasonal outdoor suitability.',
    estimatedSeconds: 4,
  },
  {
    id: 'stage-5',
    name: 'Calculating budget',
    backendStage: 'budget',
    defaultDescription: 'Allocating target budget across stays, intermodal passes, and dining.',
    estimatedSeconds: 4,
  },
  {
    id: 'stage-6',
    name: 'Optimizing your journey',
    backendStage: 'optimizer',
    defaultDescription: 'Eliminating backtrack transit and calibrating unhurried exploration pauses.',
    estimatedSeconds: 5,
  },
  {
    id: 'stage-7',
    name: 'Your Safarnama is ready',
    backendStage: 'complete',
    defaultDescription: 'Assembling interactive day-by-day editorial travel dossier.',
    estimatedSeconds: 5,
  },
];

export const TripPlanningProgressScreen: React.FC<TripPlanningProgressScreenProps> = ({
  onNavigateReview,
  onNavigateOverview,
}) => {
  const { tripDetails, destinations, preferences, budget, setItinerary, setPlanRunState } =
    useTripPlanning();

  const [currentStageIndex, setCurrentStageIndex] = useState<number>(0);
  const [progressPercent, setProgressPercent] = useState<number>(15);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [stageDetails, setStageDetails] = useState<Record<string, string>>({});
  const [errorState, setErrorState] = useState<string | null>(null);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const streamCleanupRef = useRef<(() => void) | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Format Origin / Destination corridor
  const stopsList: Array<{ id?: string; name: string; nights: number; role?: string }> =
    destinations.length > 0
      ? destinations
      : [{ name: tripDetails.destination, nights: tripDetails.durationDays }];
  const corridorText = `${tripDetails.origin.split('(')[0].trim()} → ${stopsList.map((s) => s.name.split(',')[0].trim()).join(' → ')}`;

  const formatInr = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(Number.isFinite(amount) ? amount : 0);

  // Start Stream and Timer
  useEffect(() => {
    const planRequest = buildPlanRequestDraft(tripDetails, destinations, preferences, budget);
    const abortController = new AbortController();

    setPlanRunState((prev) => ({
      ...prev,
      status: 'streaming',
      currentStage: 'intake',
      progressPercent: 10,
      elapsedSeconds: 0,
    }));

    timerRef.current = setInterval(() => {
      setElapsedSeconds((sec) => sec + 1);
    }, 1000);

    const handleEvent = (event: PlanningEvent) => {
      setPlanRunState((prev) => ({
        ...prev,
        events: [...prev.events, event],
      }));

      if (event.event === 'planning_started' || event.event === 'intake_completed') {
        setCurrentStageIndex(1);
        setProgressPercent(25);
        if (event.message) setStageDetails((d) => ({ ...d, 'stage-1': event.message }));
      } else if (event.event === 'logistics_started' || event.event === 'logistics_completed') {
        setCurrentStageIndex(2);
        setProgressPercent(40);
        if (event.message) setStageDetails((d) => ({ ...d, 'stage-2': event.message }));
      } else if (event.event === 'experience_started' || event.event === 'experience_completed') {
        setCurrentStageIndex(3);
        setProgressPercent(55);
        if (event.message) setStageDetails((d) => ({ ...d, 'stage-3': event.message }));
      } else if (event.event === 'date_optimization_started' || event.event === 'date_optimization_completed') {
        setCurrentStageIndex(4);
        setProgressPercent(70);
        if (event.message) setStageDetails((d) => ({ ...d, 'stage-4': event.message }));
      } else if (event.event === 'budget_started' || event.event === 'budget_calculated') {
        setCurrentStageIndex(5);
        setProgressPercent(82);
        if (event.message) setStageDetails((d) => ({ ...d, 'stage-5': event.message }));
      } else if (event.event === 'optimization_started' || event.event === 'optimization_completed') {
        setCurrentStageIndex(6);
        setProgressPercent(92);
        if (event.message) setStageDetails((d) => ({ ...d, 'stage-6': event.message }));
      }
    };

    const handleComplete = (itinerary: FinalItinerary) => {
      setCurrentStageIndex(7);
      setProgressPercent(100);
      setIsCompleted(true);
      setItinerary(itinerary);

      setPlanRunState((prev) => ({
        ...prev,
        status: 'completed',
        currentStage: 'complete',
        progressPercent: 100,
      }));

      if (timerRef.current) clearInterval(timerRef.current);

      // Brief celebratory pause before navigating to Overview
      setTimeout(() => {
        onNavigateOverview();
      }, 900);
    };

    const handleError = (errorMsg: string) => {
      setErrorState(errorMsg);
      setPlanRunState((prev) => ({
        ...prev,
        status: 'error',
        error: errorMsg,
      }));
      if (timerRef.current) clearInterval(timerRef.current);
    };

    startPlanningStream(planRequest, {
      onEvent: handleEvent,
      onComplete: handleComplete,
      onError: handleError,
      signal: abortController.signal,
      draftContext: { tripDetails, destinations, preferences, budget },
    }).then((cleanup) => {
      streamCleanupRef.current = cleanup;
    });

    return () => {
      abortController.abort();
      if (streamCleanupRef.current) streamCleanupRef.current();
      if (timerRef.current) clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCancel = () => {
    if (streamCleanupRef.current) streamCleanupRef.current();
    if (timerRef.current) clearInterval(timerRef.current);
    onNavigateReview();
  };

  const estimatedRemainingSeconds = Math.max(0, 10 - elapsedSeconds);

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen flex flex-col antialiased">
      {/* Top Header */}
      <header className="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(41,37,33,0.04)]">
        <div className="h-20 max-w-[1280px] mx-auto px-margin-mobile lg:px-margin flex items-center justify-between gap-gutter">
          <div className="flex items-center gap-space-sm">
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
            aria-label="Planning status"
            className="hidden md:flex items-center gap-space-xs bg-surface-container-low px-space-xs py-space-xs rounded-full shadow-[0_1px_3px_-1px_rgba(41,37,33,0.03)]"
          >
            <span className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant">
              1. Review
            </span>
            <span
              aria-current="step"
              className="px-space-md py-space-xs rounded-full transition-colors bg-surface-container-high text-primary font-headline-sm font-bold flex items-center gap-1.5"
            >
              <span className="w-2 h-2 rounded-full bg-primary-container animate-pulse" />
              2. Synthesis
            </span>
            <span className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant">
              3. Overview
            </span>
          </nav>

          <div className="flex items-center gap-space-md">
            <div className="hidden lg:flex items-center gap-space-xs px-space-md py-space-xs rounded-full bg-surface-container-lowest shadow-[0_2px_8px_-2px_rgba(41,37,33,0.04)]">
              <span className="w-2 h-2 rounded-full bg-primary-container animate-pulse" />
              <span className="font-label-caption text-label-caption text-on-surface-variant uppercase tracking-wider font-semibold">
                Planning: {tripDetails.destination.split(',')[0]}
              </span>
            </div>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="w-full pt-20 bg-surface flex-1 min-h-[calc(100vh-20rem)] pb-space-xl">
        <div className="flex flex-col w-full max-w-[1280px] mx-auto px-margin-mobile lg:px-margin py-space-lg space-y-space-lg">
          {/* Top Journey Blueprint Banner */}
          <section
            aria-label="Active Journey Blueprint"
            className="w-full bg-surface-container-lowest rounded-xl p-space-md lg:p-space-lg shadow-sm border border-outline-variant/30 flex flex-col md:flex-row md:items-center justify-between gap-space-md"
          >
            <div className="space-y-space-xs">
              <div className="flex flex-wrap items-center gap-space-xs text-on-surface">
                <span className="font-label-caption text-label-caption text-secondary uppercase tracking-widest font-semibold">
                  Active Blueprint
                </span>
                <span className="text-outline-variant">•</span>
                <span className="font-headline-sm text-headline-sm tracking-tight text-on-surface font-bold">
                  {corridorText}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-x-space-md gap-y-1 font-body-sm text-body-sm text-on-surface-variant">
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[15px] text-primary" aria-hidden="true">
                    calendar_month
                  </span>
                  {tripDetails.departureDate} – {tripDetails.returnDate} ({tripDetails.durationDays} Days)
                </span>
                <span className="text-outline-variant hidden sm:inline">•</span>
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[15px] text-secondary" aria-hidden="true">
                    eco
                  </span>
                  Peak Seasonal Window
                </span>
                <span className="text-outline-variant hidden sm:inline">•</span>
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[15px] text-tertiary" aria-hidden="true">
                    group
                  </span>
                  {tripDetails.adults} {tripDetails.adults === 1 ? 'Explorer' : 'Explorers'} · {preferences.pace || 'Balanced'} Rhythm
                </span>
                <span className="text-outline-variant hidden sm:inline">•</span>
                <span className="flex items-center gap-1 font-medium text-on-surface">
                  {formatInr(budget.budgetInr)} Budget Cap
                </span>
              </div>
            </div>

            <div className="flex items-center gap-space-sm self-start md:self-center shrink-0">
              <div className="px-space-md py-space-xs rounded-full bg-surface-container-low flex items-center gap-space-xs border border-outline-variant/30">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary-container" />
                </span>
                <span className="font-label-caption text-label-caption uppercase tracking-wider text-on-surface-variant font-medium">
                  Batch #SF-8492
                </span>
              </div>
            </div>
          </section>

          {/* Central Planning Engine Interface: Two-Column Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-start">
            {/* Left Column: Primary Progress Stage Engine (7 cols) */}
            <section
              aria-labelledby="planning-engine-title"
              className="lg:col-span-7 bg-surface-container-lowest rounded-xl p-space-md sm:p-space-lg shadow-sm border border-outline-variant/30 space-y-space-lg"
            >
              {/* Header */}
              <div className="space-y-space-xs">
                <div className="inline-flex items-center gap-space-xs px-space-sm py-1 rounded-full bg-primary/10 text-primary font-label-caption text-label-caption uppercase tracking-wider font-semibold">
                  <span className="material-symbols-outlined text-[14px]">memory</span>
                  Continuous Synthesis Protocol
                </div>
                <h1 id="planning-engine-title" className="font-headline-md text-headline-md text-on-surface tracking-tight font-bold">
                  Safarnama is synthesizing your bespoke journey
                </h1>
                <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                  Our mindful planning engine is orchestrating your route, lodging buffers, seasonal microclimates, and regional connections into an unhurried dossier.
                </p>
              </div>

              {/* Error Alert */}
              {errorState && (
                <div role="alert" className="p-space-md rounded-lg bg-error-container/40 border border-error text-on-error-container space-y-2">
                  <div className="font-bold flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px]">error</span>
                    Planning Interrupted
                  </div>
                  <p className="text-sm">{errorState}</p>
                  <button
                    type="button"
                    onClick={() => window.location.reload()}
                    className="mt-2 px-4 py-1.5 rounded-lg bg-primary text-on-primary text-sm font-semibold"
                  >
                    Retry Synthesis
                  </button>
                </div>
              )}

              {/* Vertical Stage Timeline */}
              <div
                aria-live="polite"
                role="status"
                className="relative pl-7 space-y-space-lg before:content-[''] before:absolute before:left-[13px] before:top-3 before:bottom-3 before:w-[2px] before:bg-surface-variant"
              >
                {TIMELINE_STAGES.map((stage, idx) => {
                  const isDone = currentStageIndex > idx || isCompleted;
                  const isActive = currentStageIndex === idx && !isCompleted;
                  const isUpcoming = currentStageIndex < idx && !isCompleted;

                  return (
                    <div
                      key={stage.id}
                      className={`relative group transition-opacity duration-300 ${isUpcoming ? 'opacity-60' : 'opacity-100'}`}
                    >
                      {/* Stage Indicator Node */}
                      {isDone && (
                        <span className="absolute -left-7 top-0.5 w-[26px] h-[26px] rounded-full bg-secondary flex items-center justify-center text-on-secondary shadow-sm">
                          <span className="material-symbols-outlined text-[16px]">check</span>
                        </span>
                      )}

                      {isActive && (
                        <span className="absolute -left-7 top-0.5 w-[26px] h-[26px] rounded-full bg-primary-container flex items-center justify-center text-on-primary shadow-[0_0_12px_rgba(232,117,36,0.45)]">
                          <span className="material-symbols-outlined text-[15px] animate-spin">refresh</span>
                        </span>
                      )}

                      {isUpcoming && (
                        <span className="absolute -left-7 top-1 w-[26px] h-[26px] rounded-full bg-surface-container-high flex items-center justify-center text-outline">
                          <span className="w-2 h-2 rounded-full bg-outline" />
                        </span>
                      )}

                      {/* Stage Content */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-space-xs">
                            <span className="font-headline-sm text-headline-sm text-on-surface font-semibold">
                              {stage.name}
                            </span>
                            {isActive && (
                              <span className="font-label-caption text-label-caption px-space-xs py-0.5 rounded-full bg-primary/15 text-primary uppercase font-bold tracking-wider">
                                Live
                              </span>
                            )}
                          </div>
                          {isDone ? (
                            <span className="font-label-caption text-label-caption text-on-surface-variant">
                              0.{idx + 2}s
                            </span>
                          ) : isActive ? (
                            <span className="font-label-caption text-label-caption text-primary font-medium">
                              In Progress
                            </span>
                          ) : null}
                        </div>

                        <p className="font-body-sm text-body-sm text-on-surface-variant">
                          {stageDetails[stage.id] || stage.defaultDescription}
                        </p>

                        {/* Contextual Detail Card when active */}
                        {isActive && (
                          <div className="bg-surface-container-low rounded-lg p-space-md space-y-space-sm shadow-sm mt-2 border border-outline-variant/30">
                            <div className="flex items-center gap-space-xs text-on-surface font-label-md text-label-md font-semibold">
                              <span className="material-symbols-outlined text-[16px] text-primary-container animate-pulse">
                                cloud_sync
                              </span>
                              <span>Calibrating route dynamics & destination context</span>
                            </div>
                            <ul className="space-y-space-xs font-body-sm text-body-sm text-on-surface-variant">
                              <li className="flex items-start gap-space-xs">
                                <span className="text-primary-container mt-0.5 font-bold">›</span>
                                <span>
                                  <strong className="text-on-surface font-medium">Route Rhythm:</strong> Balanced transitions calibrated for {tripDetails.durationDays} days.
                                </span>
                              </li>
                              <li className="flex items-start gap-space-xs">
                                <span className="text-primary-container mt-0.5 font-bold">›</span>
                                <span>
                                  <strong className="text-on-surface font-medium">Pacing Leeway:</strong> Unhurried morning access and restorative evening windows scheduled.
                                </span>
                              </li>
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Linear Engine Progress Bar */}
              <div className="pt-space-md space-y-space-xs bg-surface-container-low rounded-lg p-space-md border border-outline-variant/30">
                <div className="flex items-center justify-between font-label-md text-label-md">
                  <span className="text-on-surface font-semibold">
                    Synthesis Progress:{' '}
                    <span className="text-primary-container font-bold" id="progress-val">
                      {progressPercent}%
                    </span>
                  </span>
                  <span className="text-on-surface-variant font-normal">
                    {isCompleted ? 'Synthesis complete!' : `Estimated remaining: ~${estimatedRemainingSeconds}s`}
                  </span>
                </div>
                <div
                  role="progressbar"
                  aria-valuenow={progressPercent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label="Trip synthesis progress"
                  className="w-full h-2 rounded-full bg-surface-container-high overflow-hidden"
                >
                  <div
                    className="h-full bg-primary-container rounded-full transition-all duration-700 ease-out"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            </section>

            {/* Right Column: Journey Route Visualizer & Engine Telemetry (5 cols) */}
            <section
              aria-label="Transit and Corridor Telemetry"
              className="lg:col-span-5 space-y-space-md"
            >
              {/* Route Alignment Visualizer Card */}
              <div className="bg-surface-container-lowest rounded-xl p-space-md sm:p-space-lg shadow-sm border border-outline-variant/30 space-y-space-md">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="font-label-caption text-label-caption text-secondary uppercase tracking-widest font-semibold">
                      Corridor Layout
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                      Transit & Route Alignment
                    </h2>
                  </div>
                  <span className="material-symbols-outlined text-primary-container text-[20px]" aria-hidden="true">
                    explore
                  </span>
                </div>

                {/* Stylized Route Nodes Progression */}
                <div className="relative bg-surface-container-low rounded-lg p-space-md overflow-hidden space-y-space-md border border-outline-variant/20">
                  <div className="absolute -right-8 -top-8 w-36 h-36 rounded-full bg-primary/5 pointer-events-none blur-2xl" />

                  <div className="relative space-y-space-md">
                    {/* Origin Stop */}
                    <div className="flex items-start gap-space-sm">
                      <div className="flex flex-col items-center">
                        <div className="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center text-on-surface font-label-caption text-label-caption font-bold shadow-sm">
                          {tripDetails.origin.includes('(') ? tripDetails.origin.split('(')[1].slice(0, 3) : 'ORIG'}
                        </div>
                        <div className="w-[2px] h-9 bg-surface-variant flex items-center justify-center my-0.5">
                          <span className="material-symbols-outlined text-[13px] text-outline rotate-90" aria-hidden="true">
                            {tripDetails.scope === 'DOMESTIC' ? 'train' : 'flight'}
                          </span>
                        </div>
                      </div>
                      <div className="pt-0.5">
                        <span className="font-label-md text-label-md text-on-surface font-semibold block">
                          {tripDetails.origin}
                        </span>
                        <p className="font-body-sm text-body-sm text-on-surface-variant">
                          Origin Departure Hub · Direct Departure
                        </p>
                      </div>
                    </div>

                    {/* Destination Stops */}
                    {stopsList.map((stop, sIndex) => {
                      const isLast = sIndex === stopsList.length - 1;
                      return (
                        <div key={stop.id || `stop-${sIndex}`} className="flex items-start gap-space-sm">
                          <div className="flex flex-col items-center">
                            <div className="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container font-label-caption text-label-caption font-bold shadow-sm ring-2 ring-primary-container/20">
                              {stop.nights}N
                            </div>
                            {!isLast && (
                              <div className="relative w-[2px] h-10 bg-outline-variant overflow-hidden my-0.5">
                                <div className="absolute inset-0 bg-primary-container animate-pulse" />
                              </div>
                            )}
                          </div>
                          <div className="pt-0.5 space-y-1">
                            <div className="flex items-center gap-space-xs">
                              <span className="font-label-md text-label-md text-on-surface font-semibold">
                                {stop.name}
                              </span>
                              <span className="px-space-xs py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-caption text-label-caption">
                                {stop.nights} {stop.nights === 1 ? 'Night' : 'Nights'}
                              </span>
                            </div>
                            <span className="inline-block px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-caption text-label-caption font-medium">
                              {stop.role || 'Curated Waypoint'}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Route Footnote */}
                  <div className="pt-space-xs flex items-center justify-between text-on-surface-variant font-label-caption text-label-caption border-t border-outline-variant/30">
                    <span className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary-container" />
                      Intermodal connections calibrated
                    </span>
                    <span>{tripDetails.durationDays} Days Total</span>
                  </div>
                </div>
              </div>

              {/* Telemetry & Trust Badges Card */}
              <div className="bg-surface-container-lowest rounded-xl p-space-md sm:p-space-lg shadow-sm border border-outline-variant/30 space-y-space-md">
                <div className="space-y-space-xs">
                  <span className="font-label-caption text-label-caption text-secondary uppercase tracking-widest font-semibold">
                    Safarnama Logic
                  </span>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                    Data & Calibration Architecture
                  </h3>
                </div>
                <div className="space-y-space-xs">
                  <div className="flex items-start gap-space-xs p-space-xs rounded bg-surface-container-low text-on-surface font-body-sm text-body-sm">
                    <span className="material-symbols-outlined text-[18px] text-primary shrink-0 mt-0.5">verified</span>
                    <span>Live transit schedules & seat availability buffers</span>
                  </div>
                  <div className="flex items-start gap-space-xs p-space-xs rounded bg-surface-container-low text-on-surface font-body-sm text-body-sm">
                    <span className="material-symbols-outlined text-[18px] text-primary shrink-0 mt-0.5">verified</span>
                    <span>Seasonal historical intelligence & uncrowded morning hours</span>
                  </div>
                  <div className="flex items-start gap-space-xs p-space-xs rounded bg-surface-container-low text-on-surface font-body-sm text-body-sm">
                    <span className="material-symbols-outlined text-[18px] text-primary shrink-0 mt-0.5">verified</span>
                    <span>Indicative stay tariffs & real-time INR currency buffer</span>
                  </div>
                </div>

                {/* Editorial Philosophy Excerpt */}
                <div className="p-space-md rounded-lg bg-surface-container space-y-1 border-l-2 border-primary">
                  <p className="font-body-sm text-body-sm text-on-surface italic leading-relaxed">
                    &ldquo;Every journey is an unhurried story. We balance logistics so you can savor the cadence of travel.&rdquo;
                  </p>
                  <span className="block font-label-caption text-label-caption text-on-surface-variant font-medium text-right">
                    — Safarnama Editorial Desk
                  </span>
                </div>

                {/* Bottom Assurance & Actions */}
                <div className="pt-space-xs space-y-space-xs border-t border-outline-variant/30">
                  <div className="flex items-center gap-space-xs text-on-surface-variant font-label-caption text-label-caption">
                    <span className="material-symbols-outlined text-[16px] text-secondary">lock</span>
                    <span>All drafts are securely saved on your device.</span>
                  </div>
                  <div className="pt-space-xs flex items-center justify-between">
                    <button
                      type="button"
                      onClick={handleCancel}
                      className="inline-flex items-center gap-1 font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors py-1 cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
                    >
                      <span className="material-symbols-outlined text-[16px]">arrow_back</span>
                      Cancel and return to review
                    </button>
                    {isCompleted && (
                      <button
                        type="button"
                        onClick={onNavigateOverview}
                        className="px-4 py-2 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold hover:bg-primary-container shadow-sm transition-all"
                      >
                        Open Dossier
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};
