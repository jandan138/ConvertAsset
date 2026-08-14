#!/usr/bin/env python3
"""Build an Isaac 4.1 static-retention fixture for one container package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
from typing import Any


PARTICLE_COUNT = 548
INNER_RADIUS_M = 0.019185
FLOOR_Z_M = 0.011705
PARTICLE_CONTACT_OFFSET_M = 0.005
DEFAULT_CONTAINER_CONTACT_OFFSET_M = 0.001
INITIAL_CLEARANCE_MARGIN_M = 0.0005


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def _write_json(path: Path, payload: Any) -> Path:
    return _write(path, json.dumps(payload, indent=2, sort_keys=True))


def authored_points(
    count: int = PARTICLE_COUNT,
    *,
    container_contact_offset_m: float = DEFAULT_CONTAINER_CONTACT_OFFSET_M,
) -> list[list[float]]:
    """Pack 0812-sized particles above the measured cylinder floor."""

    points: list[list[float]] = []
    # Measured nearest-neighbour pitch in liquid_0812/test.usd is about
    # 5.82 mm.  A denser 5.2 mm packing creates a large initial PBD overlap
    # impulse and can eject particles through otherwise valid thin walls.
    spacing = 0.00582
    radial_limit = (
        INNER_RADIUS_M
        - PARTICLE_CONTACT_OFFSET_M
        - container_contact_offset_m
        - INITIAL_CLEARANCE_MARGIN_M
    )
    if radial_limit <= 0:
        raise ValueError("combined contact offsets leave no usable cavity radius")
    z = FLOOR_Z_M + PARTICLE_CONTACT_OFFSET_M
    layer = 0
    while len(points) < count:
        phase = 0.5 * spacing if layer % 2 else 0.0
        candidates = [
            (ix * spacing + phase, iy * spacing)
            for ix in range(-4, 5)
            for iy in range(-4, 5)
            if math.hypot(ix * spacing + phase, iy * spacing) <= radial_limit
        ]
        candidates.sort(key=lambda point: (math.hypot(*point), point[0], point[1]))
        for x, y in candidates:
            points.append([round(x, 7), round(y, 7), round(z, 7)])
            if len(points) == count:
                return points
        layer += 1
        z += spacing
    return points


def remap_reference_particle_cloud(
    reference_points: list[list[float]],
    *,
    source_center_xy_m: tuple[float, float],
    target_radial_limit_m: float,
) -> tuple[list[list[float]], dict[str, Any]]:
    """Fit a settled reference cloud while preserving its occupied volume.

    The radial fit alone would compress particle density.  Compensating in Z
    keeps the affine transform volume-preserving and uses the cylinder's tall
    cavity instead of introducing an overlapping, high-pressure initial state.
    """

    if not reference_points:
        raise ValueError("reference particle cloud is empty")
    cx, cy = source_center_xy_m
    source_radius = max(
        math.hypot(point[0] - cx, point[1] - cy)
        for point in reference_points
    )
    if source_radius <= 0 or target_radial_limit_m <= 0:
        raise ValueError("source and target particle radii must be positive")
    # Keep rounded USDA coordinates strictly inside the requested limit.
    effective_radial_limit = max(0.0, target_radial_limit_m - 1e-7)
    radial_scale = effective_radial_limit / source_radius
    vertical_scale = 1.0 / (radial_scale * radial_scale)
    source_floor = min(point[2] for point in reference_points)
    target_floor = FLOOR_Z_M + PARTICLE_CONTACT_OFFSET_M
    remapped = [
        [
            round((point[0] - cx) * radial_scale, 7),
            round((point[1] - cy) * radial_scale, 7),
            round(target_floor + (point[2] - source_floor) * vertical_scale, 7),
        ]
        for point in reference_points
    ]
    if max(point[2] for point in remapped) >= 0.27824 - PARTICLE_CONTACT_OFFSET_M:
        raise ValueError("volume-preserving reference cloud does not fit below rim")
    return remapped, {
        "mapping": "volume_preserving_radial_fit",
        "source_center_xy_m": [cx, cy],
        "source_radial_extent_m": source_radius,
        "target_radial_limit_m": target_radial_limit_m,
        "effective_radial_limit_m": effective_radial_limit,
        "radial_scale": radial_scale,
        "vertical_scale": vertical_scale,
        "source_floor_z_m": source_floor,
        "target_floor_z_m": target_floor,
    }


def _vec3_array(values: list[list[float]]) -> str:
    return ", ".join(f"({x:.7g}, {y:.7g}, {z:.7g})" for x, y, z in values)


def _component_usda(*, entry_prim: str, points: list[list[float]]) -> str:
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
    def Xform "Container" (
        prepend apiSchemas = ["PhysicsRigidBodyAPI"]
        prepend references = @deps/container/asset.usd@<{entry_prim}>
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
        token outputs:surface.connect = </World/LiquidMaterial/PreviewSurface.outputs:surface>
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
        rel material:binding = </World/LiquidMaterial>
        rel physxParticle:particleSystem = </World/ParticleSystem>
        point3f[] physxParticle:simulationPoints = [{positions}]
        point3f[] points = [{positions}]
        vector3f[] velocities = [{zeros}]
        float[] widths = [{widths}]
        token visibility = "invisible"
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
        float3 xformOp:scale = (0.5, 0.5, 0.02)
        double3 xformOp:translate = (0, 0, -0.01)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
    }
    def Camera "QualificationCamera"
    {
        float focalLength = 45
        float horizontalAperture = 20.955
        matrix4d xformOp:transform = ((0.8637789009, 0.5038710255, 0, 0), (-0.0805565346, 0.1380969165, 0.9871372176, 0), (0.4973898422, -0.8526683009, 0.1598753064, 0), (0.28, -0.48, 0.22, 1))
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
    container_package: Path,
    output: Path,
    particle_count: int = PARTICLE_COUNT,
    particle_seed: Path | None = None,
    particle_seed_bounds: Path | None = None,
) -> dict[str, Any]:
    container_package = container_package.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite fixture: {output}")
    entrypoint = container_package / "asset.usd"
    profile_path = container_package / "gpu_pbd_static_container_profile.json"
    if not entrypoint.is_file() or not profile_path.is_file():
        raise FileNotFoundError("container package is missing asset.usd or profile")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    entry_prim = str(profile["entry_prim"])
    container_contact_offset_m = float(
        profile["collision"].get(
            "contact_offset_m", DEFAULT_CONTAINER_CONTACT_OFFSET_M
        )
    )
    output.mkdir(parents=True)
    shutil.copytree(container_package, output / "deps/container")
    initial_state: dict[str, Any]
    if particle_seed is not None:
        if particle_seed_bounds is None:
            raise ValueError("particle_seed_bounds is required with particle_seed")
        particle_seed = particle_seed.resolve()
        particle_seed_bounds = particle_seed_bounds.resolve()
        seed_payload = json.loads(particle_seed.read_text(encoding="utf-8"))
        bounds_payload = json.loads(
            particle_seed_bounds.read_text(encoding="utf-8")
        )
        bounds_payload = bounds_payload.get("containment_bounds", bounds_payload)
        source_center = bounds_payload["center_xy_m"]
        radial_limit = (
            INNER_RADIUS_M
            - PARTICLE_CONTACT_OFFSET_M
            - container_contact_offset_m
            - INITIAL_CLEARANCE_MARGIN_M
        )
        points, transform = remap_reference_particle_cloud(
            seed_payload["positions"],
            source_center_xy_m=(float(source_center[0]), float(source_center[1])),
            target_radial_limit_m=radial_limit,
        )
        initial_state = {
            "kind": "normalized_reference_particle_cloud",
            "source": str(particle_seed),
            "source_sha256": _sha(particle_seed),
            "source_bounds": str(particle_seed_bounds),
            "source_bounds_sha256": _sha(particle_seed_bounds),
            "transform": transform,
        }
    else:
        points = authored_points(
            count=particle_count,
            container_contact_offset_m=container_contact_offset_m,
        )
        initial_state = {"kind": "deterministic_reference_pitch_lattice"}
    if max(point[2] for point in points) >= 0.27824 - PARTICLE_CONTACT_OFFSET_M:
        raise ValueError("548 reference particles do not fit below the measured rim")
    points_path = _write_json(output / "authored_particle_points.json", points)
    component = _write(
        output / "component.usda",
        _component_usda(entry_prim=entry_prim, points=points),
    )
    qualification = _write(output / "qualification.usda", _qualification_usda())
    fixture = {
        "schema_version": "aan.gpu_pbd_static_fixture.v1",
        "container_package": str(container_package),
        "container_entrypoint_sha256": _sha(entrypoint),
        "container_profile_sha256": _sha(profile_path),
        "entry_prim": entry_prim,
        "container_actor_mode": "kinematic_rigid_body",
        "collision_mesh_prim": (
            profile["collision"].get("mesh_prim")
            or profile["collision"]["root_prim"]
        ),
        "particle_count": len(points),
        "particle_parameters": {
            "source": "LabUtopia inputs/usd/scene/liquid_0812/test.usd",
            "initial_state": initial_state,
            "particle_contact_offset_m": PARTICLE_CONTACT_OFFSET_M,
            "container_contact_offset_m": container_contact_offset_m,
            "initial_clearance_margin_m": INITIAL_CLEARANCE_MARGIN_M,
            "rest_offset_m": 0.0,
            "authored_nearest_neighbor_pitch_m": 0.00582,
            "solver_position_iteration_count": "isaac41_default",
        },
        "cavity": {
            "radius_m": INNER_RADIUS_M,
            "floor_z_m": FLOOR_Z_M,
        },
        "containment_bounds": {
            "center_xy_m": [0.0, 0.0],
            "radius_m": INNER_RADIUS_M,
            "floor_z_m": FLOOR_Z_M,
            "rim_z_m": 0.27824,
            "support_z_m": 0.0,
        },
        "files": {
            "component": {"path": component.name, "sha256": _sha(component)},
            "qualification": {
                "path": qualification.name,
                "sha256": _sha(qualification),
            },
            "points": {"path": points_path.name, "sha256": _sha(points_path)},
        },
        "claim_boundary": (
            "Static GPU-PBD qualification fixture only; no pour or robot claim."
        ),
    }
    _write_json(output / "fixture_profile.json", fixture)
    return {
        "status": "candidate",
        "fixture": str(output),
        "particle_count": len(points),
        "qualification": str(qualification),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container-package", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--particle-count", type=int, default=PARTICLE_COUNT)
    parser.add_argument("--particle-seed", type=Path)
    parser.add_argument("--particle-seed-bounds", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build_fixture(
                container_package=args.container_package,
                output=args.out,
                particle_count=args.particle_count,
                particle_seed=args.particle_seed,
                particle_seed_bounds=args.particle_seed_bounds,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
