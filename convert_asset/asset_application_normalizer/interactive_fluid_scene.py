"""Contracts for source-bound PhysX PBD interactive fluid scene packages.

This module is intentionally simulator-free.  Isaac Sim authoring and runtime
qualification live in scripts; the admission layer only validates the portable
producer profile and its package-local evidence bindings.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


SCHEMA_VERSION = "aan.interactive_fluid_scene_profile.v1"
_ALLOWED_COMPOSITION = {
    "visual_static_environment",
    "static_support",
    "robot_config_injection",
}


class InteractiveFluidSceneProfileError(ValueError):
    """Raised when an interactive fluid scene profile is not admissible."""


@dataclass(frozen=True)
class InteractiveFluidSceneProfile:
    path: Path
    profile_id: str
    component_root_prim: str
    particle_count: int
    points_path: Path
    points_sha256: str
    entrypoint_hz: dict[str, int]
    collision_meshes: tuple[str, ...]
    allowed_consumer_composition: tuple[str, ...]
    payload: Mapping[str, Any]


def load_interactive_fluid_scene_profile(
    profile_path: str | Path,
) -> InteractiveFluidSceneProfile:
    path = Path(profile_path).resolve()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InteractiveFluidSceneProfileError("cannot read fluid profile") from exc
    data = _mapping(raw, "profile")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise InteractiveFluidSceneProfileError("unsupported fluid profile schema")
    profile_id = _string(data.get("profile_id"), "profile_id")
    if data.get("runtime_profile") != "isaac41":
        raise InteractiveFluidSceneProfileError("runtime_profile must be isaac41")
    root = _prim_path(data.get("component_root_prim"), "component_root_prim")

    members = _mapping(data.get("members"), "members")
    if set(members) != {
        "source_container",
        "target_container",
        "particle_system",
        "particles",
    }:
        raise InteractiveFluidSceneProfileError("fluid member set mismatch")
    for name, value in members.items():
        member = _prim_path(value, f"members.{name}")
        if not (member == root or member.startswith(root + "/")):
            raise InteractiveFluidSceneProfileError(f"members.{name} is outside component root")

    particles = _mapping(data.get("particles"), "particles")
    if particles.get("kind") != "PhysX_PBD":
        raise InteractiveFluidSceneProfileError("particles.kind must be PhysX_PBD")
    count = particles.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise InteractiveFluidSceneProfileError("particle count must be positive")
    points_rel = _relative_path(
        particles.get("authored_points_path"), "particles.authored_points_path"
    )
    points_path = path.parent / points_rel
    try:
        points = json.loads(points_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InteractiveFluidSceneProfileError("cannot read authored particle points") from exc
    if not isinstance(points, list) or len(points) != count:
        raise InteractiveFluidSceneProfileError("particle count does not match authored points")
    for index, point in enumerate(points):
        if (
            not isinstance(point, list)
            or len(point) != 3
            or any(not _finite_number(value) for value in point)
        ):
            raise InteractiveFluidSceneProfileError(
                f"authored particle point {index} must be a finite xyz vector"
            )
    points_digest = sha256(points_path.read_bytes()).hexdigest()
    expected_digest = particles.get("authored_points_sha256")
    if expected_digest != "AUTO" and expected_digest != points_digest:
        raise InteractiveFluidSceneProfileError("authored particle points hash mismatch")
    if particles.get("display") != "physx_isosurface":
        raise InteractiveFluidSceneProfileError("only physx_isosurface display is supported")

    collision = _mapping(data.get("container_collision"), "container_collision")
    if collision.get("strategy") != "visual_mesh_convex_decomposition":
        raise InteractiveFluidSceneProfileError("unsupported container collision strategy")
    raw_meshes = collision.get("meshes")
    if not isinstance(raw_meshes, list) or not raw_meshes:
        raise InteractiveFluidSceneProfileError("container collision meshes must not be empty")
    collision_meshes: list[str] = []
    for index, raw_mesh in enumerate(raw_meshes):
        mesh = _mapping(raw_mesh, f"container_collision.meshes[{index}]")
        prim = _prim_path(mesh.get("prim_path"), f"container_collision.meshes[{index}].prim_path")
        if not prim.startswith(root + "/"):
            raise InteractiveFluidSceneProfileError("collision mesh is outside component root")
        if mesh.get("approximation") != "convexDecomposition":
            raise InteractiveFluidSceneProfileError("collision approximation must be convexDecomposition")
        error = mesh.get("error_percentage")
        if not _finite_number(error) or not 0.01 <= float(error) <= 25.0:
            raise InteractiveFluidSceneProfileError(
                "convex decomposition error_percentage must be in [0.01, 25]"
            )
        collision_meshes.append(prim)

    entrypoints = _mapping(data.get("entrypoints"), "entrypoints")
    if not entrypoints:
        raise InteractiveFluidSceneProfileError("entrypoints must not be empty")
    entrypoint_hz: dict[str, int] = {}
    for name, raw_entrypoint in entrypoints.items():
        if not isinstance(name, str) or not name:
            raise InteractiveFluidSceneProfileError("entrypoint names must be non-empty")
        entrypoint = _mapping(raw_entrypoint, f"entrypoints.{name}")
        _relative_path(entrypoint.get("path"), f"entrypoints.{name}.path")
        rate = entrypoint.get("physics_hz")
        if not isinstance(rate, int) or isinstance(rate, bool) or rate <= 0:
            raise InteractiveFluidSceneProfileError("entrypoint physics_hz must be positive")
        entrypoint_hz[name] = rate

    allowed = data.get("allowed_consumer_composition")
    if not isinstance(allowed, list) or not allowed:
        raise InteractiveFluidSceneProfileError("allowed consumer composition must not be empty")
    if any(item not in _ALLOWED_COMPOSITION for item in allowed):
        raise InteractiveFluidSceneProfileError("unsupported consumer composition capability")

    qualification = _mapping(data.get("qualification"), "qualification")
    retention = qualification.get("minimum_source_retention_ratio")
    peak = qualification.get("minimum_peak_target_ratio")
    if not _ratio(retention) or not _ratio(peak):
        raise InteractiveFluidSceneProfileError("qualification ratios must be in [0, 1]")
    performance = _mapping(qualification.get("performance"), "qualification.performance")
    for field in ("width", "height", "required_repeats"):
        if not isinstance(performance.get(field), int) or performance[field] <= 0:
            raise InteractiveFluidSceneProfileError(f"performance.{field} must be positive")
    if not _finite_number(performance.get("minimum_rtx_fps")):
        raise InteractiveFluidSceneProfileError("performance.minimum_rtx_fps must be finite")

    return InteractiveFluidSceneProfile(
        path=path,
        profile_id=profile_id,
        component_root_prim=root,
        particle_count=count,
        points_path=points_path,
        points_sha256=points_digest,
        entrypoint_hz=entrypoint_hz,
        collision_meshes=tuple(collision_meshes),
        allowed_consumer_composition=tuple(str(item) for item in allowed),
        payload=dict(data),
    )


def classify_interactive_fluid_runtime_log(log_text: str) -> dict[str, Any]:
    """Classify hard runtime blockers without manufacturing positive evidence.

    Passing the full fluid qualification needs particle trajectories, timings,
    and screenshots from the dedicated worker.  A text log can only establish
    a hard negative (or that no hard negative was observed).
    """
    gpu_convex_failure = any(
        marker in log_text
        for marker in (
            "failed to cook GPU-compatible mesh",
            "Non-GPU-compatible convex mesh is not able to collide with particle system",
        )
    )
    invalid_error = "Invalid volume error percentage" in log_text
    blocked: list[str] = []
    if gpu_convex_failure:
        blocked.append("gpu_incompatible_visual_mesh_convex_decomposition")
    if invalid_error:
        blocked.append("invalid_convex_decomposition_error_percentage")
    return {
        "schema_version": "aan.interactive_fluid_scene_runtime_observation.v1",
        "overall_status": "blocked" if blocked else "incomplete",
        "blocked_reasons": blocked,
        "gates": {
            "visual_mesh_convex_cooking": {
                "status": "blocked" if gpu_convex_failure else "not_observed",
                "required": "GPU-compatible convex decomposition for PhysX PBD contacts",
            },
            "convex_parameter_validity": {
                "status": "blocked" if invalid_error else "not_observed",
            },
            "static_hold_8s": {"status": "not_qualified"},
            "kinematic_oracle_transfer": {"status": "not_qualified"},
            "rtx_960x540_fps": {"status": "not_qualified"},
        },
        "claim_boundary": (
            "negative runtime observation only; no static-hold, transfer, FPS, "
            "robot, policy, or benchmark pass is inferred"
        ),
    }


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InteractiveFluidSceneProfileError(f"{field} must be a mapping")
    return value


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise InteractiveFluidSceneProfileError(f"{field} must be a non-empty string")
    return value


def _prim_path(value: object, field: str) -> str:
    text = _string(value, field)
    if not text.startswith("/") or "//" in text or text.endswith("/"):
        raise InteractiveFluidSceneProfileError(f"{field} must be an absolute USD prim path")
    return text


def _relative_path(value: object, field: str) -> str:
    text = _string(value, field)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts:
        raise InteractiveFluidSceneProfileError(f"{field} must be package-relative")
    return text


def _finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _ratio(value: object) -> bool:
    return _finite_number(value) and 0.0 <= float(value) <= 1.0
