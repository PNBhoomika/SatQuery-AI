"""
SatQuery-AI Module 1: image preprocessing.

This script only prepares images for later modules.
It does not use machine learning, RemoteCLIP, or FAISS.

PNG / JPG files are saved as 256x256 PNG tiles (not georeferenced).
GeoTIFF / TIFF files are saved as 256x256 GeoTIFF tiles when possible.
"""

from pathlib import Path
import csv

import numpy as np
from PIL import Image
import rasterio
from rasterio.windows import Window
from rasterio.windows import bounds as window_bounds
from rasterio.windows import transform as window_transform


# Folders used by this module
RAW_DIR = Path("raw_data")
TILE_DIR = Path("processed_data") / "tiles"
META_DIR = Path("processed_data") / "metadata"
METADATA_CSV = META_DIR / "metadata.csv"

# Each saved tile is a full 256 x 256 square
TILE_SIZE = 256

# File types we accept from raw_data/
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
TIFF_EXTENSIONS = {".tif", ".tiff"}

# Used in metadata.csv when a file has no real geospatial information
UNAVAILABLE = "unavailable"

METADATA_FIELDS = [
    "tile_id",
    "source_image",
    "tile_x",
    "tile_y",
    "width",
    "height",
    "crs",
    "transform",
    "bbox",
]


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
    """Turn pixel values into 0-255 so PNG/JPG tiles can be saved as normal images."""
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


def pillow_to_rgb(path):
    """Read PNG / JPG images with Pillow and convert them to RGB."""
    with Image.open(path) as img:
        rgb_img = img.convert("RGB")
        return np.array(rgb_img)


def is_blank_tile(tile):
    """
    Return True if a tile has no useful pixels.

    A tile is treated as blank/empty when:
    - it has no pixels, or
    - every pixel is NaN, or
    - every pixel has the same value (all black, all white, or no detail).
    """
    array = np.asarray(tile)
    if array.size == 0:
        return True

    if np.isnan(array).all():
        return True

    min_val = np.nanmin(array)
    max_val = np.nanmax(array)
    return min_val == max_val


def save_png_tile(tile, tile_path):
    """Save one RGB tile as a PNG file (used for PNG/JPG inputs)."""
    Image.fromarray(tile, mode="RGB").save(tile_path)


def affine_to_text(transform):
    """Store an Affine geotransform as 6 comma-separated numbers."""
    return (
        f"{transform.a},{transform.b},{transform.c},"
        f"{transform.d},{transform.e},{transform.f}"
    )


def bbox_to_text(bounds):
    """Store a bounding box as left,bottom,right,top."""
    left, bottom, right, top = bounds
    return f"{left},{bottom},{right},{top}"


def geospatial_metadata_for_window(src, window):
    """
    Build crs / transform / bbox text for one tile.

    We never invent a CRS. If the source has no CRS and no real
    geotransform, we store "unavailable" instead.
    """
    has_crs = src.crs is not None
    has_real_transform = src.transform is not None and not src.transform.is_identity

    if not has_crs and not has_real_transform:
        return UNAVAILABLE, UNAVAILABLE, UNAVAILABLE

    tile_transform = window_transform(window, src.transform)
    bounds = window_bounds(window, src.transform)

    crs_value = str(src.crs) if has_crs else UNAVAILABLE
    transform_value = affine_to_text(tile_transform)
    bbox_value = bbox_to_text(bounds)
    return crs_value, transform_value, bbox_value


def make_tile_row(tile_id, source_name, tile_x, tile_y, crs, transform, bbox):
    """Create one metadata.csv row."""
    return {
        "tile_id": tile_id,
        "source_image": source_name,
        "tile_x": tile_x,
        "tile_y": tile_y,
        "width": TILE_SIZE,
        "height": TILE_SIZE,
        "crs": crs,
        "transform": transform,
        "bbox": bbox,
    }


def write_metadata(rows, metadata_csv=METADATA_CSV):
    """Write tile information to processed_data/metadata/metadata.csv."""
    metadata_csv = Path(metadata_csv)
    metadata_csv.parent.mkdir(parents=True, exist_ok=True)

    with metadata_csv.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=METADATA_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def iter_full_tile_windows(width, height):
    """
    Yield 256x256 windows that fit completely inside the image.

    Incomplete right / bottom edge tiles are ignored on purpose.
    """
    for tile_y in range(0, height - TILE_SIZE + 1, TILE_SIZE):
        for tile_x in range(0, width - TILE_SIZE + 1, TILE_SIZE):
            window = Window(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
            yield tile_x, tile_y, window


def process_regular_image(image_path, tile_dir, metadata_rows):
    """
    Existing PNG / JPG path: convert to RGB and save 256x256 PNG tiles.

    These files are not georeferenced, so crs/transform/bbox are "unavailable".
    """
    generated = 0
    rejected = 0

    rgb = pillow_to_rgb(image_path)
    height, width = rgb.shape[0], rgb.shape[1]

    for tile_x, tile_y, window in iter_full_tile_windows(width, height):
        tile = rgb[tile_y:tile_y + TILE_SIZE, tile_x:tile_x + TILE_SIZE]

        if is_blank_tile(tile):
            rejected += 1
            continue

        tile_id = f"{image_path.stem}_x{tile_x}_y{tile_y}"
        save_png_tile(tile, tile_dir / f"{tile_id}.png")

        metadata_rows.append(
            make_tile_row(
                tile_id,
                image_path.name,
                tile_x,
                tile_y,
                UNAVAILABLE,
                UNAVAILABLE,
                UNAVAILABLE,
            )
        )
        generated += 1

    return generated, rejected


def save_geotiff_tile(src, data, window, tile_path):
    """
    Write one 256x256 GeoTIFF tile.

    The tile keeps the source CRS (or None) and a transform calculated
    from the parent geotransform and this tile's window.
    """
    tile_transform = window_transform(window, src.transform)

    profile = {
        "driver": "GTiff",
        "height": TILE_SIZE,
        "width": TILE_SIZE,
        "count": data.shape[0],
        "dtype": data.dtype,
        "crs": src.crs,  # None is allowed; we do not invent a CRS
        "transform": tile_transform,
    }
    if src.nodata is not None:
        profile["nodata"] = src.nodata

    with rasterio.open(tile_path, "w", **profile) as dst:
        dst.write(data)

    return tile_transform


def process_geotiff_image(image_path, tile_dir, metadata_rows):
    """
    GeoTIFF / TIFF path: read with Rasterio and save georeferenced .tif tiles.

    Useful raster bands and the original dtype are preserved.
    """
    generated = 0
    rejected = 0

    with rasterio.open(image_path) as src:
        for tile_x, tile_y, window in iter_full_tile_windows(src.width, src.height):
            data = src.read(window=window)

            if is_blank_tile(data):
                rejected += 1
                continue

            tile_id = f"{image_path.stem}_x{tile_x}_y{tile_y}"
            save_geotiff_tile(src, data, window, tile_dir / f"{tile_id}.tif")

            crs_value, transform_value, bbox_value = geospatial_metadata_for_window(
                src, window
            )
            metadata_rows.append(
                make_tile_row(
                    tile_id,
                    image_path.name,
                    tile_x,
                    tile_y,
                    crs_value,
                    transform_value,
                    bbox_value,
                )
            )
            generated += 1

    return generated, rejected


def process_one_image(image_path, tile_dir, metadata_rows):
    """Choose the PNG path or the GeoTIFF path for one input file."""
    suffix = image_path.suffix.lower()

    if suffix in TIFF_EXTENSIONS:
        try:
            return process_geotiff_image(image_path, tile_dir, metadata_rows)
        except Exception as error:
            # If Rasterio cannot open it, fall back to the old PNG path.
            print(f"Rasterio could not read {image_path.name} ({error}). Trying Pillow...")
            return process_regular_image(image_path, tile_dir, metadata_rows)

    return process_regular_image(image_path, tile_dir, metadata_rows)


def process_images(
    raw_dir=RAW_DIR,
    tile_dir=TILE_DIR,
    metadata_csv=METADATA_CSV,
):
    """Cut every input image into 256x256 tiles and save the valid ones."""
    raw_dir = Path(raw_dir)
    tile_dir = Path(tile_dir)
    metadata_csv = Path(metadata_csv)

    tile_dir.mkdir(parents=True, exist_ok=True)

    image_paths = list_input_images(raw_dir)
    metadata_rows = []
    tiles_generated = 0
    tiles_rejected = 0

    for image_path in image_paths:
        print(f"Processing {image_path.name}...")
        generated, rejected = process_one_image(image_path, tile_dir, metadata_rows)
        tiles_generated += generated
        tiles_rejected += rejected

    # Always write metadata.csv after processing, even if zero tiles were kept.
    write_metadata(metadata_rows, metadata_csv=metadata_csv)

    print("\nPreprocessing finished.")
    print(f"Number of input images: {len(image_paths)}")
    print(f"Number of tiles generated: {tiles_generated}")
    print(f"Number of rejected tiles: {tiles_rejected}")

    return tiles_generated, tiles_rejected, len(image_paths)


if __name__ == "__main__":
    process_images()
