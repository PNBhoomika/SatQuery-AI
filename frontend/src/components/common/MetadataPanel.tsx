/**
 * MetadataPanel — Member 5 Component
 * Displays full satellite tile metadata when an analyst selects a result.
 * Data comes exclusively from the API (GET /api/metadata/{id} via apiService.getMetadata).
 * Does NOT perform any geospatial computation.
 */

import React, { useEffect, useState } from 'react';
import {
  Satellite,
  Calendar,
  MapPin,
  Layers,
  Cloud,
  Hash,
  Database,
  Activity,
  Radio,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';
import { TileMetadata } from '../../types/api';
import { apiService } from '../../services/api';
import { ConfidenceBadge } from './ConfidenceBadge';

interface MetadataPanelProps {
  tileId: string | null;
  /** If provided, overrides the tileId lookup with pre-fetched metadata */
  metadata?: TileMetadata | null;
  compact?: boolean;
}

const MetaRow: React.FC<{ label: string; value: React.ReactNode; accent?: boolean }> = ({
  label,
  value,
  accent,
}) => (
  <div className="flex items-start justify-between gap-2 py-1.5 border-b border-white/[0.04] last:border-0">
    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 shrink-0 pt-0.5">
      {label}
    </span>
    <span
      className={`text-xs font-mono text-right break-all leading-tight ${
        accent ? 'text-emerald-400 font-semibold' : 'text-slate-200'
      }`}
    >
      {value ?? <span className="text-slate-600 italic">N/A</span>}
    </span>
  </div>
);

export const MetadataPanel: React.FC<MetadataPanelProps> = ({
  tileId,
  metadata: propMetadata,
  compact = false,
}) => {
  const [metadata, setMetadata] = useState<TileMetadata | null>(propMetadata || null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(!compact);

  useEffect(() => {
    if (propMetadata) {
      setMetadata(propMetadata);
      return;
    }
    if (!tileId) return;
    let cancelled = false;
    setLoading(true);
    apiService.getMetadata(tileId).then((data) => {
      if (!cancelled) {
        setMetadata(data);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [tileId, propMetadata]);

  if (!tileId && !propMetadata) {
    return (
      <div className="p-4 rounded-xl border border-white/[0.08] bg-[#0d1117]/80 text-center">
        <Info className="w-5 h-5 text-slate-600 mx-auto mb-1.5" />
        <p className="text-xs text-slate-500 font-mono">Select a result to view metadata</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-4 rounded-xl border border-white/[0.08] bg-[#0d1117]/80">
        <div className="animate-pulse space-y-2">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-3 rounded bg-slate-800" style={{ width: `${60 + (i % 3) * 15}%` }} />
          ))}
        </div>
      </div>
    );
  }

  if (!metadata) return null;

  const ndviDisplay =
    metadata.ndvi !== null ? (
      <span className={metadata.ndvi < 0 ? 'text-rose-400' : 'text-emerald-400'}>
        {metadata.ndvi.toFixed(2)} ({metadata.ndvi < -0.2 ? 'Significant Loss' : metadata.ndvi < 0 ? 'Slight Loss' : 'Gain'})
      </span>
    ) : null;

  const ndwiDisplay =
    metadata.ndwi !== null ? (
      <span className={metadata.ndwi > 0.3 ? 'text-cyan-400' : 'text-slate-300'}>
        {metadata.ndwi.toFixed(2)}
      </span>
    ) : null;

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#070a10]/80 backdrop-blur-md overflow-hidden shadow-xl">
      {/* Panel Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 border-b border-white/[0.06] hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-300 font-semibold">
            STAC SATELLITE TELEMETRY
          </span>
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/[0.03] text-slate-400 border border-white/10">
            {metadata.tileId}
          </span>
        </div>
        {compact && (
          expanded ? (
            <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          )
        )}
      </button>

      {expanded && (
        <div className="px-4 py-3 space-y-4">
          {/* Section 1: Platform & Sensor */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Satellite className="w-3 h-3 text-cyan-400" />
              <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest font-semibold">
                Platform
              </span>
            </div>
            <div className="space-y-0">
              <MetaRow label="Satellite" value={metadata.satellite} accent />
              <MetaRow label="Sensor" value={metadata.sensor} />
              <MetaRow label="Platform" value={metadata.platformName} />
              <MetaRow label="Orbit Track" value={`Relative Orbit ${metadata.orbitRelative}`} />
              <MetaRow label="Bands" value={metadata.bands.join(', ')} />
            </div>
          </div>

          {/* Section 2: Acquisition */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Calendar className="w-3 h-3 text-emerald-400" />
              <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest font-semibold">
                Acquisition
              </span>
            </div>
            <div className="space-y-0">
              <MetaRow label="Date" value={metadata.acquisitionDate} accent />
              <MetaRow label="Resolution" value={metadata.resolution} />
              <MetaRow
                label="Cloud Cover"
                value={
                  metadata.cloudPercent !== null
                    ? `${metadata.cloudPercent.toFixed(1)}%`
                    : 'N/A (SAR)'
                }
              />
              <MetaRow label="Atm. Quality" value={metadata.atmosphericQa} />
            </div>
          </div>

          {/* Section 3: Location */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <MapPin className="w-3 h-3 text-amber-400" />
              <span className="text-[10px] font-mono text-amber-400 uppercase tracking-widest font-semibold">
                Location
              </span>
            </div>
            <div className="space-y-0">
              <MetaRow
                label="Coordinates"
                value={`${metadata.latitude.toFixed(4)}°N, ${metadata.longitude.toFixed(4)}°E`}
              />
              <MetaRow
                label="Bounding Box"
                value={`[${metadata.bbox.map((v) => v.toFixed(3)).join(', ')}]`}
              />
            </div>
          </div>

          {/* Section 4: Processing & Source */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Layers className="w-3 h-3 text-slate-400" />
              <span className="text-[10px] font-mono text-slate-300 uppercase tracking-widest font-semibold">
                Processing
              </span>
            </div>
            <div className="space-y-0">
              <MetaRow label="Source" value={metadata.source} />
              <MetaRow label="Processing" value={metadata.processingStatus} accent />
              <MetaRow label="Category" value={metadata.category} />
            </div>
          </div>

          {/* Section 5: Spectral Indices (only if available) */}
          {(metadata.ndvi !== null || metadata.ndwi !== null) && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Activity className="w-3 h-3 text-rose-400" />
                <span className="text-[10px] font-mono text-rose-400 uppercase tracking-widest font-semibold">
                  Spectral Indices
                </span>
              </div>
              <div className="space-y-0">
                {metadata.ndvi !== null && <MetaRow label="NDVI Delta" value={ndviDisplay} />}
                {metadata.ndwi !== null && <MetaRow label="NDWI" value={ndwiDisplay} />}
              </div>
            </div>
          )}

          {/* Confidence Score */}
          <div className="pt-2 border-t border-white/[0.06]">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                Model Confidence
              </span>
              <ConfidenceBadge score={metadata.confidence} size="sm" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
