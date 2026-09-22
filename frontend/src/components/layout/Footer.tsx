import React from 'react';
import { Globe, ShieldCheck, Database, Layers, Radio } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-white/[0.08] bg-[#04060a] pt-16 pb-12 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-white/[0.06]">
          {/* Col 1: Brand & Problem Statement */}
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="flex items-center justify-center w-8 h-8 rounded bg-emerald-500/10 border border-emerald-500/30">
                <Globe className="w-4 h-4 text-emerald-400" />
              </div>
              <span className="font-heading font-extrabold text-white text-base">ORBITINTEL</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              SatQuery-AI: Multimodal Semantic Retrieval & Spatio-Temporal Change Analytics Engine for Earth Observation.
            </p>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-[11px] font-mono">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>SIH 2026 Problem Statement 26227</span>
            </div>
          </div>

          {/* Col 2: Ingestion & Models */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">Sensor Constellations</h4>
            <ul className="space-y-2 text-xs">
              <li className="flex items-center gap-2">
                <Radio className="w-3.5 h-3.5 text-emerald-400" />
                <span>Sentinel-1 SAR C-Band (GRD VV/VH)</span>
              </li>
              <li className="flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
                <span>Sentinel-2 MSI (Level-2A BOA, 10m GSD)</span>
              </li>
              <li className="flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                <span>USGS Landsat-8/9 Collection 2 OLI-2</span>
              </li>
              <li className="flex items-center gap-2">
                <Globe className="w-3.5 h-3.5 text-indigo-400" />
                <span>ISRO Bhuvan Open Data Architecture</span>
              </li>
            </ul>
          </div>

          {/* Col 3: ML Pipeline Contracts */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">Architecture Modules</h4>
            <ul className="space-y-2 text-xs">
              <li>M1: Ingestion & Preprocessing (COG/STAC)</li>
              <li>M2: Semantic Retrieval (RemoteCLIP / 512-dim)</li>
              <li>M3: Change Detection (Bi-Temporal & NDVI/NDWI)</li>
              <li>M4: FastAPI Glue Layer & PostGIS Spec</li>
              <li>M5: Analyst Workstation & Feedback UI</li>
            </ul>
          </div>

          {/* Col 4: Engine Status */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-200">Telemetry & Health</h4>
            <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 font-mono text-xs space-y-1.5">
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-400">Vector Engine:</span>
                <span className="text-emerald-400">Qdrant Active</span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-400">Clustering:</span>
                <span className="text-cyan-400">HDBSCAN</span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-400">Atmosphere QA:</span>
                <span className="text-slate-200">SCL Masking</span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-400">Air-Gap Demo:</span>
                <span className="text-amber-400">STANDALONE READY</span>
              </div>
            </div>
          </div>
        </div>

        {/* Copyright & Team attribution */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p>© 2026 OrbitIntel Team. Built for Smart India Hackathon 2026.</p>
          <div className="flex items-center gap-6 font-mono text-[11px]">
            <span>STAC 1.0.0</span>
            <span>REST API v1.0</span>
            <span>AIR-GAPPED COMPLIANT</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
