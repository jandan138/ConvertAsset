#!/usr/bin/env python3
"""Region-scoped spoon cross-section scales with locked topology.

Handle, neck, and head are separate deform windows. This does not rewrite the
source EBench intervention script. Inertia overlays stay on the matched-spoon
tool and must be locked to the control ledger in Phase 2.
"""

from __future__ import annotations


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def band_weight(z: float, inner_lo: float, inner_hi: float, fade: float = 0.05) -> float:
    if inner_lo > inner_hi:
        raise ValueError("inner band must be ordered")
    if inner_lo <= z <= inner_hi:
        return 1.0
    if z < inner_lo:
        return 1.0 - smoothstep((inner_lo - z) / fade)
    return 1.0 - smoothstep((z - inner_hi) / fade)


def region_weight(z: float, region: str) -> float:
    if region == "handle":
        return band_weight(z, -10.0, -0.1, fade=0.05)
    if region == "neck":
        return band_weight(z, -0.05, 0.05, fade=0.02)
    if region == "head":
        return band_weight(z, 0.1, 10.0, fade=0.05)
    raise ValueError(f"unknown region: {region}")


def deform_point(point, scale: float, region: str, axes: str = "xy"):
    if not 1.0 <= scale <= 3.0:
        raise ValueError("scale must be in [1, 3]")
    if axes not in {"xy", "x", "y"}:
        raise ValueError("axes must be xy, x, or y")
    x, y, z = point
    factor = 1.0 + (scale - 1.0) * region_weight(z, region)
    if axes == "xy":
        return [x * factor, y * factor, z]
    if axes == "x":
        return [x * factor, y, z]
    return [x, y * factor, z]


def cell_spec(cell_id: str):
    spec = REGIONS[cell_id]
    region, scale = spec[0], spec[1]
    axes = spec[2] if len(spec) > 2 else "xy"
    return region, scale, axes


REGIONS = {
    "P2-handle-1p25": ("handle", 1.25),
    "P2-handle-1p50": ("handle", 1.50),
    "P2-handle-2p00": ("handle", 2.00),
    "P2-neck-1p50": ("neck", 1.50),
    "P2-neck-2p00": ("neck", 2.00),
    "P2-head-2p00": ("head", 2.00),
    "P2-handle-thick-2p00": ("handle", 2.00, "y"),
}

MESH_PATH = "/root/obj_spoon/geometry_0/geometry_0"
SPOON_PATH = "/root/obj_spoon"
INERTIA_ATTRS = (
    "physics:mass",
    "physics:centerOfMass",
    "physics:diagonalInertia",
    "physics:principalAxes",
)


def ledger(stage, prim_path: str = SPOON_PATH) -> dict:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim:
        raise ValueError(f"missing spoon prim: {prim_path}")
    values = {}
    for name in INERTIA_ATTRS:
        attr = prim.GetAttribute(name)
        if not attr or not attr.HasAuthoredValueOpinion():
            raise ValueError(f"unauthored {name}")
        values[name] = attr.Get()
    return values


def write_deformed_overlay(source_overlay, output, cell_id: str) -> dict:
    """Copy a native overlay, deform one region, keep the authored inertia ledger."""
    from pxr import Gf, Usd, UsdGeom, Vt

    import hashlib
    import shutil
    from pathlib import Path

    source_overlay = Path(source_overlay)
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    region, scale, axes = cell_spec(cell_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_overlay, output)
    before = Usd.Stage.Open(str(source_overlay))
    locked = ledger(before)
    stage = Usd.Stage.Open(str(output))
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath(MESH_PATH))
    if not mesh:
        raise ValueError("spoon mesh missing")
    old = [tuple(p) for p in mesh.GetPointsAttr().Get()]
    new = [deform_point(p, scale, region, axes) for p in old]
    if len(new) != len(old):
        raise ValueError("topology changed")
    if any(a[2] != b[2] for a, b in zip(old, new)):
        raise ValueError("deform must not move z")
    mesh.GetPointsAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*p) for p in new]))
    lo = [min(p[i] for p in new) for i in range(3)]
    hi = [max(p[i] for p in new) for i in range(3)]
    mesh.GetExtentAttr().Set([Gf.Vec3f(*lo), Gf.Vec3f(*hi)])
    stage.GetRootLayer().Save()
    after = Usd.Stage.Open(str(output))
    got = ledger(after)
    if got != locked:
        raise ValueError(f"inertia ledger drifted for {cell_id}")
    moved = sum(
        1 for a, b in zip(old, new) if any(abs(x - y) > 1e-12 for x, y in zip(a, b))
    )
    report = {
        "schema": "convertasset.spoon_physics_lane.geometry_overlay.v1",
        "cell_id": cell_id,
        "region": region,
        "scale": scale,
        "axes": axes,
        "source_overlay": str(source_overlay.resolve()),
        "output": str(output.resolve()),
        "vertex_count": len(old),
        "moved_vertices": moved,
        "inertia_locked_to_source": True,
        "normals_recomputed": False,
        "collision_note": "convexDecomposition recooks from updated points; face normals left authored",
        "source_sha256": hashlib.sha256(source_overlay.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "ledger": {name: _encode(value) for name, value in locked.items()},
    }
    output.with_suffix(".json").write_text(
        __import__("json").dumps(report, indent=2) + "\n"
    )
    return report


def _encode(value):
    if value is None:
        return None
    imag = getattr(value, "imaginary", None)
    if imag is not None and hasattr(value, "real"):
        return [float(value.real), *[float(v) for v in imag]]
    if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        return [float(v) for v in value]
    if hasattr(value, "real") and not hasattr(value, "imaginary"):
        return float(value)
    return value
