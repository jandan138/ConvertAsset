#!/usr/bin/env python3
"""Build the r10 centrifuge facade: package-level colliders for two visual cups.

The r9 box proxies bound the rotor exterior but leave the arm-plate cup
interiors without colliders, so a physical tube falls through the measured
visual cup floors. This producer-owned overlay adds, per balanced cup:

- one floor pad (30 mm square, 4 mm thick, top face on the measured visual
  cup floor z=0.1281) — wide enough that PhysX does not ignore it;
- eight wall panels around the cup wall (inner face at the measured ~8.5 mm
  cup radius) so an off-axis tube meets a real guide surface.

Nothing else changes: visuals, transforms, joints, drives, and the complete
mass/inertia bundle are inherited from the r9 facade by sublayering. The
physics profile is rebound to the new facade hash without parameter changes.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_R9_FACADE = REPO_ROOT / "outputs/centrifuge_identity_root_r9/facade/facade.usda"
DEFAULT_R9_PHYSICS = REPO_ROOT / "outputs/centrifuge_identity_root_r9/centrifuge.physics.json"
DEFAULT_OUT_ROOT = REPO_ROOT / "outputs/centrifuge_identity_root_r10_cup_colliders"
ROOT = "/World/Centrifuge"
ROTOR_BODY = f"{ROOT}/group_6"
PROXY_SCOPE = f"{ROTOR_BODY}/__aan_collision_proxy"
PROFILE_REVISION = "r3-cup-colliders"

# Measured against the r9 package visual mesh (raycast, 2026-08-19).
CUP_FLOOR_Z_M = 0.1281
CUP_RIM_TOP_Z_M = 0.145
CUP_WALL_INNER_RADIUS_M = 0.0085
SOCKETS = {
    "socket_1": (0.0208, 0.0142),
    "socket_2": (-0.1016, -0.1107),
}
FLOOR_PAD_WORLD_M = (0.030, 0.030, 0.004)
WALL_PANEL_COUNT = 8
WALL_PANEL_RADIUS_M = 0.009  # center radius; inner face at ~8.5 mm
WALL_PANEL_SIZE_WORLD_M = (0.001, 0.008, 0.020)
WALL_PANEL_CENTER_Z_M = 0.1366

# Parked rotor world-from-local EFFECTIVE matrix (0.175 scale, axis
# permutation), verified against composed package AABBs. Note: USDA matrix4d
# text is stored transposed relative to the effective map (Gf prints the
# transpose), so prim matrices are authored via _to_usd_matrix below.
ROTOR_WORLD_MATRIX = (
    (3.885780520013599e-17, -3.885780520013599e-17, 0.17499999701976776, 0.0),
    (0.17499999701976776, 8.628166003918023e-33, -3.885780520013599e-17, 0.0),
    (0.0, 0.17499999701976776, 3.885780520013599e-17, 0.10363300144672394),
    (0.0, 0.0, 0.0, 1.0),
)


def _transpose(m: list[list[float]]) -> list[list[float]]:
    return [[m[j][i] for j in range(4)] for i in range(4)]


def _to_usd_matrix(effective_local: list[list[float]]) -> list[list[float]]:
    """USD stores matrix4d text transposed vs the effective map."""
    return _transpose(effective_local)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _mat_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [
        [sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)]
        for i in range(4)
    ]


def _mat_inv_rigid_scale(m: list[list[float]]) -> list[list[float]]:
    """Invert an affine matrix (rotation + uniform positive scale + translate)."""
    r = [[m[i][j] for j in range(3)] for i in range(3)]
    t = [m[i][3] for i in range(3)]
    scale_sq = sum(r[i][0] ** 2 for i in range(3))
    if scale_sq <= 0.0:
        raise ValueError("singular linear part")
    inv_r = [[r[j][i] / scale_sq for j in range(3)] for i in range(3)]
    inv_t = [-sum(inv_r[i][k] * t[k] for k in range(3)) for i in range(3)]
    return [inv_r[i] + [inv_t[i]] for i in range(3)] + [[0.0, 0.0, 0.0, 1.0]]


def _shape_matrix(
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    yaw_rad: float = 0.0,
) -> list[list[float]]:
    c, s = math.cos(yaw_rad), math.sin(yaw_rad)
    return [
        [c * size[0], -s * size[1], 0.0, center[0]],
        [s * size[0], c * size[1], 0.0, center[1]],
        [0.0, 0.0, size[2], center[2]],
        [0.0, 0.0, 0.0, 1.0],
    ]


def cup_collider_local_matrices() -> dict[str, list[list[float]]]:
    """group_6-local transforms for every cup collider prim."""
    inv = _mat_inv_rigid_scale([list(row) for row in ROTOR_WORLD_MATRIX])
    mats: dict[str, list[list[float]]] = {}
    for socket_name, (sx, sy) in SOCKETS.items():
        floor_world = _shape_matrix(
            (sx, sy, CUP_FLOOR_Z_M - FLOOR_PAD_WORLD_M[2] / 2.0), FLOOR_PAD_WORLD_M
        )
        mats[f"{socket_name}_cup_floor"] = _mat_mul(inv, floor_world)
        for index in range(WALL_PANEL_COUNT):
            theta = 2.0 * math.pi * index / WALL_PANEL_COUNT
            center = (
                sx + WALL_PANEL_RADIUS_M * math.cos(theta),
                sy + WALL_PANEL_RADIUS_M * math.sin(theta),
                WALL_PANEL_CENTER_Z_M,
            )
            world = _shape_matrix(center, WALL_PANEL_SIZE_WORLD_M, yaw_rad=theta)
            mats[f"{socket_name}_cup_wall_{index}"] = _mat_mul(inv, world)
    return mats


def resolve_world(local_matrix: list[list[float]]) -> list[list[float]]:
    return _mat_mul([list(row) for row in ROTOR_WORLD_MATRIX], local_matrix)


def _fmt_matrix(m: list[list[float]]) -> str:
    rows = []
    for row in m:
        rows.append("(" + ", ".join(f"{v:.12g}" for v in row) + ")")
    return "( " + ", ".join(rows) + " )"


def facade_overlay_text() -> str:
    mats = cup_collider_local_matrices()
    blocks = []
    for name, matrix in mats.items():
        blocks.append(
            f'''                def Cube "{name}" (
                    prepend apiSchemas = ["PhysicsCollisionAPI"]
                )
                {{
                    bool physics:collisionEnabled = 1
                    double size = 1
                    token visibility = "invisible"
                    matrix4d xformOp:transform = {_fmt_matrix(_to_usd_matrix(matrix))}
                    uniform token[] xformOpOrder = ["xformOp:transform"]
                }}'''
        )
    joined = "\n".join(blocks)
    return f'''over "World"
{{
    over "Centrifuge"
    {{
        over "group_6"
        {{
            over "__aan_collision_proxy"
            {{
{joined}
            }}
        }}
    }}
}}
'''


def _rebind_physics_profile(value: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    import copy

    rebound = copy.deepcopy(value)
    binding = rebound.get("source_binding")
    if not isinstance(binding, dict):
        raise ValueError("physics profile source_binding must be an object")
    profile_id = rebound.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id:
        raise ValueError("physics profile profile_id must be a non-empty string")
    binding["sha256"] = source_sha256
    rebound["profile_id"] = f"{profile_id}.cup-colliders-r10"
    rebound["revision"] = PROFILE_REVISION
    return rebound


def build(*, r9_facade: Path, r9_physics: Path, out_root: Path) -> dict[str, Path]:
    r9_facade = r9_facade.resolve()
    r9_physics = r9_physics.resolve()
    if not r9_facade.is_file():
        raise FileNotFoundError(r9_facade)
    if not r9_physics.is_file():
        raise FileNotFoundError(r9_physics)
    facade_dir = out_root / "facade"
    facade_dir.mkdir(parents=True, exist_ok=True)
    relative_r9 = Path(__import__("os").path.relpath(r9_facade, facade_dir))
    overlay = facade_overlay_text()
    facade_text = f'''#usda 1.0
(
    defaultPrim = "World"
    framesPerSecond = 24
    metersPerUnit = 1
    subLayers = [
        @{relative_r9.as_posix()}@
    ]
    timeCodesPerSecond = 60
    upAxis = "Z"
)

{overlay}'''
    facade_path = facade_dir / "facade.usda"
    if facade_path.exists():
        raise FileExistsError(f"refusing to replace generated artifact: {facade_path}")
    facade_path.write_text(facade_text, encoding="utf-8")
    facade_sha = _sha(facade_path)

    physics = json.loads(r9_physics.read_text(encoding="utf-8"))
    rebound = _rebind_physics_profile(physics, source_sha256=facade_sha)
    physics_path = out_root / "centrifuge.physics.json"
    if physics_path.exists():
        raise FileExistsError(f"refusing to replace generated artifact: {physics_path}")
    physics_path.write_text(
        json.dumps(rebound, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    provenance = {
        "schema_version": "aan.centrifuge_cup_collider_facade.v1",
        "base_facade": str(r9_facade),
        "base_facade_sha256": _sha(r9_facade),
        "facade_sha256": facade_sha,
        "physics_profile_sha256": _sha(physics_path),
        "revision": PROFILE_REVISION,
        "added_colliders": sorted(cup_collider_local_matrices()),
        "cup_model": {
            "floor_z_m": CUP_FLOOR_Z_M,
            "rim_top_z_m": CUP_RIM_TOP_Z_M,
            "wall_inner_radius_m": CUP_WALL_INNER_RADIUS_M,
            "sockets_world_xy_m": {k: list(v) for k, v in SOCKETS.items()},
        },
        "claim_boundary": (
            "Overlay adds cup floor/wall colliders under the rotor proxy scope. "
            "Visuals, transforms, joints, drives, and mass bundle are inherited "
            "from the r9 facade unchanged."
        ),
    }
    provenance_path = facade_dir / "facade_provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "facade": facade_path,
        "physics": physics_path,
        "provenance": provenance_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r9-facade", type=Path, default=DEFAULT_R9_FACADE)
    parser.add_argument("--r9-physics", type=Path, default=DEFAULT_R9_PHYSICS)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    args = parser.parse_args()
    result = build(
        r9_facade=args.r9_facade,
        r9_physics=args.r9_physics,
        out_root=args.out_root,
    )
    print(json.dumps({k: str(v) for k, v in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
