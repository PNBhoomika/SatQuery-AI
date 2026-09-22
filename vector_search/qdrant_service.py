"""
Vector Database service abstraction and local Qdrant implementation.
Stores image embeddings, spatial coordinates, acquisition date, sensor, and STAC metadata.
"""

import os
import uuid
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
try:
    from qdrant_client.http import models as rest
except ImportError:
    from qdrant_client import models as rest

logger = logging.getLogger("satquery.vector_db")

COLLECTION_NAME = "satellite_tiles"
VECTOR_DIM = 512


class SearchResultItem(BaseModel):
    id: str
    title: str
    thumbnail: str
    latitude: float
    longitude: float
    acquisition_date: str
    sensor: str
    relevance_score: float
    confidence: float
    spectral_profile: Dict[str, Any] = Field(default_factory=dict)
    stac_metadata: Dict[str, Any] = Field(default_factory=dict)
    bbox: List[float] = Field(default_factory=list)

    def to_frontend_dict(self) -> Dict[str, Any]:
        """Serialize to camelCase JSON keys matching TypeScript SearchResult interface."""
        return {
            "id": self.id,
            "title": self.title,
            "thumbnail": self.thumbnail,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "acquisitionDate": self.acquisition_date,
            "sensor": self.sensor,
            "relevanceScore": self.relevance_score,
            "confidence": self.confidence,
            "category": self.stac_metadata.get("category", ""),
            "details": self.stac_metadata.get("details", ""),
            "coordinates": f"{self.latitude:.4f}\u00b0 N, {self.longitude:.4f}\u00b0 E",
            "bbox": self.bbox,
        }


class BaseVectorDB:
    """Abstract vector storage contract supporting Qdrant, Milvus, and FAISS."""

    def initialize(self):
        raise NotImplementedError

    def upsert_tile(
        self,
        tile_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
    ) -> bool:
        raise NotImplementedError

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResultItem]:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError


class QdrantVectorDB(BaseVectorDB):
    """
    Qdrant implementation for local and production deployment.
    Uses local on-disk storage or in-memory persistence.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        if storage_path:
            os.makedirs(storage_path, exist_ok=True)
            self.client = QdrantClient(path=storage_path)
            logger.info(f"Qdrant running in local persistent mode at: {storage_path}")
        else:
            self.client = QdrantClient(":memory:")
            logger.info("Qdrant running in in-memory mode")
        self.collection_name = COLLECTION_NAME
        self.initialize()

    def initialize(self):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=rest.VectorParams(
                        size=VECTOR_DIM,
                        distance=rest.Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")

    def upsert_tile(
        self,
        tile_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
    ) -> bool:
        try:
            # Deterministic integer or UUID from tile_id
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, tile_id))
            point = rest.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "tile_id": tile_id,
                    "title": metadata.get("title", tile_id),
                    "thumbnail": metadata.get("thumbnail", ""),
                    "latitude": float(metadata.get("latitude", 0.0)),
                    "longitude": float(metadata.get("longitude", 0.0)),
                    "acquisition_date": metadata.get("acquisition_date", ""),
                    "sensor": metadata.get("sensor", "Sentinel-2"),
                    "confidence": float(metadata.get("confidence", 0.90)),
                    "spectral_profile": metadata.get("spectral_profile", {}),
                    "stac_metadata": metadata.get("stac_metadata", {}),
                    "bbox": metadata.get("bbox", []),
                },
            )
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert tile {tile_id}: {e}")
            return False

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResultItem]:
        try:
            # qdrant-client >= 1.7: use query_points instead of deprecated search()
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
            )
            raw_points = response.points if hasattr(response, "points") else response
            items = []
            for r in raw_points:
                payload = r.payload or {}
                # Cosine similarity score → percentage (score is already in [-1,1])
                relevance = max(0.0, min(100.0, float((r.score + 1.0) / 2.0 * 100.0)))
                item = SearchResultItem(
                    id=payload.get("tile_id", str(r.id)),
                    title=payload.get("title", f"Scene {r.id}"),
                    thumbnail=payload.get("thumbnail", ""),
                    latitude=payload.get("latitude", 13.3408),
                    longitude=payload.get("longitude", 77.1009),
                    acquisition_date=payload.get("acquisition_date", "2026-08-12"),
                    sensor=payload.get("sensor", "Sentinel-2"),
                    relevance_score=round(relevance, 1),
                    confidence=payload.get("confidence", 0.92),
                    spectral_profile=payload.get("spectral_profile", {}),
                    stac_metadata=payload.get("stac_metadata", {}),
                    bbox=payload.get("bbox", []),
                )
                items.append(item)
            return items
        except Exception as e:
            logger.error(f"Error executing vector search: {e}")
            return []

    def count(self) -> int:
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception:
            return 0


class MilvusVectorDBAdapter(BaseVectorDB):
    """Placeholder adapter for Milvus vector engine substitution."""

    def __init__(self, host: str = "localhost", port: int = 19530):
        self.host = host
        self.port = port
        logger.info(f"Milvus Vector DB adapter initialized for {host}:{port}")

    def initialize(self):
        logger.info("Milvus connection initialized.")

    def upsert_tile(self, tile_id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        logger.info(f"Milvus upsert tile: {tile_id}")
        return True

    def search(self, query_vector: List[float], top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        return []

    def count(self) -> int:
        return 0


_VECTOR_DB_INSTANCE: Optional[BaseVectorDB] = None

def get_vector_db(storage_dir: Optional[str] = None) -> BaseVectorDB:
    """Singleton getter for vector database."""
    global _VECTOR_DB_INSTANCE
    if _VECTOR_DB_INSTANCE is None:
        target_dir = storage_dir or os.path.join(os.path.dirname(__file__), "..", "data", "qdrant_db")
        _VECTOR_DB_INSTANCE = QdrantVectorDB(storage_path=target_dir)
    return _VECTOR_DB_INSTANCE
