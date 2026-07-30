#!/usr/bin/env python3
"""Promote an already-qualified articulated AAN package without changing USD."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Mapping
import uuid

if __package__:
    from .articulated_mounting_contract import validate_mounting
else:
    from articulated_mounting_contract import validate_mounting

PROFILE_SCHEMA_VERSION = "aan.articulated_device_profile.v1"
CONTRACT_SCHEMA_VERSION = "aan.articulation_contract.v1"
REPORT_SCHEMA_VERSION = "aan.articulation_runtime_qualification.v1"
PROMOTION_SCHEMA_VERSION = "aan.articulation_package_promotion.v1"
PROFILE_RELATIVE_PATH = "articulation/device_profile.json"
REPORT_RELATIVE_PATH = "evidence/articulation_runtime_qualification/report.json"
PROMOTION_RELATIVE_PATH = "evidence/articulation_runtime_qualification/promotion.json"


class ArticulatedPackageFinalizationError(ValueError):
    """Raised when a producer handoff cannot be promoted safely."""


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _reject_nonstandard_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def _load_json_object_bytes(value: bytes, label: str) -> dict[str, Any]:
    try:
        decoded = json.loads(
            value.decode("utf-8"),
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ArticulatedPackageFinalizationError(f"{label} is not valid JSON") from exc
    if not isinstance(decoded, dict):
        raise ArticulatedPackageFinalizationError(f"{label} must be a JSON object")
    return decoded


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        return _load_json_object_bytes(path.read_bytes(), label)
    except OSError as exc:
        raise ArticulatedPackageFinalizationError(
            f"{label} is not readable: {path}"
        ) from exc


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ArticulatedPackageFinalizationError(f"{label} must be an object")
    return value


def _mapping_list(value: object, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ArticulatedPackageFinalizationError(f"{label} must be a list of objects")
    return value


def _required_string(value: Mapping[str, Any], key: str, label: str) -> str:
    candidate = value.get(key)
    if not isinstance(candidate, str) or not candidate:
        raise ArticulatedPackageFinalizationError(f"{label}.{key} must be a non-empty string")
    return candidate


def _require_exact_fields(
    value: Mapping[str, Any],
    expected: set[str],
    label: str,
) -> None:
    actual = set(value)
    if actual != expected:
        missing = ", ".join(sorted(expected - actual))
        extra = ", ".join(sorted(actual - expected))
        details = []
        if missing:
            details.append(f"missing: {missing}")
        if extra:
            details.append(f"unexpected: {extra}")
        raise ArticulatedPackageFinalizationError(
            f"{label} fields do not match the producer ABI ({'; '.join(details)})"
        )


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ArticulatedPackageFinalizationError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ArticulatedPackageFinalizationError(f"{label} must be a finite number")
    return result


def _number_list(value: object, length: int, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ArticulatedPackageFinalizationError(
            f"{label} must be a list of {length} finite numbers"
        )
    return [_finite_number(item, f"{label}[{index}]") for index, item in enumerate(value)]


def _is_within(path: str, root: str, *, allow_root: bool) -> bool:
    if path == root:
        return allow_root
    return path.startswith(root.rstrip("/") + "/")


def _require_prim_within(
    path: str,
    root: str,
    label: str,
    *,
    allow_root: bool,
) -> None:
    if not path.startswith("/") or "//" in path or not _is_within(
        path,
        root,
        allow_root=allow_root,
    ):
        raise ArticulatedPackageFinalizationError(f"{label} must be within {root}")


def _validate_mounting(
    value: object,
    *,
    articulation_root: str,
    runtime_reset_by_index: Mapping[int, float],
) -> dict[str, Any]:
    try:
        return validate_mounting(
            value,
            asset_entry_prim=articulation_root,
            expected_resets_by_index=runtime_reset_by_index,
        )
    except ValueError as exc:
        raise ArticulatedPackageFinalizationError(
            f"device profile.mounting is invalid: {exc}"
        ) from exc


def _validate_controllable_joint_records(
    closure: Mapping[str, Any],
    articulation_root: str,
) -> tuple[dict[str, Mapping[str, Any]], dict[str, float], dict[str, tuple[float, float]]]:
    joints_by_prim: dict[str, Mapping[str, Any]] = {}
    reset_by_joint: dict[str, float] = {}
    limits_by_joint: dict[str, tuple[float, float]] = {}
    for index, joint in enumerate(
        _mapping_list(closure.get("joints"), "manifest.articulation_closure.joints")
    ):
        label = f"manifest.articulation_closure.joints[{index}]"
        joint_prim = _required_string(joint, "prim_path", label)
        _require_prim_within(
            joint_prim,
            articulation_root,
            f"{label}.prim_path",
            allow_root=False,
        )
        if joint_prim in joints_by_prim:
            raise ArticulatedPackageFinalizationError(
                "manifest.articulation_closure.joints prim paths must be unique"
            )
        joints_by_prim[joint_prim] = joint
        if joint.get("joint_type") not in {
            "PhysicsPrismaticJoint",
            "PhysicsRevoluteJoint",
        }:
            continue
        axis = _mapping(joint.get("axis"), f"{label}.axis")
        if axis.get("status") != "pass":
            raise ArticulatedPackageFinalizationError(f"{label}.axis.status must be pass")
        _required_string(axis, "value", f"{label}.axis")
        limits = _mapping(joint.get("limits"), f"{label}.limits")
        if limits.get("status") != "pass":
            raise ArticulatedPackageFinalizationError(
                f"{label}.limits.status must be pass"
            )
        lower = _mapping(limits.get("lower"), f"{label}.limits.lower")
        upper = _mapping(limits.get("upper"), f"{label}.limits.upper")
        if lower.get("status") != "pass" or upper.get("status") != "pass":
            raise ArticulatedPackageFinalizationError(
                f"{label}.limits bounds must both pass"
            )
        lower_value = _finite_number(lower.get("value"), f"{label}.limits.lower.value")
        upper_value = _finite_number(upper.get("value"), f"{label}.limits.upper.value")
        if lower_value >= upper_value:
            raise ArticulatedPackageFinalizationError(
                f"{label}.limits must have lower.value < upper.value"
            )
        enabled = _mapping(joint.get("enabled"), f"{label}.enabled")
        if enabled.get("status") != "pass" or enabled.get("value") is not True:
            raise ArticulatedPackageFinalizationError(
                f"{label}.enabled must be a passing true value"
            )
        reset = _mapping(joint.get("reset_value"), f"{label}.reset_value")
        if reset.get("status") != "pass":
            raise ArticulatedPackageFinalizationError(
                f"{label}.reset_value.status must be pass"
            )
        reset_value = _finite_number(reset.get("value"), f"{label}.reset_value.value")
        if not lower_value <= reset_value <= upper_value:
            raise ArticulatedPackageFinalizationError(
                f"{label}.reset_value must be within joint limits"
            )
        reset_by_joint[joint_prim] = reset_value
        limits_by_joint[joint_prim] = (lower_value, upper_value)
    return joints_by_prim, reset_by_joint, limits_by_joint


def _validate_manifest(
    package_root: Path,
    manifest_path: Path,
) -> tuple[
    dict[str, Any],
    str,
    str,
    str,
    dict[int, Mapping[str, Any]],
    dict[str, float],
    dict[str, tuple[float, float]],
]:
    if not package_root.is_dir():
        raise ArticulatedPackageFinalizationError(
            f"package root does not exist: {package_root}"
        )
    if not manifest_path.is_file():
        raise ArticulatedPackageFinalizationError(
            f"manifest does not exist: {manifest_path}"
        )
    embedded_manifest = package_root / "evidence" / "manifest.json"
    if not embedded_manifest.is_file():
        raise ArticulatedPackageFinalizationError(
            "package evidence/manifest.json does not exist"
        )
    manifest_bytes = manifest_path.read_bytes()
    if embedded_manifest.read_bytes() != manifest_bytes:
        raise ArticulatedPackageFinalizationError(
            "external and embedded manifests must be byte-identical before promotion"
        )
    manifest = _load_json_object_bytes(manifest_bytes, "manifest")
    if manifest.get("schema_version") != "asset_application_normalizer.v1":
        raise ArticulatedPackageFinalizationError(
            "manifest.schema_version must be asset_application_normalizer.v1"
        )
    if manifest.get("overall_status") != "pass":
        raise ArticulatedPackageFinalizationError("manifest.overall_status must be pass")
    if "articulation_contract" in manifest:
        raise ArticulatedPackageFinalizationError(
            "package already contains articulation_contract; refusing to replace it"
        )
    asset_path = package_root / "asset.usd"
    if not asset_path.is_file():
        raise ArticulatedPackageFinalizationError("package asset.usd does not exist")
    source = _mapping(manifest.get("source"), "manifest.source")
    source_sha = _required_string(source, "sha256", "manifest.source")
    entrypoints = _mapping(manifest.get("entrypoints"), "manifest.entrypoints")
    asset_entry_prim = _required_string(
        entrypoints,
        "asset_entry_prim",
        "manifest.entrypoints",
    )
    closure = _mapping(manifest.get("articulation_closure"), "manifest.articulation_closure")
    if closure.get("status") != "pass":
        raise ArticulatedPackageFinalizationError(
            "manifest.articulation_closure.status must be pass"
        )
    roots = _mapping_list(
        closure.get("articulation_roots"),
        "manifest.articulation_closure.articulation_roots",
    )
    if len(roots) != 1:
        raise ArticulatedPackageFinalizationError(
            "manifest.articulation_closure must have exactly one articulation root"
        )
    articulation_root = _required_string(
        roots[0],
        "prim_path",
        "manifest.articulation_closure.articulation_roots[0]",
    )
    if articulation_root != asset_entry_prim:
        raise ArticulatedPackageFinalizationError(
            "articulation root must match manifest asset_entry_prim"
        )
    scope = _mapping(closure.get("scope"), "manifest.articulation_closure.scope")
    if scope.get("asset_scope_prims") != [articulation_root]:
        raise ArticulatedPackageFinalizationError(
            "manifest.articulation_closure.scope.asset_scope_prims must match the articulation root"
        )
    joints_by_prim, joint_reset_by_prim, joint_limits_by_prim = (
        _validate_controllable_joint_records(
        closure,
        articulation_root,
        )
    )
    mapping_by_index: dict[int, Mapping[str, Any]] = {}
    mapped_joint_prims: set[str] = set()
    for index, item in enumerate(
        _mapping_list(closure.get("dof_mapping"), "manifest.articulation_closure.dof_mapping")
    ):
        label = f"manifest.articulation_closure.dof_mapping[{index}]"
        dof_index = item.get("dof_index")
        if isinstance(dof_index, bool) or not isinstance(dof_index, int) or dof_index < 0:
            raise ArticulatedPackageFinalizationError(
                f"{label}.dof_index must be a non-negative integer"
            )
        if dof_index in mapping_by_index:
            raise ArticulatedPackageFinalizationError(
                "manifest.articulation_closure.dof_mapping indices must be unique"
            )
        joint_prim = _required_string(item, "joint_prim", label)
        if joint_prim in mapped_joint_prims:
            raise ArticulatedPackageFinalizationError(
                "manifest.articulation_closure.dof_mapping joint_prim values must be unique"
            )
        _require_prim_within(
            joint_prim,
            articulation_root,
            f"{label}.joint_prim",
            allow_root=False,
        )
        joint = joints_by_prim.get(joint_prim)
        if joint is None or joint_prim not in joint_reset_by_prim:
            raise ArticulatedPackageFinalizationError(
                f"{label}.joint_prim must identify a controllable joint record"
            )
        if item.get("joint_type") != joint.get("joint_type"):
            raise ArticulatedPackageFinalizationError(
                f"{label}.joint_type must match manifest.articulation_closure.joints"
            )
        axis = _mapping(joint.get("axis"), f"{label}.joint axis")
        if item.get("axis") != axis.get("value"):
            raise ArticulatedPackageFinalizationError(
                f"{label}.axis must match manifest.articulation_closure.joints"
            )
        mapped_joint_prims.add(joint_prim)
        mapping_by_index[dof_index] = item
    if not mapping_by_index or sorted(mapping_by_index) != list(range(len(mapping_by_index))):
        raise ArticulatedPackageFinalizationError(
            "manifest.articulation_closure.dof_mapping must be contiguous from 0"
        )
    mapping_by_joint = {
        str(item["joint_prim"]): item for item in mapping_by_index.values()
    }
    reset_by_joint: dict[str, float] = {}
    for index, item in enumerate(
        _mapping_list(closure.get("reset_values"), "manifest.articulation_closure.reset_values")
    ):
        label = f"manifest.articulation_closure.reset_values[{index}]"
        joint_prim = _required_string(item, "joint_prim", label)
        if joint_prim in reset_by_joint:
            raise ArticulatedPackageFinalizationError(
                "manifest.articulation_closure.reset_values joint paths must be unique"
            )
        mapping = mapping_by_joint.get(joint_prim)
        if mapping is not None and item.get("joint_type") != mapping.get("joint_type"):
            raise ArticulatedPackageFinalizationError(
                f"{label}.joint_type must match manifest.articulation_closure.dof_mapping"
            )
        reset = _mapping(item.get("reset_value"), f"{label}.reset_value")
        if reset.get("status") != "pass":
            raise ArticulatedPackageFinalizationError(f"{label}.reset_value.status must be pass")
        reset_value = _finite_number(
            reset.get("value"),
            f"{label}.reset_value.value",
        )
        if mapping is not None and reset_value != joint_reset_by_prim[joint_prim]:
            raise ArticulatedPackageFinalizationError(
                f"{label}.reset_value must match manifest.articulation_closure.joints"
            )
        reset_by_joint[joint_prim] = reset_value
    mapped_joints = set(mapping_by_joint)
    if set(reset_by_joint) != mapped_joints:
        raise ArticulatedPackageFinalizationError(
            "manifest.articulation_closure.reset_values must cover every mapped DOF"
        )
    summary = _mapping(closure.get("summary"), "manifest.articulation_closure.summary")
    if summary.get("articulation_root_count") != 1:
        raise ArticulatedPackageFinalizationError(
            "manifest.articulation_closure.summary.articulation_root_count must be 1"
        )
    if summary.get("joint_count") != len(joints_by_prim):
        raise ArticulatedPackageFinalizationError(
            "manifest.articulation_closure.summary.joint_count must match joints"
        )
    if summary.get("controllable_dof_count") != len(mapping_by_index):
        raise ArticulatedPackageFinalizationError(
            "manifest.articulation_closure.summary.controllable_dof_count must match DOFs"
        )
    return (
        manifest,
        _sha256_bytes(manifest_bytes),
        source_sha,
        articulation_root,
        mapping_by_index,
        reset_by_joint,
        joint_limits_by_prim,
    )


def _validate_profile(
    profile: Mapping[str, Any],
    *,
    source_sha: str,
    articulation_root: str,
    mapping_by_index: Mapping[int, Mapping[str, Any]],
    reset_by_joint: Mapping[str, float],
    joint_limits_by_prim: Mapping[str, tuple[float, float]],
) -> tuple[str, str, tuple[str, ...], dict[str, Any] | None]:
    profile_fields = {
        "schema_version",
        "profile_id",
        "revision",
        "source_sha256",
        "asset_entry_prim",
        "articulation_root_prim",
        "runtime_units",
        "semantic_joints",
        "named_frames",
        "required_runtime_task_gates",
    }
    if "mounting" in profile:
        profile_fields.add("mounting")
    _require_exact_fields(
        profile,
        profile_fields,
        "device profile",
    )
    if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ArticulatedPackageFinalizationError(
            "device profile schema_version is unsupported"
        )
    profile_id = _required_string(profile, "profile_id", "device profile")
    revision = _required_string(profile, "revision", "device profile")
    if _required_string(profile, "source_sha256", "device profile") != source_sha:
        raise ArticulatedPackageFinalizationError(
            "device profile source_sha256 does not match manifest.source.sha256"
        )
    for field_name in ("asset_entry_prim", "articulation_root_prim"):
        if _required_string(profile, field_name, "device profile") != articulation_root:
            raise ArticulatedPackageFinalizationError(
                f"device profile {field_name} does not match the articulation root"
            )
    runtime_units = _mapping(profile.get("runtime_units"), "device profile.runtime_units")
    if dict(runtime_units) != {"revolute": "radian", "prismatic": "meter"}:
        raise ArticulatedPackageFinalizationError(
            "device profile runtime_units must declare radians and meters"
        )
    required_gates_value = profile.get("required_runtime_task_gates")
    if (
        not isinstance(required_gates_value, list)
        or not required_gates_value
        or not all(isinstance(value, str) and value for value in required_gates_value)
        or len(set(required_gates_value)) != len(required_gates_value)
    ):
        raise ArticulatedPackageFinalizationError(
            "device profile required_runtime_task_gates must be a unique non-empty list"
        )
    requires_mounting = "benchtop_stability" in required_gates_value
    if requires_mounting != ("mounting" in profile):
        raise ArticulatedPackageFinalizationError(
            "device profile.mounting is required exactly when "
            "benchtop_stability is a required runtime task gate"
        )
    semantic_joints = _mapping(profile.get("semantic_joints"), "device profile.semantic_joints")
    seen_indices: set[int] = set()
    runtime_reset_by_index: dict[int, float] = {}
    for semantic_name, raw_semantic in semantic_joints.items():
        if (
            not isinstance(semantic_name, str)
            or not semantic_name
            or "." in semantic_name
        ):
            raise ArticulatedPackageFinalizationError(
                "device profile semantic joint names must be non-empty and contain no '.'"
            )
        label = f"device profile.semantic_joints.{semantic_name}"
        semantic = _mapping(raw_semantic, label)
        _require_exact_fields(
            semantic,
            {
                "joint_prim",
                "part_prim",
                "dof_index",
                "runtime_reset_value",
                "reset_state",
                "states",
            },
            label,
        )
        dof_index = semantic.get("dof_index")
        if isinstance(dof_index, bool) or not isinstance(dof_index, int):
            raise ArticulatedPackageFinalizationError(f"{label}.dof_index must be an integer")
        mapping = mapping_by_index.get(dof_index)
        if mapping is None or semantic.get("joint_prim") != mapping.get("joint_prim"):
            raise ArticulatedPackageFinalizationError(
                f"{label} does not match the static DOF mapping"
            )
        if dof_index in seen_indices:
            raise ArticulatedPackageFinalizationError(
                "device profile semantic joints must map each DOF once"
            )
        seen_indices.add(dof_index)
        part_prim = _required_string(semantic, "part_prim", label)
        _require_prim_within(part_prim, articulation_root, f"{label}.part_prim", allow_root=False)
        raw_reset = reset_by_joint[str(mapping["joint_prim"])]
        expected_reset = (
            math.radians(raw_reset)
            if mapping.get("joint_type") == "PhysicsRevoluteJoint"
            else raw_reset
        )
        raw_lower_limit, raw_upper_limit = joint_limits_by_prim[
            str(mapping["joint_prim"])
        ]
        runtime_lower_limit = (
            math.radians(raw_lower_limit)
            if mapping.get("joint_type") == "PhysicsRevoluteJoint"
            else raw_lower_limit
        )
        runtime_upper_limit = (
            math.radians(raw_upper_limit)
            if mapping.get("joint_type") == "PhysicsRevoluteJoint"
            else raw_upper_limit
        )
        runtime_reset = _finite_number(semantic.get("runtime_reset_value"), f"{label}.runtime_reset_value")
        if not math.isclose(runtime_reset, expected_reset, rel_tol=0.0, abs_tol=1.0e-6):
            raise ArticulatedPackageFinalizationError(
                f"{label}.runtime_reset_value does not match the static reset"
            )
        runtime_reset_by_index[dof_index] = runtime_reset
        states = _mapping(semantic.get("states"), f"{label}.states")
        if not states:
            raise ArticulatedPackageFinalizationError(f"{label}.states must not be empty")
        parsed_states: dict[str, list[float]] = {}
        for state_name, interval in states.items():
            if (
                not isinstance(state_name, str)
                or not state_name
                or "." in state_name
            ):
                raise ArticulatedPackageFinalizationError(
                    f"{label}.states must use non-empty names without '.'"
                )
            values = _number_list(interval, 2, f"{label}.states.{state_name}")
            if values[0] > values[1]:
                raise ArticulatedPackageFinalizationError(
                    f"{label}.states.{state_name} bounds are reversed"
                )
            if (
                values[0] < runtime_lower_limit - 1.0e-6
                or values[1] > runtime_upper_limit + 1.0e-6
            ):
                raise ArticulatedPackageFinalizationError(
                    f"{label}.states.{state_name} must remain within static joint limits"
                )
            parsed_states[state_name] = values
        reset_state = _required_string(semantic, "reset_state", label)
        if reset_state not in parsed_states or not (
            parsed_states[reset_state][0] <= runtime_reset <= parsed_states[reset_state][1]
        ):
            raise ArticulatedPackageFinalizationError(
                f"{label}.reset_state must contain runtime_reset_value"
            )
    if seen_indices != set(mapping_by_index):
        raise ArticulatedPackageFinalizationError(
            "device profile semantic joints must cover every static DOF"
        )
    frames = _mapping(profile.get("named_frames"), "device profile.named_frames")
    if not frames:
        raise ArticulatedPackageFinalizationError("device profile.named_frames must not be empty")
    for frame_name, raw_frame in frames.items():
        if (
            not isinstance(frame_name, str)
            or not frame_name
            or "." in frame_name
        ):
            raise ArticulatedPackageFinalizationError(
                "device profile named frame names must be non-empty and contain no '.'"
            )
        label = f"device profile.named_frames.{frame_name}"
        frame = _mapping(raw_frame, label)
        _require_exact_fields(
            frame,
            {
                "parent_prim",
                "translation_parent_local_m",
                "rotation_parent_local_wxyz",
                "authoritative",
            },
            label,
        )
        _require_prim_within(
            _required_string(frame, "parent_prim", label),
            articulation_root,
            f"{label}.parent_prim",
            allow_root=True,
        )
        _number_list(frame.get("translation_parent_local_m"), 3, f"{label}.translation_parent_local_m")
        rotation = _number_list(frame.get("rotation_parent_local_wxyz"), 4, f"{label}.rotation_parent_local_wxyz")
        if not math.isclose(sum(component * component for component in rotation), 1.0, rel_tol=0.0, abs_tol=1.0e-6):
            raise ArticulatedPackageFinalizationError(
                f"{label}.rotation_parent_local_wxyz must be a unit quaternion"
            )
        if frame.get("authoritative") is not True:
            raise ArticulatedPackageFinalizationError(f"{label}.authoritative must be true")
    mounting = (
        _validate_mounting(
            profile.get("mounting"),
            articulation_root=articulation_root,
            runtime_reset_by_index=runtime_reset_by_index,
        )
        if requires_mounting
        else None
    )
    return profile_id, revision, tuple(required_gates_value), mounting


def _validate_runtime_report(
    report: Mapping[str, Any],
    *,
    prequalification_manifest_sha256: str,
    asset_sha256: str,
    profile_sha256: str,
    source_sha256: str,
    asset_entry_prim: str,
    target_runtime_profile: str,
    mapping_by_index: Mapping[int, Mapping[str, Any]],
    required_gates: tuple[str, ...],
    mounting: Mapping[str, Any] | None,
) -> None:
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ArticulatedPackageFinalizationError("runtime report schema_version is unsupported")
    if report.get("status") != "pass":
        raise ArticulatedPackageFinalizationError("runtime report status must be pass")
    inputs = _mapping(report.get("inputs"), "runtime report.inputs")
    device_profile = _mapping(
        inputs.get("device_profile"),
        "runtime report.inputs.device_profile",
    )
    _require_exact_fields(
        device_profile,
        {"schema_version", "profile_sha256", "source_sha256"},
        "runtime report.inputs.device_profile",
    )
    if device_profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ArticulatedPackageFinalizationError(
            "runtime report.inputs.device_profile.schema_version is unsupported"
        )
    if (
        _required_string(
            device_profile,
            "profile_sha256",
            "runtime report.inputs.device_profile",
        )
        != profile_sha256
    ):
        raise ArticulatedPackageFinalizationError(
            "runtime report.inputs.device_profile.profile_sha256 does not match "
            "the promoted device profile"
        )
    if (
        _required_string(
            device_profile,
            "source_sha256",
            "runtime report.inputs.device_profile",
        )
        != source_sha256
    ):
        raise ArticulatedPackageFinalizationError(
            "runtime report.inputs.device_profile.source_sha256 does not match "
            "manifest.source.sha256"
        )
    integrity = _mapping(
        inputs.get("integrity"),
        "runtime report.inputs.integrity",
    )
    if integrity.get("status") != "pass":
        raise ArticulatedPackageFinalizationError(
            "runtime report input integrity status must be pass"
        )
    qualified_package = _mapping(
        inputs.get("qualified_package"),
        "runtime report.inputs.qualified_package",
    )
    _require_exact_fields(
        qualified_package,
        {
            "asset_path",
            "asset_entry_prim",
            "runtime_profile",
            "prequalification_manifest_sha256",
            "asset_usd_sha256_before",
            "asset_usd_sha256_after",
        },
        "runtime report.inputs.qualified_package",
    )
    if qualified_package.get("asset_path") != "asset.usd":
        raise ArticulatedPackageFinalizationError(
            "runtime report qualified package asset_path must be asset.usd"
        )
    if qualified_package.get("asset_entry_prim") != asset_entry_prim:
        raise ArticulatedPackageFinalizationError(
            "runtime report qualified package asset_entry_prim does not match the package"
        )
    if qualified_package.get("runtime_profile") != target_runtime_profile:
        raise ArticulatedPackageFinalizationError(
            "runtime report qualified package runtime_profile does not match the package"
        )
    if (
        qualified_package.get("prequalification_manifest_sha256")
        != prequalification_manifest_sha256
    ):
        raise ArticulatedPackageFinalizationError(
            "runtime report is not bound to the prequalification manifest SHA-256"
        )
    if (
        qualified_package.get("asset_usd_sha256_before") != asset_sha256
        or qualified_package.get("asset_usd_sha256_after") != asset_sha256
    ):
        raise ArticulatedPackageFinalizationError(
            "runtime report does not bind an unchanged package asset.usd SHA-256"
        )
    runtime = _mapping(report.get("runtime"), "runtime report.runtime")
    if runtime.get("runtime_profile") != target_runtime_profile:
        raise ArticulatedPackageFinalizationError(
            "runtime report runtime_profile does not match the package"
        )
    drive_integrity = _mapping(report.get("drive_integrity"), "runtime report.drive_integrity")
    if drive_integrity.get("status") != "pass":
        raise ArticulatedPackageFinalizationError(
            "runtime report drive_integrity status must be pass"
        )
    runtime_mapping = _mapping_list(
        report.get("runtime_dof_mapping"),
        "runtime report.runtime_dof_mapping",
    )
    runtime_by_index: dict[int, Mapping[str, Any]] = {}
    for index, item in enumerate(runtime_mapping):
        label = f"runtime report.runtime_dof_mapping[{index}]"
        _require_exact_fields(item, {"dof_index", "dof_name", "joint_prim"}, label)
        dof_index = item.get("dof_index")
        if isinstance(dof_index, bool) or not isinstance(dof_index, int) or dof_index in runtime_by_index:
            raise ArticulatedPackageFinalizationError(
                f"{label}.dof_index must be unique"
            )
        _required_string(item, "dof_name", label)
        expected = mapping_by_index.get(dof_index)
        if expected is None or item.get("joint_prim") != expected.get("joint_prim"):
            raise ArticulatedPackageFinalizationError(
                f"{label} does not match the static DOF mapping"
            )
        runtime_by_index[dof_index] = item
    if set(runtime_by_index) != set(mapping_by_index):
        raise ArticulatedPackageFinalizationError(
            "runtime report must cover every static DOF index"
        )
    task_gates = _mapping(report.get("task_gates"), "runtime report.task_gates")
    for gate_name in required_gates:
        gate = _mapping(task_gates.get(gate_name), f"runtime report.task_gates.{gate_name}")
        if gate.get("status") != "pass":
            raise ArticulatedPackageFinalizationError(
                f"runtime report.task_gates.{gate_name}.status must be pass"
            )
    if mounting is None:
        if "qualified_consumer_placement" in report:
            raise ArticulatedPackageFinalizationError(
                "runtime report.qualified_consumer_placement is valid only "
                "for a benchtop_stability mounting contract"
            )
    else:
        qualified_placement = _mapping(
            report.get("qualified_consumer_placement"),
            "runtime report.qualified_consumer_placement",
        )
        expected_placement = {
            **dict(mounting),
            "status": "pass",
            "profile_sha256": profile_sha256,
            "source_sha256": source_sha256,
        }
        if dict(qualified_placement) != expected_placement:
            raise ArticulatedPackageFinalizationError(
                "runtime report.qualified_consumer_placement must exactly "
                "match the hash-bound device profile mounting candidate"
            )


def _atomic_write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary_path.write_bytes(value)
    temporary_path.replace(path)


def _prepare_new_package_artifact(package_root: Path, path: Path) -> None:
    if path.exists() or path.is_symlink():
        raise ArticulatedPackageFinalizationError(
            f"refusing to replace an existing promotion artifact: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    resolved_parent = path.parent.resolve()
    if resolved_parent != package_root and package_root not in resolved_parent.parents:
        raise ArticulatedPackageFinalizationError(
            f"promotion artifact parent escapes package root: {path}"
        )


def _manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def finalize_articulated_package(
    *,
    package_root: Path,
    manifest_path: Path,
    profile_path: Path,
    runtime_report_path: Path,
) -> dict[str, Any]:
    """Bind a producer profile and a passing runtime report into one AAN package."""
    package_root = package_root.resolve()
    manifest_path = manifest_path.resolve()
    profile_path = profile_path.resolve()
    runtime_report_path = runtime_report_path.resolve()
    if not profile_path.is_file():
        raise ArticulatedPackageFinalizationError(
            f"device profile does not exist: {profile_path}"
        )
    if not runtime_report_path.is_file():
        raise ArticulatedPackageFinalizationError(
            f"runtime report does not exist: {runtime_report_path}"
        )
    (
        manifest,
        prequalification_manifest_sha256,
        source_sha,
        articulation_root,
        mapping_by_index,
        reset_by_joint,
        joint_limits_by_prim,
    ) = _validate_manifest(package_root, manifest_path)
    target = _mapping(manifest.get("target"), "manifest.target")
    target_runtime_profile = _required_string(
        target,
        "target_runtime_profile",
        "manifest.target",
    )
    try:
        profile_bytes = profile_path.read_bytes()
        report_bytes = runtime_report_path.read_bytes()
    except OSError as exc:
        raise ArticulatedPackageFinalizationError(
            "device profile or runtime report became unreadable during finalization"
        ) from exc
    profile = _load_json_object_bytes(profile_bytes, "device profile")
    report = _load_json_object_bytes(report_bytes, "runtime report")
    profile_sha256 = _sha256_bytes(profile_bytes)
    profile_id, revision, required_gates, mounting = _validate_profile(
        profile,
        source_sha=source_sha,
        articulation_root=articulation_root,
        mapping_by_index=mapping_by_index,
        reset_by_joint=reset_by_joint,
        joint_limits_by_prim=joint_limits_by_prim,
    )
    _validate_runtime_report(
        report,
        prequalification_manifest_sha256=prequalification_manifest_sha256,
        asset_sha256=_sha256_file(package_root / "asset.usd"),
        profile_sha256=profile_sha256,
        source_sha256=source_sha,
        asset_entry_prim=articulation_root,
        target_runtime_profile=target_runtime_profile,
        mapping_by_index=mapping_by_index,
        required_gates=required_gates,
        mounting=mounting,
    )
    package_profile_path = package_root / PROFILE_RELATIVE_PATH
    package_report_path = package_root / REPORT_RELATIVE_PATH
    report_digest_path = package_report_path.with_name("report.sha256.json")
    promotion_path = package_root / PROMOTION_RELATIVE_PATH
    for path in (
        package_profile_path,
        package_report_path,
        report_digest_path,
        promotion_path,
    ):
        _prepare_new_package_artifact(package_root, path)
    report_sha256 = _sha256_bytes(report_bytes)
    articulation_contract = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "status": "pass",
        "profile": {
            "schema_version": PROFILE_SCHEMA_VERSION,
            "profile_id": profile_id,
            "revision": revision,
            "source_sha256": source_sha,
            "profile_sha256": profile_sha256,
            "package_path": PROFILE_RELATIVE_PATH,
        },
        "runtime_qualification": {
            "status": "pass",
            "report_path": REPORT_RELATIVE_PATH,
            "report_sha256": report_sha256,
        },
    }
    if mounting is not None:
        articulation_contract["mounting"] = {
            **mounting,
            "status": "pass",
            "profile_sha256": profile_sha256,
            "runtime_report_sha256": report_sha256,
            "source_sha256": source_sha,
        }
    manifest["articulation_contract"] = articulation_contract
    final_manifest_bytes = _manifest_bytes(manifest)
    final_manifest_sha256 = _sha256_bytes(final_manifest_bytes)
    promotion = {
        "schema_version": PROMOTION_SCHEMA_VERSION,
        "status": "pass",
        "prequalification_manifest_sha256": prequalification_manifest_sha256,
        "final_manifest_sha256": final_manifest_sha256,
        "asset_usd_sha256": _sha256_file(package_root / "asset.usd"),
        "profile_path": PROFILE_RELATIVE_PATH,
        "profile_sha256": profile_sha256,
        "runtime_report_path": REPORT_RELATIVE_PATH,
        "runtime_report_sha256": report_sha256,
        "claim_boundary": (
            "This promotion binds a producer profile and runtime report without "
            "changing the package USD, physics, drives, or colliders."
        ),
    }
    report_digest = {
        "report": package_report_path.name,
        "report_sha256": report_sha256,
    }
    _atomic_write(package_profile_path, profile_bytes)
    _atomic_write(package_report_path, report_bytes)
    _atomic_write(
        report_digest_path,
        (json.dumps(report_digest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    _atomic_write(manifest_path, final_manifest_bytes)
    _atomic_write(package_root / "evidence" / "manifest.json", final_manifest_bytes)
    _atomic_write(
        promotion_path,
        (json.dumps(promotion, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return {
        "status": "pass",
        "package_root": str(package_root),
        "prequalification_manifest_sha256": prequalification_manifest_sha256,
        "final_manifest_sha256": final_manifest_sha256,
        "profile_sha256": profile_sha256,
        "runtime_report_sha256": report_sha256,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Promote a verified articulated ConvertAsset package."
    )
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--runtime-report", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = finalize_articulated_package(
            package_root=args.package_root,
            manifest_path=args.manifest,
            profile_path=args.profile,
            runtime_report_path=args.runtime_report,
        )
    except ArticulatedPackageFinalizationError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
