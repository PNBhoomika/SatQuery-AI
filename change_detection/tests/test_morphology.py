"""
Tests for morphology classification.
"""
import unittest
import numpy as np
from change_detection.classify_change import classify_change_morphology_rule_based


class TestMorphology(unittest.TestCase):
    def test_morphology_appearance(self):
        t1 = np.zeros((20, 20), dtype=bool)
        t2 = np.zeros((20, 20), dtype=bool)
        t2[5:15, 5:15] = True
        mask = (t2 != t1).astype(np.uint8)

        morph = classify_change_morphology_rule_based(t1, t2, mask)
        self.assertIn(morph, ["appearance", "expansion"])


if __name__ == "__main__":
    unittest.main()
