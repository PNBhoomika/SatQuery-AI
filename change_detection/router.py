"""
FastAPI Router for Change Detection Module (Member 3).
Mounted by Member 4 (Backend / API Service).
Exposes endpoints for single-pair change detection, stack earliest-date analysis,
feedback ingestion, model metadata, and health probes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/change", tags=["Change Detection"])


class DetectChangeRequest(BaseModel):
    tile_t1_path: str = Field(..., description="File path or URI to t1 COG GeoTIFF")
    tile_t2_path: str = Field(..., description="File path or URI to t2 COG GeoTIFF")
    qa_mask_t1_path: str = Field(..., description="File path to t1 QA mask")
    qa_mask_t2_path: str = Field(..., description="File path to t2 QA mask")
    sar_t1_path: Optional[str] = Field(None, description="Optional path to co-registered S1 SAR t1")
    sar_t2_path: Optional[str] = Field(None, description="Optional path to co-registered S1 SAR t2")
    stac_item_t1: Optional[Dict[str, Any]] = Field(None, description="STAC metadata for t1")
    stac_item_t2: Optional[Dict[str, Any]] = Field(None, description="STAC metadata for t2")


class TileStackItem(BaseModel):
    tile_path: str
    date: str
    qa_mask_path: str
    sar_path: Optional[str] = None
    stac_item: Optional[Dict[str, Any]] = None


class DetectChangeStackRequest(BaseModel):
    stack: List[TileStackItem] = Field(..., min_length=3, description="Chronological stack of >= 3 acquisitions")


class FeedbackLabel(BaseModel):
    change_event_id: str
    decision: str = Field(..., pattern="^(confirm|reject)$")
    analyst_id: str
    timestamp: str
    notes: Optional[str] = None


class FeedbackUpdateRequest(BaseModel):
    labels: List[FeedbackLabel] = Field(..., min_length=1)


@router.post("/detect_change", status_code=status.HTTP_200_OK)
async def detect_change_endpoint(request: DetectChangeRequest):
    """
    Detect bi-temporal change between two COG tiles with 5-stage false-alarm suppression.
    Stubbed in Phase 1 — implemented in Phase 6.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint /detect_change not implemented in Phase 1 (Scaffold). Implemented in Phase 6."
    )


@router.post("/detect_change_over_stack", status_code=status.HTTP_200_OK)
async def detect_change_over_stack_endpoint(request: DetectChangeStackRequest):
    """
    Sliding window analysis over multi-temporal tile stack to identify earliest supported date.
    Stubbed in Phase 1 — implemented in Phase 6.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint /detect_change_over_stack not implemented in Phase 1 (Scaffold). Implemented in Phase 6."
    )


@router.post("/feedback/update", status_code=status.HTTP_200_OK)
async def feedback_update_endpoint(request: FeedbackUpdateRequest):
    """
    Ingest analyst Confirm/Reject feedback labels and trigger active learning retraining hook.
    Stubbed in Phase 1 — implemented in Phase 6.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint /feedback/update not implemented in Phase 1 (Scaffold). Implemented in Phase 6."
    )


@router.get("/model/info", status_code=status.HTTP_200_OK)
async def model_info_endpoint():
    """
    Retrieve active model architecture, weight checksums (SHA-256), and calibration metadata.
    Stubbed in Phase 1 — implemented in Phase 6.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint /model/info not implemented in Phase 1 (Scaffold). Implemented in Phase 6."
    )


@router.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz_endpoint():
    """
    Liveness and readiness health probe.
    Stubbed in Phase 1 — implemented in Phase 6.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint /healthz not implemented in Phase 1 (Scaffold). Implemented in Phase 6."
    )

