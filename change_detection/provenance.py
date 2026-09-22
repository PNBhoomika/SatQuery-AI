"""
Provenance tracking and STAC export utilities.
Covering PS §2.2.5.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


def get_git_sha() -> str:
    """Retrieve current git commit SHA or return fallback version."""
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return sha.decode("utf-8").strip()
    except Exception:
        version_file = Path("change_detection/VERSION")
        if version_file.exists():
            return version_file.read_text().strip()
        return "git-sha-unavailable"


def export_provenance(change_event: Dict[str, Any], out_dir: str) -> str:
    """
    Export change event artifacts to disk:
      - <event_id>.stac.json
      - <event_id>.mask.tif
      - <event_id>.provenance.json
      - <event_id>.README.txt
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    event_id = change_event.get("stac_change_event", {}).get("id", "change_event")

    # 1. STAC Item JSON
    stac_path = out / f"{event_id}.stac.json"
    with open(stac_path, "w", encoding="utf-8") as f:
        json.dump(change_event.get("stac_change_event", {}), f, indent=2)

    # 2. COG change mask
    src_mask = change_event.get("change_mask")
    mask_dest = out / f"{event_id}.mask.tif"
    if src_mask and Path(src_mask).exists():
        shutil.copyfile(src_mask, mask_dest)
    else:
        # Create empty placeholder mask
        mask_dest.touch()

    # 3. Provenance JSON
    prov_path = out / f"{event_id}.provenance.json"
    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump(change_event.get("provenance", {}), f, indent=2)

    # 4. Human-readable README.txt
    readme_path = out / f"{event_id}.README.txt"
    prov = change_event.get("provenance", {})
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"SatQuery-AI Change Event: {event_id}\n")
        f.write(f"Model: {prov.get('model_name')} v{prov.get('model_version')}\n")
        f.write(f"Weights SHA-256: {prov.get('weights_sha256')}\n")
        f.write(f"Code Git SHA: {prov.get('code_git_sha')}\n")
        f.write(f"Confidence: {change_event.get('confidence')}\n")
        f.write(f"Change Type: {change_event.get('change_type')}\n")
        f.write(f"Morphology: {change_event.get('change_morphology')}\n")

    return str(out)
