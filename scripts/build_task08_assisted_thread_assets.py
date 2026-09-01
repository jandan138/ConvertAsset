#!/usr/bin/env python3
"""Build smooth-collider wrappers for Task 08 assisted cap tightening."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
from typing import Any


SOURCE_SET = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "scientific_workbench_task08_r12_assets_20260901"
)
DEFAULT_OUT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "scientific_workbench_task08_assisted_thread_r2_20260902"
)
TUBE_SOURCE_PACKAGE = "tube15_long_neck_threaded_body_glass_v1_2"
CAP_SOURCE_PACKAGE = "tube15_long_neck_threaded_closed_cap_red_v1_2"
TUBE_PACKAGE = "tube15_long_neck_assisted_thread_body_r2"
CAP_PACKAGE = "tube15_long_neck_assisted_thread_cap_r2"
TUBE_ENTRY = "/World/Tube15LongNeckThreadedBody"
CAP_ENTRY = "/World/Tube15LongNeckThreadedClosedCap"
CONTACT_OFFSET_M = 0.0002
REST_OFFSET_M = 0.0


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _set_identity_xform(xform: Any) -> None:
    from pxr import Gf

    xform.AddTranslateOp().Set(Gf.Vec3d(0.0))
    xform.AddOrientOp().Set(Gf.Quatf(1.0))
    xform.AddScaleOp().Set(Gf.Vec3d(1.0))


def _make_collider(geom: Any) -> None:
    from pxr import Sdf, UsdGeom, UsdPhysics

    prim = geom.GetPrim()
    UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
    prim.CreateAttribute(
        "physxCollision:contactOffset", Sdf.ValueTypeNames.Float
    ).Set(CONTACT_OFFSET_M)
    prim.CreateAttribute(
        "physxCollision:restOffset", Sdf.ValueTypeNames.Float
    ).Set(REST_OFFSET_M)
    UsdGeom.Imageable(prim).CreateVisibilityAttr(UsdGeom.Tokens.invisible)


def _cylinder(
    stage: Any,
    path: str,
    *,
    radius: float,
    height: float,
    z: float,
) -> None:
    from pxr import Gf, UsdGeom

    geom = UsdGeom.Cylinder.Define(stage, path)
    geom.CreateAxisAttr(UsdGeom.Tokens.z)
    geom.CreateRadiusAttr(radius)
    geom.CreateHeightAttr(height)
    geom.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, z))
    _make_collider(geom)


def _box(
    stage: Any,
    path: str,
    *,
    xyz: tuple[float, float, float],
    size_xyz: tuple[float, float, float],
    yaw_deg: float,
) -> Any:
    from pxr import Gf, UsdGeom

    geom = UsdGeom.Cube.Define(stage, path)
    geom.CreateSizeAttr(1.0)
    geom.AddTranslateOp().Set(Gf.Vec3d(*xyz))
    geom.AddRotateZOp().Set(yaw_deg)
    geom.AddScaleOp().Set(Gf.Vec3d(*size_xyz))
    _make_collider(geom)
    return geom


def _grasp_material(stage: Any, entry: str) -> Any:
    from pxr import Sdf, UsdShade

    material = UsdShade.Material.Define(stage, entry + "/__aan_grasp_material")
    prim = material.GetPrim()
    prim.SetMetadata(
        "apiSchemas",
        Sdf.TokenListOp.Create(
            prependedItems=["PhysicsMaterialAPI", "PhysxMaterialAPI"]
        ),
    )
    prim.CreateAttribute("physics:staticFriction", Sdf.ValueTypeNames.Float).Set(1.0)
    prim.CreateAttribute("physics:dynamicFriction", Sdf.ValueTypeNames.Float).Set(0.9)
    prim.CreateAttribute("physics:restitution", Sdf.ValueTypeNames.Float).Set(0.0)
    prim.CreateAttribute(
        "physxMaterial:frictionCombineMode", Sdf.ValueTypeNames.Token
    ).Set("max")
    return material


def _build_wrapper(
    package: Path,
    *,
    source_package: Path,
    dep_name: str,
    entry: str,
    role: str,
) -> dict[str, Any]:
    from pxr import Sdf, Usd, UsdGeom, UsdShade

    dep = package / "deps" / dep_name
    shutil.copytree(source_package, dep)
    stage = Usd.Stage.CreateNew(str(package / "asset.usd"))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    stage.DefinePrim("/World", "Xform")
    root = UsdGeom.Xform.Define(stage, entry)
    root.GetPrim().GetReferences().AddReference(
        f"deps/{dep_name}/asset.usd", entry
    )
    stage.SetDefaultPrim(root.GetPrim())
    detailed = stage.OverridePrim(entry + "/node_/mesh_")
    detailed.CreateAttribute(
        "physics:collisionEnabled", Sdf.ValueTypeNames.Bool
    ).Set(False)
    proxy_root = UsdGeom.Xform.Define(stage, entry + "/__aan_collision_proxy")
    proxy_root.GetPrim().CreateAttribute(
        "scenarioForge:interactionRole", Sdf.ValueTypeNames.Token
    ).Set(role)
    if role == "tube_body":
        _cylinder(
            stage,
            entry + "/__aan_collision_proxy/body",
            radius=0.00725,
            height=0.082,
            z=0.052,
        )
        _cylinder(
            stage,
            entry + "/__aan_collision_proxy/neck",
            radius=0.00820,
            height=0.010,
            z=0.096,
        )
        tube_grasp = _box(
            stage,
            entry + "/__aan_collision_proxy/grasp_box",
            xyz=(0.0, 0.0, 0.085),
            size_xyz=(0.018, 0.018, 0.018),
            yaw_deg=0.0,
        )
        tube_grasp.GetPrim().CreateAttribute(
            "scenarioForge:graspOnly", Sdf.ValueTypeNames.Bool
        ).Set(False)
        UsdShade.MaterialBindingAPI.Apply(tube_grasp.GetPrim()).Bind(
            _grasp_material(stage, entry), materialPurpose="physics"
        )
    else:
        segment_count = 12
        ring_radius = 0.00972
        radial_thickness = 0.00130
        tangent_width = (
            2.0 * ring_radius * math.tan(math.pi / segment_count) * 1.04
        )
        for index in range(segment_count):
            theta = 360.0 * index / segment_count
            radians = math.radians(theta)
            _box(
                stage,
                entry + f"/__aan_collision_proxy/shell_{index:02d}",
                xyz=(
                    ring_radius * math.cos(radians),
                    ring_radius * math.sin(radians),
                    -0.0004,
                ),
                size_xyz=(tangent_width, radial_thickness, 0.0172),
                yaw_deg=theta - 90.0,
            )
        _cylinder(
            stage,
            entry + "/__aan_collision_proxy/top",
            radius=0.0102,
            height=0.0016,
            z=0.0085,
        )
        for collider_name in (
            *(f"shell_{index:02d}" for index in range(segment_count)),
            "top",
        ):
            stage.GetPrimAtPath(
                entry + "/__aan_collision_proxy/" + collider_name
            ).GetAttribute("physics:collisionEnabled").Set(False)
        grasp = _box(
            stage,
            entry + "/__aan_collision_proxy/grasp_box",
            xyz=(0.0, 0.0, 0.0),
            size_xyz=(0.018, 0.018, 0.014),
            yaw_deg=0.0,
        )
        grasp.GetPrim().CreateAttribute(
            "scenarioForge:graspOnly", Sdf.ValueTypeNames.Bool
        ).Set(True)
        UsdShade.MaterialBindingAPI.Apply(grasp.GetPrim()).Bind(
            _grasp_material(stage, entry), materialPurpose="physics"
        )
    stage.GetRootLayer().Save()
    colliders = [
        str(prim.GetPath())
        for prim in stage.Traverse()
        if prim.GetAttribute("physics:collisionEnabled").Get() is True
    ]
    return {
        "schema_version": "aan.task08_assisted_thread_proxy.v1",
        "entrypoint": entry,
        "source": {
            "package": str(source_package),
            "asset_sha256": _sha(source_package / "asset.usd"),
            "copied_asset_sha256": _sha(dep / "asset.usd"),
        },
        "visual_geometry_changed": False,
        "detailed_thread_collision_enabled": False,
        "proxy_colliders": colliders,
        "contact_offset_m": CONTACT_OFFSET_M,
        "rest_offset_m": REST_OFFSET_M,
        "grasp_proxy": (
            None
            if role == "tube_body"
            else {
                "relative_path": "__aan_collision_proxy/grasp_box",
                "disable_state": "capture",
                "size_xyz_m": [0.018, 0.018, 0.014],
                "initial_collision_mode": "pickup_box_only",
                "capture_collision_mode": "smooth_shell_only",
            }
        ),
        "claim_boundary": (
            "Smooth collision candidate for assisted VR threading; does not claim "
            "fine-thread contact, robot policy success, or benchmark success."
        ),
    }


def build(output: Path = DEFAULT_OUT, source_set: Path = SOURCE_SET) -> Path:
    output = output.resolve()
    source_set = source_set.resolve()
    index = json.loads((source_set / "asset_set_manifest.json").read_text())
    if index.get("status") != "pass":
        raise RuntimeError("Task08 r12 source asset set is not promoted")
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    staging = output.parent / f".{output.name}.staging"
    if staging.exists():
        shutil.rmtree(staging)
    try:
        packages = staging / "packages"
        tube_package = packages / TUBE_PACKAGE
        cap_package = packages / CAP_PACKAGE
        tube_package.mkdir(parents=True)
        cap_package.mkdir(parents=True)
        tube_profile = _build_wrapper(
            tube_package,
            source_package=source_set / "packages" / TUBE_SOURCE_PACKAGE,
            dep_name="tube",
            entry=TUBE_ENTRY,
            role="tube_body",
        )
        cap_profile = _build_wrapper(
            cap_package,
            source_package=source_set / "packages" / CAP_SOURCE_PACKAGE,
            dep_name="cap",
            entry=CAP_ENTRY,
            role="cap_shell",
        )
        _write_json(tube_package / "interaction/profile.json", tube_profile)
        _write_json(cap_package / "interaction/profile.json", cap_profile)
        manifest = {
            "schema_version": "aan.task08_assisted_thread_asset_set.v1",
            "status": "candidate_runtime_pending",
            "source_set": str(source_set),
            "packages": {
                "tube": f"packages/{TUBE_PACKAGE}",
                "cap": f"packages/{CAP_PACKAGE}",
            },
            "interaction_contract": {
                "visual_thread_preserved": True,
                "fine_thread_contact_enabled": False,
                "smooth_proxy_collision": True,
                "grasp_proxy_collision_path": "__aan_collision_proxy/grasp_box",
                "tube_grasp_proxy_collision_path": "__aan_collision_proxy/grasp_box",
                "grasp_proxy_disable_state": "capture",
                "effective_lead_m_per_turn": 0.0076,
                "physical_thread_contact_claimed": False,
            },
            "claims": {
                "proxy_geometry_authored": True,
                "thread_interaction_ready": False,
                "robot_policy_success": False,
                "benchmark_success": False,
            },
        }
        _write_json(staging / "asset_set_manifest.json", manifest)
        staging.rename(output)
        return output
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-set", type=Path, default=SOURCE_SET)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(build(args.out, args.source_set))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
