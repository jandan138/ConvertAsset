#!/usr/bin/env python3
"""Build dynamic interaction variants from the promoted exact Wangshuai assets."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np


DEFAULT_EXACT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "wangshuai_funnel_tube15_exact_asset_set_20260826"
)
DEFAULT_OUT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "wangshuai_funnel_tube15_dynamic_asset_set_20260827"
)


DYNAMIC_SPECS = {
    "tube15_threaded_liquid_dynamic": {
        "exact_id": "tube15_threaded_liquid_ready",
        "profile_id": "wangshuai.tube15_threaded.dynamic.v1",
        "mass_properties": {
            "mass_kg": 0.015,
            "center_of_mass_body_local_m": [0.0, 0.0, 0.052],
            "diagonal_inertia_kg_m2": [1.3e-5, 1.3e-5, 5.2e-7],
            "principal_axes_wxyz": [1.0, 0.0, 0.0, 0.0],
            "method": "reused_same_geometry_provisional_profile_r7",
        },
    },
    "tube15_threaded_closed_cap_dynamic": {
        "exact_id": "tube15_threaded_closed_cap",
        "profile_id": "wangshuai.tube15_threaded_closed_cap.dynamic.v1",
        "mesh_relative_path": "/node_/mesh_",
        "target_mass_kg": 0.002,
        "method": "geometry_inertia_normalized_to_prior_cap_mass",
    },
    "funnel_small_v2_liquid_dynamic": {
        "exact_id": "funnel_small_v2_liquid_ready",
        "profile_id": "wangshuai.funnel_small_v2.dynamic.v1",
        "mesh_relative_path": "/Visual",
        "density_kg_m3": 2230.0,
        "method": "closed_mesh_tetrahedral_integration_borosilicate_density",
    },
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _rotation_matrix_to_quaternion(matrix: np.ndarray) -> list[float]:
    trace = float(np.trace(matrix))
    if trace > 0.0:
        scale = (trace + 1.0) ** 0.5 * 2.0
        w = 0.25 * scale
        x = (matrix[2, 1] - matrix[1, 2]) / scale
        y = (matrix[0, 2] - matrix[2, 0]) / scale
        z = (matrix[1, 0] - matrix[0, 1]) / scale
    else:
        axis = int(np.argmax(np.diag(matrix)))
        if axis == 0:
            scale = (1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2]) ** 0.5 * 2.0
            w = (matrix[2, 1] - matrix[1, 2]) / scale
            x = 0.25 * scale
            y = (matrix[0, 1] + matrix[1, 0]) / scale
            z = (matrix[0, 2] + matrix[2, 0]) / scale
        elif axis == 1:
            scale = (1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2]) ** 0.5 * 2.0
            w = (matrix[0, 2] - matrix[2, 0]) / scale
            x = (matrix[0, 1] + matrix[1, 0]) / scale
            y = 0.25 * scale
            z = (matrix[1, 2] + matrix[2, 1]) / scale
        else:
            scale = (1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1]) ** 0.5 * 2.0
            w = (matrix[1, 0] - matrix[0, 1]) / scale
            x = (matrix[0, 2] + matrix[2, 0]) / scale
            y = (matrix[1, 2] + matrix[2, 1]) / scale
            z = 0.25 * scale
    quaternion = np.asarray([w, x, y, z], dtype=float)
    quaternion /= np.linalg.norm(quaternion)
    if quaternion[0] < 0.0:
        quaternion *= -1.0
    return quaternion.tolist()


def mesh_mass_properties(
    stage: Any,
    mesh_path: str,
    *,
    density_kg_m3: float = 1.0,
    target_mass_kg: float | None = None,
) -> dict[str, Any]:
    """Integrate a closed triangle mesh in entry-root coordinates."""

    from pxr import Gf, UsdGeom

    mesh_prim = stage.GetPrimAtPath(mesh_path)
    mesh = UsdGeom.Mesh(mesh_prim)
    transform = UsdGeom.XformCache().GetLocalToWorldTransform(mesh_prim)
    points = np.asarray(
        [transform.Transform(Gf.Vec3d(*point)) for point in mesh.GetPointsAttr().Get()],
        dtype=float,
    )
    counts = list(mesh.GetFaceVertexCountsAttr().Get())
    indices = list(mesh.GetFaceVertexIndicesAttr().Get())
    volume = 0.0
    first = np.zeros(3)
    second = np.zeros((3, 3))
    offset = 0
    for count in counts:
        face = indices[offset : offset + count]
        offset += count
        for index in range(1, count - 1):
            vertices = np.asarray(
                [points[face[0]], points[face[index]], points[face[index + 1]]]
            )
            signed_volume = float(
                np.dot(vertices[0], np.cross(vertices[1], vertices[2])) / 6.0
            )
            volume += signed_volume
            first += signed_volume * vertices.sum(axis=0) / 4.0
            for row in range(3):
                for column in range(3):
                    diagonal = sum(
                        vertices[i, row] * vertices[i, column] for i in range(3)
                    ) / 10.0
                    off_diagonal = sum(
                        vertices[i, row] * vertices[j, column]
                        for i in range(3)
                        for j in range(3)
                        if i != j
                    ) / 20.0
                    second[row, column] += signed_volume * (
                        diagonal + off_diagonal
                    )
    if volume < 0.0:
        volume *= -1.0
        first *= -1.0
        second *= -1.0
    if volume <= 0.0 or not np.isfinite(volume):
        raise RuntimeError(f"mesh is not a positive closed volume: {mesh_path}")
    center = first / volume
    density = (
        float(target_mass_kg) / volume
        if target_mass_kg is not None
        else float(density_kg_m3)
    )
    mass = density * volume
    inertia_origin = density * np.asarray(
        [
            [second[1, 1] + second[2, 2], -second[0, 1], -second[0, 2]],
            [-second[1, 0], second[0, 0] + second[2, 2], -second[1, 2]],
            [-second[2, 0], -second[2, 1], second[0, 0] + second[1, 1]],
        ]
    )
    shift = mass * ((np.dot(center, center) * np.eye(3)) - np.outer(center, center))
    inertia_center = (inertia_origin - shift + (inertia_origin - shift).T) * 0.5
    eigenvalues, eigenvectors = np.linalg.eigh(inertia_center)
    if np.linalg.det(eigenvectors) < 0.0:
        eigenvectors[:, 0] *= -1.0
    if np.any(eigenvalues <= 0.0) or not np.all(np.isfinite(eigenvalues)):
        raise RuntimeError(f"invalid integrated inertia: {mesh_path}")
    return {
        "volume_m3": volume,
        "density_kg_m3": density,
        "mass_kg": mass,
        "center_of_mass_body_local_m": center.tolist(),
        "diagonal_inertia_kg_m2": eigenvalues.tolist(),
        "principal_axes_wxyz": _rotation_matrix_to_quaternion(eigenvectors),
    }


def _collision_signature(stage: Any, root_path: str) -> str:
    from pxr import UsdGeom, UsdPhysics

    records = []
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        if not path.startswith(root_path) or not prim.HasAPI(UsdPhysics.CollisionAPI):
            continue
        attrs = {
            attr.GetName(): repr(attr.Get())
            for attr in prim.GetAttributes()
            if attr.GetName().startswith(("physics:", "physx"))
            and attr.HasAuthoredValueOpinion()
        }
        mesh_hash = None
        if prim.IsA(UsdGeom.Mesh):
            mesh = UsdGeom.Mesh(prim)
            digest = sha256()
            for attr in (
                mesh.GetPointsAttr(),
                mesh.GetFaceVertexCountsAttr(),
                mesh.GetFaceVertexIndicesAttr(),
            ):
                digest.update(repr(list(attr.Get())).encode())
            mesh_hash = digest.hexdigest()
        records.append(
            {
                "path": path[len(root_path) :] or "/",
                "schemas": list(prim.GetAppliedSchemas()),
                "attributes": attrs,
                "mesh_sha256": mesh_hash,
            }
        )
    return sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()


def _author_mass(stage: Any, root: Any, properties: dict[str, Any]) -> None:
    from pxr import Gf, UsdPhysics

    root.RemoveProperty("physics:kinematicEnabled")
    rigid = UsdPhysics.RigidBodyAPI.Apply(root)
    rigid.CreateRigidBodyEnabledAttr(True)
    mass = UsdPhysics.MassAPI.Apply(root)
    mass.CreateMassAttr(float(properties["mass_kg"]))
    mass.CreateDensityAttr(0.0)
    mass.CreateCenterOfMassAttr(
        Gf.Vec3f(*properties["center_of_mass_body_local_m"])
    )
    mass.CreateDiagonalInertiaAttr(Gf.Vec3f(*properties["diagonal_inertia_kg_m2"]))
    quaternion = properties["principal_axes_wxyz"]
    mass.CreatePrincipalAxesAttr(
        Gf.Quatf(float(quaternion[0]), Gf.Vec3f(*quaternion[1:]))
    )


def _build_dynamic_package(
    exact_root: Path, output: Path, asset_id: str, spec: dict[str, Any]
) -> dict[str, Any]:
    from pxr import Usd

    exact_package = exact_root / "packages" / spec["exact_id"]
    shutil.copytree(exact_package, output)
    exact_manifest_path = output / "evidence/manifest.json"
    exact_manifest = json.loads(exact_manifest_path.read_text())
    shutil.copy2(exact_manifest_path, output / "evidence/exact_source_manifest.json")
    asset = output / "asset.usda"
    stage = Usd.Stage.Open(str(asset))
    root = stage.GetDefaultPrim()
    root_path = str(root.GetPath())
    collision_before = _collision_signature(stage, root_path)
    if "mass_properties" in spec:
        properties = dict(spec["mass_properties"])
    else:
        properties = mesh_mass_properties(
            stage,
            root_path + spec["mesh_relative_path"],
            density_kg_m3=float(spec.get("density_kg_m3", 1.0)),
            target_mass_kg=spec.get("target_mass_kg"),
        )
        properties["method"] = spec["method"]
    _author_mass(stage, root, properties)
    stage.GetRootLayer().Save()
    verified = Usd.Stage.Open(str(asset))
    collision_after = _collision_signature(verified, root_path)
    if collision_before != collision_after:
        raise RuntimeError(f"collision changed while making {asset_id} dynamic")
    profile = {
        "schema_version": "aan.physics_profile.v1",
        "profile_id": spec["profile_id"],
        "revision": "v1",
        "quality_tier": "provisional_geometry",
        "motion_role": "dynamic",
        "source_exact_package": str(exact_package),
        "source_asset_sha256": _sha(exact_package / "asset.usda"),
        "mass_properties": properties,
        "effective_kinematic": False,
        "replacement_contract": "replace the complete profile in a new revision",
    }
    physics_dir = output / "physics"
    physics_dir.mkdir(exist_ok=True)
    (physics_dir / "profile.json").write_text(
        json.dumps(profile, indent=2, sort_keys=True) + "\n"
    )
    manifest = {
        **exact_manifest,
        "schema_version": "aan.dynamic_liquid_interaction_asset.v1",
        "package_id": f"wangshuai_{asset_id}_v1",
        "overall_status": "candidate",
        "blocked_reasons": ["dynamic_runtime_qualification_pending"],
        "source_exact_manifest": "evidence/exact_source_manifest.json",
        "source_exact_manifest_sha256": _sha(output / "evidence/exact_source_manifest.json"),
        "physics_profile": {
            "path": "physics/profile.json",
            "sha256": _sha(physics_dir / "profile.json"),
            "quality_tier": "provisional_geometry",
        },
        "collision_signature_sha256": collision_after,
    }
    manifest["claims"].update(
        {
            "effective_kinematic": False,
            "collision_geometry_unchanged": True,
            "dynamic_runtime_qualified": False,
            "robot_policy_success": False,
            "task_success": False,
            "benchmark_success": False,
        }
    )
    exact_manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def build_dynamic_asset_set(exact_root: Path, output: Path) -> Path:
    exact_root = exact_root.resolve()
    output = output.resolve()
    exact_index = json.loads((exact_root / "asset_set_manifest.json").read_text())
    if exact_index.get("status") != "pass":
        raise RuntimeError("exact source asset set must be pass")
    staging = output.parent / f".{output.name}.staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    try:
        records = []
        for asset_id, spec in DYNAMIC_SPECS.items():
            package = staging / "packages" / asset_id
            package.parent.mkdir(parents=True, exist_ok=True)
            manifest = _build_dynamic_package(exact_root, package, asset_id, spec)
            records.append(
                {
                    "id": asset_id,
                    "package": f"packages/{asset_id}",
                    "entry_usd": f"packages/{asset_id}/asset.usda",
                    "entry_prim": manifest["entrypoints"]["asset_entry_prim"],
                    "contains_liquid": False,
                    "overall_status": "candidate",
                    "default_consumption": "dynamic",
                }
            )
        overlay_id = "small_v2_liquid_seed_1948"
        overlay_source = exact_root / "packages" / overlay_id
        overlay_destination = staging / "packages" / overlay_id
        shutil.copytree(overlay_source, overlay_destination)
        overlay_manifest = json.loads(
            (overlay_destination / "evidence/manifest.json").read_text()
        )
        records.append(
            {
                "id": overlay_id,
                "package": f"packages/{overlay_id}",
                "entry_usd": f"packages/{overlay_id}/asset.usda",
                "entry_prim": overlay_manifest["entrypoints"]["asset_entry_prim"],
                "contains_liquid": True,
                "particle_count": 1948,
                "overall_status": "pass",
                "default_consumption": "overlay",
            }
        )
        index = {
            "schema_version": "aan.wangshuai_funnel_tube15_dynamic_asset_set.v1",
            "status": "candidate_runtime_pending",
            "default_consumption": "dynamic",
            "exact_source_asset_set": str(exact_root),
            "exact_source_manifest_sha256": _sha(exact_root / "asset_set_manifest.json"),
            "assets": records,
            "claims": {
                "effective_kinematic": False,
                "collision_geometry_unchanged": True,
                "dynamic_runtime_qualified": False,
                "robot_policy_success": False,
                "task_success": False,
                "benchmark_success": False,
            },
        }
        (staging / "asset_set_manifest.json").write_text(
            json.dumps(index, indent=2, sort_keys=True) + "\n"
        )
        if output.exists():
            shutil.rmtree(output)
        staging.rename(output)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exact", type=Path, default=DEFAULT_EXACT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(build_dynamic_asset_set(args.exact, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
