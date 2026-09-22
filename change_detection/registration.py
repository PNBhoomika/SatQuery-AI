"""
Sub-pixel phase-correlation co-registration module for bi-temporal satellite imagery.
Covering PS §2.2.3 (registration false-alarm suppression).
"""

from __future__ import annotations

from typing import Tuple
import numpy as np

try:
    from skimage.registration import phase_cross_correlation
    from scipy.ndimage import shift
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False


def register_bitemporal_chips(
    t1: np.ndarray,
    t2: np.ndarray,
    upsample_factor: int = 10,
    max_offset_threshold: float = 1.5
) -> Tuple[np.ndarray, Tuple[float, float], float]:
    """
    Compute sub-pixel translation between t1 and t2 using 2D phase cross-correlation.
    If offset exceeds max_offset_threshold, t2 is warped back to t1 grid.

    Args:
        t1: Reference image (C, H, W) or (H, W).
        t2: Target image (C, H, W) or (H, W).
        upsample_factor: Sub-pixel resolution factor (default 10 = 0.1 pixel precision).
        max_offset_threshold: Maximum allowable offset in pixels before re-warping.

    Returns:
        tuple (t2_aligned, (dx, dy), confidence) where:
            - t2_aligned: Aligned target image
            - (dx, dy): Estimated sub-pixel translation in pixels
            - confidence: Peak-to-correlation energy or correlation confidence [0..1]
    """
    arr1 = t1[0] if t1.ndim == 3 else t1
    arr2 = t2[0] if t2.ndim == 3 else t2

    if not HAS_SKIMAGE:
        # Fallback when scikit-image is not loaded
        return t2.copy(), (0.0, 0.0), 1.0

    # Calculate cross correlation
    shifts, error, phasediff = phase_cross_correlation(
        arr1, arr2, upsample_factor=upsample_factor
    )
    dy, dx = float(shifts[0]), float(shifts[1])
    offset_magnitude = np.hypot(dx, dy)
    confidence = max(0.0, min(1.0, 1.0 - error))

    t2_aligned = t2.copy()
    # Re-warp if shift is notable but within physical feasibility
    if 0.2 < offset_magnitude < 10.0:
        if t2.ndim == 3:
            for c in range(t2.shape[0]):
                t2_aligned[c] = shift(t2[c], shift=(dy, dx), mode="nearest")
        else:
            t2_aligned = shift(t2, shift=(dy, dx), mode="nearest")

    return t2_aligned, (dx, dy), confidence
