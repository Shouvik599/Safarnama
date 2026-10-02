import React from 'react';
import type { TransportMilestone } from '../../types/itinerary';

interface TransportMilestoneFlowProps {
  milestones: TransportMilestone[];
}

export const TransportMilestoneFlow: React.FC<TransportMilestoneFlowProps> = ({
  milestones,
}) => {
  return (
    <div className="w-full bg-surface-container-lowest rounded-2xl p-space-lg border border-outline-variant/30 shadow-sm">
      <div className="flex items-center justify-between mb-space-lg">
        <div className="flex items-center gap-space-xs">
          <span className="material-symbols-outlined text-[20px] text-primary" aria-hidden="true">
            route
          </span>
          <h3 className="font-headline-sm text-headline-sm font-bold text-on-surface">
            Synchronized Corridor Milestone Flow
          </h3>
        </div>
        <span className="font-label-caption text-label-caption text-on-surface-variant font-semibold bg-surface-container px-space-md py-1 rounded-full">
          {milestones.length} Checkpoints Coordinated
        </span>
      </div>

      <div className="relative">
        {/* Horizontal connecting track line behind nodes on md+ */}
        <div className="hidden md:block absolute top-7 left-8 right-8 h-0.5 bg-outline-variant/30 -z-0" />

        <div className="grid grid-cols-1 md:grid-cols-5 gap-space-md relative z-10">
          {milestones.map((node, index) => {
            const isCompleted = node.status === 'completed';
            const isActive = node.status === 'active';

            return (
              <div
                key={node.time + node.label}
                className={`flex flex-col p-space-md rounded-xl transition-all border ${
                  isActive
                    ? 'bg-primary/5 border-primary shadow-sm'
                    : 'bg-surface-container-low/70 border-outline-variant/20'
                }`}
              >
                {/* Node icon & status circle */}
                <div className="flex items-center justify-between mb-space-sm">
                  <div className="relative">
                    {isActive && (
                      <span className="absolute -inset-1 rounded-full bg-primary-container/50 animate-ping" />
                    )}
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-label-sm ${
                        isCompleted
                          ? 'bg-secondary text-on-secondary'
                          : isActive
                          ? 'bg-primary text-on-primary shadow-md'
                          : 'bg-surface-container-high text-on-surface-variant'
                      }`}
                    >
                      <span className="material-symbols-outlined text-[18px]">
                        {isCompleted ? 'check' : node.icon || 'circle'}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`font-label-caption text-label-caption font-bold px-2 py-0.5 rounded-full ${
                      isActive
                        ? 'bg-primary text-on-primary'
                        : isCompleted
                        ? 'bg-secondary/20 text-secondary'
                        : 'bg-surface-container text-on-surface-variant'
                    }`}
                  >
                    Checkpoint 0{index + 1}
                  </span>
                </div>

                {/* Node Timing & Labels */}
                <span className="font-label-sm text-label-sm font-bold text-primary">
                  {node.time}
                </span>
                <h4 className="font-headline-sm text-[16px] font-bold text-on-surface mt-0.5 leading-snug">
                  {node.label}
                </h4>
                <div className="flex items-center gap-1 font-label-caption text-label-caption text-on-surface-variant mt-1 font-medium">
                  <span className="material-symbols-outlined text-[13px] text-primary" aria-hidden="true">
                    pin_drop
                  </span>
                  <span className="truncate">{node.location}</span>
                </div>

                <p className="font-body-sm text-[13px] text-on-surface-variant mt-space-xs leading-relaxed">
                  {node.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
