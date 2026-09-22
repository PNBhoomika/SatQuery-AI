# SatQuery-AI: Member 3 — Change Detection Engine

**SIH 2026 Problem Statement 26227**: *"Semantic Retrieval and Multi-Temporal Change Analysis of Satellite Imagery"*  
**Owner**: Member 3 — Change Detection Engineer  
**Role**: On-premises, air-gapped bi-temporal satellite change detection, multi-temporal earliest-date identification, 5-stage false-alarm suppression, and active feedback retraining.

---

## 1. System Overview & Architecture

The Change Detection Module acts as the **"detect"** core of SatQuery-AI. It analyzes paired or stacked multi-temporal satellite imagery (Sentinel-2, Sentinel-1, Landsat-8/9, ISRO Bhuvan) to identify real terrestrial changes (infrastructure development, land clearance, water expansion/recession, road construction) while aggressively suppressing false alarms caused by clouds, shadows, seasonal phenology, and coregistration artifacts.

```
       +---------------------------------------------+
       |   Member 1: Data Ingestion & Preprocessing  |
       +---------------------------------------------+
               | (COG Tiles, 8-bit QA, S1 SAR, STAC)
               v
       +---------------------------------------------+
       |   Member 3: Change Detection Module         |
       |   1. Sub-pixel Phase Co-Registration        |
       |   2. Optical QA Contaminant Masking         |
       |   3. Seasonal NDVI/NDWI & Radiometric Norm  |
       |   4. Siamese Backbone (ConvNeXt/Prithvi)    |
       |   5. SAR Backscatter Fusion (VV/VH delta)   |
       |   6. Morphology & Semantic Type Heads       |
       |   7. Multi-temporal Earliest-Date Engine    |
       |   8. STAC & Cryptographic Provenance Export |
       +---------------------------------------------+
               | (Change GeoTIFF, Change Event JSON, STAC Item)
               v
       +---------------------------------------------+
       |   Member 4: Backend / API Service           |
       |   (FastAPI Orchestrator, PostGIS, Alerts)   |
       +---------------------------------------------+
               |
               v
       +---------------------------------------------+
       |   Member 5: Analyst Dashboard (React)       |
       +---------------------------------------------+
```

---

## 2. Input / Output Contracts

### 2.1 Inputs (from Member 1 — Data Ingestion)
- **`tile_t1`, `tile_t2`**: Cloud-Optimized GeoTIFF (COG) image chips (same AOI, different acquisition dates). Recommended 10 m Ground Sampling Distance (GSD) matching Sentinel-2.
- **`qa_mask_t1`, `qa_mask_t2`**: 8-bit integer QA mask chips aligned with the optical tiles, formatted according to `contracts/qa_mask.schema.json`.
- **`sar_t1`, `sar_t2` (Optional)**: Co-registered Sentinel-1 SAR chips (VV and VH polarizations in linear or dB scale).
- **`tile_stack`**: Ordered list of $\ge 3$ acquisitions `(tile, date, qa_mask, sar, stac_meta)` used for sliding-window earliest-change-date discovery.
- **`meta`**: STAC Item metadata dictionary or JSON specifying acquisition datetime, platform, orbit, CRS, affine transform, and incidence/view angles.

#### QA Mask Bit Specification:
Member 1 must encode pixel validity using the standard 8-bit allocation:
| Bit Index | Value | Name | Meaning when Bit = 1 |
|---|---|---|---|
| `bit 0` | `1` | `valid_data` | Valid sensor pixel (not nodata/fill) |
| `bit 1` | `2` | `cloud` | Opaque / thick cloud detected |
| `bit 2` | `4` | `cloud_shadow` | Cloud shadow detected on ground |
| `bit 3` | `8` | `snow` | Snow or ice cover detected |
| `bit 4` | `16` | `haze` | Atmospheric haze / aerosol scattering |
| `bit 5` | `32` | `water` | Permanent water baseline |
| `bit 6` | `64` | `saturated` | Sensor detector saturation / blooming |
| `bit 7` | `128` | `cirrus` | Thin high-altitude cirrus cloud |

### 2.2 Outputs (to Member 4 — Backend)
The module returns structured change events strictly matching `contracts/change_event.schema.json`:
```json
{
  "change_mask": "/path/to/change_mask.tif",
  "change_type": "construction",
  "change_morphology": "appearance",
  "confidence": 0.925,
  "earliest_supported_date": "2024-03-15T05:32:10Z",
  "bbox_wgs84": [77.2090, 28.6139, 77.2290, 28.6339],
  "stac_change_event": {
    "type": "Feature",
    "stac_version": "1.0.0",
    "id": "ce_20240315_a7b9c",
    "geometry": { ... },
    "properties": {
      "datetime": "2024-03-15T05:32:10Z",
      "change:type": "construction",
      "change:morphology": "appearance",
      "change:confidence": 0.925
    }
  },
  "provenance": {
    "model_name": "SatQuery-Siamese-ConvNeXt-T",
    "model_version": "1.0.0",
    "weights_sha256": "3a8f...91e2",
    "code_git_sha": "d4c81a2",
    "t1_scene_id": "S2A_20231201_T43REQ",
    "t2_scene_id": "S2B_20240315_T43REQ",
    "qa_mask_version": "1.0.0",
    "sar_fused": true,
    "suppression_stages_fired": ["qa", "registration", "seasonal", "sar", "confidence"],
    "radiometric_method": "histogram_matching",
    "registration_offset_px": [0.12, -0.08],
    "inference_latency_ms": 48
  },
  "debug": {
    "raw_change_prob": 0.96,
    "qa_coverage": 0.98,
    "sar_agreement": 0.91,
    "seasonal_delta": 0.04,
    "registration_confidence": 0.99
  }
}
```

---

## 3. How Member 4 Mounts `router.py`

Member 4 can mount the change detection router directly into their main FastAPI application without code duplication:

```python
# Member 4: backend/main.py
from fastapi import FastAPI
from change_detection.router import router as change_router

app = FastAPI(title="SatQuery-AI Enterprise Backend")

# Mount Member 3's router directly
app.include_router(change_router)

# All routes become available under /change:
#   POST /change/detect_change
#   POST /change/detect_change_over_stack
#   POST /change/feedback/update
#   GET  /change/model/info
#   GET  /change/healthz
```

---

## 4. How Member 1 Provides QA and SAR Data

1. **Optical QA Masks**:
   Member 1 writes 8-bit single-band GeoTIFF chips where pixel values represent bitwise OR combinations of the bit flags defined in Section 2.1.
2. **Sentinel-1 SAR Data**:
   When available, Member 1 provides co-registered 2-band GeoTIFFs (Band 1 = VV, Band 2 = VH) clipped to the exact bounding box and resolution of the optical tiles. If SAR is unavailable for a given pass, Member 1 passes `sar_t1=None, sar_t2=None`. The system gracefully degrades by relying on high optical model confidence ($\tau > 0.85$).

---

## 5. Air-Gap & On-Premises Deployment Procedure

To meet strict defense and national security requirements (air-gapped, no outbound internet access during inference):

### 5.1 Dataset Staging (Run Once Prior to Air-Gapping)
Execute the staging script on a staging machine with internet access:
```bash
bash change_detection/scripts/stage_offline_data.sh
```
This fetches:
- **LEVIR-CD+**: High-resolution building change detection dataset
- **S2Looking**: Global satellite side-looking bi-temporal change dataset
- **OSCD**: Onera Satellite Change Detection (multi-band Sentinel-2)
- **SECOND**: Semantic Change Detection dataset (multi-class change)
- **Sen1Floods11**: Sentinel-1 SAR and Sentinel-2 optical flood/water dataset

All downloaded archives are verified against `data/raw/MANIFEST.sha256`.

### 5.2 Offline Model Weight Verification
Before serving or running inference, weights are verified:
```bash
sha256sum -c change_detection/weights/MANIFEST.sha256
```
If a weight file's checksum fails, the service aborts startup immediately to prevent tampered or corrupted execution.

### 5.3 Deterministic Execution Guarantee
All PyTorch backbones, NumPy RNGs, and CUDA algorithms are seeded:
- `torch.manual_seed(42)`
- `numpy.random.seed(42)`
- `os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"`

### 5.4 Model Provenance (PS §2.2.7)
In accordance with SIH 2026 Problem Statement §2.2.7 (Pretrained public models):
- **Backbone**: `ibm-nasa-geospatial/Prithvi-EO-1.0-100M`
- **Source**: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-1.0-100M
- **Licence**: Apache 2.0 (Open Source, research and commercial deployment permitted)
- **Trained on**: HLS (Harmonized Landsat + Sentinel-2), 6-band surface reflectance
- **SHA-256**: `7fac0c8a8693198e32a055e0c5a967f8b005f382182b63df1b29fdcd5c880731` (verified in `change_detection/weights/prithvi/MANIFEST.sha256`)
- **Download script**: `change_detection/scripts/download_prithvi_weights.py`
- **Offline packaging**: `change_detection/weights/prithvi/` is distributed with the repository / air-gapped drive bundle so inference executes completely offline without external network calls.
- **Fine-tuning Strategy**: The 100M ViT encoder backbone remains **FROZEN** (`freeze_backbone: true`). Only the multi-task heads (`change_head`, `morphology_head`, `type_head`, and fusion neck) are fine-tuned on open change-detection datasets (LEVIR-CD+, OSCD, SECOND, Sen1Floods11).

---

## 6. Assumptions

1. **Target GSD**: 10 meters per pixel (matching Sentinel-2 10 m bands). High-resolution datasets (LEVIR-CD+ 0.5 m) are dynamically downsampled via area interpolation during training/inference adaptation.
2. **Angular Discrepancy Threshold**: A default angular limit of $15^\circ$ is enforced. Off-nadir differences $> 15^\circ$ without SAR structural backscatter confirmation will trigger false-alarm suppression.
3. **Precision Bias**: In adherence to PS §2.2.3, false alarms are weighted more severely than missed detections ($w_{FP} = 2 \times w_{FN}$) to minimize analyst fatigue.
4. **Environment Resilience**: In environments where native GDAL/rasterio bindings are missing, `io_utils.py` contains automated pure-Python / PIL fallback drivers while preserving GeoTIFF profiles.
