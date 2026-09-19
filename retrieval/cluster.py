import faiss
import torch
import hdbscan

INDEX_PATH = "retrieval/data/satellite.index"
NAMES_PATH = "retrieval/data/image_names.pt"
OUTPUT_PATH = "retrieval/data/cluster_results.pt"


# Load FAISS index
index = faiss.read_index(INDEX_PATH)

# Extract embeddings from FAISS
embeddings = index.reconstruct_n(0, index.ntotal)

print("Number of embeddings:", embeddings.shape[0])
print("Embedding dimension:", embeddings.shape[1])


# Run HDBSCAN
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=2,
    min_samples=1,
    metric="euclidean"
)

labels = clusterer.fit_predict(embeddings)


# Load image/tile names
image_names = torch.load(
    NAMES_PATH,
    map_location="cpu",
    weights_only=False
)


# Display results
print("\nHDBSCAN Results:")
print("----------------")

for name, label in zip(image_names, labels):
    if label == -1:
        print(f"{name} -> OUTLIER")
    else:
        print(f"{name} -> Cluster {label}")


# Save results
results = {
    "image_names": image_names,
    "cluster_labels": labels.tolist()
}

torch.save(results, OUTPUT_PATH)


# Summary
number_of_clusters = len(set(labels)) - (1 if -1 in labels else 0)
number_of_outliers = list(labels).count(-1)

print("\nCluster results saved to:")
print(OUTPUT_PATH)

print("\nNumber of clusters:", number_of_clusters)
print("Number of outliers:", number_of_outliers)