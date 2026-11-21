#!/usr/bin/env python3
"""Build the compact source-bound Task 09 oven-cart static-support candidate."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Sequence
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from convert_asset.asset_application_normalizer.model import (  # noqa: E402
    NormalizeAssetRequest,
)
from convert_asset.asset_application_normalizer.pipeline import (  # noqa: E402
    normalize_asset,
)


DEFAULT_ARCHIVE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_xinyu/glovebox_frame_florence_flask_6_samples_simready.zip"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/task09_r13_compact_oven_cart_20260831"
ARCHIVE_SHA256 = "3668cfb94d06da553c6ed54e43bf8cfb8155b2335f6712d885a5ab66ff1f3989"
CANDIDATE = "input_01_seed_250103"
SOURCE_USD_MEMBER = f"simready/{CANDIDATE}/{CANDIDATE}.usdc"
VISUAL_USD_MEMBER = f"visual_usd/{CANDIDATE}/model.usdc"
TEXTURE_MEMBERS = (
    f"visual_usd/{CANDIDATE}/textures/textured_mesh.jpg",
    f"visual_usd/{CANDIDATE}/textures/"
    "textured_mesh_metallic-textured_mesh_roughness.png",
)
SOURCE_HASHES = {
    SOURCE_USD_MEMBER: "3bf68ff435d7b3a642e1d432893a22bfcdd8835812a9477de0ac19e56488a1d9",
    VISUAL_USD_MEMBER: "64da0bad12e54e241ecb5d7e6d741fe59a86e589f980d52932249567f06b66af",
    TEXTURE_MEMBERS[0]: "f0241a405afb7e1d1267d5f8f4ae4a96165f25ed2a8c06716c84d0ebd538693b",
    TEXTURE_MEMBERS[1]: "903726d0b258189383d29f2b3666eea6668809001e59b8366c179c6312377633",
}
TARGET_DIMENSIONS_M = (0.9, 0.76, 0.755)


@dataclass(frozen=True)
class CartBuildResult:
    output: Path
    asset_usd: Path
    manifest: Path


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _map_x(value: float) -> float:
    if value <= -0.75:
        return value + 0.35
    if value >= 0.75:
        return value - 0.35
    return value * (0.4 / 0.75)


def _map_z(value: float) -> float:
    if value <= 0.02:
        return value
    return 0.02 + (value - 0.02) * (0.735 / 0.72)


def _rewrite_visual(path: Path) -> None:
    from pxr import Gf, Usd, UsdGeom

    stage = Usd.Stage.Open(str(path))
    if stage is None:
        raise RuntimeError("cannot open compact-cart visual source")
    meshes = [prim for prim in stage.Traverse() if prim.IsA(UsdGeom.Mesh)]
    if len(meshes) != 1:
        raise ValueError(f"expected one reviewed visual mesh, found {len(meshes)}")
    mesh = UsdGeom.Mesh(meshes[0])
    points = mesh.GetPointsAttr().Get()
    rewritten = [
        Gf.Vec3f(_map_x(float(point[0])), float(point[1]), _map_z(float(point[2])))
        for point in points
    ]
    mesh.GetPointsAttr().Set(rewritten)
    minimum = Gf.Vec3f(
        min(point[0] for point in rewritten),
        min(point[1] for point in rewritten),
        min(point[2] for point in rewritten),
    )
    maximum = Gf.Vec3f(
        max(point[0] for point in rewritten),
        max(point[1] for point in rewritten),
        max(point[2] for point in rewritten),
    )
    mesh.CreateExtentAttr().Set([minimum, maximum])
    stage.GetRootLayer().Save()


def _rewrite_colliders(path: Path) -> None:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    stage = Usd.Stage.Open(str(path))
    if stage is None:
        raise RuntimeError("cannot open compact-cart physics source")
    colliders = [
        prim for prim in stage.Traverse() if prim.HasAPI(UsdPhysics.CollisionAPI)
    ]
    if len(colliders) != 16:
        raise ValueError(f"expected 16 producer colliders, found {len(colliders)}")
    for prim in colliders:
        translate_attr = prim.GetAttribute("xformOp:translate")
        translate = translate_attr.Get()
        x = _map_x(float(translate[0]))
        z = _map_z(float(translate[2]))
        if prim.GetTypeName() == "Cube":
            scale_attr = prim.GetAttribute("xformOp:scale")
            scale = scale_attr.Get()
            x_min = _map_x(float(translate[0]) - float(scale[0]))
            x_max = _map_x(float(translate[0]) + float(scale[0]))
            z_min = _map_z(float(translate[2]) - float(scale[2]))
            z_max = _map_z(float(translate[2]) + float(scale[2]))
            x = (x_min + x_max) * 0.5
            z = (z_min + z_max) * 0.5
            scale_attr.Set(
                Gf.Vec3f(
                    (x_max - x_min) * 0.5,
                    float(scale[1]),
                    (z_max - z_min) * 0.5,
                )
            )
        translate_attr.Set(Gf.Vec3d(x, float(translate[1]), z))

    support = UsdGeom.Cube.Define(stage, "/ObjectRoot/__aan_support_surface")
    support.CreateSizeAttr(2.0)
    support.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.735))
    support.AddScaleOp().Set(Gf.Vec3f(0.42, 0.36, 0.02))
    support.CreateVisibilityAttr().Set(UsdGeom.Tokens.invisible)
    UsdPhysics.CollisionAPI.Apply(support.GetPrim()).CreateCollisionEnabledAttr(True)
    support.GetPrim().SetCustomDataByKey("aan:role", "oven_load_support_surface")
    stage.GetRootLayer().Save()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def build_cart(
    output: Path = DEFAULT_OUTPUT,
    *,
    archive: Path = DEFAULT_ARCHIVE,
) -> CartBuildResult:
    output = output.resolve()
    archive = archive.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    if _sha(archive) != ARCHIVE_SHA256:
        raise ValueError("source archive SHA-256 mismatch")
    input_root = output / "input"
    derived = input_root / "derived"
    input_root.mkdir(parents=True)
    shutil.copy2(archive, input_root / "source.zip")
    with ZipFile(archive) as bundle:
        for member, expected in SOURCE_HASHES.items():
            data = bundle.read(member)
            if sha256(data).hexdigest() != expected:
                raise ValueError(f"archive member SHA-256 mismatch: {member}")
            destination = derived / member
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)

    visual_path = derived / VISUAL_USD_MEMBER
    source_path = derived / SOURCE_USD_MEMBER
    _rewrite_visual(visual_path)
    _rewrite_colliders(source_path)

    facade = input_root / "compact_cart_source.usda"
    facade.write_text(
        f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)
def Xform "World"
{{
    def Xform "OvenCart" (
        prepend references = @./derived/{SOURCE_USD_MEMBER}@</ObjectRoot>
    )
    {{
    }}
}}
''',
        encoding="utf-8",
    )
    profile = input_root / "static_support_profile.json"
    _write_json(
        profile,
        {
            "schema_version": "aan.static_support_profile.v1",
            "profile_id": "scientific_workbench.task09_r13.compact_oven_cart",
            "revision": "r1",
            "source_binding": {"sha256": _sha(facade)},
            "asset_entry_prim": "/World/OvenCart",
            "collider_policy": "prefer_source_then_proxy",
            "source_collider_prim": "/World/OvenCart/__aan_support_surface",
            "proxy": {
                "prim_path": "/World/OvenCart/__aan_support_surface",
                "center_xyz": [0.0, 0.0, 0.735],
                "size_xyz": [0.84, 0.72, 0.04],
            },
            "support_surface": {
                "top_z": 0.755,
                "x_range": [-0.42, 0.42],
                "y_range": [-0.36, 0.36],
                "edge_band_m": 0.04,
            },
            "physics_material": {
                "prim_path": "/World/OvenCart/__aan_static_support_material",
                "static_friction": 0.6,
                "dynamic_friction": 0.5,
                "restitution": 0.0,
                "friction_combine_mode": "max",
                "restitution_combine_mode": "multiply",
                "calibration_status": "provisional_unmeasured",
            },
        },
    )
    package = output / "package"
    request = NormalizeAssetRequest(
        source_usd=facade,
        out_dir=package,
        asset_id="scientific_workbench_task09_r13_compact_oven_cart",
        asset_class="static_support",
        asset_role="static_support",
        source_runtime="generic_usd",
        target_runtime="isaac41",
        target_benchmark="scenario-forge",
        task_id="ScientificWorkbench.Task09.OvenCart",
        required_prims=["/World/OvenCart"],
        asset_scope_prims=["/World/OvenCart"],
        material_policy="native-or-mirror",
        static_support_profile=profile,
        gates=["static"],
        evidence_out=package / "evidence/manifest.json",
    )
    normalized = normalize_asset(request)
    if normalized.return_code != 0:
        raise RuntimeError("AAN static-support normalization did not pass")
    manifest_path = package / "evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["overall_status"] = "candidate_runtime_qualification_pending"
    manifest["source_derivation"] = {
        "archive_sha256": ARCHIVE_SHA256,
        "source_candidate": CANDIDATE,
        "source_member_sha256": SOURCE_HASHES,
        "target_dimensions_m": list(TARGET_DIMENSIONS_M),
        "x_warp": "preserve_50mm_side_members_shorten_center_span",
        "z_warp": "feet_fixed_top_surface_to_0p755m",
        "original_archive_unchanged": True,
    }
    manifest["claims"] = {
        "static_support_geometry_candidate": True,
        "oven_load_support_qualified": False,
        "robot_policy_success": False,
        "benchmark_success": False,
    }
    _write_json(manifest_path, manifest)
    return CartBuildResult(
        output=output,
        asset_usd=package / "asset.usd",
        manifest=manifest_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    print(build_cart(args.output, archive=args.archive).manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
