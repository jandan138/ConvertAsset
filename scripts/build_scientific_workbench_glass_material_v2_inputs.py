#!/usr/bin/env python3
"""Build source-bound admission inputs for the two manual glassware vessels."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tarfile
from typing import Any


ARCHIVE_SHA256 = "731eb7eb539377b7c1fec015065c256d932e13b548d39f8697ec9b1444074afd"
STAGE_METRICS = {
    "meters_per_unit": 1.0,
    "kilograms_per_unit": 1.0,
    "up_axis": "Z",
    "time_codes_per_second": 24.0,
    "frames_per_second": 24.0,
}
VESSELS = {
    "reagent_bottle_90x55": {
        "archive_member": "manual_glassware_v1/source_usd/reagent_bottle_90x55_source.usdc",
        "source_sha256": "19f0885f33a76f689aa29418cb0d29e03be5e517a46118d4a857b65af3b268ad",
        "source_root": "/ROOT_ReagentBottle",
        "entry_name": "ReagentBottle90x55",
        "source_prefix": "ReagentBottle",
        "visual_xform": "VIS_ReagentBottle_ClearGlass",
        "visual_mesh": "VIS_ReagentBottle_ClearGlass_Mesh",
        "bottom_mesh": "Cylinder",
        "cube_start": 0,
        "mass_kg": 0.28,
        "center_of_mass_z_m": 0.09,
        "diagonal_inertia_kg_m2": [0.00090, 0.00090, 0.00028],
        "grasp_z_m": 0.09,
        "opening_z_m": 0.18,
        "interior_z_m": 0.08,
        "ground_faces": 2080,
        "decal_materials": {},
    },
    "erlenmeyer_flask_250ml_90x35": {
        "archive_member": "manual_glassware_v1/source_usd/erlenmeyer_flask_250ml_90x35_source.usdc",
        "source_sha256": "32eaa48a9b17808c50411030aa26d8209b35ca5567911c30e6a8b8fd8bcc136c",
        "source_root": "/ROOT_ErlenmeyerFlask",
        "entry_name": "ErlenmeyerFlask250ml90x35",
        "source_prefix": "ErlenmeyerFlask",
        "visual_xform": "VIS_ErlenmeyerFlask_ClearGlass",
        "visual_mesh": "VIS_ErlenmeyerFlask_ClearGlass_Mesh",
        "bottom_mesh": "Cylinder_002",
        "cube_start": 96,
        "mass_kg": 0.15,
        "center_of_mass_z_m": 0.06,
        "diagonal_inertia_kg_m2": [0.00036, 0.00036, 0.00015],
        "grasp_z_m": 0.075,
        "opening_z_m": 0.15,
        "interior_z_m": 0.055,
        "ground_faces": 1600,
        "decal_materials": {
            "DECAL_Erlenmeyer_29_42/DECAL_Erlenmeyer_29_42_Curve": "MAT_Marking_Red",
            "DECAL_Erlenmeyer_250mL/DECAL_Erlenmeyer_250mL_Curve": "MAT_Marking_White",
        },
    },
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    return _write(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False),
    )


def _frame(z: float) -> dict[str, Any]:
    return {
        "translation_body_local_usd": [0.0, 0.0, z],
        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
    }


def _mesh_name(index: int) -> str:
    return "Cube" if index == 0 else f"Cube_{index:03d}"


def _collision_paths(spec: dict[str, Any]) -> list[str]:
    prefix = str(spec["source_prefix"])
    paths = [f"Visual/Source/COL_{prefix}_Bottom/{spec['bottom_mesh']}"]
    cube_index = int(spec["cube_start"])
    for ring in range(4):
        for segment in range(24):
            paths.append(
                f"Visual/Source/COL_{prefix}_Wall{ring:02d}_{segment:02d}/"
                f"{_mesh_name(cube_index)}"
            )
            cube_index += 1
    return paths


def _facade_text(source: Path, spec: dict[str, Any]) -> str:
    collider_overrides = []
    for relative_path in _collision_paths(spec):
        _, _, parent_name, mesh_name = relative_path.split("/")
        collider_overrides.append(
            f'''                over "{parent_name}"
                {{
                    token visibility = "invisible"
                    over "{mesh_name}" (
                        prepend apiSchemas = ["PhysicsCollisionAPI", "PhysicsMeshCollisionAPI"]
                    )
                    {{
                        bool physics:collisionEnabled = true
                        uniform token physics:approximation = "convexHull"
                    }}
                }}'''
        )
    hidden_overrides = "\n".join(collider_overrides)
    looks_path = f"/World/{spec['entry_name']}/Visual/SourceLooks"
    material_overrides = f'''                over "{spec['visual_xform']}"
                {{
                    over "{spec['visual_mesh']}"
                    {{
                        rel material:binding = <{looks_path}/MAT_Borosilicate_Clear>
                        over "MAT_Borosilicate_Clear"
                        {{
                            rel material:binding = <{looks_path}/MAT_Borosilicate_Clear>
                        }}
                        over "MAT_GroundGlass_Frosted"
                        {{
                            rel material:binding = <{looks_path}/MAT_GroundGlass_Frosted>
                        }}
                    }}
                }}'''
    decal_overrides = []
    for relative_path, material_name in spec["decal_materials"].items():
        xform_name, mesh_name = relative_path.split("/")
        decal_overrides.append(
            f'''                over "{xform_name}"
                {{
                    over "{mesh_name}"
                    {{
                        rel material:binding = <{looks_path}/{material_name}>
                    }}
                }}'''
        )
    decal_text = "\n".join(decal_overrides)
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
    def Xform "{spec['entry_name']}"
    {{
        def Xform "Visual"
        {{
            def Xform "Source" (
                prepend references = @{source.as_posix()}@<{spec['source_root']}>
            )
            {{
{hidden_overrides}
{material_overrides}
{decal_text}
            }}

            def Scope "SourceLooks" (
                prepend references = @{source.as_posix()}@</_materials>
            ) {{}}
        }}
    }}
}}
'''


def _interaction_profile(facade: Path, spec: dict[str, Any]) -> dict[str, Any]:
    entry = f"/World/{spec['entry_name']}"
    colliders = [
        {
            "relative_path": path,
            "mode": "preserve",
            "purpose": ["gripper", "support", "containment"],
            "approximation": "convexHull",
        }
        for path in _collision_paths(spec)
    ]
    return {
        "schema_version": "aan.object_interaction_profile.v2",
        "profile_id": f"scientific_workbench.{spec['entry_name']}.glass_v2",
        "revision": "glass_v2",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "asset_entry_prim": entry,
        "rigid_root": {
            "motion_role": "dynamic",
            "disable_descendant_rigid_bodies": True,
            "remove_descendant_mass_api": True,
        },
        "colliders": colliders,
        "required_named_frames": ["support", "grasp", "opening", "interior_center"],
        "named_frames": {
            "support": _frame(0.0),
            "grasp": _frame(float(spec["grasp_z_m"])),
            "opening": _frame(float(spec["opening_z_m"])),
            "interior_center": _frame(float(spec["interior_z_m"])),
        },
        "open_top": {
            "required": True,
            "axis_body_local": [0.0, 0.0, 1.0],
            "aperture_frame": "opening",
            "evidence": {
                "status": "declared",
                "method": "producer-authored 24-segment compound open-mouth proxy",
                "claim_boundary": (
                    "The source proxy preserves the vessel opening. Liquid containment, "
                    "plug interaction, and robot-policy success remain outside this admission."
                ),
            },
        },
        "runtime_gates": {
            "root_motion": {"required": True, "min_translation_m": 0.01},
            "stable_support": {"required": True},
            "gripper_collision": {"required": True},
        },
    }


def _physics_profile(facade: Path, spec: dict[str, Any]) -> dict[str, Any]:
    entry = f"/World/{spec['entry_name']}"
    return {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": f"scientific_workbench.{spec['entry_name']}.provisional.glass_v2",
        "revision": "glass_v2",
        "source_binding": {"sha256": _sha(facade), "stage_metrics": STAGE_METRICS},
        "evidence": {
            "parameter_status": "provisional_geometry",
            "claim_boundary": (
                "Mass comes from manual_glassware_v1; center of mass and inertia are "
                "geometry estimates, not measured borosilicate parameters."
            ),
            "center_of_mass_convention": "asset_entry_prim_body_local_usd",
            "inertia_convention": "canonical SI kg*m^2",
            "replacement_contract": "Replace the complete source-bound bundle in a new revision.",
        },
        "scope_rules": [
            {
                "scope_path": entry,
                "body_rules": [
                    {
                        "relative_path": ".",
                        "motion_role": "dynamic",
                        "clear_density": True,
                        "mass_properties": {
                            "mode": "explicit",
                            "quality_tier": "provisional_geometry",
                            "mass_kg": float(spec["mass_kg"]),
                            "diagonal_inertia_kg_m2": spec["diagonal_inertia_kg_m2"],
                            "center_of_mass_body_local": [
                                0.0,
                                0.0,
                                float(spec["center_of_mass_z_m"]),
                            ],
                            "principal_axes": [1.0, 0.0, 0.0, 0.0],
                        },
                    }
                ],
            }
        ],
    }


def build_inputs(*, archive: Path, out: Path) -> dict[str, dict[str, Path]]:
    archive = archive.resolve()
    out = out.resolve()
    if _sha(archive) != ARCHIVE_SHA256:
        raise ValueError("manual_glassware_v1 archive SHA-256 does not match the reviewed source")
    results: dict[str, dict[str, Path]] = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for asset_id, spec in VESSELS.items():
            member = bundle.getmember(str(spec["archive_member"]))
            stream = bundle.extractfile(member)
            if stream is None:
                raise FileNotFoundError(member.name)
            source = out / "source/manual_glassware_v1/source_usd" / Path(member.name).name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(stream.read())
            if _sha(source) != spec["source_sha256"]:
                raise ValueError(f"source SHA-256 mismatch for {asset_id}")

            facade = _write(out / asset_id / "facade.usda", _facade_text(source, spec))
            interaction = _write_json(
                out / asset_id / "interaction_profile.json",
                _interaction_profile(facade, spec),
            )
            physics = _write_json(
                out / asset_id / "physics_profile.json",
                _physics_profile(facade, spec),
            )
            provenance = _write_json(
                out / asset_id / "source_provenance.json",
                {
                    "schema_version": "aan.manual_glassware_source.v1",
                    "archive_path": str(archive),
                    "archive_sha256": ARCHIVE_SHA256,
                    "archive_member": member.name,
                    "source_sha256": _sha(source),
                    "facade_sha256": _sha(facade),
                    "source_modified": False,
                    "producer_runtime_evidence": "Isaac Sim 4.5 evidence only; not inherited as Isaac 4.1 admission.",
                    "clear_material_scope": (
                        f"/World/{spec['entry_name']}/Visual/Source/{spec['visual_xform']}/"
                        f"{spec['visual_mesh']}/MAT_Borosilicate_Clear"
                    ),
                    "ground_glass_faces_preserved": int(spec["ground_faces"]),
                },
            )
            results[asset_id] = {
                "source": source,
                "facade": facade,
                "interaction": interaction,
                "physics": physics,
                "provenance": provenance,
            }
    _write_json(
        out / "inputs_manifest.json",
        {
            "schema_version": "aan.scientific_workbench_glass_material_v2_inputs.v1",
            "archive_sha256": ARCHIVE_SHA256,
            "assets": {
                asset_id: {key: str(path) for key, path in paths.items()}
                for asset_id, paths in results.items()
            },
        },
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    results = build_inputs(archive=args.archive, out=args.out)
    print(json.dumps({key: {name: str(path) for name, path in value.items()} for key, value in results.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
