"""
Integration Sanity Test Suite for Member 3 Change Detection Engine.
Validates real-world STAC flavours, QA mask encodings (bit-flags & SCL),
COG validation, and repository gitignore guarantees.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path
import numpy as np

from change_detection.io_utils import (
    parse_stac_item,
    decode_qa_mask,
    write_cog,
    read_cog,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "real"


class TestIntegrationSanity(unittest.TestCase):

    # =========================================================================
    # CHECK 1: STAC PARSER ROBUSTNESS
    # =========================================================================
    def test_stac_aws_s2(self):
        """Verify AWS Sentinel-2 STAC flavor (properties.platform)."""
        fixture_path = FIXTURES_DIR / "fixture_aws_s2.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        parsed = parse_stac_item(data)

        self.assertIn(parsed["platform"], ("sentinel-2a", "sentinel-2b", "landsat-8"))
        self.assertEqual(parsed["crs"], "EPSG:32644")
        self.assertIsNotNone(parsed["datetime"])

    def test_stac_eo_ext(self):
        """Verify EO extension STAC flavor (eo:platform)."""
        fixture_path = FIXTURES_DIR / "fixture_eo_ext.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        parsed = parse_stac_item(data)

        self.assertIn(parsed["platform"], ("sentinel-2a", "sentinel-2b", "landsat-8"))
        self.assertEqual(parsed["crs"], "EPSG:32644")
        self.assertIsNotNone(parsed["datetime"])

    def test_stac_landsat(self):
        """Verify Landsat Collection 2 STAC flavor."""
        fixture_path = FIXTURES_DIR / "fixture_landsat.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        parsed = parse_stac_item(data)

        self.assertIn(parsed["platform"], ("sentinel-2a", "sentinel-2b", "landsat-8"))
        self.assertEqual(parsed["crs"], "EPSG:32644")
        self.assertIsNotNone(parsed["datetime"])

    # =========================================================================
    # CHECK 2: QA MASK ENCODING DETECTION
    # =========================================================================
    def test_qa_bitflags(self):
        """Verify custom 8-bit flag QA decoding."""
        qa_path = FIXTURES_DIR / "qa_bitflags.tif"
        a = decode_qa_mask(qa_path)

        self.assertTrue(a["cloud"][10, 10])
        self.assertTrue(a["cloud_shadow"][20, 20])
        self.assertTrue(a["usable"][0, 0])
        self.assertFalse(a["cloud"][0, 0])

    def test_qa_mask_scl_auto_detect(self):
        """Verify Sentinel-2 SCL (Scene Classification Layer) auto-detection."""
        qa_path = FIXTURES_DIR / "qa_scl.tif"
        decoded = decode_qa_mask(str(qa_path))

        self.assertTrue(decoded["cloud"][10, 10], "SCL 8 must be decoded as cloud")
        self.assertTrue(decoded["cloud_shadow"][20, 20], "SCL 3 must be decoded as cloud_shadow")
        self.assertTrue(decoded["water"][28, 28], "SCL 6 must be decoded as water")
        self.assertTrue(decoded["usable"][0, 0], "SCL 4 (vegetation) must be decoded as usable")
        self.assertFalse(decoded["cloud"][0, 0], "SCL 4 must not be decoded as cloud")

    # =========================================================================
    # CHECK 3: COG OUTPUT VALIDITY
    # =========================================================================
    def test_cog_validation_and_roundtrip(self):
        """Verify write_cog produces valid COG and roundtrips through read_cog."""
        np.random.seed(42)
        arr = (np.random.rand(1024, 1024) > 0.5).astype(np.uint8)
        cog_path = FIXTURES_DIR / "_cog_check.tif"

        write_cog(
            str(cog_path),
            arr,
            {
                "crs": "EPSG:4326",
                "transform": (77.0, 0.0001, 0.0, 13.0, 0.0, -0.0001)
            }
        )

        # Step 2: Validate with rio-cogeo if installed
        try:
            from rio_cogeo.cogeo import cog_validate
            is_valid, errors, warnings = cog_validate(str(cog_path), strict=True)
            print("cog_validate is_valid:", is_valid)
            print("errors:", errors)
            print("warnings:", warnings)
            self.assertTrue(is_valid, f"COG validation failed: {errors}")
        except ImportError:
            print("[WARN] rio-cogeo not installed, skipping strict cog_validate.")

        # Step 3: Roundtrip with read_cog
        arr2, profile = read_cog(str(cog_path))
        # Account for potential channel dimension (1, H, W) vs (H, W)
        shape_matches = (arr2.shape == arr.shape) or (arr2.shape == (1, arr.shape[0], arr.shape[1]))
        self.assertTrue(shape_matches, f"Shape mismatch: {arr2.shape} vs {arr.shape}")
        self.assertIsNotNone(profile.get("crs") or profile.get("crs_str"))

    # =========================================================================
    # CHECK 4: GITIGNORE CORRECTNESS
    # =========================================================================
    def test_gitignore_manifest_preserved(self):
        """
        Verify MANIFEST.sha256 is NOT actually ignored by git.

        `git check-ignore -v <file>` exit codes:
            1   = no matching ignore rule  → file is NOT ignored (GOOD)
            0   = a rule matched
                   - if the rule line starts with '!' → NEGATION 
                     (file is un-ignored)         → GOOD
                   - otherwise                      → file IS ignored (BAD)
            128 = git error
        """
        import subprocess
        from pathlib import Path

        manifest = Path("change_detection/weights/MANIFEST.sha256")
        if not manifest.exists():
            self.skipTest("MANIFEST.sha256 not present")

        res = subprocess.run(
            ["git", "check-ignore", "-v", str(manifest)],
            capture_output=True, text=True,
        )

        if res.returncode == 1:
            return  # no matching rule → not ignored → GOOD

        if res.returncode == 0:
            # stdout format: "<.gitignore-path>:<line>:<pattern>\t<file>"
            # If the pattern begins with '!', the file is un-ignored → GOOD.
            line = res.stdout.strip().split("\t")[0]
            pattern = line.rsplit(":", 1)[-1].strip()
            if pattern.startswith("!"):
                return  # negated → not ignored → GOOD

        self.fail(f"MANIFEST.sha256 IS ignored by git: {res.stdout}")


if __name__ == "__main__":
    unittest.main()
