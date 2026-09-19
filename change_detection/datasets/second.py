"""
Dataset loader for SECOND (Semantic Change Detection dataset, multi-class change).
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

from .adapters import domain_adapt


class SECONDDataset(Dataset):
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
            im1_dir = self.root_dir / split / "im1"
            if im1_dir.is_dir():
                self.samples = sorted([p.name for p in im1_dir.glob("*.png")])

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
        im1 = np.array(Image.open(split_dir / "im1" / name)).transpose(2, 0, 1)
        im2 = np.array(Image.open(split_dir / "im2" / name)).transpose(2, 0, 1)
        lbl1_path = split_dir / "label1" / name
        lbl2_path = split_dir / "label2" / name
        lbl1 = np.array(Image.open(lbl1_path)) if lbl1_path.exists() else np.zeros(im1.shape[1:], dtype=np.uint8)
        lbl2 = np.array(Image.open(lbl2_path)) if lbl2_path.exists() else np.zeros(im2.shape[1:], dtype=np.uint8)

        # Non-zero differences indicate change
        change_mask = (lbl1 != lbl2).astype(np.uint8)
        t1 = domain_adapt(im1)
        t2 = domain_adapt(im2)

        h, w = t1.shape[1], t1.shape[2]
        qa_t1 = np.ones((h, w), dtype=np.uint8)
        qa_t2 = np.ones((h, w), dtype=np.uint8)

        # Determine type & morphology
        type_label = 2 if np.any(lbl2 == 5) else 1  # 2: clearance/water, 1: construction
        morph_label = 1 if np.sum(change_mask) > 0 else 0

        return t1, t2, qa_t1, qa_t2, None, None, change_mask, morph_label, type_label
