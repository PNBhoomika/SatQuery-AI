"""
Tests for evaluate.py metrics calculation.
"""
import unittest
from change_detection.evaluate import evaluate_held_out


class TestEvaluate(unittest.TestCase):
    def test_evaluate_held_out_metrics(self):
        res = evaluate_held_out()
        self.assertIn("change_detection", res)
        self.assertGreater(res["change_detection"]["precision"], 0.90)
        self.assertGreater(res["change_detection"]["recall"], 0.85)
        self.assertGreater(res["change_detection"]["f1"], 0.85)
        self.assertIn("morphology", res)
        self.assertIn("type", res)


if __name__ == "__main__":
    unittest.main()
