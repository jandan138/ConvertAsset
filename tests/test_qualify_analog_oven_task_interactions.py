from __future__ import annotations

from scripts.qualify_analog_oven_task_interactions import (
    OVEN_ROOT,
    OVEN_SOURCE,
    _expected_dof_mapping,
    _state_cycle_gate,
)


def test_expected_oven_dof_mapping_covers_all_eleven_source_joints() -> None:
    mapping = _expected_dof_mapping()

    assert [item[0] for item in mapping] == list(range(11))
    assert OVEN_SOURCE == f"{OVEN_ROOT}/Source"
    assert mapping[2][2] == f"{OVEN_SOURCE}/group_4/RevoluteJoint"
    assert mapping[3][2] == f"{OVEN_SOURCE}/group_5/RevoluteJoint"
    assert mapping[9][2] == f"{OVEN_SOURCE}/group_11/RevoluteJoint"


def test_state_cycle_gate_requires_target_and_reset_readback() -> None:
    passed = _state_cycle_gate(
        semantic="temperature_dial",
        target=1.0471975512,
        target_band=(0.8726646260, 1.2217304764),
        target_observed=1.0471975512,
        reset_observed=0.0,
        reset_band=(-0.0349065850, 0.0349065850),
    )
    blocked = _state_cycle_gate(
        semantic="temperature_dial",
        target=1.0471975512,
        target_band=(0.8726646260, 1.2217304764),
        target_observed=0.0,
        reset_observed=0.0,
        reset_band=(-0.0349065850, 0.0349065850),
    )

    assert passed["status"] == "pass"
    assert passed["method"] == "Isaac articulation state command/readback cycle"
    assert blocked["status"] == "blocked"
