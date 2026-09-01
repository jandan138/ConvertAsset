#!/usr/bin/env python3
"""Build Task 08 r12 producer-owned rack and threaded-tube visual variants."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "outputs/scientific_workbench_task08_r12_assets_20260901"
DEFAULT_RACK = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "task11_r5_context_assets_20260824/mixed_rack_r2/package"
)
DEFAULT_TUBE_SET = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "tube15_long_neck_threaded_geometry_v1_1_20260901"
)
OMNI_GLASS = Path(
    "/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/"
    "embodied-eval-os-sim-isaacsim41-genmanip-py310/lib/python3.10/"
    "site-packages/omni/mdl/core/Base/OmniGlass.mdl"
)
OMNI_GLASS_OPACITY = OMNI_GLASS.with_name("OmniGlass_Opacity.mdl")
RACK_SCALE = (1.1, 1.1, 1.3)
BODY_ENTRY = "/World/Tube15LongNeckThreadedBody"
CAP_ENTRY = "/World/Tube15LongNeckThreadedClosedCap"
BODY_PACKAGE = "tube15_long_neck_threaded_body_glass_v1_2"
CAP_PACKAGE = "tube15_long_neck_threaded_closed_cap_red_v1_2"
RACK_PACKAGE = "mixed_rack_18plus4_scaled_sdf_r3"
RED_CAP = {
    "diffuse_color": [0.56, 0.004, 0.008],
    "roughness": 0.42,
    "ior": 1.47,
    "metallic": 0.0,
    "opacity": 1.0,
    "specular": 0.5,
}
GLASS_INPUTS = {
    "cutout_opacity": ("float", 0.0),
    "depth": ("float", 0.002),
    "enable_opacity": ("bool", False),
    "frosting_roughness": ("float", 0.035),
    "glass_color": ("color3f", [0.99, 0.998, 1.0]),
    "glass_ior": ("float", 1.47),
    "reflection_color": ("color3f", [1.0, 1.0, 1.0]),
    "roughness_texture_influence": ("float", 1.0),
    "thin_walled": ("bool", False),
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return path


def _copy_package(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination)


def _scale_vector(value: Any) -> tuple[float, float, float]:
    return tuple(float(value[index]) * RACK_SCALE[index] for index in range(3))


def _bake_rack(package: Path) -> None:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

    asset = package / "asset.usd"
    stage = Usd.Stage.Open(str(asset))
    root = stage.GetDefaultPrim()
    UsdGeom.Xformable(root).ClearXformOpOrder()
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath(str(root.GetPath()) + "/Cube_015"))
    points = [_scale_vector(point) for point in mesh.GetPointsAttr().Get()]
    mesh.GetPointsAttr().Set([Gf.Vec3f(*point) for point in points])
    minimum = [min(point[index] for point in points) for index in range(3)]
    maximum = [max(point[index] for point in points) for index in range(3)]
    mesh.CreateExtentAttr([Gf.Vec3f(*minimum), Gf.Vec3f(*maximum)])
    normals_attr = mesh.GetNormalsAttr()
    normals = normals_attr.Get() if normals_attr else None
    if normals:
        converted = []
        for normal in normals:
            values = [float(normal[index]) / RACK_SCALE[index] for index in range(3)]
            length = math.sqrt(sum(value * value for value in values)) or 1.0
            converted.append(Gf.Vec3f(*(value / length for value in values)))
        normals_attr.Set(converted)
    frames = stage.GetPrimAtPath(str(root.GetPath()) + "/__frames")
    for prim in Usd.PrimRange(frames):
        if prim == frames:
            continue
        attr = prim.GetAttribute("xformOp:translate")
        if attr and attr.HasAuthoredValueOpinion():
            attr.Set(Gf.Vec3d(*_scale_vector(attr.Get())))
    proxy_path = str(root.GetPath()) + "/__aan_collision_proxy"
    stage.RemovePrim(proxy_path)
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr("sdf")
    schemas = list(mesh.GetPrim().GetAppliedSchemas())
    for name in ("PhysxCollisionAPI", "PhysxSDFMeshCollisionAPI"):
        if name not in schemas:
            schemas.append(name)
    mesh.GetPrim().SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit(schemas))
    mesh.GetPrim().CreateAttribute(
        "physxSDFMeshCollision:sdfResolution", Sdf.ValueTypeNames.UInt
    ).Set(256)
    mesh.GetPrim().CreateAttribute(
        "physxSDFMeshCollision:sdfSubgridResolution", Sdf.ValueTypeNames.UInt
    ).Set(6)
    for row in range(3):
        for column in range(6):
            slot = f"slot_15ml_r{row:02d}_c{column:02d}"
            frame = stage.GetPrimAtPath(
                str(root.GetPath()) + f"/__frames/{slot}_inserted_bottom"
            )
            point = UsdGeom.XformCache().GetLocalToWorldTransform(
                frame
            ).ExtractTranslation()
            support = UsdGeom.Cylinder.Define(stage, proxy_path + "/" + slot)
            support.CreateAxisAttr("Z")
            support.CreateRadiusAttr(0.00979)
            support.CreateHeightAttr(0.0026)
            support.CreateVisibilityAttr("invisible")
            support.AddTranslateOp().Set(
                Gf.Vec3d(float(point[0]), float(point[1]), float(point[2]) - 0.0013)
            )
            UsdPhysics.CollisionAPI.Apply(support.GetPrim())
    root.SetCustomDataByKey("aan:bakedScaleXyz", Gf.Vec3d(*RACK_SCALE))
    root.SetCustomDataByKey("aan:collisionPolicy", "visual_mesh_sdf_plus_18_slot_supports")
    stage.GetRootLayer().Save()
    profile = json.loads((package / "interaction/profile.json").read_text())
    profile["revision"] = "r3-task08-baked-scale-sdf-all-15ml-supports"
    profile["baked_scale_xyz"] = list(RACK_SCALE)
    profile["collision"] = {
        "main": "visual_mesh_sdf",
        "sdf_resolution": 256,
        "sdf_subgrid_resolution": 6,
        "slot_bottom_support_count": 18,
    }
    _write_json(package / "interaction/profile.json", profile)


def _author_glass(package: Path) -> None:
    from pxr import Gf, Sdf, Usd, UsdShade

    deps = package / "deps/mdl"
    deps.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OMNI_GLASS, deps / OMNI_GLASS.name)
    shutil.copy2(OMNI_GLASS_OPACITY, deps / OMNI_GLASS_OPACITY.name)
    stage = Usd.Stage.Open(str(package / "asset.usd"))
    material_path = BODY_ENTRY + "/Looks/WebStandardClearBorosilicate"
    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, material_path + "/Shader")
    shader.SetSourceAsset(Sdf.AssetPath("./deps/mdl/OmniGlass.mdl"), "mdl")
    shader.SetSourceAssetSubIdentifier("OmniGlass", "mdl")
    output = shader.CreateOutput("out", Sdf.ValueTypeNames.Token)
    output.GetAttr().SetMetadata("renderType", "material")
    for name, (kind, value) in GLASS_INPUTS.items():
        type_name = {
            "float": Sdf.ValueTypeNames.Float,
            "bool": Sdf.ValueTypeNames.Bool,
            "color3f": Sdf.ValueTypeNames.Color3f,
        }[kind]
        if kind == "color3f":
            value = Gf.Vec3f(*value)
        shader.CreateInput(name, type_name).Set(value)
    for material_output in (
        material.CreateSurfaceOutput("mdl"),
        material.CreateVolumeOutput("mdl"),
        material.CreateDisplacementOutput("mdl"),
    ):
        material_output.ConnectToSource(shader.ConnectableAPI(), "out")
    mesh = stage.GetPrimAtPath(BODY_ENTRY + "/node_/mesh_")
    UsdShade.MaterialBindingAPI.Apply(mesh).Bind(material)
    stage.GetPrimAtPath(BODY_ENTRY).SetCustomDataByKey(
        "aan:visualProfile", "WebStandardClearBorosilicate.nine_input.v1"
    )
    stage.GetRootLayer().Save()
    _write_json(
        package / "visual/profile.json",
        {
            "schema_version": "aan.visual_material_profile.v2",
            "profile_id": "scientific_workbench.tube15_long_neck_threaded.glass_web_standard",
            "revision": "v1_2",
            "binding_target": BODY_ENTRY + "/node_/mesh_",
            "material": "WebStandardClearBorosilicate",
            "mdl_inputs": {
                name: {"type": kind, "value": value}
                for name, (kind, value) in GLASS_INPUTS.items()
            },
            "claim_boundary": "Visual-only override; geometry, SDF, mass, inertia, and thread claims are unchanged.",
        },
    )


def _author_red_cap(package: Path) -> None:
    from pxr import Gf, Sdf, Usd, UsdShade

    stage = Usd.Stage.Open(str(package / "asset.usd"))
    material_path = CAP_ENTRY + "/Looks/Task11RedCapPP"
    material = UsdShade.Material.Define(stage, material_path)
    shader = UsdShade.Shader.Define(stage, material_path + "/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(*RED_CAP["diffuse_color"])
    )
    for name in ("roughness", "ior", "metallic", "opacity", "specular"):
        shader.CreateInput(name, Sdf.ValueTypeNames.Float).Set(RED_CAP[name])
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    mesh = stage.GetPrimAtPath(CAP_ENTRY + "/node_/mesh_")
    UsdShade.MaterialBindingAPI.Apply(mesh).Bind(material)
    stage.GetPrimAtPath(CAP_ENTRY).SetCustomDataByKey(
        "aan:visualProfile", "Task11RedCapPP.v1"
    )
    stage.GetRootLayer().Save()
    _write_json(
        package / "visual/profile.json",
        {
            "schema_version": "aan.visual_material_profile.v1",
            "profile_id": "scientific_workbench.tube15_long_neck_threaded.cap_red_pp",
            "revision": "v1_2",
            "binding_target": CAP_ENTRY + "/node_/mesh_",
            "material": RED_CAP,
            "claim_boundary": "Visual-only override; closed-top geometry, SDF, mass, inertia, and thread claims are unchanged.",
        },
    )


def _candidate_manifest(
    package: Path,
    *,
    asset_id: str,
    entry: str,
    role: str,
    source: Path,
    claims: dict[str, bool],
) -> None:
    _write_json(
        package / "evidence/manifest.json",
        {
            "schema_version": "aan.task08_r12_asset_manifest.v1",
            "package_id": asset_id,
            "asset_id": asset_id,
            "asset_role": role,
            "overall_status": "candidate_runtime_pending",
            "blocked_reasons": ["Isaac Sim 4.1 cold-start qualification pending"],
            "entrypoints": {"root_usd": "asset.usd", "asset_entry_prim": entry},
            "source": {
                "package": str(source),
                "asset_sha256": _sha(source / "asset.usd"),
            },
            "asset_sha256": _sha(package / "asset.usd"),
            "claims": claims,
        },
    )


def build_assets(
    output: Path = DEFAULT_OUTPUT,
    *,
    rack_source: Path = DEFAULT_RACK,
    tube_set: Path = DEFAULT_TUBE_SET,
) -> dict[str, Any]:
    output = output.resolve()
    rack_source = rack_source.resolve()
    tube_set = tube_set.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    rack = output / "packages" / RACK_PACKAGE
    body = output / "packages" / BODY_PACKAGE
    cap = output / "packages" / CAP_PACKAGE
    body_source = tube_set / "packages/tube15_long_neck_threaded_body_v1_1"
    cap_source = tube_set / "packages/tube15_long_neck_threaded_closed_cap_v1_1"
    _copy_package(rack_source, rack)
    _copy_package(body_source, body)
    _copy_package(cap_source, cap)
    _bake_rack(rack)
    _author_glass(body)
    _author_red_cap(cap)
    _candidate_manifest(
        rack,
        asset_id=RACK_PACKAGE,
        entry="/TubeRack15ml50ml_OriginalMesh",
        role="static_support_object",
        source=rack_source,
        claims={
            "baked_scale_xyz_1_1_1_1_1_3": True,
            "main_sdf_collision": True,
            "all_15ml_slot_supports": True,
            "isaac41_selected_slot_stability": False,
        },
    )
    _candidate_manifest(
        body,
        asset_id=BODY_PACKAGE,
        entry=BODY_ENTRY,
        role="dynamic",
        source=body_source,
        claims={
            "web_standard_glass": True,
            "geometry_physics_unchanged": True,
            "dynamic_runtime_qualified": False,
            "thread_interaction_ready": False,
        },
    )
    _candidate_manifest(
        cap,
        asset_id=CAP_PACKAGE,
        entry=CAP_ENTRY,
        role="dynamic",
        source=cap_source,
        claims={
            "task11_red_pp": True,
            "closed_top_geometry": True,
            "geometry_physics_unchanged": True,
            "dynamic_runtime_qualified": False,
            "thread_interaction_ready": False,
        },
    )
    _write_json(
        output / "asset_set_manifest.json",
        {
            "schema_version": "aan.task08_r12_asset_set.v1",
            "status": "candidate_runtime_pending",
            "packages": {
                "rack": f"packages/{RACK_PACKAGE}",
                "body": f"packages/{BODY_PACKAGE}",
                "cap": f"packages/{CAP_PACKAGE}",
            },
            "claims": {
                "rack_scaled_sdf_ready": False,
                "visual_material_variants_ready": False,
                "thread_interaction_ready": False,
                "task08_success": False,
                "robot_policy_success": False,
                "benchmark_success": False,
            },
        },
    )
    return {
        "root": output,
        "rack": rack,
        "body": body,
        "cap": cap,
        "sources": {"rack": rack_source, "body": body_source, "cap": cap_source},
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--rack", type=Path, default=DEFAULT_RACK)
    parser.add_argument("--tube-set", type=Path, default=DEFAULT_TUBE_SET)
    args = parser.parse_args(argv)
    print(build_assets(args.out, rack_source=args.rack, tube_set=args.tube_set)["root"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
