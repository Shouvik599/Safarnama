import React from 'react';

interface CounterStepperProps {
  label: string;
  subLabel: string;
  value: number;
  min?: number;
  max?: number;
  onChange: (newValue: number) => void;
}

export const CounterStepper: React.FC<CounterStepperProps> = ({
  label,
  subLabel,
  value,
  min = 0,
  max = 12,
  onChange,
}) => {
  return (
    <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between">
      <div>
        <span className="block font-label-md text-label-md text-on-surface font-semibold">
          {label}
        </span>
        <span className="font-body-sm text-body-sm text-on-surface-variant">
          {subLabel}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          disabled={value <= min}
          onClick={() => onChange(Math.max(min, value - 1))}
          className={`w-8 h-8 rounded-full bg-surface-container-lowest text-on-surface flex items-center justify-center shadow-sm active:scale-95 transition-all ${
            value <= min
              ? 'opacity-40 cursor-not-allowed'
              : 'hover:bg-surface-container-high cursor-pointer'
          }`}
          title={`Decrease ${label}`}
        >
          <span className="material-symbols-outlined text-[16px]">remove</span>
        </button>

        <span className="font-headline-sm text-headline-sm text-on-surface w-6 text-center select-none">
          {value}
        </span>

        <button
          type="button"
          disabled={value >= max}
          onClick={() => onChange(Math.min(max, value + 1))}
          className={`w-8 h-8 rounded-full bg-surface-container-lowest text-on-surface flex items-center justify-center shadow-sm active:scale-95 transition-all ${
            value >= max
              ? 'opacity-40 cursor-not-allowed'
              : 'hover:bg-surface-container-high cursor-pointer'
          }`}
          title={`Increase ${label}`}
        >
          <span className="material-symbols-outlined text-[16px]">add</span>
        </button>
      </div>
    </div>
  );
};
