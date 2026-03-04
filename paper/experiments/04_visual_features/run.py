#!/usr/bin/env python3
"""Experiment #3a: CLIP/DINOv2 Feature Similarity.

No Isaac Sim needed. Uses rendered image pairs from Experiment #0.

Usage:
    pip install transformers torch pillow
    python paper/experiments/04_visual_features/run.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RENDERS_DIR = PROJECT_ROOT / "paper" / "results" / "raw" / "renders"
OUTPUT_DIR = PROJECT_ROOT / "paper" / "results" / "raw"

SCENE_IDS = [
    "chestofdrawers_0004",
    "chestofdrawers_0011",
    "chestofdrawers_0023",
    "chestofdrawers_0029",
]

ANGLES = ["front", "back", "left", "right", "top_front_left", "top_front_right"]


def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    a_flat = a.flatten()
    b_flat = b.flatten()
    dot = np.dot(a_flat, b_flat)
    norm_a = np.linalg.norm(a_flat)
    norm_b = np.linalg.norm(b_flat)
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return float(dot / (norm_a * norm_b))


def main():
    import torch
    from PIL import Image

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect image pairs
    pairs = []
    for scene_id in SCENE_IDS:
        scene_dir = RENDERS_DIR / scene_id
        for angle in ANGLES:
            a_path = scene_dir / f"A_{angle}.png"
            b_path = scene_dir / f"B_{angle}.png"
            if a_path.exists() and b_path.exists():
                pairs.append((scene_id, angle, str(a_path), str(b_path)))

    print(f"[Exp#3a] Found {len(pairs)} image pairs")
    if not pairs:
        print("[ERROR] No image pairs found")
        return 1

    # Load all images
    all_images_a = []
    all_images_b = []
    for _, _, a_path, b_path in pairs:
        all_images_a.append(Image.open(a_path).convert("RGB"))
        all_images_b.append(Image.open(b_path).convert("RGB"))

    # ── CLIP Features ──────────────────────────────────────────────────────
    print("[Exp#3a] Extracting CLIP features...")
    clip_emb_a = []
    clip_emb_b = []
    try:
        from transformers import CLIPProcessor, CLIPModel

        clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        if torch.cuda.is_available():
            clip_model = clip_model.cuda()

        clip_model.eval()

        for i, (img_a, img_b) in enumerate(zip(all_images_a, all_images_b)):
            inputs_a = clip_processor(images=img_a, return_tensors="pt")
            inputs_b = clip_processor(images=img_b, return_tensors="pt")
            if torch.cuda.is_available():
                inputs_a = {k: v.cuda() for k, v in inputs_a.items()}
                inputs_b = {k: v.cuda() for k, v in inputs_b.items()}

            with torch.no_grad():
                feat_a = clip_model.get_image_features(**inputs_a).pooler_output.cpu().numpy().squeeze()
                feat_b = clip_model.get_image_features(**inputs_b).pooler_output.cpu().numpy().squeeze()

            clip_emb_a.append(feat_a)
            clip_emb_b.append(feat_b)

        print(f"  CLIP: extracted {len(clip_emb_a)} embedding pairs, dim={clip_emb_a[0].shape}")
    except Exception as e:
        print(f"[WARN] CLIP extraction failed: {e}")
        import traceback
        traceback.print_exc()

    # ── DINOv2 Features ────────────────────────────────────────────────────
    print("[Exp#3a] Extracting DINOv2 features...")
    dino_emb_a = []
    dino_emb_b = []
    try:
        from transformers import AutoImageProcessor, AutoModel

        dino_processor = AutoImageProcessor.from_pretrained("facebook/dinov2-small")
        dino_model = AutoModel.from_pretrained("facebook/dinov2-small")

        if torch.cuda.is_available():
            dino_model = dino_model.cuda()

        dino_model.eval()

        for i, (img_a, img_b) in enumerate(zip(all_images_a, all_images_b)):
            inputs_a = dino_processor(images=img_a, return_tensors="pt")
            inputs_b = dino_processor(images=img_b, return_tensors="pt")
            if torch.cuda.is_available():
                inputs_a = {k: v.cuda() for k, v in inputs_a.items()}
                inputs_b = {k: v.cuda() for k, v in inputs_b.items()}

            with torch.no_grad():
                feat_a = dino_model(**inputs_a).last_hidden_state[:, 0].cpu().numpy().squeeze()
                feat_b = dino_model(**inputs_b).last_hidden_state[:, 0].cpu().numpy().squeeze()

            dino_emb_a.append(feat_a)
            dino_emb_b.append(feat_b)

        print(f"  DINOv2: extracted {len(dino_emb_a)} embedding pairs, dim={dino_emb_a[0].shape}")
    except Exception as e:
        print(f"[WARN] DINOv2 extraction failed: {e}")
        import traceback
        traceback.print_exc()

    # ── Save embeddings ────────────────────────────────────────────────────
    if clip_emb_a:
        np.savez(
            str(OUTPUT_DIR / "clip_embeddings.npz"),
            A=np.array(clip_emb_a),
            B=np.array(clip_emb_b),
            pairs=np.array([(s, a) for s, a, _, _ in pairs]),
        )
        print(f"  Saved clip_embeddings.npz")

    if dino_emb_a:
        np.savez(
            str(OUTPUT_DIR / "dino_embeddings.npz"),
            A=np.array(dino_emb_a),
            B=np.array(dino_emb_b),
            pairs=np.array([(s, a) for s, a, _, _ in pairs]),
        )
        print(f"  Saved dino_embeddings.npz")

    # ── Compute per-pair similarities ──────────────────────────────────────
    rows = []
    for i, (scene_id, angle, _, _) in enumerate(pairs):
        row = {"scene_id": scene_id, "angle": angle}

        if i < len(clip_emb_a):
            row["clip_cosine"] = round(cosine_similarity(clip_emb_a[i], clip_emb_b[i]), 6)
        else:
            row["clip_cosine"] = ""

        if i < len(dino_emb_a):
            row["dino_cosine"] = round(cosine_similarity(dino_emb_a[i], dino_emb_b[i]), 6)
        else:
            row["dino_cosine"] = ""

        rows.append(row)

    csv_path = OUTPUT_DIR / "feature_similarity.csv"
    with open(str(csv_path), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["scene_id", "angle", "clip_cosine", "dino_cosine"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[Exp#3a] Wrote {len(rows)} rows to {csv_path}")

    # Summary
    if clip_emb_a:
        clip_sims = [r["clip_cosine"] for r in rows if r["clip_cosine"] != ""]
        print(f"  CLIP cosine:  mean={np.mean(clip_sims):.4f} +/- {np.std(clip_sims):.4f}")
    if dino_emb_a:
        dino_sims = [r["dino_cosine"] for r in rows if r["dino_cosine"] != ""]
        print(f"  DINOv2 cosine: mean={np.mean(dino_sims):.4f} +/- {np.std(dino_sims):.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
