/**
 * SearchPage — Member 5 Page
 * Full-screen dedicated search interface. Analyst can run natural language or
 * image-based searches and browse results with full metadata panels.
 * All search calls go through apiService → Member 4 REST API.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, SlidersHorizontal, ArrowUpRight, Database, Satellite } from 'lucide-react';
import { SearchBar } from '../components/search/SearchBar';
import { SearchResultsList } from '../components/search/SearchResultsList';
import { MetadataPanel } from '../components/common/MetadataPanel';
import { ConfidenceBadge } from '../components/common/ConfidenceBadge';
import { useIntelligence } from '../context/IntelligenceContext';

const MOCK_MODE = import.meta.env.VITE_USE_MOCK_API === 'true';

export const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const { searchResults, selectedResult, isSearching, searchError, systemHealth } = useIntelligence();
  const [showMetadata, setShowMetadata] = useState(false);

  return (
    <div className="min-h-screen pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto page-bg text-[#f8fafc] space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-6">
        <div>
          <div className="inline-flex items-center gap-2 font-mono text-[11px] text-cyan-400 uppercase tracking-widest mb-1.5">
            <Search className="w-3.5 h-3.5" />
            <span>SEMANTIC RETRIEVAL // REMOTECLIP 512-DIM</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
            SEARCH EARTH ARCHIVES.
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-sans mt-2 max-w-2xl leading-relaxed">
            Query satellite imagery archives using natural language phrases or upload target image tiles.
            Results are ranked by cosine similarity from the vector index.
          </p>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-2 font-mono text-xs shrink-0">
          {MOCK_MODE && (
            <div className="px-2.5 py-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-400 text-[10px] font-semibold animate-pulse">
              MOCK DATA ACTIVE
            </div>
          )}
          <div className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60">
            <span className="text-slate-400">Vector Index:</span>{' '}
            <span className="font-bold text-white">
              {systemHealth?.vector_database?.indexed_tiles_count ?? '—'} tiles
            </span>
          </div>
          <div className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60">
            <span className="text-slate-400">Results:</span>{' '}
            <span className="font-bold text-emerald-400">{searchResults.length}</span>
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="max-w-3xl">
        <SearchBar />
      </div>

      {/* Error State */}
      {searchError && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/[0.05] text-xs font-mono text-rose-300">
          {searchError}
        </div>
      )}

      {/* Loading shimmer */}
      {isSearching && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-36 rounded-xl border border-white/[0.06] bg-slate-900/40 animate-pulse" />
          ))}
        </div>
      )}

      {/* Results + Metadata Layout */}
      {!isSearching && searchResults.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Results Stream (left) */}
          <div className="lg:col-span-7 xl:col-span-8">
            <div className="flex items-center justify-between mb-3 px-1">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold">
                Ranked Results ({searchResults.length})
              </span>
              <button
                type="button"
                onClick={() => setShowMetadata(!showMetadata)}
                className={`flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-1 rounded border transition-colors ${
                  showMetadata
                    ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300'
                    : 'border-slate-700 bg-slate-900 text-slate-400 hover:text-slate-200'
                }`}
              >
                <Database className="w-3 h-3" />
                <span>{showMetadata ? 'Hide' : 'Show'} Full Metadata</span>
              </button>
            </div>

            {/* Expanded result cards with full metadata inline */}
            {showMetadata ? (
              <div className="space-y-4">
                {searchResults.map((res) => (
                  <div
                    key={res.id}
                    className="rounded-2xl border border-white/[0.08] bg-[#0d1117]/80 p-5 space-y-4 shadow-xl"
                  >
                    {/* Card top */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-4">
                        {/* Thumbnail */}
                        <div className="w-20 h-20 rounded-lg overflow-hidden border border-slate-800 shrink-0 bg-slate-950">
                          <img
                            src={res.thumbnail}
                            alt={res.title}
                            className="w-full h-full object-cover"
                            onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
                          />
                        </div>
                        <div>
                          <h3 className="text-sm font-heading font-bold text-white">{res.title}</h3>
                          <div className="flex items-center gap-2 mt-1 text-[11px] font-mono text-slate-400">
                            <Satellite className="w-3 h-3" />
                            <span>{res.sensor}</span>
                            <span className="text-slate-600">•</span>
                            <span>{res.acquisitionDate}</span>
                          </div>
                          {res.category && (
                            <span className="mt-1.5 inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                              {res.category}
                            </span>
                          )}
                          {res.details && (
                            <p className="mt-1.5 text-xs text-slate-400 font-sans leading-relaxed max-w-md">
                              {res.details}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="shrink-0 flex flex-col items-end gap-2">
                        <span className="text-sm font-mono font-bold text-emerald-400">
                          {res.relevanceScore}% Match
                        </span>
                        <ConfidenceBadge score={res.confidence} size="sm" />
                      </div>
                    </div>

                    {/* Full Metadata Panel inline */}
                    <MetadataPanel tileId={`tile_${res.id}`} compact={false} />

                    {/* Action */}
                    <div className="flex justify-end pt-1">
                      <button
                        type="button"
                        onClick={() => navigate('/analysis/analysis_tumakuru_01')}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono font-bold text-xs uppercase tracking-wider transition-all"
                      >
                        <span>Open Bi-Temporal Slider</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 rounded-xl border border-white/[0.08] bg-[#0d1117]/80">
                <SearchResultsList results={searchResults} />
              </div>
            )}
          </div>

          {/* Metadata Sidebar (right) — shows selected result metadata */}
          <div className="lg:col-span-5 xl:col-span-4 space-y-4">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 px-1 block">
              Selected Tile Metadata
            </span>
            {selectedResult ? (
              <MetadataPanel tileId={`tile_${selectedResult.id}`} />
            ) : (
              <MetadataPanel tileId={null} />
            )}

            {/* API Mode Indicator */}
            <div className="p-3 rounded-xl border border-white/[0.06] bg-[#0d1117]/60 text-[10px] font-mono text-slate-500 space-y-1">
              <div className="flex justify-between">
                <span>Mode</span>
                <span className={MOCK_MODE ? 'text-amber-400' : 'text-emerald-400'}>
                  {MOCK_MODE ? 'MOCK API' : 'LIVE API'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Endpoint</span>
                <span className="text-slate-400">{import.meta.env.VITE_API_BASE_URL || '/api'}</span>
              </div>
              <div className="flex justify-between">
                <span>Search Engine</span>
                <span className="text-slate-400">Member 2 (RemoteCLIP / Qdrant)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isSearching && searchResults.length === 0 && !searchError && (
        <div className="py-20 text-center space-y-3">
          <Search className="w-10 h-10 text-slate-700 mx-auto" />
          <p className="text-slate-400 font-sans text-sm">Enter a query above to search satellite imagery.</p>
          <p className="text-slate-600 font-mono text-xs">
            Example: "Find new construction near water bodies in Karnataka"
          </p>
        </div>
      )}
    </div>
  );
};
