import React, { useState } from 'react';
import type { TripDetailsState, RouteStop } from '../types/trip';
import { TripPlanningContext } from './TripPlanningContextDef';
import { PRECONFIGURED_CIRCUITS } from '../data/locations';
import {
  resolveDestinationData,
  resolveSingleDestinationData,
  generateScenicTransitConnector,
  splitDestinationsString,
} from '../data/destinationsRegistry';

const formatLocalIso = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
};

const formatLocalDisplay = (d: Date) => {
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${days[d.getDay()]}, ${months[d.getMonth()]} ${d.getDate()}`;
};

const createInitialTripDetails = (): TripDetailsState => {
  const now = new Date();
  const retDate = new Date(now);
  retDate.setDate(retDate.getDate() + 10);

  return {
    scope: 'INTERNATIONAL',
    origin: 'New Delhi (DEL - Indira Gandhi Intl)',
    destination: 'Kyoto, Japan (KIX - Kansai Intl / Shinkansen Rail)',
    destinations: ['Kyoto, Japan (KIX - Kansai Intl / Shinkansen Rail)'],
    departureDate: formatLocalDisplay(now),
    returnDate: formatLocalDisplay(retDate),
    departureDateIso: formatLocalIso(now),
    returnDateIso: formatLocalIso(retDate),
    departureLegInfo: `${now.getFullYear()} • Morning leg`,
    returnLegInfo: `${retDate.getFullYear()} • Evening leg`,
    durationDays: 10,
    flexibleDates: true,
    partyType: 'couple',
    adults: 2,
    children: 0,
    infants: 0,
  };
};

export const TripPlanningProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tripDetails, setTripDetails] = useState<TripDetailsState>(() => createInitialTripDetails());
  const [destinations, setDestinations] = useState<RouteStop[]>(() =>
    JSON.parse(JSON.stringify(PRECONFIGURED_CIRCUITS[0].defaultStops))
  );

  const updateTripDetails = (partial: Partial<TripDetailsState>) => {
    setTripDetails((prev) => {
      const next = { ...prev, ...partial };
      if (partial.destination !== undefined && partial.destinations === undefined) {
        next.destinations = splitDestinationsString(partial.destination);
      } else if (partial.destinations !== undefined && partial.destination === undefined) {
        next.destination = partial.destinations.join(', ');
      }
      return next;
    });
  };

  const addDestination = (stop: RouteStop) => {
    setDestinations((prev) => {
      const updated = [...prev];
      if (updated.length > 0 && !updated[updated.length - 1].transitToNext) {
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          transitToNext: generateScenicTransitConnector(
            stop.name,
            tripDetails.destination,
            tripDetails.scope
          ),
        };
      }
      return [...updated, stop];
    });
  };

  const removeDestination = (id: string) => {
    setDestinations((prev) => {
      const filtered = prev.filter((d) => d.id !== id);
      if (filtered.length > 0) {
        filtered[filtered.length - 1] = {
          ...filtered[filtered.length - 1],
          transitToNext: undefined,
        };
      }
      return filtered;
    });
  };

  const updateStopNights = (id: string, nights: number) => {
    setDestinations((prev) =>
      prev.map((stop) => (stop.id === id ? { ...stop, nights: Math.max(1, nights) } : stop))
    );
  };

  const batchUpdateStopNights = (updates: { id: string; nights: number }[]) => {
    const map = new Map(updates.map((u) => [u.id, Math.max(1, u.nights)]));
    setDestinations((prev) =>
      prev.map((stop) => (map.has(stop.id) ? { ...stop, nights: map.get(stop.id)! } : stop))
    );
  };

  const moveDestinationUp = (index: number) => {
    if (index <= 0) return;
    setDestinations((prev) => {
      const copy = [...prev];
      const temp = copy[index - 1];
      copy[index - 1] = copy[index];
      copy[index] = temp;
      return syncTransitConnectors(copy);
    });
  };

  const moveDestinationDown = (index: number) => {
    setDestinations((prev) => {
      if (index >= prev.length - 1) return prev;
      const copy = [...prev];
      const temp = copy[index + 1];
      copy[index + 1] = copy[index];
      copy[index] = temp;
      return syncTransitConnectors(copy);
    });
  };

  const seedDestination = (
    destinationQuery: string | string[],
    scopeHint?: 'DOMESTIC' | 'INTERNATIONAL'
  ) => {
    const effectiveScope = scopeHint || tripDetails.scope;
    const destItem = resolveDestinationData(destinationQuery, effectiveScope);
    if (!destItem) return;

    const rawParts = Array.isArray(destinationQuery)
      ? destinationQuery
      : splitDestinationsString(destinationQuery);

    const parts =
      rawParts.length <= 1
        ? [destItem.name]
        : rawParts.map((q) => {
            const it = resolveSingleDestinationData(q, effectiveScope);
            return it ? it.name : q;
          });

    // Calculate dates matching the destination's default duration
    const departure = tripDetails.departureDateIso
      ? new Date(tripDetails.departureDateIso)
      : new Date();
    const returnD = new Date(departure);
    returnD.setDate(departure.getDate() + destItem.defaultDurationDays);

    const depFormatted = formatLocalDisplay(departure);
    const retFormatted = formatLocalDisplay(returnD);
    const depIso = formatLocalIso(departure);
    const retIso = formatLocalIso(returnD);

    setTripDetails((prev) => ({
      ...prev,
      scope: destItem.scope,
      destination: destItem.name,
      destinations: parts,
      durationDays: destItem.defaultDurationDays,
      departureDate: depFormatted,
      returnDate: retFormatted,
      departureDateIso: depIso,
      returnDateIso: retIso,
      departureLegInfo: `${departure.getFullYear()} • Morning leg`,
      returnLegInfo: `${returnD.getFullYear()} • Evening leg`,
    }));

    setDestinations(destItem.defaultStops);
  };

  const seedCircuit = (circuitId: string) => {
    seedDestination(circuitId, tripDetails.scope);
  };

  const syncTransitConnectors = (list: RouteStop[]): RouteStop[] => {
    return list.map((stop, i) => {
      if (i === list.length - 1) {
        return { ...stop, transitToNext: undefined };
      }
      const nextStop = list[i + 1];
      return {
        ...stop,
        transitToNext:
          stop.transitToNext ||
          generateScenicTransitConnector(
            nextStop.name,
            tripDetails.destination,
            tripDetails.scope
          ),
      };
    });
  };

  const resetAll = () => {
    setTripDetails(createInitialTripDetails());
    setDestinations(JSON.parse(JSON.stringify(PRECONFIGURED_CIRCUITS[0].defaultStops)));
  };

  return (
    <TripPlanningContext.Provider
      value={{
        tripDetails,
        updateTripDetails,
        destinations,
        addDestination,
        removeDestination,
        updateStopNights,
        batchUpdateStopNights,
        moveDestinationUp,
        moveDestinationDown,
        seedCircuit,
        seedDestination,
        resetAll,
      }}
    >
      {children}
    </TripPlanningContext.Provider>
  );
};
