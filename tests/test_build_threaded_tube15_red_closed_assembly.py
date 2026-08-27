from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_threaded_tube15_red_closed_assembly import (
    CAP_CLOSED_Z_M,
    CAP_CLOSED_YAW_DEG,
    build,
)


SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "wangshuai_funnel_tube15_dynamic_asset_set_20260827"
)


@pytest.mark.skipif(not SOURCE.is_dir(), reason="dynamic source set unavailable")
def test_builds_one_dynamic_closed_assembly_with_red_cap(tmp_path: Path) -> None:
    from pxr import Usd, UsdGeom, UsdPhysics, UsdShade

    output = build(SOURCE, tmp_path / "asset_set")
    package = output / "packages/threaded_tube15_red_closed_assembly"
    stage = Usd.Stage.Open(str(package / "asset.usda"))
    root = stage.GetDefaultPrim()
    assert str(root.GetPath()) == "/ThreadedTube15RedClosed"
    assert root.HasAPI(UsdPhysics.RigidBodyAPI)
    assert root.HasAPI(UsdPhysics.MassAPI)
    assert root.GetAttribute("physics:mass").Get() == pytest.approx(0.017)
    assert not root.GetAttribute("physics:kinematicEnabled").HasAuthoredValueOpinion()
    assert all(
        not prim.HasAPI(UsdPhysics.RigidBodyAPI)
        for prim in Usd.PrimRange(root)
        if prim != root
    )

    cap = stage.GetPrimAtPath("/ThreadedTube15RedClosed/Cap")
    matrix = UsdGeom.Xformable(cap).GetLocalTransformation()
    assert matrix.ExtractTranslation()[2] == pytest.approx(CAP_CLOSED_Z_M)
    assert cap.GetAttribute("scenarioForge:closedYawDegrees").Get() == pytest.approx(
        CAP_CLOSED_YAW_DEG
    )
    shader = UsdShade.Shader(
        stage.GetPrimAtPath("/ThreadedTube15RedClosed/Looks/RedCapPP/Shader")
    )
    assert tuple(shader.GetInput("diffuseColor").Get()) == pytest.approx(
        (0.56, 0.004, 0.008)
    )
    assert shader.GetInput("roughness").Get() == pytest.approx(0.42)
    assert stage.GetPrimAtPath(
        "/ThreadedTube15RedClosed/Cap/node_/mesh_"
    ).HasAPI(UsdPhysics.CollisionAPI)


@pytest.mark.skipif(not SOURCE.is_dir(), reason="dynamic source set unavailable")
def test_manifest_preserves_source_collision_and_closed_top_claim(tmp_path: Path) -> None:
    output = build(SOURCE, tmp_path / "asset_set")
    package = output / "packages/threaded_tube15_red_closed_assembly"
    manifest = json.loads((package / "evidence/manifest.json").read_text())
    assert manifest["overall_status"] == "candidate_runtime_pending"
    assert manifest["claims"]["single_rigid_body_closed_assembly"] is True
    assert manifest["claims"]["source_collision_geometry_unchanged"] is True
    assert manifest["claims"]["closed_top_source_geometry"] is True
    assert manifest["claims"]["cap_fixed_to_body"] is True
    assert manifest["claims"]["cap_tightening_task_success"] is False
    assert manifest["closed_pose"] == {
        "cap_translate_xyz_m": [0.0, 0.0, CAP_CLOSED_Z_M],
        "cap_yaw_deg": CAP_CLOSED_YAW_DEG,
        "basis": "scaled_source_gravity_seated_phase",
    }
    assert (package / "deps/body/asset.usda").read_bytes() == (
        SOURCE / "packages/tube15_threaded_liquid_dynamic/asset.usda"
    ).read_bytes()
    assert (package / "deps/cap/asset.usda").read_bytes() == (
        SOURCE / "packages/tube15_threaded_closed_cap_dynamic/asset.usda"
    ).read_bytes()
