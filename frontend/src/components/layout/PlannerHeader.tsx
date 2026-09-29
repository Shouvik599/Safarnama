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
  const steps = [
    { num: 1, label: 'Trip Details' },
    { num: 2, label: 'Destinations' },
    { num: 3, label: 'Preferences' },
    { num: 4, label: 'Budget' },
    { num: 5, label: 'Review' },
  ];

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
        <nav aria-label="Trip planning steps" className="hidden md:flex items-center gap-space-xs px-space-sm py-space-xs bg-surface-container-low rounded-full">
          {steps.map((step) => (
            <button
              key={step.num}
              type="button"
              onClick={() => onNavigateStep?.(step.num)}
              disabled={step.num > currentStep || !onNavigateStep}
              aria-current={step.num === currentStep ? 'step' : undefined}
              className={`px-space-md py-space-xs rounded-full font-label-md transition-all ${
                currentStep === step.num
                  ? 'bg-surface-container-high text-primary font-bold shadow-[0_1px_4px_rgba(41,37,33,0.04)]'
                  : step.num < currentStep
                    ? 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface cursor-pointer'
                    : 'text-outline/60 cursor-not-allowed'
              }`}
            >
              {step.num}. {step.label}
            </button>
          ))}
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
