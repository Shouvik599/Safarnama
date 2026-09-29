import React from 'react';
import type { DestinationSuggestion } from '../../types/trip';

interface SuggestionCardProps {
  suggestion: DestinationSuggestion;
  isAdded: boolean;
  onAdd: () => void;
}

export const SuggestionCard: React.FC<SuggestionCardProps> = ({
  suggestion,
  isAdded,
  onAdd,
}) => {
  return (
    <div className="bg-surface-container-lowest rounded-2xl p-space-md shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
      <div className="flex flex-col">
        {/* Photo with inset badge */}
        <div className="h-32 w-full rounded-xl overflow-hidden mb-space-sm relative bg-surface-dim">
          <img
            src={suggestion.imageUrl}
            alt={suggestion.imageAlt || suggestion.name}
            className="w-full h-full object-cover"
            loading="lazy"
          />
          <span className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-surface-container-lowest/90 backdrop-blur-sm text-on-surface font-label-caption text-label-caption font-semibold shadow-xs">
            {suggestion.tag}
          </span>
        </div>

        {/* Title & Description */}
        <h4 className="font-headline-sm text-headline-sm text-on-surface mb-1 font-bold">
          {suggestion.name}
        </h4>
        <p className="font-body-sm text-body-sm text-on-surface-variant line-clamp-2 mb-4">
          {suggestion.description}
        </p>
      </div>

      {/* Action Button */}
      <button
        type="button"
        disabled={isAdded}
        onClick={onAdd}
        className={`w-full py-2 rounded-lg font-label-md text-label-md font-semibold flex items-center justify-center gap-1 transition-all ${
          isAdded
            ? 'bg-surface-container text-on-surface-variant/60 cursor-default'
            : 'bg-surface-container-low hover:bg-primary-fixed hover:text-on-primary-fixed text-primary cursor-pointer active:scale-98'
        }`}
      >
        <span className="material-symbols-outlined text-[16px]">
          {isAdded ? 'check' : 'add'}
        </span>
        <span>{isAdded ? 'Added to Route' : suggestion.actionLabel}</span>
      </button>
    </div>
  );
};
