from __future__ import annotations

from scripts.build_centrifuge_device_profile_r9 import (
    ROOT,
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
