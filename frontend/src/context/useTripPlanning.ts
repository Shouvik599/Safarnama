import { useContext } from 'react';
import { TripPlanningContext } from './TripPlanningContextDef';
import type { TripPlanningContextType } from './TripPlanningContextDef';

export const useTripPlanning = (): TripPlanningContextType => {
  const context = useContext(TripPlanningContext);
  if (!context) {
    throw new Error('useTripPlanning must be used within a TripPlanningProvider');
  }
  return context;
};
