#!/usr/bin/env python3
"""Build Task 02 r8.1 candidates with visible partitioned cylinder collision."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
from typing import TYPE_CHECKING, Any

from convert_asset.asset_application_normalizer.interactive_fluid_scene import (
    load_interactive_fluid_scene_profile,
)

if TYPE_CHECKING:
    from pxr import Usd, UsdGeom


COMPONENT_ROOT = "/World/FluidWorkcell"
SOURCE = COMPONENT_ROOT + "/SourceContainer"
TARGET = COMPONENT_ROOT + "/TargetContainer"
PARTICLE_SYSTEM = COMPONENT_ROOT + "/ParticleSystem"
PARTICLES = COMPONENT_ROOT + "/ParticleSet"
SOURCE_XYZ = (0.16, -0.15, 0.0)
TARGET_XYZ = (-0.16, -0.17, 0.0)
SOURCE_BODY = SOURCE + "/Visual/Source/Hollow_Body/Hollow_Body_Mesh_002"
SOURCE_BOTTOM = SOURCE + "/Visual/Source/Closed_Inner_Bottom/Cylinder_006"
TARGET_BODY = (
    TARGET + "/Visual/Source/Beaker_Hollow_Body/Beaker_Hollow_Body_Mesh"
)
PARTITION_COUNTS = (12, 24, 48)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _copy_package(source: Path, destination: Path) -> None:
    if not (source / "asset.usd").is_file():
        raise FileNotFoundError(f"missing source-bound asset.usd: {source}")
    shutil.copytree(source, destination, dirs_exist_ok=True)


def authored_points(count: int = 548) -> list[list[float]]:
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
                if math.hypot(x, y) <= radial_limit:
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


def partition_face_indices(mesh: UsdGeom.Mesh, count: int) -> list[list[int]]:
    """Assign every source face to one angular sector exactly once."""
    if count not in PARTITION_COUNTS:
        raise ValueError(f"partition count must be one of {PARTITION_COUNTS}")
    points = mesh.GetPointsAttr().Get() or []
    counts = mesh.GetFaceVertexCountsAttr().Get() or []
    indices = mesh.GetFaceVertexIndicesAttr().Get() or []
    sectors: list[list[int]] = [[] for _ in range(count)]
    offset = 0
    for face_index, face_size in enumerate(counts):
        face = indices[offset : offset + face_size]
        offset += face_size
        x = sum(float(points[index][0]) for index in face)
        y = sum(float(points[index][1]) for index in face)
        angle = math.atan2(y, x) % (2.0 * math.pi)
        sector = min(int(angle / (2.0 * math.pi) * count), count - 1)
        sectors[sector].append(face_index)
    if any(not sector for sector in sectors):
        raise ValueError("partition produced an empty visible sector")
    flattened = [index for sector in sectors for index in sector]
    if sorted(flattened) != list(range(len(counts))):
        raise ValueError("partition face coverage is not exact")
    return sectors


def _copy_selected_faces(
    source: UsdGeom.Mesh,
    destination: UsdGeom.Mesh,
    face_indices: list[int],
) -> None:
    from pxr import Sdf, UsdGeom

    points = source.GetPointsAttr().Get() or []
    counts = source.GetFaceVertexCountsAttr().Get() or []
    indices = source.GetFaceVertexIndicesAttr().Get() or []
    offsets: list[int] = []
    offset = 0
    for size in counts:
        offsets.append(offset)
        offset += size
    used = sorted(
        {
            index
            for face_index in face_indices
            for index in indices[
                offsets[face_index] : offsets[face_index] + counts[face_index]
            ]
        }
    )
    remap = {old: new for new, old in enumerate(used)}
    destination.GetPointsAttr().Set([points[index] for index in used])
    destination.GetFaceVertexCountsAttr().Set([counts[index] for index in face_indices])
    destination.GetFaceVertexIndicesAttr().Set(
        [
            remap[index]
            for face_index in face_indices
            for index in indices[
                offsets[face_index] : offsets[face_index] + counts[face_index]
            ]
        ]
    )
    source_normals = source.GetNormalsAttr().Get() or []
    if source_normals:
        interpolation = source.GetNormalsInterpolation()
        if interpolation == UsdGeom.Tokens.faceVarying:
            destination.GetNormalsAttr().Set(
                [
                    source_normals[index]
                    for face_index in face_indices
                    for index in range(
                        offsets[face_index],
                        offsets[face_index] + counts[face_index],
                    )
                ]
            )
        elif interpolation == UsdGeom.Tokens.vertex:
            destination.GetNormalsAttr().Set([source_normals[index] for index in used])
        elif interpolation == UsdGeom.Tokens.uniform:
            destination.GetNormalsAttr().Set(
                [source_normals[index] for index in face_indices]
            )
        elif interpolation == UsdGeom.Tokens.constant:
            destination.GetNormalsAttr().Set(source_normals)
        else:
            raise ValueError(f"unsupported normal interpolation: {interpolation}")
        destination.SetNormalsInterpolation(interpolation)
    destination.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
    destination.GetOrientationAttr().Set(source.GetOrientationAttr().Get())
    destination.GetDoubleSidedAttr().Set(source.GetDoubleSidedAttr().Get())
    destination.GetExtentAttr().Set(UsdGeom.Mesh.ComputeExtent(destination.GetPointsAttr().Get()))
    destination.GetPrim().CreateAttribute(
        "aan:sourceFaceIndices", Sdf.ValueTypeNames.IntArray, custom=True
    ).Set(face_indices)


def _apply_convex_collision(prim: Usd.Prim, *, max_hulls: int = 8) -> None:
    from pxr import Sdf, UsdPhysics

    UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
    UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(
        UsdPhysics.Tokens.convexDecomposition
    )
    prim.CreateAttribute(
        "physxConvexDecompositionCollision:errorPercentage",
        Sdf.ValueTypeNames.Float,
    ).Set(10.0)
    prim.CreateAttribute(
        "physxConvexDecompositionCollision:hullVertexLimit",
        Sdf.ValueTypeNames.UInt,
    ).Set(32)
    prim.CreateAttribute(
        "physxConvexDecompositionCollision:maxConvexHulls",
        Sdf.ValueTypeNames.UInt,
    ).Set(max_hulls)
    prim.CreateAttribute(
        "physxConvexDecompositionCollision:minThickness",
        Sdf.ValueTypeNames.Float,
    ).Set(0.001)
    prim.CreateAttribute(
        "physxConvexDecompositionCollision:shrinkWrap",
        Sdf.ValueTypeNames.Bool,
    ).Set(True)
    prim.CreateAttribute(
        "physxConvexDecompositionCollision:voxelResolution",
        Sdf.ValueTypeNames.UInt,
    ).Set(50000)


def _author_component(
    path: Path,
    cylinder_asset: Path,
    beaker_asset: Path,
    points: list[list[float]],
    partition_count: int,
) -> tuple[list[str], list[list[int]]]:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    world = UsdGeom.Xform.Define(stage, "/World").GetPrim()
    stage.SetDefaultPrim(world)
    UsdGeom.Xform.Define(stage, COMPONENT_ROOT)
    source = UsdGeom.Xform.Define(stage, SOURCE)
    source.GetPrim().GetReferences().AddReference(
        "deps/source_container/asset.usd", "/World/GraduatedCylinder250ml"
    )
    source.AddTranslateOp().Set(Gf.Vec3d(*SOURCE_XYZ))
    target = UsdGeom.Xform.Define(stage, TARGET)
    target.GetPrim().GetReferences().AddReference(
        "deps/target_container/asset.usd", "/World/Beaker325ml"
    )
    target.AddTranslateOp().Set(Gf.Vec3d(*TARGET_XYZ))
    for root in (SOURCE, TARGET):
        proxy = stage.OverridePrim(root + "/__aan_collision_proxy")
        proxy.CreateAttribute("physics:collisionEnabled", Sdf.ValueTypeNames.Bool).Set(False)
        for child in ("bottom", "wall_neg_x", "wall_neg_y", "wall_pos_x", "wall_pos_y"):
            stage.OverridePrim(f"{root}/__aan_collision_proxy/{child}").CreateAttribute(
                "physics:collisionEnabled", Sdf.ValueTypeNames.Bool
            ).Set(False)

    source_stage = Usd.Stage.Open(str(cylinder_asset))
    source_mesh = UsdGeom.Mesh(
        source_stage.GetPrimAtPath(
            "/World/GraduatedCylinder250ml/Visual/Source/Hollow_Body/"
            "Hollow_Body_Mesh_002"
        )
    )
    sectors = partition_face_indices(source_mesh, partition_count)
    original = stage.OverridePrim(SOURCE_BODY)
    original.CreateAttribute("visibility", Sdf.ValueTypeNames.Token).Set("invisible")
    original.CreateAttribute("physics:collisionEnabled", Sdf.ValueTypeNames.Bool).Set(False)
    partition_paths: list[str] = []
    partition_root = SOURCE + "/Visual/Source/Hollow_Body/VisibleCollisionPartitions"
    UsdGeom.Scope.Define(stage, partition_root)
    material = Sdf.Path(
        SOURCE + "/Visual/Source/_materials/USD_Glass_002"
    )
    for index, face_indices in enumerate(sectors):
        prim_path = f"{partition_root}/sector_{index:03d}"
        mesh = UsdGeom.Mesh.Define(stage, prim_path)
        _copy_selected_faces(source_mesh, mesh, face_indices)
        mesh.GetPrim().CreateRelationship("material:binding").SetTargets([material])
        _apply_convex_collision(mesh.GetPrim())
        partition_paths.append(prim_path)

    _apply_convex_collision(stage.OverridePrim(SOURCE_BOTTOM), max_hulls=8)
    _apply_convex_collision(stage.OverridePrim(TARGET_BODY), max_hulls=32)

    particle_system = stage.DefinePrim(PARTICLE_SYSTEM, "PhysxParticleSystem")
    particle_system.SetMetadata(
        "apiSchemas",
        Sdf.TokenListOp.Create(prependedItems=["PhysxParticleIsosurfaceAPI"]),
    )
    particle_system.CreateAttribute("particleContactOffset", Sdf.ValueTypeNames.Float).Set(0.005)
    particle_system.CreateAttribute("restOffset", Sdf.ValueTypeNames.Float).Set(0.0)
    particle_system.CreateAttribute("maxVelocity", Sdf.ValueTypeNames.Float).Set(1.5)
    particle_system.CreateAttribute(
        "physxParticleIsosurface:gridFilteringPasses", Sdf.ValueTypeNames.Int
    ).Set(1)
    particle_system.CreateAttribute(
        "physxParticleIsosurface:gridSmoothingRadius", Sdf.ValueTypeNames.Float
    ).Set(0.010)
    particle_system.CreateAttribute(
        "physxParticleIsosurface:meshSmoothingPasses", Sdf.ValueTypeNames.Int
    ).Set(1)
    particle_system.CreateAttribute(
        "physxParticleIsosurface:surfaceDistance", Sdf.ValueTypeNames.Float
    ).Set(0.008)
    liquid_material = UsdShade.Material.Define(stage, COMPONENT_ROOT + "/LiquidMaterial")
    shader = UsdShade.Shader.Define(
        stage, COMPONENT_ROOT + "/LiquidMaterial/PreviewSurface"
    )
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.20, 0.58, 0.82)
    )
    shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.333)
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.18)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.06)
    liquid_material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface"
    )
    particles = UsdGeom.Points.Define(stage, PARTICLES)
    particles.GetPointsAttr().Set([Gf.Vec3f(*point) for point in points])
    particles.GetWidthsAttr().Set([0.005] * len(points))
    particles.GetVelocitiesAttr().Set([Gf.Vec3f(0) for _ in points])
    particles.GetVisibilityAttr().Set(UsdGeom.Tokens.invisible)
    particles.GetPrim().CreateRelationship("physxParticle:particleSystem").SetTargets(
        [Sdf.Path(PARTICLE_SYSTEM)]
    )
    particles.GetPrim().CreateAttribute("physxParticle:fluid", Sdf.ValueTypeNames.Bool).Set(True)
    particles.GetPrim().CreateAttribute(
        "physxParticle:selfCollision", Sdf.ValueTypeNames.Bool
    ).Set(True)
    particles.GetPrim().CreateAttribute(
        "physxParticle:particleGroup", Sdf.ValueTypeNames.Int
    ).Set(0)
    UsdPhysics.MassAPI.Apply(particles.GetPrim()).CreateMassAttr(0.00045)
    UsdShade.MaterialBindingAPI.Apply(particles.GetPrim()).Bind(liquid_material)
    particles.GetPrim().SetMetadata(
        "apiSchemas",
        Sdf.TokenListOp.Create(
            prependedItems=[
                "PhysxParticleSetAPI",
                "PhysicsMassAPI",
                "MaterialBindingAPI",
            ]
        ),
    )
    stage.GetRootLayer().Save()
    return partition_paths, sectors


def _entrypoint(path: Path, *, rate: int, qualification: bool) -> Path:
    support = '''
    def Cube "QualificationSupport" (
        prepend apiSchemas = ["PhysicsCollisionAPI"]
    )
    {
        double size = 1
        float3 xformOp:scale = (1.2, 0.7, 0.04)
        double3 xformOp:translate = (0, 0, -0.02)
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
    }
''' if qualification else ""
    path.write_text(
        f'''#usda 1.0
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
    def PhysicsScene "PhysicsScene"
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
''',
        encoding="utf-8",
    )
    return path


def _diagnostic_no_partitions(path: Path, qualification: Path) -> Path:
    """Write a negative-control scene that removes only the new partitions."""
    path.write_text(
        f'''#usda 1.0
(
    subLayers = [@{qualification.name}@]
)

over "World"
{{
    over "FluidWorkcell"
    {{
        over "SourceContainer"
        {{
            over "Visual"
            {{
                over "Source"
                {{
                    over "Hollow_Body"
                    {{
                        over "VisibleCollisionPartitions" (active = false)
                        {{
                        }}
                    }}
                }}
            }}
        }}
    }}
}}
''',
        encoding="utf-8",
    )
    return path


def build(
    *,
    cylinder_package: Path,
    beaker_package: Path,
    out: Path,
    partition_count: int,
) -> dict[str, Path]:
    from pxr import Usd, UsdGeom

    cylinder_package = cylinder_package.resolve()
    beaker_package = beaker_package.resolve()
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    _copy_package(cylinder_package, out / "deps/source_container")
    _copy_package(beaker_package, out / "deps/target_container")
    points = authored_points()
    points_path = _write_json(out / "authored_particle_points.json", points)
    component = out / "component.usda"
    partition_paths, sectors = _author_component(
        component,
        cylinder_package / "asset.usd",
        beaker_package / "asset.usd",
        points,
        partition_count,
    )
    qualification = _entrypoint(out / "qualification_30hz.usda", rate=30, qualification=True)
    consumer = _entrypoint(out / "consumer_60hz.usda", rate=60, qualification=False)
    diagnostic_no_partitions = _diagnostic_no_partitions(
        out / "diagnostic_no_partitions.usda", qualification
    )
    shutil.copy2(consumer, out / "asset.usd")
    mesh_records = [
        {
            "prim_path": path,
            "approximation": "convexDecomposition",
            "error_percentage": 10.0,
            "render_visible": True,
            "source_face_indices": sector,
        }
        for path, sector in zip(partition_paths, sectors)
    ]
    mesh_records.extend(
        [
            {
                "prim_path": SOURCE_BOTTOM,
                "approximation": "convexDecomposition",
                "error_percentage": 10.0,
                "render_visible": True,
                "source_face_indices": [],
            },
            {
                "prim_path": TARGET_BODY,
                "approximation": "convexDecomposition",
                "error_percentage": 10.0,
                "render_visible": True,
                "source_face_indices": [],
            },
        ]
    )
    profile_payload = {
        "schema_version": "aan.interactive_fluid_scene_profile.v2",
        "profile_id": f"scientific_workbench.task02.fluid.r8.1.p{partition_count}",
        "revision": "r8.1",
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
            "strategy": "visual_mesh_partitioned_convex_decomposition",
            "partition_candidates": list(PARTITION_COUNTS),
            "selected_partition_count": partition_count,
            "source_visual_mesh": SOURCE_BODY,
            "disable_existing_proxy_paths": [
                SOURCE + "/__aan_collision_proxy",
                TARGET + "/__aan_collision_proxy",
            ],
            "meshes": mesh_records,
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
                "radius_m": 0.035,
                "height_m": 0.108,
            },
        },
        "qualification": {
            "static_hold_seconds": 8.0,
            "minimum_source_retention_ratio": 0.95,
            "maximum_below_support_count": 0,
            "minimum_final_target_ratio": 0.8,
            "maximum_tabletop_spill_ratio": 0.05,
            "required_cold_runs": 3,
            "oracle": {
                "pivot_inside_target_rim_m": 0.025,
                "pivot_above_target_rim_m": 0.06,
                "tilt_axis": "local_y",
                "tilt_degrees": -110.0,
                "tilt_seconds": 3.0,
                "hold_seconds": 3.0,
                "settle_seconds": 2.0,
            },
            "performance": {
                "width": 960,
                "height": 540,
                "minimum_rtx_fps": 40.0,
                "required_repeats": 3,
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
    source_asset_stage = Usd.Stage.Open(str(cylinder_package / "asset.usd"))
    source_mesh = UsdGeom.Mesh(
        source_asset_stage.GetPrimAtPath(
            "/World/GraduatedCylinder250ml/Visual/Source/Hollow_Body/"
            "Hollow_Body_Mesh_002"
        )
    )
    geometry_report = _write_json(
        out / "evidence/geometry_derivation.json",
        {
            "schema_version": "aan.visible_mesh_partition_derivation.v1",
            "source_mesh": SOURCE_BODY,
            "source_asset_sha256": _sha(cylinder_package / "asset.usd"),
            "source_face_count": len(source_mesh.GetFaceVertexCountsAttr().Get()),
            "partition_count": partition_count,
            "partition_face_counts": [len(sector) for sector in sectors],
            "exact_face_coverage": True,
            "source_points_unchanged": True,
            "source_material_binding_preserved": True,
            "hidden_collision_geometry_added": False,
        },
    )
    manifest = _write_json(
        out / "evidence/manifest.json",
        {
            "schema_version": "aan.interactive_fluid_scene_package.v2",
            "producer": "ConvertAsset",
            "package_id": f"scientific_workbench_task02_fluid_component_r81_p{partition_count}",
            "producer_revision": "2026-08-14-task02-fluid-r81-candidate",
            "overall_status": "candidate_pending_runtime",
            "blocked_reasons": ["runtime_qualification_not_run"],
            "entrypoints": profile_payload["entrypoints"],
            "profile": {"path": profile.name, "sha256": _sha(profile)},
            "geometry_derivation": {
                "path": geometry_report.relative_to(out).as_posix(),
                "sha256": _sha(geometry_report),
            },
            "source_packages": {
                "source_container": {"asset_sha256": _sha(cylinder_package / "asset.usd")},
                "target_container": {"asset_sha256": _sha(beaker_package / "asset.usd")},
            },
            "runtime_qualification": {"status": "not_run"},
            "claims": profile_payload["claim_boundary"],
        },
    )
    return {
        "asset": out / "asset.usd",
        "component": component,
        "qualification": qualification,
        "consumer": consumer,
        "diagnostic_no_partitions": diagnostic_no_partitions,
        "profile": profile,
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cylinder-package", required=True, type=Path)
    parser.add_argument("--beaker-package", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--partition-count", required=True, type=int, choices=PARTITION_COUNTS)
    args = parser.parse_args()
    result = build(
        cylinder_package=args.cylinder_package,
        beaker_package=args.beaker_package,
        out=args.out,
        partition_count=args.partition_count,
    )
    print(json.dumps({key: value.as_posix() for key, value in result.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
