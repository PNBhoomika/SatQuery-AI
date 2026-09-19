import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  Layers,
  ShieldAlert,
  SlidersHorizontal,
  ArrowUpRight,
  Database,
  Satellite,
  Compass,
  CheckCircle2,
  XCircle,
  Eye,
} from 'lucide-react';
import { SearchBar } from '../components/search/SearchBar';
import { SearchResultsList } from '../components/search/SearchResultsList';
import { MapView } from '../components/map/MapView';
import { MetadataPanel } from '../components/common/MetadataPanel';
import { ClusterView } from '../components/common/ClusterView';
import { ConfidenceBadge } from '../components/common/ConfidenceBadge';
import { FeedbackModal } from '../components/feedback/FeedbackModal';
import { useIntelligence } from '../context/IntelligenceContext';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    searchResults,
    selectedResult,
    alerts,
    clusters,
    feedbackModalAlert,
    setFeedbackModalAlert,
    systemHealth,
    setMapCenter,
    setMapZoom,
  } = useIntelligence();

  const [rightPanelTab, setRightPanelTab] = useState<'inspector' | 'clusters' | 'alerts'>('inspector');
  const [modalAction, setModalAction] = useState<'CONFIRM' | 'REJECT'>('CONFIRM');
  const [activeAoi, setActiveAoi] = useState<'tumakuru' | 'krishna' | 'bengaluru'>('tumakuru');
  const [sensorFilter, setSensorFilter] = useState<'ALL' | 'OPTICAL' | 'SAR'>('ALL');

  const pendingAlerts = alerts.filter((a) => a.status === 'PENDING REVIEW');
  const activeAlert = alerts[0];

  const handleSelectAoi = (aoi: 'tumakuru' | 'krishna' | 'bengaluru') => {
    setActiveAoi(aoi);
    if (aoi === 'tumakuru') {
      setMapCenter([13.3408, 77.1009]);
      setMapZoom(12);
    } else if (aoi === 'krishna') {
      setMapCenter([16.5062, 80.6480]);
      setMapZoom(11);
    } else {
      setMapCenter([12.9716, 77.5946]);
      setMapZoom(11);
    }
  };

  const handleOpenAction = (alert: any, action: 'CONFIRM' | 'REJECT') => {
    setModalAction(action);
    setFeedbackModalAlert(alert);
  };

  const filteredResults = searchResults.filter((res) => {
    if (sensorFilter === 'OPTICAL') return res.sensor?.includes('MSI') || res.sensor?.includes('Landsat');
    if (sensorFilter === 'SAR') return res.sensor?.includes('SAR') || res.sensor?.includes('Sentinel-1');
    return true;
  });

  return (
    <div className="min-h-screen pt-20 pb-8 px-3 sm:px-5 lg:px-6 page-bg-dashboard text-[#f8fafc] flex flex-col space-y-3">
      {/* ── Top Header & Mission Telemetry ─────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-1 border-b border-white/[0.06] pb-2.5">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-heading font-extrabold text-sm tracking-tight text-white uppercase">
              ORBITINTEL // ANALYST WORKSPACE
            </span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-white/10 text-slate-400">
            MISSION ID: PS-26227
          </span>
        </div>

        {/* Global Stats */}
        <div className="flex items-center gap-2 font-mono text-[10px]">
          <div className="px-2.5 py-1 rounded border border-white/10 bg-white/[0.02] text-slate-300">
            INDEX: <span className="font-bold text-white">100K+ TILES</span>
          </div>
          <div className="px-2.5 py-1 rounded border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 font-semibold">
            MOCK MODE ACTIVE
          </div>
        </div>
      </div>

      {/* ── TOP: Natural Language Search ───────────────────────────────── */}
      <div className="w-full">
        <SearchBar />
      </div>

      {/* ── MAIN 3-COLUMN ANALYST WORKSTATION (CENTER MAP IS HERO) ───────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 flex-1 min-h-[640px]">
        {/* ── LEFT: Contextual Navigation & Ranked Results (col-span-3) ── */}
        <div className="lg:col-span-3 flex flex-col h-full rounded-xl border border-white/[0.08] bg-[#070a10]/80 backdrop-blur-md p-3 space-y-3">
          {/* Contextual AOI Quick Selector */}
          <div className="space-y-1.5 pb-2.5 border-b border-white/[0.06]">
            <span className="text-[9px] font-mono uppercase tracking-widest text-slate-400 font-bold block">
              OPERATIONAL AOI
            </span>
            <div className="grid grid-cols-3 gap-1">
              <button
                type="button"
                onClick={() => handleSelectAoi('tumakuru')}
                className={`py-1 px-1.5 rounded text-[9px] font-mono uppercase tracking-wider text-center transition-all ${
                  activeAoi === 'tumakuru'
                    ? 'bg-emerald-500/20 border border-emerald-400 text-emerald-300 font-bold'
                    : 'bg-white/[0.03] border border-white/5 text-slate-400 hover:text-slate-200'
                }`}
              >
                Tumakuru
              </button>
              <button
                type="button"
                onClick={() => handleSelectAoi('krishna')}
                className={`py-1 px-1.5 rounded text-[9px] font-mono uppercase tracking-wider text-center transition-all ${
                  activeAoi === 'krishna'
                    ? 'bg-emerald-500/20 border border-emerald-400 text-emerald-300 font-bold'
                    : 'bg-white/[0.03] border border-white/5 text-slate-400 hover:text-slate-200'
                }`}
              >
                Krishna
              </button>
              <button
                type="button"
                onClick={() => handleSelectAoi('bengaluru')}
                className={`py-1 px-1.5 rounded text-[9px] font-mono uppercase tracking-wider text-center transition-all ${
                  activeAoi === 'bengaluru'
                    ? 'bg-emerald-500/20 border border-emerald-400 text-emerald-300 font-bold'
                    : 'bg-white/[0.03] border border-white/5 text-slate-400 hover:text-slate-200'
                }`}
              >
                Bengaluru
              </button>
            </div>
          </div>

          {/* Sensor Modality Filters */}
          <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
            <span className="text-[9px] font-mono uppercase tracking-widest text-slate-400 font-semibold">
              MODALITY
            </span>
            <div className="flex items-center gap-1 font-mono text-[9px]">
              {(['ALL', 'OPTICAL', 'SAR'] as const).map((filter) => (
                <button
                  key={filter}
                  type="button"
                  onClick={() => setSensorFilter(filter)}
                  className={`px-2 py-0.5 rounded transition-all ${
                    sensorFilter === filter
                      ? 'bg-white/10 text-white font-bold border border-white/20'
                      : 'text-slate-400 hover:text-slate-300'
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>

          {/* Editorial Ranked Search Results */}
          <div className="flex-1 overflow-hidden">
            <SearchResultsList results={filteredResults} />
          </div>
        </div>

        {/* ── CENTER: Large Immersive Geospatial Map (col-span-6 HERO) ───── */}
        <div className="lg:col-span-6 h-[520px] lg:h-full min-h-[520px] rounded-xl border border-white/[0.08] overflow-hidden shadow-2xl">
          <MapView />
        </div>

        {/* ── RIGHT: Intelligence Inspector & Telemetry (col-span-3) ────── */}
        <div className="lg:col-span-3 flex flex-col h-full rounded-xl border border-white/[0.08] bg-[#070a10]/80 backdrop-blur-md overflow-hidden">
          {/* Tab Selector */}
          <div className="flex items-center border-b border-white/[0.06] bg-[#04060a]/60">
            <button
              type="button"
              onClick={() => setRightPanelTab('inspector')}
              className={`flex-1 py-2 text-[10px] font-mono uppercase tracking-wider transition-colors ${
                rightPanelTab === 'inspector'
                  ? 'text-white border-b-2 border-emerald-400 bg-white/[0.02] font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              INSPECTOR
            </button>
            <button
              type="button"
              onClick={() => setRightPanelTab('clusters')}
              className={`flex-1 py-2 text-[10px] font-mono uppercase tracking-wider transition-colors ${
                rightPanelTab === 'clusters'
                  ? 'text-white border-b-2 border-emerald-400 bg-white/[0.02] font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              CLUSTERS ({clusters.length})
            </button>
            <button
              type="button"
              onClick={() => setRightPanelTab('alerts')}
              className={`flex-1 py-2 text-[10px] font-mono uppercase tracking-wider transition-colors ${
                rightPanelTab === 'alerts'
                  ? 'text-white border-b-2 border-emerald-400 bg-white/[0.02] font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ALERTS ({pendingAlerts.length})
            </button>
          </div>

          {/* Tab Contents */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {/* TAB 1: INSPECTOR */}
            {rightPanelTab === 'inspector' && (
              <div className="space-y-3">
                {selectedResult ? (
                  <>
                    <div className="p-3 rounded-lg border border-white/[0.06] bg-[#04060a]/80 space-y-2">
                      <div className="flex items-center justify-between text-[10px] font-mono uppercase text-slate-400">
                        <span>TARGET #{selectedResult.id}</span>
                        <span className="text-emerald-400 font-bold">{selectedResult.relevanceScore}% MATCH</span>
                      </div>
                      <h4 className="text-xs font-heading font-bold text-white">{selectedResult.title}</h4>
                      <p className="text-[11px] text-slate-400 font-sans">{selectedResult.details}</p>
                    </div>

                    <MetadataPanel tileId={selectedResult.id} compact />

                    <button
                      type="button"
                      onClick={() => navigate('/analysis/analysis_tumakuru_01')}
                      className="w-full py-2.5 rounded bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono text-xs font-bold uppercase tracking-wider transition-all"
                    >
                      OPEN BI-TEMPORAL SLIDER &rarr;
                    </button>
                  </>
                ) : (
                  <div className="py-12 text-center text-slate-400 font-mono text-xs">
                    Select a target on the map or search stream to inspect telemetry.
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: CLUSTERS */}
            {rightPanelTab === 'clusters' && <ClusterView clusters={clusters} />}

            {/* TAB 3: ALERTS */}
            {rightPanelTab === 'alerts' && (
              <div className="space-y-2">
                {alerts.map((alt) => (
                  <div key={alt.id} className="p-3 rounded-lg border border-white/[0.06] bg-[#04060a]/70 space-y-2">
                    <div className="flex items-center justify-between text-[10px] font-mono uppercase">
                      <span className="text-slate-400">{alt.id}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        alt.status === 'CONFIRMED' ? 'bg-emerald-500/20 text-emerald-300' :
                        alt.status === 'REJECTED' ? 'bg-rose-500/20 text-rose-300' :
                        'bg-amber-500/20 text-amber-300'
                      }`}>
                        {alt.status}
                      </span>
                    </div>

                    <h5 className="text-xs font-heading font-bold text-white">{alt.type}</h5>
                    <p className="text-[10px] font-mono text-slate-400">{alt.locationName}</p>

                    <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => handleOpenAction(alt, 'CONFIRM')}
                          className="px-2 py-0.5 rounded border border-emerald-500/40 bg-emerald-500/10 text-emerald-300 text-[10px] font-mono uppercase hover:bg-emerald-500/20"
                        >
                          Confirm
                        </button>
                        <button
                          type="button"
                          onClick={() => handleOpenAction(alt, 'REJECT')}
                          className="px-2 py-0.5 rounded border border-rose-500/40 bg-rose-500/10 text-rose-300 text-[10px] font-mono uppercase hover:bg-rose-500/20"
                        >
                          Reject
                        </button>
                      </div>

                      <button
                        type="button"
                        onClick={() => navigate('/analysis/analysis_tumakuru_01')}
                        className="text-[10px] font-mono text-slate-400 hover:text-white uppercase"
                      >
                        Analysis &rarr;
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Feedback Modal for Confirmation / Rejection */}
      {feedbackModalAlert && (
        <FeedbackModal
          alert={feedbackModalAlert}
          initialAction={modalAction}
          onClose={() => setFeedbackModalAlert(null)}
        />
      )}
    </div>
  );
};
