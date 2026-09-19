"""
Tile preprocessing, radiometric normalization, cloud mask generation, and spatial tiling.
"""

import os
import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
from PIL import Image

try:
    import tifffile
    HAS_TIFFFILE = True
except ImportError:
    HAS_TIFFFILE = False


class ImageTile(BaseModel):
    tile_id: str
    parent_scene_id: str
    row: int
    col: int
    width: int
    height: int
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    center: Tuple[float, float]  # (lat, lon)
    cloud_percentage: float
    stac_metadata: Dict[str, Any]
    image_path: Optional[str] = None


def radiometric_normalization(array: np.ndarray, lower_pct: float = 2.0, upper_pct: float = 98.0) -> np.ndarray:
    """Normalize multi-band image array to [0, 1] using robust percentile stretching."""
    if array.dtype == np.uint8:
        return array.astype(np.float32) / 255.0

    normalized = np.zeros_like(array, dtype=np.float32)
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


def create_cloud_mask(rgb_array: np.ndarray, scl_array: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Generate boolean cloud mask (True = cloud/shadow, False = clear).
    Uses Sentinel-2 SCL if provided, or high-reflectance thresholding.
    """
    if scl_array is not None:
        # Sentinel-2 SCL classes: 3=cloud shadows, 8=cloud medium prob, 9=cloud high prob, 10=cirrus
        cloud_classes = {3, 8, 9, 10}
        return np.isin(scl_array, list(cloud_classes))

    # Optical heuristic: clouds are characterized by uniformly high reflectance across all channels
    if rgb_array.ndim == 3 and rgb_array.shape[-1] >= 3:
        brightness = np.mean(rgb_array[..., :3], axis=-1)
        # Cloud mask where brightness is high and color saturation is low
        r, g, b = rgb_array[..., 0], rgb_array[..., 1], rgb_array[..., 2]
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
    # Avoid division by zero
    ndvi = np.where(denominator != 0, (nir - red) / (denominator + 1e-8), 0.0)
    return np.clip(ndvi, -1.0, 1.0)


def calculate_ndwi(green_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """
    Calculate Normalized Difference Water Index (NDWI) (McFeeters).
    NDWI = (Green - NIR) / (Green + NIR)
    Positive values typically indicate open water bodies.
    """
    green = green_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = green + nir
    ndwi = np.where(denominator != 0, (green - nir) / (denominator + 1e-8), 0.0)
    return np.clip(ndwi, -1.0, 1.0)


class TileProcessor:
    """Performs spatial tiling and metadata generation on scenes."""

    def __init__(self, tile_size: int = 256):
        self.tile_size = tile_size

    def generate_tiles(
        self,
        scene_image: np.ndarray,
        parent_scene_id: str,
        bbox: List[float],
        output_dir: Optional[str] = None,
    ) -> List[Tuple[ImageTile, np.ndarray]]:
        """
        Subdivide a satellite scene into standard tiles with interpolated geographic coordinates.
        Returns list of (ImageTile metadata, tile array).
        """
        h, w = scene_image.shape[:2]
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
                # Pad to uniform tile_size if edge tile
                if tile_crop.shape[0] != self.tile_size or tile_crop.shape[1] != self.tile_size:
                    pad_h = self.tile_size - tile_crop.shape[0]
                    pad_w = self.tile_size - tile_crop.shape[1]
                    if tile_crop.ndim == 3:
                        tile_crop = np.pad(tile_crop, ((0, pad_h), (0, pad_w), (0, 0)), mode="reflect")
                    else:
                        tile_crop = np.pad(tile_crop, ((0, pad_h), (0, pad_w)), mode="reflect")

                # Interpolate geographic bounding box
                tile_min_lon = min_lon + (x_start / w) * (max_lon - min_lon)
                tile_max_lon = min_lon + (x_end / w) * (max_lon - min_lon)
                tile_max_lat = max_lat - (y_start / h) * (max_lat - min_lat)
                tile_min_lat = max_lat - (y_end / h) * (max_lat - min_lat)

                center_lat = (tile_min_lat + tile_max_lat) / 2.0
                center_lon = (tile_min_lon + tile_max_lon) / 2.0

                tile_id = f"{parent_scene_id}_tile_r{r}_c{c}"
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
