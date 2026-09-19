# M2 - Semantic Retrieval and Embedding

## Overview

This module handles semantic retrieval of satellite imagery using
RemoteCLIP embeddings, FAISS similarity search, and HDBSCAN clustering.

## Pipeline

Satellite Images
        ↓
RemoteCLIP
        ↓
512-D Image Embeddings
        ↓
 ┌───────────────┐
 ↓               ↓
FAISS          HDBSCAN
 ↓               ↓
Similarity      Clusters
Search          + Outliers

## Components

### 1. RemoteCLIP Embeddings

RemoteCLIP ViT-B/32 is used to convert satellite images into
512-dimensional embeddings.

The embeddings are normalized before storage and retrieval.

### 2. FAISS Retrieval

FAISS `IndexFlatIP` is used for similarity search.

It supports:

- Text-to-image retrieval
- Image-to-image retrieval
- Top-k similarity ranking

### 3. HDBSCAN Clustering

HDBSCAN is applied to the RemoteCLIP embeddings to discover
naturally similar groups of satellite images.

It can also identify unusual images as outliers.

The clustering is unsupervised, so HDBSCAN does not automatically
assign semantic labels such as "urban", "water", or "road".

### 4. Current Test Dataset

The current implementation has been tested using 13 sample satellite
images.

Example test result:

- 3 clusters
- 1 outlier

The sample images are only for testing. The final system will use
satellite tiles provided by the M1 Data Ingestion module.

## Files

- `embed.py` - RemoteCLIP model loading and embedding functions
- `create_embeddings.py` - generates image embeddings
- `build_index.py` - creates the FAISS index
- `search.py` - semantic similarity search
- `cluster.py` - HDBSCAN clustering
- `requirements.txt` - Python dependencies
- `tests/test_search.py` - retrieval tests

## Data Flow with M1

M1 provides processed satellite tiles.

M2 will process those tiles using RemoteCLIP, generate embeddings,
build the FAISS index, and perform HDBSCAN clustering.

Metadata such as tile ID, date, platform, and location will be mapped
back to the retrieval results using the tile identifiers.

## Future Work

- Integrate M1's real satellite tile dataset
- Support large-scale tile collections
- Connect retrieval results to the backend API
- Connect HDBSCAN cluster information with satellite metadata