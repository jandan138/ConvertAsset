#!/usr/bin/env python3
"""Build the source-bound Task 02 r8 PhysX PBD fluid workcell component."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
from typing import Any

from convert_asset.asset_application_normalizer.interactive_fluid_scene import (
    load_interactive_fluid_scene_profile,
)


COMPONENT_ROOT = "/World/FluidWorkcell"
SOURCE = COMPONENT_ROOT + "/SourceContainer"
TARGET = COMPONENT_ROOT + "/TargetContainer"
PARTICLE_SYSTEM = COMPONENT_ROOT + "/ParticleSystem"
PARTICLES = COMPONENT_ROOT + "/ParticleSet"
SOURCE_XYZ = (0.16, -0.15, 0.0)
TARGET_XYZ = (-0.16, -0.17, 0.0)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _write_json(path: Path, payload: Any) -> Path:
    return _write(
        path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    )


def _copy_package(source: Path, destination: Path) -> None:
    if not (source / "asset.usd").is_file():
        raise FileNotFoundError(f"missing source-bound asset.usd: {source}")
    shutil.copytree(source, destination, dirs_exist_ok=True)


def authored_points(count: int = 548) -> list[list[float]]:
    """Return a deterministic compact fill inside the 250 mL cylinder."""
    points: list[list[float]] = []
    spacing = 0.0052
    radial_limit = 0.0157
    z = 0.010
    layer = 0
    while len(points) < count:
        phase = 0.5 * spacing if layer % 2 else 0.0
        for ix in range(-3, 4):
            for iy in range(-3, 4):
                x = ix * spacing + phase
                y = iy * spacing
                if math.hypot(x, y) > radial_limit:
                    continue
                points.append(
                    [
                        round(SOURCE_XYZ[0] + x, 7),
                        round(SOURCE_XYZ[1] + y, 7),
                        round(z, 7),
                    ]
                )
                if len(points) == count:
                    return points
        layer += 1
        z += spacing
    return points


def _vec3_array(values: list[list[float]]) -> str:
    return ", ".join(f"({x:.7g}, {y:.7g}, {z:.7g})" for x, y, z in values)


def _component_usda(points: list[list[float]]) -> str:
    positions = _vec3_array(points)
    zeros = ", ".join("(0, 0, 0)" for _ in points)
    widths = ", ".join("0.005" for _ in points)
    return f"""#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Xform "FluidWorkcell"
    {{
        def Xform "SourceContainer" (
            prepend references = @deps/source_container/asset.usd@</World/GraduatedCylinder250ml>
        )
        {{
            double3 xformOp:translate = ({SOURCE_XYZ[0]}, {SOURCE_XYZ[1]}, {SOURCE_XYZ[2]})
            uniform token[] xformOpOrder = ["xformOp:translate"]
            over "__aan_collision_proxy"
            {{
                bool physics:collisionEnabled = 0
                over "bottom" {{
                    bool physics:collisionEnabled = 0
                }}
                over "wall_neg_x" {{
                    bool physics:collisionEnabled = 0
                }}
                over "wall_neg_y" {{
                    bool physics:collisionEnabled = 0
                }}
                over "wall_pos_x" {{
                    bool physics:collisionEnabled = 0
                }}
                over "wall_pos_y" {{
                    bool physics:collisionEnabled = 0
                }}
            }}
            over "Visual"
            {{
                over "Source"
                {{
                    over "Hollow_Body"
                    {{
                        over "Hollow_Body_Mesh_002" (
                            prepend apiSchemas = ["PhysicsCollisionAPI", "PhysxCollisionAPI", "PhysxConvexHullCollisionAPI", "PhysicsMeshCollisionAPI", "PhysxConvexDecompositionCollisionAPI"]
                        )
                        {{
                            bool physics:collisionEnabled = 1
                            token physics:approximation = "convexDecomposition"
                            float physxCollision:contactOffset = 0.01
                            float physxCollision:restOffset = 0.004
                            float physxConvexDecompositionCollision:errorPercentage = 10
                            uint physxConvexDecompositionCollision:hullVertexLimit = 32
                            uint physxConvexDecompositionCollision:maxConvexHulls = 32
                            float physxConvexDecompositionCollision:minThickness = 0.001
                            bool physxConvexDecompositionCollision:shrinkWrap = 1
                            uint physxConvexDecompositionCollision:voxelResolution = 500000
                            uint physxConvexHullCollision:hullVertexLimit = 32
                            float physxConvexHullCollision:minThickness = 0.001
                        }}
                    }}
                    over "Closed_Inner_Bottom"
                    {{
                        over "Cylinder_006" (
                            prepend apiSchemas = ["PhysicsCollisionAPI", "PhysxCollisionAPI", "PhysxConvexHullCollisionAPI", "PhysicsMeshCollisionAPI", "PhysxConvexDecompositionCollisionAPI"]
                        )
                        {{
                            bool physics:collisionEnabled = 1
                            token physics:approximation = "convexDecomposition"
                            float physxConvexDecompositionCollision:errorPercentage = 10
                            uint physxConvexDecompositionCollision:hullVertexLimit = 32
                            uint physxConvexDecompositionCollision:maxConvexHulls = 8
                            uint physxConvexDecompositionCollision:voxelResolution = 500000
                        }}
                    }}
                }}
            }}
        }}

        def Xform "TargetContainer" (
            prepend references = @deps/target_container/asset.usd@</World/Beaker325ml>
        )
        {{
            double3 xformOp:translate = ({TARGET_XYZ[0]}, {TARGET_XYZ[1]}, {TARGET_XYZ[2]})
            uniform token[] xformOpOrder = ["xformOp:translate"]
            over "__aan_collision_proxy"
            {{
                bool physics:collisionEnabled = 0
                over "bottom" {{
                    bool physics:collisionEnabled = 0
                }}
                over "wall_neg_x" {{
                    bool physics:collisionEnabled = 0
                }}
                over "wall_neg_y" {{
                    bool physics:collisionEnabled = 0
                }}
                over "wall_pos_x" {{
                    bool physics:collisionEnabled = 0
                }}
                over "wall_pos_y" {{
                    bool physics:collisionEnabled = 0
                }}
            }}
            over "Visual"
            {{
                over "Source"
                {{
                    over "Beaker_Hollow_Body"
                    {{
                        over "Beaker_Hollow_Body_Mesh" (
                            prepend apiSchemas = ["PhysicsCollisionAPI", "PhysxCollisionAPI", "PhysxConvexHullCollisionAPI", "PhysicsMeshCollisionAPI", "PhysxConvexDecompositionCollisionAPI"]
                        )
                        {{
                            bool physics:collisionEnabled = 1
                            token physics:approximation = "convexDecomposition"
                            float physxCollision:contactOffset = 0.01
                            float physxCollision:restOffset = 0.001
                            float physxConvexDecompositionCollision:errorPercentage = 10
                            uint physxConvexDecompositionCollision:hullVertexLimit = 32
                            uint physxConvexDecompositionCollision:maxConvexHulls = 32
                            float physxConvexDecompositionCollision:minThickness = 0.001
                            bool physxConvexDecompositionCollision:shrinkWrap = 1
                            uint physxConvexDecompositionCollision:voxelResolution = 500000
                            uint physxConvexHullCollision:hullVertexLimit = 32
                            float physxConvexHullCollision:minThickness = 0.001
                        }}
                    }}
                }}
            }}
        }}

        def PhysxParticleSystem "ParticleSystem" (
            prepend apiSchemas = ["PhysxParticleIsosurfaceAPI"]
        )
        {{
            float maxVelocity = 0.3
            float particleContactOffset = 0.005
            float restOffset = 0
            int physxParticleIsosurface:gridFilteringPasses = 1
            float physxParticleIsosurface:gridSmoothingRadius = 0.010
            int physxParticleIsosurface:meshSmoothingPasses = 1
            float physxParticleIsosurface:surfaceDistance = 0.008
        }}

        def Material "LiquidMaterial"
        {{
            token outputs:surface.connect = </World/FluidWorkcell/LiquidMaterial/PreviewSurface.outputs:surface>
            def Shader "PreviewSurface"
            {{
                uniform token info:id = "UsdPreviewSurface"
                color3f inputs:diffuseColor = (0.20, 0.58, 0.82)
                float inputs:ior = 1.333
                float inputs:opacity = 0.18
                float inputs:roughness = 0.06
                token outputs:surface
            }}
        }}

        def Points "ParticleSet" (
            prepend apiSchemas = ["PhysxParticleSetAPI", "PhysicsMassAPI", "MaterialBindingAPI"]
        )
        {{
            rel material:binding = </World/FluidWorkcell/LiquidMaterial>
            rel physxParticle:particleSystem = </World/FluidWorkcell/ParticleSystem>
            bool physxParticle:fluid = 1
            int physxParticle:particleGroup = 0
            bool physxParticle:selfCollision = 1
            point3f[] points = [{positions}]
            vector3f[] velocities = [{zeros}]
            float[] widths = [{widths}]
            token visibility = "invisible"
        }}
    }}
}}
"""


def _entrypoint(rate: int, *, qualification: bool) -> str:
    support = (
        """
    def Cube "QualificationSupport" (
        prepend apiSchemas = ["PhysicsCollisionAPI"]
    )
    {
        double size = 1
        float3 xformOp:scale = (1.2, 0.7, 0.04)
        double3 xformOp:translate = (0, 0, -0.02)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
    }
"""
        if qualification
        else ""
    )
    return f"""#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
    framesPerSecond = {rate}
    timeCodesPerSecond = {rate}
    subLayers = [@component.usda@]
)

over "World"
{{
    def PhysicsScene "PhysicsScene" (
        prepend apiSchemas = ["PhysxSceneAPI"]
    )
    {{
        vector3f physics:gravityDirection = (0, 0, -1)
        float physics:gravityMagnitude = 9.81
        token physxScene:broadphaseType = "GPU"
        bool physxScene:enableGPUDynamics = 1
        uint physxScene:gpuMaxParticleContacts = 1048576
        token physxScene:solverType = "TGS"
        uint physxScene:timeStepsPerSecond = {rate}
    }}
{support}}}
"""


def build(
    *, cylinder_package: Path, beaker_package: Path, out: Path
) -> dict[str, Path]:
    cylinder_package = Path(cylinder_package).resolve()
    beaker_package = Path(beaker_package).resolve()
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    _copy_package(cylinder_package, out / "deps/source_container")
    _copy_package(beaker_package, out / "deps/target_container")

    points = authored_points()
    points_path = _write_json(out / "authored_particle_points.json", points)
    component = _write(out / "component.usda", _component_usda(points))
    qualification = _write(
        out / "qualification_30hz.usda", _entrypoint(30, qualification=True)
    )
    consumer = _write(out / "consumer_60hz.usda", _entrypoint(60, qualification=False))
    asset = _write(out / "asset.usd", _entrypoint(60, qualification=False))

    collision_meshes = [
        f"{SOURCE}/Visual/Source/Hollow_Body/Hollow_Body_Mesh_002",
        f"{SOURCE}/Visual/Source/Closed_Inner_Bottom/Cylinder_006",
        f"{TARGET}/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh",
    ]
    profile_payload = {
        "schema_version": "aan.interactive_fluid_scene_profile.v1",
        "profile_id": "scientific_workbench.task02.cylinder_to_beaker.fluid_fast.r8",
        "revision": "r8",
        "runtime_profile": "isaac41",
        "component_root_prim": COMPONENT_ROOT,
        "members": {
            "source_container": SOURCE,
            "target_container": TARGET,
            "particle_system": PARTICLE_SYSTEM,
            "particles": PARTICLES,
        },
        "particles": {
            "kind": "PhysX_PBD",
            "count": len(points),
            "authored_points_path": points_path.name,
            "authored_points_sha256": _sha(points_path),
            "display": "physx_isosurface",
            "volume_claim": "unmeasured_fast_prototype_not_250ml_calibration",
        },
        "container_collision": {
            "strategy": "visual_mesh_convex_decomposition",
            "disable_existing_proxy_paths": [
                f"{SOURCE}/__aan_collision_proxy",
                f"{TARGET}/__aan_collision_proxy",
            ],
            "meshes": [
                {
                    "prim_path": path,
                    "approximation": "convexDecomposition",
                    "error_percentage": 10.0,
                }
                for path in collision_meshes
            ],
        },
        "entrypoints": {
            "qualification_30hz": {"path": qualification.name, "physics_hz": 30},
            "consumer_60hz": {"path": consumer.name, "physics_hz": 60},
        },
        "classification_regions": {
            "source": {
                "kind": "cylinder",
                "center_xyz_m": list(SOURCE_XYZ),
                "radius_m": 0.018,
                "height_m": 0.268,
            },
            "target": {
                "kind": "cylinder",
                "center_xyz_m": list(TARGET_XYZ),
                "radius_m": 0.039,
                "height_m": 0.108,
            },
        },
        "qualification": {
            "static_hold_seconds": 8.0,
            "minimum_source_retention_ratio": 0.8,
            "maximum_below_support_count": 0,
            "minimum_peak_target_ratio": 0.05,
            "performance": {
                "width": 960,
                "height": 540,
                "minimum_rtx_fps": 40.0,
                "required_repeats": 1,
                "gpu": "NVIDIA GeForce RTX 4090",
            },
        },
        "allowed_consumer_composition": [
            "visual_static_environment",
            "static_support",
            "robot_config_injection",
        ],
        "claim_boundary": {
            "prototype": True,
            "liquid_metric_active": False,
            "robot_grasp_success": False,
            "policy_success": False,
            "benchmark_success": False,
        },
    }
    profile = _write_json(out / "interactive_fluid_scene_profile.json", profile_payload)
    load_interactive_fluid_scene_profile(profile)

    closure = []
    for path in sorted(
        p for p in out.rglob("*") if p.is_file() and "evidence" not in p.parts
    ):
        closure.append({"path": path.relative_to(out).as_posix(), "sha256": _sha(path)})
    manifest = _write_json(
        out / "evidence/manifest.json",
        {
            "schema_version": "aan.interactive_fluid_scene_package.v1",
            "producer": "ConvertAsset",
            "package_id": "scientific_workbench_task02_fluid_component_r8",
            "producer_revision": "2026-08-13-task02-fluid-r8-candidate",
            "overall_status": "candidate_pending_runtime",
            "blocked_reasons": ["runtime_qualification_not_run"],
            "entrypoints": profile_payload["entrypoints"],
            "profile": {"path": profile.name, "sha256": _sha(profile)},
            "source_packages": {
                "source_container": {
                    "asset_sha256": _sha(cylinder_package / "asset.usd")
                },
                "target_container": {
                    "asset_sha256": _sha(beaker_package / "asset.usd")
                },
            },
            "closure": {"files": closure},
            "runtime_qualification": {"status": "not_run"},
            "claims": profile_payload["claim_boundary"],
        },
    )
    return {
        "asset": asset,
        "component": component,
        "qualification": qualification,
        "consumer": consumer,
        "profile": profile,
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cylinder-package", required=True, type=Path)
    parser.add_argument("--beaker-package", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = build(
        cylinder_package=args.cylinder_package,
        beaker_package=args.beaker_package,
        out=args.out,
    )
    print(json.dumps({key: path.as_posix() for key, path in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
