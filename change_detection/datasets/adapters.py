"""
Domain adaptation, resolution-matched augmentation, and class-balanced sampling
utilities for cross-sensor satellite change detection.
Covering PS §2.2.2 & §2.2.3.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Union
import numpy as np


def resolution_matched_augment(
    img: np.ndarray,
    source_gsd: float,
    target_gsd: float = 10.0,
    random_resample: bool = False
) -> np.ndarray:
    """
    Resample an image chip from source GSD to target GSD (default 10m Sentinel-2 GSD).
    Handles:
      - Downsampling high-resolution sensors (e.g. 0.5m LEVIR-CD+) to 10m.
      - Upsampling coarse-resolution sensors (e.g. 30m Landsat) to 10m.
      - Random resampling within [0.85 * target, 1.15 * target] to simulate cross-sensor GSD variations.

    Args:
        img: Array of shape (C, H, W) or (H, W).
        source_gsd: Ground sampling distance of input in meters (e.g. 0.5 for LEVIR, 30.0 for Landsat).
        target_gsd: Desired target ground sampling distance in meters (default 10.0 for Sentinel-2).
        random_resample: If True, randomly jitters target GSD between [0.85 * target, 1.15 * target].

    Returns:
        Resampled np.ndarray matching the target spatial scale.
    """
    if source_gsd <= 0 or target_gsd <= 0:
        raise ValueError("GSD values must be strictly positive.")

    eff_target_gsd = target_gsd
    if random_resample:
        eff_target_gsd *= float(np.random.uniform(0.85, 1.15))

    scale_factor = source_gsd / eff_target_gsd
    if abs(scale_factor - 1.0) < 1e-3:
        return img.copy()

    is_2d = img.ndim == 2
    data = img[np.newaxis, ...] if is_2d else img
    c, h, w = data.shape
    new_h = max(1, int(round(h * scale_factor)))
    new_w = max(1, int(round(w * scale_factor)))

    try:
        from scipy.ndimage import zoom
        # Zoom along spatial axes (1, 2)
        zoom_factors = (1.0, new_h / h, new_w / w)
        order = 1 if scale_factor < 1.0 else 3
        resampled = zoom(data, zoom_factors, order=order)
    except ImportError:
        row_idx = (np.linspace(0, h - 1, new_h)).astype(int)
        col_idx = (np.linspace(0, w - 1, new_w)).astype(int)
        resampled = data[:, row_idx[:, None], col_idx]

    return resampled[0] if is_2d else resampled


def histogram_match(source: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """
    Match the cumulative distribution function (CDF) of source to reference image per channel.

    Args:
        source: Source image array (C, H, W) or (H, W).
        reference: Reference image array (C, H, W) or (H, W).

    Returns:
        Histogram-matched np.ndarray with shape and dtype matching source.
    """
    is_2d = source.ndim == 2
    src = source[np.newaxis, ...] if is_2d else source
    ref = reference[np.newaxis, ...] if reference.ndim == 2 else reference

    matched = np.zeros_like(src, dtype=np.float32)
    for c in range(src.shape[0]):
        src_c = src[c].flatten()
        ref_c = ref[c % ref.shape[0]].flatten()

        s_vals, bin_idx, s_counts = np.unique(src_c, return_inverse=True, return_counts=True)
        r_vals, r_counts = np.unique(ref_c, return_counts=True)

        s_quantiles = np.cumsum(s_counts).astype(np.float64) / src_c.size
        r_quantiles = np.cumsum(r_counts).astype(np.float64) / ref_c.size

        interp_r_vals = np.interp(s_quantiles, r_quantiles, r_vals)
        matched[c] = interp_r_vals[bin_idx].reshape(src[c].shape)

    return matched[0] if is_2d else matched


def domain_adapt(
    tile: np.ndarray,
    reference_image: Optional[np.ndarray] = None,
    reference_mean: Optional[np.ndarray] = None,
    reference_std: Optional[np.ndarray] = None,
    method: str = "standardization"
) -> np.ndarray:
    """
    Standardize tile reflectance to Sentinel-2 reference distribution.
    Supports histogram matching against reference scene and per-channel standardization.

    Args:
        tile: np.ndarray of shape (C, H, W) or (H, W).
        reference_image: Optional reference image for CDF histogram matching.
        reference_mean: Optional mean vector per channel.
        reference_std: Optional standard deviation vector per channel.
        method: "standardization", "histogram_match", or "both".

    Returns:
        Normalized np.ndarray float32 clamped to Sentinel-2 reflectance range [0.0, 1.0].
    """
    arr = tile.astype(np.float32)

    # 1. Histogram matching if reference image provided or requested
    if (method in ("histogram_match", "both") or reference_image is not None) and reference_image is not None:
        arr = histogram_match(arr, reference_image.astype(np.float32))

    # 2. Per-channel standardization to Sentinel-2 reflectance range
    if method in ("standardization", "both"):
        c = arr.shape[0] if arr.ndim == 3 else 1
        if reference_mean is None:
            reference_mean = np.array([0.15] * c, dtype=np.float32)
        if reference_std is None:
            reference_std = np.array([0.10] * c, dtype=np.float32)

        for i in range(c):
            ch = arr[i] if arr.ndim == 3 else arr
            m, s = float(np.mean(ch)), float(np.std(ch))
            if s > 1e-6:
                ch_norm = (ch - m) / s
                ch_adapted = ch_norm * reference_std[i] + reference_mean[i]
                if arr.ndim == 3:
                    arr[i] = ch_adapted
                else:
                    arr = ch_adapted

    # Clip to valid physical reflectance range [0.0, 1.0]
    return np.clip(arr, 0.0, 1.0)


def class_balanced_sampler(
    class_labels: Union[List[int], np.ndarray],
    num_classes: int = 5
) -> np.ndarray:
    """
    Compute inverse-frequency sampling weights for balancing rare change classes
    (e.g., road, water_extent, clearance).

    Args:
        class_labels: List or array of class indices.
        num_classes: Total number of classes.

    Returns:
        np.ndarray of sampling weights per sample.
    """
    labels = np.asarray(class_labels, dtype=int)
    if len(labels) == 0:
        return np.array([], dtype=np.float32)

    counts = np.bincount(labels, minlength=num_classes)
    total = len(labels)
    # Inverse-frequency weight with smoothing
    weights_per_class = total / (np.maximum(counts, 1) * num_classes)
    sample_weights = np.array([weights_per_class[c] for c in labels], dtype=np.float32)
    sum_weights = np.sum(sample_weights)
    if sum_weights > 0:
        return sample_weights / sum_weights
    return np.ones(len(labels), dtype=np.float32) / len(labels)
