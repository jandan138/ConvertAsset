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
    inner_radius_m: float = INNER_RADIUS_M,
    floor_z_m: float = FLOOR_Z_M,
    particle_contact_offset_m: float = PARTICLE_CONTACT_OFFSET_M,
) -> list[list[float]]:
    """Pack 0812-sized particles above the measured cylinder floor."""

    points: list[list[float]] = []
    # Measured nearest-neighbour pitch in liquid_0812/test.usd is about
    # 5.82 mm.  A denser 5.2 mm packing creates a large initial PBD overlap
    # impulse and can eject particles through otherwise valid thin walls.
    spacing = 0.00582
    radial_limit = (
        inner_radius_m
        - particle_contact_offset_m
        - container_contact_offset_m
        - INITIAL_CLEARANCE_MARGIN_M
    )
    if radial_limit <= 0:
        raise ValueError("combined contact offsets leave no usable cavity radius")
    z = floor_z_m + particle_contact_offset_m
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
    target_floor_z_m: float = FLOOR_Z_M,
    target_rim_z_m: float = 0.27824,
    particle_contact_offset_m: float = PARTICLE_CONTACT_OFFSET_M,
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
    target_floor = target_floor_z_m + particle_contact_offset_m
    remapped = [
        [
            round((point[0] - cx) * radial_scale, 7),
            round((point[1] - cy) * radial_scale, 7),
            round(target_floor + (point[2] - source_floor) * vertical_scale, 7),
        ]
        for point in reference_points
    ]
    if max(point[2] for point in remapped) >= (
        target_rim_z_m - particle_contact_offset_m
    ):
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


def translate_reference_particle_cloud(
    reference_points: list[list[float]],
    *,
    source_center_xy_m: tuple[float, float],
    target_center_xy_m: tuple[float, float],
    target_floor_z_m: float,
    target_cavity_radius_m: float,
    target_rim_z_m: float,
    particle_contact_offset_m: float = PARTICLE_CONTACT_OFFSET_M,
) -> tuple[list[list[float]], dict[str, Any]]:
    """Move an already-settled cloud without introducing new PBD overlap."""

    if not reference_points:
        raise ValueError("reference particle cloud is empty")
    source_x, source_y = source_center_xy_m
    target_x, target_y = target_center_xy_m
    source_floor = min(point[2] for point in reference_points)
    source_radius = max(
        math.hypot(point[0] - source_x, point[1] - source_y)
        for point in reference_points
    )
    source_height = max(point[2] for point in reference_points) - source_floor
    if source_radius > target_cavity_radius_m:
        raise ValueError("settled reference cloud does not fit target cavity radius")
    target_floor = target_floor_z_m + particle_contact_offset_m
    if target_floor + source_height >= target_rim_z_m:
        raise ValueError("settled reference cloud does not fit below target rim")
    translated = [
        [
            target_x + point[0] - source_x,
            target_y + point[1] - source_y,
            target_floor + point[2] - source_floor,
        ]
        for point in reference_points
    ]
    return translated, {
        "mapping": "rigid_translate_settled_cloud",
        "source_center_xy_m": [source_x, source_y],
        "target_center_xy_m": [target_x, target_y],
        "source_radial_extent_m": source_radius,
        "target_cavity_radius_m": target_cavity_radius_m,
        "source_floor_z_m": source_floor,
        "target_floor_z_m": target_floor,
        "pairwise_spacing_preserved": True,
    }


def _vec3_array(values: list[list[float]]) -> str:
    return ", ".join(f"({x:.7g}, {y:.7g}, {z:.7g})" for x, y, z in values)


def _component_usda(
    *,
    entry_prim: str,
    points: list[list[float]],
    actor_mode: str,
    particle_contact_offset_m: float = PARTICLE_CONTACT_OFFSET_M,
) -> str:
    if actor_mode not in ("kinematic_rigid_body", "dynamic_rigid_body"):
        raise ValueError(f"unsupported container actor mode: {actor_mode}")
    kinematic = 1 if actor_mode == "kinematic_rigid_body" else 0
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
        bool physics:kinematicEnabled = {kinematic}
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
    particle_seed_usd: Path | None = None,
    particle_seed_prim: str = "/World/ParticleSet",
    particle_seed_bounds: Path | None = None,
    actor_mode: str = "kinematic_rigid_body",
    particle_seed_mapping: str = "volume_preserving_radial_fit",
    particle_contact_offset_m: float = PARTICLE_CONTACT_OFFSET_M,
) -> dict[str, Any]:
    container_package = container_package.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite fixture: {output}")
    if not math.isfinite(particle_contact_offset_m) or particle_contact_offset_m <= 0:
        raise ValueError("particle contact offset must be finite and positive")
    entrypoint = container_package / "asset.usd"
    profile_path = container_package / "gpu_pbd_static_container_profile.json"
    if not entrypoint.is_file() or not profile_path.is_file():
        raise FileNotFoundError("container package is missing asset.usd or profile")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    entry_prim = str(profile["entry_prim"])
    cavity = profile.get("cavity") or {
        "center_xy_m": [0.0, 0.0],
        "radius_m": INNER_RADIUS_M,
        "floor_z_m": FLOOR_Z_M,
        "rim_z_m": 0.27824,
        "support_z_m": 0.0,
    }
    center_xy_m = [float(value) for value in cavity["center_xy_m"]]
    inner_radius_m = float(cavity["radius_m"])
    floor_z_m = float(cavity["floor_z_m"])
    rim_z_m = float(cavity["rim_z_m"])
    support_z_m = float(cavity["support_z_m"])
    container_contact_offset_m = float(
        profile["collision"].get(
            "contact_offset_m", DEFAULT_CONTAINER_CONTACT_OFFSET_M
        )
    )
    output.mkdir(parents=True)
    shutil.copytree(container_package, output / "deps/container")
    initial_state: dict[str, Any]
    if particle_seed is not None and particle_seed_usd is not None:
        raise ValueError("particle_seed and particle_seed_usd are mutually exclusive")
    if particle_seed is not None or particle_seed_usd is not None:
        if particle_seed_bounds is None:
            raise ValueError("particle_seed_bounds is required with a particle seed")
        particle_seed_bounds = particle_seed_bounds.resolve()
        if particle_seed_usd is not None:
            from pxr import Usd, UsdGeom

            particle_seed_usd = particle_seed_usd.resolve()
            seed_stage = Usd.Stage.Open(str(particle_seed_usd))
            if seed_stage is None:
                raise ValueError(f"cannot open particle seed USD: {particle_seed_usd}")
            seed_points = UsdGeom.Points(
                seed_stage.GetPrimAtPath(particle_seed_prim)
            )
            if not seed_points.GetPrim().IsValid():
                raise ValueError(
                    f"particle seed prim is not Points: {particle_seed_prim}"
                )
            seed_positions = [
                [float(value) for value in point]
                for point in (seed_points.GetPointsAttr().Get() or [])
            ]
            seed_source = particle_seed_usd
            seed_kind = "source_authored_particle_cloud"
        else:
            assert particle_seed is not None
            particle_seed = particle_seed.resolve()
            seed_payload = json.loads(particle_seed.read_text(encoding="utf-8"))
            seed_positions = (
                seed_payload["positions"]
                if isinstance(seed_payload, dict)
                else seed_payload
            )
            seed_source = particle_seed
            seed_kind = "normalized_reference_particle_cloud"
        bounds_payload = json.loads(
            particle_seed_bounds.read_text(encoding="utf-8")
        )
        bounds_payload = bounds_payload.get("containment_bounds", bounds_payload)
        source_center = bounds_payload["center_xy_m"]
        if particle_seed_mapping == "volume_preserving_radial_fit":
            radial_limit = (
                inner_radius_m
                - particle_contact_offset_m
                - container_contact_offset_m
                - INITIAL_CLEARANCE_MARGIN_M
            )
            points, transform = remap_reference_particle_cloud(
                seed_positions,
                source_center_xy_m=(float(source_center[0]), float(source_center[1])),
                target_radial_limit_m=radial_limit,
                target_floor_z_m=floor_z_m,
                target_rim_z_m=rim_z_m,
                particle_contact_offset_m=particle_contact_offset_m,
            )
        elif particle_seed_mapping in (
            "rigid_translate_settled_cloud",
            "rigid_translate_authored_cloud",
        ):
            points, transform = translate_reference_particle_cloud(
                seed_positions,
                source_center_xy_m=(float(source_center[0]), float(source_center[1])),
                target_center_xy_m=(center_xy_m[0], center_xy_m[1]),
                target_floor_z_m=floor_z_m,
                target_cavity_radius_m=inner_radius_m,
                target_rim_z_m=rim_z_m,
                particle_contact_offset_m=particle_contact_offset_m,
            )
        else:
            raise ValueError(
                f"unsupported particle seed mapping: {particle_seed_mapping}"
            )
        initial_state = {
            "kind": seed_kind,
            "source": str(seed_source),
            "source_sha256": _sha(seed_source),
            "source_bounds": str(particle_seed_bounds),
            "source_bounds_sha256": _sha(particle_seed_bounds),
            "transform": transform,
        }
        if particle_seed_usd is not None:
            initial_state["source_prim"] = particle_seed_prim
    else:
        points = authored_points(
            count=particle_count,
            container_contact_offset_m=container_contact_offset_m,
            inner_radius_m=inner_radius_m,
            floor_z_m=floor_z_m,
            particle_contact_offset_m=particle_contact_offset_m,
        )
        initial_state = {"kind": "deterministic_reference_pitch_lattice"}
    if max(point[2] for point in points) >= rim_z_m - particle_contact_offset_m:
        raise ValueError("reference particles do not fit below the measured rim")
    points_path = _write_json(output / "authored_particle_points.json", points)
    component = _write(
        output / "component.usda",
        _component_usda(
            entry_prim=entry_prim,
            points=points,
            actor_mode=actor_mode,
            particle_contact_offset_m=particle_contact_offset_m,
        ),
    )
    qualification = _write(output / "qualification.usda", _qualification_usda())
    fixture = {
        "schema_version": "aan.gpu_pbd_static_fixture.v1",
        "container_package": str(container_package),
        "container_entrypoint_sha256": _sha(entrypoint),
        "container_profile_sha256": _sha(profile_path),
        "entry_prim": entry_prim,
        "container_actor_mode": actor_mode,
        "collision_mesh_prim": (
            profile["collision"].get("mesh_prim")
            or profile["collision"]["root_prim"]
        ),
        "particle_count": len(points),
        "particle_parameters": {
            "source": "LabUtopia inputs/usd/scene/liquid_0812/test.usd",
            "initial_state": initial_state,
            "particle_contact_offset_m": particle_contact_offset_m,
            "container_contact_offset_m": container_contact_offset_m,
            "initial_clearance_margin_m": INITIAL_CLEARANCE_MARGIN_M,
            "rest_offset_m": 0.0,
            "authored_nearest_neighbor_pitch_m": 0.00582,
            "solver_position_iteration_count": "isaac41_default",
        },
        "cavity": {
            "radius_m": inner_radius_m,
            "floor_z_m": floor_z_m,
        },
        "containment_bounds": {
            "center_xy_m": center_xy_m,
            "radius_m": inner_radius_m,
            "floor_z_m": floor_z_m,
            "rim_z_m": rim_z_m,
            "support_z_m": support_z_m,
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
    parser.add_argument("--particle-seed-usd", type=Path)
    parser.add_argument("--particle-seed-prim", default="/World/ParticleSet")
    parser.add_argument("--particle-seed-bounds", type=Path)
    parser.add_argument(
        "--particle-contact-offset-m",
        type=float,
        default=PARTICLE_CONTACT_OFFSET_M,
    )
    parser.add_argument(
        "--actor-mode",
        choices=("kinematic_rigid_body", "dynamic_rigid_body"),
        default="kinematic_rigid_body",
    )
    parser.add_argument(
        "--particle-seed-mapping",
        choices=(
            "volume_preserving_radial_fit",
            "rigid_translate_settled_cloud",
            "rigid_translate_authored_cloud",
        ),
        default="volume_preserving_radial_fit",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            build_fixture(
                container_package=args.container_package,
                output=args.out,
                particle_count=args.particle_count,
                particle_seed=args.particle_seed,
                particle_seed_usd=args.particle_seed_usd,
                particle_seed_prim=args.particle_seed_prim,
                particle_seed_bounds=args.particle_seed_bounds,
                actor_mode=args.actor_mode,
                particle_seed_mapping=args.particle_seed_mapping,
                particle_contact_offset_m=args.particle_contact_offset_m,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
