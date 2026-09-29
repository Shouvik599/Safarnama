import React from 'react';
import { PlannerHeader } from '../components/layout/PlannerHeader';
import { PlannerFooter } from '../components/layout/PlannerFooter';
import { ProgressStepper } from '../components/planner/ProgressStepper';

interface PlannerStepLayoutProps {
  currentStep: number;
  onNavigateHome: () => void;
  onNavigateStep: (step: number) => void;
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
}

export const PlannerStepLayout: React.FC<PlannerStepLayoutProps> = ({
  currentStep,
  onNavigateHome,
  onNavigateStep,
  eyebrow,
  title,
  description,
  children,
}) => (
  <div className="min-h-screen bg-surface text-on-surface flex flex-col font-body-md">
    <PlannerHeader
      currentStep={currentStep}
      onNavigateHome={onNavigateHome}
      onNavigateStep={onNavigateStep}
    />
    <main className="w-full flex-1 pt-20 px-margin-mobile sm:px-margin">
      <div className="max-w-[1120px] mx-auto">
        <ProgressStepper currentStep={currentStep} onSelectStep={onNavigateStep} />
        <header className="max-w-3xl mx-auto text-center mb-space-xl">
          <p className="inline-flex items-center rounded-full bg-primary-fixed px-3 py-1 font-label-md text-label-md font-semibold text-on-primary-fixed-variant">
            {eyebrow}
          </p>
          <h1 className="mt-3 font-headline-lg text-headline-lg text-on-surface">{title}</h1>
          <p className="mt-2 font-body-lg text-body-lg text-on-surface-variant">{description}</p>
        </header>
        {children}
      </div>
    </main>
    <PlannerFooter />
  </div>
);