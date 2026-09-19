"""
Unit tests for change detection dataset loaders.
Verifies uniform return contract across:
  - LevirCDDataset (0.5m high-res optical PNGs)
  - S2LookingDataset (side-looking bi-temporal PNGs)
  - OSCDDataset (Sentinel-2 multi-band GeoTIFFs)
  - SECONDDataset (semantic change detection pairs)
  - Sen1Floods11Dataset (optical + Sentinel-1 SAR flood extent)
"""

import unittest
import numpy as np

from change_detection.datasets.levir_cd import LevirCDDataset
from change_detection.datasets.s2looking import S2LookingDataset
from change_detection.datasets.oscd import OSCDDataset
from change_detection.datasets.second import SECONDDataset
from change_detection.datasets.sen1floods11 import Sen1Floods11Dataset


class TestDatasetLoaders(unittest.TestCase):
    def _assert_uniform_contract(self, sample, dataset_name):
        self.assertEqual(len(sample), 9, f"{dataset_name} must return exactly 9 items")
        t1, t2, qa_t1, qa_t2, sar_t1, sar_t2, change_mask, morph_label, type_label = sample

        self.assertIsInstance(t1, np.ndarray, f"{dataset_name}: t1 must be np.ndarray")
        self.assertIsInstance(t2, np.ndarray, f"{dataset_name}: t2 must be np.ndarray")
        self.assertIsInstance(qa_t1, np.ndarray, f"{dataset_name}: qa_t1 must be np.ndarray")
        self.assertIsInstance(qa_t2, np.ndarray, f"{dataset_name}: qa_t2 must be np.ndarray")
        self.assertIsInstance(change_mask, np.ndarray, f"{dataset_name}: change_mask must be np.ndarray")
        self.assertIsInstance(morph_label, int, f"{dataset_name}: morph_label must be int")
        self.assertIsInstance(type_label, int, f"{dataset_name}: type_label must be int")

        self.assertEqual(t1.ndim, 3, f"{dataset_name}: t1 must have shape (C, H, W)")
        self.assertEqual(t2.ndim, 3, f"{dataset_name}: t2 must have shape (C, H, W)")
        self.assertEqual(change_mask.ndim, 2, f"{dataset_name}: change_mask must have shape (H, W)")

    def test_levir_cd_loader(self):
        ds = LevirCDDataset(root_dir="data/raw/levir_cd", split="train")
        sample = ds[0]
        self._assert_uniform_contract(sample, "LevirCDDataset")

    def test_s2looking_loader(self):
        ds = S2LookingDataset(root_dir="data/raw/s2looking", split="train")
        sample = ds[0]
        self._assert_uniform_contract(sample, "S2LookingDataset")

    def test_oscd_loader(self):
        ds = OSCDDataset(root_dir="data/raw/oscd", split="train")
        sample = ds[0]
        self._assert_uniform_contract(sample, "OSCDDataset")

    def test_second_loader(self):
        ds = SECONDDataset(root_dir="data/raw/second", split="train")
        sample = ds[0]
        self._assert_uniform_contract(sample, "SECONDDataset")

    def test_sen1floods11_loader(self):
        ds = Sen1Floods11Dataset(root_dir="data/raw/sen1floods11", split="train")
        sample = ds[0]
        self._assert_uniform_contract(sample, "Sen1Floods11Dataset")
        # Sen1Floods11 explicitly yields SAR channels
        sar_t1, sar_t2 = sample[4], sample[5]
        self.assertIsNotNone(sar_t1)
        self.assertIsNotNone(sar_t2)
        self.assertEqual(sar_t1.shape[0], 2)


if __name__ == "__main__":
    unittest.main()
