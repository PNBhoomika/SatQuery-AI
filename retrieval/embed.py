import torch
import open_clip
MODEL_PATH = r"C:\Users\Kusu K\Desktop\SatQuery-AI-local\checkpoints\models--chendelong--RemoteCLIP\snapshots\bf1d8a3ccf2ddbf7c875705e46373bfe542bce38\RemoteCLIP-ViT-B-32.pt"

# Load RemoteCLIP
model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32",
    pretrained=None
)

checkpoint = torch.load(MODEL_PATH, map_location="cpu")
model.load_state_dict(checkpoint)
model.eval()

# Tokenizer for text
tokenizer = open_clip.get_tokenizer("ViT-B-32")


# Text → embedding
def embed_text(text):
    tokens = tokenizer([text])

    with torch.no_grad():
        embedding = model.encode_text(tokens)

    embedding /= embedding.norm(dim=-1, keepdim=True)

    return embedding


# Image → embedding
def embed_image(image):
    image = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        embedding = model.encode_image(image)

    embedding /= embedding.norm(dim=-1, keepdim=True)

    return embedding