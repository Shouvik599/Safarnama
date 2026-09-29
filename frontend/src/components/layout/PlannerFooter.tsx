import React from 'react';

export const PlannerFooter: React.FC = () => {
  return (
    <footer className="w-full bg-surface-container-low py-space-xl mt-space-xl">
      <div className="max-w-[1280px] mx-auto px-margin flex flex-col sm:flex-row items-center justify-between gap-space-md text-center sm:text-left">
        <div className="font-body-sm text-body-sm text-on-surface-variant">
          &copy; 2025 Safarnama Travel Technologies. Crafted with quiet intention for mindful journeys.
        </div>
        <div className="flex items-center gap-space-lg">
          <a
            href="#support"
            className="font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors"
          >
            Concierge Support
          </a>
          <a
            href="#advisories"
            className="font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors"
          >
            Travel Advisories
          </a>
        </div>
      </div>
    </footer>
  );
};
