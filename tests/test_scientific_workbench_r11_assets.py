from __future__ import annotations

import json
from pathlib import Path

from scripts.build_scientific_workbench_r11_assets import build_r11_assets


def _source(path: Path, root: str = "root") -> Path:
    path.write_text(
        f'#usda 1.0\n(defaultPrim = "{root}" metersPerUnit = 1 upAxis = "Z")\n'
        f'def Xform "{root}" {{}}\n',
        encoding="utf-8",
    )
    return path


def test_r11_builder_keeps_flat_flask_source_bound_and_open(tmp_path: Path) -> None:
    result = build_r11_assets(
        flat_flask_source=_source(tmp_path / "flask.usda"),
        oven_source=_source(tmp_path / "oven.usda"),
        out=tmp_path / "out",
    )

    facade = result["flat_flask_facade"].read_text(encoding="utf-8")
    interaction = json.loads(
        result["flat_flask_interaction"].read_text(encoding="utf-8")
    )
    fit = json.loads(result["flat_flask_fit"].read_text(encoding="utf-8"))

    assert 'def Xform "FlatBottomFlask2942"' in facade
    assert "flask.usda@</root>" in facade
    assert interaction["asset_entry_prim"] == "/World/FlatBottomFlask2942"
    assert interaction["open_top"]["required"] is True
    assert interaction["named_frames"]["closure_seat"][
        "translation_body_local_usd"
    ] == [0.0, 0.0, 0.10372]
    assert fit["status"] == "pass"
    assert fit["measurements_mm"]["joint_radial_clearance"] == 0.905
    assert fit["gates"]["stopper_handle_retained"]["status"] == "pass"


def test_r11_builder_declares_identity_oven_and_reviewed_controls(tmp_path: Path) -> None:
    result = build_r11_assets(
        flat_flask_source=_source(tmp_path / "flask.usda"),
        oven_source=_source(tmp_path / "oven.usda"),
        out=tmp_path / "out",
    )

    facade = result["oven_facade"].read_text(encoding="utf-8")
    profile = json.loads(result["oven_device_profile"].read_text(encoding="utf-8"))
    task_semantics = json.loads(
        result["oven_task_semantics"].read_text(encoding="utf-8")
    )
    provenance = json.loads(result["oven_provenance"].read_text(encoding="utf-8"))

    assert 'def Xform "AnalogGravityConvectionOven" (' in facade
    assert 'def Xform "Source" (' in facade
    assert "oven.usda@</root>" in facade
    assert 'prepend apiSchemas = ["PhysxRigidBodyAPI"]' in facade
    assert "physxRigidBody:disableGravity = true" in facade
    assert "xformOp:" not in facade.split(
        'def Xform "AnalogGravityConvectionOven"', 1
    )[1].split("{", 1)[0]
    assert profile["asset_entry_prim"] == "/World/AnalogGravityConvectionOven"
    assert profile["articulation_root_prim"] == "/World/AnalogGravityConvectionOven"
    assert set(task_semantics["task_operated_semantics"]) == {
        "main_door",
        "power_rocker",
        "temperature_dial",
    }
    assert "sample_shelf" in task_semantics["task_locked_semantics"]
    assert profile["named_frames"]["sample_shelf_target"]["parent_prim"].endswith(
        "/group_7"
    )
    assert profile["mounting"]["support_plane_to_root_mount_pose"][
        "rotation_wxyz"
    ] == [0.7071067811865476, 0.7071067811865475, 0.0, 0.0]
    assert provenance["source_modified"] is False
    assert provenance["source_stage_metadata"]["meters_per_unit"] == 0.01
    assert provenance["geometry_interpretation"]["effective_meters_per_unit"] == 1.0


def test_r11_oven_profile_covers_all_source_dofs(tmp_path: Path) -> None:
    result = build_r11_assets(
        flat_flask_source=_source(tmp_path / "flask.usda"),
        oven_source=_source(tmp_path / "oven.usda"),
        out=tmp_path / "out",
    )
    profile = json.loads(result["oven_device_profile"].read_text(encoding="utf-8"))

    assert len(profile["semantic_joints"]) == 11
    assert sorted(value["dof_index"] for value in profile["semantic_joints"].values()) == list(
        range(11)
    )
    assert profile["required_runtime_task_gates"] == [
        "main_door_state_cycle",
        "temperature_dial_state_cycle",
        "power_rocker_state_cycle",
        "locked_joint_stability",
        "sample_shelf_support",
        "benchtop_stability",
    ]
