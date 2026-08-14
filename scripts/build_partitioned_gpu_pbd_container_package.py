#!/usr/bin/env python3
"""Build a source-derived low-vertex GPU-convex vessel package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any

from convert_asset.asset_application_normalizer.container_topology import (
    UnifiedCylindricalVesselSpec,
    build_gpu_convex_vessel_partition,
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build_partitioned_package(
    *,
    unified_package: Path,
    output: Path,
    vessel_root: str,
    unified_mesh_prim: str,
    spec: UnifiedCylindricalVesselSpec,
    profile_id: str,
    contact_offset_m: float = 0.001,
    rest_offset_m: float = 0.0,
    voxel_resolution: int = 10000,
    piece_approximation: str = "convexDecomposition",
    collision_render_mode: str = "guide",
    support_bottom_z_m: float = 0.0,
    wall_vertical_segments: int = 8,
    reuse_rotated_wall_geometry: bool = False,
) -> dict[str, Any]:
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics

    unified_package = unified_package.resolve()
    source_entrypoint = unified_package / "asset.usd"
    if not source_entrypoint.is_file():
        raise FileNotFoundError(source_entrypoint)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite package: {output}")
    output.mkdir(parents=True)
    packaged_source = output / "deps/unified_source"
    shutil.copytree(unified_package, packaged_source)
    source_stage = Usd.Stage.Open(str(packaged_source / "asset.usd"))
    default_prim_name = source_stage.GetDefaultPrim().GetName()

    overlay_rel = "overlays/source_derived_gpu_convex_partition.usda"
    overlay_path = output / overlay_rel
    overlay_path.parent.mkdir(parents=True)
    overlay_layer = Sdf.Layer.CreateNew(str(overlay_path))
    root = Sdf.Layer.CreateNew(str(output / "asset.usd"))
    root.defaultPrim = default_prim_name
    root.subLayerPaths = [overlay_rel, "deps/unified_source/asset.usd"]
    root.Save()

    partition = build_gpu_convex_vessel_partition(
        spec,
        support_bottom_z=support_bottom_z_m,
        wall_vertical_segments=wall_vertical_segments,
        reuse_rotated_wall_geometry=reuse_rotated_wall_geometry,
    )
    stage = Usd.Stage.Open(str(output / "asset.usd"))
    stage.SetEditTarget(overlay_layer)
    visible = stage.GetPrimAtPath(unified_mesh_prim)
    if not visible.IsValid():
        raise ValueError(f"unified visible mesh does not exist: {unified_mesh_prim}")
    # Disabling collision alone still asks PhysX to pre-cook the source mesh.
    # Remove both applied APIs in the stronger overlay so the render mesh is
    # never presented to the GPU collision cooker.
    visible.RemoveAPI(UsdPhysics.MeshCollisionAPI)
    visible.RemoveAPI(UsdPhysics.CollisionAPI)
    collision_root_path = f"{vessel_root}/PBD_GPU_Collision"
    collision_root = UsdGeom.Xform.Define(stage, collision_root_path)
    if collision_render_mode == "guide":
        collision_root.GetPurposeAttr().Set(UsdGeom.Tokens.guide)
    elif collision_render_mode != "visible_diagnostic":
        raise ValueError(f"unsupported collision render mode: {collision_render_mode}")
    piece_records = []
    for piece in partition.pieces:
        mesh = UsdGeom.Mesh.Define(stage, f"{collision_root_path}/{piece.name}")
        mesh.GetPointsAttr().Set(piece.points)
        mesh.GetFaceVertexCountsAttr().Set(piece.face_vertex_counts)
        mesh.GetFaceVertexIndicesAttr().Set(piece.face_vertex_indices)
        if piece.rotation_z_degrees:
            UsdGeom.Xformable(mesh).AddRotateZOp().Set(piece.rotation_z_degrees)
        collision = UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        collision.CreateCollisionEnabledAttr(True)
        # Match the 0812 compound-collider convention: child meshes are
        # shapes owned by the vessel root actor, never independent bodies.
        mesh.GetPrim().CreateAttribute(
            "physics:rigidBodyEnabled", Sdf.ValueTypeNames.Bool
        ).Set(False)
        mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim())
        if piece_approximation not in {"convexDecomposition", "convexHull"}:
            raise ValueError(f"unsupported piece approximation: {piece_approximation}")
        mesh_collision.CreateApproximationAttr(piece_approximation)
        mesh.GetPrim().CreateAttribute(
            "physxCollision:contactOffset", Sdf.ValueTypeNames.Float
        ).Set(contact_offset_m)
        mesh.GetPrim().CreateAttribute(
            "physxCollision:restOffset", Sdf.ValueTypeNames.Float
        ).Set(rest_offset_m)
        if piece_approximation == "convexDecomposition":
            for name, value_type, value in (
                ("hullVertexLimit", Sdf.ValueTypeNames.UInt, 64),
                ("maxConvexHulls", Sdf.ValueTypeNames.UInt, 1),
                ("errorPercentage", Sdf.ValueTypeNames.Float, 0.1),
                ("voxelResolution", Sdf.ValueTypeNames.UInt, voxel_resolution),
                ("minThickness", Sdf.ValueTypeNames.Float, 0.001),
                ("shrinkWrap", Sdf.ValueTypeNames.Bool, True),
            ):
                mesh.GetPrim().CreateAttribute(
                    f"physxConvexDecompositionCollision:{name}", value_type
                ).Set(value)
        else:
            mesh.GetPrim().CreateAttribute(
                "physxConvexHullCollision:hullVertexLimit",
                Sdf.ValueTypeNames.UInt,
            ).Set(64)
            mesh.GetPrim().CreateAttribute(
                "physxConvexHullCollision:minThickness",
                Sdf.ValueTypeNames.Float,
            ).Set(0.001)
        piece_records.append(
            {
                "prim_path": str(mesh.GetPath()),
                "role": piece.role,
                "point_count": len(piece.points),
                "face_count": len(piece.face_vertex_counts),
                "approximation": piece_approximation,
                "rotation_z_degrees": piece.rotation_z_degrees,
            }
        )
    overlay_layer.Save()

    profile = {
        "schema_version": "aan.gpu_pbd_static_container_profile.v1",
        "profile_id": profile_id,
        "runtime_profile": "isaac41",
        "role": "gpu_pbd_static_container",
        "entrypoint": "asset.usd",
        "entry_prim": vessel_root,
        "collision": {
            "strategy": "source_derived_low_vertex_gpu_convex_partition",
            "root_prim": collision_root_path,
            "visible_mesh_prim": unified_mesh_prim,
            "render_and_collision_same_prim": False,
            "source_derived_not_primitive_proxy": True,
            "piece_count": len(partition.pieces),
            "wall_piece_count": partition.wall_piece_count,
            "bottom_piece_count": partition.bottom_piece_count,
            "maximum_inner_surface_error_m": partition.maximum_surface_error_m,
            "contact_offset_m": contact_offset_m,
            "rest_offset_m": rest_offset_m,
            "voxel_resolution": voxel_resolution,
            "piece_approximation": piece_approximation,
            "collision_render_mode": collision_render_mode,
            "support_bottom_z_m": support_bottom_z_m,
            "wall_vertical_segments": wall_vertical_segments,
            "reuse_rotated_wall_geometry": reuse_rotated_wall_geometry,
            "support_bottom_source_prims": [
                f"{vessel_root}/Visual/Source/Hex_Base/Cylinder_004",
                f"{vessel_root}/Visual/Source/Base_Connector/Cylinder_005",
            ],
        },
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
            "Static GPU-PBD container candidate only. Collision pieces are "
            "source-derived geometry, not primitive proxies."
        ),
    }
    _write_json(output / "gpu_pbd_static_container_profile.json", profile)
    evidence = {
        "schema_version": "aan.gpu_convex_vessel_partition.v1",
        "profile_id": profile_id,
        "source_binding": {
            "package": str(unified_package),
            "entrypoint_sha256": _sha(source_entrypoint),
            "unified_visible_mesh_prim": unified_mesh_prim,
        },
        "partition": profile["collision"],
        "pieces": piece_records,
        "claim_boundary": (
            "Authored low-vertex convex topology only; GPU cooking requires "
            "runtime qualification."
        ),
    }
    _write_json(output / "evidence/gpu_convex_partition.json", evidence)
    manifest = {
        "schema_version": "aan.source_bound_package_manifest.v1",
        "package_id": profile_id,
        "overall_status": "candidate",
        "entrypoints": {"root_usd": "asset.usd", "asset_entry_prim": vessel_root},
        "source_binding": evidence["source_binding"],
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
        "piece_count": len(partition.pieces),
        "collision_root": collision_root_path,
    }
    _write_json(output / "evidence/build_result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unified-package", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--profile-id", required=True)
    parser.add_argument("--contact-offset-m", type=float, default=0.001)
    parser.add_argument("--rest-offset-m", type=float, default=0.0)
    parser.add_argument("--voxel-resolution", type=int, default=10000)
    parser.add_argument("--wall-vertical-segments", type=int, default=8)
    parser.add_argument(
        "--reuse-rotated-wall-geometry", action="store_true"
    )
    parser.add_argument(
        "--piece-approximation",
        choices=("convexDecomposition", "convexHull"),
        default="convexDecomposition",
    )
    parser.add_argument(
        "--collision-render-mode",
        choices=("guide", "visible_diagnostic"),
        default="guide",
    )
    args = parser.parse_args()
    root = "/World/GraduatedCylinder250ml"
    mesh = (
        f"{root}/Visual/Source/PBD_Unified_Vessel/PBD_Unified_Vessel_Mesh"
    )
    result = build_partitioned_package(
        unified_package=args.unified_package,
        output=args.out,
        vessel_root=root,
        unified_mesh_prim=mesh,
        spec=UnifiedCylindricalVesselSpec(
            outer_radius=0.02099,
            inner_radius=0.019185,
            bottom_z=0.0099,
            floor_z=0.011705,
            rim_center_z=0.27659,
            rim_major_radius=0.020825,
            rim_radial_radius=0.0011,
            rim_vertical_radius=0.00165,
        ),
        profile_id=args.profile_id,
        contact_offset_m=args.contact_offset_m,
        rest_offset_m=args.rest_offset_m,
        voxel_resolution=args.voxel_resolution,
        piece_approximation=args.piece_approximation,
        collision_render_mode=args.collision_render_mode,
        wall_vertical_segments=args.wall_vertical_segments,
        reuse_rotated_wall_geometry=args.reuse_rotated_wall_geometry,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
