import React from 'react';

interface ConfidenceBadgeProps {
  score: number; // 0.0 to 1.0 or 0 to 100
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  score,
  size = 'md',
  showLabel = true,
}) => {
  // Normalize to 0-100 scale
  const normalized = score > 1.0 ? Math.round(score) : Math.round(score * 100);

  let tier: 'HIGH' | 'MEDIUM' | 'LOW' = 'HIGH';
  let colorClass = 'text-emerald-400 stroke-emerald-500 border-emerald-500/30 bg-emerald-500/10';
  let badgeBorder = 'border-emerald-500/30';

  if (normalized < 70) {
    tier = 'LOW';
    colorClass = 'text-rose-400 stroke-rose-500 border-rose-500/30 bg-rose-500/10';
    badgeBorder = 'border-rose-500/30';
  } else if (normalized < 85) {
    tier = 'MEDIUM';
    colorClass = 'text-amber-400 stroke-amber-500 border-amber-500/30 bg-amber-500/10';
    badgeBorder = 'border-amber-500/30';
  }

  // SVG Circular progress
  const radius = 16;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalized / 100) * circumference;

  if (size === 'sm') {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border ${badgeBorder} bg-slate-900/60 text-xs font-mono`}>
        <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
        <span className="font-semibold text-slate-200">{normalized}%</span>
        {showLabel && <span className="text-[10px] text-slate-400 font-sans tracking-wide">{tier}</span>}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="relative flex items-center justify-center w-11 h-11">
        <svg className="w-11 h-11 transform -rotate-90" viewBox="0 0 40 40">
          <circle
            cx="20"
            cy="20"
            r={radius}
            stroke="currentColor"
            strokeWidth="3.5"
            fill="transparent"
            className="text-slate-800"
          />
          <circle
            cx="20"
            cy="20"
            r={radius}
            stroke="currentColor"
            strokeWidth="3.5"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className={`transition-all duration-700 ease-out ${colorClass.split(' ')[1]}`}
          />
        </svg>
        <span className="absolute font-mono text-xs font-bold text-slate-100">{normalized}%</span>
      </div>
      {showLabel && (
        <div className="flex flex-col">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">Confidence</span>
          <span className={`text-xs font-semibold tracking-wide ${colorClass.split(' ')[0]}`}>{tier} CERTAINTY</span>
        </div>
      )}
    </div>
  );
};
