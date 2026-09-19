import torch
import faiss
from PIL import Image
import matplotlib.pyplot as plt

from embed import embed_text


# Load FAISS index
index = faiss.read_index("satellite.index")

# Load image names
image_names = torch.load("image_names.pt", map_location="cpu")

# Get user query
query = input("Enter your search query: ")

# Create text embedding
embedding = embed_text(query)

# Convert to NumPy
embedding = embedding.numpy().astype("float32")

# Search FAISS
scores, indices = index.search(embedding, 5)

print("\nTop matching satellite images:\n")

for rank, (score, index_number) in enumerate(
    zip(scores[0], indices[0]), start=1
):
    print(
        f"{rank}. {image_names[index_number]} "
        f"Score: {score:.4f}"
    )


# Display images
fig, axes = plt.subplots(1, 5, figsize=(20, 5))

for i, (score, index_number) in enumerate(
    zip(scores[0], indices[0])
):
    image_path = "satellite_images/" + image_names[index_number]

    image = Image.open(image_path).convert("RGB")

    axes[i].imshow(image)
    axes[i].set_title(
        f"{image_names[index_number]}\nScore: {score:.4f}"
    )
    axes[i].axis("off")

plt.tight_layout()
plt.show()