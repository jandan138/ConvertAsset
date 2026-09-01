from __future__ import annotations

import json

from pxr import Usd, UsdPhysics

from scripts.build_ika_oven_r15_instance_layout import build


def test_r15_places_every_oven_link_under_instance(tmp_path) -> None:
    result = build(tmp_path / "r15")
    stage = Usd.Stage.Open(str(result.asset_usd))
    links = [
        str(prim.GetPath())
        for prim in stage.Traverse()
        if prim.HasAPI(UsdPhysics.RigidBodyAPI)
    ]
    assert links
    assert all(path.startswith("/World/obj_oven/Instance/") for path in links)
    assert not stage.GetPrimAtPath("/World/obj_oven/Body")
    assert stage.GetPrimAtPath("/World/obj_oven/Instance/Body")
    assert stage.GetPrimAtPath(
        "/World/obj_oven/Instance/ControlPanel/Runtime/ControllerGraph"
    )
    for prim in stage.Traverse():
        if prim.IsA(UsdPhysics.Joint):
            for name in ("physics:body0", "physics:body1"):
                for target in prim.GetRelationship(name).GetTargets():
                    assert str(target).startswith("/World/obj_oven/Instance/")


def test_r15_manifest_keeps_r14_mechanics_and_instance_claim_pending(tmp_path) -> None:
    result = build(tmp_path / "r15")
    manifest = json.loads(result.manifest.read_text())
    assert manifest["overall_status"] == "candidate_runtime_qualification_pending"
    assert manifest["instance_layout"]["instance_prim_path"] == (
        "/World/obj_oven/Instance"
    )
    assert manifest["claims"]["all_links_under_instance"] is True
    assert manifest["claims"]["runtime_namespace_qualified"] is False
