"""Static physics and articulation evidence for AAN-05."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

from .model import MILESTONE_AAN05, NormalizeAssetRequest
from .package_layout import TargetPackageLayout


JOINT_TYPE_NAMES = {
    "PhysicsFixedJoint",
    "PhysicsRevoluteJoint",
    "PhysicsPrismaticJoint",
    "PhysicsSphericalJoint",
    "PhysicsDistanceJoint",
}
LIMITED_DOF_JOINT_TYPES = {"PhysicsRevoluteJoint", "PhysicsPrismaticJoint"}


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


def build_not_run_physics_checks(reason: str) -> PhysicsCheckResult:
    report = {
        "status": "not_run",
        "reason": reason,
        "rigid_body_count": 0,
        "collision_count": 0,
        "mass_record_count": 0,
    }
    articulation_report = {
        "status": "not_run",
        "reason": reason,
        "articulation_root_count": 0,
        "joint_count": 0,
    }
    return PhysicsCheckResult(
        overall_status="blocked",
        return_code=0,
        physics_closure={
            "status": "not_run",
            "reason": reason,
            "summary": {
                "rigid_body_count": 0,
                "collision_count": 0,
                "mass_record_count": 0,
            },
        },
        articulation_closure={
            "status": "not_run",
            "reason": reason,
            "summary": {
                "articulation_root_count": 0,
                "joint_count": 0,
            },
        },
        static_physics_report=report,
        static_articulation_report=articulation_report,
        stage_gate={
            "check_id": MILESTONE_AAN05,
            "stage": "physics_static",
            "status": "not_run",
            "summary": reason,
        },
        blocked_reasons=[],
    )


def build_physics_checks(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
) -> PhysicsCheckResult:
    root_usd = layout.root_usd
    stage = _open_stage(root_usd)
    if stage is None:
        reason = "AAN-05 could not open the package root USD for physics inspection."
        return _blocked_result(
            root_usd,
            reason,
            [
                {
                    "blocker_id": "aan05_block_physics_stage_open",
                    "severity": "blocking",
                    "summary": reason,
                    "required_resolution": "Fix the package USD so Usd.Stage.Open succeeds.",
                }
            ],
        )

    required = _required_prim_records(stage, request.required_prims)
    required_blockers = [
        {
            "blocker_id": "aan05_block_required_prim_missing",
            "severity": "blocking",
            "summary": "One or more required prim paths are absent in the packaged USD.",
            "count": sum(1 for item in required if item["status"] == "blocked"),
            "required_resolution": "Fix the task contract or package USD prim layout.",
        }
    ] if any(item["status"] == "blocked" for item in required) else []

    scoped_prims = _scoped_prims(stage, request.required_prims)
    rigid_bodies = [_rigid_body_record(prim) for prim in scoped_prims if _has_api(prim, "PhysicsRigidBodyAPI")]
    collisions = [_collision_record(prim) for prim in scoped_prims if _has_api(prim, "PhysicsCollisionAPI")]
    mass_records = [_mass_record(prim) for prim in scoped_prims if _has_api(prim, "PhysicsMassAPI")]
    articulation_roots = [
        _articulation_root_record(prim)
        for prim in scoped_prims
        if _has_api(prim, "PhysicsArticulationRootAPI")
    ]
    joints = [_joint_record(prim) for prim in scoped_prims if prim.GetTypeName() in JOINT_TYPE_NAMES]

    blockers = [
        *required_blockers,
        *_physics_blockers(request, required, rigid_bodies, collisions, mass_records),
        *_articulation_blockers(request, articulation_roots, joints),
    ]
    status = "blocked" if blockers else "pass"
    return_code = 5 if blockers else 0
    summary = _summary(rigid_bodies, collisions, mass_records)
    articulation_summary = _articulation_summary(articulation_roots, joints)

    physics_closure = {
        "status": status,
        "root_usd": str(root_usd),
        "scope": _scope_record(request.required_prims),
        "value_policy": "preserve_authored_then_generate_with_provenance",
        "required_prims": required,
        "rigid_bodies": rigid_bodies,
        "collisions": collisions,
        "mass_properties": mass_records,
        "scale": _scale_record(stage),
        "reset_pose": _reset_pose_record(stage, request.required_prims),
        "summary": summary,
    }
    articulation_closure = {
        "status": status,
        "root_usd": str(root_usd),
        "scope": _scope_record(request.required_prims),
        "articulation_roots": articulation_roots,
        "joints": joints,
        "dof_mapping": _dof_mapping(joints),
        "reset_values": _joint_reset_values(joints),
        "summary": articulation_summary,
    }
    static_physics_report = {
        "status": status,
        "root_usd": str(root_usd),
        **summary,
        "required_prims": required,
    }
    static_articulation_report = {
        "status": status,
        "root_usd": str(root_usd),
        **articulation_summary,
        "required_prims": required,
    }

    return PhysicsCheckResult(
        overall_status=status,
        return_code=return_code,
        physics_closure=physics_closure,
        articulation_closure=articulation_closure,
        static_physics_report=static_physics_report,
        static_articulation_report=static_articulation_report,
        stage_gate={
            "check_id": MILESTONE_AAN05,
            "stage": "physics_static",
            "status": status,
            "summary": (
                "AAN-05 recorded static physics and articulation evidence."
                if status == "pass"
                else "AAN-05 found blocking physics or articulation gaps."
            ),
        },
        blocked_reasons=blockers,
    )


def _blocked_result(
    root_usd: Path,
    reason: str,
    blockers: list[dict[str, Any]],
) -> PhysicsCheckResult:
    return PhysicsCheckResult(
        overall_status="blocked",
        return_code=5,
        physics_closure={
            "status": "blocked",
            "root_usd": str(root_usd),
            "reason": reason,
            "summary": {
                "rigid_body_count": 0,
                "collision_count": 0,
                "mass_record_count": 0,
            },
        },
        articulation_closure={
            "status": "blocked",
            "root_usd": str(root_usd),
            "reason": reason,
            "summary": {
                "articulation_root_count": 0,
                "joint_count": 0,
            },
        },
        static_physics_report={
            "status": "blocked",
            "root_usd": str(root_usd),
            "reason": reason,
        },
        static_articulation_report={
            "status": "blocked",
            "root_usd": str(root_usd),
            "reason": reason,
        },
        stage_gate={
            "check_id": MILESTONE_AAN05,
            "stage": "physics_static",
            "status": "blocked",
            "summary": reason,
        },
        blocked_reasons=blockers,
    )


def _open_stage(root_usd: Path) -> Any | None:
    try:
        from pxr import Usd  # type: ignore
    except Exception:
        return None
    try:
        return Usd.Stage.Open(str(root_usd))
    except Exception:
        return None


def _required_prim_records(stage: Any, required_prims: list[str]) -> list[dict[str, Any]]:
    records = []
    for path in required_prims:
        prim = stage.GetPrimAtPath(path)
        exists = bool(prim and prim.IsValid())
        records.append({"path": path, "exists": exists, "status": "pass" if exists else "blocked"})
    return records


def _scoped_prims(stage: Any, required_prims: list[str]) -> list[Any]:
    roots = []
    for path in required_prims:
        prim = stage.GetPrimAtPath(path)
        if prim and prim.IsValid():
            roots.append(prim)
    if not roots:
        roots = [stage.GetPseudoRoot()]

    scoped = []
    seen = set()
    try:
        from pxr import Usd  # type: ignore
    except Exception:
        return []
    for root in roots:
        for prim in Usd.PrimRange(root):
            key = prim.GetPath().pathString
            if key in seen:
                continue
            seen.add(key)
            scoped.append(prim)
    return scoped


def _has_api(prim: Any, api_schema: str) -> bool:
    try:
        return api_schema in set(prim.GetAppliedSchemas())
    except Exception:
        return False


def _rigid_body_record(prim: Any) -> dict[str, Any]:
    return {
        "prim_path": prim.GetPath().pathString,
        "type_name": prim.GetTypeName(),
        "owning_layer": _owning_layer(prim),
        "enabled": _authored_value_record(prim, "physics:rigidBodyEnabled"),
        "kinematic": _authored_value_record(prim, "physics:kinematicEnabled"),
        "velocity": _authored_value_record(prim, "physics:velocity"),
        "angular_velocity": _authored_value_record(prim, "physics:angularVelocity"),
        "value_source": "authored",
    }


def _collision_record(prim: Any) -> dict[str, Any]:
    return {
        "prim_path": prim.GetPath().pathString,
        "type_name": prim.GetTypeName(),
        "owning_layer": _owning_layer(prim),
        "enabled": _authored_value_record(prim, "physics:collisionEnabled"),
        "approximation": _authored_value_record(prim, "physics:approximation"),
        "value_source": "authored",
    }


def _mass_record(prim: Any) -> dict[str, Any]:
    return {
        "prim_path": prim.GetPath().pathString,
        "type_name": prim.GetTypeName(),
        "owning_layer": _owning_layer(prim),
        "mass": _physics_value_record(prim, "physics:mass", generated_method="bbox_density_template_v0"),
        "density": _authored_value_record(prim, "physics:density"),
        "center_of_mass": _authored_value_record(prim, "physics:centerOfMass"),
        "inertia": _physics_value_record(
            prim,
            "physics:diagonalInertia",
            generated_method="bbox_inertia_template_v0",
        ),
        "principal_axes": _authored_value_record(prim, "physics:principalAxes"),
    }


def _physics_value_record(
    prim: Any,
    attr_name: str,
    *,
    generated_method: str,
) -> dict[str, Any]:
    record = _authored_value_record(prim, attr_name)
    if record["value_source"] == "authored":
        return record
    return {
        "value": None,
        "value_source": "derived",
        "status": "not_generated",
        "method": generated_method,
        "input_artifacts": ["UsdGeom bbox or mesh volume"],
        "required_gate": "AAN-06-runtime-smoke",
    }


def _articulation_root_record(prim: Any) -> dict[str, Any]:
    return {
        "prim_path": prim.GetPath().pathString,
        "type_name": prim.GetTypeName(),
        "owning_layer": _owning_layer(prim),
        "value_source": "authored",
    }


def _joint_record(prim: Any) -> dict[str, Any]:
    joint_type = prim.GetTypeName()
    lower = _authored_value_record(prim, "physics:lowerLimit")
    upper = _authored_value_record(prim, "physics:upperLimit")
    return {
        "prim_path": prim.GetPath().pathString,
        "joint_type": joint_type,
        "owning_layer": _owning_layer(prim),
        "axis": _authored_value_record(prim, "physics:axis"),
        "limits": {
            "lower": lower,
            "upper": upper,
            "status": _joint_limit_status(joint_type, lower, upper),
        },
        "enabled": _authored_value_record(prim, "physics:jointEnabled"),
        "collision_enabled": _authored_value_record(prim, "physics:collisionEnabled"),
        "local_pos0": _authored_value_record(prim, "physics:localPos0"),
        "local_pos1": _authored_value_record(prim, "physics:localPos1"),
        "local_rot0": _authored_value_record(prim, "physics:localRot0"),
        "local_rot1": _authored_value_record(prim, "physics:localRot1"),
        "drive_status": _drive_status(prim),
        "reset_value": _joint_reset_value(prim, joint_type),
        "value_source": "authored",
    }


def _joint_limit_status(
    joint_type: str,
    lower: dict[str, Any],
    upper: dict[str, Any],
) -> str:
    if joint_type not in LIMITED_DOF_JOINT_TYPES:
        return "not_applicable"
    if lower["value_source"] != "authored" or upper["value_source"] != "authored":
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
    attr_name = "state:angular:physics:position"
    if joint_type == "PhysicsPrismaticJoint":
        attr_name = "state:linear:physics:position"
    return _authored_value_record(prim, attr_name)


def _authored_value_record(prim: Any, attr_name: str) -> dict[str, Any]:
    attr = prim.GetAttribute(attr_name)
    if not attr:
        return {"value": None, "value_source": "missing", "status": "missing"}
    try:
        value = attr.Get()
    except Exception:
        value = None
    if value is None:
        return {"value": None, "value_source": "missing", "status": "missing"}
    return {
        "value": _json_value(value),
        "value_source": "authored",
        "status": "pass",
        "attribute": f"{prim.GetPath().pathString}.{attr_name}",
    }


def _scale_record(stage: Any) -> dict[str, Any]:
    try:
        from pxr import UsdGeom  # type: ignore

        meters = UsdGeom.GetStageMetersPerUnit(stage)
        up_axis = UsdGeom.GetStageUpAxis(stage)
    except Exception:
        meters = None
        up_axis = None
    return {
        "meters_per_unit": {
            "value": _json_value(meters),
            "value_source": "authored" if meters is not None else "missing",
        },
        "up_axis": {
            "value": _json_value(up_axis),
            "value_source": "authored" if up_axis is not None else "missing",
        },
    }


def _reset_pose_record(stage: Any, required_prims: list[str]) -> dict[str, Any]:
    records = []
    for path in required_prims:
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsValid():
            records.append({"prim_path": path, "status": "blocked", "value_source": "missing"})
            continue
        records.append(
            {
                "prim_path": path,
                "status": "pass",
                "value_source": "authored" if _has_authored_xform(prim) else "identity_or_composed_default",
                "transform": _local_transform(prim),
            }
        )
    return {"required_prims": records}


def _has_authored_xform(prim: Any) -> bool:
    return any(attr.GetName().startswith("xformOp:") for attr in prim.GetAttributes())


def _local_transform(prim: Any) -> list[list[float]] | None:
    try:
        from pxr import UsdGeom  # type: ignore

        matrix = UsdGeom.Xformable(prim).GetLocalTransformation()
    except Exception:
        return None
    return _matrix_to_lists(matrix)


def _matrix_to_lists(matrix: Any) -> list[list[float]]:
    rows = []
    for row_idx in range(4):
        rows.append([round(float(matrix[row_idx][col_idx]), 8) for col_idx in range(4)])
    return rows


def _physics_blockers(
    request: NormalizeAssetRequest,
    required: list[dict[str, Any]],
    rigid_bodies: list[dict[str, Any]],
    collisions: list[dict[str, Any]],
    mass_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if any(item["status"] == "blocked" for item in required):
        return []
    if request.asset_class not in {"rigid", "articulated"}:
        return []
    blockers = []
    if not rigid_bodies:
        blockers.append(
            {
                "blocker_id": "aan05_block_missing_rigid_body",
                "severity": "blocking",
                "summary": "No PhysicsRigidBodyAPI prim was found under the required asset scope.",
                "required_resolution": "Author a rigid body, provide a generated rigid proxy with provenance, or correct asset_class.",
            }
        )
    if not collisions:
        blockers.append(
            {
                "blocker_id": "aan05_block_missing_collision",
                "severity": "blocking",
                "summary": "No PhysicsCollisionAPI prim was found under the required asset scope.",
                "required_resolution": "Author collision geometry or generate a collision proxy with provenance.",
            }
        )
    if rigid_bodies and not mass_records:
        blockers.append(
            {
                "blocker_id": "aan05_block_missing_mass_inertia",
                "severity": "blocking",
                "summary": "Rigid bodies exist but no mass/inertia provenance was found.",
                "required_resolution": "Preserve authored MassAPI values or generate derived/template values with provenance.",
            }
        )
    return blockers


def _articulation_blockers(
    request: NormalizeAssetRequest,
    articulation_roots: list[dict[str, Any]],
    joints: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if request.asset_class != "articulated":
        return []
    blockers = []
    if not articulation_roots:
        blockers.append(
            {
                "blocker_id": "aan05_block_missing_articulation",
                "severity": "blocking",
                "summary": "Asset class is articulated but no PhysicsArticulationRootAPI prim was found.",
                "required_resolution": "Author an articulation root, provide a manual contract override, or correct asset_class.",
            }
        )
    if not joints:
        blockers.append(
            {
                "blocker_id": "aan05_block_missing_joint",
                "severity": "blocking",
                "summary": "Asset class is articulated but no physics joint prim was found.",
                "required_resolution": "Author joint type/axis/limit/reset pose or provide a manual contract override.",
            }
        )
    bad_joints = [
        joint
        for joint in joints
        if joint["joint_type"] in LIMITED_DOF_JOINT_TYPES
        and (
            joint["axis"]["value_source"] != "authored"
            or joint["limits"]["status"] != "pass"
        )
    ]
    if bad_joints:
        blockers.append(
            {
                "blocker_id": "aan05_block_incomplete_joint_semantics",
                "severity": "blocking",
                "summary": "One or more articulated joints lack authored axis or valid limits.",
                "count": len(bad_joints),
                "required_resolution": "Preserve joint axis/limits from source USD or attach a reviewed manual override.",
            }
        )
    return blockers


def _summary(
    rigid_bodies: list[dict[str, Any]],
    collisions: list[dict[str, Any]],
    mass_records: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        "rigid_body_count": len(rigid_bodies),
        "collision_count": len(collisions),
        "mass_record_count": len(mass_records),
        "authored_mass_count": sum(
            1 for record in mass_records if record["mass"]["value_source"] == "authored"
        ),
        "authored_inertia_count": sum(
            1 for record in mass_records if record["inertia"]["value_source"] == "authored"
        ),
    }


def _articulation_summary(
    articulation_roots: list[dict[str, Any]],
    joints: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        "articulation_root_count": len(articulation_roots),
        "joint_count": len(joints),
        "controllable_dof_count": sum(
            1 for joint in joints if joint["joint_type"] in LIMITED_DOF_JOINT_TYPES
        ),
    }


def _scope_record(required_prims: list[str]) -> dict[str, Any]:
    return {
        "mode": "required_prims" if required_prims else "whole_stage",
        "required_prims": required_prims,
    }


def _dof_mapping(joints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapping = []
    dof_index = 0
    for joint in joints:
        if joint["joint_type"] not in LIMITED_DOF_JOINT_TYPES:
            continue
        mapping.append(
            {
                "dof_index": dof_index,
                "joint_prim": joint["prim_path"],
                "joint_type": joint["joint_type"],
                "axis": joint["axis"]["value"],
                "value_source": "authored",
            }
        )
        dof_index += 1
    return mapping


def _joint_reset_values(joints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "joint_prim": joint["prim_path"],
            "joint_type": joint["joint_type"],
            "reset_value": joint["reset_value"],
        }
        for joint in joints
        if joint["joint_type"] in LIMITED_DOF_JOINT_TYPES
    ]


def _owning_layer(prim: Any) -> str | None:
    try:
        stack = prim.GetPrimStack()
    except Exception:
        return None
    if not stack:
        return None
    layer = getattr(stack[0], "layer", None)
    if not layer:
        return None
    return str(getattr(layer, "realPath", None) or getattr(layer, "identifier", ""))


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return round(float(value), 8)
        return str(value)
    if isinstance(value, (list, tuple)) or (
        hasattr(value, "__len__") and hasattr(value, "__getitem__")
    ):
        try:
            return [_json_value(value[idx]) for idx in range(len(value))]
        except Exception:
            return str(value)
    return str(value)
