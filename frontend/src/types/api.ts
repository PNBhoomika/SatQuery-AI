/**
 * OrbitIntel / SatQuery-AI - Frontend Type Contracts
 * Synchronized with Member 4 FastAPI REST API response schemas.
 * Member 5 owns this file — defines all API consumption interfaces.
 */

export interface SearchResult {
  id: string;
  title: string;
  thumbnail: string;
  latitude: number;
  longitude: number;
  acquisitionDate: string;
  sensor: string;
  relevanceScore: number;
  confidence: number;
  category?: string;
  coordinates?: string;
  details?: string;
  bbox?: number[];
  spectralProfile?: Record<string, unknown>;
}

export type AlertStatus = 'PENDING REVIEW' | 'CONFIRMED' | 'REJECTED';

export interface Alert {
  id: string;
  type: string;
  latitude: number;
  longitude: number;
  confidence: number;
  detectedAt: string;
  status: AlertStatus;
  sensor: string;
  affectedArea: string;
  locationName: string;
  analysisId: string;
  summary: string;
  feedback?: {
    action: string;
    rationale?: string;
    analystNotes?: string;
    reviewedAt: string;
  };
}

export interface ClusterDetection {
  id: string;
  lat: number;
  lng: number;
  confidence: number;
  type: string;
}

export interface Cluster {
  cluster_id: string;
  cluster_name: string;
  center_lat: number;
  center_lng: number;
  member_count: number;
  confidence: number;
  detections: ClusterDetection[];
  bounds: [[number, number], [number, number]];
}

export interface ChangeAnalysis {
  id: string;
  title: string;
  location: string;
  beforeDate: string;
  afterDate: string;
  beforeImage: string;
  afterImage: string;
  changeMask: string;
  changeHeatmap: string;
  confidence: number;
  changeType: string;
  affectedArea: string;
  sensor: string;
  gsd: string;
  meanDeltaNdvi?: number;
  status: AlertStatus;
  notes: string;
}

export interface FeedbackPayload {
  alert_id: string;
  action: 'CONFIRM' | 'REJECT';
  rationale?: string;
  analyst_notes?: string;
}

export interface SystemHealth {
  status: string;
  service: string;
  timestamp: string;
  vector_database: {
    type: string;
    indexed_tiles_count: number;
  };
  modules: Record<string, string>;
}

/** Full metadata record for a satellite tile — Member 4: GET /api/metadata/{id} */
export interface TileMetadata {
  tile_id: string;
  title: string;
  satellite: string;
  sensor: string;
  acquisitionDate: string;
  latitude: number;
  longitude: number;
  resolution: string;
  cloudPercent: number | null;
  tileId: string;
  source: string;
  processingStatus: string;
  confidence: number;
  relevanceScore: number;
  category: string;
  bbox: number[];
  bands: string[];
  ndvi: number | null;
  ndwi: number | null;
  atmosphericQa: string;
  orbitRelative: number;
  platformName: string;
}
