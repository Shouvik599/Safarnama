import React from 'react';

interface HeaderProps {
  onStartPlanning: () => void;
  onNavigateHome?: () => void;
  onExploreHowItWorks?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onStartPlanning,
  onNavigateHome,
  onExploreHowItWorks,
}) => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(41,37,33,0.04)]">
      <div className="h-20 max-w-[1280px] mx-auto px-margin-mobile md:px-gutter lg:px-margin flex items-center justify-between gap-space-md">
        {/* Brand */}
        <div className="flex items-center gap-space-md">
          <button
            onClick={onNavigateHome}
            className="flex items-center gap-space-sm text-left focus:outline-none cursor-pointer"
            title="Safarnama Home"
          >
            <img
              src="/safarnama-symbol.svg"
              alt="Safarnama Logo Symbol"
              className="h-9 w-9 object-contain"
            />
            <span className="font-headline-sm text-headline-sm text-on-surface font-bold tracking-tight">
              Safarnama
            </span>
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="hidden lg:flex items-center gap-space-lg">
          <button
            onClick={onStartPlanning}
            className="font-body-md text-body-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
          >
            Destinations
          </button>
          <button
            onClick={onExploreHowItWorks}
            className="font-body-md text-body-md text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
          >
            How It Works
          </button>
          <a
            href="#stories"
            className="font-body-md text-body-md text-on-surface-variant hover:text-on-surface transition-colors"
          >
            Stories &amp; Guides
          </a>
          <a
            href="#about"
            className="font-body-md text-body-md text-on-surface-variant hover:text-on-surface transition-colors"
          >
            About Safarnama
          </a>
        </nav>

        {/* Primary CTA & Avatar */}
        <div className="flex items-center gap-space-md">
          <button
            onClick={onStartPlanning}
            className="hidden sm:inline-flex items-center justify-center bg-primary-container text-on-primary font-label-lg text-label-lg px-space-lg py-space-sm rounded-xl hover:bg-primary transition-colors shadow-[0_2px_8px_-2px_rgba(41,37,33,0.08)] cursor-pointer"
          >
            Plan My Trip
          </button>
          <div
            className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary cursor-pointer hover:opacity-90 transition-opacity"
            title="Traveler Profile"
          >
            <span className="material-symbols-outlined text-[18px]">person</span>
          </div>
        </div>
      </div>
    </header>
  );
};
