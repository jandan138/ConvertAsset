"""Strict AAN-05 physics admission, provenance, and source-family audits."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .model import MILESTONE_AAN05, NormalizeAssetRequest
from .package_layout import TargetPackageLayout
from .stage_metrics import physical_frame_report


JOINT_TYPE_NAMES = {
    "PhysicsFixedJoint",
    "PhysicsRevoluteJoint",
    "PhysicsPrismaticJoint",
    "PhysicsSphericalJoint",
    "PhysicsDistanceJoint",
}
LIMITED_DOF_JOINT_TYPES = {"PhysicsRevoluteJoint", "PhysicsPrismaticJoint"}
GENERATED_MASS_METHOD = "bbox_shell_density_template_v1"
GENERATED_MASS_DENSITY_KG_M3 = 1000.0
GENERATED_MASS_SHELL_OCCUPANCY = 0.08
GENERATED_MASS_MIN_KG = 0.02
GENERATED_MASS_MAX_KG = 10.0
GENERATED_DIMENSION_MIN_M = 0.01
GENERATED_INERTIA_MIN = 1.0e-6
PROVENANCE_CUSTOM_KEY = "aan:provenance"
PROVENANCE_FIELD_BY_ATTRIBUTE = {
    "physics:mass": "mass",
    "physics:diagonalInertia": "inertia",
    "physics:centerOfMass": "center_of_mass",
    "physics:principalAxes": "principal_axes",
}


@dataclass(frozen=True)
class PhysicsCheckResult:
    overall_status: str
    return_code: int
    physics_closure: dict[str, Any]
    articulation_closure: dict[str, Any]
    static_physics_report: dict[str, Any]
    static_articulation_report: dict[str, Any]
    stage_gate: dict[str, Any]
    blocked_reasons: list[dict[str, Any]]
    source_physics_audit: dict[str, Any]
    output_role_admission: dict[str, Any]


def build_not_run_physics_checks(reason: str) -> PhysicsCheckResult:
    summary = {
        "rigid_body_count": 0,
        "collision_count": 0,
        "mass_record_count": 0,
        "invalid_rigid_body_count": 0,
    }
    return PhysicsCheckResult(
        overall_status="blocked",
        return_code=0,
        physics_closure={"status": "not_run", "reason": reason, "summary": summary},
        articulation_closure={
            "status": "not_run",
            "reason": reason,
            "summary": {"articulation_root_count": 0, "joint_count": 0},
        },
        static_physics_report={"status": "not_run", "reason": reason, **summary},
        static_articulation_report={
            "status": "not_run",
            "reason": reason,
            "articulation_root_count": 0,
            "joint_count": 0,
        },
        stage_gate={
            "check_id": MILESTONE_AAN05,
            "stage": "physics_static",
            "status": "not_run",
            "summary": reason,
        },
        blocked_reasons=[],
        source_physics_audit={"status": "not_run", "reason": reason},
        output_role_admission={"status": "not_run", "reason": reason},
    )


def audit_source_physics(source_usd: Path, scope_prims: list[str]) -> dict[str, Any]:
    """Read-only strict inventory for one or more source scopes.

    This deliberately treats a non-authored schema fallback as a finding.  It is
    separate from package normalization, so a role conversion cannot conceal a
    malformed source family.
    """
    stage = _open_stage(source_usd)
    source_sha = _sha256_file(source_usd) if source_usd.exists() else None
    if stage is None:
        return {
            "status": "blocked",
            "source_sha256": source_sha,
            "scope": scope_prims,
            "summary": {"invalid_rigid_body_count": 0},
            "family_members": [],
            "blocked_reasons": [
                {
                    "blocker_id": "aan05_block_source_physics_stage_open",
                    "severity": "blocking",
                    "summary": "Could not open source USD for physics audit.",
                }
            ],
        }
    effective_scopes = scope_prims or ["/"]
    members = []
    for scope in effective_scopes:
        scope_prim = stage.GetPrimAtPath(scope)
        if not scope_prim or not scope_prim.IsValid():
            members.append(
                {
                    "scope": scope,
                    "status": "blocked",
                    "summary": {
                        "rigid_body_count": 0,
                        "collision_count": 0,
                        "mass_record_count": 0,
                        "invalid_rigid_body_count": 0,
                    },
                    "rigid_bodies": [],
                    "collisions": [],
                    "mass_properties": [],
                    "articulation_roots": [],
                    "joints": [],
                    "blocked_reasons": [
                        {
                            "blocker_id": "aan05_block_source_scope_missing",
                            "severity": "blocking",
                            "summary": "A declared asset scope is absent from the source USD.",
                            "scope": scope,
                        }
                    ],
                }
            )
            continue
        inspection = _inspect_stage(stage, [scope])
        blockers = _strict_mass_blockers(inspection["mass_records"])
        members.append(
            {
                "scope": scope,
                "status": "blocked" if blockers else "pass",
                "summary": inspection["summary"],
                "rigid_bodies": inspection["rigid_bodies"],
                "collisions": inspection["collisions"],
                "mass_properties": inspection["mass_records"],
                "articulation_roots": inspection["articulation_roots"],
                "joints": inspection["joints"],
                "blocked_reasons": blockers,
            }
        )
    invalid_count = sum(
        int(member["summary"].get("invalid_rigid_body_count", 0)) for member in members
    )
    return {
        "status": "blocked" if any(member["status"] == "blocked" for member in members) else "pass",
        "source_path": str(source_usd),
        "source_sha256": source_sha,
        "scope": effective_scopes,
        "summary": {
            "family_member_count": len(members),
            "invalid_rigid_body_count": invalid_count,
            "rigid_body_count": sum(int(member["summary"]["rigid_body_count"]) for member in members),
        },
        "family_members": members,
    }


def build_physics_checks(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
    *,
    source_physics_audit: dict[str, Any] | None = None,
    normalization_actions: list[dict[str, Any]] | None = None,
    physics_profile_admission: dict[str, Any] | None = None,
    physics_profile_actions: list[dict[str, Any]] | None = None,
    physics_profile_blockers: list[dict[str, Any]] | None = None,
) -> PhysicsCheckResult:
    source_audit = source_physics_audit or audit_source_physics(
        request.source_usd, request.effective_asset_scope_prims
    )
    stage = _open_stage(layout.root_usd)
    if stage is None:
        return _blocked_result(
            layout.root_usd,
            "AAN-05 could not open the package root USD for physics inspection.",
            [
                {
                    "blocker_id": "aan05_block_physics_stage_open",
                    "severity": "blocking",
                    "summary": "AAN-05 could not open the package root USD for physics inspection.",
                }
            ],
            source_audit,
        )

    required = _required_prim_records(stage, request.required_prims)
    scope = request.effective_asset_scope_prims
    scoped_required = _required_prim_records(stage, scope)
    physical_frame = physical_frame_report(request.source_usd, layout.root_usd, scope)
    if request.asset_role == "visual_static":
        output_admission = _visual_static_output_admission(stage, scope)
        blockers = [
            {
                "blocker_id": "aan05_block_required_prim_missing",
                "severity": "blocking",
                "summary": "One or more required prim paths are absent in the packaged USD.",
            }
            for item in required
            if item["status"] == "blocked"
        ]
        blockers.extend(
            {
                "blocker_id": "aan05_block_asset_scope_missing",
                "severity": "blocking",
                "summary": "One or more declared asset-scope prim paths are absent in the packaged USD.",
                "scope": item["path"],
            }
            for item in scoped_required
            if item["status"] == "blocked"
        )
        if output_admission["status"] != "pass":
            blockers.append(
                {
                    "blocker_id": "aan05_block_visual_static_physics_residue",
                    "severity": "blocking",
                    "summary": "visual_static output still has active physics semantics in its declared scope.",
                    "residue": output_admission.get("residue", []),
                    "required_resolution": "Delete applied Physics/Physx APIs and deactivate typed physics joints in the package overlay.",
                }
            )
        if physical_frame["status"] != "pass":
            blockers.append(_physical_frame_blocker(physical_frame))
        status = "blocked" if blockers else "pass"
        inspection = _inspect_stage(stage, scope)
        summary = inspection["summary"]
        physics_closure = {
            "status": status,
            "role": "visual_static",
            "root_usd": str(layout.root_usd),
            "scope": _scope_record(scope),
            "source_physics_audit": source_audit,
            "output_role_admission": output_admission,
            "normalization_actions": normalization_actions or [],
            "required_prims": required,
            "rigid_bodies": inspection["rigid_bodies"],
            "collisions": inspection["collisions"],
            "mass_properties": inspection["mass_records"],
            "scale": _scale_record(stage),
            "physical_frame": physical_frame,
            "summary": summary,
        }
        articulation_closure = {
            "status": status,
            "role": "visual_static",
            "articulation_roots": inspection["articulation_roots"],
            "joints": inspection["joints"],
            "summary": _articulation_summary(inspection["articulation_roots"], inspection["joints"]),
        }
        return _result(
            status,
            blockers,
            physics_closure,
            articulation_closure,
            source_audit,
            output_admission,
        )

    profile_requested = request.physics_profile is not None
    profile_admission = physics_profile_admission or {
        "status": "not_requested" if not profile_requested else "blocked",
        "reason": "no profile authoring result was supplied" if profile_requested else None,
    }
    # A source-bound profile is the whole dynamic physical property set.  Do
    # not mix it with legacy bbox/template inference; a profile failure blocks
    # instead of allowing generic automatic-mass repair to hide the failure.
    generated = (
        {}
        if profile_requested
        else _author_invalid_mass_properties(stage, _scoped_prims(stage, scope))
    )
    if generated:
        try:
            stage.GetRootLayer().Save()
        except Exception as exc:
            return _blocked_result(
                layout.root_usd,
                f"AAN-05 could not save generated mass properties: {exc}",
                [
                    {
                        "blocker_id": "aan05_block_generated_mass_save",
                        "severity": "blocking",
                        "summary": "AAN-05 could not save generated mass properties into the package USD.",
                    }
                ],
                source_audit,
            )
        stage = _open_stage(layout.root_usd)
        if stage is None:
            return _blocked_result(
                layout.root_usd,
                "AAN-05 could not reopen the package USD after mass normalization.",
                [
                    {
                        "blocker_id": "aan05_block_generated_mass_reopen",
                        "severity": "blocking",
                        "summary": "AAN-05 could not reopen the package USD after mass normalization.",
                    }
                ],
                source_audit,
            )
        required = _required_prim_records(stage, request.required_prims)
        scoped_required = _required_prim_records(stage, scope)

    inspection = _inspect_stage(stage, scope, generated=generated)
    blockers = list(physics_profile_blockers or [])
    if profile_requested and profile_admission.get("status") != "pass" and not blockers:
        blockers.append(
            {
                "blocker_id": "aan05_block_physics_profile",
                "severity": "blocking",
                "summary": "Dynamic physics profile admission did not pass.",
                "detail": profile_admission.get("errors") or profile_admission.get("reason"),
            }
        )
    if any(item["status"] == "blocked" for item in required):
        blockers.append(
            {
                "blocker_id": "aan05_block_required_prim_missing",
                "severity": "blocking",
                "summary": "One or more required prim paths are absent in the packaged USD.",
            }
        )
    if any(item["status"] == "blocked" for item in scoped_required):
        blockers.append(
            {
                "blocker_id": "aan05_block_asset_scope_missing",
                "severity": "blocking",
                "summary": "One or more declared asset-scope prim paths are absent in the packaged USD.",
                "scope_prims": [item["path"] for item in scoped_required if item["status"] == "blocked"],
            }
        )
    blockers.extend(_physics_blockers(request, inspection))
    if physical_frame["status"] != "pass":
        blockers.append(_physical_frame_blocker(physical_frame))
    blockers.extend(
        _articulation_blockers(
            request,
            inspection["articulation_roots"],
            inspection["joints"],
        )
    )
    status = "blocked" if blockers else "pass"
    output_admission = {
        "status": status,
        "role": request.asset_role,
        "scope": scope,
        "summary": inspection["summary"],
    }
    physics_closure = {
        "status": status,
        "role": request.asset_role,
        "root_usd": str(layout.root_usd),
        "scope": _scope_record(scope),
        "value_policy": (
            "source_bound_profile_full_mass_bundle"
            if profile_requested
            else "legacy_preserve_valid_authored_then_derive_with_persistent_provenance"
        ),
        "profile_admission": profile_admission,
        "profile_normalization_actions": physics_profile_actions or [],
        "source_physics_audit": source_audit,
        "output_role_admission": output_admission,
        "normalization_actions": normalization_actions or [],
        "required_prims": required,
        "rigid_bodies": inspection["rigid_bodies"],
        "collisions": inspection["collisions"],
        "mass_properties": inspection["mass_records"],
        "scale": _scale_record(stage),
        "physical_frame": physical_frame,
        "reset_pose": _reset_pose_record(stage, request.required_prims),
        "summary": inspection["summary"],
    }
    articulation_closure = {
        "status": status,
        "root_usd": str(layout.root_usd),
        "scope": _scope_record(scope),
        "articulation_roots": inspection["articulation_roots"],
        "joints": inspection["joints"],
        "dof_mapping": _dof_mapping(inspection["joints"]),
        "reset_values": _joint_reset_values(inspection["joints"]),
        "summary": _articulation_summary(inspection["articulation_roots"], inspection["joints"]),
    }
    return _result(
        status,
        blockers,
        physics_closure,
        articulation_closure,
        source_audit,
        output_admission,
    )


def _result(
    status: str,
    blockers: list[dict[str, Any]],
    physics_closure: dict[str, Any],
    articulation_closure: dict[str, Any],
    source_audit: dict[str, Any],
    output_admission: dict[str, Any],
) -> PhysicsCheckResult:
    summary = physics_closure.get("summary", {})
    articulation_summary = articulation_closure.get("summary", {})
    return PhysicsCheckResult(
        overall_status=status,
        return_code=5 if status == "blocked" else 0,
        physics_closure=physics_closure,
        articulation_closure=articulation_closure,
        static_physics_report={
            "status": status,
            "root_usd": physics_closure.get("root_usd"),
            **summary,
            "required_prims": physics_closure.get("required_prims", []),
        },
        static_articulation_report={
            "status": status,
            "root_usd": articulation_closure.get("root_usd"),
            **articulation_summary,
            "required_prims": physics_closure.get("required_prims", []),
        },
        stage_gate={
            "check_id": MILESTONE_AAN05,
            "stage": "physics_static",
            "status": status,
            "summary": (
                "AAN-05 recorded strict source/output physics admission evidence."
                if status == "pass"
                else "AAN-05 found blocking physics, role, or articulation gaps."
            ),
        },
        blocked_reasons=blockers,
        source_physics_audit=source_audit,
        output_role_admission=output_admission,
    )


def _physical_frame_blocker(physical_frame: dict[str, Any]) -> dict[str, Any]:
    return {
        "blocker_id": "aan05_block_physical_frame_parity",
        "severity": "blocking",
        "summary": "Package stage metadata or scoped world bounds changed the source physical frame.",
        "metric_mismatches": physical_frame.get("metric_mismatches", []),
        "scope_prims": physical_frame.get("blocked_scope_prims", []),
        "required_resolution": (
            "Preserve metersPerUnit, kilogramsPerUnit, upAxis, timing, and scope world bounds "
            "on the ConvertAsset-owned package entry layer."
        ),
    }


def _blocked_result(
    root_usd: Path,
    reason: str,
    blockers: list[dict[str, Any]],
    source_audit: dict[str, Any],
) -> PhysicsCheckResult:
    return _result(
        "blocked",
        blockers,
        {
            "status": "blocked",
            "root_usd": str(root_usd),
            "reason": reason,
            "summary": {
                "rigid_body_count": 0,
                "collision_count": 0,
                "mass_record_count": 0,
                "invalid_rigid_body_count": 0,
            },
        },
        {
            "status": "blocked",
            "root_usd": str(root_usd),
            "reason": reason,
            "summary": {"articulation_root_count": 0, "joint_count": 0},
        },
        source_audit,
        {"status": "blocked", "reason": reason},
    )


def _open_stage(path: Path) -> Any | None:
    try:
        from pxr import Usd  # type: ignore

        return Usd.Stage.Open(str(path))
    except Exception:
        return None


def _required_prim_records(stage: Any, required_prims: list[str]) -> list[dict[str, Any]]:
    records = []
    for path in required_prims:
        prim = stage.GetPrimAtPath(path)
        exists = bool(prim and prim.IsValid())
        records.append({"path": path, "exists": exists, "status": "pass" if exists else "blocked"})
    return records


def _scoped_prims(stage: Any, scope_prims: list[str], *, include_inactive: bool = False) -> list[Any]:
    roots = []
    for path in scope_prims:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            roots.append(prim)
    if not roots and not scope_prims:
        roots = [stage.GetPseudoRoot()]
    if not roots:
        return []
    try:
        all_prims = list(stage.TraverseAll()) if include_inactive else list(stage.Traverse())
    except Exception:
        all_prims = list(stage.Traverse())
    root_paths = [root.GetPath().pathString for root in roots]
    return [
        prim
        for prim in all_prims
        if any(
            prim.GetPath().pathString == root
            or prim.GetPath().pathString.startswith(root.rstrip("/") + "/")
            for root in root_paths
        )
    ]


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


def _has_api(prim: Any, api_schema: str) -> bool:
    return api_schema in _schema_tokens(prim)


def _inspect_stage(
    stage: Any,
    scope: list[str],
    *,
    generated: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    scoped = _scoped_prims(stage, scope)
    rigid_bodies = [_rigid_body_record(prim) for prim in scoped if _has_api(prim, "PhysicsRigidBodyAPI")]
    collisions = [_collision_record(prim) for prim in scoped if _has_api(prim, "PhysicsCollisionAPI")]
    mass_records = [_mass_record(prim, (generated or {}).get(prim.GetPath().pathString)) for prim in scoped if _has_api(prim, "PhysicsRigidBodyAPI")]
    articulation_roots = [
        _articulation_root_record(prim)
        for prim in scoped
        if _has_api(prim, "PhysicsArticulationRootAPI") or _has_api(prim, "PhysxArticulationAPI")
    ]
    joints = [_joint_record(prim) for prim in scoped if prim.GetTypeName() in JOINT_TYPE_NAMES]
    return {
        "rigid_bodies": rigid_bodies,
        "collisions": collisions,
        "mass_records": mass_records,
        "articulation_roots": articulation_roots,
        "joints": joints,
        "summary": _summary(rigid_bodies, collisions, mass_records),
    }


def _author_invalid_mass_properties(stage: Any, scoped_prims: list[Any]) -> dict[str, dict[str, Any]]:
    try:
        from pxr import Gf, UsdPhysics  # type: ignore
    except Exception:
        return {}
    generated: dict[str, dict[str, Any]] = {}
    for prim in scoped_prims:
        if not _has_api(prim, "PhysicsRigidBodyAPI"):
            continue
        existing_mass = _value_record(prim, "physics:mass", _valid_positive_scalar)
        existing_inertia = _value_record(prim, "physics:diagonalInertia", _valid_positive_vec3)
        existing_com = _value_record(prim, "physics:centerOfMass", _valid_finite_vec3)
        existing_axes = _value_record(prim, "physics:principalAxes", _valid_principal_axes)
        need_mass = existing_mass["status"] != "pass"
        # Replacing an invalid mass requires a new, consistent inertia even if the old
        # inertia happened to be numerically positive.
        need_inertia = need_mass or existing_inertia["status"] != "pass"
        need_com = existing_com["status"] != "pass"
        need_axes = existing_axes["status"] != "pass"
        if not any((need_mass, need_inertia, need_com, need_axes)):
            continue
        derived = _derive_mass_properties(stage, prim)
        mass_api = UsdPhysics.MassAPI.Apply(prim)
        record: dict[str, Any] = {
            "bbox_dimensions_m": derived["bbox_dimensions_m"],
            "bbox_volume_m3": derived["bbox_volume_m3"],
            "effective_volume_m3": derived["effective_volume_m3"],
        }
        if need_mass:
            mass_value = float(derived["mass"])
            mass_basis = {
                "attribute": f"{prim.GetPath().pathString}.physics:mass",
                "source": "template",
                "value": mass_value,
            }
            attr = mass_api.CreateMassAttr(mass_value)
            attr.Set(mass_value)
            _set_provenance(
                attr,
                method=GENERATED_MASS_METHOD,
                field="mass",
                mass_basis=mass_basis,
                dimensions_m=derived["bbox_dimensions_m"],
            )
            record["mass"] = mass_value
        else:
            # Keep computation tied to the authored USD scalar, rather than the
            # JSON presentation value (which is rounded for evidence output).
            try:
                mass_value = float(prim.GetAttribute("physics:mass").Get())
            except Exception:
                mass_value = float(existing_mass["value"])
            mass_basis = {
                "attribute": f"{prim.GetPath().pathString}.physics:mass",
                "source": str(existing_mass["value_source"]),
                "value": round(mass_value, 8),
                "raw_value": mass_value,
            }
        if need_inertia:
            inertia = _inertia_from_dimensions(mass_value, derived["bbox_dimensions_m"])
            value = Gf.Vec3f(float(inertia[0]), float(inertia[1]), float(inertia[2]))
            attr = mass_api.CreateDiagonalInertiaAttr(value)
            attr.Set(value)
            _set_provenance(
                attr,
                method="bbox_inertia_from_mass_v1",
                field="inertia",
                mass_basis=mass_basis,
                dimensions_m=derived["bbox_dimensions_m"],
            )
            record["inertia"] = inertia
            record["mass_basis"] = mass_basis
        if need_com:
            center = _local_center_of_mass(prim)
            value = Gf.Vec3f(float(center[0]), float(center[1]), float(center[2]))
            attr = mass_api.CreateCenterOfMassAttr(value)
            attr.Set(value)
            _set_provenance(
                attr,
                method="local_bbox_center_v1",
                field="center_of_mass",
                dimensions_m=derived["bbox_dimensions_m"],
            )
            record["center_of_mass"] = center
        if need_axes:
            axes = Gf.Quatf(1.0, Gf.Vec3f(0.0, 0.0, 0.0))
            attr = mass_api.CreatePrincipalAxesAttr(axes)
            attr.Set(axes)
            _set_provenance(
                attr,
                method="identity_principal_axes_v1",
                field="principal_axes",
                dimensions_m=derived["bbox_dimensions_m"],
            )
            record["principal_axes"] = [1.0, 0.0, 0.0, 0.0]
        generated[prim.GetPath().pathString] = record
    return generated


def _set_provenance(
    attr: Any,
    *,
    method: str,
    field: str,
    dimensions_m: list[float],
    mass_basis: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "value_source": "derived",
        "method": method,
        "field": field,
        "input_artifacts": ["UsdGeom world bbox"],
        "bbox_dimensions_m": dimensions_m,
        "package_authored": True,
    }
    if mass_basis is not None:
        payload["mass_basis"] = mass_basis
    attr.SetCustomDataByKey(PROVENANCE_CUSTOM_KEY, json.dumps(payload, sort_keys=True))


def _derive_mass_properties(stage: Any, prim: Any) -> dict[str, Any]:
    dims_m = _bbox_dimensions_m(stage, prim)
    bbox_volume = max(dims_m[0] * dims_m[1] * dims_m[2], 0.0)
    effective_volume = bbox_volume * GENERATED_MASS_SHELL_OCCUPANCY
    mass = min(max(effective_volume * GENERATED_MASS_DENSITY_KG_M3, GENERATED_MASS_MIN_KG), GENERATED_MASS_MAX_KG)
    return {
        "bbox_dimensions_m": [round(float(value), 8) for value in dims_m],
        "bbox_volume_m3": round(float(bbox_volume), 10),
        "effective_volume_m3": round(float(effective_volume), 10),
        "mass": round(float(mass), 8),
    }


def _inertia_from_dimensions(mass: float, dims_m: list[float]) -> list[float]:
    return [
        round(max(mass * (dims_m[1] ** 2 + dims_m[2] ** 2) / 12.0, GENERATED_INERTIA_MIN), 10),
        round(max(mass * (dims_m[0] ** 2 + dims_m[2] ** 2) / 12.0, GENERATED_INERTIA_MIN), 10),
        round(max(mass * (dims_m[0] ** 2 + dims_m[1] ** 2) / 12.0, GENERATED_INERTIA_MIN), 10),
    ]


def _bbox_dimensions_m(stage: Any, prim: Any) -> list[float]:
    try:
        from pxr import Usd, UsdGeom  # type: ignore

        meters_per_unit = float(UsdGeom.GetStageMetersPerUnit(stage) or 1.0)
        cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        size = cache.ComputeWorldBound(prim).ComputeAlignedBox().GetSize()
        return [max(abs(float(size[index])) * meters_per_unit, GENERATED_DIMENSION_MIN_M) for index in range(3)]
    except Exception:
        return [GENERATED_DIMENSION_MIN_M] * 3


def _local_center_of_mass(prim: Any) -> list[float]:
    try:
        from pxr import Usd, UsdGeom  # type: ignore

        cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        aligned = cache.ComputeLocalBound(prim).ComputeAlignedBox()
        minimum = aligned.GetMin()
        maximum = aligned.GetMax()
        center = (minimum + maximum) * 0.5
        return [round(float(center[index]), 8) for index in range(3)]
    except Exception:
        return [0.0, 0.0, 0.0]


def _rigid_body_record(prim: Any) -> dict[str, Any]:
    return {
        "prim_path": prim.GetPath().pathString,
        "type_name": prim.GetTypeName(),
        "owning_layer": _owning_layer(prim),
        "enabled": _value_record(prim, "physics:rigidBodyEnabled", _valid_boolean),
        "kinematic": _value_record(prim, "physics:kinematicEnabled", _valid_boolean),
    }


def _collision_record(prim: Any) -> dict[str, Any]:
    return {
        "prim_path": prim.GetPath().pathString,
        "type_name": prim.GetTypeName(),
        "owning_layer": _owning_layer(prim),
        "enabled": _value_record(prim, "physics:collisionEnabled", _valid_boolean),
        "approximation": _value_record(prim, "physics:approximation", _valid_any),
    }


def _mass_record(prim: Any, generated: dict[str, Any] | None = None) -> dict[str, Any]:
    mass = _value_record(prim, "physics:mass", _valid_positive_scalar)
    inertia = _value_record(prim, "physics:diagonalInertia", _valid_positive_vec3)
    center_of_mass = _value_record(prim, "physics:centerOfMass", _valid_finite_vec3)
    principal_axes = _value_record(prim, "physics:principalAxes", _valid_principal_axes)
    records = [mass, inertia, center_of_mass, principal_axes]
    invalid = any(
        record["status"] != "pass" or record.get("provenance_status") != "pass"
        for record in records
    )
    auto_compute_reliance = _has_api(prim, "PhysicsMassAPI") and any(
        record["value_source"] in {"fallback", "missing"} for record in records
    )
    result = {
        "prim_path": prim.GetPath().pathString,
        "type_name": prim.GetTypeName(),
        "owning_layer": _owning_layer(prim),
        "mass_api_applied": _has_api(prim, "PhysicsMassAPI"),
        "mass": mass,
        "density": _value_record(prim, "physics:density", _valid_positive_scalar),
        "center_of_mass": center_of_mass,
        "inertia": inertia,
        "principal_axes": principal_axes,
        "provenance_complete": all(
            record.get("provenance_status") == "pass" for record in records
        ),
        "invalid_auto_compute_reliance": auto_compute_reliance,
        "status": "blocked" if invalid or auto_compute_reliance else "pass",
    }
    if generated:
        result["generation"] = {
            "method": GENERATED_MASS_METHOD,
            "value_source": "derived",
            "package_authored": True,
            "density_template_kg_m3": GENERATED_MASS_DENSITY_KG_M3,
            "shell_occupancy": GENERATED_MASS_SHELL_OCCUPANCY,
            "bbox_dimensions_m": generated["bbox_dimensions_m"],
            "bbox_volume_m3": generated["bbox_volume_m3"],
            "effective_volume_m3": generated["effective_volume_m3"],
            "generated_fields": sorted(
                key for key in ("mass", "inertia", "center_of_mass", "principal_axes") if key in generated
            ),
        }
    return result


def _value_record(prim: Any, attr_name: str, validator: Any) -> dict[str, Any]:
    attr = prim.GetAttribute(attr_name)
    attribute_path = f"{prim.GetPath().pathString}.{attr_name}"
    expected_field = PROVENANCE_FIELD_BY_ATTRIBUTE.get(attr_name)
    if not attr:
        return {
            "value": None,
            "value_source": "missing",
            "status": "missing",
            "attribute": attribute_path,
            "provenance_status": "invalid" if expected_field else "not_applicable",
        }
    try:
        value = attr.Get()
    except Exception:
        value = None
    provenance = _provenance(attr)
    if value is None:
        return {
            "value": None,
            "value_source": str(provenance.get("value_source", "missing")) if provenance else "missing",
            "status": "missing",
            "attribute": attribute_path,
            "provenance_status": "invalid" if expected_field else "not_applicable",
            **_provenance_fields(provenance),
        }
    if provenance:
        value_source = str(provenance.get("value_source", "derived"))
        provenance_status, normalized_provenance = _validate_physics_provenance(
            provenance,
            expected_field=expected_field,
            attr=attr,
            prim=prim,
            value_source=value_source,
        )
    else:
        try:
            value_source = "authored" if attr.HasAuthoredValueOpinion() else "fallback"
        except Exception:
            value_source = "fallback"
        provenance_status, normalized_provenance = _implicit_provenance(
            attr,
            prim,
            expected_field=expected_field,
            value_source=value_source,
        )
    record: dict[str, Any] = {
        "value": _json_value(value),
        "value_source": value_source,
        "status": "pass" if validator(value) else "invalid",
        "attribute": attribute_path,
        "provenance_status": provenance_status,
    }
    if normalized_provenance is not None:
        record["provenance"] = normalized_provenance
    record.update(_provenance_fields(provenance))
    return record


def _implicit_provenance(
    attr: Any,
    prim: Any,
    *,
    expected_field: str | None,
    value_source: str,
) -> tuple[str, dict[str, Any] | None]:
    if expected_field is None:
        return "not_applicable", None
    if value_source != "authored":
        return "invalid", {
            "value_source": value_source,
            "reason": "No authored opinion or persistent derived/template provenance was found.",
        }
    return "pass", {
        "value_source": "authored",
        "method": "usd_authored_value",
        "field": expected_field,
        "authored_value_opinion": True,
        "authoring_layer": _attribute_authoring_layer(attr) or _owning_layer(prim),
    }


def _validate_physics_provenance(
    provenance: dict[str, Any],
    *,
    expected_field: str | None,
    attr: Any,
    prim: Any,
    value_source: str,
) -> tuple[str, dict[str, Any] | None]:
    if expected_field is None:
        return "not_applicable", provenance
    normalized = dict(provenance)
    if value_source == "authored":
        # A custom authored record must be at least as complete as the implicit
        # authored record emitted for a plain USD authored opinion.
        normalized.setdefault("method", "usd_authored_value")
        normalized.setdefault("field", expected_field)
        normalized.setdefault("authored_value_opinion", bool(attr.HasAuthoredValueOpinion()))
        normalized.setdefault("authoring_layer", _attribute_authoring_layer(attr) or _owning_layer(prim))
        required = {"method", "field", "authored_value_opinion", "authoring_layer"}
        valid = (
            all(normalized.get(key) for key in required)
            and normalized.get("field") == expected_field
            and bool(attr.HasAuthoredValueOpinion())
        )
        return ("pass" if valid else "invalid"), normalized
    if value_source not in {"derived", "template", "manual_override", "profile"}:
        return "invalid", normalized
    common_valid = (
        isinstance(normalized.get("method"), str)
        and bool(normalized["method"].strip())
        and normalized.get("field") == expected_field
        and isinstance(normalized.get("input_artifacts"), list)
        and bool(normalized["input_artifacts"])
        and isinstance(normalized.get("package_authored"), bool)
    )
    if value_source != "profile":
        common_valid = common_valid and _valid_positive_dimensions(normalized.get("bbox_dimensions_m"))
    if value_source == "template":
        common_valid = common_valid and isinstance(normalized.get("template_id"), str) and bool(normalized["template_id"].strip())
    if value_source == "profile":
        common_valid = common_valid and all(
            isinstance(normalized.get(key), str) and bool(normalized[key].strip())
            for key in ("profile_id", "profile_revision", "profile_sha256", "source_sha256", "quality_tier", "frame")
        )
    if expected_field in {"mass", "inertia"}:
        common_valid = common_valid and _valid_mass_basis(normalized.get("mass_basis"))
    return ("pass" if common_valid else "invalid"), normalized


def _valid_positive_dimensions(value: Any) -> bool:
    values = _vec_components(value, 3)
    return values is not None and all(math.isfinite(item) and item > 0.0 for item in values)


def _valid_mass_basis(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        isinstance(value.get("attribute"), str)
        and value["attribute"].endswith(".physics:mass")
        and str(value.get("source", "")) in {"authored", "derived", "template", "manual_override", "profile"}
        and _valid_positive_scalar(value.get("value"))
    )


def _provenance(attr: Any) -> dict[str, Any] | None:
    try:
        raw = attr.GetCustomDataByKey(PROVENANCE_CUSTOM_KEY)
    except Exception:
        return None
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _provenance_fields(provenance: dict[str, Any] | None) -> dict[str, Any]:
    if not provenance:
        return {}
    result = {
        key: provenance[key]
        for key in (
            "method",
            "input_artifacts",
            "bbox_dimensions_m",
            "package_authored",
            "mass_basis",
            "profile_id",
            "profile_revision",
            "profile_sha256",
            "source_sha256",
            "quality_tier",
            "frame",
            "si_value",
        )
        if key in provenance
    }
    return result


def _valid_positive_scalar(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0.0
    except (TypeError, ValueError):
        return False


def _valid_positive_vec3(value: Any) -> bool:
    values = _vec_components(value, 3)
    return values is not None and all(math.isfinite(item) and item > 0.0 for item in values)


def _valid_finite_vec3(value: Any) -> bool:
    values = _vec_components(value, 3)
    return values is not None and all(math.isfinite(item) for item in values)


def _valid_principal_axes(value: Any) -> bool:
    try:
        if hasattr(value, "GetReal") and hasattr(value, "GetImaginary"):
            imaginary = value.GetImaginary()
            values = [float(value.GetReal()), *(float(imaginary[index]) for index in range(3))]
        else:
            values = _vec_components(value, 4)
        if values is None or not all(math.isfinite(item) for item in values):
            return False
        norm = math.sqrt(sum(item * item for item in values))
        # A principal-axes quaternion represents a rotation.  A nonzero but
        # arbitrarily scaled quaternion is not an explicit valid orientation.
        return abs(norm - 1.0) <= 1.0e-4
    except Exception:
        return False


def _valid_boolean(value: Any) -> bool:
    return isinstance(value, bool)


def _valid_any(value: Any) -> bool:
    return value is not None


def _vec_components(value: Any, expected: int) -> list[float] | None:
    if value is None:
        return None
    try:
        values = [float(value[index]) for index in range(expected)]
    except Exception:
        return None
    return values if len(values) == expected else None


def _physics_blockers(request: NormalizeAssetRequest, inspection: dict[str, Any]) -> list[dict[str, Any]]:
    blockers = []
    if request.asset_class in {"rigid", "articulated"} and not inspection["rigid_bodies"]:
        blockers.append(
            {
                "blocker_id": "aan05_block_missing_rigid_body",
                "severity": "blocking",
                "summary": "No PhysicsRigidBodyAPI prim was found under the declared asset scope.",
            }
        )
    if request.asset_class in {"rigid", "articulated"} and not inspection["collisions"]:
        blockers.append(
            {
                "blocker_id": "aan05_block_missing_collision",
                "severity": "blocking",
                "summary": "No PhysicsCollisionAPI prim was found under the declared asset scope.",
            }
        )
    strict = _strict_mass_blockers(inspection["mass_records"])
    if strict:
        blockers.extend(strict)
    return blockers


def _strict_mass_blockers(mass_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    invalid = [record for record in mass_records if record["status"] != "pass"]
    if not invalid:
        return []
    return [
        {
            "blocker_id": "aan05_block_invalid_mass_properties",
            "severity": "blocking",
            "summary": "Every scoped rigid body requires explicit finite positive mass/inertia, finite COM, a normalizable principal-axes quaternion, and complete provenance.",
            "count": len(invalid),
            "prim_paths": [record["prim_path"] for record in invalid],
            "required_resolution": "Author valid package values or derive them with persistent provenance; do not rely on PhysX auto-compute fallbacks.",
        }
    ]


def _articulation_blockers(request: NormalizeAssetRequest, articulation_roots: list[dict[str, Any]], joints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if request.asset_class != "articulated":
        return []
    blockers = []
    if not articulation_roots:
        blockers.append(
            {
                "blocker_id": "aan05_block_missing_articulation",
                "severity": "blocking",
                "summary": "Asset class is articulated but no articulation root was found.",
            }
        )
    if not joints:
        blockers.append(
            {
                "blocker_id": "aan05_block_missing_joint",
                "severity": "blocking",
                "summary": "Asset class is articulated but no physics joint was found.",
            }
        )
    bad_joints = [
        joint
        for joint in joints
        if joint["joint_type"] in LIMITED_DOF_JOINT_TYPES
        and (joint["axis"]["status"] != "pass" or joint["limits"]["status"] != "pass")
    ]
    if bad_joints:
        blockers.append(
            {
                "blocker_id": "aan05_block_incomplete_joint_semantics",
                "severity": "blocking",
                "summary": "One or more articulated joints lack valid axis or limits.",
                "count": len(bad_joints),
            }
        )
    return blockers


def _articulation_root_record(prim: Any) -> dict[str, Any]:
    return {
        "prim_path": prim.GetPath().pathString,
        "type_name": prim.GetTypeName(),
        "owning_layer": _owning_layer(prim),
        "value_source": "authored",
    }


def _joint_record(prim: Any) -> dict[str, Any]:
    joint_type = prim.GetTypeName()
    lower = _value_record(prim, "physics:lowerLimit", _valid_finite_scalar)
    upper = _value_record(prim, "physics:upperLimit", _valid_finite_scalar)
    return {
        "prim_path": prim.GetPath().pathString,
        "joint_type": joint_type,
        "owning_layer": _owning_layer(prim),
        "axis": _value_record(prim, "physics:axis", _valid_any),
        "limits": {"lower": lower, "upper": upper, "status": _joint_limit_status(joint_type, lower, upper)},
        "enabled": _value_record(prim, "physics:jointEnabled", _valid_boolean),
        "collision_enabled": _value_record(prim, "physics:collisionEnabled", _valid_boolean),
        "drive_status": _drive_status(prim),
        "reset_value": _joint_reset_value(prim, joint_type),
    }


def _valid_finite_scalar(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _joint_limit_status(joint_type: str, lower: dict[str, Any], upper: dict[str, Any]) -> str:
    if joint_type not in LIMITED_DOF_JOINT_TYPES:
        return "not_applicable"
    if lower["status"] != "pass" or upper["status"] != "pass":
        return "missing"
    try:
        return "pass" if float(lower["value"]) <= float(upper["value"]) else "invalid_order"
    except (TypeError, ValueError):
        return "invalid_value"


def _drive_status(prim: Any) -> str:
    for attr in prim.GetAttributes():
        name = attr.GetName()
        if "drive" in name.lower() or name.startswith("physxJoint:"):
            return "authored"
    return "not_authored"


def _joint_reset_value(prim: Any, joint_type: str) -> dict[str, Any]:
    attr_name = "state:linear:physics:position" if joint_type == "PhysicsPrismaticJoint" else "state:angular:physics:position"
    return _value_record(prim, attr_name, _valid_finite_scalar)


def _summary(rigid_bodies: list[dict[str, Any]], collisions: list[dict[str, Any]], mass_records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "rigid_body_count": len(rigid_bodies),
        "collision_count": len(collisions),
        "mass_record_count": len(mass_records),
        "authored_mass_count": sum(1 for item in mass_records if item["mass"]["value_source"] == "authored"),
        "authored_inertia_count": sum(1 for item in mass_records if item["inertia"]["value_source"] == "authored"),
        "derived_mass_count": sum(1 for item in mass_records if item["mass"]["value_source"] == "derived"),
        "derived_inertia_count": sum(1 for item in mass_records if item["inertia"]["value_source"] == "derived"),
        "invalid_rigid_body_count": sum(1 for item in mass_records if item["status"] != "pass"),
    }


def _articulation_summary(articulation_roots: list[dict[str, Any]], joints: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "articulation_root_count": len(articulation_roots),
        "joint_count": len(joints),
        "controllable_dof_count": sum(1 for joint in joints if joint["joint_type"] in LIMITED_DOF_JOINT_TYPES),
    }


def _visual_static_output_admission(stage: Any, scope: list[str]) -> dict[str, Any]:
    prims = _scoped_prims(stage, scope, include_inactive=True)
    residue = []
    active_rigid = active_collision = active_articulation = active_joint = 0
    for prim in prims:
        if not prim.IsActive():
            continue
        tokens = _schema_tokens(prim)
        categories = []
        if "PhysicsRigidBodyAPI" in tokens:
            active_rigid += 1
            categories.append("rigid_body")
        if "PhysicsCollisionAPI" in tokens or "PhysicsMeshCollisionAPI" in tokens:
            active_collision += 1
            categories.append("collision")
        if "PhysicsArticulationRootAPI" in tokens or "PhysxArticulationAPI" in tokens:
            active_articulation += 1
            categories.append("articulation")
        if prim.GetTypeName() in JOINT_TYPE_NAMES:
            active_joint += 1
            categories.append("joint")
        physics_tokens = sorted(token for token in tokens if token.startswith(("Physics", "Physx")))
        if physics_tokens and "schema_tokens" not in categories:
            categories.append("schema_tokens")
        if categories:
            residue.append({"prim_path": prim.GetPath().pathString, "categories": categories, "tokens": physics_tokens})
    summary = {
        "active_articulation_root_count": active_articulation,
        "active_collision_count": active_collision,
        "active_joint_count": active_joint,
        "active_rigid_body_count": active_rigid,
    }
    return {"status": "pass" if not residue else "blocked", "scope": scope, "summary": summary, "residue": residue}


def _scale_record(stage: Any) -> dict[str, Any]:
    try:
        from pxr import UsdGeom  # type: ignore

        meters = UsdGeom.GetStageMetersPerUnit(stage)
        up_axis = UsdGeom.GetStageUpAxis(stage)
    except Exception:
        meters = None
        up_axis = None
    return {
        "meters_per_unit": {"value": _json_value(meters), "value_source": "authored" if meters is not None else "missing"},
        "up_axis": {"value": _json_value(up_axis), "value_source": "authored" if up_axis is not None else "missing"},
        "mass_derivation_dimensions": "world_bounds_meters",
    }


def _reset_pose_record(stage: Any, required_prims: list[str]) -> dict[str, Any]:
    records = []
    for path in required_prims:
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsValid():
            records.append({"prim_path": path, "status": "blocked", "value_source": "missing"})
            continue
        records.append({"prim_path": path, "status": "pass", "transform": _world_transform(prim)})
    return {"required_prims": records}


def _world_transform(prim: Any) -> list[list[float]] | None:
    try:
        from pxr import Usd, UsdGeom  # type: ignore

        matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        return [[round(float(matrix[row][column]), 8) for column in range(4)] for row in range(4)]
    except Exception:
        return None


def _scope_record(scope: list[str]) -> dict[str, Any]:
    return {"mode": "asset_scope_prims" if scope else "whole_stage", "asset_scope_prims": scope}


def _dof_mapping(joints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapping = []
    for index, joint in enumerate(joint for joint in joints if joint["joint_type"] in LIMITED_DOF_JOINT_TYPES):
        mapping.append({"dof_index": index, "joint_prim": joint["prim_path"], "joint_type": joint["joint_type"], "axis": joint["axis"]["value"], "value_source": joint["axis"]["value_source"]})
    return mapping


def _joint_reset_values(joints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"joint_prim": joint["prim_path"], "joint_type": joint["joint_type"], "reset_value": joint["reset_value"]} for joint in joints if joint["joint_type"] in LIMITED_DOF_JOINT_TYPES]


def _owning_layer(prim: Any) -> str | None:
    try:
        stack = prim.GetPrimStack()
        layer = getattr(stack[0], "layer", None) if stack else None
        return str(getattr(layer, "realPath", None) or getattr(layer, "identifier", "")) if layer else None
    except Exception:
        return None


def _attribute_authoring_layer(attr: Any) -> str | None:
    try:
        stack = attr.GetPropertyStack()
        layer = getattr(stack[0], "layer", None) if stack else None
        if layer is None:
            return None
        return str(getattr(layer, "realPath", None) or getattr(layer, "identifier", ""))
    except Exception:
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return round(value, 8) if math.isfinite(value) else str(value)
    if hasattr(value, "GetReal") and hasattr(value, "GetImaginary"):
        try:
            imaginary = value.GetImaginary()
            return [round(float(value.GetReal()), 8), *(round(float(imaginary[index]), 8) for index in range(3))]
        except Exception:
            return str(value)
    try:
        return [_json_value(value[index]) for index in range(len(value))]
    except Exception:
        return str(value)
