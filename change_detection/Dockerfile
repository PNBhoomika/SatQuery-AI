# ==============================================================================
# SatQuery-AI: Change Detection Service (Member 3)
# Air-Gapped Production Container Build
# SIH 2026 Problem Statement 26227
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    CUBLAS_WORKSPACE_CONFIG=:4096:8

WORKDIR /app

# Install native system dependencies required for GDAL, rasterio, and compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY change_detection/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source code
COPY change_detection /app/change_detection

# Ensure offline weights directory exists
RUN mkdir -p /app/change_detection/weights

# Healthcheck probe using internal endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/change/healthz || exit 1

EXPOSE 8000

# Default runtime command (does not run at build time)
CMD ["uvicorn", "change_detection.router:app", "--host", "0.0.0.0", "--port", "8000"]

