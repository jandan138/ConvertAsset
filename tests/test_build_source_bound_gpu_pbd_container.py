from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from pxr import Usd, UsdGeom, UsdShade


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


def test_builds_tapered_source_bound_container_from_recipe(tmp_path: Path) -> None:
    source = _source_package(tmp_path)
    recipe = tmp_path / "recipe.json"
    recipe.write_text(
        json.dumps(
            {
                "schema_version": "aan.source_bound_cylindrical_container_recipe.v1",
                "profile_id": "beaker-325ml.gpu-pbd-static.r1",
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
    assert profile["collision"]["piece_count"] == 49
    assert profile["collision"]["support_bottom_source_prims"] == [
        "/World/Beaker325ml/Visual/Source/Body"
    ]
    assert profile["cavity"]["radius_m"] == 0.03527
    assert profile["cavity"]["radial_profile"] == {
        "bottom_radius_m": 0.03527,
        "top_radius_m": 0.03669,
    }
    stage = Usd.Stage.Open(str(candidate / "asset.usd"))
    assert not stage.GetPrimAtPath(
        "/World/Beaker325ml/__aan_collision_proxy"
    ).IsActive()
