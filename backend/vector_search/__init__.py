"""
OrbitIntel / SatQuery-AI - Module 4: Vector Search
Vector database abstractions and Qdrant local integration.
"""

from .qdrant_service import (
    BaseVectorDB,
    QdrantVectorDB,
    MilvusVectorDBAdapter,
    SearchResultItem,
    get_vector_db,
)

__all__ = [
    "BaseVectorDB",
    "QdrantVectorDB",
    "MilvusVectorDBAdapter",
    "SearchResultItem",
    "get_vector_db",
]
