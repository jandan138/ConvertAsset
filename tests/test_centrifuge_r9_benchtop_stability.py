from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.qualify_articulated_benchtop_stability import (
    _evaluate_stability_observation,
    _merge_stability_gate,
    _scoped_physx_error_lines,
)


def _passing_observation() -> dict[str, object]:
    return {
        "release_height_m": 0.01,
        "warmup_frames": 50,
        "settle_frames": 240,
        "table_top_z_m": -0.01,
        "initial_root_pose": {
            "position_m": [0.0, 0.0, 0.103633],
            "orientation_wxyz": [1.0, 0.0, 0.0, 0.0],
        },
        "final_root_pose": {
            "position_m": [0.0, 0.0, 0.093633],
            "orientation_wxyz": [1.0, 0.0, 0.0, 0.0],
        },
        "initial_extent_m": [0.32123, 0.35, 0.22597],
        "final_extent_m": [0.3211, 0.3501, 0.2259],
        "final_support_world_m": [0.0, 0.0, -0.0097],
        "source_integrity": {"status": "pass"},
    }


def test_stability_gate_accepts_the_exact_release_and_settle_protocol() -> None:
    gate = _evaluate_stability_observation(
        _passing_observation(),
        scoped_physx_errors=[],
    )

    assert gate["status"] == "pass"
    assert gate["root_tilt_deg"] == pytest.approx(0.0)
    assert gate["support_gap_m"] == pytest.approx(0.0003)
    assert gate["table_penetration_m"] == pytest.approx(0.0)
    assert gate["maximum_extent_relative_error"] < 0.05


@pytest.mark.parametrize(
    ("field", "value", "blocked_reason"),
    [
        (
            "final_root_pose",
            {
                "position_m": [0.0, 0.0, 0.093633],
                "orientation_wxyz": [0.9914449, 0.1305262, 0.0, 0.0],
            },
            "root_tilt_exceeds_limit",
        ),
        (
            "final_extent_m",
            [0.36, 0.35, 0.22597],
            "extent_drift_exceeds_limit",
        ),
        (
            "final_support_world_m",
            [0.0, 0.0, 0.002],
            "support_gap_exceeds_limit",
        ),
        (
            "final_support_world_m",
            [0.0, 0.0, -0.012],
            "table_penetration",
        ),
    ],
)
def test_stability_gate_blocks_each_geometry_failure(
    field: str,
    value: object,
    blocked_reason: str,
) -> None:
    observation = _passing_observation()
    observation[field] = value

    gate = _evaluate_stability_observation(
        observation,
        scoped_physx_errors=[],
    )

    assert gate["status"] == "blocked"
    assert blocked_reason in gate["blocked_reasons"]


def test_scoped_physx_errors_are_not_confused_with_global_runtime_noise() -> None:
    stderr = "\n".join(
        [
            "[Error] [omni.physx.plugin] unrelated /World/Other mass problem",
            "[Error] [omni.physx.plugin] invalid body /World/Centrifuge/group_0",
            "PhysX Error: Centrifuge support collider failed",
        ]
    )

    errors = _scoped_physx_error_lines(stderr, "/World/Centrifuge")
    gate = _evaluate_stability_observation(
        _passing_observation(),
        scoped_physx_errors=errors,
    )

    assert len(errors) == 2
    assert gate["status"] == "blocked"
    assert "scoped_physx_errors" in gate["blocked_reasons"]


def test_stability_gate_is_merged_into_the_finalizer_bound_runtime_report() -> None:
    original = {
        "schema_version": "aan.articulation_runtime_qualification.v1",
        "status": "pass",
        "inputs": {
            "device_profile": {
                "schema_version": "aan.articulated_device_profile.v1",
                "profile_sha256": "a" * 64,
                "source_sha256": "b" * 64,
            }
        },
        "runtime": {"runtime_profile": "isaac41"},
        "task_gates": {
            "lid_contact_cycle": {"status": "pass"},
            "button_contact_cycle": {"status": "pass"},
        },
    }
    before = deepcopy(original)
    gate = _evaluate_stability_observation(
        _passing_observation(),
        scoped_physx_errors=[],
    )

    merged = _merge_stability_gate(
        original,
        gate=gate,
        profile_sha256="a" * 64,
        source_sha256="b" * 64,
    )

    assert original == before
    assert merged["status"] == "pass"
    assert merged["task_gates"]["benchtop_stability"]["status"] == "pass"
    assert merged["inputs"]["device_profile"]["profile_sha256"] == "a" * 64
