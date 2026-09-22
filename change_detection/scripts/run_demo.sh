#!/usr/bin/env bash
# ==============================================================================
# SatQuery-AI: Run Air-Gapped Demo
# SIH 2026 Problem Statement 26227
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "======================================================================"
echo "SatQuery-AI: Launching Change Detection Demo Service"
echo "======================================================================"

# 1. Verify Checksum Manifest
MANIFEST_PATH="${MODULE_DIR}/weights/MANIFEST.sha256"
if [ -f "${MANIFEST_PATH}" ] && [ -s "${MANIFEST_PATH}" ]; then
    echo "[VERIFY] Checking weights against MANIFEST.sha256..."
    cd "${MODULE_DIR}/weights"
    sha256sum -c MANIFEST.sha256 || {
        echo "[ERROR] Checksum verification failed!"
        exit 1
    }
else
    echo "[INFO] No pre-staged weights manifest found or empty; skipping checksum."
fi

# 2. Start Uvicorn Server in background
echo "[SERVER] Starting FastAPI server on http://localhost:8000..."
uvicorn change_detection.router:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server startup
sleep 3

# 3. Health Probe Smoke Test
echo "[TEST] Running smoke test against /change/healthz..."
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/change/healthz || true

echo "[READY] Demo service active. PID=${SERVER_PID}"
