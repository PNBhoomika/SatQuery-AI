"""
Tests for sub-pixel co-registration.
"""
import unittest
import numpy as np
from change_detection.registration import register_bitemporal_chips


class TestRegistration(unittest.TestCase):
    def test_registration_zero_shift(self):
        t1 = np.ones((3, 64, 64), dtype=np.float32)
        t2 = np.ones((3, 64, 64), dtype=np.float32)
        aligned, (dx, dy), conf = register_bitemporal_chips(t1, t2)
        self.assertLess(abs(dx), 0.1)
        self.assertLess(abs(dy), 0.1)
        self.assertGreaterEqual(conf, 0.0)


if __name__ == "__main__":
    unittest.main()
