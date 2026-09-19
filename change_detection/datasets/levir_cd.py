"""
Dataset loader for LEVIR-CD+ (Building change detection, high-resolution optical pairs).
Uniformly returns (t1, t2, qa_t1, qa_t2, sar_t1, sar_t2, change_mask, morph_label, type_label).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np

try:
    import torch
    from torch.utils.data import Dataset
except ImportError:
    Dataset = object
    torch = None

from .adapters import resolution_matched_augment, domain_adapt


class LevirCDDataset(Dataset):
    """
    LEVIR-CD+ Dataset for bi-temporal building change detection.
    Source GSD: 0.5 m, resampled to 10.0 m Sentinel-2 target GSD.
    """

    def __init__(
        self,
        root_dir: Union[str, Path],
        split: str = "train",
        target_gsd: float = 10.0,
        transform=None,
    ):
        self.root_dir = Path(root_dir)
        self.split = split
        self.target_gsd = target_gsd
        self.transform = transform
        self.samples = []
        if self.root_dir.is_dir():
            split_dir = self.root_dir / split
            a_dir = split_dir / "A"
            if a_dir.is_dir():
                self.samples = sorted([p.name for p in a_dir.glob("*.png")])

    def __len__(self) -> int:
        return max(1, len(self.samples))

    def __getitem__(
        self, idx: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray], np.ndarray, int, int]:
        # Return synthetic sample if empty directory
        if not self.samples:
            h, w = 128, 128
            t1 = np.zeros((3, h, w), dtype=np.float32)
            t2 = np.zeros((3, h, w), dtype=np.float32)
            qa_t1 = np.ones((h, w), dtype=np.uint8)  # bit 0 = 1 (valid)
            qa_t2 = np.ones((h, w), dtype=np.uint8)
            sar_t1, sar_t2 = None, None
            change_mask = np.zeros((h, w), dtype=np.uint8)
            morph_label = 0  # none
            type_label = 0   # unknown / construction
            return t1, t2, qa_t1, qa_t2, sar_t1, sar_t2, change_mask, morph_label, type_label

        sample_name = self.samples[idx]
        split_dir = self.root_dir / self.split
        # Load from disk using PIL or image loader
        from PIL import Image
        img_a = np.array(Image.open(split_dir / "A" / sample_name)).transpose(2, 0, 1)
        img_b = np.array(Image.open(split_dir / "B" / sample_name)).transpose(2, 0, 1)
        mask_path = split_dir / "label" / sample_name
        mask = np.array(Image.open(mask_path)) if mask_path.exists() else np.zeros(img_a.shape[1:], dtype=np.uint8)
        if mask.ndim == 3:
            mask = mask[..., 0]
        mask = (mask > 0).astype(np.uint8)

        # Resolution match from 0.5m to target_gsd
        t1 = resolution_matched_augment(img_a, source_gsd=0.5, target_gsd=self.target_gsd)
        t2 = resolution_matched_augment(img_b, source_gsd=0.5, target_gsd=self.target_gsd)
        change_mask = resolution_matched_augment(mask, source_gsd=0.5, target_gsd=self.target_gsd)
        change_mask = (change_mask > 0.5).astype(np.uint8)

        t1 = domain_adapt(t1)
        t2 = domain_adapt(t2)

        h, w = t1.shape[1], t1.shape[2]
        qa_t1 = np.ones((h, w), dtype=np.uint8)
        qa_t2 = np.ones((h, w), dtype=np.uint8)
        sar_t1, sar_t2 = None, None

        # LEVIR-CD+ changes represent building construction
        type_label = 1 if np.sum(change_mask) > 0 else 0  # 1 = construction
        morph_label = 1 if np.sum(change_mask) > 0 else 0  # 1 = appearance

        return t1, t2, qa_t1, qa_t2, sar_t1, sar_t2, change_mask, morph_label, type_label
