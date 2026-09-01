from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_task08_assisted_thread_assets import (
    CAP_ENTRY,
    SOURCE_SET,
    TUBE_ENTRY,
    build,
)


@pytest.mark.skipif(not SOURCE_SET.is_dir(), reason="Task08 r12 source set unavailable")
def test_builds_smooth_proxy_packages_without_changing_visual_sources(
    tmp_path: Path,
) -> None:
    from pxr import Usd, UsdGeom, UsdPhysics

    output = build(tmp_path / "assisted_thread")
    for package_id, entry, source_package in (
        ("tube15_long_neck_assisted_thread_body_r2", TUBE_ENTRY, "tube"),
        ("tube15_long_neck_assisted_thread_cap_r2", CAP_ENTRY, "cap"),
    ):
        package = output / "packages" / package_id
        stage = Usd.Stage.Open(str(package / "asset.usd"))
        assert str(stage.GetDefaultPrim().GetPath()) == entry
        root = stage.GetPrimAtPath(entry)
        assert root.HasAPI(UsdPhysics.RigidBodyAPI)
        detailed = stage.GetPrimAtPath(f"{entry}/node_/mesh_")
        assert detailed.IsA(UsdGeom.Mesh)
        assert detailed.GetAttribute("physics:collisionEnabled").Get() is False
        proxies = stage.GetPrimAtPath(f"{entry}/__aan_collision_proxy")
        assert proxies
        colliders = [
            prim
            for prim in Usd.PrimRange(proxies)
            if prim.HasAPI(UsdPhysics.CollisionAPI)
        ]
        assert colliders
        enabled = [
            prim
            for prim in colliders
            if prim.GetAttribute("physics:collisionEnabled").Get() is True
        ]
        if source_package == "cap":
            assert [prim.GetName() for prim in enabled] == ["grasp_box"]
        else:
            assert len(enabled) == len(colliders)
        assert (
            package / f"deps/{source_package}/asset.usd"
        ).read_bytes() == (
            SOURCE_SET
            / "packages"
            / (
                "tube15_long_neck_threaded_body_glass_v1_2"
                if source_package == "tube"
                else "tube15_long_neck_threaded_closed_cap_red_v1_2"
            )
            / "asset.usd"
        ).read_bytes()


@pytest.mark.skipif(not SOURCE_SET.is_dir(), reason="Task08 r12 source set unavailable")
def test_manifest_declares_assisted_not_contact_threading(tmp_path: Path) -> None:
    output = build(tmp_path / "assisted_thread")
    manifest = json.loads((output / "asset_set_manifest.json").read_text())
    assert manifest["status"] == "candidate_runtime_pending"
    assert manifest["interaction_contract"] == {
        "visual_thread_preserved": True,
        "fine_thread_contact_enabled": False,
        "smooth_proxy_collision": True,
        "effective_lead_m_per_turn": 0.0076,
        "physical_thread_contact_claimed": False,
        "grasp_proxy_collision_path": "__aan_collision_proxy/grasp_box",
        "grasp_proxy_disable_state": "capture",
        "tube_grasp_proxy_collision_path": "__aan_collision_proxy/grasp_box",
    }
    assert manifest["claims"]["thread_interaction_ready"] is False
    assert manifest["claims"]["robot_policy_success"] is False


@pytest.mark.skipif(not SOURCE_SET.is_dir(), reason="Task08 r12 source set unavailable")
def test_cap_adds_flat_high_friction_grasp_proxy_for_pickup_only(
    tmp_path: Path,
) -> None:
    from pxr import Usd, UsdGeom, UsdPhysics

    output = build(tmp_path / "assisted_thread")
    package = output / "packages/tube15_long_neck_assisted_thread_cap_r2"
    stage = Usd.Stage.Open(str(package / "asset.usd"))
    grasp = stage.GetPrimAtPath(CAP_ENTRY + "/__aan_collision_proxy/grasp_box")
    assert grasp.IsA(UsdGeom.Cube)
    assert grasp.HasAPI(UsdPhysics.CollisionAPI)
    assert grasp.GetAttribute("physics:collisionEnabled").Get() is True
    assert grasp.GetAttribute("scenarioForge:graspOnly").Get() is True
    assert tuple(grasp.GetAttribute("xformOp:scale").Get()) == pytest.approx(
        (0.018, 0.018, 0.014)
    )
    material = stage.GetPrimAtPath(CAP_ENTRY + "/__aan_grasp_material")
    assert material.GetAttribute("physics:staticFriction").Get() == pytest.approx(1.0)
    assert material.GetAttribute("physics:dynamicFriction").Get() == pytest.approx(0.9)
    manifest = json.loads((output / "asset_set_manifest.json").read_text())
    assert manifest["interaction_contract"]["grasp_proxy_collision_path"] == (
        "__aan_collision_proxy/grasp_box"
    )
    assert manifest["interaction_contract"]["grasp_proxy_disable_state"] == "capture"


@pytest.mark.skipif(not SOURCE_SET.is_dir(), reason="Task08 r12 source set unavailable")
def test_tube_adds_persistent_grasp_box_below_the_thread(tmp_path: Path) -> None:
    from pxr import Usd, UsdGeom, UsdPhysics

    output = build(tmp_path / "assisted_thread")
    package = output / "packages/tube15_long_neck_assisted_thread_body_r2"
    stage = Usd.Stage.Open(str(package / "asset.usd"))
    grasp = stage.GetPrimAtPath(TUBE_ENTRY + "/__aan_collision_proxy/grasp_box")
    assert grasp.IsA(UsdGeom.Cube)
    assert grasp.HasAPI(UsdPhysics.CollisionAPI)
    assert grasp.GetAttribute("scenarioForge:graspOnly").Get() is False
    assert tuple(grasp.GetAttribute("xformOp:translate").Get()) == pytest.approx(
        (0.0, 0.0, 0.085)
    )
    assert tuple(grasp.GetAttribute("xformOp:scale").Get()) == pytest.approx(
        (0.018, 0.018, 0.018)
    )
