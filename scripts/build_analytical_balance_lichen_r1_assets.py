#!/usr/bin/env python3
"""Build source-bound LICHEN analytical-balance admission inputs.

The incoming USDA has four independent sliding doors and sibling handles, but
no UsdPhysics joints.  This producer facade authors a fixed-base articulation
with four prismatic doors and welded handles.  Buttons stay visual-only.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


BALANCE_ENTRY = "/World/AnalyticalBalanceLichen"
BALANCE_SOURCE = f"{BALANCE_ENTRY}/Source"
ANIMATION_OPEN_M = 0.105
STAGE_METRICS = {
    "meters_per_unit": 1.0,
    "kilograms_per_unit": 1.0,
    "up_axis": "Z",
    "time_codes_per_second": 24.0,
    "frames_per_second": 24.0,
}


@dataclass(frozen=True)
class DoorSpec:
    semantic: str
    prim_name: str
    handle_prim_name: str
    mesh_name: str
    handle_mesh_name: str
    axis: str
    upper_limit_m: float
    dof_index: int
    extent_xyz: tuple[float, float, float]
    handle_extent_xyz: tuple[float, float, float]
    rest_xyz: tuple[float, float, float]
    grasp_parent_local_m: list[float]
    handle_collision: bool = False


DOORS: tuple[DoorSpec, ...] = (
    DoorSpec(
        "front_door",
        "Front_Sliding_Glass_Door",
        "Front_Door_Handle",
        "Cube_019",
        "Cube_021",
        "X",
        0.125,
        0,
        (0.14636, 0.003, 0.18595),
        (0.012, 0.008, 0.052),
        (0.0, -0.024855000898241997, 0.16856500506401062),
        [0.0, -0.0125, 0.0],
        True,
    ),
    DoorSpec(
        "left_door",
        "Left_Sliding_Glass_Door",
        "Left_Door_Handle",
        "Cube_016",
        "Cube_022",
        "Y",
        0.135,
        1,
        (0.003, 0.15014, 0.18595),
        (0.008, 0.012, 0.052),
        (-0.07168000191450119, 0.04871499910950661, 0.16856500506401062),
        [-0.0105, 0.0, 0.0],
    ),
    DoorSpec(
        "right_door",
        "Right_Sliding_Glass_Door",
        "Right_Door_Handle",
        "Cube_017",
        "Cube_023",
        "Y",
        0.135,
        2,
        (0.003, 0.15014, 0.18595),
        (0.008, 0.012, 0.052),
        (0.07168000191450119, 0.04871499910950661, 0.16856500506401062),
        [0.0105, 0.0, 0.0],
    ),
    DoorSpec(
        "top_door",
        "Top_Sliding_Glass",
        "Top_Door_Handle",
        "Cube_020",
        "Cube_024",
        "Y",
        0.120,
        3,
        (0.14636, 0.15014, 0.003),
        (0.044, 0.016, 0.007),
        (0.0, 0.04871499910950661, 0.26104000210762024),
        [0.0, 0.012, 0.008],
    ),
)


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


def _usda_point(values: tuple[float, float, float] | list[float]) -> str:
    parts: list[str] = []
    for value in values:
        if value == 0:
            parts.append("0")
        elif value == int(value) and abs(value) < 1_000_000:
            parts.append(str(int(value)))
        else:
            parts.append(format(float(value), ".15g"))
    return f"({parts[0]}, {parts[1]}, {parts[2]})"


def _box_inertia(mass: float, extent: tuple[float, float, float]) -> list[float]:
    x, y, z = extent
    return [
        mass * (y * y + z * z) / 12.0,
        mass * (x * x + z * z) / 12.0,
        mass * (x * x + y * y) / 12.0,
    ]


def _body_rule(relative_path: str, mass: float, extent: tuple[float, float, float]) -> dict[str, Any]:
    return {
        "relative_path": relative_path,
        "motion_role": "dynamic",
        "clear_density": True,
        "mass_properties": {
            "mode": "explicit",
            "quality_tier": "provisional_geometry",
            "mass_kg": mass,
            "diagonal_inertia_kg_m2": _box_inertia(mass, extent),
            "center_of_mass_body_local": [0.0, 0.0, 0.0],
            "principal_axes": [1.0, 0.0, 0.0, 0.0],
        },
    }


def _collision_over(mesh_name: str, indent: str) -> str:
    return f'''{indent}over Mesh "{mesh_name}" (
{indent}    prepend apiSchemas = ["PhysicsCollisionAPI", "PhysicsMeshCollisionAPI"]
{indent})
{indent}{{
{indent}    uniform token physics:approximation = "convexHull"
{indent}}}'''


def _door_block(door: DoorSpec) -> str:
    rest = _usda_point(door.rest_xyz)
    grasp = _usda_point(tuple(door.grasp_parent_local_m))
    handle_collision = (
        "\n" + _collision_over(door.handle_mesh_name, "            ")
        if door.handle_collision
        else ""
    )
    return f'''        over Xform "{door.prim_name}" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysxRigidBodyAPI"]
        )
        {{
            bool physics:rigidBodyEnabled = 1
            bool physxRigidBody:disableGravity = true
            uniform token[] xformOpOrder = ["!resetXformStack!", "xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]
            def PhysicsPrismaticJoint "PrismaticJoint"
            {{
                rel physics:body0 = <{BALANCE_SOURCE}>
                rel physics:body1 = <{BALANCE_SOURCE}/{door.prim_name}>
                uniform token physics:axis = "{door.axis}"
                float physics:lowerLimit = 0
                float physics:upperLimit = {door.upper_limit_m}
                point3f physics:localPos0 = {rest}
                point3f physics:localPos1 = (0, 0, 0)
                float state:linear:physics:position = 0
                bool physics:collisionEnabled = 0
            }}
        }}
        over Xform "{door.handle_prim_name}" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysxRigidBodyAPI"]
        )
        {{
            bool physics:rigidBodyEnabled = 1
            bool physxRigidBody:disableGravity = true
            uniform token[] xformOpOrder = ["!resetXformStack!", "xformOp:translate", "xformOp:rotateXYZ", "xformOp:scale"]
            def PhysicsFixedJoint "FixedJoint"
            {{
                rel physics:body0 = <{BALANCE_SOURCE}/{door.prim_name}>
                rel physics:body1 = <{BALANCE_SOURCE}/{door.handle_prim_name}>
                point3f physics:localPos0 = {grasp}
                point3f physics:localPos1 = (0, 0, 0)
                bool physics:collisionEnabled = 0
            }}{handle_collision}
        }}'''


def _lichen_facade(source: Path) -> str:
    door_blocks = "\n".join(_door_block(door) for door in DOORS)
    child_order = ", ".join(
        ['"FixedJoint"', '"_materials"']
        + [f'"{name}"' for door in DOORS for name in (door.prim_name, door.handle_prim_name)]
    )
    return f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
    timeCodesPerSecond = 24
    framesPerSecond = 24
)

def Xform "World"
{{
    def Xform "AnalyticalBalanceLichen" (
        prepend apiSchemas = ["PhysicsArticulationRootAPI"]
    )
    {{
        def Xform "Source" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI"]
            prepend references = @{source.as_posix()}@</root>
        )
        {{
            bool physics:rigidBodyEnabled = 1
            reorder nameChildren = [{child_order}]
            def PhysicsFixedJoint "FixedJoint"
            {{
                rel physics:body0 = <{BALANCE_ENTRY}>
                rel physics:body1 = <{BALANCE_SOURCE}>
                bool physics:collisionEnabled = 0
            }}
            over Xform "White_Main_Housing"
            {{
{_collision_over("Cube_001", "                ")}
            }}
            over Xform "Black_Lower_Platform"
            {{
{_collision_over("Cube", "                ")}
            }}
{door_blocks}
        }}
    }}
}}
'''


def _lichen_physics(facade: Path) -> dict[str, Any]:
    body_rules = [_body_rule("Source", 4.2, (0.178, 0.283, 0.261))]
    for door in DOORS:
        body_rules.append(_body_rule(f"Source/{door.prim_name}", 0.12, door.extent_xyz))
        body_rules.append(
            _body_rule(f"Source/{door.handle_prim_name}", 0.02, door.handle_extent_xyz)
        )
    return {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": "scientific_workbench.analytical_balance_lichen.provisional.r1",
        "revision": "r1",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": (
                "Source-bound geometry estimates replace missing mass/inertia. "
                "They are not measured instrument parameters."
            ),
            "center_of_mass_convention": "body_local_usd",
            "inertia_convention": "canonical SI kg*m^2",
            "replacement_contract": "Replace the complete source-bound body bundle in a new profile revision.",
        },
        "scope_rules": [{
            "scope_path": BALANCE_ENTRY,
            "body_rules": body_rules,
        }],
    }


def _lichen_device_profile(facade: Path) -> dict[str, Any]:
    semantics = {}
    for door in DOORS:
        semantics[door.semantic] = {
            "joint_prim": f"{BALANCE_SOURCE}/{door.prim_name}/PrismaticJoint",
            "part_prim": f"{BALANCE_SOURCE}/{door.prim_name}",
            "dof_index": door.dof_index,
            "runtime_reset_value": 0.0,
            "reset_state": "closed",
            "states": {
                "closed": [0.0, 0.002],
                "open": [0.100, min(door.upper_limit_m, 0.110)],
            },
        }
    named_frames = {
        "support": {
            "parent_prim": BALANCE_ENTRY,
            "translation_parent_local_m": [0.0, 0.0, 0.0],
            "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            "authoritative": True,
        }
    }
    for door in DOORS:
        named_frames[f"{door.semantic}_grasp"] = {
            "parent_prim": f"{BALANCE_SOURCE}/{door.prim_name}",
            "translation_parent_local_m": door.grasp_parent_local_m,
            "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            "authoritative": True,
        }
    resets = [
        {"dof_index": door.dof_index, "position": 0.0}
        for door in DOORS
    ]
    return {
        "schema_version": "aan.articulated_device_profile.v1",
        "profile_id": "scientific_workbench.analytical_balance_lichen.r1",
        "revision": "r1",
        "source_sha256": _sha(facade),
        "asset_entry_prim": BALANCE_ENTRY,
        "articulation_root_prim": BALANCE_ENTRY,
        "runtime_units": {"revolute": "radian", "prismatic": "meter"},
        "semantic_joints": semantics,
        "named_frames": named_frames,
        "required_runtime_task_gates": [
            "front_door_state_cycle",
            "left_door_state_cycle",
            "right_door_state_cycle",
            "top_door_state_cycle",
            "handle_follow_front_door",
            "front_door_contact_cycle",
            "benchtop_stability",
        ],
        "mounting": {
            "schema_version": "aan.articulated_mounting.v1",
            "motion_mode": "fixed_base",
            "asset_entry_prim": BALANCE_ENTRY,
            "coordinate_semantics": {
                "stage_up_axis": "Z",
                "linear_units": "meter",
                "quaternion_order": "wxyz",
                "support_frame": "runtime_articulation_root_pose_local",
                "mount_pose": "support_plane_to_runtime_articulation_root_pose_world_axes_at_yaw_zero",
                "qualified_extents": "world_axis_aligned_at_mount_pose_after_joint_reset",
            },
            "support_frame_root_local": {
                "translation_m": [0.0, 0.0, 0.0],
                "rotation_wxyz": [1.0, 0.0, 0.0, 0.0],
            },
            "support_plane_to_root_mount_pose": {
                "translation_m": [0.0, 0.0, 0.0],
                "rotation_wxyz": [1.0, 0.0, 0.0, 0.0],
            },
            "initial_joint_reset_positions": resets,
            "qualified_reset_geometry": {
                "warmup_frames": 50,
                "warmup_extent_world_aabb_m": [
                    0.17827999591827393,
                    0.28356999158859253,
                    0.27254000771790743,
                ],
                "settle_frames": 240,
                "final_extent_world_aabb_m": [
                    0.17827999591827393,
                    0.28356999158859253,
                    0.27254000771790743,
                ],
            },
            "verification_required": "benchtop_stability",
        },
    }


def build_lichen_balance_r1_assets(*, source: Path, out: Path) -> dict[str, Path]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"LICHEN analytical-balance source USD is required: {source}")
    out = out.resolve()
    facade = _write(out / "analytical_balance_lichen/facade.usda", _lichen_facade(source))
    physics = _json(
        out / "analytical_balance_lichen/physics_profile.json",
        _lichen_physics(facade),
    )
    device_profile = _json(
        out / "analytical_balance_lichen/device_profile.json",
        _lichen_device_profile(facade),
    )
    task_semantics = _json(
        out / "analytical_balance_lichen/task_semantics.json",
        {
            "schema_version": "aan.articulated_task_semantics.v1",
            "asset_entry_prim": BALANCE_ENTRY,
            "task_operated_semantics": [door.semantic for door in DOORS],
            "task_locked_semantics": [],
            "claim_boundary": (
                "Door state travel and front-handle block contact only; tare, "
                "weighing readout, button press, and robot-policy success "
                "remain separate evidence."
            ),
        },
    )
    provenance = _json(
        out / "analytical_balance_lichen/provenance.json",
        {
            "schema_version": "aan.analytical_balance_lichen_source_bound_build.v1",
            "source_usd": str(source),
            "source_sha256": _sha(source),
            "source_modified": False,
            "facade_sha256": _sha(facade),
            "source_stage_metadata": {"up_axis": "Z", "meters_per_unit": 1.0},
            "geometry_interpretation": {
                "basis": "LICHEN procedural USDA is already Z-up metres with bottom at Z=0",
                "effective_meters_per_unit": 1.0,
                "source_to_consumer_rotation": "identity",
                "source_to_consumer_translation_m": [0.0, 0.0, 0.0],
                "entry_prim_identity": True,
            },
            "source_repairs": [
                "authored PhysicsArticulationRootAPI on the public identity entry",
                "authored four prismatic door joints from the URDF travel limits",
                "authored joint localPos0 from source rest poses so PhysX keeps door origins",
                "world-fixed the Source base to the public entry prim for the benchtop contract",
                "welded sibling door handles to moving door links with PhysicsFixedJoint",
                "left buttons as visual-static meshes with no press joints",
                "kept housing/platform colliders, enabled front-handle convex hull, and omitted remaining door/handle collision",
                "source-bound provisional mass, COM, and inertia profile",
            ],
            "claim_boundary": (
                "Facade/profile construction only; Isaac 4.1 runtime qualification "
                "and task rollout are independent."
            ),
        },
    )
    return {
        "facade": facade,
        "physics_profile": physics,
        "device_profile": device_profile,
        "task_semantics": task_semantics,
        "provenance": provenance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build_lichen_balance_r1_assets(source=args.source, out=args.out)
    print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
