import type { RouteStop, TripDetailsState } from '../types/trip';
import { resolveSingleDestinationData, splitDestinationsString } from './destinationsRegistry';

export interface MustVisitOption {
  name: string;
  region: string;
  kind: 'Route stop' | 'Curated place';
}

const normalize = (value: string) => value.trim().toLocaleLowerCase();

export const getMustVisitOptions = (
  details: TripDetailsState,
  routeStops: RouteStop[]
): MustVisitOption[] => {
  const options: MustVisitOption[] = [];
  const seen = new Set<string>();
  const add = (name: string, region: string, kind: MustVisitOption['kind']) => {
    const key = normalize(name);
    if (!key || seen.has(key)) return;
    seen.add(key);
    options.push({ name: name.trim(), region: region.trim(), kind });
  };

  routeStops.forEach((stop) => add(stop.name, stop.region || stop.country, 'Route stop'));

  const selectedDestinations = details.destinations?.length
    ? details.destinations
    : splitDestinationsString(details.destination);

  selectedDestinations.forEach((destination) => {
    const curated = resolveSingleDestinationData(destination, details.scope);
    curated.defaultStops.forEach((stop) => add(stop.name, stop.region || stop.country, 'Curated place'));
    curated.suggestions.forEach((suggestion) => add(suggestion.name, suggestion.region, 'Curated place'));
  });

  return options;
};