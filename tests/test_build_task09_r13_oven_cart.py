from __future__ import annotations

import json
from pathlib import Path

import pytest
from pxr import Usd, UsdGeom, UsdPhysics

from scripts.build_task09_r13_oven_cart import build_cart


def test_compact_cart_preserves_member_thickness_and_adds_support(tmp_path: Path) -> None:
    result = build_cart(tmp_path / "cart")

    stage = Usd.Stage.Open(str(result.asset_usd))
    assert stage and stage.GetDefaultPrim().GetPath() == "/World"
    cart = stage.GetPrimAtPath("/World/OvenCart")
    assert cart.IsValid()
    assert not UsdGeom.Xformable(cart).GetOrderedXformOps()
    cache = UsdGeom.BBoxCache(0, ["default", "render", "proxy"], useExtentsHint=True)
    bounds = cache.ComputeWorldBound(cart).ComputeAlignedRange()
    size = bounds.GetSize()
    assert [round(float(value), 3) for value in size] == [0.9, 0.76, 0.755]

    support = stage.GetPrimAtPath("/World/OvenCart/__aan_support_surface")
    assert support.GetTypeName() == "Cube"
    assert support.HasAPI(UsdPhysics.CollisionAPI)
    assert support.GetAttribute("physics:collisionEnabled").Get() is True
    assert UsdGeom.Imageable(support).GetVisibilityAttr().Get() == UsdGeom.Tokens.invisible
    assert list(support.GetAttribute("xformOp:scale").Get()) == pytest.approx(
        [0.42, 0.36, 0.02]
    )
    assert list(support.GetAttribute("xformOp:translate").Get()) == pytest.approx(
        [0.0, 0.0, 0.735]
    )

    left = stage.GetPrimAtPath("/World/OvenCart/Colliders/Leg_00")
    right = stage.GetPrimAtPath("/World/OvenCart/Colliders/Leg_02")
    assert left.GetAttribute("xformOp:translate").Get()[0] == pytest.approx(-0.425)
    assert right.GetAttribute("xformOp:translate").Get()[0] == pytest.approx(0.425)
    assert left.GetAttribute("xformOp:scale").Get()[0] == pytest.approx(0.025)


def test_cart_package_is_source_bound_and_static_support_promoted_candidate(
    tmp_path: Path,
) -> None:
    result = build_cart(tmp_path / "cart")

    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
    assert manifest["overall_status"] == "candidate_runtime_qualification_pending"
    assert manifest["static_support_contract"]["status"] == "pass"
    assert manifest["static_support_contract"]["collider_selection"] == "preserved_source"
    assert manifest["source_derivation"]["source_candidate"] == "input_01_seed_250103"
    assert manifest["source_derivation"]["target_dimensions_m"] == [0.9, 0.76, 0.755]
    assert manifest["claims"]["oven_load_support_qualified"] is False
    assert (result.output / "input/source.zip").is_file()
