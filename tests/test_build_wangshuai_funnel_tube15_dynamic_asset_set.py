from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts.build_wangshuai_funnel_tube15_dynamic_asset_set import (
    build_dynamic_asset_set,
    mesh_mass_properties,
)


EXACT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "wangshuai_funnel_tube15_exact_asset_set_20260826"
)


@pytest.mark.skipif(not EXACT.is_dir(), reason="exact Wangshuai asset set unavailable")
def test_geometry_integration_produces_expected_funnel_provisional_mass() -> None:
    from pxr import Usd

    asset = EXACT / "packages/funnel_small_v2_liquid_ready/asset.usda"
    stage = Usd.Stage.Open(str(asset))
    result = mesh_mass_properties(
        stage,
        "/FunnelSmallV2LiquidReady/Visual",
        density_kg_m3=2230.0,
    )
    assert result["volume_m3"] == pytest.approx(1.412707684769701e-05, rel=1e-8)
    assert result["mass_kg"] == pytest.approx(0.03150338137036433, rel=1e-8)
    assert all(value > 0.0 for value in result["diagonal_inertia_kg_m2"])
    assert len(result["center_of_mass_body_local_m"]) == 3


@pytest.mark.skipif(not EXACT.is_dir(), reason="exact Wangshuai asset set unavailable")
def test_dynamic_packages_remove_kinematic_mode_and_preserve_collision(tmp_path: Path) -> None:
    from pxr import Usd, UsdPhysics

    output = tmp_path / "dynamic"
    build_dynamic_asset_set(EXACT, output)
    index = json.loads((output / "asset_set_manifest.json").read_text())
    assert index["status"] == "candidate_runtime_pending"
    assert index["default_consumption"] == "dynamic"
    for item in index["assets"]:
        if item["id"] == "small_v2_liquid_seed_1948":
            continue
        package = output / item["package"]
        stage = Usd.Stage.Open(str(package / "asset.usda"))
        root = stage.GetDefaultPrim()
        kinematic = root.GetAttribute("physics:kinematicEnabled")
        assert not kinematic or kinematic.HasAuthoredValueOpinion() is False
        assert root.HasAPI(UsdPhysics.RigidBodyAPI)
        assert root.HasAPI(UsdPhysics.MassAPI)
        assert root.GetAttribute("physics:mass").Get() > 0.0
        manifest = json.loads((package / "evidence/manifest.json").read_text())
        assert manifest["claims"]["effective_kinematic"] is False
        assert manifest["claims"]["collision_geometry_unchanged"] is True
        assert manifest["claims"]["robot_policy_success"] is False
        assert manifest["physics_profile"]["quality_tier"] == "provisional_geometry"


@pytest.mark.skipif(not EXACT.is_dir(), reason="exact Wangshuai asset set unavailable")
def test_dynamic_set_reuses_overlay_byte_identically(tmp_path: Path) -> None:
    output = tmp_path / "dynamic"
    build_dynamic_asset_set(EXACT, output)
    original = EXACT / "packages/small_v2_liquid_seed_1948"
    copied = output / "packages/small_v2_liquid_seed_1948"
    assert sha256((copied / "asset.usda").read_bytes()).hexdigest() == sha256(
        (original / "asset.usda").read_bytes()
    ).hexdigest()
    manifest = json.loads((output / "asset_set_manifest.json").read_text())
    overlay = next(item for item in manifest["assets"] if item["contains_liquid"])
    assert overlay["particle_count"] == 1948
    assert overlay["overall_status"] == "pass"
