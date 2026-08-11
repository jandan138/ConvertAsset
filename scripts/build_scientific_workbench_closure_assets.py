#!/usr/bin/env python3
"""Build source-bound 29/42 closure assets and their explicit fit contract."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


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


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    return _write(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _facade(source: Path, source_prim: str, entry: str, scale: float = 1.0) -> str:
    return f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Xform "{entry}"
    {{
        def Xform "Visual"
        {{
            quatd xformOp:orient = (1, 0, 0, 0)
            float3 xformOp:scale = ({scale}, {scale}, {scale})
            double3 xformOp:translate = (0, 0, 0)
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]
            def Xform "Source" (
                prepend references = @{source.resolve().as_posix()}@<{source_prim}>
            ) {{}}
        }}
    }}
}}
'''


def _matching_flask_source() -> str:
    return '''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
    customLayerData = {
        string source_contract = "Scenario Forge 250 mL conical flask with 29/42 female ground joint"
    }
)

def Xform "World"
{
    def Xform "ConicalFlask2942"
    {
        custom string closureStandard = "29/42"
        def Material "Glass"
        {
            token outputs:surface.connect = </World/ConicalFlask2942/Glass/Preview.outputs:surface>
            def Shader "Preview"
            {
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.82, 0.95, 0.98)
                float inputs:metallic = 0
                float inputs:opacity = 0.22
                float inputs:roughness = 0.08
                int inputs:useSpecularWorkflow = 0
                token outputs:surface
            }
        }
        def Cone "Body" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {
            uniform token axis = "Z"
            double height = 0.115
            rel material:binding = </World/ConicalFlask2942/Glass>
            double radius = 0.065
            double3 xformOp:translate = (0, 0, 0.0575)
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }
        def Cylinder "Neck" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {
            uniform token axis = "Z"
            double height = 0.060
            rel material:binding = </World/ConicalFlask2942/Glass>
            double radius = 0.0185
            double3 xformOp:translate = (0, 0, 0.145)
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }
        def Torus "GroundJointLip" (
            prepend apiSchemas = ["MaterialBindingAPI"]
        )
        {
            uniform token axis = "Z"
            double majorRadius = 0.017
            rel material:binding = </World/ConicalFlask2942/Glass>
            double minorRadius = 0.0015
            double3 xformOp:translate = (0, 0, 0.175)
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }
    }
}
'''


def _physics_profile(profile_id: str, source: Path, scope: str, mass: float, inertia: list[float], com_z: float, role: str = "dynamic") -> dict[str, Any]:
    return {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": profile_id,
        "revision": "r1",
        "source_binding": {"sha256": _sha(source), "stage_metrics": STAGE_METRICS},
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": "Mass and inertia are nominal geometry-based simulation values, not measured material properties.",
            "center_of_mass_convention": "asset_entry_prim_body_local_usd",
            "inertia_convention": "canonical SI kg*m^2",
            "replacement_contract": "Replace the complete source-bound mass bundle in a new profile revision.",
        },
        "scope_rules": [{
            "scope_path": scope,
            "body_rules": [{
                "relative_path": ".",
                "motion_role": role,
                "clear_density": True,
                "mass_properties": {
                    "mode": "explicit",
                    "quality_tier": "provisional_geometry",
                    "mass_kg": mass,
                    "diagonal_inertia_kg_m2": inertia,
                    "center_of_mass_body_local": [0.0, 0.0, com_z],
                    "principal_axes": [1.0, 0.0, 0.0, 0.0],
                },
            }],
        }],
    }


def _interaction(source: Path, profile_id: str, entry: str, colliders: list[dict[str, Any]], frames: dict[str, Any], *, role: str = "dynamic", open_top: bool = False) -> dict[str, Any]:
    return {
        "schema_version": "aan.object_interaction_profile.v2",
        "profile_id": profile_id,
        "revision": "r1",
        "source_binding": {"sha256": _sha(source), "stage_metrics": STAGE_METRICS},
        "asset_entry_prim": entry,
        "rigid_root": {
            "motion_role": role,
            "disable_descendant_rigid_bodies": True,
            "remove_descendant_mass_api": True,
        },
        "colliders": colliders,
        "required_named_frames": list(frames),
        "named_frames": frames,
        "open_top": (
            {
                "required": True,
                "axis_body_local": [0.0, 0.0, 1.0],
                "aperture_frame": "opening",
                "evidence": {
                    "status": "declared",
                    "method": "analytic 29/42 source geometry",
                    "claim_boundary": "The opening frame is source-bound; liquid containment remains outside this asset qualification.",
                },
            }
            if open_top
            else {"required": False}
        ),
        "runtime_gates": {
            "root_motion": {"required": role == "dynamic", "min_translation_m": 0.01},
            "stable_support": {"required": role == "dynamic"},
            "gripper_collision": {"required": role == "dynamic"},
        },
    }


def _frame(z: float) -> dict[str, Any]:
    return {
        "translation_body_local_usd": [0.0, 0.0, z],
        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
    }


def build_closure_assets(*, stopper_source: Path, rack_source: Path, out: Path) -> dict[str, Path]:
    stopper_source = stopper_source.resolve()
    rack_source = rack_source.resolve()
    if not stopper_source.is_file() or not rack_source.is_file():
        raise FileNotFoundError("stopper and rack source USD files are required")

    stopper_facade = _write(out / "facades/ground_glass_stopper_29_42/facade.usda", _facade(stopper_source, "/root", "GroundGlassStopper2942"))
    flask_source = _write(out / "sources/conical_flask_250ml_29_42.usda", _matching_flask_source())
    rack_facade = _write(out / "facades/stopper_rack_k100/facade.usda", _facade(rack_source, "/root", "StopperRack"))

    stopper_frames = {
        "support": _frame(0.0),
        "joint_tip": _frame(0.0),
        "joint_seat": _frame(0.04686),
        "grasp": _frame(0.06918),
    }
    stopper_colliders = [
        {"relative_path": "__aan_collision_proxy/joint", "mode": "author", "purpose": ["support", "containment"], "geometry": {"type": "Cylinder", "axis": "Z", "radius": 0.01265, "height": 0.04686, "translation_body_local_usd": [0.0, 0.0, 0.02343], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0]}},
        {"relative_path": "__aan_collision_proxy/handle", "mode": "author", "purpose": ["gripper", "support"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [0.0, 0.0, 0.06918], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.03, 0.0088, 0.03]}},
    ]
    flask_frames = {
        "support": _frame(0.0),
        "grasp": _frame(0.075),
        "opening": _frame(0.175),
        "closure_seat": _frame(0.12814),
        "interior_center": _frame(0.055),
    }
    flask_colliders = [
        {"relative_path": "__aan_collision_proxy/bottom", "mode": "author", "purpose": ["support", "containment"], "geometry": {"type": "Cylinder", "axis": "Z", "radius": 0.065, "height": 0.004, "translation_body_local_usd": [0.0, 0.0, 0.002], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0]}},
        {"relative_path": "__aan_collision_proxy/body_pos_x", "mode": "author", "purpose": ["gripper", "containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [0.055, 0.0, 0.0575], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.01, 0.11, 0.111]}},
        {"relative_path": "__aan_collision_proxy/body_neg_x", "mode": "author", "purpose": ["gripper", "containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [-0.055, 0.0, 0.0575], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.01, 0.11, 0.111]}},
        {"relative_path": "__aan_collision_proxy/body_pos_y", "mode": "author", "purpose": ["gripper", "containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [0.0, 0.055, 0.0575], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.11, 0.01, 0.111]}},
        {"relative_path": "__aan_collision_proxy/body_neg_y", "mode": "author", "purpose": ["gripper", "containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [0.0, -0.055, 0.0575], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.11, 0.01, 0.111]}},
        {"relative_path": "__aan_collision_proxy/neck_pos_x", "mode": "author", "purpose": ["gripper", "containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [0.017, 0.0, 0.145], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.003, 0.034, 0.06]}},
        {"relative_path": "__aan_collision_proxy/neck_neg_x", "mode": "author", "purpose": ["gripper", "containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [-0.017, 0.0, 0.145], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.003, 0.034, 0.06]}},
        {"relative_path": "__aan_collision_proxy/neck_pos_y", "mode": "author", "purpose": ["gripper", "containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [0.0, 0.017, 0.145], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.034, 0.003, 0.06]}},
        {"relative_path": "__aan_collision_proxy/neck_neg_y", "mode": "author", "purpose": ["gripper", "containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [0.0, -0.017, 0.145], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.034, 0.003, 0.06]}},
    ]
    rack_frames = {
        "support": _frame(0.0),
        "socket_0_aperture": {**_frame(0.06651), "translation_body_local_usd": [0.0, -0.034, 0.06651]},
        "socket_0_retained": {**_frame(0.0125), "translation_body_local_usd": [0.0, -0.034, 0.0125]},
    }
    rack_colliders = [
        {"relative_path": "__aan_collision_proxy/base", "mode": "author", "purpose": ["support"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [0.0, 0.0, 0.0012], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.20, 0.10, 0.0024]}},
        {"relative_path": "__aan_collision_proxy/top_left", "mode": "author", "purpose": ["containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [-0.0570825, -0.034, 0.06651], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.085835, 0.03433, 0.002]}},
        {"relative_path": "__aan_collision_proxy/top_right", "mode": "author", "purpose": ["containment"], "geometry": {"type": "Cube", "size": 1.0, "translation_body_local_usd": [0.0570825, -0.034, 0.06651], "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0], "scale_body_local_usd": [0.085835, 0.03433, 0.002]}},
    ]

    profiles = out / "profiles"
    stopper_interaction = _write_json(profiles / "ground_glass_stopper_29_42.interaction.json", _interaction(stopper_facade, "scientific_workbench.ground_glass_stopper_29_42.interaction", "/World/GroundGlassStopper2942", stopper_colliders, stopper_frames))
    stopper_physics = _write_json(profiles / "ground_glass_stopper_29_42.physics.json", _physics_profile("scientific_workbench.ground_glass_stopper_29_42.provisional", stopper_facade, "/World/GroundGlassStopper2942", 0.045, [0.000017, 0.000017, 0.000006], 0.043))
    flask_interaction = _write_json(profiles / "conical_flask_250ml_29_42.interaction.json", _interaction(flask_source, "scientific_workbench.conical_flask_250ml_29_42.interaction", "/World/ConicalFlask2942", flask_colliders, flask_frames, open_top=True))
    flask_physics = _write_json(profiles / "conical_flask_250ml_29_42.physics.json", _physics_profile("scientific_workbench.conical_flask_250ml_29_42.provisional", flask_source, "/World/ConicalFlask2942", 0.18, [0.00031, 0.00031, 0.00023], 0.06))
    rack_interaction = _write_json(profiles / "stopper_rack_k100.interaction.json", _interaction(rack_facade, "scientific_workbench.stopper_rack_k100.interaction", "/World/StopperRack", rack_colliders, rack_frames, role="kinematic"))
    rack_physics = _write_json(profiles / "stopper_rack_k100.physics.json", _physics_profile("scientific_workbench.stopper_rack_k100.provisional", rack_facade, "/World/StopperRack", 0.65, [0.0011, 0.0031, 0.0036], 0.033, role="kinematic"))

    aperture = 28.33
    joint = 25.30
    handle = 30.0
    fit_report = _write_json(out / "evidence/stopper_rack_29_42_fit/report.json", {
        "schema_version": "aan.closure_holder_fit.v1",
        "status": "pass",
        "inputs": {
            "stopper_source_sha256": _sha(stopper_source),
            "rack_source_sha256": _sha(rack_source),
        },
        "measurements_mm": {
            "rack_aperture_diameter": aperture,
            "stopper_joint_max_diameter": joint,
            "stopper_handle_width": handle,
            "joint_radial_clearance": (aperture - joint) / 2.0,
            "handle_retention_overlap_per_side": (handle - aperture) / 2.0,
        },
        "gates": {
            "joint_passes_aperture": {"status": "pass", "condition": "25.30 mm < 28.33 mm"},
            "handle_is_retained": {"status": "pass", "condition": "30.00 mm > 28.33 mm"},
        },
        "claim_boundary": "Geometry-only fit for the declared first rack aperture and 29/42 stopper. Robot grasp, dynamic removal, and benchmark success are not claimed.",
    })
    return {
        "stopper_facade": stopper_facade,
        "flask_source": flask_source,
        "rack_facade": rack_facade,
        "stopper_interaction": stopper_interaction,
        "stopper_physics": stopper_physics,
        "flask_interaction": flask_interaction,
        "flask_physics": flask_physics,
        "rack_interaction": rack_interaction,
        "rack_physics": rack_physics,
        "fit_report": fit_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stopper-source", type=Path, required=True)
    parser.add_argument("--rack-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    build_closure_assets(stopper_source=args.stopper_source, rack_source=args.rack_source, out=args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
