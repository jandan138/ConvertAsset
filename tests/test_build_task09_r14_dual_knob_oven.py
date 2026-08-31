from __future__ import annotations

import json

from pxr import Usd, UsdPhysics

from scripts.build_task09_r14_dual_knob_oven import build_dual_knob_oven


def test_r14_has_two_independent_physical_knobs_and_shared_controller(tmp_path) -> None:
    result = build_dual_knob_oven(tmp_path / "oven")

    stage = Usd.Stage.Open(str(result.asset_usd))
    assert stage
    aux = stage.GetPrimAtPath("/World/obj_oven/ControlPanel/AuxControlKnob")
    assert aux.IsValid()
    carrier = stage.GetPrimAtPath(
        "/World/obj_oven/ControlPanel/AuxControlKnob/PressCarrier"
    )
    rotor = stage.GetPrimAtPath("/World/obj_oven/ControlPanel/AuxControlKnob/Rotor")
    assert carrier.HasAPI(UsdPhysics.RigidBodyAPI)
    assert rotor.HasAPI(UsdPhysics.RigidBodyAPI)
    assert carrier.GetAttribute("xformOp:translate").Get()[0] == -0.22
    assert rotor.GetAttribute("xformOp:translate").Get()[0] == -0.22
    press = UsdPhysics.Joint(
        stage.GetPrimAtPath(
            "/World/obj_oven/ControlPanel/AuxControlKnob/Joints/Press"
        )
    )
    assert [str(path) for path in press.GetBody1Rel().GetTargets()] == [
        "/World/obj_oven/ControlPanel/AuxControlKnob/PressCarrier"
    ]
    script = stage.GetPrimAtPath(
        "/World/obj_oven/ControlPanel/Runtime/ControllerGraph/Controller"
    ).GetAttribute("inputs:script").Get()
    assert "KNOB_ROOTS = (KNOB_ROOT, AUX_KNOB_ROOT)" in script
    assert "for knob_root in KNOB_ROOTS:" in script
    assert "_root_uniform_scale(stage)" in script
    compile(script, "<dual-knob-controller>", "exec")


def test_r14_door_limit_damping_and_root_trs_are_authored(tmp_path) -> None:
    result = build_dual_knob_oven(tmp_path / "oven")
    stage = Usd.Stage.Open(str(result.asset_usd))
    door = stage.GetPrimAtPath("/World/obj_oven/Joints/DoorHinge")
    assert door.GetAttribute("drive:angular:physics:damping").Get() == 9.0
    assert door.GetAttribute("physics:upperLimit").Get() == 60.0
    root = stage.GetPrimAtPath("/World/obj_oven")
    assert root.GetAttribute("xformOpOrder").Get() == [
        "xformOp:translate",
        "xformOp:orient",
        "xformOp:scale",
    ]
    assert list(root.GetAttribute("xformOp:scale").Get()) == [1.0, 1.0, 1.0]
    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "candidate_runtime_qualification_pending"
    assert manifest["claims"]["dual_physical_knobs"] is False
