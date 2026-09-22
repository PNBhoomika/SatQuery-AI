"""
Siamese Deep Change Detection Architecture with Multi-Task Heads.
Backbone: Pretrained NASA-IBM Prithvi-EO-1.0-100M Foundation Model ViT encoder.
Fallback: ConvNeXt-T.
Covering SIH 2026 PS §2.2.2, §2.2.7 & §2.3.
"""

from __future__ import annotations

import os
import sys
import random
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    nn = object
    torch = None

# Canonical class vocabularies per PS §2.2.2
MORPHOLOGY_CLASSES: List[str] = ["appearance", "disappearance", "expansion", "contraction", "none"]
TYPE_CLASSES: List[str] = ["construction", "clearance", "water_extent", "road", "unknown"]

PRITHVI_DEFAULT_WEIGHTS_PATH = Path("change_detection/weights/prithvi/Prithvi_100M.pt")

# Global flag for one-time 3-channel warning
_WARNED_3_CHANNELS = False


def set_seed(seed: int = 42) -> None:
    """
    Set deterministic seeds across random, numpy, and torch.
    Enforces CUBLAS_WORKSPACE_CONFIG for deterministic CUDA operations.

    Args:
        seed: Integer seed value (default: 42).
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    os.environ["PYTHONHASHSEED"] = str(seed)

    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        try:
            torch.use_deterministic_algorithms(True)
        except Exception:
            pass


@dataclass
class ModelBundle:
    """Wrapper holding loaded PyTorch model, device, and cryptographic weight SHA-256."""
    model: Any
    device: str
    weights_sha256: str
    model_name: str
    model_version: str = "1.0.0"


def compute_sha256(filepath: Union[str, os.PathLike]) -> str:
    """
    Compute cryptographic SHA-256 hash of a file.

    Args:
        filepath: Path to the target file.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


if HAS_TORCH:
    class ConvNeXtBlock(nn.Module):
        """
        ConvNeXt depthwise separable block with 7x7 kernel, GELU activation,
        and inverted bottleneck (4x feature expansion).
        """
        def __init__(self, dim: int):
            super().__init__()
            self.dwconv = nn.Conv2d(dim, dim, kernel_size=7, padding=3, groups=dim)
            self.norm = nn.GroupNorm(1, dim)
            self.pwconv1 = nn.Conv2d(dim, 4 * dim, kernel_size=1)
            self.act = nn.GELU()
            self.pwconv2 = nn.Conv2d(4 * dim, dim, kernel_size=1)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            residual = x
            x = self.dwconv(x)
            x = self.norm(x)
            x = self.pwconv1(x)
            x = self.act(x)
            x = self.pwconv2(x)
            return residual + x

    class ConvNeXtTinyBackbone(nn.Module):
        """
        Hierarchical ConvNeXt-Tiny style encoder for satellite imagery chips.
        Produces multi-scale feature representations at stride 1/4 of input.
        """
        def __init__(self, in_channels: int = 3, feature_dim: int = 64):
            super().__init__()
            self.stem = nn.Sequential(
                nn.Conv2d(in_channels, feature_dim // 2, kernel_size=3, stride=2, padding=1),
                nn.GroupNorm(1, feature_dim // 2),
                nn.GELU(),
                nn.Conv2d(feature_dim // 2, feature_dim, kernel_size=3, stride=2, padding=1),
                nn.GroupNorm(1, feature_dim),
                nn.GELU(),
            )
            self.stage1 = nn.Sequential(
                ConvNeXtBlock(feature_dim),
                ConvNeXtBlock(feature_dim),
            )
            self.out_dim = feature_dim

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = self.stem(x)
            return self.stage1(x)

    class PrithviViTBlock(nn.Module):
        """
        Transformer Encoder Block for Prithvi-EO-1.0-100M ViT.
        Matches exact state dict keys in Prithvi_100M.pt:
        norm1, attn.qkv, attn.proj, norm2, mlp.fc1, mlp.fc2.
        """
        def __init__(self, dim: int = 768, num_heads: int = 12, mlp_ratio: float = 4.0):
            super().__init__()
            self.norm1 = nn.LayerNorm(dim)
            self.attn = nn.Module()
            self.attn.qkv = nn.Linear(dim, dim * 3)
            self.attn.proj = nn.Linear(dim, dim)
            self.norm2 = nn.LayerNorm(dim)
            self.mlp = nn.Module()
            self.mlp.fc1 = nn.Linear(dim, int(dim * mlp_ratio))
            self.mlp.fc2 = nn.Linear(int(dim * mlp_ratio), dim)
            self.num_heads = num_heads
            self.head_dim = dim // num_heads

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            norm_x = self.norm1(x)
            b, n, c = norm_x.shape
            qkv = self.attn.qkv(norm_x).reshape(b, n, 3, self.num_heads, self.head_dim).permute(2, 0, 3, 1, 4)
            q, k, v = qkv[0], qkv[1], qkv[2]
            attn = (q @ k.transpose(-2, -1)) * (self.head_dim ** -0.5)
            attn = attn.softmax(dim=-1)
            out = (attn @ v).transpose(1, 2).reshape(b, n, c)
            x = x + self.attn.proj(out)
            norm_x2 = self.norm2(x)
            mlp_out = self.mlp.fc2(F.gelu(self.mlp.fc1(norm_x2)))
            return x + mlp_out

    class Prithvi100MBackbone(nn.Module):
        """
        NASA-IBM Prithvi-EO-1.0-100M ViT Encoder Backbone.
        Expects 6-band input: [B02, B03, B04, B05, B06, B07] (Blue, Green, Red, NIR, SWIR1, SWIR2).
        Outputs spatial feature map (B, 768, H // 16, W // 16).
        """
        def __init__(
            self,
            in_chans: int = 6,
            embed_dim: int = 768,
            depth: int = 12,
            num_heads: int = 12,
            patch_size: int = 16
        ):
            super().__init__()
            self.embed_dim = embed_dim
            self.patch_size = patch_size
            self.out_dim = embed_dim

            # 3D Patch embedding (patch_size=(1, 16, 16))
            self.patch_embed = nn.Module()
            self.patch_embed.proj = nn.Conv3d(
                in_chans, embed_dim, kernel_size=(1, patch_size, patch_size), stride=(1, patch_size, patch_size)
            )
            self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
            # 1 + (3 frames * 14 * 14 patches) = 589
            self.pos_embed = nn.Parameter(torch.zeros(1, 589, embed_dim))
            self.blocks = nn.ModuleList([
                PrithviViTBlock(dim=embed_dim, num_heads=num_heads) for _ in range(depth)
            ])
            self.norm = nn.LayerNorm(embed_dim)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x shape: (B, 6, H, W)
            if x.dim() == 4:
                x = x.unsqueeze(2)  # (B, 6, 1, H, W)
            b, c, t, h, w = x.shape
            feat = self.patch_embed.proj(x)  # (B, 768, 1, hp, wp)
            hp, wp = feat.shape[3], feat.shape[4]
            feat = feat.squeeze(2).flatten(2).transpose(1, 2)  # (B, hp*wp, 768)

            # Interpolate 2D positional embeddings if spatial size differs from standard 14x14
            grid_pos = self.pos_embed[:, 1:197, :].reshape(1, 14, 14, self.embed_dim).permute(0, 3, 1, 2)
            if (hp, wp) != (14, 14):
                grid_pos = F.interpolate(grid_pos, size=(hp, wp), mode="bicubic", align_corners=False)
            pos = grid_pos.permute(0, 2, 3, 1).reshape(1, hp * wp, self.embed_dim)
            feat = feat + pos

            for blk in self.blocks:
                feat = blk(feat)
            feat = self.norm(feat)

            # Return spatial feature map (B, 768, hp, wp)
            spatial = feat.transpose(1, 2).reshape(b, self.embed_dim, hp, wp)
            return spatial

    class SiameseChangeNet(nn.Module):
        """
        Configurable Siamese Change Detection Network with:
          1. Backbone: Pretrained Prithvi-EO-1.0-100M ViT (or ConvNeXt-Tiny fallback)
          2. Fused Bi-Temporal Feature Neck: [f1, f2, |f1 - f2|]
          3. Multi-Task Decoders:
             a) change_head: Pixel-level change logit (B, 1, H, W)
             b) morphology_head: 5-class morphology categorization
             c) type_head: 5-class semantic change type categorization
        """
        def __init__(
            self,
            in_channels: int = 3,
            feature_dim: int = 128,
            backbone: str = "prithvi_100m",
            freeze_backbone: bool = True
        ):
            super().__init__()
            self.backbone_name = backbone.lower()
            self.freeze_backbone = freeze_backbone

            if self.backbone_name in ("prithvi", "prithvi_100m", "prithvi-100m"):
                self.backbone = Prithvi100MBackbone(in_chans=6)
                raw_backbone_dim = 768
            else:
                self.backbone = ConvNeXtTinyBackbone(in_channels=in_channels, feature_dim=64)
                raw_backbone_dim = 64

            if self.freeze_backbone:
                for param in self.backbone.parameters():
                    param.requires_grad = False

            fused_dim = raw_backbone_dim * 3
            self.fusion = nn.Sequential(
                nn.Conv2d(fused_dim, feature_dim, kernel_size=3, padding=1),
                nn.GroupNorm(1, feature_dim),
                nn.GELU(),
                ConvNeXtBlock(feature_dim),
            )

            # Head a: Per-pixel change logit decoder with multi-scale upsampling
            self.change_head = nn.Sequential(
                nn.ConvTranspose2d(feature_dim, feature_dim // 2, kernel_size=4, stride=2, padding=1),
                nn.GroupNorm(1, feature_dim // 2),
                nn.GELU(),
                nn.ConvTranspose2d(feature_dim // 2, feature_dim // 4, kernel_size=4, stride=2, padding=1),
                nn.GroupNorm(1, feature_dim // 4),
                nn.GELU(),
                nn.Conv2d(feature_dim // 4, 1, kernel_size=1)
            )

            # Global pooling for classification heads
            self.global_pool = nn.AdaptiveAvgPool2d((1, 1))

            # Head b: Morphology {appearance, disappearance, expansion, contraction, none}
            self.morphology_head = nn.Sequential(
                nn.Linear(feature_dim, 32),
                nn.GELU(),
                nn.Linear(32, 5)
            )

            # Head c: Semantic Type {construction, clearance, water_extent, road, unknown}
            self.type_head = nn.Sequential(
                nn.Linear(feature_dim, 32),
                nn.GELU(),
                nn.Linear(32, 5)
            )

        def _prepare_input(self, x: torch.Tensor) -> torch.Tensor:
            global _WARNED_3_CHANNELS
            if self.backbone_name in ("prithvi", "prithvi_100m", "prithvi-100m") and x.shape[1] == 3:
                if not _WARNED_3_CHANNELS:
                    print(
                        "[MODEL] Input has 3 channels; padding to 6 for Prithvi. "
                        "For best accuracy, request 6-band tiles from Member 1."
                    )
                    _WARNED_3_CHANNELS = True
                pad = torch.zeros(x.shape[0], 3, x.shape[2], x.shape[3], device=x.device, dtype=x.dtype)
                return torch.cat([x, pad], dim=1)
            return x

        def forward_features(self, x: torch.Tensor) -> torch.Tensor:
            x_prep = self._prepare_input(x)
            return self.backbone(x_prep)

        def forward(
            self, t1: torch.Tensor, t2: torch.Tensor
        ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            f1 = self.forward_features(t1)
            f2 = self.forward_features(t2)
            diff = torch.abs(f1 - f2)
            fused = torch.cat([f1, f2, diff], dim=1)
            feat = self.fusion(fused)

            # Output Head a: Pixel change logits (interpolated to match t1 target spatial resolution)
            change_logits = self.change_head(feat)
            if change_logits.shape[-2:] != t1.shape[-2:]:
                change_logits = F.interpolate(
                    change_logits, size=t1.shape[-2:], mode="bilinear", align_corners=False
                )

            # Output Heads b & c: Categorical classification logits
            pooled = self.global_pool(feat).flatten(1)
            morph_logits = self.morphology_head(pooled)
            type_logits = self.type_head(pooled)

            return change_logits, morph_logits, type_logits

    class DiceLoss(nn.Module):
        """
        Soft Dice Loss with precision > recall bias (PS §2.2.3).
        Weighting false positives more heavily penalizes over-detection.
        """
        def __init__(self, smooth: float = 1e-6, fp_penalty_weight: float = 1.2):
            super().__init__()
            self.smooth = smooth
            self.fp_penalty_weight = fp_penalty_weight

        def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
            probs = torch.sigmoid(logits)
            targets = targets.float()
            intersection = torch.sum(probs * targets)
            fp = torch.sum(probs * (1.0 - targets))
            fn = torch.sum((1.0 - probs) * targets)
            # Biased denominator penalizing false positives
            denominator = 2.0 * intersection + self.fp_penalty_weight * fp + fn + self.smooth
            dice = (2.0 * intersection + self.smooth) / denominator
            return 1.0 - dice

    class CombinedChangeLoss(nn.Module):
        """
        Multi-task Loss:
          L = w_bce * BCE + w_dice * Dice + w_morph * CE(morph) + w_type * CE(type)
        """
        def __init__(
            self,
            w_bce: float = 1.0,
            w_dice: float = 1.0,
            w_morph: float = 0.5,
            w_type: float = 0.5,
            pos_weight: float = 0.8  # Precision > recall bias
        ):
            super().__init__()
            self.w_bce = w_bce
            self.w_dice = w_dice
            self.w_morph = w_morph
            self.w_type = w_type
            self.bce = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight]))
            self.dice = DiceLoss()
            self.ce = nn.CrossEntropyLoss()

        def forward(
            self,
            change_logits: torch.Tensor,
            morph_logits: torch.Tensor,
            type_logits: torch.Tensor,
            gt_change: torch.Tensor,
            gt_morph: torch.Tensor,
            gt_type: torch.Tensor,
        ) -> Dict[str, torch.Tensor]:
            loss_bce = self.bce(change_logits.squeeze(1), gt_change.float())
            loss_dice = self.dice(change_logits.squeeze(1), gt_change.float())
            loss_morph = self.ce(morph_logits, gt_morph.long())
            loss_type = self.ce(type_logits, gt_type.long())

            total = (
                self.w_bce * loss_bce
                + self.w_dice * loss_dice
                + self.w_morph * loss_morph
                + self.w_type * loss_type
            )
            return {
                "total_loss": total,
                "loss_bce": loss_bce,
                "loss_dice": loss_dice,
                "loss_morph": loss_morph,
                "loss_type": loss_type,
            }

else:
    # Deterministic NumPy Fallback Model when PyTorch is not present
    class FallbackSiameseNet:
        """Lightweight NumPy fallback executing deterministic forward pass."""
        def __init__(self, backbone: str = "prithvi_100m"):
            self.backbone_name = backbone

        def __call__(self, t1: Any, t2: Any) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
            arr1 = np.asarray(t1)
            arr2 = np.asarray(t2)
            h, w = arr1.shape[-2], arr1.shape[-1]
            diff = np.mean(np.abs(arr2 - arr1), axis=0 if arr1.ndim == 3 else 1)
            change_logits = np.log((diff / (np.max(diff) + 1e-6)) + 1e-6)
            morph_logits = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
            type_logits = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
            return change_logits, morph_logits, type_logits

    SiameseChangeNet = FallbackSiameseNet
    DiceLoss = object
    CombinedChangeLoss = object


def load_model(
    weights_path: Optional[str] = None,
    backbone: str = "prithvi_100m",
    device: str = "auto",
    freeze_backbone: bool = True
) -> ModelBundle:
    """
    Load Siamese change detection model bundle.
    Uses pretrained NASA-IBM Prithvi-EO-1.0-100M foundation model ViT encoder.
    Falls back to ConvNeXt-Tiny with loud warning if Prithvi weights are missing.

    Args:
        weights_path: Optional file path to local finetuned head checkpoint (.pt).
        backbone: Backbone architecture ('prithvi_100m' or 'convnext_tiny').
        device: Target execution device ('auto', 'cpu', 'cuda').
        freeze_backbone: Freeze encoder backbone (default: True).

    Returns:
        ModelBundle containing model instance, device, and verified SHA-256.
    """
    set_seed(42)

    if not HAS_TORCH:
        sha256_hash = "0" * 64
        if weights_path and os.path.isfile(weights_path):
            sha256_hash = compute_sha256(weights_path)
        return ModelBundle(
            model=FallbackSiameseNet(backbone=backbone),
            device="cpu",
            weights_sha256=sha256_hash,
            model_name=f"SatQuery-Siamese-{backbone}",
            model_version="1.0.0"
        )

    if device == "auto":
        dev = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        dev = device

    bb_lower = backbone.lower()
    active_backbone = bb_lower

    # Check if Prithvi backbone requested
    if bb_lower in ("prithvi", "prithvi_100m", "prithvi-100m"):
        prithvi_file = PRITHVI_DEFAULT_WEIGHTS_PATH
        if prithvi_file.is_file():
            model = SiameseChangeNet(
                backbone="prithvi_100m",
                freeze_backbone=freeze_backbone
            ).to(dev)
            # Load pretrained Prithvi encoder weights
            ckpt = torch.load(prithvi_file, map_location=dev)
            if isinstance(ckpt, dict):
                encoder_weights = {
                    k[len("encoder."):]: v for k, v in ckpt.items() if k.startswith("encoder.")
                }
                model.backbone.load_state_dict(encoder_weights, strict=False)
            sha256_hash = compute_sha256(prithvi_file)
            active_backbone = "prithvi_100m"
        else:
            print(
                "[MODEL] WARNING: Prithvi weights not found. Using random-init ConvNeXt-Tiny. Results will be poor."
            )
            model = SiameseChangeNet(
                backbone="convnext_tiny",
                freeze_backbone=False
            ).to(dev)
            sha256_hash = "0" * 64
            active_backbone = "convnext_tiny"
    else:
        model = SiameseChangeNet(
            backbone="convnext_tiny",
            freeze_backbone=False
        ).to(dev)
        sha256_hash = "0" * 64

    # Load finetuned head weights if provided
    if weights_path and os.path.isfile(weights_path):
        sha256_hash = compute_sha256(weights_path)
        checkpoint = torch.load(weights_path, map_location=dev)
        state_dict = checkpoint.get("state_dict", checkpoint)
        model.load_state_dict(state_dict, strict=False)

    model.eval()

    return ModelBundle(
        model=model,
        device=dev,
        weights_sha256=sha256_hash,
        model_name=f"SatQuery-Siamese-{active_backbone}",
        model_version="1.0.0"
    )
