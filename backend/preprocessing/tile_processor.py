"""
OrbitIntel / SatQuery-AI - Preprocessing & Tiling Engine
Combines Member 1 (256x256 tiling, blank-tile rejection, metadata.csv export)
with Member 5 (radiometric normalization, cloud masking, NDVI, NDWI calculations).
"""

import os
import csv
import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from pydantic import BaseModel
from PIL import Image

try:
    import tifffile
    HAS_TIFFFILE = True
except ImportError:
    HAS_TIFFFILE = False

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


class ImageTile(BaseModel):
    tile_id: str
    parent_scene_id: str
    row: int
    col: int
    tile_x: int = 0
    tile_y: int = 0
    width: int = 256
    height: int = 256
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    center: Tuple[float, float]  # (lat, lon)
    cloud_percentage: float = 0.0
    stac_metadata: Dict[str, Any] = {}
    image_path: Optional[str] = None


def is_valid_tile(
    tile_array: np.ndarray,
    min_std: float = 4.0,
    max_blank_ratio: float = 0.95
) -> bool:
    """
    Member 1 Filter: Reject uniform or blank tiles (e.g., black nodata borders, open deep ocean, sensor cutoffs).
    """
    if tile_array is None or tile_array.size == 0:
        return False

    # Check standard deviation across channels
    std_val = float(np.std(tile_array))
    # If array is normalized [0, 1], scale standard deviation comparison
    threshold_std = min_std / 255.0 if tile_array.max() <= 1.0 else min_std
    if std_val < threshold_std:
        return False

    # Check fraction of pure zero (black border) or max value (white wash)
    v_min = tile_array.min()
    v_max = tile_array.max()
    zero_ratio = float(np.mean(tile_array == v_min))
    if zero_ratio > max_blank_ratio:
        return False

    sat_ratio = float(np.mean(tile_array == v_max))
    if sat_ratio > max_blank_ratio:
        return False

    return True


def radiometric_normalization(
    array: np.ndarray,
    lower_pct: float = 2.0,
    upper_pct: float = 98.0
) -> np.ndarray:
    """Normalize multi-band image array to [0, 1] using robust percentile stretching."""
    if array.dtype == np.uint8:
        return array.astype(np.float32) / 255.0

    if array.ndim == 2:
        channels = [array]
    else:
        channels = [array[..., c] for c in range(array.shape[-1])]

    stretched_channels = []
    for ch in channels:
        v_min, v_max = np.percentile(ch, (lower_pct, upper_pct))
        if v_max > v_min:
            scaled = np.clip((ch - v_min) / (v_max - v_min), 0.0, 1.0)
        else:
            scaled = np.zeros_like(ch, dtype=np.float32)
        stretched_channels.append(scaled)

    if array.ndim == 2:
        return stretched_channels[0]
    return np.stack(stretched_channels, axis=-1)


def create_cloud_mask(
    rgb_array: np.ndarray,
    scl_array: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Generate boolean cloud mask (True = cloud/shadow, False = clear).
    Uses Sentinel-2 SCL if provided, or optical reflectance thresholding.
    """
    if scl_array is not None:
        cloud_classes = {3, 8, 9, 10}
        return np.isin(scl_array, list(cloud_classes))

    if rgb_array.ndim == 3 and rgb_array.shape[-1] >= 3:
        brightness = np.mean(rgb_array[..., :3], axis=-1)
        saturation = np.max(rgb_array[..., :3], axis=-1) - np.min(rgb_array[..., :3], axis=-1)
        is_cloud = (brightness > 0.78) & (saturation < 0.12)
        return is_cloud
    return np.zeros((rgb_array.shape[0], rgb_array.shape[1]), dtype=bool)


def calculate_ndvi(nir_band: np.ndarray, red_band: np.ndarray) -> np.ndarray:
    """
    Calculate Normalized Difference Vegetation Index (NDVI).
    NDVI = (NIR - Red) / (NIR + Red)
    """
    nir = nir_band.astype(np.float32)
    red = red_band.astype(np.float32)
    denominator = nir + red
    ndvi = np.where(denominator != 0, (nir - red) / (denominator + 1e-8), 0.0)
    return np.clip(ndvi, -1.0, 1.0)


def calculate_ndwi(green_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """
    Calculate Normalized Difference Water Index (NDWI) (McFeeters).
    NDWI = (Green - NIR) / (Green + NIR)
    """
    green = green_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = green + nir
    ndwi = np.where(denominator != 0, (green - nir) / (denominator + 1e-8), 0.0)
    return np.clip(ndwi, -1.0, 1.0)


def load_satellite_image(image_path: str) -> np.ndarray:
    """
    Universal satellite image loader with fallback cascade:
    1. rasterio (multi-band GeoTIFF with geo-referencing)
    2. tifffile (fast scientific TIFF)
    3. PIL (standard formats: PNG, JPG, JPEG, TIFF)
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Satellite image not found: {image_path}")

    ext = os.path.splitext(image_path)[1].lower()

    if HAS_RASTERIO and ext in [".tif", ".tiff"]:
        try:
            with rasterio.open(image_path) as src:
                arr = src.read()
                # rasterio gives [bands, H, W] -> convert to [H, W, bands]
                if arr.ndim == 3:
                    return np.transpose(arr, (1, 2, 0))
                return arr
        except Exception:
            pass

    if HAS_TIFFFILE and ext in [".tif", ".tiff"]:
        try:
            arr = tifffile.imread(image_path)
            return arr
        except Exception:
            pass

    # Fallback: PIL
    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img)


class TileProcessor:
    """Performs spatial 256x256 tiling, filtering, and metadata generation."""

    def __init__(self, tile_size: int = 256):
        self.tile_size = tile_size

    def generate_tiles(
        self,
        scene_image: np.ndarray,
        parent_scene_id: str,
        bbox: Optional[List[float]] = None,
        output_dir: Optional[str] = None,
        filter_blank: bool = True,
        min_std: float = 4.0,
    ) -> List[Tuple[ImageTile, np.ndarray]]:
        """
        Subdivide satellite scene into standard 256x256 tiles.
        Filters invalid/blank edge tiles using Member 1 standard.
        """
        h, w = scene_image.shape[:2]
        if bbox is None:
            bbox = [77.0, 13.0, 77.2, 13.2]

        min_lon, min_lat, max_lon, max_lat = bbox

        tiles = []
        rows = math.ceil(h / self.tile_size)
        cols = math.ceil(w / self.tile_size)

        for r in range(rows):
            for c in range(cols):
                y_start = r * self.tile_size
                y_end = min((r + 1) * self.tile_size, h)
                x_start = c * self.tile_size
                x_end = min((c + 1) * self.tile_size, w)

                tile_crop = scene_image[y_start:y_end, x_start:x_end]

                # Member 1 edge tile handling: skip incomplete or blank edge crops if filter_blank
                if filter_blank and (tile_crop.shape[0] < self.tile_size // 2 or tile_crop.shape[1] < self.tile_size // 2):
                    continue

                if filter_blank and not is_valid_tile(tile_crop, min_std=min_std):
                    continue

                # Pad to uniform tile_size if needed
                if tile_crop.shape[0] != self.tile_size or tile_crop.shape[1] != self.tile_size:
                    pad_h = self.tile_size - tile_crop.shape[0]
                    pad_w = self.tile_size - tile_crop.shape[1]
                    if tile_crop.ndim == 3:
                        tile_crop = np.pad(tile_crop, ((0, pad_h), (0, pad_w), (0, 0)), mode="reflect")
                    else:
                        tile_crop = np.pad(tile_crop, ((0, pad_h), (0, pad_w)), mode="reflect")

                tile_min_lon = min_lon + (x_start / w) * (max_lon - min_lon)
                tile_max_lon = min_lon + (x_end / w) * (max_lon - min_lon)
                tile_max_lat = max_lat - (y_start / h) * (max_lat - min_lat)
                tile_min_lat = max_lat - (y_end / h) * (max_lat - min_lat)

                center_lat = (tile_min_lat + tile_max_lat) / 2.0
                center_lon = (tile_min_lon + tile_max_lon) / 2.0

                tile_id = f"{parent_scene_id}_x{x_start}_y{y_start}"
                cloud_mask = create_cloud_mask(tile_crop)
                cloud_pct = float(np.mean(cloud_mask) * 100.0)

                tile_path = None
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    tile_path = os.path.join(output_dir, f"{tile_id}.png")
                    save_img = (tile_crop * 255).astype(np.uint8) if tile_crop.max() <= 1.0 else tile_crop.astype(np.uint8)
                    Image.fromarray(save_img).save(tile_path)

                tile_meta = ImageTile(
                    tile_id=tile_id,
                    parent_scene_id=parent_scene_id,
                    row=r,
                    col=c,
                    tile_x=x_start,
                    tile_y=y_start,
                    width=self.tile_size,
                    height=self.tile_size,
                    bbox=[tile_min_lon, tile_min_lat, tile_max_lon, tile_max_lat],
                    center=(center_lat, center_lon),
                    cloud_percentage=cloud_pct,
                    stac_metadata={"source": "Sentinel-2", "cloud_cover": cloud_pct},
                    image_path=tile_path,
                )
                tiles.append((tile_meta, tile_crop))

        return tiles

    @staticmethod
    def export_metadata_csv(tiles: List[ImageTile], output_csv_path: str) -> None:
        """
        Exports tiles metadata to CSV matching Member 1 format with geospatial extensions.
        """
        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        fieldnames = [
            "tile_id",
            "source_image",
            "tile_x",
            "tile_y",
            "width",
            "height",
            "min_lon",
            "min_lat",
            "max_lon",
            "max_lat",
            "cloud_percentage"
        ]
        with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in tiles:
                writer.writerow({
                    "tile_id": t.tile_id,
                    "source_image": t.parent_scene_id,
                    "tile_x": t.tile_x,
                    "tile_y": t.tile_y,
                    "width": t.width,
                    "height": t.height,
                    "min_lon": round(t.bbox[0], 6),
                    "min_lat": round(t.bbox[1], 6),
                    "max_lon": round(t.bbox[2], 6),
                    "max_lat": round(t.bbox[3], 6),
                    "cloud_percentage": round(t.cloud_percentage, 2)
                })
