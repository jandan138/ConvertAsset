#!/usr/bin/env python3
"""Build a source-bound 29.77 mm magnetic stir-bar package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil


SOURCE_BASENAME = "magnetic_stir_bar_01_29_77mm.usda"
ENTRY = "/World/MagneticStirBar"
LENGTH_M = 0.02977
DIAMETER_M = 0.00871
RADIUS_M = DIAMETER_M / 2.0
REFERENCE_MASS_KG = 0.0045
REFERENCE_LENGTH_M = 0.03462
REFERENCE_DIAMETER_M = 0.00883


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def build(source: Path, output: Path) -> Path:
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    source = source.resolve()
    if source.name != SOURCE_BASENAME:
        raise ValueError(f"expected {SOURCE_BASENAME}, got {source.name}")
    if output.exists():
        shutil.rmtree(output)
    deps = output / "deps/usd"
    deps.mkdir(parents=True)
    packaged_source = deps / SOURCE_BASENAME
    shutil.copy2(source, packaged_source)
    source_sha = _sha(source)

    source_root_path = deps / "source_root.usda"
    source_root = Usd.Stage.CreateNew(str(source_root_path))
    UsdGeom.SetStageMetersPerUnit(source_root, 1.0)
    UsdGeom.SetStageUpAxis(source_root, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(source_root, "/World").GetPrim()
    source_root.SetDefaultPrim(world)
    UsdGeom.Xform.Define(source_root, ENTRY)
    UsdGeom.Xform.Define(source_root, f"{ENTRY}/Visual")
    source_prim = UsdGeom.Xform.Define(source_root, f"{ENTRY}/Visual/Source")
    source_prim.GetPrim().GetReferences().AddReference(SOURCE_BASENAME, "/root")
    source_root.GetRootLayer().Save()

    interaction_path = output / "overlays/interaction.usda"
    interaction_path.parent.mkdir(parents=True)
    interaction = Usd.Stage.CreateNew(str(interaction_path))
    UsdGeom.Xform.Define(interaction, "/World")
    body = UsdGeom.Xform.Define(interaction, ENTRY)
    rigid = UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
    rigid.CreateRigidBodyEnabledAttr(True)
    rigid.CreateKinematicEnabledAttr(False)
    proxy = UsdGeom.Xform.Define(interaction, f"{ENTRY}/__aan_collision_proxy")
    collider = UsdGeom.Cylinder.Define(interaction, f"{proxy.GetPath()}/bar")
    collider.CreateAxisAttr("X")
    collider.CreateRadiusAttr(RADIUS_M)
    collider.CreateHeightAttr(LENGTH_M)
    collider.CreateVisibilityAttr("invisible")
    UsdGeom.Xformable(collider).AddTranslateOp().Set(
        Gf.Vec3d(0.0, 0.0, RADIUS_M)
    )
    UsdPhysics.CollisionAPI.Apply(collider.GetPrim())
    for name, xyz in (
        ("support", (0.0, 0.0, 0.0)),
        ("grasp", (0.0, 0.0, RADIUS_M)),
    ):
        frame = UsdGeom.Xform.Define(interaction, f"{ENTRY}/__aan_frame_{name}")
        frame.AddTranslateOp().Set(Gf.Vec3d(*xyz))
    interaction.GetRootLayer().Save()

    volume_ratio = (
        LENGTH_M * DIAMETER_M**2
        / (REFERENCE_LENGTH_M * REFERENCE_DIAMETER_M**2)
    )
    mass_kg = REFERENCE_MASS_KG * volume_ratio
    inertia_x = 0.5 * mass_kg * RADIUS_M**2
    inertia_yz = mass_kg * (3.0 * RADIUS_M**2 + LENGTH_M**2) / 12.0
    physics_path = output / "overlays/physics_profile.usda"
    physics = Usd.Stage.CreateNew(str(physics_path))
    UsdGeom.Xform.Define(physics, "/World")
    physics_body = UsdGeom.Xform.Define(physics, ENTRY)
    UsdPhysics.RigidBodyAPI.Apply(physics_body.GetPrim())
    mass = UsdPhysics.MassAPI.Apply(physics_body.GetPrim())
    mass.CreateMassAttr(mass_kg)
    mass.CreateCenterOfMassAttr(Gf.Vec3f(0.0, 0.0, RADIUS_M))
    mass.CreateDiagonalInertiaAttr(
        Gf.Vec3f(inertia_x, inertia_yz, inertia_yz)
    )
    mass.CreatePrincipalAxesAttr(Gf.Quatf(1.0, Gf.Vec3f(0.0)))
    physics.GetRootLayer().Save()

    asset_path = output / "asset.usd"
    asset = Usd.Stage.CreateNew(str(asset_path))
    UsdGeom.SetStageMetersPerUnit(asset, 1.0)
    UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
    asset.SetMetadata("kilogramsPerUnit", 1.0)
    asset_world = UsdGeom.Xform.Define(asset, "/World").GetPrim()
    asset.SetDefaultPrim(asset_world)
    asset.GetRootLayer().subLayerPaths = [
        "overlays/physics_profile.usda",
        "overlays/interaction.usda",
        "deps/usd/source_root.usda",
    ]
    asset.GetRootLayer().Save()

    source_binding = {
        "sha256": source_sha,
        "stage_metrics": {
            "meters_per_unit": 1.0,
            "kilograms_per_unit": 1.0,
            "up_axis": "Z",
        },
    }
    _write_json(
        output / "interaction/profile.json",
        {
            "schema_version": "aan.object_interaction_profile.v2",
            "profile_id": "scientific_workbench.magnetic_stir_bar_29_77mm.interaction",
            "revision": "r1",
            "source_binding": source_binding,
            "asset_entry_prim": ENTRY,
            "rigid_root": {
                "motion_role": "dynamic",
                "disable_descendant_rigid_bodies": True,
                "remove_descendant_mass_api": True,
            },
            "colliders": [
                {
                    "relative_path": "__aan_collision_proxy/bar",
                    "mode": "author",
                    "purpose": ["gripper", "support"],
                    "geometry": {
                        "type": "Cylinder",
                        "axis": "X",
                        "radius": RADIUS_M,
                        "height": LENGTH_M,
                        "translation_body_local_usd": [0.0, 0.0, RADIUS_M],
                    },
                }
            ],
            "required_named_frames": ["support", "grasp"],
            "named_frames": {
                "support": {"translation_body_local_usd": [0.0, 0.0, 0.0]},
                "grasp": {
                    "translation_body_local_usd": [0.0, 0.0, RADIUS_M]
                },
            },
            "open_top": {"required": False},
            "runtime_gates": {
                "root_motion": {"required": True, "min_translation_m": 0.01},
                "stable_support": {"required": True},
                "gripper_collision": {"required": False},
            },
        },
    )
    _write_json(
        output / "physics/profile.json",
        {
            "schema_version": "aan.physics_profile.v1",
            "profile_id": "scientific_workbench.magnetic_stir_bar_29_77mm.provisional",
            "revision": "r1",
            "source_binding": source_binding,
            "evidence": {
                "parameter_status": "provisional_geometry",
                "claim_boundary": "Nominal PTFE simulation values; not measured.",
            },
            "mass_properties": {
                "mass_kg": mass_kg,
                "center_of_mass_body_local": [0.0, 0.0, RADIUS_M],
                "diagonal_inertia_kg_m2": [inertia_x, inertia_yz, inertia_yz],
            },
        },
    )
    _write_json(
        output / "evidence/manifest.json",
        {
            "schema_version": "asset_application_normalizer.v1",
            "package_id": "scientific_workbench_magnetic_stir_bar_29_77mm_r1_isaac41",
            "asset_id": "scientific_workbench_magnetic_stir_bar_29_77mm",
            "asset_role": "dynamic_object",
            "overall_status": "candidate_pending_runtime",
            "blocked_reasons": ["isaac41_runtime_qualification_not_run"],
            "entrypoints": {
                "root_usd": "asset.usd",
                "default_prim": "World",
                "asset_entry_prim": ENTRY,
                "asset_scope_prims": [ENTRY],
                "consumer_profile": "scenario-forge",
            },
            "source": {
                "path": str(source),
                "sha256": source_sha,
                "source_sha256": source_sha,
                "package_member": f"deps/usd/{SOURCE_BASENAME}",
                "package_member_sha256": _sha(packaged_source),
                "raw_source_unchanged": True,
            },
            "geometry": {
                "type": "rounded_cylindrical_stir_bar",
                "length_m": LENGTH_M,
                "diameter_m": DIAMETER_M,
            },
            "claims": {
                "identity_entry": True,
                "source_bound": True,
                "isaac41_stable_support": False,
                "robot_grasp_success": False,
                "task_success": False,
            },
        },
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.source, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
