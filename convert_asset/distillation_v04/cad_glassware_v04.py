"""Parametric 0.05 mm-coaxial borosilicate glassware CAD & collider exporter (distillation_v04)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


# Shared physical kinematic constants (world Z-up, z_table = 0.755 m)
Z_TABLE = 0.755
PITCH_DEG = 18.0
PITCH_RAD = math.radians(PITCH_DEG)
COS_P = math.cos(PITCH_RAD)
SIN_P = math.sin(PITCH_RAD)
DIR_ARM = np.array([COS_P, 0.0, -SIN_P], dtype=np.float64)
# Rotation around +Y by +18 deg: wxyz = (cos(9 deg), 0, sin(9 deg), 0)
WXYZ_CONDENSER = (math.cos(0.5 * PITCH_RAD), 0.0, math.sin(0.5 * PITCH_RAD), 0.0)
WXYZ_IDENTITY = (1.0, 0.0, 0.0, 0.0)

# Exact shared datum coordinates
FLASK_ASM_POS = (-0.18, 0.00, 0.870)
HEAD_ASM_POS = (-0.18, 0.00, 0.985)
J_SIDEARM_WORLD = (-0.18, 0.00, 1.007)  # z_sidearm_bottom == z_bulb_top == 1.007 m
THM_ASM_POS = (-0.18, 0.00, 1.065)    # bulb top at z_local = -0.058 -> z_world = 1.007 m
COND_ASM_POS = (
    float(J_SIDEARM_WORLD[0] + 0.210 * DIR_ARM[0]),
    0.00,
    float(J_SIDEARM_WORLD[2] + 0.210 * DIR_ARM[2]),
)  # (+0.019722, 0.0, +0.942106)
TAIL_ASM_POS = (
    float(J_SIDEARM_WORLD[0] + 0.330 * DIR_ARM[0]),
    0.00,
    float(J_SIDEARM_WORLD[2] + 0.330 * DIR_ARM[2]),
)  # (+0.133849, 0.0, +0.905024)
RECEIVER_ASM_POS = (float(TAIL_ASM_POS[0] + 0.066), 0.00, Z_TABLE)

# Barb world coordinates ("下进上出": lower inlet at z_root=0.916, upper outlet at z_root=0.956)
U_BARB_WORLD = np.array([0.0, -math.sqrt(0.5), -math.sqrt(0.5)], dtype=np.float64)
LOWER_INLET_BARB_ROOT = (
    float(J_SIDEARM_WORLD[0] + 0.275 * DIR_ARM[0]),
    -0.014,
    float(Z_TABLE + 0.161),  # 0.916 m
)
UPPER_OUTLET_BARB_ROOT = (
    float(J_SIDEARM_WORLD[0] + 0.145 * DIR_ARM[0]),
    -0.014,
    float(Z_TABLE + 0.201),  # 0.956 m
)
LOWER_INLET_BARB_TIP = tuple(float(a + 0.036 * b) for a, b in zip(LOWER_INLET_BARB_ROOT, U_BARB_WORLD))
UPPER_OUTLET_BARB_TIP = tuple(float(a + 0.036 * b) for a, b in zip(UPPER_OUTLET_BARB_ROOT, U_BARB_WORLD))


@dataclass(frozen=True)
class ComponentCADSpec:
    component_id: str
    category: str
    material_kind: str  # "borosilicate" | "iron" | "brass" | "polymer"
    dynamic_in_sop: bool
    mass_kg: float
    assembled_xyz: tuple[float, float, float]
    assembled_wxyz: tuple[float, float, float, float]
    staged_xyz: tuple[float, float, float]
    staged_wxyz: tuple[float, float, float, float]
    grasp_local_xyz: tuple[float, float, float]


DISTILLATION_COMPONENT_SPECS: dict[str, ComponentCADSpec] = {
    "alcohol_lamp": ComponentCADSpec(
        component_id="alcohol_lamp",
        category="glass_alcohol_burner",
        material_kind="borosilicate",
        dynamic_in_sop=True,
        mass_kg=0.22,
        assembled_xyz=(-0.18, 0.00, Z_TABLE),
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(0.06, -0.15, Z_TABLE),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.042),
    ),
    "iron_stand_left": ComponentCADSpec(
        component_id="iron_stand_left",
        category="retort_iron_stand",
        material_kind="iron",
        dynamic_in_sop=False,
        mass_kg=1.80,
        assembled_xyz=(-0.18, 0.08, Z_TABLE),
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(-0.18, 0.08, Z_TABLE),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.16),
    ),
    "iron_stand_right": ComponentCADSpec(
        component_id="iron_stand_right",
        category="retort_iron_stand_inclined",
        material_kind="iron",
        dynamic_in_sop=False,
        mass_kg=1.80,
        assembled_xyz=(COND_ASM_POS[0], 0.08, Z_TABLE),
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(COND_ASM_POS[0], 0.08, Z_TABLE),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.16),
    ),
    "iron_ring_gauze": ComponentCADSpec(
        component_id="iron_ring_gauze",
        category="iron_ring_with_wire_gauze",
        material_kind="iron",
        dynamic_in_sop=True,
        mass_kg=0.18,
        assembled_xyz=(-0.18, 0.00, 0.865),
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(-0.05, -0.15, Z_TABLE),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, -0.048, 0.008),
    ),
    "distillation_flask": ComponentCADSpec(
        component_id="distillation_flask",
        category="round_bottom_distillation_flask",
        material_kind="borosilicate",
        dynamic_in_sop=True,
        mass_kg=0.24,
        assembled_xyz=FLASK_ASM_POS,
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(-0.22, -0.15, Z_TABLE),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.078),
    ),
    "distillation_head": ComponentCADSpec(
        component_id="distillation_head",
        category="75deg_distillation_head",
        material_kind="borosilicate",
        dynamic_in_sop=True,
        mass_kg=0.16,
        assembled_xyz=HEAD_ASM_POS,
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(-0.06, -0.14, Z_TABLE + 0.030),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.038),
    ),
    "mercury_thermometer": ComponentCADSpec(
        component_id="mercury_thermometer",
        category="precision_glass_thermometer",
        material_kind="borosilicate",
        dynamic_in_sop=True,
        mass_kg=0.06,
        assembled_xyz=THM_ASM_POS,
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(-0.14, -0.14, Z_TABLE + 0.072),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.082),
    ),
    "liebig_condenser": ComponentCADSpec(
        component_id="liebig_condenser",
        category="liebig_water_condenser",
        material_kind="borosilicate",
        dynamic_in_sop=True,
        mass_kg=0.32,
        assembled_xyz=COND_ASM_POS,
        assembled_wxyz=WXYZ_CONDENSER,
        staged_xyz=(0.02, -0.15, Z_TABLE + 0.026),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.0),
    ),
    "tail_adapter": ComponentCADSpec(
        component_id="tail_adapter",
        category="curved_vacuum_tail_adapter",
        material_kind="borosilicate",
        dynamic_in_sop=True,
        mass_kg=0.11,
        assembled_xyz=TAIL_ASM_POS,
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(0.14, -0.15, Z_TABLE + 0.058),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.024, 0.0, -0.012),
    ),
    "erlenmeyer_receiver": ComponentCADSpec(
        component_id="erlenmeyer_receiver",
        category="erlenmeyer_receiving_flask",
        material_kind="borosilicate",
        dynamic_in_sop=True,
        mass_kg=0.19,
        assembled_xyz=RECEIVER_ASM_POS,
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(0.24, -0.15, Z_TABLE),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.072),
    ),
    "bench_water_ports": ComponentCADSpec(
        component_id="bench_water_ports",
        category="bench_tap_and_drain_manifold",
        material_kind="polymer",
        dynamic_in_sop=False,
        mass_kg=1.20,
        assembled_xyz=(0.0, -0.175, Z_TABLE),
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(0.0, -0.175, Z_TABLE),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.015),
    ),
    "staging_trays": ComponentCADSpec(
        component_id="staging_trays",
        category="silicone_lined_apparatus_organizer",
        material_kind="polymer",
        dynamic_in_sop=False,
        mass_kg=0.90,
        assembled_xyz=(0.0, -0.15, Z_TABLE),
        assembled_wxyz=WXYZ_IDENTITY,
        staged_xyz=(0.0, -0.15, Z_TABLE),
        staged_wxyz=WXYZ_IDENTITY,
        grasp_local_xyz=(0.0, 0.0, 0.005),
    ),
}


def _quat_to_rot(wxyz: tuple[float, float, float, float]) -> np.ndarray:
    w, x, y, z = wxyz
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def _lathe_profile_mesh(
    profile_rz: list[tuple[float, float]],
    *,
    n_theta: int = 32,
    axis: str = "Z",
    center_offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Generate revolved manifold triangle mesh from (r, h) profile points."""
    th = np.linspace(0.0, 2.0 * math.pi, n_theta, endpoint=False)
    pts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    ox, oy, oz = center_offset

    # Sample rings (duplicate pole if r==0)
    rings: list[list[int]] = []
    for r, h in profile_rz:
        if r <= 1e-6:
            idx = len(pts)
            p = (ox + h, oy, oz) if axis == "X" else (ox, oy, oz + h)
            pts.append(p)
            rings.append([idx] * n_theta)
        else:
            ring_ids = []
            for t in th:
                c, s = math.cos(float(t)), math.sin(float(t))
                if axis == "X":
                    pts.append((ox + h, oy + r * c, oz + r * s))
                else:
                    pts.append((ox + r * c, oy + r * s, oz + h))
                ring_ids.append(len(pts) - 1)
            rings.append(ring_ids)

    for k in range(len(rings) - 1):
        r0 = rings[k]
        r1 = rings[k + 1]
        is_pole0 = r0[0] == r0[1]
        is_pole1 = r1[0] == r1[1]
        if is_pole0 and not is_pole1:
            for j in range(n_theta):
                jn = (j + 1) % n_theta
                tris.append((r0[0], r1[jn], r1[j]))
        elif is_pole1 and not is_pole0:
            for j in range(n_theta):
                jn = (j + 1) % n_theta
                tris.append((r0[j], r0[jn], r1[0]))
        elif not is_pole0 and not is_pole1:
            for j in range(n_theta):
                jn = (j + 1) % n_theta
                tris.append((r0[j], r0[jn], r1[jn]))
                tris.append((r0[j], r1[jn], r1[j]))
    return pts, tris


def _swept_tube_mesh(
    centers: np.ndarray,
    radii: np.ndarray,
    n_theta: int = 20,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    """Generate swept smooth tubular mesh along 3D centerline."""
    pts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    th = np.linspace(0.0, 2.0 * math.pi, n_theta, endpoint=False)
    prev_n = None
    rings: list[list[int]] = []
    for i, c in enumerate(centers):
        if i == 0:
            t = centers[1] - centers[0]
        elif i == len(centers) - 1:
            t = centers[-1] - centers[-2]
        else:
            t = centers[i + 1] - centers[i - 1]
        t = t / max(float(np.linalg.norm(t)), 1e-9)
        if prev_n is None:
            ref = np.array([0.0, 1.0, 0.0], dtype=np.float64)
            if abs(float(np.dot(t, ref))) > 0.9:
                ref = np.array([1.0, 0.0, 0.0], dtype=np.float64)
            n = np.cross(t, ref)
        else:
            n = prev_n - float(np.dot(prev_n, t)) * t
        nn = float(np.linalg.norm(n))
        if nn < 1e-7:
            n = np.cross(t, np.array([0.0, 0.0, 1.0]))
            nn = float(np.linalg.norm(n))
        n = n / max(nn, 1e-9)
        prev_n = n
        b = np.cross(t, n)
        ring = []
        r = float(radii[i])
        for ang in th:
            p = c + r * (math.cos(float(ang)) * n + math.sin(float(ang)) * b)
            pts.append((float(p[0]), float(p[1]), float(p[2])))
            ring.append(len(pts) - 1)
        rings.append(ring)

    for i in range(len(rings) - 1):
        r0, r1 = rings[i], rings[i + 1]
        for j in range(n_theta):
            jn = (j + 1) % n_theta
            tris.append((r0[j], r0[jn], r1[jn]))
            tris.append((r0[j], r1[jn], r1[j]))
    # End caps
    c_s = len(pts)
    pts.append((float(centers[0, 0]), float(centers[0, 1]), float(centers[0, 2])))
    c_e = len(pts)
    pts.append((float(centers[-1, 0]), float(centers[-1, 1]), float(centers[-1, 2])))
    for j in range(n_theta):
        jn = (j + 1) % n_theta
        tris.append((c_s, rings[0][jn], rings[0][j]))
        tris.append((c_e, rings[-1][j], rings[-1][jn]))
    return pts, tris


def _box_mesh(
    center: tuple[float, float, float],
    size_xyz: tuple[float, float, float],
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    cx, cy, cz = center
    hx, hy, hz = 0.5 * size_xyz[0], 0.5 * size_xyz[1], 0.5 * size_xyz[2]
    pts = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    tris = [
        (0, 2, 1), (0, 3, 2),
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]
    return pts, tris


def _ring_wedge_boxes(
    center: tuple[float, float, float],
    radius: float,
    thickness: float,
    height: float,
    n_wedges: int = 12,
    axis: str = "Z",
) -> list[dict[str, Any]]:
    """Generate 12-wedge circumferential convex box ring for genuine ground-glass socket insertion."""
    boxes = []
    tang_w = max(0.003, 2.0 * math.pi * radius / float(n_wedges) * 0.92)
    for k in range(n_wedges):
        th = 2.0 * math.pi * k / float(n_wedges)
        ct, st = math.cos(th), math.sin(th)
        if axis == "X":
            pos = (center[0], center[1] + radius * ct, center[2] + radius * st)
            half_size = (0.5 * height, 0.5 * thickness, 0.5 * tang_w)
            wxyz = (math.cos(0.5 * th), math.sin(0.5 * th), 0.0, 0.0)
        else:
            pos = (center[0] + radius * ct, center[1] + radius * st, center[2])
            half_size = (0.5 * thickness, 0.5 * tang_w, 0.5 * height)
            wxyz = (math.cos(0.5 * th), 0.0, 0.0, math.sin(0.5 * th))
        boxes.append(
            {
                "pos": [round(pos[0], 6), round(pos[1], 6), round(pos[2], 6)],
                "half_size": [round(half_size[0], 6), round(half_size[1], 6), round(half_size[2], 6)],
                "wxyz": [round(v, 7) for v in wxyz],
            }
        )
    return boxes


def _build_component_visual_submeshes(component_id: str) -> list[tuple[str, str, list[tuple[float, float, float]], list[tuple[int, int, int]]]]:
    """Return list of (mesh_name, material_name, pts, tris) for each apparatus component."""
    submeshes: list[tuple[str, str, list[tuple[float, float, float]], list[tuple[int, int, int]]]] = []

    if component_id == "alcohol_lamp":
        pts, tris = _lathe_profile_mesh(
            [
                (0.0, 0.000), (0.036, 0.000), (0.038, 0.010), (0.038, 0.044),
                (0.016, 0.062), (0.015, 0.072), (0.010, 0.072), (0.0, 0.062),
            ]
        )
        submeshes.append(("LampBodyGlass", "BorosilicateGlassMat", pts, tris))
        pts_eth, tris_eth = _lathe_profile_mesh(
            [(0.0, 0.004), (0.033, 0.004), (0.033, 0.034), (0.0, 0.034)]
        )
        submeshes.append(("EthanolFill", "SolventLiquidMat", pts_eth, tris_eth))
        pts_col, tris_col = _lathe_profile_mesh(
            [(0.0, 0.070), (0.0155, 0.070), (0.0155, 0.079), (0.007, 0.079), (0.0, 0.078)]
        )
        submeshes.append(("BrassCollar", "BrassBurnerMat", pts_col, tris_col))
        pts_wk, tris_wk = _lathe_profile_mesh(
            [(0.0, 0.078), (0.0045, 0.078), (0.0042, 0.088), (0.0, 0.088)]
        )
        submeshes.append(("CottonWick", "CeramicWhiteMat", pts_wk, tris_wk))

    elif component_id in ("iron_stand_left", "iron_stand_right"):
        pts_b, tris_b = _box_mesh((0.0, 0.0, 0.006), (0.145, 0.115, 0.012))
        submeshes.append(("BasePlate", "DarkCastIronMat", pts_b, tris_b))
        rod_h = 0.42 if component_id == "iron_stand_left" else 0.36
        pts_r, tris_r = _lathe_profile_mesh(
            [(0.0, 0.012), (0.0065, 0.012), (0.0065, rod_h), (0.0, rod_h)],
            center_offset=(0.0, 0.030, 0.0),
        )
        submeshes.append(("RetortRod", "BrushedSteelMat", pts_r, tris_r))
        clamp_z = 0.170 if component_id == "iron_stand_left" else 0.187
        pts_arm, tris_arm = _box_mesh((0.0, -0.018, clamp_z), (0.014, 0.092, 0.012))
        submeshes.append(("ClampArm", "BrushedSteelMat", pts_arm, tris_arm))
        # U/V cradle jaw tips extending to y_local = -0.08 (which is world y = 0.00)
        pts_jl, tris_jl = _box_mesh((-0.022, -0.080, clamp_z), (0.006, 0.036, 0.020))
        pts_jr, tris_jr = _box_mesh((0.022, -0.080, clamp_z), (0.006, 0.036, 0.020))
        submeshes.append(("ClampJawL", "BrushedSteelMat", pts_jl, tris_jl))
        submeshes.append(("ClampJawR", "BrushedSteelMat", pts_jr, tris_jr))

    elif component_id == "iron_ring_gauze":
        # Open iron ring + square wire gauze with white ceramic center disc + front grasp tab
        ring_c = np.array(
            [[0.048 * math.cos(t), 0.048 * math.sin(t), 0.0] for t in np.linspace(0.0, 2.0 * math.pi, 28, endpoint=False)]
        )
        pts_rg, tris_rg = _swept_tube_mesh(ring_c, np.full(len(ring_c), 0.0045))
        submeshes.append(("IronRing", "DarkCastIronMat", pts_rg, tris_rg))
        pts_gz, tris_gz = _box_mesh((0.0, 0.0, 0.0045), (0.096, 0.096, 0.0025))
        submeshes.append(("WireGauze", "BrushedSteelMat", pts_gz, tris_gz))
        pts_cm, tris_cm = _lathe_profile_mesh([(0.0, 0.0055), (0.032, 0.0055), (0.032, 0.0065), (0.0, 0.0065)])
        submeshes.append(("AsbestosCeramicCore", "CeramicWhiteMat", pts_cm, tris_cm))
        pts_tab, tris_tab = _box_mesh((0.0, -0.048, 0.008), (0.036, 0.016, 0.014))
        submeshes.append(("FrontGraspLug", "BrushedSteelMat", pts_tab, tris_tab))

    elif component_id == "distillation_flask":
        # Round-bottom bulb (R=0.042 at z=0.042) + cylindrical neck + 1:10 frosted ground socket
        prof = []
        for deg in range(5, 152, 8):
            ang = math.radians(deg)
            r = max(0.0138, 0.042 * math.sin(ang))
            z = 0.042 - 0.042 * math.cos(ang)
            prof.append((r, z))
        prof[0] = (0.0, 0.0)
        prof.extend([(0.0138, 0.095), (0.0155, 0.095), (0.0168, 0.125), (0.0132, 0.125), (0.0118, 0.095), (0.0, 0.075)])
        pts_fl, tris_fl = _lathe_profile_mesh(prof)
        submeshes.append(("FlaskBodyGlass", "BorosilicateGlassMat", pts_fl, tris_fl))
        pts_col, tris_col = _lathe_profile_mesh([(0.0130, 0.096), (0.0168, 0.096), (0.0172, 0.125), (0.0135, 0.125)])
        submeshes.append(("FlaskGroundSocket", "FrostedGroundGlassMat", pts_col, tris_col))
        pts_sol, tris_sol = _lathe_profile_mesh([(0.0, 0.004), (0.036, 0.014), (0.038, 0.032), (0.0, 0.032)])
        submeshes.append(("DistillationMixture", "SolventLiquidMat", pts_sol, tris_sol))

    elif component_id == "distillation_head":
        # Vertical stem + top socket + frosted lower male taper + -18 deg side-arm
        pts_v, tris_v = _lathe_profile_mesh(
            [
                (0.0, -0.025), (0.0108, -0.025), (0.0132, 0.002), (0.0132, 0.058),
                (0.0152, 0.060), (0.0160, 0.082), (0.0124, 0.082), (0.0, 0.058),
            ]
        )
        submeshes.append(("HeadVerticalGlass", "BorosilicateGlassMat", pts_v, tris_v))
        pts_m, tris_m = _lathe_profile_mesh([(0.0108, -0.025), (0.0132, 0.002), (0.0110, 0.002), (0.0095, -0.025)])
        submeshes.append(("LowerMaleTaper", "FrostedGroundGlassMat", pts_m, tris_m))
        pts_ts, tris_ts = _lathe_profile_mesh([(0.0135, 0.058), (0.0162, 0.058), (0.0165, 0.082), (0.0132, 0.082)])
        submeshes.append(("TopThermometerSocket", "FrostedGroundGlassMat", pts_ts, tris_ts))
        # -18 deg vapor side-arm starting from (0,0,0.022) along DIR_ARM
        sa_c = np.array([DIR_ARM * s + np.array([0.0, 0.0, 0.022]) for s in np.linspace(0.006, 0.098, 8)])
        sa_r = np.array([0.009, 0.009, 0.009, 0.009, 0.0125, 0.0120, 0.0112, 0.0105])
        pts_sa, tris_sa = _swept_tube_mesh(sa_c, sa_r, n_theta=20)
        submeshes.append(("SideArmTube", "BorosilicateGlassMat", pts_sa, tris_sa))
        sm_c = sa_c[-3:]
        pts_sm, tris_sm = _swept_tube_mesh(sm_c, np.array([0.0128, 0.0118, 0.0108]), n_theta=20)
        submeshes.append(("SideArmMaleTaper", "FrostedGroundGlassMat", pts_sm, tris_sm))

    elif component_id == "mercury_thermometer":
        pts_st, tris_st = _lathe_profile_mesh(
            [(0.0, -0.068), (0.0046, -0.068), (0.0048, -0.054), (0.0048, 0.108), (0.0, 0.108)]
        )
        submeshes.append(("GlassCapillaryStem", "BorosilicateGlassMat", pts_st, tris_st))
        # Crimson mercury bulb whose top rim sits at exact z_local = -0.058 m
        pts_mb, tris_mb = _lathe_profile_mesh([(0.0, -0.067), (0.0040, -0.067), (0.0040, -0.058), (0.0, -0.058)])
        submeshes.append(("MercuryBulb", "MercuryRedMat", pts_mb, tris_mb))
        pts_th, tris_th = _lathe_profile_mesh([(0.0, -0.058), (0.0014, -0.058), (0.0014, 0.085), (0.0, 0.085)])
        submeshes.append(("MercuryThread", "MercuryRedMat", pts_th, tris_th))
        pts_hd, tris_hd = _lathe_profile_mesh([(0.0046, 0.058), (0.0054, 0.058), (0.0054, 0.104), (0.0046, 0.104)])
        submeshes.append(("CalibrationHandleBand", "CeramicWhiteMat", pts_hd, tris_hd))

    elif component_id == "liebig_condenser":
        # Along local X: inner vapor tube x in [-0.130, 0.130], water jacket x in [-0.095, 0.095]
        pts_in, tris_in = _lathe_profile_mesh(
            [(0.0, -0.130), (0.0085, -0.130), (0.0085, 0.130), (0.0, 0.130)], axis="X"
        )
        submeshes.append(("InnerVaporTube", "BorosilicateGlassMat", pts_in, tris_in))
        pts_jk, tris_jk = _lathe_profile_mesh(
            [(0.0086, -0.095), (0.0175, -0.095), (0.0175, 0.095), (0.0086, 0.095)], axis="X"
        )
        submeshes.append(("OuterWaterJacket", "BorosilicateGlassMat", pts_jk, tris_jk))
        pts_us, tris_us = _lathe_profile_mesh(
            [(0.0115, -0.132), (0.0165, -0.132), (0.0155, -0.105), (0.0115, -0.105)], axis="X"
        )
        submeshes.append(("UpperFemaleSocket", "FrostedGroundGlassMat", pts_us, tris_us))
        pts_lm, tris_lm = _lathe_profile_mesh(
            [(0.0128, 0.105), (0.0102, 0.132), (0.0082, 0.132), (0.0082, 0.105)], axis="X"
        )
        submeshes.append(("LowerMaleTaper", "FrostedGroundGlassMat", pts_lm, tris_lm))

        # Barbs point along world U_BARB_WORLD; transform U_BARB_WORLD into condenser local frame
        r_cond = _quat_to_rot(WXYZ_CONDENSER)
        u_local = r_cond.T @ U_BARB_WORLD
        for bname, x_off in (("LowerInletBarb", 0.065), ("UpperOutletBarb", -0.065)):
            # Compute local jacket offset so barb root sits around world y=-0.014
            b0 = np.array([x_off, -0.012, -0.005], dtype=np.float64)
            s_vals = np.linspace(0.0, 0.036, 6)
            b_pts = np.array([b0 + s * u_local for s in s_vals])
            b_rad = np.array([0.0058, 0.0062, 0.0072, 0.0068, 0.0058, 0.0052], dtype=np.float64)
            bp, bt = _swept_tube_mesh(b_pts, b_rad, n_theta=16)
            submeshes.append((bname, "BorosilicateGlassMat", bp, bt))

    elif component_id == "tail_adapter":
        # Curves gently from (0, 0, 0) downward to world (+0.066, 0, -0.050) drip tip
        t_c = np.array(
            [
                [0.000, 0.0, 0.000],
                [0.022, 0.0, -0.008],
                [0.044, 0.0, -0.018],
                [0.058, 0.0, -0.030],
                [0.066, 0.0, -0.050],
            ],
            dtype=np.float64,
        )
        t_r = np.array([0.0155, 0.0125, 0.0105, 0.0095, 0.0070], dtype=np.float64)
        pts_ta, tris_ta = _swept_tube_mesh(t_c, t_r, n_theta=20)
        submeshes.append(("CurvedAdapterGlass", "BorosilicateGlassMat", pts_ta, tris_ta))
        pts_ts, tris_ts = _swept_tube_mesh(t_c[:2], np.array([0.0165, 0.0145]), n_theta=20)
        submeshes.append(("AdapterGroundSocket", "FrostedGroundGlassMat", pts_ts, tris_ts))

    elif component_id == "erlenmeyer_receiver":
        pts_er, tris_er = _lathe_profile_mesh(
            [
                (0.0, 0.000), (0.035, 0.000), (0.037, 0.006), (0.014, 0.065),
                (0.014, 0.092), (0.017, 0.093), (0.013, 0.093), (0.012, 0.065), (0.0, 0.012),
            ]
        )
        submeshes.append(("ErlenmeyerBodyGlass", "BorosilicateGlassMat", pts_er, tris_er))
        pts_dn, tris_dn = _lathe_profile_mesh([(0.0, 0.004), (0.031, 0.004), (0.027, 0.018), (0.0, 0.018)])
        submeshes.append(("DistillatePool", "SolventLiquidMat", pts_dn, tris_dn))

    elif component_id == "bench_water_ports":
        pb, tb = _box_mesh((0.0, 0.0, 0.006), (0.42, 0.070, 0.012))
        submeshes.append(("UtilityManifoldBase", "DarkCastIronMat", pb, tb))
        ptap, ttap = _lathe_profile_mesh([(0.0, 0.012), (0.018, 0.012), (0.018, 0.030), (0.0, 0.030)], center_offset=(0.18, 0.0, 0.0))
        submeshes.append(("WaterTapPort", "PortBlueMat", ptap, ttap))
        pdr, tdr = _lathe_profile_mesh([(0.0, 0.012), (0.018, 0.012), (0.018, 0.030), (0.0, 0.030)], center_offset=(-0.15, 0.0, 0.0))
        submeshes.append(("DrainPort", "PortAmberMat", pdr, tdr))

    elif component_id == "staging_trays":
        pts_t, tris_t = _box_mesh((0.0, 0.0, 0.002), (0.58, 0.096, 0.004))
        submeshes.append(("BenchOrganizerMat", "PolymerSlateMat", pts_t, tris_t))

    return submeshes


def _component_colliders(component_id: str) -> dict[str, Any]:
    """Return engine-agnostic convex collider specification + 12-wedge sockets for component."""
    if component_id == "alcohol_lamp":
        return {
            "cylinders": [
                {"pos": [0.0, 0.0, 0.030], "radius": 0.035, "half_height": 0.030},
                {"pos": [0.0, 0.0, 0.068], "radius": 0.015, "half_height": 0.010},
            ],
            "boxes": [],
            "socket_wedges": [],
        }
    if component_id == "iron_stand_left":
        return {
            "boxes": [
                {"pos": [0.0, 0.0, 0.006], "half_size": [0.072, 0.058, 0.006], "wxyz": [1, 0, 0, 0]},
                {"pos": [0.0, -0.018, 0.170], "half_size": [0.007, 0.046, 0.006], "wxyz": [1, 0, 0, 0]},
                {"pos": [-0.024, -0.080, 0.170], "half_size": [0.004, 0.018, 0.010], "wxyz": [1, 0, 0, 0]},
                {"pos": [0.024, -0.080, 0.170], "half_size": [0.004, 0.018, 0.010], "wxyz": [1, 0, 0, 0]},
            ],
            "cylinders": [{"pos": [0.0, 0.030, 0.215], "radius": 0.0065, "half_height": 0.205}],
            "socket_wedges": [],
        }
    if component_id == "iron_stand_right":
        return {
            "boxes": [
                {"pos": [0.0, 0.0, 0.006], "half_size": [0.072, 0.058, 0.006], "wxyz": [1, 0, 0, 0]},
                {"pos": [0.0, -0.018, 0.187], "half_size": [0.007, 0.046, 0.006], "wxyz": [1, 0, 0, 0]},
                {"pos": [-0.025, -0.080, 0.187], "half_size": [0.004, 0.018, 0.012], "wxyz": [1, 0, 0, 0]},
                {"pos": [0.025, -0.080, 0.187], "half_size": [0.004, 0.018, 0.012], "wxyz": [1, 0, 0, 0]},
            ],
            "cylinders": [{"pos": [0.0, 0.030, 0.185], "radius": 0.0065, "half_height": 0.175}],
            "socket_wedges": [],
        }
    if component_id == "iron_ring_gauze":
        return {
            "boxes": [
                {"pos": [0.0, 0.0, 0.004], "half_size": [0.048, 0.048, 0.004], "wxyz": [1, 0, 0, 0]},
                {"pos": [0.0, -0.048, 0.008], "half_size": [0.018, 0.008, 0.007], "wxyz": [1, 0, 0, 0]},
            ],
            "cylinders": [],
            "socket_wedges": [],
        }
    if component_id == "distillation_flask":
        return {
            "cylinders": [
                {"pos": [0.0, 0.0, 0.040], "radius": 0.040, "half_height": 0.038},
                {"pos": [0.0, 0.0, 0.080], "radius": 0.014, "half_height": 0.016},
            ],
            "boxes": [],
            "socket_wedges": _ring_wedge_boxes((0.0, 0.0, 0.110), radius=0.0185, thickness=0.003, height=0.028, n_wedges=12, axis="Z"),
        }
    if component_id == "distillation_head":
        return {
            "cylinders": [
                {"pos": [0.0, 0.0, -0.012], "radius": 0.0108, "half_height": 0.014},
                {"pos": [0.0, 0.0, 0.030], "radius": 0.0132, "half_height": 0.028},
            ],
            "boxes": [],
            "socket_wedges": _ring_wedge_boxes((0.0, 0.0, 0.070), radius=0.0165, thickness=0.003, height=0.022, n_wedges=12, axis="Z"),
        }
    if component_id == "mercury_thermometer":
        return {
            "cylinders": [{"pos": [0.0, 0.0, 0.020], "radius": 0.0048, "half_height": 0.088}],
            "boxes": [],
            "socket_wedges": [],
        }
    if component_id == "liebig_condenser":
        r_cond = _quat_to_rot(WXYZ_CONDENSER)
        u_local = r_cond.T @ U_BARB_WORLD
        barbs = []
        for bname, x_off in (("lower_inlet_barb", 0.065), ("upper_outlet_barb", -0.065)):
            barbs.append(
                {
                    "name": bname,
                    "root_local": [x_off, -0.012, -0.005],
                    "axis_local": [round(float(v), 7) for v in u_local],
                    "length_m": 0.036,
                    "r_tip_m": 0.0052,
                    "r_ridge_m": 0.0072,
                    "r_root_m": 0.0058,
                }
            )
        return {
            "cylinders": [
                {"pos": [0.0, 0.0, 0.0], "radius": 0.0175, "half_height": 0.095, "axis": "X"},
                {"pos": [0.118, 0.0, 0.0], "radius": 0.0115, "half_height": 0.014, "axis": "X"},
            ],
            "boxes": [],
            "socket_wedges": _ring_wedge_boxes((-0.118, 0.0, 0.0), radius=0.0160, thickness=0.003, height=0.026, n_wedges=12, axis="X"),
            "barbs": barbs,
        }
    if component_id == "tail_adapter":
        return {
            "cylinders": [],
            "boxes": [{"pos": [0.028, 0.0, -0.014], "half_size": [0.024, 0.011, 0.012], "wxyz": [1, 0, 0, 0]}],
            "socket_wedges": _ring_wedge_boxes((0.0, 0.0, 0.0), radius=0.0160, thickness=0.003, height=0.022, n_wedges=12, axis="X"),
        }
    if component_id == "erlenmeyer_receiver":
        return {
            "cylinders": [
                {"pos": [0.0, 0.0, 0.028], "radius": 0.032, "half_height": 0.028},
                {"pos": [0.0, 0.0, 0.075], "radius": 0.014, "half_height": 0.018},
            ],
            "boxes": [],
            "socket_wedges": [],
        }
    if component_id == "bench_water_ports":
        return {
            "boxes": [{"pos": [0.0, 0.0, 0.006], "half_size": [0.21, 0.035, 0.006], "wxyz": [1, 0, 0, 0]}],
            "cylinders": [],
            "socket_wedges": [],
        }
    return {
        "boxes": [{"pos": [0.0, 0.0, 0.002], "half_size": [0.29, 0.048, 0.002], "wxyz": [1, 0, 0, 0]}],
        "cylinders": [],
        "socket_wedges": [],
    }


def compute_nominal_apparatus_layout() -> dict[str, Any]:
    """Compute nominal 0.05 mm coaxial apparatus joint world coordinates and tolerances."""
    head_taper_world = (HEAD_ASM_POS[0], HEAD_ASM_POS[1], HEAD_ASM_POS[2] + 0.000)
    flask_socket_world = (FLASK_ASM_POS[0], FLASK_ASM_POS[1], FLASK_ASM_POS[2] + 0.115)
    # Coaxial alignment along head-flask stem: z_flask_rim = 0.870 + 0.115 = 0.985 == head_taper_world[2]
    head_top_socket = (HEAD_ASM_POS[0], HEAD_ASM_POS[1], HEAD_ASM_POS[2] + 0.080)  # 1.065 m
    thm_septum_seat = THM_ASM_POS  # 1.065 m
    thm_bulb_top = (THM_ASM_POS[0], THM_ASM_POS[1], THM_ASM_POS[2] - 0.058)  # 1.007 m
    head_sidearm_bottom = J_SIDEARM_WORLD  # 1.007 m

    sidearm_taper_world = tuple(float(J_SIDEARM_WORLD[k] + 0.090 * DIR_ARM[k]) for k in range(3))
    r_cond = _quat_to_rot(WXYZ_CONDENSER)
    cond_upper_socket_world = tuple(float(v) for v in (np.array(COND_ASM_POS) + r_cond @ np.array([-0.120, 0.0, 0.0])))
    cond_lower_taper_world = tuple(float(v) for v in (np.array(COND_ASM_POS) + r_cond @ np.array([0.120, 0.0, 0.0])))
    tail_drip_tip_world = (TAIL_ASM_POS[0] + 0.066, TAIL_ASM_POS[1], TAIL_ASM_POS[2] - 0.050)
    receiver_mouth_world = (RECEIVER_ASM_POS[0], RECEIVER_ASM_POS[1], RECEIVER_ASM_POS[2] + 0.092)

    pairs = [
        ("flask_neck_to_head_taper", flask_socket_world, head_taper_world),
        ("head_top_to_thermometer_septum", head_top_socket, thm_septum_seat),
        ("thermometer_bulb_top_to_sidearm_lip", thm_bulb_top, head_sidearm_bottom),
        ("head_sidearm_to_condenser_upper_socket", sidearm_taper_world, cond_upper_socket_world),
        ("condenser_lower_taper_to_tail_adapter", cond_lower_taper_world, TAIL_ASM_POS),
        ("tail_drip_tip_to_receiver_mouth_xy", (tail_drip_tip_world[0], tail_drip_tip_world[1], 0.0), (receiver_mouth_world[0], receiver_mouth_world[1], 0.0)),
    ]
    pair_records = []
    max_err_mm = 0.0
    for name, pa, pb in pairs:
        err_mm = float(np.linalg.norm(np.array(pa) - np.array(pb)) * 1000.0)
        max_err_mm = max(max_err_mm, err_mm)
        pair_records.append(
            {
                "joint_name": name,
                "frame_a_world": [round(float(x), 6) for x in pa],
                "frame_b_world": [round(float(x), 6) for x in pb],
                "error_mm": round(err_mm, 5),
            }
        )
    return {
        "schema_version": "distillation_v04_coaxial_layout/v0.1",
        "z_table_m": Z_TABLE,
        "pitch_deg": PITCH_DEG,
        "max_coaxial_error_mm": round(max_err_mm, 5),
        "lower_inlet_barb_root_world": list(LOWER_INLET_BARB_ROOT),
        "lower_inlet_barb_tip_world": list(LOWER_INLET_BARB_TIP),
        "upper_outlet_barb_root_world": list(UPPER_OUTLET_BARB_ROOT),
        "upper_outlet_barb_tip_world": list(UPPER_OUTLET_BARB_TIP),
        "coaxial_joint_pairs": pair_records,
    }


def _material_scope_usda(comp_id: str) -> str:
    return f'''        def Scope "Looks"
        {{
            def Material "BorosilicateGlassMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/BorosilicateGlassMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.86, 0.94, 0.98)
                    float inputs:ior = 1.47
                    float inputs:metallic = 0.0
                    float inputs:opacity = 0.26
                    float inputs:roughness = 0.05
                    token outputs:surface
                }}
            }}
            def Material "FrostedGroundGlassMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/FrostedGroundGlassMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.90, 0.93, 0.95)
                    float inputs:ior = 1.47
                    float inputs:metallic = 0.0
                    float inputs:opacity = 0.68
                    float inputs:roughness = 0.52
                    token outputs:surface
                }}
            }}
            def Material "SolventLiquidMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/SolventLiquidMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.36, 0.72, 0.92)
                    float inputs:ior = 1.36
                    float inputs:metallic = 0.0
                    float inputs:opacity = 0.42
                    float inputs:roughness = 0.04
                    token outputs:surface
                }}
            }}
            def Material "MercuryRedMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/MercuryRedMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.82, 0.08, 0.12)
                    float inputs:metallic = 0.1
                    float inputs:roughness = 0.18
                    token outputs:surface
                }}
            }}
            def Material "BrushedSteelMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/BrushedSteelMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.72, 0.74, 0.77)
                    float inputs:metallic = 0.85
                    float inputs:roughness = 0.28
                    token outputs:surface
                }}
            }}
            def Material "DarkCastIronMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/DarkCastIronMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.14, 0.16, 0.19)
                    float inputs:metallic = 0.45
                    float inputs:roughness = 0.62
                    token outputs:surface
                }}
            }}
            def Material "BrassBurnerMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/BrassBurnerMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.78, 0.60, 0.24)
                    float inputs:metallic = 0.90
                    float inputs:roughness = 0.24
                    token outputs:surface
                }}
            }}
            def Material "CeramicWhiteMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/CeramicWhiteMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.94, 0.94, 0.92)
                    float inputs:metallic = 0.0
                    float inputs:roughness = 0.78
                    token outputs:surface
                }}
            }}
            def Material "PortBlueMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/PortBlueMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.18, 0.56, 0.88)
                    float inputs:metallic = 0.2
                    float inputs:roughness = 0.35
                    token outputs:surface
                }}
            }}
            def Material "PortAmberMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/PortAmberMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.86, 0.45, 0.20)
                    float inputs:metallic = 0.2
                    float inputs:roughness = 0.35
                    token outputs:surface
                }}
            }}
            def Material "PolymerSlateMat"
            {{
                token outputs:surface.connect = </World/{comp_id}/Looks/PolymerSlateMat/Shader.outputs:surface>
                def Shader "Shader"
                {{
                    uniform token info:id = "UsdPreviewSurface"
                    color3f inputs:diffuseColor = (0.20, 0.24, 0.28)
                    float inputs:metallic = 0.05
                    float inputs:roughness = 0.72
                    token outputs:surface
                }}
            }}
        }}'''


def _write_component_usda(path: Path, spec: ComponentCADSpec, submeshes: list[Any]) -> None:
    mesh_blocks: list[str] = []
    for name, mat, pts, tris in submeshes:
        p_str = ", ".join(f"({p[0]:.6f}, {p[1]:.6f}, {p[2]:.6f})" for p in pts)
        c_str = ", ".join("3" for _ in range(len(tris)))
        i_str = ", ".join(str(int(k)) for tri in tris for k in tri)
        mesh_blocks.append(
            f'''        def Mesh "{name}" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {{
            rel material:binding = </World/{spec.component_id}/Looks/{mat}>
            bool doubleSided = 1
            uniform token subdivisionScheme = "none"
            int[] faceVertexCounts = [{c_str}]
            int[] faceVertexIndices = [{i_str}]
            point3f[] points = [{p_str}]
        }}'''
        )

    meshes_text = "\n".join(mesh_blocks)
    usda = f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Xform "{spec.component_id}" (
        kind = "component"
    )
    {{
{_material_scope_usda(spec.component_id)}

{meshes_text}
    }}
}}
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(usda, encoding="utf-8")


def build_all_glassware_cad_v04(cad_root: str | Path) -> dict[str, Any]:
    """Generate all 12 parametric OpenUSD apparatus components + glassware_cad_specs.json."""
    root = Path(cad_root)
    root.mkdir(parents=True, exist_ok=True)
    layout = compute_nominal_apparatus_layout()
    components_payload: dict[str, Any] = {}

    for comp_id, spec in DISTILLATION_COMPONENT_SPECS.items():
        submeshes = _build_component_visual_submeshes(comp_id)
        asset_usda = root / comp_id / "asset.usda"
        _write_component_usda(asset_usda, spec, submeshes)
        col = _component_colliders(comp_id)
        components_payload[comp_id] = {
            "component_id": comp_id,
            "category": spec.category,
            "material_kind": spec.material_kind,
            "dynamic_in_sop": spec.dynamic_in_sop,
            "mass_kg": spec.mass_kg,
            "assembled_xyz": list(spec.assembled_xyz),
            "assembled_wxyz": list(spec.assembled_wxyz),
            "staged_xyz": list(spec.staged_xyz),
            "staged_wxyz": list(spec.staged_wxyz),
            "grasp_local_xyz": list(spec.grasp_local_xyz),
            "submesh_count": len(submeshes),
            "colliders": col,
            "asset_relpath": f"{comp_id}/asset.usda",
        }

    specs_doc = {
        "schema_version": "distillation_v04_cad_specs/v0.1",
        "layout": layout,
        "components": components_payload,
    }
    (root / "glassware_cad_specs.json").write_text(json.dumps(specs_doc, indent=2), encoding="utf-8")
    return specs_doc
