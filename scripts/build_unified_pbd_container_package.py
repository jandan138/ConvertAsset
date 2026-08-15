#!/usr/bin/env python3
"""Build a source-bound 0812-style unified GPU-PBD vessel candidate."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
from typing import Any, Sequence

from convert_asset.asset_application_normalizer.container_topology import (
    UnifiedCylindricalVesselSpec,
    analyze_mesh_topology,
    build_unified_cylindrical_vessel_mesh,
)


UNIFIED_MESH_SUFFIX = "__aan_pbd_collision_proxy/PBD_Unified_Vessel_Mesh"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _uvs(points: Sequence[Sequence[float]], *, bottom_z: float, top_z: float):
    from pxr import Gf

    height = top_z - bottom_z
    values = []
    for x, y, z in points:
        angle = math.atan2(float(y), float(x))
        u = (angle + math.pi) / (2.0 * math.pi)
        v = (float(z) - bottom_z) / height
        values.append(Gf.Vec2f(u, v))
    return values


def _load_and_warp_template_mesh(
    *,
    template_usd: Path,
    template_prim: str,
    spec: UnifiedCylindricalVesselSpec,
    seal_boundaries: bool,
    dimension_mapping: str,
    copy_mass_properties: bool,
    copy_authored_properties: bool,
) -> tuple[
    list[tuple[float, float, float]],
    list[int],
    list[int],
    float,
    Any | None,
    Any | None,
    list[tuple[str, Any, Any]],
    dict[str, Any],
]:
    """Bake a source mesh's composed topology into the target vessel frame.

    The template is a build-time provenance input only.  Its composed points are
    centered in XY, uniformly scaled to the requested outer radius, and scaled
    in Z to the requested bottom/rim band.  No reference to the template USD is
    authored into the output package.
    """
    from pxr import Gf, Usd, UsdGeom, UsdPhysics

    template_usd = template_usd.resolve()
    if not template_usd.is_file():
        raise FileNotFoundError(f"template USD does not exist: {template_usd}")
    stage = Usd.Stage.Open(str(template_usd))
    if stage is None:
        raise ValueError(f"cannot open template USD: {template_usd}")
    prim = stage.GetPrimAtPath(template_prim)
    if not prim.IsValid() or not prim.IsA(UsdGeom.Mesh):
        raise ValueError(f"template prim is not a mesh: {template_prim}")
    mesh = UsdGeom.Mesh(prim)
    local_points = mesh.GetPointsAttr().Get() or []
    counts = [int(value) for value in (mesh.GetFaceVertexCountsAttr().Get() or [])]
    indices = [int(value) for value in (mesh.GetFaceVertexIndicesAttr().Get() or [])]
    if not local_points or not counts or not indices:
        raise ValueError(f"template mesh has no topology: {template_prim}")
    source_face_count = len(counts)
    source_audit = analyze_mesh_topology(counts, indices)
    if source_audit.non_manifold_edge_count:
        raise ValueError(
            f"template mesh has non-manifold edges: {source_audit.non_manifold_edge_count}"
        )
    directed_edges: set[tuple[int, int]] = set()
    offset = 0
    for count in counts:
        face = indices[offset : offset + count]
        offset += count
        for start, end in zip(face, face[1:] + face[:1]):
            directed_edges.add((start, end))
    if seal_boundaries:
        for loop in source_audit.boundary_loops:
            ordered = list(loop)
            if len(ordered) < 3:
                raise ValueError("template mesh contains a degenerate boundary loop")
            # Existing boundary edges must be opposed by the sealing face.
            if (ordered[0], ordered[1]) in directed_edges:
                ordered.reverse()
            for index in range(1, len(ordered) - 1):
                counts.append(3)
                indices.extend((ordered[0], ordered[index], ordered[index + 1]))
    sealed_audit = analyze_mesh_topology(counts, indices)
    if (
        seal_boundaries
        and (sealed_audit.boundary_edge_count or sealed_audit.non_manifold_edge_count)
    ):
        raise ValueError(
            "template boundary sealing did not produce a closed manifold mesh"
        )
    transform = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    composed = [transform.Transform(point) for point in local_points]
    basis_scales = [
        transform.TransformDir(axis).GetLength()
        for axis in ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    ]
    local_coordinate_scale = sum(basis_scales) / len(basis_scales)
    if local_coordinate_scale <= 0.0:
        raise ValueError(f"template mesh has degenerate composed scale: {template_prim}")
    minimum = [min(float(point[index]) for point in composed) for index in range(3)]
    maximum = [max(float(point[index]) for point in composed) for index in range(3)]
    center_x = 0.5 * (minimum[0] + maximum[0])
    center_y = 0.5 * (minimum[1] + maximum[1])
    maximum_radius = max(
        math.hypot(float(point[0]) - center_x, float(point[1]) - center_y)
        for point in composed
    )
    source_height = maximum[2] - minimum[2]
    if maximum_radius <= 0.0 or source_height <= 0.0:
        raise ValueError(f"template mesh has degenerate bounds: {template_prim}")
    mesh_transform = None
    mesh_parent_transform = None
    template_xform_attrs: list[tuple[str, Any, Any]] = []
    remeshed = None
    if dimension_mapping == "fit_target_dimensions":
        target_outer_radius = max(
            spec.outer_radius,
            spec.rim_major_radius + spec.rim_radial_radius,
        )
        target_top_z = spec.rim_center_z + spec.rim_vertical_radius
        radial_scale = target_outer_radius / maximum_radius
        axial_scale = (target_top_z - spec.bottom_z) / source_height
    elif dimension_mapping == "recenter_only":
        target_outer_radius = maximum_radius
        target_top_z = spec.bottom_z + source_height
        radial_scale = 1.0
        axial_scale = 1.0
    elif dimension_mapping == "clone_local_frame_recentered":
        target_outer_radius = maximum_radius
        target_top_z = spec.bottom_z + source_height
        radial_scale = 1.0
        axial_scale = 1.0
        translation = transform.ExtractTranslation()
        mesh_transform = Gf.Matrix4d(transform)
        mesh_transform.SetTranslateOnly(
            Gf.Vec3d(
                translation[0] - center_x,
                translation[1] - center_y,
                translation[2] + spec.bottom_z - minimum[2],
            )
        )
    elif dimension_mapping == "clone_authored_xform_stack_recentered":
        target_outer_radius = maximum_radius
        target_top_z = spec.bottom_z + source_height
        radial_scale = 1.0
        axial_scale = 1.0
        translation = transform.ExtractTranslation()
        desired_composed = Gf.Matrix4d(transform)
        desired_composed.SetTranslateOnly(
            Gf.Vec3d(
                translation[0] - center_x,
                translation[1] - center_y,
                translation[2] + spec.bottom_z - minimum[2],
            )
        )
        xformable = UsdGeom.Xformable(prim)
        local_transform = xformable.GetLocalTransformation()
        mesh_parent_transform = local_transform.GetInverse() * desired_composed
        for op in xformable.GetOrderedXformOps():
            attr = op.GetAttr()
            template_xform_attrs.append(
                (attr.GetName(), attr.GetTypeName(), attr.Get())
            )
    elif dimension_mapping in (
        "remesh_measured_vessel",
        "remesh_measured_vessel_in_template_units",
    ):
        remeshed = build_unified_cylindrical_vessel_mesh(spec)
        target_outer_radius = max(
            spec.outer_radius,
            spec.rim_major_radius + spec.rim_radial_radius,
        )
        target_top_z = spec.rim_center_z + spec.rim_vertical_radius
        radial_scale = target_outer_radius / maximum_radius
        axial_scale = (target_top_z - spec.bottom_z) / source_height
        if dimension_mapping == "remesh_measured_vessel":
            local_coordinate_scale = 1.0
    else:
        raise ValueError(f"unsupported template dimension_mapping: {dimension_mapping}")
    if remeshed is not None:
        points = [
            tuple(float(value) / local_coordinate_scale for value in point)
            for point in remeshed.points
        ]
        counts = list(remeshed.face_vertex_counts)
        indices = list(remeshed.face_vertex_indices)
    elif mesh_transform is not None or template_xform_attrs:
        points = [tuple(float(value) for value in point) for point in local_points]
    else:
        world_points = [
            (
                (float(point[0]) - center_x) * radial_scale,
                (float(point[1]) - center_y) * radial_scale,
                spec.bottom_z + (float(point[2]) - minimum[2]) * axial_scale,
            )
            for point in composed
        ]
        points = [
            tuple(value / local_coordinate_scale for value in point)
            for point in world_points
        ]
    binding = {
        "usd": str(template_usd),
        "usd_sha256": _sha(template_usd),
        "prim": template_prim,
        "source_point_count": len(local_points),
        "source_face_count": source_face_count,
        "sealed_face_count": len(counts),
        "source_boundary_edge_count": source_audit.boundary_edge_count,
        "seal_boundaries": seal_boundaries,
        "sealed_boundary_loop_count": (
            source_audit.boundary_loop_count if seal_boundaries else 0
        ),
        "source_composed_bounds": {"minimum": minimum, "maximum": maximum},
        "mapping": {
            "mode": dimension_mapping,
            "xy_center": [center_x, center_y],
            "radial_scale": radial_scale,
            "axial_scale": axial_scale,
            "target_outer_radius_m": target_outer_radius,
            "target_bottom_z_m": spec.bottom_z,
            "target_top_z_m": target_top_z,
            "authored_mesh_scale": local_coordinate_scale,
        },
        "runtime_dependency": False,
        "authored_properties_copied": copy_authored_properties,
    }
    if copy_mass_properties:
        mass_api = UsdPhysics.MassAPI(prim)
        if not prim.HasAPI(UsdPhysics.MassAPI):
            raise ValueError(
                f"template prim has no PhysicsMassAPI to copy: {template_prim}"
            )
        mass = mass_api.GetMassAttr().Get()
        if mass is None or not math.isfinite(float(mass)) or float(mass) <= 0.0:
            raise ValueError(f"template prim has no positive mass: {template_prim}")
        binding["mass_properties"] = {"mass_kg": float(mass)}
    return (
        points,
        counts,
        indices,
        local_coordinate_scale,
        mesh_transform,
        mesh_parent_transform,
        template_xform_attrs,
        binding,
    )


def _author_cooking(
    prim: Any,
    recipe: str,
    *,
    contact_offset_m: float,
    rest_offset_m: float,
) -> dict[str, Any]:
    from pxr import Sdf

    def set_attr(name: str, type_name: Any, value: Any) -> None:
        attr = prim.GetAttribute(name)
        if not attr.IsValid():
            attr = prim.CreateAttribute(name, type_name)
        attr.Set(value)

    # Match liquid_0812: standard USD Physics APIs own the collider while the
    # PhysX cooking attributes remain authored properties. PhysxSchema is an
    # Isaac extension and must not become a pure-package import dependency.
    set_attr("physxCollision:contactOffset", Sdf.ValueTypeNames.Float, contact_offset_m)
    set_attr("physxCollision:restOffset", Sdf.ValueTypeNames.Float, rest_offset_m)
    set_attr(
        "physxConvexDecompositionCollision:minThickness", Sdf.ValueTypeNames.Float, 0.001
    )
    set_attr(
        "physxConvexDecompositionCollision:shrinkWrap", Sdf.ValueTypeNames.Bool, True
    )
    set_attr(
        "physxConvexDecompositionCollision:voxelResolution",
        Sdf.ValueTypeNames.UInt,
        500000,
    )
    authored: dict[str, Any] = {
        "approximation": "convexDecomposition",
        "contact_offset_m": contact_offset_m,
        "rest_offset_m": rest_offset_m,
        "min_thickness_m": 0.001,
        "shrink_wrap": True,
        "voxel_resolution": 500000,
    }
    if recipe == "current_r82":
        set_attr(
            "physxConvexDecompositionCollision:errorPercentage",
            Sdf.ValueTypeNames.Float,
            10.0,
        )
        set_attr(
            "physxConvexDecompositionCollision:hullVertexLimit",
            Sdf.ValueTypeNames.UInt,
            32,
        )
        set_attr(
            "physxConvexDecompositionCollision:maxConvexHulls",
            Sdf.ValueTypeNames.UInt,
            32,
        )
        authored.update(
            error_percentage=10.0,
            hull_vertex_limit=32,
            max_convex_hulls=32,
        )
    elif recipe == "liquid_0812_exact_diagnostic":
        set_attr(
            "physxConvexDecompositionCollision:errorPercentage",
            Sdf.ValueTypeNames.Float,
            0.0,
        )
        authored.update(
            error_percentage=0.0,
            diagnostic_only_invalid_for_promotion=True,
        )
    elif recipe == "liquid_0812_promotable":
        set_attr(
            "physxConvexDecompositionCollision:errorPercentage",
            Sdf.ValueTypeNames.Float,
            0.1,
        )
        authored["error_percentage"] = 0.1
    else:
        raise ValueError(f"unsupported cooking recipe: {recipe}")
    return authored


def build_unified_pbd_container_package(
    *,
    source_package: Path,
    output: Path,
    vessel_root: str,
    replaced_prim_paths: Sequence[str],
    glass_material_path: str,
    spec: UnifiedCylindricalVesselSpec,
    profile_id: str,
    cooking_recipe: str,
    contact_offset_m: float = 0.01,
    rest_offset_m: float = 0.001,
    template_usd: Path | None = None,
    template_prim: str | None = None,
    seal_template_boundaries: bool = True,
    template_dimension_mapping: str = "fit_target_dimensions",
    copy_template_mass_properties: bool = False,
    copy_template_authored_properties: bool = False,
    template_authored_property_scope: str = "all",
    collision_render_mode: str = "hidden_default_purpose",
) -> dict[str, Any]:
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics

    source_package = source_package.resolve()
    source_entrypoint = source_package / "asset.usd"
    if not source_entrypoint.is_file():
        raise FileNotFoundError(f"source package has no asset.usd: {source_package}")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite candidate package: {output}")
    source_sha = _sha(source_entrypoint)
    output.mkdir(parents=True)
    packaged_source = output / "deps/source_package"
    shutil.copytree(source_package, packaged_source)

    output_entrypoint = output / "asset.usd"
    copied_stage = Usd.Stage.Open(str(packaged_source / "asset.usd"))
    default_prim_name = copied_stage.GetDefaultPrim().GetName()
    overlay_rel = "overlays/unified_pbd_visible_vessel.usda"
    overlay_path = output / overlay_rel
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_layer = Sdf.Layer.CreateNew(str(overlay_path))
    root_layer = Sdf.Layer.CreateNew(str(output_entrypoint))
    root_layer.defaultPrim = default_prim_name
    root_layer.subLayerPaths = [overlay_rel, "deps/source_package/asset.usd"]
    root_layer.Save()

    generated = build_unified_cylindrical_vessel_mesh(spec)
    template_binding: dict[str, Any] | None = None
    if (template_usd is None) != (template_prim is None):
        raise ValueError("template_usd and template_prim must be provided together")
    if template_usd is not None and template_prim is not None:
        (
            points,
            face_counts,
            face_indices,
            mesh_local_scale,
            mesh_transform,
            mesh_parent_transform,
            template_xform_attrs,
            template_binding,
        ) = (
            _load_and_warp_template_mesh(
                template_usd=template_usd,
                template_prim=template_prim,
                spec=spec,
                seal_boundaries=seal_template_boundaries,
                dimension_mapping=template_dimension_mapping,
                copy_mass_properties=copy_template_mass_properties,
                copy_authored_properties=copy_template_authored_properties,
            )
        )
    else:
        points = list(generated.points)
        face_counts = list(generated.face_vertex_counts)
        face_indices = list(generated.face_vertex_indices)
        mesh_local_scale = 1.0
        mesh_transform = None
        mesh_parent_transform = None
        template_xform_attrs = []
    stage = Usd.Stage.Open(str(output_entrypoint))
    stage.SetEditTarget(overlay_layer)
    for path in replaced_prim_paths:
        prim = stage.GetPrimAtPath(path)
        if not prim.IsValid():
            raise ValueError(f"replaced prim does not exist: {path}")
    legacy_collision = stage.GetPrimAtPath(f"{vessel_root}/__aan_collision_proxy")
    if legacy_collision.IsValid():
        legacy_collision.SetActive(False)
    parent_path = f"{vessel_root}/{UNIFIED_MESH_SUFFIX.rsplit('/', 1)[0]}"
    mesh_path = f"{vessel_root}/{UNIFIED_MESH_SUFFIX}"
    collision_parent = UsdGeom.Xform.Define(stage, parent_path)
    if mesh_parent_transform is not None:
        UsdGeom.Xformable(collision_parent).AddTransformOp().Set(
            mesh_parent_transform
        )
    mesh = UsdGeom.Mesh.Define(stage, mesh_path)
    if copy_template_authored_properties:
        if template_usd is None or template_prim is None:
            raise ValueError(
                "copy_template_authored_properties requires a template mesh"
            )
        template_stage = Usd.Stage.Open(str(template_usd.resolve()))
        source_prim = template_stage.GetPrimAtPath(template_prim)
        api_schemas = source_prim.GetMetadata("apiSchemas")
        if api_schemas is not None:
            mesh.GetPrim().SetMetadata("apiSchemas", api_schemas)
        for source_attr in source_prim.GetAttributes():
            name = source_attr.GetName()
            if (
                not source_attr.HasAuthoredValueOpinion()
                or name.startswith("xformOp")
            ):
                continue
            if template_authored_property_scope == "physics_cooking" and not (
                name.startswith(("physics:", "physx", "newton:"))
                or name == "labutopia:nativeMeshCollisionEnabled"
            ):
                continue
            if template_authored_property_scope not in ("all", "physics_cooking"):
                raise ValueError(
                    "unsupported template_authored_property_scope: "
                    f"{template_authored_property_scope}"
                )
            target_attr = mesh.GetPrim().CreateAttribute(
                name,
                source_attr.GetTypeName(),
                custom=source_attr.IsCustom(),
                variability=source_attr.GetVariability(),
            )
            target_attr.Set(source_attr.Get())
    mesh.GetPointsAttr().Set(points)
    mesh.GetFaceVertexCountsAttr().Set(face_counts)
    mesh.GetFaceVertexIndicesAttr().Set(face_indices)
    mesh.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
    mesh.GetDoubleSidedAttr().Set(True)
    if template_xform_attrs:
        for name, type_name, value in template_xform_attrs:
            mesh.GetPrim().CreateAttribute(name, type_name).Set(value)
        mesh.GetPrim().CreateAttribute(
            "xformOpOrder", Sdf.ValueTypeNames.TokenArray
        ).Set([name for name, _, _ in template_xform_attrs])
    elif mesh_transform is not None:
        UsdGeom.Xformable(mesh).AddTransformOp().Set(mesh_transform)
    elif mesh_local_scale != 1.0:
        UsdGeom.Xformable(mesh).AddScaleOp().Set(
            (mesh_local_scale, mesh_local_scale, mesh_local_scale)
        )
    minimum = tuple(min(point[index] for point in points) for index in range(3))
    maximum = tuple(max(point[index] for point in points) for index in range(3))
    mesh.GetExtentAttr().Set([minimum, maximum])
    imageable = UsdGeom.Imageable(mesh.GetPrim())
    # Keep the collider in the default purpose.  Isaac/PhysX stage traversal
    # may omit guide-purpose prims even when CollisionAPI is authored.  It is
    # hidden by visibility, so this does not change the source visual.
    imageable.CreatePurposeAttr().Set(UsdGeom.Tokens.default_)
    if collision_render_mode == "hidden_default_purpose":
        imageable.CreateVisibilityAttr().Set(UsdGeom.Tokens.invisible)
    elif collision_render_mode == "source_parity_visible":
        imageable.CreateVisibilityAttr().Set(UsdGeom.Tokens.inherited)
    else:
        raise ValueError(f"unsupported collision_render_mode: {collision_render_mode}")
    collision = UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    collision.CreateCollisionEnabledAttr(True)
    mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim())
    mesh_collision.CreateApproximationAttr("convexDecomposition")
    if template_binding and "mass_properties" in template_binding:
        mass_api = UsdPhysics.MassAPI.Apply(mesh.GetPrim())
        mass_api.CreateMassAttr(
            float(template_binding["mass_properties"]["mass_kg"])
        )
    cooking = _author_cooking(
        mesh.GetPrim(),
        cooking_recipe,
        contact_offset_m=contact_offset_m,
        rest_offset_m=rest_offset_m,
    )
    overlay_layer.Save()

    composed = Usd.Stage.Open(str(output_entrypoint))
    composed_mesh = UsdGeom.Mesh(composed.GetPrimAtPath(mesh_path))
    audit = analyze_mesh_topology(
        composed_mesh.GetFaceVertexCountsAttr().Get() or [],
        composed_mesh.GetFaceVertexIndicesAttr().Get() or [],
    )
    topology = {
        "schema_version": "aan.unified_pbd_vessel_topology.v1",
        "profile_id": profile_id,
        "source_binding": {
            "package": str(source_package),
            "entrypoint_sha256": source_sha,
            "replaced_prim_paths": list(replaced_prim_paths),
        },
        "mesh_prim": mesh_path,
        "geometry": {
            "recipe": (
                "liquid_0812_topology_template_warp.v1"
                if template_binding
                else "source_measured_0812_style_unified_triangle_vessel.v1"
            ),
            "point_count": len(points),
            "face_count": len(face_counts),
            "all_triangle_faces": set(face_counts) == {3},
            "boundary_edge_count": audit.boundary_edge_count,
            "non_manifold_edge_count": audit.non_manifold_edge_count,
            "radial_side_count": generated.radial_side_count,
            "cavity_radius_m": generated.cavity_radius,
            "cavity_floor_z_m": generated.cavity_floor_z,
            "maximum_rim_chord_error_m": generated.maximum_rim_chord_error_m,
            "source_surface_tolerance_m": 0.0001,
            "render_and_collision_same_prim": False,
            "visual_source_unchanged": True,
            "body_axial_segments": spec.body_axial_segments,
            "sealed_template_boundary_loop_count": (
                template_binding["sealed_boundary_loop_count"]
                if template_binding
                else 0
            ),
        },
        "cooking": cooking,
        "claim_boundary": (
            "Topology and authored cooking candidate only. GPU compatibility and "
            "PBD retention require cold runtime qualification."
        ),
    }
    if template_binding is not None:
        topology["template_binding"] = template_binding
    _write_json(output / "evidence/unified_vessel_topology.json", topology)
    profile = {
        "schema_version": "aan.gpu_pbd_static_container_profile.v2",
        "profile_id": profile_id,
        "runtime_profile": "isaac41",
        "role": "gpu_pbd_static_container",
        "entrypoint": "asset.usd",
        "entry_prim": vessel_root,
        "collision": {
            "strategy": (
                "source_derived_single_closed_mesh_convex_decomposition"
                if audit.boundary_edge_count == 0
                else "source_derived_single_mesh_open_boundary_diagnostic"
            ),
            "mesh_prim": mesh_path,
            "render_and_collision_same_prim": False,
            "source_derived_not_primitive_proxy": True,
            "piece_approximation": "convexDecomposition",
            "piece_count": 1,
            "render_mode": collision_render_mode,
            "cooking_recipe": cooking_recipe,
            **cooking,
        },
        "visual_source_unchanged": True,
        "cavity": {
            "center_xy_m": [0.0, 0.0],
            "radius_m": spec.inner_radius,
            "floor_z_m": spec.floor_z,
            "rim_z_m": spec.rim_center_z + spec.rim_vertical_radius,
            "support_z_m": spec.bottom_z,
            "radial_profile": {
                "bottom_radius_m": spec.inner_radius,
                "top_radius_m": spec.inner_top_radius or spec.inner_radius,
            },
        },
        "topology_evidence": "evidence/unified_vessel_topology.json",
        "promotion": {
            "status": (
                "candidate"
                if audit.boundary_edge_count == 0
                else "diagnostic_not_promotable"
            ),
            "candidate_minimum_retention_ratio": 0.90,
            "final_maximum_outside_particles": 10,
            "required_runtime_gates": [
                "three_cold_live_points_runs",
                "gpu_cooking",
                "eight_second_retention_candidate_90pct",
                "eight_second_final_maximum_outside_10",
                "zero_below_support",
                "rtx_40_fps",
                "visual_source_unchanged",
            ],
        },
        "claim_boundary": (
            "Static GPU-PBD container candidate only. No pour, grasp, policy, "
            "benchmark, or full task success is claimed."
        ),
    }
    _write_json(output / "gpu_pbd_static_container_profile.json", profile)
    manifest = {
        "schema_version": "aan.source_bound_package_manifest.v1",
        "package_id": profile_id,
        "overall_status": "candidate",
        "entrypoints": {"root_usd": "asset.usd", "asset_entry_prim": vessel_root},
        "source_binding": topology["source_binding"],
        "gpu_pbd_static_container": {
            "status": "not_qualified",
            "profile": "gpu_pbd_static_container_profile.json",
        },
        "promotion": {"allowed": False, "reason": "runtime_gates_not_run"},
    }
    _write_json(output / "evidence/manifest.json", manifest)
    result = {
        "status": "candidate",
        "package": str(output.resolve()),
        "entrypoint": str(output_entrypoint.resolve()),
        "mesh_prim": mesh_path,
        "cooking_recipe": cooking_recipe,
    }
    _write_json(output / "evidence/build_result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--profile-id", required=True)
    parser.add_argument(
        "--cooking-recipe",
        choices=(
            "current_r82",
            "liquid_0812_exact_diagnostic",
            "liquid_0812_promotable",
        ),
        required=True,
    )
    args = parser.parse_args()
    root = "/World/GraduatedCylinder250ml"
    source = f"{root}/Visual/Source"
    spec = UnifiedCylindricalVesselSpec(
        outer_radius=0.02099,
        inner_radius=0.019185,
        bottom_z=0.0099,
        floor_z=0.011705,
        rim_center_z=0.27659,
        rim_major_radius=0.020825,
        rim_radial_radius=0.0011,
        rim_vertical_radius=0.00165,
        sides=32,
        body_axial_segments=32,
    )
    result = build_unified_pbd_container_package(
        source_package=args.source_package,
        output=args.out,
        vessel_root=root,
        replaced_prim_paths=(
            f"{source}/Hollow_Body",
            f"{source}/Closed_Inner_Bottom",
            f"{source}/Thickened_Rim",
        ),
        glass_material_path=f"{source}/_materials/USD_Glass_002",
        spec=spec,
        profile_id=args.profile_id,
        cooking_recipe=args.cooking_recipe,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
