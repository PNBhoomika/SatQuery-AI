"""
Tests for 5-stage false-alarm suppression pipeline.
"""
import unittest
import numpy as np
from change_detection.suppress import FalseAlarmSuppressor


class TestSuppression(unittest.TestCase):
    def test_suppression_cloud_pixel(self):
        suppressor = FalseAlarmSuppressor()
        raw_prob = np.ones((10, 10), dtype=np.float32)
        # Optical QA with cloud in upper left
        qa_t1 = {"usable": np.ones((10, 10), dtype=bool)}
        qa_t2 = {"usable": np.ones((10, 10), dtype=bool)}
        qa_t2["usable"][0:3, 0:3] = False  # Cloud contaminated

        mask, conf, stages, debug = suppressor.suppress(
            raw_change_prob=raw_prob,
            qa_decoded_t1=qa_t1,
            qa_decoded_t2=qa_t2,
            registration_offset=(0.0, 0.0),
            registration_conf=1.0,
            seasonal_delta=0.0
        )

        # Contaminated pixels must be suppressed to 0
        self.assertTrue(np.all(mask[0:3, 0:3] == 0))
        self.assertIn("qa", stages)
        self.assertIn("confidence", stages)


if __name__ == "__main__":
    unittest.main()
