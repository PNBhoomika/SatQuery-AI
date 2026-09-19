import React from 'react';

interface TelemetryPillProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
}

export const TelemetryPill: React.FC<TelemetryPillProps> = ({ label, value, icon }) => {
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded border border-slate-800 bg-slate-900/80 text-xs font-mono">
      {icon && <span className="text-emerald-400">{icon}</span>}
      <span className="text-slate-400 uppercase tracking-wider text-[10px]">{label}:</span>
      <span className="font-medium text-slate-200">{value}</span>
    </div>
  );
};
