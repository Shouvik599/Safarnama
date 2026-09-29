import React from 'react';
import { Header } from '../components/layout/Header';
import { Footer } from '../components/layout/Footer';

interface WelcomeScreenProps {
  onStartPlanning: () => void;
  onSelectCuratedRoute?: (route: { origin: string; destination: string }) => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  onStartPlanning,
  onSelectCuratedRoute,
}) => {
  return (
    <div className="bg-surface font-body-md text-on-surface antialiased min-h-screen flex flex-col">
      {/* Top Header */}
      <Header
        onStartPlanning={onStartPlanning}
        onExploreHowItWorks={() => {
          document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' });
        }}
      />

      {/* Main Content Area */}
      <main className="w-full pt-20 bg-surface flex-1">
        <div className="flex flex-col w-full">
          {/* Top Decorative Organic Ambient Background */}
          <div className="relative w-full overflow-hidden">
            <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[1000px] h-[480px] bg-gradient-to-b from-primary-fixed/30 via-primary-fixed-dim/10 to-transparent blur-3xl pointer-events-none rounded-full" />
            <div className="absolute top-48 -left-32 w-80 h-80 bg-secondary-fixed/20 blur-3xl pointer-events-none rounded-full" />

            {/* HERO SECTION */}
            <div className="max-w-[1280px] mx-auto px-margin-mobile md:px-gutter lg:px-margin pt-8 pb-16 md:pt-14 md:pb-24">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-y-12 lg:gap-x-10 items-center">
                {/* Left Column: Copy & CTAs */}
                <div className="lg:col-span-6 flex flex-col items-start space-y-6">
                  {/* Eyebrow Badge */}
                  <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-surface-container-low shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-secondary" />
                    <span className="font-label-md text-label-md text-on-secondary-fixed-variant tracking-wider uppercase font-semibold">
                      Travel from India to Anywhere
                    </span>
                    <span className="material-symbols-outlined text-primary-container text-[16px]">
                      alt_route
                    </span>
                  </div>

                  {/* Primary Headline */}
                  <h1 className="font-display-hero text-headline-lg sm:text-display-hero text-on-background tracking-tight">
                    Plan your journey.{' '}
                    <span className="block text-primary-container">Discover more.</span>
                  </h1>

                  {/* Supporting Editorial Paragraph */}
                  <p className="font-body-lg text-body-md sm:text-body-lg text-on-surface-variant max-w-xl">
                    From the quiet valleys of Ladakh to the winding streets of Kyoto and the sunlit Mediterranean coast — Safarnama helps you design complete journeys with thoughtful routes, handpicked stays, weather insights, and budget clarity.
                  </p>

                  {/* Dual Call to Action Buttons */}
                  <div className="flex flex-wrap items-center gap-4 pt-2 w-full sm:w-auto">
                    <button
                      onClick={onStartPlanning}
                      className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-primary-container text-on-primary font-label-lg text-label-lg px-7 py-3.5 rounded-xl hover:bg-primary transition-all duration-200 shadow-md hover:shadow-lg cursor-pointer active:scale-98"
                    >
                      <span>Plan My Trip</span>
                      <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                    </button>

                    <a
                      href="#how-it-works"
                      className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-surface-container-lowest text-on-surface font-label-lg text-label-lg px-6 py-3.5 rounded-xl hover:bg-surface-container transition-all duration-200 shadow-sm hover:shadow-md cursor-pointer text-center"
                    >
                      <span className="material-symbols-outlined text-[18px] text-on-surface-variant">
                        explore
                      </span>
                      <span>Explore Safarnama</span>
                    </a>
                  </div>

                  {/* Trust & Scope Indicators */}
                  <div className="pt-4 flex flex-wrap items-center gap-y-3 gap-x-6 text-on-surface-variant font-label-caption text-label-caption">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary-container" />
                      <span className="font-medium text-on-surface">Domestic &amp; Global Itineraries</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
                      <span className="font-medium text-on-surface">Visa-Aware Guidance</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary-container" />
                      <span className="font-medium text-on-surface">Curated Stays &amp; Scenic Transit</span>
                    </div>
                  </div>
                </div>

                {/* Right Column: Hero Visual Composition with Floating Overlays */}
                <div className="lg:col-span-6 relative w-full flex justify-center">
                  {/* Background Journey Path SVG Motif */}
                  <svg
                    className="absolute -top-10 -right-8 w-72 h-72 text-primary-fixed-dim/40 pointer-events-none -z-0"
                    fill="none"
                    viewBox="0 0 200 200"
                  >
                    <path
                      d="M20,160 C60,40 140,20 180,80 C210,120 120,180 80,140 C50,110 120,40 170,30"
                      stroke="currentColor"
                      strokeDasharray="4 6"
                      strokeLinecap="round"
                      strokeWidth="2.5"
                    />
                  </svg>

                  {/* Main Visual Frame */}
                  <div className="relative w-full max-w-lg rounded-2xl p-2 bg-surface-container-low shadow-xl">
                    <div className="relative overflow-hidden rounded-xl aspect-[4/3] bg-surface-dim">
                      <img
                        className="w-full h-full object-cover transition-transform duration-700 hover:scale-105"
                        alt="Flat lay of traveler notebook open to hand-drawn expedition routes and mountain sketches beside camera, brass compass, and postcards"
                        src="https://lh3.googleusercontent.com/aida-public/AB6AXuAmScbGF6eqElMipak_JhGAvqoakhhMUdAw2XLiAlvWLov1Xv-8E1IbBFQGRGbDwUHWN-BFKBGtDWNJdrlGTV5HCpBp2Rn03NBtRVn8cik4-RypoQlWtOCkOAW0MQwvyjxp4zvNT1qiVDgHfQ5-LU0Nig8nGjy9hX9vH1doe183czC0m9ZxKRCafGFD4Dxb1AnTCT0nWrS3wUOOLjPBeBnAWnT37m28xQ63PB05GooRAFXiHqk78horjg"
                      />
                      {/* Photo warmth gradient overlay */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none" />
                      {/* Inset Tag */}
                      <div className="absolute bottom-3 left-3 bg-surface-container-lowest/90 backdrop-blur-md px-3 py-1.5 rounded-lg shadow-sm flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary-container text-[16px]">
                          menu_book
                        </span>
                        <span className="font-label-caption text-label-caption text-on-surface font-semibold tracking-wide">
                          Journal 04 • The Leh &amp; Nubra Trail
                        </span>
                      </div>
                    </div>

                    {/* Floating Context Card 1 (Top Right) */}
                    <div className="absolute -top-5 -right-3 md:-right-6 bg-surface-container-lowest/95 backdrop-blur-md p-3.5 rounded-xl shadow-lg flex items-center gap-3.5 max-w-[240px] border border-outline-variant/30">
                      <div className="w-10 h-10 rounded-lg bg-surface-container-high flex items-center justify-center text-secondary shrink-0">
                        <span className="material-symbols-outlined text-[22px]">calendar_month</span>
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="font-label-md text-label-md text-on-surface font-bold truncate">
                          Kyoto &amp; Kanazawa
                        </span>
                        <span className="font-label-caption text-label-caption text-on-surface-variant flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-primary-container" />
                          Optimal: Oct — Nov
                        </span>
                      </div>
                    </div>

                    {/* Floating Context Card 2 (Bottom Left) */}
                    <div className="absolute -bottom-6 -left-3 md:-left-6 bg-surface-container-lowest/95 backdrop-blur-md p-4 rounded-xl shadow-lg flex flex-col gap-2 max-w-[260px] border border-outline-variant/30">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-primary-container text-[18px]">
                            conversion_path
                          </span>
                          <span className="font-label-md text-label-md text-on-surface font-bold">
                            Smart Route Plotted
                          </span>
                        </div>
                        <span className="font-label-caption text-label-caption bg-secondary-fixed/50 text-on-secondary-fixed-variant px-2 py-0.5 rounded-full font-semibold">
                          Verified
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-on-surface-variant font-label-caption text-label-caption pt-1">
                        <span className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-[14px]">distance</span>
                          1,420 km
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-[14px]">sunny</span>
                          22°C Clear
                        </span>
                        <span className="text-primary font-semibold">₹85,000 pp</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION: HOW SAFARNAMA SHAPES YOUR JOURNEY (6 BENTO CORE CAPABILITIES) */}
          <section className="w-full bg-surface-container-low/70 py-16 md:py-24" id="how-it-works">
            <div className="max-w-[1280px] mx-auto px-margin-mobile md:px-gutter lg:px-margin">
              {/* Section Header */}
              <div className="max-w-2xl mb-12 md:mb-16">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container text-on-secondary-fixed-variant font-label-md text-label-md font-semibold uppercase tracking-wider mb-3">
                  Thoughtful Architecture
                </div>
                <h2 className="font-headline-lg text-headline-lg text-on-background tracking-tight">
                  Every detail of your trip, thoughtfully connected.
                </h2>
                <p className="font-body-md text-body-md text-on-surface-variant mt-3">
                  Say goodbye to scattered tabs, fragmented notes, and disjointed bookings. Plan your complete journey in one harmonious space.
                </p>
              </div>

              {/* 3x2 Grid of Feature Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Card 1: Smart Itinerary */}
                <div className="bg-surface-container-lowest rounded-2xl p-7 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div>
                    <div className="w-12 h-12 rounded-xl bg-primary-fixed/40 flex items-center justify-center text-primary-container mb-5">
                      <span className="material-symbols-outlined text-[26px]">map</span>
                    </div>
                    <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-2">
                      Smart Itinerary
                    </h3>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Day-by-day travel schedules that balance travel pace, transit times, and spontaneous discoveries without exhausting rushing.
                    </p>
                  </div>
                  <div className="pt-6 mt-4 flex items-center gap-2 text-primary-container font-label-md text-label-md font-semibold">
                    <span>Adaptive day-pacing</span>
                    <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                  </div>
                </div>

                {/* Card 2: Routes & Transport */}
                <div className="bg-surface-container-lowest rounded-2xl p-7 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div>
                    <div className="w-12 h-12 rounded-xl bg-secondary-fixed/50 flex items-center justify-center text-secondary mb-5">
                      <span className="material-symbols-outlined text-[26px]">directions_subway</span>
                    </div>
                    <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-2">
                      Routes &amp; Transport
                    </h3>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Seamless connections across flights, scenic railways, road transfers, and regional transit anywhere in the world.
                    </p>
                  </div>
                  <div className="pt-6 mt-4 flex items-center gap-2 text-secondary font-label-md text-label-md font-semibold">
                    <span>Intermodal routing</span>
                    <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                  </div>
                </div>

                {/* Card 3: Hotels & Experiences */}
                <div className="bg-surface-container-lowest rounded-2xl p-7 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div>
                    <div className="w-12 h-12 rounded-xl bg-primary-fixed/40 flex items-center justify-center text-primary-container mb-5">
                      <span className="material-symbols-outlined text-[26px]">holiday_village</span>
                    </div>
                    <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-2">
                      Hotels &amp; Experiences
                    </h3>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Handpicked stays from boutique Indian heritage havelis to cliffside Mediterranean eco-lodges and design sanctuaries globally.
                    </p>
                  </div>
                  <div className="pt-6 mt-4 flex items-center gap-2 text-primary-container font-label-md text-label-md font-semibold">
                    <span>Curated sanctuaries</span>
                    <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                  </div>
                </div>

                {/* Card 4: Weather-Aware Planning */}
                <div className="bg-surface-container-lowest rounded-2xl p-7 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div>
                    <div className="w-12 h-12 rounded-xl bg-surface-container-high flex items-center justify-center text-primary mb-5">
                      <span className="material-symbols-outlined text-[26px]">wb_twilight</span>
                    </div>
                    <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-2">
                      Weather-Aware Planning
                    </h3>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Pack and travel with confidence using climate insights, monsoon calendars, shoulder season perks, and optimal sunshine windows.
                    </p>
                  </div>
                  <div className="pt-6 mt-4 flex items-center gap-2 text-primary font-label-md text-label-md font-semibold">
                    <span>Microclimate calendars</span>
                    <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                  </div>
                </div>

                {/* Card 5: Visa & Travel Information */}
                <div className="bg-surface-container-lowest rounded-2xl p-7 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div>
                    <div className="w-12 h-12 rounded-xl bg-secondary-fixed/50 flex items-center justify-center text-secondary mb-5">
                      <span className="material-symbols-outlined text-[26px]">badge</span>
                    </div>
                    <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-2">
                      Visa &amp; Travel Guidance
                    </h3>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Clear visa processing timelines, eVisa checkpoints, document checklists, and currency advice tailored for Indian passport holders.
                    </p>
                  </div>
                  <div className="pt-6 mt-4 flex items-center gap-2 text-secondary font-label-md text-label-md font-semibold">
                    <span>Indian passport verified</span>
                    <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                  </div>
                </div>

                {/* Card 6: Budget Planning */}
                <div className="bg-surface-container-lowest rounded-2xl p-7 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div>
                    <div className="w-12 h-12 rounded-xl bg-primary-fixed/40 flex items-center justify-center text-primary-container mb-5">
                      <span className="material-symbols-outlined text-[26px]">payments</span>
                    </div>
                    <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-2">
                      Budget Planning
                    </h3>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Track realistic trip expenses, multi-currency conversions, buffer funds, and customized daily allowances with zero surprises.
                    </p>
                  </div>
                  <div className="pt-6 mt-4 flex items-center gap-2 text-primary-container font-label-md text-label-md font-semibold">
                    <span>Transparent expense ledger</span>
                    <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION: CURATED INSPIRATION / POPULAR JOURNEYS */}
          <section className="w-full py-16 md:py-24">
            <div className="max-w-[1280px] mx-auto px-margin-mobile md:px-gutter lg:px-margin">
              {/* Section Header with View All Link */}
              <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10 gap-4">
                <div>
                  <span className="font-label-md text-label-md text-secondary font-semibold uppercase tracking-wider block mb-1">
                    Hand-Crafted Expeditions
                  </span>
                  <h2 className="font-headline-lg text-headline-lg text-on-background tracking-tight">
                    Popular Journey Routes
                  </h2>
                </div>
                <button
                  onClick={onStartPlanning}
                  className="inline-flex items-center gap-1.5 text-primary-container font-label-lg text-label-lg font-semibold hover:text-primary transition-colors cursor-pointer self-start sm:self-auto"
                >
                  <span>Explore All 48 Circuits</span>
                  <span className="material-symbols-outlined text-[18px]">north_east</span>
                </button>
              </div>

              {/* 3 Journey Preview Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-7">
                {/* Card 1: Ladakh */}
                <div
                  onClick={() => {
                    if (onSelectCuratedRoute) {
                      onSelectCuratedRoute({
                        origin: 'New Delhi, India (DEL)',
                        destination: 'Leh & Ladakh Circuit, India',
                      });
                    } else {
                      onStartPlanning();
                    }
                  }}
                  className="group bg-surface-container-lowest rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col cursor-pointer"
                >
                  <div className="relative h-60 w-full overflow-hidden bg-surface-dim">
                    <img
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      alt="Pangong Tso high altitude lake in Ladakh surrounded by barren Himalayan peaks"
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuD7hvrOUblL6helHGgFAMcUR7U3EPEILzLqPeulKE-nxnyN2hEGNn1NwxlKcHvikC1FCWp3Xy6nzJJAOUlAp9KYFqtjZPn19ZCDnfyGduvwsMieGa4XfyW0pxhor-JXs0T2kog6xE0aUaNDVJA_fsT9QzASZs5_ZRXx8kxDwCNXz3yfm4Ume_eGePLT-Bai4ddfc8X-QSFjrpIwv9oS-ehMcl50MoJBYx41vx1c98ebFxJf3OP5226VQA"
                      loading="lazy"
                    />
                    <div className="absolute top-3 left-3 bg-surface-container-lowest/90 backdrop-blur-md px-3 py-1 rounded-full text-secondary font-label-caption text-label-caption font-semibold">
                      Domestic Circuit
                    </div>
                    <div className="absolute bottom-3 right-3 bg-on-background/70 backdrop-blur-md text-surface px-2.5 py-1 rounded-lg text-label-caption font-medium flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">schedule</span>
                      8 Days
                    </div>
                  </div>
                  <div className="p-6 flex-1 flex flex-col justify-between space-y-4">
                    <div>
                      <div className="flex items-center gap-2 text-on-surface-variant font-label-caption text-label-caption mb-1.5">
                        <span>Leh</span>
                        <span className="material-symbols-outlined text-[14px] text-primary-container">
                          arrow_forward
                        </span>
                        <span>Nubra Valley</span>
                        <span className="material-symbols-outlined text-[14px] text-primary-container">
                          arrow_forward
                        </span>
                        <span>Pangong Tso</span>
                      </div>
                      <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold group-hover:text-primary-container transition-colors">
                        The High Passes of Ladakh
                      </h3>
                      <p className="font-body-sm text-body-sm text-on-surface-variant mt-2 line-clamp-2">
                        Conquer mountain passes, explore ancient cliffside monasteries, and spend silent star-filled nights by turquoise glacial lakes.
                      </p>
                    </div>
                    <div className="pt-3 flex items-center justify-between">
                      <div className="flex flex-col">
                        <span className="font-label-caption text-label-caption text-on-surface-variant">Recommended</span>
                        <span className="font-label-md text-label-md font-semibold text-on-surface">May — Sept</span>
                      </div>
                      <span className="inline-flex items-center gap-1 text-primary-container font-label-lg text-label-lg font-semibold group-hover:translate-x-1 transition-transform">
                        <span>Route Preview</span>
                        <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card 2: Kyoto & Kanazawa */}
                <div
                  onClick={() => {
                    if (onSelectCuratedRoute) {
                      onSelectCuratedRoute({
                        origin: 'New Delhi, India (DEL)',
                        destination: 'Kyoto & Kanazawa, Japan',
                      });
                    } else {
                      onStartPlanning();
                    }
                  }}
                  className="group bg-surface-container-lowest rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col cursor-pointer"
                >
                  <div className="relative h-60 w-full overflow-hidden bg-surface-dim">
                    <img
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      alt="Traditional historic wooden machiya alley in Kyoto during autumn with vibrant crimson Japanese maples"
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuCnRTowc0c7Auufma6M0HGK-QGaZPLV0vV7S5y8UPoWDYs8x6ngxcWlqDE2rm-kgBl1ZEj7jzkKHp0itJeOEBGEI8cIGF1WwjMLEaLHNtBplSrX5prNbP3SuwJQg4dP4_IdXwaNnrpckqmi1OkroYAFkT66Z2ZoAJpxmsKBsMsVg1U5bxy18HqnQ9-TUpEM_S8kzY9cqYA2G26J7eWp6t09a4fMHcwHystIbXkMlN2hw9Ym8KJdmEiBwA"
                      loading="lazy"
                    />
                    <div className="absolute top-3 left-3 bg-surface-container-lowest/90 backdrop-blur-md px-3 py-1 rounded-full text-secondary font-label-caption text-label-caption font-semibold">
                      International
                    </div>
                    <div className="absolute bottom-3 right-3 bg-on-background/70 backdrop-blur-md text-surface px-2.5 py-1 rounded-lg text-label-caption font-medium flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">schedule</span>
                      10 Days
                    </div>
                  </div>
                  <div className="p-6 flex-1 flex flex-col justify-between space-y-4">
                    <div>
                      <div className="flex items-center gap-2 text-on-surface-variant font-label-caption text-label-caption mb-1.5">
                        <span>Osaka</span>
                        <span className="material-symbols-outlined text-[14px] text-primary-container">
                          arrow_forward
                        </span>
                        <span>Kyoto</span>
                        <span className="material-symbols-outlined text-[14px] text-primary-container">
                          arrow_forward
                        </span>
                        <span>Kanazawa</span>
                      </div>
                      <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold group-hover:text-primary-container transition-colors">
                        Autumn in Kyoto &amp; Kanazawa
                      </h3>
                      <p className="font-body-sm text-body-sm text-on-surface-variant mt-2 line-clamp-2">
                        Stroll historic geisha quarters, partake in private tea ceremonies, and ride high-speed Shinkansen across cedar-forested valleys.
                      </p>
                    </div>
                    <div className="pt-3 flex items-center justify-between">
                      <div className="flex flex-col">
                        <span className="font-label-caption text-label-caption text-on-surface-variant">eVisa Available</span>
                        <span className="font-label-md text-label-md font-semibold text-on-surface">Oct — Nov</span>
                      </div>
                      <span className="inline-flex items-center gap-1 text-primary-container font-label-lg text-label-lg font-semibold group-hover:translate-x-1 transition-transform">
                        <span>Route Preview</span>
                        <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card 3: Amalfi Coast */}
                <div
                  onClick={() => {
                    if (onSelectCuratedRoute) {
                      onSelectCuratedRoute({
                        origin: 'Mumbai, India (BOM)',
                        destination: 'Amalfi & Tuscany, Italy',
                      });
                    } else {
                      onStartPlanning();
                    }
                  }}
                  className="group bg-surface-container-lowest rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col cursor-pointer"
                >
                  <div className="relative h-60 w-full overflow-hidden bg-surface-dim">
                    <img
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      alt="Amalfi Coast in Italy with colorful pastel houses clustered on towering limestone cliffs overlooking the azure Mediterranean sea"
                      src="https://lh3.googleusercontent.com/aida-public/AB6AXuAQOr-Jwi-E2Av5m4OSTPUCodU3aWEysFk_glFHIMNqIbIgsIu4r9JpTNOm1AMcI-oRuvNpSFLj1SPZPzd-SHVY552gvwNghsH9J674O9HBH4FJv-g3ly1PZ47t8ONFF8DTzg0oM6U81l5NlvhSo40oYZFOBrC6_zOV-8Lw7QBSJ1r2RAMngIdyIO1BUtJ9ZIZHQmQnA5HBI5JvAFYTRXj6MaGIdHDmlJk-lhFcd_V5y-S8uptO8u_ZYQ"
                      loading="lazy"
                    />
                    <div className="absolute top-3 left-3 bg-surface-container-lowest/90 backdrop-blur-md px-3 py-1 rounded-full text-secondary font-label-caption text-label-caption font-semibold">
                      International
                    </div>
                    <div className="absolute bottom-3 right-3 bg-on-background/70 backdrop-blur-md text-surface px-2.5 py-1 rounded-lg text-label-caption font-medium flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">schedule</span>
                      12 Days
                    </div>
                  </div>
                  <div className="p-6 flex-1 flex flex-col justify-between space-y-4">
                    <div>
                      <div className="flex items-center gap-2 text-on-surface-variant font-label-caption text-label-caption mb-1.5">
                        <span>Rome</span>
                        <span className="material-symbols-outlined text-[14px] text-primary-container">
                          arrow_forward
                        </span>
                        <span>Florence</span>
                        <span className="material-symbols-outlined text-[14px] text-primary-container">
                          arrow_forward
                        </span>
                        <span>Positano</span>
                      </div>
                      <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold group-hover:text-primary-container transition-colors">
                        Amalfi Coast &amp; Tuscan Hills
                      </h3>
                      <p className="font-body-sm text-body-sm text-on-surface-variant mt-2 line-clamp-2">
                        Panoramic coastal drives, quiet family-run olive groves, Renaissance masterpieces, and sunset boat passages in southern Italy.
                      </p>
                    </div>
                    <div className="pt-3 flex items-center justify-between">
                      <div className="flex flex-col">
                        <span className="font-label-caption text-label-caption text-on-surface-variant">Schengen Guidance</span>
                        <span className="font-label-md text-label-md font-semibold text-on-surface">Apr — June</span>
                      </div>
                      <span className="inline-flex items-center gap-1 text-primary-container font-label-lg text-label-lg font-semibold group-hover:translate-x-1 transition-transform">
                        <span>Route Preview</span>
                        <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION: EDITORIAL CLOSING BANNER */}
          <section className="w-full pb-16 md:pb-24">
            <div className="max-w-[1280px] mx-auto px-margin-mobile md:px-gutter lg:px-margin">
              <div className="relative overflow-hidden rounded-3xl bg-surface-container p-8 md:p-14 shadow-md">
                {/* Decorative background glows */}
                <div className="absolute -right-20 -bottom-20 w-80 h-80 rounded-full bg-primary-fixed/40 blur-3xl pointer-events-none" />
                <div className="absolute -left-20 -top-20 w-72 h-72 rounded-full bg-secondary-fixed/40 blur-2xl pointer-events-none" />

                <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
                  <div className="max-w-xl space-y-3">
                    <div className="inline-flex items-center gap-2 text-secondary font-label-md text-label-md font-bold uppercase tracking-wider">
                      <span className="material-symbols-outlined text-[18px]">explore</span>
                      <span>Your Personal Safarnama</span>
                    </div>
                    <h2 className="font-headline-lg text-headline-lg text-on-background tracking-tight">
                      Ready to begin your next story?
                    </h2>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Start planning your upcoming journey with Safarnama. Create bespoke itineraries, sync scenic transit, and venture with complete peace of mind.
                    </p>
                  </div>

                  <div className="shrink-0 w-full sm:w-auto">
                    <button
                      onClick={onStartPlanning}
                      className="w-full sm:w-auto inline-flex items-center justify-center gap-3 bg-primary-container text-on-primary font-label-lg text-label-lg px-8 py-4 rounded-xl hover:bg-primary transition-all duration-200 shadow-md hover:shadow-lg cursor-pointer active:scale-98"
                    >
                      <span>Plan My Trip</span>
                      <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};
