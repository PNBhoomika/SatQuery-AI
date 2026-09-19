import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  Search,
  CheckCircle2,
  XCircle,
  Eye,
  SlidersHorizontal,
  ArrowUpRight,
} from 'lucide-react';
import { useIntelligence } from '../context/IntelligenceContext';
import { Alert } from '../types/api';
import { FeedbackModal } from '../components/feedback/FeedbackModal';

export const AlertsPage: React.FC = () => {
  const navigate = useNavigate();
  const { alerts, feedbackModalAlert, setFeedbackModalAlert, setMapCenter, setMapZoom } = useIntelligence();

  const [activeFilter, setActiveFilter] = useState<'ALL' | 'PENDING' | 'CONFIRMED' | 'REJECTED'>('ALL');
  const [modalAction, setModalAction] = useState<'CONFIRM' | 'REJECT'>('CONFIRM');
  const [searchFilter, setSearchFilter] = useState('');

  const filteredAlerts = alerts.filter((alert) => {
    if (activeFilter === 'PENDING' && alert.status !== 'PENDING REVIEW') return false;
    if (activeFilter === 'CONFIRMED' && alert.status !== 'CONFIRMED') return false;
    if (activeFilter === 'REJECTED' && alert.status !== 'REJECTED') return false;

    if (searchFilter.trim()) {
      const q = searchFilter.toLowerCase();
      return (
        alert.id.toLowerCase().includes(q) ||
        alert.type.toLowerCase().includes(q) ||
        alert.locationName.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleOpenAction = (alert: Alert, action: 'CONFIRM' | 'REJECT') => {
    setModalAction(action);
    setFeedbackModalAlert(alert);
  };

  const handleViewAnalysis = (alert: Alert) => {
    navigate(`/analysis/${alert.analysisId || 'analysis_tumakuru_01'}`);
  };

  return (
    <div className="min-h-screen pt-28 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto page-bg text-[#f8fafc] space-y-8">
      {/* ── Page Header ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-6">
        <div>
          <div className="inline-flex items-center gap-2 font-mono text-[11px] text-amber-400 uppercase tracking-widest mb-2">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>MISSION ALERT QUEUE // BI-TEMPORAL DETECTIONS</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-heading font-extrabold text-white tracking-tight">
            CHANGE EVENT DISPATCH.
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-sans mt-2 max-w-2xl leading-relaxed">
            Multi-temporal satellite changes flagged by AI models for verification. Confirm verified infrastructure
            expansion or reject false alarms into the retraining loop.
          </p>
        </div>

        {/* Status Counters */}
        <div className="flex items-center gap-2 font-mono text-xs shrink-0">
          <div className="px-3 py-1.5 rounded border border-white/10 bg-white/[0.02] text-slate-300">
            TOTAL: <span className="font-bold text-white">{alerts.length}</span>
          </div>
          <div className="px-3 py-1.5 rounded border border-amber-500/30 bg-amber-500/10 text-amber-300">
            PENDING: <span className="font-bold text-amber-400">{alerts.filter(a => a.status === 'PENDING REVIEW').length}</span>
          </div>
        </div>
      </div>

      {/* ── Filter Bar ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div className="flex items-center gap-2">
          {(['ALL', 'PENDING', 'CONFIRMED', 'REJECTED'] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveFilter(tab)}
              className={`px-3 py-1.5 rounded text-xs font-mono uppercase tracking-wider transition-colors ${
                activeFilter === tab
                  ? 'bg-white/10 text-white font-bold border border-white/20'
                  : 'text-slate-400 hover:text-white border border-transparent'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="FILTER ALERTS..."
            className="w-full bg-[#070a10] border border-white/10 rounded pl-8 pr-3 py-1.5 text-xs font-mono text-white placeholder-slate-400"
          />
        </div>
      </div>

      {/* ── Editorial Alert Cards Grid ───────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        {filteredAlerts.map((alt) => (
          <div
            key={alt.id}
            className="rounded-xl border border-white/[0.08] bg-[#070a10]/80 p-6 flex flex-col justify-between space-y-6 hover:border-white/20 transition-all shadow-xl"
          >
            {/* Top row: Event ID & Sensor */}
            <div>
              <div className="flex items-center justify-between text-[11px] font-mono uppercase tracking-widest text-slate-400 mb-3">
                <span className="text-amber-400 font-semibold">CHANGE EVENT // {alt.id}</span>
                <span className="px-2 py-0.5 rounded border border-white/10 text-slate-300">
                  {alt.sensor || 'SENTINEL-2 MSI'}
                </span>
              </div>

              {/* Event Type & Location */}
              <h3 className="text-xl sm:text-2xl font-heading font-extrabold text-white tracking-tight uppercase leading-snug">
                {alt.type}
              </h3>
              <p className="text-xs font-mono text-slate-400 mt-1">
                {alt.locationName}
              </p>
              <p className="text-xs text-slate-400 font-sans mt-3 leading-relaxed">
                {alt.summary}
              </p>
            </div>

            {/* Metrics Row: Confidence + Affected Area + Date */}
            <div className="grid grid-cols-3 gap-4 py-4 border-y border-white/[0.06] text-left">
              <div>
                <span className="block text-[10px] font-mono text-slate-400 uppercase">CONFIDENCE</span>
                <span className="text-lg font-heading font-extrabold text-emerald-400">
                  {Math.round(alt.confidence * 100)}%
                </span>
              </div>
              <div>
                <span className="block text-[10px] font-mono text-slate-400 uppercase">AFFECTED AREA</span>
                <span className="text-lg font-heading font-extrabold text-white">
                  {alt.affectedArea || '18.4 HA'}
                </span>
              </div>
              <div>
                <span className="block text-[10px] font-mono text-slate-400 uppercase">ACQUIRED</span>
                <span className="text-xs font-mono text-slate-300 mt-1 block">
                  {alt.detectedAt ? new Date(alt.detectedAt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase() : '18 JUN 2026'}
                </span>
              </div>
            </div>

            {/* Action Buttons: Confirm / Reject / View Analysis */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleOpenAction(alt, 'CONFIRM')}
                  className="px-4 py-2 rounded border border-emerald-500/50 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 text-xs font-mono font-bold uppercase transition-all"
                >
                  CONFIRM
                </button>
                <button
                  type="button"
                  onClick={() => handleOpenAction(alt, 'REJECT')}
                  className="px-4 py-2 rounded border border-rose-500/50 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-mono font-bold uppercase transition-all"
                >
                  REJECT
                </button>
              </div>

              <button
                type="button"
                onClick={() => handleViewAnalysis(alt)}
                className="inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-wider text-slate-300 hover:text-emerald-300 transition-colors"
              >
                <span>VIEW ANALYSIS</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Analyst Feedback Modal */}
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
