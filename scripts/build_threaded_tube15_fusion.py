#!/usr/bin/env python3
"""Build real-scale threaded 15 mL body/cap source-bound candidate packages."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
from typing import Any


EXPECTED_SOURCE_SHA256 = "a2bc4b55af223f55c43b8001038990ec30ad08c10ebd632b2859a0ac3d9d4af5"
SOURCE_TUBE = "/World/shiguan/node_/mesh_"
SOURCE_CAP = "/World/cap/node_/mesh_"
SOURCE_SCALE = 0.1
BODY_ENTRY = "/World/TubeBody"
CAP_ENTRY = "/World/Cap"
CAP_ASSEMBLY_Z_M = 0.10799568140775846
OMNIGLASS = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "tube15_single_mesh_final_small_v2_20260825/package/deps/"
    "source_package/deps/mdl/OmniGlass.mdl"
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _source_mesh(stage: Any, prim_path: str, *, origin: tuple[float, float, float]):
    from pxr import Gf, UsdGeom, Vt

    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid() or not prim.IsA(UsdGeom.Mesh):
        raise ValueError(f"source mesh missing: {prim_path}")
    mesh = UsdGeom.Mesh(prim)
    matrix = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    points = []
    for value in mesh.GetPointsAttr().Get() or []:
        world = matrix.Transform(Gf.Vec3d(*map(float, value)))
        points.append(
            Gf.Vec3f(
                float(world[0]) * SOURCE_SCALE - origin[0],
                float(world[1]) * SOURCE_SCALE - origin[1],
                float(world[2]) * SOURCE_SCALE - origin[2],
            )
        )
    normals = []
    for value in mesh.GetNormalsAttr().Get() or []:
        world = matrix.TransformDir(Gf.Vec3d(*map(float, value)))
        length = max(math.sqrt(sum(float(x) ** 2 for x in world)), 1e-12)
        normals.append(Gf.Vec3f(*(float(x) / length for x in world)))
    counts = list(mesh.GetFaceVertexCountsAttr().Get() or [])
    indices = list(mesh.GetFaceVertexIndicesAttr().Get() or [])
    if not points or not counts or not indices:
        raise ValueError(f"source mesh has incomplete topology: {prim_path}")
    minimum = Gf.Vec3f(*(min(float(p[i]) for p in points) for i in range(3)))
    maximum = Gf.Vec3f(*(max(float(p[i]) for p in points) for i in range(3)))
    return {
        "points": Vt.Vec3fArray(points),
        "normals": Vt.Vec3fArray(normals),
        "normal_interpolation": mesh.GetNormalsInterpolation(),
        "counts": counts,
        "indices": indices,
        "extent": Vt.Vec3fArray([minimum, maximum]),
        "bounds": {"minimum": list(minimum), "maximum": list(maximum)},
    }


def _set_sdf(prim: Any, *, contact: float, rest: float) -> None:
    from pxr import Sdf, UsdPhysics

    UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
    UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("sdf")
    existing = list(prim.GetAppliedSchemas())
    for schema in ("PhysxCollisionAPI", "PhysxSDFMeshCollisionAPI"):
        if schema not in existing:
            existing.append(schema)
    prim.SetMetadata(
        "apiSchemas", Sdf.TokenListOp.Create(prependedItems=existing)
    )
    values = {
        "physxCollision:contactOffset": (Sdf.ValueTypeNames.Float, contact),
        "physxCollision:restOffset": (Sdf.ValueTypeNames.Float, rest),
        "physxSDFMeshCollision:sdfResolution": (Sdf.ValueTypeNames.UInt, 512),
        "physxSDFMeshCollision:sdfSubgridResolution": (Sdf.ValueTypeNames.UInt, 6),
        "physxSDFMeshCollision:sdfBitsPerSubgridPixel": (
            Sdf.ValueTypeNames.Token,
            "BitsPerPixel16",
        ),
        "physxSDFMeshCollision:sdfMargin": (Sdf.ValueTypeNames.Float, 0.00035),
        "physxSDFMeshCollision:sdfNarrowBandThickness": (
            Sdf.ValueTypeNames.Float,
            0.00035,
        ),
        "physxSDFMeshCollision:sdfEnableRemeshing": (
            Sdf.ValueTypeNames.Bool,
            False,
        ),
    }
    for name, (type_name, value) in values.items():
        prim.CreateAttribute(name, type_name, custom=True).Set(value)


def _glass_material(stage: Any, root: str):
    from pxr import Sdf, UsdShade

    material = UsdShade.Material.Define(stage, root + "/Looks/TransparentTube")
    shader = UsdShade.Shader.Define(stage, root + "/Looks/TransparentTube/Shader")
    shader.GetPrim().CreateAttribute(
        "info:implementationSource", Sdf.ValueTypeNames.Token
    ).Set("sourceAsset")
    shader.GetPrim().CreateAttribute(
        "info:mdl:sourceAsset", Sdf.ValueTypeNames.Asset
    ).Set(Sdf.AssetPath("deps/mdl/OmniGlass.mdl"))
    shader.GetPrim().CreateAttribute(
        "info:mdl:sourceAsset:subIdentifier", Sdf.ValueTypeNames.Token
    ).Set("OmniGlass")
    output = shader.CreateOutput("out", Sdf.ValueTypeNames.Token)
    for context in ("mdl:surface", "mdl:volume", "mdl:displacement"):
        material.CreateOutput(context, Sdf.ValueTypeNames.Token).ConnectToSource(output)
    return material


def _plastic_material(stage: Any, root: str):
    from pxr import Gf, Sdf, UsdShade

    material = UsdShade.Material.Define(stage, root + "/Looks/PlasticCap")
    shader = UsdShade.Shader.Define(stage, root + "/Looks/PlasticCap/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.16, 0.22, 0.32)
    )
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.38)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _write_asset(
    *,
    path: Path,
    entry: str,
    mesh_data: dict[str, Any],
    mass_kg: float,
    contact: float,
    rest: float,
    glass: bool,
    sdf_resolution: int = 512,
    enhance_thread_contact: bool = False,
) -> None:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

    path.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    root = UsdGeom.Xform.Define(stage, entry).GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(root).CreateRigidBodyEnabledAttr(True)
    UsdPhysics.MassAPI.Apply(root).CreateMassAttr(mass_kg)
    visual = UsdGeom.Mesh.Define(stage, entry + "/Visual")
    visual.CreatePointsAttr(mesh_data["points"])
    visual.CreateFaceVertexCountsAttr(mesh_data["counts"])
    visual.CreateFaceVertexIndicesAttr(mesh_data["indices"])
    visual.CreateExtentAttr(mesh_data["extent"])
    visual.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    if len(mesh_data["normals"]):
        visual.CreateNormalsAttr(mesh_data["normals"])
        visual.SetNormalsInterpolation(mesh_data["normal_interpolation"])
    material = _glass_material(stage, entry) if glass else _plastic_material(stage, entry)
    UsdShade.MaterialBindingAPI.Apply(visual.GetPrim()).Bind(material)
    if not glass:
        # The inherited 15 mL cap profile is an open sleeve. Close the centre
        # with the producer-declared 1.5 mm PP top thickness while keeping the
        # threaded shell unchanged under the same rigid root.
        top_z = float(mesh_data["bounds"]["maximum"][2])
        top = UsdGeom.Cylinder.Define(stage, entry + "/CapTop")
        top.CreateAxisAttr(UsdGeom.Tokens.z)
        top.CreateRadiusAttr(0.00890)
        top.CreateHeightAttr(0.00150)
        top.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, top_z - 0.00075))
        UsdShade.MaterialBindingAPI.Apply(top.GetPrim()).Bind(material)
        UsdPhysics.CollisionAPI.Apply(top.GetPrim()).CreateCollisionEnabledAttr(True)

    collision_points = []
    for point in mesh_data["points"]:
        x, y, z = map(float, point)
        radius = math.hypot(x, y)
        if enhance_thread_contact and glass and 0.092 <= z <= 0.1005 and radius >= 0.00845:
            target = radius + 0.00018
            scale = target / max(radius, 1e-12)
            x *= scale
            y *= scale
        collision_points.append(Gf.Vec3f(x, y, z))
    collision_extent = Vt.Vec3fArray(
        [
            Gf.Vec3f(*(min(float(p[i]) for p in collision_points) for i in range(3))),
            Gf.Vec3f(*(max(float(p[i]) for p in collision_points) for i in range(3))),
        ]
    )
    collision = UsdGeom.Mesh.Define(stage, entry + "/Collision")
    collision.CreatePointsAttr(Vt.Vec3fArray(collision_points))
    collision.CreateFaceVertexCountsAttr(mesh_data["counts"])
    collision.CreateFaceVertexIndicesAttr(mesh_data["indices"])
    collision.CreateExtentAttr(collision_extent)
    collision.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    collision.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
    _set_sdf(collision.GetPrim(), contact=contact, rest=rest)
    collision.GetPrim().GetAttribute("physxSDFMeshCollision:sdfResolution").Set(
        int(sdf_resolution)
    )
    root.SetCustomDataByKey("source_sha256", EXPECTED_SOURCE_SHA256)
    root.SetCustomDataByKey("source_scope", SOURCE_TUBE if glass else SOURCE_CAP)
    stage.GetRootLayer().Save()


def _write_assembly(path: Path) -> None:
    from pxr import Gf, Sdf, Usd, UsdGeom

    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    body = UsdGeom.Xform.Define(stage, BODY_ENTRY).GetPrim()
    body.GetReferences().AddReference("body/package/asset.usda", Sdf.Path(BODY_ENTRY))
    cap = UsdGeom.Xform.Define(stage, CAP_ENTRY)
    cap.GetPrim().GetReferences().AddReference("cap/package/asset.usda", Sdf.Path(CAP_ENTRY))
    cap.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, CAP_ASSEMBLY_Z_M))
    stage.GetRootLayer().Save()


def build_fusion(*, source: Path, out: Path, diagnostic_high_thread_detail: bool = False) -> dict[str, Any]:
    from pxr import Usd

    source = source.resolve()
    out = out.resolve()
    if _sha(source) != EXPECTED_SOURCE_SHA256:
        raise ValueError("threaded source SHA-256 mismatch")
    stage = Usd.Stage.Open(str(source), load=Usd.Stage.LoadAll)
    body = _source_mesh(stage, SOURCE_TUBE, origin=(0.0, 0.0, 0.0))
    cap = _source_mesh(
        stage, SOURCE_CAP, origin=(0.0, 0.0, CAP_ASSEMBLY_Z_M)
    )
    body_path = out / "body/package/asset.usda"
    cap_path = out / "cap/package/asset.usda"
    _write_asset(
        path=body_path,
        entry=BODY_ENTRY,
        mesh_data=body,
        mass_kg=0.015,
        contact=0.00035,
        rest=0.000175,
        glass=True,
        sdf_resolution=1024 if diagnostic_high_thread_detail else 512,
        enhance_thread_contact=diagnostic_high_thread_detail,
    )
    _write_asset(
        path=cap_path,
        entry=CAP_ENTRY,
        mesh_data=cap,
        mass_kg=0.002,
        contact=0.00035 if diagnostic_high_thread_detail else 0.00005,
        rest=0.000175 if diagnostic_high_thread_detail else 0.0,
        glass=False,
    )
    mdl_out = body_path.parent / "deps/mdl/OmniGlass.mdl"
    mdl_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OMNIGLASS, mdl_out)
    _write_assembly(out / "assembly.usda")

    result = {
        "schema_version": "aan.threaded_tube15_fusion_build.v1",
        "source": str(source),
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "source_prims": {"body": SOURCE_TUBE, "cap": SOURCE_CAP},
        "diagnostic_high_thread_detail": diagnostic_high_thread_detail,
        "cap_top": {"status": "closed", "thickness_m": 0.0015, "radius_m": 0.0089},
        "body_dimensions_m": {
            "height": body["bounds"]["maximum"][2] - body["bounds"]["minimum"][2],
            "diameter": max(
                body["bounds"]["maximum"][0] - body["bounds"]["minimum"][0],
                body["bounds"]["maximum"][1] - body["bounds"]["minimum"][1],
            ),
        },
        "cap_dimensions_m": {
            "height": cap["bounds"]["maximum"][2] - cap["bounds"]["minimum"][2],
            "diameter": max(
                cap["bounds"]["maximum"][0] - cap["bounds"]["minimum"][0],
                cap["bounds"]["maximum"][1] - cap["bounds"]["minimum"][1],
            ),
        },
    }
    profile = {
        "schema_version": "aan.threaded_pair_profile.v1",
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "entries": {"body": BODY_ENTRY, "cap": CAP_ENTRY},
        "closed_pose": {"cap_translate_xyz_m": [0.0, 0.0, CAP_ASSEMBLY_Z_M]},
        "thread_semantics": "geometry_contact_no_joint_no_z_trajectory",
        "contact_candidates": [
            {"id": "a", "body_contact_rest_mm": [0.35, 0.175], "cap_contact_rest_mm": [0.05, 0.0]},
            {"id": "b", "body_contact_rest_mm": [0.10, 0.0], "cap_contact_rest_mm": [0.05, 0.0]},
            {"id": "c", "body_contact_rest_mm": [0.05, 0.0], "cap_contact_rest_mm": [0.05, 0.0]},
        ],
        "delivery": {
            "base_assets_include_particles": False,
            "body_package": "body/package",
            "cap_package": "cap/package",
            "assembly": "assembly.usda",
        },
        "forbidden": {
            "bottom_cube": True,
            "overlapping_full_body_sdf": True,
            "hidden_screw_joint": True,
            "prescribed_cap_z_trajectory": True,
        },
        "claims": {"robot_policy_success": False, "benchmark_success": False},
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "build_manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "thread_pair_profile.json").write_text(json.dumps(profile, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--diagnostic-high-thread-detail", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            build_fusion(
                source=args.source,
                out=args.out,
                diagnostic_high_thread_detail=args.diagnostic_high_thread_detail,
            ),
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
