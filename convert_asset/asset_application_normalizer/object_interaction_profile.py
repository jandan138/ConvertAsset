"""Source-bound object interaction profile admission.

The profile deliberately does not contain mass or inertia.  It describes the
runtime identity of one manipulable object: its rigid root, collision prims,
open-top intent, and authoritative body-local frames.  Mass remains owned by
``aan.physics_profile.v1`` and is resolved only after this contract is applied.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .grasp_cross_section import resolve_grasp_cross_section_config
from .stage_metrics import METRIC_FIELDS, metrics_match, read_stage_metrics


PROFILE_SCHEMA_VERSION = "aan.object_interaction_profile.v1"
REQUIRED_NAMED_FRAMES = {"opening", "grasp", "support"}
COLLIDER_MODES = {"preserve", "author", "disable"}
COLLIDER_PURPOSES = {"gripper", "support", "containment"}
MOTION_ROLES = {"dynamic", "kinematic"}
AUTHORABLE_COLLIDER_TYPES = {
    "Capsule",
    "Cone",
    "Cube",
    "Cylinder",
    "Mesh",
    "Plane",
    "Sphere",
}
COLLISION_APPROXIMATIONS = {
    "none",
    "convexHull",
    "convexDecomposition",
    "meshSimplification",
    "boundingCube",
    "boundingSphere",
    "sdf",
}


@dataclass(frozen=True)
class ObjectInteractionProfileResolution:
    """Immutable profile bytes plus a fully validated authoring plan."""

    status: str
    profile_admission: dict[str, Any]
    resolved: dict[str, Any] | None
    blockers: list[dict[str, Any]]
    profile_bytes: bytes | None


def load_and_resolve_interaction_profile(
    profile_path: Path,
    source_usd: Path,
    package_stage: Any,
    scope_prims: list[str],
) -> ObjectInteractionProfileResolution:
    """Parse and bind one object interaction profile without mutating USD."""
    profile_bytes: bytes | None = None
    profile: dict[str, Any] | None = None
    parse_error: str | None = None
    try:
        profile_bytes = profile_path.read_bytes()
        raw = json.loads(profile_bytes.decode("utf-8"))
        profile = raw if isinstance(raw, dict) else None
        if profile is None:
            parse_error = "profile JSON root must be an object"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        parse_error = str(exc)

    source_sha = _sha256_file(source_usd) if source_usd.is_file() else None
    profile_sha = (
        hashlib.sha256(profile_bytes).hexdigest() if profile_bytes is not None else None
    )
    admission: dict[str, Any] = {
        "status": "blocked",
        "schema_version": profile.get("schema_version") if profile else None,
        "profile_path": str(profile_path),
        "profile_sha256": profile_sha,
        "profile_id": profile.get("profile_id") if profile else None,
        "revision": profile.get("revision") if profile else None,
        "source_sha256": source_sha,
        "asset_entry_prim": profile.get("asset_entry_prim") if profile else None,
        "errors": [],
    }
    if profile is None:
        admission["errors"].append(f"profile could not be parsed: {parse_error}")
        return _blocked(admission, profile_bytes)

    errors: list[str] = admission["errors"]
    if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        errors.append(
            f"unsupported interaction profile schema: {profile.get('schema_version')!r}"
        )
    for field in ("profile_id", "revision"):
        if not isinstance(profile.get(field), str) or not profile[field].strip():
            errors.append(f"{field} must be a non-empty string")

    _validate_source_binding(
        profile.get("source_binding"), source_usd, source_sha, errors
    )

    asset_entry_prim = profile.get("asset_entry_prim")
    if not isinstance(asset_entry_prim, str) or not asset_entry_prim.startswith("/"):
        errors.append("asset_entry_prim must be an absolute USD prim path")
        asset_entry_prim = None
    elif not scope_prims or asset_entry_prim != scope_prims[0]:
        errors.append(
            "asset_entry_prim must equal the first declared package asset scope"
        )
    elif not _valid_prim(package_stage.GetPrimAtPath(asset_entry_prim)):
        errors.append("asset_entry_prim does not exist in the package stage")

    rigid_root = profile.get("rigid_root")
    if not isinstance(rigid_root, dict):
        errors.append("rigid_root must be an object")
        rigid_root = {}
    if rigid_root.get("motion_role") not in MOTION_ROLES:
        errors.append(f"rigid_root.motion_role must be one of {sorted(MOTION_ROLES)}")
    if rigid_root.get("disable_descendant_rigid_bodies") is not True:
        errors.append("rigid_root.disable_descendant_rigid_bodies must be true for v1")
    if rigid_root.get("remove_descendant_mass_api") is not True:
        errors.append("rigid_root.remove_descendant_mass_api must be true for v1")

    source_rigid_bodies: list[str] = []
    descendant_mass_prims: list[str] = []
    source_collision_prims: list[str] = []
    if asset_entry_prim is not None:
        source_rigid_bodies = _active_schema_paths(
            package_stage,
            asset_entry_prim,
            "PhysicsRigidBodyAPI",
            "physics:rigidBodyEnabled",
        )
        descendant_mass_prims = [
            path
            for path in _schema_paths(package_stage, asset_entry_prim, "PhysicsMassAPI")
            if path != asset_entry_prim
        ]
        source_collision_prims = _active_schema_paths(
            package_stage,
            asset_entry_prim,
            "PhysicsCollisionAPI",
            "physics:collisionEnabled",
        )

    colliders = _resolve_colliders(
        profile.get("colliders"),
        package_stage,
        asset_entry_prim,
        source_collision_prims,
        errors,
    )
    frames = _resolve_named_frames(
        profile.get("named_frames"), asset_entry_prim, package_stage, errors
    )
    open_top = _resolve_open_top(profile.get("open_top"), frames, errors)
    grasp_cross_section = resolve_grasp_cross_section_config(
        profile.get("grasp_cross_section"),
        named_frames=frames,
        open_top=open_top,
        errors=errors,
    )
    runtime_gates = _resolve_runtime_gates(profile.get("runtime_gates"), errors)

    if errors:
        return _blocked(admission, profile_bytes)

    admission.update(
        {
            "status": "pass",
            "source_binding": profile["source_binding"],
            "source_active_rigid_bodies": source_rigid_bodies,
            "source_descendant_mass_prims": descendant_mass_prims,
            "resolved_collider_count": len(colliders),
            "resolved_named_frames": sorted(frames),
            "grasp_cross_section_required": grasp_cross_section is not None,
        }
    )
    return ObjectInteractionProfileResolution(
        status="pass",
        profile_admission=admission,
        resolved={
            "profile_id": profile["profile_id"],
            "revision": profile["revision"],
            "asset_entry_prim": asset_entry_prim,
            "motion_role": rigid_root["motion_role"],
            "source_rigid_bodies": source_rigid_bodies,
            "descendant_mass_prims": descendant_mass_prims,
            "colliders": colliders,
            "named_frames": frames,
            "open_top": open_top,
            "grasp_cross_section": grasp_cross_section,
            "runtime_gates": runtime_gates,
        },
        blockers=[],
        profile_bytes=profile_bytes,
    )


def _validate_source_binding(
    binding: Any,
    source_usd: Path,
    source_sha: str | None,
    errors: list[str],
) -> None:
    if not isinstance(binding, dict):
        errors.append("source_binding must be an object")
        return
    if binding.get("sha256") != source_sha:
        errors.append("source_binding.sha256 does not match the input USD")
    source_metrics = read_stage_metrics(source_usd)
    expected_metrics = binding.get("stage_metrics")
    if source_metrics is None or not isinstance(expected_metrics, dict):
        errors.append("source_binding.stage_metrics could not be verified")
        return
    metric_ok, _ = metrics_match(source_metrics, expected_metrics, fields=METRIC_FIELDS)
    if not metric_ok:
        errors.append("source_binding.stage_metrics does not match the input USD")


def _resolve_colliders(
    raw_colliders: Any,
    stage: Any,
    root: str | None,
    source_collision_prims: list[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(raw_colliders, list) or not raw_colliders:
        errors.append("colliders must be a non-empty list")
        return []
    resolved: list[dict[str, Any]] = []
    paths: list[str] = []
    for index, collider in enumerate(raw_colliders):
        if not isinstance(collider, dict):
            errors.append(f"colliders[{index}] must be an object")
            continue
        relative = collider.get("relative_path")
        if not _valid_relative_path(relative):
            errors.append(
                f"colliders[{index}].relative_path must be a safe root-relative prim path"
            )
            continue
        prim_path = _join_prim_path(root, relative)
        prim = stage.GetPrimAtPath(prim_path) if prim_path else None
        mode = collider.get("mode")
        if mode not in COLLIDER_MODES:
            errors.append(
                f"colliders[{index}].mode must be one of {sorted(COLLIDER_MODES)}"
            )
        geometry = _resolve_authored_geometry(
            collider.get("geometry"),
            index=index,
            errors=errors,
        )
        if collider.get("geometry") is not None and mode != "author":
            errors.append(
                f"colliders[{index}].geometry is only valid when mode is author"
            )
        prim_exists = _valid_prim(prim)
        tokens = _schema_tokens(prim) if prim_exists else set()
        if mode in {"preserve", "disable"} and not prim_exists:
            errors.append(f"colliders[{index}] target does not exist: {prim_path}")
        if mode in {"preserve", "disable"} and "PhysicsCollisionAPI" not in tokens:
            errors.append(
                f"colliders[{index}] {mode} target has no PhysicsCollisionAPI"
            )
        if mode == "author" and prim_exists and geometry is not None:
            errors.append(
                f"colliders[{index}] package geometry target already exists in source composition"
            )
        if mode == "author" and not prim_exists and geometry is None:
            errors.append(
                f"colliders[{index}] missing author target requires a geometry object"
            )
        if (
            mode == "author"
            and not prim_exists
            and not str(relative).startswith("__aan_collision_proxy/")
        ):
            errors.append(
                f"colliders[{index}] package geometry must use __aan_collision_proxy/"
            )
        if mode == "author" and prim_exists and str(prim.GetTypeName()) not in AUTHORABLE_COLLIDER_TYPES:
            errors.append(
                f"colliders[{index}] author target type {prim.GetTypeName()!r} is not a supported geometry prim"
            )
        purpose = collider.get("purpose")
        valid_purpose = (
            isinstance(purpose, list)
            and all(item in COLLIDER_PURPOSES for item in purpose)
            and len(set(purpose)) == len(purpose)
            and ((mode == "disable" and not purpose) or (mode != "disable" and bool(purpose)))
        )
        if not valid_purpose:
            errors.append(
                f"colliders[{index}].purpose must be empty for disable or a non-empty unique subset of {sorted(COLLIDER_PURPOSES)}"
            )
        approximation = collider.get("approximation")
        if mode == "disable" and approximation is not None:
            errors.append(f"colliders[{index}] disable cannot request an approximation")
        if approximation is not None:
            if approximation not in COLLISION_APPROXIMATIONS:
                errors.append(
                    f"colliders[{index}].approximation must be one of {sorted(COLLISION_APPROXIMATIONS)}"
                )
            if not prim_exists or str(prim.GetTypeName()) != "Mesh":
                errors.append(
                    f"colliders[{index}].approximation may only target a Mesh prim"
                )
        paths.append(str(prim_path))
        resolved.append(
            {
                "prim_path": str(prim_path),
                "relative_path": relative,
                "mode": mode,
                "purpose": sorted(purpose) if isinstance(purpose, list) else [],
                "approximation": approximation,
                "geometry": geometry,
            }
        )
    if len(paths) != len(set(paths)):
        errors.append("colliders must not target the same prim more than once")
    undeclared = sorted(set(source_collision_prims) - set(paths))
    if undeclared:
        errors.append(
            "colliders must cover every active source collision prim under asset_entry_prim: "
            + ", ".join(undeclared)
        )
    return sorted(resolved, key=lambda item: item["prim_path"])


def _resolve_authored_geometry(
    raw: Any,
    *,
    index: int,
    errors: list[str],
) -> dict[str, Any] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        errors.append(f"colliders[{index}].geometry must be an object")
        return None
    if set(raw) != {
        "type",
        "size",
        "translation_body_local_usd",
        "rotation_body_local_wxyz",
        "scale_body_local_usd",
    }:
        errors.append(
            f"colliders[{index}].geometry must contain exactly type, size, translation, rotation, and scale"
        )
    if raw.get("type") != "Cube":
        errors.append(f"colliders[{index}].geometry.type must be Cube")
    if not _positive_finite(raw.get("size")):
        errors.append(f"colliders[{index}].geometry.size must be positive and finite")
    translation = raw.get("translation_body_local_usd")
    rotation = raw.get("rotation_body_local_wxyz")
    scale = raw.get("scale_body_local_usd")
    if not _finite_vector(translation, 3):
        errors.append(
            f"colliders[{index}].geometry.translation_body_local_usd must be finite vec3"
        )
    if not _unit_quaternion(rotation):
        errors.append(
            f"colliders[{index}].geometry.rotation_body_local_wxyz must be a unit quaternion"
        )
    if not _finite_vector(scale, 3) or any(float(item) <= 0.0 for item in scale):
        errors.append(
            f"colliders[{index}].geometry.scale_body_local_usd must be positive finite vec3"
        )
    return {
        "type": raw.get("type"),
        "size": float(raw.get("size", 0.0)),
        "translation_body_local_usd": list(translation)
        if isinstance(translation, list)
        else translation,
        "rotation_body_local_wxyz": list(rotation)
        if isinstance(rotation, list)
        else rotation,
        "scale_body_local_usd": list(scale) if isinstance(scale, list) else scale,
    }


def _resolve_named_frames(
    raw_frames: Any,
    root: str | None,
    stage: Any,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    if not isinstance(raw_frames, dict) or set(raw_frames) != REQUIRED_NAMED_FRAMES:
        errors.append(
            "named_frames must contain exactly the authoritative opening, grasp, and support frames"
        )
        return {}
    frames: dict[str, dict[str, Any]] = {}
    for name in sorted(REQUIRED_NAMED_FRAMES):
        raw = raw_frames[name]
        if not isinstance(raw, dict):
            errors.append(f"named_frames.{name} must be an object")
            continue
        translation = raw.get("translation_body_local_usd")
        rotation = raw.get("rotation_body_local_wxyz")
        if not _finite_vector(translation, 3):
            errors.append(
                f"named_frames.{name}.translation_body_local_usd must be finite vec3"
            )
        if not _unit_quaternion(rotation):
            errors.append(
                f"named_frames.{name}.rotation_body_local_wxyz must be a unit quaternion"
            )
        prim_path = f"{root}/__aan_frame_{name}" if root else None
        if prim_path and _valid_prim(stage.GetPrimAtPath(prim_path)):
            errors.append(
                f"reserved named-frame prim already exists in source composition: {prim_path}"
            )
        frames[name] = {
            "prim_path": prim_path,
            "translation_body_local_usd": list(translation)
            if isinstance(translation, list)
            else translation,
            "rotation_body_local_wxyz": list(rotation)
            if isinstance(rotation, list)
            else rotation,
        }
    return frames


def _resolve_open_top(
    raw: Any,
    frames: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, Any]:
    if not isinstance(raw, dict) or not isinstance(raw.get("required"), bool):
        errors.append("open_top must be an object with boolean required")
        return {}
    required = bool(raw["required"])
    axis = raw.get("axis_body_local")
    aperture_frame = raw.get("aperture_frame")
    evidence = raw.get("evidence")
    if required:
        if not _unit_vector(axis, 3):
            errors.append("open_top.axis_body_local must be a finite unit vec3")
        if aperture_frame not in frames:
            errors.append(
                "open_top.aperture_frame must name an authoritative named frame"
            )
        if not isinstance(evidence, dict):
            errors.append("open_top.evidence must be an object")
        else:
            if evidence.get("status") != "declared":
                errors.append(
                    "open_top.evidence.status must be declared before runtime probing"
                )
            for field in ("method", "claim_boundary"):
                if (
                    not isinstance(evidence.get(field), str)
                    or not evidence[field].strip()
                ):
                    errors.append(
                        f"open_top.evidence.{field} must be a non-empty string"
                    )
    return {
        "required": required,
        "axis_body_local": list(axis) if isinstance(axis, list) else axis,
        "aperture_frame": aperture_frame,
        "status": "declared" if required else "not_applicable",
        "evidence": evidence if isinstance(evidence, dict) else {},
    }


def _resolve_runtime_gates(raw: Any, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict):
        errors.append("runtime_gates must be an object")
        return {}
    required_keys = {"root_motion", "stable_support", "gripper_collision"}
    if set(raw) != required_keys:
        errors.append(
            "runtime_gates must contain exactly root_motion, stable_support, and gripper_collision"
        )
    resolved: dict[str, dict[str, Any]] = {}
    for name in sorted(required_keys):
        gate = raw.get(name)
        if not isinstance(gate, dict) or not isinstance(gate.get("required"), bool):
            errors.append(f"runtime_gates.{name}.required must be boolean")
            continue
        normalized = {"required": bool(gate["required"])}
        if name == "root_motion":
            threshold = gate.get("min_translation_m")
            if not _positive_finite(threshold):
                errors.append(
                    "runtime_gates.root_motion.min_translation_m must be positive and finite"
                )
            else:
                normalized["min_translation_m"] = float(threshold)
        resolved[name] = normalized
    return resolved


def _schema_paths(stage: Any, root: str, schema: str) -> list[str]:
    prefix = root.rstrip("/") + "/"
    paths = []
    for prim in _all_prims(stage):
        path = prim.GetPath().pathString
        if path != root and not path.startswith(prefix):
            continue
        if schema in _schema_tokens(prim):
            paths.append(path)
    return sorted(paths)


def _active_schema_paths(
    stage: Any, root: str, schema: str, enabled_attr: str
) -> list[str]:
    paths = []
    for path in _schema_paths(stage, root, schema):
        prim = stage.GetPrimAtPath(path)
        attr = prim.GetAttribute(enabled_attr)
        try:
            if attr and attr.Get() is False:
                continue
        except Exception:
            pass
        paths.append(path)
    return paths


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
        op = prim.GetMetadata("apiSchemas")
        if hasattr(op, "GetAppliedItems"):
            tokens.update(str(item) for item in op.GetAppliedItems())
    except Exception:
        pass
    return tokens


def _valid_prim(prim: Any) -> bool:
    try:
        return bool(prim and prim.IsValid())
    except Exception:
        return False


def _valid_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or value.startswith("/"):
        return False
    return all(part not in {"", ".", ".."} for part in value.split("/"))


def _join_prim_path(root: str | None, relative: str) -> str | None:
    return f"{root.rstrip('/')}/{relative}" if root else None


def _finite_vector(value: Any, length: int) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        return False
    try:
        return all(math.isfinite(float(item)) for item in value)
    except (TypeError, ValueError):
        return False


def _unit_vector(value: Any, length: int) -> bool:
    if not _finite_vector(value, length):
        return False
    norm = math.sqrt(sum(float(item) ** 2 for item in value))
    return math.isclose(norm, 1.0, rel_tol=1.0e-5, abs_tol=1.0e-5)


def _unit_quaternion(value: Any) -> bool:
    return _unit_vector(value, 4)


def _positive_finite(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0.0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _blocked(
    admission: dict[str, Any], profile_bytes: bytes | None
) -> ObjectInteractionProfileResolution:
    admission["status"] = "blocked"
    blocker = {
        "blocker_id": "aan05i_block_interaction_profile",
        "severity": "blocking",
        "summary": "Object interaction profile admission did not establish a complete runtime identity.",
        "detail": list(admission.get("errors", [])),
        "required_resolution": (
            "Provide a source-bound v1 interaction profile with one asset root, complete collider "
            "coverage, and authoritative opening/grasp/support frames."
        ),
    }
    return ObjectInteractionProfileResolution(
        status="blocked",
        profile_admission=admission,
        resolved=None,
        blockers=[blocker],
        profile_bytes=profile_bytes,
    )
