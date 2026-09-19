"""
Tests for active learning feedback loop.
"""
import unittest
import tempfile
from pathlib import Path
from change_detection.feedback import update_from_feedback


class TestFeedback(unittest.TestCase):
    def test_update_from_feedback_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Path(tmpdir) / "feedback.jsonl"
            labels = [
                {
                    "change_event_id": f"ce_{i}",
                    "decision": "confirm" if i % 2 == 0 else "reject",
                    "analyst_id": "analyst_01",
                    "timestamp": "2024-03-15T12:00:00Z"
                }
                for i in range(25)
            ]

            res = update_from_feedback(labels, feedback_store_path=store, retrain_threshold=20)
            self.assertEqual(res["n_labels_used"], 25)
            self.assertIsNotNone(res["new_checkpoint"])
            self.assertGreaterEqual(res["val_f1_after"], res["val_f1_before"])


if __name__ == "__main__":
    unittest.main()
