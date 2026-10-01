import React, { useEffect, useState } from 'react';
import { TripPlanningProvider } from './context/TripPlanningContext';
import { useTripPlanning } from './context/useTripPlanning';
import { WelcomeScreen } from './screens/WelcomeScreen';
import { TripDetailsScreen } from './screens/TripDetailsScreen';
import { DestinationsScreen } from './screens/DestinationsScreen';
import { PreferencesScreen } from './screens/PreferencesScreen';
import { BudgetScreen } from './screens/BudgetScreen';
import { ReviewScreen } from './screens/ReviewScreen';
import { TripPlanningProgressScreen } from './screens/TripPlanningProgressScreen';
import { TripOverviewScreen } from './screens/TripOverviewScreen';

type Route =
  | 'welcome'
  | 'trip-details'
  | 'destinations'
  | 'preferences'
  | 'budget'
  | 'review'
  | 'progress'
  | 'overview'
  | 'itinerary';

const routePaths: Record<Route, string> = {
  welcome: '/',
  'trip-details': '/planner/trip-details',
  destinations: '/planner/destinations',
  preferences: '/planner/preferences',
  budget: '/planner/budget',
  review: '/planner/review',
  progress: '/planner/progress',
  overview: '/trip/overview',
  itinerary: '/trip/itinerary',
};

const routeFromPath = (path: string): Route =>
  (Object.keys(routePaths) as Route[]).find((route) => routePaths[route] === path) ?? 'welcome';

const routeForStep: Record<number, Route> = {
  1: 'trip-details',
  2: 'destinations',
  3: 'preferences',
  4: 'budget',
  5: 'review',
};

const AppContent: React.FC = () => {
  const [currentRoute, setCurrentRoute] = useState<Route>(() => routeFromPath(window.location.pathname));
  const { updateTripDetails, seedDestination } = useTripPlanning();

  useEffect(() => {
    const syncRoute = () => {
      const route = routeFromPath(window.location.pathname);
      if (routePaths[route] !== window.location.pathname) {
        window.history.replaceState(null, '', routePaths[route]);
      }
      setCurrentRoute(route);
    };
    window.addEventListener('popstate', syncRoute);
    return () => window.removeEventListener('popstate', syncRoute);
  }, []);

  const navigate = (route: Route) => {
    const path = routePaths[route];
    if (window.location.pathname !== path) window.history.pushState(null, '', path);
    setCurrentRoute(route);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStartPlanning = () => navigate('trip-details');

  const handleSelectCuratedRoute = (route: { origin: string; destination: string }) => {
    seedDestination(route.destination);
    updateTripDetails({
      origin: route.origin,
      destination: route.destination,
      destinations: [route.destination],
    });
    navigate('trip-details');
  };

  const navigateToStep = (step: number) => {
    const route = routeForStep[step];
    if (route) navigate(route);
  };

  return (
    <>
      {currentRoute === 'welcome' && (
        <WelcomeScreen
          onStartPlanning={handleStartPlanning}
          onSelectCuratedRoute={handleSelectCuratedRoute}
        />
      )}

      {currentRoute === 'trip-details' && (
        <TripDetailsScreen
          onBackToWelcome={() => navigate('welcome')}
          onContinueToDestinations={() => navigate('destinations')}
        />
      )}

      {currentRoute === 'destinations' && (
        <DestinationsScreen
          onBackToTripDetails={() => navigate('trip-details')}
          onNavigateHome={() => navigate('welcome')}
          onContinueToPreferences={() => navigate('preferences')}
        />
      )}

      {currentRoute === 'preferences' && (
        <PreferencesScreen onNavigateHome={() => navigate('welcome')} onNavigateStep={navigateToStep} />
      )}

      {currentRoute === 'budget' && (
        <BudgetScreen onNavigateHome={() => navigate('welcome')} onNavigateStep={navigateToStep} />
      )}

      {currentRoute === 'review' && (
        <ReviewScreen
          onNavigateHome={() => navigate('welcome')}
          onNavigateStep={navigateToStep}
          onConfirmPlan={() => navigate('progress')}
        />
      )}

      {currentRoute === 'progress' && (
        <TripPlanningProgressScreen
          onNavigateReview={() => navigate('review')}
          onNavigateOverview={() => navigate('overview')}
        />
      )}

      {currentRoute === 'overview' && (
        <TripOverviewScreen
          onNavigateHome={() => navigate('welcome')}
          onNavigateItinerary={() => navigate('itinerary')}
          onNavigateEditTrip={() => navigate('trip-details')}
        />
      )}

      {currentRoute === 'itinerary' && (
        <div className="bg-surface min-h-screen flex flex-col items-center justify-center p-6 text-center">
          <div className="max-w-md p-8 bg-surface-container-lowest rounded-2xl shadow-md border border-outline-variant/30 space-y-4">
            <span className="material-symbols-outlined text-[48px] text-primary">calendar_month</span>
            <h2 className="font-headline-md text-headline-md text-on-surface font-bold">
              Day-by-Day Itinerary
            </h2>
            <p className="text-on-surface-variant font-body-md text-body-md">
              The detailed day-by-day activity schedule and timeline will be implemented in Batch 4. Your synthesized dossier is safely saved.
            </p>
            <button
              type="button"
              onClick={() => navigate('overview')}
              className="px-6 py-2.5 rounded-xl bg-primary text-on-primary font-semibold hover:bg-primary-container transition-colors shadow-sm"
            >
              Back to Trip Overview
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export function App() {
  return (
    <TripPlanningProvider>
      <AppContent />
    </TripPlanningProvider>
  );
}

export default App;
