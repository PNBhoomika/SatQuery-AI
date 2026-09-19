# Module 1 — Data Ingestion & Preprocessing

## Purpose

This module prepares raw satellite images for the downstream ML and image analysis modules.

## Input

- Raw satellite images
- Supported formats: PNG, JPG, JPEG, TIFF, TIF

## Processing

The preprocessing pipeline:

1. Reads the raw satellite image.
2. Converts the image to RGB format.
3. Divides the image into 256×256 tiles.
4. Ignores incomplete edge tiles.
5. Rejects blank or empty tiles.
6. Saves the valid tiles.
7. Generates metadata for each tile.

## Output

- 256×256 processed image tiles
- `metadata.csv`

The metadata contains:

- `tile_id`
- `source_image`
- `tile_x`
- `tile_y`
- `width`
- `height`

## Folder Structure

```text
processed_data/
├── tiles/
└── metadata/
    └── metadata.csv
