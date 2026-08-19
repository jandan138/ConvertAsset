from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from scripts.build_centrifuge_cup_collider_facade_r10 import (
    CUP_FLOOR_Z_M,
    CUP_RIM_TOP_Z_M,
    CUP_WALL_INNER_RADIUS_M,
    FLOOR_PAD_WORLD_M,
    PROFILE_REVISION,
    SOCKETS,
    WALL_PANEL_COUNT,
    WALL_PANEL_RADIUS_M,
    build,
    cup_collider_local_matrices,
    facade_overlay_text,
    resolve_world,
)


def _world_center_and_axes(local_matrix: list[list[float]]):
    world = resolve_world(local_matrix)
    center = [world[0][3], world[1][3], world[2][3]]
    axes = [
        math.sqrt(world[0][i] ** 2 + world[1][i] ** 2 + world[2][i] ** 2)
        for i in range(3)
    ]
    return center, axes


def test_cup_floor_pads_resolve_to_measured_cup_floors() -> None:
    mats = cup_collider_local_matrices()
    for socket_name, (sx, sy) in SOCKETS.items():
        center, axes = _world_center_and_axes(mats[f"{socket_name}_cup_floor"])
        assert center[0] == pytest.approx(sx, abs=1e-6)
        assert center[1] == pytest.approx(sy, abs=1e-6)
        top_z = center[2] + axes[2] / 2.0
        assert top_z == pytest.approx(CUP_FLOOR_Z_M, abs=1e-6)
        assert axes[0] == pytest.approx(FLOOR_PAD_WORLD_M[0], abs=1e-6)
        assert axes[1] == pytest.approx(FLOOR_PAD_WORLD_M[1], abs=1e-6)
        # PhysX on this host ignores static discs below ~15 mm radius; the
        # square pad's half-extent is exactly 15 mm.
        assert FLOOR_PAD_WORLD_M[0] / 2.0 >= 0.015


def test_rotor_matrix_matches_device_profile_socket_0_resolution() -> None:
    # Independent anchor: the r7 device profile's socket_0 aperture local
    # translation must resolve to its published world pose.
    from scripts.build_centrifuge_cup_collider_facade_r10 import ROTOR_WORLD_MATRIX

    assert tuple(ROTOR_WORLD_MATRIX[3]) == (0.0, 0.0, 0.0, 1.0)
    local = (-0.27542857611909216, 0.2815150022506715, -0.3628571490365632, 1.0)
    world = [
        sum(ROTOR_WORLD_MATRIX[i][k] * local[k] for k in range(4)) for i in range(3)
    ]
    assert world == pytest.approx([-0.0635, -0.0482, 0.15289813], abs=1e-6)


def test_cup_floor_pads_resolve_to_measured_cup_floors() -> None:
    mats = cup_collider_local_matrices()
    for socket_name, (sx, sy) in SOCKETS.items():
        center, axes = _world_center_and_axes(mats[f"{socket_name}_cup_floor"])
        assert center[0] == pytest.approx(sx, abs=1e-6)
        assert center[1] == pytest.approx(sy, abs=1e-6)
        top_z = center[2] + axes[2] / 2.0
        assert top_z == pytest.approx(CUP_FLOOR_Z_M, abs=1e-6)
        assert axes[0] == pytest.approx(FLOOR_PAD_WORLD_M[0], abs=1e-6)
        assert axes[1] == pytest.approx(FLOOR_PAD_WORLD_M[1], abs=1e-6)
        # PhysX on this host ignores static discs below ~15 mm radius; the
        # square pad's half-extent is exactly 15 mm.
        assert FLOOR_PAD_WORLD_M[0] / 2.0 >= 0.015


def test_cup_wall_panels_ring_the_measured_cup_wall() -> None:
    mats = cup_collider_local_matrices()
    for socket_name, (sx, sy) in SOCKETS.items():
        radii = []
        for index in range(WALL_PANEL_COUNT):
            center, axes = _world_center_and_axes(
                mats[f"{socket_name}_cup_wall_{index}"]
            )
            radius = math.hypot(center[0] - sx, center[1] - sy)
            radii.append(radius)
            # thin radial panel, tall enough to span the cup depth
            assert min(axes) == pytest.approx(0.001, abs=1e-6)
            assert max(axes) == pytest.approx(0.020, abs=1e-6)
            assert center[2] > CUP_FLOOR_Z_M
            assert center[2] < CUP_RIM_TOP_Z_M
        for radius in radii:
            assert radius == pytest.approx(WALL_PANEL_RADIUS_M, abs=1e-6)
        inner_face = WALL_PANEL_RADIUS_M - 0.001 / 2.0
        assert inner_face == pytest.approx(CUP_WALL_INNER_RADIUS_M, abs=2e-3)


def test_overlay_text_authors_invisible_collision_cubes() -> None:
    text = facade_overlay_text()
    assert text.count('def Cube "') == 2 * (1 + WALL_PANEL_COUNT)
    assert text.count('PhysicsCollisionAPI') == 2 * (1 + WALL_PANEL_COUNT)
    assert 'token visibility = "invisible"' in text
    assert "socket_1_cup_floor" in text
    assert "socket_2_cup_wall_7" in text
    assert "quad_0" not in text  # inherited from the r9 sublayer, not redefined


def test_stored_matrix_composes_to_world_pose_under_usd_convention() -> None:
    # USD matrix4d text is stored transposed vs the effective map; parse the
    # authored tuple back and compose with the effective rotor matrix.
    import re

    from scripts.build_centrifuge_cup_collider_facade_r10 import ROTOR_WORLD_MATRIX

    text = facade_overlay_text()
    match = re.search(
        r'def Cube "socket_1_cup_floor".*?matrix4d xformOp:transform = '
        r"\( \(([^)]*)\), \(([^)]*)\), \(([^)]*)\), \(([^)]*)\) \)",
        text,
        re.DOTALL,
    )
    assert match is not None
    stored = [
        [float(v.strip()) for v in match.group(i + 1).split(",")] for i in range(4)
    ]
    transposed = [[stored[j][i] for j in range(4)] for i in range(4)]
    composed = [
        [sum(ROTOR_WORLD_MATRIX[i][k] * transposed[k][j] for k in range(4)) for j in range(4)]
        for i in range(4)
    ]
    sx, sy = SOCKETS["socket_1"]
    assert composed[0][3] == pytest.approx(sx, abs=1e-6)
    assert composed[1][3] == pytest.approx(sy, abs=1e-6)
    assert composed[2][3] == pytest.approx(CUP_FLOOR_Z_M - FLOOR_PAD_WORLD_M[2] / 2.0, abs=1e-6)


def test_build_writes_facade_and_rebound_physics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    r9_dir = tmp_path / "r9"
    facade_dir = r9_dir / "facade"
    facade_dir.mkdir(parents=True)
    r9_facade = facade_dir / "facade.usda"
    r9_facade.write_text("#usda 1.0\n(\n    defaultPrim = \"World\"\n)\n\ndef Xform \"World\" {}\n", encoding="utf-8")
    r9_physics = r9_dir / "centrifuge.physics.json"
    r9_physics.write_text(
        json.dumps(
            {
                "profile_id": "hci955350.centrifuge.physics",
                "revision": "r2-benchtop-support",
                "source_binding": {"sha256": "f" * 64},
            }
        ),
        encoding="utf-8",
    )
    before = r9_facade.read_bytes()

    result = build(r9_facade=r9_facade, r9_physics=r9_physics, out_root=tmp_path / "r10")

    assert r9_facade.read_bytes() == before
    facade_text = result["facade"].read_text(encoding="utf-8")
    assert "subLayers" in facade_text
    assert "facade.usda" in facade_text
    physics = json.loads(result["physics"].read_text(encoding="utf-8"))
    assert physics["source_binding"]["sha256"] != "f" * 64
    assert physics["profile_id"].endswith(".cup-colliders-r10")
    assert physics["revision"] == PROFILE_REVISION
    provenance = json.loads(result["provenance"].read_text(encoding="utf-8"))
    assert len(provenance["added_colliders"]) == 2 * (1 + WALL_PANEL_COUNT)
    with pytest.raises(FileExistsError):
        build(r9_facade=r9_facade, r9_physics=r9_physics, out_root=tmp_path / "r10")
