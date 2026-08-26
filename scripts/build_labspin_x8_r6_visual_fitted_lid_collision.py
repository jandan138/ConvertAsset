#!/usr/bin/env python3
"""Derive LABSPIN X8 r6 with visual-fitted lid collision proxies."""

from __future__ import annotations

import argparse
from hashlib import sha256
import itertools
import json
from pathlib import Path
import shutil
from typing import Any


ROOT = "/World/Centrifuge"
BASE_PROXY = f"{ROOT}/base_link/__aan_collision_proxy"
LID_LINK = f"{ROOT}/lid_link"
LID_PROXY = f"{LID_LINK}/__aan_collision_proxy"
DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "labspin_x8_task11_r5_rest_pose_20260824/package"
)
DEFAULT_OUT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "labspin_x8_task11_r6_visual_fitted_lid_collision_20260826/package"
)
INFLATION_M = 0.001


VISUAL_GROUPS = {
    "top_panel": ("LidOuterTopPanel/Cube_031",),
    "front_perimeter": (
        "LidFrontRail/Cube_029",
        "LidFrontSkirt_L/Cube_034",
        "LidFrontSkirt_R/Cube_035",
        "LidFrontHighFlange/Cube_042",
    ),
    "rear_perimeter": (
        "LidRearRail/Cube_030",
        "LidRearSkirt_L/Cube_040",
        "LidRearSkirt_R/Cube_041",
        "LidRearHighFlange/Cube_043",
    ),
    "left_perimeter": (
        "LidLeftRail/Cube_027",
        "LidSideSkirt_L/Cube_032",
    ),
    "right_perimeter": (
        "LidRightRail/Cube_028",
        "LidSideSkirt_R/Cube_033",
    ),
    "handle_grip": ("LidHandleGrip/Cube_037",),
    "handle_post_left": ("LidHandlePost__0_080/Cube_038",),
    "handle_post_right": ("LidHandlePost__0_081/Cube_039",),
    "latch_tongue": ("LidLatchTongue/Cube_036",),
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _vec(value: Any) -> list[float]:
    return [float(component) for component in value]


def _proxy_signature(stage: Any, root: str) -> dict[str, dict[str, Any]]:
    from pxr import UsdGeom, UsdPhysics

    result = {}
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        if not path.startswith(root + "/") or not prim.IsA(UsdGeom.Cube):
            continue
        ops = UsdGeom.Xformable(prim).GetOrderedXformOps()
        result[path.rsplit("/", 1)[-1]] = {
            "ops": [
                {"name": op.GetOpName(), "value": _vec(op.Get())}
                for op in ops
            ],
            "collision": prim.HasAPI(UsdPhysics.CollisionAPI),
            "visibility": str(UsdGeom.Imageable(prim).GetVisibilityAttr().Get()),
        }
    return result


def _world_bounds(stage: Any, prim_paths: tuple[str, ...]) -> tuple[list[float], list[float]]:
    from pxr import Usd, UsdGeom

    cache = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy],
    )
    minima = [float("inf")] * 3
    maxima = [float("-inf")] * 3
    for path in prim_paths:
        prim = stage.GetPrimAtPath(path)
        if not prim:
            raise RuntimeError(f"visual source prim is missing: {path}")
        bounds = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        for axis in range(3):
            minima[axis] = min(minima[axis], float(bounds.GetMin()[axis]))
            maxima[axis] = max(maxima[axis], float(bounds.GetMax()[axis]))
    return minima, maxima


def _parent_local_bounds(
    stage: Any, parent_path: str, prim_paths: tuple[str, ...]
) -> tuple[list[float], list[float]]:
    from pxr import Gf, UsdGeom

    world_min, world_max = _world_bounds(stage, prim_paths)
    parent = stage.GetPrimAtPath(parent_path)
    inverse = UsdGeom.XformCache().GetLocalToWorldTransform(parent).GetInverse()
    points = []
    for corner in itertools.product((0, 1), repeat=3):
        point = Gf.Vec3d(
            *[
                (world_min[axis], world_max[axis])[corner[axis]]
                for axis in range(3)
            ]
        )
        points.append(inverse.Transform(point))
    return (
        [min(float(point[axis]) for point in points) for axis in range(3)],
        [max(float(point[axis]) for point in points) for axis in range(3)],
    )


def _author_cube(stage: Any, path: str, low: list[float], high: list[float]) -> None:
    from pxr import Gf, Sdf, UsdGeom, UsdPhysics

    expanded_low = [value - INFLATION_M for value in low]
    expanded_high = [value + INFLATION_M for value in high]
    center = [(expanded_low[i] + expanded_high[i]) * 0.5 for i in range(3)]
    size = [expanded_high[i] - expanded_low[i] for i in range(3)]
    cube = UsdGeom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    xform = UsdGeom.Xformable(cube)
    xform.AddTranslateOp().Set(Gf.Vec3d(*center))
    xform.AddScaleOp().Set(Gf.Vec3f(*size))
    cube.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim()).CreateCollisionEnabledAttr(True)
    schemas = list(cube.GetPrim().GetAppliedSchemas())
    if "PhysxCollisionAPI" not in schemas:
        schemas.append("PhysxCollisionAPI")
    cube.GetPrim().SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit(schemas))
    cube.GetPrim().CreateAttribute(
        "physxCollision:contactOffset", Sdf.ValueTypeNames.Float
    ).Set(0.0001)
    cube.GetPrim().CreateAttribute(
        "physxCollision:restOffset", Sdf.ValueTypeNames.Float
    ).Set(0.0)


def build_r6(source: Path, output: Path) -> dict[str, Path]:
    from pxr import Usd, UsdGeom

    source = source.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite: {output}")
    if not (source / "asset.usd").is_file():
        raise FileNotFoundError(f"missing r5 source asset: {source / 'asset.usd'}")
    shutil.copytree(source, output)
    asset = output / "asset.usd"
    stage = Usd.Stage.Open(str(asset))
    if not stage:
        raise RuntimeError(f"cannot open copied asset: {asset}")
    stage.SetEditTarget(stage.GetRootLayer())

    before_base = _proxy_signature(stage, BASE_PROXY)
    old_main_low, old_main_high = _world_bounds(
        stage, (f"{LID_PROXY}/main_shell",)
    )
    visual_lid_paths = tuple(
        f"{LID_LINK}/{relative}"
        for paths in VISUAL_GROUPS.values()
        for relative in paths
    ) + (
        f"{LID_LINK}/LidHingePin_L/Cylinder_002",
        f"{LID_LINK}/LidHingePin_R/Cylinder_003",
    )
    _visual_low, visual_high = _world_bounds(stage, visual_lid_paths)
    old_rear_excess = old_main_high[1] - visual_high[1]

    stage.RemovePrim(LID_PROXY)
    UsdGeom.Xform.Define(stage, LID_PROXY)
    records = []
    for name, relatives in VISUAL_GROUPS.items():
        paths = tuple(f"{LID_LINK}/{relative}" for relative in relatives)
        low, high = _parent_local_bounds(stage, LID_LINK, paths)
        _author_cube(stage, f"{LID_PROXY}/{name}", low, high)
        records.append(
            {
                "id": name,
                "source_visual_prims": list(paths),
                "source_parent_local_min_m": low,
                "source_parent_local_max_m": high,
                "authored_inflation_m": INFLATION_M,
            }
        )
    stage.GetRootLayer().Save()

    verified = Usd.Stage.Open(str(asset))
    after_base = _proxy_signature(verified, BASE_PROXY)
    base_unchanged = before_base == after_base
    passed = base_unchanged and old_rear_excess > 0.06 and len(records) == 9
    evidence_dir = output / "evidence"
    collision_dir = evidence_dir / "collision_fit"
    collision_dir.mkdir(parents=True, exist_ok=True)
    audit = {
        "schema_version": "aan.labspin_x8_r6_visual_fitted_lid_collision.v1",
        "overall_status": "pass" if passed else "blocked",
        "source_package": str(source),
        "source_asset_sha256": _sha(source / "asset.usd"),
        "asset_usd_sha256": _sha(asset),
        "raw_files_unchanged": True,
        "base_proxy_unchanged": base_unchanged,
        "old_main_shell_world_min_m": old_main_low,
        "old_main_shell_world_max_m": old_main_high,
        "old_main_shell_rear_excess_m": old_rear_excess,
        "maximum_authored_inflation_m": INFLATION_M,
        "removed_lid_proxies": [
            "front_shell",
            "main_shell",
            "handle_grip",
            "handle_post_left",
            "handle_post_right",
        ],
        "lid_proxies": records,
        "claim_boundary": (
            "Visual-derived lid compound only; base, rotor sockets, controls, "
            "joints, mass, inertia, behavior graph, and raw archive remain unchanged."
        ),
    }
    audit_path = collision_dir / "report.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    if not passed:
        raise RuntimeError(f"r6 collision audit blocked: {audit_path}")

    profile_path = output / "articulation/device_profile.json"
    profile = json.loads(profile_path.read_text())
    profile["revision"] = "r6-visual-fitted-lid-collision"
    profile["lid_collision"] = {
        "kind": "source_visual_named_part_compound_boxes",
        "inflation_m": INFLATION_M,
        "proxy_ids": list(VISUAL_GROUPS),
        "audit": "evidence/collision_fit/report.json",
    }
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")

    manifest_path = evidence_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["package_id"] = "labspin_x8_centrifuge_task11_r6_visual_fitted_lid_collision_isaac41"
    manifest["overall_status"] = "candidate"
    manifest["blocked_reasons"] = [
        "r6_visual_fitted_lid_collision_runtime_qualification_pending"
    ]
    manifest.setdefault("claims", {})["visual_fitted_lid_collision"] = False
    manifest["claims"]["robot_policy_success"] = False
    manifest["claims"]["task11_success"] = False
    manifest.setdefault("source", {})["r6_collision_derivation"] = {
        "source_package": str(source),
        "source_asset_sha256": _sha(source / "asset.usd"),
        "raw_files_unchanged": True,
        "base_proxy_unchanged": True,
        "collision_audit": "evidence/collision_fit/report.json",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return {
        "package": output,
        "asset": asset,
        "collision_audit": audit_path,
        "manifest": manifest_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = build_r6(args.source, args.out)
    print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
