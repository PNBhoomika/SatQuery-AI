/**
 * OrbitIntel / SatQuery-AI - Unified REST API Client Layer (Member 5 -> Member 4)
 * Handles semantic search, image query, alerts, clusters, and analyst feedback.
 * Supports transparent fallback to offline mock datasets when VITE_USE_MOCK_API=true or backend offline.
 */

import { SearchResult, Alert, Cluster, ChangeAnalysis, FeedbackPayload, SystemHealth, TileMetadata } from '../types/api';
import mockSearchResults from '../mock/searchResults.json';
import mockAlerts from '../mock/alerts.json';
import mockClusters from '../mock/clusters.json';
import mockAnalysis from '../mock/analysis.json';
import mockMetadata from '../mock/metadata.json';

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true';
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiService {
  private inMemoryAlerts: Alert[] = [...(mockAlerts as Alert[])];

  async getHealth(): Promise<SystemHealth> {
    if (USE_MOCK) {
      return {
        status: 'HEALTHY (MOCK MODE)',
        service: 'OrbitIntel Mock Intelligence Gateway',
        timestamp: new Date().toISOString(),
        vector_database: { type: 'Qdrant In-Memory Proxy', indexed_tiles_count: 4 },
        modules: {
          ingestion: 'SIMULATED',
          embeddings: 'HYBRID-512',
          vector_db: 'LOCAL_STANDALONE',
          change_detection: 'BI-TEMPORAL ACTIVE',
        },
      };
    }
    try {
      const res = await fetch(`${BASE_URL}/health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Backend unavailable, falling back to mock health data', err);
      return {
        status: 'STANDALONE LOCAL',
        service: 'OrbitIntel Standalone Engine',
        timestamp: new Date().toISOString(),
        vector_database: { type: 'Qdrant (Local)', indexed_tiles_count: 4 },
        modules: { pipeline: 'OFFLINE READY' },
      };
    }
  }

  async searchSemantic(query: string, topK: number = 10): Promise<SearchResult[]> {
    if (USE_MOCK) {
      // Simulate network latency for realistic feel
      await new Promise(r => setTimeout(r, 250));
      return this.filterMockSearch(query);
    }
    try {
      const res = await fetch(`${BASE_URL}/search/semantic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return Array.isArray(data) ? data : (mockSearchResults as SearchResult[]);
    } catch (err) {
      console.warn('Backend search error, using mock results', err);
      return this.filterMockSearch(query);
    }
  }

  async searchByImage(file: File, topK: number = 10): Promise<SearchResult[]> {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500));
      return mockSearchResults as SearchResult[];
    }
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('top_k', topK.toString());

      const res = await fetch(`${BASE_URL}/search/image`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Backend image search error, using fallback', err);
      return mockSearchResults as SearchResult[];
    }
  }

  async getAlerts(statusFilter?: string): Promise<Alert[]> {
    if (USE_MOCK) {
      if (!statusFilter || statusFilter.toUpperCase() === 'ALL') {
        return this.inMemoryAlerts;
      }
      return this.inMemoryAlerts.filter(a => a.status.toUpperCase() === statusFilter.toUpperCase());
    }
    try {
      const queryParam = statusFilter && statusFilter.toUpperCase() !== 'ALL' ? `?status=${statusFilter}` : '';
      const res = await fetch(`${BASE_URL}/alerts${queryParam}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Backend alerts unavailable, using in-memory store', err);
      if (!statusFilter || statusFilter.toUpperCase() === 'ALL') return this.inMemoryAlerts;
      return this.inMemoryAlerts.filter(a => a.status.toUpperCase() === statusFilter.toUpperCase());
    }
  }

  async getAlertById(id: string): Promise<Alert | null> {
    if (USE_MOCK) {
      return this.inMemoryAlerts.find(a => a.id === id) || null;
    }
    try {
      const res = await fetch(`${BASE_URL}/alerts/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      return this.inMemoryAlerts.find(a => a.id === id) || null;
    }
  }

  async submitFeedback(payload: FeedbackPayload): Promise<boolean> {
    // Update local cache regardless
    const alert = this.inMemoryAlerts.find(a => a.id === payload.alert_id);
    if (alert) {
      alert.status = payload.action === 'CONFIRM' ? 'CONFIRMED' : 'REJECTED';
      alert.feedback = {
        action: payload.action,
        rationale: payload.rationale,
        analystNotes: payload.analyst_notes,
        reviewedAt: new Date().toISOString(),
      };
    }

    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 200));
      return true;
    }

    try {
      const res = await fetch(`${BASE_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      return res.ok;
    } catch (err) {
      console.warn('Feedback submission to backend failed, recorded locally in memory', err);
      return true;
    }
  }

  async getClusters(): Promise<Cluster[]> {
    if (USE_MOCK) {
      return mockClusters as Cluster[];
    }
    try {
      const res = await fetch(`${BASE_URL}/clusters`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Backend clusters unavailable, using fallback', err);
      return mockClusters as Cluster[];
    }
  }

  async getChangeAnalysis(analysisId: string): Promise<ChangeAnalysis> {
    const analysisMap = mockAnalysis as Record<string, ChangeAnalysis>;
    if (USE_MOCK) {
      return analysisMap[analysisId] || analysisMap['analysis_tumakuru_01'];
    }
    try {
      const res = await fetch(`${BASE_URL}/change-detection/${analysisId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Backend analysis unavailable, using fallback', err);
      return analysisMap[analysisId] || analysisMap['analysis_tumakuru_01'];
    }
  }

  private filterMockSearch(query: string): SearchResult[] {
    const items = mockSearchResults as SearchResult[];
    if (!query || query.trim() === '') return items;
    const lower = query.toLowerCase();
    const filtered = items.filter(
      item =>
        item.title.toLowerCase().includes(lower) ||
        (item.category && item.category.toLowerCase().includes(lower)) ||
        (item.details && item.details.toLowerCase().includes(lower))
    );
    return filtered.length > 0 ? filtered : items;
  }

  /**
   * GET /api/metadata/{id}
   * Returns full satellite metadata for a tile (sensor, resolution, cloud%, tile ID, bands, NDVI, etc.)
   * Member 4 endpoint — falls back to mock metadata.json
   */
  async getMetadata(tileId: string): Promise<TileMetadata | null> {
    const metaList = mockMetadata as TileMetadata[];
    const idMap: Record<string, string> = {
      res_001: 'tile_tumakuru_01',
      res_002: 'tile_krishna_flood_03',
      res_003: 'tile_ghats_forest_04',
      res_004: 'tile_bhadra_farm_05',
      tile_res_001: 'tile_tumakuru_01',
      tile_res_002: 'tile_krishna_flood_03',
      tile_res_003: 'tile_ghats_forest_04',
      tile_res_004: 'tile_bhadra_farm_05',
    };
    const resolvedId = idMap[tileId] || tileId;

    if (USE_MOCK) {
      return metaList.find(m => m.tile_id === resolvedId) || metaList[0];
    }
    try {
      const res = await fetch(`${BASE_URL}/metadata/${tileId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn(`Metadata fetch failed for ${tileId}, using mock`, err);
      return metaList.find(m => m.tile_id === resolvedId) || metaList[0];
    }
  }

  /**
   * GET /api/tiles/{id}
   * Returns tile record by ID — primarily the thumbnail URL and basic metadata.
   * Member 4 endpoint — falls back to mock search results.
   */
  async getTile(tileId: string): Promise<SearchResult | null> {
    if (USE_MOCK) {
      return (mockSearchResults as SearchResult[]).find(r => r.id === tileId) || null;
    }
    try {
      const res = await fetch(`${BASE_URL}/tiles/${tileId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn(`Tile fetch failed for ${tileId}, using mock`, err);
      return (mockSearchResults as SearchResult[]).find(r => r.id === tileId) || null;
    }
  }
}

export const apiService = new ApiService();
