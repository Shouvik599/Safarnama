import React from 'react';
import type { DestinationDetail } from '../../types/itinerary';

interface DestinationSnapshotGridProps {
  snapshot: DestinationDetail['snapshot'];
}

export const DestinationSnapshotGrid: React.FC<DestinationSnapshotGridProps> = ({
  snapshot,
}) => {
  const cards = [
    {
      label: 'Recommended Stay',
      value: snapshot.recommended_stay,
      icon: 'hotel',
      color: 'text-primary',
    },
    {
      label: 'Seasonal Window',
      value: snapshot.seasonal_context,
      icon: 'calendar_today',
      color: 'text-primary-container',
    },
    {
      label: 'Weather Context',
      value: snapshot.weather_context,
      icon: 'wb_sunny',
      color: 'text-secondary',
    },
    {
      label: 'Currency & Exchange',
      value: snapshot.currency_fx,
      icon: 'currency_exchange',
      color: 'text-primary',
    },
    {
      label: 'Language & Signage',
      value: snapshot.language,
      icon: 'translate',
      color: 'text-secondary',
    },
    {
      label: 'Time Difference',
      value: snapshot.timezone,
      icon: 'schedule',
      color: 'text-primary-container',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-gutter w-full">
      {cards.map((card) => (
        <div
          key={card.label}
          className="p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 flex flex-col justify-between shadow-xs hover:border-primary/40 transition-colors"
        >
          <div className="flex items-center gap-space-xs text-on-surface-variant mb-space-xs">
            <span className={`material-symbols-outlined text-[20px] ${card.color}`} aria-hidden="true">
              {card.icon}
            </span>
            <span className="font-label-caption text-label-caption uppercase tracking-wider font-bold">
              {card.label}
            </span>
          </div>
          <div className="font-headline-sm text-[17px] font-bold text-on-surface leading-snug">
            {card.value}
          </div>
        </div>
      ))}
    </div>
  );
};
