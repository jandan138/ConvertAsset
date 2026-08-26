from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_threaded_tube15_fusion import (
    EXPECTED_SOURCE_SHA256,
    SOURCE_CAP,
    SOURCE_TUBE,
    build_fusion,
)


SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/"
    "incoming/from_wangshuai/shiguan.usd"
)


@pytest.mark.skipif(not SOURCE.is_file(), reason="threaded source delivery unavailable")
def test_builds_identity_dual_packages_at_real_15ml_scale(tmp_path: Path) -> None:
    result = build_fusion(source=SOURCE, out=tmp_path)

    assert result["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert result["source_prims"] == {"body": SOURCE_TUBE, "cap": SOURCE_CAP}
    assert result["body_dimensions_m"]["height"] == pytest.approx(0.101, abs=2e-6)
    assert result["body_dimensions_m"]["diameter"] == pytest.approx(0.01722, abs=5e-5)
    assert result["cap_dimensions_m"]["height"] == pytest.approx(0.01874, abs=2e-6)
    assert (tmp_path / "body/package/asset.usda").is_file()
    assert (tmp_path / "cap/package/asset.usda").is_file()
    assert (tmp_path / "assembly.usda").is_file()

    from pxr import Usd, UsdGeom, UsdPhysics

    body = Usd.Stage.Open(str(tmp_path / "body/package/asset.usda"))
    root = body.GetPrimAtPath("/World/TubeBody")
    assert root.HasAPI(UsdPhysics.RigidBodyAPI)
    assert UsdGeom.Xformable(root).GetOrderedXformOps() == []
    collider = body.GetPrimAtPath("/World/TubeBody/Collision")
    assert collider.HasAPI(UsdPhysics.CollisionAPI)
    assert collider.GetAttribute("physics:approximation").Get() == "sdf"
    assert collider.GetAttribute("physxSDFMeshCollision:sdfResolution").Get() == 512
    assert body.GetPrimAtPath("/World/Cube").IsValid() is False

    cap = Usd.Stage.Open(str(tmp_path / "cap/package/asset.usda"))
    cap_root = cap.GetPrimAtPath("/World/Cap")
    assert cap_root.HasAPI(UsdPhysics.RigidBodyAPI)
    assert UsdGeom.Xformable(cap_root).GetOrderedXformOps() == []
    assert cap.GetPrimAtPath("/World/Cap/Collision").GetAttribute(
        "physics:approximation"
    ).Get() == "sdf"
    top = cap.GetPrimAtPath("/World/Cap/CapTop")
    assert top.IsValid()
    assert top.HasAPI(UsdPhysics.CollisionAPI)
    cylinder = UsdGeom.Cylinder(top)
    assert cylinder.GetAxisAttr().Get() == UsdGeom.Tokens.z
    assert cylinder.GetRadiusAttr().Get() == pytest.approx(0.0089)
    assert cylinder.GetHeightAttr().Get() == pytest.approx(0.0015)
    top_translate = UsdGeom.Xformable(top).GetOrderedXformOps()[0].Get()
    visual_extent = UsdGeom.Boundable(
        cap.GetPrimAtPath("/World/Cap/Visual")
    ).GetExtentAttr().Get()
    assert tuple(top_translate) == pytest.approx(
        (0.0, 0.0, float(visual_extent[1][2]) - 0.00075)
    )


@pytest.mark.skipif(not SOURCE.is_file(), reason="threaded source delivery unavailable")
def test_pair_profile_is_empty_asset_first_and_forbids_fake_screw(tmp_path: Path) -> None:
    build_fusion(source=SOURCE, out=tmp_path)
    profile = json.loads((tmp_path / "thread_pair_profile.json").read_text())

    assert profile["delivery"]["base_assets_include_particles"] is False
    assert profile["thread_semantics"] == "geometry_contact_no_joint_no_z_trajectory"
    assert profile["forbidden"]["bottom_cube"] is True
    assert profile["forbidden"]["overlapping_full_body_sdf"] is True
    assert len(profile["contact_candidates"]) == 3
