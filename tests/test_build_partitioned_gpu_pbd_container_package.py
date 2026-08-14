from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from pxr import Usd, UsdGeom, UsdPhysics

from convert_asset.asset_application_normalizer.container_topology import (
    UnifiedCylindricalVesselSpec,
)


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/build_partitioned_gpu_pbd_container_package.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("build_partitioned_gpu_pbd", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_authors_source_derived_gpu_convex_hulls_and_removes_render_mesh_collision(
    tmp_path: Path,
) -> None:
    package = tmp_path / "unified"
    package.mkdir()
    stage = Usd.Stage.CreateNew(str(package / "asset.usd"))
    world = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world)
    stage.DefinePrim("/World/GraduatedCylinder250ml", "Xform")
    mesh = UsdGeom.Mesh.Define(
        stage,
        "/World/GraduatedCylinder250ml/Visual/Source/"
        "PBD_Unified_Vessel/PBD_Unified_Vessel_Mesh",
    )
    mesh.GetPointsAttr().Set([(0, 0, 0), (1, 0, 0), (0, 1, 0)])
    mesh.GetFaceVertexCountsAttr().Set([3])
    mesh.GetFaceVertexIndicesAttr().Set([0, 1, 2])
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim()).CreateCollisionEnabledAttr(True)
    stage.GetRootLayer().Save()
    (package / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "entry_prim": "/World/GraduatedCylinder250ml",
                "collision": {"mesh_prim": str(mesh.GetPath())},
            }
        )
    )

    result = _module().build_partitioned_package(
        unified_package=package,
        output=tmp_path / "partitioned",
        vessel_root="/World/GraduatedCylinder250ml",
        unified_mesh_prim=str(mesh.GetPath()),
        spec=UnifiedCylindricalVesselSpec(
            outer_radius=0.02099,
            inner_radius=0.019185,
            bottom_z=0.0099,
            floor_z=0.011705,
            rim_center_z=0.27659,
            rim_major_radius=0.020825,
            rim_radial_radius=0.0011,
            rim_vertical_radius=0.00165,
        ),
        profile_id="graduated-cylinder-250ml.gpu-pbd-static.partitioned-r1",
        support_bottom_source_prims=(
            "/World/GraduatedCylinder250ml/Visual/Source/Bottom",
        ),
    )

    assert result["piece_count"] == 249
    stage = Usd.Stage.Open(str(tmp_path / "partitioned/asset.usd"))
    visible = stage.GetPrimAtPath(str(mesh.GetPath()))
    assert not visible.HasAPI(UsdPhysics.CollisionAPI)
    assert not visible.HasAPI(UsdPhysics.MeshCollisionAPI)
    collision_root = stage.GetPrimAtPath(
        "/World/GraduatedCylinder250ml/PBD_GPU_Collision"
    )
    pieces = [prim for prim in collision_root.GetChildren() if prim.IsA(UsdGeom.Mesh)]
    assert len(pieces) == 249
    assert all(prim.HasAPI(UsdPhysics.CollisionAPI) for prim in pieces)
    assert all(len(UsdGeom.Mesh(prim).GetPointsAttr().Get()) <= 64 for prim in pieces)
    assert all(
        prim.GetAttribute("physics:approximation").Get() == "convexDecomposition"
        for prim in pieces
    )
    assert all(
        prim.GetAttribute("physxCollision:contactOffset").Get()
        == pytest.approx(0.001)
        for prim in pieces
    )
    assert all(
        prim.GetAttribute("physxCollision:restOffset").Get()
        == pytest.approx(0.0)
        for prim in pieces
    )
    assert all(
        prim.GetAttribute("physics:rigidBodyEnabled").Get() is False
        for prim in pieces
    )
    profile = json.loads(
        (tmp_path / "partitioned/gpu_pbd_static_container_profile.json").read_text()
    )
    assert profile["collision"]["support_bottom_z_m"] == pytest.approx(0.0)
    assert profile["collision"]["support_bottom_source_prims"] == [
        "/World/GraduatedCylinder250ml/Visual/Source/Bottom"
    ]
    assert profile["cavity"] == {
        "center_xy_m": [0.0, 0.0],
        "floor_z_m": pytest.approx(0.011705),
        "radius_m": pytest.approx(0.019185),
        "radial_profile": {
            "bottom_radius_m": pytest.approx(0.019185),
            "top_radius_m": pytest.approx(0.019185),
        },
        "rim_z_m": pytest.approx(0.27824),
        "support_z_m": pytest.approx(0.0),
    }
    assert all(
        prim.GetAttribute(
            "physxConvexDecompositionCollision:voxelResolution"
        ).Get()
        == 10000
        for prim in pieces
    )
    assert UsdGeom.Imageable(collision_root).GetPurposeAttr().Get() == "guide"
    assert all(
        UsdGeom.Imageable(prim).GetVisibilityAttr().Get() == "inherited"
        for prim in pieces
    )
