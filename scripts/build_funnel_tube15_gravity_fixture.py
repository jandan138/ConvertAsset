#!/usr/bin/env python3
"""Compose the qualified funnel above the tube15 candidate with small liquid."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from convert_asset.fluid_interaction_runtime import _seed_cylinder
from convert_asset.liquid_autofill_runtime import _define_overlay, _qualification_scene
from convert_asset.liquid_recipe import load_liquid_recipe, liquid_recipe_sha256


def build(
    *, funnel: Path, tube: Path, recipe_path: Path, output: Path
) -> tuple[Path, Path]:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdPhysics

    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    shutil.copytree(funnel.resolve(), output / "deps/funnel")
    shutil.copytree(tube.resolve(), output / "deps/tube15")
    recipe = load_liquid_recipe(recipe_path)
    spacing = float(recipe["particle_set"]["spacing_m"])
    source = output / "source.usda"
    stage = Usd.Stage.CreateNew(str(source))
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    tube_root = UsdGeom.Xform.Define(stage, "/World/Tube15")
    tube_root.GetPrim().GetReferences().AddReference(
        "deps/tube15/asset.usda", "/FluidInteractionAsset"
    )
    funnel_root = UsdGeom.Xform.Define(stage, "/World/Funnel")
    funnel_root.GetPrim().GetReferences().AddReference(
        "deps/funnel/asset.usda", "/FluidInteractionAsset"
    )
    funnel_root.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.086))
    for rigid in (tube_root.GetPrim(), funnel_root.GetPrim()):
        UsdPhysics.RigidBodyAPI.Apply(rigid).CreateRigidBodyEnabledAttr(True).Set(True)
        rigid.CreateAttribute("physics:kinematicEnabled", Sdf.ValueTypeNames.Bool).Set(
            True
        )
    physics = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    physics.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
    physics.CreateGravityMagnitudeAttr(9.81)
    for name, value, kind in (
        ("physxScene:broadphaseType", "GPU", Sdf.ValueTypeNames.Token),
        ("physxScene:solverType", "TGS", Sdf.ValueTypeNames.Token),
        ("physxScene:enableGPUDynamics", True, Sdf.ValueTypeNames.Bool),
        ("physxScene:gpuMaxParticleContacts", 1048576, Sdf.ValueTypeNames.UInt),
        ("physxScene:timeStepsPerSecond", 120, Sdf.ValueTypeNames.UInt),
    ):
        physics.GetPrim().CreateAttribute(name, kind).Set(value)
    light = UsdLux.DomeLight.Define(stage, "/World/Light")
    light.CreateIntensityAttr(750.0)
    stage.GetRootLayer().Save()

    points = _seed_cylinder(
        center=[0.0, 0.0, 0.12],
        radius=0.010,
        z0=0.128,
        z1=0.140,
        spacing=spacing,
    )
    analysis = {
        "container_prim": "/World/Funnel",
        "up_axis": "Z",
        "meters_per_unit": 1.0,
        "instanceable_target": False,
        "collision_prims": [],
        "existing_collider_prims": [],
        "physics_scene_path": "/World/PhysicsScene",
    }
    overlay, _, particle_path, _ = _define_overlay(
        scene=source,
        output=output,
        analysis=analysis,
        points_m=points,
        recipe_override=recipe,
    )
    scene = output / "scene.usda"
    _qualification_scene(source, overlay, scene)
    fixture = {
        "schema_version": "aan.funnel_tube15_gravity_fixture.v1",
        "scene": "scene.usda",
        "particle_set_prim": particle_path,
        "particle_count": len(points),
        "physics_scene_path": "/World/PhysicsScene",
        "funnel_outlet_z_m": 0.086,
        "funnel_outer_outlet_radius_m": 0.005,
        "tube": {
            "floor_z_m": 0.015,
            "rim_z_m": 0.101,
            "inner_radius_m": 0.00664,
            "insertion_depth_m": 0.015,
            "retention_profile": [
                {"z_m": 0.015, "inner_radius_m": 0.0001},
                {"z_m": 0.016, "inner_radius_m": 0.0001},
                {"z_m": 0.020, "inner_radius_m": 0.0022852},
                {"z_m": 0.026, "inner_radius_m": 0.005112},
                {"z_m": 0.031, "inner_radius_m": 0.00664},
                {"z_m": 0.0945, "inner_radius_m": 0.00664},
                {"z_m": 0.098, "inner_radius_m": 0.005555},
                {"z_m": 0.101, "inner_radius_m": 0.005555},
            ],
        },
        "liquid_recipe": {
            "id": recipe["recipe_id"],
            "sha256": liquid_recipe_sha256(recipe),
            "payload": recipe,
        },
        "acceptance": {
            "minimum_legal_outlet_ratio": 0.90,
            "minimum_tube_capture_ratio": 0.85,
            "maximum_structural_leak_count": 0,
        },
    }
    fixture_path = output / "fixture.json"
    fixture_path.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n")
    return scene, fixture_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--funnel", type=Path, required=True)
    parser.add_argument("--tube", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(build(funnel=args.funnel, tube=args.tube, recipe_path=args.recipe, output=args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
