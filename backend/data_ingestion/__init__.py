"""
OrbitIntel / SatQuery-AI - Module 1: Data Ingestion
Contracts and ingestors for Sentinel-1, Sentinel-2, Landsat, and ISRO Bhuvan satellite imagery.
"""

from .stac_provider import (
    SatelliteSource,
    STACMetadata,
    BaseSatelliteIngestor,
    Sentinel1Ingestor,
    Sentinel2Ingestor,
    LandsatIngestor,
    BhuvanIngestor,
    DataIngestionRegistry,
)

__all__ = [
    "SatelliteSource",
    "STACMetadata",
    "BaseSatelliteIngestor",
    "Sentinel1Ingestor",
    "Sentinel2Ingestor",
    "LandsatIngestor",
    "BhuvanIngestor",
    "DataIngestionRegistry",
]
