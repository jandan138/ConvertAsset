from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from pxr import Usd, UsdGeom


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/build_task02_r81_fluid_component.py"


def _module() -> object:
    spec = importlib.util.spec_from_file_location("build_task02_r81", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_partition_face_indices_cover_every_source_face_once() -> None:
    module = _module()
    stage = Usd.Stage.CreateInMemory()
    mesh = UsdGeom.Mesh.Define(stage, "/mesh")
    mesh.GetPointsAttr().Set(
        [
            (1, 0, 0),
            (0, 1, 0),
            (-1, 0, 0),
            (0, -1, 0),
            (1, 0, 1),
            (0, 1, 1),
            (-1, 0, 1),
            (0, -1, 1),
        ]
    )
    mesh.GetFaceVertexCountsAttr().Set([4, 4, 4, 4])
    mesh.GetFaceVertexIndicesAttr().Set(
        [0, 1, 5, 4, 1, 2, 6, 5, 2, 3, 7, 6, 3, 0, 4, 7]
    )
    module.PARTITION_COUNTS = (4,)

    partitions = module.partition_face_indices(mesh, 4)

    assert sorted(index for part in partitions for index in part) == [0, 1, 2, 3]
    assert all(len(part) == 1 for part in partitions)


def test_real_package_build_preserves_visible_face_coverage(tmp_path: Path) -> None:
    module = _module()
    root = Path(__file__).resolve().parents[1]
    cylinder = root / "outputs/scientific_workbench_r7_task_assets_20260813/packages/graduated_cylinder_250ml"
    beaker = root / "outputs/scientific_workbench_r7_task_assets_20260813/packages/beaker_325ml"
    if not cylinder.exists() or not beaker.exists():
        return
    out = tmp_path / "r81"

    module.build(
        cylinder_package=cylinder,
        beaker_package=beaker,
        out=out,
        partition_count=12,
    )

    profile = json.loads((out / "interactive_fluid_scene_profile.json").read_text())
    report = json.loads((out / "evidence/geometry_derivation.json").read_text())
    stage = Usd.Stage.Open(str(out / "component.usda"))
    partitions = [
        prim
        for prim in stage.Traverse()
        if "/VisibleCollisionPartitions/sector_" in str(prim.GetPath())
    ]
    assert profile["schema_version"].endswith(".v2")
    assert len(partitions) == 12
    assert report["source_face_count"] == 288
    assert sum(report["partition_face_counts"]) == 288
    assert report["source_points_unchanged"] is True
    assert report["hidden_collision_geometry_added"] is False
    assert stage.GetPrimAtPath(module.SOURCE_BODY).GetAttribute("visibility").Get() == "invisible"
    assert all(
        prim.GetAttribute("physics:approximation").Get() == "convexDecomposition"
        and prim.GetAttribute("visibility").Get() != "invisible"
        and UsdGeom.Mesh(prim).GetNormalsInterpolation() == UsdGeom.Tokens.faceVarying
        and len(UsdGeom.Mesh(prim).GetNormalsAttr().Get())
        == sum(UsdGeom.Mesh(prim).GetFaceVertexCountsAttr().Get())
        for prim in partitions
    )
    particles = stage.GetPrimAtPath("/World/FluidWorkcell/ParticleSet")
    particle_system = stage.GetPrimAtPath("/World/FluidWorkcell/ParticleSystem")
    assert "PhysxParticleSetAPI" in particles.GetMetadata("apiSchemas").explicitItems
    assert (
        "PhysxParticleIsosurfaceAPI"
        in particle_system.GetMetadata("apiSchemas").explicitItems
    )
