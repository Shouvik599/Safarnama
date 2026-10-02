import React from 'react';
import type { DayPlan } from '../../types/itinerary';

interface DayBentoMetricsProps {
  day: DayPlan;
}

export const DayBentoMetrics: React.FC<DayBentoMetricsProps> = ({ day }) => {
  const metrics = day.metrics || {
    active_hours: 5.5,
    rest_hours: 2.5,
    walking_steps: 8400,
    walking_km: 6.2,
    pacing_label: 'Balanced & Meditative',
  };

  const weather = day.weather_forecast || {
    temp_celsius: 16,
    condition: 'Crisp Autumn',
    precipitation_chance: 0,
    icon: 'park',
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-space-sm w-full">
      {/* 1. Active Rhythm */}
      <div className="p-space-md rounded-2xl bg-surface-container-lowest border border-outline-variant/30 flex flex-col justify-between shadow-sm hover:border-primary/40 transition-colors">
        <div className="flex items-center justify-between text-on-surface-variant">
          <span className="font-label-caption text-label-caption uppercase tracking-wider font-semibold">
            Active Rhythm
          </span>
          <span className="material-symbols-outlined text-[18px] text-primary" aria-hidden="true">
            schedule
          </span>
        </div>
        <div className="mt-space-xs">
          <div className="font-headline-sm text-headline-sm font-bold text-on-surface">
            {metrics.active_hours}h
          </div>
          <span className="font-label-caption text-label-caption text-on-surface-variant">
            Light-Moderate Cadence
          </span>
        </div>
      </div>

      {/* 2. Pacing Leeway Buffer */}
      <div className="p-space-md rounded-2xl bg-surface-container-lowest border border-outline-variant/30 flex flex-col justify-between shadow-sm hover:border-primary/40 transition-colors">
        <div className="flex items-center justify-between text-on-surface-variant">
          <span className="font-label-caption text-label-caption uppercase tracking-wider font-semibold">
            Pacing Buffer
          </span>
          <span className="material-symbols-outlined text-[18px] text-primary-container" aria-hidden="true">
            spa
          </span>
        </div>
        <div className="mt-space-xs">
          <div className="font-headline-sm text-headline-sm font-bold text-on-surface">
            {metrics.rest_hours}h
          </div>
          <span className="font-label-caption text-label-caption text-on-surface-variant truncate">
            {metrics.pacing_label}
          </span>
        </div>
      </div>

      {/* 3. Walking Footprint */}
      <div className="p-space-md rounded-2xl bg-surface-container-lowest border border-outline-variant/30 flex flex-col justify-between shadow-sm hover:border-primary/40 transition-colors">
        <div className="flex items-center justify-between text-on-surface-variant">
          <span className="font-label-caption text-label-caption uppercase tracking-wider font-semibold">
            Walking Footprint
          </span>
          <span className="material-symbols-outlined text-[18px] text-secondary" aria-hidden="true">
            directions_walk
          </span>
        </div>
        <div className="mt-space-xs">
          <div className="font-headline-sm text-headline-sm font-bold text-on-surface">
            ~{metrics.walking_steps.toLocaleString()}
          </div>
          <span className="font-label-caption text-label-caption text-on-surface-variant">
            {metrics.walking_km} km • Scenic Terrain
          </span>
        </div>
      </div>

      {/* 4. Microclimate Atmosphere */}
      <div className="p-space-md rounded-2xl bg-surface-container-lowest border border-outline-variant/30 flex flex-col justify-between shadow-sm hover:border-primary/40 transition-colors">
        <div className="flex items-center justify-between text-on-surface-variant">
          <span className="font-label-caption text-label-caption uppercase tracking-wider font-semibold">
            Microclimate
          </span>
          <span className="material-symbols-outlined text-[18px] text-primary" aria-hidden="true">
            {weather.icon || 'sunny'}
          </span>
        </div>
        <div className="mt-space-xs">
          <div className="font-headline-sm text-headline-sm font-bold text-on-surface">
            {weather.temp_celsius}°C
          </div>
          <span className="font-label-caption text-label-caption text-on-surface-variant truncate">
            {weather.condition} • {weather.precipitation_chance ?? 0}% Rain
          </span>
        </div>
      </div>
    </div>
  );
};
