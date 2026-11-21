from __future__ import annotations

import json

from pxr import Usd, UsdGeom, UsdPhysics

from scripts.build_ika_oven_r16_fixed_articulation import build


R15_ASSET = (
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "ika_oven_125_task09_r15_instance_layout_20260901/package/asset.usd"
)


def test_r16_is_a_fixed_base_articulation_with_stable_paths(tmp_path) -> None:
    result = build(tmp_path / "r16")
    stage = Usd.Stage.Open(str(result.asset_usd))
    root = stage.GetPrimAtPath("/World/obj_oven")
    instance = stage.GetPrimAtPath("/World/obj_oven/Instance")
    body = stage.GetPrimAtPath("/World/obj_oven/Instance/Body")
    fixed = stage.GetPrimAtPath("/World/obj_oven/Instance/Joints/BaseFixed")

    assert root.HasAPI(UsdPhysics.ArticulationRootAPI)
    assert root.GetAttribute("physxArticulation:articulationEnabled").Get() is True
    assert instance.IsA(UsdGeom.Xform)
    assert body.GetAttribute("physics:kinematicEnabled").Get() is False
    assert fixed.IsA(UsdPhysics.FixedJoint)
    assert fixed.GetRelationship("physics:body0").GetTargets() == [root.GetPath()]
    assert fixed.GetRelationship("physics:body1").GetTargets() == [body.GetPath()]
    assert stage.GetPrimAtPath("/World/obj_oven/Instance/Joints/DoorHinge")
    assert stage.GetPrimAtPath(
        "/World/obj_oven/Instance/ControlPanel/Runtime/ControllerGraph"
    )


def test_r16_manifest_is_runtime_pending_and_does_not_overclaim(tmp_path) -> None:
    result = build(tmp_path / "r16")
    manifest = json.loads(result.manifest.read_text())
    assert manifest["overall_status"] == "candidate_runtime_qualification_pending"
    assert manifest["claims"]["fixed_base_articulation"] is True
    assert manifest["claims"]["instance_xform"] is True
    assert manifest["claims"]["runtime_namespace_qualified"] is False
    assert manifest["claims"]["robot_policy_success"] is False


def test_r16_preserves_every_r15_prim_path_and_only_adds_base_fixed(tmp_path) -> None:
    result = build(tmp_path / "r16")
    before = Usd.Stage.Open(R15_ASSET)
    after = Usd.Stage.Open(str(result.asset_usd))
    before_paths = {str(prim.GetPath()) for prim in before.Traverse()}
    after_paths = {str(prim.GetPath()) for prim in after.Traverse()}
    assert before_paths <= after_paths
    assert after_paths - before_paths == {"/World/obj_oven/Instance/Joints/BaseFixed"}
