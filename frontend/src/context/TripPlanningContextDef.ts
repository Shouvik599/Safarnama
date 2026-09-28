import { createContext } from 'react';
import type { TripDetailsState, RouteStop } from '../types/trip';

export interface TripPlanningContextType {
  tripDetails: TripDetailsState;
  updateTripDetails: (details: Partial<TripDetailsState>) => void;
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
}

export const TripPlanningContext = createContext<TripPlanningContextType | undefined>(undefined);
