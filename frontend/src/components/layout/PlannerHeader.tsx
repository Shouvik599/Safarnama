import React from 'react';

interface PlannerHeaderProps {
  currentStep: number;
  onNavigateHome: () => void;
  onNavigateStep?: (step: number) => void;
}

export const PlannerHeader: React.FC<PlannerHeaderProps> = ({
  currentStep,
  onNavigateHome,
  onNavigateStep,
}) => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-surface/90 backdrop-blur-xl shadow-[0_1px_8px_rgba(41,37,33,0.04)]">
      <div className="h-20 max-w-[1280px] mx-auto px-margin flex items-center justify-between gap-space-lg">
        {/* Brand */}
        <div className="flex items-center gap-space-md shrink-0">
          <button
            onClick={onNavigateHome}
            className="flex items-center gap-space-sm text-left focus:outline-none cursor-pointer"
            title="Return to Safarnama Home"
          >
            <img
              src="/safarnama-symbol.svg"
              alt="Safarnama Logo"
              className="h-8 w-8 object-contain"
            />
            <span className="hidden sm:inline-block font-headline-sm text-headline-sm text-on-surface tracking-tight font-bold">
              Safarnama
            </span>
          </button>
        </div>

        {/* Central Planning Progress Nav Pills */}
        <nav className="hidden md:flex items-center gap-space-xs px-space-sm py-space-xs bg-surface-container-low rounded-full">
          <button
            onClick={() => onNavigateStep && onNavigateStep(1)}
            className={`px-space-md py-space-xs rounded-full font-label-md transition-all cursor-pointer ${
              currentStep === 1
                ? 'bg-surface-container-high text-primary font-bold shadow-[0_1px_4px_rgba(41,37,33,0.04)]'
                : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
            }`}
          >
            1. Trip Details
          </button>

          <button
            onClick={() => onNavigateStep && onNavigateStep(2)}
            className={`px-space-md py-space-xs rounded-full font-label-md transition-all cursor-pointer ${
              currentStep === 2
                ? 'bg-surface-container-high text-primary font-bold shadow-[0_1px_4px_rgba(41,37,33,0.04)]'
                : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
            }`}
          >
            2. Destinations
          </button>

          <span className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-outline/60 cursor-not-allowed select-none">
            3. Preferences
          </span>
          <span className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-outline/60 cursor-not-allowed select-none">
            4. Budget
          </span>
          <span className="px-space-md py-space-xs rounded-full font-label-md text-label-md text-outline/60 cursor-not-allowed select-none">
            5. Review
          </span>
        </nav>

        {/* Save & Exit + User Avatar */}
        <div className="flex items-center gap-space-md shrink-0">
          <button
            onClick={onNavigateHome}
            className="font-label-lg text-label-lg text-on-surface-variant hover:text-primary transition-colors hidden sm:inline-block cursor-pointer"
          >
            Save &amp; Exit
          </button>
          <div
            className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0 text-on-primary cursor-pointer hover:opacity-90 transition-opacity"
            title="Account"
          >
            <span className="material-symbols-outlined text-[18px]">person</span>
          </div>
        </div>
      </div>
    </header>
  );
};
