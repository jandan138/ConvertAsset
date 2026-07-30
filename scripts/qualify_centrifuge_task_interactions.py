#!/usr/bin/env python3
"""Run producer-owned Isaac 4.1 contact evidence for the centrifuge package.

The probe authors only transient session-layer fixtures.  It never changes the
source facade, package USD layers, or any centrifuge joint-drive attribute.
The five-gate report binds the exact package manifest, asset USD, source SHA,
and device-profile SHA for subsequent benchtop merge and package finalization.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CENTRIFUGE_PACKAGE = (
    REPO_ROOT / "outputs/centrifuge_identity_root_r9/package"
)
DEFAULT_TUBE_PACKAGE = (
    REPO_ROOT
    / "outputs/tube_task_assets_20260729/uniform_scale_k0365/test_tube/package"
)
CENTRIFUGE_ROOT = "/World/Centrifuge"
BUTTON_BODY = f"{CENTRIFUGE_ROOT}/group_2"
ROTOR_BODY = f"{CENTRIFUGE_ROOT}/group_6"
LID_BODY = f"{CENTRIFUGE_ROOT}/group_23"
BUTTON_JOINT = f"{BUTTON_BODY}/PrismaticJoint"
ROTOR_JOINT = f"{ROTOR_BODY}/RevoluteJoint"
LID_JOINT = f"{LID_BODY}/RevoluteJoint"
BUTTON_PROXY = f"{BUTTON_BODY}/__aan_collision_proxy/button_face"
LID_PROXY = f"{LID_BODY}/__aan_collision_proxy/lid_shell"
TUBE_PROBE_ROOT = "/World/__aan_task_contact_probe/TestTube"

EXPECTED_DOF_MAPPING = (
    (0, "PrismaticJoint", BUTTON_JOINT),
    (1, "RevoluteJoint", ROTOR_JOINT),
    (2, "RevoluteJoint", LID_JOINT),
)
BUTTON_RELEASED_BAND = (-0.0005, 0.0)
BUTTON_PRESSED_BAND = (-0.0055, -0.0045)
LID_OPEN_BAND = (-1.5556521049, -1.45)
LID_CLOSED_BAND = (-0.0872664626, 0.0)
LID_TRAVEL_BAND = (LID_OPEN_BAND[0], LID_CLOSED_BAND[1])
ROTOR_PARKED_BAND = (-0.05, 0.0)
TUBE_RADIUS_M = 0.00332103061
TUBE_HEIGHT_M = 0.0438
LID_PUSHER_SIZE_M = (0.08, 0.08, 0.04)
LID_PUSHER_HALF_DEPTH_M = LID_PUSHER_SIZE_M[2] / 2.0
LID_PUSHER_CLEARANCE_M = 0.0005
PROFILE_SCHEMA_VERSION = "aan.articulated_device_profile.v1"
REQUIRED_PROFILE_FRAMES = {
    "tube_socket_0_aperture": f"{ROTOR_BODY}",
    "tube_socket_0_inserted_bottom_parked_root": CENTRIFUGE_ROOT,
    "lid_close_contact": f"{LID_BODY}",
    "start_button_press": f"{BUTTON_BODY}",
}
FIVE_INTERACTION_GATES = (
    "lid_contact_cycle",
    "button_contact_cycle",
    "button_reset_stability",
    "rotor_reset_stability",
    "socket_insertion_clearance",
)


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSON object is unreadable: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _load_device_profile(
    path: Path,
    *,
    source_sha256: str,
    articulation_root_prim: str,
) -> dict[str, Any]:
    """Load the producer profile before starting Isaac qualification."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"device profile is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError("device profile must be a JSON object")
    if value.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ValueError("device profile schema_version is unsupported")
    if value.get("source_sha256") != source_sha256:
        raise ValueError("device profile source_sha256 does not match the manifest")
    for field_name in ("asset_entry_prim", "articulation_root_prim"):
        if value.get(field_name) != articulation_root_prim:
            raise ValueError(f"device profile {field_name} does not match the articulation root")
    required_gates = value.get("required_runtime_task_gates")
    if not isinstance(required_gates, list):
        raise ValueError("device profile.required_runtime_task_gates must be a list")
    for gate_name in FIVE_INTERACTION_GATES:
        if gate_name not in required_gates:
            raise ValueError(
                "device profile is missing required interaction gate "
                f"{gate_name}"
            )
    frames = value.get("named_frames")
    if not isinstance(frames, dict):
        raise ValueError("device profile.named_frames must be an object")
    for frame_name, expected_parent in REQUIRED_PROFILE_FRAMES.items():
        frame = frames.get(frame_name)
        if not isinstance(frame, dict):
            raise ValueError(f"device profile is missing {frame_name}")
        if frame.get("parent_prim") != expected_parent:
            raise ValueError(
                f"device profile {frame_name}.parent_prim must be {expected_parent}"
            )
        if frame.get("authoritative") is not True:
            raise ValueError(f"device profile {frame_name}.authoritative must be true")
        for field_name, length in (
            ("translation_parent_local_m", 3),
            ("rotation_parent_local_wxyz", 4),
        ):
            components = frame.get(field_name)
            if (
                not isinstance(components, list)
                or len(components) != length
                or any(
                    isinstance(component, bool)
                    or not isinstance(component, (int, float))
                    or not math.isfinite(float(component))
                    for component in components
                )
            ):
                raise ValueError(
                    f"device profile {frame_name}.{field_name} must be {length} finite numbers"
                )
    return value


def _profile_frame_world_pose(
    stage: Any,
    profile: dict[str, Any],
    frame_name: str,
    *,
    usd: Any,
    usd_geom: Any,
    gf: Any,
    np: Any,
) -> tuple[Any, Any]:
    """Resolve a profile frame through its current moving parent transform."""
    frame = profile["named_frames"][frame_name]
    parent = stage.GetPrimAtPath(frame["parent_prim"])
    if not parent.IsValid():
        raise RuntimeError(f"profile parent is missing at runtime: {frame['parent_prim']}")
    parent_matrix = usd_geom.Xformable(parent).ComputeLocalToWorldTransform(
        usd.TimeCode.Default()
    )
    position = np.asarray(
        parent_matrix.Transform(gf.Vec3d(*frame["translation_parent_local_m"])),
        dtype=float,
    )
    w, x, y, z = (float(component) for component in frame["rotation_parent_local_wxyz"])
    quaternion_vector = np.asarray([x, y, z], dtype=float)
    local_z = np.asarray([0.0, 0.0, 1.0], dtype=float)
    twice_cross = 2.0 * np.cross(quaternion_vector, local_z)
    rotated_local_z = local_z + w * twice_cross + np.cross(quaternion_vector, twice_cross)
    world_z = _normalise(
        parent_matrix.TransformDir(gf.Vec3d(*rotated_local_z)),
        np,
    )
    return position, world_z


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "unbounded"
    try:
        return [_json_value(float(component)) for component in value]
    except (TypeError, ValueError):
        return str(value)


def _within(value: float, interval: tuple[float, float]) -> bool:
    return interval[0] <= value <= interval[1]


def _normalise(vector: Any, np: Any) -> Any:
    result = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(result))
    if norm <= 1.0e-9:
        raise RuntimeError("cannot normalise a zero vector")
    return result / norm


def _orientation_wxyz_for_z_axis(z_axis: Any, np: Any) -> Any:
    """Return a unit quaternion that maps the pusher's local +Z to ``z_axis``."""
    target = _normalise(z_axis, np)
    local_z = np.asarray([0.0, 0.0, 1.0], dtype=float)
    dot = float(np.clip(np.dot(local_z, target), -1.0, 1.0))
    if dot <= -1.0 + 1.0e-9:
        return np.asarray([0.0, 1.0, 0.0, 0.0], dtype=float)
    cross = np.cross(local_z, target)
    return _normalise(np.asarray([1.0 + dot, *cross], dtype=float), np)


def _lid_pusher_centers(
    contact_positions: list[Any],
    *,
    pivot: Any,
    axis: Any,
    direction_sign: float,
    pusher_half_depth_m: float,
    clearance_m: float,
    np: Any,
) -> tuple[list[Any], list[Any]]:
    """Offset the pusher center behind each measured lid contact position."""
    centers: list[Any] = []
    face_normals: list[Any] = []
    unit_axis = _normalise(axis, np)
    for contact_position in contact_positions:
        offset = contact_position - pivot
        radial = offset - unit_axis * float(np.dot(offset, unit_axis))
        face_normal = direction_sign * _normalise(np.cross(unit_axis, radial), np)
        centers.append(
            contact_position - face_normal * (pusher_half_depth_m + clearance_m)
        )
        face_normals.append(face_normal)
    return centers, face_normals


def _world_bound(stage: Any, prim_path: str, usd: Any, usd_geom: Any, np: Any) -> tuple[Any, Any]:
    cache = usd_geom.BBoxCache(usd.TimeCode.Default(), [usd_geom.Tokens.default_])
    bound = cache.ComputeWorldBound(stage.GetPrimAtPath(prim_path)).ComputeAlignedBox()
    minimum = np.asarray(bound.GetMin(), dtype=float)
    maximum = np.asarray(bound.GetMax(), dtype=float)
    if not np.isfinite(minimum).all() or not np.isfinite(maximum).all():
        raise RuntimeError(f"invalid world bound for {prim_path}")
    return minimum, maximum


def _world_axis(stage: Any, prim_path: str, axis_name: str, usd: Any, usd_geom: Any, gf: Any, np: Any) -> Any:
    basis = {
        "X": gf.Vec3d(1.0, 0.0, 0.0),
        "Y": gf.Vec3d(0.0, 1.0, 0.0),
        "Z": gf.Vec3d(0.0, 0.0, 1.0),
    }.get(axis_name)
    if basis is None:
        raise RuntimeError(f"unsupported joint axis: {axis_name!r}")
    matrix = usd_geom.Xformable(stage.GetPrimAtPath(prim_path)).ComputeLocalToWorldTransform(
        usd.TimeCode.Default()
    )
    return _normalise(matrix.TransformDir(basis), np)


def _joint_drive_snapshot(stage: Any) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for prim in stage.Traverse():
        for attribute in prim.GetAttributes():
            if attribute.GetName().startswith("drive:"):
                snapshot[str(attribute.GetPath())] = _json_value(attribute.Get())
    return dict(sorted(snapshot.items()))


def _contact_summary(view: Any, *, np: Any, dt: float) -> dict[str, Any]:
    matrix = view.get_contact_force_matrix(dt=dt)
    if matrix is None:
        return {
            "status": "blocked",
            "reason": "RigidContactView physics handle was unavailable",
        }
    force_matrix = np.asarray(matrix, dtype=float)
    details = view.get_contact_force_data(dt=dt)
    if details is None:
        return {
            "status": "blocked",
            "reason": "RigidContactView detailed contact data was unavailable",
        }
    forces, points, normals, distances, counts, starts = details
    count = int(np.asarray(counts)[0, 0])
    start = int(np.asarray(starts)[0, 0])
    entries = []
    for index in range(start, start + count):
        entries.append(
            {
                "force_n": [round(float(value), 8) for value in np.asarray(forces)[index].reshape(-1)],
                "point_m": [round(float(value), 8) for value in np.asarray(points)[index]],
                "normal": [round(float(value), 8) for value in np.asarray(normals)[index]],
                "separation_m": round(float(np.asarray(distances)[index].reshape(-1)[0]), 8),
            }
        )
    return {
        "status": "pass",
        "pair_contact_count": count,
        "force_vector_n": [
            round(float(value), 8) for value in force_matrix[0, 0].reshape(-1)
        ],
        "force_norm_n": round(float(np.linalg.norm(force_matrix[0, 0])), 8),
        "contacts": entries,
    }


def _max_contact_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [record for record in records if record.get("status") == "pass"]
    if not valid:
        return {"pair_contact_count": 0, "force_norm_n": 0.0, "contacts": []}
    return max(valid, key=lambda record: float(record.get("force_norm_n", 0.0)))


def _observed_state_values(
    records: list[dict[str, Any]],
    field_name: str,
    interval: tuple[float, float],
) -> list[float]:
    values: list[float] = []
    for record in records:
        raw_value = record.get(field_name)
        if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
            value = float(raw_value)
            if _within(value, interval):
                values.append(value)
    return values


def _all_values_within(values: list[float], interval: tuple[float, float]) -> bool:
    return bool(values) and all(_within(value, interval) for value in values)


def _create_kinematic_cube(stage: Any, path: str, *, size: tuple[float, float, float], usd_geom: Any, usd_physics: Any, gf: Any) -> None:
    cube = usd_geom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    cube.CreateVisibilityAttr(usd_geom.Tokens.invisible).Set(usd_geom.Tokens.invisible)
    cube.AddTranslateOp().Set(gf.Vec3d(0.0, 0.0, -10.0))
    cube.AddOrientOp().Set(gf.Quatf(1.0, gf.Vec3f(0.0, 0.0, 0.0)))
    cube.AddScaleOp().Set(gf.Vec3d(*size))
    prim = cube.GetPrim()
    usd_physics.CollisionAPI.Apply(prim)
    rigid = usd_physics.RigidBodyAPI.Apply(prim)
    rigid.CreateRigidBodyEnabledAttr().Set(True)
    rigid.CreateKinematicEnabledAttr().Set(True)


def _move_through_path(
    view: Any,
    contact_view: Any,
    positions: list[Any],
    *,
    world: Any,
    dt: float,
    np: Any,
    on_step: Any | None = None,
    stop_when: Any | None = None,
    session_translation_prim: Any | None = None,
    session_orientations_wxyz: list[Any] | None = None,
    gf: Any | None = None,
) -> list[dict[str, Any]]:
    if session_orientations_wxyz is not None and len(session_orientations_wxyz) != len(positions):
        raise ValueError("session orientations must match the controlled path length")
    records: list[dict[str, Any]] = []
    identity = np.asarray([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    for index, position in enumerate(positions):
        if session_translation_prim is None:
            view.set_world_poses(
                positions=np.asarray([position], dtype=np.float32),
                orientations=identity,
            )
        else:
            if gf is None:
                raise RuntimeError("session-layer kinematic motion requires Gf")
            _set_session_kinematic_position(
                session_translation_prim,
                position,
                gf=gf,
                orientation_wxyz=(
                    None
                    if session_orientations_wxyz is None
                    else session_orientations_wxyz[index]
                ),
            )
        world.step(render=False)
        record = _contact_summary(contact_view, np=np, dt=dt)
        observed_positions, _ = view.get_world_poses()
        record["controlled_body_world_position_m"] = [
            round(float(value), 8) for value in np.asarray(observed_positions[0])
        ]
        if on_step is not None:
            record.update(on_step())
        records.append(record)
        if stop_when is not None and stop_when(record):
            break
    return records


def _set_session_kinematic_position(
    prim: Any,
    position: Any,
    *,
    gf: Any,
    orientation_wxyz: Any | None = None,
) -> None:
    prim.GetAttribute("xformOp:translate").Set(
        gf.Vec3d(*[float(value) for value in position])
    )
    if orientation_wxyz is not None:
        w, x, y, z = (float(value) for value in orientation_wxyz)
        prim.GetAttribute("xformOp:orient").Set(
            gf.Quatf(w, gf.Vec3f(x, y, z))
        )


def _linear_positions(start: Any, end: Any, *, increment_m: float, np: Any) -> list[Any]:
    distance = float(np.linalg.norm(end - start))
    steps = max(2, int(math.ceil(distance / increment_m)) + 1)
    return [start + (end - start) * index / (steps - 1) for index in range(steps)]


def _arc_positions(
    *,
    center: Any,
    start_offset: Any,
    axis: Any,
    sweep_rad: float,
    increment_rad: float,
    np: Any,
) -> list[Any]:
    if increment_rad <= 0.0:
        raise ValueError("increment_rad must be positive")
    unit_axis = _normalise(axis, np)
    steps = max(2, int(math.ceil(abs(sweep_rad) / increment_rad)) + 1)
    values: list[Any] = []
    for index in range(steps):
        angle = sweep_rad * index / (steps - 1)
        cosine = math.cos(angle)
        sine = math.sin(angle)
        rotated = (
            start_offset * cosine
            + np.cross(unit_axis, start_offset) * sine
            + unit_axis
            * float(np.dot(unit_axis, start_offset))
            * (1.0 - cosine)
        )
        values.append(center + rotated)
    return values


def _reset_and_sync(
    world: Any,
    app: Any,
    *,
    steps: int,
    unregistered_kinematic_views: list[Any] | None = None,
) -> None:
    world.reset()
    for view in unregistered_kinematic_views or []:
        view.initialize()
    app.update()
    for _ in range(steps):
        world.step(render=False)


def _prepare_tube(stage: Any, tube_asset: Path, usd_physics: Any) -> None:
    tube = stage.DefinePrim(TUBE_PROBE_ROOT, "Xform")
    tube.GetReferences().AddReference(str(tube_asset), "/World/TestTube")
    rigid = usd_physics.RigidBodyAPI.Apply(tube)
    rigid.CreateRigidBodyEnabledAttr().Set(True)
    rigid.CreateKinematicEnabledAttr().Set(True)


def _runtime_dof_mapping(articulation: Any) -> list[dict[str, Any]]:
    names = list(articulation.dof_names)
    if len(names) != len(EXPECTED_DOF_MAPPING):
        raise RuntimeError(
            f"expected {len(EXPECTED_DOF_MAPPING)} runtime DOFs, found {len(names)}"
        )
    return [
        {
            "dof_index": index,
            "dof_name": names[index],
            "joint_prim": joint_prim,
        }
        for index, _, joint_prim in EXPECTED_DOF_MAPPING
    ]


def _qualified_package_identity(
    *,
    asset_entry_prim: str,
    runtime_profile: str,
    prequalification_manifest_sha256: str,
    asset_sha256_before: str,
    asset_sha256_after: str,
) -> dict[str, str]:
    return {
        "asset_path": "asset.usd",
        "asset_entry_prim": asset_entry_prim,
        "runtime_profile": runtime_profile,
        "prequalification_manifest_sha256": prequalification_manifest_sha256,
        "asset_usd_sha256_before": asset_sha256_before,
        "asset_usd_sha256_after": asset_sha256_after,
    }


def _runtime_profile_gate(
    observed_kit_version: object,
    expected_version: str = "4.1",
) -> dict[str, Any]:
    observed = str(observed_kit_version or "")
    status = (
        "pass"
        if observed == expected_version
        or observed.startswith(expected_version + ".")
        else "blocked"
    )
    return {
        "status": status,
        "expected_version": expected_version,
        "observed_kit_version": observed or None,
        "reason": (
            None
            if status == "pass"
            else "Runtime does not provide the required Isaac/Kit fingerprint."
        ),
    }


def _runtime_report_inputs(
    *,
    centrifuge_package: Path,
    tube_package: Path,
    profile: dict[str, Any],
    profile_sha256: str,
    input_hashes: dict[str, str],
    runtime_profile: str,
) -> dict[str, Any]:
    """Build finalizer-compatible bindings for a freshly executed five-gate run."""
    required_hashes = {
        "centrifuge_manifest_sha256",
        "centrifuge_asset_usd_sha256_before",
        "centrifuge_asset_usd_sha256_after",
        "tube_manifest_sha256",
        "tube_asset_usd_sha256_before",
        "tube_asset_usd_sha256_after",
    }
    missing = sorted(required_hashes - set(input_hashes))
    if missing:
        raise ValueError(f"runtime input hashes are incomplete: {missing}")
    source_sha256 = profile.get("source_sha256")
    if not isinstance(source_sha256, str) or not source_sha256:
        raise ValueError("device profile source_sha256 is missing")
    source_integrity = {
        "status": (
            "pass"
            if input_hashes["centrifuge_asset_usd_sha256_before"]
            == input_hashes["centrifuge_asset_usd_sha256_after"]
            and input_hashes["tube_asset_usd_sha256_before"]
            == input_hashes["tube_asset_usd_sha256_after"]
            else "blocked"
        ),
        **input_hashes,
    }
    return {
        "centrifuge_package": str(centrifuge_package),
        "tube_package": str(tube_package),
        "centrifuge_asset_entry_prim": CENTRIFUGE_ROOT,
        "tube_probe_prim": TUBE_PROBE_ROOT,
        "device_profile": {
            "schema_version": profile["schema_version"],
            "profile_sha256": profile_sha256,
            "source_sha256": source_sha256,
        },
        "integrity": source_integrity,
        "qualified_package": _qualified_package_identity(
            asset_entry_prim=CENTRIFUGE_ROOT,
            runtime_profile=runtime_profile,
            prequalification_manifest_sha256=input_hashes[
                "centrifuge_manifest_sha256"
            ],
            asset_sha256_before=input_hashes[
                "centrifuge_asset_usd_sha256_before"
            ],
            asset_sha256_after=input_hashes[
                "centrifuge_asset_usd_sha256_after"
            ],
        ),
    }


def _write_report(output_dir: Path, report: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.json"
    report_path.write_text(
        json.dumps(
            _json_value(report),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    digest_path = output_dir / "report.sha256.json"
    digest_path.write_text(
        json.dumps(
            {"report": report_path.name, "report_sha256": _sha256_file(report_path)},
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


def _run(args: argparse.Namespace) -> dict[str, Any]:
    manifest = _json_object(args.centrifuge_manifest)
    source = manifest.get("source")
    entrypoints = manifest.get("entrypoints")
    if (
        not isinstance(source, dict)
        or not isinstance(source.get("sha256"), str)
        or not isinstance(entrypoints, dict)
        or entrypoints.get("asset_entry_prim") != CENTRIFUGE_ROOT
    ):
        raise ValueError("centrifuge manifest does not describe the expected articulation root")
    profile = _load_device_profile(
        args.device_profile,
        source_sha256=source["sha256"],
        articulation_root_prim=CENTRIFUGE_ROOT,
    )
    profile_sha256 = _sha256_file(args.device_profile)
    # Isaac Sim must be constructed before importing omni or pxr modules.
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting"})
    try:
        import numpy as np
        import omni.kit.app
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from omni.isaac.core.prims import RigidPrimView
        from pxr import Gf, Usd, UsdGeom, UsdPhysics

        centrifuge_asset = args.centrifuge_package / "asset.usd"
        tube_asset = args.tube_package / "asset.usd"
        for path in (centrifuge_asset, tube_asset):
            if not path.is_file():
                raise FileNotFoundError(path)

        input_hashes = {
            "centrifuge_asset_usd_sha256_before": _sha256_file(centrifuge_asset),
            "tube_asset_usd_sha256_before": _sha256_file(tube_asset),
            "centrifuge_manifest_sha256": _sha256_file(args.centrifuge_manifest),
            "tube_manifest_sha256": _sha256_file(args.tube_manifest),
        }
        context = omni.usd.get_context()
        if not context.open_stage(str(centrifuge_asset)):
            raise RuntimeError(f"could not open centrifuge package: {centrifuge_asset}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(60):
            app.update()
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("Isaac did not provide an open USD stage")
        kit_app = omni.kit.app.get_app()
        observed_kit_version = (
            str(kit_app.get_app_version()) if kit_app is not None else None
        )
        runtime_profile_gate = _runtime_profile_gate(observed_kit_version)
        if runtime_profile_gate.get("status") != "pass":
            return {
                "schema_version": "aan.articulation_runtime_qualification.v1",
                "status": "blocked",
                "runtime": {"runtime_profile_gate": runtime_profile_gate},
                "host_failure": (
                    "Isaac/Kit runtime fingerprint does not match required 4.1"
                ),
            }
        observed_major_minor = ".".join(
            str(runtime_profile_gate["observed_kit_version"]).split(".", 2)[:2]
        )
        runtime_profile = "isaac" + observed_major_minor.replace(".", "")
        stage.SetEditTarget(stage.GetSessionLayer())

        _prepare_tube(stage, tube_asset, UsdPhysics)
        _create_kinematic_cube(
            stage,
            "/World/__aan_task_contact_probe/button_pusher",
            size=(0.02, 0.02, 0.02),
            usd_geom=UsdGeom,
            usd_physics=UsdPhysics,
            gf=Gf,
        )
        _create_kinematic_cube(
            stage,
            "/World/__aan_task_contact_probe/lid_pusher",
            size=LID_PUSHER_SIZE_M,
            usd_geom=UsdGeom,
            usd_physics=UsdPhysics,
            gf=Gf,
        )

        world = World(
            stage_units_in_meters=1.0,
            physics_dt=float(args.physics_dt),
            rendering_dt=float(args.physics_dt),
        )
        articulation = Articulation(CENTRIFUGE_ROOT, name="centrifuge_contact_probe")
        button_pusher = RigidPrimView(
            "/World/__aan_task_contact_probe/button_pusher",
            name="button_contact_pusher",
            track_contact_forces=True,
            contact_filter_prim_paths_expr=[BUTTON_PROXY],
            max_contact_count=64,
            disable_stablization=False,
        )
        lid_pusher = RigidPrimView(
            "/World/__aan_task_contact_probe/lid_pusher",
            name="lid_contact_pusher",
            track_contact_forces=True,
            contact_filter_prim_paths_expr=[LID_PROXY],
            max_contact_count=64,
            disable_stablization=False,
        )
        tube = RigidPrimView(
            TUBE_PROBE_ROOT,
            name="tube_insertion_probe",
            track_contact_forces=True,
            contact_filter_prim_paths_expr=[ROTOR_BODY, LID_BODY],
            max_contact_count=128,
            disable_stablization=False,
        )
        world.scene.add(articulation)
        kinematic_contact_views = [button_pusher, lid_pusher, tube]
        _reset_and_sync(
            world,
            app,
            steps=30,
            unregistered_kinematic_views=kinematic_contact_views,
        )
        # RigidPrimView.post_reset writes linear/angular velocity defaults, which
        # is invalid for these intentionally kinematic qualification probes.
        # Manual initialization keeps their contact views live without enrolling
        # them in World.scene reset handling.
        if not articulation.handles_initialized:
            raise RuntimeError("centrifuge Articulation handle did not initialize")
        if articulation.num_dof != len(EXPECTED_DOF_MAPPING):
            raise RuntimeError(
                f"expected {len(EXPECTED_DOF_MAPPING)} centrifuge DOFs, found {articulation.num_dof}"
            )

        drives_before = _joint_drive_snapshot(stage)
        dof_mapping = _runtime_dof_mapping(articulation)

        def joint_positions() -> Any:
            return np.asarray(articulation.get_joint_positions(), dtype=float)

        # First demonstrate the package reset state without any probe contact.
        _reset_and_sync(
            world,
            app,
            steps=60,
            unregistered_kinematic_views=kinematic_contact_views,
        )
        reset_positions = joint_positions()
        button_reset = float(reset_positions[0])
        rotor_reset = float(reset_positions[1])
        lid_reset = float(reset_positions[2])
        button_reset_gate = {
            "status": "pass" if _within(button_reset, BUTTON_RELEASED_BAND) else "blocked",
            "observed_runtime_position_m": button_reset,
            "required_released_band_m": list(BUTTON_RELEASED_BAND),
        }
        rotor_reset_gate = {
            "status": "pass" if _within(rotor_reset, ROTOR_PARKED_BAND) else "blocked",
            "observed_runtime_position_rad": rotor_reset,
            "required_parked_band_rad": list(ROTOR_PARKED_BAND),
        }

        # The actual tube collider follows the producer-measured profile frame,
        # not a consumer-owned world-coordinate estimate.
        _reset_and_sync(
            world,
            app,
            steps=30,
            unregistered_kinematic_views=kinematic_contact_views,
        )
        socket_aperture, socket_axis = _profile_frame_world_pose(
            stage,
            profile,
            "tube_socket_0_aperture",
            usd=Usd,
            usd_geom=UsdGeom,
            gf=Gf,
            np=np,
        )
        tube_target, _ = _profile_frame_world_pose(
            stage,
            profile,
            "tube_socket_0_inserted_bottom_parked_root",
            usd=Usd,
            usd_geom=UsdGeom,
            gf=Gf,
            np=np,
        )
        aperture_to_target = tube_target - socket_aperture
        insertion_depth = -float(np.dot(aperture_to_target, socket_axis))
        lateral_error = float(
            np.linalg.norm(aperture_to_target + insertion_depth * socket_axis)
        )
        if insertion_depth <= 0.0 or lateral_error > 0.001:
            raise RuntimeError(
                "profile socket frames do not define a common insertion axis"
            )
        tube_start = socket_aperture + socket_axis * 0.09
        tube.set_world_poses(
            positions=np.asarray([tube_start], dtype=np.float32),
            orientations=np.asarray([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32),
        )
        world.step(render=False)
        rotor_min, rotor_max = _world_bound(stage, ROTOR_BODY, Usd, UsdGeom, np)
        insertion_contacts = _move_through_path(
            tube,
            tube,
            _linear_positions(tube_start, tube_target, increment_m=0.001, np=np),
            world=world,
            dt=float(args.physics_dt),
            np=np,
        )
        rotor_contacts = [
            record
            for record in insertion_contacts
            if record.get("status") == "pass" and record.get("pair_contact_count", 0) > 0
        ]
        tube_support_crossed_aperture = (
            float(np.dot(tube_start - socket_aperture, socket_axis)) > 0.0
            and float(np.dot(tube_target - socket_aperture, socket_axis)) < 0.0
        )
        tube_at_target_positions, _ = tube.get_world_poses()
        tube_at_target = np.asarray(tube_at_target_positions[0], dtype=float)
        tube_target_error = float(np.linalg.norm(tube_at_target - tube_target))
        insertion_gate = {
            "status": (
                "pass"
                if tube_support_crossed_aperture
                and not rotor_contacts
                and tube_target_error <= 0.001
                else "blocked"
            ),
            "method": "session-only kinematic sweep of the delivered tube collider",
            "claim_boundary": "Collider path qualification only; no robot-policy success claim.",
            "tube_package_asset_usd_sha256": input_hashes["tube_asset_usd_sha256_before"],
            "tube_radius_m": TUBE_RADIUS_M,
            "tube_height_m": TUBE_HEIGHT_M,
            "profile_aperture_world_m": [
                round(float(value), 8) for value in socket_aperture
            ],
            "profile_insertion_axis_world": [
                round(float(value), 8) for value in socket_axis
            ],
            "profile_insertion_depth_m": round(insertion_depth, 8),
            "profile_lateral_error_m": round(lateral_error, 8),
            "start_support_position_m": [round(float(value), 8) for value in tube_start],
            "target_support_position_m": [round(float(value), 8) for value in tube_target],
            "observed_target_support_position_m": [round(float(value), 8) for value in tube_at_target],
            "target_error_m": round(tube_target_error, 8),
            "rotor_world_bounds_m": {
                "min": [round(float(value), 8) for value in rotor_min],
                "max": [round(float(value), 8) for value in rotor_max],
            },
            "support_crossed_rotor_top_plane": bool(tube_support_crossed_aperture),
            "rotor_pair_contact_samples": len(rotor_contacts),
            "peak_rotor_pair_contact": _max_contact_record(rotor_contacts),
        }

        # Push the button from each physical side.  The accepted run must create
        # pair-filtered contact and move the measured prismatic DOF into pressed.
        button_center, button_axis = _profile_frame_world_pose(
            stage,
            profile,
            "start_button_press",
            usd=Usd,
            usd_geom=UsdGeom,
            gf=Gf,
            np=np,
        )
        button_pusher_prim = stage.GetPrimAtPath(
            "/World/__aan_task_contact_probe/button_pusher"
        )
        button_attempts = []
        for direction_sign in (-1.0, 1.0):
            _reset_and_sync(
                world,
                app,
                steps=30,
                unregistered_kinematic_views=kinematic_contact_views,
            )
            direction = button_axis * direction_sign
            start = button_center - direction * 0.08
            end = button_center + direction * 0.03
            _set_session_kinematic_position(button_pusher_prim, start, gf=Gf)
            world.step(render=False)
            records = _move_through_path(
                button_pusher,
                button_pusher,
                _linear_positions(start, end, increment_m=0.001, np=np),
                world=world,
                dt=float(args.physics_dt),
                np=np,
                on_step=lambda: {"button_runtime_position_m": float(joint_positions()[0])},
                session_translation_prim=button_pusher_prim,
                gf=Gf,
            )
            button_positions = [
                float(record["button_runtime_position_m"])
                for record in records
                if "button_runtime_position_m" in record
            ]
            minimum = min(button_positions)
            maximum = max(button_positions)
            pressed_values = _observed_state_values(
                records,
                "button_runtime_position_m",
                BUTTON_PRESSED_BAND,
            )
            contacts = [
                record
                for record in records
                if record.get("status") == "pass" and record.get("pair_contact_count", 0) > 0
            ]
            for position in _linear_positions(end, start, increment_m=0.001, np=np):
                _set_session_kinematic_position(button_pusher_prim, position, gf=Gf)
                world.step(render=False)
            for _ in range(100):
                world.step(render=False)
            released = float(joint_positions()[0])
            button_attempts.append(
                {
                    "direction_sign": direction_sign,
                    "start_m": [round(float(value), 8) for value in start],
                    "end_m": [round(float(value), 8) for value in end],
                    "minimum_runtime_position_m": minimum,
                    "maximum_runtime_position_m": maximum,
                    "pressed_runtime_position_samples_m": [
                        round(value, 8) for value in pressed_values
                    ],
                    "post_withdrawal_position_m": released,
                    "pair_contact_samples": len(contacts),
                    "peak_pair_contact": _max_contact_record(contacts),
                    "observed_controlled_path_start_m": records[0][
                        "controlled_body_world_position_m"
                    ],
                    "observed_controlled_path_end_m": records[-1][
                        "controlled_body_world_position_m"
                    ],
                    "pressed": bool(pressed_values),
                    "released_after_withdrawal": _within(released, BUTTON_RELEASED_BAND),
                }
            )
        successful_button_attempts = [
            item
            for item in button_attempts
            if item["pair_contact_samples"] > 0
            and item["pressed"]
            and item["released_after_withdrawal"]
        ]
        button_gate = {
            "status": "pass" if successful_button_attempts else "blocked",
            "method": "kinematic pusher with pair-filtered PhysX contact",
            "button_semantics": "momentary",
            "required_pressed_band_m": list(BUTTON_PRESSED_BAND),
            "required_released_band_m": list(BUTTON_RELEASED_BAND),
            "attempts": button_attempts,
        }

        # Keep the actual tube at its admitted target while checking the lid. The
        # pusher follows a hinge-centered arc so it stays tangential as the shell
        # turns; only physical pair contact with a closed-state response qualifies.
        lid_pusher_prim = stage.GetPrimAtPath(
            "/World/__aan_task_contact_probe/lid_pusher"
        )
        lid_joint = stage.GetPrimAtPath(LID_JOINT)
        local_pivot = lid_joint.GetAttribute("physics:localPos0").Get()
        base_matrix = UsdGeom.Xformable(
            stage.GetPrimAtPath(CENTRIFUGE_ROOT + "/group_0")
        ).ComputeLocalToWorldTransform(
            Usd.TimeCode.Default()
        )
        pivot = np.asarray(base_matrix.Transform(local_pivot), dtype=float)
        lid_axis = _world_axis(
            stage,
            CENTRIFUGE_ROOT + "/group_0",
            "X",
            Usd,
            UsdGeom,
            Gf,
            np,
        )
        lid_attempts = []
        # The profile contact's positive right-hand tangent advances the lid
        # from its open lower state toward its closed upper state. A reverse
        # sweep only pushes into the lower joint limit and is not a closure test.
        for direction_sign in (1.0,):
            _reset_and_sync(
                world,
                app,
                steps=30,
                unregistered_kinematic_views=kinematic_contact_views,
            )
            tube.set_world_poses(
                positions=np.asarray([tube_target], dtype=np.float32),
                orientations=np.asarray([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32),
            )
            world.step(render=False)
            lid_center, _ = _profile_frame_world_pose(
                stage,
                profile,
                "lid_close_contact",
                usd=Usd,
                usd_geom=UsdGeom,
                gf=Gf,
                np=np,
            )
            contact_arc_positions = _arc_positions(
                center=pivot,
                start_offset=lid_center - pivot,
                axis=lid_axis,
                sweep_rad=direction_sign * float(args.lid_sweep_rad),
                increment_rad=0.0075,
                np=np,
            )
            arc_positions, arc_face_normals = _lid_pusher_centers(
                contact_arc_positions,
                pivot=pivot,
                axis=lid_axis,
                direction_sign=direction_sign,
                pusher_half_depth_m=LID_PUSHER_HALF_DEPTH_M,
                clearance_m=LID_PUSHER_CLEARANCE_M,
                np=np,
            )
            direction = arc_face_normals[0]
            approach_end = arc_positions[0]
            start = approach_end - direction * 0.08
            approach_positions = _linear_positions(
                start,
                approach_end,
                increment_m=0.0015,
                np=np,
            )
            positions = approach_positions + arc_positions[1:]
            orientations = [
                _orientation_wxyz_for_z_axis(direction, np)
                for _ in approach_positions
            ] + [
                _orientation_wxyz_for_z_axis(face_normal, np)
                for face_normal in arc_face_normals[1:]
            ]
            end = positions[-1]
            _set_session_kinematic_position(
                lid_pusher_prim,
                start,
                gf=Gf,
                orientation_wxyz=orientations[0],
            )
            world.step(render=False)
            records = _move_through_path(
                lid_pusher,
                lid_pusher,
                positions,
                world=world,
                dt=float(args.physics_dt),
                np=np,
                on_step=lambda: {
                    "lid_runtime_position_rad": float(joint_positions()[2]),
                    "tube_lid_pair_contact": _contact_summary(tube, np=np, dt=float(args.physics_dt)),
                },
                stop_when=lambda record: _within(
                    float(record.get("lid_runtime_position_rad", float("nan"))),
                    LID_CLOSED_BAND,
                ),
                session_translation_prim=lid_pusher_prim,
                session_orientations_wxyz=orientations,
                gf=Gf,
            )
            lid_positions = [
                float(record["lid_runtime_position_rad"])
                for record in records
                if "lid_runtime_position_rad" in record
            ]
            minimum = min(lid_positions)
            maximum = max(lid_positions)
            stayed_within_travel_range = _all_values_within(
                lid_positions,
                LID_TRAVEL_BAND,
            )
            closed_values = _observed_state_values(
                records,
                "lid_runtime_position_rad",
                LID_CLOSED_BAND,
            )
            lid_contacts = [
                record
                for record in records
                if record.get("status") == "pass" and record.get("pair_contact_count", 0) > 0
            ]
            tube_lid_contacts = [
                record["tube_lid_pair_contact"]
                for record in records
                if record.get("tube_lid_pair_contact", {}).get("status") == "pass"
                and record["tube_lid_pair_contact"].get("pair_contact_count", 0) > 0
            ]
            executed_positions = positions[: len(records)]
            executed_orientations = orientations[: len(records)]
            for position, orientation in zip(
                reversed(executed_positions),
                reversed(executed_orientations),
            ):
                _set_session_kinematic_position(
                    lid_pusher_prim,
                    position,
                    gf=Gf,
                    orientation_wxyz=orientation,
                )
                world.step(render=False)
            for _ in range(120):
                world.step(render=False)
            returned = float(joint_positions()[2])
            lid_attempts.append(
                {
                    "direction_sign": direction_sign,
                    "trajectory": "linear_approach_then_hinge_arc",
                    "pusher_sweep_rad": direction_sign * float(args.lid_sweep_rad),
                    "pusher_half_depth_m": LID_PUSHER_HALF_DEPTH_M,
                    "pusher_clearance_m": LID_PUSHER_CLEARANCE_M,
                    "trajectory_stopped_on_closed_band": bool(closed_values),
                    "hinge_world_position_m": [
                        round(float(value), 8) for value in pivot
                    ],
                    "hinge_axis_world": [
                        round(float(value), 8) for value in lid_axis
                    ],
                    "start_m": [round(float(value), 8) for value in start],
                    "approach_end_m": [
                        round(float(value), 8) for value in approach_end
                    ],
                    "end_m": [round(float(value), 8) for value in end],
                    "minimum_runtime_position_rad": minimum,
                    "maximum_runtime_position_rad": maximum,
                    "required_travel_band_rad": list(LID_TRAVEL_BAND),
                    "stayed_within_travel_range": stayed_within_travel_range,
                    "closed_runtime_position_samples_rad": [
                        round(value, 8) for value in closed_values
                    ],
                    "post_withdrawal_position_rad": returned,
                    "pair_contact_samples": len(lid_contacts),
                    "peak_pair_contact": _max_contact_record(lid_contacts),
                    "observed_controlled_path_start_m": records[0][
                        "controlled_body_world_position_m"
                    ],
                    "observed_controlled_path_end_m": records[-1][
                        "controlled_body_world_position_m"
                    ],
                    "tube_lid_pair_contact_samples": len(tube_lid_contacts),
                    "peak_tube_lid_pair_contact": _max_contact_record(tube_lid_contacts),
                    "closed": bool(closed_values),
                    "returned_open": _within(returned, LID_OPEN_BAND),
                }
            )
        successful_lid_attempts = [
            item
            for item in lid_attempts
            if item["pair_contact_samples"] > 0
            and item["closed"]
            and item["returned_open"]
            and item["stayed_within_travel_range"]
            and item["tube_lid_pair_contact_samples"] == 0
        ]
        lid_gate = {
            "status": "pass" if successful_lid_attempts else "blocked",
            "method": "linear-approach hinge-centered kinematic pusher with pair-filtered PhysX contact",
            "required_closed_band_rad": list(LID_CLOSED_BAND),
            "required_open_band_rad": list(LID_OPEN_BAND),
            "required_travel_band_rad": list(LID_TRAVEL_BAND),
            "tube_at_inserted_target_during_lid_probe": True,
            "attempts": lid_attempts,
        }

        drives_after = _joint_drive_snapshot(stage)
        drive_integrity = {
            "status": "pass" if drives_before == drives_after else "blocked",
            "before": drives_before,
            "after": drives_after,
            "description": "No centrifuge drive:* attributes may change during physical-contact qualification.",
        }
        input_hashes.update(
            {
                "centrifuge_asset_usd_sha256_after": _sha256_file(centrifuge_asset),
                "tube_asset_usd_sha256_after": _sha256_file(tube_asset),
            }
        )
        task_gates = {
            "lid_contact_cycle": lid_gate,
            "button_contact_cycle": button_gate,
            "button_reset_stability": button_reset_gate,
            "rotor_reset_stability": rotor_reset_gate,
            "socket_insertion_clearance": insertion_gate,
        }
        if tuple(task_gates) != FIVE_INTERACTION_GATES:
            raise RuntimeError("five-gate report construction order has drifted")
        report_inputs = _runtime_report_inputs(
            centrifuge_package=args.centrifuge_package,
            tube_package=args.tube_package,
            profile=profile,
            profile_sha256=profile_sha256,
            input_hashes=input_hashes,
            runtime_profile=runtime_profile,
        )
        source_integrity = report_inputs["integrity"]
        overall = "pass" if all(gate["status"] == "pass" for gate in task_gates.values()) and drive_integrity["status"] == "pass" and source_integrity["status"] == "pass" else "blocked"
        return {
            "schema_version": "aan.articulation_runtime_qualification.v1",
            "status": overall,
            "runtime": {
                "runtime_profile": runtime_profile,
                "runtime_profile_gate": runtime_profile_gate,
                "physics_dt_seconds": float(args.physics_dt),
                "contact_method": "session-layer kinematic collision pushers with RigidContactView pair filtering",
                "source_mutation": "none",
            },
            "inputs": report_inputs,
            "runtime_dof_mapping": dof_mapping,
            "reset_runtime_positions": {
                "button_m": button_reset,
                "rotor_rad": rotor_reset,
                "lid_rad": lid_reset,
            },
            "drive_integrity": drive_integrity,
            "task_gates": task_gates,
            "claim_boundary": "This proves only the package's specified collider/contact and articulated-state gates. It does not claim robot-policy success, benchmark score, or real-world physical parity.",
        }
    finally:
        # Isaac Sim 4.1 can terminate the interpreter from ``close()`` before
        # the caller persists its report.  This short-lived CLI process exits
        # immediately after writing evidence, so Kit teardown remains process
        # scoped rather than risking a lost qualification record.
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run ConvertAsset-owned Isaac Sim 4.1 physical-contact "
            "qualification for the centrifuge's five interaction gates."
        )
    )
    parser.add_argument(
        "--centrifuge-package",
        type=Path,
        default=DEFAULT_CENTRIFUGE_PACKAGE,
    )
    parser.add_argument("--tube-package", type=Path, default=DEFAULT_TUBE_PACKAGE)
    parser.add_argument("--centrifuge-manifest", type=Path)
    parser.add_argument("--tube-manifest", type=Path)
    parser.add_argument(
        "--device-profile",
        type=Path,
        required=True,
        help="Producer-measured pre-promotion articulated device profile.",
    )
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--physics-dt", type=float, default=0.01)
    parser.add_argument(
        "--lid-sweep-rad",
        type=float,
        default=2.0,
        help="Signed sweep magnitude for each profile-driven lid contact attempt.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.centrifuge_package = args.centrifuge_package.resolve()
    args.tube_package = args.tube_package.resolve()
    args.device_profile = args.device_profile.resolve()
    if args.lid_sweep_rad <= 0.0:
        raise SystemExit("--lid-sweep-rad must be positive")
    args.centrifuge_manifest = (
        args.centrifuge_manifest.resolve()
        if args.centrifuge_manifest is not None
        else args.centrifuge_package.parent / "package.manifest.json"
    )
    args.tube_manifest = (
        args.tube_manifest.resolve()
        if args.tube_manifest is not None
        else args.tube_package.parent / "package.manifest.json"
    )
    args.out_dir = (
        args.out_dir.resolve()
        if args.out_dir is not None
        else args.centrifuge_package / "evidence/articulated_task_qualification"
    )
    report: dict[str, Any]
    try:
        report = _run(args)
    except Exception as exc:
        report = {
            "schema_version": "aan.articulation_runtime_qualification.v1",
            "status": "blocked",
            "host_failure": f"{type(exc).__name__}: {exc}",
        }
    report_path = _write_report(args.out_dir, report)
    print(json.dumps({"status": report["status"], "report": str(report_path)}), flush=True)
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
