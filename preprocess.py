"""
SatQuery-AI Module 1: image preprocessing.

This script only prepares images for later modules.
It does not use machine learning, RemoteCLIP, or FAISS.
"""

from pathlib import Path
import csv

import numpy as np
from PIL import Image
import rasterio


# Folders used by this module
RAW_DIR = Path("raw_data")
TILE_DIR = Path("processed_data") / "tiles"
META_DIR = Path("processed_data") / "metadata"
METADATA_CSV = META_DIR / "metadata.csv"

# Each saved tile is a full 256 x 256 square
TILE_SIZE = 256

# File types we accept from raw_data/
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def list_input_images(folder):
    """Return a sorted list of supported image files in folder."""
    images = []
    if not folder.exists():
        return images

    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(path)
    return images


def scale_to_uint8(array):
    """Turn pixel values into 0-255 so tiles can be saved as normal images."""
    array = np.nan_to_num(array, nan=0.0)

    if array.dtype == np.uint8:
        return array

    array = array.astype(np.float32)
    min_val = float(array.min())
    max_val = float(array.max())

    # Empty / constant data cannot be stretched
    if max_val <= min_val:
        return np.zeros(array.shape, dtype=np.uint8)

    scaled = (array - min_val) / (max_val - min_val) * 255.0
    return np.clip(scaled, 0, 255).astype(np.uint8)


def rasterio_to_rgb(path):
    """
    Read a TIFF with Rasterio and convert it to an RGB numpy array.

    GeoTIFF files often have extra bands or 16-bit values.
    We keep this conversion simple:
    - 1 band  -> copy it into R, G, and B
    - 3+ bands -> use the first 3 bands as R, G, B
    """
    with rasterio.open(path) as src:
        data = src.read()  # shape: (bands, height, width)

    if data.ndim != 3 or data.shape[0] < 1:
        raise ValueError(f"Could not read image bands from {path.name}")

    if data.shape[0] == 1:
        rgb = np.stack([data[0], data[0], data[0]], axis=-1)
    else:
        # (bands, H, W) -> (H, W, 3)
        rgb = np.transpose(data[:3], (1, 2, 0))

    return scale_to_uint8(rgb)


def pillow_to_rgb(path):
    """Read PNG / JPG images with Pillow and convert them to RGB."""
    with Image.open(path) as img:
        rgb_img = img.convert("RGB")
        return np.array(rgb_img)


def load_image_as_rgb(path):
    """
    Load one image as an RGB numpy array.

    TIFF / TIF files are read with Rasterio when possible.
    Other formats are read with Pillow.
    """
    suffix = path.suffix.lower()
    if suffix in {".tif", ".tiff"}:
        try:
            return rasterio_to_rgb(path)
        except Exception as error:
            # If Rasterio cannot open it, try Pillow as a backup.
            print(f"Rasterio could not read {path.name} ({error}). Trying Pillow...")
            return pillow_to_rgb(path)

    return pillow_to_rgb(path)


def is_blank_tile(tile):
    """
    Return True if a tile has no useful pixels.

    A tile is treated as blank/empty when:
    - every pixel is 0 (all black), or
    - every pixel is 255 (all white), or
    - every pixel has the same value (no visible detail).
    """
    if tile.size == 0:
        return True

    min_val = int(tile.min())
    max_val = int(tile.max())

    if min_val == max_val:
        return True

    return False


def save_tile(tile, tile_path):
    """Save one RGB tile as a PNG file."""
    Image.fromarray(tile, mode="RGB").save(tile_path)


def write_metadata(rows):
    """Write tile information to processed_data/metadata/metadata.csv."""
    META_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = ["tile_id", "source_image", "tile_x", "tile_y", "width", "height"]
    with METADATA_CSV.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def process_images():
    """Cut every input image into 256x256 tiles and save the valid ones."""
    TILE_DIR.mkdir(parents=True, exist_ok=True)

    image_paths = list_input_images(RAW_DIR)
    metadata_rows = []
    tiles_generated = 0
    tiles_rejected = 0

    for image_path in image_paths:
        print(f"Processing {image_path.name}...")
        rgb = load_image_as_rgb(image_path)

        height, width = rgb.shape[0], rgb.shape[1]

        # Walk across the image in 256-pixel steps.
        # Incomplete right / bottom edges are ignored on purpose.
        for tile_y in range(0, height - TILE_SIZE + 1, TILE_SIZE):
            for tile_x in range(0, width - TILE_SIZE + 1, TILE_SIZE):
                tile = rgb[tile_y:tile_y + TILE_SIZE, tile_x:tile_x + TILE_SIZE]

                # Skip tiles that are completely empty or have no detail.
                if is_blank_tile(tile):
                    tiles_rejected += 1
                    continue

                tile_id = f"{image_path.stem}_x{tile_x}_y{tile_y}"
                tile_filename = f"{tile_id}.png"
                save_tile(tile, TILE_DIR / tile_filename)

                metadata_rows.append(
                    {
                        "tile_id": tile_id,
                        "source_image": image_path.name,
                        "tile_x": tile_x,
                        "tile_y": tile_y,
                        "width": TILE_SIZE,
                        "height": TILE_SIZE,
                    }
                )
                tiles_generated += 1

    write_metadata(metadata_rows)

    print("\nPreprocessing finished.")
    print(f"Number of input images: {len(image_paths)}")
    print(f"Number of tiles generated: {tiles_generated}")
    print(f"Number of rejected tiles: {tiles_rejected}")


if __name__ == "__main__":
    process_images()
