import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import Affine, from_origin

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from preprocess import UNAVAILABLE, process_images


class TestPreprocessedTiles(unittest.TestCase):

    def test_sample_tiles_exist(self):
        tile_folder = Path("sample_output/tiles")
        tiles = list(tile_folder.glob("*.png"))

        self.assertGreater(len(tiles), 0)

    def test_tile_size(self):
        tile_folder = Path("sample_output/tiles")
        tiles = list(tile_folder.glob("*.png"))

        for tile in tiles:
            with Image.open(tile) as img:
                self.assertEqual(img.size, (256, 256))


class TestGeoTIFFPreprocess(unittest.TestCase):
    """Simple geospatial checks for Module 1 GeoTIFF tiles."""

    def test_geotiff_tile_crs_transform_and_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_dir = tmp_path / "raw_data"
            tile_dir = tmp_path / "processed_data" / "tiles"
            metadata_csv = tmp_path / "processed_data" / "metadata" / "metadata.csv"
            raw_dir.mkdir()

            # Build a small georeferenced raster: 512x512, 3 bands, EPSG:4326.
            # Pixel values vary so the tiles are not rejected as blank.
            height, width, bands = 512, 512, 3
            transform = from_origin(100.0, 20.0, 0.01, 0.01)
            # A simple x-direction ramp so tiles are not blank/constant.
            ramp = np.arange(width, dtype=np.uint8)
            data = np.zeros((bands, height, width), dtype=np.uint8)
            data[:] = ramp[None, None, :]

            source_path = raw_dir / "geo_sample.tif"
            with rasterio.open(
                source_path,
                "w",
                driver="GTiff",
                height=height,
                width=width,
                count=bands,
                dtype="uint8",
                crs="EPSG:4326",
                transform=transform,
            ) as dst:
                dst.write(data)

            generated, rejected, n_images = process_images(
                raw_dir=raw_dir,
                tile_dir=tile_dir,
                metadata_csv=metadata_csv,
            )

            self.assertEqual(n_images, 1)
            self.assertEqual(generated, 4)
            self.assertEqual(rejected, 0)

            tiles = list(tile_dir.glob("*.tif"))
            self.assertGreater(len(tiles), 0)

            with rasterio.open(tiles[0]) as src:
                self.assertIsNotNone(src.crs)
                self.assertEqual(src.crs.to_string(), "EPSG:4326")
                self.assertFalse(src.transform.is_identity)
                self.assertNotEqual(src.transform, Affine.identity())
                self.assertEqual(src.width, 256)
                self.assertEqual(src.height, 256)
                self.assertEqual(src.count, bands)
                loaded = src.read()
                self.assertEqual(loaded.shape, (bands, 256, 256))

            self.assertTrue(metadata_csv.exists())
            text = metadata_csv.read_text(encoding="utf-8")
            self.assertIn("crs", text)
            self.assertIn("EPSG:4326", text)
            self.assertNotIn(UNAVAILABLE, text.splitlines()[1])

    def test_png_metadata_is_not_georeferenced(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_dir = tmp_path / "raw_data"
            tile_dir = tmp_path / "processed_data" / "tiles"
            metadata_csv = tmp_path / "processed_data" / "metadata" / "metadata.csv"
            raw_dir.mkdir()

            png_path = raw_dir / "plain.png"
            pixels = np.zeros((256, 256, 3), dtype=np.uint8)
            pixels[0, 0] = [10, 20, 30]
            Image.fromarray(pixels, mode="RGB").save(png_path)

            process_images(
                raw_dir=raw_dir,
                tile_dir=tile_dir,
                metadata_csv=metadata_csv,
            )

            png_tiles = list(tile_dir.glob("*.png"))
            tif_tiles = list(tile_dir.glob("*.tif"))
            self.assertEqual(len(png_tiles), 1)
            self.assertEqual(len(tif_tiles), 0)

            rows = metadata_csv.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreater(len(rows), 1)
            values = rows[1].split(",")
            self.assertIn(UNAVAILABLE, values)


if __name__ == "__main__":
    unittest.main()
