export type PartyType = 'solo' | 'couple' | 'family' | 'friends';

export interface RouteStop {
  id: string;
  name: string;
  country: string;
  region?: string;
  nights: number;
  role: string;
  imageUrl: string;
  imageAlt?: string;
  transitToNext?: {
    mode: string;
    icon: string;
    duration: string;
    title: string;
  };
}

export interface DestinationSuggestion {
  id: string;
  name: string;
  region: string;
  tag: string;
  description: string;
  imageUrl: string;
  imageAlt?: string;
  actionLabel: string;
  isDayTrip?: boolean;
}

export interface ContextualCityItem {
  id: string;
  name: string;
  region: string;
  country: string;
  isPopular: boolean;
  role: string;
  imageUrl: string;
  imageAlt?: string;
}

export interface TripDetailsState {
  scope?: 'DOMESTIC' | 'INTERNATIONAL';
  origin: string;
  destination: string;
  departureDate: string; // e.g. "Sat, Oct 18, 2025"
  returnDate: string; // e.g. "Tue, Oct 28, 2025"
  departureDateIso: string; // e.g. "2025-10-18"
  returnDateIso: string; // e.g. "2025-10-28"
  departureLegInfo: string; // "Morning leg"
  returnLegInfo: string; // "Evening leg"
  durationDays: number;
  flexibleDates: boolean;
  partyType: PartyType;
  adults: number;
  children: number;
  infants: number;
}

export interface TripPlanningState {
  tripDetails: TripDetailsState;
  destinations: RouteStop[];
  editorialNote?: string;
}
