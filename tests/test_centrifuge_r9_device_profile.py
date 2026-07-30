from __future__ import annotations

from scripts.build_centrifuge_device_profile_r9 import (
    ROOT,
    _mounting_contract,
    _required_runtime_task_gates,
    _semantic_joints,
    _support_frame,
)


def test_r9_profile_keeps_existing_joint_semantics() -> None:
    joints = _semantic_joints()

    assert set(joints) == {"start_button", "rotor", "lid"}
    assert {item["dof_index"] for item in joints.values()} == {0, 1, 2}
    assert joints["lid"]["reset_state"] == "open"


def test_r9_profile_requires_hash_bound_benchtop_stability() -> None:
    gates = _required_runtime_task_gates()

    assert gates == [
        "lid_contact_cycle",
        "button_contact_cycle",
        "button_reset_stability",
        "rotor_reset_stability",
        "socket_insertion_clearance",
        "benchtop_stability",
    ]


def test_r9_profile_exposes_authoritative_root_local_support_frame() -> None:
    frame = _support_frame(0.0)

    assert frame == {
        "parent_prim": ROOT,
        "translation_parent_local_m": [0.0, 0.0, 0.0],
        "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
        "authoritative": True,
    }


def test_r9_profile_exposes_the_measured_consumer_mount_candidate() -> None:
    mounting = _mounting_contract(
        {
            "schema_version": "aan.articulated_benchtop_observation.v1",
            "status": "pass",
            "asset_entry_prim": ROOT,
            "runtime_profile": "isaac41",
            "runtime_profile_gate": {
                "status": "pass",
                "expected_version": "4.1",
                "observed_kit_version": (
                    "4.1.0-rc.7+4.1.14801.71533b68.gl"
                ),
                "reason": None,
            },
            "stage_up_axis": "Z",
            "meters_per_unit": 1.0,
            "warmup_frames": 50,
            "settle_frames": 240,
            "initial_root_pose": {
                "position_m": [0.0, 0.0, 0.103633],
                "orientation_wxyz": [0.5, 0.5, 0.5, 0.5],
            },
            "support_offset_base_local_m": [0.0, -0.103633, 0.0],
            "initial_joint_reset_positions": [
                {"dof_index": 0, "position": 1.0e-7},
                {"dof_index": 1, "position": 0.0},
                {"dof_index": 2, "position": -1.5556529270464334},
            ],
            "warmup_extent_m": [0.3893976, 0.35, 0.444873],
            "final_extent_m": [0.3893976, 0.35, 0.444873],
        }
    )

    assert mounting == {
        "schema_version": "aan.articulated_mounting.v1",
        "motion_mode": "fixed_base",
        "asset_entry_prim": ROOT,
        "coordinate_semantics": {
            "stage_up_axis": "Z",
            "linear_units": "meter",
            "quaternion_order": "wxyz",
            "support_frame": "runtime_articulation_root_pose_local",
            "mount_pose": (
                "support_plane_to_runtime_articulation_root_pose_"
                "world_axes_at_yaw_zero"
            ),
            "qualified_extents": (
                "world_axis_aligned_at_mount_pose_after_joint_reset"
            ),
        },
        "support_frame_root_local": {
            "translation_m": [0.0, -0.103633, 0.0],
            "rotation_wxyz": [1.0, 0.0, 0.0, 0.0],
        },
        "support_plane_to_root_mount_pose": {
            "translation_m": [0.0, 0.0, 0.103633],
            "rotation_wxyz": [0.5, 0.5, 0.5, 0.5],
        },
        "initial_joint_reset_positions": [
            {"dof_index": 0, "position": 0.0},
            {"dof_index": 1, "position": 0.0},
            {"dof_index": 2, "position": -1.5556529270464334},
        ],
        "qualified_reset_geometry": {
            "warmup_frames": 50,
            "warmup_extent_world_aabb_m": [0.3893976, 0.35, 0.444873],
            "settle_frames": 240,
            "final_extent_world_aabb_m": [0.3893976, 0.35, 0.444873],
        },
        "verification_required": "benchtop_stability",
    }
