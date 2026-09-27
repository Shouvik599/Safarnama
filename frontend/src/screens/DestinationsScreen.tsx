import React, { useState, useEffect } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import { PlannerHeader } from '../components/layout/PlannerHeader';
import { PlannerFooter } from '../components/layout/PlannerFooter';
import { ProgressStepper } from '../components/planner/ProgressStepper';
import { RouteSequenceItem } from '../components/planner/RouteSequenceItem';
import { SuggestionCard } from '../components/planner/SuggestionCard';
import type { DestinationSuggestion, RouteStop } from '../types/trip';
import {
  resolveDestinationData,
  ALL_CURATED_DESTINATIONS,
} from '../data/destinationsRegistry';

interface DestinationsScreenProps {
  onBackToTripDetails: () => void;
  onNavigateHome: () => void;
  onContinueToPreferences?: () => void;
}

export const DestinationsScreen: React.FC<DestinationsScreenProps> = ({
  onBackToTripDetails,
  onNavigateHome,
  onContinueToPreferences,
}) => {
  const {
    destinations,
    addDestination,
    removeDestination,
    updateStopNights,
    moveDestinationUp,
    moveDestinationDown,
    tripDetails,
    updateTripDetails,
    seedDestination,
  } = useTripPlanning();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [showNextStepAlert, setShowNextStepAlert] = useState(false);

  // Dynamically resolve active destination and route template from user's chosen destination
  const activeCircuit = resolveDestinationData(tripDetails.destination);

  // Ensure stops are synced with activeCircuit if destination changed
  useEffect(() => {
    const activeFirstCountry = activeCircuit.defaultStops[0]?.country?.toLowerCase() || '';
    const currentFirstCountry = destinations[0]?.country?.toLowerCase() || '';
    if (
      destinations.length === 0 ||
      (activeFirstCountry &&
        currentFirstCountry &&
        !activeFirstCountry.includes(currentFirstCountry) &&
        !currentFirstCountry.includes(activeFirstCountry))
    ) {
      seedDestination(activeCircuit.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripDetails.destination, activeCircuit.id]);

  // Duration reconciliation calculations
  const totalAllocatedNights = destinations.reduce((sum, d) => sum + (d.nights || 0), 0);
  const targetDurationDays = tripDetails.durationDays || 1;
  const durationDiff = totalAllocatedNights - targetDurationDays;

  // Sync trip return date to match total allocated stop nights
  const handleAlignTripDuration = () => {
    const departure = tripDetails.departureDateIso
      ? new Date(tripDetails.departureDateIso)
      : new Date();
    const returnD = new Date(departure);
    returnD.setDate(departure.getDate() + totalAllocatedNights);

    const retFormatted = returnD.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
    const retIso = returnD.toISOString().split('T')[0];

    updateTripDetails({
      durationDays: totalAllocatedNights,
      returnDate: retFormatted,
      returnDateIso: retIso,
      returnLegInfo: `${returnD.getFullYear()} • Evening leg`,
    });
  };

  const categories = [
    'All',
    'Current Circuit Suggestions',
    'Domestic Circuits (India)',
    'International',
    'Scenic & Nature',
    'Cultural & Heritage',
  ];

  // Dynamically resolve suggestions
  const getFilteredSuggestions = (): DestinationSuggestion[] => {
    let pool: DestinationSuggestion[] = [];

    if (activeCategory === 'Current Circuit Suggestions' || activeCategory === 'All') {
      pool = [...activeCircuit.suggestions];
    } else if (activeCategory === 'Domestic Circuits (India)') {
      pool = ALL_CURATED_DESTINATIONS.filter((c) => c.scope === 'DOMESTIC').flatMap(
        (c) => c.suggestions
      );
    } else if (activeCategory === 'International') {
      pool = ALL_CURATED_DESTINATIONS.filter((c) => c.scope === 'INTERNATIONAL').flatMap(
        (c) => c.suggestions
      );
    } else if (activeCategory === 'Scenic & Nature') {
      pool = ALL_CURATED_DESTINATIONS.flatMap((c) =>
        c.suggestions.filter(
          (s) =>
            s.tag.toLowerCase().includes('scenic') ||
            s.tag.toLowerCase().includes('lake') ||
            s.tag.toLowerCase().includes('cliff') ||
            s.tag.toLowerCase().includes('sanctuary') ||
            s.tag.toLowerCase().includes('fjord') ||
            s.tag.toLowerCase().includes('mountain') ||
            s.tag.toLowerCase().includes('alpine')
        )
      );
    } else {
      pool = ALL_CURATED_DESTINATIONS.flatMap((c) => c.suggestions);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      pool = pool.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.region.toLowerCase().includes(q) ||
          s.tag.toLowerCase().includes(q)
      );
    }

    return pool.slice(0, 6);
  };

  const currentSuggestions = getFilteredSuggestions();

  const handleAddCustomDestination = () => {
    if (!searchQuery.trim()) return;
    const name = searchQuery.trim();
    const newStop: RouteStop = {
      id: `custom-${Date.now()}`,
      name,
      country: activeCircuit.scope === 'DOMESTIC' ? 'India' : 'International',
      nights: 2,
      role: 'Custom Stop',
      imageUrl:
        'https://lh3.googleusercontent.com/aida-public/AB6AXuD6mcxF54MPkKZuSc4IKenZHCkkj4fqa7VhihkWiSrZSkPj1t56XCkq7yA_tl7gobd3cqHYwesjfCWhbuSnaBjsalbEyub274sIagz887vs-R5V1iB3iguh3AgVFU2Na8y-oVAXvd7ZTFh_6fp-pPAcwYZ0jE-KK5YlQ3zBBwdfJKe0eYP_yShgXMqJMWF3SoOxSVBpPtTOW3lkx67sCW53IxFaw6Uo2gkmsYFVgoY0XcJCntKjZClZqw',
    };
    addDestination(newStop);
    setSearchQuery('');
  };

  const handleAddSuggestion = (s: DestinationSuggestion) => {
    const newStop: RouteStop = {
      id: s.id,
      name: s.name,
      country: activeCircuit.scope === 'DOMESTIC' ? 'India' : 'International',
      nights: s.isDayTrip ? 1 : 2,
      role: s.isDayTrip ? 'Day Trip Excursion' : s.tag,
      imageUrl: s.imageUrl,
      imageAlt: s.imageAlt,
    };
    addDestination(newStop);
  };

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen flex flex-col antialiased">
      {/* Planner Header */}
      <PlannerHeader
        currentStep={2}
        onNavigateHome={onNavigateHome}
        onNavigateStep={(step) => {
          if (step === 1) onBackToTripDetails();
        }}
      />

      {/* Main Content */}
      <main className="w-full pt-20 flex-1 max-w-[1280px] mx-auto px-margin-mobile sm:px-margin bg-surface">
        <div className="flex flex-col w-full">
          {/* Stepper Progress Header */}
          <ProgressStepper
            currentStep={2}
            onSelectStep={(step) => {
              if (step === 1) onBackToTripDetails();
            }}
          />

          {/* Eyebrow & Hero Header */}
          <div className="max-w-3xl mx-auto text-center mb-space-xl">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-surface-container-high text-on-secondary-fixed-variant mb-3 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
              <span className="font-label-md text-label-md uppercase tracking-widest font-semibold">
                Step 2 of 5 • Route &amp; Stops
              </span>
            </div>
            <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight mb-2">
              Where would you like to explore?
            </h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto">
              Craft your route by adding stops along your journey. Reorder stops to optimize transit,
              balance nights, or explore curated regional pairings.
            </p>
          </div>

          {/* Main Planner Container */}
          <div className="max-w-4xl mx-auto w-full flex flex-col gap-space-xl">
            {/* Quick Circuit Preset Switcher */}
            <div className="bg-surface-container-lowest p-space-md sm:p-space-lg rounded-2xl shadow-sm border border-outline-variant/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[20px]">hub</span>
                <span className="font-label-md text-label-md font-bold text-on-surface">
                  Curated Route Templates:
                </span>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {[
                  { id: 'norway', alias: 'Norway Fjords' },
                  { id: 'japan', alias: 'Japan (Autumn Trail)' },
                  { id: 'ladakh', alias: 'Ladakh (High Passes)' },
                  { id: 'italy', alias: 'Italy Circuit' },
                  { id: 'rajasthan', alias: 'Rajasthan Royals' },
                  { id: 'switzerland', alias: 'Swiss Alps' },
                  { id: 'kerala', alias: 'Kerala Backwaters' },
                  { id: 'goa', alias: 'Goa Coast' },
                ].map((circuit) => {
                  const isCircuitActive =
                    activeCircuit.id === circuit.id ||
                    tripDetails.destination.toLowerCase().includes(circuit.id);
                  return (
                    <button
                      key={circuit.id}
                      type="button"
                      onClick={() => seedDestination(circuit.id)}
                      className={`px-3 py-1.5 rounded-full font-label-md text-label-md transition-all cursor-pointer flex items-center gap-1.5 ${
                        isCircuitActive
                          ? 'bg-primary text-on-primary font-bold shadow-sm ring-2 ring-primary/30'
                          : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                      }`}
                    >
                      <span className="material-symbols-outlined text-[14px]">
                        {isCircuitActive ? 'check_circle' : 'alt_route'}
                      </span>
                      <span>{circuit.alias}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Search & Quick Selection Section */}
            <div className="bg-surface-container-lowest p-space-lg rounded-2xl shadow-sm flex flex-col gap-space-md border border-outline-variant/30">
              <div className="relative flex items-center w-full">
                <span className="material-symbols-outlined absolute left-4 text-on-surface-variant text-[24px]">
                  search
                </span>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleAddCustomDestination();
                  }}
                  placeholder="Search destinations (e.g. Kyoto, Jaipur, Florence, Leh, Tokyo)..."
                  className="w-full pl-12 pr-36 py-3.5 bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/60 rounded-xl font-body-md text-body-md focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all border border-outline-variant/30"
                />
                <button
                  type="button"
                  onClick={handleAddCustomDestination}
                  className="absolute right-2 px-space-md py-2 bg-primary text-on-primary rounded-lg font-label-md text-label-md flex items-center gap-1.5 shadow hover:opacity-95 transition-opacity cursor-pointer"
                  id="btn-add-destination"
                >
                  <span className="material-symbols-outlined text-[18px]">add_location_alt</span>
                  <span>Add Stop</span>
                </button>
              </div>

              {/* Quick Category Chips */}
              <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
                {categories.map((cat) => {
                  const isCatActive = activeCategory === cat;
                  return (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => setActiveCategory(cat)}
                      className={`px-3.5 py-1.5 rounded-full font-label-md text-label-md transition-colors whitespace-nowrap cursor-pointer ${
                        isCatActive
                          ? 'bg-surface-container-highest text-primary font-bold shadow-sm'
                          : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high'
                      }`}
                    >
                      {cat}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Route Sequence Component */}
            <div className="bg-surface-container-lowest p-space-lg sm:p-space-xl rounded-2xl shadow-sm border border-outline-variant/30">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-space-md mb-space-md gap-3 border-b border-outline-variant/20">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary-fixed flex items-center justify-center text-on-primary-fixed">
                    <span className="material-symbols-outlined text-[18px]">route</span>
                  </div>
                  <div>
                    <h2 className="font-headline-md text-headline-md text-on-surface font-bold">
                      Your Route Sequence
                    </h2>
                    <p className="font-body-sm text-body-sm text-on-surface-variant">
                      Active Circuit: <strong className="text-on-surface">{activeCircuit.alias}</strong> ({activeCircuit.scope.toLowerCase()})
                    </p>
                  </div>
                </div>

                <div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-container-high rounded-full self-start sm:self-auto">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                  <span className="font-label-md text-label-md text-on-surface-variant font-medium">
                    {destinations.length} destination{destinations.length !== 1 ? 's' : ''} added &bull; Use arrows to reorder
                  </span>
                </div>
              </div>

              {/* Dynamic Duration Reconciliation Status Banner */}
              <div
                className={`p-3.5 sm:p-4 rounded-xl mb-space-lg border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                  durationDiff === 0
                    ? 'bg-secondary-fixed/30 border-secondary/30 text-on-secondary-fixed-variant'
                    : durationDiff < 0
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-200'
                    : 'bg-primary-fixed/40 border-primary/30 text-on-primary-fixed-variant'
                }`}
                id="duration-reconciliation-banner"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className={`material-symbols-outlined text-[20px] shrink-0 ${
                      durationDiff === 0
                        ? 'text-secondary font-bold'
                        : durationDiff < 0
                        ? 'text-amber-600'
                        : 'text-primary'
                    }`}
                  >
                    {durationDiff === 0 ? 'check_circle' : 'pending_actions'}
                  </span>
                  <div className="flex flex-col">
                    <span className="font-label-md text-label-md font-bold">
                      {durationDiff === 0
                        ? `✓ Balanced Itinerary: All ${totalAllocatedNights} nights allocated across ${destinations.length} stops`
                        : durationDiff < 0
                        ? `⏳ Duration Gap: ${totalAllocatedNights} of ${targetDurationDays} nights allocated (${Math.abs(
                            durationDiff
                          )} unallocated ${Math.abs(durationDiff) === 1 ? 'night' : 'nights'})`
                        : `⚠️ Over-allocated: ${totalAllocatedNights} nights assigned for a ${targetDurationDays}-night trip (+${durationDiff} extra ${
                            durationDiff === 1 ? 'night' : 'nights'
                          })`}
                    </span>
                    <span className="text-[12px] opacity-80">
                      Trip Duration: {targetDurationDays} days ({tripDetails.departureDate} → {tripDetails.returnDate})
                    </span>
                  </div>
                </div>

                {durationDiff !== 0 && (
                  <button
                    type="button"
                    onClick={handleAlignTripDuration}
                    className="px-3.5 py-1.5 rounded-lg bg-surface-container-lowest text-primary hover:bg-surface-container font-label-md text-label-md font-bold shadow-xs transition-colors self-start sm:self-auto cursor-pointer border border-outline-variant/30 flex items-center gap-1.5 shrink-0"
                    title="Synchronize departure and return dates with your allocated stop nights"
                    id="btn-reconcile-duration"
                  >
                    <span className="material-symbols-outlined text-[16px]">sync_alt</span>
                    <span>Sync Trip Duration to {totalAllocatedNights} Nights</span>
                  </button>
                )}
              </div>

              {/* Linear Route Timeline Visualizer */}
              <div className="flex flex-col relative pl-4 sm:pl-8">
                {/* Continuous Route Spine Line */}
                {destinations.length > 1 && (
                  <div className="absolute left-9 sm:left-13 top-6 bottom-16 w-[2px] bg-primary/20 -z-0" />
                )}

                {/* Destination Items with Night Counter Steppers */}
                {destinations.map((stop, idx) => (
                  <RouteSequenceItem
                    key={stop.id}
                    stop={stop}
                    index={idx}
                    totalStops={destinations.length}
                    onMoveUp={() => moveDestinationUp(idx)}
                    onMoveDown={() => moveDestinationDown(idx)}
                    onRemove={() => removeDestination(stop.id)}
                    onUpdateNights={(nights) => updateStopNights(stop.id, nights)}
                  />
                ))}

                {/* Add Stop Placeholder Trigger */}
                <button
                  type="button"
                  onClick={() => {
                    const nextSuggestion = currentSuggestions.find(
                      (s) => !destinations.some((d) => d.id === s.id)
                    );
                    if (nextSuggestion) {
                      handleAddSuggestion(nextSuggestion);
                    } else {
                      handleAddSuggestion({
                        id: `stop-${Date.now()}`,
                        name: 'Tokyo',
                        region: 'Kanto, Japan',
                        tag: 'Metropolitan Finale',
                        description:
                          'High-energy cityscape, world-class gastronomy, and historic Asakusa.',
                        imageUrl:
                          'https://lh3.googleusercontent.com/aida-public/AB6AXuD6mcxF54MPkKZuSc4IKenZHCkkj4fqa7VhihkWiSrZSkPj1t56XCkq7yA_tl7gobd3cqHYwesjfCWhbuSnaBjsalbEyub274sIagz887vs-R5V1iB3iguh3AgVFU2Na8y-oVAXvd7ZTFh_6fp-pPAcwYZ0jE-KK5YlQ3zBBwdfJKe0eYP_yShgXMqJMWF3SoOxSVBpPtTOW3lkx67sCW53IxFaw6Uo2gkmsYFVgoY0XcJCntKjZClZqw',
                        actionLabel: '+ Add Stop',
                      });
                    }
                  }}
                  className="mt-2 ml-14 sm:ml-16 py-3 px-4 rounded-xl bg-surface-container-high/60 hover:bg-surface-container-high text-primary font-label-md text-label-md flex items-center justify-center gap-2 transition-all cursor-pointer self-start"
                >
                  <span className="material-symbols-outlined text-[20px]">add_circle</span>
                  <span>+ Add another destination to route</span>
                </button>
              </div>
            </div>

            {/* Editorial Route Intelligence Note */}
            <div className="bg-surface-container-low rounded-2xl p-space-lg flex items-start gap-4 shadow-sm border border-outline-variant/30">
              <div className="w-10 h-10 rounded-full bg-primary-fixed text-on-primary-fixed flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-[22px]">explore</span>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="font-label-md text-label-md font-bold text-primary uppercase tracking-wider">
                    Safarnama Route Note
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant font-label-caption text-label-caption">
                    Logistics Optimized
                  </span>
                </div>
                <p className="font-body-md text-body-md text-on-surface">
                  The{' '}
                  <strong>
                    {destinations.map((d) => d.name).join(' → ') || 'Selected Route'}
                  </strong>{' '}
                  corridor offers exceptional rail and road efficiency, allowing seamless luggage
                  transfers between stays without back-tracking.
                </p>
              </div>
            </div>

            {/* Explore Suggestions & Detours Grid */}
            <div className="flex flex-col gap-space-md">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h2 className="font-headline-md text-headline-md text-on-surface font-bold">
                    Explore suggestions for your journey
                  </h2>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">
                    Commonly paired destinations and scenic detours for your route
                  </p>
                </div>
              </div>

              {/* Recommendation Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
                {currentSuggestions.map((sug) => {
                  const isAdded = destinations.some((d) => d.id === sug.id);
                  return (
                    <SuggestionCard
                      key={sug.id}
                      suggestion={sug}
                      isAdded={isAdded}
                      onAdd={() => handleAddSuggestion(sug)}
                    />
                  );
                })}
              </div>
            </div>

            {/* Next Step Notice / Alert modal or toast */}
            {showNextStepAlert && (
              <div className="p-4 rounded-xl bg-primary-fixed text-on-primary-fixed-variant flex items-center justify-between shadow-sm animate-fade-in">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[20px] text-primary">
                    info
                  </span>
                  <span className="font-label-md text-label-md font-semibold">
                    Batch 1 scope complete: Step 3 (Preferences) will be unlocked in Batch 2!
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowNextStepAlert(false)}
                  className="text-on-primary-fixed-variant hover:text-primary cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>
            )}

            {/* Bottom Action Navigation Bar */}
            <div className="bg-surface-container-lowest p-space-md sm:p-space-lg rounded-2xl shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4 mt-space-sm mb-space-lg border border-outline-variant/30">
              <div className="flex items-center gap-2 text-on-surface-variant font-label-md text-label-md">
                <span
                  className="material-symbols-outlined text-[18px] text-primary"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  cloud_done
                </span>
                <span>
                  Auto-saved to your draft ({destinations.length} destination
                  {destinations.length !== 1 ? 's' : ''}, {totalAllocatedNights} nights queued)
                </span>
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                <button
                  type="button"
                  onClick={onBackToTripDetails}
                  className="px-5 py-3 rounded-xl bg-surface-container-low hover:bg-surface-container text-on-surface font-label-md text-label-md font-semibold transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">arrow_back</span>
                  <span>Back</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    if (onContinueToPreferences) {
                      onContinueToPreferences();
                    } else {
                      setShowNextStepAlert(true);
                    }
                  }}
                  className="px-8 py-3.5 rounded-xl bg-primary text-on-primary hover:opacity-95 shadow-md font-label-md text-label-md font-bold transition-all flex items-center gap-2 cursor-pointer active:scale-98"
                >
                  <span>Continue to Preferences</span>
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <PlannerFooter />
    </div>
  );
};
