# SatQuery-AI (SIH 2026 Problem Statement 26227)

Semantic Retrieval and Multi-Temporal Change Analysis of Satellite Imagery.

## Modules
- `change_detection/`: Change Detection Engine (Member 3)
  - Bi-temporal deep network + morphology & type heads
  - 5-stage false-alarm suppression pipeline (optical QA, sub-pixel co-registration, seasonal NDVI/NDWI climatology, Sentinel-1 SAR fusion, calibrated confidence weighting)
  - Multi-temporal sliding-window earliest-supported-date analysis
  - Active learning feedback loop & audit provenance
  - FastAPI router mountable by Member 4
