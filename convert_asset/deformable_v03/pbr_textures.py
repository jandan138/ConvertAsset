"""PBR albedo, tangent-space normal, and roughness texture synthesis for v0.3 assets."""

from __future__ import annotations

from pathlib import Path
import math
from typing import Any

import numpy as np
from PIL import Image


def _make_seamless_tile(rgb: np.ndarray, out_size: int) -> np.ndarray:
    """Resize an image and feather only the outer 6% rim symmetrically so periodic patterns stay crisp."""
    img = Image.open(raw) if isinstance(raw := rgb, (str, Path)) else Image.fromarray(rgb, mode="RGB")
    img = img.resize((out_size, out_size), Image.Resampling.LANCZOS)
    arr = np.asarray(img, dtype=np.float32)
    margin = max(8, out_size // 16)
    flipped_x = arr[:, ::-1, :]
    flipped_y = arr[::-1, :, :]

    # Blend outer left/right border strips smoothly into wrapped edge to prevent sharp seam lines
    t = np.linspace(0.0, 0.5, margin, dtype=np.float32)
    w_x = 0.5 - 0.5 * np.cos(math.pi * t)
    for k in range(margin):
        alpha = float(w_x[k])
        col_l = arr[:, k, :].copy()
        col_r = arr[:, out_size - 1 - k, :].copy()
        avg = 0.5 * (col_l + col_r)
        arr[:, k, :] = (1.0 - 2.0 * alpha) * avg + 2.0 * alpha * col_l
        arr[:, out_size - 1 - k, :] = (1.0 - 2.0 * alpha) * avg + 2.0 * alpha * col_r
    for k in range(margin):
        alpha = float(w_x[k])
        row_t = arr[k, :, :].copy()
        row_b = arr[out_size - 1 - k, :, :].copy()
        avg = 0.5 * (row_t + row_b)
        arr[k, :, :] = (1.0 - 2.0 * alpha) * avg + 2.0 * alpha * row_t
        arr[out_size - 1 - k, :, :] = (1.0 - 2.0 * alpha) * avg + 2.0 * alpha * row_b
    _ = (flipped_x, flipped_y)
    return np.clip(arr, 0.0, 255.0).astype(np.uint8)


def load_or_generate_albedo(
    raw_path: Path | None,
    *,
    fallback_rgb: tuple[int, int, int] = (205, 145, 72),
    out_size: int = 1024,
) -> np.ndarray:
    """Load an AI-generated raw image or emit a deterministic micro-textured fallback if absent."""
    if raw_path is not None and raw_path.is_file():
        img = Image.open(raw_path).convert("RGB")
        # Crop central 88% to strip any border vignette from generative image models
        w, h = img.size
        mx, my = int(w * 0.06), int(h * 0.06)
        cropped = img.crop((mx, my, w - mx, h - my))
        return _make_seamless_tile(np.asarray(cropped, dtype=np.uint8), out_size=out_size)

    rng = np.random.default_rng(sum(fallback_rgb) + out_size)
    ys = np.linspace(0.0, 2.0 * np.pi, out_size, endpoint=False, dtype=np.float32)[:, None]
    xs = np.linspace(0.0, 2.0 * np.pi, out_size, endpoint=False, dtype=np.float32)[None, :]
    grain = 8.0 * np.sin(12.0 * xs) * np.sin(12.0 * ys) + rng.normal(0.0, 4.5, (out_size, out_size))
    base = np.zeros((out_size, out_size, 3), dtype=np.float32)
    for c in range(3):
        base[:, :, c] = float(fallback_rgb[c]) + grain
    return np.clip(base, 0.0, 255.0).astype(np.uint8)


def derive_pbr_maps_from_albedo(
    albedo_path: Path,
    out_dir: Path,
    *,
    normal_strength: float = 2.6,
    roughness_range: tuple[float, float] = (0.35, 0.72),
    out_size: int = 1024,
    fallback_rgb: tuple[int, int, int] = (205, 145, 72),
) -> dict[str, Path]:
    """Generate tiled ``albedo.png``, tangent-space ``normal.png``, and ``roughness.png``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    albedo_u8 = load_or_generate_albedo(albedo_path, fallback_rgb=fallback_rgb, out_size=out_size)

    lum = (
        0.299 * albedo_u8[:, :, 0].astype(np.float32)
        + 0.587 * albedo_u8[:, :, 1].astype(np.float32)
        + 0.114 * albedo_u8[:, :, 2].astype(np.float32)
    ) / 255.0

    # Periodic finite differences preserve tileability across texture borders
    dx = (np.roll(lum, -1, axis=1) - np.roll(lum, 1, axis=1)) * 0.5 * float(normal_strength)
    dy = (np.roll(lum, -1, axis=0) - np.roll(lum, 1, axis=0)) * 0.5 * float(normal_strength)
    nz = np.ones_like(lum, dtype=np.float32)
    norm_len = np.sqrt(dx * dx + dy * dy + nz * nz)
    nx = -dx / norm_len
    ny = -dy / norm_len
    nz = nz / norm_len
    nrm_u8 = np.clip(np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, nz * 0.5 + 0.5], axis=-1) * 255.0, 0.0, 255.0).astype(
        np.uint8
    )

    r_min, r_max = float(roughness_range[0]), float(roughness_range[1])
    # Darker crevices slightly rougher, highlights slightly smoother
    rough = r_max - lum * (r_max - r_min)
    rough_u8 = np.clip(rough * 255.0, 0.0, 255.0).astype(np.uint8)

    p_alb = out_dir / "albedo.png"
    p_nrm = out_dir / "normal.png"
    p_rgh = out_dir / "roughness.png"
    Image.fromarray(albedo_u8, mode="RGB").save(p_alb, format="PNG")
    Image.fromarray(nrm_u8, mode="RGB").save(p_nrm, format="PNG")
    Image.fromarray(rough_u8, mode="L").save(p_rgh, format="PNG")
    return {"albedo": p_alb, "normal": p_nrm, "roughness": p_rgh}
