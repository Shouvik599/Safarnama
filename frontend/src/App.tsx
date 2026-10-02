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
import { DayByDayItineraryScreen } from './screens/DayByDayItineraryScreen';
import { DayDetailTimelineScreen } from './screens/DayDetailTimelineScreen';
import { DestinationDetailScreen } from './screens/DestinationDetailScreen';
import { TransportDetailScreen } from './screens/TransportDetailScreen';
import { Batch5HandoffScreen } from './screens/Batch5HandoffScreen';

type Route =
  | 'welcome'
  | 'trip-details'
  | 'destinations'
  | 'preferences'
  | 'budget'
  | 'review'
  | 'progress'
  | 'overview'
  | 'itinerary'
  | 'day-detail'
  | 'destination'
  | 'transport'
  | 'stays'
  | 'dining'
  | 'experience'
  | 'map';

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
  'day-detail': '/trip/day-detail',
  destination: '/trip/destination',
  transport: '/trip/transport',
  stays: '/trip/stays',
  dining: '/trip/dining',
  experience: '/trip/experience',
  map: '/trip/map',
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

  // Query parameter states for deep linking & history synchronization
  const [selectedDay, setSelectedDay] = useState<number>(() => {
    const params = new URLSearchParams(window.location.search);
    const day = params.get('day');
    return day ? parseInt(day, 10) || 3 : 3;
  });

  const [selectedDestination, setSelectedDestination] = useState<string>(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('name') || 'Kyoto';
  });

  const [selectedLeg, setSelectedLeg] = useState<string>(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('leg') || 'leg-3';
  });

  const [selectedItemTitle, setSelectedItemTitle] = useState<string>(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('item') || '';
  });

  const { updateTripDetails, seedDestination } = useTripPlanning();

  useEffect(() => {
    const syncRoute = () => {
      const route = routeFromPath(window.location.pathname);
      const params = new URLSearchParams(window.location.search);

      const dayParam = params.get('day');
      if (dayParam) setSelectedDay(parseInt(dayParam, 10) || 3);

      const nameParam = params.get('name');
      if (nameParam) setSelectedDestination(nameParam);

      const legParam = params.get('leg');
      if (legParam) setSelectedLeg(legParam);

      const itemParam = params.get('item');
      if (itemParam) setSelectedItemTitle(itemParam);

      setCurrentRoute(route);
    };

    window.addEventListener('popstate', syncRoute);
    return () => window.removeEventListener('popstate', syncRoute);
  }, []);

  const navigate = (
    route: Route,
    options?: { day?: number; destination?: string; leg?: string; item?: string }
  ) => {
    const basePath = routePaths[route];
    const params = new URLSearchParams();

    if (options?.day !== undefined) {
      setSelectedDay(options.day);
      params.set('day', String(options.day));
    }
    if (options?.destination !== undefined) {
      setSelectedDestination(options.destination);
      params.set('name', options.destination);
    }
    if (options?.leg !== undefined) {
      setSelectedLeg(options.leg);
      params.set('leg', options.leg);
    }
    if (options?.item !== undefined) {
      setSelectedItemTitle(options.item);
      params.set('item', options.item);
    }

    const queryStr = params.toString() ? `?${params.toString()}` : '';
    const fullPath = `${basePath}${queryStr}`;

    if (window.location.pathname + window.location.search !== fullPath) {
      window.history.pushState(null, '', fullPath);
    }
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
          onNavigateItinerary={() => navigate('itinerary', { day: selectedDay })}
          onNavigateEditTrip={() => navigate('trip-details')}
          onNavigateDestination={(dest) => navigate('destination', { destination: dest })}
          onNavigateTransport={(leg) => navigate('transport', { leg: leg || 'leg-3' })}
          onNavigateDayDetail={(day) => navigate('day-detail', { day })}
        />
      )}

      {currentRoute === 'itinerary' && (
        <DayByDayItineraryScreen
          initialDay={selectedDay}
          onNavigateHome={() => navigate('welcome')}
          onNavigateOverview={() => navigate('overview')}
          onNavigateDayDetail={(day) => navigate('day-detail', { day })}
          onNavigateDestination={(dest) => navigate('destination', { destination: dest })}
          onNavigateTransport={(leg) => navigate('transport', { leg: leg || 'leg-3' })}
          onNavigateEditTrip={() => navigate('trip-details')}
          onNavigateStay={(hotel) => navigate('stays', { item: hotel, day: selectedDay })}
          onNavigateDining={(meal) => navigate('dining', { item: meal, day: selectedDay })}
          onNavigateExperience={(poi) => navigate('experience', { item: poi, day: selectedDay })}
          onNavigateMap={() => navigate('map', { day: selectedDay })}
        />
      )}

      {currentRoute === 'day-detail' && (
        <DayDetailTimelineScreen
          dayNumber={selectedDay}
          onNavigateHome={() => navigate('welcome')}
          onNavigateOverview={() => navigate('overview')}
          onNavigateItinerary={(day) => navigate('itinerary', { day: day ?? selectedDay })}
          onNavigateDestination={(dest) => navigate('destination', { destination: dest })}
          onNavigateTransport={(leg) => navigate('transport', { leg: leg || 'leg-3' })}
          onNavigateEditTrip={() => navigate('trip-details')}
          onNavigateStay={(hotel) => navigate('stays', { item: hotel, day: selectedDay })}
          onNavigateDining={(meal) => navigate('dining', { item: meal, day: selectedDay })}
          onNavigateExperience={(poi) => navigate('experience', { item: poi, day: selectedDay })}
          onNavigateMap={() => navigate('map', { day: selectedDay })}
        />
      )}

      {currentRoute === 'destination' && (
        <DestinationDetailScreen
          destinationName={selectedDestination}
          onNavigateHome={() => navigate('welcome')}
          onNavigateOverview={() => navigate('overview')}
          onNavigateItinerary={(day) => navigate('itinerary', { day: day || 3 })}
          onNavigateTransport={(leg) => navigate('transport', { leg: leg || 'leg-3' })}
          onNavigateEditTrip={() => navigate('trip-details')}
          onNavigateStay={(hotel) => navigate('stays', { item: hotel, day: selectedDay })}
          onNavigateDining={(meal) => navigate('dining', { item: meal, day: selectedDay })}
          onNavigateExperience={(poi) => navigate('experience', { item: poi, day: selectedDay })}
          onNavigateMap={() => navigate('map', { day: selectedDay })}
        />
      )}

      {currentRoute === 'transport' && (
        <TransportDetailScreen
          legId={selectedLeg}
          onNavigateHome={() => navigate('welcome')}
          onNavigateOverview={() => navigate('overview')}
          onNavigateItinerary={(day) => navigate('itinerary', { day: day || 7 })}
          onNavigateDestination={(dest) => navigate('destination', { destination: dest })}
          onNavigateEditTrip={() => navigate('trip-details')}
          onNavigateMap={() => navigate('map', { day: selectedDay })}
        />
      )}

      {(currentRoute === 'stays' ||
        currentRoute === 'dining' ||
        currentRoute === 'experience' ||
        currentRoute === 'map') && (
        <Batch5HandoffScreen
          category={currentRoute}
          itemTitle={selectedItemTitle}
          dayNumber={selectedDay}
          onNavigateHome={() => navigate('welcome')}
          onNavigateOverview={() => navigate('overview')}
          onNavigateItinerary={(day) => navigate('itinerary', { day: day ?? selectedDay })}
        />
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
