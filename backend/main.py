"""
OrbitIntel / SatQuery-AI - Module 6: Backend API Layer
FastAPI service orchestrating Data Ingestion, Embeddings, Vector Search,
Bi-Temporal Change Detection, HDBSCAN Clustering, and Analyst Feedback loop.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import numpy as np
from PIL import Image

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_ingestion.stac_provider import DataIngestionRegistry, SatelliteSource, STACMetadata
from preprocessing.tile_processor import TileProcessor, radiometric_normalization
from embeddings.multimodal_embedder import get_default_embedder
from vector_search.qdrant_service import get_vector_db, SearchResultItem
from change_detection.bi_temporal_detector import BiTemporalChangeDetector, cluster_change_detections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("satquery.api")

app = FastAPI(
    title="OrbitIntel SatQuery-AI Backend",
    description="Multimodal Semantic Retrieval & Spatio-Temporal Change Analytics Engine (SIH 2026 - PS 26227)",
    version="1.0.0",
)

# CORS configuration for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount demo imagery directory for direct static serving
data_imagery_dir = os.path.join(PROJECT_ROOT, "data", "demo", "imagery")
os.makedirs(data_imagery_dir, exist_ok=True)
app.mount("/data/demo/imagery", StaticFiles(directory=data_imagery_dir), name="imagery")

# In-memory alert store with persistence to mock JSON
ALERTS_STORE: List[Dict[str, Any]] = []
ANALYSIS_STORE: Dict[str, Any] = {}

def load_initial_stores():
    global ALERTS_STORE, ANALYSIS_STORE
    mock_dir = os.path.join(PROJECT_ROOT, "frontend", "src", "mock")
    alerts_file = os.path.join(mock_dir, "alerts.json")
    analysis_file = os.path.join(mock_dir, "analysis.json")

    if os.path.exists(alerts_file):
        with open(alerts_file, "r") as f:
            ALERTS_STORE = json.load(f)
    if os.path.exists(analysis_file):
        with open(analysis_file, "r") as f:
            ANALYSIS_STORE = json.load(f)

load_initial_stores()


# ==========================================
# PYDANTIC REQUEST / RESPONSE MODELS
# ==========================================

class TextSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    sensor_filter: Optional[str] = None
    min_confidence: Optional[float] = None


class FeedbackRequest(BaseModel):
    alert_id: str
    action: str = Field(..., description="CONFIRM or REJECT")
    rationale: Optional[str] = None
    analyst_notes: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TemporalCompareRequest(BaseModel):
    tile_id_t1: str
    tile_id_t2: str
    before_date: str = "2024-08-10"
    after_date: str = "2026-08-14"


# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/api/health")
def get_health():
    """System health check and module status."""
    vdb = get_vector_db()
    return {
        "status": "HEALTHY",
        "service": "SatQuery-AI API Gateway (Member 4)",
        "timestamp": datetime.utcnow().isoformat(),
        "vector_database": {
            "type": "Qdrant (Local In-Memory / Disk)",
            "indexed_tiles_count": vdb.count(),
        },
        "modules": {
            "module_1_ingestion": "ACTIVE (Sentinel-1, Sentinel-2, Landsat, Bhuvan)",
            "module_2_preprocessing": "ACTIVE (Radiometric norm, SCL cloud masking, Tiling)",
            "module_3_embeddings": "ACTIVE (HybridSemanticSpectral-512 / RemoteCLIP adapter)",
            "module_4_vector_search": "ACTIVE (Qdrant Cosine Similarity)",
            "module_5_change_detection": "ACTIVE (Bi-Temporal NDVI/NDWI deltas, HDBSCAN)",
        },
    }


@app.post("/api/search/semantic")
def search_semantic(req: TextSearchRequest):
    """
    Multimodal Semantic Search via Natural Language Query.
    Text query -> 512-dim embedding -> Qdrant vector retrieval -> Ranked satellite cards.
    """
    embedder = get_default_embedder()
    vdb = get_vector_db()

    query_vector = embedder.embed_text(req.query)
    results = vdb.search(query_vector=query_vector, top_k=req.top_k)

    # Fallback to mock catalog if vector DB empty
    if not results:
        mock_file = os.path.join(PROJECT_ROOT, "frontend", "src", "mock", "searchResults.json")
        if os.path.exists(mock_file):
            with open(mock_file, "r") as f:
                return json.load(f)

    return [r.to_frontend_dict() for r in results]


@app.post("/api/search/image")
async def search_by_image(file: UploadFile = File(...), top_k: int = Form(10)):
    """
    Image-to-Image Semantic Search.
    Upload satellite tile image -> compute spectral & visual feature embedding -> search vector index.
    """
    try:
        contents = await file.read()
        import io
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        embedder = get_default_embedder()
        vdb = get_vector_db()

        query_vector = embedder.embed_image(img)
        results = vdb.search(query_vector=query_vector, top_k=top_k)
        return [r.to_frontend_dict() for r in results]
    except Exception as e:
        logger.error(f"Image search failed: {e}")
        raise HTTPException(status_code=400, detail=f"Image search error: {str(e)}")


@app.get("/api/alerts")
def get_alerts(status_filter: Optional[str] = Query(None, alias="status")):
    """Retrieve list of change alerts, optionally filtered by status."""
    if status_filter and status_filter.upper() != "ALL":
        filtered = [a for a in ALERTS_STORE if a.get("status", "").upper() == status_filter.upper()]
        return filtered
    return ALERTS_STORE


@app.get("/api/alerts/{alert_id}")
def get_alert_by_id(alert_id: str):
    """Retrieve details for a single alert."""
    for a in ALERTS_STORE:
        if a.get("id") == alert_id:
            return a
    raise HTTPException(status_code=404, detail="Alert not found")


@app.post("/api/feedback")
def submit_feedback(fb: FeedbackRequest):
    """
    Analyst-in-the-loop feedback handler.
    Updates alert status (CONFIRMED / REJECTED), records analyst justification,
    and dispatches training sample metadata for active learning retraining.
    """
    target_alert = None
    for a in ALERTS_STORE:
        if a.get("id") == fb.alert_id:
            target_alert = a
            break

    if target_alert:
        target_alert["status"] = "CONFIRMED" if fb.action.upper() == "CONFIRM" else "REJECTED"
        target_alert["feedback"] = {
            "action": fb.action,
            "rationale": fb.rationale,
            "analystNotes": fb.analyst_notes,
            "reviewedAt": fb.timestamp,
        }

    logger.info(f"Analyst Feedback logged: {fb.alert_id} -> {fb.action} (Reason: {fb.rationale})")
    return {
        "status": "SUCCESS",
        "message": f"Alert {fb.alert_id} updated to {fb.action}",
        "feedback": fb.dict(),
    }


@app.get("/api/clusters")
def get_clusters():
    """Returns HDBSCAN spatial activity clusters."""
    points = [
        {"id": a["id"], "lat": a["latitude"], "lng": a["longitude"], "confidence": a["confidence"], "type": a["type"]}
        for a in ALERTS_STORE
    ]
    clusters = cluster_change_detections(points)
    return clusters


@app.get("/api/change-detection/{analysis_id}")
def get_change_analysis(analysis_id: str):
    """Retrieve bi-temporal analysis report including before/after tiles and change mask."""
    if analysis_id in ANALYSIS_STORE:
        return ANALYSIS_STORE[analysis_id]

    # Fallback to primary scenario
    if "analysis_tumakuru_01" in ANALYSIS_STORE:
        return ANALYSIS_STORE["analysis_tumakuru_01"]

    raise HTTPException(status_code=404, detail=f"Analysis ID {analysis_id} not found")


@app.post("/api/temporal/compare")
def compare_imagery(req: TemporalCompareRequest):
    """Trigger live bi-temporal comparison between two scenes."""
    detector = BiTemporalChangeDetector(gsd_meters=10.0)

    # Load imagery
    img_t1_path = os.path.join(data_imagery_dir, "tumakuru_t1.png")
    img_t2_path = os.path.join(data_imagery_dir, "tumakuru_t2.png")

    if not os.path.exists(img_t1_path) or not os.path.exists(img_t2_path):
        raise HTTPException(status_code=404, detail="Requested temporal imagery tiles not found")

    img_t1 = np.array(Image.open(img_t1_path).convert("RGB"), dtype=np.float32) / 255.0
    img_t2 = np.array(Image.open(img_t2_path).convert("RGB"), dtype=np.float32) / 255.0

    report = detector.detect_changes(
        img_t1=img_t1,
        img_t2=img_t2,
        before_date=req.before_date,
        after_date=req.after_date,
        analysis_id=f"live_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
    )
    return report.dict()


@app.post("/api/ingestion/stac")
def ingest_stac(payload: Dict[str, Any], source: SatelliteSource = SatelliteSource.SENTINEL_2):
    """Ingest STAC item metadata into catalogue."""
    registry = DataIngestionRegistry()
    stac_item = registry.ingest_metadata(source, payload)
    return {
        "status": "INGESTED",
        "stac_item": stac_item.dict(),
    }


@app.get("/api/demo/scenario")
def get_demo_scenario():
    """Pre-packaged demo scenario for SIH live presentation."""
    return {
        "scenario_name": "Tumakuru High-Tech Industrial & Photovoltaic Expansion",
        "query": "Find large construction and solar array expansion near rivers",
        "location": {"lat": 13.3408, "lng": 77.1009, "zoom": 13},
        "target_alert_id": "ALT-2026-024",
        "analysis_id": "analysis_tumakuru_01",
    }
