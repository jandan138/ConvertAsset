#!/usr/bin/env python3
"""Build a minimal fixed-target GPU-PBD liquid-transfer fixture."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
from typing import Any


SOURCE_INITIAL_XYZ = (0.25, 0.0, 0.0)
REFERENCE_0812_PARTICLE_CONTACT_OFFSET_M = 0.005
REFERENCE_0812_PARTICLE_WIDTH_M = 0.00594
REFERENCE_0812_PARTICLE_SPACING_M = 0.00582
R84_PARTICLE_WIDTH_M = 0.005
INITIAL_CLEARANCE_MARGIN_M = 0.0005
VISIBLE_LIQUID_RGB = (0.32, 0.72, 0.95)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def _load_pre_settled_particle_state(path: Path) -> list[list[float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("pre-settled particle state must be a JSON mapping")
    if payload.get("schema_version") != "aan.gpu_pbd_settled_particle_state.v1":
        raise ValueError("unsupported pre-settled particle state schema")
    if payload.get("coordinate_space") != "world":
        raise ValueError("pre-settled particle state must use world coordinates")
    positions = payload.get("positions")
    if not isinstance(positions, list) or not positions:
        raise ValueError("pre-settled particle state positions must be non-empty")
    if payload.get("particle_count") != len(positions):
        raise ValueError("pre-settled particle count does not match positions")
    source_pose = payload.get("source_pose", {})
    if source_pose.get("xyz_m") != list(SOURCE_INITIAL_XYZ) or source_pose.get(
        "wxyz"
    ) != [1.0, 0.0, 0.0, 0.0]:
        raise ValueError("pre-settled particle state source pose does not match fixture")
    return [[float(value) for value in point] for point in positions]


def _load_package(
    package: Path,
) -> tuple[dict[str, Any], dict[str, float], list[list[float]], float]:
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
    fixture_path = package / str(profile["promotion"].get("fixture", ""))
    particle_contact_offset_m = 0.005
    if fixture_path.is_file():
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        particle_contact_offset_m = float(
            fixture.get("particle_parameters", {}).get(
                "particle_contact_offset_m", particle_contact_offset_m
            )
        )
    return profile, cavity, points, particle_contact_offset_m


def _vec3_array(values: list[list[float]]) -> str:
    return ", ".join(f"({x:.7g}, {y:.7g}, {z:.7g})" for x, y, z in values)


def _pack_to_fill_ratio(
    *,
    cavity: dict[str, Any],
    target_fill_ratio: float,
    particle_contact_offset_m: float,
    particle_spacing_m: float,
    container_contact_offset_m: float,
) -> list[list[float]]:
    """Pack a deterministic hexagonal lattice up to a cavity-height ratio."""

    if not 0.0 < target_fill_ratio < 1.0:
        raise ValueError("target_settled_fill_ratio must be between zero and one")
    radius = float(cavity["radius_m"])
    floor = float(cavity["floor_z_m"])
    rim = float(cavity["rim_z_m"])
    radial_limit = (
        radius
        - particle_contact_offset_m
        - INITIAL_CLEARANCE_MARGIN_M
    )
    if radial_limit <= 0.0:
        return []
    target_surface = floor + target_fill_ratio * (rim - floor)
    first_z = floor + particle_contact_offset_m
    last_z = target_surface - particle_contact_offset_m
    if last_z < first_z:
        return []

    points: list[list[float]] = []
    center_x, center_y = [float(value) for value in cavity.get("center_xy_m", [0, 0])]
    row_step = particle_spacing_m * math.sqrt(3.0) / 2.0
    layer = 0
    z = first_z
    while z <= last_z + 1e-9:
        layer_shift = 0.5 * particle_spacing_m if layer % 2 else 0.0
        row = -math.ceil(radial_limit / row_step)
        while row * row_step <= radial_limit + 1e-9:
            y = row * row_step
            x_shift = layer_shift + (0.5 * particle_spacing_m if row % 2 else 0.0)
            column = -math.ceil(radial_limit / particle_spacing_m)
            while column * particle_spacing_m <= radial_limit + 1e-9:
                x = column * particle_spacing_m + x_shift
                if math.hypot(x, y) <= radial_limit + 1e-9:
                    points.append(
                        [
                            round(center_x + x, 7),
                            round(center_y + y, 7),
                            round(z, 7),
                        ]
                    )
                column += 1
            row += 1
        layer += 1
        z = first_z + layer * particle_spacing_m
    return points


def _visible_fill_state(
    *,
    source_profile: dict[str, Any],
    source_cavity: dict[str, Any],
    baseline_particle_count: int,
    source_particle_contact_offset_m: float,
    target_fill_ratio: float,
    initial_packing_fill_ratio: float,
) -> tuple[list[list[float]], float, float, dict[str, Any]]:
    """Try exact 0812 particles first, then the immutable r8.4 parameters."""

    container_contact_offset = float(
        source_profile.get("collision", {}).get("contact_offset_m", 0.0)
    )
    attempts: list[dict[str, Any]] = []
    exact = _pack_to_fill_ratio(
        cavity=source_cavity,
        target_fill_ratio=initial_packing_fill_ratio,
        particle_contact_offset_m=REFERENCE_0812_PARTICLE_CONTACT_OFFSET_M,
        particle_spacing_m=REFERENCE_0812_PARTICLE_SPACING_M,
        container_contact_offset_m=container_contact_offset,
    )
    if len(exact) >= baseline_particle_count:
        attempts.append(
            {
                "baseline": "labutopia_0812_exact",
                "status": "selected",
                "particle_count": len(exact),
            }
        )
        return (
            exact,
            REFERENCE_0812_PARTICLE_CONTACT_OFFSET_M,
            REFERENCE_0812_PARTICLE_WIDTH_M,
            {"selected_baseline": "labutopia_0812_exact", "attempts": attempts},
        )
    attempts.append(
        {
            "baseline": "labutopia_0812_exact",
            "status": "not_applicable",
            "particle_count_at_target_fill": len(exact),
            "reason": "increase_only_policy_cannot_reduce_baseline_particle_count",
        }
    )

    # PhysX derives the 0812 fluid-rest spacing as roughly 1.188 times the
    # authored particle contact offset.  Preserve the r8.4 contact offset and
    # use the corresponding non-overlapping lattice instead of stretching the
    # old 548-particle cloud.
    fallback_spacing = source_particle_contact_offset_m * 1.188
    fallback = _pack_to_fill_ratio(
        cavity=source_cavity,
        target_fill_ratio=initial_packing_fill_ratio,
        particle_contact_offset_m=source_particle_contact_offset_m,
        particle_spacing_m=fallback_spacing,
        container_contact_offset_m=container_contact_offset,
    )
    if len(fallback) <= baseline_particle_count:
        raise ValueError("r8.4 fallback did not increase the particle count")
    attempts.append(
        {
            "baseline": "task02_r84",
            "status": "selected",
            "particle_count": len(fallback),
            "particle_spacing_m": fallback_spacing,
            "container_contact_offset_m_recorded_not_double_subtracted": (
                container_contact_offset
            ),
        }
    )
    return (
        fallback,
        source_particle_contact_offset_m,
        R84_PARTICLE_WIDTH_M,
        {"selected_baseline": "task02_r84", "attempts": attempts},
    )


def _component_usda(
    *,
    source_entry: str,
    target_entry: str,
    points: list[list[float]],
    particle_contact_offset_m: float,
    particle_width_m: float = R84_PARTICLE_WIDTH_M,
    diffuse_color: tuple[float, float, float] = (0.20, 0.58, 0.82),
    opacity: float = 0.18,
    roughness: float = 0.06,
) -> str:
    positions = _vec3_array(points)
    zeros = ", ".join("(0, 0, 0)" for _ in points)
    widths = ", ".join(f"{particle_width_m:.7g}" for _ in points)
    color = ", ".join(f"{value:.7g}" for value in diffuse_color)
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
            float particleContactOffset = {particle_contact_offset_m:.7g}
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
                color3f inputs:diffuseColor = ({color})
                float inputs:ior = 1.333
                float inputs:opacity = {opacity:.7g}
                float inputs:roughness = {roughness:.7g}
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
        uint physxScene:timeStepsPerSecond = 120
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
    *,
    source_package: Path,
    target_package: Path,
    output: Path,
    target_settled_fill_ratio: float | None = None,
    settled_fill_ratio_tolerance: float = 0.05,
    initial_packing_fill_ratio: float | None = None,
    pre_settled_particle_state: Path | None = None,
) -> dict[str, Any]:
    source_package = source_package.resolve()
    target_package = target_package.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    (
        source_profile,
        source_cavity,
        particle_points,
        source_particle_contact_offset_m,
    ) = _load_package(source_package)
    (
        target_profile,
        target_cavity,
        _,
        target_particle_contact_offset_m,
    ) = _load_package(target_package)
    particle_contact_offset_m = min(
        source_particle_contact_offset_m, target_particle_contact_offset_m
    )
    particle_width_m = R84_PARTICLE_WIDTH_M
    particle_parameter_selection: dict[str, Any] | None = None
    diffuse_color = (0.20, 0.58, 0.82)
    opacity = 0.18
    roughness = 0.06
    if target_settled_fill_ratio is not None:
        packing_fill_ratio = (
            initial_packing_fill_ratio
            if initial_packing_fill_ratio is not None
            else target_settled_fill_ratio
        )
        (
            particle_points,
            particle_contact_offset_m,
            particle_width_m,
            particle_parameter_selection,
        ) = _visible_fill_state(
            source_profile=source_profile,
            source_cavity=source_cavity,
            baseline_particle_count=len(particle_points),
            source_particle_contact_offset_m=particle_contact_offset_m,
            target_fill_ratio=target_settled_fill_ratio,
            initial_packing_fill_ratio=packing_fill_ratio,
        )
        diffuse_color = VISIBLE_LIQUID_RGB
        opacity = 0.34
        roughness = 0.02
    output.mkdir(parents=True)
    shutil.copytree(source_package, output / "deps/source")
    shutil.copytree(target_package, output / "deps/target")
    pre_settled_source_sha256: str | None = None
    if pre_settled_particle_state is not None:
        pre_settled_particle_state = pre_settled_particle_state.resolve()
        points = _load_pre_settled_particle_state(pre_settled_particle_state)
        pre_settled_source_sha256 = _sha(pre_settled_particle_state)
    else:
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
            particle_contact_offset_m=particle_contact_offset_m,
            particle_width_m=particle_width_m,
            diffuse_color=diffuse_color,
            opacity=opacity,
            roughness=roughness,
        ),
        encoding="utf-8",
    )
    qualification = output / "qualification.usda"
    qualification.write_text(_qualification_usda(), encoding="utf-8")
    points_path = _write_json(output / "initial_particle_state.json", points)
    candidates = [
        {
            "candidate_id": "c01",
            "rim_offset_x_m": 0.000,
            "rim_gap_m": 0.010,
            "tilt_deg": -105.0,
            "dwell_seconds": 3.0,
        },
        {
            "candidate_id": "c02",
            "rim_offset_x_m": -0.010,
            "rim_gap_m": 0.010,
            "tilt_deg": -105.0,
            "dwell_seconds": 3.0,
        },
        {
            "candidate_id": "c03",
            "rim_offset_x_m": 0.000,
            "rim_gap_m": 0.010,
            "tilt_deg": -115.0,
            "dwell_seconds": 3.0,
        },
        {
            "candidate_id": "c04",
            "rim_offset_x_m": -0.010,
            "rim_gap_m": 0.010,
            "tilt_deg": -115.0,
            "dwell_seconds": 3.0,
        },
    ]
    profile = {
        "schema_version": (
            "aan.gpu_pbd_transfer_fixture.v2"
            if target_settled_fill_ratio is not None
            else "aan.gpu_pbd_transfer_fixture.v1"
        ),
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
            "particle_contact_offset_m": particle_contact_offset_m,
            "selection": "minimum_promoted_endpoint_particle_contact_offset",
            "rest_offset_m": 0.0,
            "max_velocity_m_s": 0.3,
            "particle_width_m": particle_width_m,
            "initial_particle_state": points_path.name,
            "initial_particle_state_sha256": _sha(points_path),
            "initial_state_kind": (
                "pre_settled_world_space"
                if pre_settled_particle_state is not None
                else "deterministic_packed_world_space"
            ),
            "appearance": {
                "reference": "LabUtopia inputs/usd/scene/liquid_0812/test.usd",
                "shader": "UsdPreviewSurface",
                "diffuse_color": list(diffuse_color),
                "ior": 1.333,
                "opacity": opacity,
                "roughness": roughness,
                "extra_lights_or_volume_materials_added": False,
            },
        },
        "trajectory_protocol": {
            "physics_hz": 120,
            "settle_seconds": 2.0,
            "lift_seconds": 2.0,
            "lateral_approach_seconds": 2.0,
            "pretilt_degrees": -20.0,
            "pretilt_seconds": 0.5,
            "tilt_and_approach_seconds": 2.0,
            "retreat_seconds": 1.0,
            "upright_seconds": 0.5,
            "return_seconds": 1.0,
            "final_settle_seconds": 2.0,
            "high_root_z_m": 0.2,
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
            "minimum_mean_rtx_fps": (
                20.0 if target_settled_fill_ratio is not None else 40.0
            ),
            "target_mean_rtx_fps": (
                30.0 if target_settled_fill_ratio is not None else 40.0
            ),
        },
        "claim_boundary": "Prescribed kinematic transfer feasibility only; no robot, policy, benchmark, or 90 percent completion claim.",
    }
    if target_settled_fill_ratio is not None:
        profile["liquid_parameters"].update(
            {
                "target_settled_fill_ratio": target_settled_fill_ratio,
                "settled_fill_ratio_tolerance": settled_fill_ratio_tolerance,
                "initial_packing_fill_ratio": packing_fill_ratio,
                "particle_parameter_selection": particle_parameter_selection,
            }
        )
    if pre_settled_source_sha256 is not None:
        profile["liquid_parameters"]["pre_settled_source_sha256"] = (
            pre_settled_source_sha256
        )
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
    parser.add_argument("--target-settled-fill-ratio", type=float)
    parser.add_argument("--settled-fill-ratio-tolerance", type=float, default=0.05)
    parser.add_argument("--initial-packing-fill-ratio", type=float)
    parser.add_argument("--pre-settled-particle-state", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build_fixture(
                source_package=args.source_package,
                target_package=args.target_package,
                output=args.out,
                target_settled_fill_ratio=args.target_settled_fill_ratio,
                settled_fill_ratio_tolerance=args.settled_fill_ratio_tolerance,
                initial_packing_fill_ratio=args.initial_packing_fill_ratio,
                pre_settled_particle_state=args.pre_settled_particle_state,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
