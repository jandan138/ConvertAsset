from __future__ import annotations

from scripts.qualify_analytical_balance_lichen_task_interactions import (
    ANIMATION_OPEN_M,
    BALANCE_ROOT,
    BALANCE_SOURCE,
    PULLER_APPROACH_GAP_M,
    _aabb_overlap,
    _contact_cycle_gate,
    _expected_dof_mapping,
    _handle_follow_gate,
    _puller_close_start_end,
    _puller_start_end,
    _qualification_package_inputs,
    _qualification_runtime,
    _state_cycle_gate,
)


def test_expected_lichen_dof_mapping_covers_four_prismatic_doors() -> None:
    mapping = _expected_dof_mapping()

    assert [item[0] for item in mapping] == [0, 1, 2, 3]
    assert BALANCE_SOURCE == f"{BALANCE_ROOT}/Source"
    assert mapping[0][2] == f"{BALANCE_SOURCE}/Front_Sliding_Glass_Door/PrismaticJoint"
    assert mapping[1][2] == f"{BALANCE_SOURCE}/Left_Sliding_Glass_Door/PrismaticJoint"
    assert mapping[2][2] == f"{BALANCE_SOURCE}/Right_Sliding_Glass_Door/PrismaticJoint"
    assert mapping[3][2] == f"{BALANCE_SOURCE}/Top_Sliding_Glass/PrismaticJoint"


def test_lichen_state_cycle_gate_requires_open_and_close_readback() -> None:
    passed = _state_cycle_gate(
        semantic="front_door",
        target=0.105,
        target_band=(0.100, 0.110),
        target_observed=0.105,
        reset_observed=0.0,
        reset_band=(0.0, 0.002),
    )
    blocked = _state_cycle_gate(
        semantic="front_door",
        target=0.105,
        target_band=(0.100, 0.110),
        target_observed=0.0,
        reset_observed=0.0,
        reset_band=(0.0, 0.002),
    )

    assert passed["status"] == "pass"
    assert passed["method"] == "Isaac articulation state command/readback cycle"
    assert blocked["status"] == "blocked"


def test_lichen_handle_follow_gate_rejects_collapsed_rest_pose() -> None:
    rest = [0.0, -0.024855000898241997, 0.16856500506401062]
    handle = [0.0, -0.037355000898241997, 0.16856500506401062]
    opened = [rest[0] + ANIMATION_OPEN_M, rest[1], rest[2]]
    opened_handle = [handle[0] + ANIMATION_OPEN_M, handle[1], handle[2]]
    passed = _handle_follow_gate(
        closed_door=rest,
        closed_handle=handle,
        open_door=opened,
        open_handle=opened_handle,
        commanded=ANIMATION_OPEN_M,
        joint_after_step=ANIMATION_OPEN_M,
    )
    collapsed = _handle_follow_gate(
        closed_door=[0.037, 0.0, 0.0],
        closed_handle=[0.037, 0.0, 0.0],
        open_door=[0.125, 0.0, 0.0],
        open_handle=[0.125, 0.0, 0.0],
        commanded=ANIMATION_OPEN_M,
        joint_after_step=0.125,
    )

    assert passed["status"] == "pass"
    assert collapsed["status"] == "blocked"
    assert collapsed["rest_pose_pass"] is False


def test_lichen_qualification_report_abi_matches_articulated_finalizer() -> None:
    runtime = _qualification_runtime(
        {"status": "pass", "expected_version": "4.1", "observed_kit_version": "4.1.0"}
    )
    inputs = _qualification_package_inputs(
        profile_sha256="profile",
        source_sha256="source",
        manifest_sha256="manifest",
        asset_sha_before="asset",
        asset_sha_after="asset",
    )

    assert runtime["runtime_profile"] == "isaac41"
    assert runtime["source_mutation"] == "none"
    assert set(inputs["qualified_package"]) == {
        "asset_path",
        "asset_entry_prim",
        "runtime_profile",
        "prequalification_manifest_sha256",
        "asset_usd_sha256_before",
        "asset_usd_sha256_after",
    }
    assert inputs["qualified_package"]["asset_entry_prim"] == BALANCE_ROOT
    assert inputs["qualified_package"]["prequalification_manifest_sha256"] == "manifest"


def test_lichen_front_door_contact_gate_rejects_joint_command_and_rest_overlap() -> None:
    passed = _contact_cycle_gate(
        open_observed=0.105,
        closed_observed=0.0,
        rest_overlap=False,
        joint_commanded=False,
    )
    commanded = _contact_cycle_gate(
        open_observed=0.105,
        closed_observed=0.0,
        rest_overlap=False,
        joint_commanded=True,
    )
    overlapping = _contact_cycle_gate(
        open_observed=0.105,
        closed_observed=0.0,
        rest_overlap=True,
        joint_commanded=False,
    )
    stuck = _contact_cycle_gate(
        open_observed=0.0,
        closed_observed=0.0,
        rest_overlap=False,
        joint_commanded=False,
    )

    assert passed["status"] == "pass"
    assert passed["method"] == "session-only kinematic block contact on Front_Door_Handle"
    assert commanded["status"] == "blocked"
    assert overlapping["status"] == "blocked"
    assert stuck["status"] == "blocked"


def test_lichen_front_handle_rest_aabb_clears_housing_and_puller_moves_plus_x() -> None:
    handle = ((-0.006, -0.041355, 0.142565), (0.006, -0.033355, 0.194565))
    housing = ((-0.08914, -0.141785, 0.018), (0.08914, 0.141785, 0.06315))
    start, end = _puller_start_end(
        handle_rest_m=(0.0, -0.037355, 0.168565),
        handle_half_extent_m=(0.006, 0.004, 0.026),
    )
    close_start, close_end = _puller_close_start_end(
        handle_rest_m=(ANIMATION_OPEN_M, -0.037355, 0.168565),
        handle_half_extent_m=(0.006, 0.004, 0.026),
    )

    assert _aabb_overlap(handle, housing) is False
    assert start[0] < 0.0 < end[0]
    assert abs(end[0] - start[0] - ANIMATION_OPEN_M - PULLER_APPROACH_GAP_M) < 1e-9
    assert start[1] == end[1] == -0.037355
    assert start[2] == end[2] == 0.168565
    assert close_end[0] < close_start[0]
    assert abs(close_start[0] - close_end[0] - ANIMATION_OPEN_M - PULLER_APPROACH_GAP_M) < 1e-9
