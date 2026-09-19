import unittest
from pathlib import Path
from PIL import Image


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


if __name__ == "__main__":
    unittest.main()
    