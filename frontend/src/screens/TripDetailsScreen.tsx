import React, { useState, useEffect, useRef } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import { PlannerHeader } from '../components/layout/PlannerHeader';
import { PlannerFooter } from '../components/layout/PlannerFooter';
import { ProgressStepper } from '../components/planner/ProgressStepper';
import { CounterStepper } from '../components/planner/CounterStepper';
import {
  INDIAN_ORIGIN_AIRPORTS,
  getSeasonDescription,
  getMultiDestinationVisaVerdict,
} from '../data/locations';
import {
  searchAllDestinations,
  resolveDestinationData,
  searchOriginLocations,
  splitDestinationsString,
  type OriginLocationOption,
} from '../data/destinationsRegistry';
import type { PartyType } from '../types/trip';

interface TripDetailsScreenProps {
  onBackToWelcome: () => void;
  onContinueToDestinations: () => void;
}

export const TripDetailsScreen: React.FC<TripDetailsScreenProps> = ({
  onBackToWelcome,
  onContinueToDestinations,
}) => {
  const { tripDetails, updateTripDetails, seedDestination, destinations } = useTripPlanning();

  const activeScope: 'DOMESTIC' | 'INTERNATIONAL' = tripDetails.scope || 'INTERNATIONAL';

  // Autocomplete dropdown states
  const [originQuery, setOriginQuery] = useState(tripDetails.origin);
  const [showOriginDropdown, setShowOriginDropdown] = useState(false);
  const originRef = useRef<HTMLDivElement>(null);

  const [destQuery, setDestQuery] = useState(tripDetails.destination);
  const [showDestDropdown, setShowDestDropdown] = useState(false);
  const destRef = useRef<HTMLDivElement>(null);
  const depInputRef = useRef<HTMLInputElement>(null);
  const retInputRef = useRef<HTMLInputElement>(null);

  // Sync queries when context changes externally during render (React recommended pattern)
  const [prevOrigin, setPrevOrigin] = useState(tripDetails.origin);
  if (tripDetails.origin !== prevOrigin) {
    setPrevOrigin(tripDetails.origin);
    setOriginQuery(tripDetails.origin);
  }

  const [prevDest, setPrevDest] = useState(tripDetails.destination);
  if (tripDetails.destination !== prevDest) {
    setPrevDest(tripDetails.destination);
    setDestQuery(tripDetails.destination);
  }

  // Click outside listener to dismiss autocomplete dropdowns
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (originRef.current && !originRef.current.contains(event.target as Node)) {
        setShowOriginDropdown(false);
      }
      if (destRef.current && !destRef.current.contains(event.target as Node)) {
        setShowDestDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filtered Indian origins based on scope (Domestic = 4,198 cities + airports; International = strictly IATA departure airports)
  const filteredOrigins = searchOriginLocations(originQuery, activeScope);

  // Filtered destination options using full static datasets strictly partitioned by scope
  const filteredDestinations = searchAllDestinations(destQuery, activeScope);

  // Handle scope toggle switch
  const handleToggleScope = (newScope: 'DOMESTIC' | 'INTERNATIONAL') => {
    if (newScope === activeScope) return;

    if (newScope === 'DOMESTIC') {
      const resolved = resolveDestinationData(tripDetails.destination);
      const isAlreadyDomestic = resolved.scope === 'DOMESTIC';
      const targetDest = isAlreadyDomestic
        ? tripDetails.destination
        : 'Rajasthan (Jaipur, Jodhpur, Udaipur & Jaisalmer)';
      updateTripDetails({
        scope: 'DOMESTIC',
        destination: targetDest,
        destinations: [targetDest],
      });
      setDestQuery(targetDest);
      seedDestination(targetDest, 'DOMESTIC');
    } else {
      const resolved = resolveDestinationData(tripDetails.destination);
      const isAlreadyIntl = resolved.scope === 'INTERNATIONAL';
      const targetDest = isAlreadyIntl
        ? tripDetails.destination
        : 'Norway (Oslo, Flåm, Bergen & Tromsø)';

      // International origin strictly restricted to Indian commercial airports
      const isAirportOrigin = INDIAN_ORIGIN_AIRPORTS.some(
        (a) =>
          tripDetails.origin.toLowerCase().includes(a.code.toLowerCase()) ||
          tripDetails.origin.toLowerCase().includes(a.city.toLowerCase())
      );
      const safeOrigin = isAirportOrigin ? tripDetails.origin : 'New Delhi (DEL)';

      updateTripDetails({
        scope: 'INTERNATIONAL',
        destination: targetDest,
        destinations: [targetDest],
        origin: safeOrigin,
      });
      setDestQuery(targetDest);
      setOriginQuery(safeOrigin);
      seedDestination(targetDest, 'INTERNATIONAL');
    }
  };

  // Handle origin selection
  const handleSelectOrigin = (opt: OriginLocationOption) => {
    updateTripDetails({ origin: opt.name });
    setOriginQuery(opt.name);
    setShowOriginDropdown(false);
  };

  // Selected destinations list respecting parentheses
  const selectedDestinations =
    tripDetails.destinations && tripDetails.destinations.length > 0
      ? tripDetails.destinations
      : splitDestinationsString(tripDetails.destination);
  const [isAddingDestination, setIsAddingDestination] = useState(false);

  // Handle destination selection
  const handleSelectDestination = (destIdOrName: string) => {
    if (isAddingDestination) {
      const found = filteredDestinations.find(
        (d) => d.id === destIdOrName || d.title.toLowerCase() === destIdOrName.toLowerCase()
      );
      const nameToAdd = found ? found.title : destIdOrName;
      const alreadyHas = selectedDestinations.some(
        (d) =>
          d.toLowerCase() === nameToAdd.toLowerCase() ||
          nameToAdd.toLowerCase().includes(d.toLowerCase()) ||
          d.toLowerCase().includes(nameToAdd.toLowerCase())
      );
      const updated = alreadyHas ? selectedDestinations : [...selectedDestinations, nameToAdd];
      updateTripDetails({
        destination: updated.join(', '),
        destinations: updated,
      });
      seedDestination(updated, activeScope);
      setIsAddingDestination(false);
      setDestQuery(updated.join(', '));
      setShowDestDropdown(false);
      return;
    }

    seedDestination(destIdOrName, activeScope);
    setShowDestDropdown(false);
  };

  // Handle removing an individual destination chip
  const handleRemoveDestination = (indexToRemove: number) => {
    const updated = selectedDestinations.filter((_, idx) => idx !== indexToRemove);
    if (updated.length === 0) {
      updateTripDetails({
        destination: '',
        destinations: [],
      });
      setDestQuery('');
    } else {
      const combined = updated.join(', ');
      updateTripDetails({
        destination: combined,
        destinations: updated,
      });
      seedDestination(updated, activeScope);
      setDestQuery(combined);
    }
  };

  // Safe continue handler ensuring route stops match destination
  const handleContinue = () => {
    const targetDest = destQuery || tripDetails.destination;
    const resolved = resolveDestinationData(targetDest, activeScope);
    const currentFirstCountry = destinations[0]?.country?.toLowerCase() || '';
    const resolvedFirstCountry = (resolved.defaultStops[0]?.country || resolved.name).toLowerCase();
    if (!currentFirstCountry.includes(resolvedFirstCountry) && !resolvedFirstCountry.includes(currentFirstCountry)) {
      seedDestination(targetDest, activeScope);
    }
    onContinueToDestinations();
  };

  // Leg time toggles
  const legTimes = ['Morning leg', 'Afternoon leg', 'Evening leg'];

  const getLegTimeOnly = (fullInfo: string, defaultTime: string) => {
    const match = legTimes.find((t) => fullInfo.includes(t));
    return match || defaultTime;
  };

  // Date change calculations
  const handleDepartureDateChange = (newIso: string) => {
    if (!newIso) return;
    const depDate = new Date(newIso);
    let retDate = new Date(tripDetails.returnDateIso || newIso);

    // If return date is on or before departure date, advance return date by 7 days
    if (retDate <= depDate) {
      retDate = new Date(depDate);
      retDate.setDate(depDate.getDate() + 7);
    }

    const duration = Math.max(1, Math.round((retDate.getTime() - depDate.getTime()) / (1000 * 60 * 60 * 24)));
    const depFormatted = depDate.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
    const retFormatted = retDate.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });

    const depYear = newIso.split('-')[0] || '2025';
    const retYearIso = retDate.toISOString().split('T')[0];
    const retYear = retYearIso.split('-')[0] || depYear;
    const depLegTime = getLegTimeOnly(tripDetails.departureLegInfo || '', 'Morning leg');
    const retLegTime = getLegTimeOnly(tripDetails.returnLegInfo || '', 'Evening leg');

    updateTripDetails({
      departureDateIso: newIso,
      returnDateIso: retYearIso,
      departureDate: depFormatted,
      returnDate: retFormatted,
      departureLegInfo: `${depYear} • ${depLegTime}`,
      returnLegInfo: `${retYear} • ${retLegTime}`,
      durationDays: duration,
    });
  };

  const handleReturnDateChange = (newIso: string) => {
    if (!newIso) return;
    let retDate = new Date(newIso);
    const depDate = new Date(tripDetails.departureDateIso || newIso);

    if (retDate <= depDate) {
      retDate = new Date(depDate);
      retDate.setDate(depDate.getDate() + 1);
    }

    const duration = Math.max(1, Math.round((retDate.getTime() - depDate.getTime()) / (1000 * 60 * 60 * 24)));
    const retFormatted = retDate.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });

    const retYearIso = retDate.toISOString().split('T')[0];
    const retYear = retYearIso.split('-')[0] || '2025';
    const retLegTime = getLegTimeOnly(tripDetails.returnLegInfo || '', 'Evening leg');

    updateTripDetails({
      returnDateIso: retYearIso,
      returnDate: retFormatted,
      returnLegInfo: `${retYear} • ${retLegTime}`,
      durationDays: duration,
    });
  };

  const cycleDepartureLeg = () => {
    const curTime = getLegTimeOnly(tripDetails.departureLegInfo || '', 'Morning leg');
    const nextIdx = (legTimes.indexOf(curTime) + 1) % legTimes.length;
    const year = tripDetails.departureDateIso.split('-')[0] || '2025';
    updateTripDetails({ departureLegInfo: `${year} • ${legTimes[nextIdx]}` });
  };

  const cycleReturnLeg = () => {
    const curTime = getLegTimeOnly(tripDetails.returnLegInfo || '', 'Evening leg');
    const nextIdx = (legTimes.indexOf(curTime) + 1) % legTimes.length;
    const year = tripDetails.returnDateIso.split('-')[0] || '2025';
    updateTripDetails({ returnLegInfo: `${year} • ${legTimes[nextIdx]}` });
  };

  const formatTripDateDisplay = (iso: string) => {
    if (!iso) return 'Select Date';
    const parts = iso.split('-');
    if (parts.length === 3) {
      const y = parseInt(parts[0], 10);
      const m = parseInt(parts[1], 10) - 1;
      const d = parseInt(parts[2], 10);
      const date = new Date(Date.UTC(y, m, d));
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${days[date.getUTCDay()]}, ${months[date.getUTCMonth()]} ${d}`;
    }
    return iso;
  };

  const handleOpenDepPicker = () => {
    if (depInputRef.current) {
      if (typeof depInputRef.current.showPicker === 'function') {
        try {
          depInputRef.current.showPicker();
        } catch {
          depInputRef.current.focus();
        }
      } else {
        depInputRef.current.focus();
      }
    }
  };

  const handleOpenRetPicker = () => {
    if (retInputRef.current) {
      if (typeof retInputRef.current.showPicker === 'function') {
        try {
          retInputRef.current.showPicker();
        } catch {
          retInputRef.current.focus();
        }
      } else {
        retInputRef.current.focus();
      }
    }
  };

  // Dynamic real-time weather badge & visa verdict
  const activeDestinations =
    tripDetails.destinations && tripDetails.destinations.length > 0
      ? tripDetails.destinations
      : splitDestinationsString(tripDetails.destination || destQuery);
  const activeResolved = resolveDestinationData(
    activeDestinations.length > 0 ? activeDestinations : destQuery,
    activeScope
  );
  const seasonBadgeText =
    activeResolved.seasonSummary ||
    getSeasonDescription(activeDestinations[0] || tripDetails.destination, tripDetails.departureDateIso);
  const visaVerdictText =
    activeResolved.visaStatus ||
    getMultiDestinationVisaVerdict(activeDestinations, activeScope);

  const partyButtons: { type: PartyType; label: string; icon: string }[] = [
    { type: 'solo', label: 'Solo', icon: 'person' },
    { type: 'couple', label: 'Couple / Pair', icon: 'favorite' },
    { type: 'family', label: 'Family', icon: 'family_restroom' },
    { type: 'friends', label: 'Friends Group', icon: 'groups' },
  ];

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen flex flex-col antialiased">
      {/* Planner Header */}
      <PlannerHeader currentStep={1} onNavigateHome={onBackToWelcome} />

      {/* Main Content */}
      <main className="w-full pt-20 flex-1 max-w-[1280px] mx-auto px-margin-mobile sm:px-margin bg-surface">
        <div className="flex flex-col w-full relative">
          {/* Ambient Journey Path Contour SVG Background */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden select-none -z-10 opacity-60">
            <svg
              className="w-full h-full text-outline-variant"
              fill="none"
              preserveAspectRatio="none"
              viewBox="0 0 1200 900"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                className="opacity-40"
                d="M-80 180 C 240 100, 480 320, 720 180 S 1080 30, 1320 160"
                stroke="currentColor"
                strokeDasharray="6 6"
                strokeWidth="1.5"
              />
              <path
                className="opacity-30"
                d="M-40 440 C 280 490, 520 280, 840 420 S 1120 540, 1360 410"
                stroke="currentColor"
                strokeDasharray="4 6"
                strokeWidth="1.25"
              />
              <circle className="opacity-70" cx="720" cy="180" fill="#E87524" r="4" />
              <circle className="opacity-60" cx="840" cy="420" fill="#7A2E2E" r="3.5" />
            </svg>
          </div>

          {/* Progress Stepper Header */}
          <ProgressStepper currentStep={1} />

          {/* Editorial Section Title & Intro */}
          <section className="max-w-4xl mx-auto w-full pt-space-md pb-space-lg text-center">
            <div className="inline-flex items-center gap-space-xs px-space-md py-1 rounded-full bg-surface-container text-on-secondary-fixed-variant mb-space-sm shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-container" />
              <span className="font-label-caption text-label-caption tracking-wider font-semibold uppercase">
                Step 1 of 5 • Basic Journey Details
              </span>
            </div>
            <h1 className="font-display-hero text-headline-lg sm:text-display-hero text-on-surface tracking-tight mb-space-xs">
              Where are you going?
            </h1>
            <p className="font-body-lg text-body-md sm:text-body-lg text-on-surface-variant max-w-xl mx-auto">
              Let&rsquo;s plan your journey. Tell us where your story starts and where you wish to explore.
            </p>
          </section>

          {/* Main Planner Form Card */}
          <section className="max-w-4xl mx-auto w-full mb-space-xl">
            <div className="bg-surface-container-lowest rounded-xl shadow-md p-space-lg sm:p-space-xl border border-outline-variant/30">
              <div className="space-y-space-xl">
                {/* 0. SCOPE TOGGLE: Domestic (Within India) vs International */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 sm:p-4 rounded-2xl bg-surface-container-low border border-outline-variant/30">
                  <div className="flex items-center gap-2.5">
                    <span className="material-symbols-outlined text-primary text-[22px]">
                      travel_explore
                    </span>
                    <div>
                      <span className="font-label-md text-label-md font-bold text-on-surface block">
                        Travel Scope
                      </span>
                      <span className="font-label-caption text-label-caption text-on-surface-variant">
                        {activeScope === 'DOMESTIC'
                          ? 'Domestic Travel: Indian states, UTs & 4,198 rail hubs/cities'
                          : 'International: 250 sovereign countries & major global circuits'}
                      </span>
                    </div>
                  </div>

                  <div
                    className="inline-flex p-1 rounded-xl bg-surface-container-high/90 border border-outline-variant/40 shadow-inner self-start sm:self-auto"
                    role="group"
                    aria-label="Scope Toggle"
                  >
                    <button
                      type="button"
                      id="btn-scope-domestic"
                      onClick={() => handleToggleScope('DOMESTIC')}
                      className={`px-4 py-2 rounded-lg font-label-md text-label-md font-semibold flex items-center gap-2 transition-all cursor-pointer ${
                        activeScope === 'DOMESTIC'
                          ? 'bg-primary text-on-primary shadow-sm font-bold ring-2 ring-primary/20'
                          : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container'
                      }`}
                    >
                      <span className="text-[16px]">🇮🇳</span>
                      <span>Domestic (Within India)</span>
                    </button>
                    <button
                      type="button"
                      id="btn-scope-international"
                      onClick={() => handleToggleScope('INTERNATIONAL')}
                      className={`px-4 py-2 rounded-lg font-label-md text-label-md font-semibold flex items-center gap-2 transition-all cursor-pointer ${
                        activeScope === 'INTERNATIONAL'
                          ? 'bg-primary text-on-primary shadow-sm font-bold ring-2 ring-primary/20'
                          : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container'
                      }`}
                    >
                      <span className="text-[16px]">✈️</span>
                      <span>International</span>
                    </button>
                  </div>
                </div>

                {/* 1. ORIGIN & DESTINATION SPLIT ROW WITH AUTOCOMPLETE */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-space-lg relative">
                  {/* Origin Box */}
                  <div className="flex flex-col space-y-space-xs relative" ref={originRef}>
                    <div className="flex items-center justify-between">
                      <label
                        className="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5"
                        htmlFor="origin-input"
                      >
                        <span className="material-symbols-outlined text-primary-container text-[18px]">
                          flight_takeoff
                        </span>
                        {activeScope === 'DOMESTIC'
                          ? 'Starting From (Origin City, Rail Hub, or Airport)'
                          : 'Starting From (Origin Airport)'}
                      </label>
                      <span className="font-label-caption text-label-caption text-outline">
                        {activeScope === 'DOMESTIC'
                          ? 'Any Indian City or Hub'
                          : 'IATA Airport Only'}
                      </span>
                    </div>

                    <div className="relative flex items-center">
                      <input
                        id="origin-input"
                        type="text"
                        value={originQuery}
                        onChange={(e) => {
                          setOriginQuery(e.target.value);
                          updateTripDetails({ origin: e.target.value });
                          setShowOriginDropdown(true);
                        }}
                        onFocus={() => setShowOriginDropdown(true)}
                        placeholder={
                          activeScope === 'DOMESTIC'
                            ? 'Search any Indian city, town, station, or airport...'
                            : 'Search departure airport (e.g. DEL, BOM, BLR, CCU)...'
                        }
                        className="w-full h-13 pl-11 pr-10 py-3 text-on-surface font-body-md text-body-md rounded-lg focus:outline-none focus:bg-surface focus:shadow-[0_0_0_2px_#e87524] transition-all border border-outline-variant/40 bg-surface-container-low"
                      />
                      <span className="material-symbols-outlined absolute left-3.5 text-on-surface-variant text-[20px]">
                        trip_origin
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          const temp = tripDetails.origin;
                          updateTripDetails({
                            origin: tripDetails.destination,
                            destination: temp,
                          });
                          setOriginQuery(tripDetails.destination);
                          setDestQuery(temp);
                        }}
                        className="absolute right-3 text-outline hover:text-primary transition-colors cursor-pointer"
                        title="Swap Origin and Destination"
                      >
                        <span className="material-symbols-outlined text-[18px]">sync_alt</span>
                      </button>
                    </div>

                    {/* Autocomplete Dropdown for Origin */}
                    {showOriginDropdown && (
                      <div className="absolute top-[80px] left-0 right-0 z-30 bg-surface-container-lowest rounded-xl shadow-xl border border-outline-variant/40 max-h-56 overflow-y-auto divide-y divide-outline-variant/20">
                        {filteredOrigins.length > 0 ? (
                          filteredOrigins.map((opt) => (
                            <button
                              key={opt.id}
                              type="button"
                              onClick={() => handleSelectOrigin(opt)}
                              className="w-full px-4 py-2.5 text-left hover:bg-surface-container-low transition-colors flex items-center justify-between cursor-pointer"
                            >
                              <div className="flex flex-col pr-2">
                                <span className="font-label-md text-label-md font-semibold text-on-surface">
                                  {opt.name}
                                </span>
                                <span className="font-label-caption text-label-caption text-on-surface-variant">
                                  {opt.detail}
                                </span>
                              </div>
                              <span
                                className={`font-label-caption text-label-caption px-2 py-0.5 rounded font-mono ${
                                  opt.type === 'AIRPORT'
                                    ? 'bg-primary-fixed text-on-primary-fixed font-bold'
                                    : 'bg-surface-container text-outline'
                                }`}
                              >
                                {opt.code ? opt.code : 'CITY'}
                              </span>
                            </button>
                          ))
                        ) : (
                          <div className="px-4 py-3 text-on-surface-variant font-label-caption text-label-caption">
                            {activeScope === 'DOMESTIC'
                              ? 'No matching Indian cities found. Type custom city name.'
                              : 'Restricted strictly to Indian commercial departure airports (DEL, BOM, BLR, etc.).'}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Quick Origins */}
                    <div className="flex flex-wrap items-center gap-space-xs pt-1">
                      <span className="font-label-caption text-label-caption text-outline">
                        Frequent:
                      </span>
                      {activeScope === 'DOMESTIC'
                        ? [
                            { name: 'New Delhi (DEL)', city: 'Delhi' },
                            { name: 'Mumbai (BOM)', city: 'Mumbai' },
                            { name: 'Bengaluru (BLR)', city: 'Bengaluru' },
                            { name: 'Kolkata (CCU)', city: 'Kolkata' },
                            { name: 'Jaipur (JAI)', city: 'Jaipur' },
                          ].map((hub) => (
                            <button
                              key={hub.name}
                              type="button"
                              onClick={() => {
                                updateTripDetails({ origin: hub.name });
                                setOriginQuery(hub.name);
                              }}
                              className="px-2.5 py-1 rounded-full bg-surface-container text-on-surface font-label-caption text-label-caption hover:bg-surface-container-high transition-colors cursor-pointer"
                            >
                              {hub.name}
                            </button>
                          ))
                        : INDIAN_ORIGIN_AIRPORTS.slice(0, 4).map((a) => (
                            <button
                              key={a.code}
                              type="button"
                              onClick={() => {
                                updateTripDetails({ origin: a.label });
                                setOriginQuery(a.label);
                              }}
                              className="px-2.5 py-1 rounded-full bg-surface-container text-on-surface font-label-caption text-label-caption hover:bg-surface-container-high transition-colors cursor-pointer"
                            >
                              {a.city} ({a.code})
                            </button>
                          ))}
                    </div>
                  </div>

                  {/* Destination Box */}
                  <div className="flex flex-col space-y-space-xs relative" ref={destRef}>
                    <div className="flex items-center justify-between">
                      <label
                        className="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5"
                        htmlFor="destination-input"
                      >
                        <span className="material-symbols-outlined text-on-secondary-fixed-variant text-[18px]">
                          location_on
                        </span>
                        {activeScope === 'DOMESTIC'
                          ? 'Going To (State, UT, or Region)'
                          : 'Going To (Destination)'}
                      </label>
                      {visaVerdictText ? (
                        <span className="font-label-caption text-label-caption text-on-secondary-fixed-variant font-semibold bg-secondary-fixed/50 px-2 py-0.5 rounded-full">
                          {visaVerdictText}
                        </span>
                      ) : null}
                    </div>

                    {/* Selected Destinations Interactive Chips */}
                    {selectedDestinations.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-0.5 pb-1">
                        {selectedDestinations.map((destName, idx) => {
                          const cleanName = destName
                            .replace(/\s*\([^)]*\).*/, '')
                            .replace(/,\s*India$/i, '')
                            .replace(/\s*Circuit$/i, '')
                            .trim();
                          return (
                            <span
                              key={`${destName}-${idx}`}
                              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-on-surface font-label-md text-label-md shadow-xs"
                            >
                              <span className="material-symbols-outlined text-[15px] text-primary">
                                {activeScope === 'DOMESTIC' ? 'location_city' : 'public'}
                              </span>
                              <span className="font-semibold text-on-surface">{cleanName}</span>
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleRemoveDestination(idx);
                                }}
                                className="w-4 h-4 ml-0.5 rounded-full hover:bg-primary/20 flex items-center justify-center text-outline hover:text-on-surface cursor-pointer transition-colors"
                                title="Remove destination"
                                aria-label="Remove destination"
                              >
                                <span className="material-symbols-outlined text-[13px] leading-none">close</span>
                              </button>
                            </span>
                          );
                        })}

                        <button
                          type="button"
                          onClick={() => {
                            setIsAddingDestination(true);
                            setDestQuery('');
                            setShowDestDropdown(true);
                            destRef.current?.querySelector('input')?.focus();
                          }}
                          className={`inline-flex items-center gap-1 px-3 py-1 rounded-full font-label-caption text-label-caption font-semibold transition-colors cursor-pointer border ${
                            isAddingDestination
                              ? 'bg-primary text-on-primary border-primary'
                              : 'bg-surface-container text-primary hover:bg-surface-container-high border-outline-variant/50'
                          }`}
                        >
                          <span className="material-symbols-outlined text-[14px]">add</span>
                          {activeScope === 'DOMESTIC' ? 'Add Another State/UT/City' : 'Add Another Country'}
                        </button>
                      </div>
                    )}

                    <div className="relative flex items-center">
                      <input
                        id="destination-input"
                        type="text"
                        value={destQuery}
                        onChange={(e) => {
                          setDestQuery(e.target.value);
                          if (!isAddingDestination) {
                            updateTripDetails({ destination: e.target.value });
                          }
                          setShowDestDropdown(true);
                        }}
                        onFocus={() => setShowDestDropdown(true)}
                        placeholder={
                          isAddingDestination
                            ? activeScope === 'DOMESTIC'
                              ? 'Type and select Indian state, UT, or city to add...'
                              : 'Type and select sovereign country to add...'
                            : activeScope === 'DOMESTIC'
                            ? 'Search Indian state, UT, or region (e.g. Rajasthan, Kerala)...'
                            : 'Search sovereign country or circuit (e.g. Norway, Japan)...'
                        }
                        className="w-full h-13 pl-11 pr-10 py-3 text-on-surface font-body-md text-body-md rounded-lg focus:outline-none focus:bg-surface focus:shadow-[0_0_0_2px_#e87524] transition-all border border-outline-variant/40 bg-surface-container-low"
                      />
                      <span className="material-symbols-outlined absolute left-3.5 text-on-secondary-fixed-variant text-[20px]">
                        near_me
                      </span>
                      <button
                        type="button"
                        className="absolute right-3 text-outline hover:text-primary transition-colors cursor-pointer"
                        title="Explore regions"
                        onClick={() => setShowDestDropdown(!showDestDropdown)}
                      >
                        <span className="material-symbols-outlined text-[18px]">map</span>
                      </button>
                    </div>

                    {/* Autocomplete Dropdown for Destination */}
                    {showDestDropdown && (
                      <div className="absolute top-[80px] left-0 right-0 z-30 bg-surface-container-lowest rounded-xl shadow-xl border border-outline-variant/40 max-h-64 overflow-y-auto divide-y divide-outline-variant/20">
                        {filteredDestinations.length > 0 ? (
                          filteredDestinations.map((dest) => (
                            <button
                              key={dest.id}
                              type="button"
                              onClick={() => handleSelectDestination(dest.id)}
                              className="w-full px-4 py-2.5 text-left hover:bg-surface-container-low transition-colors flex items-center justify-between cursor-pointer"
                            >
                              <div className="flex flex-col pr-2">
                                <span className="font-label-md text-label-md font-semibold text-on-surface">
                                  {dest.title}
                                </span>
                                <span className="font-label-caption text-label-caption text-on-surface-variant">
                                  {dest.subtitle}
                                  {dest.visaStatus ? ` • ${dest.visaStatus}` : ''}
                                </span>
                              </div>
                              <span
                                className={`font-label-caption text-label-caption px-2 py-0.5 rounded font-semibold whitespace-nowrap ${
                                  dest.scope === 'DOMESTIC'
                                    ? 'bg-secondary-container text-on-secondary-container'
                                    : 'bg-primary-fixed text-on-primary-fixed-variant'
                                }`}
                              >
                                {dest.scope}
                              </span>
                            </button>
                          ))
                        ) : (
                          <div className="px-4 py-3 text-on-surface-variant font-label-caption text-label-caption">
                            {activeScope === 'DOMESTIC'
                              ? 'No matching Indian states or regions found. Please choose an Indian state or UT.'
                              : `Press Continue or select to explore ${destQuery}`}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Featured Destination Inspirations */}
                    <div className="flex flex-wrap items-center gap-space-xs pt-1">
                      <span className="font-label-caption text-label-caption text-outline">
                        Featured:
                      </span>
                      {(activeScope === 'DOMESTIC'
                        ? [
                            { id: 'rajasthan', label: 'Rajasthan Royals' },
                            { id: 'kerala', label: 'Kerala Backwaters' },
                            { id: 'ladakh', label: 'Ladakh Passes' },
                            { id: 'goa', label: 'Goa Beaches' },
                            { id: 'himachal-pradesh', label: 'Himachal Valleys' },
                            { id: 'kashmir', label: 'Kashmir Meadows' },
                          ]
                        : [
                            { id: 'norway', label: 'Norway (Fjords)' },
                            { id: 'japan', label: 'Japan (Autumn Trail)' },
                            { id: 'switzerland', label: 'Switzerland (Alps)' },
                            { id: 'italy', label: 'Italy Circuit' },
                            { id: 'france', label: 'France (Riviera)' },
                            { id: 'iceland', label: 'Iceland (Ring Road)' },
                          ]
                      ).map((c) => {
                        const isCurrent = tripDetails.destination.toLowerCase().includes(c.id);
                        return (
                          <button
                            key={c.id}
                            type="button"
                            onClick={() => handleSelectDestination(c.id)}
                            className={`px-2.5 py-1 rounded-full font-label-caption text-label-caption transition-colors cursor-pointer ${
                              isCurrent
                                ? 'bg-primary-fixed text-on-primary-fixed-variant font-semibold'
                                : 'bg-surface-container text-on-surface hover:bg-surface-container-high'
                            }`}
                          >
                            {c.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* 2. INTERACTIVE TRAVEL DATES & DURATION RECONCILIATION */}
                <div className="flex flex-col space-y-space-sm pt-space-xs">
                  <div className="flex flex-wrap items-center justify-between gap-space-xs">
                    <div className="flex items-center gap-space-xs">
                      <span className="material-symbols-outlined text-primary-container text-[20px]">
                        calendar_month
                      </span>
                      <span className="font-label-md text-label-md text-on-surface font-semibold">
                        Travel Window &amp; Dates
                      </span>
                    </div>

                    {/* Dynamic Real-time Seasonal Quality Indicator */}
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-fixed text-on-secondary-fixed-variant font-label-caption text-label-caption font-semibold shadow-xs">
                      <span className="material-symbols-outlined text-[14px]">wb_sunny</span>
                      {seasonBadgeText}
                    </div>
                  </div>

                  {/* Date Selector Panel */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-sm items-stretch">
                    {/* Departure & Return Date Segment */}
                    <div className="lg:col-span-8 bg-surface-container-low rounded-xl p-3.5 sm:p-space-md flex flex-col sm:flex-row items-center justify-between gap-3 border border-outline-variant/30 min-w-0 shadow-xs">
                      {/* Departure Date with interactive picker */}
                      <div
                        role="button"
                        tabIndex={0}
                        onClick={handleOpenDepPicker}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleOpenDepPicker();
                          }
                        }}
                        className="relative w-full sm:w-auto sm:flex-1 min-w-0 flex items-center gap-2.5 sm:gap-3 cursor-pointer group rounded-lg hover:bg-surface-container-high/40 p-1 -m-1 transition-colors select-none"
                        title="Click to pick departure date"
                      >
                        <div
                          className="w-10 h-10 rounded-lg bg-surface-container-lowest flex items-center justify-center text-primary-container shadow-sm shrink-0 group-hover:scale-105 transition-transform"
                        >
                          <span className="material-symbols-outlined text-[20px]">flight_takeoff</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="block font-label-caption text-label-caption text-outline uppercase font-semibold truncate">
                            Departure Date
                          </span>
                          <span className="block font-headline-sm text-headline-sm text-on-surface truncate">
                            {formatTripDateDisplay(tripDetails.departureDateIso)}
                          </span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              cycleDepartureLeg();
                            }}
                            className="relative z-20 block font-body-sm text-body-sm text-primary hover:underline text-left cursor-pointer truncate max-w-full"
                            title="Click to cycle departure leg preference"
                          >
                            {`${tripDetails.departureDateIso.split('-')[0] || '2025'} • ${getLegTimeOnly(tripDetails.departureLegInfo || '', 'Morning leg')}`}
                          </button>
                        </div>
                        {/* Hidden accessible native date picker */}
                        <input
                          ref={depInputRef}
                          id="dep-date-picker"
                          aria-label="Departure Date"
                          type="date"
                          value={tripDetails.departureDateIso}
                          onChange={(e) => handleDepartureDateChange(e.target.value)}
                          className="sr-only"
                          tabIndex={-1}
                        />
                      </div>

                      {/* Journey Duration Graphic */}
                      <div className="flex flex-col items-center justify-center px-1 shrink-0 py-1 sm:py-0 my-1 sm:my-0 select-none">
                        <span className="font-label-caption text-label-caption text-primary font-bold px-2.5 py-0.5 rounded-full bg-primary-fixed whitespace-nowrap">
                          {tripDetails.durationDays} Days • {Math.max(1, tripDetails.durationDays - 1)} Nights
                        </span>
                        <div className="w-12 sm:w-16 h-0.5 border-t border-dashed border-primary-container mt-1" />
                      </div>

                      {/* Return Date with interactive picker */}
                      <div
                        role="button"
                        tabIndex={0}
                        onClick={handleOpenRetPicker}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleOpenRetPicker();
                          }
                        }}
                        className="relative w-full sm:w-auto sm:flex-1 min-w-0 flex items-center gap-2.5 sm:gap-3 justify-between sm:justify-end text-left sm:text-right cursor-pointer group rounded-lg hover:bg-surface-container-high/40 p-1 -m-1 transition-colors select-none"
                        title="Click to pick return date"
                      >
                        <div className="flex-1 min-w-0 order-1">
                          <span className="block font-label-caption text-label-caption text-outline uppercase font-semibold truncate">
                            Return Journey
                          </span>
                          <span className="block font-headline-sm text-headline-sm text-on-surface truncate">
                            {formatTripDateDisplay(tripDetails.returnDateIso)}
                          </span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              cycleReturnLeg();
                            }}
                            className="relative z-20 block font-body-sm text-body-sm text-primary hover:underline text-left sm:text-right w-full cursor-pointer truncate max-w-full"
                            title="Click to cycle return leg preference"
                          >
                            {`${tripDetails.returnDateIso.split('-')[0] || '2025'} • ${getLegTimeOnly(tripDetails.returnLegInfo || '', 'Evening leg')}`}
                          </button>
                        </div>
                        <div
                          className="w-10 h-10 rounded-lg bg-surface-container-lowest flex items-center justify-center text-on-secondary-fixed-variant shadow-sm shrink-0 group-hover:scale-105 transition-transform order-2"
                        >
                          <span className="material-symbols-outlined text-[20px]">flight_land</span>
                        </div>
                        {/* Hidden accessible native date picker */}
                        <input
                          ref={retInputRef}
                          id="ret-date-picker"
                          aria-label="Return Date"
                          type="date"
                          value={tripDetails.returnDateIso}
                          min={tripDetails.departureDateIso}
                          onChange={(e) => handleReturnDateChange(e.target.value)}
                          className="sr-only"
                          tabIndex={-1}
                        />
                      </div>
                    </div>

                    {/* Date Flexibility Toggle Card */}
                    <div className="lg:col-span-4 bg-surface-container rounded-xl p-space-md flex flex-col justify-center border border-outline-variant/30 shadow-xs">
                      <label className="flex items-center gap-3 cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={tripDetails.flexibleDates}
                          onChange={(e) => updateTripDetails({ flexibleDates: e.target.checked })}
                          className="w-5 h-5 rounded accent-primary-container cursor-pointer shrink-0"
                        />
                        <div className="flex flex-col min-w-0">
                          <span className="font-label-md text-label-md text-on-surface font-semibold truncate">
                            Flexible on dates
                          </span>
                          <span className="font-body-sm text-body-sm text-on-surface-variant truncate">
                            &plusmn; 3 days for scenic connections
                          </span>
                        </div>
                      </label>
                      <div className="mt-2 pl-8">
                        <span className="font-label-caption text-label-caption text-primary-container font-medium block">
                          {tripDetails.flexibleDates
                            ? 'Calculates lowest fares & calmest travel days'
                            : 'Strict calendar departure and arrival locked'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3. TRAVELERS & PARTY TYPE */}
                <div className="flex flex-col space-y-space-md pt-space-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-space-xs">
                      <span className="material-symbols-outlined text-primary-container text-[20px]">
                        group
                      </span>
                      <span className="font-label-md text-label-md text-on-surface font-semibold">
                        Travelers &amp; Journey Dynamic
                      </span>
                    </div>
                    <span className="font-label-caption text-label-caption text-outline">
                      Pacing customized to party composition
                    </span>
                  </div>

                  {/* Trip Dynamic Pill Selectors */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-space-sm" id="party-type-group">
                    {partyButtons.map((btn) => {
                      const isActive = tripDetails.partyType === btn.type;
                      return (
                        <button
                          key={btn.type}
                          type="button"
                          onClick={() => {
                            updateTripDetails({
                              partyType: btn.type,
                              adults: btn.type === 'solo' ? 1 : btn.type === 'couple' ? 2 : Math.max(2, tripDetails.adults),
                            });
                          }}
                          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-label-md text-label-md transition-all cursor-pointer ${
                            isActive
                              ? 'bg-primary-container text-on-primary shadow-sm font-semibold'
                              : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
                          }`}
                        >
                          <span className="material-symbols-outlined text-[18px]">
                            {btn.icon}
                          </span>
                          <span>{btn.label}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Structured Traveler Stepper Counter Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
                    <CounterStepper
                      label="Adults"
                      subLabel="Age 12+ years"
                      value={tripDetails.adults}
                      min={1}
                      max={12}
                      onChange={(adults) => updateTripDetails({ adults })}
                    />
                    <CounterStepper
                      label="Children"
                      subLabel="Age 2–11 years"
                      value={tripDetails.children}
                      min={0}
                      max={8}
                      onChange={(children) => updateTripDetails({ children })}
                    />
                    <CounterStepper
                      label="Infants"
                      subLabel="Under 2 years"
                      value={tripDetails.infants}
                      min={0}
                      max={4}
                      onChange={(infants) => updateTripDetails({ infants })}
                    />
                  </div>
                </div>

                {/* 4. EDITORIAL CONTEXT CALLOUT / CONCIERGE TIP */}
                <div className="p-space-md rounded-lg bg-surface-container flex items-start gap-space-md border border-outline-variant/20">
                  <div className="w-8 h-8 rounded-full bg-primary-fixed text-primary flex items-center justify-center shrink-0 mt-0.5">
                    <span className="material-symbols-outlined text-[18px]">lightbulb</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-label-md text-label-md text-on-surface font-semibold mb-0.5">
                      Safarnama Editorial Insight
                    </h4>
                    <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                      Traveling as a {tripDetails.partyType} in {tripDetails.departureDate.split(',')[1]?.trim() || 'October'} offers tailored logistics for {tripDetails.destination.split(',')[0]}. Safarnama balances iconic highlights with mindful, unhurried stays at a cadence calibrated to your group size ({tripDetails.adults + tripDetails.children + tripDetails.infants} traveler{tripDetails.adults + tripDetails.children + tripDetails.infants !== 1 ? 's' : ''}).
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Footer Bar */}
              <div className="mt-space-xl pt-space-lg flex flex-col sm:flex-row items-center justify-between gap-space-md border-t border-outline-variant/30">
                {/* Autosave Status Badge */}
                <div className="flex items-center gap-2 text-on-surface-variant font-label-caption text-label-caption order-3 sm:order-1">
                  <span className="material-symbols-outlined text-[16px] text-primary">
                    cloud_done
                  </span>
                  <span>Draft synchronized with your Safarnama account</span>
                </div>

                {/* Navigation Buttons */}
                <div className="flex items-center gap-space-md w-full sm:w-auto order-1 sm:order-2">
                  <button
                    type="button"
                    onClick={onBackToWelcome}
                    className="w-1/2 sm:w-auto px-space-lg py-3 rounded-lg font-label-md text-label-md text-on-surface bg-surface-container hover:bg-surface-container-high transition-colors text-center cursor-pointer"
                  >
                    &larr; Back
                  </button>
                  <button
                    type="button"
                    onClick={handleContinue}
                    className="w-1/2 sm:w-auto px-space-xl py-3 rounded-lg font-label-md text-label-md text-on-primary bg-primary-container hover:bg-primary transition-all shadow-md flex items-center justify-center gap-2 group text-center cursor-pointer active:scale-98"
                  >
                    <span>Continue to Destinations</span>
                    <span className="material-symbols-outlined text-[18px] group-hover:translate-x-1 transition-transform">
                      arrow_forward
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <PlannerFooter />
    </div>
  );
};
