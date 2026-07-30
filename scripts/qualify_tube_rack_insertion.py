#!/usr/bin/env python3
"""Qualify one delivered test tube falling dynamically into one rack socket.

Both packages are composed by explicit entry prim.  The rack is held
kinematically as a test fixture; the tube remains a dynamic rigid body and is
positioned only once before stepping.  No per-frame translate authoring is
allowed.  Pair-filtered PhysX contacts, maximum penetration, axis alignment,
and the authoritative inserted-bottom frame determine the result.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REPORT_SCHEMA_VERSION = "aan.tube_rack_insertion_qualification.v2"
BOTTOM_DISTANCE_TOLERANCE_M = 0.002
MAX_PENETRATION_M = 0.001
AXIS_ALIGNMENT_TOLERANCE_DEG = 10.0
MINIMUM_DEPTH_FRACTION = 0.9
DEFAULT_START_CLEARANCE_M = 0.002
DEFAULT_PHYSICS_DT = 0.001
DEFAULT_MAX_STEPS = 900


class PackageIdentityError(ValueError):
    """Raised when a package cannot be bound to immutable runtime inputs."""


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise PackageIdentityError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise PackageIdentityError(f"{label} must be a JSON object")
    return value


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise PackageIdentityError(f"{label} must be an object")
    return value


def _required_string(value: Mapping[str, Any], key: str, label: str) -> str:
    candidate = value.get(key)
    if not isinstance(candidate, str) or not candidate:
        raise PackageIdentityError(f"{label}.{key} must be a non-empty string")
    return candidate


def _in_scope(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def _artifact_sha256(
    interaction_contract: Mapping[str, Any],
    relative_path: str,
) -> str:
    closure = _mapping(
        interaction_contract.get("closure"),
        "interaction_contract.closure",
    )
    if closure.get("status") != "pass":
        raise PackageIdentityError("interaction_contract.closure.status must be pass")
    artifacts = closure.get("artifacts")
    if not isinstance(artifacts, list):
        raise PackageIdentityError("interaction_contract.closure.artifacts must be a list")
    matches = [
        item
        for item in artifacts
        if isinstance(item, dict) and item.get("path") == relative_path
    ]
    if len(matches) != 1:
        raise PackageIdentityError(
            f"interaction closure must bind exactly one {relative_path}"
        )
    return _required_string(matches[0], "sha256", "closure artifact")


def load_package_identity(
    package_root: Path,
    manifest_path: Path,
    *,
    role: str,
) -> dict[str, Any]:
    """Validate one AAN package and return the exact identity bound to a report."""
    package_root = package_root.resolve()
    manifest_path = manifest_path.resolve()
    if role not in {"rack", "tube"}:
        raise PackageIdentityError("role must be rack or tube")
    if not package_root.is_dir():
        raise PackageIdentityError(f"{role} package root does not exist: {package_root}")
    if not manifest_path.is_file():
        raise PackageIdentityError(f"{role} manifest does not exist: {manifest_path}")
    embedded_manifest_path = package_root / "evidence" / "manifest.json"
    if not embedded_manifest_path.is_file():
        raise PackageIdentityError(
            f"{role} package is missing evidence/manifest.json"
        )
    manifest_bytes = manifest_path.read_bytes()
    if embedded_manifest_path.read_bytes() != manifest_bytes:
        raise PackageIdentityError(
            f"{role} external and embedded manifests are not byte-identical"
        )
    manifest = _json_object(manifest_path, f"{role} manifest")
    if manifest.get("schema_version") != "asset_application_normalizer.v1":
        raise PackageIdentityError(
            f"{role} manifest schema_version is unsupported"
        )
    if manifest.get("overall_status") != "pass":
        raise PackageIdentityError(f"{role} manifest overall_status must be pass")
    entrypoints = _mapping(manifest.get("entrypoints"), f"{role} entrypoints")
    entry_prim = _required_string(
        entrypoints,
        "asset_entry_prim",
        f"{role} entrypoints",
    )
    if not entry_prim.startswith("/") or "//" in entry_prim:
        raise PackageIdentityError(f"{role} asset_entry_prim must be absolute")
    contract = _mapping(
        manifest.get("interaction_contract"),
        f"{role} interaction_contract",
    )
    if contract.get("status") != "pass":
        raise PackageIdentityError(
            f"{role} interaction_contract.status must be pass"
        )
    if contract.get("asset_entry_prim") != entry_prim:
        raise PackageIdentityError(
            f"{role} interaction_contract asset_entry_prim does not match entrypoints"
        )
    runtime_identity = _mapping(
        contract.get("runtime_identity"),
        f"{role} runtime_identity",
    )
    active_rigid_bodies = runtime_identity.get("active_rigid_body_prims")
    if (
        runtime_identity.get("exactly_one_active_rigid_body") is not True
        or runtime_identity.get("rigid_root_prim") != entry_prim
        or active_rigid_bodies != [entry_prim]
    ):
        raise PackageIdentityError(
            f"{role} package must bind exactly one rigid body at asset_entry_prim"
        )
    asset_path = package_root / "asset.usd"
    if not asset_path.is_file():
        raise PackageIdentityError(f"{role} package asset.usd does not exist")
    asset_sha256 = _sha256_file(asset_path)
    if _artifact_sha256(contract, "asset.usd") != asset_sha256:
        raise PackageIdentityError(
            f"{role} asset.usd SHA-256 differs from interaction closure"
        )
    named_frames = _mapping(
        contract.get("named_frames"),
        f"{role} interaction_contract.named_frames",
    )
    required_frames = (
        ("support", "socket_0_aperture", "socket_0_inserted_bottom")
        if role == "rack"
        else ("support",)
    )
    for frame_name in required_frames:
        frame = _mapping(
            named_frames.get(frame_name),
            f"{role} named frame {frame_name}",
        )
        prim_path = _required_string(
            frame,
            "prim_path",
            f"{role} named frame {frame_name}",
        )
        if not _in_scope(prim_path, entry_prim):
            raise PackageIdentityError(
                f"{role} named frame {frame_name} escapes asset_entry_prim"
            )
        if frame.get("parent_prim") != entry_prim:
            raise PackageIdentityError(
                f"{role} named frame {frame_name} parent_prim must equal asset_entry_prim"
            )
        if frame.get("authoritative") is not True:
            raise PackageIdentityError(
                f"{role} named frame {frame_name} must be authoritative"
            )
        translation = frame.get("translation_body_local_usd")
        if (
            not isinstance(translation, list)
            or len(translation) != 3
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in translation
            )
        ):
            raise PackageIdentityError(
                f"{role} named frame {frame_name} translation must be three finite numbers"
            )
    collider_prims = contract.get("collider_prims")
    if role == "rack":
        if not isinstance(collider_prims, list):
            raise PackageIdentityError("rack collider_prims must be a list")
        collider_paths = [
            item.get("prim_path")
            for item in collider_prims
            if isinstance(item, dict) and isinstance(item.get("prim_path"), str)
        ]
        bottom_paths = [
            path for path in collider_paths if path.endswith("/socket_0_bottom")
        ]
        side_paths = [
            path for path in collider_paths if "/socket_0_wall_" in path
        ]
        if len(bottom_paths) != 1 or not side_paths:
            raise PackageIdentityError(
                "rack interaction contract must bind one socket bottom and side proxies"
            )
    else:
        bottom_paths = []
        side_paths = []
    return {
        "role": role,
        "package_root": package_root,
        "manifest_path": manifest_path,
        "asset_path": asset_path,
        "package_manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "asset_usd_sha256": asset_sha256,
        "asset_entry_prim": entry_prim,
        "active_rigid_body_prims": list(active_rigid_bodies),
        "interaction_contract": dict(contract),
        "named_frames": dict(named_frames),
        "bottom_collider_paths": bottom_paths,
        "side_collider_paths": side_paths,
    }


def _number(value: Any) -> float:
    if isinstance(value, bool):
        return math.nan
    try:
        result = float(value)
    except (TypeError, ValueError):
        return math.nan
    return result if math.isfinite(result) else math.nan


def _gate(errors: list[str], observations: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": "pass" if not errors else "blocked",
        "errors": errors,
        "observations": dict(observations),
    }


def evaluate_insertion_observations(
    observations: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply fail-closed thresholds to simulator observations."""
    composition = (
        observations.get("composition")
        if isinstance(observations.get("composition"), dict)
        else {}
    )
    trajectory = (
        observations.get("trajectory")
        if isinstance(observations.get("trajectory"), dict)
        else {}
    )
    contacts = (
        observations.get("contacts")
        if isinstance(observations.get("contacts"), dict)
        else {}
    )
    composition_errors: list[str] = []
    rack_root = composition.get("rack_expected_rigid_root")
    tube_root = composition.get("tube_expected_rigid_root")
    if composition.get("rack_active_rigid_body_prims") != [rack_root]:
        composition_errors.append("rack composition contains nested or missing rigid bodies")
    if composition.get("tube_active_rigid_body_prims") != [tube_root]:
        composition_errors.append("tube composition contains nested or missing rigid bodies")
    if composition.get("tube_kinematic") is not False:
        composition_errors.append("tube must remain dynamic, not kinematic")
    if composition.get("authored_translation_updates") != 0:
        composition_errors.append("per-frame authored translate updates are forbidden")

    dynamic_errors: list[str] = []
    sample_count = _number(trajectory.get("sample_count"))
    expected_depth = _number(trajectory.get("expected_insertion_depth_m"))
    observed_depth = _number(trajectory.get("observed_insertion_depth_m"))
    alignment = _number(trajectory.get("axis_alignment_error_deg"))
    if observations.get("finite") is not True:
        dynamic_errors.append("runtime observations are not finite")
    if not math.isfinite(sample_count) or sample_count < 2:
        dynamic_errors.append("dynamic trajectory has too few samples")
    if not math.isfinite(expected_depth) or expected_depth <= 0.0:
        dynamic_errors.append("expected insertion depth is invalid")
    elif (
        not math.isfinite(observed_depth)
        or observed_depth < MINIMUM_DEPTH_FRACTION * expected_depth
    ):
        dynamic_errors.append("dynamic tube travel did not reach the insertion depth")
    if (
        not math.isfinite(alignment)
        or alignment > AXIS_ALIGNMENT_TOLERANCE_DEG
    ):
        dynamic_errors.append("tube insertion axis alignment exceeds tolerance")

    clearance_errors: list[str] = []
    max_side_penetration = _number(
        contacts.get("max_side_penetration_m")
    )
    if (
        not math.isfinite(max_side_penetration)
        or max_side_penetration < 0.0
    ):
        clearance_errors.append("side penetration observation is invalid")
    elif max_side_penetration > MAX_PENETRATION_M:
        clearance_errors.append("side penetration exceeds 1 mm")

    bottom_errors: list[str] = []
    bottom_axial_error = _number(
        trajectory.get("final_bottom_axial_error_m")
    )
    bottom_samples = _number(contacts.get("bottom_pair_contact_samples"))
    if contacts.get("contact_probe_available") is not True:
        bottom_errors.append("pair-filtered bottom contact probe is unavailable")
    if not math.isfinite(bottom_samples) or bottom_samples < 1:
        bottom_errors.append("no pair-filtered bottom contact was observed")
    if (
        not math.isfinite(bottom_axial_error)
        or bottom_axial_error > BOTTOM_DISTANCE_TOLERANCE_M
    ):
        bottom_errors.append("tube support did not reach the authoritative bottom frame")

    gates = {
        "composition_identity": _gate(composition_errors, composition),
        "dynamic_insertion": _gate(dynamic_errors, trajectory),
        "side_clearance": _gate(clearance_errors, contacts),
        "bottom_contact": _gate(bottom_errors, {**trajectory, **contacts}),
    }
    return {
        "status": (
            "pass"
            if all(gate["status"] == "pass" for gate in gates.values())
            else "blocked"
        ),
        "gates": gates,
    }


def _report_input(identity: Mapping[str, Any]) -> dict[str, str]:
    return {
        "package_manifest_sha256": str(identity["package_manifest_sha256"]),
        "asset_usd_sha256": str(identity["asset_usd_sha256"]),
        "asset_entry_prim": str(identity["asset_entry_prim"]),
    }


def _normalise(vector: Any, np: Any) -> Any:
    result = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(result))
    if not math.isfinite(norm) or norm <= 1.0e-9:
        raise RuntimeError("cannot normalize a zero or non-finite vector")
    return result / norm


def _orientation_wxyz_for_z_axis(z_axis: Any, np: Any) -> Any:
    target = _normalise(z_axis, np)
    local_z = np.asarray([0.0, 0.0, 1.0], dtype=float)
    dot = float(np.clip(np.dot(local_z, target), -1.0, 1.0))
    if dot <= -1.0 + 1.0e-9:
        return np.asarray([0.0, 1.0, 0.0, 0.0], dtype=float)
    cross = np.cross(local_z, target)
    return _normalise(np.asarray([1.0 + dot, *cross], dtype=float), np)


def _rotate_vector_wxyz(quaternion: Any, vector: Any, np: Any) -> Any:
    quaternion = _normalise(quaternion, np)
    w = float(quaternion[0])
    imaginary = np.asarray(quaternion[1:], dtype=float)
    vector = np.asarray(vector, dtype=float)
    twice_cross = 2.0 * np.cross(imaginary, vector)
    return vector + w * twice_cross + np.cross(imaginary, twice_cross)


def _frame_translation(identity: Mapping[str, Any], frame_name: str, np: Any) -> Any:
    frame = identity["named_frames"][frame_name]
    return np.asarray(frame["translation_body_local_usd"], dtype=float)


def _active_rigid_bodies(stage: Any, root_path: str, usd_physics: Any) -> list[str]:
    root = stage.GetPrimAtPath(root_path)
    if not root or not root.IsValid():
        return []
    paths: list[str] = []
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        if not _in_scope(path, root_path) or not prim.HasAPI(usd_physics.RigidBodyAPI):
            continue
        enabled = usd_physics.RigidBodyAPI(prim).GetRigidBodyEnabledAttr().Get()
        if enabled is not False:
            paths.append(path)
    return sorted(paths)


def _contact_snapshot(
    view: Any,
    *,
    filter_paths: list[str],
    np: Any,
    physics_dt: float,
) -> dict[str, Any]:
    matrix = view.get_contact_force_matrix(dt=physics_dt)
    details = view.get_contact_force_data(dt=physics_dt)
    if matrix is None or details is None:
        return {
            "available": False,
            "filters": {
                path: {"contact_count": 0, "contacts": []}
                for path in filter_paths
            },
            "max_penetration_m": math.nan,
        }
    forces, points, normals, distances, counts, starts = details
    counts_array = np.asarray(counts)
    starts_array = np.asarray(starts)
    forces_array = np.asarray(forces)
    points_array = np.asarray(points)
    normals_array = np.asarray(normals)
    distances_array = np.asarray(distances)
    filters: dict[str, Any] = {}
    maximum_penetration = 0.0
    maximum_penetration_by_filter: dict[str, float] = {}
    deepest_contact: dict[str, Any] | None = None
    for filter_index, path in enumerate(filter_paths):
        count = int(counts_array[0, filter_index])
        start = int(starts_array[0, filter_index])
        entries: list[dict[str, Any]] = []
        filter_maximum_penetration = 0.0
        for index in range(start, start + count):
            separation = float(distances_array[index].reshape(-1)[0])
            entry = {
                "force_n": [
                    round(float(value), 8)
                    for value in forces_array[index].reshape(-1)
                ],
                "point_m": [
                    round(float(value), 8) for value in points_array[index]
                ],
                "normal": [
                    round(float(value), 8) for value in normals_array[index]
                ],
                "separation_m": round(separation, 8),
            }
            entries.append(entry)
            penetration = max(0.0, -separation)
            filter_maximum_penetration = max(
                filter_maximum_penetration,
                penetration,
            )
            if penetration > maximum_penetration:
                maximum_penetration = penetration
                deepest_contact = {"filter_path": path, **entry}
        filters[path] = {"contact_count": count, "contacts": entries}
        maximum_penetration_by_filter[path] = filter_maximum_penetration
    return {
        "available": True,
        "filters": filters,
        "max_penetration_m": maximum_penetration,
        "max_penetration_by_filter_m": maximum_penetration_by_filter,
        "deepest_contact": deepest_contact,
    }


def _run_runtime(
    rack: Mapping[str, Any],
    tube: Mapping[str, Any],
    *,
    expected_runtime_version: str,
    physics_dt: float,
    max_steps: int,
    start_clearance_m: float,
) -> dict[str, Any]:
    from isaacsim import SimulationApp  # type: ignore

    app = SimulationApp(
        {
            "headless": True,
            "multi_gpu": False,
            "renderer": "RayTracedLighting",
        }
    )
    world = None
    try:
        import omni  # type: ignore
        from omni.isaac.core import World  # type: ignore
        from omni.isaac.core.prims import RigidPrimView  # type: ignore
        import numpy as np  # type: ignore
        from pxr import UsdGeom, UsdPhysics  # type: ignore

        from convert_asset.asset_application_normalizer.runtime_smoke import (
            _runtime_environment,
            _runtime_profile_gate,
        )

        environment = _runtime_environment()
        runtime_gate = _runtime_profile_gate(environment, expected_runtime_version)
        if runtime_gate.get("status") != "pass":
            raise RuntimeError("Isaac/Kit runtime fingerprint does not match request")
        context = omni.usd.get_context()
        context.new_stage()
        for _ in range(8):
            app.update()
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("Isaac did not provide a new stage")
        stage.SetEditTarget(stage.GetSessionLayer())
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        stage.DefinePrim("/World", "Xform")
        rack_root = str(rack["asset_entry_prim"])
        tube_root = str(tube["asset_entry_prim"])
        if _in_scope(rack_root, tube_root) or _in_scope(tube_root, rack_root):
            raise RuntimeError("rack and tube entry prims must be disjoint")
        rack_prim = stage.DefinePrim(rack_root, "Xform")
        tube_prim = stage.DefinePrim(tube_root, "Xform")
        rack_prim.GetReferences().AddReference(
            str(rack["asset_path"]),
            rack_root,
        )
        tube_prim.GetReferences().AddReference(
            str(tube["asset_path"]),
            tube_root,
        )
        for _ in range(60):
            app.update()
        rack_prim = stage.GetPrimAtPath(rack_root)
        tube_prim = stage.GetPrimAtPath(tube_root)
        if not rack_prim.IsValid() or not tube_prim.IsValid():
            raise RuntimeError("explicit entry-prim composition did not resolve")
        rack_bodies = _active_rigid_bodies(stage, rack_root, UsdPhysics)
        tube_bodies = _active_rigid_bodies(stage, tube_root, UsdPhysics)
        if rack_bodies != [rack_root] or tube_bodies != [tube_root]:
            raise RuntimeError(
                "entry-prim composition produced nested or missing rigid bodies"
            )
        rack_rigid = UsdPhysics.RigidBodyAPI(rack_prim)
        rack_rigid.CreateKinematicEnabledAttr().Set(True)
        tube_rigid = UsdPhysics.RigidBodyAPI(tube_prim)
        tube_rigid.CreateKinematicEnabledAttr().Set(False)

        filter_paths = list(rack["bottom_collider_paths"]) + list(
            rack["side_collider_paths"]
        )
        world = World(
            stage_units_in_meters=1.0,
            physics_dt=physics_dt,
            rendering_dt=physics_dt,
        )
        tube_view = RigidPrimView(
            tube_root,
            name="dynamic_test_tube",
            track_contact_forces=True,
            contact_filter_prim_paths_expr=filter_paths,
            max_contact_count=512,
            disable_stablization=False,
        )
        world.scene.add(tube_view)
        world.reset()
        for _ in range(12):
            world.step(render=False)

        aperture = _frame_translation(rack, "socket_0_aperture", np)
        bottom = _frame_translation(rack, "socket_0_inserted_bottom", np)
        insertion_vector = bottom - aperture
        expected_depth = float(np.linalg.norm(insertion_vector))
        insertion_axis = _normalise(insertion_vector, np)
        tube_support_local = _frame_translation(tube, "support", np)
        tube_local_z_world = -insertion_axis
        orientation = _orientation_wxyz_for_z_axis(tube_local_z_world, np)
        start_support = aperture - insertion_axis * start_clearance_m
        root_position = start_support - _rotate_vector_wxyz(
            orientation,
            tube_support_local,
            np,
        )
        tube_view.set_world_poses(
            positions=np.asarray([root_position], dtype=np.float32),
            orientations=np.asarray([orientation], dtype=np.float32),
        )
        tube_view.set_linear_velocities(np.zeros((1, 3), dtype=np.float32))
        tube_view.set_angular_velocities(np.zeros((1, 3), dtype=np.float32))
        world.step(render=False)

        bottom_paths = set(rack["bottom_collider_paths"])
        side_paths = set(rack["side_collider_paths"])
        bottom_contact_samples = 0
        side_contact_samples = 0
        maximum_penetration = 0.0
        maximum_side_penetration = 0.0
        deepest_contact: dict[str, Any] | None = None
        contact_probe_available = True
        final_support = start_support.copy()
        final_axis = tube_local_z_world.copy()
        sample_count = 0
        stable_bottom_samples = 0
        for _ in range(max_steps):
            world.step(render=False)
            sample_count += 1
            positions, orientations = tube_view.get_world_poses()
            observed_root = np.asarray(positions[0], dtype=float)
            observed_orientation = np.asarray(orientations[0], dtype=float)
            final_support = observed_root + _rotate_vector_wxyz(
                observed_orientation,
                tube_support_local,
                np,
            )
            final_axis = _normalise(
                _rotate_vector_wxyz(
                    observed_orientation,
                    [0.0, 0.0, 1.0],
                    np,
                ),
                np,
            )
            contact = _contact_snapshot(
                tube_view,
                filter_paths=filter_paths,
                np=np,
                physics_dt=physics_dt,
            )
            contact_probe_available = (
                contact_probe_available and contact["available"] is True
            )
            if contact["available"] is True:
                if float(contact["max_penetration_m"]) > maximum_penetration:
                    contact_record = contact.get("deepest_contact")
                    deepest_contact = (
                        {"sample_index": sample_count, **contact_record}
                        if isinstance(contact_record, dict)
                        else None
                    )
                maximum_penetration = max(
                    maximum_penetration,
                    float(contact["max_penetration_m"]),
                )
                maximum_side_penetration = max(
                    maximum_side_penetration,
                    *(
                        float(
                            contact["max_penetration_by_filter_m"].get(
                                path,
                                0.0,
                            )
                        )
                        for path in side_paths
                    ),
                )
                bottom_count = sum(
                    int(contact["filters"][path]["contact_count"])
                    for path in bottom_paths
                )
                side_count = sum(
                    int(contact["filters"][path]["contact_count"])
                    for path in side_paths
                )
                if bottom_count:
                    bottom_contact_samples += 1
                    stable_bottom_samples += 1
                else:
                    stable_bottom_samples = 0
                if side_count:
                    side_contact_samples += 1
            if stable_bottom_samples >= 12:
                break

        observed_depth = float(np.dot(start_support - final_support, -insertion_axis))
        bottom_distance = float(np.linalg.norm(final_support - bottom))
        bottom_axial_error = abs(
            float(np.dot(final_support - bottom, insertion_axis))
        )
        bottom_lateral_offset = float(
            np.linalg.norm(
                (final_support - bottom)
                - np.dot(final_support - bottom, insertion_axis)
                * insertion_axis
            )
        )
        dot = float(np.clip(np.dot(final_axis, tube_local_z_world), -1.0, 1.0))
        alignment_error = math.degrees(math.acos(dot))
        observations = {
            "finite": bool(
                np.isfinite(final_support).all()
                and math.isfinite(observed_depth)
                and math.isfinite(bottom_distance)
                and math.isfinite(alignment_error)
                and math.isfinite(maximum_penetration)
            ),
            "composition": {
                "rack_active_rigid_body_prims": rack_bodies,
                "tube_active_rigid_body_prims": tube_bodies,
                "rack_expected_rigid_root": rack_root,
                "tube_expected_rigid_root": tube_root,
                "rack_fixture_kinematic": True,
                "tube_kinematic": bool(
                    tube_rigid.GetKinematicEnabledAttr().Get()
                ),
                "authored_translation_updates": 0,
                "composition_method": "explicit references to delivered asset entry prims",
            },
            "trajectory": {
                "sample_count": sample_count,
                "start_support_position_m": [
                    float(value) for value in start_support
                ],
                "final_support_position_m": [
                    float(value) for value in final_support
                ],
                "authoritative_bottom_position_m": [
                    float(value) for value in bottom
                ],
                "insertion_axis_world": [
                    float(value) for value in insertion_axis
                ],
                "expected_insertion_depth_m": expected_depth + start_clearance_m,
                "observed_insertion_depth_m": observed_depth,
                "final_bottom_distance_m": bottom_distance,
                "final_bottom_axial_error_m": bottom_axial_error,
                "final_bottom_lateral_offset_m": bottom_lateral_offset,
                "axis_alignment_error_deg": alignment_error,
            },
            "contacts": {
                "method": "RigidContactView pair-filtered contact data",
                "contact_probe_available": contact_probe_available,
                "bottom_filter_paths": sorted(bottom_paths),
                "side_filter_paths": sorted(side_paths),
                "bottom_pair_contact_samples": bottom_contact_samples,
                "side_pair_contact_samples": side_contact_samples,
                "max_penetration_m": maximum_penetration,
                "max_side_penetration_m": maximum_side_penetration,
                "deepest_contact": deepest_contact,
            },
        }
        evaluation = evaluate_insertion_observations(observations)
        return {
            "environment": environment,
            "runtime_profile_gate": runtime_gate,
            "observations": observations,
            **evaluation,
        }
    finally:
        # Isaac Sim 4.1/4.5 may terminate the interpreter from ``close()``
        # before the caller persists the report.  This worker is a short-lived
        # CLI process, so Kit teardown is deliberately left to process exit
        # after ``main`` has written the evidence file.
        pass


def qualify_tube_rack_insertion(
    *,
    rack_package_root: Path,
    rack_manifest_path: Path,
    tube_package_root: Path,
    tube_manifest_path: Path,
    expected_runtime_version: str = "4.1",
    physics_dt: float = DEFAULT_PHYSICS_DT,
    max_steps: int = DEFAULT_MAX_STEPS,
    start_clearance_m: float = DEFAULT_START_CLEARANCE_M,
) -> dict[str, Any]:
    """Run a source-bound dynamic insertion qualification and return its report."""
    if not math.isfinite(physics_dt) or physics_dt <= 0.0:
        raise ValueError("physics_dt must be finite and positive")
    if max_steps < 2:
        raise ValueError("max_steps must be at least 2")
    if not math.isfinite(start_clearance_m) or start_clearance_m <= 0.0:
        raise ValueError("start_clearance_m must be finite and positive")
    rack = load_package_identity(
        rack_package_root,
        rack_manifest_path,
        role="rack",
    )
    tube = load_package_identity(
        tube_package_root,
        tube_manifest_path,
        role="tube",
    )
    if rack["asset_entry_prim"] == tube["asset_entry_prim"]:
        raise PackageIdentityError("rack and tube asset_entry_prim must differ")
    before = {
        "rack_asset_usd_sha256": rack["asset_usd_sha256"],
        "rack_package_manifest_sha256": rack["package_manifest_sha256"],
        "tube_asset_usd_sha256": tube["asset_usd_sha256"],
        "tube_package_manifest_sha256": tube["package_manifest_sha256"],
    }
    runtime_result = _run_runtime(
        rack,
        tube,
        expected_runtime_version=expected_runtime_version,
        physics_dt=physics_dt,
        max_steps=max_steps,
        start_clearance_m=start_clearance_m,
    )
    after = {
        "rack_asset_usd_sha256": _sha256_file(rack["asset_path"]),
        "rack_package_manifest_sha256": _sha256_file(rack["manifest_path"]),
        "tube_asset_usd_sha256": _sha256_file(tube["asset_path"]),
        "tube_package_manifest_sha256": _sha256_file(tube["manifest_path"]),
    }
    source_integrity_passed = before == after
    source_integrity = {
        "status": "pass" if source_integrity_passed else "blocked",
        "rack_asset_usd_sha256_before": before["rack_asset_usd_sha256"],
        "rack_asset_usd_sha256_after": after["rack_asset_usd_sha256"],
        "rack_package_manifest_sha256_before": before[
            "rack_package_manifest_sha256"
        ],
        "rack_package_manifest_sha256_after": after[
            "rack_package_manifest_sha256"
        ],
        "tube_asset_usd_sha256_before": before["tube_asset_usd_sha256"],
        "tube_asset_usd_sha256_after": after["tube_asset_usd_sha256"],
        "tube_package_manifest_sha256_before": before[
            "tube_package_manifest_sha256"
        ],
        "tube_package_manifest_sha256_after": after[
            "tube_package_manifest_sha256"
        ],
    }
    gates = dict(runtime_result["gates"])
    gates["source_integrity"] = {
        "status": source_integrity["status"],
        "errors": (
            []
            if source_integrity_passed
            else ["package inputs changed during runtime qualification"]
        ),
        "observations": source_integrity,
    }
    status = (
        "pass"
        if runtime_result["status"] == "pass" and source_integrity_passed
        else "blocked"
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": status,
        "runtime": {
            "expected_runtime_version": expected_runtime_version,
            "environment": runtime_result.get("environment", {}),
            "runtime_profile_gate": runtime_result.get(
                "runtime_profile_gate",
                {"status": "blocked"},
            ),
            "physics_dt_seconds": physics_dt,
        },
        "inputs": {
            "rack": _report_input(rack),
            "tube": _report_input(tube),
        },
        "protocol": {
            "rack_fixture_kinematic": True,
            "tube_kinematic": False,
            "authored_translation_updates": 0,
            "tube_motion": "single initial pose followed by unconstrained gravity",
            "max_steps": max_steps,
            "start_clearance_m": start_clearance_m,
            "bottom_distance_tolerance_m": BOTTOM_DISTANCE_TOLERANCE_M,
            "maximum_penetration_m": MAX_PENETRATION_M,
            "axis_alignment_tolerance_deg": AXIS_ALIGNMENT_TOLERANCE_DEG,
        },
        "observations": runtime_result["observations"],
        "source_integrity": source_integrity,
        "gates": gates,
        "claim_boundary": (
            "This report qualifies only the delivered rack/tube collider path, "
            "pair-filtered contact, and named-frame arrival under the recorded "
            "fixed-rack gravity protocol. It does not claim robot-policy or "
            "benchmark success."
        ),
    }


def _write_report(path: Path, report: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run source-bound dynamic tube insertion qualification."
    )
    parser.add_argument("--rack-package", type=Path, required=True)
    parser.add_argument("--rack-manifest", type=Path, required=True)
    parser.add_argument("--tube-package", type=Path, required=True)
    parser.add_argument("--tube-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-runtime-version", default="4.1")
    parser.add_argument("--physics-dt", type=float, default=DEFAULT_PHYSICS_DT)
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument(
        "--start-clearance-m",
        type=float,
        default=DEFAULT_START_CLEARANCE_M,
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = qualify_tube_rack_insertion(
            rack_package_root=args.rack_package,
            rack_manifest_path=args.rack_manifest,
            tube_package_root=args.tube_package,
            tube_manifest_path=args.tube_manifest,
            expected_runtime_version=str(args.expected_runtime_version),
            physics_dt=float(args.physics_dt),
            max_steps=int(args.max_steps),
            start_clearance_m=float(args.start_clearance_m),
        )
    except Exception as exc:
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "blocked",
            "host_failure": {
                "exception_type": type(exc).__name__,
                "reason": str(exc),
            },
        }
    _write_report(args.out.resolve(), report)
    return 0 if report.get("status") == "pass" else 2


if __name__ == "__main__":
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)
