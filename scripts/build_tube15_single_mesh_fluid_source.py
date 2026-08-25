#!/usr/bin/env python3
"""Build the no-Cube tube15 source using its watertight visual mesh as SDF."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil


RETENTION_PROFILE = [
    {"z_m": 0.015, "inner_radius_m": 0.0001},
    {"z_m": 0.016, "inner_radius_m": 0.0001},
    {"z_m": 0.020, "inner_radius_m": 0.0022852},
    {"z_m": 0.026, "inner_radius_m": 0.005112},
    {"z_m": 0.031, "inner_radius_m": 0.00664},
    {"z_m": 0.0945, "inner_radius_m": 0.00664},
    {"z_m": 0.098, "inner_radius_m": 0.005555},
    {"z_m": 0.101, "inner_radius_m": 0.005555},
]


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build(*, admitted_package: Path, output: Path) -> Path:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

    admitted_package = admitted_package.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    shutil.copytree(admitted_package, output / "deps/tube15")
    scene = output / "source.usda"
    stage = Usd.Stage.CreateNew(str(scene))
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    root = UsdGeom.Xform.Define(stage, "/World/Tube15SingleMeshFluid").GetPrim()
    root.GetReferences().AddReference(
        "deps/tube15/asset.usd", "/World/CentrifugeTube15mlBody"
    )
    stage.OverridePrim(
        "/World/Tube15SingleMeshFluid/__aan_collision_proxy"
    ).SetActive(False)
    mesh_path = (
        "/World/Tube15SingleMeshFluid/Visual/Source/Tube_Body_Hollow_Mesh"
    )
    stage.GetRootLayer().Save()

    composed = Usd.Stage.Open(str(scene), Usd.Stage.LoadAll)
    visual = UsdGeom.Mesh(composed.GetPrimAtPath(mesh_path))
    raw_points = list(visual.GetPointsAttr().Get())
    if len(raw_points) != 1536:
        raise ValueError("unexpected tube visual point count")
    for index in range(96):
        point = raw_points[index]
        raw_points[index] = Gf.Vec3d(point[0], point[1], -0.002)
    for group, target_z in ((11, 0.031), (12, 0.026), (13, 0.020), (14, 0.016), (15, 0.015)):
        for index in range(group * 96, (group + 1) * 96):
            point = raw_points[index]
            raw_points[index] = Gf.Vec3d(point[0], point[1], target_z)
    for index in range(768, 1536):
        point = raw_points[index]
        radius = (float(point[0]) ** 2 + float(point[1]) ** 2) ** 0.5
        target_radius = max(0.0001, radius - 0.001)
        scale = target_radius / max(radius, 1e-9)
        raw_points[index] = Gf.Vec3d(
            float(point[0]) * scale,
            float(point[1]) * scale,
            float(point[2]),
        )
    cache = UsdGeom.XformCache()
    inverse = cache.GetLocalToWorldTransform(root).GetInverse()
    visual_world = cache.GetLocalToWorldTransform(visual.GetPrim())
    points = [inverse.Transform(visual_world.Transform(point)) for point in raw_points]
    counts = list(visual.GetFaceVertexCountsAttr().Get())
    indices = list(visual.GetFaceVertexIndicesAttr().Get())
    proxy_path = (
        "/World/Tube15SingleMeshFluid/__aan_pbd_collision_proxy/"
        "PBD_SingleMesh_ThickBottom"
    )
    proxy = UsdGeom.Mesh.Define(stage, proxy_path)
    proxy.CreatePointsAttr(points)
    proxy.CreateFaceVertexCountsAttr(counts)
    proxy.CreateFaceVertexIndicesAttr(indices)
    proxy.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    proxy.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
    proxy.CreateDoubleSidedAttr(True)
    proxy_prim = proxy.GetPrim()
    UsdPhysics.CollisionAPI.Apply(proxy_prim).CreateCollisionEnabledAttr(True).Set(True)
    UsdPhysics.MeshCollisionAPI.Apply(proxy_prim).CreateApproximationAttr("sdf")
    proxy_prim.SetMetadata(
        "apiSchemas",
        Sdf.TokenListOp.CreateExplicit(
            [
                "PhysicsCollisionAPI",
                "PhysxCollisionAPI",
                "PhysicsMeshCollisionAPI",
                "PhysxSDFMeshCollisionAPI",
            ]
        ),
    )
    stage.GetRootLayer().Save()

    edges: Counter[tuple[int, int]] = Counter()
    cursor = 0
    for count in counts:
        face = indices[cursor : cursor + count]
        cursor += count
        for first, second in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((int(first), int(second))))] += 1
    topology = {
        "point_count": len(points),
        "face_count": len(counts),
        "boundary_edge_count": sum(value == 1 for value in edges.values()),
        "non_manifold_edge_count": sum(value > 2 for value in edges.values()),
        "connected_component_count": 1,
    }
    if topology["boundary_edge_count"] or topology["non_manifold_edge_count"]:
        raise ValueError("tube visual mesh is not watertight manifold")
    record = {
        "schema_version": "aan.tube15_single_mesh_fluid_source.v1",
        "admitted_package": str(admitted_package),
        "admitted_asset_sha256": _sha(admitted_package / "asset.usd"),
        "entrypoint": {"path": "source.usda", "prim": "/World/Tube15SingleMeshFluid"},
        "collision": {
            "only_active_collider": proxy_path,
            "approximation": "sdf",
            "cube_present": False,
            "old_solid_proxy": "inactive",
            "visual_mesh_collision": False,
            "topology_source": mesh_path,
            "bottom_thickening": {
                "outer_tip_z_m": -0.002,
                "inner_profile_floor_z_m": 0.015,
                "inner_profile_full_radius_z_m": 0.031,
                "inner_wall_inward_offset_m": 0.001,
            },
        },
        "topology": topology,
        "retention_profile": {
            "kind": "axisymmetric_inner_wall",
            "source": "ordered inner rings of bottom-thickened collision copy",
            "stations": RETENTION_PROFILE,
        },
    }
    (output / "source_manifest.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return scene


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admitted-package", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(build(admitted_package=args.admitted_package, output=args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
