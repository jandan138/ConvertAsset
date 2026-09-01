#!/usr/bin/env python3
"""Split Wangshuai's long-neck threaded 15 mL tube into identity packages."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_wangshuai/tube.usd"
)
DEFAULT_OUTPUT = REPO_ROOT / "outputs/tube15_long_neck_threaded_geometry_v1_20260901"
SOURCE_SHA256 = "0f279e39685656b508ed6b359f8dc56be099263364084e04ab812170c9ca3be0"
ASSETS = {
    "body": {
        "source_prim": "/World/tube",
        "entry": "/World/Tube15LongNeckThreadedBody",
        "package": "tube15_long_neck_threaded_body_v1",
        "mass": 0.015,
        "com": [0.0, 0.0, 0.052],
        "inertia": [1.3e-05, 1.3e-05, 5.2e-07],
    },
    "cap": {
        "source_prim": "/World/cap",
        "entry": "/World/Tube15LongNeckThreadedClosedCap",
        "package": "tube15_long_neck_threaded_closed_cap_v1",
        "mass": 0.002,
        "com": [0.0, 0.0, 0.00157037164052563],
        "inertia": [1.451261904108106e-07, 1.451285854728665e-07, 1.656781579265902e-07],
    },
}


@dataclass(frozen=True)
class Tube15PackageResult:
    output: Path
    packages: dict[str, Path]
    manifest: Path
    assembly_profile: Path


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _retarget(stage: Any, old_prefix: Any, new_prefix: Any) -> None:
    for prim in stage.Traverse():
        if not prim.GetPath().HasPrefix(new_prefix):
            continue
        for relationship in prim.GetRelationships():
            targets = relationship.GetTargets()
            rewritten = [
                target.ReplacePrefix(old_prefix, new_prefix)
                if target.HasPrefix(old_prefix)
                else target
                for target in targets
            ]
            if rewritten != targets:
                relationship.SetTargets(rewritten)


def _package(source_layer: Any, destination: Path, spec: dict[str, Any]) -> None:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

    destination.mkdir(parents=True)
    asset = destination / "asset.usd"
    stage = Usd.Stage.CreateNew(str(asset))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    stage.GetRootLayer().Save()
    layer = Sdf.Layer.FindOrOpen(str(asset))
    Sdf.CopySpec(source_layer, spec["source_prim"], layer, spec["entry"])
    source_material = "/World/PhysicsMaterial"
    target_material = spec["entry"] + "/PhysicsMaterial"
    Sdf.CopySpec(source_layer, source_material, layer, target_material)
    layer.Save()
    stage = Usd.Stage.Open(str(asset))
    old = Sdf.Path(spec["source_prim"])
    new = Sdf.Path(spec["entry"])
    _retarget(stage, old, new)
    root = stage.GetPrimAtPath(spec["entry"])
    xform = UsdGeom.Xformable(root)
    xform.ClearXformOpOrder()
    UsdPhysics.RigidBodyAPI(root).CreateKinematicEnabledAttr(False)
    mass = UsdPhysics.MassAPI.Apply(root)
    mass.CreateMassAttr(spec["mass"])
    mass.CreateCenterOfMassAttr(Gf.Vec3f(*spec["com"]))
    mass.CreateDiagonalInertiaAttr(Gf.Vec3f(*spec["inertia"]))
    mass.CreatePrincipalAxesAttr(Gf.Quatf(1.0))
    colliders = [
        prim
        for prim in stage.Traverse()
        if prim.GetPath().HasPrefix(new) and prim.HasAPI(UsdPhysics.CollisionAPI)
    ]
    if len(colliders) != 1:
        raise ValueError("expected exactly one source SDF collider")
    material = UsdShade.Material(stage.GetPrimAtPath(target_material))
    UsdShade.MaterialBindingAPI.Apply(colliders[0]).Bind(
        material, materialPurpose="physics"
    )
    frames = UsdGeom.Scope.Define(stage, spec["entry"] + "/Frames")
    if spec["package"].endswith("body_v1"):
        for name, z in (("Opening", 0.101), ("ThreadAxis", 0.0962), ("Grasp", 0.055)):
            frame = UsdGeom.Xform.Define(stage, str(frames.GetPath()) + "/" + name)
            frame.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, z))
    else:
        for name, z in (("ThreadMate", -0.00939), ("Grasp", 0.0), ("ClosedTop", 0.00935)):
            frame = UsdGeom.Xform.Define(stage, str(frames.GetPath()) + "/" + name)
            frame.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, z))
    root.SetCustomDataByKey("aan:motionRole", "dynamic")
    root.SetCustomDataByKey("aan:qualityTier", "provisional_geometry")
    stage.GetRootLayer().Save()
    _write_json(
        destination / "physics/profile.json",
        {
            "schema_version": "aan.physics_profile.v1",
            "profile_id": spec["package"] + ".physics.v1",
            "motion_role": "dynamic",
            "effective_kinematic": False,
            "quality_tier": "provisional_geometry",
            "mass_properties": {
                "mass_kg": spec["mass"],
                "center_of_mass_body_local_m": spec["com"],
                "diagonal_inertia_kg_m2": spec["inertia"],
                "principal_axes_wxyz": [1.0, 0.0, 0.0, 0.0],
                "method": "reused_family_provisional_profile_not_measured",
            },
        },
    )


def build_packages(
    output: Path = DEFAULT_OUTPUT,
    *,
    source: Path = DEFAULT_SOURCE,
) -> Tube15PackageResult:
    from pxr import Sdf

    output = output.resolve()
    source = source.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to replace output: {output}")
    if _sha(source) != SOURCE_SHA256:
        raise ValueError("source USD SHA-256 mismatch")
    input_root = output / "input"
    input_root.mkdir(parents=True)
    shutil.copy2(source, input_root / "source.usd")
    source_layer = Sdf.Layer.FindOrOpen(str(source))
    packages = {}
    for name, spec in ASSETS.items():
        package = output / "packages" / spec["package"]
        _package(source_layer, package, spec)
        packages[name] = package
    assembly_profile = output / "assembly_profile.json"
    _write_json(
        assembly_profile,
        {
            "schema_version": "aan.tube15_threaded_assembly_pose.v1",
            "body_entry": ASSETS["body"]["entry"],
            "cap_entry": ASSETS["cap"]["entry"],
            "cap_pose": {
                "xyz_m": [0.0, 0.0, 0.10998681642541698],
                "wxyz": [0.5569506, 0.0, 0.0, 0.8305456],
            },
            "claim": "author_initial_pose_only_not_tightened_or_locked",
        },
    )
    manifest = output / "asset_set_manifest.json"
    _write_json(
        manifest,
        {
            "schema_version": "aan.tube15_long_neck_threaded_asset_set.v1",
            "overall_status": "candidate_runtime_qualification_pending",
            "source": {"path": str(source), "sha256": SOURCE_SHA256, "original_unchanged": True},
            "lineage": {
                "kind": "inferred_geometry_lineage_not_producer_provenance",
                "geometry_fingerprint_matches_long_neck_master": True,
                "total_height_m": 0.101,
                "neck_start_m": 0.08376,
                "fixed_tip_and_cone_end_m": 0.0232,
            },
            "packages": {
                name: str(path.relative_to(output)) for name, path in packages.items()
            },
            "thread_profile": {
                "body_external_turns": 4.0,
                "cap_internal_turns": 4.0,
                "nominal_pitch_m": 0.0019,
                "geometry_present": True,
            },
            "cap_topology": {
                "closed_top": True,
                "connected_components": 1,
                "boundary_edges": 0,
                "nonmanifold_edges": 0,
            },
            "claims": {
                "dynamic_geometry_ready": False,
                "sdf_collision_ready": False,
                "thread_interaction_ready": False,
                "task08_ready": False,
                "liquid_container_ready": False,
                "robot_policy_success": False,
                "benchmark_success": False,
            },
        },
    )
    return Tube15PackageResult(
        output=output,
        packages=packages,
        manifest=manifest,
        assembly_profile=assembly_profile,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    print(build_packages(args.output, source=args.source).manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
