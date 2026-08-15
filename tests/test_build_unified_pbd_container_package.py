from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from pxr import Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

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


def _reference_template(root: Path) -> Path:
    path = root / "reference.usda"
    stage = Usd.Stage.CreateNew(str(path))
    world = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world)
    mesh = UsdGeom.Mesh.Define(stage, "/World/ReferenceVessel")
    UsdGeom.Xformable(mesh).AddScaleOp().Set((0.5, 0.5, 0.5))
    mesh.GetPointsAttr().Set(
        [
            (-2, -2, 0),
            (2, -2, 0),
            (2, 2, 0),
            (-2, 2, 0),
            (-2, -2, 4),
            (2, -2, 4),
            (2, 2, 4),
            (-2, 2, 4),
        ]
    )
    # Deliberately omit the top face.  The 0812 reference mesh itself contains
    # two tiny boundary loops, so the package builder must seal source-derived
    # topology before it can claim a closed collision mesh.
    mesh.GetFaceVertexCountsAttr().Set([4] * 5)
    mesh.GetFaceVertexIndicesAttr().Set(
        [0, 3, 2, 1, 0, 1, 5, 4, 1, 2, 6, 5, 2, 3, 7, 6, 3, 0, 4, 7]
    )
    mass = UsdPhysics.MassAPI.Apply(mesh.GetPrim())
    mass.CreateMassAttr(0.02)
    stage.GetRootLayer().Save()
    return path


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
    assert not mesh.GetPrim().IsValid()
    collision_mesh = UsdGeom.Mesh(
        stage.GetPrimAtPath(
            "/World/GraduatedCylinder250ml/__aan_collision_proxy/"
            "PBD_Unified_Vessel_Mesh"
        )
    )
    assert not collision_mesh.GetPrim().IsValid()
    collision_mesh = UsdGeom.Mesh(
        stage.GetPrimAtPath(
            "/World/GraduatedCylinder250ml/__aan_pbd_collision_proxy/"
            "PBD_Unified_Vessel_Mesh"
        )
    )
    assert collision_mesh.GetPrim().IsValid()
    mesh = collision_mesh
    assert mesh.GetPrim().HasAPI(UsdPhysics.CollisionAPI)
    assert mesh.GetPrim().IsActive()
    assert mesh.GetVisibilityAttr().Get() == UsdGeom.Tokens.invisible
    assert mesh.GetPurposeAttr().Get() == UsdGeom.Tokens.default_
    assert mesh.GetSubdivisionSchemeAttr().Get() == UsdGeom.Tokens.none
    assert mesh.GetDoubleSidedAttr().Get() is True
    assert set(mesh.GetFaceVertexCountsAttr().Get()) == {3}
    audit = analyze_mesh_topology(
        mesh.GetFaceVertexCountsAttr().Get(), mesh.GetFaceVertexIndicesAttr().Get()
    )
    assert audit.boundary_edge_count == 0
    assert stage.GetPrimAtPath(
        "/World/GraduatedCylinder250ml/Visual/Source/Body"
    ).IsActive()
    profile = json.loads((output / "gpu_pbd_static_container_profile.json").read_text())
    assert profile["schema_version"] == "aan.gpu_pbd_static_container_profile.v2"
    assert profile["promotion"]["status"] == "candidate"
    assert profile["collision"]["render_and_collision_same_prim"] is False
    assert profile["collision"]["source_derived_not_primitive_proxy"] is True
    assert profile["collision"]["piece_approximation"] == "convexDecomposition"
    assert profile["collision"]["piece_count"] == 1
    assert profile["visual_source_unchanged"] is True
    assert (output / "evidence/unified_vessel_topology.json").is_file()


def test_warps_0812_template_topology_without_runtime_dependency(tmp_path: Path) -> None:
    module = _module()
    source = _source_package(tmp_path)
    template = _reference_template(tmp_path)
    output = tmp_path / "candidate"

    module.build_unified_pbd_container_package(
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
        profile_id="graduated-cylinder.template-warp.r1",
        cooking_recipe="liquid_0812_promotable",
        template_usd=template,
        template_prim="/World/ReferenceVessel",
        copy_template_mass_properties=True,
    )

    topology = json.loads(
        (output / "evidence/unified_vessel_topology.json").read_text()
    )
    assert topology["geometry"]["recipe"] == "liquid_0812_topology_template_warp.v1"
    assert topology["geometry"]["point_count"] == 8
    assert topology["geometry"]["boundary_edge_count"] == 0
    assert topology["geometry"]["sealed_template_boundary_loop_count"] == 1
    assert topology["template_binding"]["prim"] == "/World/ReferenceVessel"
    assert topology["template_binding"]["usd_sha256"] == module._sha(template)
    assert topology["template_binding"]["mapping"]["authored_mesh_scale"] == 0.5
    assert topology["template_binding"]["mass_properties"]["mass_kg"] == pytest.approx(0.02)
    stage = Usd.Stage.Open(str(output / "asset.usd"))
    collision_mesh = UsdGeom.Mesh(
        stage.GetPrimAtPath(
            "/World/GraduatedCylinder250ml/__aan_pbd_collision_proxy/"
            "PBD_Unified_Vessel_Mesh"
        )
    )
    assert UsdGeom.Xformable(collision_mesh).GetOrderedXformOps()[0].Get() == (0.5, 0.5, 0.5)
    assert collision_mesh.GetPrim().HasAPI(UsdPhysics.MassAPI)
    assert UsdPhysics.MassAPI(collision_mesh.GetPrim()).GetMassAttr().Get() == pytest.approx(0.02)
    root_layer = Sdf.Layer.FindOrOpen(str(output / "asset.usd"))
    assert root_layer is not None
    assert all(str(template) not in value for value in root_layer.subLayerPaths)


def test_remeshes_measured_vessel_but_keeps_0812_physics_properties(
    tmp_path: Path,
) -> None:
    module = _module()
    source = _source_package(tmp_path)
    template = _reference_template(tmp_path)
    template_stage = Usd.Stage.Open(str(template))
    template_prim = template_stage.GetPrimAtPath("/World/ReferenceVessel")
    template_prim.CreateAttribute(
        "newton:contactGap", Sdf.ValueTypeNames.Float, custom=True
    ).Set(0.01)
    template_stage.GetRootLayer().Save()
    output = tmp_path / "candidate"

    module.build_unified_pbd_container_package(
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
            sides=32,
            body_axial_segments=32,
        ),
        profile_id="graduated-cylinder.remeshed.r1",
        cooking_recipe="liquid_0812_promotable",
        template_usd=template,
        template_prim="/World/ReferenceVessel",
        template_dimension_mapping="remesh_measured_vessel",
        copy_template_mass_properties=True,
        copy_template_authored_properties=True,
        template_authored_property_scope="physics_cooking",
    )

    stage = Usd.Stage.Open(str(output / "asset.usd"))
    mesh = UsdGeom.Mesh(
        stage.GetPrimAtPath(
            "/World/GraduatedCylinder250ml/__aan_pbd_collision_proxy/"
            "PBD_Unified_Vessel_Mesh"
        )
    )
    assert len(mesh.GetPointsAttr().Get()) > 8
    audit = analyze_mesh_topology(
        mesh.GetFaceVertexCountsAttr().Get(), mesh.GetFaceVertexIndicesAttr().Get()
    )
    assert audit.boundary_edge_count == 0
    assert mesh.GetNormalsAttr().Get() is None
    assert mesh.GetPrim().GetAttribute("newton:contactGap").Get() == pytest.approx(0.01)
    topology = json.loads(
        (output / "evidence/unified_vessel_topology.json").read_text()
    )
    assert topology["template_binding"]["mapping"]["mode"] == (
        "remesh_measured_vessel"
    )


def test_remeshes_in_template_units_and_preserves_composed_dimensions(
    tmp_path: Path,
) -> None:
    module = _module()
    source = _source_package(tmp_path)
    template = _reference_template(tmp_path)
    output = tmp_path / "candidate"

    module.build_unified_pbd_container_package(
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
            sides=16,
            body_axial_segments=1,
        ),
        profile_id="graduated-cylinder.template-units.r1",
        cooking_recipe="liquid_0812_promotable",
        template_usd=template,
        template_prim="/World/ReferenceVessel",
        template_dimension_mapping="remesh_measured_vessel_in_template_units",
        copy_template_mass_properties=True,
        copy_template_authored_properties=True,
        template_authored_property_scope="physics_cooking",
    )

    stage = Usd.Stage.Open(str(output / "asset.usd"))
    mesh_prim = stage.GetPrimAtPath(
        "/World/GraduatedCylinder250ml/__aan_pbd_collision_proxy/"
        "PBD_Unified_Vessel_Mesh"
    )
    points = UsdGeom.Mesh(mesh_prim).GetPointsAttr().Get()
    scale_ops = UsdGeom.Xformable(mesh_prim).GetOrderedXformOps()
    assert len(scale_ops) == 1
    assert tuple(scale_ops[0].Get()) == pytest.approx((0.5, 0.5, 0.5))
    assert max(float(point[2]) for point in points) > 0.5

    world_range = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]
    ).ComputeWorldBound(mesh_prim).ComputeAlignedRange()
    assert world_range.GetMin()[2] == pytest.approx(0.0099, abs=1e-6)
    assert world_range.GetMax()[2] == pytest.approx(0.27824, abs=1e-6)

    topology = json.loads(
        (output / "evidence/unified_vessel_topology.json").read_text()
    )
    mapping = topology["template_binding"]["mapping"]
    assert mapping["mode"] == "remesh_measured_vessel_in_template_units"
    assert mapping["authored_mesh_scale"] == pytest.approx(0.5)
