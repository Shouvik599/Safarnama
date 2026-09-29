import React, { useState } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import { buildPlanRequestDraft, validateTripDraft } from '../data/planRequest';
import { getMustVisitOptions } from '../data/mustVisitOptions';
import { PlannerStepLayout } from './PlannerStepLayout';

interface ReviewScreenProps {
  onNavigateHome: () => void;
  onNavigateStep: (step: number) => void;
}

const formatInr = (amount: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number.isFinite(amount) ? amount : 0);

const styleLabel: Record<string, string> = {
  BUDGET: 'Thoughtful value',
  COMFORTABLE: 'Comfortable',
  PREMIUM: 'Premium',
  LUXURY: 'Luxury',
};

const paceLabel: Record<string, string> = {
  RELAXED: 'Unhurried',
  BALANCED: 'Balanced',
  PACKED: 'Full days',
};

const interestLabels: Record<string, string> = {
  HISTORY_HERITAGE: 'Landmarks & heritage',
  LOCAL_EXPERIENCE: 'Local life & hidden corners',
  ART_CULTURE: 'Arts, crafts & culture',
  FOOD_EXPERIENCE: 'Food & culinary',
  NATURE: 'Nature & landscapes',
  ADVENTURE: 'Adventure',
  PHOTOGRAPHY: 'Scenic viewpoints',
  NIGHTLIFE: 'Nightlife & evening walks',
  RELAXATION: 'Rest & relaxation',
  SHOPPING: 'Shopping',
  FAMILY_KIDS: 'Family-friendly',
  SPIRITUAL: 'Spiritual places',
};

export const ReviewScreen: React.FC<ReviewScreenProps> = ({ onNavigateHome, onNavigateStep }) => {
  const { tripDetails, destinations, preferences, budget } = useTripPlanning();
  const [showValidation, setShowValidation] = useState(false);
  const [handoffMessage, setHandoffMessage] = useState('');
  const mustVisitOptions = getMustVisitOptions(tripDetails, destinations);
  const issues = validateTripDraft(tripDetails, destinations, preferences, budget, mustVisitOptions);
  const request = buildPlanRequestDraft(tripDetails, destinations, preferences, budget);

  const confirm = () => {
    setShowValidation(true);
    if (issues.length > 0) {
      setHandoffMessage('');
      return;
    }
    setHandoffMessage(
      `Your trip request is validated and saved on this device. Planning will be available in Batch 3. No plan has been submitted. (${request.destinations.length} stops)`
    );
  };

  const editButton = (step: number, label: string) => (
    <button type="button" onClick={() => onNavigateStep(step)} className="min-h-10 rounded-sm px-2 text-sm font-semibold text-primary hover:bg-primary-fixed/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
      Edit {label}
    </button>
  );

  const formatDateRange = () => `${tripDetails.departureDate} – ${tripDetails.returnDate}`;

  return (
    <PlannerStepLayout
      currentStep={5}
      onNavigateHome={onNavigateHome}
      onNavigateStep={onNavigateStep}
      eyebrow="Step 5 of 5 · Review"
      title="Your journey, at a glance"
      description="Check the details before confirming your planning request."
    >
      <div className="max-w-4xl mx-auto space-y-4 pb-space-xl">
        {showValidation && issues.length > 0 && (
          <section role="alert" aria-labelledby="review-errors-title" className="rounded-md border border-error/40 bg-error-container/40 p-4">
            <h2 id="review-errors-title" className="font-semibold text-on-error-container">A few details need attention</h2>
            <ul className="mt-2 space-y-1 text-sm text-on-error-container">
              {issues.map((issue, index) => {
                const step = issue.section === 'trip-details' ? 1 : issue.section === 'destinations' ? 2 : issue.section === 'preferences' ? 3 : 4;
                return (
                  <li key={`${issue.section}-${index}`} className="flex flex-wrap items-center justify-between gap-2">
                    <span>{issue.message}</span>
                    <button type="button" onClick={() => onNavigateStep(step)} className="font-semibold underline underline-offset-2">Edit {issue.section.replace('-', ' ')}</button>
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        <section className="overflow-hidden rounded-lg border border-outline-variant/50 bg-surface-container-lowest">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-outline-variant/40 bg-surface-container-low px-5 py-4 sm:px-6">
            <div>
              <p className="text-xs font-semibold uppercase text-on-surface-variant">Your route</p>
              <h2 className="mt-1 font-headline-sm text-headline-sm font-bold">{tripDetails.origin} to {tripDetails.destination}</h2>
            </div>
            {editButton(2, 'route')}
          </div>
          <ol className="divide-y divide-outline-variant/30 px-5 sm:px-6" aria-label="Ordered route stops">
            {destinations.map((stop, index) => (
              <li key={stop.id} className="flex min-w-0 items-center gap-3 py-3.5">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-fixed text-sm font-bold text-on-primary-fixed-variant">{index + 1}</span>
                <span className="min-w-0 flex-1">
                  <span className="block break-words font-semibold">{stop.name}</span>
                  <span className="block text-sm text-on-surface-variant">{stop.nights} {stop.nights === 1 ? 'night' : 'nights'}{stop.region ? ` · ${stop.region}` : ''}</span>
                </span>
                {index < destinations.length - 1 && stop.transitToNext && (
                  <span className="hidden max-w-44 text-right text-xs text-on-surface-variant sm:block">{stop.transitToNext.title} · {stop.transitToNext.duration}</span>
                )}
              </li>
            ))}
          </ol>
          <div className="flex flex-wrap justify-between gap-2 border-t border-outline-variant/40 px-5 py-3 text-sm sm:px-6">
            <span className="text-on-surface-variant">{destinations.reduce((sum, stop) => sum + stop.nights, 0)} nights · {tripDetails.durationDays} days</span>
            <span className="font-semibold">{tripDetails.scope === 'DOMESTIC' ? 'Within India' : 'International journey'}</span>
          </div>
        </section>

        <section className="rounded-lg border border-outline-variant/50 bg-surface-container-lowest p-5 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase text-on-surface-variant">Trip details</p>
              <h2 className="mt-1 font-headline-sm text-headline-sm font-bold">Travellers & dates</h2>
            </div>
            {editButton(1, 'trip details')}
          </div>
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            <div><dt className="text-sm text-on-surface-variant">Travellers</dt><dd className="mt-1 font-semibold">{tripDetails.adults} adults · {tripDetails.children} children · {tripDetails.infants} infants</dd></div>
            <div><dt className="text-sm text-on-surface-variant">Travel dates</dt><dd className="mt-1 font-semibold">{formatDateRange()}</dd></div>
          </dl>
        </section>

        <section className="rounded-lg border border-outline-variant/50 bg-surface-container-lowest p-5 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase text-on-surface-variant">Your preferences</p>
              <h2 className="mt-1 font-headline-sm text-headline-sm font-bold">How you want to travel</h2>
            </div>
            {editButton(3, 'preferences')}
          </div>
          <dl className="mt-4 grid gap-4 sm:grid-cols-2">
            <div><dt className="text-sm text-on-surface-variant">Travel style</dt><dd className="mt-1 font-semibold">{styleLabel[preferences.travelStyle] ?? 'Not selected'}</dd></div>
            <div><dt className="text-sm text-on-surface-variant">Pace</dt><dd className="mt-1 font-semibold">{paceLabel[preferences.pace] ?? 'Not selected'}</dd></div>
            <div className="sm:col-span-2"><dt className="text-sm text-on-surface-variant">Experience interests</dt><dd className="mt-1 leading-6">{preferences.activityPreferences.map((item) => interestLabels[item] ?? item).join(' · ') || 'None selected'}</dd></div>
            <div className="sm:col-span-2"><dt className="text-sm text-on-surface-variant">Must-visit places</dt><dd className="mt-1 leading-6">{preferences.mustVisits.join(' · ') || 'None added'}</dd></div>
          </dl>
        </section>

        <section className="rounded-lg border border-outline-variant/50 bg-surface-container-lowest p-5 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase text-on-surface-variant">Budget target</p>
              <h2 className="mt-1 font-headline-sm text-headline-sm font-bold">{formatInr(budget.budgetInr)}</h2>
              <p className="mt-1 text-sm text-on-surface-variant">{budget.budgetMode === 'PER_PERSON' ? 'Per person' : 'For the total trip'} · INR</p>
            </div>
            {editButton(4, 'budget')}
          </div>
          <p className="mt-4 border-t border-outline-variant/40 pt-3 text-sm leading-6 text-on-surface-variant">This is your target, not a live quote. Category estimates will be provided when planning is available.</p>
        </section>

        {handoffMessage && <p role="status" className="rounded-md border border-secondary/40 bg-secondary-fixed/30 p-4 text-sm font-medium text-on-secondary-fixed-variant">{handoffMessage}</p>}
        <div className="flex flex-col-reverse gap-3 border-t border-outline-variant/40 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <button type="button" onClick={() => onNavigateStep(4)} className="min-h-12 rounded-md px-4 font-semibold text-on-surface-variant hover:bg-surface-container-low focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
            <span aria-hidden="true" className="material-symbols-outlined mr-1 align-middle">arrow_back</span>Back to budget
          </button>
          <button type="button" onClick={confirm} className="min-h-12 rounded-md bg-primary px-6 font-semibold text-on-primary hover:opacity-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
            Confirm trip details <span aria-hidden="true" className="material-symbols-outlined ml-1 align-middle">task_alt</span>
          </button>
        </div>
      </div>
    </PlannerStepLayout>
  );
};