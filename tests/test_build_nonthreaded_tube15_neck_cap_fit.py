from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_nonthreaded_tube15_neck_cap_fit import (
    BODY_BOTTOM_FIXED_M,
    CAP_INNER_SLEEVE_M,
    TARGET_NECK_START_M,
    build,
    warp_z,
)


SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "task11_r5_context_assets_20260824/target_tube_r2/package/asset.usd"
)


def test_piecewise_warp_preserves_tip_and_total_height() -> None:
    assert warp_z(0.0) == pytest.approx(0.0)
    assert warp_z(BODY_BOTTOM_FIXED_M) == pytest.approx(BODY_BOTTOM_FIXED_M)
    assert warp_z(0.095) == pytest.approx(TARGET_NECK_START_M)
    assert warp_z(0.101) == pytest.approx(0.101)
    assert 0.0232 < warp_z(0.052) < 0.052


@pytest.mark.skipif(not SOURCE.is_file(), reason="legacy non-threaded source unavailable")
def test_builds_body_cap_and_closed_identity_packages(tmp_path: Path) -> None:
    from pxr import Usd, UsdGeom, UsdPhysics

    output = build(SOURCE, tmp_path / "out")
    body = Usd.Stage.Open(str(output / "packages/body/asset.usda"))
    cap = Usd.Stage.Open(str(output / "packages/cap/asset.usda"))
    assembly = Usd.Stage.Open(str(output / "packages/closed_assembly/asset.usda"))
    assert body.GetDefaultPrim().HasAPI(UsdPhysics.RigidBodyAPI)
    assert cap.GetDefaultPrim().HasAPI(UsdPhysics.RigidBodyAPI)
    assert assembly.GetDefaultPrim().HasAPI(UsdPhysics.RigidBodyAPI)
    assert not UsdGeom.Xformable(body.GetDefaultPrim()).GetOrderedXformOps()
    assert not UsdGeom.Xformable(cap.GetDefaultPrim()).GetOrderedXformOps()
    assert not UsdGeom.Xformable(assembly.GetDefaultPrim()).GetOrderedXformOps()
    cap_child = assembly.GetPrimAtPath("/Tube15NonThreadedNeckCapFit/Cap")
    assert assembly.GetPrimAtPath("/Tube15NonThreadedNeckCapFit/Body/Visual")
    assert assembly.GetPrimAtPath("/Tube15NonThreadedNeckCapFit/Cap/Visual")
    assert UsdGeom.Xformable(cap_child).GetLocalTransformation().ExtractTranslation()[2] == pytest.approx(
        TARGET_NECK_START_M
    )
    assert all(
        not prim.HasAPI(UsdPhysics.RigidBodyAPI)
        for prim in Usd.PrimRange(assembly.GetDefaultPrim())
        if prim != assembly.GetDefaultPrim()
    )


@pytest.mark.skipif(not SOURCE.is_file(), reason="legacy non-threaded source unavailable")
def test_mating_profile_matches_effective_sleeve_not_total_cap_height(tmp_path: Path) -> None:
    output = build(SOURCE, tmp_path / "out")
    profile = json.loads((output / "mating_profile.json").read_text())
    assert profile["neck"]["length_m"] == pytest.approx(CAP_INNER_SLEEVE_M)
    assert profile["cap_inner_sleeve"]["length_m"] == pytest.approx(
        CAP_INNER_SLEEVE_M
    )
    assert profile["closed_pose"]["cap_translate_z_m"] == pytest.approx(
        TARGET_NECK_START_M
    )
    assert profile["radial_fit"]["single_side_clearance_m"] == pytest.approx(
        0.00025, abs=0.00005
    )
    assert profile["claims"]["thread_geometry_present"] is False
    assert profile["claims"]["existing_task_packages_replaced"] is False
