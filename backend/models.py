"""
OrbitIntel / SatQuery-AI - Database Models (Member 4)
ORM models for Alerts, Analyst Feedback, Change Detection records, and Satellite Tiles.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from database import Base


class Alert(Base):
    """Geospatial anomaly change alert."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, index=True)
    type = Column(String(128), nullable=False)
    status = Column(String(32), default="PENDING REVIEW")  # PENDING REVIEW, CONFIRMED, REJECTED
    confidence = Column(Float, default=0.90)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(256), default="")
    affected_area = Column(String(64), default="")
    sensor = Column(String(64), default="Sentinel-2 MSI")
    detected_at = Column(String(64), default=datetime.utcnow().isoformat)
    analysis_id = Column(String(64), default="")
    summary = Column(Text, default="")
    feedback_action = Column(String(32), nullable=True)
    feedback_rationale = Column(String(128), nullable=True)
    feedback_notes = Column(Text, nullable=True)
    feedback_reviewed_at = Column(String(64), nullable=True)

    def to_dict(self):
        res = {
            "id": self.alert_id,
            "type": self.type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "confidence": self.confidence,
            "detectedAt": self.detected_at,
            "status": self.status,
            "sensor": self.sensor,
            "affectedArea": self.affected_area,
            "locationName": self.location_name,
            "analysisId": self.analysis_id,
            "summary": self.summary,
        }
        if self.feedback_action:
            res["feedback"] = {
                "action": self.feedback_action,
                "rationale": self.feedback_rationale or "",
                "analystNotes": self.feedback_notes or "",
                "reviewedAt": self.feedback_reviewed_at or "",
            }
        return res


class Feedback(Base):
    """Analyst active-learning review feedback."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), index=True, nullable=False)
    action = Column(String(32), nullable=False)  # CONFIRM, REJECT
    rationale = Column(String(128), default="")
    analyst_notes = Column(Text, default="")
    timestamp = Column(String(64), default=datetime.utcnow().isoformat)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChangeDetection(Base):
    """Historical record of bi-temporal change runs."""
    __tablename__ = "change_detections"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(64), unique=True, index=True)
    tile_id_t1 = Column(String(128))
    tile_id_t2 = Column(String(128))
    change_type = Column(String(128))
    confidence = Column(Float)
    affected_area_ha = Column(Float)
    affected_area_sq_m = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class SatelliteTile(Base):
    """Cataloged satellite image tile metadata."""
    __tablename__ = "satellite_tiles"

    id = Column(Integer, primary_key=True, index=True)
    tile_id = Column(String(128), unique=True, index=True)
    parent_scene_id = Column(String(128))
    sensor = Column(String(64))
    tile_x = Column(Integer, default=0)
    tile_y = Column(Integer, default=0)
    width = Column(Integer, default=256)
    height = Column(Integer, default=256)
    cloud_cover = Column(Float, default=0.0)
    file_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
