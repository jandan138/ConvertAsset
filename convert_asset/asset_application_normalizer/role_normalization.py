"""Role-scoped, ConvertAsset-owned USD normalization overlays.

The module intentionally knows nothing about a particular LabUtopia asset name.
It receives explicit prim scopes from the request and writes only the package root
overlay created by AAN-03.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from .model import NormalizeAssetRequest
from .package_layout import TargetPackageLayout
from .usd_closure import SOURCE_MATERIAL_PRIM_CUSTOM_DATA_KEY


@dataclass(frozen=True)
class RoleNormalizationResult:
    overall_status: str
    return_code: int
    normalization_actions: list[dict[str, Any]] = field(default_factory=list)
    visual_preservation_fingerprint: dict[str, Any] = field(default_factory=dict)
    blocked_reasons: list[dict[str, Any]] = field(default_factory=list)


def build_not_run_role_normalization(reason: str) -> RoleNormalizationResult:
    return RoleNormalizationResult(
        overall_status="not_run",
        return_code=0,
        visual_preservation_fingerprint={"status": "not_run", "reason": reason},
    )


def normalize_asset_role(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
) -> RoleNormalizationResult:
    if request.asset_role == "dynamic":
        return _verify_dynamic_visual_preservation(layout, request)
    if request.asset_role != "visual_static":
        return _blocked(
            f"Unsupported asset role: {request.asset_role}",
            "aan_role_block_unknown_role",
        )

    stage = _open_stage(layout.root_usd)
    if stage is None:
        return _blocked(
            "Could not open the package root USD before visual_static normalization.",
            "aan_role_block_stage_open",
        )
    scopes = request.effective_asset_scope_prims
    if not scopes:
        return _blocked(
            "visual_static requires at least one --asset-scope-prim or --required-prim.",
            "aan_role_block_missing_scope",
        )
    missing = [path for path in scopes if not _valid_prim(stage.GetPrimAtPath(path))]
    if missing:
        return _blocked(
            "One or more visual_static scope prims are missing from the package.",
            "aan_role_block_scope_missing",
            paths=missing,
        )

    source_stage = _open_stage(request.source_usd)
    if source_stage is None:
        return _blocked(
            "Could not open the immutable source USD for visual preservation comparison.",
            "aan_role_block_source_stage_open",
        )
    raw_source = _visual_fingerprint(source_stage, scopes)
    before = _visual_fingerprint(stage, scopes)
    actions: list[dict[str, Any]] = []
    scoped_prims = _scope_prims(stage, scopes, include_inactive=True)
    scoped_paths = {prim.GetPath().pathString for prim in scoped_prims}
    for prim in scoped_prims:
        removed = _remove_physics_api_tokens(prim)
        if removed:
            actions.append(
                {
                    "prim_path": prim.GetPath().pathString,
                    "action": "delete_applied_physics_api_tokens",
                    "tokens": removed,
                }
            )
        if _is_physics_typed_prim(prim):
            prim.SetActive(False)
            actions.append(
                {
                    "prim_path": prim.GetPath().pathString,
                    "action": "deactivate_physics_typed_prim",
                    "type_name": prim.GetTypeName(),
                }
            )

    # A joint may live outside the declared subtree while targeting a body inside it.
    # It remains physics-active unless it is also disabled in this owned overlay.
    for prim in _all_prims(stage):
        if prim.GetPath().pathString in scoped_paths or not _is_physics_joint(prim):
            continue
        targets = _joint_targets(prim)
        if any(_is_under_scope(str(target), scopes) for target in targets):
            prim.SetActive(False)
            actions.append(
                {
                    "prim_path": prim.GetPath().pathString,
                    "action": "deactivate_external_joint_targeting_scope",
                    "targets": sorted(str(target) for target in targets),
                }
            )

    try:
        stage.GetRootLayer().Save()
    except Exception as exc:
        return _blocked(
            f"Could not save visual_static overlay: {exc}",
            "aan_role_block_overlay_save",
        )
    output_stage = _open_stage(layout.root_usd)
    if output_stage is None:
        return _blocked(
            "Could not reopen the package root USD after visual_static normalization.",
            "aan_role_block_overlay_reopen",
        )
    after = _visual_fingerprint(output_stage, scopes)
    preserved = raw_source["signature"] == before["signature"] == after["signature"]
    preservation = {
        "status": "pass" if preserved else "blocked",
        "raw_source": raw_source,
        "package_before_role": before,
        "package_after_role": after,
        "scope": scopes,
    }
    if preservation["status"] != "pass":
        return RoleNormalizationResult(
            overall_status="blocked",
            return_code=5,
            normalization_actions=actions,
            visual_preservation_fingerprint=preservation,
            blocked_reasons=[
                {
                    "blocker_id": "aan_role_block_visual_preservation",
                    "severity": "blocking",
                    "summary": "The raw source, package pre-role, and package post-role visual fingerprints differ.",
                    "required_resolution": "Limit the overlay to physics semantics and preserve visual composition.",
                }
            ],
        )
    return RoleNormalizationResult(
        overall_status="pass",
        return_code=0,
        normalization_actions=actions,
        visual_preservation_fingerprint=preservation,
    )


def _verify_dynamic_visual_preservation(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
) -> RoleNormalizationResult:
    """Fail closed if a dynamic package changes visible composition or pose.

    A dynamic profile later writes only MassAPI/RigidBody properties into its
    own overlay, but the package closure itself can still accidentally change
    a mesh binding, visibility, or transform.  Compare source and composed
    package here, before physics authoring, then rely on AAN-05 physical-frame
    bounds parity to protect the profile-owned output layer as well.
    """
    scopes = request.effective_asset_scope_prims
    source_stage = _open_stage(request.source_usd)
    package_stage = _open_stage(layout.root_usd)
    if source_stage is None or package_stage is None:
        return _blocked(
            "Could not open source and package USD for dynamic visual preservation comparison.",
            "aan_role_block_dynamic_visual_stage_open",
        )
    missing_source = [
        path for path in scopes if not _valid_prim(source_stage.GetPrimAtPath(path))
    ]
    missing_package = [
        path for path in scopes if not _valid_prim(package_stage.GetPrimAtPath(path))
    ]
    if missing_source or missing_package:
        return _blocked(
            "One or more dynamic visual-preservation scope prims are missing.",
            "aan_role_block_dynamic_visual_scope_missing",
            paths=sorted(set([*missing_source, *missing_package])),
        )
    raw_source = _visual_fingerprint(source_stage, scopes)
    package = _visual_fingerprint(package_stage, scopes)
    preserved = raw_source["signature"] == package["signature"]
    preservation = {
        "status": "pass" if preserved else "blocked",
        "raw_source": raw_source,
        "package_before_physics_profile": package,
        "scope": scopes,
        "policy": "mesh_visibility_material_bindings_and_world_transforms_must_match",
    }
    if not preserved:
        return RoleNormalizationResult(
            overall_status="blocked",
            return_code=5,
            visual_preservation_fingerprint=preservation,
            blocked_reasons=[
                {
                    "blocker_id": "aan_role_block_dynamic_visual_preservation",
                    "severity": "blocking",
                    "summary": "The dynamic package changed a scoped mesh visibility, material binding, or world transform.",
                    "required_resolution": "Preserve source visual composition while authoring physics only in the package-owned overlay.",
                }
            ],
        )
    return RoleNormalizationResult(
        overall_status="pass",
        return_code=0,
        visual_preservation_fingerprint=preservation,
    )


def _blocked(
    summary: str,
    blocker_id: str,
    *,
    paths: list[str] | None = None,
) -> RoleNormalizationResult:
    blocker: dict[str, Any] = {
        "blocker_id": blocker_id,
        "severity": "blocking",
        "summary": summary,
    }
    if paths:
        blocker["paths"] = paths
    return RoleNormalizationResult(
        overall_status="blocked",
        return_code=5,
        blocked_reasons=[blocker],
        visual_preservation_fingerprint={"status": "blocked", "reason": summary},
    )


def _open_stage(path: Path) -> Any | None:
    try:
        from pxr import Usd  # type: ignore

        return Usd.Stage.Open(str(path))
    except Exception:
        return None


def _valid_prim(prim: Any) -> bool:
    try:
        return bool(prim and prim.IsValid())
    except Exception:
        return False


def _all_prims(stage: Any) -> list[Any]:
    try:
        return list(stage.TraverseAll())
    except Exception:
        return list(stage.Traverse())


def _scope_prims(stage: Any, scopes: list[str], *, include_inactive: bool) -> list[Any]:
    candidates = _all_prims(stage) if include_inactive else list(stage.Traverse())
    return [
        prim
        for prim in candidates
        if _valid_prim(prim) and _is_under_scope(prim.GetPath().pathString, scopes)
    ]


def _is_under_scope(path: str, scopes: list[str]) -> bool:
    return any(path == scope or path.startswith(scope.rstrip("/") + "/") for scope in scopes)


def _schema_tokens(prim: Any) -> list[str]:
    tokens = set()
    try:
        tokens.update(str(token) for token in prim.GetAppliedSchemas())
    except Exception:
        pass
    try:
        op = prim.GetMetadata("apiSchemas")
        if hasattr(op, "GetAppliedItems"):
            tokens.update(str(token) for token in op.GetAppliedItems())
    except Exception:
        pass
    return sorted(tokens)


def _remove_physics_api_tokens(prim: Any) -> list[str]:
    removed = [
        token
        for token in _schema_tokens(prim)
        if token.startswith("Physics") or token.startswith("Physx")
    ]
    if not removed:
        return []
    try:
        from pxr import Sdf  # type: ignore

        prim.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(deletedItems=removed))
    except Exception:
        return []
    return removed


def _is_physics_typed_prim(prim: Any) -> bool:
    return str(prim.GetTypeName()).startswith("Physics")


def _is_physics_joint(prim: Any) -> bool:
    return "Joint" in str(prim.GetTypeName()) and _is_physics_typed_prim(prim)


def _joint_targets(prim: Any) -> list[Any]:
    targets: list[Any] = []
    for relationship in prim.GetRelationships():
        if not relationship.GetName().startswith("physics:body"):
            continue
        try:
            targets.extend(relationship.GetTargets())
        except Exception:
            continue
    return targets


def _visual_fingerprint(stage: Any, scopes: list[str]) -> dict[str, Any]:
    meshes = []
    for prim in _scope_prims(stage, scopes, include_inactive=True):
        if not prim.IsActive() or prim.GetTypeName() != "Mesh":
            continue
        material_targets = []
        for relationship in prim.GetRelationships():
            if relationship.GetName().startswith("material:binding"):
                material_targets.extend(
                    _canonical_material_target(stage, target)
                    for target in relationship.GetTargets()
                )
        meshes.append(
            {
                "path": prim.GetPath().pathString,
                "visibility": _attribute_value(prim, "visibility"),
                "material_targets": sorted(material_targets),
                "world_transform": _world_transform(prim),
            }
        )
    records = {"scope_world_transforms": {}, "meshes": sorted(meshes, key=lambda item: item["path"])}
    for scope in scopes:
        prim = stage.GetPrimAtPath(scope)
        records["scope_world_transforms"][scope] = _world_transform(prim) if _valid_prim(prim) else None
    encoded = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return {**records, "signature": hashlib.sha256(encoded.encode("utf-8")).hexdigest()}


def _canonical_material_target(stage: Any, target: Any) -> str:
    """Compare relocated package materials against their immutable source identity."""
    try:
        target_prim = stage.GetPrimAtPath(target.GetPrimPath())
        source_material = target_prim.GetCustomDataByKey(
            SOURCE_MATERIAL_PRIM_CUSTOM_DATA_KEY
        )
    except Exception:
        source_material = None
    if isinstance(source_material, str) and source_material.startswith("/"):
        return source_material
    return str(target)


def _attribute_value(prim: Any, name: str) -> Any:
    try:
        value = prim.GetAttribute(name).Get()
    except Exception:
        return None
    return _json_value(value)


def _world_transform(prim: Any) -> list[list[float]] | None:
    try:
        from pxr import Usd, UsdGeom  # type: ignore

        matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        return [
            [round(float(matrix[row][column]), 8) for column in range(4)]
            for row in range(4)
        ]
    except Exception:
        return None


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return round(value, 8)
    try:
        return [round(float(value[index]), 8) for index in range(len(value))]
    except Exception:
        return str(value)
