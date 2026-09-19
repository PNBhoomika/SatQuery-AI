import React from 'react';
import { AlertStatus } from '../../types/api';

interface StatusBadgeProps {
  status: AlertStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = (status || 'PENDING REVIEW').toUpperCase();

  let colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  let dotColor = 'bg-amber-400';

  if (normalized.includes('CONFIRM')) {
    colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    dotColor = 'bg-emerald-400';
  } else if (normalized.includes('REJECT')) {
    colorClasses = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    dotColor = 'bg-rose-400';
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-mono font-medium tracking-wide uppercase ${colorClasses} ${padding}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor} animate-pulse`}></span>
      {normalized}
    </span>
  );
};
