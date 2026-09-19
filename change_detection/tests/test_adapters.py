"""
Unit tests for change_detection/datasets/adapters.py.
Testing resolution matching (downsampling LEVIR 0.5m -> 10m, upsampling Landsat 30m -> 10m),
domain adaptation (histogram matching, standardization), and class-balanced sampling.
"""

import unittest
import numpy as np

from change_detection.datasets.adapters import (
    resolution_matched_augment,
    histogram_match,
    domain_adapt,
    class_balanced_sampler,
)


class TestAdapters(unittest.TestCase):
    def test_resolution_matched_downsample_levir(self):
        """Downsample 0.5m LEVIR chip to 10m Sentinel-2 GSD (factor 0.05)."""
        # Input 200x200 at 0.5m represents 100m ground width
        # At 10m target GSD, 100m should be ~10x10 pixels
        img = np.ones((3, 200, 200), dtype=np.float32)
        resampled = resolution_matched_augment(img, source_gsd=0.5, target_gsd=10.0)
        self.assertEqual(resampled.shape[0], 3)
        self.assertEqual(resampled.shape[1], 10)
        self.assertEqual(resampled.shape[2], 10)

    def test_resolution_matched_upsample_landsat(self):
        """Upsample 30m Landsat chip to 10m Sentinel-2 GSD (factor 3.0)."""
        # Input 10x10 at 30m represents 300m ground width
        # At 10m target GSD, 300m should be ~30x30 pixels
        img = np.ones((3, 10, 10), dtype=np.float32)
        resampled = resolution_matched_augment(img, source_gsd=30.0, target_gsd=10.0)
        self.assertEqual(resampled.shape[0], 3)
        self.assertEqual(resampled.shape[1], 30)
        self.assertEqual(resampled.shape[2], 30)

    def test_resolution_matched_random_resample(self):
        """Verify random resampling applies scale jitter within expected envelope."""
        img = np.ones((3, 100, 100), dtype=np.float32)
        resampled = resolution_matched_augment(
            img, source_gsd=10.0, target_gsd=10.0, random_resample=True
        )
        self.assertGreaterEqual(resampled.shape[1], 80)
        self.assertLessEqual(resampled.shape[1], 120)

    def test_domain_adapt_standardization(self):
        """Standardize reflectance to Sentinel-2 target range [0.0, 1.0]."""
        raw_tile = np.random.uniform(500.0, 3000.0, size=(3, 32, 32)).astype(np.float32)
        adapted = domain_adapt(raw_tile, method="standardization")
        self.assertGreaterEqual(float(np.min(adapted)), 0.0)
        self.assertLessEqual(float(np.max(adapted)), 1.0)
        # Expected Sentinel-2 mean around 0.15 (+/- 0.05)
        self.assertAlmostEqual(float(np.mean(adapted)), 0.15, delta=0.08)

    def test_domain_adapt_histogram_matching(self):
        """Verify CDF histogram matching aligns distribution toward reference."""
        source = np.ones((3, 32, 32), dtype=np.float32) * 50.0
        reference = np.ones((3, 32, 32), dtype=np.float32) * 200.0
        matched = histogram_match(source, reference)
        self.assertEqual(matched.shape, source.shape)
        np.testing.assert_allclose(matched, reference)

    def test_class_balanced_sampler(self):
        """Verify inverse frequency weighting weights rare classes more heavily."""
        # 10 samples: 8 of class 0, 1 of class 1, 1 of class 2
        labels = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2]
        weights = class_balanced_sampler(labels, num_classes=5)
        self.assertEqual(len(weights), 10)
        self.assertAlmostEqual(float(np.sum(weights)), 1.0, places=5)
        # Rare class 1 should have higher weight than common class 0
        self.assertGreater(weights[8], weights[0])
        self.assertAlmostEqual(weights[8], weights[9])


if __name__ == "__main__":
    unittest.main()
