"""
Tests for earliest date logic.
"""
import unittest
from change_detection.earliest_date import find_earliest_supported_date


class TestEarliestDate(unittest.TestCase):
    def test_earliest_date_monotonic(self):
        stack = [
            {"tile_path": "t1.tif", "date": "2023-01-01T00:00:00Z", "qa_mask_path": "q1.tif"},
            {"tile_path": "t2.tif", "date": "2023-06-01T00:00:00Z", "qa_mask_path": "q2.tif"},
            {"tile_path": "t3.tif", "date": "2024-01-01T00:00:00Z", "qa_mask_path": "q3.tif"},
        ]

        def mock_detect(item1, item2):
            # Change only triggers at t3
            conf = 0.95 if item2["date"] == "2024-01-01T00:00:00Z" else 0.10
            return {"confidence": conf, "debug": {"qa_coverage": 1.0}}

        res = find_earliest_supported_date(stack, mock_detect)
        self.assertEqual(res["earliest_supported_date"], "2024-01-01T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
