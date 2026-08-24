#!/usr/bin/env python3
"""Package Wangshuai's SDF beaker behind a metre/Z-up source-bound facade."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import traceback


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_wangshuai/obj_beaker_sdf.usd"
)
DEFAULT_MDL = (
    ROOT
    / "outputs/scientific_workbench_glass_web_standard_20260819/packages/"
    "beaker_325ml_glass_web_standard_v1/deps/mdl"
)
DEFAULT_OUT = (
    ROOT
    / "outputs/scientific_workbench_beaker_325ml_sdf_web_standard_20260824/"
    "package"
)
ENTRY = "/World/Beaker325mlSdf"
GLASS_MESHES = (
    "Visual/Source/Rolled_Rim/Torus",
    "Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh",
    "Visual/Source/Pour_Spout/Pour_Spout_Mesh",
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build(source: Path, mdl_source: Path, output: Path) -> Path:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

    source = source.resolve()
    mdl_source = mdl_source.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite: {output}")
    (output / "deps/source").mkdir(parents=True)
    (output / "deps/usd").mkdir(parents=True)
    (output / "deps/mdl").mkdir(parents=True)
    (output / "overlays").mkdir(parents=True)
    (output / "evidence").mkdir(parents=True)
    shutil.copy2(source, output / "deps/source/obj_beaker_sdf.usd")
    for name in ("OmniGlass.mdl", "OmniGlass_Opacity.mdl"):
        shutil.copy2(mdl_source / name, output / "deps/mdl" / name)

    scoped_path = output / "deps/usd/scoped_source.usda"
    scoped = Usd.Stage.CreateNew(str(scoped_path))
    UsdGeom.SetStageMetersPerUnit(scoped, 1.0)
    UsdGeom.SetStageUpAxis(scoped, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(scoped, "/World")
    scoped.SetDefaultPrim(world.GetPrim())
    beaker = UsdGeom.Xform.Define(scoped, ENTRY)
    beaker.GetPrim().GetReferences().AddReference(
        "../source/obj_beaker_sdf.usd", "/Root/obj_beaker"
    )
    scoped.GetRootLayer().Save()

    material_path = output / "overlays/visual_material.usda"
    material_stage = Usd.Stage.CreateNew(str(material_path))
    material = UsdShade.Material.Define(
        material_stage, ENTRY + "/__aan_visual_materials/WebStandardClearBorosilicate"
    )
    shader = UsdShade.Shader.Define(material_stage, str(material.GetPath()) + "/Shader")
    shader.SetSourceAsset(Sdf.AssetPath("../deps/mdl/OmniGlass.mdl"), "mdl")
    shader.SetSourceAssetSubIdentifier("OmniGlass", "mdl")
    shader.CreateInput("cutout_opacity", Sdf.ValueTypeNames.Float).Set(0.0)
    shader.CreateInput("depth", Sdf.ValueTypeNames.Float).Set(0.002)
    shader.CreateInput("enable_opacity", Sdf.ValueTypeNames.Bool).Set(False)
    shader.CreateInput("frosting_roughness", Sdf.ValueTypeNames.Float).Set(0.035)
    shader.CreateInput("glass_color", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.99, 0.998, 1.0)
    )
    shader.CreateInput("glass_ior", Sdf.ValueTypeNames.Float).Set(1.47)
    shader.CreateInput("reflection_color", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(1.0)
    )
    shader.CreateInput("roughness_texture_influence", Sdf.ValueTypeNames.Float).Set(1.0)
    shader.CreateInput("thin_walled", Sdf.ValueTypeNames.Bool).Set(False)
    material.CreateSurfaceOutput("mdl").ConnectToSource(shader.ConnectableAPI(), "out")
    material.CreateVolumeOutput("mdl").ConnectToSource(shader.ConnectableAPI(), "out")
    material.CreateDisplacementOutput("mdl").ConnectToSource(
        shader.ConnectableAPI(), "out"
    )
    for relative in GLASS_MESHES:
        prim = material_stage.OverridePrim(f"{ENTRY}/{relative}")
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
    material_stage.GetRootLayer().Save()

    asset_path = output / "asset.usd"
    asset = Sdf.Layer.CreateNew(str(asset_path))
    asset.defaultPrim = "World"
    asset.subLayerPaths = ["overlays/visual_material.usda", "deps/usd/scoped_source.usda"]
    asset.Save()
    stage = Usd.Stage.Open(str(asset_path), Usd.Stage.LoadAll)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    stage.GetRootLayer().Save()

    bbox = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(), [UsdGeom.Tokens.default_, UsdGeom.Tokens.render]
    ).ComputeWorldBound(stage.GetPrimAtPath(ENTRY)).ComputeAlignedBox()
    size = [float(value) for value in bbox.GetMax() - bbox.GetMin()]
    expected = [0.08249, 0.08849, 0.11509]
    if any(abs(actual - target) > 1e-5 for actual, target in zip(size, expected)):
        raise RuntimeError(f"unexpected composed beaker size: {size}")
    body = stage.GetPrimAtPath(
        ENTRY + "/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh"
    )
    if body.GetAttribute("physics:approximation").Get() != "sdf":
        raise RuntimeError("beaker body SDF collision is missing")
    schemas = set(body.GetAppliedSchemas())
    if "PhysxSDFMeshCollisionAPI" not in schemas:
        raise RuntimeError("beaker body lacks PhysxSDFMeshCollisionAPI")

    source_sha = _sha(source)
    manifest = {
        "schema_version": "aan.source_bound_sdf_beaker.v1",
        "package_id": "scientific_workbench_beaker_325ml_sdf_web_standard_v1",
        "overall_status": "pass",
        "blocked_reasons": [],
        "entrypoints": {
            "root_usd": "asset.usd",
            "default_prim": "World",
            "asset_entry_prim": ENTRY,
        },
        "source": {
            "path": str(source),
            "sha256": source_sha,
            "unchanged": _sha(output / "deps/source/obj_beaker_sdf.usd") == source_sha,
        },
        "stage_metrics": {"meters_per_unit": 1.0, "up_axis": "Z"},
        "composed_size_m": size,
        "collision": {
            "body_and_rim": "sdf_with_PhysxSDFMeshCollisionAPI",
            "spout": "convexHull",
            "legacy_unified_proxy_enabled": False,
        },
        "visual_material": {
            "profile_id": "scientific_workbench.beaker_325ml.glass_web_standard_v1",
            "material": "WebStandardClearBorosilicate",
        },
        "claims": {
            "source_bound": True,
            "dependency_closure_package_local": True,
            "dynamic_pbd_retention": "validated_in_consumer_scene",
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }
    (output / "evidence/manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--mdl-source", type=Path, default=DEFAULT_MDL)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    app = None
    try:
        try:
            import pxr  # noqa: F401
        except ImportError:
            from isaacsim import SimulationApp

            app = SimulationApp({"headless": True, "multi_gpu": False})
        build(args.source, args.mdl_source, args.out)
        return 0
    except BaseException:
        traceback.print_exc()
        return 2
    finally:
        if app is not None:
            app.close()


if __name__ == "__main__":
    raise SystemExit(main())
