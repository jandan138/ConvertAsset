from __future__ import annotations

import importlib.util
import math
from pathlib import Path

from pxr import Usd, UsdGeom, UsdPhysics

from convert_asset.asset_application_normalizer.container_topology import (
    analyze_mesh_topology,
)


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/build_closed_wall_container_package.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("build_closed_wall", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source_package(root: Path) -> Path:
    package = root / "source"
    package.mkdir()
    stage = Usd.Stage.CreateNew(str(package / "asset.usd"))
    world = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world)
    stage.DefinePrim("/World/Vessel", "Xform")
    mesh = UsdGeom.Mesh.Define(stage, "/World/Vessel/Body")
    sides = 12
    points = []
    for z in (0.0, 1.0):
        for radius in (2.0, 1.5):
            for index in range(sides):
                angle = 2 * math.pi * index / sides
                points.append((radius * math.cos(angle), radius * math.sin(angle), z))
    ob, ib, ot, it = 0, sides, 2 * sides, 3 * sides
    faces = []
    for index in range(sides):
        nxt = (index + 1) % sides
        faces.extend(
            [
                (ob + index, ob + nxt, ot + nxt, ot + index),
                (ib + nxt, ib + index, it + index, it + nxt),
                (ob + nxt, ob + index, ib + index, ib + nxt),
            ]
        )
    mesh.GetPointsAttr().Set(points)
    mesh.GetFaceVertexCountsAttr().Set([4] * len(faces))
    mesh.GetFaceVertexIndicesAttr().Set([vertex for face in faces for vertex in face])
    stage.GetRootLayer().Save()
    return package


def test_builds_source_bound_overlay_without_mutating_source(tmp_path: Path) -> None:
    module = _module()
    source = _source_package(tmp_path)
    before = (source / "asset.usd").read_bytes()
    output = tmp_path / "candidate"

    result = module.build_closed_wall_package(
        source_package=source,
        output=output,
        mesh_prim="/World/Vessel/Body",
        profile_id="example.vessel.closed-wall.v1",
    )

    assert (source / "asset.usd").read_bytes() == before
    assert result["status"] == "candidate"
    assert result["repair"]["added_face_count"] == 12
    stage = Usd.Stage.Open(str(output / "asset.usd"))
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/World/Vessel/Body"))
    audit = analyze_mesh_topology(
        mesh.GetFaceVertexCountsAttr().Get(), mesh.GetFaceVertexIndicesAttr().Get()
    )
    assert audit.boundary_edge_count == 0
    assert mesh.GetPrim().HasAPI(UsdPhysics.CollisionAPI)
    assert (output / "evidence/container_topology.json").is_file()
