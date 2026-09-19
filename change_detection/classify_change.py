"""
Morphology and semantic change type classification module.
Covering PS §2.2.2.
"""

from __future__ import annotations

from typing import Tuple
import numpy as np

try:
    from scipy.ndimage import label, binary_dilation
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

MORPHOLOGY_CLASSES = ["appearance", "disappearance", "expansion", "contraction", "none"]
TYPE_CLASSES = ["construction", "clearance", "water_extent", "road", "unknown"]


def classify_change_morphology_rule_based(
    t1_bin: np.ndarray,
    t2_bin: np.ndarray,
    change_mask: np.ndarray
) -> str:
    """
    Rule-based morphology classification using connected component analysis:
      - appearance: features present in t2 where none existed in t1.
      - disappearance: features present in t1 absent in t2.
      - expansion: t2 feature borders dilated from t1 feature.
      - contraction: t1 feature borders shrunk to t2 feature.
      - none: no significant change.
    """
    if np.sum(change_mask) == 0:
        return "none"

    if not HAS_SCIPY:
        return "appearance"

    diff_pos = (t2_bin.astype(int) - t1_bin.astype(int)) > 0
    diff_neg = (t1_bin.astype(int) - t2_bin.astype(int)) > 0

    has_pos = np.any(diff_pos & (change_mask > 0))
    has_neg = np.any(diff_neg & (change_mask > 0))

    if has_pos and not has_neg:
        t1_dilated = binary_dilation(t1_bin)
        if np.any(t1_dilated & diff_pos):
            return "expansion"
        return "appearance"
    elif has_neg and not has_pos:
        t2_dilated = binary_dilation(t2_bin)
        if np.any(t2_dilated & diff_neg):
            return "contraction"
        return "disappearance"
    elif has_pos and has_neg:
        return "expansion"

    return "appearance"


def classify_change_semantics(
    morph_logits: Optional[np.ndarray],
    type_logits: Optional[np.ndarray],
    change_mask: np.ndarray
) -> Tuple[str, str]:
    """
    Convert model logits or fallback statistics to semantic category strings.

    Returns:
        tuple (change_type, change_morphology)
    """
    if np.sum(change_mask) == 0:
        return "unknown", "none"

    if morph_logits is not None and len(morph_logits) > 0:
        idx = int(np.argmax(morph_logits))
        morph_str = MORPHOLOGY_CLASSES[min(idx, len(MORPHOLOGY_CLASSES) - 1)]
    else:
        morph_str = "appearance"

    if type_logits is not None and len(type_logits) > 0:
        idx = int(np.argmax(type_logits))
        type_str = TYPE_CLASSES[min(idx, len(TYPE_CLASSES) - 1)]
    else:
        type_str = "construction"

    return type_str, morph_str
