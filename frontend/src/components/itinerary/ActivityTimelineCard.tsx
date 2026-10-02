import React, { useState } from 'react';
import type { ActivitySlot } from '../../types/itinerary';

interface ActivityTimelineCardProps {
  activity: ActivitySlot;
  timeWindow?: string;
  onNavigateDetail?: () => void;
  onNavigateExperience?: () => void;
}

export const ActivityTimelineCard: React.FC<ActivityTimelineCardProps> = ({
  activity,
  timeWindow = '08:30 – 10:30',
  onNavigateDetail,
  onNavigateExperience,
}) => {
  const [expanded, setExpanded] = useState(false);
  const { poi, notes, is_weather_substituted, weather_note } = activity;

  const categoryLabels: Record<string, { label: string; icon: string }> = {
    SPIRITUAL: { label: 'Spiritual & Zen', icon: 'self_improvement' },
    HISTORY_HERITAGE: { label: 'History & Heritage', icon: 'account_balance' },
    NATURE: { label: 'Nature & Gardens', icon: 'park' },
    FOOD_EXPERIENCE: { label: 'Gastronomy', icon: 'restaurant' },
    LOCAL_EXPERIENCE: { label: 'Local Immersion', icon: 'explore' },
    ART_CULTURE: { label: 'Art & Guilds', icon: 'palette' },
  };

  const catMeta = categoryLabels[poi.category] || {
    label: poi.category.replace('_', ' '),
    icon: 'place',
  };

  const formatInr = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);

  return (
    <div className="group relative flex flex-col p-space-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/30 hover:border-primary/50 transition-all shadow-sm hover:shadow-md">
      {/* Top Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-space-xs pb-space-sm border-b border-outline-variant/15">
        <div className="flex items-center gap-space-xs">
          <span className="flex items-center gap-1 font-label-sm text-label-sm font-bold text-primary bg-primary/10 px-space-sm py-0.5 rounded-full">
            <span className="material-symbols-outlined text-[14px]">schedule</span>
            {timeWindow}
          </span>
          <span className="flex items-center gap-1 font-label-caption text-label-caption font-semibold text-on-surface-variant bg-surface-container px-space-sm py-0.5 rounded-full">
            <span className="material-symbols-outlined text-[13px]">{catMeta.icon}</span>
            {catMeta.label}
          </span>
        </div>

        <div className="flex items-center gap-space-xs">
          {poi.is_must_visit && (
            <span className="font-label-caption text-label-caption font-bold text-on-primary bg-primary px-space-sm py-0.5 rounded-full flex items-center gap-1 shadow-sm">
              <span className="material-symbols-outlined text-[12px]">verified</span>
              Must Experience
            </span>
          )}
          {is_weather_substituted && (
            <span className="font-label-caption text-label-caption font-bold text-on-error bg-error px-space-sm py-0.5 rounded-full">
              Weather Alternate
            </span>
          )}
          <span className="font-label-sm text-label-sm font-bold text-on-surface">
            {poi.estimated_cost_inr > 0 ? formatInr(poi.estimated_cost_inr) : 'Included in Pass'}
          </span>
        </div>
      </div>

      {/* Title & Description */}
      <div className="pt-space-sm">
        <h4 className="font-headline-sm text-headline-sm font-bold text-on-surface group-hover:text-primary transition-colors">
          {poi.name}
        </h4>
        <div className="flex items-center gap-1 text-on-surface-variant font-label-caption text-label-caption mt-0.5 mb-space-xs">
          <span className="material-symbols-outlined text-[14px] text-primary" aria-hidden="true">
            location_on
          </span>
          <span>{poi.city}</span>
          {poi.address && <span>• {poi.address}</span>}
        </div>
        <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
          {poi.description}
        </p>
      </div>

      {/* Weather substitution advisory */}
      {is_weather_substituted && weather_note && (
        <div className="mt-space-sm p-space-sm rounded-xl bg-surface-container-high border border-outline-variant/30 flex items-start gap-space-xs text-on-surface-variant font-label-caption text-label-caption">
          <span className="material-symbols-outlined text-[16px] text-primary" aria-hidden="true">
            cloud
          </span>
          <div>
            <span className="font-bold text-on-surface">Substituted for weather comfort:</span>{' '}
            {weather_note}
          </div>
        </div>
      )}

      {/* Curator notes / Insider access */}
      {notes && (
        <div className="mt-space-sm pt-space-xs text-on-surface-variant font-body-sm text-body-sm bg-surface-container-low/60 p-space-sm rounded-xl border border-outline-variant/20 flex items-start gap-space-xs">
          <span className="material-symbols-outlined text-[16px] text-primary mt-0.5" aria-hidden="true">
            lightbulb
          </span>
          <div className="flex-1">
            <span className="font-bold text-on-surface font-label-caption text-label-caption uppercase tracking-wider block">
              Curator Access Guidance
            </span>
            <span className="text-on-surface-variant text-body-sm leading-normal">{notes}</span>
          </div>
        </div>
      )}

      {/* Bottom CTA / Action */}
      <div className="mt-space-md pt-space-xs flex items-center justify-between">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="text-on-surface-variant hover:text-on-surface font-label-sm text-label-sm font-semibold flex items-center gap-1 transition-colors cursor-pointer"
        >
          <span>{expanded ? 'Hide Access Protocols' : 'View Access Protocols'}</span>
          <span className="material-symbols-outlined text-[16px]">
            {expanded ? 'expand_less' : 'expand_more'}
          </span>
        </button>

        {onNavigateExperience && (
          <button
            type="button"
            onClick={onNavigateExperience}
            className="flex items-center gap-1 px-space-md py-1.5 rounded-xl bg-primary/10 hover:bg-primary hover:text-on-primary text-primary font-label-sm text-label-sm font-bold transition-all shadow-xs group/btn cursor-pointer"
          >
            <span>Experience Details</span>
            <span className="material-symbols-outlined text-[16px]">attractions</span>
          </button>
        )}

        {onNavigateDetail && (
          <button
            type="button"
            onClick={onNavigateDetail}
            className="flex items-center gap-1 px-space-md py-1.5 rounded-xl bg-surface-container hover:bg-primary hover:text-on-primary text-on-surface font-label-sm text-label-sm font-bold transition-all shadow-xs group/btn cursor-pointer"
          >
            <span>Timeline Deep-Dive</span>
            <span className="material-symbols-outlined text-[16px] group-hover/btn:translate-x-0.5 transition-transform">
              arrow_forward
            </span>
          </button>
        )}
      </div>

      {expanded && (
        <div className="mt-space-sm p-space-md rounded-xl bg-surface-container border border-outline-variant/30 text-on-surface font-body-sm text-body-sm space-y-2 animate-fadeIn">
          <div className="flex items-center gap-1.5 font-bold font-label-sm text-label-sm text-primary">
            <span className="material-symbols-outlined text-[16px]">how_to_reg</span>
            Arrival & Verification Protocol
          </div>
          <p className="text-on-surface-variant text-body-sm leading-relaxed">
            Present your Safarnama digital pass voucher upon entrance. Priority quiet entrance gate is active for early morning entry windows. For footwear removal at tatami temples, shoe bags are provided at engawa verandas.
          </p>
        </div>
      )}
    </div>
  );
};
