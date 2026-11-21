#!/usr/bin/env python3
"""Extract the matched reagent-bottle plug SimReady input for AAN admission."""

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
    "time_codes_per_second": 60.0,
    "frames_per_second": 60.0,
}
PLUGS = {
    "reagent_bottle_plug_45_40": {
        "archive_member": "manual_glassware_v1/simready/reagent_bottle_plug_45_40.usdc",
        "source_sha256": "ea6f4b5f13f7f55c6c8bb53073f9afde8e6a6f1131afffffda462d1e8b3ce612",
        "source_dependency_member": (
            "manual_glassware_v1/source_usd/reagent_bottle_plug_45_40_source.usdc"
        ),
        "source_dependency_sha256": (
            "7d419bc7669a49991b56de09607188b694ff1cf0b5a7fac12e4955989c577f1c"
        ),
        "matched_vessel": "reagent_bottle_90x55",
        "mass_kg": 0.085,
        "center_of_mass_z_m": 0.032,
        "diagonal_inertia_kg_m2": [0.000038, 0.000038, 0.000027],
        "colliders": [
            {
                "relative_path": (
                    "Model/COL_ReagentBottlePlug_Stem/COL_ReagentBottlePlug_Stem_Mesh"
                ),
                "purpose": ["support", "containment"],
            },
            {
                "relative_path": "Model/COL_ReagentBottlePlug_Cap/Cylinder_001",
                "purpose": ["gripper", "support"],
            },
        ],
        "named_frames_z_m": {
            "support": 0.0,
            "joint_tip": 0.0,
            "joint_seat": 0.040,
            "grasp": 0.052,
        },
    }
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    return path


def _frame(z: float) -> dict[str, Any]:
    return {
        "translation_body_local_usd": [0.0, 0.0, z],
        "rotation_body_local_wxyz": [1.0, 0.0, 0.0, 0.0],
    }


def _interaction_profile(source: Path, asset_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    frames = spec["named_frames_z_m"]
    return {
        "schema_version": "aan.object_interaction_profile.v2",
        "profile_id": f"scientific_workbench.{asset_id}.original_simready",
        "revision": "reagent_bottle_pair_v1",
        "source_binding": {"sha256": _sha(source), "stage_metrics": STAGE_METRICS},
        "asset_entry_prim": "/ObjectRoot",
        "rigid_root": {
            "motion_role": "dynamic",
            "disable_descendant_rigid_bodies": True,
            "remove_descendant_mass_api": True,
        },
        "colliders": [
            {
                "relative_path": item["relative_path"],
                "mode": "preserve",
                "purpose": list(item["purpose"]),
                "approximation": "convexHull",
            }
            for item in spec["colliders"]
        ],
        "required_named_frames": ["support", "joint_tip", "joint_seat", "grasp"],
        "named_frames": {name: _frame(float(z)) for name, z in frames.items()},
        "open_top": {
            "required": False,
            "evidence": {
                "status": "declared",
                "method": "producer-authored independent ground-glass plug",
                "claim_boundary": (
                    "This admission preserves the matched 45/40 plug as a separate "
                    "dynamic rigid. Vessel seating, pull/insert success, and "
                    "robot-policy evidence remain outside this package."
                ),
            },
        },
        "runtime_gates": {
            "root_motion": {"required": True, "min_translation_m": 0.01},
            "stable_support": {"required": True},
            "gripper_collision": {"required": True},
        },
    }


def _physics_profile(source: Path, asset_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": f"scientific_workbench.{asset_id}.provisional.original_simready",
        "revision": "reagent_bottle_pair_v1",
        "source_binding": {"sha256": _sha(source), "stage_metrics": STAGE_METRICS},
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
                "scope_path": "/ObjectRoot",
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
        for asset_id, spec in PLUGS.items():
            member = bundle.getmember(str(spec["archive_member"]))
            stream = bundle.extractfile(member)
            if stream is None:
                raise FileNotFoundError(member.name)
            source = out / "source/manual_glassware_v1/simready" / Path(member.name).name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(stream.read())
            if _sha(source) != spec["source_sha256"]:
                raise ValueError(f"source SHA-256 mismatch for {asset_id}")

            dependency_member = bundle.getmember(str(spec["source_dependency_member"]))
            dependency_stream = bundle.extractfile(dependency_member)
            if dependency_stream is None:
                raise FileNotFoundError(dependency_member.name)
            source_dependency = (
                out
                / "source/manual_glassware_v1/source_usd"
                / Path(dependency_member.name).name
            )
            source_dependency.parent.mkdir(parents=True, exist_ok=True)
            source_dependency.write_bytes(dependency_stream.read())
            if _sha(source_dependency) != spec["source_dependency_sha256"]:
                raise ValueError(f"source dependency SHA-256 mismatch for {asset_id}")

            interaction = _write_json(
                out / asset_id / "interaction_profile.json",
                _interaction_profile(source, asset_id, spec),
            )
            physics = _write_json(
                out / asset_id / "physics_profile.json",
                _physics_profile(source, asset_id, spec),
            )
            provenance = _write_json(
                out / asset_id / "source_provenance.json",
                {
                    "schema_version": "aan.manual_glassware_source.v2",
                    "archive_path": str(archive),
                    "archive_sha256": ARCHIVE_SHA256,
                    "archive_member": member.name,
                    "source_sha256": _sha(source),
                    "source_dependency_member": dependency_member.name,
                    "source_dependency_sha256": _sha(source_dependency),
                    "source_modified": False,
                    "visual_material_policy": "preserve_original_simready",
                    "visual_material_claim": (
                        "The producer-authored ClearBorosilicate, GroundGlass, material "
                        "bindings, and GeomSubset membership are preserved."
                    ),
                    "matched_vessel": spec["matched_vessel"],
                    "producer_runtime_evidence": (
                        "Producer plug-fit evidence is Isaac Sim 4.5 only; this input "
                        "requires a new Isaac Sim 4.1 admission."
                    ),
                },
            )
            results[asset_id] = {
                "source": source,
                "source_dependency": source_dependency,
                "interaction": interaction,
                "physics": physics,
                "provenance": provenance,
            }
    _write_json(
        out / "inputs_manifest.json",
        {
            "schema_version": "aan.scientific_workbench_reagent_bottle_plug_inputs.v1",
            "archive_sha256": ARCHIVE_SHA256,
            "visual_material_policy": "preserve_original_simready",
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
    print(
        json.dumps(
            {
                asset_id: {name: str(path) for name, path in paths.items()}
                for asset_id, paths in results.items()
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
