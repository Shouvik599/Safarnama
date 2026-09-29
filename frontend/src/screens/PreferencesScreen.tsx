import React, { useState } from 'react';
import { useTripPlanning } from '../context/useTripPlanning';
import type { ActivityPreference, TravelPace, TravelStyle } from '../types/trip';
import { handleRadioGroupKeyDown } from '../components/planner/radioKeyboard';
import { getMustVisitOptions } from '../data/mustVisitOptions';
import { PlannerStepLayout } from './PlannerStepLayout';

interface PreferencesScreenProps {
  onNavigateHome: () => void;
  onNavigateStep: (step: number) => void;
}

const travelStyles: { value: TravelStyle; title: string; description: string }[] = [
  { value: 'BUDGET', title: 'Thoughtful value', description: 'Keep the journey comfortable and cost-conscious.' },
  { value: 'COMFORTABLE', title: 'Comfortable', description: 'A balanced stay, convenient transport, and room to explore.' },
  { value: 'PREMIUM', title: 'Premium', description: 'Give extra weight to standout stays and smoother connections.' },
  { value: 'LUXURY', title: 'Luxury', description: 'Prioritize exceptional stays and elevated experiences.' },
];

const paces: { value: TravelPace; title: string; description: string; icon: string }[] = [
  { value: 'RELAXED', title: 'Unhurried', description: 'Leave space for pauses, longer meals, and spontaneous detours.', icon: 'coffee' },
  { value: 'BALANCED', title: 'Balanced', description: 'Mix signature highlights with time to find your own rhythm.', icon: 'balance' },
  { value: 'PACKED', title: 'Full days', description: 'Make room for more sights and a lively daily schedule.', icon: 'bolt' },
];

const interests: { value: ActivityPreference; label: string; icon: string }[] = [
  { value: 'HISTORY_HERITAGE', label: 'Landmarks & heritage', icon: 'account_balance' },
  { value: 'LOCAL_EXPERIENCE', label: 'Local life & hidden corners', icon: 'explore' },
  { value: 'ART_CULTURE', label: 'Arts, crafts & culture', icon: 'palette' },
  { value: 'FOOD_EXPERIENCE', label: 'Food & culinary', icon: 'restaurant' },
  { value: 'NATURE', label: 'Nature & landscapes', icon: 'forest' },
  { value: 'ADVENTURE', label: 'Adventure', icon: 'kayaking' },
  { value: 'PHOTOGRAPHY', label: 'Scenic viewpoints', icon: 'photo_camera' },
  { value: 'NIGHTLIFE', label: 'Nightlife & evening walks', icon: 'nightlife' },
  { value: 'RELAXATION', label: 'Rest & relaxation', icon: 'spa' },
  { value: 'SHOPPING', label: 'Shopping', icon: 'shopping_bag' },
  { value: 'FAMILY_KIDS', label: 'Family-friendly', icon: 'family_restroom' },
  { value: 'SPIRITUAL', label: 'Spiritual places', icon: 'temple_hindu' },
];

export const PreferencesScreen: React.FC<PreferencesScreenProps> = ({
  onNavigateHome,
  onNavigateStep,
}) => {
  const { preferences, updatePreferences, tripDetails, destinations } = useTripPlanning();
  const [placeDraft, setPlaceDraft] = useState('');
  const [showPlaceOptions, setShowPlaceOptions] = useState(false);
  const [activePlaceIndex, setActivePlaceIndex] = useState(0);
  const [error, setError] = useState('');
  const mustVisitOptions = getMustVisitOptions(tripDetails, destinations);
  const matchingMustVisitOptions = mustVisitOptions.filter((option) => {
    const query = placeDraft.trim().toLocaleLowerCase();
    return !query || `${option.name} ${option.region}`.toLocaleLowerCase().includes(query);
  });

  const toggleInterest = (value: ActivityPreference) => {
    const selected = preferences.activityPreferences.includes(value);
    updatePreferences({
      activityPreferences: selected
        ? preferences.activityPreferences.filter((item) => item !== value)
        : [...preferences.activityPreferences, value],
    });
  };

  const addMustVisit = (place: string) => {
    if (preferences.mustVisits.some((item) => item.toLocaleLowerCase() === place.toLocaleLowerCase())) {
      setError('That place is already on your list.');
      return;
    }
    updatePreferences({ mustVisits: [...preferences.mustVisits, place] });
    setPlaceDraft('');
    setShowPlaceOptions(false);
    setActivePlaceIndex(0);
    setError('');
  };

  const continueToBudget = () => {
    if (!preferences.travelStyle || !preferences.pace) {
      setError('Choose a travel style and pace to continue.');
      return;
    }
    if (preferences.activityPreferences.some((value) => !interests.some((item) => item.value === value))) {
      setError('Remove unsupported experience interests before continuing.');
      return;
    }
    if (new Set(preferences.activityPreferences).size !== preferences.activityPreferences.length) {
      setError('Remove duplicate experience interests before continuing.');
      return;
    }
    if (preferences.mustVisits.some((place) => !place.trim())) {
      setError('Remove blank must-visit places before continuing.');
      return;
    }
    if (
      preferences.mustVisits.some(
        (place) => !mustVisitOptions.some((option) => option.name.toLocaleLowerCase() === place.trim().toLocaleLowerCase())
      )
    ) {
      setError('Remove or replace must-visit places that are not available for the current destinations.');
      return;
    }
    setError('');
    onNavigateStep(4);
  };

  return (
    <PlannerStepLayout
      currentStep={3}
      onNavigateHome={onNavigateHome}
      onNavigateStep={onNavigateStep}
      eyebrow="Step 3 of 5 · Travel preferences"
      title="How do you want to travel?"
      description="Set the rhythm and experiences that will shape your journey."
    >
      <div className="max-w-4xl mx-auto space-y-space-lg pb-space-xl">
        <section className="bg-surface-container-lowest border border-outline-variant/40 rounded-lg p-5 sm:p-7">
          <fieldset>
            <legend className="font-headline-md text-headline-md font-bold">Travel style</legend>
            <p className="mt-1 mb-5 text-on-surface-variant">Choose the comfort level that feels right for this trip.</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {travelStyles.map((style) => (
                <label key={style.value} className="cursor-pointer">
                  <input
                    className="peer sr-only"
                    type="radio"
                    name="travel-style"
                    value={style.value}
                    checked={preferences.travelStyle === style.value}
                    onChange={() => updatePreferences({ travelStyle: style.value })}
                    onKeyDown={handleRadioGroupKeyDown}
                  />
                  <span className="block h-full min-h-24 rounded-md border border-outline-variant/60 p-4 transition peer-checked:border-primary peer-checked:bg-primary-fixed/40 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primary">
                    <span className="block font-semibold">{style.title}</span>
                    <span className="mt-1 block text-sm leading-5 text-on-surface-variant">{style.description}</span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
        </section>

        <section className="bg-surface-container-lowest border border-outline-variant/40 rounded-lg p-5 sm:p-7">
          <fieldset>
            <legend className="font-headline-md text-headline-md font-bold">Travel pace</legend>
            <p className="mt-1 mb-5 text-on-surface-variant">Choose how full you want each day to feel.</p>
            <div className="grid gap-3 md:grid-cols-3">
              {paces.map((pace) => (
                <label key={pace.value} className="cursor-pointer">
                  <input
                    className="peer sr-only"
                    type="radio"
                    name="travel-pace"
                    value={pace.value}
                    checked={preferences.pace === pace.value}
                    onChange={() => updatePreferences({ pace: pace.value })}
                    onKeyDown={handleRadioGroupKeyDown}
                  />
                  <span className="block h-full min-h-36 rounded-md border border-outline-variant/60 p-4 transition peer-checked:border-primary peer-checked:bg-primary-fixed/40 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primary">
                    <span className="flex items-center gap-2 font-semibold">
                      <span aria-hidden="true" className="material-symbols-outlined text-primary">{pace.icon}</span>
                      {pace.title}
                    </span>
                    <span className="mt-2 block text-sm leading-5 text-on-surface-variant">{pace.description}</span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
        </section>

        <section className="bg-surface-container-lowest border border-outline-variant/40 rounded-lg p-5 sm:p-7">
          <fieldset>
            <legend className="font-headline-md text-headline-md font-bold">Experience preferences</legend>
            <p className="mt-1 mb-5 text-on-surface-variant">Select the kinds of moments you would like along the route.</p>
            <div className="flex flex-wrap gap-2.5">
              {interests.map((interest) => {
                const checked = preferences.activityPreferences.includes(interest.value);
                return (
                  <label key={interest.value} className="cursor-pointer">
                    <input
                      className="peer sr-only"
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleInterest(interest.value)}
                    />
                    <span className="inline-flex min-h-11 items-center gap-2 rounded-md border border-outline-variant/60 px-3 py-2 text-sm transition peer-checked:border-primary peer-checked:bg-primary-fixed/50 peer-checked:text-on-primary-fixed-variant peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primary">
                      <span aria-hidden="true" className="material-symbols-outlined text-[18px]">{interest.icon}</span>
                      {interest.label}
                      {checked && <span className="sr-only">selected</span>}
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>
        </section>

        <section className="bg-surface-container-lowest border border-outline-variant/40 rounded-lg p-5 sm:p-7">
          <div>
            <h2 className="font-headline-md text-headline-md font-bold">Must-visit places</h2>
            <p className="mt-1 mb-5 text-on-surface-variant">
              Choose a source-backed attraction in one of your route cities. City names and restaurants are not Must-visits.
            </p>
          </div>
          <div className="relative">
            <label htmlFor="must-visit-input" className="sr-only">Search must-visit places in your destinations</label>
            <input
              id="must-visit-input"
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={showPlaceOptions}
              aria-controls="must-visit-options"
              aria-activedescendant={
                showPlaceOptions && matchingMustVisitOptions[activePlaceIndex]
                  ? `must-visit-option-${activePlaceIndex}`
                  : undefined
              }
              autoComplete="off"
              value={placeDraft}
              onFocus={() => setShowPlaceOptions(true)}
              onChange={(event) => {
                setPlaceDraft(event.target.value);
                setActivePlaceIndex(0);
                setShowPlaceOptions(true);
                setError('');
              }}
              onKeyDown={(event) => {
                if (event.key === 'Escape') {
                  setShowPlaceOptions(false);
                  return;
                }
                if (event.key === 'ArrowDown' && matchingMustVisitOptions.length > 0) {
                  event.preventDefault();
                  setShowPlaceOptions(true);
                  setActivePlaceIndex((index) => (index + 1) % matchingMustVisitOptions.length);
                } else if (event.key === 'ArrowUp' && matchingMustVisitOptions.length > 0) {
                  event.preventDefault();
                  setActivePlaceIndex((index) => (index - 1 + matchingMustVisitOptions.length) % matchingMustVisitOptions.length);
                } else if (event.key === 'Enter') {
                  event.preventDefault();
                  const selected = matchingMustVisitOptions[activePlaceIndex];
                  if (selected) addMustVisit(selected.name);
                  else setError('Choose a place from the suggestions for your destinations.');
                }
              }}
              placeholder="Search places in your selected destinations"
              className="min-h-11 w-full min-w-0 rounded-md border border-outline-variant bg-surface px-3 py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            />
            {showPlaceOptions && (
              <div
                id="must-visit-options"
                role="listbox"
                aria-label="Must-visit suggestions"
                className="absolute left-0 right-0 z-20 mt-1 max-h-64 overflow-y-auto rounded-md border border-outline-variant bg-surface-container-lowest shadow-lg"
              >
                {matchingMustVisitOptions.length > 0 ? matchingMustVisitOptions.map((option, index) => (
                  <button
                    id={`must-visit-option-${index}`}
                    key={`${option.name}-${option.region}`}
                    type="button"
                    role="option"
                    aria-selected={index === activePlaceIndex}
                    onMouseDown={(event) => event.preventDefault()}
                    onMouseEnter={() => setActivePlaceIndex(index)}
                    onClick={() => addMustVisit(option.name)}
                    className={`flex min-h-12 w-full items-center justify-between gap-3 px-3 py-2 text-left hover:bg-surface-container-low ${index === activePlaceIndex ? 'bg-surface-container-low' : ''}`}
                  >
                    <span className="min-w-0">
                      <span className="block break-words text-sm font-semibold">{option.name}</span>
                      <span className="block text-xs text-on-surface-variant">{option.region} · {option.kind}</span>
                    </span>
                    <span aria-hidden="true" className="material-symbols-outlined shrink-0 text-primary text-[18px]">add</span>
                  </button>
                )) : (
                  <p className="px-3 py-3 text-sm text-on-surface-variant">
                    No matching places in the selected destinations.
                  </p>
                )}
              </div>
            )}
          </div>
          {preferences.mustVisits.length > 0 && (
            <ul aria-label="Must-visit places" className="mt-4 flex flex-wrap gap-2">
              {preferences.mustVisits.map((place) => (
                <li key={place} className="inline-flex min-h-10 items-center gap-2 rounded-md bg-surface-container-low px-3 py-1.5 text-sm">
                  <span>
                    {place}
                    {!mustVisitOptions.some((option) => option.name.toLocaleLowerCase() === place.trim().toLocaleLowerCase()) && (
                      <span className="ml-1 text-error">(not in the current attraction catalog)</span>
                    )}
                  </span>
                  <button
                    type="button"
                    aria-label={`Remove ${place}`}
                    onClick={() => updatePreferences({ mustVisits: preferences.mustVisits.filter((item) => item !== place) })}
                    className="rounded-sm p-1 text-on-surface-variant hover:text-error focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
                  >
                    <span aria-hidden="true" className="material-symbols-outlined text-[18px]">close</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {error && <p role="alert" className="mt-3 text-sm font-medium text-error">{error}</p>}
        </section>

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button type="button" onClick={() => onNavigateStep(2)} className="min-h-12 rounded-md px-4 font-semibold text-on-surface-variant hover:bg-surface-container-low focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
            <span aria-hidden="true" className="material-symbols-outlined mr-1 align-middle">arrow_back</span>Back to destinations
          </button>
          <button type="button" onClick={continueToBudget} className="min-h-12 rounded-md bg-primary px-6 font-semibold text-on-primary hover:opacity-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
            Continue to budget <span aria-hidden="true" className="material-symbols-outlined ml-1 align-middle">arrow_forward</span>
          </button>
        </div>
      </div>
    </PlannerStepLayout>
  );
};