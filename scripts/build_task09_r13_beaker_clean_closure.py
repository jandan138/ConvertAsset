#!/usr/bin/env python3
"""Produce a clean-closure copy of the admitted 325 mL SDF beaker."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "scientific_workbench_beaker_325ml_sdf_web_standard_20260824/package"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/task09_r13_beaker_325ml_sdf_clean_closure_r2_20260831"
STALE_PATH = (
    "/data/teleop/assets/scenes/task02_r10_3_colleague_collision_unvalidated/"
    "variants/fill20/vr/deps/transfer/deps/target_visual/deps/mdl/OmniGlass.mdl"
)


@dataclass(frozen=True)
class CleanBeakerResult:
    output: Path
    package: Path
    receipt: Path


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def build_clean_beaker(
    output: Path = DEFAULT_OUTPUT,
    *,
    source_package: Path = SOURCE_PACKAGE,
) -> CleanBeakerResult:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdUtils

    output = output.resolve()
    source_package = source_package.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    package = output / "package"
    shutil.copytree(source_package, package)
    source_layer = package / "deps/source/obj_beaker_sdf.usd"
    stage = Usd.Stage.Open(str(source_layer))
    if stage is None:
        raise RuntimeError("cannot open package-local beaker source")
    shader = stage.GetPrimAtPath(
        "/Root/obj_beaker/__aan_visual_materials/WebStandardClearBorosilicate/Shader"
    )
    attribute = shader.GetAttribute("info:mdl:sourceAsset")
    value = attribute.Get()
    if not isinstance(value, Sdf.AssetPath) or value.path != STALE_PATH:
        raise ValueError("reviewed stale OmniGlass path did not match")
    attribute.Set(Sdf.AssetPath("../mdl/OmniGlass.mdl"))
    collision_mesh = UsdGeom.Mesh(
        stage.GetPrimAtPath(
            "/Root/obj_beaker/__aan_pbd_collision_proxy/PBD_Unified_Vessel_Mesh"
        )
    )
    collision_mesh.GetNormalsAttr().Set([Gf.Vec3f(0.0, 0.0, 1.0)])
    collision_mesh.SetNormalsInterpolation(UsdGeom.Tokens.constant)
    stage.GetRootLayer().Save()
    _layers, _assets, unresolved = UsdUtils.ComputeAllDependencies(
        str(package / "asset.usd")
    )
    if unresolved:
        raise RuntimeError(f"beaker dependency closure remains unresolved: {unresolved}")
    receipt = output / "promotion_receipt.json"
    _write_json(
        receipt,
        {
            "schema_version": "aan.dependency_closure_promotion_receipt.v1",
            "status": "promoted",
            "asset_id": "task09_r13_beaker_325ml_sdf_clean_closure",
            "source_asset_sha256": _sha(source_package / "asset.usd"),
            "package_asset_sha256": _sha(package / "asset.usd"),
            "rewritten_package_local_source": "deps/source/obj_beaker_sdf.usd",
            "rewritten_path": "../mdl/OmniGlass.mdl",
            "original_package_unchanged": True,
            "claims": {
                "dependency_closure": True,
                "hydra_collision_proxy_normals_compatible": True,
                "dynamic_graspable_sdf": True,
                "liquid_particles_included": False,
                "robot_policy_success": False,
                "benchmark_success": False,
            },
        },
    )
    return CleanBeakerResult(output=output, package=package, receipt=receipt)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-package", type=Path, default=SOURCE_PACKAGE)
    args = parser.parse_args(argv)
    print(build_clean_beaker(args.output, source_package=args.source_package).receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
