"""
Unit tests for change_detection/train.py.
Testing YAML training config execution, held-out partition isolation,
metrics computation (including explicit False-Positive Rate), and MANIFEST SHA-256 recording.
"""

import unittest
import numpy as np
from pathlib import Path

from change_detection.train import (
    create_held_out_split,
    compute_metrics,
    record_manifest,
    train,
)


class TestTrain(unittest.TestCase):
    def test_create_held_out_split_isolation(self):
        """Verify 20% split is deterministic, disjoint, and written to disk."""
        samples = [f"chip_{i:03d}" for i in range(100)]
        split_path = Path("change_detection/tests/fixtures/test_held_out.txt")
        try:
            train_s, held_out_s = create_held_out_split(
                samples, held_out_ratio=0.20, seed=42, split_file_path=split_path
            )
            self.assertEqual(len(held_out_s), 20)
            self.assertEqual(len(train_s), 80)
            # Ensure disjoint
            self.assertEqual(len(set(train_s).intersection(set(held_out_s))), 0)
            # Ensure saved to disk
            self.assertTrue(split_path.exists())
            saved_lines = split_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(saved_lines, held_out_s)
        finally:
            if split_path.exists():
                split_path.unlink()

    def test_compute_metrics_with_fpr(self):
        """Verify binary change metrics and false positive rate calculation."""
        # 4 pixels: (1, 1) TP, (1, 0) FP, (0, 1) FN, (0, 0) TN
        pred_m = np.array([[[1, 1], [0, 0]]], dtype=np.uint8)
        gt_m = np.array([[[1, 0], [1, 0]]], dtype=np.uint8)
        pred_morph = np.array([0])
        gt_morph = np.array([0])
        pred_type = np.array([1])
        gt_type = np.array([1])

        metrics = compute_metrics(pred_m, gt_m, pred_morph, gt_morph, pred_type, gt_type)

        self.assertIn("val_precision", metrics)
        self.assertIn("val_recall", metrics)
        self.assertIn("val_f1", metrics)
        self.assertIn("val_iou", metrics)
        self.assertIn("val_fpr", metrics)
        self.assertIn("val_morph_acc", metrics)
        self.assertIn("val_type_acc", metrics)

        # TP = 1, FP = 1, FN = 1, TN = 1
        # Precision = 1 / 2 = 0.5
        # Recall = 1 / 2 = 0.5
        # FPR = FP / (FP + TN) = 1 / 2 = 0.5
        self.assertEqual(metrics["val_precision"], 0.5)
        self.assertEqual(metrics["val_recall"], 0.5)
        self.assertEqual(metrics["val_fpr"], 0.5)
        self.assertEqual(metrics["val_morph_acc"], 1.0)
        self.assertEqual(metrics["val_type_acc"], 1.0)

    def test_train_pipeline_execution_and_manifest(self):
        """Verify train() executes config, writes checkpoint, and registers in MANIFEST.sha256."""
        res = train("change_detection/configs/train_levir.yaml")

        self.assertIn("metrics", res)
        self.assertIn("checkpoint", res)
        self.assertIn("sha256", res)
        self.assertEqual(len(res["sha256"]), 64)

        # Verify checkpoint exists
        ckpt = Path(res["checkpoint"])
        self.assertTrue(ckpt.exists())

        # Verify manifest entry exists
        manifest_path = Path("change_detection/weights/MANIFEST.sha256")
        self.assertTrue(manifest_path.exists())
        manifest_text = manifest_path.read_text(encoding="utf-8")
        self.assertIn(res["sha256"], manifest_text)


if __name__ == "__main__":
    unittest.main()
