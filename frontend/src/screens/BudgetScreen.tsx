import React, { useState } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import type { BudgetMode } from '../types/trip';
import { handleRadioGroupKeyDown } from '../components/planner/radioKeyboard';
import { PlannerStepLayout } from './PlannerStepLayout';

interface BudgetScreenProps {
  onNavigateHome: () => void;
  onNavigateStep: (step: number) => void;
}

const formatInr = (amount: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number.isFinite(amount) ? amount : 0);

export const BudgetScreen: React.FC<BudgetScreenProps> = ({ onNavigateHome, onNavigateStep }) => {
  const { budget, updateBudget, tripDetails } = useTripPlanning();
  const [error, setError] = useState('');
  const modes: { value: BudgetMode; title: string; description: string }[] = [
    { value: 'TOTAL', title: 'Total trip', description: 'One target for everyone travelling.' },
    { value: 'PER_PERSON', title: 'Per person', description: 'A target amount for each traveller.' },
  ];

  const continueToReview = () => {
    if (!['TOTAL', 'PER_PERSON'].includes(budget.budgetMode)) {
      setError('Choose whether this amount is for the total trip or per person.');
      return;
    }
    if (!Number.isFinite(budget.budgetInr) || budget.budgetInr < 1000) {
      setError('Enter a budget of at least ₹1,000.');
      return;
    }
    setError('');
    onNavigateStep(5);
  };

  return (
    <PlannerStepLayout
      currentStep={4}
      onNavigateHome={onNavigateHome}
      onNavigateStep={onNavigateStep}
      eyebrow="Step 4 of 5 · Budget"
      title="What is your trip budget?"
      description="Set an all-inclusive INR target. You can refine it before planning begins."
    >
      <div className="max-w-4xl mx-auto space-y-space-lg pb-space-xl">
        <section className="grid gap-6 rounded-lg border border-outline-variant/40 bg-surface-container-lowest p-5 sm:p-8 md:grid-cols-[1.15fr_0.85fr]">
          <div>
            <label htmlFor="budget-amount" className="block font-headline-md text-headline-md font-bold">Target amount</label>
            <p className="mt-1 text-on-surface-variant">Include transport, stays, meals, activities, and local travel.</p>
            <div className="mt-6 flex min-h-16 items-center rounded-md border border-outline-variant bg-surface px-4 focus-within:outline focus-within:outline-2 focus-within:outline-primary">
              <span className="mr-3 text-xl font-semibold text-on-surface-variant" aria-hidden="true">₹</span>
              <input
                id="budget-amount"
                aria-label="Target amount in INR"
                type="number"
                inputMode="numeric"
                min="1000"
                step="1000"
                value={Number.isFinite(budget.budgetInr) ? budget.budgetInr : ''}
                onChange={(event) => {
                  updateBudget({ budgetInr: event.target.value === '' ? 0 : Number(event.target.value) });
                  setError('');
                }}
                aria-describedby="budget-hint"
                className="w-full min-w-0 border-0 bg-transparent text-2xl font-bold text-on-surface outline-none"
              />
              <span className="ml-2 text-sm font-semibold text-on-surface-variant">INR</span>
            </div>
            <p id="budget-hint" className="mt-2 text-sm text-on-surface-variant">Minimum target ₹1,000</p>
            <fieldset className="mt-7">
              <legend className="mb-3 font-semibold">This amount is for</legend>
              <div className="grid gap-3 sm:grid-cols-2">
                {modes.map((mode) => (
                  <label key={mode.value} className="cursor-pointer">
                    <input
                      className="peer sr-only"
                      type="radio"
                      name="budget-mode"
                      value={mode.value}
                      checked={budget.budgetMode === mode.value}
                      onChange={() => updateBudget({ budgetMode: mode.value })}
                      onKeyDown={handleRadioGroupKeyDown}
                    />
                    <span className="block min-h-24 rounded-md border border-outline-variant/60 p-4 peer-checked:border-primary peer-checked:bg-primary-fixed/40 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-primary">
                      <span className="block font-semibold">{mode.title}</span>
                      <span className="mt-1 block text-sm leading-5 text-on-surface-variant">{mode.description}</span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
          </div>

          <aside className="flex flex-col justify-between rounded-md bg-surface-container-low p-5 sm:p-6" aria-label="Budget estimate information">
            <div>
              <span aria-hidden="true" className="material-symbols-outlined text-3xl text-primary">receipt_long</span>
              <h2 className="mt-3 font-headline-sm text-headline-sm font-bold">Your planning target</h2>
              <p className="mt-2 text-sm leading-6 text-on-surface-variant">
                {formatInr(budget.budgetInr)} {budget.budgetMode === 'PER_PERSON' ? 'per traveller' : 'for the trip'}
              </p>
            </div>
            <div className="mt-6 border-t border-outline-variant/50 pt-4 text-sm leading-6 text-on-surface-variant">
              <p className="font-semibold text-on-surface">A transparent estimate comes later</p>
              <p className="mt-1">No live prices or category allocations are available at this step. The planner will use this as your target when you start planning.</p>
              <p className="mt-3">{tripDetails.adults + tripDetails.children + tripDetails.infants} travellers · {tripDetails.durationDays} days</p>
            </div>
          </aside>
        </section>

        {error && <p role="alert" className="text-sm font-medium text-error">{error}</p>}
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button type="button" onClick={() => onNavigateStep(3)} className="min-h-12 rounded-md px-4 font-semibold text-on-surface-variant hover:bg-surface-container-low focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
            <span aria-hidden="true" className="material-symbols-outlined mr-1 align-middle">arrow_back</span>Back to preferences
          </button>
          <button type="button" onClick={continueToReview} className="min-h-12 rounded-md bg-primary px-6 font-semibold text-on-primary hover:opacity-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
            Review trip <span aria-hidden="true" className="material-symbols-outlined ml-1 align-middle">arrow_forward</span>
          </button>
        </div>
      </div>
    </PlannerStepLayout>
  );
};