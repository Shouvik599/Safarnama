import React from 'react';
import type { DayPlan } from '../../types/itinerary';

interface ItineraryDayRailProps {
  days: DayPlan[];
  selectedDayNumber: number;
  onSelectDay: (dayNumber: number) => void;
}

export const ItineraryDayRail: React.FC<ItineraryDayRailProps> = ({
  days,
  selectedDayNumber,
  onSelectDay,
}) => {
  return (
    <div className="w-full bg-surface-container-lowest/80 backdrop-blur-md rounded-2xl p-space-md border border-outline-variant/30 shadow-sm">
      <div className="flex items-center justify-between mb-space-sm px-space-xs">
        <div className="flex items-center gap-space-xs">
          <span className="material-symbols-outlined text-[18px] text-primary" aria-hidden="true">
            linear_scale
          </span>
          <span className="font-label-sm text-label-sm font-bold uppercase tracking-wider text-on-surface">
            Journey Progression Rail
          </span>
        </div>
        <span className="font-label-caption text-label-caption text-on-surface-variant font-medium">
          {days.length} Days Coordinated • Click any day to focus
        </span>
      </div>

      <div
        className="flex items-center gap-space-sm overflow-x-auto pb-space-xs pt-1 no-scrollbar scroll-smooth"
        role="tablist"
        aria-label="Trip Days Rail"
      >
        {days.map((day, idx) => {
          const isSelected = day.day_number === selectedDayNumber;
          const isCompleted = day.day_number < selectedDayNumber;

          return (
            <button
              key={day.day_number}
              role="tab"
              aria-selected={isSelected}
              aria-label={`Day ${day.day_number}: ${day.city} - ${day.theme}`}
              onClick={() => onSelectDay(day.day_number)}
              type="button"
              className={`flex-shrink-0 flex items-center gap-space-sm px-space-md py-space-sm rounded-xl transition-all duration-200 cursor-pointer text-left border ${
                isSelected
                  ? 'bg-primary text-on-primary border-primary shadow-md scale-[1.02]'
                  : isCompleted
                  ? 'bg-surface-container-low text-on-surface border-outline-variant/30 hover:border-primary/50'
                  : 'bg-surface-container-lowest text-on-surface-variant border-outline-variant/20 hover:border-outline-variant/60'
              }`}
            >
              {/* Day Node Circle Indicator */}
              <div className="relative flex items-center justify-center">
                {isSelected && (
                  <span className="absolute -inset-1 rounded-full bg-primary-container/40 animate-ping" />
                )}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center font-bold font-label-sm text-label-sm ${
                    isSelected
                      ? 'bg-on-primary text-primary'
                      : isCompleted
                      ? 'bg-secondary text-on-secondary'
                      : 'bg-surface-container-high text-on-surface-variant'
                  }`}
                >
                  {isCompleted ? (
                    <span className="material-symbols-outlined text-[16px]">check</span>
                  ) : (
                    <span>{String(day.day_number).padStart(2, '0')}</span>
                  )}
                </div>
              </div>

              {/* Day Meta Info */}
              <div className="flex flex-col min-w-[70px]">
                <div className="flex items-center gap-1">
                  <span
                    className={`font-label-sm text-label-sm font-bold leading-tight ${
                      isSelected ? 'text-on-primary' : 'text-on-surface'
                    }`}
                  >
                    Day {day.day_number}
                  </span>
                  {isSelected && (
                    <span className="w-1.5 h-1.5 rounded-full bg-on-primary" />
                  )}
                </div>
                <span
                  className={`font-label-caption text-label-caption truncate max-w-[100px] leading-tight ${
                    isSelected ? 'text-on-primary/85' : 'text-on-surface-variant'
                  }`}
                >
                  {day.city}
                </span>
              </div>

              {/* Connecting arrow for sequence */}
              {idx < days.length - 1 && (
                <span
                  className={`material-symbols-outlined text-[14px] ml-1 ${
                    isSelected ? 'text-on-primary/60' : 'text-outline-variant/60'
                  }`}
                  aria-hidden="true"
                >
                  chevron_right
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
