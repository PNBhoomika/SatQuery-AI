import torch
import faiss
import numpy as np

# Load image embeddings
data = torch.load("image_embeddings.pt", map_location="cpu")

embeddings = data["embeddings"]
image_names = data["image_names"]

# Convert PyTorch tensor to NumPy
embeddings = embeddings.numpy().astype("float32")

# Create FAISS index
dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)

# Add embeddings to FAISS
index.add(embeddings)

# Save the index
faiss.write_index(index, "satellite.index")

# Save image names
torch.save(image_names, "image_names.pt")

print("FAISS index created successfully!")
print("Number of images:", index.ntotal)
print("Embedding dimension:", dimension)