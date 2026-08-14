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


UNIFIED_MESH_SUFFIX = "Visual/Source/PBD_Unified_Vessel/PBD_Unified_Vessel_Mesh"


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


def _author_cooking(prim: Any, recipe: str) -> dict[str, Any]:
    from pxr import Sdf

    # Match liquid_0812: standard USD Physics APIs own the collider while the
    # PhysX cooking attributes remain authored properties. PhysxSchema is an
    # Isaac extension and must not become a pure-package import dependency.
    prim.CreateAttribute(
        "physxCollision:contactOffset", Sdf.ValueTypeNames.Float
    ).Set(0.01)
    prim.CreateAttribute(
        "physxCollision:restOffset", Sdf.ValueTypeNames.Float
    ).Set(0.001)
    prim.CreateAttribute(
        "physxConvexDecompositionCollision:minThickness", Sdf.ValueTypeNames.Float
    ).Set(0.001)
    prim.CreateAttribute(
        "physxConvexDecompositionCollision:shrinkWrap", Sdf.ValueTypeNames.Bool
    ).Set(True)
    prim.CreateAttribute(
        "physxConvexDecompositionCollision:voxelResolution",
        Sdf.ValueTypeNames.UInt,
    ).Set(500000)
    authored: dict[str, Any] = {
        "approximation": "convexDecomposition",
        "contact_offset_m": 0.01,
        "rest_offset_m": 0.001,
        "min_thickness_m": 0.001,
        "shrink_wrap": True,
        "voxel_resolution": 500000,
    }
    if recipe == "current_r82":
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
        ).Set(32)
        authored.update(
            error_percentage=10.0,
            hull_vertex_limit=32,
            max_convex_hulls=32,
        )
    elif recipe == "liquid_0812_exact_diagnostic":
        prim.CreateAttribute(
            "physxConvexDecompositionCollision:errorPercentage",
            Sdf.ValueTypeNames.Float,
        ).Set(0.0)
        authored.update(
            error_percentage=0.0,
            diagnostic_only_invalid_for_promotion=True,
        )
    elif recipe == "liquid_0812_promotable":
        prim.CreateAttribute(
            "physxConvexDecompositionCollision:errorPercentage",
            Sdf.ValueTypeNames.Float,
        ).Set(0.01)
        authored["error_percentage"] = 0.01
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
) -> dict[str, Any]:
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

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
    stage = Usd.Stage.Open(str(output_entrypoint))
    stage.SetEditTarget(overlay_layer)
    for path in replaced_prim_paths:
        prim = stage.GetPrimAtPath(path)
        if not prim.IsValid():
            raise ValueError(f"replaced prim does not exist: {path}")
        prim.SetActive(False)
    parent_path = f"{vessel_root}/{UNIFIED_MESH_SUFFIX.rsplit('/', 1)[0]}"
    mesh_path = f"{vessel_root}/{UNIFIED_MESH_SUFFIX}"
    UsdGeom.Xform.Define(stage, parent_path)
    mesh = UsdGeom.Mesh.Define(stage, mesh_path)
    mesh.GetPointsAttr().Set(generated.points)
    mesh.GetFaceVertexCountsAttr().Set(generated.face_vertex_counts)
    mesh.GetFaceVertexIndicesAttr().Set(generated.face_vertex_indices)
    minimum = tuple(min(point[index] for point in generated.points) for index in range(3))
    maximum = tuple(max(point[index] for point in generated.points) for index in range(3))
    mesh.GetExtentAttr().Set([minimum, maximum])
    primvars = UsdGeom.PrimvarsAPI(mesh)
    st = primvars.CreatePrimvar(
        "st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex
    )
    st.Set(_uvs(generated.points, bottom_z=spec.bottom_z, top_z=maximum[2]))
    material_prim = stage.GetPrimAtPath(glass_material_path)
    if not material_prim.IsValid():
        raise ValueError(f"glass material does not exist: {glass_material_path}")
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(
        UsdShade.Material(material_prim)
    )
    collision = UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    collision.CreateCollisionEnabledAttr(True)
    mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim())
    mesh_collision.CreateApproximationAttr("convexDecomposition")
    cooking = _author_cooking(mesh.GetPrim(), cooking_recipe)
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
            "recipe": "source_measured_0812_style_unified_triangle_vessel.v1",
            "point_count": len(generated.points),
            "face_count": len(generated.face_vertex_counts),
            "all_triangle_faces": set(generated.face_vertex_counts) == {3},
            "boundary_edge_count": audit.boundary_edge_count,
            "non_manifold_edge_count": audit.non_manifold_edge_count,
            "radial_side_count": generated.radial_side_count,
            "cavity_radius_m": generated.cavity_radius,
            "cavity_floor_z_m": generated.cavity_floor_z,
            "maximum_rim_chord_error_m": generated.maximum_rim_chord_error_m,
            "source_surface_tolerance_m": 0.0001,
            "render_and_collision_same_prim": True,
        },
        "cooking": cooking,
        "claim_boundary": (
            "Topology and authored cooking candidate only. GPU compatibility and "
            "PBD retention require cold runtime qualification."
        ),
    }
    _write_json(output / "evidence/unified_vessel_topology.json", topology)
    profile = {
        "schema_version": "aan.gpu_pbd_static_container_profile.v1",
        "profile_id": profile_id,
        "runtime_profile": "isaac41",
        "role": "gpu_pbd_static_container",
        "entrypoint": "asset.usd",
        "entry_prim": vessel_root,
        "collision": {
            "strategy": "unified_visible_triangle_mesh_convex_decomposition",
            "mesh_prim": mesh_path,
            "render_and_collision_same_prim": True,
            "cooking_recipe": cooking_recipe,
        },
        "topology_evidence": "evidence/unified_vessel_topology.json",
        "promotion": {
            "status": "candidate",
            "required_runtime_gates": [
                "three_cold_five_update_runs",
                "gpu_cooking",
                "eight_second_retention_95pct",
                "zero_below_support",
                "rtx_40_fps",
                "visual_equivalence",
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
