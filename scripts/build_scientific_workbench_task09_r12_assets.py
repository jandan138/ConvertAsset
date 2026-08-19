#!/usr/bin/env python3
"""Build Task 09 r12 oven and room-floor source-bound admission inputs."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

if __package__:
    from .build_scientific_workbench_r11_assets import (
        _oven_device_profile,
        _oven_facade,
        _oven_physics,
    )
else:
    from build_scientific_workbench_r11_assets import (
        _oven_device_profile,
        _oven_facade,
        _oven_physics,
    )


OVEN_PARTS = {
    0: "base",
    1: "chimney_damper",
    2: "door_latch",
    3: "lower_dial",
    4: "main_door",
    5: "power_rocker",
    6: "shelf",
    7: "shelf",
    8: "shelf",
    9: "shelf",
    10: "temperature_needle",
    11: "upper_dial",
}
VR_TASK_PARTS = {4: "main_door", 5: "power_rocker", 11: "upper_dial"}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _json(path: Path, payload: dict[str, Any]) -> Path:
    return _write(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False),
    )


def _oven_r12_facade(source: Path, *, parts: dict[int, str]) -> str:
    facade = _oven_facade(source)
    for group, part in parts.items():
        pattern = re.compile(
            rf'(        over Xform "group_{group}"(?: \(.*?^        \))?\n        \{{)',
            re.MULTILINE | re.DOTALL,
        )
        collision = f'''
            over Xform "{part}"
            {{
                over Mesh "mesh_0"
                {{
                    token physics:approximation = "convexDecomposition"
                }}
            }}'''
        facade, count = pattern.subn(lambda match: match.group(1) + collision, facade, count=1)
        if count != 1:
            raise ValueError(f"could not locate unique oven group override: {group}")
    return facade


def _floor_facade(room_source: Path) -> str:
    del room_source
    return '''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{
    def Xform "table"
    {
        def Cube "floor_support" (
            prepend apiSchemas = ["PhysicsCollisionAPI"]
        )
        {
            color3f[] primvars:displayColor = [(0.18, 0.18, 0.18)]
            double size = 1
            double3 xformOp:scale = (6.5, 5.5, 0.02)
            double3 xformOp:translate = (0, 0, -0.01)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
        }
    }
}
'''


def _floor_support_profile(facade: Path) -> dict[str, Any]:
    return {
        "schema_version": "aan.static_support_profile.v1",
        "profile_id": "scientific_workbench.analytical_room.floor.compat_static_support",
        "revision": "r1",
        "source_binding": {"sha256": _sha(facade)},
        "asset_entry_prim": "/World/table",
        "collider_policy": "prefer_source_then_proxy",
        "source_collider_prim": "/World/table/floor_support",
        "proxy": {
            "prim_path": "/World/table/__aan_static_support_proxy",
            "center_xyz": [0.0, 0.0, -0.01],
            "size_xyz": [6.5, 5.5, 0.02],
        },
        "support_surface": {
            "top_z": 0.0,
            "x_range": [-3.25, 3.25],
            "y_range": [-2.75, 2.75],
            "edge_band_m": 0.05,
        },
        "physics_material": {
            "prim_path": "/World/table/__aan_static_support_material",
            "static_friction": 0.5,
            "dynamic_friction": 0.5,
            "restitution": 0.0,
            "friction_combine_mode": "max",
            "restitution_combine_mode": "multiply",
            "calibration_status": "provisional_unmeasured",
        },
    }


def build_r12_assets(*, oven_source: Path, room_source: Path, out: Path) -> dict[str, Path]:
    oven_source = oven_source.resolve()
    room_source = room_source.resolve()
    out = out.resolve()
    if not oven_source.is_file() or not room_source.is_file():
        raise FileNotFoundError("oven source and analytical-room source USD are required")

    oven_facade = _write(
        out / "analog_gravity_convection_oven_r12/facade.usda",
        _oven_r12_facade(oven_source, parts=VR_TASK_PARTS),
    )
    oven_all_parts_experimental = _write(
        out / "analog_gravity_convection_oven_r12/facade_all_parts_experimental.usda",
        _oven_r12_facade(oven_source, parts=OVEN_PARTS),
    )
    oven_physics_payload = _oven_physics(oven_facade)
    oven_physics_payload["profile_id"] = (
        "scientific_workbench.analog_gravity_convection_oven.provisional.r12"
    )
    oven_physics_payload["revision"] = "r12"
    oven_physics = _json(
        out / "analog_gravity_convection_oven_r12/physics_profile.json",
        oven_physics_payload,
    )
    oven_device_payload = _oven_device_profile(oven_facade)
    oven_device_payload["profile_id"] = (
        "scientific_workbench.analog_gravity_convection_oven.r12"
    )
    oven_device_payload["revision"] = "r12"
    oven_device_profile = _json(
        out / "analog_gravity_convection_oven_r12/device_profile.json",
        oven_device_payload,
    )
    collision_meshes = [
        {
            "prim_path": (
                f"/World/AnalogGravityConvectionOven/Source/group_{group}/"
                f"{part}/mesh_0"
            ),
            "rigid_link": f"/World/AnalogGravityConvectionOven/Source/group_{group}",
            "approximation": "convexDecomposition",
        }
        for group, part in sorted(VR_TASK_PARTS.items())
    ]
    oven_collision_audit = _json(
        out / "analog_gravity_convection_oven_r12/collision_intent.json",
        {
            "schema_version": "aan.articulated_collision_intent.v1",
            "status": "declared",
            "source_usd": str(oven_source),
            "source_sha256": _sha(oven_source),
            "source_modified": False,
            "facade_sha256": _sha(oven_facade),
            "expected_collision_mesh_count": 3,
            "collision_meshes": collision_meshes,
            "joint_topology_policy": "preserve_source_per_link_articulation",
            "fallback_policy": "task_controls_no_convex_hull_fallback",
            "fixed_and_non_task_link_policy": "preserve_source_collision_approximation",
            "all_parts_experiment": {
                "facade": str(oven_all_parts_experimental),
                "status": "blocked_runtime_cook_timeout",
                "timeout_seconds": 900,
            },
            "claim_boundary": (
                "Declared per-link collision approximation only; Isaac 4.1 cooking and "
                "state-cycle evidence are required before promotion."
            ),
        },
    )

    floor_facade = _write(
        out / "analytical_room_floor_static_support/facade.usda",
        _floor_facade(room_source),
    )
    floor_support_profile = _json(
        out / "analytical_room_floor_static_support/static_support_profile.json",
        _floor_support_profile(floor_facade),
    )
    floor_provenance = _json(
        out / "analytical_room_floor_static_support/provenance.json",
        {
            "schema_version": "aan.room_floor_support_source_binding.v1",
            "source_usd": str(room_source),
            "source_sha256": _sha(room_source),
            "source_prim": "/World/Floor",
            "source_modified": False,
            "facade_sha256": _sha(floor_facade),
            "visible_floor_owner": "scientific_environment_code_room_analytical_instrumentation_v2",
            "compatibility_runtime_id": "table",
            "claim_boundary": (
                "The package provides qualified collision/support geometry. The room "
                "environment owns final floor rendering; Scenario Forge consumer wrappers "
                "hide the duplicate support presentation."
            ),
        },
    )
    return {
        "oven_facade": oven_facade,
        "oven_all_parts_experimental": oven_all_parts_experimental,
        "oven_physics": oven_physics,
        "oven_device_profile": oven_device_profile,
        "oven_collision_audit": oven_collision_audit,
        "floor_facade": floor_facade,
        "floor_support_profile": floor_support_profile,
        "floor_provenance": floor_provenance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oven-source", type=Path, required=True)
    parser.add_argument("--room-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build_r12_assets(
        oven_source=args.oven_source,
        room_source=args.room_source,
        out=args.out,
    )
    print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
