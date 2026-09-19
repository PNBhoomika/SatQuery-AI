"""
Unit tests for io_utils.py, schema validation, and contract parsing.
Phase 1 verification.
"""

import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

from change_detection.io_utils import (
    read_cog,
    write_cog,
    decode_qa_mask,
    parse_stac_item,
    QA_BIT_VALID_DATA,
    QA_BIT_CLOUD,
    QA_BIT_CLOUD_SHADOW,
    QA_BIT_SNOW,
    QA_BIT_HAZE,
    QA_BIT_WATER,
    QA_BIT_SATURATED,
    QA_BIT_CIRRUS,
)


class TestIOUtils(unittest.TestCase):

    def test_decode_qa_mask_bits(self):
        """Verify exact decoding of all 8 QA bit flags mandated by PS §2.2.3."""
        h, w = 4, 4
        mask = np.zeros((h, w), dtype=np.uint8)

        # Set individual pixels with distinct flags
        mask[0, 0] = QA_BIT_VALID_DATA                               # 1: clear valid pixel
        mask[0, 1] = QA_BIT_VALID_DATA | QA_BIT_CLOUD               # 1 + 2: cloud
        mask[0, 2] = QA_BIT_VALID_DATA | QA_BIT_CLOUD_SHADOW        # 1 + 4: shadow
        mask[0, 3] = QA_BIT_VALID_DATA | QA_BIT_SNOW                # 1 + 8: snow
        mask[1, 0] = QA_BIT_VALID_DATA | QA_BIT_HAZE                # 1 + 16: haze
        mask[1, 1] = QA_BIT_VALID_DATA | QA_BIT_WATER               # 1 + 32: water
        mask[1, 2] = QA_BIT_VALID_DATA | QA_BIT_SATURATED           # 1 + 64: saturated
        mask[1, 3] = QA_BIT_VALID_DATA | QA_BIT_CIRRUS              # 1 + 128: cirrus
        mask[2, 0] = 0                                               # 0: no-data fill

        decoded = decode_qa_mask(mask)

        self.assertTrue(decoded["valid_data"][0, 0])
        self.assertTrue(decoded["cloud"][0, 1])
        self.assertTrue(decoded["cloud_shadow"][0, 2])
        self.assertTrue(decoded["snow"][0, 3])
        self.assertTrue(decoded["haze"][1, 0])
        self.assertTrue(decoded["water"][1, 1])
        self.assertTrue(decoded["saturated"][1, 2])
        self.assertTrue(decoded["cirrus"][1, 3])
        self.assertFalse(decoded["valid_data"][2, 0])

        # Usable test: only pixel [0, 0] is valid and clean; pixel [1, 1] is also clear water
        self.assertTrue(decoded["usable"][0, 0])
        self.assertFalse(decoded["usable"][0, 1])  # cloud
        self.assertFalse(decoded["usable"][0, 2])  # shadow
        self.assertFalse(decoded["usable"][2, 0])  # invalid data

    def test_parse_stac_item(self):
        """Verify STAC item metadata extraction for optical and SAR parameters."""
        sample_stac = {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "S2A_MSIL2A_20240315T053211",
            "bbox": [77.10, 28.50, 77.30, 28.70],
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.1, 28.5], [77.3, 28.5], [77.3, 28.7], [77.1, 28.7], [77.1, 28.5]]]
            },
            "properties": {
                "datetime": "2024-03-15T05:32:11Z",
                "platform": "sentinel-2a",
                "view:incidence_angle": 12.4,
                "view:off_nadir": 5.2,
                "sat:orbit_state": "descending",
                "proj:epsg": 32643
            }
        }

        parsed = parse_stac_item(sample_stac)

        self.assertEqual(parsed["id"], "S2A_MSIL2A_20240315T053211")
        self.assertEqual(parsed["datetime"], "2024-03-15T05:32:11Z")
        self.assertEqual(parsed["platform"], "sentinel-2a")
        self.assertEqual(parsed["incidence_angle"], 12.4)
        self.assertEqual(parsed["view_angle"], 5.2)
        self.assertEqual(parsed["orbit"], "descending")
        self.assertEqual(parsed["crs"], "EPSG:32643")
        self.assertEqual(parsed["bbox"], [77.10, 28.50, 77.30, 28.70])

    def test_write_and_read_cog_roundtrip(self):
        """Verify writing and reading a COG GeoTIFF roundtrips array dimensions and values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "test_tile.tif"
            synthetic_data = (np.random.rand(3, 64, 64) * 255).astype(np.uint8)

            saved_path = write_cog(out_path, synthetic_data)
            self.assertTrue(Path(saved_path).is_file())

            read_arr, prof = read_cog(saved_path)
            self.assertEqual(read_arr.shape, synthetic_data.shape)
            self.assertTrue(np.array_equal(read_arr, synthetic_data))
            self.assertEqual(prof["width"], 64)
            self.assertEqual(prof["height"], 64)

    def test_contracts_schema_validation(self):
        """Verify that contracts/ schemas are syntactically valid Draft 2020-12 schemas."""
        import jsonschema

        contracts_dir = Path("change_detection/contracts")
        schemas = [
            "qa_mask.schema.json",
            "change_event.schema.json",
            "stac_change_event.schema.json",
            "feedback.schema.json",
        ]

        for schema_name in schemas:
            schema_path = contracts_dir / schema_name
            self.assertTrue(schema_path.is_file(), f"Missing schema: {schema_path}")
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_json = json.load(f)
            # Validate schema structure
            jsonschema.Draft202012Validator.check_schema(schema_json)


if __name__ == "__main__":
    unittest.main()
