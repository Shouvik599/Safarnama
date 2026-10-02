import React from 'react';
import { useTripPlanning } from '../context/useTripPlanning';

export type Batch5Category = 'stays' | 'dining' | 'experience' | 'map';

interface Batch5HandoffScreenProps {
  category: Batch5Category;
  itemTitle?: string;
  dayNumber?: number;
  onNavigateHome: () => void;
  onNavigateOverview: () => void;
  onNavigateItinerary: (dayNumber?: number) => void;
}

export const Batch5HandoffScreen: React.FC<Batch5HandoffScreenProps> = ({
  category,
  itemTitle,
  dayNumber = 3,
  onNavigateHome,
  onNavigateOverview,
  onNavigateItinerary,
}) => {
  const { itinerary, tripDetails } = useTripPlanning();

  const categoryMeta: Record<
    Batch5Category,
    { title: string; subtitle: string; icon: string; badge: string; color: string }
  > = {
    stays: {
      title: 'Sanctuary Stays & Historic Ryokan Lodging',
      subtitle:
        'Direct boutique host reservation previews, neighborhood access protocols, and confirmed check-in leeway.',
      icon: 'hotel',
      badge: 'Batch 5 Preview • Screen 14: Hotel / Accommodation',
      color: 'text-primary',
    },
    dining: {
      title: 'Artisanal Dining & Evening Kaiseki Counters',
      subtitle:
        'Seasonal degustation menus, teahouse appointments, and reservation timing calibrated to sunset lantern hours.',
      icon: 'restaurant',
      badge: 'Batch 5 Preview • Screen 15: Restaurant / Food Experience',
      color: 'text-primary-container',
    },
    experience: {
      title: 'Attraction & Guild Experience Dossier',
      subtitle:
        'Deep artisan craft master profiles, heritage histories, private courtyard admission, and crowd evasion radars.',
      icon: 'attractions',
      badge: 'Batch 5 Preview • Screen 16: Attraction & Experience Details',
      color: 'text-primary',
    },
    map: {
      title: 'Interactive Journey Route & Spatial Geometry',
      subtitle:
        'Dynamic geospatial waypoint tracking, scenic rail corridors, and interactive elevation & walking contour overlays.',
      icon: 'map',
      badge: 'Batch 5 Preview • Screen 17: Map / Journey Route',
      color: 'text-secondary',
    },
  };

  const current = categoryMeta[category] || categoryMeta.stays;
  const activeTitle = itemTitle || (category === 'map' ? 'Full Route Corridor' : 'Curated Highlight');

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen flex flex-col antialiased">
      {/* Top Header */}
      <header className="fixed top-0 w-full z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(41,37,33,0.04)]">
        <div className="h-20 max-w-[1280px] mx-auto px-margin-mobile lg:px-margin flex items-center justify-between gap-gutter">
          <div className="flex items-center gap-space-sm cursor-pointer" onClick={onNavigateHome}>
            <img alt="Safarnama Logo" className="h-8 w-auto object-contain" src="/safarnama-symbol.svg" />
            <span className="hidden sm:inline-block font-headline-sm text-headline-sm text-on-surface tracking-tight ml-space-xs font-bold">
              Safarnama
            </span>
          </div>

          <nav
            aria-label="Application navigation"
            className="hidden md:flex items-center gap-space-xs bg-surface-container-low px-space-xs py-space-xs rounded-full shadow-[0_1px_3px_-1px_rgba(41,37,33,0.03)]"
          >
            <button
              type="button"
              onClick={onNavigateHome}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Explore
            </button>
            <button
              type="button"
              onClick={onNavigateOverview}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Overview
            </button>
            <button
              type="button"
              onClick={() => onNavigateItinerary(dayNumber)}
              className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            >
              Itinerary
            </button>
          </nav>

          <div className="flex items-center gap-space-sm">
            <button
              type="button"
              onClick={() => onNavigateItinerary(dayNumber)}
              className="px-space-md py-2 rounded-xl bg-primary text-on-primary font-label-sm text-label-sm font-bold flex items-center gap-1 transition-all cursor-pointer shadow-xs"
            >
              <span className="material-symbols-outlined text-[18px]">calendar_today</span>
              <span>Back to Itinerary</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-[800px] w-full mx-auto px-margin-mobile lg:px-margin pt-36 pb-space-2xl flex flex-col items-center justify-center text-center">
        <div className="w-full p-space-xl md:p-space-2xl rounded-3xl bg-surface-container-lowest border border-outline-variant/30 shadow-md flex flex-col items-center gap-space-lg">
          {/* Badge */}
          <div className="inline-flex items-center gap-1.5 px-space-md py-1 rounded-full bg-surface-container text-on-surface-variant font-label-caption text-label-caption font-bold border border-outline-variant/20">
            <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
            <span>{current.badge}</span>
          </div>

          {/* Icon */}
          <div className="w-20 h-20 rounded-3xl bg-surface-container-low flex items-center justify-center shadow-inner">
            <span className={`material-symbols-outlined text-[44px] ${current.color}`}>
              {current.icon}
            </span>
          </div>

          {/* Content */}
          <div className="space-y-space-xs max-w-lg">
            <h2 className="font-headline-lg text-headline-lg font-bold text-on-surface tracking-tight">
              {current.title}
            </h2>
            <div className="font-label-md text-label-md font-semibold text-primary pt-1">
              Active Selection: &ldquo;{activeTitle}&rdquo;
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant pt-2 leading-relaxed">
              {current.subtitle}
            </p>
          </div>

          {/* Notice Box */}
          <div className="w-full p-space-md rounded-2xl bg-surface-container-low border border-outline-variant/20 text-left font-body-sm text-body-sm text-on-surface-variant flex items-start gap-space-sm">
            <span className="material-symbols-outlined text-[20px] text-primary flex-shrink-0 mt-0.5">
              bookmark_added
            </span>
            <div>
              <span className="font-bold text-on-surface block">
                Dossier #{itinerary?.trip_id || 'SN-JP-2025-HKR'} Seamless Handoff
              </span>
              <span>
                Your itinerary schedule, dates ({tripDetails.departureDate} – {tripDetails.returnDate}), and traveler preferences are safely synchronized. Batch 5 expands this item into full interactive booking specs and rich multimedia galleries.
              </span>
            </div>
          </div>

          {/* Action Navigation */}
          <div className="flex flex-wrap items-center justify-center gap-space-sm w-full pt-space-xs">
            <button
              type="button"
              onClick={() => onNavigateItinerary(dayNumber)}
              className="px-space-xl py-space-sm rounded-xl bg-primary text-on-primary font-label-md text-label-md font-bold hover:bg-primary/90 transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_back</span>
              <span>Return to Day {dayNumber} Itinerary</span>
            </button>
            <button
              type="button"
              onClick={onNavigateOverview}
              className="px-space-lg py-space-sm rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md font-semibold transition-colors cursor-pointer border border-outline-variant/30"
            >
              Trip Overview
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-outline-variant/20 bg-surface-container-lowest py-space-md text-center font-label-caption text-label-caption text-on-surface-variant">
        Safarnama Journey Planning Architecture • Seamless Multi-Batch Continuity
      </footer>
    </div>
  );
};
