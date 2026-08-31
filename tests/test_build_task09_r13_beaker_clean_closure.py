from __future__ import annotations

import json

from pxr import Sdf, Usd, UsdGeom, UsdUtils

from scripts.build_task09_r13_beaker_clean_closure import build_clean_beaker


def test_beaker_closure_rewrites_only_the_stale_package_local_mdl_path(tmp_path) -> None:
    result = build_clean_beaker(tmp_path / "beaker")

    stage = Usd.Stage.Open(str(result.package / "deps/source/obj_beaker_sdf.usd"))
    shader = stage.GetPrimAtPath(
        "/Root/obj_beaker/__aan_visual_materials/WebStandardClearBorosilicate/Shader"
    )
    value = shader.GetAttribute("info:mdl:sourceAsset").Get()
    assert isinstance(value, Sdf.AssetPath)
    assert value.path == "../mdl/OmniGlass.mdl"
    collision = UsdGeom.Mesh(
        stage.GetPrimAtPath(
            "/Root/obj_beaker/__aan_pbd_collision_proxy/PBD_Unified_Vessel_Mesh"
        )
    )
    assert len(collision.GetNormalsAttr().Get()) == 1
    assert collision.GetNormalsInterpolation() == UsdGeom.Tokens.constant
    _layers, _assets, unresolved = UsdUtils.ComputeAllDependencies(
        str(result.package / "asset.usd")
    )
    assert unresolved == []
    receipt = json.loads(result.receipt.read_text(encoding="utf-8"))
    assert receipt["status"] == "promoted"
    assert receipt["claims"]["dynamic_graspable_sdf"] is True
