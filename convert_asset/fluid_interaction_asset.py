"""Portable contracts for source-bound fluid-interaction asset packages.

Geometry inspection, USD authoring, and Isaac Sim qualification deliberately
live in :mod:`convert_asset.fluid_interaction_runtime`.  This module contains
only versioned proposal/profile validation and deterministic policy helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path
from typing import Any, Mapping

import yaml


PROPOSAL_SCHEMA = "aan.fluid_interaction_proposal.v1"
PROFILE_SCHEMA = "aan.fluid_interaction_asset_profile.v1"
BEHAVIORS = frozenset({"reservoir", "conduit", "surface_guide"})
ROLE_APPROXIMATIONS = {
    "wall": "sdf",
    "rim": "sdf",
    "neck": "sdf",
    "guide_surface": "sdf",
    "partition_wall": "convexHull",
    "bottom": "convexHull",
    "base": "convexHull",
    "connector": "convexHull",
    "spout": "convexHull",
    "ignore": "none",
}


class FluidInteractionError(ValueError):
    """Raised when a fluid-interaction handoff is incomplete or overclaimed."""


@dataclass(frozen=True)
class ApprovedFluidInteractionProposal:
    path: Path
    payload: Mapping[str, Any]
    source_usd: Path
    source_sha256: str
    scope_prim: str
    behavior: str
    minimum_clearance_radius_m: float


def file_sha256(path: Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def normalized_collision_presets(minimum_clearance_radius_m: float) -> list[dict[str, Any]]:
    """Return the bounded r10.3-derived SDF ladder for one measured throat.

    The Task02 values remain upper bounds.  Smaller vessels scale offsets and
    SDF bands down so an admitted throat cannot be consumed by a 10 mm margin.
    """

    radius = float(minimum_clearance_radius_m)
    if not math.isfinite(radius) or radius <= 0:
        raise FluidInteractionError("minimum clearance radius must be positive")
    # Keep at least eighty percent of a measured narrow throat available.  The
    # earlier 20/12/20 percent bands exactly consumed the 7.46 mm funnel bore
    # once the 5.94 mm Task02 particle width was included.
    narrow_factor = 0.10 if radius < 0.006 else 0.20
    contact = min(0.005, narrow_factor * radius)
    rest = min(0.003, (0.05 if radius < 0.006 else 0.12) * radius)
    margin = min(0.010, narrow_factor * radius)
    return [
        {
            "id": name,
            "sdf_resolution": resolution,
            "sdf_subgrid_resolution": 6,
            "sdf_margin_m": round(margin, 7),
            "sdf_narrow_band_m": round(margin, 7),
            "sdf_bits_per_subgrid_pixel": "BitsPerPixel16",
            "sdf_enable_remeshing": False,
            "contact_offset_m": round(contact, 7),
            "rest_offset_m": round(rest, 7),
        }
        for name, resolution in (("low", 128), ("medium", 256), ("high", 512))
    ]


def qualification_policy(behavior: str) -> dict[str, Any]:
    if behavior not in BEHAVIORS:
        raise FluidInteractionError(f"unsupported fluid behavior: {behavior}")
    common: dict[str, Any] = {
        "runtime": "isaac41",
        "required_cold_runs": 3,
        "maximum_structural_leak_count": 0,
        "hard_physx_cuda_error_count": 0,
        "robot_policy_success": False,
        "benchmark_success": False,
    }
    if behavior == "reservoir":
        common.update(
            {
                "canonical_fill_ratio": 0.40,
                "minimum_static_retention_ratio": 0.99,
                "minimum_motion_retention_ratio": 0.95,
                "minimum_pour_outflow_ratio": 0.50,
                "pour_angle_deg": 110.0,
                "pour_hold_seconds": 4.0,
            }
        )
    elif behavior == "conduit":
        common.update(
            {
                "minimum_legal_outlet_ratio": 0.90,
                "maximum_structural_leak_count": 0,
            }
        )
    else:
        common.update(
            {
                "minimum_receiver_capture_ratio": 0.80,
                "minimum_capture_improvement_ratio": 0.20,
                "comparison": "paired_with_guide_vs_without_guide",
                "failure_disposition": "not_applicable",
            }
        )
    return common


def evaluate_qualification_runs(
    behavior: str, runs: list[Mapping[str, Any]]
) -> dict[str, Any]:
    """Aggregate three process-isolated observations without simulator imports."""

    policy = qualification_policy(behavior)
    blocked: list[str] = []
    if len(runs) != int(policy["required_cold_runs"]):
        blocked.append("required_cold_runs_missing")
    if any(item.get("hard_errors") for item in runs):
        blocked.append("hard_runtime_errors")
    if any(int(item.get("structural_leak_count", 0)) != 0 for item in runs):
        blocked.append("structural_leak_detected")
    if behavior == "reservoir":
        if any(
            float(item.get("static_retention_ratio", 0.0))
            < float(policy["minimum_static_retention_ratio"])
            for item in runs
        ):
            blocked.append("static_retention_below_threshold")
        if any(
            float(item.get("motion_retention_ratio", 0.0))
            < float(policy["minimum_motion_retention_ratio"])
            for item in runs
        ):
            blocked.append("motion_retention_below_threshold")
        if any(
            float(item.get("pour_outflow_ratio", 0.0))
            < float(policy["minimum_pour_outflow_ratio"])
            for item in runs
        ):
            blocked.append("pour_outflow_below_threshold")
    elif behavior == "conduit":
        if any(
            float(item.get("legal_outlet_ratio", 0.0))
            < float(policy["minimum_legal_outlet_ratio"])
            for item in runs
        ):
            blocked.append("legal_outlet_ratio_below_threshold")
    else:
        if any(
            float(item.get("capture_ratio", 0.0))
            < float(policy["minimum_receiver_capture_ratio"])
            or float(item.get("capture_ratio", 0.0))
            - float(item.get("baseline_capture_ratio", 0.0))
            < float(policy["minimum_capture_improvement_ratio"])
            for item in runs
        ):
            blocked.append("surface_guide_effect_not_established")
    status = "pass" if not blocked else "blocked"
    if behavior == "surface_guide" and blocked == [
        "surface_guide_effect_not_established"
    ]:
        status = "not_applicable"
    return {
        "schema_version": "aan.fluid_interaction_qualification_report.v1",
        "behavior": behavior,
        "overall_status": status,
        "blocked_reasons": blocked,
        "policy": policy,
        "runs": [dict(item) for item in runs],
    }


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FluidInteractionError(f"{label} must be a mapping")
    return value


def _absolute_prim(value: object, label: str) -> str:
    path = str(value)
    if not path.startswith("/") or path == "/" or "//" in path:
        raise FluidInteractionError(f"{label} must be an absolute USD prim path")
    return path


def load_approved_proposal(path: Path) -> ApprovedFluidInteractionProposal:
    proposal_path = Path(path).resolve()
    try:
        raw = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise FluidInteractionError(f"cannot read proposal: {proposal_path}") from error
    payload = _mapping(raw, "proposal")
    if payload.get("schema_version") != PROPOSAL_SCHEMA:
        raise FluidInteractionError("unsupported fluid interaction proposal schema")
    review = _mapping(payload.get("review"), "review")
    if review.get("status") != "approved" or not str(review.get("reviewer", "")).strip():
        raise FluidInteractionError("proposal review must be approved by a named reviewer")
    behavior_record = _mapping(payload.get("behavior"), "behavior")
    behavior = str(behavior_record.get("confirmed", ""))
    if behavior not in BEHAVIORS:
        raise FluidInteractionError("proposal must confirm one supported behavior")
    source = _mapping(payload.get("source_binding"), "source_binding")
    source_usd = Path(str(source.get("source_usd", ""))).resolve()
    if not source_usd.is_file():
        raise FluidInteractionError(f"proposal source USD does not exist: {source_usd}")
    expected_sha = str(source.get("source_sha256", ""))
    actual_sha = file_sha256(source_usd)
    if expected_sha not in {"AUTO", actual_sha}:
        raise FluidInteractionError("proposal source USD SHA-256 does not match")
    geometry = _mapping(payload.get("geometry"), "geometry")
    radius = float(geometry.get("minimum_clearance_radius_m", 0.0))
    normalized_collision_presets(radius)
    roles = geometry.get("roles")
    if not isinstance(roles, list) or not roles:
        raise FluidInteractionError("proposal geometry roles must not be empty")
    for index, role_record in enumerate(roles):
        role = _mapping(role_record, f"geometry.roles[{index}]")
        _absolute_prim(role.get("prim_path"), f"geometry.roles[{index}].prim_path")
        role_name = str(role.get("role", ""))
        if role_name not in ROLE_APPROXIMATIONS:
            raise FluidInteractionError(f"unsupported geometry role: {role_name}")
        expected = ROLE_APPROXIMATIONS[role_name]
        if role.get("approximation") != expected:
            raise FluidInteractionError(
                f"geometry role {role_name} must use approximation {expected}"
            )
    return ApprovedFluidInteractionProposal(
        path=proposal_path,
        payload=payload,
        source_usd=source_usd,
        source_sha256=actual_sha,
        scope_prim=_absolute_prim(source.get("scope_prim"), "source_binding.scope_prim"),
        behavior=behavior,
        minimum_clearance_radius_m=radius,
    )
