"""Read-only source/package admission for grasp-section collision geometry.

The interaction runtime probes intentionally test cooked collision behaviour,
but they do not establish the outer envelope available to a parallel gripper.
This module closes that gap without changing either the source USD or a
consumer scene: it measures a declared body-local grasp band in metres from
the composed source visual mesh and every active package collision primitive.

The first profile-driven implementation supports package-owned ``Cube``
proxies exactly.  Any other enabled collision geometry blocks admission rather
than being silently excluded from the physical envelope.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any


ALGORITHM_ID = "aan.grasp_cross_section.v1"
CHECK_ID = "AAN-05G-grasp-cross-section"
_EPSILON_M = 1.0e-8
_CONFIG_FIELDS = {
    "required",
    "frame",
    "axis_body_local",
    "sample_offsets_body_local_usd",
    "source_visual_mesh_relative_paths",
    "closing_axis_body_local",
    "expected_visual_width_m",
    "visual_width_tolerance_m",
    "collision_visual_width_tolerance_m",
    "max_gripper_opening_m",
    "minimum_opening_clearance_m",
    "claim_boundary",
}


def resolve_grasp_cross_section_config(
    raw: Any,
    *,
    named_frames: dict[str, dict[str, Any]],
    open_top: dict[str, Any],
    errors: list[str],
) -> dict[str, Any] | None:
    """Validate the optional profile declaration without importing ``pxr``.

    Existing interaction-profile v1 inputs have no declaration and remain
    valid.  Once one is declared, its measurements are mandatory and
    fail-closed; this avoids a new profile field that can silently become an
    unaudited comment.
    """

    if raw is None:
        return None
    if not isinstance(raw, dict):
        errors.append("grasp_cross_section must be an object")
        return None
    if set(raw) != _CONFIG_FIELDS:
        errors.append(
            "grasp_cross_section must contain exactly "
            + ", ".join(sorted(_CONFIG_FIELDS))
        )
    required = raw.get("required")
    if not isinstance(required, bool):
        errors.append("grasp_cross_section.required must be boolean")
    elif not required:
        errors.append("grasp_cross_section.required must be true when declared")

    frame = raw.get("frame")
    if not isinstance(frame, str) or frame not in named_frames:
        errors.append("grasp_cross_section.frame must name an authoritative frame")
        frame = None

    axis = raw.get("axis_body_local")
    if not _unit_vector(axis, 3):
        errors.append("grasp_cross_section.axis_body_local must be a finite unit vec3")
    closing_axis = raw.get("closing_axis_body_local")
    if not _unit_vector(closing_axis, 3):
        errors.append(
            "grasp_cross_section.closing_axis_body_local must be a finite unit vec3"
        )
    if _unit_vector(axis, 3) and _unit_vector(closing_axis, 3):
        if not math.isclose(
            sum(float(a) * float(b) for a, b in zip(axis, closing_axis)),
            0.0,
            abs_tol=1.0e-5,
        ):
            errors.append(
                "grasp_cross_section.closing_axis_body_local must be perpendicular to axis_body_local"
            )
    open_axis = open_top.get("axis_body_local") if isinstance(open_top, dict) else None
    if _unit_vector(axis, 3) and _unit_vector(open_axis, 3):
        alignment = abs(sum(float(a) * float(b) for a, b in zip(axis, open_axis)))
        if not math.isclose(alignment, 1.0, rel_tol=0.0, abs_tol=1.0e-5):
            errors.append(
                "grasp_cross_section.axis_body_local must align with open_top.axis_body_local"
            )

    offsets = raw.get("sample_offsets_body_local_usd")
    if (
        not isinstance(offsets, list)
        or not offsets
        or not all(_finite_number(value) for value in offsets)
    ):
        errors.append(
            "grasp_cross_section.sample_offsets_body_local_usd must be a non-empty finite number list"
        )
        offsets = []
    else:
        normalized_offsets = [float(value) for value in offsets]
        if normalized_offsets != sorted(normalized_offsets):
            errors.append(
                "grasp_cross_section.sample_offsets_body_local_usd must be sorted"
            )
        if len(set(normalized_offsets)) != len(normalized_offsets):
            errors.append(
                "grasp_cross_section.sample_offsets_body_local_usd must not contain duplicates"
            )
        if not any(math.isclose(value, 0.0, abs_tol=1.0e-9) for value in normalized_offsets):
            errors.append(
                "grasp_cross_section.sample_offsets_body_local_usd must include the grasp frame plane (0)"
            )
        offsets = normalized_offsets

    visual_paths = raw.get("source_visual_mesh_relative_paths")
    if (
        not isinstance(visual_paths, list)
        or not visual_paths
        or any(not _valid_relative_path(path) for path in visual_paths)
        or len(set(visual_paths)) != len(visual_paths)
    ):
        errors.append(
            "grasp_cross_section.source_visual_mesh_relative_paths must be a non-empty unique list of safe root-relative paths"
        )
        visual_paths = []

    positive_fields = (
        "expected_visual_width_m",
        "visual_width_tolerance_m",
        "collision_visual_width_tolerance_m",
        "max_gripper_opening_m",
        "minimum_opening_clearance_m",
    )
    for field in positive_fields:
        if not _positive_finite(raw.get(field)):
            errors.append(f"grasp_cross_section.{field} must be positive and finite")
    if (
        _positive_finite(raw.get("expected_visual_width_m"))
        and _positive_finite(raw.get("max_gripper_opening_m"))
        and float(raw["max_gripper_opening_m"])
        <= float(raw["expected_visual_width_m"])
    ):
        errors.append(
            "grasp_cross_section.max_gripper_opening_m must exceed expected_visual_width_m"
        )
    boundary = raw.get("claim_boundary")
    if not isinstance(boundary, str) or not boundary.strip():
        errors.append("grasp_cross_section.claim_boundary must be a non-empty string")

    if errors:
        return None
    assert frame is not None
    return {
        "required": True,
        "frame": frame,
        "plane_origin_body_local_usd": list(
            named_frames[frame]["translation_body_local_usd"]
        ),
        "axis_body_local": [float(value) for value in axis],
        "sample_offsets_body_local_usd": offsets,
        "source_visual_mesh_relative_paths": list(visual_paths),
        "closing_axis_body_local": [float(value) for value in closing_axis],
        "expected_visual_width_m": float(raw["expected_visual_width_m"]),
        "visual_width_tolerance_m": float(raw["visual_width_tolerance_m"]),
        "collision_visual_width_tolerance_m": float(
            raw["collision_visual_width_tolerance_m"]
        ),
        "max_gripper_opening_m": float(raw["max_gripper_opening_m"]),
        "minimum_opening_clearance_m": float(raw["minimum_opening_clearance_m"]),
        "claim_boundary": boundary,
    }


def evaluate_grasp_cross_section(
    *,
    source_usd: Path,
    package_usd: Path,
    asset_entry_prim: str,
    grasp_cross_section: dict[str, Any],
    named_frames: dict[str, dict[str, Any]],
    declared_colliders: list[dict[str, Any]],
) -> dict[str, Any]:
    """Measure visual and collision envelopes for one source-bound grasp band.

    Coordinates are authored in the root body's USD-local space.  All
    dimensions in this report are calculated after composed transforms in
    world-space metres, which protects against the source mesh's local scale
    and root rotations.
    """

    report = _base_report(
        source_usd=source_usd,
        package_usd=package_usd,
        asset_entry_prim=asset_entry_prim,
        grasp_cross_section=grasp_cross_section,
    )
    try:
        from pxr import Gf, Usd, UsdGeom  # type: ignore

        source_stage = Usd.Stage.Open(str(source_usd))
        package_stage = Usd.Stage.Open(str(package_usd))
        if source_stage is None or package_stage is None:
            report["errors"].append("could not open source and package stages")
            return _finish_report(report)
        source_root = source_stage.GetPrimAtPath(asset_entry_prim)
        package_root = package_stage.GetPrimAtPath(asset_entry_prim)
        if not _valid_prim(source_root) or not _valid_prim(package_root):
            report["errors"].append(
                "asset_entry_prim must exist in both source and package stages"
            )
            return _finish_report(report)

        frame_name = grasp_cross_section.get("frame")
        frame = named_frames.get(frame_name) if isinstance(frame_name, str) else None
        if not isinstance(frame, dict) or not _finite_vector(
            frame.get("translation_body_local_usd"), 3
        ):
            report["errors"].append("grasp frame is absent or has no finite body-local origin")
            return _finish_report(report)
        origin_body = tuple(
            float(value) for value in frame["translation_body_local_usd"]
        )
        axis_body = _tuple3(grasp_cross_section.get("axis_body_local"))
        closing_body = _tuple3(grasp_cross_section.get("closing_axis_body_local"))
        if axis_body is None or closing_body is None:
            report["errors"].append("grasp cross-section vectors are invalid")
            return _finish_report(report)

        source_context = _stage_context(source_stage, source_root, axis_body, closing_body, Gf, UsdGeom)
        package_context = _stage_context(package_stage, package_root, axis_body, closing_body, Gf, UsdGeom)
        report["source"]["stage_metrics"] = source_context["stage_metrics"]
        report["package"]["stage_metrics"] = package_context["stage_metrics"]

        source_meshes = _source_visual_meshes(
            source_stage,
            source_root,
            grasp_cross_section.get("source_visual_mesh_relative_paths"),
        )
        package_meshes = _source_visual_meshes(
            package_stage,
            package_root,
            grasp_cross_section.get("source_visual_mesh_relative_paths"),
        )
        if source_meshes["errors"] or package_meshes["errors"]:
            report["errors"].extend(source_meshes["errors"])
            report["errors"].extend(package_meshes["errors"])
            report["source"]["visual_meshes"] = source_meshes["records"]
            report["package"]["visual_meshes"] = package_meshes["records"]
            return _finish_report(report)
        report["source"]["visual_meshes"] = source_meshes["records"]
        report["package"]["visual_meshes"] = package_meshes["records"]

        active_collisions = _active_package_collisions(package_stage, asset_entry_prim)
        report["package"]["active_collision_prims"] = active_collisions["active_paths"]
        report["package"]["disabled_collision_prims"] = active_collisions["disabled_paths"]
        report["summary"]["unsupported_active_collision_prims"] = active_collisions[
            "unsupported_paths"
        ]
        if active_collisions["errors"]:
            report["errors"].extend(active_collisions["errors"])

        purposes = {
            str(item.get("prim_path")): sorted(str(value) for value in item.get("purpose", []))
            for item in declared_colliders
            if isinstance(item, dict) and isinstance(item.get("prim_path"), str)
        }
        sample_reports: list[dict[str, Any]] = []
        support_intersections: set[str] = set()
        for offset in grasp_cross_section.get("sample_offsets_body_local_usd", []):
            offset_value = float(offset)
            source_plane = _plane_at_offset(source_context, origin_body, offset_value, axis_body)
            package_plane = _plane_at_offset(package_context, origin_body, offset_value, axis_body)
            source_visual = _measure_meshes(
                source_meshes["meshes"], source_context, source_plane, Gf, UsdGeom
            )
            package_visual = _measure_meshes(
                package_meshes["meshes"], package_context, package_plane, Gf, UsdGeom
            )
            collision = _measure_collisions(
                active_collisions["cubes"], package_plane, purposes, Gf
            )
            support_intersections.update(collision["support_intersecting_paths"])
            checks, sample_errors = _evaluate_sample(
                source_visual,
                package_visual,
                collision,
                grasp_cross_section,
            )
            sample_reports.append(
                {
                    "offset_body_local_usd": offset_value,
                    "source_visual": source_visual,
                    "package_visual": package_visual,
                    "collision": collision,
                    "checks": checks,
                    "errors": sample_errors,
                    "status": "pass" if not sample_errors else "blocked",
                }
            )
        report["samples"] = sample_reports
        report["summary"]["support_colliders_intersect_grasp_band"] = sorted(
            support_intersections
        )
        if support_intersections:
            report["errors"].append(
                "support collider(s) intersect the declared grasp band: "
                + ", ".join(sorted(support_intersections))
            )
        if not sample_reports:
            report["errors"].append("grasp cross-section has no sample planes")
    except Exception as exc:  # Fail closed for malformed USD/transforms too.
        report["errors"].append(f"grasp cross-section checker exception: {exc}")
    return _finish_report(report)


def _base_report(
    *,
    source_usd: Path,
    package_usd: Path,
    asset_entry_prim: str,
    grasp_cross_section: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "aan.grasp_cross_section_report.v1",
        "check_id": CHECK_ID,
        "algorithm_id": ALGORITHM_ID,
        "status": "blocked",
        "asset_entry_prim": asset_entry_prim,
        "source": {
            "path": str(source_usd),
            "sha256": _sha256_file(source_usd) if source_usd.is_file() else None,
            "stage_metrics": {},
            "visual_meshes": [],
        },
        "package": {
            "path": str(package_usd),
            "root_usd_sha256": _sha256_file(package_usd) if package_usd.is_file() else None,
            "stage_metrics": {},
            "visual_meshes": [],
            "active_collision_prims": [],
            "disabled_collision_prims": [],
        },
        "configuration": dict(grasp_cross_section),
        "samples": [],
        "summary": {
            "support_colliders_intersect_grasp_band": [],
            "unsupported_active_collision_prims": [],
        },
        "claim_boundary": grasp_cross_section.get("claim_boundary"),
        "errors": [],
    }


def _finish_report(report: dict[str, Any]) -> dict[str, Any]:
    sample_errors = [
        error
        for sample in report.get("samples", [])
        if isinstance(sample, dict)
        for error in sample.get("errors", [])
    ]
    report["summary"]["sample_count"] = len(report.get("samples", []))
    report["summary"]["sample_blocked_count"] = sum(
        1
        for sample in report.get("samples", [])
        if isinstance(sample, dict) and sample.get("status") != "pass"
    )
    report["summary"]["error_count"] = len(report.get("errors", [])) + len(sample_errors)
    report["status"] = (
        "pass"
        if report.get("samples")
        and not report.get("errors")
        and not sample_errors
        else "blocked"
    )
    return report


def _stage_context(stage: Any, root: Any, axis_body: tuple[float, float, float], closing_body: tuple[float, float, float], gf: Any, usd_geom: Any) -> dict[str, Any]:
    cache = usd_geom.XformCache()
    root_matrix = cache.GetLocalToWorldTransform(root)
    meters_per_unit = float(usd_geom.GetStageMetersPerUnit(stage))
    if not math.isfinite(meters_per_unit) or meters_per_unit <= 0.0:
        raise ValueError("stage metersPerUnit is not positive and finite")
    tangent_u, tangent_v = _plane_basis(axis_body)
    transformed_u = _normalize(_vec(root_matrix.TransformDir(gf.Vec3d(*tangent_u))))
    transformed_v = _normalize(_vec(root_matrix.TransformDir(gf.Vec3d(*tangent_v))))
    normal = _normalize(_cross(transformed_u, transformed_v))
    transformed_axis = _normalize(_vec(root_matrix.TransformDir(gf.Vec3d(*axis_body))))
    if _dot(normal, transformed_axis) < 0.0:
        normal = _scale(normal, -1.0)
    closing = _normalize(_vec(root_matrix.TransformDir(gf.Vec3d(*closing_body))))
    if abs(_dot(normal, closing)) > 1.0e-5:
        raise ValueError("transformed closing axis is not tangent to grasp plane")
    orthogonal = _normalize(_cross(normal, closing))
    body_x = _normalize(_vec(root_matrix.TransformDir(gf.Vec3d(1.0, 0.0, 0.0))))
    body_z = _normalize(_vec(root_matrix.TransformDir(gf.Vec3d(0.0, 0.0, 1.0))))
    return {
        "cache": cache,
        "root_matrix": root_matrix,
        "meters_per_unit": meters_per_unit,
        "normal": normal,
        "closing": closing,
        "orthogonal": orthogonal,
        "body_x": body_x,
        "body_z": body_z,
        "stage_metrics": {
            "meters_per_unit": meters_per_unit,
            "up_axis": str(usd_geom.GetStageUpAxis(stage)),
        },
    }


def _plane_at_offset(
    context: dict[str, Any],
    origin_body: tuple[float, float, float],
    offset: float,
    axis_body: tuple[float, float, float],
) -> dict[str, Any]:
    body_point = _add(origin_body, _scale(axis_body, offset))
    from pxr import Gf  # type: ignore

    point_world = context["root_matrix"].Transform(Gf.Vec3d(*body_point))
    origin_m = _scale(_vec(point_world), context["meters_per_unit"])
    return {
        "origin_m": origin_m,
        "meters_per_unit": context["meters_per_unit"],
        "normal": context["normal"],
        "closing": context["closing"],
        "orthogonal": context["orthogonal"],
        "body_x": context["body_x"],
        "body_z": context["body_z"],
    }


def _source_visual_meshes(stage: Any, root: Any, raw_paths: Any) -> dict[str, Any]:
    errors: list[str] = []
    meshes: list[Any] = []
    records: list[dict[str, Any]] = []
    if not isinstance(raw_paths, list) or not raw_paths:
        return {"errors": ["visual mesh paths are absent"], "meshes": [], "records": []}
    root_path = root.GetPath().pathString
    for relative in raw_paths:
        if not _valid_relative_path(relative):
            errors.append(f"invalid visual mesh relative path: {relative!r}")
            continue
        path = root_path.rstrip("/") + "/" + relative
        prim = stage.GetPrimAtPath(path)
        if not _valid_prim(prim) or prim.GetTypeName() != "Mesh":
            errors.append(f"declared visual mesh is not a valid Mesh: {path}")
            continue
        try:
            from pxr import UsdGeom  # type: ignore

            visibility = UsdGeom.Imageable(prim).ComputeVisibility()
            if str(visibility) == str(UsdGeom.Tokens.invisible):
                errors.append(f"declared visual mesh is invisible: {path}")
                continue
            mesh = UsdGeom.Mesh(prim)
            points = mesh.GetPointsAttr().Get()
            counts = mesh.GetFaceVertexCountsAttr().Get()
            indices = mesh.GetFaceVertexIndicesAttr().Get()
            if not _sequence(points):
                errors.append(f"declared visual mesh has no points: {path}")
                continue
            if not _sequence(counts) or not _sequence(indices):
                errors.append(f"declared visual mesh has no readable topology: {path}")
                continue
            if any(int(count) != 3 for count in counts):
                errors.append(f"declared visual mesh must use triangle topology: {path}")
                continue
            if len(indices) != 3 * len(counts):
                errors.append(f"declared visual mesh has inconsistent triangle indices: {path}")
                continue
            if any(not _finite_vector(point, 3) for point in points):
                errors.append(f"declared visual mesh has non-finite points: {path}")
                continue
            if any(
                not _valid_index(index, len(points))
                for index in indices
            ):
                errors.append(f"declared visual mesh has out-of-range triangle indices: {path}")
                continue
            records.append(
                {
                    "prim_path": path,
                    "point_count": len(points),
                    "triangle_count": len(counts),
                    "topology": "triangles",
                }
            )
            meshes.append(mesh)
        except Exception as exc:
            errors.append(f"could not read declared visual mesh {path}: {exc}")
    return {"errors": errors, "meshes": meshes, "records": records}


def _active_package_collisions(stage: Any, root_path: str) -> dict[str, Any]:
    active_paths: list[str] = []
    disabled_paths: list[str] = []
    unsupported_paths: list[str] = []
    errors: list[str] = []
    cubes: list[Any] = []
    prefix = root_path.rstrip("/") + "/"
    for prim in _all_prims(stage):
        path = prim.GetPath().pathString
        if path != root_path and not path.startswith(prefix):
            continue
        if "PhysicsCollisionAPI" not in _schema_tokens(prim):
            continue
        enabled_attr = prim.GetAttribute("physics:collisionEnabled")
        try:
            observed_enabled = enabled_attr.Get() if enabled_attr else None
            enabled = True if observed_enabled is None else observed_enabled
        except Exception:
            enabled = None
        if enabled is False:
            disabled_paths.append(path)
            continue
        if enabled is None:
            errors.append(f"collision enabled state is unreadable: {path}")
            continue
        active_paths.append(path)
        if prim.GetTypeName() != "Cube":
            unsupported_paths.append(path)
            continue
        cubes.append(prim)
    if not active_paths:
        errors.append("no active collision primitive exists under asset_entry_prim")
    if unsupported_paths:
        errors.append(
            "cannot prove the complete collision envelope for active non-Cube collision primitive(s): "
            + ", ".join(sorted(unsupported_paths))
        )
    return {
        "active_paths": sorted(active_paths),
        "disabled_paths": sorted(disabled_paths),
        "unsupported_paths": sorted(unsupported_paths),
        "cubes": cubes,
        "errors": errors,
    }


def _measure_meshes(meshes: list[Any], context: dict[str, Any], plane: dict[str, Any], gf: Any, usd_geom: Any) -> dict[str, Any]:
    points: list[tuple[float, float, float]] = []
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for mesh in meshes:
        prim = mesh.GetPrim()
        try:
            local_points = mesh.GetPointsAttr().Get()
            indices = mesh.GetFaceVertexIndicesAttr().Get()
            matrix = context["cache"].GetLocalToWorldTransform(prim)
            triangles = 0
            hits = 0
            coplanar = 0
            for start in range(0, len(indices), 3):
                triangle = [
                    _world_point_m(matrix, local_points[int(index)], context["meters_per_unit"], gf)
                    for index in indices[start : start + 3]
                ]
                triangles += 1
                intersection, was_coplanar = _polygon_plane_intersections(triangle, plane)
                if intersection:
                    hits += 1
                    points.extend(intersection)
                if was_coplanar:
                    coplanar += 1
            records.append(
                {
                    "prim_path": prim.GetPath().pathString,
                    "triangle_count": triangles,
                    "intersected_triangle_count": hits,
                    "coplanar_triangle_count": coplanar,
                }
            )
        except Exception as exc:
            errors.append(f"could not measure visual mesh {prim.GetPath()}: {exc}")
    return _measurement(points, plane, records, errors, primitive_kind="visual_mesh")


def _measure_collisions(cubes: list[Any], plane: dict[str, Any], purposes: dict[str, list[str]], gf: Any) -> dict[str, Any]:
    points: list[tuple[float, float, float]] = []
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    support_intersecting: list[str] = []
    support_gaps: list[float] = []
    for prim in cubes:
        path = prim.GetPath().pathString
        try:
            size_attr = prim.GetAttribute("size")
            size = size_attr.Get() if size_attr else 2.0
            if not _positive_finite(size):
                raise ValueError("Cube size is not positive and finite")
            from pxr import UsdGeom  # type: ignore

            matrix = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
            vertices = [
                _vec(matrix.Transform(gf.Vec3d(x, y, z)))
                for x in (-float(size) / 2.0, float(size) / 2.0)
                for y in (-float(size) / 2.0, float(size) / 2.0)
                for z in (-float(size) / 2.0, float(size) / 2.0)
            ]
            # The package stage carries the same metres-per-unit as its root.
            # ``plane`` is already metres, so derive it from the matrix points
            # through the recorded root stage conversion below.
            meters = _plane_meters_per_unit(plane)
            vertices = [_scale(vertex, meters) for vertex in vertices]
            intersection, coplanar = _cube_plane_intersections(vertices, plane)
            purpose = purposes.get(path, [])
            normal_gap = min(abs(_plane_distance(vertex, plane)) for vertex in vertices)
            record = {
                "prim_path": path,
                "purpose": purpose,
                "intersection_point_count": len(_dedupe(intersection)),
                "intersects_plane": bool(intersection),
                "coplanar_edge_count": coplanar,
                "minimum_normal_gap_m": 0.0 if intersection else normal_gap,
            }
            records.append(record)
            if "support" in purpose:
                support_gaps.append(record["minimum_normal_gap_m"])
                if intersection:
                    support_intersecting.append(path)
            if intersection:
                unique = _dedupe(intersection)
                if not _has_non_collinear_plane_points(unique, plane):
                    errors.append(
                        f"active collision Cube has only tangential grasp-plane contact: {path}"
                    )
                points.extend(unique)
        except Exception as exc:
            errors.append(f"could not measure active collision Cube {path}: {exc}")
    result = _measurement(points, plane, records, errors, primitive_kind="collision_cube")
    result["support_intersecting_paths"] = sorted(support_intersecting)
    result["support_min_normal_gap_m"] = min(support_gaps) if support_gaps else None
    return result


def _plane_meters_per_unit(plane: dict[str, Any]) -> float:
    # The evaluator keeps plane directions dimensionless; a private field avoids
    # passing stage state through every intersection helper.
    value = plane.get("meters_per_unit")
    if not _positive_finite(value):
        raise ValueError("plane metres-per-unit is absent")
    return float(value)


def _measurement(points: list[tuple[float, float, float]], plane: dict[str, Any], records: list[dict[str, Any]], errors: list[str], *, primitive_kind: str) -> dict[str, Any]:
    unique = _dedupe(points)
    result: dict[str, Any] = {
        "status": "blocked",
        "primitive_kind": primitive_kind,
        "records": records,
        "intersection_point_count": len(unique),
        "closing_axis_width_m": None,
        "orthogonal_axis_width_m": None,
        "body_local_x_span_m": None,
        "body_local_z_span_m": None,
        "max_in_plane_width_m": None,
        "errors": list(errors),
    }
    if not unique:
        result["errors"].append("no geometry intersects this grasp plane")
        return result
    if not _has_non_collinear_plane_points(unique, plane):
        result["errors"].append("grasp-plane intersection is degenerate")
        return result
    result.update(
        {
            "status": "pass",
            "closing_axis_width_m": _projection_width(unique, plane["closing"]),
            "orthogonal_axis_width_m": _projection_width(unique, plane["orthogonal"]),
            "body_local_x_span_m": _projection_width(unique, plane["body_x"]),
            "body_local_z_span_m": _projection_width(unique, plane["body_z"]),
            "max_in_plane_width_m": _max_pairwise_distance(unique),
        }
    )
    return result


def _evaluate_sample(source_visual: dict[str, Any], package_visual: dict[str, Any], collision: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, bool], list[str]]:
    errors: list[str] = []
    checks = {
        "source_visual_is_valid": source_visual.get("status") == "pass",
        "package_visual_is_valid": package_visual.get("status") == "pass",
        "collision_is_complete_and_valid": collision.get("status") == "pass",
        "source_visual_matches_expected": False,
        "package_visual_matches_source": False,
        "collision_matches_visual": False,
        "collision_within_max_gripper_opening": False,
        "support_clear_of_grasp_plane": not collision.get("support_intersecting_paths"),
    }
    for name, measurement in (
        ("source visual", source_visual),
        ("package visual", package_visual),
        ("collision", collision),
    ):
        if measurement.get("status") != "pass":
            errors.append(f"{name} geometry could not establish a non-degenerate grasp section")
    if errors:
        return checks, errors

    expected = float(config["expected_visual_width_m"])
    visual_tolerance = float(config["visual_width_tolerance_m"])
    collision_tolerance = float(config["collision_visual_width_tolerance_m"])
    source_width = float(source_visual["max_in_plane_width_m"])
    package_width = float(package_visual["max_in_plane_width_m"])
    collision_width = float(collision["max_in_plane_width_m"])
    checks["source_visual_matches_expected"] = abs(source_width - expected) <= visual_tolerance
    checks["package_visual_matches_source"] = abs(package_width - source_width) <= visual_tolerance
    width_deltas = (
        abs(collision_width - package_width),
        abs(
            float(collision["closing_axis_width_m"])
            - float(package_visual["closing_axis_width_m"])
        ),
        abs(
            float(collision["orthogonal_axis_width_m"])
            - float(package_visual["orthogonal_axis_width_m"])
        ),
    )
    checks["collision_matches_visual"] = all(
        delta <= collision_tolerance for delta in width_deltas
    )
    checks["collision_within_max_gripper_opening"] = (
        collision_width + float(config["minimum_opening_clearance_m"])
        <= float(config["max_gripper_opening_m"])
    )
    if not checks["source_visual_matches_expected"]:
        errors.append("source visual max in-plane width does not match the declared expected width")
    if not checks["package_visual_matches_source"]:
        errors.append("package visual max in-plane width differs from the immutable source visual")
    if not checks["collision_matches_visual"]:
        errors.append("collision envelope does not match the package visual grasp-section envelope")
    if not checks["collision_within_max_gripper_opening"]:
        errors.append("collision envelope plus required clearance exceeds max gripper opening")
    if not checks["support_clear_of_grasp_plane"]:
        errors.append("support collider intersects grasp plane")
    return checks, errors


def _world_point_m(matrix: Any, point: Any, meters_per_unit: float, gf: Any) -> tuple[float, float, float]:
    world = matrix.Transform(gf.Vec3d(float(point[0]), float(point[1]), float(point[2])))
    return _scale(_vec(world), meters_per_unit)


def _polygon_plane_intersections(vertices: list[tuple[float, float, float]], plane: dict[str, Any]) -> tuple[list[tuple[float, float, float]], bool]:
    points: list[tuple[float, float, float]] = []
    coplanar = False
    for index in range(len(vertices)):
        segment_points, segment_coplanar = _segment_plane_intersections(
            vertices[index], vertices[(index + 1) % len(vertices)], plane
        )
        points.extend(segment_points)
        coplanar = coplanar or segment_coplanar
    return _dedupe(points), coplanar


def _cube_plane_intersections(vertices: list[tuple[float, float, float]], plane: dict[str, Any]) -> tuple[list[tuple[float, float, float]], int]:
    edges = (
        (0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
        (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7),
    )
    points: list[tuple[float, float, float]] = []
    coplanar = 0
    for first, second in edges:
        segment_points, segment_coplanar = _segment_plane_intersections(
            vertices[first], vertices[second], plane
        )
        points.extend(segment_points)
        coplanar += int(segment_coplanar)
    return _dedupe(points), coplanar


def _segment_plane_intersections(first: tuple[float, float, float], second: tuple[float, float, float], plane: dict[str, Any]) -> tuple[list[tuple[float, float, float]], bool]:
    first_distance = _plane_distance(first, plane)
    second_distance = _plane_distance(second, plane)
    first_on = abs(first_distance) <= _EPSILON_M
    second_on = abs(second_distance) <= _EPSILON_M
    if first_on and second_on:
        return [first, second], True
    if first_on:
        return [first], False
    if second_on:
        return [second], False
    if first_distance * second_distance < 0.0:
        ratio = first_distance / (first_distance - second_distance)
        return [_add(first, _scale(_sub(second, first), ratio))], False
    return [], False


def _plane_distance(point: tuple[float, float, float], plane: dict[str, Any]) -> float:
    return _dot(_sub(point, plane["origin_m"]), plane["normal"])


def _has_non_collinear_plane_points(points: list[tuple[float, float, float]], plane: dict[str, Any]) -> bool:
    if len(points) < 3:
        return False
    origin = points[0]
    for first_index in range(1, len(points)):
        first = _sub(points[first_index], origin)
        if _length(first) <= _EPSILON_M:
            continue
        for second_index in range(first_index + 1, len(points)):
            second = _sub(points[second_index], origin)
            area = _length(_cross(first, _sub(points[second_index], origin)))
            if area > _EPSILON_M * _EPSILON_M:
                return True
    return False


def _projection_width(points: list[tuple[float, float, float]], direction: tuple[float, float, float]) -> float:
    projections = [_dot(point, direction) for point in points]
    return max(projections) - min(projections)


def _max_pairwise_distance(points: list[tuple[float, float, float]]) -> float:
    maximum = 0.0
    for index, first in enumerate(points):
        for second in points[index + 1 :]:
            maximum = max(maximum, _length(_sub(first, second)))
    return maximum


def _plane_basis(normal: tuple[float, float, float]) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    reference = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.9 else (0.0, 1.0, 0.0)
    first = _normalize(_cross(normal, reference))
    second = _normalize(_cross(normal, first))
    return first, second


def _dedupe(points: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    unique: list[tuple[float, float, float]] = []
    for point in points:
        if not any(_length(_sub(point, prior)) <= _EPSILON_M for prior in unique):
            unique.append(point)
    return unique


def _all_prims(stage: Any) -> list[Any]:
    try:
        return list(stage.TraverseAll())
    except Exception:
        return list(stage.Traverse())


def _schema_tokens(prim: Any) -> set[str]:
    tokens: set[str] = set()
    try:
        tokens.update(str(item) for item in prim.GetAppliedSchemas())
    except Exception:
        pass
    try:
        operation = prim.GetMetadata("apiSchemas")
        if hasattr(operation, "GetAppliedItems"):
            tokens.update(str(item) for item in operation.GetAppliedItems())
    except Exception:
        pass
    return tokens


def _valid_prim(prim: Any) -> bool:
    try:
        return bool(prim and prim.IsValid())
    except Exception:
        return False


def _valid_relative_path(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and not value.startswith("/")
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def _finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _positive_finite(value: Any) -> bool:
    return _finite_number(value) and float(value) > 0.0


def _finite_vector(value: Any, length: int) -> bool:
    try:
        return len(value) == length and all(_finite_number(item) for item in value)
    except (TypeError, ValueError):
        return False


def _sequence(value: Any) -> bool:
    try:
        return value is not None and len(value) > 0
    except (TypeError, ValueError):
        return False


def _valid_index(value: Any, point_count: int) -> bool:
    try:
        index = int(value)
    except (TypeError, ValueError):
        return False
    return not isinstance(value, bool) and index == value and 0 <= index < point_count


def _unit_vector(value: Any, length: int) -> bool:
    if not _finite_vector(value, length):
        return False
    norm = math.sqrt(sum(float(item) * float(item) for item in value))
    return math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1.0e-5)


def _tuple3(value: Any) -> tuple[float, float, float] | None:
    if not _finite_vector(value, 3):
        return None
    return (float(value[0]), float(value[1]), float(value[2]))


def _vec(value: Any) -> tuple[float, float, float]:
    return (float(value[0]), float(value[1]), float(value[2]))


def _add(first: tuple[float, float, float], second: tuple[float, float, float]) -> tuple[float, float, float]:
    return (first[0] + second[0], first[1] + second[1], first[2] + second[2])


def _sub(first: tuple[float, float, float], second: tuple[float, float, float]) -> tuple[float, float, float]:
    return (first[0] - second[0], first[1] - second[1], first[2] - second[2])


def _scale(value: tuple[float, float, float], scalar: float) -> tuple[float, float, float]:
    return (value[0] * scalar, value[1] * scalar, value[2] * scalar)


def _dot(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return first[0] * second[0] + first[1] * second[1] + first[2] * second[2]


def _cross(first: tuple[float, float, float], second: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _length(value: tuple[float, float, float]) -> float:
    return math.sqrt(_dot(value, value))


def _normalize(value: tuple[float, float, float]) -> tuple[float, float, float]:
    length = _length(value)
    if not math.isfinite(length) or length <= _EPSILON_M:
        raise ValueError("transform produced a degenerate direction")
    return _scale(value, 1.0 / length)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
