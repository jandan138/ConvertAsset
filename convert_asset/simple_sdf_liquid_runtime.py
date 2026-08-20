"""USD authoring for the reviewed simple-SDF and multi-set liquid route."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import yaml

from .simple_sdf_liquid import (
    COLLISION_SCHEMA,
    FLUID_ROOT,
    RESULT_SCHEMA,
    CollisionSpec,
    MultiLiquidRequest,
    SimpleSdfLiquidError,
    load_approved_collision_spec,
    load_multi_liquid_request,
    evaluate_multi_set_runs,
    select_shared_recipe,
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def propose_simple_sdf(
    *, source: Path, container_prim: str, visual_mesh_prim: str,
    particle_scale: str, output: Path
) -> Path:
    """Write a review document; no source or physics opinion is changed."""
    from pxr import Usd, UsdGeom  # type: ignore

    source = Path(source).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite proposal: {output}")
    stage = Usd.Stage.Open(str(source))
    if stage is None:
        raise SimpleSdfLiquidError(f"cannot open source scene: {source}")
    container = stage.GetPrimAtPath(container_prim)
    mesh = stage.GetPrimAtPath(visual_mesh_prim)
    if not container.IsValid() or not mesh.IsA(UsdGeom.Mesh):
        raise SimpleSdfLiquidError("container or exact visual Mesh prim is invalid")
    if not visual_mesh_prim.startswith(container_prim.rstrip("/") + "/"):
        raise SimpleSdfLiquidError("visual mesh must be inside the container scope")
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    box = cache.ComputeLocalBound(container).ComputeAlignedBox()
    minimum, maximum = box.GetMin(), box.GetMax()
    extent = [float(maximum[i] - minimum[i]) for i in range(3)]
    leaf = container_prim.rsplit("/", 1)[-1].lower()
    pointed_hint = any(token in leaf for token in ("tube", "vial", "centrifuge"))
    plug = {"mode": "none"}
    if pointed_hint:
        side = max(0.001, min(extent[0], extent[1]) * 0.14)
        height = max(0.001, min(0.002, extent[2] * 0.03))
        plug = {
            "mode": "approved_cube",
            "approved": False,
            "size_m": [side, side, height],
            "translate_local_m": [
                0.5 * float(minimum[0] + maximum[0]),
                0.5 * float(minimum[1] + maximum[1]),
                float(minimum[2]) + 0.5 * height,
            ],
            "suggestion_only": True,
        }
    output.mkdir(parents=True)
    proposal = output / "proposal.yaml"
    proposal.write_text(
        yaml.safe_dump(
            {
                "schema_version": COLLISION_SCHEMA,
                "source_scene": str(source),
                "source_sha256": _sha(source),
                "containers": [
                    {
                        "id": container_prim.rsplit("/", 1)[-1],
                        "container_prim": container_prim,
                        "visual_mesh_prim": visual_mesh_prim,
                        "particle_scale": particle_scale,
                        "bottom_plug": plug,
                    }
                ],
                "review": {
                    "status": "pending",
                    "instruction": (
                        "Confirm the exact visual mesh. If a cube is suggested, inspect its "
                        "local size/translation and set approved: true before build."
                    ),
                },
            },
            sort_keys=False,
        )
    )
    return proposal


def _copy_scene_closure(spec: CollisionSpec, output: Path) -> Path:
    return _copy_full_scene_closure(
        scene=spec.source_scene,
        required_prims=[item.container_prim for item in spec.containers],
        output=output,
    )


def _copy_full_scene_closure(*, scene: Path, required_prims: list[str], output: Path) -> Path:
    manifest_path = scene.parent / "manifest.json"
    if manifest_path.is_file():
        try:
            package_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SimpleSdfLiquidError("source package manifest is invalid JSON") from error
        if (
            package_manifest.get("schema_version")
            == "aan.simple_sdf_collision_result.v1"
            and package_manifest.get("overall_status") == "pass"
            and package_manifest.get("entrypoints", {}).get("root_usd") == scene.name
        ):
            root = output / "deps/source"
            shutil.copytree(scene.parent, root)
            return root / scene.name
    from .asset_application_normalizer.model import NormalizeAssetRequest
    from .asset_application_normalizer.usd_closure import build_usd_closure_package

    scope = "/" + required_prims[0].strip("/").split("/", 1)[0]
    root = output / "deps/source"
    result = build_usd_closure_package(
        NormalizeAssetRequest(
            source_usd=scene,
            out_dir=root,
            asset_id="SimpleSdfSourceClosure",
            asset_class="simple_sdf_source",
            source_runtime="generic_usd",
            target_runtime="isaac41",
            target_benchmark="scenario-forge",
            task_id="scenario_forge.simple_sdf_liquid",
            asset_role="dynamic",
            required_prims=required_prims,
            asset_scope_prims=[scope],
            gates=["static"],
        )
    )
    if result.overall_status != "pass":
        raise SimpleSdfLiquidError(f"source dependency closure blocked: {result.blocked_reasons}")
    path = Path(result.root_usd_package_path)
    return path if path.is_absolute() else root / path


def build_simple_sdf_package(*, spec_path: Path, output: Path) -> Path:
    """Disable old scope colliders and use one exact visual mesh SDF per container."""
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics  # type: ignore

    spec = load_approved_collision_spec(spec_path)
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite package: {output}")
    output.mkdir(parents=True)
    try:
        source_copy = _copy_scene_closure(spec, output)
        source_stage = Usd.Stage.Open(str(spec.source_scene))
        overlay_path = output / "collision_overlay.usda"
        overlay = Usd.Stage.CreateNew(str(overlay_path))
        for item in spec.containers:
            scope = source_stage.GetPrimAtPath(item.container_prim)
            if not scope.IsValid():
                raise SimpleSdfLiquidError(f"missing container prim: {item.container_prim}")
            mesh = source_stage.GetPrimAtPath(item.visual_mesh_prim)
            if not mesh.IsA(UsdGeom.Mesh):
                raise SimpleSdfLiquidError(f"visual target is not Mesh: {item.visual_mesh_prim}")
            for prim in Usd.PrimRange(scope):
                if "PhysicsCollisionAPI" in set(prim.GetAppliedSchemas()):
                    overlay.OverridePrim(prim.GetPath()).CreateAttribute(
                        "physics:collisionEnabled", Sdf.ValueTypeNames.Bool
                    ).Set(False)
            target = overlay.OverridePrim(item.visual_mesh_prim)
            UsdPhysics.CollisionAPI.Apply(target).CreateCollisionEnabledAttr(True).Set(True)
            UsdPhysics.MeshCollisionAPI.Apply(target).CreateApproximationAttr("sdf")
            target.SetMetadata(
                "apiSchemas",
                Sdf.TokenListOp.CreateExplicit(
                    [
                        "PhysicsCollisionAPI",
                        "PhysxCollisionAPI",
                        "PhysxConvexHullCollisionAPI",
                        "PhysicsMeshCollisionAPI",
                        "PhysxSDFMeshCollisionAPI",
                    ]
                ),
            )
            if item.bottom_plug.mode == "approved_cube":
                path = item.container_prim.rstrip("/") + "/__aan_simple_sdf_bottom_plug"
                cube = UsdGeom.Cube.Define(overlay, path)
                cube.CreateSizeAttr(1.0)
                cube.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
                xform = UsdGeom.Xformable(cube)
                xform.AddTranslateOp().Set(Gf.Vec3d(*item.bottom_plug.translate_local_m))
                xform.AddScaleOp().Set(Gf.Vec3d(*item.bottom_plug.size_m))
                UsdPhysics.CollisionAPI.Apply(cube.GetPrim()).CreateCollisionEnabledAttr(True).Set(True)
                UsdPhysics.MeshCollisionAPI.Apply(cube.GetPrim()).CreateApproximationAttr("convexHull")
                cube.GetPrim().SetMetadata(
                    "apiSchemas",
                    Sdf.TokenListOp.CreateExplicit(
                        [
                            "PhysicsCollisionAPI",
                            "PhysxCollisionAPI",
                            "PhysicsMeshCollisionAPI",
                            "PhysxConvexHullCollisionAPI",
                        ]
                    ),
                )
        overlay.GetRootLayer().Save()
        entry = output / "asset.usda"
        layer = Sdf.Layer.CreateNew(str(entry))
        layer.subLayerPaths = [
            overlay_path.relative_to(output).as_posix(),
            source_copy.relative_to(output).as_posix(),
        ]
        source_default = source_stage.GetDefaultPrim()
        if source_default.IsValid():
            layer.defaultPrim = source_default.GetName()
        layer.Save()
        entry_stage = Usd.Stage.Open(str(entry))
        UsdGeom.SetStageMetersPerUnit(
            entry_stage, float(UsdGeom.GetStageMetersPerUnit(source_stage))
        )
        UsdGeom.SetStageUpAxis(entry_stage, UsdGeom.GetStageUpAxis(source_stage))
        entry_stage.GetRootLayer().Save()
        manifest = {
            "schema_version": "aan.simple_sdf_collision_result.v1",
            "overall_status": "pass",
            "blocked_reasons": [],
            "entrypoints": {"root_usd": "asset.usda", "overlay_usd": "collision_overlay.usda"},
            "source_binding": {"scene_sha256": _sha(spec.source_scene)},
            "containers": [
                {
                    "id": item.container_id,
                    "container_prim": item.container_prim,
                    "visual_mesh_prim": item.visual_mesh_prim,
                    "collision": "sdf",
                    "bottom_plug": item.bottom_plug.mode,
                    "particle_scale": item.particle_scale,
                }
                for item in spec.containers
            ],
            "claim_boundary": (
                "Source-bound collision authoring only; no liquid, robot, policy, pour, "
                "metric, or benchmark success claim."
            ),
        }
        manifest_path = output / "manifest.json"
        _write_json(manifest_path, manifest)
        return manifest_path
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise


def _triangles(stage: Any, mesh_path: str) -> list[tuple[tuple[float, ...], ...]]:
    from pxr import UsdGeom  # type: ignore

    prim = stage.GetPrimAtPath(mesh_path)
    if not prim.IsA(UsdGeom.Mesh):
        raise SimpleSdfLiquidError(f"sampler is not a Mesh: {mesh_path}")
    mesh = UsdGeom.Mesh(prim)
    points = mesh.GetPointsAttr().Get() or []
    counts = mesh.GetFaceVertexCountsAttr().Get() or []
    indices = mesh.GetFaceVertexIndicesAttr().Get() or []
    matrix = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    world = [tuple(float(v) for v in matrix.Transform(point)) for point in points]
    result = []
    cursor = 0
    for count in counts:
        face = [int(v) for v in indices[cursor : cursor + count]]
        cursor += count
        for index in range(1, len(face) - 1):
            result.append((world[face[0]], world[face[index]], world[face[index + 1]]))
    if not result:
        raise SimpleSdfLiquidError(f"sampler Mesh has no faces: {mesh_path}")
    return result


def _ray_x_intersection(y: float, z: float, tri: tuple[tuple[float, ...], ...]) -> float | None:
    a, b, c = tri
    # Barycentric coordinates in the yz projection. A tiny deterministic offset
    # in caller sampling avoids most edge/vertex degeneracy.
    denominator = (b[1] - c[1]) * (a[2] - c[2]) + (c[2] - b[2]) * (a[1] - c[1])
    if abs(denominator) < 1e-14:
        return None
    u = ((b[1] - c[1]) * (z - c[2]) + (c[2] - b[2]) * (y - c[1])) / denominator
    v = ((c[1] - a[1]) * (z - c[2]) + (a[2] - c[2]) * (y - c[1])) / denominator
    w = 1.0 - u - v
    if min(u, v, w) < -1e-9:
        return None
    return u * a[0] + v * b[0] + w * c[0]


def sample_closed_mesh(stage: Any, mesh_path: str, *, spacing_stage: float, limit: int) -> list[list[float]]:
    triangles = _triangles(stage, mesh_path)
    vertices = [point for tri in triangles for point in tri]
    minimum = [min(point[i] for point in vertices) for i in range(3)]
    maximum = [max(point[i] for point in vertices) for i in range(3)]
    epsilon = spacing_stage * 1e-4
    result: list[list[float]] = []
    # Match PhysX volume sampling's observed safety inset: centers are not
    # emitted directly against the sampler surface.  The colleague golden
    # scene yields a ~1.2 x sampling-distance inset for the 15 mL tube.
    boundary_margin = 1.2 * spacing_stage
    y = minimum[1] + boundary_margin + epsilon
    while y < maximum[1] - boundary_margin:
        z = minimum[2] + boundary_margin + 2.0 * epsilon
        while z < maximum[2] - boundary_margin:
            intersections = sorted(
                value for tri in triangles
                if (value := _ray_x_intersection(y, z, tri)) is not None
            )
            # Collapse duplicate intersections caused by two triangles sharing a face edge.
            unique: list[float] = []
            for value in intersections:
                if not unique or abs(value - unique[-1]) > spacing_stage * 1e-5:
                    unique.append(value)
            for left, right in zip(unique[0::2], unique[1::2]):
                x = left + boundary_margin
                while x < right - boundary_margin:
                    result.append([round(x, 9), round(y, 9), round(z, 9)])
                    if len(result) > max(limit * 20, 2_000_000):
                        raise SimpleSdfLiquidError(
                            f"sampler {mesh_path} is too large for the bounded simple route"
                        )
                    x += spacing_stage
            z += spacing_stage
        y += spacing_stage
    if not result:
        raise SimpleSdfLiquidError(f"sampler produced no interior particles: {mesh_path}")
    if len(result) > limit:
        # PhysX's maxSamples is a cap, not a reason to bias-fill the first side
        # of a volume. Keep an evenly distributed deterministic subset.
        result = [
            result[round(index * (len(result) - 1) / (limit - 1))]
            for index in range(limit)
        ]
    return result


def build_multi_liquid_candidate(*, request_path: Path, output: Path) -> Path:
    """Bake one Points prim per sampler and bind all sets to one system."""
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade  # type: ignore

    request: MultiLiquidRequest = load_multi_liquid_request(request_path)
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite output: {output}")
    output.mkdir(parents=True)
    try:
        source_stage = Usd.Stage.Open(str(request.scene))
        if source_stage is None:
            raise SimpleSdfLiquidError(f"cannot open scene: {request.scene}")
        meters_per_unit = float(UsdGeom.GetStageMetersPerUnit(source_stage))
        recipe = select_shared_recipe(request.sets)
        source_copy = _copy_full_scene_closure(
            scene=request.scene,
            required_prims=[item.container_prim for item in request.sets],
            output=output,
        )
        spacing_stage = float(recipe["particle_set"]["spacing_m"]) / meters_per_unit
        per_set_limit = int(recipe["particle_set"]["maximum_count_per_set"])
        sampled: dict[str, list[list[float]]] = {}
        for item in request.sets:
            sampler_stage = (
                Usd.Stage.Open(str(item.sampler_usd)) if item.sampler_usd else source_stage
            )
            sampled[item.set_id] = sample_closed_mesh(
                sampler_stage, item.sampler_mesh_prim,
                spacing_stage=spacing_stage, limit=per_set_limit,
            )
        total = sum(len(points) for points in sampled.values())
        if total > int(recipe["particle_set"]["maximum_count_total"]):
            raise SimpleSdfLiquidError("scene-wide particle budget exceeds 100,000")
        overlay_path = output / "liquid_overlay.usda"
        stage = Usd.Stage.CreateNew(str(overlay_path))
        stage.DefinePrim(FLUID_ROOT, "Scope")
        system_path = FLUID_ROOT + "/ParticleSystem"
        system = stage.DefinePrim(system_path, "PhysxParticleSystem")
        system.SetMetadata(
            "apiSchemas", Sdf.TokenListOp.Create(prependedItems=["PhysxParticleIsosurfaceAPI"])
        )
        ps = recipe["particle_system"]
        for name, key in (
            ("maxVelocity", "max_velocity_m_s"),
            ("particleContactOffset", "particle_contact_offset_m"),
            ("restOffset", "effective_rest_offset_m"),
        ):
            system.CreateAttribute(name, Sdf.ValueTypeNames.Float).Set(float(ps[key]) / meters_per_unit)
        for name, key, type_name in (
            ("physxParticleIsosurface:gridFilteringPasses", "grid_filtering_passes", Sdf.ValueTypeNames.Int),
            ("physxParticleIsosurface:gridSmoothingRadius", "grid_smoothing_radius_m", Sdf.ValueTypeNames.Float),
            ("physxParticleIsosurface:meshSmoothingPasses", "mesh_smoothing_passes", Sdf.ValueTypeNames.Int),
            ("physxParticleIsosurface:surfaceDistance", "surface_distance_m", Sdf.ValueTypeNames.Float),
        ):
            value = ps[key]
            if "Radius" in name or "Distance" in name:
                value = float(value) / meters_per_unit
            system.CreateAttribute(name, type_name).Set(value)
        material = UsdShade.Material.Define(stage, FLUID_ROOT + "/LiquidMaterial")
        shader = UsdShade.Shader.Define(stage, FLUID_ROOT + "/LiquidMaterial/PreviewSurface")
        shader.CreateIdAttr("UsdPreviewSurface")
        mat = recipe["material"]
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*mat["diffuse_color"]))
        shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(mat["ior"])
        shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(mat["opacity"])
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(mat["roughness"])
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        set_records = []
        for item in request.sets:
            values = [Gf.Vec3f(*point) for point in sampled[item.set_id]]
            points = UsdGeom.Points.Define(stage, item.particle_prim)
            points.GetPointsAttr().Set(values)
            points.GetPrim().CreateAttribute(
                "physxParticle:simulationPoints", Sdf.ValueTypeNames.Point3fArray
            ).Set(values)
            points.GetWidthsAttr().Set(
                [float(recipe["particle_set"]["width_m"]) / meters_per_unit] * len(values)
            )
            points.GetVelocitiesAttr().Set([Gf.Vec3f(0.0)] * len(values))
            prim = points.GetPrim()
            prim.CreateRelationship("physxParticle:particleSystem").SetTargets([Sdf.Path(system_path)])
            prim.CreateAttribute("physxParticle:fluid", Sdf.ValueTypeNames.Bool).Set(True)
            prim.CreateAttribute("physxParticle:selfCollision", Sdf.ValueTypeNames.Bool).Set(True)
            prim.CreateAttribute("physxParticle:particleGroup", Sdf.ValueTypeNames.Int).Set(item.particle_group)
            prim.CreateAttribute("scenarioForge:setId", Sdf.ValueTypeNames.String).Set(item.set_id)
            prim.CreateAttribute("scenarioForge:samplerMeshPrim", Sdf.ValueTypeNames.String).Set(item.sampler_mesh_prim)
            if item.preview_color is not None:
                points.CreateDisplayColorPrimvar(UsdGeom.Tokens.constant).Set([Gf.Vec3f(*item.preview_color)])
            UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(recipe["particle_set"]["mass_kg"])
            UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
            prim.SetMetadata(
                "apiSchemas",
                Sdf.TokenListOp.Create(
                    prependedItems=["PhysxParticleSetAPI", "PhysicsMassAPI", "MaterialBindingAPI"]
                ),
            )
            set_records.append(
                {
                    "id": item.set_id,
                    "particle_prim": item.particle_prim,
                    "particle_group": item.particle_group,
                    "particle_count": len(values),
                    "sampler_mesh_prim": item.sampler_mesh_prim,
                    "sampler_usd": str(item.sampler_usd or request.scene),
                    "container_prim": item.container_prim,
                    "initial_min_z_stage": min(point[2] for point in sampled[item.set_id]),
                }
            )
        if not any(prim.GetTypeName() == "PhysicsScene" for prim in source_stage.Traverse()):
            scene = UsdPhysics.Scene.Define(stage, FLUID_ROOT + "/PhysicsScene")
            scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
            scene.CreateGravityMagnitudeAttr(9.81 / meters_per_unit)
        stage.GetRootLayer().Save()
        entry = output / "scene.usda"
        layer = Sdf.Layer.CreateNew(str(entry))
        layer.subLayerPaths = [
            overlay_path.name,
            source_copy.relative_to(output).as_posix(),
        ]
        default_prim = source_stage.GetDefaultPrim()
        if default_prim.IsValid():
            layer.defaultPrim = default_prim.GetName()
        layer.Save()
        entry_stage = Usd.Stage.Open(str(entry))
        UsdGeom.SetStageMetersPerUnit(entry_stage, meters_per_unit)
        UsdGeom.SetStageUpAxis(entry_stage, UsdGeom.GetStageUpAxis(source_stage))
        entry_stage.GetRootLayer().Save()
        _write_json(output / "recipe.json", recipe)
        manifest = {
            "schema_version": RESULT_SCHEMA,
            "overall_status": "candidate",
            "blocked_reasons": ["runtime_validation_not_run"],
            "entrypoints": {
                "root_usd": "scene.usda",
                "overlay_usd": "liquid_overlay.usda",
                "particle_system_prim": system_path,
                "particle_sets_root": FLUID_ROOT + "/ParticleSets",
            },
            "source_binding": {"scene": str(request.scene), "sha256": _sha(request.scene)},
            "sampling": {
                "backend": "producer_time_closed_mesh_volume_lattice",
                "runtime_resampling": False,
                "spacing_m": recipe["particle_set"]["spacing_m"],
            },
            "recipe": {"id": recipe["recipe_id"], "path": "recipe.json"},
            "sets": set_records,
            "validation": {"mode": request.validation, "status": "not_run"},
            "claim_boundary": "No robot, pour, metric, or benchmark success claim.",
        }
        manifest_path = output / "manifest.json"
        _write_json(manifest_path, manifest)
        return manifest_path
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise


def validate_multi_liquid_candidate(
    *, output: Path, launcher: Path, worker: Path
) -> Path:
    """Run one 3 s quick check or three 8 s qualification cold processes."""
    output = Path(output).resolve()
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("overall_status") != "candidate":
        raise SimpleSdfLiquidError("only a candidate can be runtime validated")
    mode = str(manifest["validation"]["mode"])
    count, seconds = (1, 3.0) if mode == "quick" else (3, 8.0)
    evidence = output / "evidence/runtime_validation"
    evidence.mkdir(parents=True, exist_ok=False)
    environment = dict(os.environ)
    for name in (
        "PYTHONPATH", "LD_LIBRARY_PATH", "CARB_APP_PATH", "EXP_PATH",
        "ISAAC_PATH", "ISAAC_SIM_ROOT",
    ):
        environment.pop(name, None)
    environment["ACCEPT_EULA"] = "Y"
    environment.setdefault("PRIVACY_CONSENT", "Y")
    runs = []
    for index in range(1, count + 1):
        destination = evidence / f"cold_run_{index}.json"
        completed = subprocess.run(
            [
                str(launcher), str(worker),
                "--scene", str(output / manifest["entrypoints"]["root_usd"]),
                "--manifest", str(manifest_path),
                "--seconds", str(seconds),
                "--run-index", str(index),
                "--out", str(destination),
            ],
            check=False,
            env=environment,
        )
        if completed.returncode:
            raise SimpleSdfLiquidError(
                f"Isaac multi-liquid cold run {index} failed with {completed.returncode}"
            )
        runs.append(json.loads(destination.read_text()))
    evaluation = evaluate_multi_set_runs(
        runs, set_ids=[item["id"] for item in manifest["sets"]], mode=mode
    )
    report = {
        "schema_version": "aan.multi_liquid_validation_report.v1",
        "runtime": "isaac41",
        "mode": mode,
        "required_cold_runs": count,
        "duration_seconds_per_run": seconds,
        "per_set_minimum_retention_ratio": 0.99,
        "maximum_below_floor_count": 0,
        **evaluation,
        "runs": [f"cold_run_{index}.json" for index in range(1, count + 1)],
    }
    report_path = evidence / "report.json"
    _write_json(report_path, report)
    manifest["overall_status"] = evaluation["overall_status"]
    manifest["blocked_reasons"] = evaluation["blocked_reasons"]
    manifest["validation"] = {
        "mode": mode,
        "status": evaluation["overall_status"],
        "report": str(report_path.relative_to(output)),
        "report_sha256": _sha(report_path),
    }
    manifest["claim"] = evaluation["claim"]
    manifest["robot_policy_success"] = False
    manifest["benchmark_success"] = False
    _write_json(manifest_path, manifest)
    if evaluation["overall_status"] != "pass":
        raise SimpleSdfLiquidError("multi-liquid runtime validation failed")
    return report_path
