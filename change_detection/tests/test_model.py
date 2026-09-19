"""
Unit tests for change_detection/model.py.
Testing Siamese architecture, ConvNeXt-T and Prithvi backbones, 3 heads,
seed determinism, and SHA-256 hash loading.
"""

import os
import unittest
import numpy as np
from pathlib import Path

from change_detection.model import (
    set_seed,
    compute_sha256,
    load_model,
    ModelBundle,
    MORPHOLOGY_CLASSES,
    TYPE_CLASSES,
    HAS_TORCH,
)


class TestModel(unittest.TestCase):
    def setUp(self):
        set_seed(42)

    def test_vocabularies(self):
        """Verify canonical class vocabularies per PS §2.2.2."""
        self.assertEqual(len(MORPHOLOGY_CLASSES), 5)
        self.assertEqual(MORPHOLOGY_CLASSES, ["appearance", "disappearance", "expansion", "contraction", "none"])
        self.assertEqual(len(TYPE_CLASSES), 5)
        self.assertEqual(TYPE_CLASSES, ["construction", "clearance", "water_extent", "road", "unknown"])

    def test_seed_determinism(self):
        """Verify set_seed produces reproducible numpy random draws and CUBLAS setting."""
        set_seed(123)
        r1 = np.random.rand(5)
        set_seed(123)
        r2 = np.random.rand(5)
        np.testing.assert_allclose(r1, r2)
        self.assertEqual(os.environ.get("CUBLAS_WORKSPACE_CONFIG"), ":4096:8")

    def test_compute_sha256(self):
        """Verify compute_sha256 outputs valid 64-char hexadecimal hash."""
        test_file = Path("change_detection/tests/fixtures/sha_test.bin")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_bytes(b"SatQueryAI_SIH2026_Member3")
        try:
            h = compute_sha256(test_file)
            self.assertEqual(len(h), 64)
            # Known SHA-256 for b"SatQueryAI_SIH2026_Member3"
            import hashlib
            expected = hashlib.sha256(b"SatQueryAI_SIH2026_Member3").hexdigest()
            self.assertEqual(h, expected)
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_load_model_fallback_and_bundle(self):
        """Verify load_model returns valid ModelBundle with convnext_tiny and prithvi_100m."""
        bundle_conv = load_model(backbone="convnext_tiny")
        self.assertIsInstance(bundle_conv, ModelBundle)
        self.assertIn("convnext_tiny", bundle_conv.model_name)
        self.assertEqual(bundle_conv.device, "cpu")

        bundle_prithvi = load_model(backbone="prithvi_100m")
        self.assertIsInstance(bundle_prithvi, ModelBundle)
        self.assertIn("prithvi_100m", bundle_prithvi.model_name)

    def test_model_forward_shapes(self):
        """Verify model forward pass outputs (change_logits, morph_logits, type_logits)."""
        bundle = load_model(backbone="convnext_tiny")
        if HAS_TORCH:
            import torch
            t1 = torch.zeros(1, 3, 64, 64)
            t2 = torch.zeros(1, 3, 64, 64)
            change_logit, morph_logit, type_logit = bundle.model(t1, t2)
            self.assertEqual(change_logit.shape, (1, 1, 64, 64))
            self.assertEqual(morph_logit.shape, (1, 5))
            self.assertEqual(type_logit.shape, (1, 5))
        else:
            t1 = np.zeros((1, 3, 64, 64), dtype=np.float32)
            t2 = np.zeros((1, 3, 64, 64), dtype=np.float32)
            change_logit, morph_logit, type_logit = bundle.model(t1, t2)
            self.assertEqual(len(morph_logit), 5)
            self.assertEqual(len(type_logit), 5)


if __name__ == "__main__":
    unittest.main()
