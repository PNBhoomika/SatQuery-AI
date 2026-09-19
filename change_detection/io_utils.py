"""
I/O and Geospatial Utilities for Change Detection Module (Member 3).
Handles Cloud-Optimized GeoTIFF (COG) read/write, QA mask bit-flag decoding,
STAC Item parsing, and SAR co-registration.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("change_detection.io_utils")

# Try importing rasterio; fall back to PIL / tifffile / synthetic array handling if missing
try:
    import rasterio
    from rasterio.transform import Affine
    from rasterio.crs import CRS
    HAS_RASTERIO = True
except ImportError:  # pragma: no cover
    HAS_RASTERIO = False
    rasterio = None
    Affine = None
    CRS = None

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# QA Mask Bit Allocations as mandated by PS §2.2.3
QA_BIT_VALID_DATA = 1 << 0      # bit 0 = 1
QA_BIT_CLOUD = 1 << 1           # bit 1 = 2
QA_BIT_CLOUD_SHADOW = 1 << 2    # bit 2 = 4
QA_BIT_SNOW = 1 << 3            # bit 3 = 8
QA_BIT_HAZE = 1 << 4            # bit 4 = 16
QA_BIT_WATER = 1 << 5           # bit 5 = 32
QA_BIT_SATURATED = 1 << 6       # bit 6 = 64
QA_BIT_CIRRUS = 1 << 7          # bit 7 = 128


def read_cog(path: Union[str, Path]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Read a Cloud-Optimized GeoTIFF (COG) into a numpy array and profile dictionary.

    Args:
        path: Path to the GeoTIFF/COG file.

    Returns:
        tuple (array, profile) where:
            - array: np.ndarray of shape (C, H, W) or (H, W)
            - profile: dict containing geospatial and raster metadata (CRS, transform, dtype, etc.)
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {p}")

    if HAS_RASTERIO:
        with rasterio.open(p) as src:
            data = src.read()  # (C, H, W)
            profile = src.profile.copy()
            if src.count == 1:
                data = data[0]
            # Convert transform and crs to serializable/inspectable representation if needed
            profile["crs_str"] = str(src.crs) if src.crs else "EPSG:4326"
            profile["bounds"] = list(src.bounds)
            return data, profile

    # Fallback when rasterio is not installed in lightweight test environments
    if HAS_PIL:
        img = Image.open(p)
        arr = np.array(img)
        if arr.ndim == 2:
            arr = arr[np.newaxis, ...]  # (1, H, W)
        elif arr.ndim == 3 and arr.shape[2] in (1, 3, 4):
            arr = np.transpose(arr, (2, 0, 1))  # (C, H, W)
        h, w = arr.shape[-2], arr.shape[-1]
        profile = {
            "driver": "GTiff",
            "count": arr.shape[0],
            "dtype": str(arr.dtype),
            "width": w,
            "height": h,
            "crs_str": "EPSG:4326",
            "bounds": [0.0, 0.0, float(w), float(h)],
            "transform": [1.0, 0.0, 0.0, 0.0, -1.0, float(h)],
        }
        return arr[0] if arr.shape[0] == 1 else arr, profile

    raise RuntimeError("Neither rasterio nor PIL is available to read image files.")


def write_cog(
    path: Union[str, Path],
    array: np.ndarray,
    profile: Optional[Dict[str, Any]] = None
) -> str:
    """
    Write a numpy array to disk as a Cloud-Optimized GeoTIFF (COG).

    Args:
        path: Destination file path.
        array: np.ndarray of shape (H, W) or (C, H, W).
        profile: Optional dictionary of raster properties (driver, CRS, transform, nodata).

    Returns:
        Absolute string path to the created file.
    """
    out_path = Path(path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    arr = np.asarray(array)
    if arr.ndim == 2:
        arr = arr[np.newaxis, ...]  # Ensure shape (C, H, W) for dimension tracking
    count, height, width = arr.shape

    base_profile: Dict[str, Any] = {
        "driver": "GTiff",
        "count": count,
        "dtype": str(arr.dtype),
        "width": width,
        "height": height,
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "deflate",
        "nodata": None,
    }

    if profile:
        # Override defaults with provided profile attributes
        for k in ["crs", "transform", "nodata", "compress", "photometric", "count", "dtype"]:
            if k in profile:
                base_profile[k] = profile[k]

    if HAS_RASTERIO:
        # If CRS/transform are missing, supply default WGS84 unit grid
        if "crs" not in base_profile or base_profile["crs"] is None:
            base_profile["crs"] = "EPSG:4326"
        if "transform" not in base_profile or base_profile["transform"] is None:
            base_profile["transform"] = Affine(1.0, 0.0, 0.0, 0.0, -1.0, float(height))
        elif isinstance(base_profile["transform"], (tuple, list)):
            t = base_profile["transform"]
            if len(t) == 6:
                base_profile["transform"] = Affine.from_gdal(*t)

        base_profile["blockxsize"] = 512
        base_profile["blockysize"] = 512

        # Squeeze 3D single-band arrays to 2D before writing
        if arr.ndim == 3 and arr.shape[0] == 1 and base_profile.get("count") == 1:
            arr = arr[0]

        # Filter out non-rasterio profile keys
        valid_keys = [
            "driver", "count", "dtype", "width", "height", "crs", "transform",
            "tiled", "blockxsize", "blockysize", "compress", "nodata", "photometric"
        ]
        write_prof = {k: base_profile[k] for k in valid_keys if k in base_profile}

        try:
            from rio_cogeo.cogeo import cog_translate
            from rio_cogeo.profiles import cog_profiles

            temp_path = out_path.with_suffix(".tmp.tif")
            try:
                with rasterio.open(temp_path, "w", **write_prof) as dst:
                    if arr.ndim == 2:
                        dst.write(arr, 1)
                    else:
                        dst.write(arr)
                dst_profile = cog_profiles.get("deflate")
                dst_profile["blockxsize"] = 512
                dst_profile["blockysize"] = 512
                cog_translate(temp_path, out_path, dst_profile, in_memory=True, quiet=True)
            finally:
                if temp_path.exists():
                    temp_path.unlink()
        except ImportError:
            with rasterio.open(out_path, "w", **write_prof) as dst:
                if arr.ndim == 2:
                    dst.write(arr, 1)
                else:
                    dst.write(arr)
                if max(height, width) >= 512:
                    from rasterio.enums import Resampling
                    dst.build_overviews([2, 4, 8, 16], Resampling.average)
                    dst.update_tags(ns="rio_overview", resampling="average")
        return str(out_path)

    # Fallback using PIL
    if HAS_PIL:
        if count == 1:
            img = Image.fromarray(arr[0] if arr.ndim == 3 else arr)
        else:
            img = Image.fromarray(np.transpose(arr, (1, 2, 0)))
        img.save(out_path, format="TIFF")
        return str(out_path)

    raise RuntimeError("Neither rasterio nor PIL is available to write image files.")


def _looks_like_scl(arr: np.ndarray) -> bool:
    """
    Detect Sentinel-2 Scene Classification Layer (SCL values 0..11).
    Must NOT match custom bit-flag masks (which use powers of two ORed 
    together, so values can exceed 11, and never contain land classes 
    {4,5,6,7} unless explicitly constructed).

    Discriminators:
      - dtype must be uint8
      - max <= 11 (bit-flags with cloud+snow = 0b00001011 = 11 is a corner 
        case; require presence of land-class markers to disambiguate)
      - must contain at least one of {4 (vegetation), 5 (bare), 
        6 (water), 7 (unclassified)}
      - must contain at least 2 distinct values (a constant array is 
        ambiguous and defaults to bitflags)
    """
    if arr.dtype != np.uint8:
        return False
    if arr.min() < 0 or arr.max() > 11:
        return False
    present = set(np.unique(arr).tolist())
    if len(present) < 2:
        return False
    scl_land_markers = {4, 6, 7}
    return bool(present & scl_land_markers) or bool((5 in present) and (present & {8, 9, 10}))


def _decode_scl(arr: np.ndarray) -> Dict[str, np.ndarray]:
    """Decode Sentinel-2 SCL values 0..11 into standard boolean masks."""
    valid_data = arr != 0
    saturated = arr == 1
    cloud_shadow = arr == 3
    usable = (arr == 2) | (arr == 4) | (arr == 5) | (arr == 6) | (arr == 7)
    water = arr == 6
    cloud = (arr == 8) | (arr == 9)
    cirrus = arr == 10
    snow = arr == 11
    haze = np.zeros_like(valid_data, dtype=bool)
    return {
        "valid_data": valid_data,
        "cloud": cloud,
        "cloud_shadow": cloud_shadow,
        "snow": snow,
        "haze": haze,
        "water": water,
        "saturated": saturated,
        "cirrus": cirrus,
        "usable": usable,
    }


def _decode_bitflags(mask: np.ndarray) -> Dict[str, np.ndarray]:
    """Decode 8-bit optical QA mask into individual boolean masks based on PS §2.2.3."""
    valid_data = (mask & QA_BIT_VALID_DATA) > 0
    cloud = (mask & QA_BIT_CLOUD) > 0
    cloud_shadow = (mask & QA_BIT_CLOUD_SHADOW) > 0
    snow = (mask & QA_BIT_SNOW) > 0
    haze = (mask & QA_BIT_HAZE) > 0
    water = (mask & QA_BIT_WATER) > 0
    saturated = (mask & QA_BIT_SATURATED) > 0
    cirrus = (mask & QA_BIT_CIRRUS) > 0

    unusable = cloud | cloud_shadow | snow | haze | saturated | cirrus
    usable = valid_data & (~unusable)

    return {
        "valid_data": valid_data,
        "cloud": cloud,
        "cloud_shadow": cloud_shadow,
        "snow": snow,
        "haze": haze,
        "water": water,
        "saturated": saturated,
        "cirrus": cirrus,
        "usable": usable,
    }


def decode_qa_mask(
    path_or_array: Union[str, Path, np.ndarray],
    encoding: str = "auto",  # "auto" | "bitflags" | "scl"
) -> Dict[str, np.ndarray]:
    """
    Decode optical QA mask into individual boolean masks based on PS §2.2.3.
    Supports both custom 8-bit flag encoding and Sentinel-2 Scene Classification Layer (SCL).

    Bit Allocation (for bitflags):
        bit 0: valid_data (1)
        bit 1: cloud (2)
        bit 2: cloud_shadow (4)
        bit 3: snow (8)
        bit 4: haze (16)
        bit 5: water (32)
        bit 6: saturated (64)
        bit 7: cirrus (128)

    Args:
        path_or_array: File path to QA mask COG or pre-loaded 2D uint8 numpy array.
        encoding: Encoding format ('auto', 'bitflags', or 'scl').

    Returns:
        dict with boolean arrays of shape (H, W):
            - "valid_data": True where sensor pixel is valid
            - "cloud": True where cloud is present
            - "cloud_shadow": True where cloud shadow is cast
            - "snow": True where snow/ice is present
            - "haze": True where aerosol/haze is present
            - "water": True where permanent water baseline exists
            - "saturated": True where detector saturation occurred
            - "cirrus": True where thin cirrus cloud is detected
            - "usable": Composite boolean mask where pixel is clear of contaminants
    """
    if isinstance(path_or_array, (str, Path)):
        arr, _ = read_cog(path_or_array)
        if arr.ndim == 3:
            arr = arr[0]
    else:
        arr = np.asarray(path_or_array)
        if arr.ndim == 3:
            arr = arr[0]

    mask = arr.astype(np.uint8)
    if encoding == "scl":
        return _decode_scl(mask)
    if encoding == "bitflags":
        return _decode_bitflags(mask)
    # auto
    if _looks_like_scl(mask):
        return _decode_scl(mask)
    return _decode_bitflags(mask)


def parse_stac_item(path_or_dict: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse a STAC Item dictionary or JSON file into standardized metadata dictionary.

    Args:
        path_or_dict: File path to STAC Item JSON or dict representation.

    Returns:
        dict with standard fields:
            - id: Item identifier
            - datetime: Acquisition ISO8601 string
            - platform: Satellite platform (e.g., 'sentinel-2', 'landsat-8', 'sentinel-1')
            - incidence_angle: Float view/incidence angle in degrees (or None)
            - view_angle: Float off-nadir or viewing angle in degrees (or None)
            - orbit: Orbit number or direction ('ascending', 'descending', or int)
            - crs: CRS string or EPSG code
            - transform: Affine transform array or list
            - bbox: [minx, miny, maxx, maxy] in WGS84
    """
    if isinstance(path_or_dict, (str, Path)):
        p = Path(path_or_dict)
        if not p.is_file():
            raise FileNotFoundError(f"STAC Item file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif isinstance(path_or_dict, dict):
        data = path_or_dict
    else:
        raise TypeError(f"Expected dict or path, got {type(path_or_dict)}")

    props = data.get("properties", {})

    # Extract acquisition datetime
    dt = props.get("datetime") or props.get("acquisition_datetime") or props.get("start_datetime")

    # Extract platform with full extension hierarchy and alias normalization
    platform = (
        props.get("platform")
        or props.get("constellation")
        or props.get("eo:platform")
        or props.get("sar:platform")
        or props.get("sensor")
    )
    if not platform:
        for asset in data.get("assets", {}).values():
            if isinstance(asset, dict):
                platform = asset.get("eo:platform") or asset.get("sar:platform")
                if platform:
                    break
    if not platform and isinstance(props.get("instruments"), list) and props.get("instruments"):
        platform = props["instruments"][0]
    if not platform:
        platform = "unknown"

    platform = str(platform).lower().strip()
    platform = platform.replace("_", "-")
    platform_aliases = {
        "s2a": "sentinel-2a",
        "s2b": "sentinel-2b",
        "s2c": "sentinel-2c",
        "s1a": "sentinel-1a",
        "s1b": "sentinel-1b",
        "landsat-8": "landsat-8",
        "landsat-9": "landsat-9",
        "landsat8": "landsat-8",
        "landsat9": "landsat-9",
        "lc08": "landsat-8",
        "lc09": "landsat-9",
    }
    platform = platform_aliases.get(platform, platform)

    # Extract incidence angle (e.g. for SAR or off-nadir optical)
    incidence_angle = (
        props.get("sat:incidence_angle")
        or props.get("view:incidence_angle")
        or props.get("incidence_angle")
        or props.get("sar:incidence_angle")
    )
    if incidence_angle is not None:
        try:
            incidence_angle = float(incidence_angle)
        except (ValueError, TypeError):
            incidence_angle = None

    # Extract view angle / off-nadir
    view_angle = (
        props.get("view:off_nadir")
        or props.get("view:sun_elevation")
        or props.get("view_angle")
    )
    if view_angle is not None:
        try:
            view_angle = float(view_angle)
        except (ValueError, TypeError):
            view_angle = None

    # Extract orbit
    orbit = (
        props.get("sat:orbit_state")
        or props.get("sat:relative_orbit")
        or props.get("orbit")
        or props.get("orbit_state")
    )

    # Extract CRS and transform from proj extension
    raw_crs = props.get("proj:epsg") or props.get("proj:wkt2") or props.get("crs")
    if isinstance(raw_crs, (int, np.integer)):
        crs = f"EPSG:{raw_crs}"
    elif isinstance(raw_crs, str) and raw_crs.isdigit():
        crs = f"EPSG:{raw_crs}"
    else:
        crs = raw_crs or "EPSG:4326"

    transform = props.get("proj:transform") or props.get("transform")

    bbox = data.get("bbox", [0.0, 0.0, 0.0, 0.0])

    return {
        "id": data.get("id", "unknown_item"),
        "datetime": dt,
        "platform": platform,
        "incidence_angle": incidence_angle,
        "view_angle": view_angle,
        "orbit": orbit,
        "crs": crs,
        "transform": transform,
        "bbox": bbox,
        "properties": props,
    }
