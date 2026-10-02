import React from 'react';
import type { DayMeal } from '../../types/itinerary';

interface DayMealCardProps {
  meal: DayMeal;
  timeWindow?: string;
  onNavigateDining?: () => void;
}

export const DayMealCard: React.FC<DayMealCardProps> = ({
  meal,
  timeWindow = '12:30 – 14:00',
  onNavigateDining,
}) => {
  const formatInr = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);

  const mealIcons: Record<string, string> = {
    BREAKFAST: 'bakery_dining',
    LUNCH: 'lunch_dining',
    DINNER: 'dinner_dining',
  };

  return (
    <div
      onClick={onNavigateDining}
      className={`flex flex-col p-space-lg rounded-2xl bg-surface-container-low border border-outline-variant/30 hover:border-primary/40 transition-all shadow-xs ${
        onNavigateDining ? 'cursor-pointer hover:shadow-sm' : ''
      }`}
    >
      <div className="flex items-center justify-between pb-space-xs border-b border-outline-variant/15">
        <div className="flex items-center gap-space-xs">
          <span className="flex items-center gap-1 font-label-caption text-label-caption font-bold text-primary bg-primary/10 px-space-sm py-0.5 rounded-full">
            <span className="material-symbols-outlined text-[14px]">
              {mealIcons[meal.meal_type] || 'restaurant'}
            </span>
            {meal.meal_type} PAIRING
          </span>
          <span className="font-label-caption text-label-caption text-on-surface-variant font-medium">
            {timeWindow}
          </span>
        </div>

        <span className="font-label-sm text-label-sm font-bold text-on-surface">
          {formatInr(meal.estimated_cost_inr)}
        </span>
      </div>

      <div className="pt-space-sm">
        <h4 className="font-headline-sm text-headline-sm font-bold text-on-surface">
          {meal.name}
        </h4>
        <div className="flex items-center gap-2 text-on-surface-variant font-label-caption text-label-caption mt-0.5 mb-space-xs">
          <span className="font-semibold text-primary">{meal.cuisine}</span>
          {meal.restaurant_name && (
            <>
              <span>•</span>
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[13px] text-on-surface-variant">
                  storefront
                </span>
                {meal.restaurant_name}
              </span>
            </>
          )}
        </div>
      </div>

      {meal.notes && (
        <div className="mt-space-xs text-on-surface-variant font-body-sm text-body-sm bg-surface-container-lowest/70 p-space-sm rounded-xl border border-outline-variant/20 flex items-center gap-space-xs">
          <span className="material-symbols-outlined text-[15px] text-secondary" aria-hidden="true">
            table_restaurant
          </span>
          <span className="text-body-sm">{meal.notes}</span>
        </div>
      )}
    </div>
  );
};
