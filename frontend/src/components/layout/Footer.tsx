import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-surface-container-low mt-space-xl shadow-[0_-1px_6px_rgba(41,37,33,0.03)]">
      <div className="max-w-[1280px] mx-auto px-margin-mobile md:px-gutter lg:px-margin py-space-xl">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-space-lg mb-space-xl">
          {/* Brand Bio */}
          <div className="lg:col-span-2 flex flex-col gap-space-sm">
            <div className="flex items-center gap-space-sm">
              <img
                src="/safarnama-symbol.svg"
                alt="Safarnama Logo"
                className="h-7 w-7 object-contain"
              />
              <span className="font-headline-sm text-headline-sm text-on-surface font-bold">
                Safarnama
              </span>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-sm">
              Mindful itineraries, timeless routes, and conscious expedition planning crafted for the modern traveler.
            </p>
          </div>

          {/* Domestic Escapes */}
          <div>
            <h4 className="font-label-lg text-label-lg text-on-surface mb-space-sm font-bold">
              Domestic Escapes
            </h4>
            <ul className="flex flex-col gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Rajasthan Heritage Circuits
              </li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Ladakh &amp; Spiti High Trails
              </li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Kerala Backwaters &amp; Coast
              </li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Meghalaya &amp; Northeast Valleys
              </li>
            </ul>
          </div>

          {/* Worldwide Itineraries */}
          <div>
            <h4 className="font-label-lg text-label-lg text-on-surface mb-space-sm font-bold">
              Worldwide Itineraries
            </h4>
            <ul className="flex flex-col gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Central Asian Silk Route
              </li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Mediterranean Overland
              </li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Nordic Rail &amp; Fjords
              </li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Southeast Asian Archipelago
              </li>
            </ul>
          </div>

          {/* Resources & Support */}
          <div>
            <h4 className="font-label-lg text-label-lg text-on-surface mb-space-sm font-bold">
              Resources &amp; Support
            </h4>
            <ul className="flex flex-col gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Travel Advisory &amp; Visas
              </li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Packing &amp; Climate Guides
              </li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Responsible Travel Charter
              </li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">
                Concierge Desk
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom copyright & legal bar */}
        <div className="pt-space-lg flex flex-col sm:flex-row items-center justify-between gap-space-sm text-on-surface-variant font-label-caption text-label-caption bg-surface-container-high/40 px-space-md py-space-sm rounded-xl">
          <span>&copy; 2025 Safarnama Travel Technologies. All rights reserved.</span>
          <div className="flex items-center gap-space-md">
            <span className="hover:text-on-surface transition-colors cursor-pointer">Privacy Policy</span>
            <span className="hover:text-on-surface transition-colors cursor-pointer">Terms of Journey</span>
            <span className="hover:text-on-surface transition-colors cursor-pointer">Booking Guarantee</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
