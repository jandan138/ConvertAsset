#!/usr/bin/env python3
"""Build a source-bound visible closed-wall vessel candidate package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any

from convert_asset.asset_application_normalizer.container_topology import (
    analyze_mesh_topology,
    close_annular_wall_rim,
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _extend_face_varying_data(mesh: Any, added_corners: int) -> None:
    from pxr import Gf, UsdGeom

    normals = list(mesh.GetNormalsAttr().Get() or [])
    if normals and mesh.GetNormalsInterpolation() == UsdGeom.Tokens.faceVarying:
        normals.extend(Gf.Vec3f(0.0, 0.0, 1.0) for _ in range(added_corners))
        mesh.GetNormalsAttr().Set(normals)
    for primvar in UsdGeom.PrimvarsAPI(mesh).GetPrimvars():
        if primvar.GetInterpolation() != UsdGeom.Tokens.faceVarying:
            continue
        values = list(primvar.Get() or [])
        if not values:
            continue
        values.extend(values[0] for _ in range(added_corners))
        primvar.Set(values)


def build_closed_wall_package(
    *,
    source_package: Path,
    output: Path,
    mesh_prim: str,
    profile_id: str,
) -> dict[str, Any]:
    from pxr import Sdf, Usd, UsdGeom, UsdPhysics

    source_package = source_package.resolve()
    source_entrypoint = source_package / "asset.usd"
    if not source_entrypoint.is_file():
        raise FileNotFoundError(f"source package has no asset.usd: {source_package}")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite candidate package: {output}")
    shutil.copytree(source_package, output)

    output_entrypoint = output / "asset.usd"
    original_stage = Usd.Stage.Open(str(output_entrypoint))
    default_prim_name = original_stage.GetDefaultPrim().GetName()
    root_layer = original_stage.GetRootLayer()
    source_copy = output / "source_asset.usd"
    output_entrypoint.rename(source_copy)
    stage = Usd.Stage.Open(str(source_copy))
    source_mesh = UsdGeom.Mesh(stage.GetPrimAtPath(mesh_prim))
    if not source_mesh or not source_mesh.GetPrim().IsValid():
        raise ValueError(f"mesh prim does not exist: {mesh_prim}")
    points = list(source_mesh.GetPointsAttr().Get() or [])
    counts = list(source_mesh.GetFaceVertexCountsAttr().Get() or [])
    indices = list(source_mesh.GetFaceVertexIndicesAttr().Get() or [])
    before = analyze_mesh_topology(counts, indices)
    repair = close_annular_wall_rim(points, counts, indices)

    repair_rel = "overlays/closed_wall_visible_mesh.usda"
    repair_path = output / repair_rel
    repair_path.parent.mkdir(parents=True, exist_ok=True)
    repair_layer = Sdf.Layer.CreateNew(str(repair_path))
    root_layer.Clear()
    root_layer.defaultPrim = default_prim_name
    root_layer.subLayerPaths = [repair_rel, "source_asset.usd"]
    root_layer.Save()
    stage = Usd.Stage.Open(str(output_entrypoint))
    stage.SetEditTarget(repair_layer)
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath(mesh_prim))
    mesh.GetPointsAttr().Set(points)
    mesh.GetFaceVertexCountsAttr().Set(list(repair.face_vertex_counts))
    mesh.GetFaceVertexIndicesAttr().Set(list(repair.face_vertex_indices))
    _extend_face_varying_data(mesh, repair.added_face_count * 4)
    collision = UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    collision.CreateCollisionEnabledAttr(True)
    mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim())
    mesh_collision.CreateApproximationAttr("convexDecomposition")

    for prim in stage.Traverse():
        if prim.GetName() == "__aan_collision_proxy":
            prim.SetActive(False)
    repair_layer.Save()

    composed = Usd.Stage.Open(str(output_entrypoint))
    composed_mesh = UsdGeom.Mesh(composed.GetPrimAtPath(mesh_prim))
    after = analyze_mesh_topology(
        composed_mesh.GetFaceVertexCountsAttr().Get() or [],
        composed_mesh.GetFaceVertexIndicesAttr().Get() or [],
    )
    topology = {
        "schema_version": "aan.container_topology_evidence.v1",
        "profile_id": profile_id,
        "source": {
            "package": str(source_package),
            "entrypoint_sha256": _sha(source_entrypoint),
            "mesh_prim": mesh_prim,
            "point_count": len(points),
            "face_count": len(counts),
            "boundary_edge_count": before.boundary_edge_count,
            "boundary_loop_count": before.boundary_loop_count,
        },
        "repair": {
            "recipe": "close_coplanar_concentric_dual_rim_loops.v1",
            "source_points_preserved": True,
            "source_faces_preserved_as_prefix": True,
            "added_vertex_count": 0,
            "added_face_count": repair.added_face_count,
            "central_aperture_capped": False,
        },
        "result": {
            "face_count": len(repair.face_vertex_counts),
            "boundary_edge_count": after.boundary_edge_count,
            "boundary_loop_count": after.boundary_loop_count,
            "non_manifold_edge_count": after.non_manifold_edge_count,
            "collision_strategy": "visual_mesh_closed_wall_convex_decomposition",
            "render_visible": True,
        },
    }
    evidence_path = output / "evidence/container_topology.json"
    _write_json(evidence_path, topology)
    profile = {
        "schema_version": "aan.asset_role_admission_profile.v1",
        "profile_id": profile_id,
        "runtime_profile": "isaac41",
        "role": "liquid_container",
        "entrypoint": "asset.usd",
        "entry_prim": str(composed.GetDefaultPrim().GetPath()),
        "source_binding": {
            "package": str(source_package),
            "entrypoint_sha256": _sha(source_entrypoint),
        },
        "repair": topology["repair"],
        "container_collision": topology["result"],
        "topology_evidence": "evidence/container_topology.json",
        "promotion": {
            "status": "candidate",
            "required_runtime_gates": [
                "three_cold_five_update_runs",
                "eight_second_retention",
                "zero_below_support",
                "rtx_40_fps",
            ],
        },
        "claim_boundary": (
            "Candidate geometry only. No liquid retention, transfer, robot, policy, "
            "or benchmark success is claimed before runtime qualification."
        ),
    }
    _write_json(output / "asset_role_profile.json", profile)
    result = {
        "status": "candidate",
        "package": str(output.resolve()),
        "entrypoint": str(output_entrypoint.resolve()),
        "repair": topology["repair"],
        "topology": topology["result"],
    }
    _write_json(output / "evidence/build_result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-package", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mesh-prim", required=True)
    parser.add_argument("--profile-id", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            build_closed_wall_package(
                source_package=args.source_package,
                output=args.out,
                mesh_prim=args.mesh_prim,
                profile_id=args.profile_id,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
