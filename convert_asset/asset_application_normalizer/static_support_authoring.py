"""Compile a source-bound static support profile into package-owned USD.

This role is deliberately neither ``dynamic`` nor ``visual_static``: it owns
collision and a provisional contact material, but never rigid-body, mass,
joint, or articulation semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from .model import NormalizeAssetRequest
from .package_layout import TargetPackageLayout


PROFILE_SCHEMA_VERSION = "aan.static_support_profile.v1"
CONTRACT_SCHEMA_VERSION = "aan.static_support_contract.v1"


@dataclass(frozen=True)
class StaticSupportAuthoringResult:
    overall_status: str
    return_code: int
    contract: dict[str, Any]
    normalization_actions: list[dict[str, Any]]
    blocked_reasons: list[dict[str, Any]]


def build_not_requested_static_support() -> StaticSupportAuthoringResult:
    return StaticSupportAuthoringResult(
        "not_requested",
        0,
        {"schema_version": CONTRACT_SCHEMA_VERSION, "status": "not_requested"},
        [],
        [],
    )


def build_not_run_static_support(reason: str) -> StaticSupportAuthoringResult:
    return StaticSupportAuthoringResult(
        "not_run",
        0,
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "status": "not_run",
            "reason": reason,
        },
        [],
        [],
    )


def apply_static_support_profile(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
) -> StaticSupportAuthoringResult:
    if request.asset_role != "static_support":
        return build_not_requested_static_support()
    profile_path = request.static_support_profile
    if profile_path is None:
        return _blocked("static support profile was not supplied")
    try:
        profile_bytes = profile_path.read_bytes()
        payload = json.loads(profile_bytes.decode("utf-8"))
    except Exception as exc:
        return _blocked(f"could not read static support profile: {exc}")

    errors = _validate_profile(payload, request)
    source_sha = _sha256(request.source_usd)
    if payload.get("source_binding", {}).get("sha256") != source_sha:
        errors.append("source_binding.sha256 does not match the immutable source USD")
    if errors:
        return _blocked("; ".join(errors))

    try:
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade  # type: ignore

        stage = Usd.Stage.Open(str(layout.root_usd))
        if stage is None:
            raise RuntimeError(f"could not open package USD: {layout.root_usd}")
        overlay = Sdf.Layer.FindOrOpen(str(layout.static_support_overlay_usd))
        if overlay is None:
            raise RuntimeError(
                f"could not open static support overlay: {layout.static_support_overlay_usd}"
            )
        stage.SetEditTarget(Usd.EditTarget(overlay))

        source_path = payload.get("source_collider_prim")
        source_prim = stage.GetPrimAtPath(source_path) if source_path else None
        if _qualified_source_collider(source_prim):
            collider = source_prim
            selection = "preserved_source"
            collider_source = "qualified_source"
            actions = [
                {
                    "action": "preserve_qualified_source_collider",
                    "prim_path": source_path,
                }
            ]
        else:
            proxy = payload["proxy"]
            cube = UsdGeom.Cube.Define(stage, proxy["prim_path"])
            cube.CreateSizeAttr(1.0).Set(1.0)
            xform = UsdGeom.Xformable(cube.GetPrim())
            xform.ClearXformOpOrder()
            xform.AddTranslateOp().Set(Gf.Vec3d(*proxy["center_xyz"]))
            xform.AddScaleOp().Set(Gf.Vec3f(*proxy["size_xyz"]))
            collider = cube.GetPrim()
            UsdPhysics.CollisionAPI.Apply(collider).CreateCollisionEnabledAttr(True).Set(True)
            selection = "authored_proxy"
            collider_source = "package_owned_proxy"
            actions = [
                {
                    "action": "author_static_support_proxy",
                    "prim_path": proxy["prim_path"],
                    "center_xyz": list(proxy["center_xyz"]),
                    "size_xyz": list(proxy["size_xyz"]),
                }
            ]

        material_spec = payload["physics_material"]
        material = UsdShade.Material.Define(stage, material_spec["prim_path"])
        # PhysxSchema Python bindings are only available after the PhysX Kit
        # plugin loads.  AAN's pure package layer therefore authors the schema
        # token and its registered USD attributes directly; runtime admission
        # later proves Isaac 4.1 consumes them.
        material_prim = material.GetPrim()
        material_prim.SetMetadata(
            "apiSchemas",
            Sdf.TokenListOp.Create(
                prependedItems=["PhysicsMaterialAPI", "PhysxMaterialAPI"]
            ),
        )
        material_prim.CreateAttribute(
            "physics:staticFriction", Sdf.ValueTypeNames.Float
        ).Set(material_spec["static_friction"])
        material_prim.CreateAttribute(
            "physics:dynamicFriction", Sdf.ValueTypeNames.Float
        ).Set(material_spec["dynamic_friction"])
        material_prim.CreateAttribute(
            "physics:restitution", Sdf.ValueTypeNames.Float
        ).Set(material_spec["restitution"])
        material_prim.CreateAttribute(
            "physxMaterial:frictionCombineMode", Sdf.ValueTypeNames.Token
        ).Set(material_spec["friction_combine_mode"])
        material_prim.CreateAttribute(
            "physxMaterial:restitutionCombineMode", Sdf.ValueTypeNames.Token
        ).Set(material_spec["restitution_combine_mode"])
        material.GetPrim().SetCustomDataByKey(
            "aan:calibration_status", material_spec["calibration_status"]
        )
        UsdShade.MaterialBindingAPI.Apply(collider).Bind(
            material,
            materialPurpose="physics",
        )
        actions.append(
            {
                "action": "bind_provisional_static_support_material",
                "collider_prim": collider.GetPath().pathString,
                "material_prim": material_spec["prim_path"],
                "calibration_status": material_spec["calibration_status"],
            }
        )
        overlay.Save()
        layout.static_support_profile_json.parent.mkdir(parents=True, exist_ok=True)
        layout.static_support_profile_json.write_bytes(profile_bytes)
        if _sha256(layout.static_support_profile_json) != hashlib.sha256(profile_bytes).hexdigest():
            raise RuntimeError("packaged static support profile bytes changed")
    except Exception as exc:
        return _blocked(f"could not author static support package: {exc}")

    profile_sha = hashlib.sha256(profile_bytes).hexdigest()
    contract = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "status": "pass",
        "profile_id": payload["profile_id"],
        "profile_revision": payload["revision"],
        "asset_entry_prim": payload["asset_entry_prim"],
        "collider_policy": payload["collider_policy"],
        "collider_selection": selection,
        "colliders": [
            {
                "prim_path": collider.GetPath().pathString,
                "collision_enabled": True,
                "source": collider_source,
            }
        ],
        "support_surface": dict(payload["support_surface"]),
        "physics_material": dict(material_spec),
        "profile": {
            "package_path": "static_support/profile.json",
            "sha256": profile_sha,
            "source_usd_sha256": source_sha,
        },
        "overlay_path": "overlays/static_support.usda",
        "guarantees": ["tabletop_support", "tabletop_edge_contact"],
        "non_guarantees": ["leg_collision", "cabinet_collision", "measured_contact_parameters"],
        "consumer_override": {
            "mechanism": "stronger_usd_layer",
            "requirement": "explicitly disable every collider listed in this contract before replacing it",
        },
        "qualification": {
            "status": "pending_runtime",
            "required_probes": [
                "center_drop",
                "north_edge_drop",
                "south_edge_drop",
                "east_edge_drop",
                "west_edge_drop",
                "side_impact",
            ],
        },
    }
    return StaticSupportAuthoringResult("pass", 0, contract, actions, [])


def finalize_static_support_contract(
    layout: TargetPackageLayout,
    result: StaticSupportAuthoringResult,
    runtime_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Bind exact runtime probe evidence into the consumer-facing contract."""
    contract = json.loads(json.dumps(result.contract))
    if contract.get("status") != "pass":
        return contract
    qualification = runtime_evidence.get("static_support_qualification")
    if not isinstance(qualification, dict) or qualification.get("status") not in {
        "pass",
        "blocked",
    }:
        return contract
    layout.static_support_qualification_json.parent.mkdir(parents=True, exist_ok=True)
    layout.static_support_qualification_json.write_text(
        json.dumps(qualification, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    contract["qualification"] = {
        "status": qualification.get("status"),
        "schema_version": qualification.get("schema_version"),
        "report_path": "evidence/static_support/runtime_qualification.json",
        "report_sha256": _sha256(layout.static_support_qualification_json),
        "probe_count": qualification.get("probe_count"),
        "required_probes": [
            "center_drop",
            "north_edge_drop",
            "south_edge_drop",
            "east_edge_drop",
            "west_edge_drop",
            "side_impact",
        ],
    }
    return contract


def _validate_profile(payload: Any, request: NormalizeAssetRequest) -> list[str]:
    if not isinstance(payload, dict):
        return ["profile root must be an object"]
    errors: list[str] = []
    if payload.get("schema_version") != PROFILE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {PROFILE_SCHEMA_VERSION}")
    for name in ("profile_id", "revision", "asset_entry_prim"):
        if not isinstance(payload.get(name), str) or not payload[name]:
            errors.append(f"{name} must be a non-empty string")
    if payload.get("asset_entry_prim") not in request.effective_asset_scope_prims:
        errors.append("asset_entry_prim must equal one declared asset scope")
    if payload.get("collider_policy") != "prefer_source_then_proxy":
        errors.append("collider_policy must be prefer_source_then_proxy")
    source_collider = payload.get("source_collider_prim")
    if source_collider is not None and not _path_under(source_collider, payload.get("asset_entry_prim")):
        errors.append("source_collider_prim must be below asset_entry_prim")
    proxy = payload.get("proxy")
    if not isinstance(proxy, dict):
        errors.append("proxy must be an object")
    else:
        if not _path_under(proxy.get("prim_path"), payload.get("asset_entry_prim")):
            errors.append("proxy.prim_path must be below asset_entry_prim")
        _vec3(errors, proxy.get("center_xyz"), "proxy.center_xyz", positive=False)
        _vec3(errors, proxy.get("size_xyz"), "proxy.size_xyz", positive=True)
    surface = payload.get("support_surface")
    if not isinstance(surface, dict):
        errors.append("support_surface must be an object")
    else:
        _finite(errors, surface.get("top_z"), "support_surface.top_z")
        for name in ("x_range", "y_range"):
            value = surface.get(name)
            if not isinstance(value, list) or len(value) != 2:
                errors.append(f"support_surface.{name} must contain two numbers")
            else:
                _finite(errors, value[0], f"support_surface.{name}[0]")
                _finite(errors, value[1], f"support_surface.{name}[1]")
                try:
                    if float(value[0]) >= float(value[1]):
                        errors.append(f"support_surface.{name} must be increasing")
                except Exception:
                    pass
        _positive(errors, surface.get("edge_band_m"), "support_surface.edge_band_m")
    material = payload.get("physics_material")
    if not isinstance(material, dict):
        errors.append("physics_material must be an object")
    else:
        if not _path_under(material.get("prim_path"), payload.get("asset_entry_prim")):
            errors.append("physics_material.prim_path must be below asset_entry_prim")
        for name in ("static_friction", "dynamic_friction", "restitution"):
            _nonnegative(errors, material.get(name), f"physics_material.{name}")
        if material.get("friction_combine_mode") != "max":
            errors.append("physics_material.friction_combine_mode must be max in v1")
        if material.get("restitution_combine_mode") != "multiply":
            errors.append("physics_material.restitution_combine_mode must be multiply in v1")
        if material.get("calibration_status") != "provisional_unmeasured":
            errors.append("physics_material.calibration_status must be provisional_unmeasured")
    return errors


def _qualified_source_collider(prim: Any) -> bool:
    if not prim or not prim.IsValid() or not prim.IsActive():
        return False
    if "PhysicsCollisionAPI" not in set(prim.GetAppliedSchemas()):
        return False
    attr = prim.GetAttribute("physics:collisionEnabled")
    return not attr or not attr.HasAuthoredValueOpinion() or bool(attr.Get())


def _path_under(path: Any, root: Any) -> bool:
    return (
        isinstance(path, str)
        and isinstance(root, str)
        and path.startswith("/")
        and (path == root or path.startswith(root.rstrip("/") + "/"))
    )


def _finite(errors: list[str], value: Any, name: str) -> None:
    try:
        import math

        if not math.isfinite(float(value)):
            raise ValueError
    except Exception:
        errors.append(f"{name} must be finite")


def _positive(errors: list[str], value: Any, name: str) -> None:
    _finite(errors, value, name)
    try:
        if float(value) <= 0:
            errors.append(f"{name} must be positive")
    except Exception:
        pass


def _nonnegative(errors: list[str], value: Any, name: str) -> None:
    _finite(errors, value, name)
    try:
        if float(value) < 0:
            errors.append(f"{name} must be non-negative")
    except Exception:
        pass


def _vec3(errors: list[str], value: Any, name: str, *, positive: bool) -> None:
    if not isinstance(value, list) or len(value) != 3:
        errors.append(f"{name} must contain three numbers")
        return
    for index, item in enumerate(value):
        (_positive if positive else _finite)(errors, item, f"{name}[{index}]")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _blocked(detail: str) -> StaticSupportAuthoringResult:
    blocker = {
        "blocker_id": "aan05_block_static_support_profile",
        "severity": "blocking",
        "summary": "Static support profile admission did not pass.",
        "detail": detail,
        "required_resolution": "Repair and re-qualify the source-bound profile; do not add a consumer-side collider.",
    }
    return StaticSupportAuthoringResult(
        "blocked",
        5,
        {
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "status": "blocked",
            "reason": detail,
        },
        [],
        [blocker],
    )
