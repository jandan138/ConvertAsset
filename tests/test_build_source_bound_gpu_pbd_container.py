from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from pxr import Usd, UsdGeom, UsdPhysics, UsdShade
from pxr import Sdf


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/build_source_bound_gpu_pbd_container.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("build_source_bound_gpu_pbd", SCRIPT)
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
    stage.DefinePrim("/World/Beaker325ml", "Xform")
    stage.DefinePrim("/World/Beaker325ml/Visual/Source", "Xform")
    stage.DefinePrim("/World/Beaker325ml/__aan_collision_proxy", "Xform")
    material = UsdShade.Material.Define(
        stage, "/World/Beaker325ml/Visual/Source/Looks/Glass"
    )
    for name in ("Body", "Rim"):
        mesh = UsdGeom.Mesh.Define(
            stage, f"/World/Beaker325ml/Visual/Source/{name}"
        )
        mesh.GetPointsAttr().Set([(0, 0, 0), (1, 0, 0), (0, 1, 0)])
        mesh.GetFaceVertexCountsAttr().Set([3])
        mesh.GetFaceVertexIndicesAttr().Set([0, 1, 2])
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
    stage.GetRootLayer().Save()
    return package


def _template(root: Path) -> Path:
    path = root / "template.usda"
    stage = Usd.Stage.CreateNew(str(path))
    world = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world)
    mesh = UsdGeom.Mesh.Define(stage, "/World/ReferenceVessel")
    UsdGeom.Xformable(mesh).AddScaleOp().Set((0.5, 0.5, 0.5))
    mesh.GetPointsAttr().Set(
        [
            (-1, -1, 0),
            (1, -1, 0),
            (1, 1, 0),
            (-1, 1, 0),
            (-1, -1, 2),
            (1, -1, 2),
            (1, 1, 2),
            (-1, 1, 2),
        ]
    )
    mesh.GetFaceVertexCountsAttr().Set([4] * 5)
    mesh.GetFaceVertexIndicesAttr().Set(
        [0, 3, 2, 1, 0, 1, 5, 4, 1, 2, 6, 5, 2, 3, 7, 6, 3, 0, 4, 7]
    )
    UsdPhysics.MassAPI.Apply(mesh.GetPrim()).CreateMassAttr(0.02)
    mesh.GetPrim().CreateAttribute(
        "physxConvexDecompositionCollision:voxelResolution",
        Sdf.ValueTypeNames.Int,
    ).Set(500000)
    mesh.GetPrim().CreateAttribute(
        "physics:rigidBodyEnabled", Sdf.ValueTypeNames.Bool
    ).Set(False)
    mesh.GetPrim().CreateAttribute(
        "newton:contactGap", Sdf.ValueTypeNames.Float, custom=True
    ).Set(0.01)
    stage.GetRootLayer().Save()
    return path


def test_builds_tapered_source_bound_container_from_recipe(tmp_path: Path) -> None:
    source = _source_package(tmp_path)
    template = _template(tmp_path)
    recipe = tmp_path / "recipe.json"
    recipe.write_text(
        json.dumps(
            {
                "schema_version": "aan.source_bound_cylindrical_container_recipe.v1",
                "profile_id": "beaker-325ml.gpu-pbd-static.r1",
                "collision_strategy": "single_mesh",
                "cooking_recipe": "liquid_0812_exact_diagnostic",
                "template": {
                    "usd": str(template),
                    "prim": "/World/ReferenceVessel",
                    "seal_boundaries": False,
                    "dimension_mapping": "clone_authored_xform_stack_recentered",
                    "copy_mass_properties": True,
                    "copy_authored_properties": True,
                },
                "vessel_root": "/World/Beaker325ml",
                "replaced_prim_paths": [
                    "/World/Beaker325ml/Visual/Source/Body",
                    "/World/Beaker325ml/Visual/Source/Rim",
                    "/World/Beaker325ml/__aan_collision_proxy",
                ],
                "glass_material_path": (
                    "/World/Beaker325ml/Visual/Source/Looks/Glass"
                ),
                "support_bottom_source_prims": [
                    "/World/Beaker325ml/Visual/Source/Body"
                ],
                "geometry": {
                    "outer_radius": 0.03727,
                    "inner_radius": 0.03527,
                    "outer_top_radius": 0.03869,
                    "inner_top_radius": 0.03669,
                    "bottom_z": 0.0,
                    "floor_z": 0.003,
                    "rim_center_z": 0.11349,
                    "rim_major_radius": 0.0389675,
                    "rim_radial_radius": 0.0022775,
                    "rim_vertical_radius": 0.0016,
                    "sides": 128,
                    "rim_arc_segments": 8,
                    "body_axial_segments": 24,
                },
                "partition": {
                    "wall_segments": 48,
                    "wall_vertical_segments": 1,
                    "bottom_segments": 1,
                    "bottom_arc_subdivisions": 48,
                    "reuse_rotated_wall_geometry": True,
                    "contact_offset_m": 0.001,
                    "rest_offset_m": 0.0,
                    "support_bottom_z_m": 0.0,
                    "collision_render_mode": "source_parity_visible",
                },
            }
        )
    )

    result = _module().build_source_bound_container(
        source_package=source,
        recipe_path=recipe,
        output=tmp_path / "build",
    )

    assert result["status"] == "candidate"
    candidate = Path(result["candidate_package"])
    profile = json.loads(
        (candidate / "gpu_pbd_static_container_profile.json").read_text()
    )
    assert profile["entry_prim"] == "/World/Beaker325ml"
    assert profile["schema_version"] == "aan.gpu_pbd_static_container_profile.v2"
    assert profile["collision"]["piece_count"] == 1
    assert profile["collision"]["cooking_recipe"] == "liquid_0812_exact_diagnostic"
    assert profile["collision"]["strategy"] == (
        "source_derived_single_mesh_open_boundary_diagnostic"
    )
    topology = json.loads(
        (candidate / "evidence/unified_vessel_topology.json").read_text()
    )
    assert topology["geometry"]["recipe"] == "liquid_0812_topology_template_warp.v1"
    assert topology["template_binding"]["prim"] == "/World/ReferenceVessel"
    assert topology["template_binding"]["mapping"]["mode"] == (
        "clone_authored_xform_stack_recentered"
    )
    assert topology["template_binding"]["mass_properties"]["mass_kg"] == pytest.approx(0.02)
    assert topology["geometry"]["boundary_edge_count"] == 4
    assert profile["promotion"]["status"] == "diagnostic_not_promotable"
    assert profile["cavity"]["radius_m"] == 0.03527
    assert profile["cavity"]["radial_profile"] == {
        "bottom_radius_m": 0.03527,
        "top_radius_m": 0.03669,
    }
    stage = Usd.Stage.Open(str(candidate / "asset.usd"))
    assert not stage.GetPrimAtPath(
        "/World/Beaker325ml/__aan_collision_proxy"
    ).IsActive()
    assert stage.GetPrimAtPath(
        "/World/Beaker325ml/__aan_pbd_collision_proxy/PBD_Unified_Vessel_Mesh"
    ).IsValid()
    collision_mesh = UsdGeom.Mesh(
        stage.GetPrimAtPath(
            "/World/Beaker325ml/__aan_pbd_collision_proxy/PBD_Unified_Vessel_Mesh"
        )
    )
    assert collision_mesh.GetVisibilityAttr().Get() == UsdGeom.Tokens.inherited
    assert collision_mesh.GetPrim().GetAttribute(
        "physxConvexDecompositionCollision:voxelResolution"
    ).GetTypeName() == Sdf.ValueTypeNames.Int
    assert collision_mesh.GetPrim().GetAttribute("physics:rigidBodyEnabled").Get() is False
    assert collision_mesh.GetPrim().GetAttribute("newton:contactGap").Get() == pytest.approx(0.01)
    template_stage = Usd.Stage.Open(str(template))
    template_mesh = UsdGeom.Mesh(
        template_stage.GetPrimAtPath("/World/ReferenceVessel")
    )
    assert collision_mesh.GetPointsAttr().Get() == template_mesh.GetPointsAttr().Get()
    assert UsdGeom.Xformable(collision_mesh).GetOrderedXformOps()[0].GetOpType() == (
        UsdGeom.XformOp.TypeScale
    )
    collision_parent = UsdGeom.Xformable(
        stage.GetPrimAtPath("/World/Beaker325ml/__aan_pbd_collision_proxy")
    )
    assert collision_parent.GetOrderedXformOps()[0].GetOpType() == (
        UsdGeom.XformOp.TypeTransform
    )
