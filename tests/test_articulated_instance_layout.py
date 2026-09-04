from __future__ import annotations

from pathlib import Path

from pxr import Usd, UsdGeom, UsdPhysics

from convert_asset.asset_application_normalizer.articulated_instance_layout import (
    audit_fixed_base_articulation_layout,
    audit_instance_layout,
    author_fixed_base_articulation,
    move_asset_contents_under_instance,
)


def _fixture(path: Path) -> Path:
    stage = Usd.Stage.CreateNew(str(path))
    root = UsdGeom.Xform.Define(stage, "/World/obj_device").GetPrim()
    stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
    body = UsdGeom.Xform.Define(stage, "/World/obj_device/Body").GetPrim()
    door = UsdGeom.Xform.Define(stage, "/World/obj_device/Door").GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(body)
    UsdPhysics.RigidBodyAPI.Apply(door)
    joint = UsdPhysics.RevoluteJoint.Define(stage, "/World/obj_device/Joints/Door")
    joint.CreateBody0Rel().SetTargets([body.GetPath()])
    joint.CreateBody1Rel().SetTargets([door.GetPath()])
    root.SetCustomDataByKey("test", "preserved")
    stage.GetRootLayer().Save()
    return path


def test_move_wraps_complete_subtree_and_retargets_joint_links(tmp_path: Path) -> None:
    path = _fixture(tmp_path / "device.usda")
    stage = Usd.Stage.Open(str(path))
    move_asset_contents_under_instance(stage, "/World/obj_device")
    stage.GetRootLayer().Save()
    reopened = Usd.Stage.Open(str(path))
    assert reopened.GetPrimAtPath("/World/obj_device/Instance/Body").HasAPI(
        UsdPhysics.RigidBodyAPI
    )
    assert reopened.GetPrimAtPath("/World/obj_device/Instance/Door").HasAPI(
        UsdPhysics.RigidBodyAPI
    )
    joint = reopened.GetPrimAtPath("/World/obj_device/Instance/Joints/Door")
    assert joint.GetRelationship("physics:body0").GetTargets() == [
        "/World/obj_device/Instance/Body"
    ]
    assert joint.GetRelationship("physics:body1").GetTargets() == [
        "/World/obj_device/Instance/Door"
    ]
    assert audit_instance_layout(reopened, "/World/obj_device")["status"] == "pass"
    assert reopened.GetPrimAtPath("/World/obj_device/Instance").IsA(UsdGeom.Xform)


def test_audit_blocks_links_outside_instance(tmp_path: Path) -> None:
    stage = Usd.Stage.Open(str(_fixture(tmp_path / "device.usda")))
    report = audit_instance_layout(stage, "/World/obj_device")
    assert report["status"] == "blocked"
    assert len(report["links_outside_instance"]) == 2


def test_fixed_base_articulation_has_xform_instance_and_nonkinematic_links(
    tmp_path: Path,
) -> None:
    path = _fixture(tmp_path / "device.usda")
    stage = Usd.Stage.Open(str(path))
    move_asset_contents_under_instance(stage, "/World/obj_device")
    result = author_fixed_base_articulation(
        stage,
        "/World/obj_device",
        base_link="/World/obj_device/Instance/Body",
    )
    stage.GetRootLayer().Save()

    reopened = Usd.Stage.Open(str(path))
    root = reopened.GetPrimAtPath("/World/obj_device")
    body = reopened.GetPrimAtPath("/World/obj_device/Instance/Body")
    joint = reopened.GetPrimAtPath("/World/obj_device/Instance/Joints/BaseFixed")
    assert root.HasAPI(UsdPhysics.ArticulationRootAPI)
    assert root.GetAttribute("physxArticulation:articulationEnabled").Get() is True
    assert body.GetAttribute("physics:kinematicEnabled").Get() is False
    assert joint.GetRelationship("physics:body0").GetTargets() == [root.GetPath()]
    assert joint.GetRelationship("physics:body1").GetTargets() == [body.GetPath()]
    assert result["status"] == "pass"
    assert (
        audit_fixed_base_articulation_layout(
            reopened,
            "/World/obj_device",
            base_link=str(body.GetPath()),
        )["status"]
        == "pass"
    )


def test_fixed_base_audit_blocks_kinematic_base(tmp_path: Path) -> None:
    path = _fixture(tmp_path / "device.usda")
    stage = Usd.Stage.Open(str(path))
    move_asset_contents_under_instance(stage, "/World/obj_device")
    author_fixed_base_articulation(
        stage,
        "/World/obj_device",
        base_link="/World/obj_device/Instance/Body",
    )
    stage.GetPrimAtPath("/World/obj_device/Instance/Body").GetAttribute(
        "physics:kinematicEnabled"
    ).Set(True)
    report = audit_fixed_base_articulation_layout(
        stage,
        "/World/obj_device",
        base_link="/World/obj_device/Instance/Body",
    )
    assert report["status"] == "blocked"
    assert report["kinematic_link_prim_paths"] == ["/World/obj_device/Instance/Body"]
