"""Compile an admitted object interaction profile into package-owned USD."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .model import NormalizeAssetRequest
from .object_interaction_profile import load_and_resolve_interaction_profile
from .package_layout import TargetPackageLayout


CONTRACT_SCHEMA_VERSION = "aan.interaction_contract.v1"
PROFILE_PACKAGE_PATH = "interaction/profile.json"
OVERLAY_PACKAGE_PATH = "overlays/interaction.usda"
RUNTIME_ARTIFACT_ROOTS = ("deps/", "interaction/", "overlays/", "physics/")


@dataclass(frozen=True)
class InteractionAuthoringResult:
    """Interaction authoring status, actions, and consumer contract."""

    overall_status: str
    return_code: int
    interaction_contract: dict[str, Any]
    normalization_actions: list[dict[str, Any]]
    blocked_reasons: list[dict[str, Any]]


def build_not_requested_interaction_authoring() -> InteractionAuthoringResult:
    """Return the compatibility result for packages without this optional profile."""
    return InteractionAuthoringResult(
        overall_status="not_requested",
        return_code=0,
        interaction_contract={
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "status": "not_requested",
        },
        normalization_actions=[],
        blocked_reasons=[],
    )


def build_not_run_interaction_authoring(reason: str) -> InteractionAuthoringResult:
    """Return a non-successful stage record after an earlier gate blocks."""
    return InteractionAuthoringResult(
        overall_status="not_run",
        return_code=0,
        interaction_contract={
            "schema_version": CONTRACT_SCHEMA_VERSION,
            "status": "not_run",
            "reason": reason,
        },
        normalization_actions=[],
        blocked_reasons=[],
    )


def apply_object_interaction_profile(
    layout: TargetPackageLayout,
    request: NormalizeAssetRequest,
) -> InteractionAuthoringResult:
    """Normalize rigid identity and frames before mass-profile resolution."""
    if request.interaction_profile is None:
        return build_not_requested_interaction_authoring()
    try:
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics  # type: ignore

        stage = Usd.Stage.Open(str(layout.root_usd))
        if stage is None:
            raise RuntimeError(f"could not open package USD: {layout.root_usd}")
    except Exception as exc:
        return _authoring_blocked(
            "Object interaction authoring could not open the package stage.", str(exc)
        )

    resolution = load_and_resolve_interaction_profile(
        request.interaction_profile,
        request.source_usd,
        stage,
        request.effective_asset_scope_prims,
    )
    if resolution.status != "pass" or resolution.resolved is None:
        return InteractionAuthoringResult(
            overall_status="blocked",
            return_code=5,
            interaction_contract={
                "schema_version": CONTRACT_SCHEMA_VERSION,
                "status": "blocked",
                "profile_admission": resolution.profile_admission,
            },
            normalization_actions=[],
            blocked_reasons=resolution.blockers,
        )

    resolved = resolution.resolved
    actions: list[dict[str, Any]] = []
    disabled_records: list[dict[str, Any]] = []
    try:
        overlay = Sdf.Layer.FindOrOpen(str(layout.interaction_overlay_usd))
        if overlay is None:
            raise RuntimeError(
                f"could not open interaction overlay: {layout.interaction_overlay_usd}"
            )
        stage.SetEditTarget(Usd.EditTarget(overlay))
        root_path = str(resolved["asset_entry_prim"])
        root = stage.GetPrimAtPath(root_path)
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(root)
        rigid_api.CreateRigidBodyEnabledAttr(True).Set(True)
        rigid_api.CreateKinematicEnabledAttr(
            resolved["motion_role"] == "kinematic"
        ).Set(resolved["motion_role"] == "kinematic")
        actions.append(
            {
                "action": "author_unique_rigid_root",
                "prim_path": root_path,
                "motion_role": resolved["motion_role"],
            }
        )

        mass_paths = set(resolved["descendant_mass_prims"])
        for prim_path in sorted(set(resolved["source_rigid_bodies"]) - {root_path}):
            prim = stage.GetPrimAtPath(prim_path)
            removed = ["PhysicsRigidBodyAPI"]
            if prim_path in mass_paths:
                removed.append("PhysicsMassAPI")
            _delete_api_schemas(prim, removed, Sdf)
            prim.CreateAttribute(
                "physics:rigidBodyEnabled", Sdf.ValueTypeNames.Bool
            ).Set(False)
            record = {
                "prim_path": prim_path,
                "rigid_body_api_removed": True,
                "rigid_body_disabled": True,
                "mass_api_removed": prim_path in mass_paths,
            }
            disabled_records.append(record)
            actions.append({"action": "disable_descendant_rigid_body", **record})

        # A source can contain MassAPI without an active rigid-body API.  It is
        # still removed so the root owns the only mass bundle after the next
        # pipeline stage.
        for prim_path in sorted(mass_paths - set(resolved["source_rigid_bodies"])):
            prim = stage.GetPrimAtPath(prim_path)
            _delete_api_schemas(prim, ["PhysicsMassAPI"], Sdf)
            actions.append(
                {
                    "action": "remove_descendant_mass_api",
                    "prim_path": prim_path,
                    "mass_api_removed": True,
                }
            )

        collider_records: list[dict[str, Any]] = []
        for collider in resolved["colliders"]:
            prim = stage.GetPrimAtPath(collider["prim_path"])
            if collider.get("geometry") is not None:
                prim = _define_package_collider_geometry(
                    stage,
                    collider["prim_path"],
                    collider["geometry"],
                    UsdGeom,
                    Gf,
                )
                actions.append(
                    {
                        "action": "author_package_collider_geometry",
                        "prim_path": collider["prim_path"],
                        "geometry": dict(collider["geometry"]),
                    }
                )
            if collider["mode"] == "author":
                collision_api = UsdPhysics.CollisionAPI.Apply(prim)
                collision_api.CreateCollisionEnabledAttr(True).Set(True)
                actions.append(
                    {
                        "action": "author_collision_api",
                        "prim_path": collider["prim_path"],
                    }
                )
            elif collider["mode"] == "disable":
                collision_api = UsdPhysics.CollisionAPI(prim)
                collision_api.CreateCollisionEnabledAttr(False).Set(False)
                actions.append(
                    {
                        "action": "disable_source_collision_prim",
                        "prim_path": collider["prim_path"],
                    }
                )
            if collider.get("approximation") is not None:
                mesh_collision = UsdPhysics.MeshCollisionAPI.Apply(prim)
                mesh_collision.CreateApproximationAttr(collider["approximation"]).Set(
                    collider["approximation"]
                )
                actions.append(
                    {
                        "action": "author_mesh_collision_approximation",
                        "prim_path": collider["prim_path"],
                        "approximation": collider["approximation"],
                    }
                )
            collider_records.append(
                {
                    "prim_path": collider["prim_path"],
                    "mode": collider["mode"],
                    "collision_enabled": collider["mode"] != "disable",
                    "purpose": list(collider["purpose"]),
                    "requested_approximation": collider.get("approximation"),
                    "observed_approximation": None,
                }
            )

        named_frames: dict[str, dict[str, Any]] = {}
        for name, frame in sorted(resolved["named_frames"].items()):
            frame_xform = UsdGeom.Xform.Define(stage, frame["prim_path"])
            translate = [float(item) for item in frame["translation_body_local_usd"]]
            rotation = [float(item) for item in frame["rotation_body_local_wxyz"]]
            frame_xform.AddTranslateOp().Set(Gf.Vec3d(*translate))
            frame_xform.AddOrientOp().Set(
                Gf.Quatf(rotation[0], Gf.Vec3f(rotation[1], rotation[2], rotation[3]))
            )
            named_frames[name] = {
                "prim_path": frame["prim_path"],
                "parent_prim": root_path,
                "translation_body_local_usd": translate,
                "rotation_body_local_wxyz": rotation,
                "authoritative": True,
            }
            actions.append(
                {
                    "action": "author_named_interaction_frame",
                    "name": name,
                    "prim_path": frame["prim_path"],
                }
            )
        overlay.Save()

        profile_bytes = resolution.profile_bytes
        profile_sha = resolution.profile_admission.get("profile_sha256")
        if profile_bytes is None or not isinstance(profile_sha, str):
            raise RuntimeError(
                "admitted interaction profile bytes or digest are missing"
            )
        _write_immutable_copy(
            layout.interaction_profile_json,
            profile_bytes,
            expected_sha256=profile_sha,
        )

        output_stage = Usd.Stage.Open(str(layout.root_usd))
        if output_stage is None:
            raise RuntimeError("could not reopen package after interaction authoring")
        active_rigid = _active_rigid_body_paths(output_stage, root_path)
        if active_rigid != [root_path]:
            raise RuntimeError(
                f"interaction overlay did not produce exactly one active rigid root: {active_rigid}"
            )
        reference_stage = Usd.Stage.CreateInMemory()
        reference_probe_path = Sdf.Path("/__aan_interaction_reference_probe")
        reference_probe = reference_stage.DefinePrim(reference_probe_path, "Xform")
        if not reference_probe.GetReferences().AddReference(
            str(layout.root_usd.resolve()),
            root_path,
        ):
            raise RuntimeError("could not author interaction entry reference probe")
        referenced_rigid = _active_rigid_body_paths(
            reference_stage,
            reference_probe_path.pathString,
        )
        if referenced_rigid != [reference_probe_path.pathString]:
            raise RuntimeError(
                "interaction entry reference did not preserve the unique rigid root: "
                f"{referenced_rigid}"
            )
        actions.append(
            {
                "action": "qualify_asset_entry_reference",
                "asset_entry_prim": root_path,
                "probe_prim": reference_probe_path.pathString,
                "observed_active_rigid_body_prims": referenced_rigid,
                "status": "pass",
            }
        )
        for record in disabled_records:
            prim = output_stage.GetPrimAtPath(record["prim_path"])
            schemas = set(str(item) for item in prim.GetAppliedSchemas())
            if "PhysicsRigidBodyAPI" in schemas:
                raise RuntimeError(
                    f"descendant RigidBodyAPI remains active: {record['prim_path']}"
                )
            if record["mass_api_removed"] and "PhysicsMassAPI" in schemas:
                raise RuntimeError(
                    f"descendant MassAPI remains active: {record['prim_path']}"
                )
        for prim_path in sorted(mass_paths):
            prim = output_stage.GetPrimAtPath(prim_path)
            if "PhysicsMassAPI" in set(str(item) for item in prim.GetAppliedSchemas()):
                raise RuntimeError(f"descendant MassAPI remains active: {prim_path}")
        for collider in collider_records:
            prim = output_stage.GetPrimAtPath(collider["prim_path"])
            if "PhysicsCollisionAPI" not in set(
                str(item) for item in prim.GetAppliedSchemas()
            ):
                raise RuntimeError(
                    f"declared collider is missing after authoring: {collider['prim_path']}"
                )
            enabled_attr = prim.GetAttribute("physics:collisionEnabled")
            observed_enabled = enabled_attr.Get() if enabled_attr else True
            if bool(observed_enabled) != collider["collision_enabled"]:
                raise RuntimeError(
                    f"collider enabled readback mismatch at {collider['prim_path']}: "
                    f"{observed_enabled!r}"
                )
            approximation_attr = prim.GetAttribute("physics:approximation")
            approximation = approximation_attr.Get() if approximation_attr else None
            collider["observed_approximation"] = (
                str(approximation) if approximation is not None else None
            )
            if (
                collider["requested_approximation"] is not None
                and collider["observed_approximation"]
                != collider["requested_approximation"]
            ):
                raise RuntimeError(
                    f"collider approximation readback mismatch at {collider['prim_path']}: "
                    f"{collider['observed_approximation']!r}"
                )
    except Exception as exc:
        return _authoring_blocked(
            "AAN could not author the admitted object interaction profile into its owned overlay.",
            str(exc),
            profile_admission=resolution.profile_admission,
            actions=actions,
        )

    contract: dict[str, Any] = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "status": "pass",
        "profile": {
            "schema_version": resolution.profile_admission["schema_version"],
            "profile_id": resolution.profile_admission["profile_id"],
            "revision": resolution.profile_admission["revision"],
            "source_sha256": resolution.profile_admission["source_sha256"],
            "profile_sha256": resolution.profile_admission["profile_sha256"],
            "package_path": PROFILE_PACKAGE_PATH,
            "overlay_path": OVERLAY_PACKAGE_PATH,
        },
        "asset_entry_prim": root_path,
        "runtime_identity": {
            "rigid_root_prim": root_path,
            "exactly_one_active_rigid_body": True,
            "active_rigid_body_prims": active_rigid,
        },
        "disabled_source_rigid_bodies": disabled_records,
        "collider_prims": sorted(collider_records, key=lambda item: item["prim_path"]),
        "open_top": dict(resolved["open_top"]),
        "named_frames": named_frames,
        "closure": {"status": "pending_finalize"},
        "root_motion_gate": _runtime_gate_placeholder(
            resolved["runtime_gates"].get("root_motion", {})
        ),
        "stable_support_gate": _runtime_gate_placeholder(
            resolved["runtime_gates"].get("stable_support", {})
        ),
        "gripper_collision_gate": _runtime_gate_placeholder(
            resolved["runtime_gates"].get("gripper_collision", {})
        ),
    }
    return InteractionAuthoringResult(
        overall_status="pass",
        return_code=0,
        interaction_contract=finalize_interaction_contract(layout, contract),
        normalization_actions=actions,
        blocked_reasons=[],
    )


def _define_package_collider_geometry(
    stage: Any,
    prim_path: str,
    geometry: dict[str, Any],
    usd_geom: Any,
    gf: Any,
) -> Any:
    parent_path = prim_path.rsplit("/", 1)[0]
    usd_geom.Xform.Define(stage, parent_path)
    if geometry["type"] != "Cube":
        raise RuntimeError(f"unsupported package collider geometry: {geometry['type']}")
    cube = usd_geom.Cube.Define(stage, prim_path)
    cube.CreateVisibilityAttr(usd_geom.Tokens.invisible).Set(
        usd_geom.Tokens.invisible
    )
    cube.CreateSizeAttr(float(geometry["size"]))
    translation = geometry["translation_body_local_usd"]
    rotation = geometry["rotation_body_local_wxyz"]
    scale = geometry["scale_body_local_usd"]
    cube.AddTranslateOp().Set(gf.Vec3d(*translation))
    cube.AddOrientOp().Set(
        gf.Quatf(rotation[0], gf.Vec3f(rotation[1], rotation[2], rotation[3]))
    )
    cube.AddScaleOp().Set(gf.Vec3d(*scale))
    return cube.GetPrim()


def finalize_interaction_contract(
    layout: TargetPackageLayout,
    interaction_contract: dict[str, Any],
) -> dict[str, Any]:
    """Hash the contract payload and final package runtime tree.

    The manifest is intentionally excluded, avoiding a self-referential hash.
    Calling this after physics-profile authoring updates the same contract with
    the final mass profile and overlay bytes.
    """
    if interaction_contract.get("status") != "pass":
        return interaction_contract
    contract = dict(interaction_contract)
    payload = {
        key: contract[key]
        for key in (
            "schema_version",
            "asset_entry_prim",
            "runtime_identity",
            "disabled_source_rigid_bodies",
            "collider_prims",
            "open_top",
            "named_frames",
        )
    }
    payload_digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
    artifacts = _runtime_artifacts(layout.root)
    tree_digest = hashlib.sha256(_canonical_json(artifacts)).hexdigest()
    contract["closure"] = {
        "status": "pass",
        "digest_algorithm": "sha256",
        "contract_encoding": "canonical_json_interaction_payload_v1",
        "contract_payload_sha256": payload_digest,
        "tree_encoding": "canonical_json_artifact_list_v1",
        "runtime_tree_sha256": tree_digest,
        "artifacts": artifacts,
    }
    return contract


def _runtime_artifacts(package_root: Path) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for path in package_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(package_root).as_posix()
        if relative != "asset.usd" and not relative.startswith(RUNTIME_ARTIFACT_ROOTS):
            continue
        artifacts.append({"path": relative, "sha256": _sha256_file(path)})
    return sorted(artifacts, key=lambda item: item["path"])


def _runtime_gate_placeholder(requirement: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "not_run",
        **requirement,
        "evidence": {
            "status": "not_run",
            "observations": [],
        },
    }


def _delete_api_schemas(prim: Any, schemas: list[str], sdf: Any) -> None:
    if not schemas:
        return
    existing = prim.GetMetadata("apiSchemas")
    deleted = set(getattr(existing, "deletedItems", []))
    deleted.update(schemas)
    prim.SetMetadata(
        "apiSchemas",
        sdf.TokenListOp.Create(deletedItems=sorted(deleted)),
    )


def _active_rigid_body_paths(stage: Any, root: str) -> list[str]:
    prefix = root.rstrip("/") + "/"
    result: list[str] = []
    try:
        prims = list(stage.TraverseAll())
    except Exception:
        prims = list(stage.Traverse())
    for prim in prims:
        path = prim.GetPath().pathString
        if path != root and not path.startswith(prefix):
            continue
        if "PhysicsRigidBodyAPI" not in set(
            str(item) for item in prim.GetAppliedSchemas()
        ):
            continue
        enabled = prim.GetAttribute("physics:rigidBodyEnabled")
        try:
            if enabled and enabled.Get() is False:
                continue
        except Exception:
            pass
        result.append(path)
    return sorted(result)


def _write_immutable_copy(
    destination: Path, payload: bytes, *, expected_sha256: str
) -> None:
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise RuntimeError("interaction profile bytes changed before package copy")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(payload)
        if _sha256_file(temporary) != expected_sha256:
            raise RuntimeError("temporary interaction profile copy hash mismatch")
        os.replace(temporary, destination)
        if _sha256_file(destination) != expected_sha256:
            raise RuntimeError("packaged interaction profile hash mismatch")
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _authoring_blocked(
    summary: str,
    detail: str,
    *,
    profile_admission: dict[str, Any] | None = None,
    actions: list[dict[str, Any]] | None = None,
) -> InteractionAuthoringResult:
    blocker = {
        "blocker_id": "aan05i_block_interaction_authoring",
        "severity": "blocking",
        "summary": summary,
        "detail": detail,
        "required_resolution": "Fix the source-bound profile or package overlay; do not patch the immutable source USD.",
    }
    contract: dict[str, Any] = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "status": "blocked",
        "authoring_error": detail,
    }
    if profile_admission is not None:
        contract["profile_admission"] = profile_admission
    return InteractionAuthoringResult(
        overall_status="blocked",
        return_code=5,
        interaction_contract=contract,
        normalization_actions=actions or [],
        blocked_reasons=[blocker],
    )


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
