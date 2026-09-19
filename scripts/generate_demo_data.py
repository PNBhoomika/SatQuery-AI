"""
Generates demo satellite datasets, runs feature embedding & vector indexing into Qdrant,
and produces precomputed mock fixtures for air-gapped demo mode.
"""

import os
import sys
import json
import numpy as np
from PIL import Image, ImageDraw

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from embeddings.multimodal_embedder import get_default_embedder
from vector_search.qdrant_service import get_vector_db
from change_detection.bi_temporal_detector import BiTemporalChangeDetector, cluster_change_detections


def generate_satellite_canvas(width=512, height=512, pattern="construction_t1"):
    """Creates a visually realistic synthetic satellite scene mimicking Sentinel-2 L2A RGB."""
    img = Image.new("RGB", (width, height), (38, 48, 36))
    draw = ImageDraw.Draw(img)

    np.random.seed(42 if "t1" in pattern else 84)

    # Base soil & vegetation texture
    pixels = np.zeros((height, width, 3), dtype=np.uint8)
    if "water" in pattern or "flood" in pattern:
        # River / water basin base (greens and earth tones)
        pixels[..., 0] = np.random.randint(45, 75, (height, width))
        pixels[..., 1] = np.random.randint(80, 120, (height, width))
        pixels[..., 2] = np.random.randint(40, 65, (height, width))
    else:
        # Semi-arid / scrubland / agricultural base
        pixels[..., 0] = np.random.randint(70, 110, (height, width))
        pixels[..., 1] = np.random.randint(85, 125, (height, width))
        pixels[..., 2] = np.random.randint(55, 85, (height, width))

    base_img = Image.fromarray(pixels)
    draw = ImageDraw.Draw(base_img)

    # Draw meandering river / canal across all scenes
    river_coords = [(0, 180), (120, 210), (260, 190), (380, 240), (512, 220)]
    for i in range(len(river_coords) - 1):
        x1, y1 = river_coords[i]
        x2, y2 = river_coords[i + 1]
        width_river = 18 if "flood" not in pattern or "t1" in pattern else 65
        river_color = (25, 45, 65) if "t1" in pattern else (30, 60, 95)
        draw.line([x1, y1, x2, y2], fill=river_color, width=width_river)

    # Agricultural field parcels
    for r in range(4):
        for c in range(4):
            x = c * 128 + 10
            y = r * 128 + 10
            field_col = (
                np.random.randint(50, 90),
                np.random.randint(90, 150),
                np.random.randint(40, 75),
            )
            draw.rectangle([x, y, x + 108, y + 108], outline=(55, 65, 50), fill=field_col)

    # Road network
    draw.line([(0, 360), (512, 380)], fill=(120, 115, 105), width=6)
    draw.line([(280, 0), (300, 512)], fill=(120, 115, 105), width=6)

    # Pattern-specific elements (T1 vs T2)
    if pattern == "construction_t1":
        # Raw open land / early cleared ground
        draw.rectangle([140, 80, 270, 200], fill=(95, 105, 85), outline=(75, 80, 65))
    elif pattern == "construction_t2":
        # Substantial new urban & industrial build-out!
        # Industrial sheds (bright high-albedo roofs)
        draw.rectangle([140, 80, 210, 140], fill=(215, 225, 235), outline=(90, 100, 110), width=2)
        draw.rectangle([220, 80, 270, 140], fill=(195, 205, 220), outline=(90, 100, 110), width=2)
        draw.rectangle([140, 150, 270, 200], fill=(205, 215, 225), outline=(90, 100, 110), width=2)
        # Solar PV array in southern sector (dark blue structured rows)
        for row_y in range(260, 340, 8):
            draw.line([(60, row_y), (220, row_y)], fill=(20, 35, 75), width=5)
        # Secondary access roads
        draw.line([(210, 140), (280, 360)], fill=(160, 155, 145), width=4)
    elif pattern == "flood_t1":
        # Normal agricultural river basin
        pass
    elif pattern == "flood_t2":
        # Inundation zones spreading over low-lying fields
        draw.ellipse([80, 160, 240, 280], fill=(28, 55, 85, 180))
        draw.ellipse([260, 180, 420, 310], fill=(28, 55, 85, 180))

    return base_img


def build_demo_dataset():
    data_dir = os.path.join(PROJECT_ROOT, "data", "demo")
    os.makedirs(data_dir, exist_ok=True)
    images_dir = os.path.join(data_dir, "imagery")
    os.makedirs(images_dir, exist_ok=True)

    print("[1/4] Generating realistic bi-temporal satellite scenes...")
    scenarios = {
        "tumakuru_t1": ("construction_t1", "Tumakuru Baseline Agricultural & Scrub", 13.3408, 77.1009, "2024-08-10"),
        "tumakuru_t2": ("construction_t2", "Tumakuru Industrial & Solar Corridor", 13.3408, 77.1009, "2026-08-14"),
        "krishna_basin_t1": ("flood_t1", "Krishna River Basin Pre-Monsoon", 16.2000, 80.5000, "2024-05-18"),
        "krishna_basin_t2": ("flood_t2", "Krishna River Flood Inundation", 16.2000, 80.5000, "2026-08-02"),
    }

    generated_paths = {}
    for key, (pattern, title, lat, lng, date_str) in scenarios.items():
        img = generate_satellite_canvas(512, 512, pattern)
        file_path = os.path.join(images_dir, f"{key}.png")
        img.save(file_path)
        generated_paths[key] = {
            "path": file_path,
            "title": title,
            "lat": lat,
            "lng": lng,
            "date": date_str,
            "img": img,
        }
        print(f"   [OK] Created {key}.png")

    print("[2/4] Running Bi-Temporal Change Detection engine...")
    detector = BiTemporalChangeDetector(gsd_meters=10.0, change_threshold=0.20)
    
    img_t1_arr = np.array(generated_paths["tumakuru_t1"]["img"], dtype=np.float32) / 255.0
    img_t2_arr = np.array(generated_paths["tumakuru_t2"]["img"], dtype=np.float32) / 255.0

    report = detector.detect_changes(
        img_t1=img_t1_arr,
        img_t2=img_t2_arr,
        before_date=generated_paths["tumakuru_t1"]["date"],
        after_date=generated_paths["tumakuru_t2"]["date"],
        analysis_id="analysis_tumakuru_01",
        center_coords=(13.3408, 77.1009),
    )
    print(f"   [OK] Change detected: {report.change_type} ({report.affected_area_hectares} ha, conf: {report.confidence_score*100}%)")

    print("[3/4] Indexing tiles into local Qdrant vector database...")
    embedder = get_default_embedder()
    vdb = get_vector_db()

    tiles_catalog = [
        {
            "id": "tile_tumakuru_ind_01",
            "title": "Tumakuru High-Tech Industrial Zone",
            "lat": 13.3408,
            "lng": 77.1009,
            "date": "2026-08-14",
            "sensor": "Sentinel-2 MSI",
            "confidence": 0.94,
            "img_key": "tumakuru_t2",
            "category": "New Construction / Solar",
        },
        {
            "id": "tile_tumakuru_base_02",
            "title": "Tumakuru South Rural Baseline",
            "lat": 13.3150,
            "lng": 77.0850,
            "date": "2024-08-10",
            "sensor": "Sentinel-2 MSI",
            "confidence": 0.88,
            "img_key": "tumakuru_t1",
            "category": "Agriculture & Soil",
        },
        {
            "id": "tile_krishna_flood_03",
            "title": "Krishna Delta Flood Inundation Zone",
            "lat": 16.2000,
            "lng": 80.5000,
            "date": "2026-08-02",
            "sensor": "Sentinel-1 SAR / Sentinel-2",
            "confidence": 0.91,
            "img_key": "krishna_basin_t2",
            "category": "Flood / Water Inundation",
        },
        {
            "id": "tile_chennai_port_04",
            "title": "Ennore Coastal Logistics Terminal",
            "lat": 13.2350,
            "lng": 80.3250,
            "date": "2026-07-29",
            "sensor": "Landsat-9 OLI-2",
            "confidence": 0.87,
            "img_key": "tumakuru_t2",
            "category": "Port & Infrastructure",
        },
    ]

    for tile in tiles_catalog:
        img_info = generated_paths[tile["img_key"]]
        vector = embedder.embed_image(img_info["img"])
        vdb.upsert_tile(
            tile_id=tile["id"],
            embedding=vector,
            metadata={
                "title": tile["title"],
                "thumbnail": f"/data/demo/imagery/{tile['img_key']}.png",
                "latitude": tile["lat"],
                "longitude": tile["lng"],
                "acquisition_date": tile["date"],
                "sensor": tile["sensor"],
                "confidence": tile["confidence"],
                "spectral_profile": {
                    "mean_ndvi": 0.42,
                    "ndwi": -0.15,
                    "surface_temp_c": 31.4,
                },
                "stac_metadata": {
                    "source": tile["sensor"],
                    "gsd": 10.0,
                    "cloud_cover": 3.2,
                },
                "bbox": [tile["lng"] - 0.02, tile["lat"] - 0.02, tile["lng"] + 0.02, tile["lat"] + 0.02],
            },
        )
        print(f"   [OK] Vector indexed: {tile['id']} ({tile['title']})")

    print(f"   [OK] Total vector index count: {vdb.count()} points")

    print("[4/4] Writing precomputed mock JSON datasets for frontend and offline demo...")
    mock_dir = os.path.join(PROJECT_ROOT, "frontend", "src", "mock")
    os.makedirs(mock_dir, exist_ok=True)

    # 1. searchResults.json
    search_results = [
        {
            "id": "res_001",
            "title": "Tumakuru Solar & Industrial Corridor",
            "thumbnail": "/data/demo/imagery/tumakuru_t2.png",
            "latitude": 13.3408,
            "longitude": 77.1009,
            "acquisitionDate": "2026-08-14",
            "sensor": "Sentinel-2 MSI",
            "relevanceScore": 94.8,
            "confidence": 0.92,
            "category": "Construction / Solar Array",
            "coordinates": "13.3408° N, 77.1009° E",
            "details": "Major land-use conversion with 18.4 hectares of new industrial shed roofing and high-efficiency photovoltaic arrays adjacent to regional transit artery.",
            "bbox": [77.0809, 13.3208, 77.1209, 13.3608]
        },
        {
            "id": "res_002",
            "title": "Krishna River South Inundation Sector",
            "thumbnail": "/data/demo/imagery/krishna_basin_t2.png",
            "latitude": 16.2000,
            "longitude": 80.5000,
            "acquisitionDate": "2026-08-02",
            "sensor": "Sentinel-1 SAR C-Band",
            "relevanceScore": 89.2,
            "confidence": 0.95,
            "category": "Flood Inundation",
            "coordinates": "16.2000° N, 80.5000° E",
            "details": "Co-registered SAR dual-polarization amplitude map showing severe floodplain expansion encroaching on agricultural holdings.",
            "bbox": [80.4800, 16.1800, 80.5200, 16.2200]
        },
        {
            "id": "res_003",
            "title": "Western Ghats Corridor Clearing",
            "thumbnail": "/data/demo/imagery/tumakuru_t1.png",
            "latitude": 12.9141,
            "longitude": 75.5000,
            "acquisitionDate": "2026-07-21",
            "sensor": "Landsat-9 OLI-2",
            "relevanceScore": 84.5,
            "confidence": 0.88,
            "category": "Canopy Disturbance",
            "coordinates": "12.9141° N, 75.5000° E",
            "details": "Linear canopy thinning along highway expansion right-of-way with localized soil exposure.",
            "bbox": [75.4800, 12.8941, 75.5200, 12.9341]
        },
        {
            "id": "res_004",
            "title": "Ennore Maritime Terminal Extension",
            "thumbnail": "/data/demo/imagery/tumakuru_t2.png",
            "latitude": 13.2350,
            "longitude": 80.3250,
            "acquisitionDate": "2026-08-11",
            "sensor": "Sentinel-2 MSI",
            "relevanceScore": 81.3,
            "confidence": 0.89,
            "category": "Coastal Infrastructure",
            "coordinates": "13.2350° N, 80.3250° E",
            "details": "Reclamation and hard-standing paving for container staging along coastal estuary margin.",
            "bbox": [80.3050, 13.2150, 80.3450, 13.2550]
        }
    ]
    with open(os.path.join(mock_dir, "searchResults.json"), "w") as f:
        json.dump(search_results, f, indent=2)

    # 2. alerts.json
    alerts = [
        {
            "id": "ALT-2026-024",
            "type": "New Construction / Urban Expansion",
            "latitude": 13.3408,
            "longitude": 77.1009,
            "confidence": 0.92,
            "detectedAt": "2026-08-14T06:22:00Z",
            "status": "PENDING REVIEW",
            "sensor": "Sentinel-2 MSI",
            "affectedArea": "18.4 ha",
            "locationName": "Tumakuru Industrial Hub, Karnataka",
            "analysisId": "analysis_tumakuru_01",
            "summary": "18.4 hectares of new industrial superstructure and solar array detected with high spectral certainty."
        },
        {
            "id": "ALT-2026-025",
            "type": "Flood / Water Inundation",
            "latitude": 16.2000,
            "longitude": 80.5000,
            "confidence": 0.95,
            "detectedAt": "2026-08-02T10:14:00Z",
            "status": "CONFIRMED",
            "sensor": "Sentinel-1 SAR",
            "affectedArea": "42.1 ha",
            "locationName": "Krishna River Delta Lowlands, Andhra Pradesh",
            "analysisId": "analysis_krishna_02",
            "summary": "Verified river overflowing embankment inundating 42.1 hectares of paddy cropland."
        },
        {
            "id": "ALT-2026-026",
            "type": "Deforestation / Land Clearing",
            "latitude": 12.9141,
            "longitude": 75.5000,
            "confidence": 0.88,
            "detectedAt": "2026-07-21T04:45:00Z",
            "status": "PENDING REVIEW",
            "sensor": "Landsat-9",
            "affectedArea": "7.8 ha",
            "locationName": "Western Ghats Ecological Buffer, Karnataka",
            "analysisId": "analysis_ghats_03",
            "summary": "NDVI drop of 0.38 indicates canopy removal across 7.8 hectares."
        },
        {
            "id": "ALT-2026-027",
            "type": "Seasonal Agricultural Variation",
            "latitude": 13.1200,
            "longitude": 76.9800,
            "confidence": 0.68,
            "detectedAt": "2026-06-15T11:00:00Z",
            "status": "REJECTED",
            "sensor": "Sentinel-2 MSI",
            "affectedArea": "5.2 ha",
            "locationName": "Kunigal Agrarian Belt, Karnataka",
            "analysisId": "analysis_kunigal_04",
            "summary": "Rejected by senior analyst: normal pre-sowing plowing cycle, not unauthorized land clearance."
        }
    ]
    with open(os.path.join(mock_dir, "alerts.json"), "w") as f:
        json.dump(alerts, f, indent=2)

    # 3. clusters.json (Generated via HDBSCAN clustering logic)
    clusters = cluster_change_detections([
        {"id": a["id"], "lat": a["latitude"], "lng": a["longitude"], "confidence": a["confidence"], "type": a["type"]}
        for a in alerts
    ])
    with open(os.path.join(mock_dir, "clusters.json"), "w") as f:
        json.dump(clusters, f, indent=2)

    # 4. analysis.json
    analysis_data = {
        "analysis_tumakuru_01": {
            "id": "analysis_tumakuru_01",
            "title": "Tumakuru Industrial & Photovoltaic Expansion",
            "location": "Tumakuru District, Karnataka (13.3408° N, 77.1009° E)",
            "beforeDate": "2024-08-10",
            "afterDate": "2026-08-14",
            "beforeImage": "/data/demo/imagery/tumakuru_t1.png",
            "afterImage": "/data/demo/imagery/tumakuru_t2.png",
            "changeMask": report.change_mask_base64,
            "changeHeatmap": report.change_heatmap_base64,
            "confidence": 0.92,
            "changeType": "New Construction / Urban Expansion",
            "affectedArea": "18.4 hectares",
            "sensor": "Sentinel-2 MSI (Level-2A BOA Reflectance)",
            "gsd": "10m Ground Sample Distance",
            "meanDeltaNdvi": -0.24,
            "status": "PENDING REVIEW",
            "notes": "Multimodal analysis confirms 18.4 ha urban infrastructure surge. High albedo roofs accompanied by systematic photovoltaic arrays."
        },
        "analysis_krishna_02": {
            "id": "analysis_krishna_02",
            "title": "Krishna River Delta Inundation",
            "location": "Guntur-Krishna Basin, Andhra Pradesh (16.2000° N, 80.5000° E)",
            "beforeDate": "2024-05-18",
            "afterDate": "2026-08-02",
            "beforeImage": "/data/demo/imagery/krishna_basin_t1.png",
            "afterImage": "/data/demo/imagery/krishna_basin_t2.png",
            "changeMask": report.change_mask_base64,
            "changeHeatmap": report.change_heatmap_base64,
            "confidence": 0.95,
            "changeType": "Flood / Water Inundation",
            "affectedArea": "42.1 hectares",
            "sensor": "Sentinel-1 SAR C-Band + Sentinel-2 MSI",
            "gsd": "10m GSD",
            "meanDeltaNdvi": -0.31,
            "status": "CONFIRMED",
            "notes": "Severe river basin swelling inundating low-lying agricultural corridors."
        }
    }
    with open(os.path.join(mock_dir, "analysis.json"), "w") as f:
        json.dump(analysis_data, f, indent=2)

    print("[OK] Successfully generated demo imagery, vector embeddings, and frontend mock fixtures!")


if __name__ == "__main__":
    build_demo_dataset()
