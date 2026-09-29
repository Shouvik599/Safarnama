import React from 'react';

interface ProgressStepperProps {
  currentStep: number; // 1: Trip Details, 2: Destinations, 3: Preferences, 4: Budget, 5: Review
  onSelectStep?: (step: number) => void;
}

export const ProgressStepper: React.FC<ProgressStepperProps> = ({
  currentStep,
  onSelectStep,
}) => {
  const steps = [
    { num: 1, label: 'Trip Details', icon: 'trip_origin', sub: 'Step 1' },
    { num: 2, label: 'Destinations', icon: 'explore', sub: 'Step 2' },
    { num: 3, label: 'Preferences', icon: 'tune', sub: 'Step 3' },
    { num: 4, label: 'Budget', icon: 'payments', sub: 'Step 4' },
    { num: 5, label: 'Review', icon: 'assignment_turned_in', sub: 'Step 5' },
  ];

  // Calculate route fill percentage
  // Step 1: 0% / dashed line, Step 2: ~28% filled, etc.
  const fillWidth = `${((currentStep - 1) / (steps.length - 1)) * 100}%`;

  return (
    <section className="w-full pt-space-lg pb-space-md">
      <div className="max-w-4xl mx-auto px-margin-mobile sm:px-0">
        <div className="relative flex items-center justify-between">
          {/* Connecting Journey Route Line */}
          <div className="absolute left-6 right-6 top-5 -translate-y-1/2 h-[2px] bg-outline-variant/40 -z-0">
            <div
              className="h-full bg-primary transition-all duration-500 ease-out"
              style={{ width: fillWidth }}
            />
          </div>

          {/* Stepper items */}
          {steps.map((step) => {
            const isCompleted = step.num < currentStep;
            const isActive = step.num === currentStep;
            const isUpcoming = step.num > currentStep;

            return (
              <button
                type="button"
                key={step.num}
                aria-current={isActive ? 'step' : undefined}
                aria-label={`${step.label}, ${isCompleted ? 'completed' : isActive ? 'current step' : 'upcoming'}`}
                disabled={!isCompleted || !onSelectStep}
                onClick={() => {
                  if (isCompleted && onSelectStep) {
                    onSelectStep(step.num);
                  }
                }}
                className={`relative z-10 flex flex-col items-center select-none bg-transparent ${
                  isCompleted ? 'cursor-pointer group' : 'cursor-default'
                } ${isUpcoming ? 'opacity-65' : ''}`}
              >
                {/* Node icon circle */}
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ring-4 ring-surface transition-all duration-300 ${
                    isActive
                      ? 'bg-primary-container text-on-primary shadow-md scale-105 ring-primary-fixed/50'
                      : isCompleted
                      ? 'bg-surface-container-lowest text-primary shadow-sm group-hover:scale-105'
                      : 'bg-surface-container-high text-on-surface-variant'
                  }`}
                >
                  {isCompleted ? (
                    <span
                      className="material-symbols-outlined text-[20px] text-primary"
                      style={{ fontVariationSettings: "'FILL' 1" }}
                    >
                      check_circle
                    </span>
                  ) : isActive ? (
                    <span
                      className="material-symbols-outlined text-[20px]"
                      style={{ fontVariationSettings: "'FILL' 1" }}
                    >
                      {step.num === 1 ? 'trip_origin' : 'alt_route'}
                    </span>
                  ) : (
                    <span aria-hidden="true" className="material-symbols-outlined h-5 w-5 shrink-0 overflow-hidden text-[18px]">
                      {step.icon}
                    </span>
                  )}
                </div>

                {/* Step labels */}
                <span
                  className={`mt-space-xs font-label-md text-label-md tracking-tight ${
                    isActive
                      ? 'text-primary font-bold'
                      : isCompleted
                      ? 'text-on-surface-variant font-medium'
                      : 'text-on-surface-variant'
                  }`}
                >
                  {step.label}
                </span>

                <span
                  className={`font-label-caption text-label-caption ${
                    isActive
                      ? 'text-primary font-semibold'
                      : isCompleted
                      ? 'text-primary font-medium'
                      : 'text-outline'
                  }`}
                >
                  {isCompleted ? 'Completed' : isActive ? 'Active Step' : step.sub}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
};
