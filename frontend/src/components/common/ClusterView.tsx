/**
 * ClusterView — Member 5 Component
 * Visualizes HDBSCAN spatial activity clusters returned by Member 4 / Member 2.
 * Shows cluster ID, member count, confidence, location, and allows map zoom-to-fit.
 * Does NOT implement HDBSCAN. Cluster data comes from GET /api/clusters via context.
 */

import React from 'react';
import { Layers, MapPin, ChevronRight, Activity, Users } from 'lucide-react';
import { Cluster } from '../../types/api';
import { ConfidenceBadge } from './ConfidenceBadge';
import { useIntelligence } from '../../context/IntelligenceContext';

interface ClusterViewProps {
  clusters: Cluster[];
  onClusterClick?: (cluster: Cluster) => void;
}

export const ClusterView: React.FC<ClusterViewProps> = ({ clusters, onClusterClick }) => {
  const { selectedCluster, setSelectedCluster, setMapCenter, setMapZoom } = useIntelligence();

  const handleSelect = (cluster: Cluster) => {
    setSelectedCluster(cluster);
    setMapCenter([cluster.center_lat, cluster.center_lng]);
    setMapZoom(13);
    if (onClusterClick) onClusterClick(cluster);
  };

  if (clusters.length === 0) {
    return (
      <div className="p-6 text-center rounded-xl border border-white/[0.06] bg-[#0d1117]/60">
        <Layers className="w-6 h-6 text-slate-600 mx-auto mb-2" />
        <p className="text-xs text-slate-500 font-mono">No clusters detected in current AOI</p>
        <p className="text-[10px] text-slate-600 font-mono mt-1">
          Run a semantic search to generate HDBSCAN site groupings
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      {/* Header */}
      <div className="flex items-center justify-between px-1 mb-1">
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-300 font-semibold">
            HDBSCAN Site Clusters
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            {clusters.length} Groups
          </span>
        </div>
        <span className="text-[10px] font-mono text-slate-500">
          Member 2 output
        </span>
      </div>

      {/* Cluster Cards */}
      {clusters.map((cluster, idx) => {
        const isSelected = selectedCluster?.cluster_id === cluster.cluster_id;
        return (
          <button
            key={cluster.cluster_id}
            type="button"
            onClick={() => handleSelect(cluster)}
            className={`w-full text-left p-3 rounded-lg border transition-all duration-200 ${
              isSelected
                ? 'border-emerald-500/60 bg-emerald-500/[0.08]'
                : 'border-white/[0.07] bg-[#070a10]/70 hover:border-white/20'
            }`}
          >
            {/* Top Row: Cluster ID + Confidence */}
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.5 rounded border font-semibold ${
                    isSelected
                      ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                      : 'bg-slate-900 border-slate-700 text-slate-300'
                  }`}
                >
                  #{String(idx + 1).padStart(2, '0')} {cluster.cluster_id.toUpperCase()}
                </span>
              </div>
              <ConfidenceBadge score={cluster.confidence} size="sm" showLabel={false} />
            </div>

            {/* Cluster Name */}
            <h4 className="text-xs font-heading font-bold text-slate-100 mb-2 leading-snug">
              {cluster.cluster_name}
            </h4>

            {/* Stats Row */}
            <div className="grid grid-cols-3 gap-2 text-[10px] font-mono text-slate-400">
              <div className="flex items-center gap-1">
                <Users className="w-3 h-3 text-slate-500 shrink-0" />
                <span>{cluster.member_count} sites</span>
              </div>
              <div className="flex items-center gap-1 col-span-2">
                <MapPin className="w-3 h-3 text-emerald-500 shrink-0" />
                <span className="truncate">
                  {cluster.center_lat.toFixed(3)}°N, {cluster.center_lng.toFixed(3)}°E
                </span>
              </div>
            </div>

            {/* Detection Type Chips */}
            {cluster.detections && cluster.detections.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-1">
                {[...new Set(cluster.detections.map((d) => d.type))].slice(0, 3).map((type) => (
                  <span
                    key={type}
                    className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400"
                  >
                    {type}
                  </span>
                ))}
              </div>
            )}

            {/* Zoom CTA */}
            <div
              className={`mt-2.5 flex items-center gap-1 text-[10px] font-mono transition-colors ${
                isSelected ? 'text-emerald-400' : 'text-slate-500 group-hover:text-slate-300'
              }`}
            >
              <Activity className="w-3 h-3" />
              <span>{isSelected ? 'Active on map' : 'Click to zoom map'}</span>
              <ChevronRight className="w-3 h-3 ml-auto" />
            </div>
          </button>
        );
      })}
    </div>
  );
};
