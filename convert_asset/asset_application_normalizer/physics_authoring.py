"""Author a validated dynamic-physics profile into a package-owned overlay."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .model import NormalizeAssetRequest
from .package_layout import TargetPackageLayout
from .physics_profile import PhysicsProfileResolution, load_and_resolve_profile
from .stage_metrics import stage_metrics


PROVENANCE_CUSTOM_KEY = "aan:provenance"
PROFILE_PRIM_CUSTOM_KEY = "aan:physics_profile"


@dataclass(frozen=True)
class PhysicsProfileAuthoringResult:
    overall_status: str
    return_code: int
    profile_admission: dict[str, Any]
    normalization_actions: list[dict[str, Any]]
    blocked_reasons: list[dict[str, Any]]


def apply_physics_profile(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
) -> PhysicsProfileAuthoringResult:
    """Resolve a profile then write its full mass bundle to the owned overlay.

    Nothing is authored if binding or coverage is incomplete.  In particular,
    an existing valid mass plus missing inertia retains that authored mass as
    the inertia basis; this avoids a hidden switch back to template mass.
    """
    if request.physics_profile is None:
        return PhysicsProfileAuthoringResult(
            "not_applicable",
            0,
            {"status": "not_applicable", "reason": "no physics profile requested"},
            [],
            [],
        )
    try:
        from pxr import Sdf, Usd, UsdPhysics  # type: ignore

        stage = Usd.Stage.Open(str(layout.root_usd))
        if stage is None:
            raise RuntimeError(f"could not open package USD: {layout.root_usd}")
    except Exception as exc:
        blocker = {
            "blocker_id": "aan05_block_physics_profile",
            "severity": "blocking",
            "summary": "Dynamic physics profile could not open the package stage.",
            "detail": str(exc),
        }
        return PhysicsProfileAuthoringResult(
            "blocked",
            5,
            {"status": "blocked", "reason": str(exc)},
            [],
            [blocker],
        )

    resolution = load_and_resolve_profile(
        request.physics_profile,
        request.source_usd,
        stage,
        request.effective_asset_scope_prims,
    )
    if resolution.status != "pass":
        return PhysicsProfileAuthoringResult(
            "blocked",
            5,
            resolution.profile_admission,
            [],
            resolution.blockers,
        )

    try:
        profile_bytes = resolution.profile_bytes
        expected_profile_sha = resolution.profile_admission.get("profile_sha256")
        if profile_bytes is None or not isinstance(resolution.profile_payload, dict):
            raise RuntimeError("admitted profile did not retain immutable source bytes and JSON payload")
        packaged_profile_sha = hashlib.sha256(profile_bytes).hexdigest()
        if packaged_profile_sha != expected_profile_sha:
            raise RuntimeError("admitted profile byte hash does not match profile admission")
        overlay = Sdf.Layer.FindOrOpen(str(layout.physics_overlay_usd))
        if overlay is None:
            raise RuntimeError(f"could not open physics overlay: {layout.physics_overlay_usd}")
        stage.SetEditTarget(Usd.EditTarget(overlay))
        frame = stage_metrics(stage)
        kilograms_per_unit = float(frame["kilograms_per_unit"])
        meters_per_unit = float(frame["meters_per_unit"])
        if kilograms_per_unit <= 0.0 or meters_per_unit <= 0.0:
            raise RuntimeError("package stage has non-positive physical units")
        actions = [
            _author_body_bundle(
                stage,
                body,
                profile_admission=resolution.profile_admission,
                kilograms_per_unit=kilograms_per_unit,
                meters_per_unit=meters_per_unit,
                usd_physics=UsdPhysics,
            )
            for body in resolution.resolved_bodies
        ]
        overlay.Save()
        _write_admitted_profile_copy(
            layout.physics_profile_json,
            profile_bytes,
            expected_sha256=packaged_profile_sha,
        )
    except Exception as exc:
        blocker = {
            "blocker_id": "aan05_block_physics_profile_authoring",
            "severity": "blocking",
            "summary": "AAN could not author the admitted physics profile into its owned overlay.",
            "detail": str(exc),
            "required_resolution": "Fix the package-local physics overlay or the profile data; do not patch the source USD.",
        }
        admission = dict(resolution.profile_admission)
        admission.update({"status": "blocked", "authoring_error": str(exc)})
        return PhysicsProfileAuthoringResult("blocked", 5, admission, [], [blocker])

    admission = dict(resolution.profile_admission)
    admission.update(
        {
            "status": "pass",
            "package_profile_path": "physics/profile.json",
            "overlay_path": "overlays/physics_profile.usda",
            "packaged_profile_sha256": packaged_profile_sha,
            "resolved_body_count": len(actions),
            "authoring_frame": {
                "meters_per_unit": meters_per_unit,
                "kilograms_per_unit": kilograms_per_unit,
                "inertia_conversion": "I_usd = I_kg_m2 / (kilogramsPerUnit * metersPerUnit^2)",
                "center_of_mass_frame": "body_local_usd",
            },
        }
    )
    return PhysicsProfileAuthoringResult("pass", 0, admission, actions, [])


def _author_body_bundle(
    stage: Any,
    body: dict[str, Any],
    *,
    profile_admission: dict[str, Any],
    kilograms_per_unit: float,
    meters_per_unit: float,
    usd_physics: Any,
) -> dict[str, Any]:
    from pxr import Gf  # type: ignore

    prim = stage.GetPrimAtPath(body["prim_path"])
    if not prim or not prim.IsValid():
        raise RuntimeError(f"profiled rigid body disappeared: {body['prim_path']}")
    mass_api = usd_physics.MassAPI.Apply(prim)
    rigid_api = usd_physics.RigidBodyAPI.Apply(prim)
    properties = body["mass_properties"]
    mode = properties["mode"]
    quality_tier = properties["quality_tier"]
    mass_attr = prim.GetAttribute("physics:mass")
    if mode == "explicit":
        mass_si = float(properties["mass_kg"])
        mass_usd = mass_si / kilograms_per_unit
        mass_attr = mass_api.CreateMassAttr(mass_usd)
        mass_attr.Set(mass_usd)
        _set_profile_provenance(
            mass_attr,
            field="mass",
            body=body,
            profile_admission=profile_admission,
            quality_tier=quality_tier,
            si_value=mass_si,
            mass_basis={
                "attribute": f"{body['prim_path']}.physics:mass",
                "source": "profile",
                "value": mass_usd,
            },
        )
        mass_basis = {
            "attribute": f"{body['prim_path']}.physics:mass",
            "source": "profile",
            "value": mass_usd,
        }
    else:
        try:
            mass_usd = float(mass_attr.Get())
        except Exception as exc:
            raise RuntimeError(f"could not read preserved authored mass for {body['prim_path']}: {exc}")
        mass_si = mass_usd * kilograms_per_unit
        mass_basis = {
            "attribute": f"{body['prim_path']}.physics:mass",
            "source": "authored",
            "value": mass_usd,
            "value_kg": mass_si,
            "profile_declared_kg": float(properties["authored_mass_kg"]),
            "profile_verified_kg": float(properties["verified_authored_mass_kg"]),
        }

    inertia_si = [float(value) for value in properties["diagonal_inertia_kg_m2"]]
    inertia_usd = [
        value / (kilograms_per_unit * meters_per_unit**2)
        for value in inertia_si
    ]
    inertia_attr = mass_api.CreateDiagonalInertiaAttr(
        Gf.Vec3f(*[float(value) for value in inertia_usd])
    )
    inertia_attr.Set(Gf.Vec3f(*[float(value) for value in inertia_usd]))
    _set_profile_provenance(
        inertia_attr,
        field="inertia",
        body=body,
        profile_admission=profile_admission,
        quality_tier=quality_tier,
        si_value=inertia_si,
        mass_basis=mass_basis,
    )

    center = [float(value) for value in properties["center_of_mass_body_local"]]
    center_attr = mass_api.CreateCenterOfMassAttr(Gf.Vec3f(*center))
    center_attr.Set(Gf.Vec3f(*center))
    _set_profile_provenance(
        center_attr,
        field="center_of_mass",
        body=body,
        profile_admission=profile_admission,
        quality_tier=quality_tier,
        si_value=None,
        mass_basis=None,
        frame="body_local_usd",
    )

    axes = [float(value) for value in properties["principal_axes"]]
    axes_value = Gf.Quatf(axes[0], Gf.Vec3f(axes[1], axes[2], axes[3]))
    axes_attr = mass_api.CreatePrincipalAxesAttr(axes_value)
    axes_attr.Set(axes_value)
    _set_profile_provenance(
        axes_attr,
        field="principal_axes",
        body=body,
        profile_admission=profile_admission,
        quality_tier=quality_tier,
        si_value=None,
        mass_basis=None,
        frame="body_local_usd",
    )

    if body.get("clear_density"):
        density_attr = mass_api.CreateDensityAttr(0.0)
        density_attr.Set(0.0)
    kinematic_attr = rigid_api.CreateKinematicEnabledAttr(
        body["motion_role"] == "kinematic"
    )
    kinematic_attr.Set(body["motion_role"] == "kinematic")
    prim.SetCustomDataByKey(
        PROFILE_PRIM_CUSTOM_KEY,
        json.dumps(
            {
                "profile_id": profile_admission["profile_id"],
                "revision": profile_admission["revision"],
                "profile_sha256": profile_admission["profile_sha256"],
                "motion_role": body["motion_role"],
                "quality_tier": quality_tier,
                "mass_mode": mode,
                "source_sha256": profile_admission["source_sha256"],
            },
            sort_keys=True,
        ),
    )
    return {
        "action": "author_physics_profile_bundle",
        "prim_path": body["prim_path"],
        "relative_path": body["relative_path"],
        "motion_role": body["motion_role"],
        "mass_mode": mode,
        "quality_tier": quality_tier,
        "mass_kg": mass_si,
        "mass_usd": mass_usd,
        "diagonal_inertia_kg_m2": inertia_si,
        "diagonal_inertia_usd": inertia_usd,
        "center_of_mass_frame": "body_local_usd",
        "density_cleared": bool(body.get("clear_density")),
    }


def _set_profile_provenance(
    attr: Any,
    *,
    field: str,
    body: dict[str, Any],
    profile_admission: dict[str, Any],
    quality_tier: str,
    si_value: Any,
    mass_basis: dict[str, Any] | None,
    frame: str = "SI",
) -> None:
    payload: dict[str, Any] = {
        "value_source": "profile",
        "method": "aan_physics_profile_v1",
        "field": field,
        "input_artifacts": [
            "physics/profile.json",
            f"source_sha256:{profile_admission['source_sha256']}",
        ],
        "package_authored": True,
        "profile_id": profile_admission["profile_id"],
        "profile_revision": profile_admission["revision"],
        "profile_sha256": profile_admission["profile_sha256"],
        "source_sha256": profile_admission["source_sha256"],
        "quality_tier": quality_tier,
        "motion_role": body["motion_role"],
        "frame": frame,
    }
    if si_value is not None:
        payload["si_value"] = si_value
    if mass_basis is not None:
        payload["mass_basis"] = mass_basis
    attr.SetCustomDataByKey(PROVENANCE_CUSTOM_KEY, json.dumps(payload, sort_keys=True))


def _write_admitted_profile_copy(
    destination: Path,
    profile_bytes: bytes,
    *,
    expected_sha256: str,
) -> None:
    """Persist exactly the bytes that profile admission hashed and resolved."""
    if hashlib.sha256(profile_bytes).hexdigest() != expected_sha256:
        raise RuntimeError("profile bytes changed before package copy could be written")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(profile_bytes)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected_sha256:
            raise RuntimeError("package profile copy hash does not match admitted profile")
        os.replace(temporary, destination)
        if hashlib.sha256(destination.read_bytes()).hexdigest() != expected_sha256:
            raise RuntimeError("package profile copy changed after atomic write")
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
