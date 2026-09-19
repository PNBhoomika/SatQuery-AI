"""
OrbitIntel / SatQuery-AI - Module 3: Multimodal Embeddings
Text-to-vector and Image-to-vector embeddings for satellite scenes.
"""

from .multimodal_embedder import (
    BaseMultimodalEmbedder,
    RemoteCLIPAdapter,
    PrithviEarthObservationAdapter,
    HybridSemanticSpectralEmbedder,
    get_default_embedder,
)

__all__ = [
    "BaseMultimodalEmbedder",
    "RemoteCLIPAdapter",
    "PrithviEarthObservationAdapter",
    "HybridSemanticSpectralEmbedder",
    "get_default_embedder",
]
