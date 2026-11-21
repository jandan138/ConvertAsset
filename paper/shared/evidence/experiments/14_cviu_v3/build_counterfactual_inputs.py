#!/usr/bin/env python3
"""Build pixel-exact 480-pair counterfactual images (target_only, background_only, photometric_matched)."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v3_common import (  # noqa: E402
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    lab_to_srgb_uint8,
    repo_root_from_script,
    resolve_asset_path,
    sanitize_pair_id,
    sha256_file,
    srgb_uint8_to_lab,
)


CONDITIONS: tuple[str, ...] = ("target_only", "background_only", "photometric_matched")


def affine_lab_match(
    src_rgb: np.ndarray,
    ref_rgb: np.ndarray,
    region_mask: np.ndarray,
    *,
    std_floor: float = 1e-4,
) -> np.ndarray:
    """Match per-region CIE Lab mean & std of src_rgb to ref_rgb on mask and ~mask."""
    src_lab, _ = srgb_uint8_to_lab(src_rgb)
    ref_lab, _ = srgb_uint8_to_lab(ref_rgb)
    out_lab = src_lab.copy()
    for region in (region_mask, ~region_mask):
        if not np.any(region):
            continue
        for ch in range(3):
            s_vals = src_lab[region, ch]
            r_vals = ref_lab[region, ch]
            mu_s = float(np.mean(s_vals))
            sd_s = float(np.std(s_vals))
            mu_r = float(np.mean(r_vals))
            sd_r = float(np.std(r_vals))
            if sd_s > std_floor:
                out_lab[region, ch] = ((s_vals - mu_s) / sd_s) * sd_r + mu_r
            else:
                out_lab[region, ch] = mu_r
    out_lab[..., 0] = np.clip(out_lab[..., 0], 0.0, 100.0)
    out_lab[..., 1:] = np.clip(out_lab[..., 1:], -128.0, 127.0)
    return lab_to_srgb_uint8(out_lab)


def synthesize_counterfactual_arrays(
    orig_rgb: np.ndarray,
    conv_rgb: np.ndarray,
    orig_mask: np.ndarray,
    conv_mask: np.ndarray,
) -> dict[str, np.ndarray]:
    """Synthesize target_only, background_only, and photometric_matched RGB arrays."""
    target_only = np.where(conv_mask[..., None], conv_rgb, orig_rgb).astype(np.uint8)
    background_only = np.where(orig_mask[..., None], orig_rgb, conv_rgb).astype(np.uint8)
    photometric_matched = affine_lab_match(orig_rgb, conv_rgb, orig_mask)
    return {
        "target_only": target_only,
        "background_only": background_only,
        "photometric_matched": photometric_matched,
    }


def build_counterfactual_dataset(
    *,
    manifest_path: Path,
    out_dir: Path,
    assets_root: Path | None = None,
    skip_hash_check: bool = False,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_pair: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in manifest["records"]:
        by_pair[row["pair_id"]][row["condition"]] = row

    out_dir.mkdir(parents=True, exist_ok=True)
    records_out: list[dict[str, Any]] = []
    pair_ids = sorted(by_pair)
    for idx, pair_id in enumerate(pair_ids, start=1):
        pair_map = by_pair[pair_id]
        orig = pair_map["original"]
        conv = pair_map["converted"]

        orig_img_p = resolve_asset_path(orig["image"]["path"], assets_root)
        conv_img_p = resolve_asset_path(conv["image"]["path"], assets_root)
        orig_mask_p = resolve_asset_path(orig["mask"]["path"], assets_root)
        conv_mask_p = resolve_asset_path(conv["mask"]["path"], assets_root)

        if not skip_hash_check:
            if sha256_file(orig_img_p) != orig["image"]["sha256"]:
                raise ValueError(f"Original image hash mismatch: {orig_img_p}")
            if sha256_file(conv_img_p) != conv["image"]["sha256"]:
                raise ValueError(f"Converted image hash mismatch: {conv_img_p}")
            if sha256_file(orig_mask_p) != orig["mask"]["sha256"]:
                raise ValueError(f"Original mask hash mismatch: {orig_mask_p}")
            if sha256_file(conv_mask_p) != conv["mask"]["sha256"]:
                raise ValueError(f"Converted mask hash mismatch: {conv_mask_p}")

        with Image.open(orig_img_p) as im_o:
            orig_rgb = np.asarray(im_o.convert("RGB"), dtype=np.uint8)
        with Image.open(conv_img_p) as im_c:
            conv_rgb = np.asarray(im_c.convert("RGB"), dtype=np.uint8)
        orig_mask = np.load(orig_mask_p, allow_pickle=False).astype(bool)
        conv_mask = np.load(conv_mask_p, allow_pickle=False).astype(bool)
        h, w = orig_mask.shape
        if orig_rgb.shape[:2] != (h, w) or conv_rgb.shape[:2] != (h, w) or conv_mask.shape != (h, w):
            raise ValueError(f"Dimension mismatch on pair {pair_id}")

        exact_mask_match = bool(np.array_equal(orig_mask, conv_mask))
        arrays = synthesize_counterfactual_arrays(orig_rgb, conv_rgb, orig_mask, conv_mask)
        safe_pair = sanitize_pair_id(pair_id)

        for cond in CONDITIONS:
            cond_dir = out_dir / "images" / cond
            cond_dir.mkdir(parents=True, exist_ok=True)
            img_out_path = cond_dir / f"{safe_pair}.png"
            if not img_out_path.is_file():
                Image.fromarray(arrays[cond]).save(img_out_path, compress_level=1)
            mask_ref = conv["mask"] if cond == "target_only" else orig["mask"]
            mask_resolved = conv_mask_p if cond == "target_only" else orig_mask_p
            records_out.append(
                {
                    "pair_id": pair_id,
                    "condition": cond,
                    "scene_id": orig["scene_id"],
                    "target_prim": orig["target_prim"],
                    "view_id": orig["view_id"],
                    "query": orig["query"],
                    "source_category": orig.get("source_category", ""),
                    "exact_mask_match": exact_mask_match,
                    "image": {
                        "path": str(img_out_path.resolve()),
                        "sha256": sha256_file(img_out_path),
                        "width": int(w),
                        "height": int(h),
                    },
                    "mask": {
                        "path": str(mask_resolved.resolve()),
                        "sha256": mask_ref["sha256"],
                        "pixels": int(mask_ref["pixels"]),
                    },
                    "source_original_image_sha256": orig["image"]["sha256"],
                    "source_converted_image_sha256": conv["image"]["sha256"],
                }
            )

        if idx % 80 == 0 or idx == len(pair_ids):
            print(f"[build_counterfactuals] synthesized {idx}/{len(pair_ids)} pairs ({len(records_out)} records)", flush=True)

    out_manifest = {
        "schema_version": 1,
        "status": "frozen_counterfactual_inputs",
        "source_manifest": str(manifest_path),
        "source_manifest_sha256": sha256_file(manifest_path),
        "pair_count": len(pair_ids),
        "conditions": list(CONDITIONS),
        "records": records_out,
    }
    manifest_out_path = out_dir / "counterfactual_manifest.json"
    manifest_out_path.write_text(json.dumps(out_manifest, indent=2) + "\n", encoding="utf-8")
    return out_manifest


def main() -> int:
    root = repo_root_from_script(Path(__file__))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=root / "paper/shared/evidence/raw/cviu_formal/v1/manifest.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("/tmp/cviu_v3_work/counterfactuals"),
    )
    parser.add_argument("--assets-root", type=Path, default=None)
    parser.add_argument("--skip-hash-check", action="store_true")
    args = parser.parse_args()

    out = build_counterfactual_dataset(
        manifest_path=args.manifest.resolve(),
        out_dir=args.out_dir.resolve(),
        assets_root=args.assets_root.resolve() if args.assets_root else None,
        skip_hash_check=args.skip_hash_check,
    )
    print(f"[ok] wrote counterfactual_manifest.json with {len(out['records'])} records -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

