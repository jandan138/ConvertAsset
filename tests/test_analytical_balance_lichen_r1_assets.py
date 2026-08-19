from __future__ import annotations

import json
from pathlib import Path

from scripts.build_analytical_balance_lichen_r1_assets import (
    BALANCE_ENTRY,
    BALANCE_SOURCE,
    DOORS,
    _usda_point,
    build_lichen_balance_r1_assets,
)


def _source(path: Path) -> Path:
    path.write_text(
        '#usda 1.0\n(defaultPrim = "root" metersPerUnit = 1 upAxis = "Z")\n'
        'def Xform "root" {}\n',
        encoding="utf-8",
    )
    return path


def test_lichen_r1_builder_authors_identity_entry_and_four_prismatic_doors(
    tmp_path: Path,
) -> None:
    source = _source(tmp_path / "analytical_balance_lichen.usda")
    result = build_lichen_balance_r1_assets(source=source, out=tmp_path / "out")

    facade = result["facade"].read_text(encoding="utf-8")
    profile = json.loads(result["device_profile"].read_text(encoding="utf-8"))
    physics = json.loads(result["physics_profile"].read_text(encoding="utf-8"))
    provenance = json.loads(result["provenance"].read_text(encoding="utf-8"))

    assert 'def Xform "AnalyticalBalanceLichen" (' in facade
    assert 'prepend apiSchemas = ["PhysicsArticulationRootAPI"]' in facade
    assert "analytical_balance_lichen.usda@</root>" in facade
    assert "timeSamples" not in facade
    assert "Blue_Function_Key" not in facade
    assert "Green_Power_Key" not in facade
    assert "def PhysicsRevoluteJoint" not in facade
    assert facade.count("def PhysicsPrismaticJoint") == 4
    assert facade.count("def PhysicsFixedJoint") == 5
    assert '"!resetXformStack!"' in facade
    assert f"rel physics:body0 = <{BALANCE_ENTRY}>" in facade
    assert f"rel physics:body1 = <{BALANCE_SOURCE}>" in facade
    assert 'over Mesh "Cube_001"' in facade
    assert "PhysicsCollisionAPI" in facade
    assert (
        f"point3f physics:localPos0 = {_usda_point(DOORS[0].rest_xyz)}"
        in facade
    )
    assert (
        f"point3f physics:localPos0 = {_usda_point(tuple(DOORS[0].grasp_parent_local_m))}"
        in facade
    )
    for door in DOORS:
        assert f'over Xform "{door.prim_name}"' in facade
        assert f'over Xform "{door.handle_prim_name}"' in facade
        assert f'uniform token physics:axis = "{door.axis}"' in facade
        assert f"float physics:upperLimit = {door.upper_limit_m}" in facade
        assert (
            f'rel physics:body0 = <{BALANCE_SOURCE}/{door.prim_name}>'
            in facade
        )
        assert f"point3f physics:localPos0 = {_usda_point(door.rest_xyz)}" in facade
        assert (
            f"point3f physics:localPos0 = {_usda_point(tuple(door.grasp_parent_local_m))}"
            in facade
        )
        assert f'over Mesh "{door.mesh_name}"' not in facade
        if door.semantic != "front_door":
            assert f'over Mesh "{door.handle_mesh_name}"' not in facade

    assert profile["asset_entry_prim"] == BALANCE_ENTRY
    assert profile["articulation_root_prim"] == BALANCE_ENTRY
    assert profile["runtime_units"]["prismatic"] == "meter"
    assert sorted(profile["semantic_joints"]) == [
        "front_door",
        "left_door",
        "right_door",
        "top_door",
    ]
    assert sorted(
        value["dof_index"] for value in profile["semantic_joints"].values()
    ) == [0, 1, 2, 3]
    for name, door in zip(
        ("front_door", "left_door", "right_door", "top_door"), DOORS, strict=True
    ):
        joint = profile["semantic_joints"][name]
        assert joint["part_prim"] == f"{BALANCE_SOURCE}/{door.prim_name}"
        assert joint["joint_prim"].endswith("/PrismaticJoint")
        assert joint["states"]["open"][0] <= 0.105 <= joint["states"]["open"][1]
        assert joint["reset_state"] == "closed"

    relative_paths = {
        rule["relative_path"]
        for rule in physics["scope_rules"][0]["body_rules"]
    }
    assert "Source" in relative_paths
    for door in DOORS:
        assert f"Source/{door.prim_name}" in relative_paths
        assert f"Source/{door.handle_prim_name}" in relative_paths

    assert provenance["source_modified"] is False
    assert provenance["source_stage_metadata"]["up_axis"] == "Z"
    assert provenance["source_stage_metadata"]["meters_per_unit"] == 1.0
    assert any("handle" in item.lower() for item in provenance["source_repairs"])


def test_lichen_r1_builder_authors_front_handle_collision_only(tmp_path: Path) -> None:
    facade = build_lichen_balance_r1_assets(
        source=_source(tmp_path / "analytical_balance_lichen.usda"),
        out=tmp_path / "out",
    )["facade"].read_text(encoding="utf-8")
    front = facade.split('over Xform "Front_Door_Handle"', 1)[1].split(
        'over Xform "', 1
    )[0]

    assert 'over Mesh "Cube_021"' in front
    assert "PhysicsCollisionAPI" in front
    assert 'uniform token physics:approximation = "convexHull"' in front
    assert 'over Mesh "Cube_019"' not in facade
    assert 'over Mesh "Cube_016"' not in facade
    assert 'over Mesh "Cube_022"' not in facade
    assert 'over Mesh "Cube_023"' not in facade
    assert 'over Mesh "Cube_012"' not in facade


def test_lichen_r1_profile_requires_door_cycles_and_benchtop(tmp_path: Path) -> None:
    result = build_lichen_balance_r1_assets(
        source=_source(tmp_path / "analytical_balance_lichen.usda"),
        out=tmp_path / "out",
    )
    profile = json.loads(result["device_profile"].read_text(encoding="utf-8"))
    task_semantics = json.loads(result["task_semantics"].read_text(encoding="utf-8"))

    assert profile["required_runtime_task_gates"] == [
        "front_door_state_cycle",
        "left_door_state_cycle",
        "right_door_state_cycle",
        "top_door_state_cycle",
        "handle_follow_front_door",
        "front_door_contact_cycle",
        "benchtop_stability",
    ]
    assert task_semantics["task_operated_semantics"] == [
        "front_door",
        "left_door",
        "right_door",
        "top_door",
    ]
    assert profile["named_frames"]["front_door_grasp"]["parent_prim"].endswith(
        "/Front_Sliding_Glass_Door"
    )
    assert profile["mounting"]["support_plane_to_root_mount_pose"][
        "translation_m"
    ] == [0.0, 0.0, 0.0]
    assert profile["mounting"]["support_plane_to_root_mount_pose"][
        "rotation_wxyz"
    ] == [1.0, 0.0, 0.0, 0.0]
    assert profile["mounting"]["qualified_reset_geometry"][
        "warmup_extent_world_aabb_m"
    ] == [0.17827999591827393, 0.28356999158859253, 0.27254000771790743]
