"""Build and MuJoCo4-verify all 8 M1 v0.3 sculpted dual-mesh + PBR deformable asset bundles."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from convert_asset.deformable_v03 import V03_ASSET_SPECS, build_v03_bundle  # noqa: E402


ARTIFACT_ROOT = Path(
    r"C:\Users\Administrator\.gemini\antigravity\brain\2833f00c-81d5-45e3-842f-b50f4070bffb"
)
RAW_TEXTURES_DIR = _REPO_ROOT / "external_artifacts" / "deformable_v03_textures" / "raw"
BUNDLES_ROOT = _REPO_ROOT / "external_artifacts" / "deformable_v03_bundles"


def stage_ai_raw_textures() -> dict[str, str]:
    """Copy latest AI-generated raw albedo textures from artifact directory into raw_textures/."""
    from PIL import Image

    RAW_TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
    staged: dict[str, str] = {}
    for spec in V03_ASSET_SPECS.values():
        dst = RAW_TEXTURES_DIR / spec.raw_texture_name
        if dst.is_file():
            staged[spec.raw_texture_name] = str(dst)
            continue
        stem = spec.raw_texture_name.replace(".png", "")
        cands = sorted(ARTIFACT_ROOT.glob(f"{stem}*.*"), key=lambda p: p.stat().st_mtime)
        if cands:
            src = cands[-1]
            Image.open(src).convert("RGB").save(dst, format="PNG")
            staged[spec.raw_texture_name] = str(src)
    return staged


def main() -> int:
    staged = stage_ai_raw_textures()
    print(f"Staged {len(staged)}/{len(V03_ASSET_SPECS)} AI raw albedo textures into {RAW_TEXTURES_DIR}")
    summaries: dict[str, object] = {}
    for asset_id in V03_ASSET_SPECS:
        b_dir = BUNDLES_ROOT / asset_id
        manifest = build_v03_bundle(
            asset_id,
            b_dir,
            raw_textures_dir=RAW_TEXTURES_DIR,
            tex_size=1024,
            run_mujoco_probe=True,
        )
        summaries[asset_id] = {
            "family": manifest["source"]["structural_family"],
            "skin_mode": manifest["skinning"]["mode"],
            "max_rest_skin_err_m": manifest["skinning"]["max_rest_skin_err_m"],
            "n_vis_tris": manifest["skinning"]["n_vis_tris"],
            "mujoco4_probe": manifest["mujoco4_probe"],
            "ai_texture": manifest["source"]["ai_texture_source"],
        }
        print(asset_id, json.dumps(summaries[asset_id]))
    summary_path = BUNDLES_ROOT / "m1_v03_bundles_summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

