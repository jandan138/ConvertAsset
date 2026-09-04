from __future__ import annotations

import json

from pxr import Usd

from scripts.build_ika_oven_r17_teleop_hardened import (
    advance_knob_rotation,
    build,
)


R16_ASSET = (
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "ika_oven_125_task09_r16_fixed_articulation_20260904/package/asset.usd"
)
KNOBS = (
    "/World/obj_oven/Instance/ControlPanel/ControlKnob",
    "/World/obj_oven/Instance/ControlPanel/AuxControlKnob",
)


def test_rotation_state_keeps_last_sample_across_pose_misses() -> None:
    first = advance_knob_rotation(None, 0.0, 0.0)
    missing = advance_knob_rotation(first.angle, first.accumulator, None)
    recovered = advance_knob_rotation(missing.angle, missing.accumulator, 45.0)

    assert missing.angle == 0.0
    assert missing.accumulator == 0.0
    assert missing.detents == 0
    assert recovered.detents == 3
    assert recovered.accumulator == 0.0


def test_rotation_state_drains_large_motion_without_clearing_residual() -> None:
    initial = advance_knob_rotation(None, 0.0, 0.0)
    burst = advance_knob_rotation(initial.angle, initial.accumulator, 90.0)
    drained = advance_knob_rotation(burst.angle, burst.accumulator, 90.0)

    assert burst.detents == 4
    assert burst.accumulator == 30.0
    assert drained.detents == 2
    assert drained.accumulator == 0.0


def test_rotation_state_subthreshold_jitter_does_not_emit_detent() -> None:
    state = advance_knob_rotation(None, 0.0, 0.0)
    for angle in (3.0, -2.0, 4.0, 0.0):
        state = advance_knob_rotation(state.angle, state.accumulator, angle)
        assert state.detents == 0
    assert state.accumulator == 0.0


def test_r17_preserves_r16_prim_paths_and_adds_only_diagnostics(tmp_path) -> None:
    result = build(tmp_path / "r17")
    before = Usd.Stage.Open(R16_ASSET)
    after = Usd.Stage.Open(str(result.asset_usd))
    assert {str(prim.GetPath()) for prim in before.Traverse()} == {
        str(prim.GetPath()) for prim in after.Traverse()
    }

    for path in KNOBS:
        knob = after.GetPrimAtPath(path)
        assert knob.GetAttribute("oven:physicalPoseSampleValid").Get() is False
        assert knob.GetAttribute("oven:poseMissCount").Get() == 0
        assert knob.GetAttribute("oven:lastPhysicalDeltaDegrees").Get() == 0.0
        assert knob.GetAttribute("oven:detentEventCount").Get() == 0

    controller = (
        after.GetPrimAtPath(
            "/World/obj_oven/Instance/ControlPanel/Runtime/ControllerGraph/Controller"
        )
        .GetAttribute("inputs:script")
        .Get()
    )
    assert "return _physx_pose(path) or _usd_pose(stage, path)" in controller
    assert "carrier_pose = _physx_pose(carrier_path)" in controller
    assert "rotor_pose = _physx_pose(rotor_path)" in controller
    assert "if abs(delta) > 60.0" not in controller
    assert "max(-4, min(4" in controller


def test_r17_manifest_stays_pending_until_dual_runtime_qualification(tmp_path) -> None:
    result = build(tmp_path / "r17")
    manifest = json.loads(result.manifest.read_text())
    assert manifest["overall_status"] == "candidate_runtime_qualification_pending"
    assert manifest["claims"]["isaac45_teleop_controls_qualified"] is False
    assert manifest["claims"]["isaac41_regression_passed"] is False
    assert manifest["claims"]["robot_policy_success"] is False
