import React from 'react';
import type { RouteStop } from '../../types/trip';

interface RouteSequenceItemProps {
  stop: RouteStop;
  index: number;
  totalStops: number;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onRemove: () => void;
  onUpdateNights: (nights: number) => void;
}

export const RouteSequenceItem: React.FC<RouteSequenceItemProps> = ({
  stop,
  index,
  totalStops,
  onMoveUp,
  onMoveDown,
  onRemove,
  onUpdateNights,
}) => {
  const isFirst = index === 0;
  const isLast = index === totalStops - 1;

  // Waypoint node icon styling
  const nodeIcon = isFirst ? 'pin_drop' : isLast ? 'flag' : 'location_on';

  return (
    <div className="relative z-10 flex w-full min-w-0 flex-col pb-6 sm:pb-8">
      <div className="flex w-full min-w-0 items-start gap-4">
        {/* Waypoint Node */}
        <div className="w-10 h-10 rounded-full bg-surface-container-lowest shadow-md flex items-center justify-center ring-4 ring-surface shrink-0 text-primary font-headline-sm">
          <span className="material-symbols-outlined text-[20px] text-primary">
            {nodeIcon}
          </span>
        </div>

        {/* Stop Card */}
        <div className="min-w-0 flex-1 bg-surface-container-low rounded-xl p-space-md sm:p-space-lg shadow-sm hover:shadow-md transition-shadow flex flex-col sm:flex-row sm:items-center justify-between gap-4 border border-outline-variant/30">
          <div className="flex min-w-0 flex-1 items-start gap-4">
            <img
              src={stop.imageUrl}
              alt={stop.imageAlt || stop.name}
              className="w-20 h-20 rounded-lg object-cover shadow-sm shrink-0 bg-surface-dim"
              loading="lazy"
            />
            <div className="flex min-w-0 flex-1 flex-col">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="font-label-md text-label-md uppercase tracking-wider text-on-secondary-fixed-variant font-semibold">
                  Stop {String(index + 1).padStart(2, '0')}
                </span>
                <span className="px-2 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant font-label-caption text-label-caption font-semibold">
                  {stop.role}
                </span>
              </div>
              <h3 className="break-words font-headline-sm text-headline-sm text-on-surface font-bold">
                {stop.name}
              </h3>
              <div className="mt-0.5 flex flex-wrap items-center gap-3 text-on-surface-variant font-body-sm text-body-sm">
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[15px]">public</span>
                  {stop.country}
                </span>
                <span>•</span>

                {/* Interactive Nights Counter Stepper */}
                <div className="inline-flex items-center gap-1.5 bg-surface-container px-2 py-0.5 rounded-full shadow-xs">
                  <span className="material-symbols-outlined text-[14px]">night_shelter</span>
                  <button
                    type="button"
                    disabled={stop.nights <= 1}
                    onClick={() => onUpdateNights(stop.nights - 1)}
                    className="w-4 h-4 rounded-full bg-surface-container-lowest text-on-surface flex items-center justify-center text-[10px] hover:bg-surface-container-high transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Decrease nights"
                  >
                    -
                  </button>
                  <span className="font-label-md text-label-md font-bold text-on-surface px-0.5 select-none">
                    {stop.nights}
                  </span>
                  <button
                    type="button"
                    disabled={stop.nights >= 14}
                    onClick={() => onUpdateNights(stop.nights + 1)}
                    className="w-4 h-4 rounded-full bg-surface-container-lowest text-on-surface flex items-center justify-center text-[10px] hover:bg-surface-container-high transition-colors cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Increase nights"
                  >
                    +
                  </button>
                  <span className="text-[12px] text-on-surface-variant">nights</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons: Move Up, Move Down, Remove */}
          <div className="flex items-center gap-1 self-end sm:self-center">
            <button
              type="button"
              disabled={isFirst}
              onClick={onMoveUp}
              className={`w-9 h-9 rounded-lg bg-surface-container-lowest text-on-surface-variant flex items-center justify-center transition-colors shadow-sm ${
                isFirst
                  ? 'opacity-30 cursor-not-allowed'
                  : 'hover:bg-surface-container hover:text-primary cursor-pointer'
              }`}
              title="Move Stop Up"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_upward</span>
            </button>

            <button
              type="button"
              disabled={isLast}
              onClick={onMoveDown}
              className={`w-9 h-9 rounded-lg bg-surface-container-lowest text-on-surface-variant flex items-center justify-center transition-colors shadow-sm ${
                isLast
                  ? 'opacity-30 cursor-not-allowed'
                  : 'hover:bg-surface-container hover:text-primary cursor-pointer'
              }`}
              title="Move Stop Down"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_downward</span>
            </button>

            <button
              type="button"
              onClick={onRemove}
              className="w-9 h-9 rounded-lg bg-surface-container-lowest hover:bg-error-container text-on-surface-variant hover:text-on-error-container flex items-center justify-center transition-colors shadow-sm cursor-pointer"
              title="Remove Stop"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
        </div>
      </div>

      {/* Transit Connector to next stop */}
      {stop.transitToNext && (
        <div className="pl-14 sm:pl-16 py-3 flex items-center gap-3 text-on-surface-variant font-label-caption text-label-caption">
          <div className="px-3 py-1 rounded-full bg-surface-container-high flex items-center gap-1.5 shadow-sm">
            <span className="material-symbols-outlined text-[14px] text-primary">
              {stop.transitToNext.icon || 'train'}
            </span>
            <span className="font-semibold text-on-surface">
              {stop.transitToNext.title}
            </span>
            <span className="opacity-60">•</span>
            <span>{stop.transitToNext.duration}</span>
          </div>
          <div className="h-[1px] flex-1 bg-outline-variant/30" />
        </div>
      )}
    </div>
  );
};
