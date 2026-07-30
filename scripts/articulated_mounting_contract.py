"""Pure validation helpers for the articulated mounting JSON contract."""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping


MOUNTING_SCHEMA_VERSION = "aan.articulated_mounting.v1"
COORDINATE_SEMANTICS = {
    "stage_up_axis": "Z",
    "linear_units": "meter",
    "quaternion_order": "wxyz",
    "support_frame": "runtime_articulation_root_pose_local",
    "mount_pose": (
        "support_plane_to_runtime_articulation_root_pose_"
        "world_axes_at_yaw_zero"
    ),
    "qualified_extents": (
        "world_axis_aligned_at_mount_pose_after_joint_reset"
    ),
}
MOUNTING_FIELDS = {
    "schema_version",
    "motion_mode",
    "asset_entry_prim",
    "coordinate_semantics",
    "support_frame_root_local",
    "support_plane_to_root_mount_pose",
    "initial_joint_reset_positions",
    "qualified_reset_geometry",
    "verification_required",
}


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _exact_fields(
    value: Mapping[str, Any],
    expected: set[str],
    label: str,
) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} fields do not match the mounting ABI")


def _finite_vector(value: object, length: int, label: str) -> list[float]:
    if (
        not isinstance(value, list)
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


def validate_mounting(
    value: object,
    *,
    asset_entry_prim: str,
    expected_resets_by_index: Mapping[int, float] | None = None,
) -> dict[str, Any]:
    """Validate and copy one ``aan.articulated_mounting.v1`` mapping."""
    mounting = deepcopy(dict(_mapping(value, "mounting")))
    _exact_fields(mounting, MOUNTING_FIELDS, "mounting")
    if (
        mounting.get("schema_version") != MOUNTING_SCHEMA_VERSION
        or mounting.get("motion_mode") != "fixed_base"
        or mounting.get("asset_entry_prim") != asset_entry_prim
        or mounting.get("verification_required") != "benchtop_stability"
    ):
        raise ValueError("mounting metadata is invalid")
    semantics = _mapping(
        mounting.get("coordinate_semantics"),
        "mounting.coordinate_semantics",
    )
    if dict(semantics) != COORDINATE_SEMANTICS:
        raise ValueError("mounting coordinate semantics are invalid")

    for field in (
        "support_frame_root_local",
        "support_plane_to_root_mount_pose",
    ):
        pose = _mapping(mounting.get(field), f"mounting.{field}")
        _exact_fields(
            pose,
            {"translation_m", "rotation_wxyz"},
            f"mounting.{field}",
        )
        _finite_vector(
            pose.get("translation_m"),
            3,
            f"mounting.{field}.translation_m",
        )
        quaternion = _finite_vector(
            pose.get("rotation_wxyz"),
            4,
            f"mounting.{field}.rotation_wxyz",
        )
        if not math.isclose(
            sum(component * component for component in quaternion),
            1.0,
            rel_tol=0.0,
            abs_tol=1.0e-6,
        ):
            raise ValueError(f"mounting.{field}.rotation_wxyz must be unit length")

    resets = mounting.get("initial_joint_reset_positions")
    if not isinstance(resets, list) or not resets:
        raise ValueError("mounting reset positions must be a non-empty list")
    reset_by_index: dict[int, float] = {}
    for record in resets:
        record = _mapping(record, "mounting reset position")
        _exact_fields(
            record,
            {"dof_index", "position"},
            "mounting reset position",
        )
        index = record.get("dof_index")
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            or index in reset_by_index
        ):
            raise ValueError("mounting reset DOF indices must be unique")
        reset_by_index[index] = _finite_vector(
            [record.get("position")],
            1,
            "mounting reset position",
        )[0]
    if sorted(reset_by_index) != list(range(len(reset_by_index))):
        raise ValueError("mounting reset DOF indices must be contiguous")
    if expected_resets_by_index is not None:
        expected = {
            int(index): float(position)
            for index, position in expected_resets_by_index.items()
        }
        if set(reset_by_index) != set(expected) or any(
            not math.isclose(
                reset_by_index[index],
                expected[index],
                rel_tol=0.0,
                abs_tol=1.0e-6,
            )
            for index in expected
        ):
            raise ValueError("mounting reset positions do not match semantic joints")

    geometry = _mapping(
        mounting.get("qualified_reset_geometry"),
        "mounting.qualified_reset_geometry",
    )
    _exact_fields(
        geometry,
        {
            "warmup_frames",
            "warmup_extent_world_aabb_m",
            "settle_frames",
            "final_extent_world_aabb_m",
        },
        "mounting.qualified_reset_geometry",
    )
    for field in ("warmup_frames", "settle_frames"):
        frames = geometry.get(field)
        if isinstance(frames, bool) or not isinstance(frames, int) or frames <= 0:
            raise ValueError(f"mounting {field} must be a positive integer")
    for field in (
        "warmup_extent_world_aabb_m",
        "final_extent_world_aabb_m",
    ):
        if any(
            component <= 0.0
            for component in _finite_vector(
                geometry.get(field),
                3,
                f"mounting {field}",
            )
        ):
            raise ValueError(f"mounting {field} must be positive")
    return mounting
