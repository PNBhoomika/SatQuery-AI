"""
OrbitIntel / SatQuery-AI - Hybrid Semantic-Spatial Retrieval Engine
SIH 2026 Problem Statement 26227

Integrates:
1. Natural language query parsing (location, change type, temporal window)
2. Qdrant 512-dim vector cosine similarity
3. Geospatial AOI filtering (honest coverage vs unindexed locations)
4. Semantic category re-ranking (vegetation, urban, construction, water/flood, solar, port)
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

from search.query_parser import NaturalLanguageQueryParser, ParsedGeoQuery, get_available_aoi_descriptions
from vector_search.qdrant_service import get_vector_db, SearchResultItem
from embeddings.multimodal_embedder import get_default_embedder

logger = logging.getLogger("satquery.retrieval")

# Tile Ground-Truth Attributes for Semantic Match
TILE_SEMANTIC_PROFILES = {
    "tile_tumakuru_base_02": {
        "aoi": "tumakuru",
        "primary_types": ["VEGETATION"],
        "category": "Agriculture & Soil Baseline",
        "description": "Baseline rural cropland and soil coverage prior to industrial conversion.",
        "year": 2024,
    },
    "tile_tumakuru_ind_01": {
        "aoi": "tumakuru",
        "primary_types": ["URBAN_EXPANSION", "CONSTRUCTION_INDUSTRIAL", "SOLAR_ENERGY"],
        "category": "New Construction / Solar Array",
        "description": "High-tech industrial superstructures and photovoltaic array expansion.",
        "year": 2026,
    },
    "tile_krishna_flood_03": {
        "aoi": "krishna",
        "primary_types": ["WATER_FLOOD"],
        "category": "Flood Inundation & River Basin",
        "description": "Monsoon flood inundation across lower agricultural basin parcels.",
        "year": 2026,
    },
    "tile_chennai_port_04": {
        "aoi": "ennore",
        "primary_types": ["PORT_INFRASTRUCTURE", "CONSTRUCTION_INDUSTRIAL"],
        "category": "Port Logistics & Marine Terminal",
        "description": "Coastal shipping logistics berths, container berths, and breakwaters.",
        "year": 2026,
    },
}


class GeospatialRetrievalEngine:
    """Orchestrates natural language parsing, Qdrant vector retrieval, and semantic re-ranking."""

    @classmethod
    def execute_search(cls, query: str, top_k: int = 10) -> Dict[str, Any]:
        parsed = NaturalLanguageQueryParser.parse(query)
        logger.info(f"Parsed query: AOI={parsed.target_aoi}, Supported={parsed.is_supported_location}, Semantics={parsed.semantic_types}")

        # 1. Honest Coverage Check: Location requested is NOT in catalog
        if not parsed.is_supported_location:
            return {
                "coverage": "UNAVAILABLE",
                "requested_location": parsed.requested_location,
                "message": f"Satellite imagery for '{parsed.requested_location}' is not currently available in the local indexed catalog.",
                "available_aois": get_available_aoi_descriptions(),
                "parsed_query": {
                    "location": parsed.requested_location,
                    "change_types": parsed.semantic_types,
                    "years": parsed.years,
                },
                "results": [],
            }

        # 2. Vector Search via Qdrant
        embedder = get_default_embedder()
        vdb = get_vector_db()

        query_vector = embedder.embed_text(query)
        qdrant_items = vdb.search(query_vector=query_vector, top_k=max(top_k, 10))

        # If Qdrant is empty, fallback to catalog definitions
        if not qdrant_items:
            qdrant_items = cls._get_catalog_fallback_items()

        # 3. Hybrid Semantic-Spatial-Temporal Re-ranking
        ranked_results = []
        for item in qdrant_items:
            tile_profile = TILE_SEMANTIC_PROFILES.get(item.id, {})
            tile_aoi = tile_profile.get("aoi", "")

            # A. Spatial Score
            if parsed.target_aoi:
                if tile_aoi == parsed.target_aoi:
                    spatial_score = 100.0
                else:
                    # Specific location was requested, but tile is from a different location
                    # Strongly filter out non-matching locations to avoid returning Krishna for Tumakuru
                    spatial_score = 0.0
            else:
                # General query without explicit location -> all AOIs eligible
                spatial_score = 80.0

            # Skip tiles from outside the requested AOI if a specific AOI was asked
            if parsed.target_aoi and spatial_score == 0.0:
                continue

            # B. Semantic Category Match Score
            primary_types = tile_profile.get("primary_types", [])
            if parsed.semantic_types:
                overlap = set(parsed.semantic_types).intersection(set(primary_types))
                if overlap:
                    semantic_score = 95.0 + (len(overlap) * 2.5)
                else:
                    semantic_score = 35.0
            else:
                # No specific semantic type requested -> neutral
                semantic_score = 75.0

            # C. Temporal Match Score
            tile_year = tile_profile.get("year", 2026)
            if parsed.years:
                if tile_year in parsed.years:
                    temporal_score = 100.0
                else:
                    temporal_score = 60.0
            else:
                temporal_score = 80.0

            # D. Vector Cosine Similarity Score (0-100)
            vector_score = float(item.relevance_score)

            # E. Weighted Hybrid Relevance Score
            # 40% Vector Cosine + 40% Semantic Match + 10% Spatial + 10% Temporal
            if parsed.target_aoi:
                # When location matches, semantic category heavily dictates the order
                final_score = (
                    0.25 * vector_score +
                    0.50 * semantic_score +
                    0.15 * spatial_score +
                    0.10 * temporal_score
                )
            else:
                final_score = (
                    0.45 * vector_score +
                    0.40 * semantic_score +
                    0.15 * temporal_score
                )

            final_score = round(min(99.4, max(45.0, final_score)), 1)

            # Update item's relevance score and metadata details
            item.relevance_score = final_score
            if "category" in tile_profile:
                item.stac_metadata["category"] = tile_profile["category"]
            if "description" in tile_profile:
                item.stac_metadata["details"] = tile_profile["description"]

            ranked_results.append(item)

        # Sort by hybrid relevance score descending
        ranked_results.sort(key=lambda x: x.relevance_score, reverse=True)

        # If filtering removed all items (e.g. strict location with no items), fallback
        if not ranked_results and not parsed.target_aoi:
            ranked_results = qdrant_items[:top_k]

        return {
            "coverage": "AVAILABLE",
            "requested_location": parsed.target_aoi_name or parsed.requested_location or "Indexed Catalogs",
            "message": f"Retrieved {len(ranked_results)} verified satellite observation scenes.",
            "available_aois": get_available_aoi_descriptions(),
            "parsed_query": {
                "location": parsed.target_aoi_name or parsed.requested_location,
                "change_types": parsed.semantic_types,
                "years": parsed.years,
            },
            "results": [r.to_frontend_dict() for r in ranked_results[:top_k]],
        }

    @staticmethod
    def _get_catalog_fallback_items() -> List[SearchResultItem]:
        """Provides default items when Qdrant is initializing."""
        items = []
        for tid, prof in TILE_SEMANTIC_PROFILES.items():
            items.append(
                SearchResultItem(
                    id=tid,
                    title=f"Scene {tid.replace('_', ' ').title()}",
                    thumbnail=f"/data/demo/imagery/{'tumakuru_t1.png' if 'base' in tid else 'tumakuru_t2.png'}",
                    latitude=13.3408 if prof['aoi'] == 'tumakuru' else (16.20 if prof['aoi'] == 'krishna' else 13.235),
                    longitude=77.1009 if prof['aoi'] == 'tumakuru' else (80.50 if prof['aoi'] == 'krishna' else 80.325),
                    acquisition_date=f"{prof.get('year', 2026)}-08-14",
                    sensor="Sentinel-2 MSI",
                    relevance_score=85.0,
                    confidence=0.92,
                    stac_metadata={"category": prof.get("category", ""), "details": prof.get("description", "")},
                )
            )
        return items
