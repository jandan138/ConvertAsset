# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from convert_asset.camera.bounds import compute_world_bounds


def test_compute_world_bounds_ignores_default_setting_descendants() -> None:
    pytest.importorskip("pxr")
    from pxr import Usd, UsdGeom  # type: ignore

    stage = Usd.Stage.CreateInMemory()
    UsdGeom.Xform.Define(stage, "/Root")
    UsdGeom.Xform.Define(stage, "/Root/Target")
    cube = UsdGeom.Cube.Define(stage, "/Root/Target/ObjectCube")
    cube.CreateSizeAttr(2.0)

    UsdGeom.Xform.Define(stage, "/Root/Target/__default_setting")
    hdr = UsdGeom.Cube.Define(stage, "/Root/Target/__default_setting/HDR_Sphere")
    hdr.CreateSizeAttr(1000.0)

    bounds = compute_world_bounds(stage, "/Root/Target")

    assert bounds.size == pytest.approx((2.0, 2.0, 2.0))
    assert bounds.diagonal < 4.0
