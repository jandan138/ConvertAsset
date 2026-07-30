#!/usr/bin/env python3
"""Qualify an articulated package for stable benchtop placement in Isaac 4.1.

The public process launches a short-lived worker of this same script, captures
its stderr, evaluates geometry and scoped PhysX evidence, and merges the
``benchtop_stability`` gate into an existing articulation runtime report.  The
merged report is directly consumable by ``finalize_articulated_package.py`` and
therefore cannot become an unbound evidence sidecar.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping


PROFILE_SCHEMA_VERSION = "aan.articulated_device_profile.v1"
REPORT_SCHEMA_VERSION = "aan.articulation_runtime_qualification.v1"
RELEASE_HEIGHT_M = 0.010
WARMUP_FRAMES = 50
SETTLE_FRAMES = 240
MAXIMUM_ROOT_TILT_DEG = 10.0
MAXIMUM_SUPPORT_GAP_M = 0.010
MAXIMUM_TABLE_PENETRATION_M = 0.001
MAXIMUM_EXTENT_RELATIVE_ERROR = 0.05
DEFAULT_PHYSICS_DT_SECONDS = 1.0 / 60.0


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to replace qualification evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to replace qualification evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _finite_vector(value: Any, length: int, label: str) -> list[float]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != length
        or any(
            isinstance(component, bool)
            or not isinstance(component, (int, float))
            or not math.isfinite(float(component))
            for component in value
        )
    ):
        raise ValueError(f"{label} must contain {length} finite numbers")
    return [float(component) for component in value]


def _normalise_quaternion(value: Any, label: str) -> list[float]:
    quaternion = _finite_vector(value, 4, label)
    norm = math.sqrt(sum(component * component for component in quaternion))
    if norm <= 1.0e-12:
        raise ValueError(f"{label} must not be zero")
    return [component / norm for component in quaternion]


def _cross(left: Iterable[float], right: Iterable[float]) -> list[float]:
    a = list(left)
    b = list(right)
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _quaternion_rotate(
    quaternion_wxyz: Any,
    vector_xyz: Any,
) -> list[float]:
    quaternion = _normalise_quaternion(quaternion_wxyz, "quaternion")
    vector = _finite_vector(vector_xyz, 3, "vector")
    real = quaternion[0]
    imaginary = quaternion[1:]
    twice_cross = [2.0 * value for value in _cross(imaginary, vector)]
    correction = _cross(imaginary, twice_cross)
    return [
        vector[index]
        + real * twice_cross[index]
        + correction[index]
        for index in range(3)
    ]


def _quaternion_inverse_rotate(
    quaternion_wxyz: Any,
    vector_xyz: Any,
) -> list[float]:
    quaternion = _normalise_quaternion(quaternion_wxyz, "quaternion")
    return _quaternion_rotate(
        [quaternion[0], -quaternion[1], -quaternion[2], -quaternion[3]],
        vector_xyz,
    )


def _root_tilt_degrees(
    initial_orientation_wxyz: Any,
    final_orientation_wxyz: Any,
) -> float:
    initial_up = _quaternion_rotate(
        initial_orientation_wxyz,
        [0.0, 0.0, 1.0],
    )
    final_up = _quaternion_rotate(
        final_orientation_wxyz,
        [0.0, 0.0, 1.0],
    )
    dot = max(
        -1.0,
        min(1.0, sum(a * b for a, b in zip(initial_up, final_up))),
    )
    return math.degrees(math.acos(dot))


def _relative_extent_errors(
    initial_extent: Any,
    final_extent: Any,
) -> list[float]:
    initial = _finite_vector(initial_extent, 3, "initial_extent_m")
    final = _finite_vector(final_extent, 3, "final_extent_m")
    if any(component <= 1.0e-9 for component in initial):
        raise ValueError("initial_extent_m must be positive on every axis")
    return [
        abs(final[index] - initial[index]) / initial[index]
        for index in range(3)
    ]


def _scoped_physx_error_lines(
    stderr: str,
    scope_prim: str,
) -> list[str]:
    """Return only PhysX error lines that identify the admitted asset scope."""
    if not isinstance(stderr, str):
        raise ValueError("stderr must be text")
    scope = scope_prim.strip().lower()
    if not scope.startswith("/") or scope == "/":
        raise ValueError("scope_prim must be an absolute non-root prim path")
    leaf = scope.rsplit("/", 1)[-1]
    result: list[str] = []
    for raw_line in stderr.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        is_physx_error = (
            "physx" in lowered
            and (
                "[error]" in lowered
                or "physx error" in lowered
                or "error:" in lowered
            )
        )
        identifies_scope = scope in lowered or leaf in lowered
        if is_physx_error and identifies_scope:
            result.append(line)
    return result


def _evaluate_stability_observation(
    observation: Mapping[str, Any],
    *,
    scoped_physx_errors: list[str],
) -> dict[str, Any]:
    """Evaluate one runtime observation against the fixed r9 protocol."""
    initial_pose = observation.get("initial_root_pose")
    final_pose = observation.get("final_root_pose")
    if not isinstance(initial_pose, Mapping) or not isinstance(
        final_pose,
        Mapping,
    ):
        raise ValueError("initial_root_pose and final_root_pose are required")
    initial_orientation = _normalise_quaternion(
        initial_pose.get("orientation_wxyz"),
        "initial_root_pose.orientation_wxyz",
    )
    final_orientation = _normalise_quaternion(
        final_pose.get("orientation_wxyz"),
        "final_root_pose.orientation_wxyz",
    )
    _finite_vector(initial_pose.get("position_m"), 3, "initial_root_pose.position_m")
    _finite_vector(final_pose.get("position_m"), 3, "final_root_pose.position_m")
    final_support = _finite_vector(
        observation.get("final_support_world_m"),
        3,
        "final_support_world_m",
    )
    table_top = observation.get("table_top_z_m")
    if (
        isinstance(table_top, bool)
        or not isinstance(table_top, (int, float))
        or not math.isfinite(float(table_top))
    ):
        raise ValueError("table_top_z_m must be finite")
    extent_errors = _relative_extent_errors(
        observation.get("initial_extent_m"),
        observation.get("final_extent_m"),
    )
    tilt = _root_tilt_degrees(initial_orientation, final_orientation)
    support_gap = final_support[2] - float(table_top)
    table_penetration = max(0.0, -support_gap)
    source_integrity = observation.get("source_integrity")
    source_integrity_pass = (
        isinstance(source_integrity, Mapping)
        and source_integrity.get("status") == "pass"
    )
    blocked_reasons: list[str] = []
    if (
        observation.get("release_height_m") != RELEASE_HEIGHT_M
        or observation.get("warmup_frames") != WARMUP_FRAMES
        or observation.get("settle_frames") != SETTLE_FRAMES
    ):
        blocked_reasons.append("protocol_mismatch")
    if tilt > MAXIMUM_ROOT_TILT_DEG:
        blocked_reasons.append("root_tilt_exceeds_limit")
    if max(extent_errors) > MAXIMUM_EXTENT_RELATIVE_ERROR:
        blocked_reasons.append("extent_drift_exceeds_limit")
    if abs(support_gap) > MAXIMUM_SUPPORT_GAP_M:
        blocked_reasons.append("support_gap_exceeds_limit")
    if table_penetration > MAXIMUM_TABLE_PENETRATION_M:
        blocked_reasons.append("table_penetration")
    if scoped_physx_errors:
        blocked_reasons.append("scoped_physx_errors")
    if not source_integrity_pass:
        blocked_reasons.append("source_integrity")
    return {
        "status": "pass" if not blocked_reasons else "blocked",
        "method": (
            "10 mm free release onto a session-only static table, followed by "
            "50 zero-action warmup frames and 240 settle frames"
        ),
        "release_height_m": observation.get("release_height_m"),
        "warmup_frames": observation.get("warmup_frames"),
        "settle_frames": observation.get("settle_frames"),
        "thresholds": {
            "maximum_root_tilt_deg": MAXIMUM_ROOT_TILT_DEG,
            "maximum_support_gap_m": MAXIMUM_SUPPORT_GAP_M,
            "maximum_table_penetration_m": MAXIMUM_TABLE_PENETRATION_M,
            "maximum_extent_relative_error": MAXIMUM_EXTENT_RELATIVE_ERROR,
            "required_scoped_physx_error_count": 0,
        },
        "root_tilt_deg": tilt,
        "support_gap_m": support_gap,
        "table_penetration_m": table_penetration,
        "extent_relative_error_by_axis": extent_errors,
        "maximum_extent_relative_error": max(extent_errors),
        "scoped_physx_error_count": len(scoped_physx_errors),
        "scoped_physx_errors": scoped_physx_errors,
        "source_integrity": deepcopy(source_integrity),
        "observation": deepcopy(dict(observation)),
        "blocked_reasons": blocked_reasons,
        "claim_boundary": (
            "This gate proves only the specified Isaac 4.1 benchtop release "
            "and settle protocol. It does not claim robot-policy success, "
            "benchmark success, or real-world physical calibration."
        ),
    }


def _merge_stability_gate(
    runtime_report: Mapping[str, Any],
    *,
    gate: Mapping[str, Any],
    profile_sha256: str,
    source_sha256: str,
) -> dict[str, Any]:
    """Merge stability into the report that the package finalizer hash-binds."""
    report = deepcopy(dict(runtime_report))
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ValueError("base runtime report schema_version is unsupported")
    inputs = report.get("inputs")
    if not isinstance(inputs, dict):
        raise ValueError("base runtime report.inputs must be an object")
    device_profile = inputs.get("device_profile")
    if not isinstance(device_profile, dict):
        raise ValueError("base runtime report device profile binding is missing")
    if device_profile.get("profile_sha256") != profile_sha256:
        raise ValueError("base runtime report is bound to another device profile")
    if device_profile.get("source_sha256") != source_sha256:
        raise ValueError("base runtime report is bound to another source")
    task_gates = report.get("task_gates")
    if not isinstance(task_gates, dict):
        raise ValueError("base runtime report.task_gates must be an object")
    if "benchtop_stability" in task_gates:
        raise ValueError("base runtime report already contains benchtop_stability")
    task_gates["benchtop_stability"] = deepcopy(dict(gate))
    runtime = report.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError("base runtime report.runtime must be an object")
    runtime["benchtop_stability_protocol"] = {
        "release_height_m": RELEASE_HEIGHT_M,
        "warmup_frames": WARMUP_FRAMES,
        "settle_frames": SETTLE_FRAMES,
    }
    all_gates_pass = all(
        isinstance(value, Mapping) and value.get("status") == "pass"
        for value in task_gates.values()
    )
    report["status"] = (
        "pass"
        if runtime_report.get("status") == "pass" and all_gates_pass
        else "blocked"
    )
    report["benchtop_stability_claim_boundary"] = gate.get("claim_boundary")
    return report


def _load_profile(
    path: Path,
    *,
    source_sha256: str,
    asset_entry_prim: str,
) -> dict[str, Any]:
    profile = _json_object(path)
    if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ValueError("device profile schema_version is unsupported")
    if profile.get("source_sha256") != source_sha256:
        raise ValueError("device profile is not bound to manifest.source.sha256")
    if profile.get("asset_entry_prim") != asset_entry_prim:
        raise ValueError("device profile asset_entry_prim does not match manifest")
    if profile.get("articulation_root_prim") != asset_entry_prim:
        raise ValueError("device profile articulation_root_prim does not match manifest")
    gates = profile.get("required_runtime_task_gates")
    if not isinstance(gates, list) or "benchtop_stability" not in gates:
        raise ValueError("device profile does not require benchtop_stability")
    frames = profile.get("named_frames")
    support = frames.get("support") if isinstance(frames, dict) else None
    if (
        not isinstance(support, dict)
        or support.get("parent_prim") != asset_entry_prim
        or support.get("authoritative") is not True
        or support.get("rotation_parent_local_wxyz")
        != [1.0, 0.0, 0.0, 0.0]
    ):
        raise ValueError("device profile support frame is not authoritative root-local")
    _finite_vector(
        support.get("translation_parent_local_m"),
        3,
        "device profile support translation",
    )
    return profile


def _world_bound(
    stage: Any,
    prim_path: str,
    *,
    usd: Any,
    usd_geom: Any,
) -> tuple[list[float], list[float]]:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        raise RuntimeError(f"missing runtime prim: {prim_path}")
    cache = usd_geom.BBoxCache(
        usd.TimeCode.Default(),
        [usd_geom.Tokens.default_],
    )
    bound = cache.ComputeWorldBound(prim).ComputeAlignedBox()
    return (
        [float(value) for value in bound.GetMin()],
        [float(value) for value in bound.GetMax()],
    )


def _extent(bound: tuple[list[float], list[float]]) -> list[float]:
    return [
        bound[1][index] - bound[0][index]
        for index in range(3)
    ]


def _profile_support_world(
    stage: Any,
    profile: Mapping[str, Any],
    *,
    usd: Any,
    usd_geom: Any,
    gf: Any,
) -> list[float]:
    frame = profile["named_frames"]["support"]
    parent = stage.GetPrimAtPath(frame["parent_prim"])
    matrix = usd_geom.Xformable(parent).ComputeLocalToWorldTransform(
        usd.TimeCode.Default()
    )
    result = matrix.Transform(
        gf.Vec3d(*frame["translation_parent_local_m"])
    )
    return [float(value) for value in result]


def _pose(articulation: Any) -> dict[str, list[float]]:
    position, orientation = articulation.get_world_pose()
    return {
        "position_m": [float(value) for value in position],
        "orientation_wxyz": [float(value) for value in orientation],
    }


def _support_from_base_pose(
    pose: Mapping[str, Any],
    support_offset_base_local_m: list[float],
) -> list[float]:
    rotated = _quaternion_rotate(
        pose["orientation_wxyz"],
        support_offset_base_local_m,
    )
    return [
        float(pose["position_m"][index]) + rotated[index]
        for index in range(3)
    ]


def _run_worker(args: argparse.Namespace) -> dict[str, Any]:
    manifest = _json_object(args.manifest)
    source = manifest.get("source")
    entrypoints = manifest.get("entrypoints")
    if (
        not isinstance(source, dict)
        or not isinstance(source.get("sha256"), str)
        or not isinstance(entrypoints, dict)
        or not isinstance(entrypoints.get("asset_entry_prim"), str)
    ):
        raise ValueError("manifest source or asset entry prim is missing")
    entry_prim = entrypoints["asset_entry_prim"]
    profile = _load_profile(
        args.device_profile,
        source_sha256=source["sha256"],
        asset_entry_prim=entry_prim,
    )
    asset_path = args.package / "asset.usd"
    if not asset_path.is_file():
        raise FileNotFoundError(asset_path)
    asset_sha_before = _sha256_file(asset_path)

    # SimulationApp must precede omni and pxr imports in the Isaac worker.
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": True, "renderer": "RayTracedLighting"})
    try:
        import numpy as np
        import omni.usd
        from omni.isaac.core import World
        from omni.isaac.core.articulations import Articulation
        from pxr import Gf, Usd, UsdGeom, UsdPhysics

        context = omni.usd.get_context()
        if not context.open_stage(str(asset_path)):
            raise RuntimeError(f"could not open package: {asset_path}")
        while context.get_stage_loading_status()[2] > 0:
            app.update()
        for _ in range(30):
            app.update()
        stage = context.get_stage()
        if stage is None:
            raise RuntimeError("Isaac did not provide an open USD stage")
        stage.SetEditTarget(stage.GetSessionLayer())
        initial_support_world = _profile_support_world(
            stage,
            profile,
            usd=Usd,
            usd_geom=UsdGeom,
            gf=Gf,
        )
        table_top_z = initial_support_world[2] - float(args.release_height)
        table = UsdGeom.Cube.Define(
            stage,
            "/World/__aan_benchtop_probe/Table",
        )
        table.GetSizeAttr().Set(1.0)
        table_xform = UsdGeom.Xformable(table.GetPrim())
        table_xform.AddTranslateOp().Set(
            Gf.Vec3d(
                initial_support_world[0],
                initial_support_world[1],
                table_top_z - 0.025,
            )
        )
        table_xform.AddScaleOp().Set(Gf.Vec3d(1.5, 1.5, 0.05))
        UsdPhysics.CollisionAPI.Apply(table.GetPrim()).GetCollisionEnabledAttr().Set(
            True
        )

        world = World(
            stage_units_in_meters=1.0,
            physics_dt=float(args.physics_dt),
            rendering_dt=float(args.physics_dt),
        )
        articulation = Articulation(
            entry_prim,
            name="aan_benchtop_stability_articulation",
        )
        world.scene.add(articulation)
        reset_positions = [0.0] * len(profile["semantic_joints"])
        for semantic in profile["semantic_joints"].values():
            reset_positions[int(semantic["dof_index"])] = float(
                semantic["runtime_reset_value"]
            )
        articulation.set_joints_default_state(
            positions=np.asarray(reset_positions, dtype=np.float32)
        )
        world.reset()
        if not articulation.handles_initialized:
            raise RuntimeError("articulation handles did not initialize")
        initial_pose = _pose(articulation)
        initial_bound = _world_bound(
            stage,
            entry_prim,
            usd=Usd,
            usd_geom=UsdGeom,
        )
        support_delta_world = [
            initial_support_world[index] - initial_pose["position_m"][index]
            for index in range(3)
        ]
        support_offset_base = _quaternion_inverse_rotate(
            initial_pose["orientation_wxyz"],
            support_delta_world,
        )
        for _ in range(int(args.warmup_frames)):
            world.step(render=False)
        warmup_pose = _pose(articulation)
        warmup_bound = _world_bound(
            stage,
            entry_prim,
            usd=Usd,
            usd_geom=UsdGeom,
        )
        for _ in range(int(args.settle_frames)):
            world.step(render=False)
        final_pose = _pose(articulation)
        final_bound = _world_bound(
            stage,
            entry_prim,
            usd=Usd,
            usd_geom=UsdGeom,
        )
        final_support = _support_from_base_pose(
            final_pose,
            support_offset_base,
        )
        asset_sha_after = _sha256_file(asset_path)
        return {
            "schema_version": "aan.articulated_benchtop_observation.v1",
            "status": "pass",
            "runtime_profile": "isaac41",
            "physics_dt_seconds": float(args.physics_dt),
            "asset_entry_prim": entry_prim,
            "release_height_m": float(args.release_height),
            "warmup_frames": int(args.warmup_frames),
            "settle_frames": int(args.settle_frames),
            "table_top_z_m": table_top_z,
            "initial_root_pose": initial_pose,
            "warmup_root_pose": warmup_pose,
            "final_root_pose": final_pose,
            "initial_extent_m": _extent(initial_bound),
            "warmup_extent_m": _extent(warmup_bound),
            "final_extent_m": _extent(final_bound),
            "initial_support_world_m": initial_support_world,
            "final_support_world_m": final_support,
            "support_offset_base_local_m": support_offset_base,
            "source_integrity": {
                "status": (
                    "pass"
                    if asset_sha_before == asset_sha_after
                    else "blocked"
                ),
                "asset_usd_sha256_before": asset_sha_before,
                "asset_usd_sha256_after": asset_sha_after,
                "manifest_sha256": _sha256_file(args.manifest),
                "device_profile_sha256": _sha256_file(args.device_profile),
            },
        }
    finally:
        # Isaac 4.1 may terminate before evidence is persisted when app.close()
        # is called. This worker is process-scoped and exits immediately.
        pass


def _worker_command(
    args: argparse.Namespace,
    observation_path: Path,
) -> list[str]:
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--package",
        str(args.package),
        "--manifest",
        str(args.manifest),
        "--device-profile",
        str(args.device_profile),
        "--release-height",
        str(args.release_height),
        "--warmup-frames",
        str(args.warmup_frames),
        "--settle-frames",
        str(args.settle_frames),
        "--physics-dt",
        str(args.physics_dt),
        "--worker-observation",
        str(observation_path),
    ]


def _orchestrate(args: argparse.Namespace) -> dict[str, Any]:
    manifest = _json_object(args.manifest)
    source = manifest.get("source")
    entrypoints = manifest.get("entrypoints")
    if (
        not isinstance(source, dict)
        or not isinstance(source.get("sha256"), str)
        or not isinstance(entrypoints, dict)
        or not isinstance(entrypoints.get("asset_entry_prim"), str)
    ):
        raise ValueError("manifest source or asset entry prim is missing")
    profile = _load_profile(
        args.device_profile,
        source_sha256=source["sha256"],
        asset_entry_prim=entrypoints["asset_entry_prim"],
    )
    profile_sha = _sha256_file(args.device_profile)
    base_report = _json_object(args.base_runtime_report)
    for path in (args.out_observation, args.stderr_log, args.out_report):
        if path.exists() or path.is_symlink():
            raise FileExistsError(
                f"refusing to replace qualification evidence: {path}"
            )
    args.out_observation.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.run(
        _worker_command(args, args.out_observation),
        check=False,
        capture_output=True,
        text=True,
    )
    _write_text(args.stderr_log, process.stderr)
    if not args.out_observation.is_file():
        raise RuntimeError(
            "Isaac worker did not persist an observation; "
            f"exit_code={process.returncode}"
        )
    observation = _json_object(args.out_observation)
    if observation.get("status") != "pass":
        gate = {
            "status": "blocked",
            "method": "Isaac 4.1 benchtop worker",
            "host_failure": observation.get("host_failure"),
            "worker_exit_code": process.returncode,
            "blocked_reasons": ["worker_failure"],
            "claim_boundary": (
                "No benchtop stability claim is available because the Isaac "
                "worker did not complete."
            ),
        }
    else:
        errors = _scoped_physx_error_lines(
            process.stderr,
            entrypoints["asset_entry_prim"],
        )
        gate = _evaluate_stability_observation(
            observation,
            scoped_physx_errors=errors,
        )
        gate["worker_exit_code"] = process.returncode
    merged = _merge_stability_gate(
        base_report,
        gate=gate,
        profile_sha256=profile_sha,
        source_sha256=source["sha256"],
    )
    _write_json(args.out_report, merged)
    return {
        "status": merged["status"],
        "runtime_report": str(args.out_report),
        "runtime_report_sha256": _sha256_file(args.out_report),
        "observation": str(args.out_observation),
        "stderr_log": str(args.stderr_log),
        "benchtop_stability": gate,
        "profile_id": profile.get("profile_id"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run and hash-bind an Isaac 4.1 articulated benchtop stability gate."
        )
    )
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--device-profile", type=Path, required=True)
    parser.add_argument("--base-runtime-report", type=Path)
    parser.add_argument("--out-report", type=Path)
    parser.add_argument("--out-observation", type=Path)
    parser.add_argument("--stderr-log", type=Path)
    parser.add_argument("--release-height", type=float, default=RELEASE_HEIGHT_M)
    parser.add_argument("--warmup-frames", type=int, default=WARMUP_FRAMES)
    parser.add_argument("--settle-frames", type=int, default=SETTLE_FRAMES)
    parser.add_argument(
        "--physics-dt",
        type=float,
        default=DEFAULT_PHYSICS_DT_SECONDS,
    )
    parser.add_argument(
        "--worker-observation",
        type=Path,
        help=argparse.SUPPRESS,
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.package = args.package.resolve()
    args.manifest = args.manifest.resolve()
    args.device_profile = args.device_profile.resolve()
    if args.worker_observation is not None:
        output = args.worker_observation.resolve()
        try:
            observation = _run_worker(args)
        except Exception as exc:
            observation = {
                "schema_version": "aan.articulated_benchtop_observation.v1",
                "status": "blocked",
                "runtime_profile": "isaac41",
                "host_failure": f"{type(exc).__name__}: {exc}",
            }
        _write_json(output, observation)
        print(
            json.dumps(
                {"status": observation["status"], "observation": str(output)},
                sort_keys=True,
            ),
            flush=True,
        )
        return 0 if observation["status"] == "pass" else 2

    if (
        args.base_runtime_report is None
        or args.out_report is None
        or args.out_observation is None
        or args.stderr_log is None
    ):
        raise SystemExit(
            "--base-runtime-report, --out-report, --out-observation, and "
            "--stderr-log are required"
        )
    args.base_runtime_report = args.base_runtime_report.resolve()
    args.out_report = args.out_report.resolve()
    args.out_observation = args.out_observation.resolve()
    args.stderr_log = args.stderr_log.resolve()
    if (
        args.release_height != RELEASE_HEIGHT_M
        or args.warmup_frames != WARMUP_FRAMES
        or args.settle_frames != SETTLE_FRAMES
    ):
        raise SystemExit(
            "qualification protocol is fixed at 10 mm, 50 warmup frames, "
            "and 240 settle frames"
        )
    if args.physics_dt <= 0.0:
        raise SystemExit("--physics-dt must be positive")
    try:
        result = _orchestrate(args)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": f"{type(exc).__name__}: {exc}",
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
