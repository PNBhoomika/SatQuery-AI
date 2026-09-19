from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geometry
from datetime import datetime


Base = declarative_base()


class SatelliteTile(Base):
    __tablename__ = "satellite_tiles"

    id = Column(Integer, primary_key=True, index=True)
    tile_id = Column(String, unique=True, nullable=False)
    satellite = Column(String, nullable=False)
    acquisition_date = Column(DateTime, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    image_url = Column(String, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, nullable=False)
    tile_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChangeDetection(Base):
    __tablename__ = "change_detections"

    id = Column(Integer, primary_key=True, index=True)
    tile_id_t1 = Column(String, nullable=False)
    tile_id_t2 = Column(String, nullable=False)
    change_detected = Column(String, nullable=False)
    change_type = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)