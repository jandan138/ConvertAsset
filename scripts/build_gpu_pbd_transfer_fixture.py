#!/usr/bin/env python3
"""Build a minimal fixed-target GPU-PBD liquid-transfer fixture."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any


SOURCE_INITIAL_XYZ = (0.25, 0.0, 0.0)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def _load_package(
    package: Path,
) -> tuple[dict[str, Any], dict[str, float], list[list[float]]]:
    profile_path = package / "gpu_pbd_static_container_profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if profile.get("promotion", {}).get("status") != "qualified":
        raise ValueError(f"container is not promoted: {package}")
    cavity = profile.get("cavity")
    if not isinstance(cavity, dict):
        fixture_path = package / str(profile["promotion"]["fixture"])
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        cavity = fixture["containment_bounds"]
    state_path = package / str(profile["promotion"]["initial_particle_state"])
    state = json.loads(state_path.read_text(encoding="utf-8"))
    points = state["positions"] if isinstance(state, dict) else state
    return profile, cavity, points


def _vec3_array(values: list[list[float]]) -> str:
    return ", ".join(f"({x:.7g}, {y:.7g}, {z:.7g})" for x, y, z in values)


def _component_usda(
    *, source_entry: str, target_entry: str, points: list[list[float]]
) -> str:
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
    def Xform "Transfer"
    {{
        def Xform "Source" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI"]
            prepend references = @deps/source/asset.usd@<{source_entry}>
        )
        {{
            bool physics:kinematicEnabled = 1
            bool physics:rigidBodyEnabled = 1
            double3 xformOp:translate = ({SOURCE_INITIAL_XYZ[0]}, 0, 0)
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }}
        def Xform "Target" (
            prepend apiSchemas = ["PhysicsRigidBodyAPI"]
            prepend references = @deps/target/asset.usd@<{target_entry}>
        )
        {{
            bool physics:kinematicEnabled = 1
            bool physics:rigidBodyEnabled = 1
        }}
        def PhysxParticleSystem "ParticleSystem" (
            prepend apiSchemas = ["PhysxParticleIsosurfaceAPI"]
        )
        {{
            float maxVelocity = 0.3
            float maxDepenetrationVelocity = inf
            float particleContactOffset = 0.005
            float restOffset = 0
            float fluidRestOffset = -inf
            float solidRestOffset = -inf
            int physxParticleIsosurface:gridFilteringPasses = 1
            float physxParticleIsosurface:gridSmoothingRadius = 0.010
            int physxParticleIsosurface:meshSmoothingPasses = 1
            float physxParticleIsosurface:surfaceDistance = 0.008
        }}
        def Material "LiquidMaterial"
        {{
            token outputs:surface.connect = </World/Transfer/LiquidMaterial/PreviewSurface.outputs:surface>
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
            rel material:binding = </World/Transfer/LiquidMaterial>
            rel physxParticle:particleSystem = </World/Transfer/ParticleSystem>
            point3f[] physxParticle:simulationPoints = [{positions}]
            point3f[] points = [{positions}]
            vector3f[] velocities = [{zeros}]
            float[] widths = [{widths}]
            token visibility = "invisible"
        }}
    }}
}}
"""


def _qualification_usda() -> str:
    return """#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    kilogramsPerUnit = 1
    upAxis = "Z"
    framesPerSecond = 30
    timeCodesPerSecond = 30
    subLayers = [@component.usda@]
)

over "World"
{
    def PhysicsScene "PhysicsScene" (
        prepend apiSchemas = ["PhysxSceneAPI"]
    )
    {
        vector3f physics:gravityDirection = (0, 0, -1)
        float physics:gravityMagnitude = 9.81
        token physxScene:broadphaseType = "GPU"
        bool physxScene:enableGPUDynamics = 1
        uint physxScene:gpuFoundLostAggregatePairsCapacity = 1500
        uint physxScene:gpuMaxParticleContacts = 1048576
        token physxScene:solverType = "TGS"
        uint physxScene:timeStepsPerSecond = 30
    }
    def Cube "Support" (
        prepend apiSchemas = ["PhysicsCollisionAPI"]
    )
    {
        double size = 1
        float3 xformOp:scale = (0.6, 0.45, 0.02)
        double3 xformOp:translate = (0, 0, -0.01)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
    }
    def Camera "QualificationCamera"
    {
        float focalLength = 45
        float horizontalAperture = 20.955
        matrix4d xformOp:transform = ((0.8637789009, 0.5038710255, 0, 0), (-0.0805565346, 0.1380969165, 0.9871372176, 0), (0.4973898422, -0.8526683009, 0.1598753064, 0), (0.55, -0.75, 0.42, 1))
        uniform token[] xformOpOrder = ["xformOp:transform"]
    }
    def DomeLight "QualificationLight"
    {
        float inputs:intensity = 1200
    }
}
"""


def build_fixture(
    *, source_package: Path, target_package: Path, output: Path
) -> dict[str, Any]:
    source_package = source_package.resolve()
    target_package = target_package.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    source_profile, source_cavity, particle_points = _load_package(source_package)
    target_profile, target_cavity, _ = _load_package(target_package)
    output.mkdir(parents=True)
    shutil.copytree(source_package, output / "deps/source")
    shutil.copytree(target_package, output / "deps/target")
    points = [
        [
            round(float(point[0]) + SOURCE_INITIAL_XYZ[0], 7),
            round(float(point[1]) + SOURCE_INITIAL_XYZ[1], 7),
            round(float(point[2]) + SOURCE_INITIAL_XYZ[2], 7),
        ]
        for point in particle_points
    ]
    component = output / "component.usda"
    component.write_text(
        _component_usda(
            source_entry=source_profile["entry_prim"],
            target_entry=target_profile["entry_prim"],
            points=points,
        ),
        encoding="utf-8",
    )
    qualification = output / "qualification.usda"
    qualification.write_text(_qualification_usda(), encoding="utf-8")
    points_path = _write_json(output / "initial_particle_state.json", points)
    candidates = [
        {
            "candidate_id": "c01",
            "rim_offset_x_m": 0.0,
            "rim_gap_m": 0.020,
            "tilt_deg": -100.0,
            "dwell_seconds": 2.0,
        },
        {
            "candidate_id": "c02",
            "rim_offset_x_m": 0.015,
            "rim_gap_m": 0.020,
            "tilt_deg": -105.0,
            "dwell_seconds": 2.5,
        },
        {
            "candidate_id": "c03",
            "rim_offset_x_m": 0.0,
            "rim_gap_m": 0.030,
            "tilt_deg": -110.0,
            "dwell_seconds": 3.0,
        },
        {
            "candidate_id": "c04",
            "rim_offset_x_m": -0.015,
            "rim_gap_m": 0.025,
            "tilt_deg": -105.0,
            "dwell_seconds": 2.5,
        },
    ]
    profile = {
        "schema_version": "aan.gpu_pbd_transfer_fixture.v1",
        "source_actor_mode": "prescribed_kinematic_trajectory",
        "target_actor_mode": "fixed_kinematic_rigid_body",
        "members": {
            "source": "/World/Transfer/Source",
            "target": "/World/Transfer/Target",
            "particles": "/World/Transfer/ParticleSet",
            "particle_system": "/World/Transfer/ParticleSystem",
        },
        "source": {
            "package": str(source_package),
            "asset_sha256": _sha(source_package / "asset.usd"),
            "profile_sha256": _sha(
                source_package / "gpu_pbd_static_container_profile.json"
            ),
            "initial_xyz_m": list(SOURCE_INITIAL_XYZ),
            "cavity": source_cavity,
        },
        "target": {
            "package": str(target_package),
            "asset_sha256": _sha(target_package / "asset.usd"),
            "profile_sha256": _sha(
                target_package / "gpu_pbd_static_container_profile.json"
            ),
            "fixed_xyz_m": [0.0, 0.0, 0.0],
            "cavity": target_cavity,
        },
        "liquid_parameters": {
            "source": "LabUtopia inputs/usd/scene/liquid_0812/test.usd",
            "particle_count": len(points),
            "particle_contact_offset_m": 0.005,
            "rest_offset_m": 0.0,
            "max_velocity_m_s": 0.3,
            "initial_particle_state": points_path.name,
            "initial_particle_state_sha256": _sha(points_path),
        },
        "trajectory_protocol": {
            "physics_hz": 30,
            "settle_seconds": 2.0,
            "lift_seconds": 0.5,
            "pretilt_degrees": -70.0,
            "pretilt_seconds": 0.5,
            "tilt_and_approach_seconds": 2.0,
            "retreat_seconds": 1.0,
            "upright_seconds": 0.5,
            "return_seconds": 1.0,
            "final_settle_seconds": 2.0,
            "high_root_z_m": 0.20,
        },
        "bounded_search": {
            "method": "deterministic_four_candidate_coarse_search_then_freeze",
            "candidates": candidates,
        },
        "qualification": {
            "minimum_target_reception_ratio": 0.5,
            "spill_is_blocking": False,
            "required_cold_runs": 3,
            "minimum_static_source_retention_ratio": 0.95,
            "maximum_below_support_count": 0,
            "minimum_mean_rtx_fps": 40.0,
        },
        "claim_boundary": "Prescribed kinematic transfer feasibility only; no robot, policy, benchmark, or 90 percent completion claim.",
    }
    profile_path = _write_json(output / "transfer_fixture_profile.json", profile)
    result = {
        "schema_version": "aan.gpu_pbd_transfer_fixture_build.v1",
        "output": str(output),
        "particle_count": len(points),
        "component_sha256": _sha(component),
        "qualification_sha256": _sha(qualification),
        "profile_sha256": _sha(profile_path),
    }
    _write_json(output / "build_result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", required=True, type=Path)
    parser.add_argument("--target-package", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build_fixture(
                source_package=args.source_package,
                target_package=args.target_package,
                output=args.out,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
