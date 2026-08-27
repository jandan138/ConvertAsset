#!/usr/bin/env python3
"""Build a one-rigid-body threaded 15 mL tube with a fixed red closed cap."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_wangshuai_funnel_tube15_dynamic_asset_set import (  # noqa: E402
    _rotation_matrix_to_quaternion,
)


DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "wangshuai_funnel_tube15_dynamic_asset_set_20260827"
)
DEFAULT_OUT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "threaded_tube15_red_closed_assembly_20260827"
)
PACKAGE_ID = "threaded_tube15_red_closed_assembly"
ENTRY_PRIM = "/ThreadedTube15RedClosed"
CAP_CLOSED_Z_M = 0.1074
CAP_CLOSED_YAW_DEG = 255.0
RED_CAP = {
    "diffuse_color": [0.56, 0.004, 0.008],
    "roughness": 0.42,
    "ior": 1.47,
    "metallic": 0.0,
    "opacity": 1.0,
    "specular": 0.5,
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _quaternion_matrix(wxyz: list[float]) -> np.ndarray:
    w, x, y, z = (float(value) for value in wxyz)
    return np.asarray(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=float,
    )


def _rotation_z(degrees: float) -> np.ndarray:
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return np.asarray([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def combined_mass_properties(body: dict[str, Any], cap: dict[str, Any]) -> dict[str, Any]:
    entries = []
    for profile, placement_rotation, placement_translation in (
        (body, np.eye(3), np.zeros(3)),
        (cap, _rotation_z(CAP_CLOSED_YAW_DEG), np.asarray([0.0, 0.0, CAP_CLOSED_Z_M])),
    ):
        mass = float(profile["mass_kg"])
        local_center = np.asarray(profile["center_of_mass_body_local_m"], dtype=float)
        center = placement_rotation @ local_center + placement_translation
        axes = placement_rotation @ _quaternion_matrix(profile["principal_axes_wxyz"])
        inertia = axes @ np.diag(profile["diagonal_inertia_kg_m2"]) @ axes.T
        entries.append((mass, center, inertia))
    mass = sum(item[0] for item in entries)
    center = sum(item[0] * item[1] for item in entries) / mass
    inertia = np.zeros((3, 3), dtype=float)
    for item_mass, item_center, item_inertia in entries:
        offset = item_center - center
        inertia += item_inertia + item_mass * (
            np.dot(offset, offset) * np.eye(3) - np.outer(offset, offset)
        )
    values, vectors = np.linalg.eigh(inertia)
    if np.linalg.det(vectors) < 0.0:
        vectors[:, 0] *= -1.0
    return {
        "mass_kg": mass,
        "center_of_mass_body_local_m": center.tolist(),
        "diagonal_inertia_kg_m2": values.tolist(),
        "principal_axes_wxyz": _rotation_matrix_to_quaternion(vectors),
        "method": "parallel_axis_merge_of_provisional_body_and_cap_profiles",
    }


def _author_red_material(stage: Any) -> Any:
    from pxr import Gf, Sdf, UsdShade

    material = UsdShade.Material.Define(stage, ENTRY_PRIM + "/Looks/RedCapPP")
    shader = UsdShade.Shader.Define(stage, ENTRY_PRIM + "/Looks/RedCapPP/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(*RED_CAP["diffuse_color"])
    )
    for name in ("roughness", "ior", "metallic", "opacity", "specular"):
        shader.CreateInput(name, Sdf.ValueTypeNames.Float).Set(float(RED_CAP[name]))
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _remove_child_rigid_body(prim: Any) -> None:
    from pxr import UsdPhysics

    if prim.HasAPI(UsdPhysics.RigidBodyAPI):
        prim.RemoveAPI(UsdPhysics.RigidBodyAPI)
    if prim.HasAPI(UsdPhysics.MassAPI):
        prim.RemoveAPI(UsdPhysics.MassAPI)


def build(source: Path, output: Path) -> Path:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

    source = source.resolve()
    output = output.resolve()
    index_path = source / "asset_set_manifest.json"
    index = json.loads(index_path.read_text())
    if index.get("status") != "pass" or index.get("default_consumption") != "dynamic":
        raise RuntimeError("dynamic Wangshuai source set is not promoted")
    body_source = source / "packages/tube15_threaded_liquid_dynamic"
    cap_source = source / "packages/tube15_threaded_closed_cap_dynamic"
    body_profile = json.loads((body_source / "physics/profile.json").read_text())[
        "mass_properties"
    ]
    cap_profile = json.loads((cap_source / "physics/profile.json").read_text())[
        "mass_properties"
    ]
    mass = combined_mass_properties(body_profile, cap_profile)

    staging = output.parent / f".{output.name}.staging"
    if staging.exists():
        shutil.rmtree(staging)
    package = staging / "packages" / PACKAGE_ID
    package.mkdir(parents=True)
    try:
        shutil.copytree(body_source, package / "deps/body")
        shutil.copytree(cap_source, package / "deps/cap")
        asset = package / "asset.usda"
        stage = Usd.Stage.CreateNew(str(asset))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        root = UsdGeom.Xform.Define(stage, ENTRY_PRIM).GetPrim()
        stage.SetDefaultPrim(root)
        rigid = UsdPhysics.RigidBodyAPI.Apply(root)
        rigid.CreateRigidBodyEnabledAttr(True)
        mass_api = UsdPhysics.MassAPI.Apply(root)
        mass_api.CreateMassAttr(float(mass["mass_kg"]))
        mass_api.CreateDensityAttr(0.0)
        mass_api.CreateCenterOfMassAttr(Gf.Vec3f(*mass["center_of_mass_body_local_m"]))
        mass_api.CreateDiagonalInertiaAttr(Gf.Vec3f(*mass["diagonal_inertia_kg_m2"]))
        quaternion = mass["principal_axes_wxyz"]
        mass_api.CreatePrincipalAxesAttr(
            Gf.Quatf(quaternion[0], Gf.Vec3f(*quaternion[1:]))
        )
        body = UsdGeom.Xform.Define(stage, ENTRY_PRIM + "/Body")
        body.GetPrim().GetReferences().AddReference(
            "deps/body/asset.usda", "/Tube15ThreadedLiquidReady"
        )
        cap = UsdGeom.Xform.Define(stage, ENTRY_PRIM + "/Cap")
        cap.GetPrim().GetReferences().AddReference(
            "deps/cap/asset.usda", "/Tube15ThreadedClosedCap"
        )
        cap.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, CAP_CLOSED_Z_M))
        cap.AddRotateZOp().Set(CAP_CLOSED_YAW_DEG)
        cap.GetPrim().CreateAttribute(
            "scenarioForge:closedYawDegrees", Sdf.ValueTypeNames.Double
        ).Set(CAP_CLOSED_YAW_DEG)
        cap.GetPrim().CreateAttribute(
            "scenarioForge:closureState", Sdf.ValueTypeNames.Token
        ).Set("fixed_closed")
        _remove_child_rigid_body(body.GetPrim())
        _remove_child_rigid_body(cap.GetPrim())
        red = _author_red_material(stage)
        cap_mesh = stage.GetPrimAtPath(ENTRY_PRIM + "/Cap/node_/mesh_")
        if not cap_mesh:
            raise RuntimeError("composed closed-cap mesh is missing")
        UsdShade.MaterialBindingAPI.Apply(cap_mesh).Bind(red)
        stage.GetRootLayer().Save()

        profile_dir = package / "physics"
        profile_dir.mkdir()
        profile = {
            "schema_version": "aan.physics_profile.v1",
            "profile_id": "wangshuai.tube15_threaded_red_closed.single_rigid.v1",
            "revision": "v1",
            "motion_role": "dynamic",
            "effective_kinematic": False,
            "quality_tier": "provisional_geometry",
            "mass_properties": mass,
            "replacement_contract": "replace the complete profile in a new revision",
        }
        profile_path = profile_dir / "profile.json"
        profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")
        evidence = package / "evidence"
        evidence.mkdir()
        manifest = {
            "schema_version": "aan.threaded_tube15_red_closed_assembly.v1",
            "package_id": PACKAGE_ID,
            "overall_status": "candidate_runtime_pending",
            "blocked_reasons": ["three Isaac Sim 4.1 cold starts pending"],
            "entrypoints": {
                "root_usd": "asset.usda",
                "default_prim": "ThreadedTube15RedClosed",
                "asset_entry_prim": ENTRY_PRIM,
            },
            "sources": {
                "asset_set_manifest": str(index_path),
                "asset_set_manifest_sha256": _sha(index_path),
                "body_asset_sha256": _sha(body_source / "asset.usda"),
                "cap_asset_sha256": _sha(cap_source / "asset.usda"),
            },
            "closed_pose": {
                "cap_translate_xyz_m": [0.0, 0.0, CAP_CLOSED_Z_M],
                "cap_yaw_deg": CAP_CLOSED_YAW_DEG,
                "basis": "scaled_source_gravity_seated_phase",
            },
            "cap_material": RED_CAP,
            "physics_profile": {
                "path": "physics/profile.json",
                "sha256": _sha(profile_path),
                "quality_tier": "provisional_geometry",
            },
            "claims": {
                "single_rigid_body_closed_assembly": True,
                "closed_top_source_geometry": True,
                "cap_fixed_to_body": True,
                "source_collision_geometry_unchanged": True,
                "red_cap_visual_override": True,
                "dynamic_runtime_qualified": False,
                "target_slot_insertion": False,
                "cap_tightening_task_success": False,
                "robot_policy_success": False,
                "task_success": False,
                "benchmark_success": False,
            },
        }
        manifest_path = evidence / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        asset_set = {
            "schema_version": "aan.threaded_tube15_red_closed_asset_set.v1",
            "status": "candidate_runtime_pending",
            "default_consumption": "dynamic_single_rigid_body",
            "assets": [
                {
                    "id": PACKAGE_ID,
                    "package": f"packages/{PACKAGE_ID}",
                    "entry_usd": f"packages/{PACKAGE_ID}/asset.usda",
                    "entry_prim": ENTRY_PRIM,
                    "overall_status": "candidate_runtime_pending",
                    "producer_manifest": f"packages/{PACKAGE_ID}/evidence/manifest.json",
                }
            ],
            "claims": manifest["claims"],
        }
        (staging / "asset_set_manifest.json").write_text(
            json.dumps(asset_set, indent=2, sort_keys=True) + "\n"
        )
        if output.exists():
            shutil.rmtree(output)
        staging.rename(output)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
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
