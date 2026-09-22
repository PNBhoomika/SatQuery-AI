"""
Dataset loader for S2Looking (Building change detection, off-nadir satellite optical pairs).
Uniformly returns (t1, t2, qa_t1, qa_t2, sar_t1, sar_t2, change_mask, morph_label, type_label).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np

try:
    from torch.utils.data import Dataset
except ImportError:
    Dataset = object

from .adapters import resolution_matched_augment, domain_adapt


class S2LookingDataset(Dataset):
    def __init__(
        self,
        root_dir: Union[str, Path],
        split: str = "train",
        target_gsd: float = 10.0,
    ):
        self.root_dir = Path(root_dir)
        self.split = split
        self.target_gsd = target_gsd
        self.samples = []
        if self.root_dir.is_dir():
            split_dir = self.root_dir / split
            image1_dir = split_dir / "Image1"
            if image1_dir.is_dir():
                self.samples = sorted([p.name for p in image1_dir.glob("*.png")])

    def __len__(self) -> int:
        return max(1, len(self.samples))

    def __getitem__(
        self, idx: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray], np.ndarray, int, int]:
        if not self.samples:
            h, w = 128, 128
            return (
                np.zeros((3, h, w), dtype=np.float32),
                np.zeros((3, h, w), dtype=np.float32),
                np.ones((h, w), dtype=np.uint8),
                np.ones((h, w), dtype=np.uint8),
                None,
                None,
                np.zeros((h, w), dtype=np.uint8),
                0,
                0,
            )

        from PIL import Image
        name = self.samples[idx]
        split_dir = self.root_dir / self.split
        img1 = np.array(Image.open(split_dir / "Image1" / name)).transpose(2, 0, 1)
        img2 = np.array(Image.open(split_dir / "Image2" / name)).transpose(2, 0, 1)
        lbl_path = split_dir / "label" / name
        mask = np.array(Image.open(lbl_path)) if lbl_path.exists() else np.zeros(img1.shape[1:], dtype=np.uint8)
        if mask.ndim == 3:
            mask = mask[..., 0]
        mask = (mask > 0).astype(np.uint8)

        t1 = resolution_matched_augment(img1, source_gsd=0.8, target_gsd=self.target_gsd)
        t2 = resolution_matched_augment(img2, source_gsd=0.8, target_gsd=self.target_gsd)
        change_mask = resolution_matched_augment(mask, source_gsd=0.8, target_gsd=self.target_gsd)
        change_mask = (change_mask > 0.5).astype(np.uint8)

        t1 = domain_adapt(t1)
        t2 = domain_adapt(t2)

        h, w = t1.shape[1], t1.shape[2]
        qa_t1 = np.ones((h, w), dtype=np.uint8)
        qa_t2 = np.ones((h, w), dtype=np.uint8)

        type_label = 1 if np.sum(change_mask) > 0 else 0   # 1 = construction
        morph_label = 1 if np.sum(change_mask) > 0 else 0  # 1 = appearance

        return t1, t2, qa_t1, qa_t2, None, None, change_mask, morph_label, type_label
