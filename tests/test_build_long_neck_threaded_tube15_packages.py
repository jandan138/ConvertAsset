from __future__ import annotations

import json

import pytest
from pxr import Usd, UsdGeom, UsdPhysics, UsdUtils

from scripts.build_long_neck_threaded_tube15_packages import build_packages


def test_builder_splits_identity_dynamic_body_and_closed_cap(tmp_path) -> None:
    result = build_packages(tmp_path / "out")

    cases = {
        "body": ("/World/Tube15LongNeckThreadedBody", 0.015),
        "cap": ("/World/Tube15LongNeckThreadedClosedCap", 0.002),
    }
    for name, (entry, mass) in cases.items():
        stage = Usd.Stage.Open(str(result.packages[name] / "asset.usd"))
        assert stage and stage.GetDefaultPrim().GetPath() == "/World"
        assert stage.GetRootLayer().subLayerPaths == []
        prim = stage.GetPrimAtPath(entry)
        assert prim.IsValid() and prim.HasAPI(UsdPhysics.RigidBodyAPI)
        assert prim.GetAttribute("physics:kinematicEnabled").Get() in (None, False)
        assert UsdPhysics.MassAPI(prim).GetMassAttr().Get() == pytest.approx(mass)
        assert not UsdGeom.Xformable(prim).GetOrderedXformOps() or list(
            UsdGeom.Xformable(prim).GetLocalTransformation().ExtractTranslation()
        ) == [0.0, 0.0, 0.0]
        colliders = [
            item for item in stage.Traverse() if item.HasAPI(UsdPhysics.CollisionAPI)
        ]
        assert len(colliders) == 1
        assert colliders[0].GetAttribute("physics:approximation").Get() == "sdf"
        _, _, unresolved = UsdUtils.ComputeAllDependencies(
            str(result.packages[name] / "asset.usd")
        )
        assert list(unresolved) == []
        assert not any(
            prim.HasAttribute("info:mdl:sourceAsset") for prim in stage.Traverse()
        )


def test_manifest_truthfully_promotes_geometry_and_blocks_thread_interaction(
    tmp_path,
) -> None:
    result = build_packages(tmp_path / "out")
    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))

    assert manifest["source"]["sha256"] == (
        "0f279e39685656b508ed6b359f8dc56be099263364084e04ab812170c9ca3be0"
    )
    assert manifest["lineage"]["geometry_fingerprint_matches_long_neck_master"] is True
    assert manifest["thread_profile"]["body_external_turns"] == 4.0
    assert manifest["thread_profile"]["cap_internal_turns"] == 4.0
    assert manifest["cap_topology"]["closed_top"] is True
    assert manifest["claims"]["dynamic_geometry_ready"] is False
    assert manifest["claims"]["thread_interaction_ready"] is False
    assert manifest["claims"]["liquid_container_ready"] is False
    profile = json.loads(result.assembly_profile.read_text(encoding="utf-8"))
    assert profile["cap_pose"]["xyz_m"] == [0.0, 0.0, 0.10998681642541698]
    assert profile["cap_pose"]["wxyz"] == [0.5569506, 0.0, 0.0, 0.8305456]
