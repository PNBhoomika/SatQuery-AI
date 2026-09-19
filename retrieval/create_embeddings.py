import torch
import open_clip
from PIL import Image
from pathlib import Path

MODEL_PATH = "checkpoints/models--chendelong--RemoteCLIP/snapshots/bf1d8a3ccf2ddbf7c875705e46373bfe542bce38/RemoteCLIP-ViT-B-32.pt"

# Load RemoteCLIP
model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32",
    pretrained=None
)

checkpoint = torch.load(MODEL_PATH, map_location="cpu")
model.load_state_dict(checkpoint)
model.eval()

# Find all images
image_folder = Path("satellite_images")
image_files = list(image_folder.glob("*"))

embeddings = []
image_names = []

for image_file in image_files:
    try:
        image = preprocess(Image.open(image_file).convert("RGB")).unsqueeze(0)

        with torch.no_grad():
            embedding = model.encode_image(image)

        # Normalize
        embedding /= embedding.norm(dim=-1, keepdim=True)

        embeddings.append(embedding)
        image_names.append(image_file.name)

        print("Processed:", image_file.name)

    except Exception as e:
        print("Skipped:", image_file.name, "-", e)

# Combine all embeddings
embeddings = torch.cat(embeddings)

# Save them
torch.save(
    {
        "embeddings": embeddings,
        "image_names": image_names
    },
    "image_embeddings.pt"
)

print("\nDone!")
print("Number of images:", len(image_names))
print("Embedding shape:", embeddings.shape)