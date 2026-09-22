"""
OrbitIntel / SatQuery-AI - Natural Language Geospatial Query Parser
SIH 2026 Problem Statement 26227

Extracts:
1. Target location / Area of Interest (AOI), checking against indexed demo catalogs
   and identifying unindexed regions (Bengaluru, Hyderabad, Mumbai, etc.)
2. Semantic change categories (vegetation, water/flood, urban expansion, construction, solar, port)
3. Temporal intervals (acquisition years, date windows)
"""

import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class ParsedGeoQuery:
    raw_query: str
    target_aoi: Optional[str] = None           # 'tumakuru' | 'krishna' | 'ennore' | None
    target_aoi_name: Optional[str] = None      # Full display name of AOI
    requested_location: Optional[str] = None   # Raw extracted location name (e.g. 'Bengaluru', 'Hyderabad')
    is_supported_location: bool = True         # False if an unindexed location was requested
    semantic_types: List[str] = field(default_factory=list)  # ['VEGETATION', 'URBAN_EXPANSION', ...]
    years: List[int] = field(default_factory=list)           # [2024, 2026]
    keywords: List[str] = field(default_factory=list)


# Supported / indexed catalog AOIs
SUPPORTED_AOIS = {
    "tumakuru": {
        "key": "tumakuru",
        "name": "Tumakuru Region / Industrial Corridor, Karnataka",
        "aliases": ["tumakuru", "tumkur", "tumakuru corridor", "vasantha narasapura", "tumkur district", "karnataka industrial"],
        "lat": 13.3408,
        "lng": 77.1009,
    },
    "krishna": {
        "key": "krishna",
        "name": "Krishna River Basin / Delta, Andhra Pradesh",
        "aliases": ["krishna", "krishna basin", "krishna delta", "krishna river", "vijayawada", "andhra basin", "andhra pradesh river"],
        "lat": 16.2000,
        "lng": 80.5000,
    },
    "ennore": {
        "key": "ennore",
        "name": "Ennore Coastal Region, Tamil Nadu",
        "aliases": ["ennore", "ennore port", "kamarajar port", "ennore coastal", "coromandel coast", "tamil nadu port"],
        "lat": 13.2350,
        "lng": 80.3250,
    },
}

# Known locations not in current local indexed catalog
KNOWN_UNINDEXED_LOCATIONS = {
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "hyderabad": "Hyderabad",
    "secunderabad": "Hyderabad",
    "telangana": "Telangana",
    "mumbai": "Mumbai",
    "delhi": "Delhi NCR",
    "new delhi": "Delhi NCR",
    "kolkata": "Kolkata",
    "pune": "Pune",
    "ahmedabad": "Ahmedabad",
    "chennai": "Chennai City",
    "chennai city": "Chennai City",
    "jaipur": "Jaipur",
    "kochi": "Kochi",
    "cochin": "Kochi",
    "kerala": "Kerala",
    "goa": "Goa",
    "gurgaon": "Gurgaon",
    "noida": "Noida",
    "lucknow": "Lucknow",
    "chandigarh": "Chandigarh",
    "visakhapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",
}

# Semantic Category Taxonomy
SEMANTIC_CATEGORIES = {
    "VEGETATION": {
        "keywords": [
            "vegetation", "loss", "deforestation", "forest", "tree", "trees",
            "agriculture", "crop", "farmland", "farming", "greenery", "canopy",
            "biomass", "flora", "green cover", "soil", "rural"
        ],
        "weight": 1.5,
    },
    "URBAN_EXPANSION": {
        "keywords": [
            "urban", "expansion", "encroachment", "settlement", "sprawl",
            "built-up", "residential", "city growth", "development", "built surface"
        ],
        "weight": 1.4,
    },
    "CONSTRUCTION_INDUSTRIAL": {
        "keywords": [
            "construction", "industrial", "shed", "factory", "superstructure",
            "building", "buildings", "high-tech", "manufacturing", "corridor",
            "industrial hub", "infrastructure"
        ],
        "weight": 1.4,
    },
    "SOLAR_ENERGY": {
        "keywords": [
            "solar", "photovoltaic", "pv", "solar array", "solar park",
            "renewable", "clean energy", "solar panel", "panels"
        ],
        "weight": 1.5,
    },
    "WATER_FLOOD": {
        "keywords": [
            "water", "water-body", "waterbody", "flood", "flooding", "inundation",
            "river", "delta", "basin", "lake", "reservoir", "submerged", "drainage"
        ],
        "weight": 1.5,
    },
    "PORT_INFRASTRUCTURE": {
        "keywords": [
            "port", "terminal", "logistics", "harbor", "harbour", "coastal",
            "shipping", "dock", "docks", "berth", "wharf", "marine"
        ],
        "weight": 1.5,
    },
}


class NaturalLanguageQueryParser:
    """Extracts entities, spatial scopes, and change semantics from queries."""

    @staticmethod
    def parse(query: str) -> ParsedGeoQuery:
        clean_q = query.strip()
        q_lower = clean_q.lower()
        words = re.findall(r"\b[\w\-]+\b", q_lower)

        parsed = ParsedGeoQuery(raw_query=clean_q, keywords=words)

        # 1. Extract Years
        years_found = [int(y) for y in re.findall(r"\b(20[12]\d)\b", q_lower)]
        parsed.years = sorted(list(set(years_found)))

        # 2. Extract Semantic Categories
        matched_categories = []
        for cat_name, cat_meta in SEMANTIC_CATEGORIES.items():
            for kw in cat_meta["keywords"]:
                # Check for single word or phrase match
                if " " in kw:
                    if kw in q_lower:
                        matched_categories.append(cat_name)
                        break
                else:
                    if kw in words:
                        matched_categories.append(cat_name)
                        break
        parsed.semantic_types = list(set(matched_categories))

        # 3. Location Extraction
        # A. Check against Supported AOIs (Aliases)
        for aoi_key, aoi_data in SUPPORTED_AOIS.items():
            for alias in aoi_data["aliases"]:
                pattern = r"\b" + re.escape(alias) + r"\b"
                if re.search(pattern, q_lower):
                    parsed.target_aoi = aoi_key
                    parsed.target_aoi_name = aoi_data["name"]
                    parsed.requested_location = alias.title()
                    parsed.is_supported_location = True
                    return parsed

        # B. Check against Known Unindexed Locations
        for unindexed_alias, formal_name in KNOWN_UNINDEXED_LOCATIONS.items():
            pattern = r"\b" + re.escape(unindexed_alias) + r"\b"
            if re.search(pattern, q_lower):
                parsed.target_aoi = None
                parsed.target_aoi_name = None
                parsed.requested_location = formal_name
                parsed.is_supported_location = False
                return parsed

        # C. Heuristic Location extraction using prepositions: "around X", "near X", "in X"
        prep_pattern = r"\b(?:around|near|in|at|across|region of)\s+([A-Za-z\-]+(?:\s+[A-Za-z\-]+)?)"
        match = re.search(prep_pattern, clean_q, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            candidate_lower = candidate.lower()
            # Exclude non-geographic stop words e.g. "2024", "between", "major", "recent"
            stopwords = {"between", "from", "the", "recent", "major", "large", "new", "satellite", "earth"}
            if candidate_lower not in stopwords and not re.match(r"^\d+$", candidate_lower):
                parsed.target_aoi = None
                parsed.target_aoi_name = None
                parsed.requested_location = candidate.title()
                parsed.is_supported_location = False
                return parsed

        # D. No location mentioned in query -> broad search across all indexed AOIs
        parsed.target_aoi = None
        parsed.target_aoi_name = None
        parsed.requested_location = None
        parsed.is_supported_location = True
        return parsed


def get_available_aoi_descriptions() -> List[str]:
    """Returns human-friendly descriptions of all indexed demo areas of interest."""
    return [aoi["name"] for aoi in SUPPORTED_AOIS.values()]
