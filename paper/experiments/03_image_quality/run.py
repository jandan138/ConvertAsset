#!/usr/bin/env python3
"""Experiment #2: Image Quality Metrics -- PSNR, SSIM, LPIPS.

No Isaac Sim needed. Uses rendered image pairs from Experiment #0.

Usage:
    python paper/experiments/03_image_quality/run.py
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

# Add Isaac Sim's bundled ML packages to path (torch, lpips, etc.)
sys.path.insert(0, "/isaac-sim/exts/omni.isaac.ml_archive/pip_prebundle")

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RENDERS_DIR = PROJECT_ROOT / "paper" / "results" / "raw" / "renders"
OUTPUT_CSV = PROJECT_ROOT / "paper" / "results" / "raw" / "image_quality.csv"

SCENE_IDS = [
    "chestofdrawers_0004",
    "chestofdrawers_0011",
    "chestofdrawers_0023",
    "chestofdrawers_0029",
]

ANGLES = ["front", "back", "left", "right", "top_front_left", "top_front_right"]


def _try_lpips():
    """Try to initialize LPIPS. Returns (fn, device) or (None, None) on failure."""
    try:
        import torch
        import lpips
        # Use VGG since its LPIPS weights are bundled in Isaac Sim
        fn = lpips.LPIPS(net="vgg", verbose=False)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        fn = fn.to(device)
        return fn, device
    except Exception as e:
        print(f"[Exp#2] LPIPS unavailable (will skip): {e}")
        return None, None


def main():
    from skimage.metrics import peak_signal_noise_ratio, structural_similarity
    from skimage import io as skio

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Try LPIPS
    lpips_fn, device = _try_lpips()
    if lpips_fn:
        print("[Exp#2] LPIPS loaded (VGG backbone)")
    else:
        print("[Exp#2] Running without LPIPS")

    rows = []

    for scene_id in SCENE_IDS:
        scene_dir = RENDERS_DIR / scene_id

        for angle in ANGLES:
            a_path = scene_dir / f"A_{angle}.png"
            b_path = scene_dir / f"B_{angle}.png"

            if not a_path.exists() or not b_path.exists():
                print(f"[WARN] Missing pair: {scene_id}/{angle}")
                continue

            img_a = skio.imread(str(a_path))
            img_b = skio.imread(str(b_path))

            # Handle RGBA -> RGB
            if img_a.shape[-1] == 4:
                img_a = img_a[:, :, :3]
            if img_b.shape[-1] == 4:
                img_b = img_b[:, :, :3]

            # Ensure same shape
            if img_a.shape != img_b.shape:
                h = min(img_a.shape[0], img_b.shape[0])
                w = min(img_a.shape[1], img_b.shape[1])
                img_a = img_a[:h, :w]
                img_b = img_b[:h, :w]

            # PSNR
            psnr = peak_signal_noise_ratio(img_a, img_b, data_range=255)

            # SSIM
            ssim = structural_similarity(img_a, img_b, channel_axis=2, data_range=255)

            # LPIPS
            lpips_val = float("nan")
            if lpips_fn is not None:
                import torch
                t_a = torch.from_numpy(img_a.copy()).permute(2, 0, 1).unsqueeze(0).float() / 127.5 - 1.0
                t_b = torch.from_numpy(img_b.copy()).permute(2, 0, 1).unsqueeze(0).float() / 127.5 - 1.0
                t_a = t_a.to(device)
                t_b = t_b.to(device)
                with torch.no_grad():
                    lpips_val = float(lpips_fn(t_a, t_b).item())

            row = {
                "scene_id": scene_id,
                "angle": angle,
                "psnr": round(psnr, 4),
                "ssim": round(ssim, 6),
                "lpips": round(lpips_val, 6) if not np.isnan(lpips_val) else "",
            }
            rows.append(row)
            lpips_str = f"{lpips_val:.4f}" if not np.isnan(lpips_val) else "N/A"
            print(f"  {scene_id}/{angle}: PSNR={psnr:.2f}, SSIM={ssim:.4f}, LPIPS={lpips_str}")

    # Write CSV
    with open(str(OUTPUT_CSV), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["scene_id", "angle", "psnr", "ssim", "lpips"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[Exp#2] Done. Wrote {len(rows)} rows to {OUTPUT_CSV}")

    # Summary stats
    if rows:
        psnrs = [r["psnr"] for r in rows]
        ssims = [r["ssim"] for r in rows]
        lpips_vals = [float(r["lpips"]) for r in rows if r["lpips"] != ""]
        print(f"  PSNR:  mean={np.mean(psnrs):.2f} +/- {np.std(psnrs):.2f}")
        print(f"  SSIM:  mean={np.mean(ssims):.4f} +/- {np.std(ssims):.4f}")
        if lpips_vals:
            print(f"  LPIPS: mean={np.mean(lpips_vals):.4f} +/- {np.std(lpips_vals):.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
