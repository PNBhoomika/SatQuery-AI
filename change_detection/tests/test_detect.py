"""
Tests for public detect_change API.
"""
import unittest
import numpy as np
from change_detection.detect import detect_change


class TestDetect(unittest.TestCase):
    def test_detect_change_synthetic(self):
        h, w = 32, 32
        t1 = np.zeros((3, h, w), dtype=np.uint8)
        t2 = np.zeros((3, h, w), dtype=np.uint8)
        # Add synthetic change rectangle
        t2[:, 10:20, 10:20] = 200
        qa1 = np.ones((h, w), dtype=np.uint8)
        qa2 = np.ones((h, w), dtype=np.uint8)

        result = detect_change(
            tile_t1=t1,
            tile_t2=t2,
            qa_mask_t1=qa1,
            qa_mask_t2=qa2
        )

        self.assertIn("change_mask", result)
        self.assertIn("confidence", result)
        self.assertIn("change_type", result)
        self.assertIn("change_morphology", result)
        self.assertIn("provenance", result)
        self.assertFalse(result["provenance"]["sar_fused"])

        # Deliverable 6: Assert change_mask matches within IoU > 0.8 and morph == appearance
        from change_detection.io_utils import read_cog
        mask, _ = read_cog(result["change_mask"])
        gt_mask = np.zeros((h, w), dtype=np.uint8)
        gt_mask[10:20, 10:20] = 1

        intersection = np.logical_and(mask > 0, gt_mask > 0).sum()
        union = np.logical_or(mask > 0, gt_mask > 0).sum()
        iou = intersection / union if union > 0 else 0.0

        self.assertGreater(iou, 0.8, f"Expected IoU > 0.8, got {iou}")
        self.assertEqual(result["change_morphology"], "appearance")


if __name__ == "__main__":
    unittest.main()
