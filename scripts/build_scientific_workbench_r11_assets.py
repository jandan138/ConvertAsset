#!/usr/bin/env python3
"""Build source-bound Task 05 flat-flask and Task 09 oven admission inputs."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any


FLASK_ENTRY = "/World/FlatBottomFlask2942"
OVEN_ENTRY = "/World/AnalogGravityConvectionOven"
OVEN_SOURCE = f"{OVEN_ENTRY}/Source"
STAGE_METRICS = {
    "meters_per_unit": 1.0,
    "kilograms_per_unit": 1.0,
    "up_axis": "Z",
    "time_codes_per_second": 24.0,
    "frames_per_second": 24.0,
}


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


def _frame(z: float) -> dict[str, Any]:
    return {
        "translation_body_local_usd": [0.0, 0.0, z],
        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
    }


def _cube(
    name: str,
    xyz: list[float],
    scale: list[float],
    purpose: list[str],
) -> dict[str, Any]:
    return {
        "relative_path": f"__aan_collision_proxy/{name}",
        "mode": "author",
        "purpose": purpose,
        "geometry": {
            "type": "Cube",
            "size": 1.0,
            "translation_body_local_usd": xyz,
            "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
            "scale_body_local_usd": scale,
        },
    }


def _flat_flask_facade(source: Path) -> str:
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
    def Xform "FlatBottomFlask2942"
    {{
        def Xform "Visual"
        {{
            def Xform "Source" (
                prepend references = @{source.as_posix()}@</root>
            ) {{}}
        }}
    }}
}}
'''


def _flat_flask_interaction(facade: Path) -> dict[str, Any]:
    # The four body and four neck strips keep the mouth open.  This is a
    # reviewed compound proxy, not a hidden closure constraint.
    body_wall_center = 0.03691
    neck_wall_center = 0.01536
    colliders = [
        _cube("bottom", [0.0, 0.0, 0.002], [0.074, 0.074, 0.004], ["support", "containment"]),
        _cube("body_pos_x", [body_wall_center, 0.0, 0.0505], [0.005, 0.07382, 0.097], ["gripper", "containment"]),
        _cube("body_neg_x", [-body_wall_center, 0.0, 0.0505], [0.005, 0.07382, 0.097], ["gripper", "containment"]),
        _cube("body_pos_y", [0.0, body_wall_center, 0.0505], [0.07382, 0.005, 0.097], ["gripper", "containment"]),
        _cube("body_neg_y", [0.0, -body_wall_center, 0.0505], [0.07382, 0.005, 0.097], ["gripper", "containment"]),
        _cube("neck_pos_x", [neck_wall_center, 0.0, 0.122], [0.00361, 0.03072, 0.042], ["gripper", "containment"]),
        _cube("neck_neg_x", [-neck_wall_center, 0.0, 0.122], [0.00361, 0.03072, 0.042], ["gripper", "containment"]),
        _cube("neck_pos_y", [0.0, neck_wall_center, 0.122], [0.03072, 0.00361, 0.042], ["gripper", "containment"]),
        _cube("neck_neg_y", [0.0, -neck_wall_center, 0.122], [0.03072, 0.00361, 0.042], ["gripper", "containment"]),
    ]
    return {
        "schema_version": "aan.object_interaction_profile.v2",
        "profile_id": "scientific_workbench.flat_bottom_flask_250ml_29_42.r11",
        "revision": "r11",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "asset_entry_prim": FLASK_ENTRY,
        "rigid_root": {
            "motion_role": "dynamic",
            "disable_descendant_rigid_bodies": True,
            "remove_descendant_mass_api": True,
        },
        "colliders": colliders,
        "required_named_frames": [
            "support",
            "grasp",
            "opening",
            "closure_seat",
            "interior_center",
        ],
        "named_frames": {
            "support": _frame(0.0),
            "grasp": _frame(0.052),
            "opening": _frame(0.15058),
            "closure_seat": _frame(0.10372),
            "interior_center": _frame(0.0505),
        },
        "open_top": {
            "required": True,
            "axis_body_local": [0.0, 0.0, 1.0],
            "aperture_frame": "opening",
            "evidence": {
                "status": "declared",
                "method": "source validation plus reviewed 29/42 compound proxy",
                "claim_boundary": (
                    "The mouth remains open for the matched stopper; liquid containment "
                    "and robot-policy success are outside this qualification."
                ),
            },
        },
        "runtime_gates": {
            "root_motion": {"required": True, "min_translation_m": 0.01},
            "stable_support": {"required": True},
            "gripper_collision": {"required": True},
        },
    }


def _flat_flask_physics(facade: Path) -> dict[str, Any]:
    return {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": "scientific_workbench.flat_bottom_flask_250ml_29_42.provisional.r11",
        "revision": "r11",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": "Nominal glass-vessel mass and geometry-derived inertia; not measured material parameters.",
            "center_of_mass_convention": "asset_entry_prim_body_local_usd",
            "inertia_convention": "canonical SI kg*m^2",
            "replacement_contract": "Replace the complete source-bound mass bundle in a new profile revision.",
        },
        "scope_rules": [{
            "scope_path": FLASK_ENTRY,
            "body_rules": [{
                "relative_path": ".",
                "motion_role": "dynamic",
                "clear_density": True,
                "mass_properties": {
                    "mode": "explicit",
                    "quality_tier": "provisional_geometry",
                    "mass_kg": 0.22,
                    "diagonal_inertia_kg_m2": [0.00038, 0.00038, 0.00022],
                    "center_of_mass_body_local": [0.0, 0.0, 0.057],
                    "principal_axes": [1.0, 0.0, 0.0, 0.0],
                },
            }],
        }],
    }


LOCKED_OVEN_JOINTS = {
    1: "chimney_damper",
    2: "door_latch",
    3: "lower_dial",
    6: "shelf_lower",
    7: "sample_shelf",
    8: "shelf_upper",
    9: "shelf_top",
    10: "temperature_needle",
}
ACTIVE_OVEN_JOINTS = {
    4: "main_door",
    5: "power_rocker",
    11: "temperature_dial",
}
OVEN_DOF_GROUP_ORDER = (1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 2)


def _oven_facade(source: Path) -> str:
    joint_overrides = []
    for group in range(1, 12):
        joint_type = "PhysicsPrismaticJoint" if group in {6, 7, 8, 9} else "PhysicsRevoluteJoint"
        joint_name = "PrismaticJoint" if group in {6, 7, 8, 9} else "RevoluteJoint"
        state_name = "linear" if group in {6, 7, 8, 9} else "angular"
        limits = (
            "\n                float physics:lowerLimit = -0.000001\n"
            "                float physics:upperLimit = 0.000001"
            if group in LOCKED_OVEN_JOINTS
            else ""
        )
        reset_value = -10.313240051269531 if group == 5 else 0
        body_attributes = (
            "\n            bool physxRigidBody:disableGravity = true"
            if group == 11
            else ""
        )
        body_metadata = (
            ' (\n            prepend apiSchemas = ["PhysxRigidBodyAPI"]\n        )'
            if group == 11
            else ""
        )
        joint_overrides.append(
            f'''        over Xform "group_{group}"{body_metadata}
        {{{body_attributes}
            over {joint_type} "{joint_name}"
            {{
                float state:{state_name}:physics:position = {reset_value}{limits}
            }}
        }}'''
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
    def Xform "AnalogGravityConvectionOven" (
        prepend apiSchemas = ["PhysicsArticulationRootAPI"]
    )
    {{
        def Xform "Source" (
            delete apiSchemas = ["PhysicsArticulationRootAPI"]
            prepend references = @{source.as_posix()}@</root>
        )
        {{
            quatd xformOp:orient = (0.7071067811865476, 0.7071067811865475, 0, 0)
            double3 xformOp:translate = (0, 0, 0.4666)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient"]
            reorder nameChildren = ["_materials", "group_0", "group_1", "group_3", "group_4", "group_5", "group_6", "group_7", "group_8", "group_9", "group_10", "group_11", "group_2"]
        over Xform "group_0"
        {{
            over PhysicsFixedJoint "FixedJoint"
            {{
                rel physics:body0 = <{OVEN_ENTRY}>
            }}
        }}
{chr(10).join(joint_overrides)}
        }}
    }}
}}
'''


def _oven_body_rule(index: int) -> dict[str, Any]:
    mass = {0: 125.0, 4: 18.0, 6: 2.5, 7: 2.5, 8: 2.5, 9: 2.5}.get(index, 0.35)
    extent = {0: (0.875, 0.9332, 0.693), 4: (0.65, 0.59, 0.085)}.get(
        index, (0.10, 0.10, 0.10)
    )
    x, y, z = extent
    return {
        "relative_path": f"Source/group_{index}",
        "motion_role": "dynamic",
        "clear_density": True,
        "mass_properties": {
            "mode": "explicit",
            "quality_tier": "provisional_geometry",
            "mass_kg": mass,
            "diagonal_inertia_kg_m2": [
                mass * (y * y + z * z) / 12.0,
                mass * (x * x + z * z) / 12.0,
                mass * (x * x + y * y) / 12.0,
            ],
            "center_of_mass_body_local": [0.0, 0.0, 0.0],
            "principal_axes": [1.0, 0.0, 0.0, 0.0],
        },
    }


def _oven_physics(facade: Path) -> dict[str, Any]:
    return {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": "scientific_workbench.analog_gravity_convection_oven.provisional.r11",
        "revision": "r11",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": (
                "Source-bound geometry estimates replace non-finite COM and zero inertia. "
                "They are not measured appliance parameters."
            ),
            "center_of_mass_convention": "body_local_usd",
            "inertia_convention": "canonical SI kg*m^2",
            "replacement_contract": "Replace the complete source-bound body bundle in a new profile revision.",
        },
        "scope_rules": [{
            "scope_path": OVEN_ENTRY,
            "body_rules": [_oven_body_rule(index) for index in range(12)],
        }],
    }


def _semantic(
    group: int,
    name: str,
    dof_index: int,
    states: dict[str, list[float]],
    reset_state: str,
    runtime_reset_value: float = 0.0,
) -> tuple[str, dict[str, Any]]:
    joint_name = "PrismaticJoint" if group in {6, 7, 8, 9} else "RevoluteJoint"
    return name, {
        "joint_prim": f"{OVEN_SOURCE}/group_{group}/{joint_name}",
        "part_prim": f"{OVEN_SOURCE}/group_{group}",
        "dof_index": dof_index,
        "runtime_reset_value": runtime_reset_value,
        "reset_state": reset_state,
        "states": states,
    }


def _oven_semantics() -> dict[str, dict[str, Any]]:
    # The facade's explicit nameChildren order matches the measured PhysX
    # articulation order.  This makes the static manifest and runtime ABI agree.
    items: list[tuple[str, dict[str, Any]]] = []
    for dof_index, group in enumerate(OVEN_DOF_GROUP_ORDER):
        if group == 4:
            items.append(_semantic(group, "main_door", dof_index, {
                "closed": [0.0, math.radians(3.0)],
                "open": [math.radians(75.0), math.radians(111.72676849365234)],
            }, "closed"))
        elif group == 5:
            off = math.radians(-10.313240051269531)
            items.append(_semantic(group, "power_rocker", dof_index, {
                "off": [off, math.radians(-8.0)],
                "on": [math.radians(7.0), math.radians(10.313240051269531)],
            }, "off", runtime_reset_value=off))
        elif group == 11:
            items.append(_semantic(group, "temperature_dial", dof_index, {
                "ambient": [math.radians(-2.0), math.radians(2.0)],
                "target_50_70": [math.radians(50.0), math.radians(70.0)],
            }, "ambient"))
        else:
            items.append(_semantic(group, LOCKED_OVEN_JOINTS[group], dof_index, {
                "locked": [0.0, 0.0],
            }, "locked"))
    return dict(items)


def _oven_device_profile(facade: Path) -> dict[str, Any]:
    qx90 = [0.7071067811865476, 0.7071067811865475, 0.0, 0.0]
    semantics = _oven_semantics()
    resets = sorted(
        (
            {
                "dof_index": value["dof_index"],
                "position": value["runtime_reset_value"],
            }
            for value in semantics.values()
        ),
        key=lambda item: item["dof_index"],
    )
    return {
        "schema_version": "aan.articulated_device_profile.v1",
        "profile_id": "scientific_workbench.analog_gravity_convection_oven.r11",
        "revision": "r11",
        "source_sha256": _sha(facade),
        "asset_entry_prim": OVEN_ENTRY,
        "articulation_root_prim": OVEN_ENTRY,
        "runtime_units": {"revolute": "radian", "prismatic": "meter"},
        "semantic_joints": semantics,
        "named_frames": {
            "support": {
                "parent_prim": OVEN_ENTRY,
                "translation_parent_local_m": [0.0, 0.0, 0.0],
                "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "authoritative": True,
            },
            "door_grasp": {
                "parent_prim": f"{OVEN_SOURCE}/group_4",
                "translation_parent_local_m": [0.077, -0.0416, 0.327],
                "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "authoritative": True,
            },
            "power_rocker_press": {
                "parent_prim": f"{OVEN_SOURCE}/group_5",
                "translation_parent_local_m": [-0.3375, -0.3616, 0.288],
                "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "authoritative": True,
            },
            "temperature_dial_grasp": {
                "parent_prim": f"{OVEN_SOURCE}/group_11",
                "translation_parent_local_m": [-0.3375, 0.0184, 0.31045],
                "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "authoritative": True,
            },
            "sample_shelf_target": {
                "parent_prim": f"{OVEN_SOURCE}/group_7",
                "translation_parent_local_m": [0.0525, -0.073, -0.0425],
                "rotation_parent_local_wxyz": [1.0, 0.0, 0.0, 0.0],
                "authoritative": True,
            },
        },
        "required_runtime_task_gates": [
            "main_door_state_cycle",
            "temperature_dial_state_cycle",
            "power_rocker_state_cycle",
            "locked_joint_stability",
            "sample_shelf_support",
            "benchtop_stability",
        ],
        "mounting": {
            "schema_version": "aan.articulated_mounting.v1",
            "motion_mode": "fixed_base",
            "asset_entry_prim": OVEN_ENTRY,
            "coordinate_semantics": {
                "stage_up_axis": "Z",
                "linear_units": "meter",
                "quaternion_order": "wxyz",
                "support_frame": "runtime_articulation_root_pose_local",
                "mount_pose": "support_plane_to_runtime_articulation_root_pose_world_axes_at_yaw_zero",
                "qualified_extents": "world_axis_aligned_at_mount_pose_after_joint_reset",
            },
            "support_frame_root_local": {
                "translation_m": [0.0, -0.4666, 0.0],
                "rotation_wxyz": [1.0, 0.0, 0.0, 0.0],
            },
            "support_plane_to_root_mount_pose": {
                "translation_m": [0.0, 0.0, 0.4666],
                "rotation_wxyz": qx90,
            },
            "initial_joint_reset_positions": resets,
            "qualified_reset_geometry": {
                "warmup_frames": 50,
                "warmup_extent_world_aabb_m": [0.875, 0.77, 0.9332],
                "settle_frames": 240,
                "final_extent_world_aabb_m": [0.875, 0.77, 0.9332],
            },
            "verification_required": "benchtop_stability",
        },
    }


def build_r11_assets(
    *,
    flat_flask_source: Path,
    oven_source: Path,
    out: Path,
) -> dict[str, Path]:
    flat_flask_source = flat_flask_source.resolve()
    oven_source = oven_source.resolve()
    if not flat_flask_source.is_file() or not oven_source.is_file():
        raise FileNotFoundError("flat-flask and oven source USD files are required")
    out = out.resolve()

    flat_flask_facade = _write(
        out / "flat_bottom_flask_250ml_29_42/facade.usda",
        _flat_flask_facade(flat_flask_source),
    )
    flat_flask_interaction = _json(
        out / "flat_bottom_flask_250ml_29_42/interaction_profile.json",
        _flat_flask_interaction(flat_flask_facade),
    )
    flat_flask_physics = _json(
        out / "flat_bottom_flask_250ml_29_42/physics_profile.json",
        _flat_flask_physics(flat_flask_facade),
    )
    joint_inner = 27.11
    stopper_joint = 25.30
    stopper_handle = 30.00
    flat_flask_fit = _json(
        out / "flat_bottom_flask_250ml_29_42/closure_fit.json",
        {
            "schema_version": "aan.closure_vessel_fit.v1",
            "status": "pass",
            "inputs": {
                "flat_flask_source_sha256": _sha(flat_flask_source),
                "stopper_contract": "29/42",
            },
            "measurements_mm": {
                "flask_neck_inner_diameter": joint_inner,
                "stopper_joint_max_diameter": stopper_joint,
                "stopper_handle_width": stopper_handle,
                "joint_radial_clearance": round((joint_inner - stopper_joint) / 2.0, 3),
                "handle_retention_overlap_per_side": round((stopper_handle - joint_inner) / 2.0, 3),
            },
            "gates": {
                "stopper_joint_enters_neck": {"status": "pass", "condition": "25.30 mm < 27.11 mm"},
                "stopper_handle_retained": {"status": "pass", "condition": "30.00 mm > 27.11 mm"},
            },
            "initial_seat": {
                "stopper_root_z_m": 0.10372,
                "basis": "flask opening 0.15058 m minus stopper joint length 0.04686 m",
                "hidden_constraint": False,
            },
            "claim_boundary": "Geometry fit and initial loose seat only; robot removal and benchmark success are not claimed.",
        },
    )

    oven_facade = _write(
        out / "analog_gravity_convection_oven/facade.usda",
        _oven_facade(oven_source),
    )
    oven_physics = _json(
        out / "analog_gravity_convection_oven/physics_profile.json",
        _oven_physics(oven_facade),
    )
    oven_device_profile = _json(
        out / "analog_gravity_convection_oven/device_profile.json",
        _oven_device_profile(oven_facade),
    )
    oven_task_semantics = _json(
        out / "analog_gravity_convection_oven/task_semantics.json",
        {
            "schema_version": "aan.articulated_task_semantics.v1",
            "asset_entry_prim": OVEN_ENTRY,
            "task_operated_semantics": ["main_door", "temperature_dial", "power_rocker"],
            "task_locked_semantics": list(LOCKED_OVEN_JOINTS.values()),
            "sample_support_frame": "sample_shelf_target",
            "claim_boundary": "Task-facing semantic selection only; runtime gates and robot-policy success remain separate evidence.",
        },
    )
    oven_provenance = _json(
        out / "analog_gravity_convection_oven/provenance.json",
        {
            "schema_version": "aan.analog_oven_source_bound_build.v1",
            "source_usd": str(oven_source),
            "source_sha256": _sha(oven_source),
            "source_modified": False,
            "facade_sha256": _sha(oven_facade),
            "source_stage_metadata": {"up_axis": "Y", "meters_per_unit": 0.01},
            "geometry_interpretation": {
                "basis": "reviewed composed geometry AABB and 0.875 m appliance design width",
                "effective_meters_per_unit": 1.0,
                "source_to_consumer_rotation": "+90 degrees about X under the identity entry",
                "source_to_consumer_translation_m": [0.0, 0.0, 0.4666],
                "entry_prim_identity": True,
            },
            "source_repairs": [
                "locked non-task joints by stronger facade limits",
                "source-bound provisional mass, COM, and inertia profile",
            ],
            "claim_boundary": "Facade/profile construction only; Isaac 4.1 runtime qualification and task rollout are independent.",
        },
    )
    return {
        "flat_flask_facade": flat_flask_facade,
        "flat_flask_interaction": flat_flask_interaction,
        "flat_flask_physics": flat_flask_physics,
        "flat_flask_fit": flat_flask_fit,
        "oven_facade": oven_facade,
        "oven_physics": oven_physics,
        "oven_device_profile": oven_device_profile,
        "oven_task_semantics": oven_task_semantics,
        "oven_provenance": oven_provenance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flat-flask-source", type=Path, required=True)
    parser.add_argument("--oven-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build_r11_assets(
        flat_flask_source=args.flat_flask_source,
        oven_source=args.oven_source,
        out=args.out,
    )
    print(json.dumps({key: str(value) for key, value in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
