import type {
  ActivityPreference,
  PlannerPreferences,
  RouteStop,
  TripBudgetDraft,
  TripDetailsState,
} from '../types/trip';
import type { MustVisitOption } from './mustVisitOptions';

export interface PlanRequestDraft {
  origin: string;
  destinations: string[];
  start_date: string;
  end_date: string;
  date_mode: 'EXACT' | 'FLEXIBLE';
  flexibility_days: number;
  duration_days: number;
  adults: number;
  children: number;
  budget_inr: number;
  budget_mode: 'TOTAL' | 'PER_PERSON';
  travel_style: 'BUDGET' | 'COMFORTABLE' | 'PREMIUM' | 'LUXURY';
  pace: 'RELAXED' | 'BALANCED' | 'PACKED';
  activity_preferences: ActivityPreference[];
  must_visits: string[];
  scope?: 'DOMESTIC' | 'INTERNATIONAL';
}

export interface DraftValidationIssue {
  section: 'trip-details' | 'destinations' | 'preferences' | 'budget';
  message: string;
}

const supportedActivities: ActivityPreference[] = [
  'HISTORY_HERITAGE',
  'NATURE',
  'FOOD_EXPERIENCE',
  'ADVENTURE',
  'RELAXATION',
  'ART_CULTURE',
  'SHOPPING',
  'LOCAL_EXPERIENCE',
  'PHOTOGRAPHY',
  'NIGHTLIFE',
  'FAMILY_KIDS',
  'SPIRITUAL',
];

const isValidIsoDate = (value: string): boolean => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
};

export const validateTripDraft = (
  details: TripDetailsState,
  stops: RouteStop[],
  preferences: PlannerPreferences,
  budget: TripBudgetDraft,
  validMustVisits?: MustVisitOption[]
): DraftValidationIssue[] => {
  const issues: DraftValidationIssue[] = [];
  const startValid = isValidIsoDate(details.departureDateIso);
  const endValid = isValidIsoDate(details.returnDateIso);

  if (!details.origin.trim()) {
    issues.push({ section: 'trip-details', message: 'Add an origin city or airport.' });
  }
  if (!details.destination.trim()) {
    issues.push({ section: 'trip-details', message: 'Choose at least one destination.' });
  }
  if (!startValid || !endValid || details.returnDateIso <= details.departureDateIso) {
    issues.push({ section: 'trip-details', message: 'Choose valid departure and return dates.' });
  }
  if (
    !Number.isInteger(details.adults) ||
    details.adults < 1 ||
    details.adults > 50 ||
    !Number.isInteger(details.children) ||
    details.children < 0 ||
    details.children > 20
  ) {
    issues.push({ section: 'trip-details', message: 'Traveler counts are outside supported limits.' });
  }
  if (details.infants > 0) {
    issues.push({
      section: 'trip-details',
      message: 'The current planning request supports adults and children, but not infants.',
    });
  }

  const allocatedNights = stops.reduce((total, stop) => total + stop.nights, 0);
  if (
    stops.length === 0 ||
    stops.some((stop) => !stop.name.trim() || !Number.isInteger(stop.nights) || stop.nights < 1) ||
    allocatedNights !== details.durationDays
  ) {
    issues.push({
      section: 'destinations',
      message: 'Add route stops and reconcile their nights with the trip duration.',
    });
  }

  if (!['BUDGET', 'COMFORTABLE', 'PREMIUM', 'LUXURY'].includes(preferences.travelStyle)) {
    issues.push({ section: 'preferences', message: 'Choose a supported travel style.' });
  }
  if (!['RELAXED', 'BALANCED', 'PACKED'].includes(preferences.pace)) {
    issues.push({ section: 'preferences', message: 'Choose a supported travel pace.' });
  }
  if (
    new Set(preferences.activityPreferences).size !== preferences.activityPreferences.length ||
    preferences.activityPreferences.some((value) => !supportedActivities.includes(value))
  ) {
    issues.push({ section: 'preferences', message: 'Remove duplicate or unsupported experience interests.' });
  }
  if (preferences.mustVisits.some((place) => !place.trim())) {
    issues.push({ section: 'preferences', message: 'Remove blank must-visit places.' });
  }
  if (
    validMustVisits &&
    preferences.mustVisits.some(
      (place) => !validMustVisits.some((option) => option.name.toLocaleLowerCase() === place.trim().toLocaleLowerCase())
    )
  ) {
    issues.push({
      section: 'preferences',
      message: 'Update must-visit places that are not available for the current destinations.',
    });
  }

  if (!['TOTAL', 'PER_PERSON'].includes(budget.budgetMode)) {
    issues.push({ section: 'budget', message: 'Choose whether this budget is total or per person.' });
  }
  if (!Number.isFinite(budget.budgetInr) || budget.budgetInr < 1000) {
    issues.push({ section: 'budget', message: 'Enter a budget of at least ₹1,000.' });
  }

  return issues;
};

export const buildPlanRequestDraft = (
  details: TripDetailsState,
  stops: RouteStop[],
  preferences: PlannerPreferences,
  budget: TripBudgetDraft
): PlanRequestDraft => ({
  origin: details.origin.trim(),
  destinations: stops.map((stop) => stop.name.trim()),
  start_date: details.departureDateIso,
  end_date: details.returnDateIso,
  date_mode: details.flexibleDates ? 'FLEXIBLE' : 'EXACT',
  flexibility_days: 0,
  duration_days: details.durationDays,
  adults: details.adults,
  children: details.children,
  budget_inr: budget.budgetInr,
  budget_mode: budget.budgetMode,
  travel_style: preferences.travelStyle,
  pace: preferences.pace,
  activity_preferences: [...preferences.activityPreferences],
  must_visits: preferences.mustVisits.map((place) => place.trim()).filter(Boolean),
  scope: details.scope,
});