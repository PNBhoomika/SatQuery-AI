"""
OrbitIntel / SatQuery-AI - API Schemas (Member 4 & 5)
Pydantic contracts for request validation and structured API responses.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TextSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search description", example="new construction in industrial hub")
    top_k: int = Field(10, ge=1, le=50)
    min_confidence: Optional[float] = Field(0.0, ge=0.0, le=1.0)


class TemporalCompareRequest(BaseModel):
    scene_id_t1: str = Field("tumakuru_t1", description="Baseline before-scene identifier")
    scene_id_t2: str = Field("tumakuru_t2", description="Monitoring after-scene identifier")
    gsd_meters: float = Field(10.0, description="Ground Sample Distance resolution")
    analysis_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    alert_id: str = Field(..., description="Target alert identifier")
    action: str = Field(..., description="CONFIRM or REJECT")
    rationale: str = Field("Visual Inspection", description="Justification code")
    analyst_notes: Optional[str] = Field("", description="Observations or remarks")
    timestamp: Optional[str] = None


class STACIngestRequest(BaseModel):
    payload: Dict[str, Any]
    source: str = "Sentinel-2"
