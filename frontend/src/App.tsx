import React, { useState } from 'react';
import { TripPlanningProvider } from './context/TripPlanningContext';
import { useTripPlanning } from './context/useTripPlanning';
import { WelcomeScreen } from './screens/WelcomeScreen';
import { TripDetailsScreen } from './screens/TripDetailsScreen';
import { DestinationsScreen } from './screens/DestinationsScreen';

type Screen = 'welcome' | 'trip-details' | 'destinations';

const AppContent: React.FC = () => {
  const [currentScreen, setCurrentScreen] = useState<Screen>('welcome');
  const { updateTripDetails } = useTripPlanning();

  const handleStartPlanning = () => {
    setCurrentScreen('trip-details');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectCuratedRoute = (route: { origin: string; destination: string }) => {
    updateTripDetails({
      origin: route.origin,
      destination: route.destination,
    });
    setCurrentScreen('trip-details');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleContinueToDestinations = () => {
    setCurrentScreen('destinations');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToTripDetails = () => {
    setCurrentScreen('trip-details');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNavigateHome = () => {
    setCurrentScreen('welcome');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <>
      {currentScreen === 'welcome' && (
        <WelcomeScreen
          onStartPlanning={handleStartPlanning}
          onSelectCuratedRoute={handleSelectCuratedRoute}
        />
      )}

      {currentScreen === 'trip-details' && (
        <TripDetailsScreen
          onBackToWelcome={handleNavigateHome}
          onContinueToDestinations={handleContinueToDestinations}
        />
      )}

      {currentScreen === 'destinations' && (
        <DestinationsScreen
          onBackToTripDetails={handleBackToTripDetails}
          onNavigateHome={handleNavigateHome}
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
