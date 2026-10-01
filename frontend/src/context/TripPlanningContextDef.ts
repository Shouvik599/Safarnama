import { createContext } from 'react';
import type {
  TripDetailsState,
  RouteStop,
  PlannerPreferences,
  TripBudgetDraft,
} from '../types/trip';

export interface TripPlanningContextType {
  tripDetails: TripDetailsState;
  updateTripDetails: (details: Partial<TripDetailsState>) => void;
  preferences: PlannerPreferences;
  updatePreferences: (preferences: Partial<PlannerPreferences>) => void;
  budget: TripBudgetDraft;
  updateBudget: (budget: Partial<TripBudgetDraft>) => void;
  destinations: RouteStop[];
  addDestination: (stop: RouteStop) => void;
  removeDestination: (id: string) => void;
  updateStopNights: (id: string, nights: number) => void;
  batchUpdateStopNights: (updates: { id: string; nights: number }[]) => void;
  moveDestinationUp: (index: number) => void;
  moveDestinationDown: (index: number) => void;
  seedCircuit: (circuitId: string) => void;
  seedDestination: (destinationOrCircuit: string | string[], scopeHint?: 'DOMESTIC' | 'INTERNATIONAL') => void;
  resetAll: () => void;
  itinerary: import('../types/itinerary').FinalItinerary | null;
  setItinerary: (itinerary: import('../types/itinerary').FinalItinerary | null) => void;
  planRunState: import('../types/itinerary').PlanRunState;
  setPlanRunState: React.Dispatch<React.SetStateAction<import('../types/itinerary').PlanRunState>>;
  clearPlan: () => void;
}

export const TripPlanningContext = createContext<TripPlanningContextType | undefined>(undefined);

