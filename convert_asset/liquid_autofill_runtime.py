"""Isaac/USD-backed producer for source-bound GPU-PBD liquid starts.

The module imports ``pxr`` only inside runtime functions.  It intentionally
fails closed: geometry that does not expose a dominant hollow axial shell is
reported as diagnostic-only instead of receiving a guessed box of particles.
"""

from __future__ import annotations

from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable, Mapping

from .liquid_autofill import (
    AUTOFILL_RESULT_SCHEMA,
    LiquidAutofillError,
    build_particle_lattice,
    recipe_payload,
    recipe_sha256,
    validate_request,
)


_CONTAINER_HINTS = (
    "beaker",
    "bottle",
    "cylinder",
    "flask",
    "vessel",
    "cup",
    "tube",
    "container",
    "jar",
    "烧杯",
    "量筒",
    "烧瓶",
    "试剂瓶",
)
_SOLID_COLLIDER_HINTS = (
    "base",
    "bottom",
    "connector",
    "stand",
    "foot",
    "pedestal",
    "spout",
    "底",
    "座",
)
_HOLLOW_WALL_HINTS = ("hollow", "inner_wall", "interior_wall")
_RIM_HINTS = ("rim", "lip")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _slug(value: str) -> str:
    leaf = value.rstrip("/").rsplit("/", 1)[-1]
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", leaf).strip("_")
    return cleaned or "Container"


def _axis_indices(up_axis: str) -> tuple[int, int, int]:
    if up_axis == "Z":
        return 0, 1, 2
    if up_axis == "Y":
        return 0, 2, 1
    raise LiquidAutofillError(f"unsupported USD up axis for v1: {up_axis}")


def _analysis_point(
    point: Iterable[float], *, up_axis: str, meters_per_unit: float
) -> list[float]:
    values = [float(value) * meters_per_unit for value in point]
    first, second, vertical = _axis_indices(up_axis)
    return [values[first], values[second], values[vertical]]


def _stage_point(
    point_m: Iterable[float], *, up_axis: str, meters_per_unit: float
) -> list[float]:
    x, y, z = [float(value) / meters_per_unit for value in point_m]
    if up_axis == "Z":
        return [x, y, z]
    return [x, z, y]


def _two_means(values: list[float]) -> tuple[float, float, int, int]:
    if len(values) < 16:
        raise LiquidAutofillError("too few shell samples to recover an inner cavity")
    low = min(values)
    high = max(values)
    for _ in range(32):
        left = [value for value in values if abs(value - low) <= abs(value - high)]
        right = [value for value in values if abs(value - low) > abs(value - high)]
        if not left or not right:
            raise LiquidAutofillError("shell samples do not separate into inner and outer walls")
        next_low = sum(left) / len(left)
        next_high = sum(right) / len(right)
        if abs(next_low - low) + abs(next_high - high) < 1e-7:
            break
        low, high = next_low, next_high
    if low > high:
        low, high = high, low
        left, right = right, left
    return low, high, len(left), len(right)


def _mesh_cavity_candidate(
    points: list[list[float]], *, prim_path: str
) -> dict[str, Any] | None:
    if len(points) < 24:
        return None
    minimum = [min(point[axis] for point in points) for axis in range(3)]
    maximum = [max(point[axis] for point in points) for axis in range(3)]
    extent = [maximum[axis] - minimum[axis] for axis in range(3)]
    if min(extent) <= 0.0 or extent[2] < 0.018:
        return None
    center = [0.5 * (minimum[axis] + maximum[axis]) for axis in range(3)]
    half_x = 0.5 * extent[0]
    half_y = 0.5 * extent[1]
    mid = [
        point
        for point in points
        if minimum[2] + 0.15 * extent[2]
        <= point[2]
        <= minimum[2] + 0.85 * extent[2]
    ]
    # Many admitted scientific vessels deliberately keep the wall mesh lean:
    # two open rings (floor and rim) joined by faces.  Their vertices carry the
    # same trustworthy inner/outer radii even though no vertex lies at mid-Z.
    # Use all wall samples in that topology instead of rejecting the proven
    # Task 02 Hollow_Body representation.
    if len(mid) < 16:
        upper_wall = [
            point for point in points if point[2] >= minimum[2] + 0.5 * extent[2]
        ]
        mid = upper_wall if len(upper_wall) >= 16 else points
    radial = [
        math.sqrt(
            ((point[0] - center[0]) / half_x) ** 2
            + ((point[1] - center[1]) / half_y) ** 2
        )
        for point in mid
    ]
    try:
        inner_peak, outer_peak, inner_count, outer_count = _two_means(radial)
    except LiquidAutofillError:
        return None
    ratio = inner_peak / outer_peak if outer_peak > 0.0 else 0.0
    if not 0.55 <= ratio <= 0.985 or min(inner_count, outer_count) < 6:
        return None
    radius_x = half_x * ratio
    radius_y = half_y * ratio
    wall = max(half_x, half_y) * (1.0 - ratio)
    floor = minimum[2] + max(0.5 * wall, 0.002)
    rim = maximum[2] - max(0.25 * wall, 0.001)
    if rim - floor < 0.015:
        return None
    volume = math.pi * radius_x * radius_y * (rim - floor)
    return {
        "prim_path": prim_path,
        "center_xy_m": [center[0], center[1]],
        "radius_x_m": radius_x,
        "radius_y_m": radius_y,
        "floor_m": floor,
        "rim_m": rim,
        "estimated_volume_m3": volume,
        "inner_outer_radial_ratio": ratio,
        "inner_sample_count": inner_count,
        "outer_sample_count": outer_count,
        "method": "two_surface_axial_shell",
    }


def _mesh_opening_candidate(points: list[list[float]]) -> dict[str, Any] | None:
    """Recover the inner ring from the highest concentric open-rim samples."""
    if len(points) < 24:
        return None
    minimum_z = min(point[2] for point in points)
    maximum_z = max(point[2] for point in points)
    height = maximum_z - minimum_z
    if height <= 0.0:
        return None
    tolerance = max(1e-7, height * 0.002)
    top = [point for point in points if point[2] >= maximum_z - tolerance]
    if len(top) < 12:
        return None
    center_x = sum(point[0] for point in top) / len(top)
    center_y = sum(point[1] for point in top) / len(top)
    radial = [math.hypot(point[0] - center_x, point[1] - center_y) for point in top]
    try:
        inner_peak, outer_peak, inner_count, outer_count = _two_means(radial)
    except LiquidAutofillError:
        return None
    if inner_peak <= 0.0 or outer_peak <= inner_peak or min(inner_count, outer_count) < 6:
        return None
    inner = [
        point
        for point, radius in zip(top, radial)
        if abs(radius - inner_peak) <= abs(radius - outer_peak)
    ]
    radius_x = max(abs(point[0] - center_x) for point in inner)
    radius_y = max(abs(point[1] - center_y) for point in inner)
    if min(radius_x, radius_y) <= 0.0:
        return None
    return {
        "center_xy_m": [center_x, center_y],
        "radius_x_m": radius_x,
        "radius_y_m": radius_y,
        "rim_m": maximum_z,
        "inner_outer_radial_ratio": inner_peak / outer_peak,
        "inner_sample_count": inner_count,
        "outer_sample_count": outer_count,
        "method": "highest_concentric_inner_ring",
    }


def _mesh_capacity_candidate(points: list[list[float]]) -> dict[str, Any] | None:
    """Find the longest repeated inner-wall ring used by the main vessel body."""
    if len(points) < 24:
        return None
    minimum = [min(point[axis] for point in points) for axis in range(3)]
    maximum = [max(point[axis] for point in points) for axis in range(3)]
    center_x = 0.5 * (minimum[0] + maximum[0])
    center_y = 0.5 * (minimum[1] + maximum[1])
    levels: dict[float, list[list[float]]] = {}
    for point in points:
        levels.setdefault(round(point[2], 6), []).append(point)
    sections: list[dict[str, Any]] = []
    for z, ring in levels.items():
        if len(ring) < 12:
            continue
        radial = [math.hypot(p[0] - center_x, p[1] - center_y) for p in ring]
        try:
            inner_peak, outer_peak, inner_count, outer_count = _two_means(radial)
        except LiquidAutofillError:
            continue
        separation = (outer_peak - inner_peak) / outer_peak if outer_peak > 0.0 else 0.0
        if (
            inner_peak <= 0.0
            or outer_peak <= inner_peak
            or separation < 0.03
            or min(inner_count, outer_count) < 6
        ):
            continue
        inner = [
            point
            for point, radius in zip(ring, radial)
            if abs(radius - inner_peak) <= abs(radius - outer_peak)
        ]
        sections.append(
            {
                "z_m": z,
                "radius_x_m": max(abs(point[0] - center_x) for point in inner),
                "radius_y_m": max(abs(point[1] - center_y) for point in inner),
                "inner_peak_m": inner_peak,
            }
        )
    sections.sort(key=lambda item: float(item["z_m"]))
    best: tuple[float, dict[str, Any], dict[str, Any]] | None = None
    for index, lower in enumerate(sections):
        for upper in sections[index + 1 :]:
            relative = abs(lower["inner_peak_m"] - upper["inner_peak_m"]) / max(
                lower["inner_peak_m"], upper["inner_peak_m"]
            )
            span = float(upper["z_m"] - lower["z_m"])
            if relative <= 0.05 and span > 0.0 and (best is None or span > best[0]):
                best = (span, lower, upper)
    if best is None:
        return None
    span, lower, upper = best
    return {
        "center_xy_m": [center_x, center_y],
        "radius_x_m": 0.5 * (lower["radius_x_m"] + upper["radius_x_m"]),
        "radius_y_m": 0.5 * (lower["radius_y_m"] + upper["radius_y_m"]),
        "lower_ring_m": lower["z_m"],
        "upper_ring_m": upper["z_m"],
        "repeated_span_m": span,
        "method": "longest_repeated_inner_wall_ring",
    }


def _mesh_inner_radial_profile(
    points: list[list[float]], *, floor_m: float
) -> list[dict[str, float]]:
    """Recover a conservative 5 mm-binned inner-radius curve."""

    levels: dict[float, list[list[float]]] = {}
    for point in points:
        levels.setdefault(round(point[2], 6), []).append(point)
    rows: list[tuple[float, float]] = []
    for z, ring in levels.items():
        if z < floor_m or len(ring) < 12:
            continue
        center_x = sum(point[0] for point in ring) / len(ring)
        center_y = sum(point[1] for point in ring) / len(ring)
        radial = [
            math.hypot(point[0] - center_x, point[1] - center_y)
            for point in ring
        ]
        try:
            inner, outer, inner_count, outer_count = _two_means(radial)
        except LiquidAutofillError:
            continue
        separation = (outer - inner) / outer if outer > 0.0 else 0.0
        if inner <= 0.0 or min(inner_count, outer_count) < 6 or separation < 0.03:
            continue
        rows.append((z, inner))
    bins: dict[int, list[tuple[float, float]]] = {}
    for z, radius in rows:
        bins.setdefault(math.floor((z - floor_m) / 0.005), []).append((z, radius))
    profile = [
        {
            "z_m": sum(z for z, _ in values) / len(values),
            "inner_radius_m": min(radius for _, radius in values),
        }
        for _, values in sorted(bins.items())
    ]
    return profile if len(profile) >= 3 else []


def analyze_container(scene: Path, container_prim: str) -> dict[str, Any]:
    from pxr import Usd, UsdGeom  # type: ignore

    stage = Usd.Stage.Open(str(Path(scene).resolve()))
    if stage is None:
        raise LiquidAutofillError(f"cannot open USD scene: {scene}")
    target = stage.GetPrimAtPath(container_prim)
    if not target.IsValid() or not target.IsActive():
        raise LiquidAutofillError(f"container prim does not exist or is inactive: {container_prim}")
    if target.IsInstanceProxy():
        raise LiquidAutofillError("instance proxy cannot be targeted; select its instance root")
    default_prim = stage.GetDefaultPrim()
    if not default_prim.IsValid():
        raise LiquidAutofillError("source scene must declare a defaultPrim")

    descendants = list(Usd.PrimRange(target))
    rigid = [
        prim.GetPath().pathString
        for prim in descendants
        if "PhysicsRigidBodyAPI" in set(prim.GetAppliedSchemas())
    ]
    articulations = [
        prim.GetPath().pathString
        for prim in descendants
        if "PhysicsArticulationRootAPI" in set(prim.GetAppliedSchemas())
        or prim.GetTypeName().endswith("Joint")
        or prim.GetTypeName() in {"Skeleton", "SkelRoot"}
    ]
    deforming = [
        prim.GetPath().pathString
        for prim in descendants
        if prim.GetTypeName() in {"BasisCurves", "NurbsPatch"}
        or any("Deformable" in schema or "Cloth" in schema for schema in prim.GetAppliedSchemas())
    ]
    if len(rigid) > 1:
        raise LiquidAutofillError("container has more than one active rigid body")
    if articulations:
        raise LiquidAutofillError("articulation, joint, or skinned containers are not supported")
    if deforming:
        raise LiquidAutofillError("soft, cloth, or deforming containers are not supported")

    up_axis = str(UsdGeom.GetStageUpAxis(stage)).upper()
    meters_per_unit = float(UsdGeom.GetStageMetersPerUnit(stage))
    if not math.isfinite(meters_per_unit) or meters_per_unit <= 0.0:
        raise LiquidAutofillError("scene has an invalid metersPerUnit")
    xform_cache = UsdGeom.XformCache()
    target_world = xform_cache.GetLocalToWorldTransform(target)
    target_inverse = target_world.GetInverse()
    up_local_stage = [0.0, 0.0, 1.0] if up_axis == "Z" else [0.0, 1.0, 0.0]
    local_up_world = target_world.TransformDir(up_local_stage)
    world_up = up_local_stage
    denominator = local_up_world.GetLength()
    cosine = (
        sum(float(local_up_world[i]) * world_up[i] for i in range(3)) / denominator
        if denominator
        else -1.0
    )
    upright_error_deg = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
    if upright_error_deg > 15.0:
        raise LiquidAutofillError(
            f"container upright error {upright_error_deg:.3f} deg exceeds 15 deg"
        )

    mesh_points: dict[str, list[list[float]]] = {}
    mesh_paths: list[str] = []
    for prim in descendants:
        if not prim.IsA(UsdGeom.Mesh) or not prim.IsActive():
            continue
        mesh = UsdGeom.Mesh(prim)
        authored = mesh.GetPointsAttr().Get() or []
        if not authored:
            continue
        world = xform_cache.GetLocalToWorldTransform(prim)
        values = [
            _analysis_point(
                target_inverse.Transform(world.Transform(point)),
                up_axis=up_axis,
                meters_per_unit=meters_per_unit,
            )
            for point in authored
        ]
        path = prim.GetPath().pathString
        mesh_paths.append(path)
        mesh_points[path] = values
    if not mesh_paths:
        raise LiquidAutofillError("container scope has no authored mesh points")

    candidates = [
        value
        for path, points in mesh_points.items()
        if (value := _mesh_cavity_candidate(points, prim_path=path)) is not None
    ]
    if not candidates:
        raise LiquidAutofillError(
            "no trustworthy hollow axial cavity was detected; a solid-looking bbox is not enough"
        )
    candidates.sort(key=lambda item: float(item["estimated_volume_m3"]), reverse=True)
    semantic_walls = [
        item
        for item in candidates
        if any(hint in str(item["prim_path"]).lower() for hint in _HOLLOW_WALL_HINTS)
    ]
    if len(semantic_walls) == 1:
        selected = semantic_walls[0]
        dominance = None
        selection_method = "unique_semantic_hollow_wall"
    elif len(candidates) > 1:
        dominance = float(candidates[0]["estimated_volume_m3"]) / float(
            candidates[1]["estimated_volume_m3"]
        )
        if dominance < 2.0:
            raise LiquidAutofillError(
                f"multiple cavity candidates are ambiguous (largest ratio {dominance:.3f} < 2.0)"
            )
        selected = candidates[0]
        selection_method = "dominant_volume"
    else:
        dominance = None
        selected = candidates[0]
        selection_method = "single_geometry_candidate"

    opening = _mesh_opening_candidate(mesh_points[str(selected["prim_path"])])
    if opening is None:
        raise LiquidAutofillError("selected hollow shell has no trustworthy open-rim inner ring")
    capacity = _mesh_capacity_candidate(mesh_points[str(selected["prim_path"])])
    if capacity is not None:
        cavity_height = float(selected["rim_m"]) - float(selected["floor_m"])
        if float(capacity["repeated_span_m"]) < 0.25 * cavity_height:
            # Short paired rings commonly describe a threaded lip, not the
            # vessel's usable body. Falling back to the full cavity estimate is
            # safer than turning that local detail into a fill-volume claim.
            capacity = None
    radial_profile = _mesh_inner_radial_profile(
        mesh_points[str(selected["prim_path"])], floor_m=float(selected["floor_m"])
    )

    collision_prims: list[dict[str, str]] = []
    for path in mesh_paths:
        lower = path.lower()
        if path == selected["prim_path"] or any(hint in lower for hint in _RIM_HINTS):
            collision_prims.append({"prim_path": path, "approximation": "sdf"})
        elif any(hint in lower for hint in _SOLID_COLLIDER_HINTS):
            collision_prims.append({"prim_path": path, "approximation": "convexHull"})
    existing_colliders = [
        prim.GetPath().pathString
        for prim in descendants
        if "PhysicsCollisionAPI" in set(prim.GetAppliedSchemas())
    ]
    physics_scenes = [
        prim.GetPath().pathString
        for prim in stage.Traverse()
        if prim.GetTypeName() == "PhysicsScene"
    ]
    return {
        "schema_version": "aan.gpu_pbd_container_analysis.v1",
        "scene": str(Path(scene).resolve()),
        "container_prim": container_prim,
        "scene_root_prim": default_prim.GetPath().pathString,
        "default_prim": default_prim.GetName(),
        "runtime": "isaac41",
        "meters_per_unit": meters_per_unit,
        "up_axis": up_axis,
        "upright_error_deg": upright_error_deg,
        "rigid_body_prims": rigid,
        "physics_scene_path": physics_scenes[0] if physics_scenes else None,
        "instanceable_target": bool(target.IsInstanceable()),
        "mesh_count": len(mesh_paths),
        "cavity_candidate_count": len(candidates),
        "dominant_cavity_volume_ratio": dominance,
        "cavity_selection_method": selection_method,
        "cavity": selected,
        "opening": opening,
        "capacity": capacity,
        "radial_profile": radial_profile,
        "collision_prims": collision_prims,
        "existing_collider_prims": existing_colliders,
        "confidence": "high",
        "claim_boundary": (
            "Dominant axial hollow-shell geometry only; runtime qualification is still required."
        ),
    }


def inspect_scene(scene: Path) -> dict[str, Any]:
    from pxr import Usd  # type: ignore

    stage = Usd.Stage.Open(str(Path(scene).resolve()))
    if stage is None:
        raise LiquidAutofillError(f"cannot open USD scene: {scene}")
    suggestions: list[dict[str, Any]] = []
    for prim in stage.Traverse():
        if not prim.IsActive() or prim.GetTypeName() != "Xform":
            continue
        path = prim.GetPath().pathString
        name = prim.GetName().lower()
        has_hint = any(hint in name for hint in _CONTAINER_HINTS)
        has_interior_frame = any(
            child.GetName() == "__aan_frame_interior_center" for child in prim.GetChildren()
        )
        if not has_hint and not has_interior_frame:
            continue
        try:
            analysis = analyze_container(scene, path)
        except LiquidAutofillError as error:
            if not has_interior_frame:
                continue
            suggestions.append(
                {
                    "prim_path": path,
                    "status": "rejected",
                    "reason": str(error),
                    "confidence": "none",
                }
            )
        else:
            suggestions.append(
                {
                    "prim_path": path,
                    "status": "candidate",
                    "confidence": analysis["confidence"],
                    "cavity": analysis["cavity"],
                }
            )
    return {
        "schema_version": "aan.gpu_pbd_container_inspection.v1",
        "scene": str(Path(scene).resolve()),
        "candidate_count": sum(item["status"] == "candidate" for item in suggestions),
        "suggestions": suggestions,
    }


def _define_overlay(
    *, scene: Path, output: Path, analysis: Mapping[str, Any], points_m: list[list[float]],
    collision_profile: str | None,
) -> tuple[Path, str, str, str | None]:
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade  # type: ignore

    source_stage = Usd.Stage.Open(str(scene.resolve()))
    if source_stage is None:
        raise LiquidAutofillError(f"cannot reopen USD scene: {scene}")
    target = source_stage.GetPrimAtPath(str(analysis["container_prim"]))
    target_world = UsdGeom.XformCache().GetLocalToWorldTransform(target)
    up_axis = str(analysis["up_axis"])
    meters_per_unit = float(analysis["meters_per_unit"])
    world_points = [
        target_world.Transform(
            Gf.Vec3d(
                *_stage_point(
                    point, up_axis=up_axis, meters_per_unit=meters_per_unit
                )
            )
        )
        for point in points_m
    ]

    overlay = output / "producer_overlay.usda"
    stage = Usd.Stage.CreateNew(str(overlay))
    stage.SetMetadata("metersPerUnit", meters_per_unit)
    stage.SetMetadata("upAxis", up_axis)
    target_override = stage.OverridePrim(str(analysis["container_prim"]))
    if analysis.get("instanceable_target"):
        target_override.SetInstanceable(False)
    enabled_paths = {item["prim_path"] for item in analysis["collision_prims"]}
    for path in analysis["existing_collider_prims"]:
        if path not in enabled_paths:
            stage.OverridePrim(path).CreateAttribute(
                "physics:collisionEnabled", Sdf.ValueTypeNames.Bool
            ).Set(False)
    for item in analysis["collision_prims"]:
        prim = stage.OverridePrim(item["prim_path"])
        UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True).Set(True)
        UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr(
            item["approximation"]
        )
    pbd_proxy_path = None
    if collision_profile == "task02_visual_mesh_convex_decomposition_v1":
        source_mesh_path = str(analysis["cavity"]["prim_path"])
        source_mesh = UsdGeom.Mesh(source_stage.GetPrimAtPath(source_mesh_path))
        source_points = source_mesh.GetPointsAttr().Get() or []
        source_counts = source_mesh.GetFaceVertexCountsAttr().Get() or []
        source_indices = source_mesh.GetFaceVertexIndicesAttr().Get() or []
        if not source_points or not source_counts or not source_indices:
            raise LiquidAutofillError(
                "PBD collision proxy source mesh has no authored closed geometry"
            )
        cache = UsdGeom.XformCache()
        source_world = cache.GetLocalToWorldTransform(source_mesh.GetPrim())
        target_inverse = target_world.GetInverse()
        pbd_proxy_path = (
            str(analysis["container_prim"])
            + "/__aan_pbd_collision_proxy/PBD_Unified_Vessel_Mesh"
        )
        proxy = UsdGeom.Mesh.Define(stage, pbd_proxy_path)
        proxy.CreatePointsAttr(
            [target_inverse.Transform(source_world.Transform(point)) for point in source_points]
        )
        proxy.CreateFaceVertexCountsAttr(source_counts)
        proxy.CreateFaceVertexIndicesAttr(source_indices)
        proxy.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        proxy.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
        proxy.CreateDoubleSidedAttr(True)
        proxy_prim = proxy.GetPrim()
        UsdPhysics.CollisionAPI.Apply(proxy_prim).CreateCollisionEnabledAttr(True).Set(True)
        UsdPhysics.MeshCollisionAPI.Apply(proxy_prim).CreateApproximationAttr(
            "convexDecomposition"
        )
        for name, value, value_type in (
            ("physxCollision:contactOffset", 0.01 / meters_per_unit, Sdf.ValueTypeNames.Float),
            ("physxCollision:restOffset", 0.005 / meters_per_unit, Sdf.ValueTypeNames.Float),
            ("physxConvexDecompositionCollision:errorPercentage", 0.1, Sdf.ValueTypeNames.Float),
            ("physxConvexDecompositionCollision:minThickness", 0.001 / meters_per_unit, Sdf.ValueTypeNames.Float),
            ("physxConvexDecompositionCollision:shrinkWrap", True, Sdf.ValueTypeNames.Bool),
            ("physxConvexDecompositionCollision:voxelResolution", 500_000, Sdf.ValueTypeNames.Int),
        ):
            proxy_prim.CreateAttribute(name, value_type).Set(value)

    liquid_root = f"/__ScenarioForgeLiquid_{_slug(str(analysis['container_prim']))}"
    particle_system_path = liquid_root + "/ParticleSystem"
    particles_path = liquid_root + "/ParticleSet"
    UsdGeom.Scope.Define(stage, liquid_root)
    recipe = recipe_payload()
    system = stage.DefinePrim(particle_system_path, "PhysxParticleSystem")
    system.SetMetadata(
        "apiSchemas",
        Sdf.TokenListOp.Create(prependedItems=["PhysxParticleIsosurfaceAPI"]),
    )
    ps = recipe["particle_system"]
    system.CreateAttribute("maxVelocity", Sdf.ValueTypeNames.Float).Set(
        ps["max_velocity_m_s"] / meters_per_unit
    )
    system.CreateAttribute("particleContactOffset", Sdf.ValueTypeNames.Float).Set(
        ps["particle_contact_offset_m"] / meters_per_unit
    )
    system.CreateAttribute("restOffset", Sdf.ValueTypeNames.Float).Set(
        ps["effective_rest_offset_m"] / meters_per_unit
    )
    system.CreateAttribute(
        "physxParticleIsosurface:gridFilteringPasses", Sdf.ValueTypeNames.Int
    ).Set(ps["grid_filtering_passes"])
    system.CreateAttribute(
        "physxParticleIsosurface:gridSmoothingRadius", Sdf.ValueTypeNames.Float
    ).Set(ps["grid_smoothing_radius_m"] / meters_per_unit)
    system.CreateAttribute(
        "physxParticleIsosurface:meshSmoothingPasses", Sdf.ValueTypeNames.Int
    ).Set(ps["mesh_smoothing_passes"])
    system.CreateAttribute(
        "physxParticleIsosurface:surfaceDistance", Sdf.ValueTypeNames.Float
    ).Set(ps["surface_distance_m"] / meters_per_unit)

    material = UsdShade.Material.Define(stage, liquid_root + "/LiquidMaterial")
    shader = UsdShade.Shader.Define(stage, liquid_root + "/LiquidMaterial/PreviewSurface")
    shader.CreateIdAttr("UsdPreviewSurface")
    mat = recipe["material"]
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(*mat["diffuse_color"])
    )
    shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(mat["ior"])
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(mat["opacity"])
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(mat["roughness"])
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

    particles = UsdGeom.Points.Define(stage, particles_path)
    values = [Gf.Vec3f(*point) for point in world_points]
    particles.GetPointsAttr().Set(values)
    particles.GetPrim().CreateAttribute(
        "physxParticle:simulationPoints", Sdf.ValueTypeNames.Point3fArray
    ).Set(values)
    particles.GetWidthsAttr().Set(
        [recipe["particle_set"]["width_m"] / meters_per_unit] * len(values)
    )
    particles.GetVelocitiesAttr().Set([Gf.Vec3f(0.0)] * len(values))
    particles.GetPrim().CreateRelationship("physxParticle:particleSystem").SetTargets(
        [Sdf.Path(particle_system_path)]
    )
    particles.GetPrim().CreateAttribute(
        "physxParticle:fluid", Sdf.ValueTypeNames.Bool
    ).Set(True)
    particles.GetPrim().CreateAttribute(
        "physxParticle:selfCollision", Sdf.ValueTypeNames.Bool
    ).Set(True)
    particles.GetPrim().CreateAttribute(
        "physxParticle:particleGroup", Sdf.ValueTypeNames.Int
    ).Set(0)
    UsdPhysics.MassAPI.Apply(particles.GetPrim()).CreateMassAttr(
        recipe["particle_set"]["mass_kg"]
    )
    UsdShade.MaterialBindingAPI.Apply(particles.GetPrim()).Bind(material)
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
    if not analysis.get("physics_scene_path"):
        physics_path = liquid_root + "/PhysicsScene"
        physics_scene = UsdPhysics.Scene.Define(stage, physics_path)
        physics_scene.CreateGravityDirectionAttr(
            Gf.Vec3f(0, 0, -1) if up_axis == "Z" else Gf.Vec3f(0, -1, 0)
        )
        physics_scene.CreateGravityMagnitudeAttr(9.81 / meters_per_unit)
    stage.GetRootLayer().Save()
    return overlay, particle_system_path, particles_path, pbd_proxy_path


def _qualification_scene(scene: Path, overlay: Path, destination: Path) -> None:
    from pxr import Sdf  # type: ignore

    layer = Sdf.Layer.CreateNew(str(destination))
    # First sublayer is strongest; producer overrides must win over source opinions.
    layer.subLayerPaths = [overlay.name, str(scene.resolve())]
    layer.Save()


def build_autofill_candidate(
    *, request: Mapping[str, Any], output: Path
) -> dict[str, Any]:
    validate_request(request)
    output = Path(output)
    if output.exists():
        raise LiquidAutofillError(f"output already exists: {output}")
    output.mkdir(parents=True)
    scene = Path(str(request["scene"]))
    try:
        analysis = analyze_container(scene, str(request["container_prim"]))
        points = build_particle_lattice(
            analysis["cavity"],
            fill=float(request["target_settled_fill_ratio"]),
            radial_profile=(
                analysis.get("radial_profile")
                if request.get("collision_profile")
                == "task02_visual_mesh_convex_decomposition_v1"
                else None
            ),
            wall_clearance_m=(
                float(recipe_payload()["particle_system"]["effective_rest_offset_m"])
                if request.get("collision_profile")
                == "task02_visual_mesh_convex_decomposition_v1"
                else None
            ),
            target_particle_count=(
                int(request["initial_particle_count"])
                if request.get("initial_particle_count") is not None
                else None
            ),
        )
        collision_profile = request.get("collision_profile")
        overlay, particle_system, particles, pbd_proxy = _define_overlay(
            scene=scene,
            output=output,
            analysis=analysis,
            points_m=points,
            collision_profile=(str(collision_profile) if collision_profile else None),
        )
        qualification_scene = output / "qualification_scene.usda"
        _qualification_scene(scene, overlay, qualification_scene)
        _write_json(output / "analysis.json", analysis)
        _write_json(output / "recipe.json", recipe_payload())
        _write_json(
            output / "initial_seed.json",
            {
                "schema_version": "aan.gpu_pbd_initial_particle_state.v1",
                "coordinate_space": "target_prim_local_analysis_meters",
                "particle_count": len(points),
                "requested_initial_particle_count": request.get("initial_particle_count"),
                "positions": points,
                "target_settled_fill_ratio": request["target_settled_fill_ratio"],
                "initialization_profile": "task02_q95_lattice_v1",
                "state_semantics": "deterministic_pre_simulation_lattice",
                "runtime_qualification_required": True,
            },
        )
        result = {
            "schema_version": AUTOFILL_RESULT_SCHEMA,
            "overall_status": "candidate",
            "blocked_reasons": [],
            "source_binding": {
                "scene": str(scene.resolve()),
                "scene_sha256": _sha(scene),
                "container_prim": request["container_prim"],
                "fluid_interaction_profile": request.get("fluid_interaction_profile"),
            },
            "recipe": {
                "recipe_id": request["recipe_id"],
                "sha256": recipe_sha256(),
                "path": "recipe.json",
            },
            "entrypoints": {
                "overlay_usd": overlay.name,
                "qualification_scene": qualification_scene.name,
                "particle_system_prim": particle_system,
                "particle_set_prim": particles,
            },
            "fill_profile": {
                "measurement": "live_points_target_local_up_q95",
                "target_settled_fill_ratio": request["target_settled_fill_ratio"],
                "tolerance": 0.05,
                "particle_count": len(points),
                "initialization_profile": "task02_q95_lattice_v1",
            },
            "analysis": "analysis.json",
            "validation_fixture": request.get("validation_fixture"),
            "collision_profile": (
                {
                    "id": collision_profile,
                    "proxy_prim": pbd_proxy,
                    "source_visual_mesh": analysis["cavity"]["prim_path"],
                    "source_sdf_preserved": True,
                }
                if collision_profile
                else None
            ),
            "qualification": {"status": "not_run"},
            "claim_boundary": (
                "Candidate only until three Isaac 4.1 live-points cold runs pass; "
                "no robot, pour, metric, or benchmark claim."
            ),
        }
        _write_json(output / "manifest.json", result)
        return result
    except Exception as error:
        failure = {
            "schema_version": AUTOFILL_RESULT_SCHEMA,
            "overall_status": "blocked",
            "blocked_reasons": [str(error)],
            "source_binding": {
                "scene": str(scene.resolve()),
                "scene_sha256": _sha(scene) if scene.is_file() else None,
                "container_prim": request.get("container_prim"),
            },
            "qualification": {"status": "not_run"},
        }
        _write_json(output / "manifest.json", failure)
        raise


def qualify_candidate(
    *, output: Path, launcher: Path, worker: Path
) -> dict[str, Any]:
    output = Path(output)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("overall_status") != "candidate":
        raise LiquidAutofillError("only an unblocked candidate can be qualified")
    evidence = output / "evidence" / "runtime_qualification"
    evidence.mkdir(parents=True, exist_ok=False)
    runs: list[dict[str, Any]] = []
    runtime_environment = dict(os.environ)
    # ConvertAsset's static-USD wrapper may have injected another Isaac
    # installation into these variables.  The absolute launcher path is the
    # runtime authority; carrying the wrapper paths across that boundary can
    # silently mix 4.5 extensions into the EOS-managed 4.1 interpreter.
    for name in (
        "PYTHONPATH",
        "LD_LIBRARY_PATH",
        "CARB_APP_PATH",
        "EXP_PATH",
        "ISAAC_PATH",
        "ISAAC_SIM_ROOT",
    ):
        runtime_environment.pop(name, None)
    runtime_environment["ACCEPT_EULA"] = "Y"
    runtime_environment.setdefault("PRIVACY_CONSENT", "Y")
    for index in range(1, 4):
        destination = evidence / f"cold_run_{index}.json"
        completed = subprocess.run(
            [
                str(launcher),
                str(worker),
                "--scene",
                str(output / manifest["entrypoints"]["qualification_scene"]),
                "--analysis",
                str(output / manifest["analysis"]),
                "--manifest",
                str(manifest_path),
                "--run-index",
                str(index),
                "--out",
                str(destination),
            ],
            check=False,
            text=True,
            env=runtime_environment,
        )
        if completed.returncode != 0:
            raise LiquidAutofillError(
                f"Isaac autofill worker cold run {index} failed with {completed.returncode}"
            )
        runs.append(json.loads(destination.read_text(encoding="utf-8")))
    passed = all(run.get("overall_status") == "pass" for run in runs)
    report = {
        "schema_version": "aan.gpu_pbd_autofill_qualification_report.v1",
        "runtime": "isaac41",
        "required_cold_runs": 3,
        "run_count": len(runs),
        "checks": {
            "minimum_retention_ratio": 0.99,
            "settled_fill_ratio_tolerance": 0.05,
            "maximum_below_floor_count": 0,
            "maximum_translation_drift_m": 0.002,
            "maximum_tilt_drift_deg": 2.0,
            "particle_readback": "points",
        },
        "overall_status": "pass" if passed else "blocked",
        "runs": [path.name for path in sorted(evidence.glob("cold_run_*.json"))],
        "analysis_sha256": _sha(output / manifest["analysis"]),
        "recipe_sha256": recipe_sha256(),
    }
    report_path = evidence / "report.json"
    _write_json(report_path, report)
    manifest["qualification"] = {
        "status": report["overall_status"],
        "report": str(report_path.relative_to(output)),
        "report_sha256": _sha(report_path),
    }
    manifest["overall_status"] = "pass" if passed else "blocked"
    manifest["blocked_reasons"] = [] if passed else ["runtime_qualification_failed"]
    if passed:
        manifest["claim"] = "qualified_gpu_pbd_loaded_start"
    _write_json(manifest_path, manifest)
    if not passed:
        raise LiquidAutofillError("one or more Isaac 4.1 cold runs failed")
    return manifest
