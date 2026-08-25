#!/usr/bin/env python3
"""Build a source-bound tube15 facade with the colleague hollow SDF and bottom Cube."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build(*, source_scene: Path, admitted_package: Path, output: Path) -> Path:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    source_scene = source_scene.resolve()
    admitted_package = admitted_package.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    shutil.copytree(admitted_package, output / "deps/tube15")
    source_stage = Usd.Stage.Open(str(source_scene), Usd.Stage.LoadAll)
    source_root = "/World/obj_centrifuge_tube_15ml_body"
    source_cube = UsdGeom.Mesh(
        source_stage.GetPrimAtPath(source_root + "/Visual/Source/Cube")
    )
    if not source_cube:
        raise ValueError("colleague bottom Cube is missing")

    scene = output / "source.usda"
    stage = Usd.Stage.CreateNew(str(scene))
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    root = UsdGeom.Xform.Define(stage, "/World/Tube15FluidSource").GetPrim()
    root.GetReferences().AddReference(
        "deps/tube15/asset.usd", "/World/CentrifugeTube15mlBody"
    )
    hollow_path = "/World/Tube15FluidSource/Visual/Source/Tube_Body_Hollow_Mesh"
    UsdGeom.Scope.Define(
        stage, "/World/Tube15FluidSource/__aan_pbd_collision_proxy"
    )

    cube_path = "/World/Tube15FluidSource/Visual/Source/Cube"
    original_scale = tuple(source_cube.GetPrim().GetAttribute("xformOp:scale").Get())
    cube = UsdGeom.Mesh.Define(stage, cube_path)
    cube.CreatePointsAttr(
        [
            Gf.Vec3f(x, y, z)
            for z in (0.0004, 0.0024)
            for y in (-0.007, 0.007)
            for x in (-0.007, 0.007)
        ]
    )
    cube.CreateFaceVertexCountsAttr([4] * 6)
    cube.CreateFaceVertexIndicesAttr(
        [0, 1, 3, 2, 4, 6, 7, 5, 0, 4, 5, 1, 2, 3, 7, 6, 0, 2, 6, 4, 1, 5, 7, 3]
    )
    cube.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    cube.CreateVisibilityAttr(UsdGeom.Tokens.invisible)

    cache = UsdGeom.XformCache()
    root_inverse = cache.GetLocalToWorldTransform(root).GetInverse()
    source_hollow = UsdGeom.Mesh(stage.GetPrimAtPath(hollow_path))
    hollow_world = cache.GetLocalToWorldTransform(source_hollow.GetPrim())
    unified_points = [
        root_inverse.Transform(hollow_world.Transform(point))
        for point in source_hollow.GetPointsAttr().Get()
    ]
    unified_counts = list(source_hollow.GetFaceVertexCountsAttr().Get())
    unified_indices = list(source_hollow.GetFaceVertexIndicesAttr().Get())
    box_start = len(unified_points)
    unified_points.extend(cube.GetPointsAttr().Get())
    unified_counts.extend(cube.GetFaceVertexCountsAttr().Get())
    unified_indices.extend(
        box_start + int(index) for index in cube.GetFaceVertexIndicesAttr().Get()
    )
    unified = UsdGeom.Mesh.Define(
        stage,
        "/World/Tube15FluidSource/__aan_pbd_collision_proxy/PBD_Unified_Tube_Mesh",
    )
    unified.CreatePointsAttr(unified_points)
    unified.CreateFaceVertexCountsAttr(unified_counts)
    unified.CreateFaceVertexIndicesAttr(unified_indices)
    unified.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    unified.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
    unified.CreateDoubleSidedAttr(True)
    unified_prim = unified.GetPrim()
    UsdPhysics.CollisionAPI.Apply(unified_prim).CreateCollisionEnabledAttr(True).Set(True)
    UsdPhysics.MeshCollisionAPI.Apply(unified_prim).CreateApproximationAttr("sdf")
    stage.GetRootLayer().Save()

    record = {
        "schema_version": "aan.tube15_colleague_fluid_source.v1",
        "source_scene": str(source_scene),
        "source_scene_sha256": _sha(source_scene),
        "source_scope": source_root,
        "admitted_package": str(admitted_package),
        "admitted_asset_sha256": _sha(admitted_package / "asset.usd"),
        "entrypoint": {"path": "source.usda", "prim": "/World/Tube15FluidSource"},
        "collision": {
            "wall": "visual hollow mesh SDF",
            "bottom": "colleague invisible Cube route, widened for small-v2 containment",
            "bottom_original_scale_m": list(original_scale),
            "bottom_profiled_scale_m": [0.014, 0.014, 0.002],
            "bottom_profiled_center_z_m": 0.0014,
            "bottom_profiled_top_z_m": 0.0024,
            "bottom_transform": "closed_parent_local_cube_mesh_for_sdf",
            "original_solid_proxy": "disabled",
            "runtime_collider": "single unified hollow-wall plus bottom-box SDF mesh",
        },
    }
    (output / "source_manifest.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return scene


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-scene", type=Path, required=True)
    parser.add_argument("--admitted-package", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(
        build(
            source_scene=args.source_scene,
            admitted_package=args.admitted_package,
            output=args.out,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
