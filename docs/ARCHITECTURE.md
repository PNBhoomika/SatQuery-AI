# OrbitIntel | SatQuery-AI - System Architecture

**Project Name**: OrbitIntel  
**Product Name**: SatQuery-AI  
**Tagline**: Multimodal Semantic Retrieval & Spatio-Temporal Change Analytics Engine  
**SIH 2026 Problem Statement**: 26227 — Semantic Retrieval and Multi-Temporal Change Analysis of Satellite Imagery  

---

## 1. Modular Division & Responsibility Contracts

```
[Satellite Data Ingestion] (Member 1)
         ↓  (Standard COG + STAC Metadata JSON)
[Preprocessing & Tiling] (Member 1)
         ↓  (Analysis-ready 512x512 normalized arrays)
    ┌────┴──────────────────────────┐
    ↓                               ↓
[Embeddings Engine] (Member 2)   [Change Detection] (Member 3)
(512-dim Multimodal Vectors)      (Radiometric Delta + NDVI/NDWI)
    ↓                               ↓
[Vector Database - Qdrant]        [HDBSCAN Clustering Engine]
    └──────────────┬────────────────┘
                   ↓
        [FastAPI Gateway] (Member 4)
                   ↓  (REST API / JSON / Static Tiles)
    [Analyst Workstation Console] (Member 5)
                   ↓  (Confirm / Reject Feedback)
        [Active Learning Loop]
```

### Module 1: Data Ingestion & Preprocessing (`/data_ingestion`, `/preprocessing`)
- **Inputs**: Raw Sentinel-1 SAR (GRD), Sentinel-2 MSI (L2A), Landsat-8/9 Collection 2, ISRO Bhuvan open data.
- **Outputs**: Analysis-Ready Tiles (Cloud-Optimized GeoTIFF/PNG) + STAC 1.0.0 metadata JSON.
- **Contract**: Ensures standard pixel resolution (10m GSD), cloud/shadow masking (SCL band), radiometric percentile stretching [0, 1].

### Module 2: Multimodal Embedding (`/embeddings`)
- **Inputs**: Text queries (string) OR Image tile arrays (RGB / spectral).
- **Outputs**: Unit-normalized 512-dimensional vector embedding.
- **Contract**: Exposes `embed_text(query)` and `embed_image(tile)`. Swappable between lightweight CPU hybrid projector and PyTorch RemoteCLIP / OpenCLIP checkpoints.

### Module 3: Change Detection & Spatial Clustering (`/change_detection`)
- **Inputs**: Bi-temporal image pair (`img_t1`, `img_t2`) from acquisition dates T1 and T2.
- **Outputs**: `ChangeDetectionReport` containing change category, confidence score, affected hectares, binary change mask, heatmap base64, and HDBSCAN cluster hulls.
- **Contract**: Exposes `detect_changes()` and `cluster_change_detections()`.

### Module 4: Backend API Gateway (`/backend`)
- **Inputs**: HTTP requests from Frontend (`/api/search/semantic`, `/api/temporal/compare`, `/api/feedback`).
- **Outputs**: Structured JSON API responses following OpenAPI specification.
- **Contract**: Isolates ML models and databases from the frontend.

### Module 5: Frontend Analyst Console (`/frontend`)
- **Inputs**: REST API JSON from Member 4.
- **Outputs**: Interactive user interface (MapLibre/Leaflet map, swipe comparison slider, natural language search, feedback modals).
- **Contract**: Never communicates directly with PyTorch, FAISS, or Qdrant.

---

## 2. API Endpoints Matrix

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Service health, vector DB points count, module statuses |
| `POST` | `/api/search/semantic` | Natural language text query -> 512-dim vector -> Qdrant retrieval |
| `POST` | `/api/search/image` | Satellite image upload -> vector retrieval |
| `GET` | `/api/alerts` | List change alerts (filterable by `status=PENDING\|CONFIRMED\|REJECTED`) |
| `GET` | `/api/alerts/{id}` | Specific alert details |
| `POST` | `/api/feedback` | Analyst-in-the-loop Confirm/Reject feedback submission |
| `GET` | `/api/clusters` | HDBSCAN spatial clusters with centroid and member detections |
| `POST` | `/api/temporal/compare` | Live bi-temporal change detection execution |
| `GET` | `/api/change-detection/{id}` | Detailed change report with before/after imagery & masks |
| `GET` | `/api/demo/scenario` | Instant SIH presentation scenario metadata |
