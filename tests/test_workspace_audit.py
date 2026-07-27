"""Tests for convert_asset.workspace.audit."""

from __future__ import annotations

import pytest

from convert_asset.workspace.audit import ClearanceSpec, audit_clearance


def _make_stage():
    Usd = pytest.importorskip("pxr.Usd")
    UsdGeom = pytest.importorskip("pxr.UsdGeom")
    Gf = pytest.importorskip("pxr.Gf")

    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    def mesh(path, center, size, thickness=None):
        m = UsdGeom.Mesh.Define(stage, path)
        cx, cy, cz = center
        sx, sy, sz = size
        m.GetPointsAttr().Set(
            [
                Gf.Vec3f(cx - sx / 2, cy - sy / 2, cz),
                Gf.Vec3f(cx + sx / 2, cy + sy / 2, cz + (thickness if thickness is not None else sz)),
            ]
        )
        m.GetFaceVertexCountsAttr().Set([2])
        m.GetFaceVertexIndicesAttr().Set([0, 1])
        return m

    # island assembly (1.8 x 1.0 x 2.4 at origin)
    UsdGeom.Xform.Define(stage, "/World/group_island")
    mesh("/World/group_island/body", (0.0, 0.0, 0.0), (1.8, 1.0, 2.4))
    # room shell floor + wall
    UsdGeom.Xform.Define(stage, "/World/floor")
    mesh("/World/floor/surface", (0.0, 0.0, 0.0), (20.0, 20.0, 0.0), thickness=0.1)
    UsdGeom.Xform.Define(stage, "/World/wall")
    mesh("/World/wall/panel", (0.0, 6.0, 0.0), (20.0, 0.1, 3.0))
    # loose prop ON the island (inside clearance)
    mesh("/World/prop_beaker", (0.2, 0.1, 1.0), (0.1, 0.1, 0.2))
    # flat decal on the floor inside clearance (thin)
    mesh("/World/decal_drain", (0.5, 0.4, 0.001), (0.5, 0.5, 0.0), thickness=0.001)
    # far content outside clearance
    mesh("/World/far_shelf", (10.0, 10.0, 0.0), (2.0, 2.0, 2.0))
    return stage


def test_audit_classifies_intruders() -> None:
    stage = _make_stage()
    spec = ClearanceSpec(
        assembly_roots=["/World/group_island"],
        anchor_xyz=(0.0, 0.0, 0.9),
        table_footprint_m=(2.45, 2.75),
        units_per_meter=1.0,
        floor_z=0.0,
    )

    def is_shell(prim) -> bool:
        return prim.GetPath().pathString.startswith(("/World/floor", "/World/wall"))

    report = audit_clearance(stage, spec, is_room_shell=is_shell)

    assert report.verdict == "blocked"
    kinds = {item.prim_path: item.classification for item in report.intruders}
    assert kinds["/World/prop_beaker"] == "loose_prop"
    assert kinds["/World/decal_drain"] == "flat_item"
    assert "/World/far_shelf" not in kinds
    assert report.room_shell_intersections >= 1


def test_audit_clean_when_only_shell_and_assembly() -> None:
    stage = _make_stage()
    spec = ClearanceSpec(
        assembly_roots=["/World/group_island", "/World/prop_beaker", "/World/decal_drain"],
        anchor_xyz=(0.0, 0.0, 0.9),
        table_footprint_m=(2.45, 2.75),
        units_per_meter=1.0,
        floor_z=0.0,
    )

    def is_shell(prim) -> bool:
        return prim.GetPath().pathString.startswith(("/World/floor", "/World/wall"))

    report = audit_clearance(stage, spec, is_room_shell=is_shell)

    assert report.verdict == "clean"
    assert report.intruders == []
    assert report.clearance_aabb_m["min"][2] == 0.0
