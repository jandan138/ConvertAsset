"""Source-bound dynamic-physics profile admission.

Profiles are intentionally data, not a growing collection of asset-name
conditionals.  They bind explicit SI inertial properties to a source SHA and
its stage frame, and are resolved against every active rigid body under the
declared package scopes before AAN authors anything.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

from .stage_metrics import METRIC_FIELDS, metrics_match, read_stage_metrics, stage_metrics


PROFILE_SCHEMA_VERSION = "aan.physics_profile.v1"
QUALITY_TIERS = {"provisional_geometry", "approved_estimate", "measured"}
MOTION_ROLES = {"dynamic", "kinematic", "fixed_child"}
MASS_MODES = {"explicit", "preserve_authored_mass"}


@dataclass(frozen=True)
class PhysicsProfileResolution:
    """The deterministic admission result used by authoring and static gates."""

    status: str
    profile_admission: dict[str, Any]
    resolved_bodies: list[dict[str, Any]]
    blockers: list[dict[str, Any]]
    profile_payload: dict[str, Any] | None
    profile_bytes: bytes | None


def load_and_resolve_profile(
    profile_path: Path,
    source_usd: Path,
    package_stage: Any,
    scope_prims: list[str],
) -> PhysicsProfileResolution:
    """Load, bind, and completely resolve one profile without USD mutation."""
    profile_bytes: bytes | None = None
    profile_sha: str | None = None
    source_sha = _sha256_file(source_usd) if source_usd.is_file() else None
    profile: dict[str, Any] | None
    parse_error: str | None = None
    try:
        profile_bytes = profile_path.read_bytes()
        profile_sha = hashlib.sha256(profile_bytes).hexdigest()
        raw = json.loads(profile_bytes.decode("utf-8"))
        profile = raw if isinstance(raw, dict) else None
        if profile is None:
            parse_error = "profile JSON root must be an object"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        profile = None
        parse_error = str(exc)

    admission: dict[str, Any] = {
        "status": "blocked",
        "schema_version": profile.get("schema_version") if profile else None,
        "profile_path": str(profile_path),
        "profile_sha256": profile_sha,
        "profile_id": profile.get("profile_id") if profile else None,
        "revision": profile.get("revision") if profile else None,
        "source_binding": profile.get("source_binding") if profile else None,
        "source_sha256": source_sha,
        "matched_scope_rules": [],
        "active_rigid_bodies": [],
        "unmatched_rigid_bodies": [],
        "ambiguous_rigid_bodies": [],
        "invalid_body_rules": [],
        "quality_tier": None,
        "evidence": profile.get("evidence") if profile else None,
        "errors": [],
    }
    blockers: list[dict[str, Any]] = []
    if profile is None:
        admission["errors"].append(f"profile could not be parsed: {parse_error}")
        return _blocked(admission, blockers, profile_bytes=profile_bytes)
    if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        admission["errors"].append(
            f"unsupported profile schema: {profile.get('schema_version')!r}"
        )
    if not isinstance(profile.get("profile_id"), str) or not profile["profile_id"].strip():
        admission["errors"].append("profile_id must be a non-empty string")
    if not isinstance(profile.get("revision"), str) or not profile["revision"].strip():
        admission["errors"].append("revision must be a non-empty string")

    source_metrics = read_stage_metrics(source_usd)
    binding = profile.get("source_binding")
    if not isinstance(binding, dict):
        admission["errors"].append("source_binding must be an object")
    else:
        if binding.get("sha256") != source_sha:
            admission["errors"].append("source_binding.sha256 does not match the input USD")
        expected_metrics = binding.get("stage_metrics")
        if not isinstance(expected_metrics, dict) or source_metrics is None:
            admission["errors"].append("source_binding.stage_metrics could not be verified")
        else:
            metric_ok, metric_mismatches = metrics_match(
                source_metrics,
                expected_metrics,
                fields=METRIC_FIELDS,
            )
            admission["source_metric_mismatches"] = metric_mismatches
            if not metric_ok:
                admission["errors"].append(
                    "source_binding.stage_metrics does not match the input USD"
                )

    scope_rules = profile.get("scope_rules")
    if not isinstance(scope_rules, list) or not scope_rules:
        admission["errors"].append("scope_rules must be a non-empty list")
        scope_rules = []
    selected_rules: dict[str, dict[str, Any]] = {}
    for scope in scope_prims:
        matches = [rule for rule in scope_rules if _scope_rule_matches(rule, scope)]
        if len(matches) != 1:
            admission["errors"].append(
                f"scope {scope} must match exactly one profile scope rule (matched {len(matches)})"
            )
            continue
        selected_rules[scope] = matches[0]
        admission["matched_scope_rules"].append(
            {
                "scope": scope,
                "selector": _scope_selector(matches[0]),
            }
        )

    all_resolved: list[dict[str, Any]] = []
    quality_tiers: set[str] = set()
    for scope in scope_prims:
        rule = selected_rules.get(scope)
        active_paths = _active_rigid_body_paths(package_stage, scope)
        admission["active_rigid_bodies"].extend(active_paths)
        if rule is None:
            admission["unmatched_rigid_bodies"].extend(active_paths)
            continue
        body_rules = rule.get("body_rules")
        if not isinstance(body_rules, list):
            admission["errors"].append(f"scope rule for {scope} has no body_rules list")
            admission["unmatched_rigid_bodies"].extend(active_paths)
            continue
        for prim_path in active_paths:
            relative = _relative_prim_path(scope, prim_path)
            matching_rules = [
                body_rule
                for body_rule in body_rules
                if isinstance(body_rule, dict) and body_rule.get("relative_path") == relative
            ]
            if not matching_rules:
                admission["unmatched_rigid_bodies"].append(prim_path)
                continue
            if len(matching_rules) != 1:
                admission["ambiguous_rigid_bodies"].append(prim_path)
                continue
            body_rule = matching_rules[0]
            errors, mass_properties = _validate_body_rule(
                body_rule,
                package_stage,
                prim_path,
            )
            if errors:
                admission["invalid_body_rules"].append(
                    {
                        "prim_path": prim_path,
                        "relative_path": relative,
                        "errors": errors,
                    }
                )
                continue
            assert mass_properties is not None
            quality_tiers.add(str(mass_properties["quality_tier"]))
            all_resolved.append(
                {
                    "scope": scope,
                    "prim_path": prim_path,
                    "relative_path": relative,
                    "motion_role": body_rule["motion_role"],
                    "clear_density": bool(body_rule.get("clear_density", False)),
                    "mass_properties": mass_properties,
                }
            )

    admission["active_rigid_bodies"] = sorted(set(admission["active_rigid_bodies"]))
    admission["unmatched_rigid_bodies"] = sorted(set(admission["unmatched_rigid_bodies"]))
    admission["ambiguous_rigid_bodies"] = sorted(set(admission["ambiguous_rigid_bodies"]))
    admission["quality_tier"] = (
        next(iter(quality_tiers))
        if len(quality_tiers) == 1
        else "mixed" if quality_tiers else None
    )
    admission["errors"].extend(_validate_profile_evidence(profile.get("evidence"), quality_tiers))
    if not all_resolved and admission["active_rigid_bodies"]:
        admission["errors"].append("profile resolved no usable active rigid-body rules")
    if admission["unmatched_rigid_bodies"]:
        admission["errors"].append("profile does not cover every active rigid body")
    if admission["ambiguous_rigid_bodies"]:
        admission["errors"].append("profile maps one or more rigid bodies more than once")
    if admission["invalid_body_rules"]:
        admission["errors"].append("profile contains invalid mass-property body rules")
    if admission["errors"]:
        return _blocked(
            admission,
            blockers,
            profile_payload=profile,
            profile_bytes=profile_bytes,
        )
    admission["status"] = "pass"
    return PhysicsProfileResolution(
        "pass",
        admission,
        all_resolved,
        [],
        profile,
        profile_bytes,
    )


def _blocked(
    admission: dict[str, Any],
    blockers: list[dict[str, Any]],
    *,
    profile_payload: dict[str, Any] | None = None,
    profile_bytes: bytes | None = None,
) -> PhysicsProfileResolution:
    admission["status"] = "blocked"
    blockers.append(
        {
            "blocker_id": "aan05_block_physics_profile",
            "severity": "blocking",
            "summary": "Dynamic physics profile admission did not establish a complete source-bound mass bundle.",
            "detail": list(admission.get("errors", [])),
            "required_resolution": (
                "Provide a valid source-bound profile covering every active rigid body with explicit "
                "mass/inertia/COM/principal-axes data, or correct the source binding."
            ),
        }
    )
    return PhysicsProfileResolution(
        "blocked",
        admission,
        [],
        blockers,
        profile_payload,
        profile_bytes,
    )


def _scope_rule_matches(rule: Any, scope: str) -> bool:
    if not isinstance(rule, dict):
        return False
    if rule.get("scope_path") == scope:
        return True
    pattern = rule.get("scope_path_regex")
    if not isinstance(pattern, str):
        return False
    try:
        return re.fullmatch(pattern, scope) is not None
    except re.error:
        return False


def _scope_selector(rule: dict[str, Any]) -> dict[str, Any]:
    if isinstance(rule.get("scope_path"), str):
        return {"scope_path": rule["scope_path"]}
    return {"scope_path_regex": rule.get("scope_path_regex")}


def _active_rigid_body_paths(stage: Any, scope: str) -> list[str]:
    root = stage.GetPrimAtPath(scope)
    if not root or not root.IsValid():
        return []
    paths: list[str] = []
    try:
        prims = list(stage.Traverse())
    except Exception:
        prims = []
    prefix = scope.rstrip("/") + "/"
    for prim in prims:
        path = prim.GetPath().pathString
        if path != scope and not path.startswith(prefix):
            continue
        if "PhysicsRigidBodyAPI" not in _schema_tokens(prim):
            continue
        enabled = prim.GetAttribute("physics:rigidBodyEnabled")
        try:
            if enabled and enabled.Get() is False:
                continue
        except Exception:
            pass
        paths.append(path)
    return sorted(paths)


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


def _relative_prim_path(scope: str, path: str) -> str:
    if path == scope:
        return "."
    return path[len(scope.rstrip("/")) + 1 :]


def _validate_body_rule(
    rule: dict[str, Any], stage: Any, prim_path: str,
) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    if rule.get("motion_role") not in MOTION_ROLES:
        errors.append(f"motion_role must be one of {sorted(MOTION_ROLES)}")
    properties = rule.get("mass_properties")
    if not isinstance(properties, dict):
        return [*errors, "mass_properties must be an object"], None
    normalized = dict(properties)
    mode = normalized.get("mode")
    if mode not in MASS_MODES:
        errors.append(f"mass_properties.mode must be one of {sorted(MASS_MODES)}")
    tier = normalized.get("quality_tier")
    if tier not in QUALITY_TIERS:
        errors.append(f"quality_tier must be one of {sorted(QUALITY_TIERS)}")
    if mode == "explicit" and not _positive_finite(normalized.get("mass_kg")):
        errors.append("explicit mass_properties.mass_kg must be positive and finite")
    if mode == "preserve_authored_mass":
        prim = stage.GetPrimAtPath(prim_path)
        mass_attr = prim.GetAttribute("physics:mass") if prim and prim.IsValid() else None
        try:
            authored = bool(mass_attr and mass_attr.HasAuthoredValueOpinion())
            authored_mass_usd = float(mass_attr.Get() if mass_attr else 0.0)
            valid = _positive_finite(authored_mass_usd)
        except Exception:
            authored = False
            valid = False
            authored_mass_usd = 0.0
        if not authored or not valid:
            errors.append("preserve_authored_mass requires an existing positive authored physics:mass")
        declared_mass_kg = normalized.get("authored_mass_kg")
        if not _positive_finite(declared_mass_kg):
            errors.append(
                "preserve_authored_mass requires positive finite authored_mass_kg as the inertia basis"
            )
        else:
            try:
                kilograms_per_unit = float(stage_metrics(stage)["kilograms_per_unit"])
                actual_mass_kg = authored_mass_usd * kilograms_per_unit
                basis_matches = math.isclose(
                    actual_mass_kg,
                    float(declared_mass_kg),
                    rel_tol=1.0e-6,
                    abs_tol=1.0e-9,
                )
            except Exception:
                actual_mass_kg = None
                basis_matches = False
            if not basis_matches:
                errors.append(
                    "authored_mass_kg does not match the current authored physics:mass in the stage frame"
                )
            else:
                normalized["verified_authored_mass_kg"] = actual_mass_kg
    if not _positive_vec3(normalized.get("diagonal_inertia_kg_m2")):
        errors.append("diagonal_inertia_kg_m2 must contain three positive finite values")
    if not _finite_vec(normalized.get("center_of_mass_body_local"), 3):
        errors.append("center_of_mass_body_local must contain three finite body-local USD values")
    if not _unit_quaternion(normalized.get("principal_axes")):
        errors.append("principal_axes must be a finite non-zero unit quaternion [w,x,y,z]")
    return errors, normalized if not errors else None


def _positive_finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0.0
    except (TypeError, ValueError):
        return False


def _finite_vec(value: Any, length: int) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        return False
    try:
        return all(math.isfinite(float(item)) for item in value)
    except (TypeError, ValueError):
        return False


def _positive_vec3(value: Any) -> bool:
    return _finite_vec(value, 3) and all(float(item) > 0.0 for item in value)


def _unit_quaternion(value: Any) -> bool:
    if not _finite_vec(value, 4):
        return False
    length = math.sqrt(sum(float(item) ** 2 for item in value))
    return math.isfinite(length) and math.isclose(length, 1.0, rel_tol=1.0e-5, abs_tol=1.0e-5)


def _validate_profile_evidence(evidence: Any, quality_tiers: set[str]) -> list[str]:
    """Require retained evidence before a profile can claim measured quality.

    A profile remains easy to replace: its values stay in JSON, while this
    contract only asks a higher-confidence revision to name and hash the
    evidence that supports its advertised tier.  ``provisional_geometry``
    still needs a claim boundary and replacement contract so it cannot be
    silently presented as a measurement.
    """
    if not isinstance(evidence, dict):
        return ["evidence must be an object describing the profile quality tier"]
    errors: list[str] = []
    status = evidence.get("parameter_status")
    expected_status = (
        next(iter(quality_tiers))
        if len(quality_tiers) == 1
        else "mixed" if quality_tiers else None
    )
    if status != expected_status:
        errors.append(
            "evidence.parameter_status must match the resolved body quality tier"
        )
    for field in ("claim_boundary", "replacement_contract"):
        if not isinstance(evidence.get(field), str) or not evidence[field].strip():
            errors.append(f"evidence.{field} must be a non-empty string")

    elevated_tiers = quality_tiers & {"approved_estimate", "measured"}
    if not elevated_tiers:
        return errors
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append(
            "evidence.artifacts must be a non-empty list for approved_estimate or measured profiles"
        )
    else:
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"evidence.artifacts[{index}] must be an object")
                continue
            if not isinstance(artifact.get("kind"), str) or not artifact["kind"].strip():
                errors.append(f"evidence.artifacts[{index}].kind must be a non-empty string")
            if not isinstance(artifact.get("uri"), str) or not artifact["uri"].strip():
                errors.append(f"evidence.artifacts[{index}].uri must be a non-empty string")
            digest = artifact.get("sha256")
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
                errors.append(f"evidence.artifacts[{index}].sha256 must be a SHA-256 hex digest")
    if "approved_estimate" in elevated_tiers:
        review = evidence.get("review")
        if not isinstance(review, dict) or not all(
            isinstance(review.get(field), str) and review[field].strip()
            for field in ("approved_by", "reviewed_at")
        ):
            errors.append(
                "evidence.review must include approved_by and reviewed_at for approved_estimate"
            )
    if "measured" in elevated_tiers:
        measurement = evidence.get("measurement")
        if not isinstance(measurement, dict) or not all(
            isinstance(measurement.get(field), str) and measurement[field].strip()
            for field in ("method", "recorded_at")
        ):
            errors.append(
                "evidence.measurement must include method and recorded_at for measured profiles"
            )
    return errors


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
