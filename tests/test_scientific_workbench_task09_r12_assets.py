from __future__ import annotations

import json
from pathlib import Path

from scripts.build_scientific_workbench_task09_r12_assets import build_r12_assets


def _source(path: Path, *, root: str = "root") -> Path:
    path.write_text(
        f'#usda 1.0\n(defaultPrim = "{root}" metersPerUnit = 1 upAxis = "Z")\n'
        f'def Xform "{root}" {{}}\n',
        encoding="utf-8",
    )
    return path


def _room(path: Path) -> Path:
    path.write_text(
        '#usda 1.0\n(defaultPrim = "World" metersPerUnit = 1 upAxis = "Z")\n'
        'def Xform "World" { def Xform "Floor" { def Cube "Cube" {} } }\n',
        encoding="utf-8",
    )
    return path


def test_r12_oven_authors_task_control_convex_decomposition_without_mutating_source(
    tmp_path: Path,
) -> None:
    oven = _source(tmp_path / "oven.usda")
    before = oven.read_bytes()
    result = build_r12_assets(
        oven_source=oven,
        room_source=_room(tmp_path / "room.usda"),
        out=tmp_path / "out",
    )

    facade = result["oven_facade"].read_text(encoding="utf-8")
    experimental = result["oven_all_parts_experimental"].read_text(encoding="utf-8")
    profile = json.loads(result["oven_device_profile"].read_text(encoding="utf-8"))
    audit = json.loads(result["oven_collision_audit"].read_text(encoding="utf-8"))

    assert oven.read_bytes() == before
    assert facade.count('token physics:approximation = "convexDecomposition"') == 3
    assert experimental.count('token physics:approximation = "convexDecomposition"') == 12
    assert profile["revision"] == "r12"
    assert profile["asset_entry_prim"] == "/World/AnalogGravityConvectionOven"
    assert len(profile["semantic_joints"]) == 11
    assert audit["expected_collision_mesh_count"] == 3
    assert len(audit["collision_meshes"]) == 3
    assert {item["prim_path"].split("/")[-2] for item in audit["collision_meshes"]} == {
        "main_door",
        "power_rocker",
        "upper_dial",
    }
    assert all(item["approximation"] == "convexDecomposition" for item in audit["collision_meshes"])


def test_r12_floor_support_matches_room_floor_and_has_no_visible_duplicate(
    tmp_path: Path,
) -> None:
    result = build_r12_assets(
        oven_source=_source(tmp_path / "oven.usda"),
        room_source=_room(tmp_path / "room.usda"),
        out=tmp_path / "out",
    )

    facade = result["floor_facade"].read_text(encoding="utf-8")
    profile = json.loads(result["floor_support_profile"].read_text(encoding="utf-8"))

    assert "references" not in facade
    assert 'def Xform "table"' in facade
    assert 'def Cube "floor_support"' in facade
    assert 'prepend apiSchemas = ["PhysicsCollisionAPI"]' in facade
    assert 'primvars:displayColor' in facade
    assert 'token visibility = "invisible"' not in facade
    assert profile["asset_entry_prim"] == "/World/table"
    assert profile["source_collider_prim"] == "/World/table/floor_support"
    assert profile["proxy"]["center_xyz"] == [0.0, 0.0, -0.01]
    assert profile["proxy"]["size_xyz"] == [6.5, 5.5, 0.02]
    assert profile["support_surface"]["top_z"] == 0.0
    assert profile["support_surface"]["x_range"] == [-3.25, 3.25]
    assert profile["support_surface"]["y_range"] == [-2.75, 2.75]
