#!/usr/bin/env python3
"""Author mass / COM / inertia / contact overlays without changing mesh topology.

Phase 2 locks inertia by copying the control overlay. Phases 3–6 start from an
already compiled native overlay and change only the declared ledger.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


SPOON_PATH = "/root/obj_spoon"
MESH_PATH = "/root/obj_spoon/geometry_0/geometry_0"
INERTIA_ATTRS = (
    "physics:mass",
    "physics:centerOfMass",
    "physics:diagonalInertia",
    "physics:principalAxes",
)


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


def read_ledger(path: Path, prim_path: str = SPOON_PATH) -> dict:
    from pxr import Usd

    stage = Usd.Stage.Open(str(path))
    prim = stage.GetPrimAtPath(prim_path)
    if not prim:
        raise ValueError(f"missing spoon prim: {prim_path}")
    values = {}
    for name in INERTIA_ATTRS:
        attr = prim.GetAttribute(name)
        if not attr or not attr.HasAuthoredValueOpinion():
            raise ValueError(f"unauthored {name}")
        values[name] = attr.Get()
    mesh = stage.GetPrimAtPath(MESH_PATH)
    contact = mesh.GetAttribute("physxCollision:contactOffset") if mesh else None
    values["physxCollision:contactOffset"] = (
        contact.Get() if contact and contact.HasAuthoredValueOpinion() else None
    )
    return values


def write_physics_overlay(source_overlay, output, updates: dict, cell_id: str) -> dict:
    from pxr import Gf, Usd, UsdPhysics, UsdShade

    source_overlay = Path(source_overlay)
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_overlay, output)
    before = Usd.Stage.Open(str(source_overlay))
    source_points = list(
        before.GetPrimAtPath(MESH_PATH).GetAttribute("points").Get()
    )
    stage = Usd.Stage.Open(str(output))
    prim = stage.GetPrimAtPath(SPOON_PATH)
    mesh = stage.GetPrimAtPath(MESH_PATH)
    applied = {}
    for name, value in updates.items():
        if name in {"physics:staticFriction", "physics:dynamicFriction"}:
            continue
        attr = prim.GetAttribute(name) if name.startswith("physics:") else mesh.GetAttribute(name)
        if not attr:
            raise ValueError(f"missing attribute {name}")
        if name == "physics:mass":
            attr.Set(float(value))
        elif name in {"physics:centerOfMass", "physics:diagonalInertia"}:
            attr.Set(Gf.Vec3f(*[float(v) for v in value]))
        elif name == "physics:principalAxes":
            attr.Set(Gf.Quatf(*[float(v) for v in value]))
        elif name == "physxCollision:contactOffset":
            attr.Set(float(value))
        else:
            raise ValueError(f"unsupported update {name}")
        applied[name] = value
    friction = {k: updates[k] for k in ("physics:staticFriction", "physics:dynamicFriction") if k in updates}
    friction_note = "source_unauthored"
    if friction:
        mat_prim = stage.DefinePrim("/root/obj_spoon/LanePhysicsMaterial")
        mat = UsdPhysics.MaterialAPI.Apply(mat_prim)
        if "physics:staticFriction" in friction:
            mat.CreateStaticFrictionAttr(float(friction["physics:staticFriction"]))
            applied["physics:staticFriction"] = friction["physics:staticFriction"]
        if "physics:dynamicFriction" in friction:
            mat.CreateDynamicFrictionAttr(float(friction["physics:dynamicFriction"]))
            applied["physics:dynamicFriction"] = friction["physics:dynamicFriction"]
        binding = UsdShade.MaterialBindingAPI.Apply(mesh)
        binding.Bind(UsdShade.Material(mat_prim), UsdShade.Tokens.weakerThanDescendants, "physics")
        friction_note = (
            "overlay_PhysicsMaterialAPI on /root/obj_spoon/LanePhysicsMaterial; "
            "source spoon had no authored friction"
        )
    stage.GetRootLayer().Save()
    after = Usd.Stage.Open(str(output))
    after_points = list(after.GetPrimAtPath(MESH_PATH).GetAttribute("points").Get())
    if source_points != after_points:
        raise ValueError("physics overlay must not change mesh points")
    report = {
        "schema": "convertasset.spoon_physics_lane.physics_overlay.v1",
        "cell_id": cell_id,
        "source_overlay": str(source_overlay.resolve()),
        "output": str(output.resolve()),
        "applied": applied,
        "friction_note": friction_note,
        "mesh_points_unchanged": True,
        "source_sha256": hashlib.sha256(source_overlay.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "source_ledger": {k: _encode(v) for k, v in read_ledger(source_overlay).items()},
        "output_ledger": {k: _encode(v) for k, v in read_ledger(output).items()},
    }
    output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    return report
