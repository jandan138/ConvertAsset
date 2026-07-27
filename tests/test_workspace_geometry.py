"""Tests for convert_asset.workspace.geometry."""

from __future__ import annotations

import numpy as np
import pytest

from convert_asset.workspace.geometry import (
    composed_mesh_world_bbox,
    estimate_counter_band,
)


@pytest.fixture()
def scaled_lab_stage():
    Usd = pytest.importorskip("pxr.Usd")
    UsdGeom = pytest.importorskip("pxr.UsdGeom")
    Gf = pytest.importorskip("pxr.Gf")

    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.Xform.Define(stage, "/World")
    group = UsdGeom.Xform.Define(stage, "/World/group_000")
    group.AddTranslateOp().Set(Gf.Vec3d(11.381, -4.179, 1.666))
    group.AddScaleOp().Set(Gf.Vec3f(0.000679, 0.000679, 0.000679))
    mesh = UsdGeom.Mesh.Define(stage, "/World/group_000/mesh_000")
    mesh.GetPointsAttr().Set(
        [Gf.Vec3f(350.0, 0.0, 0.0), Gf.Vec3f(0.0, 260.0, 0.0), Gf.Vec3f(0.0, 0.0, 1200.0)]
    )
    mesh.GetFaceVertexCountsAttr().Set([3])
    mesh.GetFaceVertexIndicesAttr().Set([0, 1, 2])
    return stage


def test_composed_bbox_uses_row_vector_convention(scaled_lab_stage) -> None:
    """Gf matrices map row vectors as p @ M; column-vector math lands the bbox far off."""
    mn, mx, mesh_count = composed_mesh_world_bbox(
        scaled_lab_stage, scaled_lab_stage.GetPrimAtPath("/World/group_000")
    )
    assert mesh_count == 1
    s = 0.000679
    expected_min = np.array([11.381, -4.179, 1.666]) + np.array([0.0, 0.0, 0.0])
    expected_max = np.array([11.381, -4.179, 1.666]) + np.array(
        [350.0 * s, 260.0 * s, 1200.0 * s]
    )
    np.testing.assert_allclose(mn, expected_min, atol=1e-6)
    np.testing.assert_allclose(mx, expected_max, atol=1e-6)


def test_composed_bbox_skips_empty_and_missing(scaled_lab_stage) -> None:
    empty = scaled_lab_stage.DefinePrim("/World/empty", "Xform")
    mn, mx, mesh_count = composed_mesh_world_bbox(scaled_lab_stage, empty)
    assert mesh_count == 0
    assert mn is None and mx is None


def test_estimate_counter_band_finds_dense_surface(scaled_lab_stage) -> None:
    UsdGeom = pytest.importorskip("pxr.UsdGeom")
    Gf = pytest.importorskip("pxr.Gf")

    stage = scaled_lab_stage
    for index, z in enumerate([0.0, 0.9, 0.9, 0.9, 2.2]):
        mesh = UsdGeom.Mesh.Define(stage, f"/World/extra_{index}")
        mesh.GetPointsAttr().Set([Gf.Vec3f(0.0, 0.0, float(z))])
        mesh.GetFaceVertexCountsAttr().Set([1])
        mesh.GetFaceVertexIndicesAttr().Set([0])

    band = estimate_counter_band(stage, ["/World/extra_0", "/World/extra_1", "/World/extra_2", "/World/extra_3", "/World/extra_4"], floor_z=0.0)

    assert band is not None
    assert abs(band["counter_z"] - 0.9) < 0.2
    assert band["units_per_meter"] == pytest.approx((0.9 - 0.0) / 0.9, rel=0.25)
