#!/usr/bin/env python3
"""Extract interpretable zero-VLM geometry, optical-regime, and paired-render delta features."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v3_common import (  # noqa: E402
    repo_root_from_script,
    resolve_asset_path,
    sha256_file,
    srgb_uint8_to_lab,
)


TRANSPARENT_CATS = {"bottle", "cup", "bowl"}
REFLECTIVE_CATS = {
    "faucet",
    "sink",
    "coffeemaker",
    "oven",
    "microwave",
    "refrigerator",
    "dishwasher",
    "hearth",
    "mirror",
    "pot",
    "pan",
    "tray",
    "shoppingtrolley",
    "ceiling_light",
    "lamp",
}
EMISSIVE_CATS = {"tv", "monitor", "laptop", "clock", "lamp", "ceiling_light"}

FEATURE_NAMES_ALL: tuple[str, ...] = (
    "log_area_frac",
    "aspect_ratio",
    "center_dist_norm",
    "border_touch",
    "mask_iou",
    "cat_is_transparent_or_glass",
    "cat_is_reflective_appliance_or_metal",
    "cat_is_emissive_or_screen",
    "is_transparent_or_glass",
    "is_reflective_appliance_or_metal",
    "is_emissive_or_screen",
    "global_rgb_mae",
    "target_rgb_mae",
    "bg_rgb_mae",
    "target_delta_L",
    "target_delta_ab",
    "target_std_L_ratio",
    "target_ssim",
    "bg_ssim",
    "target_sobel_edge_ratio",
    "target_specular_delta",
    "ring_specular_delta",
    "boundary_contrast_delta",
    "boundary_contrast_delta_lab",
)

# Strictly automated deploy-time features (excludes post-hoc visual review text flags)
DEPLOY_AUTO_FEATURES: tuple[str, ...] = (
    "log_area_frac",
    "aspect_ratio",
    "center_dist_norm",
    "border_touch",
    "mask_iou",
    "cat_is_transparent_or_glass",
    "cat_is_reflective_appliance_or_metal",
    "cat_is_emissive_or_screen",
    "global_rgb_mae",
    "target_rgb_mae",
    "bg_rgb_mae",
    "target_delta_L",
    "target_delta_ab",
    "target_std_L_ratio",
    "target_ssim",
    "bg_ssim",
    "target_sobel_edge_ratio",
    "target_specular_delta",
    "ring_specular_delta",
    "boundary_contrast_delta",
    "boundary_contrast_delta_lab",
)


def _binary_dilate_box(mask: np.ndarray, radius: int) -> np.ndarray:
    pad = np.pad(mask.astype(np.int32), ((radius, radius), (radius, radius)), mode="constant", constant_values=0)
    win = 2 * radius + 1
    cs = np.pad(pad, ((1, 0), (1, 0)), mode="constant").cumsum(axis=0).cumsum(axis=1)
    sums = cs[win:, win:] - cs[:-win, win:] - cs[win:, :-win] + cs[:-win, :-win]
    return sums > 0


def _sobel_mag(L: np.ndarray) -> np.ndarray:
    p = np.pad(L.astype(np.float64), ((1, 1), (1, 1)), mode="edge")
    gx = (-p[:-2, :-2] + p[:-2, 2:] - 2.0 * p[1:-1, :-2] + 2.0 * p[1:-1, 2:] - p[2:, :-2] + p[2:, 2:]) / 8.0
    gy = (-p[:-2, :-2] - 2.0 * p[:-2, 1:-1] - p[:-2, 2:] + p[2:, :-2] + 2.0 * p[2:, 1:-1] + p[2:, 2:]) / 8.0
    return np.hypot(gx, gy)


def _ssim_map_box(x_gray: np.ndarray, y_gray: np.ndarray, win: int = 8) -> np.ndarray:
    """Compute local win x win SSIM map via integral images on float64 images in [0, 255]."""
    h, w = x_gray.shape
    if h < win or w < win:
        return np.ones((max(1, h - win + 1), max(1, w - win + 1)), dtype=np.float64)

    def _box_mean(arr: np.ndarray) -> np.ndarray:
        cs = np.pad(arr, ((1, 0), (1, 0)), mode="constant").cumsum(axis=0).cumsum(axis=1)
        s = cs[win:, win:] - cs[:-win, win:] - cs[win:, :-win] + cs[:-win, :-win]
        return s / float(win * win)

    mu_x = _box_mean(x_gray)
    mu_y = _box_mean(y_gray)
    var_x = np.maximum(0.0, _box_mean(x_gray * x_gray) - mu_x * mu_x)
    var_y = np.maximum(0.0, _box_mean(y_gray * y_gray) - mu_y * mu_y)
    cov_xy = _box_mean(x_gray * y_gray) - mu_x * mu_y
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2
    num = (2.0 * mu_x * mu_y + c1) * (2.0 * cov_xy + c2)
    den = (mu_x * mu_x + mu_y * mu_y + c1) * (var_x + var_y + c2)
    return np.divide(num, den, out=np.ones_like(num), where=den > 1e-12)


def _infer_optical_flags(
    *,
    source_category: str,
    query: str,
    visual_evidence: str,
) -> dict[str, Any]:
    cat = source_category.strip().lower()
    q_low = query.strip().lower()
    ev_low = visual_evidence.strip().lower()
    text_all = f"{cat} {q_low} {ev_low}"
    cat_q = f"{cat} {q_low}"

    cat_transp = int(
        cat in TRANSPARENT_CATS
        or any(k in cat_q for k in ("glass", "vase", "jar", "pitcher", "wine", "clear"))
    )
    cat_refl = int(
        cat in REFLECTIVE_CATS
        or any(k in cat_q for k in ("metal", "chrome", "steel", "mirror", "ceramic", "porcelain"))
    )
    cat_emiss = int(
        cat in EMISSIVE_CATS
        or any(k in cat_q for k in ("screen", "monitor", "display", "sign", "lamp"))
    )

    ev_transp = int(any(k in text_all for k in ("opaque", "opac", "transpar", "transluc", "glass", "window", "pane", "carafe")))
    ev_refl = int(any(k in text_all for k in ("reflect", "metallic", "gloss", "shiny", "highlight", "polish", "chrome", "faucet", "mirror")))
    ev_emiss = int(any(k in text_all for k in ("emission", "emiss", "screen", "display", "monitor", "signage", "illuminat")))

    is_transp = int(bool(cat_transp or ev_transp))
    is_refl = int(bool(cat_refl or ev_refl))
    is_emiss = int(bool(cat_emiss or ev_emiss))

    if is_transp:
        prior_regime = "Transparent/Glass"
    elif is_emiss:
        prior_regime = "Emissive/Screen"
    elif is_refl:
        prior_regime = "Reflective/Metallic"
    else:
        prior_regime = "Matte/Diffuse"

    return {
        "cat_is_transparent_or_glass": cat_transp,
        "cat_is_reflective_appliance_or_metal": cat_refl,
        "cat_is_emissive_or_screen": cat_emiss,
        "is_transparent_or_glass": is_transp,
        "is_reflective_appliance_or_metal": is_refl,
        "is_emissive_or_screen": is_emiss,
        "prior_optical_regime": prior_regime,
    }


def compute_pair_optical_features(
    *,
    orig_rgb: np.ndarray,
    conv_rgb: np.ndarray,
    orig_mask: np.ndarray,
    conv_mask: np.ndarray,
    source_category: str = "",
    query: str = "",
    visual_evidence: str = "",
) -> dict[str, Any]:
    """Compute interpretable geometry, prior, and paired visual delta features for one pair."""
    h, w = orig_mask.shape
    ys, xs = np.where(orig_mask)
    area_frac = float(np.mean(orig_mask))
    log_area_frac = float(math.log(max(area_frac, 1e-6)))
    if len(xs):
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        bw = float(x1 - x0)
        bh = float(y1 - y0)
        aspect_ratio = bw / max(bh, 1.0)
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))
        center_dist_norm = float(math.hypot(cx - 0.5 * w, cy - 0.5 * h) / max(math.hypot(0.5 * w, 0.5 * h), 1.0))
        border_touch = int(y0 == 0 or y1 == h or x0 == 0 or x1 == w)
    else:
        y0, y1, x0, x1 = 0, h, 0, w
        aspect_ratio = 1.0
        center_dist_norm = 0.0
        border_touch = 0

    inter = int(np.sum(orig_mask & conv_mask))
    union = int(np.sum(orig_mask | conv_mask))
    mask_iou = float(inter / max(union, 1))

    diff_rgb = np.abs(orig_rgb.astype(np.float64) - conv_rgb.astype(np.float64)) / 255.0
    diff_px = diff_rgb.mean(axis=-1)
    global_rgb_mae = float(diff_px.mean())
    target_rgb_mae = float(diff_px[orig_mask].mean()) if np.any(orig_mask) else 0.0
    bg_mask = ~orig_mask
    bg_rgb_mae = float(diff_px[bg_mask].mean()) if np.any(bg_mask) else 0.0

    orig_lab, orig_y = srgb_uint8_to_lab(orig_rgb)
    conv_lab, conv_y = srgb_uint8_to_lab(conv_rgb)

    if np.any(orig_mask):
        ol = orig_lab[orig_mask]
        cl = conv_lab[orig_mask]
        target_delta_L = float(abs(cl[:, 0].mean() - ol[:, 0].mean()))
        target_delta_ab = float(math.hypot(cl[:, 1].mean() - ol[:, 1].mean(), cl[:, 2].mean() - ol[:, 2].mean()))
        target_std_L_ratio = float((cl[:, 0].std() + 1e-4) / (ol[:, 0].std() + 1e-4))
        target_spec_o = float(np.mean(orig_y[orig_mask] > 0.88))
        target_spec_c = float(np.mean(conv_y[orig_mask] > 0.88))
        target_specular_delta = target_spec_c - target_spec_o
    else:
        target_delta_L = 0.0
        target_delta_ab = 0.0
        target_std_L_ratio = 1.0
        target_specular_delta = 0.0

    # Exterior 12-px specular highlight change
    ring_12 = _binary_dilate_box(orig_mask, 12) & (~orig_mask)
    if np.any(ring_12):
        ring_specular_delta = float(np.mean(conv_y[ring_12] > 0.88) - np.mean(orig_y[ring_12] > 0.88))
    else:
        ring_specular_delta = 0.0

    # Contour inner 8px vs outer 8px contrast change
    outer_8 = _binary_dilate_box(orig_mask, 8) & (~orig_mask)
    inner_8 = _binary_dilate_box(~orig_mask, 8) & orig_mask
    in_reg = inner_8 if np.any(inner_8) else orig_mask
    out_reg = outer_8 if np.any(outer_8) else bg_mask
    if np.any(in_reg) and np.any(out_reg):
        in_o = orig_lab[in_reg].mean(axis=0)
        out_o = orig_lab[out_reg].mean(axis=0)
        in_c = conv_lab[in_reg].mean(axis=0)
        out_c = conv_lab[out_reg].mean(axis=0)
        c_o_L = float(abs(in_o[0] - out_o[0]))
        c_c_L = float(abs(in_c[0] - out_c[0]))
        c_o_lab = float(np.linalg.norm(in_o - out_o))
        c_c_lab = float(np.linalg.norm(in_c - out_c))
        boundary_contrast_delta = c_c_L - c_o_L
        boundary_contrast_delta_lab = c_c_lab - c_o_lab
    else:
        boundary_contrast_delta = 0.0
        boundary_contrast_delta_lab = 0.0

    # Local 8x8 SSIM using BT.601 luma gray in [0, 255]
    gray_w = np.array([0.299, 0.587, 0.114], dtype=np.float64)
    g_orig = np.tensordot(orig_rgb.astype(np.float64), gray_w, axes=([-1], [0]))
    g_conv = np.tensordot(conv_rgb.astype(np.float64), gray_w, axes=([-1], [0]))

    full_ssim = _ssim_map_box(g_orig, g_conv, win=8)
    bg_center = bg_mask[3 : h - 4, 3 : w - 4]
    bg_ssim = float(full_ssim[bg_center].mean()) if np.any(bg_center) else float(full_ssim.mean())

    cy0, cy1 = max(0, y0 - 4), min(h, y1 + 4)
    cx0, cx1 = max(0, x0 - 4), min(w, x1 + 4)
    crop_mask = orig_mask[cy0:cy1, cx0:cx1]
    crop_ssim = _ssim_map_box(g_orig[cy0:cy1, cx0:cx1], g_conv[cy0:cy1, cx0:cx1], win=8)
    ch, cw = crop_mask.shape
    if ch >= 8 and cw >= 8:
        mc = crop_mask[3 : ch - 4, 3 : cw - 4]
        target_ssim = float(crop_ssim[mc].mean()) if np.any(mc) else float(crop_ssim.mean())
    else:
        target_ssim = float(crop_ssim.mean())

    # Sobel edge magnitude ratio on Lab L* inside target
    sob_o = _sobel_mag(orig_lab[cy0:cy1, cx0:cx1, 0])
    sob_c = _sobel_mag(conv_lab[cy0:cy1, cx0:cx1, 0])
    if np.any(crop_mask):
        target_sobel_edge_ratio = float((sob_c[crop_mask].mean() + 1e-4) / (sob_o[crop_mask].mean() + 1e-4))
    else:
        target_sobel_edge_ratio = 1.0

    priors = _infer_optical_flags(
        source_category=source_category,
        query=query,
        visual_evidence=visual_evidence,
    )

    # Objective pixel-delta optical grouping (independent of category/text labels)
    if mask_iou < 0.999:
        pixel_optical_regime = "Mask/Opacity-Shift"
    elif target_specular_delta <= -0.02:
        pixel_optical_regime = "Specular-Stripped"
    elif target_sobel_edge_ratio < 0.85 or target_ssim < 0.75:
        pixel_optical_regime = "Texture/Detail-Degraded"
    else:
        pixel_optical_regime = "Low-Distortion"

    return {
        "source_category": source_category,
        "log_area_frac": log_area_frac,
        "aspect_ratio": aspect_ratio,
        "center_dist_norm": center_dist_norm,
        "border_touch": border_touch,
        "mask_iou": mask_iou,
        **priors,
        "pixel_optical_regime": pixel_optical_regime,
        "global_rgb_mae": global_rgb_mae,
        "target_rgb_mae": target_rgb_mae,
        "bg_rgb_mae": bg_rgb_mae,
        "target_delta_L": target_delta_L,
        "target_delta_ab": target_delta_ab,
        "target_std_L_ratio": target_std_L_ratio,
        "target_ssim": target_ssim,
        "bg_ssim": bg_ssim,
        "target_sobel_edge_ratio": target_sobel_edge_ratio,
        "target_specular_delta": target_specular_delta,
        "ring_specular_delta": ring_specular_delta,
        "boundary_contrast_delta": boundary_contrast_delta,
        "boundary_contrast_delta_lab": boundary_contrast_delta_lab,
    }


def _load_visual_evidence_map(reviews_dir: Path) -> dict[tuple[str, str], str]:
    ev_map: dict[tuple[str, str], str] = {}
    if not reviews_dir.is_dir():
        return ev_map
    for jf in sorted(reviews_dir.glob("*.json")):
        data = json.loads(jf.read_text(encoding="utf-8"))
        scene_id = str(data.get("scene_id") or "")
        for tgt in data.get("targets", []):
            prim = str(tgt.get("target_prim") or "")
            ev = str(tgt.get("visual_evidence") or "")
            if scene_id and prim:
                ev_map[(scene_id, prim)] = ev
    return ev_map


def extract_all_pair_features(
    *,
    manifest_path: Path,
    scenes_path: Path,
    reviews_dir: Path,
    out_dir: Path,
    assets_root: Path | None = None,
) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes_raw = json.loads(scenes_path.read_text(encoding="utf-8"))
    split_by_scene = {r["scene_id"]: r["split"] for r in scenes_raw["scenes"]}
    family_by_scene = {r["scene_id"]: r["family"] for r in scenes_raw["scenes"]}
    ev_map = _load_visual_evidence_map(reviews_dir)

    by_pair: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in manifest["records"]:
        by_pair[row["pair_id"]][row["condition"]] = row

    out_dir.mkdir(parents=True, exist_ok=True)
    rows_out: list[dict[str, Any]] = []
    pair_ids = sorted(by_pair)
    for idx, pair_id in enumerate(pair_ids, start=1):
        orig = by_pair[pair_id]["original"]
        conv = by_pair[pair_id]["converted"]
        orig_img_p = resolve_asset_path(orig["image"]["path"], assets_root)
        conv_img_p = resolve_asset_path(conv["image"]["path"], assets_root)
        orig_mask_p = resolve_asset_path(orig["mask"]["path"], assets_root)
        conv_mask_p = resolve_asset_path(conv["mask"]["path"], assets_root)

        with Image.open(orig_img_p) as im_o:
            orig_rgb = np.asarray(im_o.convert("RGB"), dtype=np.uint8)
        with Image.open(conv_img_p) as im_c:
            conv_rgb = np.asarray(im_c.convert("RGB"), dtype=np.uint8)
        orig_mask = np.load(orig_mask_p, allow_pickle=False).astype(bool)
        conv_mask = np.load(conv_mask_p, allow_pickle=False).astype(bool)

        scene_id = orig["scene_id"]
        target_prim = orig["target_prim"]
        feats = compute_pair_optical_features(
            orig_rgb=orig_rgb,
            conv_rgb=conv_rgb,
            orig_mask=orig_mask,
            conv_mask=conv_mask,
            source_category=orig.get("source_category", ""),
            query=orig["query"],
            visual_evidence=ev_map.get((scene_id, target_prim), ""),
        )
        rec = {
            "pair_id": pair_id,
            "scene_id": scene_id,
            "split": split_by_scene.get(scene_id, "unknown"),
            "family": family_by_scene.get(scene_id, "unknown"),
            "target_prim": target_prim,
            "view_id": orig["view_id"],
            "query": orig["query"],
            "visual_evidence": ev_map.get((scene_id, target_prim), ""),
            **feats,
        }
        rows_out.append(rec)
        if idx % 120 == 0 or idx == len(pair_ids):
            print(f"[optical_features] extracted {idx}/{len(pair_ids)} pairs", flush=True)

    json_path = out_dir / "pair_optical_features.json"
    json_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "manifest_sha256": sha256_file(manifest_path),
                "pair_count": len(rows_out),
                "feature_names_all": list(FEATURE_NAMES_ALL),
                "deploy_auto_features": list(DEPLOY_AUTO_FEATURES),
                "records": rows_out,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    csv_path = out_dir / "pair_optical_features.csv"
    fieldnames = [
        "pair_id",
        "scene_id",
        "split",
        "family",
        "target_prim",
        "view_id",
        "source_category",
        "prior_optical_regime",
        "pixel_optical_regime",
        *FEATURE_NAMES_ALL,
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows_out:
            writer.writerow({k: r[k] for k in fieldnames})
    return rows_out


def main() -> int:
    root = repo_root_from_script(Path(__file__))
    raw_v1 = root / "paper/shared/evidence/raw/cviu_formal/v1"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=raw_v1 / "manifest.json")
    parser.add_argument("--scenes", type=Path, default=raw_v1 / "scenes.json")
    parser.add_argument("--reviews-dir", type=Path, default=raw_v1 / "final_visual_reviews")
    parser.add_argument("--out-dir", type=Path, default=root / "paper/shared/evidence/raw/cviu_v3")
    parser.add_argument("--assets-root", type=Path, default=None)
    args = parser.parse_args()

    rows = extract_all_pair_features(
        manifest_path=args.manifest.resolve(),
        scenes_path=args.scenes.resolve(),
        reviews_dir=args.reviews_dir.resolve(),
        out_dir=args.out_dir.resolve(),
        assets_root=args.assets_root.resolve() if args.assets_root else None,
    )
    print(f"[ok] wrote pair_optical_features.json/.csv ({len(rows)} rows) -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

