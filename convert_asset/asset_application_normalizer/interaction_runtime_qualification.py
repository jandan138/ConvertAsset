"""Isaac Sim runtime qualification for package-owned interaction contracts.

The host adapter in this module is intentionally narrower than an episode
runner.  It binds one immutable package closure to one isolated Isaac worker,
collects four object-level probes, and projects each result only onto its
corresponding interaction gate.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
import uuid

from .interaction_authoring import _runtime_artifacts
from .runtime_smoke import (
    _close_simulation_app_with_report,
    _prepare_isolated_worker_exit,
    _runtime_environment,
    _runtime_profile_gate,
    _scoped_rigid_body_paths,
    _stage_loading_complete,
    runtime_subprocess_environment,
)


REPORT_SCHEMA_VERSION = "aan.interaction_runtime_qualification_report.v1"

APERTURE_NOT_QUALIFIED_CLAIM = (
    "The declared open-top collider has passed a runtime aperture probe."
)
ROOT_MOTION_NOT_QUALIFIED_CLAIM = (
    "The interaction rigid root has passed the required runtime motion probe."
)
SUPPORT_AND_GRIPPER_NOT_QUALIFIED_CLAIM = (
    "Stable support and gripper collision have passed runtime probes."
)

SUPPORT_HEIGHT_TOLERANCE_M = 0.01
SUPPORT_LINEAR_SPEED_LIMIT_M_S = 0.05
SUPPORT_ANGULAR_SPEED_LIMIT_RAD_S = 0.5
SUPPORT_TILT_LIMIT_DEG = 10.0
SUPPORT_LATERAL_DRIFT_LIMIT_M = 0.03
ROOT_POSITION_PARITY_TOLERANCE_M = 0.001
ROOT_ORIENTATION_PARITY_TOLERANCE_DEG = 0.5


@dataclass(frozen=True)
class InteractionRuntimeQualificationResult:
    """Host-side result and updated interaction contract."""

    overall_status: str
    return_code: int
    interaction_contract: dict[str, Any]
    runtime_evidence: dict[str, Any]
    blocked_reasons: list[dict[str, Any]]
    extra_commands: dict[str, Any] = field(default_factory=dict)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_runtime_package_closure(
    package_root: Path,
    interaction_contract: dict[str, Any],
) -> dict[str, Any]:
    """Recompute the static runtime tree before launching Isaac Sim.

    ``evidence/**`` is not one of the owned runtime artifact roots, so repeated
    qualification cannot alter the closure it is qualifying.
    """
    errors: list[str] = []
    closure = interaction_contract.get("closure")
    if not isinstance(closure, dict) or closure.get("status") != "pass":
        errors.append("interaction contract has no passing static closure")
        closure = {}
    observed_artifacts = _runtime_artifacts(package_root)
    observed_tree_digest = hashlib.sha256(
        _canonical_json(observed_artifacts)
    ).hexdigest()
    if closure.get("artifacts") != observed_artifacts:
        errors.append("runtime artifact list differs from the bound closure")
    if closure.get("runtime_tree_sha256") != observed_tree_digest:
        errors.append("runtime tree digest differs from the bound closure")
    if isinstance(interaction_contract.get("open_top"), dict):
        observed_payload_digest = _interaction_payload_sha256(interaction_contract)
        if closure.get("contract_payload_sha256") != observed_payload_digest:
            errors.append("interaction contract payload digest differs from the bound closure")
    else:
        observed_payload_digest = None
    return {
        "status": "pass" if not errors else "blocked",
        "errors": errors,
        "runtime_tree_sha256": observed_tree_digest,
        "contract_payload_sha256": observed_payload_digest,
        "artifact_count": len(observed_artifacts),
    }


def _number(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return math.nan
    return result if math.isfinite(result) else math.nan


def _probe_result(observation: Any, errors: list[str]) -> dict[str, Any]:
    return {
        "status": "pass" if not errors else "blocked",
        "errors": errors,
        "observations": observation if isinstance(observation, dict) else {},
    }


def evaluate_probe_observations(
    observations: dict[str, Any],
    *,
    root_motion_requirement: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Apply stable, simulator-neutral acceptance thresholds to worker facts."""
    aperture = observations.get("cooked_aperture", {})
    aperture_errors: list[str] = []
    vessel_height = _number(aperture.get("vessel_height_m"))
    bottom_depth = _number(aperture.get("bottom_depth_m"))
    radius = _number(aperture.get("probe_radius_m"))
    side_hits = aperture.get("side_hits", {})
    if aperture.get("finite") is not True:
        aperture_errors.append("aperture observations are not finite")
    if not math.isfinite(radius) or radius <= 0.0:
        aperture_errors.append("probe radius is not finite and positive")
    if aperture.get("entry_center_clear") is not True:
        aperture_errors.append("probe could not enter a clear center below the opening")
    if aperture.get("bottom_hit") is not True:
        aperture_errors.append("probe did not hit the vessel bottom")
    if (
        not math.isfinite(vessel_height)
        or vessel_height <= 0.0
        or not math.isfinite(bottom_depth)
        or bottom_depth < 0.6 * vessel_height
    ):
        aperture_errors.append("first axial hit is too shallow and may be a virtual cap")
    if not isinstance(side_hits, dict) or side_hits.get("positive") is not True:
        aperture_errors.append("positive sidewall did not block the probe")
    if not isinstance(side_hits, dict) or side_hits.get("negative") is not True:
        aperture_errors.append("negative sidewall did not block the probe")

    support = observations.get("stable_support", {})
    support_errors: list[str] = []
    support_checks = (
        (
            "support_height_error_m",
            SUPPORT_HEIGHT_TOLERANCE_M,
            "support height error exceeds tolerance",
        ),
        (
            "tail_max_linear_speed_m_s",
            SUPPORT_LINEAR_SPEED_LIMIT_M_S,
            "tail linear speed exceeds tolerance",
        ),
        (
            "tail_max_angular_speed_rad_s",
            SUPPORT_ANGULAR_SPEED_LIMIT_RAD_S,
            "tail angular speed exceeds tolerance",
        ),
        ("tilt_deg", SUPPORT_TILT_LIMIT_DEG, "settled tilt exceeds tolerance"),
        (
            "lateral_drift_m",
            SUPPORT_LATERAL_DRIFT_LIMIT_M,
            "lateral drift exceeds tolerance",
        ),
        (
            "scene_to_rigid_position_error_m",
            ROOT_POSITION_PARITY_TOLERANCE_M,
            "support scene and rigid-body positions diverge",
        ),
    )
    if support.get("finite") is not True:
        support_errors.append("support observations are not finite")
    for key, limit, message in support_checks:
        value = _number(support.get(key))
        if not math.isfinite(value) or abs(value) > limit:
            support_errors.append(message)

    motion = observations.get("root_motion_parity", {})
    motion_errors: list[str] = []
    translation = _number(motion.get("translation_m"))
    min_translation = _number(root_motion_requirement.get("min_translation_m"))
    position_error = _number(motion.get("scene_to_rigid_position_error_m"))
    orientation_error = _number(
        motion.get("scene_to_rigid_orientation_error_deg")
    )
    if motion.get("finite") is not True:
        motion_errors.append("root-motion observations are not finite")
    if not math.isfinite(min_translation) or min_translation <= 0.0:
        motion_errors.append("minimum translation requirement is invalid")
    elif not math.isfinite(translation) or translation < min_translation:
        motion_errors.append("controlled root translation is below the requirement")
    if (
        not math.isfinite(position_error)
        or position_error > ROOT_POSITION_PARITY_TOLERANCE_M
    ):
        motion_errors.append("scene and rigid-body positions diverge")
    if (
        not math.isfinite(orientation_error)
        or orientation_error > ROOT_ORIENTATION_PARITY_TOLERANCE_DEG
    ):
        motion_errors.append("scene and rigid-body orientations diverge")

    gripper = observations.get("bilateral_gripper_proxy_collision", {})
    gripper_errors: list[str] = []
    gripper_radius = _number(gripper.get("probe_radius_m"))
    positive_distance = _number(gripper.get("positive_distance_m"))
    negative_distance = _number(gripper.get("negative_distance_m"))
    if gripper.get("finite") is not True:
        gripper_errors.append("gripper proxy observations are not finite")
    if gripper.get("positive_hit") is not True:
        gripper_errors.append("positive gripper proxy did not hit the vessel")
    elif (
        not math.isfinite(gripper_radius)
        or not math.isfinite(positive_distance)
        or positive_distance < 0.5 * gripper_radius
    ):
        gripper_errors.append(
            "positive gripper proxy starts inside or too near the collider"
        )
    if gripper.get("negative_hit") is not True:
        gripper_errors.append("negative gripper proxy did not hit the vessel")
    elif (
        not math.isfinite(gripper_radius)
        or not math.isfinite(negative_distance)
        or negative_distance < 0.5 * gripper_radius
    ):
        gripper_errors.append(
            "negative gripper proxy starts inside or too near the collider"
        )

    return {
        "cooked_aperture": _probe_result(aperture, aperture_errors),
        "stable_support": _probe_result(support, support_errors),
        "root_motion_parity": _probe_result(motion, motion_errors),
        "bilateral_gripper_proxy_collision": _probe_result(
            gripper,
            gripper_errors,
        ),
    }


def _validate_report_binding(
    interaction_contract: dict[str, Any],
    report: dict[str, Any],
) -> None:
    closure = interaction_contract.get("closure", {})
    binding = report.get("binding", {})
    errors: list[str] = []
    if binding.get("runtime_tree_sha256") != closure.get("runtime_tree_sha256"):
        errors.append(
            "report binding runtime_tree_sha256 does not match the contract closure"
        )
    if binding.get("prequalification_contract_payload_sha256") != closure.get(
        "contract_payload_sha256"
    ):
        errors.append(
            "report binding prequalification_contract_payload_sha256 does not "
            "match the input contract closure"
        )
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        errors.append("runtime qualification report schema is unsupported")
    if errors:
        raise ValueError("; ".join(errors))


def _interaction_payload_sha256(interaction_contract: dict[str, Any]) -> str:
    payload = {
        key: interaction_contract[key]
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
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _promoted_gate(
    previous: dict[str, Any],
    probe_id: str,
    probe: dict[str, Any],
    *,
    report_path: str,
    report_sha256: str,
) -> dict[str, Any]:
    gate = {
        key: deepcopy(value)
        for key, value in previous.items()
        if key not in {"status", "evidence"}
    }
    gate["status"] = probe.get("status", "blocked")
    gate["evidence"] = {
        "status": gate["status"],
        "probe_id": probe_id,
        "report_path": report_path,
        "report_sha256": report_sha256,
        "observations": [deepcopy(probe.get("observations", {}))],
        "errors": list(probe.get("errors", [])),
    }
    return gate


def promote_interaction_runtime_gates(
    interaction_contract: dict[str, Any],
    report: dict[str, Any],
    *,
    report_path: str,
    report_sha256: str,
) -> dict[str, Any]:
    """Project four independently measured probes onto four contract claims."""
    _validate_report_binding(interaction_contract, report)
    probes = report.get("probes")
    if not isinstance(probes, dict):
        raise ValueError("runtime qualification report has no probes object")
    required_probe_ids = (
        "cooked_aperture",
        "stable_support",
        "root_motion_parity",
        "bilateral_gripper_proxy_collision",
    )
    missing = [name for name in required_probe_ids if not isinstance(probes.get(name), dict)]
    if missing:
        raise ValueError("runtime qualification report missing probes: " + ", ".join(missing))

    contract = deepcopy(interaction_contract)
    open_top = deepcopy(contract.get("open_top", {}))
    aperture = probes["cooked_aperture"]
    open_top["status"] = aperture.get("status", "blocked")
    previous_aperture_evidence = open_top.get("evidence", {})
    aperture_gate = _promoted_gate(
        previous_aperture_evidence,
        "cooked_aperture",
        aperture,
        report_path=report_path,
        report_sha256=report_sha256,
    )
    open_top["evidence"] = aperture_gate["evidence"]
    contract["open_top"] = open_top
    contract["stable_support_gate"] = _promoted_gate(
        contract.get("stable_support_gate", {}),
        "stable_support",
        probes["stable_support"],
        report_path=report_path,
        report_sha256=report_sha256,
    )
    contract["root_motion_gate"] = _promoted_gate(
        contract.get("root_motion_gate", {}),
        "root_motion_parity",
        probes["root_motion_parity"],
        report_path=report_path,
        report_sha256=report_sha256,
    )
    contract["gripper_collision_gate"] = _promoted_gate(
        contract.get("gripper_collision_gate", {}),
        "bilateral_gripper_proxy_collision",
        probes["bilateral_gripper_proxy_collision"],
        report_path=report_path,
        report_sha256=report_sha256,
    )
    contract["gripper_collision_gate"]["evidence"]["claim_boundary"] = (
        "Bilateral proxy scene-query hits demonstrate cooked vessel-wall collision "
        "near the grasp frame; they do not demonstrate a robot grasp."
    )
    prequalification_digest = report["binding"][
        "prequalification_contract_payload_sha256"
    ]
    contract["open_top"]["evidence"][
        "prequalification_contract_payload_sha256"
    ] = prequalification_digest
    for gate_name in (
        "stable_support_gate",
        "root_motion_gate",
        "gripper_collision_gate",
    ):
        contract[gate_name]["evidence"][
            "prequalification_contract_payload_sha256"
        ] = prequalification_digest
    closure = deepcopy(contract["closure"])
    closure["contract_payload_sha256"] = _interaction_payload_sha256(contract)
    contract["closure"] = closure
    return contract


def _promote_manifest_claim_boundaries(
    claims_forbidden: Any,
    interaction_contract: dict[str, Any],
) -> list[Any]:
    claims = list(claims_forbidden) if isinstance(claims_forbidden, list) else []
    promoted_claims: set[str] = set()
    if interaction_contract.get("open_top", {}).get("status") == "pass":
        promoted_claims.add(APERTURE_NOT_QUALIFIED_CLAIM)
    if interaction_contract.get("root_motion_gate", {}).get("status") == "pass":
        promoted_claims.add(ROOT_MOTION_NOT_QUALIFIED_CLAIM)
    if (
        interaction_contract.get("stable_support_gate", {}).get("status") == "pass"
        and interaction_contract.get("gripper_collision_gate", {}).get("status")
        == "pass"
    ):
        promoted_claims.add(SUPPORT_AND_GRIPPER_NOT_QUALIFIED_CLAIM)
    return [claim for claim in claims if claim not in promoted_claims]


def _read_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _write_manifest_pair(
    manifest_path: Path,
    package_manifest_path: Path,
    manifest: dict[str, Any],
) -> None:
    serialized = (
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_manifest = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    temporary_manifest.write_bytes(serialized)
    temporary_manifest.replace(manifest_path)
    if package_manifest_path != manifest_path:
        package_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_package_manifest = package_manifest_path.with_suffix(
            package_manifest_path.suffix + ".tmp"
        )
        temporary_package_manifest.write_bytes(serialized)
        temporary_package_manifest.replace(package_manifest_path)


def _blocked_report(binding: dict[str, Any], reason: str) -> dict[str, Any]:
    probes = {
        probe_id: {
            "status": "blocked",
            "errors": [reason],
            "observations": {},
        }
        for probe_id in (
            "cooked_aperture",
            "stable_support",
            "root_motion_parity",
            "bilateral_gripper_proxy_collision",
        )
    }
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "blocked",
        "binding": binding,
        "probes": probes,
        "host_failure": {"reason": reason},
    }


def run_interaction_runtime_qualification(
    package_root: Path,
    manifest_path: Path,
    *,
    runtime_python: Path,
    expected_runtime_version: str = "4.1",
    timeout_seconds: int = 480,
) -> InteractionRuntimeQualificationResult:
    """Run one closure-bound Isaac worker and update only frozen gate fields."""
    package_root = package_root.resolve()
    manifest_path = manifest_path.resolve()
    runtime_python = runtime_python.resolve()
    root_usd = package_root / "asset.usd"
    evidence_dir = package_root / "evidence" / "interaction_runtime_qualification"
    report_path = evidence_dir / "report.json"
    request_path = evidence_dir / "request.json"
    stdout_path = evidence_dir / "stdout.log"
    stderr_path = evidence_dir / "stderr.log"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for stale_path in (report_path, stdout_path, stderr_path):
        try:
            stale_path.unlink()
        except FileNotFoundError:
            pass

    try:
        manifest = _read_json_object(manifest_path)
        interaction_contract = manifest["interaction_contract"]
        if not isinstance(interaction_contract, dict):
            raise ValueError("manifest interaction_contract must be an object")
        if not root_usd.is_file():
            raise ValueError(f"package entry USD does not exist: {root_usd}")
        if not runtime_python.is_file():
            raise ValueError(f"runtime Python does not exist: {runtime_python}")
        closure_gate = validate_runtime_package_closure(
            package_root,
            interaction_contract,
        )
        if closure_gate["status"] != "pass":
            raise ValueError("; ".join(closure_gate["errors"]))
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        reason = str(exc)
        return InteractionRuntimeQualificationResult(
            overall_status="blocked",
            return_code=5,
            interaction_contract=(
                interaction_contract
                if "interaction_contract" in locals()
                else {"schema_version": "aan.interaction_contract.v1", "status": "blocked"}
            ),
            runtime_evidence={"status": "blocked", "reason": reason},
            blocked_reasons=[
                {
                    "blocker_id": "interaction_runtime_preflight",
                    "summary": reason,
                }
            ],
        )

    binding = {
        "run_id": uuid.uuid4().hex,
        "root_usd_sha256": _sha256_file(root_usd),
        "runtime_tree_sha256": interaction_contract["closure"][
            "runtime_tree_sha256"
        ],
        "prequalification_contract_payload_sha256": interaction_contract["closure"][
            "contract_payload_sha256"
        ],
    }
    request_record = {
        "schema_version": "aan.interaction_runtime_qualification_request.v1",
        "binding": binding,
        "expected_runtime_version": expected_runtime_version,
        "interaction_contract": interaction_contract,
    }
    _write_json(request_path, request_record)
    repo_root = Path(__file__).resolve().parents[2]
    argv = [
        str(runtime_python),
        "-m",
        "convert_asset.asset_application_normalizer.interaction_runtime_qualification",
        "--worker",
        "--root-usd",
        str(root_usd),
        "--request",
        str(request_path),
        "--report-out",
        str(report_path),
        "--expected-runtime-version",
        expected_runtime_version,
        "--process-exit-policy",
        "os-exit",
    ]
    environment, environment_policy = runtime_subprocess_environment(
        runtime_python,
        explicit_runner=True,
    )
    command_record = {
        "stage": "interaction_runtime_qualification",
        "argv": argv,
        "cwd": str(repo_root),
        "env_policy": environment_policy,
        "request_path": request_path.relative_to(package_root).as_posix(),
        "report_path": report_path.relative_to(package_root).as_posix(),
        "stdout_path": stdout_path.relative_to(package_root).as_posix(),
        "stderr_path": stderr_path.relative_to(package_root).as_posix(),
        "binding": binding,
    }
    exit_code = 5
    try:
        completed = subprocess.run(
            argv,
            cwd=repo_root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        stdout_path.write_text(completed.stdout or "", encoding="utf-8")
        stderr_path.write_text(completed.stderr or "", encoding="utf-8")
        exit_code = int(completed.returncode)
        report = _read_json_object(report_path)
    except subprocess.TimeoutExpired as exc:
        stdout_path.write_text(str(exc.stdout or ""), encoding="utf-8")
        stderr_path.write_text(str(exc.stderr or ""), encoding="utf-8")
        report = _blocked_report(
            binding,
            f"Isaac runtime qualification timed out after {timeout_seconds} seconds",
        )
        exit_code = 124
        _write_json(report_path, report)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report = _blocked_report(
            binding,
            f"Isaac runtime worker did not produce a valid report: {exc}",
        )
        _write_json(report_path, report)

    try:
        _validate_report_binding(interaction_contract, report)
        if report.get("binding", {}).get("run_id") != binding["run_id"]:
            raise ValueError("runtime report run_id does not match this invocation")
        if report.get("binding", {}).get("root_usd_sha256") != binding[
            "root_usd_sha256"
        ]:
            raise ValueError("runtime report root_usd_sha256 does not match the package")
        post_closure = validate_runtime_package_closure(
            package_root,
            interaction_contract,
        )
        if post_closure["status"] != "pass":
            raise ValueError("; ".join(post_closure["errors"]))
        report_sha256 = _sha256_file(report_path)
        relative_report_path = report_path.relative_to(package_root).as_posix()
        promoted_contract = promote_interaction_runtime_gates(
            interaction_contract,
            report,
            report_path=relative_report_path,
            report_sha256=report_sha256,
        )
    except ValueError as exc:
        return InteractionRuntimeQualificationResult(
            overall_status="blocked",
            return_code=5,
            interaction_contract=interaction_contract,
            runtime_evidence=report,
            blocked_reasons=[
                {
                    "blocker_id": "interaction_runtime_binding",
                    "summary": str(exc),
                }
            ],
            extra_commands={"interaction_runtime_qualification_001": command_record},
        )

    manifest["interaction_contract"] = promoted_contract
    manifest["claims_forbidden"] = _promote_manifest_claim_boundaries(
        manifest.get("claims_forbidden", []),
        promoted_contract,
    )
    _write_manifest_pair(
        manifest_path,
        (package_root / "evidence" / "manifest.json").resolve(),
        manifest,
    )
    probes = report.get("probes", {})
    all_passed = all(
        isinstance(probes.get(probe_id), dict)
        and probes[probe_id].get("status") == "pass"
        for probe_id in (
            "cooked_aperture",
            "stable_support",
            "root_motion_parity",
            "bilateral_gripper_proxy_collision",
        )
    )
    overall_status = "pass" if exit_code == 0 and all_passed else "blocked"
    blocked_reasons = []
    if overall_status != "pass":
        blocked_reasons.append(
            {
                "blocker_id": "interaction_runtime_probe",
                "summary": "One or more interaction runtime probes did not pass.",
            }
        )
    return InteractionRuntimeQualificationResult(
        overall_status=overall_status,
        return_code=0 if overall_status == "pass" else 5,
        interaction_contract=promoted_contract,
        runtime_evidence=report,
        blocked_reasons=blocked_reasons,
        extra_commands={"interaction_runtime_qualification_001": command_record},
    )


def _path_in_scope(path: str, root_path: str) -> bool:
    return path == root_path or path.startswith(root_path.rstrip("/") + "/")


def _as_float_list(value: Any) -> list[float]:
    return [float(item) for item in value]


def _normalized(vector: Any, np: Any) -> Any:
    result = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(result))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError("runtime direction vector is not finite and non-zero")
    return result / norm


def _prim_world_position(stage: Any, prim_path: str, np: Any) -> Any:
    from pxr import Usd, UsdGeom  # type: ignore

    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        raise ValueError(f"runtime frame prim is missing: {prim_path}")
    matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
        Usd.TimeCode.Default()
    )
    return np.asarray(matrix.ExtractTranslation(), dtype=float)


def _prim_world_direction(
    stage: Any,
    prim_path: str,
    local_direction: list[float],
    np: Any,
) -> Any:
    from pxr import Gf, Usd, UsdGeom  # type: ignore

    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        raise ValueError(f"runtime direction prim is missing: {prim_path}")
    matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
        Usd.TimeCode.Default()
    )
    direction = matrix.TransformDir(Gf.Vec3d(*local_direction))
    return _normalized(direction, np)


def _root_world_quaternion(stage: Any, prim_path: str, np: Any) -> Any:
    from pxr import Usd, UsdGeom  # type: ignore

    prim = stage.GetPrimAtPath(prim_path)
    matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
        Usd.TimeCode.Default()
    )
    quaternion = matrix.ExtractRotationQuat()
    imaginary = quaternion.GetImaginary()
    return _normalized(
        [quaternion.GetReal(), imaginary[0], imaginary[1], imaginary[2]],
        np,
    )


def _quaternion_error_deg(first: Any, second: Any, np: Any) -> float:
    first = _normalized(first, np)
    second = _normalized(second, np)
    dot = min(1.0, max(-1.0, abs(float(np.dot(first, second)))))
    return math.degrees(2.0 * math.acos(dot))


def _projected_bbox_spans(
    stage: Any,
    root_path: str,
    directions: list[Any],
    np: Any,
) -> list[float]:
    from pxr import Usd, UsdGeom  # type: ignore

    root = stage.GetPrimAtPath(root_path)
    bounds = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(),
        [UsdGeom.Tokens.default_],
        useExtentsHint=False,
    ).ComputeWorldBound(root).ComputeAlignedRange()
    minimum = np.asarray(bounds.GetMin(), dtype=float)
    maximum = np.asarray(bounds.GetMax(), dtype=float)
    corners = np.asarray(
        [
            [x, y, z]
            for x in (minimum[0], maximum[0])
            for y in (minimum[1], maximum[1])
            for z in (minimum[2], maximum[2])
        ],
        dtype=float,
    )
    return [
        float(np.max(corners @ direction) - np.min(corners @ direction))
        for direction in directions
    ]


def _serialize_query_hit(hit: Any, stage_units_in_meters: float) -> dict[str, Any]:
    return {
        "collision": str(getattr(hit, "collision", "")),
        "rigid_body": str(getattr(hit, "rigid_body", "")),
        "distance_m": float(getattr(hit, "distance", 0.0))
        * stage_units_in_meters,
        "position_m": [
            float(item) * stage_units_in_meters
            for item in getattr(hit, "position", (math.nan, math.nan, math.nan))
        ],
        "normal": _as_float_list(
            getattr(hit, "normal", (math.nan, math.nan, math.nan))
        ),
    }


def _target_sphere_sweep_hits(
    scene_query: Any,
    gf: Any,
    *,
    radius_stage_units: float,
    origin: Any,
    direction: Any,
    distance_stage_units: float,
    root_path: str,
    stage_units_in_meters: float,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []

    def collect(hit: Any) -> bool:
        collision = str(getattr(hit, "collision", ""))
        rigid_body = str(getattr(hit, "rigid_body", ""))
        if _path_in_scope(collision, root_path) or _path_in_scope(
            rigid_body,
            root_path,
        ):
            hits.append(_serialize_query_hit(hit, stage_units_in_meters))
        return True

    scene_query.sweep_sphere_all(
        float(radius_stage_units),
        gf.Vec3f(*_as_float_list(origin)),
        gf.Vec3f(*_as_float_list(direction)),
        float(distance_stage_units),
        collect,
        True,
    )
    return sorted(hits, key=lambda item: item["distance_m"])


def _target_sphere_overlap_hits(
    scene_query: Any,
    gf: Any,
    *,
    radius_stage_units: float,
    position: Any,
    root_path: str,
) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []

    def collect(hit: Any) -> bool:
        collision = str(getattr(hit, "collision", ""))
        rigid_body = str(getattr(hit, "rigid_body", ""))
        if _path_in_scope(collision, root_path) or _path_in_scope(
            rigid_body,
            root_path,
        ):
            hits.append({"collision": collision, "rigid_body": rigid_body})
        return True

    scene_query.overlap_sphere(
        float(radius_stage_units),
        gf.Vec3f(*_as_float_list(position)),
        collect,
        False,
    )
    return hits


def _collect_support_observation(
    *,
    world: Any,
    rigid: Any,
    stage: Any,
    root_path: str,
    support_path: str,
    body_axis_local: list[float],
    ground_height_stage_units: float,
    stage_units_in_meters: float,
    np: Any,
    settle_steps: int = 240,
    tail_steps: int = 30,
) -> dict[str, Any]:
    initial_position, initial_orientation = rigid.get_world_pose()
    initial_position = np.asarray(initial_position, dtype=float)
    initial_scene_root = _prim_world_position(stage, root_path, np)
    initial_scene_support = _prim_world_position(stage, support_path, np)
    support_offset = initial_scene_support - initial_scene_root
    drop_stage_units = 0.02 / stage_units_in_meters
    raised_position = initial_position + np.asarray(
        [0.0, 0.0, drop_stage_units],
        dtype=float,
    )
    rigid.set_world_pose(raised_position, initial_orientation)
    rigid.set_linear_velocity(np.zeros(3, dtype=float))
    rigid.set_angular_velocity(np.zeros(3, dtype=float))
    tail_linear: list[float] = []
    tail_angular: list[float] = []
    for step in range(settle_steps):
        world.step(render=False)
        if step >= settle_steps - tail_steps:
            tail_linear.append(float(np.linalg.norm(rigid.get_linear_velocity())))
            tail_angular.append(float(np.linalg.norm(rigid.get_angular_velocity())))
    from omni.physx import get_physx_interface  # type: ignore

    get_physx_interface().update_transformations(True, True, True, False)
    support_position = _prim_world_position(stage, support_path, np)
    scene_root_position = _prim_world_position(stage, root_path, np)
    final_axis = _prim_world_direction(stage, root_path, body_axis_local, np)
    world_up = np.asarray([0.0, 0.0, 1.0], dtype=float)
    dot = min(1.0, max(-1.0, float(np.dot(final_axis, world_up))))
    final_position, _ = rigid.get_world_pose()
    final_position = np.asarray(final_position, dtype=float)
    predicted_support_position = final_position + support_offset
    finite_values = np.concatenate(
        [
            support_position,
            final_axis,
            final_position,
            scene_root_position,
            predicted_support_position,
            np.asarray(tail_linear),
            np.asarray(tail_angular),
        ]
    )
    return {
        "finite": bool(np.isfinite(finite_values).all()),
        "settle_steps": settle_steps,
        "tail_steps": tail_steps,
        "support_height_error_m": abs(
            float(predicted_support_position[2]) - ground_height_stage_units
        )
        * stage_units_in_meters,
        "tail_max_linear_speed_m_s": max(tail_linear, default=math.inf),
        "tail_max_angular_speed_rad_s": max(tail_angular, default=math.inf),
        "tilt_deg": math.degrees(math.acos(dot)),
        "lateral_drift_m": float(
            np.linalg.norm(final_position[:2] - raised_position[:2])
        )
        * stage_units_in_meters,
        "scene_to_rigid_position_error_m": float(
            np.linalg.norm(scene_root_position - final_position)
        )
        * stage_units_in_meters,
        "final_root_position_stage_units": _as_float_list(final_position),
        "final_scene_root_position_stage_units": _as_float_list(
            scene_root_position
        ),
        "final_support_position_stage_units": _as_float_list(support_position),
        "predicted_support_position_stage_units": _as_float_list(
            predicted_support_position
        ),
    }


def _collect_scene_query_observations(
    *,
    stage: Any,
    scene_query: Any,
    interaction_contract: dict[str, Any],
    stage_units_in_meters: float,
    np: Any,
    gf: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root_path = interaction_contract["runtime_identity"]["rigid_root_prim"]
    named_frames = interaction_contract["named_frames"]
    opening_path = named_frames["opening"]["prim_path"]
    grasp_path = named_frames["grasp"]["prim_path"]
    support_path = named_frames["support"]["prim_path"]
    body_axis = interaction_contract["open_top"]["axis_body_local"]
    opening = _prim_world_position(stage, opening_path, np)
    grasp = _prim_world_position(stage, grasp_path, np)
    support = _prim_world_position(stage, support_path, np)
    axial = _prim_world_direction(stage, root_path, body_axis, np)
    closing_axis = _prim_world_direction(stage, grasp_path, [1.0, 0.0, 0.0], np)
    second_radial = _normalized(np.cross(axial, closing_axis), np)
    radial_spans = _projected_bbox_spans(
        stage,
        root_path,
        [closing_axis, second_radial],
        np,
    )
    vessel_height_stage_units = float(np.dot(opening - support, axial))
    vessel_height_m = vessel_height_stage_units * stage_units_in_meters
    smallest_radial_m = min(radial_spans) * stage_units_in_meters
    probe_radius_m = min(0.005, max(0.002, smallest_radial_m * 0.03))
    probe_radius_stage_units = probe_radius_m / stage_units_in_meters
    entry_depth_m = min(0.04, max(0.02, vessel_height_m * 0.2))
    entry_depth_stage_units = entry_depth_m / stage_units_in_meters
    axial_origin = opening + axial * (2.5 * probe_radius_stage_units)
    axial_distance_stage_units = (
        vessel_height_m + 5.0 * probe_radius_m
    ) / stage_units_in_meters
    axial_hits = _target_sphere_sweep_hits(
        scene_query,
        gf,
        radius_stage_units=probe_radius_stage_units,
        origin=axial_origin,
        direction=-axial,
        distance_stage_units=axial_distance_stage_units,
        root_path=root_path,
        stage_units_in_meters=stage_units_in_meters,
    )
    entry_center = opening - axial * entry_depth_stage_units
    entry_overlaps = _target_sphere_overlap_hits(
        scene_query,
        gf,
        radius_stage_units=probe_radius_stage_units,
        position=entry_center,
        root_path=root_path,
    )
    side_distance_stage_units = (
        max(radial_spans) * 0.75 + 4.0 * probe_radius_stage_units
    )
    positive_hits = _target_sphere_sweep_hits(
        scene_query,
        gf,
        radius_stage_units=probe_radius_stage_units,
        origin=grasp,
        direction=closing_axis,
        distance_stage_units=side_distance_stage_units,
        root_path=root_path,
        stage_units_in_meters=stage_units_in_meters,
    )
    negative_hits = _target_sphere_sweep_hits(
        scene_query,
        gf,
        radius_stage_units=probe_radius_stage_units,
        origin=grasp,
        direction=-closing_axis,
        distance_stage_units=side_distance_stage_units,
        root_path=root_path,
        stage_units_in_meters=stage_units_in_meters,
    )
    bottom_hit = axial_hits[0] if axial_hits else None
    if bottom_hit is None:
        bottom_depth_m = None
    else:
        bottom_position_stage_units = (
            np.asarray(bottom_hit["position_m"], dtype=float)
            / stage_units_in_meters
        )
        bottom_depth_m = float(
            np.dot(opening - bottom_position_stage_units, axial)
            * stage_units_in_meters
        )
    finite = bool(
        np.isfinite(
            np.concatenate(
                [opening, grasp, support, axial, closing_axis, radial_spans]
            )
        ).all()
    )
    positive_side_hit = bool(positive_hits) and (
        positive_hits[0]["distance_m"] >= 0.5 * probe_radius_m
    )
    negative_side_hit = bool(negative_hits) and (
        negative_hits[0]["distance_m"] >= 0.5 * probe_radius_m
    )
    aperture = {
        "finite": finite,
        "method": "physx_cooked_sphere_sweep_and_overlap",
        "probe_radius_m": probe_radius_m,
        "entry_depth_m": entry_depth_m,
        "entry_center_clear": not entry_overlaps,
        "entry_overlaps": entry_overlaps,
        "bottom_hit": bottom_hit is not None,
        "bottom_depth_m": bottom_depth_m,
        "bottom_observation": bottom_hit,
        "vessel_height_m": vessel_height_m,
        "side_hits": {
            "positive": positive_side_hit,
            "negative": negative_side_hit,
        },
        "side_observations": {
            "positive": positive_hits[:1],
            "negative": negative_hits[:1],
        },
    }
    gripper = {
        "finite": finite,
        "method": "physx_cooked_bilateral_sphere_sweep",
        "probe_radius_m": probe_radius_m,
        "positive_hit": bool(positive_hits),
        "negative_hit": bool(negative_hits),
        "positive_distance_m": (
            positive_hits[0]["distance_m"] if positive_hits else None
        ),
        "negative_distance_m": (
            negative_hits[0]["distance_m"] if negative_hits else None
        ),
        "positive_observation": positive_hits[0] if positive_hits else None,
        "negative_observation": negative_hits[0] if negative_hits else None,
        "claim_boundary": (
            "Proxy collision only; no robot finger, contact force, closure, or "
            "grasp-retention claim is made."
        ),
    }
    return aperture, gripper


def _collect_root_motion_observation(
    *,
    world: Any,
    rigid: Any,
    stage: Any,
    root_path: str,
    control_direction: Any,
    min_translation_m: float,
    stage_units_in_meters: float,
    np: Any,
) -> dict[str, Any]:
    initial_position, initial_orientation = rigid.get_world_pose()
    initial_position = np.asarray(initial_position, dtype=float)
    displacement_m = max(0.06, min_translation_m + 0.01)
    displacement_stage_units = displacement_m / stage_units_in_meters
    target_position = initial_position + control_direction * displacement_stage_units
    rigid.set_world_pose(target_position, initial_orientation)
    rigid.set_linear_velocity(control_direction * 0.02)
    rigid.set_angular_velocity(np.zeros(3, dtype=float))
    for _ in range(2):
        world.step(render=False)
    from omni.physx import get_physx_interface  # type: ignore

    get_physx_interface().update_transformations(True, True, True, False)
    rigid_position, rigid_orientation = rigid.get_world_pose()
    rigid_position = np.asarray(rigid_position, dtype=float)
    rigid_orientation = np.asarray(rigid_orientation, dtype=float)
    scene_position = _prim_world_position(stage, root_path, np)
    scene_orientation = _root_world_quaternion(stage, root_path, np)
    finite_values = np.concatenate(
        [
            initial_position,
            rigid_position,
            rigid_orientation,
            scene_position,
            scene_orientation,
        ]
    )
    return {
        "finite": bool(np.isfinite(finite_values).all()),
        "control": {
            "kind": "rigid_root_pose_delta_plus_velocity",
            "requested_translation_m": displacement_m,
            "linear_velocity_m_s": _as_float_list(control_direction * 0.02),
            "steps": 2,
        },
        "translation_m": float(np.linalg.norm(rigid_position - initial_position))
        * stage_units_in_meters,
        "scene_to_rigid_position_error_m": float(
            np.linalg.norm(scene_position - rigid_position)
        )
        * stage_units_in_meters,
        "scene_to_rigid_orientation_error_deg": _quaternion_error_deg(
            scene_orientation,
            rigid_orientation,
            np,
        ),
        "scene_position_stage_units": _as_float_list(scene_position),
        "rigid_position_stage_units": _as_float_list(rigid_position),
        "scene_orientation_wxyz": _as_float_list(scene_orientation),
        "rigid_orientation_wxyz": _as_float_list(rigid_orientation),
    }


def _qualification_worker_report(
    args: argparse.Namespace,
    *,
    close_simulation_app: bool = True,
) -> dict[str, Any]:
    root_usd = Path(args.root_usd).resolve()
    request_path = Path(args.request).resolve()
    report_path = Path(args.report_out).resolve()
    try:
        request = _read_json_object(request_path)
        binding = request["binding"]
        interaction_contract = request["interaction_contract"]
        if not isinstance(binding, dict) or not isinstance(
            interaction_contract,
            dict,
        ):
            raise ValueError("worker request binding and contract must be objects")
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        return _blocked_report({}, f"invalid worker request: {exc}")
    report = _blocked_report(binding, "worker did not complete all probes")
    report["environment"] = {}
    report["runtime_profile_gate"] = {"status": "not_run"}
    report["static_identity_gate"] = {"status": "not_run"}
    if not root_usd.is_file():
        return _blocked_report(binding, f"package entry USD does not exist: {root_usd}")
    if _sha256_file(root_usd) != binding.get("root_usd_sha256"):
        return _blocked_report(binding, "package entry USD hash does not match request")
    simulation_app = None
    world = None
    try:
        from isaacsim import SimulationApp  # type: ignore

        simulation_app = SimulationApp(
            {
                "headless": True,
                "multi_gpu": False,
                "renderer": "RayTracedLighting",
            }
        )
        import omni  # type: ignore
        from omni.isaac.core import World  # type: ignore
        from omni.isaac.core.prims import RigidPrim  # type: ignore
        from omni.physx import get_physx_scene_query_interface  # type: ignore
        import numpy as np  # type: ignore
        from pxr import Gf, UsdGeom  # type: ignore

        report["environment"] = _runtime_environment()
        report["runtime_profile_gate"] = _runtime_profile_gate(
            report["environment"],
            str(args.expected_runtime_version),
        )
        if report["runtime_profile_gate"]["status"] != "pass":
            raise RuntimeError("Isaac/Kit runtime fingerprint does not match request")
        context = omni.usd.get_context()
        opened = bool(context.open_stage(str(root_usd)))
        loading_complete = False
        loading_state: dict[str, Any] = {}
        for _ in range(240):
            simulation_app.update()
            loading_complete, loading_state = _stage_loading_complete(context)
            if loading_complete:
                break
        stage = context.get_stage()
        if not opened or stage is None or not loading_complete:
            raise RuntimeError(
                f"package stage did not finish loading: {loading_state}"
            )
        stage.SetEditTarget(stage.GetSessionLayer())
        if str(UsdGeom.GetStageUpAxis(stage)).upper() != "Z":
            raise RuntimeError("qualification worker currently requires a Z-up package")
        stage_units_in_meters = float(UsdGeom.GetStageMetersPerUnit(stage))
        if not math.isfinite(stage_units_in_meters) or stage_units_in_meters <= 0.0:
            raise RuntimeError("stage metersPerUnit must be finite and positive")
        root_path = interaction_contract["runtime_identity"]["rigid_root_prim"]
        entry_path = interaction_contract["asset_entry_prim"]
        if root_path != entry_path:
            raise RuntimeError("v1 qualification requires asset entry and rigid root identity")
        active_rigid_bodies = _scoped_rigid_body_paths(stage, [entry_path])
        expected_rigid_bodies = interaction_contract["runtime_identity"][
            "active_rigid_body_prims"
        ]
        identity_status = (
            "pass"
            if active_rigid_bodies == expected_rigid_bodies == [root_path]
            else "blocked"
        )
        report["static_identity_gate"] = {
            "status": identity_status,
            "observed_active_rigid_bodies": active_rigid_bodies,
            "expected_active_rigid_bodies": expected_rigid_bodies,
        }
        if identity_status != "pass":
            raise RuntimeError("runtime stage does not have the bound unique rigid root")
        support_path = interaction_contract["named_frames"]["support"]["prim_path"]
        support_position = _prim_world_position(stage, support_path, np)
        ground_height = float(support_position[2])
        world = World(
            stage_units_in_meters=stage_units_in_meters,
            physics_dt=0.01,
            rendering_dt=0.01,
        )
        physics_context = world.get_physics_context()
        physics_context.set_broadphase_type("GPU")
        physics_context.enable_gpu_dynamics(True)
        report["physics_scene"] = {
            "broadphase_type": physics_context.get_broadphase_type(),
            "gpu_dynamics_enabled": physics_context.is_gpu_dynamics_enabled(),
            "readback_mode": "usd_and_rigid_view",
        }
        world.scene.add_default_ground_plane(
            z_position=ground_height,
            name="aan_qualification_ground",
            prim_path="/World/__aan_qualification_ground",
        )
        rigid = world.scene.add(
            RigidPrim(root_path, name="aan_qualification_rigid_root")
        )
        world.reset()
        for _ in range(8):
            world.step(render=False)
        support_observation = _collect_support_observation(
            world=world,
            rigid=rigid,
            stage=stage,
            root_path=root_path,
            support_path=support_path,
            body_axis_local=interaction_contract["open_top"]["axis_body_local"],
            ground_height_stage_units=ground_height,
            stage_units_in_meters=stage_units_in_meters,
            np=np,
        )
        aperture_observation, gripper_observation = (
            _collect_scene_query_observations(
                stage=stage,
                scene_query=get_physx_scene_query_interface(),
                interaction_contract=interaction_contract,
                stage_units_in_meters=stage_units_in_meters,
                np=np,
                gf=Gf,
            )
        )
        control_direction = _prim_world_direction(
            stage,
            interaction_contract["named_frames"]["grasp"]["prim_path"],
            [1.0, 0.0, 0.0],
            np,
        )
        root_motion_observation = _collect_root_motion_observation(
            world=world,
            rigid=rigid,
            stage=stage,
            root_path=root_path,
            control_direction=control_direction,
            min_translation_m=float(
                interaction_contract["root_motion_gate"]["min_translation_m"]
            ),
            stage_units_in_meters=stage_units_in_meters,
            np=np,
        )
        observations = {
            "cooked_aperture": aperture_observation,
            "stable_support": support_observation,
            "root_motion_parity": root_motion_observation,
            "bilateral_gripper_proxy_collision": gripper_observation,
        }
        probes = evaluate_probe_observations(
            observations,
            root_motion_requirement=interaction_contract["root_motion_gate"],
        )
        report["probes"] = probes
        report["status"] = (
            "pass"
            if all(probe["status"] == "pass" for probe in probes.values())
            else "blocked"
        )
        report.pop("host_failure", None)
        return report
    except Exception as exc:
        failed = _blocked_report(binding, f"runtime qualification failed: {exc}")
        failed["environment"] = report.get("environment", {})
        failed["runtime_profile_gate"] = report.get(
            "runtime_profile_gate",
            {"status": "not_run"},
        )
        failed["static_identity_gate"] = report.get(
            "static_identity_gate",
            {"status": "not_run"},
        )
        report = failed
        return failed
    finally:
        if simulation_app is not None and close_simulation_app:
            _close_simulation_app_with_report(
                simulation_app,
                report_path,
                report,
                world=world,
            )
        elif simulation_app is not None:
            _prepare_isolated_worker_exit(report, world=world)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AAN object interaction runtime qualification worker"
    )
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--root-usd")
    parser.add_argument("--request")
    parser.add_argument("--report-out")
    parser.add_argument("--package-root")
    parser.add_argument("--manifest")
    parser.add_argument("--runtime-python")
    parser.add_argument("--timeout-seconds", type=int, default=480)
    parser.add_argument("--expected-runtime-version", default="4.1")
    parser.add_argument(
        "--process-exit-policy",
        choices=("close", "os-exit"),
        default="close",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not args.worker:
        missing = [
            flag
            for flag, value in (
                ("--package-root", args.package_root),
                ("--manifest", args.manifest),
                ("--runtime-python", args.runtime_python),
            )
            if not value
        ]
        if missing:
            parser.error("host mode requires " + ", ".join(missing))
        result = run_interaction_runtime_qualification(
            Path(args.package_root),
            Path(args.manifest),
            runtime_python=Path(args.runtime_python),
            expected_runtime_version=str(args.expected_runtime_version),
            timeout_seconds=int(args.timeout_seconds),
        )
        print(
            json.dumps(
                {
                    "status": result.overall_status,
                    "return_code": result.return_code,
                    "probe_statuses": {
                        name: value.get("status")
                        for name, value in result.runtime_evidence.get(
                            "probes",
                            {},
                        ).items()
                    },
                    "blocked_reasons": result.blocked_reasons,
                },
                indent=2,
            )
        )
        return result.return_code
    missing = [
        flag
        for flag, value in (
            ("--root-usd", args.root_usd),
            ("--request", args.request),
            ("--report-out", args.report_out),
        )
        if not value
    ]
    if missing:
        parser.error("worker mode requires " + ", ".join(missing))
    use_os_exit = args.process_exit_policy == "os-exit"
    report = _qualification_worker_report(
        args,
        close_simulation_app=not use_os_exit,
    )
    _write_json(Path(args.report_out), report)
    exit_code = 0 if report.get("status") == "pass" else 5
    if use_os_exit:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
