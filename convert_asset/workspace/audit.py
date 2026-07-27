"""Workspace clearance overlap audit with intruder classification.

The audit answers one question for a candidate eBench workspace: does the
clearance AABB intersect anything besides the replaced assembly roots and
the room shell?  Three historical failure modes are encoded here:

- wall-adjacent anchors put the fixed robot against blank walls (067 R1);
- table-depth vs aisle-depth mismatches drive the workbench through walls
  or into interior rows (067 R2/R3);
- ungrouped loose props on counters force anonymous mesh masks (085/081).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from .geometry import composed_mesh_world_bbox

DEFAULT_TABLE_FOOTPRINT_M = (2.345, 2.645)
DEFAULT_STANDING_HEIGHT_M = 2.2
FLAT_ITEM_MAX_THICKNESS_M = 0.005


@dataclass(frozen=True)
class ClearanceSpec:
    assembly_roots: list[str]
    anchor_xyz: tuple[float, float, float]
    table_footprint_m: tuple[float, float] = DEFAULT_TABLE_FOOTPRINT_M
    units_per_meter: float = 1.0
    floor_z: float = 0.0
    standing_height_m: float = DEFAULT_STANDING_HEIGHT_M


@dataclass(frozen=True)
class IntruderRecord:
    prim_path: str
    classification: str  # "loose_prop" | "flat_item"
    bbox_size: list[float]


@dataclass(frozen=True)
class AuditReport:
    verdict: str  # "clean" | "blocked"
    anchor_xyz: tuple[float, float, float]
    clearance_aabb_m: dict[str, list[float]]
    assembly_bbox: dict[str, list[float] | None]
    intruders: list[IntruderRecord] = field(default_factory=list)
    room_shell_intersections: int = 0


def _clearance_aabb(spec: ClearanceSpec) -> tuple[np.ndarray, np.ndarray]:
    half_x = spec.table_footprint_m[0] * spec.units_per_meter / 2.0
    half_y = spec.table_footprint_m[1] * spec.units_per_meter / 2.0
    cx, cy, _ = spec.anchor_xyz
    ws_min = np.array([cx - half_x, cy - half_y, spec.floor_z])
    ws_max = np.array(
        [cx + half_x, cy + half_y, spec.floor_z + spec.standing_height_m * spec.units_per_meter]
    )
    return ws_min, ws_max


def audit_clearance(
    stage: Any,
    spec: ClearanceSpec,
    *,
    is_room_shell: Callable[[Any], bool] | None = None,
) -> AuditReport:
    """Audit every mesh prim against the clearance AABB.

    ``is_room_shell`` marks kept background (floor/walls/ceiling); those
    intersections are counted but never block.  Everything else that
    intersects and is not under an assembly root blocks the placement.
    """
    ws_min, ws_max = _clearance_aabb(spec)
    assembly = [root.rstrip("/") for root in spec.assembly_roots]

    def under_assembly(path: str) -> bool:
        return any(path == root or path.startswith(root + "/") for root in assembly)

    mn_all = np.full(3, np.inf)
    mx_all = np.full(3, -np.inf)
    for root in assembly:
        mn, mx, _ = composed_mesh_world_bbox(stage, stage.GetPrimAtPath(root))
        if mn is not None:
            mn_all = np.minimum(mn_all, mn)
            mx_all = np.maximum(mx_all, mx)

    intruders: list[IntruderRecord] = []
    shell_hits = 0
    from pxr import Usd  # type: ignore

    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        path = prim.GetPath().pathString
        if under_assembly(path):
            continue
        mn, mx, mesh_count = composed_mesh_world_bbox(stage, prim)
        if not mesh_count:
            continue
        overlaps = not (
            mx[0] < ws_min[0] or mn[0] > ws_max[0]
            or mx[1] < ws_min[1] or mn[1] > ws_max[1]
            or mx[2] < ws_min[2] or mn[2] > ws_max[2]
        )
        if not overlaps:
            continue
        if is_room_shell is not None and is_room_shell(prim):
            shell_hits += 1
            continue
        if prim.GetTypeName() != "Mesh":
            continue
        size = (mx - mn).tolist()
        thickness = min(size)
        classification = (
            "flat_item" if thickness <= FLAT_ITEM_MAX_THICKNESS_M * spec.units_per_meter else "loose_prop"
        )
        intruders.append(
            IntruderRecord(
                prim_path=path,
                classification=classification,
                bbox_size=[round(float(v), 6) for v in size],
            )
        )

    return AuditReport(
        verdict="clean" if not intruders else "blocked",
        anchor_xyz=spec.anchor_xyz,
        clearance_aabb_m={
            "min": [round(float(v), 6) for v in ws_min],
            "max": [round(float(v), 6) for v in ws_max],
        },
        assembly_bbox={
            "min": None if np.isinf(mn_all).any() else [round(float(v), 6) for v in mn_all],
            "max": None if np.isinf(mx_all).any() else [round(float(v), 6) for v in mx_all],
        },
        intruders=intruders,
        room_shell_intersections=shell_hits,
    )
