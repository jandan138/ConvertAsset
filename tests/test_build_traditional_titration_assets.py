from __future__ import annotations

import json

import pytest
from pxr import Usd, UsdGeom, UsdPhysics

from scripts.build_traditional_titration_assets import build, receiver_liquid_color
from scripts.promote_traditional_titration_assets import promote


def test_color_curve_has_colorless_endpoint_and_overshoot_bands() -> None:
    assert receiver_liquid_color(0.0).phase == "colorless"
    assert receiver_liquid_color(14.69).phase == "colorless"
    assert receiver_liquid_color(14.85).phase == "transition"
    assert receiver_liquid_color(15.0).phase == "endpoint_pale_pink"
    assert receiver_liquid_color(15.3).phase == "endpoint_pale_pink"
    assert receiver_liquid_color(15.31).phase == "overshoot"
    assert receiver_liquid_color(16.3).color == pytest.approx((0.75, 0.02, 0.2))


def test_build_emits_independent_assets_and_fixed_base_station(tmp_path) -> None:
    result = build(tmp_path / "titration")
    assert result.burette_asset.is_file()
    assert result.stand_asset.is_file()
    assert result.station_asset.is_file()

    stage = Usd.Stage.Open(str(result.station_asset))
    root = stage.GetPrimAtPath("/World/TitrationStation")
    instance = stage.GetPrimAtPath("/World/TitrationStation/Instance")
    body = stage.GetPrimAtPath("/World/TitrationStation/Instance/Body")
    burette_body = stage.GetPrimAtPath(
        "/World/TitrationStation/Instance/Burette/body_link"
    )
    handle = stage.GetPrimAtPath(
        "/World/TitrationStation/Instance/Burette/stopcock_handle_link"
    )
    assert root.HasAPI(UsdPhysics.ArticulationRootAPI)
    assert instance.IsA(UsdGeom.Xform)
    for prim in (body, burette_body, handle):
        assert prim.HasAPI(UsdPhysics.RigidBodyAPI)
        assert prim.GetAttribute("physics:kinematicEnabled").Get() is False
    assert stage.GetPrimAtPath("/World/TitrationStation/Instance/Joints/BaseFixed").IsA(
        UsdPhysics.FixedJoint
    )
    mount = stage.GetPrimAtPath(
        "/World/TitrationStation/Instance/Joints/StandToBurette"
    )
    assert mount.IsA(UsdPhysics.FixedJoint)
    assert tuple(mount.GetAttribute("physics:localPos0").Get()) == pytest.approx(
        (0.22, 0.0, 0.515)
    )
    rod = stage.GetPrimAtPath("/World/TitrationStation/Instance/Body/Visual/rod")
    assert rod.GetAttribute("height").Get() == pytest.approx(0.56)
    burette_root = stage.GetPrimAtPath("/World/TitrationStation/Instance/Burette")
    assert tuple(burette_root.GetAttribute("xformOp:translate").Get()) == pytest.approx(
        (0.22, 0.0, 0.515)
    )
    stopcock = stage.GetPrimAtPath(
        "/World/TitrationStation/Instance/Burette/stopcock_joint"
    )
    assert stopcock.GetAttribute("physics:lowerLimit").Get() == 0.0
    assert stopcock.GetAttribute("physics:upperLimit").Get() == 90.0


def test_station_controller_is_relocatable_and_has_no_falling_liquid(tmp_path) -> None:
    result = build(tmp_path / "titration")
    stage = Usd.Stage.Open(str(result.station_asset))
    paths = {str(prim.GetPath()) for prim in stage.Traverse()}
    assert not any(
        "droplet" in path.lower() or "stream" in path.lower() for path in paths
    )
    root = stage.GetPrimAtPath("/World/TitrationStation")
    assert root.GetRelationship("titration:receiverLiquidShader").IsValid()
    for name in (
        "titration:burette_liquid_volume_ml",
        "titration:dispensed_volume_ml",
        "titration:spilled_volume_ml",
        "titration:stopcock_angle_deg",
        "titration:endpoint_hold_seconds",
        "titration:task_success",
        "titration:overshoot",
    ):
        assert root.GetAttribute(name).IsValid()
    controller = (
        stage.GetPrimAtPath(
            "/World/TitrationStation/Instance/Runtime/TitrationFlowGraph/FlowController"
        )
        .GetAttribute("inputs:script")
        .Get()
    )
    assert 'ROOT = "/World/' not in controller
    assert "find_articulation_dof" in controller
    assert "get_dof_position" in controller
    physics_step = stage.GetPrimAtPath(
        "/World/TitrationStation/Instance/Runtime/TitrationFlowGraph/OnPhysicsStep"
    )
    assert physics_step.GetAttribute("node:type").Get() == (
        "isaacsim.core.nodes.OnPhysicsStep"
    )
    assert "receiverLiquidShader" in controller
    assert "Feedback/stream" not in controller


def test_manifests_are_source_bound_and_runtime_pending(tmp_path) -> None:
    result = build(tmp_path / "titration")
    for manifest_path in result.manifests:
        manifest = json.loads(manifest_path.read_text())
        assert manifest["source"]["archive_sha256"]
        assert manifest["source"]["reference_doc_sha256"]
    station = json.loads(result.station_manifest.read_text())
    assert station["overall_status"] == "candidate_runtime_qualification_pending"
    assert station["claims"]["robot_policy_success"] is False
    assert station["claims"]["isaac45_runtime_qualified"] is False


def test_promotion_requires_three_passing_cold_starts(tmp_path) -> None:
    result = build(tmp_path / "titration")
    reports = []
    for index in range(3):
        path = tmp_path / f"cold_{index}.json"
        path.write_text(json.dumps({"status": "pass", "runtime_version": "4.5.0"}))
        reports.append(path)
    receipt = promote(result.output, reports)
    assert json.loads(receipt.read_text())["status"] == "promoted"
    manifest = json.loads(result.station_manifest.read_text())
    assert manifest["overall_status"] == "pass"
    assert manifest["claims"]["runtime_cold_start_passes"] == 3


def test_promotion_rejects_blocked_runtime_report(tmp_path) -> None:
    result = build(tmp_path / "titration")
    reports = []
    for index, status in enumerate(("pass", "blocked", "pass")):
        path = tmp_path / f"cold_{index}.json"
        path.write_text(json.dumps({"status": status, "runtime_version": "4.5.0"}))
        reports.append(path)
    with pytest.raises(ValueError, match="must pass"):
        promote(result.output, reports)
