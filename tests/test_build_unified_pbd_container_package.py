from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from pxr import Usd, UsdGeom, UsdPhysics, UsdShade

from convert_asset.asset_application_normalizer.container_topology import (
    UnifiedCylindricalVesselSpec,
    analyze_mesh_topology,
)


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/build_unified_pbd_container_package.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("build_unified_pbd", SCRIPT)
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
    stage.DefinePrim("/World/GraduatedCylinder250ml", "Xform")
    stage.DefinePrim("/World/GraduatedCylinder250ml/Visual", "Xform")
    stage.DefinePrim("/World/GraduatedCylinder250ml/Visual/Source", "Xform")
    material = UsdShade.Material.Define(
        stage, "/World/GraduatedCylinder250ml/Visual/Source/Looks/Glass"
    )
    for name in ("Body", "Bottom", "Rim"):
        mesh = UsdGeom.Mesh.Define(
            stage, f"/World/GraduatedCylinder250ml/Visual/Source/{name}"
        )
        mesh.GetPointsAttr().Set([(0, 0, 0), (1, 0, 0), (0, 1, 0)])
        mesh.GetFaceVertexCountsAttr().Set([3])
        mesh.GetFaceVertexIndicesAttr().Set([0, 1, 2])
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
    stage.GetRootLayer().Save()
    return package


def test_builds_source_bound_unified_visible_collision_mesh(tmp_path: Path) -> None:
    module = _module()
    source = _source_package(tmp_path)
    before = (source / "asset.usd").read_bytes()
    output = tmp_path / "candidate"
    result = module.build_unified_pbd_container_package(
        source_package=source,
        output=output,
        vessel_root="/World/GraduatedCylinder250ml",
        replaced_prim_paths=(
            "/World/GraduatedCylinder250ml/Visual/Source/Body",
            "/World/GraduatedCylinder250ml/Visual/Source/Bottom",
            "/World/GraduatedCylinder250ml/Visual/Source/Rim",
        ),
        glass_material_path=(
            "/World/GraduatedCylinder250ml/Visual/Source/Looks/Glass"
        ),
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
        profile_id="graduated-cylinder-250ml.gpu-pbd-static.r1",
        cooking_recipe="current_r82",
    )

    assert (source / "asset.usd").read_bytes() == before
    assert result["status"] == "candidate"
    stage = Usd.Stage.Open(str(output / "asset.usd"))
    mesh = UsdGeom.Mesh(
        stage.GetPrimAtPath(
            "/World/GraduatedCylinder250ml/Visual/Source/"
            "PBD_Unified_Vessel/PBD_Unified_Vessel_Mesh"
        )
    )
    assert mesh.GetPrim().IsValid()
    assert mesh.GetPrim().HasAPI(UsdPhysics.CollisionAPI)
    assert mesh.GetPrim().IsActive()
    assert mesh.GetVisibilityAttr().Get() != UsdGeom.Tokens.invisible
    assert set(mesh.GetFaceVertexCountsAttr().Get()) == {3}
    audit = analyze_mesh_topology(
        mesh.GetFaceVertexCountsAttr().Get(), mesh.GetFaceVertexIndicesAttr().Get()
    )
    assert audit.boundary_edge_count == 0
    assert not stage.GetPrimAtPath(
        "/World/GraduatedCylinder250ml/Visual/Source/Body"
    ).IsActive()
    profile = json.loads((output / "gpu_pbd_static_container_profile.json").read_text())
    assert profile["promotion"]["status"] == "candidate"
    assert profile["collision"]["render_and_collision_same_prim"] is True
    assert (output / "evidence/unified_vessel_topology.json").is_file()
