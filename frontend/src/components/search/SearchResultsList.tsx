import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SlidersHorizontal, MapPin, AlertTriangle, Satellite } from 'lucide-react';
import { SearchResult } from '../../types/api';
import { useIntelligence } from '../../context/IntelligenceContext';

interface SearchResultsListProps {
  results: SearchResult[];
  onSelectResult?: (res: SearchResult) => void;
}

export const SearchResultsList: React.FC<SearchResultsListProps> = ({ results, onSelectResult }) => {
  const {
    selectedResult, setSelectedResult, setMapCenter, setMapZoom,
    searchCoverage, searchMessage, searchAvailableAois,
  } = useIntelligence();
  const navigate = useNavigate();
  const [sortBy, setSortBy] = useState<'relevance' | 'date' | 'confidence'>('relevance');

  const sortedResults = [...results].sort((a, b) => {
    if (sortBy === 'relevance') return b.relevanceScore - a.relevanceScore;
    if (sortBy === 'confidence') return b.confidence - a.confidence;
    if (sortBy === 'date') return new Date(b.acquisitionDate).getTime() - new Date(a.acquisitionDate).getTime();
    return 0;
  });

  const handleSelect = (res: SearchResult) => {
    setSelectedResult(res);
    setMapCenter([res.latitude, res.longitude]);
    setMapZoom(13);
    if (onSelectResult) onSelectResult(res);
  };

  const handleAnalyze = (e: React.MouseEvent, res: SearchResult) => {
    e.stopPropagation();
    navigate('/analysis/analysis_tumakuru_01');
  };

  if (searchCoverage === 'UNAVAILABLE') {
    return (
      <div className="flex flex-col items-center justify-center py-8 px-4 space-y-4 text-center">
        <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
          <AlertTriangle className="w-6 h-6 text-amber-400" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-amber-300 font-mono uppercase tracking-widest mb-1">
            Location Not Indexed
          </h4>
          <p className="text-xs text-slate-400 font-sans leading-relaxed max-w-[260px]">
            {searchMessage || 'This location is not currently in the indexed catalog.'}
          </p>
        </div>
        {searchAvailableAois.length > 0 && (
          <div className="w-full bg-white/[0.03] border border-white/[0.07] rounded-lg p-3 text-left">
            <div className="flex items-center gap-1.5 mb-2">
              <Satellite className="w-3 h-3 text-cyan-400" />
              <span className="text-[10px] font-mono uppercase tracking-widest text-cyan-400 font-semibold">
                Indexed AOIs
              </span>
            </div>
            <ul className="space-y-1">
              {searchAvailableAois.map((aoi, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <MapPin className="w-3 h-3 text-emerald-400 mt-0.5 shrink-0" />
                  <span className="text-[11px] text-slate-300 font-sans">{aoi}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="py-12 text-center text-slate-400 font-mono text-xs">
        No satellite detections matching query.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-2.5">
      {/* Header & Controls */}
      <div className="flex items-center justify-between px-1 pb-2 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono uppercase tracking-widest text-slate-300 font-semibold">
            RETRIEVED TARGETS
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded border border-white/10 text-slate-400">
            {results.length}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
          <SlidersHorizontal className="w-3 h-3 text-slate-400" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-[#04060a] border border-white/10 rounded px-1.5 py-0.5 text-slate-300 text-[10px] cursor-pointer"
          >
            <option value="relevance">SORT: MATCH</option>
            <option value="confidence">SORT: CONFIDENCE</option>
            <option value="date">SORT: DATE</option>
          </select>
        </div>
      </div>

      {/* Result Rows / Editorial Records */}
      <div className="flex-1 overflow-y-auto divide-y divide-white/[0.08] pr-1">
        {sortedResults.map((res, index) => {
          const isSelected = selectedResult?.id === res.id;
          const indexNum = String(index + 1).padStart(2, '0');
          return (
            <div
              key={res.id}
              onClick={() => handleSelect(res)}
              className={`group relative py-3.5 px-2 transition-all cursor-pointer ${
                isSelected
                  ? 'bg-white/[0.04] border-l-2 border-emerald-400 pl-3'
                  : 'hover:bg-white/[0.02] border-l-2 border-transparent'
              }`}
            >
              {/* Record Header: Index, Sensor, Date */}
              <div className="flex items-baseline justify-between gap-2 mb-1.5">
                <div className="flex items-baseline gap-2">
                  <span className="font-mono text-xs font-bold text-slate-400 group-hover:text-emerald-400 transition-colors">
                    {indexNum}
                  </span>
                  <span className="font-mono text-[10px] tracking-widest uppercase text-cyan-400 font-semibold">
                    {res.sensor || 'SENTINEL-2 MSI'}
                  </span>
                </div>
                <span className="font-mono text-[10px] text-slate-400 tracking-wider">
                  {res.acquisitionDate || '18 JUN 2026'}
                </span>
              </div>

              {/* Title & Match Score */}
              <div className="flex items-start justify-between gap-3 my-1.5">
                <h4 className="text-xs font-heading font-bold text-white group-hover:text-emerald-300 transition-colors leading-snug">
                  {res.title}
                </h4>

                <div className="text-right shrink-0">
                  <span className="block font-mono text-xs font-extrabold text-emerald-400 leading-none">
                    {res.relevanceScore ? `${res.relevanceScore}%` : '94.8%'}
                  </span>
                  <span className="font-mono text-[8px] uppercase tracking-widest text-slate-400 block mt-0.5">
                    MATCH
                  </span>
                </div>
              </div>

              {/* Details line if available */}
              {res.details && (
                <p className="text-[11px] text-slate-400 font-sans line-clamp-1 mb-2">
                  {res.details}
                </p>
              )}

              {/* Coordinates & Action Link */}
              <div className="flex items-center justify-between font-mono text-[10px] text-slate-400 pt-1">
                <span className="text-slate-400 tracking-wider">
                  {res.latitude?.toFixed(4)}° N &nbsp; {res.longitude?.toFixed(4)}° E
                </span>

                <button
                  type="button"
                  onClick={(e) => handleAnalyze(e, res)}
                  className="inline-flex items-center gap-1 text-slate-400 group-hover:text-emerald-300 font-semibold tracking-wider uppercase transition-colors"
                >
                  VIEW ANALYSIS &rarr;
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
