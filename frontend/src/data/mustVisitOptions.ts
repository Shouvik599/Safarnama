import type { RouteStop, TripDetailsState } from '../types/trip';
import { resolveSingleDestinationData, splitDestinationsString } from './destinationsRegistry';
import generatedCountries from './generated_countries.json';
import attractionCatalog from './attractions.json';

export interface AttractionCatalogEntry {
  attraction_id: string;
  name: string;
  city: string;
  region?: string | null;
  country: string;
  country_code: string;
  category: string;
  description: string;
}

export interface MustVisitOption {
  name: string;
  region: string;
  kind: 'Attraction';
  description: string;
}

const normalize = (value: string) =>
  value
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLocaleLowerCase();

const countryCodeByName = new Map(
  (generatedCountries as { code: string; name: string }[]).map((country) => [
    normalize(country.name),
    country.code.toUpperCase(),
  ])
);
countryCodeByName.set('india', 'IN');

const getRouteCountryCodes = (details: TripDetailsState, routeStops: RouteStop[]): Set<string> => {
  const countryNames = new Set<string>();
  routeStops.forEach((stop) => {
    if (stop.country && stop.country.toLocaleLowerCase() !== 'international') {
      countryNames.add(stop.country);
    }
  });

  const selectedDestinations = details.destinations?.length
    ? details.destinations
    : splitDestinationsString(details.destination);
  selectedDestinations.forEach((destination) => {
    const resolved = resolveSingleDestinationData(destination, details.scope);
    resolved.defaultStops.forEach((stop) => {
      if (stop.country && stop.country.toLocaleLowerCase() !== 'international') {
        countryNames.add(stop.country);
      }
    });
  });

  const countryCodes = new Set<string>();
  countryNames.forEach((countryName) => {
    const countryCode = countryCodeByName.get(normalize(countryName));
    if (countryCode) countryCodes.add(countryCode);
  });
  if (details.scope === 'DOMESTIC') countryCodes.add('IN');
  return countryCodes;
};

export const getMustVisitOptions = (
  details: TripDetailsState,
  routeStops: RouteStop[],
  catalogEntries: AttractionCatalogEntry[] = (attractionCatalog.entries ?? []) as AttractionCatalogEntry[]
): MustVisitOption[] => {
  if (routeStops.length === 0) return [];

  const routeCities = new Map<string, number>();
  routeStops.forEach((stop, index) => {
    const city = normalize(stop.name);
    if (city && !routeCities.has(city)) routeCities.set(city, index);
  });

  const selectedCountries = getRouteCountryCodes(details, routeStops);
  if (selectedCountries.size === 0) return [];

  return catalogEntries
    .filter((entry) => {
      const city = normalize(entry.city);
      return (
        entry.category === 'ATTRACTION' &&
        routeCities.has(city) &&
        selectedCountries.has(entry.country_code.toUpperCase()) &&
        normalize(entry.name) !== city
      );
    })
    .sort((left, right) => {
      const cityOrder = routeCities.get(normalize(left.city))! - routeCities.get(normalize(right.city))!;
      return cityOrder || left.name.localeCompare(right.name);
    })
    .map((entry) => ({
      name: entry.name,
      region: [entry.city, entry.region, entry.country].filter(Boolean).join(', '),
      kind: 'Attraction' as const,
      description: entry.description,
    }));
};