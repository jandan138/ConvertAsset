#!/usr/bin/env python3
"""Build a corrected non-threaded 15 mL neck/cap-fit geometry master."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any


DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "task11_r5_context_assets_20260824/target_tube_r2/package/asset.usd"
)
DEFAULT_OUT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "centrifuge_tube_15ml_nonthreaded_neck_cap_fit_r1_20260828"
)
SOURCE_BODY = (
    "/World/CentrifugeTube15mlClosed/Visual/Source/centrifuge_tube_15ml_red_cap_ROOT/"
    "Tube_Body_Hollow/Tube_Body_Hollow_Mesh"
)
SOURCE_CAP = (
    "/World/CentrifugeTube15mlClosed/Visual/Source/centrifuge_tube_15ml_red_cap_ROOT/"
    "Cap_Controller/Cap_Removable/Cap_Shell_Mesh"
)
BODY_BOTTOM_FIXED_M = 0.0232
SOURCE_NECK_START_M = 0.095
BODY_TOP_M = 0.101
CAP_INNER_BOTTOM_M = 0.10096000134944916
CAP_INNER_TOP_M = 0.11819999665021896
CAP_OUTER_TOP_M = 0.11969999969005585
CAP_INNER_SLEEVE_M = CAP_INNER_TOP_M - CAP_INNER_BOTTOM_M
TARGET_NECK_START_M = BODY_TOP_M - CAP_INNER_SLEEVE_M
CAP_SHIFT_M = BODY_TOP_M - CAP_INNER_TOP_M
CAP_LOCAL_BOTTOM_M = CAP_INNER_BOTTOM_M + CAP_SHIFT_M
BODY_ENTRY = "/Tube15NonThreadedBodyFit"
CAP_ENTRY = "/Tube15NonThreadedCapFit"
ASSEMBLY_ENTRY = "/Tube15NonThreadedNeckCapFit"
BODY_MASS_KG = 0.015
CAP_MASS_KG = 0.004


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def warp_z(z: float) -> float:
    z = float(z)
    if z <= BODY_BOTTOM_FIXED_M:
        return z
    if z <= SOURCE_NECK_START_M:
        scale = (TARGET_NECK_START_M - BODY_BOTTOM_FIXED_M) / (
            SOURCE_NECK_START_M - BODY_BOTTOM_FIXED_M
        )
        return BODY_BOTTOM_FIXED_M + (z - BODY_BOTTOM_FIXED_M) * scale
    scale = (BODY_TOP_M - TARGET_NECK_START_M) / (
        BODY_TOP_M - SOURCE_NECK_START_M
    )
    return TARGET_NECK_START_M + (z - SOURCE_NECK_START_M) * scale


def _z_derivative(z: float) -> float:
    if z <= BODY_BOTTOM_FIXED_M:
        return 1.0
    if z <= SOURCE_NECK_START_M:
        return (TARGET_NECK_START_M - BODY_BOTTOM_FIXED_M) / (
            SOURCE_NECK_START_M - BODY_BOTTOM_FIXED_M
        )
    return (BODY_TOP_M - TARGET_NECK_START_M) / (
        BODY_TOP_M - SOURCE_NECK_START_M
    )


def _mesh_data(stage: Any, path: str, *, body_warp: bool, cap_localize: bool) -> dict:
    from pxr import Gf, UsdGeom, Vt

    prim = stage.GetPrimAtPath(path)
    mesh = UsdGeom.Mesh(prim)
    matrix = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    original_world = [matrix.Transform(Gf.Vec3d(*point)) for point in mesh.GetPointsAttr().Get()]
    points = []
    for point in original_world:
        z = warp_z(point[2]) if body_warp else float(point[2]) + CAP_SHIFT_M
        if cap_localize:
            z -= TARGET_NECK_START_M
        points.append(Gf.Vec3f(float(point[0]), float(point[1]), z))
    indices = list(mesh.GetFaceVertexIndicesAttr().Get())
    normals = []
    for index, normal in enumerate(mesh.GetNormalsAttr().Get() or []):
        transformed = matrix.TransformDir(Gf.Vec3d(*normal))
        point_index = indices[index] if index < len(indices) else 0
        derivative = _z_derivative(original_world[point_index][2]) if body_warp else 1.0
        candidate = Gf.Vec3d(
            float(transformed[0]),
            float(transformed[1]),
            float(transformed[2]) / derivative,
        ).GetNormalized()
        normals.append(Gf.Vec3f(*candidate))
    minimum = [min(float(point[i]) for point in points) for i in range(3)]
    maximum = [max(float(point[i]) for point in points) for i in range(3)]
    return {
        "points": Vt.Vec3fArray(points),
        "counts": list(mesh.GetFaceVertexCountsAttr().Get()),
        "indices": indices,
        "normals": Vt.Vec3fArray(normals),
        "normal_interpolation": mesh.GetNormalsInterpolation(),
        "extent": Vt.Vec3fArray([Gf.Vec3f(*minimum), Gf.Vec3f(*maximum)]),
        "minimum": minimum,
        "maximum": maximum,
    }


def _material(stage: Any, root: str, *, red: bool) -> Any:
    from pxr import Gf, Sdf, UsdShade

    name = "RedCapPP" if red else "TransparentPP"
    material = UsdShade.Material.Define(stage, f"{root}/Looks/{name}")
    shader = UsdShade.Shader.Define(stage, f"{root}/Looks/{name}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    values = (
        {
            "diffuseColor": Gf.Vec3f(0.56, 0.004, 0.008),
            "roughness": 0.42,
            "opacity": 1.0,
        }
        if red
        else {
            "diffuseColor": Gf.Vec3f(0.73, 0.88, 0.92),
            "roughness": 0.20,
            "opacity": 0.30,
        }
    )
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        values["diffuseColor"]
    )
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(values["roughness"])
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(values["opacity"])
    shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.47)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _apply_sdf(prim: Any) -> None:
    from pxr import Sdf, UsdPhysics

    UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
    UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("sdf")
    schemas = list(prim.GetAppliedSchemas())
    for schema in ("PhysxCollisionAPI", "PhysxSDFMeshCollisionAPI"):
        if schema not in schemas:
            schemas.append(schema)
    prim.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(prependedItems=schemas))
    prim.CreateAttribute(
        "physxSDFMeshCollision:sdfResolution", Sdf.ValueTypeNames.UInt
    ).Set(512)
    prim.CreateAttribute(
        "physxSDFMeshCollision:sdfSubgridResolution", Sdf.ValueTypeNames.UInt
    ).Set(6)


def _write_mesh_asset(
    path: Path,
    entry: str,
    data: dict,
    *,
    mass: float,
    center_z: float,
    inertia: tuple[float, float, float],
    red: bool,
) -> None:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade

    path.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    root = UsdGeom.Xform.Define(stage, entry).GetPrim()
    stage.SetDefaultPrim(root)
    UsdPhysics.RigidBodyAPI.Apply(root).CreateRigidBodyEnabledAttr(True)
    mass_api = UsdPhysics.MassAPI.Apply(root)
    mass_api.CreateMassAttr(mass)
    mass_api.CreateCenterOfMassAttr(Gf.Vec3f(0.0, 0.0, center_z))
    mass_api.CreateDiagonalInertiaAttr(Gf.Vec3f(*inertia))
    mass_api.CreatePrincipalAxesAttr(Gf.Quatf(1.0))
    mesh = UsdGeom.Mesh.Define(stage, entry + "/Visual")
    mesh.CreatePointsAttr(data["points"])
    mesh.CreateFaceVertexCountsAttr(data["counts"])
    mesh.CreateFaceVertexIndicesAttr(data["indices"])
    mesh.CreateExtentAttr(data["extent"])
    mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    mesh.CreateNormalsAttr(data["normals"])
    mesh.SetNormalsInterpolation(data["normal_interpolation"])
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(
        _material(stage, entry, red=red)
    )
    _apply_sdf(mesh.GetPrim())
    stage.GetRootLayer().Save()


def _remove_child_physics(prim: Any) -> None:
    from pxr import UsdPhysics

    if prim.HasAPI(UsdPhysics.RigidBodyAPI):
        prim.RemoveAPI(UsdPhysics.RigidBodyAPI)
    if prim.HasAPI(UsdPhysics.MassAPI):
        prim.RemoveAPI(UsdPhysics.MassAPI)


def _write_assembly(path: Path, body_com: float, cap_com: float) -> None:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    root = UsdGeom.Xform.Define(stage, ASSEMBLY_ENTRY).GetPrim()
    stage.SetDefaultPrim(root)
    UsdPhysics.RigidBodyAPI.Apply(root).CreateRigidBodyEnabledAttr(True)
    total_mass = BODY_MASS_KG + CAP_MASS_KG
    combined_com = (
        BODY_MASS_KG * body_com
        + CAP_MASS_KG * (TARGET_NECK_START_M + cap_com)
    ) / total_mass
    mass_api = UsdPhysics.MassAPI.Apply(root)
    mass_api.CreateMassAttr(total_mass)
    mass_api.CreateCenterOfMassAttr(Gf.Vec3f(0.0, 0.0, combined_com))
    mass_api.CreateDiagonalInertiaAttr(Gf.Vec3f(2.2e-5, 2.2e-5, 9.0e-7))
    mass_api.CreatePrincipalAxesAttr(Gf.Quatf(1.0))
    body = UsdGeom.Xform.Define(stage, ASSEMBLY_ENTRY + "/Body")
    body.GetPrim().GetReferences().AddReference("../body/asset.usda", BODY_ENTRY)
    cap = UsdGeom.Xform.Define(stage, ASSEMBLY_ENTRY + "/Cap")
    cap.GetPrim().GetReferences().AddReference("../cap/asset.usda", CAP_ENTRY)
    cap.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, TARGET_NECK_START_M))
    _remove_child_physics(body.GetPrim())
    _remove_child_physics(cap.GetPrim())
    stage.GetRootLayer().Save()


def build(source: Path, output: Path) -> Path:
    from pxr import Usd

    source = source.resolve()
    output = output.resolve()
    source_sha = _sha(source)
    stage = Usd.Stage.Open(str(source), Usd.Stage.LoadAll)
    body = _mesh_data(stage, SOURCE_BODY, body_warp=True, cap_localize=False)
    cap = _mesh_data(stage, SOURCE_CAP, body_warp=False, cap_localize=True)
    body_com = warp_z(0.052)
    cap_com = 0.00937
    staging = output.parent / f".{output.name}.staging"
    if staging.exists():
        shutil.rmtree(staging)
    try:
        _write_mesh_asset(
            staging / "packages/body/asset.usda",
            BODY_ENTRY,
            body,
            mass=BODY_MASS_KG,
            center_z=body_com,
            inertia=(1.15e-5, 1.15e-5, 5.2e-7),
            red=False,
        )
        _write_mesh_asset(
            staging / "packages/cap/asset.usda",
            CAP_ENTRY,
            cap,
            mass=CAP_MASS_KG,
            center_z=cap_com,
            inertia=(1.6e-7, 1.6e-7, 2.2e-7),
            red=True,
        )
        _write_assembly(
            staging / "packages/closed_assembly/asset.usda", body_com, cap_com
        )
        profile = {
            "schema_version": "aan.nonthreaded_tube15_neck_cap_fit.v1",
            "source": {"path": str(source), "sha256": source_sha},
            "body": {
                "total_height_m": BODY_TOP_M,
                "fixed_tip_and_cone_end_m": BODY_BOTTOM_FIXED_M,
                "source_neck_start_m": SOURCE_NECK_START_M,
            },
            "neck": {
                "start_m": TARGET_NECK_START_M,
                "end_m": BODY_TOP_M,
                "length_m": BODY_TOP_M - TARGET_NECK_START_M,
            },
            "cap_inner_sleeve": {
                "start_m": TARGET_NECK_START_M,
                "end_m": BODY_TOP_M,
                "length_m": CAP_INNER_SLEEVE_M,
                "top_closure_thickness_m": CAP_OUTER_TOP_M - CAP_INNER_TOP_M,
            },
            "closed_pose": {
                "cap_translate_z_m": TARGET_NECK_START_M,
                "assembled_top_m": CAP_OUTER_TOP_M + CAP_SHIFT_M,
            },
            "radial_fit": {
                "tube_outer_radius_m": 0.00861,
                "cap_inner_radius_m": 0.00886,
                "single_side_clearance_m": 0.00025,
            },
            "packages": {
                "body": "packages/body/asset.usda",
                "cap": "packages/cap/asset.usda",
                "closed_assembly": "packages/closed_assembly/asset.usda",
            },
            "claims": {
                "neck_matches_effective_cap_sleeve": True,
                "thread_geometry_present": False,
                "existing_task_packages_replaced": False,
                "robot_policy_success": False,
                "task_success": False,
                "benchmark_success": False,
            },
        }
        (staging / "mating_profile.json").write_text(
            json.dumps(profile, indent=2, sort_keys=True) + "\n"
        )
        manifest = {
            "schema_version": "aan.nonthreaded_tube15_neck_cap_fit_asset_set.v1",
            "status": "candidate_runtime_pending",
            "blocked_reasons": ["three Isaac Sim 4.1 cold starts pending"],
            "source_sha256": source_sha,
            "assets": profile["packages"],
            "claims": profile["claims"],
        }
        (staging / "asset_set_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
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
