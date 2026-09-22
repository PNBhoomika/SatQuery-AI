import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Layers,
  MapPin,
  Radio,
  CheckCircle2,
  XCircle,
  Activity,
  ShieldAlert,
  ArrowUpRight,
} from 'lucide-react';
import { BeforeAfterSlider } from '../components/comparison/BeforeAfterSlider';
import { FeedbackModal } from '../components/feedback/FeedbackModal';
import { apiService } from '../services/api';
import { ChangeAnalysis, Alert } from '../types/api';
import { useIntelligence } from '../context/IntelligenceContext';

export const AnalysisPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { alerts, feedbackModalAlert, setFeedbackModalAlert } = useIntelligence();

  const [analysis, setAnalysis] = useState<ChangeAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalAction, setModalAction] = useState<'CONFIRM' | 'REJECT'>('CONFIRM');

  useEffect(() => {
    loadAnalysisData();
  }, [id]);

  const loadAnalysisData = async () => {
    setLoading(true);
    try {
      const data = await apiService.getChangeAnalysis(id || 'analysis_tumakuru_01');
      setAnalysis(data);
    } catch (err) {
      console.error('Error fetching analysis', err);
    } finally {
      setLoading(false);
    }
  };

  const currentAlert: Alert = alerts.find((a) => a.analysisId === id) || {
    id: 'ALT-2026-024',
    type: analysis?.changeType || 'New Construction / Photovoltaic Array Expansion',
    latitude: 13.3408,
    longitude: 77.1009,
    confidence: analysis?.confidence || 0.87,
    detectedAt: analysis?.afterDate || '18 JUN 2026',
    status: analysis?.status || 'PENDING REVIEW',
    sensor: analysis?.sensor || 'Sentinel-2 MSI',
    affectedArea: analysis?.affectedArea || '18.4 ha',
    locationName: analysis?.location || 'Tumakuru Industrial Hub, Karnataka',
    analysisId: id || 'analysis_tumakuru_01',
    summary: analysis?.notes || '18.4 hectares of new industrial superstructure and solar array detected with high spectral certainty.',
  };

  const handleOpenAction = (action: 'CONFIRM' | 'REJECT') => {
    setModalAction(action);
    setFeedbackModalAlert(currentAlert);
  };

  if (loading || !analysis) {
    return (
      <div className="min-h-screen pt-28 pb-16 flex items-center justify-center page-bg text-slate-400 font-mono text-xs">
        LOADING BI-TEMPORAL INTELLIGENCE...
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto page-bg text-[#f8fafc] space-y-6">
      {/* ── Top Navigation Bar ───────────────────────────────────────── */}
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
        <button
          type="button"
          onClick={() => navigate('/dashboard')}
          className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>RETURN TO CONSOLE</span>
        </button>

        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono text-slate-400 uppercase">CASE FILE:</span>
          <span className="px-2 py-0.5 rounded border border-white/10 bg-white/[0.02] text-xs font-mono text-emerald-400 font-bold">
            {analysis.id}
          </span>
        </div>
      </div>

      {/* ── Case Header & Metadata ───────────────────────────────────── */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-6 rounded-2xl border border-white/[0.08] bg-[#070a10]/80 backdrop-blur-md">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-[10px] font-mono uppercase text-slate-400">
            <span className="text-emerald-400 font-semibold">{analysis.sensor}</span>
            <span>&bull;</span>
            <span>GSD: {analysis.gsd}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-white tracking-tight">
            {analysis.title}
          </h1>
          <p className="text-xs font-mono text-slate-400">
            {analysis.location}
          </p>
        </div>

        {/* Verification Action Buttons */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={() => handleOpenAction('CONFIRM')}
            className="px-5 py-2.5 rounded border border-emerald-500/50 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 font-mono text-xs font-bold uppercase tracking-wider transition-all"
          >
            CONFIRM EVENT
          </button>
          <button
            type="button"
            onClick={() => handleOpenAction('REJECT')}
            className="px-5 py-2.5 rounded border border-rose-500/50 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 font-mono text-xs font-bold uppercase tracking-wider transition-all"
          >
            REJECT (FALSE ALARM)
          </button>
        </div>
      </div>

      {/* ── Interactive Before / After Comparison Slider ─────────────── */}
      <div className="rounded-2xl border border-white/[0.08] bg-[#070a10]/80 p-5 backdrop-blur-md shadow-2xl">
        <BeforeAfterSlider
          beforeImage={analysis.beforeImage}
          afterImage={analysis.afterImage}
          changeMask={analysis.changeMask}
          changeHeatmap={analysis.changeHeatmap}
          beforeDate="12 JUN 2024"
          afterDate="18 JUN 2026"
          confidence={analysis.confidence || 0.87}
          changeType={analysis.changeType}
          affectedArea={analysis.affectedArea}
          height="540px"
        />
      </div>

      {/* ── Technical Diagnostics & Telemetry ────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-white/[0.08] bg-[#070a10]/80">
          <span className="block text-[10px] font-mono text-slate-400 uppercase">AFFECTED REGION</span>
          <span className="text-lg font-heading font-bold text-white mt-1 block">
            {analysis.affectedArea}
          </span>
          <span className="text-[10px] font-mono text-slate-400 mt-0.5 block">Polygon Boundary Area</span>
        </div>

        <div className="p-4 rounded-xl border border-white/[0.08] bg-[#070a10]/80">
          <span className="block text-[10px] font-mono text-slate-400 uppercase">TEMPORAL INTERVAL</span>
          <span className="text-base font-heading font-bold text-white mt-1 block">
            734 Days
          </span>
          <span className="text-[10px] font-mono text-slate-400 mt-0.5 block">2024-08-10 &rarr; 2026-08-14</span>
        </div>

        <div className="p-4 rounded-xl border border-white/[0.08] bg-[#070a10]/80">
          <span className="block text-[10px] font-mono text-slate-400 uppercase">MEAN DELTA NDVI</span>
          <span className="text-lg font-heading font-bold text-rose-400 mt-1 block">
            {analysis.meanDeltaNdvi ? analysis.meanDeltaNdvi.toFixed(2) : '-0.24'}
          </span>
          <span className="text-[10px] font-mono text-slate-400 mt-0.5 block">Vegetation to Built Surface</span>
        </div>

        <div className="p-4 rounded-xl border border-white/[0.08] bg-[#070a10]/80">
          <span className="block text-[10px] font-mono text-slate-400 uppercase">FALSE-ALARM FILTER</span>
          <span className="text-lg font-heading font-bold text-emerald-400 mt-1 block">
            94.2%
          </span>
          <span className="text-[10px] font-mono text-slate-400 mt-0.5 block">Shadow / Cloud Rejection</span>
        </div>
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
