import React, { useEffect, useState } from 'react';
import { TripPlanningProvider } from './context/TripPlanningContext';
import { useTripPlanning } from './context/useTripPlanning';
import { WelcomeScreen } from './screens/WelcomeScreen';
import { TripDetailsScreen } from './screens/TripDetailsScreen';
import { DestinationsScreen } from './screens/DestinationsScreen';
import { PreferencesScreen } from './screens/PreferencesScreen';
import { BudgetScreen } from './screens/BudgetScreen';
import { ReviewScreen } from './screens/ReviewScreen';

type Route = 'welcome' | 'trip-details' | 'destinations' | 'preferences' | 'budget' | 'review';

const routePaths: Record<Route, string> = {
  welcome: '/',
  'trip-details': '/planner/trip-details',
  destinations: '/planner/destinations',
  preferences: '/planner/preferences',
  budget: '/planner/budget',
  review: '/planner/review',
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
        <ReviewScreen onNavigateHome={() => navigate('welcome')} onNavigateStep={navigateToStep} />
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
