#!/usr/bin/env python3
"""Build the Task11 r7 tube with separate insertion and Lift2 grasp materials."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    ROOT / "outputs/task11_r5_context_assets_20260824/target_tube_r2/package"
)
DEFAULT_OUT = ROOT / "outputs/task11_r7_target_tube_grasp_20260824/package"
ENTRY = "/World/CentrifugeTube15mlClosed"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def build(source: Path, output: Path) -> Path:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

    source = source.resolve()
    output = output.resolve()
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(source, output)

    asset = output / "asset.usd"
    stage = Usd.Stage.Open(str(asset))
    cap_path = f"{ENTRY}/__aan_collision_proxy/cap"
    body_path = f"{ENTRY}/__aan_collision_proxy/body"
    insertion_material_path = f"{ENTRY}/__aan_labspin_insert_material"
    cap = stage.GetPrimAtPath(cap_path)
    body = stage.GetPrimAtPath(body_path)
    insertion_material = stage.GetPrimAtPath(insertion_material_path)
    if not cap or not body or not insertion_material:
        raise RuntimeError("expected split proxies and insertion material")
    cap.CreateAttribute(
        "physics:collisionEnabled", Sdf.ValueTypeNames.Bool
    ).Set(False)
    grasp_box_path = f"{ENTRY}/__aan_collision_proxy/cap_grasp_box"
    grasp_box = UsdGeom.Cube.Define(stage, grasp_box_path)
    grasp_box.CreateSizeAttr(1.0)
    grasp_box.CreateVisibilityAttr("invisible")
    grasp_box.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.11033))
    grasp_box.AddScaleOp().Set(Gf.Vec3f(0.019, 0.019, 0.018))
    UsdPhysics.CollisionAPI.Apply(grasp_box.GetPrim())
    grasp_box.GetPrim().CreateAttribute(
        "physxCollision:contactOffset", Sdf.ValueTypeNames.Float
    ).Set(0.001)
    grasp_box.GetPrim().CreateAttribute(
        "physxCollision:restOffset", Sdf.ValueTypeNames.Float
    ).Set(0.0)

    grasp = UsdShade.Material.Define(stage, f"{ENTRY}/__aan_lift2_grasp_material")
    grasp_prim = grasp.GetPrim()
    grasp_prim.SetMetadata(
        "apiSchemas",
        Sdf.TokenListOp.Create(
            prependedItems=["PhysicsMaterialAPI", "PhysxMaterialAPI"]
        ),
    )
    grasp_prim.CreateAttribute(
        "physics:staticFriction", Sdf.ValueTypeNames.Float
    ).Set(1.0)
    grasp_prim.CreateAttribute(
        "physics:dynamicFriction", Sdf.ValueTypeNames.Float
    ).Set(0.9)
    grasp_prim.CreateAttribute(
        "physics:restitution", Sdf.ValueTypeNames.Float
    ).Set(0.0)
    grasp_prim.CreateAttribute(
        "physxMaterial:frictionCombineMode", Sdf.ValueTypeNames.Token
    ).Set("max")
    UsdShade.MaterialBindingAPI.Apply(grasp_box.GetPrim()).Bind(
        grasp, materialPurpose="physics"
    )

    frames = UsdGeom.Scope.Define(stage, f"{ENTRY}/__frames")
    grasp_frame = UsdGeom.Xform.Define(
        stage, f"{frames.GetPath()}/lift2_upper_side_grasp"
    )
    grasp_frame.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.11033))
    stage.GetRootLayer().Save()

    profile_path = output / "interaction/profile.json"
    previous = json.loads(profile_path.read_text(encoding="utf-8"))
    profile = {
        **previous,
        "schema_version": "aan.interaction_contract.v2",
        "profile_id": (
            "scientific_workbench.centrifuge_tube_15ml_closed."
            "labspin_insert_lift2_grasp.r2"
        ),
        "revision": "r4-inscribed-flat-cap-grasp-proxy",
        "collision_role_bindings": {"body": "insertion", "cap": "grasp"},
        "insertion_material": {
            "static_friction": 0.05,
            "dynamic_friction": 0.05,
            "friction_combine_mode": "min",
        },
        "grasp_material": {
            "static_friction": 1.0,
            "dynamic_friction": 0.9,
            "friction_combine_mode": "max",
            "restitution": 0.0,
            "bound_collision_prim": grasp_box_path,
        },
        "named_grasp_frames": {
            "lift2_upper_side_grasp": {
                "prim": str(grasp_frame.GetPath()),
                "translation_root_local_m": [0.0, 0.0, 0.11033],
                "approach_axis_root_local": [0.0, -1.0, 0.0],
            }
        },
        "visual_geometry_mass_and_liquid_collision_inherited_unchanged": True,
        "grasp_contact_offset_m": 0.001,
        "insertion_body_contact_offset_m": 0.0001,
        "cap_grasp_proxy": {
            "type": "inscribed_cube",
            "size_xyz_m": [0.019, 0.019, 0.018],
            "source_cap_cylinder_enabled": False,
        },
    }
    _write_json(profile_path, profile)

    manifest_path = output / "evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "package_id": "task11_target_15ml_pbd_ready_grasp_r4_isaac41",
            "overall_status": "candidate_pending_runtime",
            "blocked_reasons": ["isaac41_close_lift_hold_not_run"],
            "asset_usd_sha256": _sha(asset),
            "source_package": str(source),
            "source_asset_usd_sha256": _sha(source / "asset.usd"),
        }
    )
    manifest.setdefault("claims", {}).update(
        {
            "target_slot_insertion": True,
            "split_insertion_and_grasp_materials": True,
            "fixed_candidate_close_lift_hold": False,
            "robot_policy_success": False,
        }
    )
    _write_json(manifest_path, manifest)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(build(args.source, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
