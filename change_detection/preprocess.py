"""
Preprocessing, radiometric normalization, view-angle verification, and seasonal baseline filtering.
Covering PS §2.2.3.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple
import numpy as np


def compute_spectral_indices(tile: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Compute Normalized Difference Vegetation Index (NDVI) and Normalized Difference Water Index (NDWI).
    Assumes channels: Red = channel 0 (or 2), Green = channel 1, NIR = channel 3 (or channel 0 if 3-band false color).
    """
    c, h, w = tile.shape if tile.ndim == 3 else (1, tile.shape[0], tile.shape[1])
    eps = 1e-6

    if c >= 4:
        red = tile[0].astype(np.float32)
        green = tile[1].astype(np.float32)
        nir = tile[3].astype(np.float32)
    elif c == 3:
        # Pseudo NIR / RGB representation
        red = tile[0].astype(np.float32)
        green = tile[1].astype(np.float32)
        nir = tile[2].astype(np.float32)
    else:
        gray = tile[0].astype(np.float32) if tile.ndim == 3 else tile.astype(np.float32)
        return {"ndvi": np.zeros_like(gray), "ndwi": np.zeros_like(gray)}

    ndvi = (nir - red) / (nir + red + eps)
    ndwi = (green - nir) / (green + nir + eps)
    return {"ndvi": ndvi, "ndwi": ndwi}


def check_view_angle_consistency(
    meta_t1: Optional[Dict],
    meta_t2: Optional[Dict],
    max_delta_deg: float = 15.0
) -> Tuple[bool, float]:
    """
    Verify if viewing/incidence angle difference between t1 and t2 is within tolerance.

    Returns:
        tuple (is_consistent, delta_degrees)
    """
    if not meta_t1 or not meta_t2:
        return True, 0.0

    angle1 = meta_t1.get("view_angle") or meta_t1.get("incidence_angle")
    angle2 = meta_t2.get("view_angle") or meta_t2.get("incidence_angle")

    if angle1 is None or angle2 is None:
        return True, 0.0

    delta = abs(float(angle1) - float(angle2))
    return (delta <= max_delta_deg), delta


def radiometric_normalization(
    t1: np.ndarray,
    t2: np.ndarray,
    method: str = "standardization"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Normalize radiometric distributions between t1 and t2.
    """
    t1_norm = t1.astype(np.float32)
    t2_norm = t2.astype(np.float32)

    if method == "standardization":
        # Per-channel mean/std alignment
        for c in range(t1.shape[0] if t1.ndim == 3 else 1):
            ch1 = t1_norm[c] if t1.ndim == 3 else t1_norm
            ch2 = t2_norm[c] if t2.ndim == 3 else t2_norm
            std1 = float(np.std(ch1))
            std2 = float(np.std(ch2))
            # Align distribution only if both have non-trivial variance
            if std1 > 1e-4 and std2 > 1e-4:
                m1, s1 = float(np.mean(ch1)), std1
                m2, s2 = float(np.mean(ch2)), std2
                aligned_ch2 = ((ch2 - m2) / s2) * s1 + m1
                if t2.ndim == 3:
                    t2_norm[c] = aligned_ch2
                else:
                    t2_norm = aligned_ch2

    return t1_norm, t2_norm
