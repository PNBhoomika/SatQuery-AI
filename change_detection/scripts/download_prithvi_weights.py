#!/usr/bin/env python3
"""
Download script for NASA-IBM Prithvi-EO-1.0-100M Foundation Model Weights.
Permitted by SIH 2026 PS §2.2.7 (Pretrained public models).
Downloads: Prithvi_100M.pt, config.json, README.md
Generates: change_detection/weights/prithvi/MANIFEST.sha256
"""

import os
import sys
import hashlib
from pathlib import Path
import requests
from huggingface_hub import hf_hub_download

REPO_ID = "ibm-nasa-geospatial/Prithvi-EO-1.0-100M"
TARGET_DIR = Path("change_detection/weights/prithvi")
FILES_TO_DOWNLOAD = ["Prithvi_100M.pt", "config.json", "README.md"]


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_file(filename: str, target_path: Path):
    print(f"[DOWNLOAD] Fetching {filename}...", flush=True)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # a) Attempt huggingface_hub.hf_hub_download as specified
        downloaded = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            local_dir=str(TARGET_DIR),
        )
        print(f"[DOWNLOAD] hf_hub_download succeeded: {downloaded}", flush=True)
    except Exception as e:
        print(f"[DOWNLOAD] hf_hub_download note ({e}); streaming direct from HuggingFace...", flush=True)
        url = f"https://huggingface.co/{REPO_ID}/resolve/main/{filename}"
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total_bytes = int(r.headers.get("content-length", 0))
            downloaded_bytes = 0
            with open(target_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        if total_bytes > 0:
                            pct = (downloaded_bytes / total_bytes) * 100
                            mb = downloaded_bytes / (1024 * 1024)
                            tot_mb = total_bytes / (1024 * 1024)
                            sys.stdout.write(f"\r[DOWNLOAD] {filename}: {mb:.1f}/{tot_mb:.1f} MB ({pct:.1f}%)")
                            sys.stdout.flush()
        print()


def main():
    print(f"[DOWNLOAD] Target repository: {REPO_ID}", flush=True)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    for filename in FILES_TO_DOWNLOAD:
        target_path = TARGET_DIR / filename
        if not target_path.exists() or target_path.stat().st_size == 0:
            download_file(filename, target_path)
        else:
            print(f"[DOWNLOAD] {filename} already present ({target_path.stat().st_size / (1024*1024):.2f} MB).", flush=True)

    # Compute SHA-256 and write MANIFEST.sha256
    manifest_path = TARGET_DIR / "MANIFEST.sha256"
    manifest_lines = []

    print("\n" + "=" * 70, flush=True)
    print("DOWNLOAD AUDIT SUMMARY:", flush=True)
    print("=" * 70, flush=True)

    for filename in FILES_TO_DOWNLOAD:
        p = TARGET_DIR / filename
        sha = compute_sha256(p)
        size_bytes = p.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        manifest_lines.append(f"{sha}  {filename}")
        print(f"File:     {filename}", flush=True)
        print(f"Size:     {size_mb:.2f} MB ({size_bytes:,} bytes)", flush=True)
        print(f"SHA-256:  {sha}", flush=True)
        print("-" * 70, flush=True)

    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    print(f"[MANIFEST] Wrote checksum manifest to: {manifest_path}", flush=True)

    # Print Licence declaration
    print("\n" + "=" * 70, flush=True)
    print("LICENCE DECLARATION (PS §2.2.7):", flush=True)
    print("=" * 70, flush=True)
    print("Model:    ibm-nasa-geospatial/Prithvi-EO-1.0-100M", flush=True)
    print("Licence:  Apache License 2.0 (Open Source / Commercial & Research Permitted)", flush=True)
    print("Origin:   NASA & IBM Research Foundation Model for Earth Observation", flush=True)
    print("Citation: Jakubik et al., Foundation Models for Generalist Geospatial AI, 2023", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    main()
