#!/usr/bin/env python3
"""Bind a passing cross-package interaction report into the rack package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Mapping
import uuid


REPORT_SCHEMA_VERSION = "aan.tube_rack_insertion_qualification.v2"
BINDING_SCHEMA_VERSION = "aan.interaction_task_qualification_binding.v1"
PROMOTION_SCHEMA_VERSION = "aan.interaction_task_qualification_promotion.v1"
QUALIFICATION_ID = "tube_insertion"
REPORT_RELATIVE_PATH = (
    "evidence/task_qualifications/tube_insertion/report.json"
)
PROMOTION_RELATIVE_PATH = (
    "evidence/task_qualifications/tube_insertion/promotion.json"
)
REQUIRED_GATES = (
    "composition_identity",
    "dynamic_insertion",
    "side_clearance",
    "bottom_contact",
    "source_integrity",
)
REQUIRED_BASE_INTERACTION_GATES = (
    "root_motion_gate",
    "stable_support_gate",
    "gripper_collision_gate",
    "open_top",
)


class InteractionTaskFinalizationError(ValueError):
    """Raised when runtime evidence cannot be promoted without overclaiming."""


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _json_object_bytes(value: bytes, label: str) -> dict[str, Any]:
    try:
        decoded = json.loads(
            value.decode("utf-8"),
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise InteractionTaskFinalizationError(
            f"{label} is not valid JSON"
        ) from exc
    if not isinstance(decoded, dict):
        raise InteractionTaskFinalizationError(f"{label} must be a JSON object")
    return decoded


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise InteractionTaskFinalizationError(f"{label} must be an object")
    return value


def _required_string(value: Mapping[str, Any], key: str, label: str) -> str:
    candidate = value.get(key)
    if not isinstance(candidate, str) or not candidate:
        raise InteractionTaskFinalizationError(
            f"{label}.{key} must be a non-empty string"
        )
    return candidate


def _package_binding(
    package_root: Path,
    manifest_path: Path,
    *,
    role: str,
) -> tuple[dict[str, Any], bytes, dict[str, str]]:
    if not package_root.is_dir():
        raise InteractionTaskFinalizationError(
            f"{role} package root does not exist: {package_root}"
        )
    if not manifest_path.is_file():
        raise InteractionTaskFinalizationError(
            f"{role} manifest does not exist: {manifest_path}"
        )
    embedded = package_root / "evidence" / "manifest.json"
    if not embedded.is_file():
        raise InteractionTaskFinalizationError(
            f"{role} package is missing evidence/manifest.json"
        )
    manifest_bytes = manifest_path.read_bytes()
    if embedded.read_bytes() != manifest_bytes:
        raise InteractionTaskFinalizationError(
            f"{role} external and embedded manifests must be byte-identical"
        )
    manifest = _json_object_bytes(manifest_bytes, f"{role} manifest")
    if manifest.get("schema_version") != "asset_application_normalizer.v1":
        raise InteractionTaskFinalizationError(
            f"{role} manifest schema_version is unsupported"
        )
    if manifest.get("overall_status") != "pass":
        raise InteractionTaskFinalizationError(
            f"{role} manifest overall_status must be pass"
        )
    entrypoints = _mapping(
        manifest.get("entrypoints"),
        f"{role} manifest.entrypoints",
    )
    entry_prim = _required_string(
        entrypoints,
        "asset_entry_prim",
        f"{role} manifest.entrypoints",
    )
    contract = _mapping(
        manifest.get("interaction_contract"),
        f"{role} manifest.interaction_contract",
    )
    if contract.get("status") != "pass":
        raise InteractionTaskFinalizationError(
            f"{role} interaction_contract.status must be pass"
        )
    if contract.get("asset_entry_prim") != entry_prim:
        raise InteractionTaskFinalizationError(
            f"{role} interaction contract entry prim does not match manifest"
        )
    runtime_identity = _mapping(
        contract.get("runtime_identity"),
        f"{role} interaction runtime_identity",
    )
    if (
        runtime_identity.get("exactly_one_active_rigid_body") is not True
        or runtime_identity.get("rigid_root_prim") != entry_prim
        or runtime_identity.get("active_rigid_body_prims") != [entry_prim]
    ):
        raise InteractionTaskFinalizationError(
            f"{role} package does not have one identity rigid root at its entry prim"
        )
    asset_path = package_root / "asset.usd"
    if not asset_path.is_file():
        raise InteractionTaskFinalizationError(
            f"{role} package asset.usd does not exist"
        )
    asset_sha256 = _sha256_file(asset_path)
    closure = _mapping(
        contract.get("closure"),
        f"{role} interaction closure",
    )
    if closure.get("status") != "pass":
        raise InteractionTaskFinalizationError(
            f"{role} interaction closure.status must be pass"
        )
    artifacts = closure.get("artifacts")
    if not isinstance(artifacts, list):
        raise InteractionTaskFinalizationError(
            f"{role} interaction closure.artifacts must be a list"
        )
    asset_records = [
        item
        for item in artifacts
        if isinstance(item, dict) and item.get("path") == "asset.usd"
    ]
    if len(asset_records) != 1 or asset_records[0].get("sha256") != asset_sha256:
        raise InteractionTaskFinalizationError(
            f"{role} interaction closure does not bind the current asset.usd"
        )
    named_frames = _mapping(
        contract.get("named_frames"),
        f"{role} interaction named_frames",
    )
    support = _mapping(
        named_frames.get("support"),
        f"{role} interaction support frame",
    )
    if support.get("parent_prim") != entry_prim:
        raise InteractionTaskFinalizationError(
            f"{role} support frame parent_prim must equal the asset entry prim"
        )
    if support.get("authoritative") is not True:
        raise InteractionTaskFinalizationError(
            f"{role} support frame must be authoritative"
        )
    return (
        manifest,
        manifest_bytes,
        {
            "package_manifest_sha256": _sha256_bytes(manifest_bytes),
            "asset_usd_sha256": asset_sha256,
            "asset_entry_prim": entry_prim,
        },
    )


def _validate_finite_json(value: Any, label: str = "report") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_finite_json(item, f"{label}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_finite_json(item, f"{label}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise InteractionTaskFinalizationError(f"{label} must be finite")


def _validate_base_interaction_gates(
    manifest: Mapping[str, Any],
    *,
    role: str,
) -> None:
    contract = _mapping(
        manifest.get("interaction_contract"),
        f"{role} manifest.interaction_contract",
    )
    for gate_name in REQUIRED_BASE_INTERACTION_GATES:
        gate = _mapping(
            contract.get(gate_name),
            f"{role} interaction_contract.{gate_name}",
        )
        if gate.get("status") != "pass":
            raise InteractionTaskFinalizationError(
                f"{role} interaction_contract.{gate_name}.status must be pass"
            )


def _validate_report(
    report: Mapping[str, Any],
    *,
    rack_binding: Mapping[str, str],
    tube_binding: Mapping[str, str],
) -> None:
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise InteractionTaskFinalizationError(
            "runtime report schema_version is unsupported"
        )
    if report.get("status") != "pass":
        raise InteractionTaskFinalizationError(
            "runtime report status must be pass"
        )
    _validate_finite_json(report)
    inputs = _mapping(report.get("inputs"), "runtime report.inputs")
    for role, expected in (
        ("rack", rack_binding),
        ("tube", tube_binding),
    ):
        observed = _mapping(inputs.get(role), f"runtime report.inputs.{role}")
        for field_name, expected_value in expected.items():
            if observed.get(field_name) != expected_value:
                label = {
                    "package_manifest_sha256": "manifest SHA-256",
                    "asset_usd_sha256": "asset USD SHA-256",
                    "asset_entry_prim": "entry prim",
                }.get(field_name, field_name.replace("_", " "))
                raise InteractionTaskFinalizationError(
                    f"runtime report {role} {label} does not match the package"
                )
    protocol = _mapping(report.get("protocol"), "runtime report.protocol")
    if protocol.get("tube_kinematic") is not False:
        raise InteractionTaskFinalizationError(
            "runtime report protocol must keep the tube dynamic"
        )
    if protocol.get("authored_translation_updates") != 0:
        raise InteractionTaskFinalizationError(
            "runtime report protocol must not author per-frame translations"
        )
    source_integrity = _mapping(
        report.get("source_integrity"),
        "runtime report.source_integrity",
    )
    if source_integrity.get("status") != "pass":
        raise InteractionTaskFinalizationError(
            "runtime report source_integrity.status must be pass"
        )
    expected_integrity = {
        "rack_asset_usd_sha256_before": rack_binding["asset_usd_sha256"],
        "rack_asset_usd_sha256_after": rack_binding["asset_usd_sha256"],
        "tube_asset_usd_sha256_before": tube_binding["asset_usd_sha256"],
        "tube_asset_usd_sha256_after": tube_binding["asset_usd_sha256"],
    }
    for field_name, expected_value in expected_integrity.items():
        if source_integrity.get(field_name) != expected_value:
            raise InteractionTaskFinalizationError(
                f"runtime report source integrity {field_name} does not match"
            )
    gates = _mapping(report.get("gates"), "runtime report.gates")
    for gate_name in REQUIRED_GATES:
        gate = _mapping(
            gates.get(gate_name),
            f"runtime report.gates.{gate_name}",
        )
        if gate.get("status") != "pass":
            raise InteractionTaskFinalizationError(
                f"runtime report gate {gate_name} status must be pass"
            )


def _manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(value)
    temporary.replace(path)


def _prepare_new_artifact(package_root: Path, path: Path) -> None:
    if path.exists() or path.is_symlink():
        raise InteractionTaskFinalizationError(
            f"refusing to replace an existing task qualification artifact: {path}"
        )
    resolved_parent = path.parent.resolve()
    if resolved_parent != package_root and package_root not in resolved_parent.parents:
        raise InteractionTaskFinalizationError(
            f"task qualification artifact escapes rack package: {path}"
        )


def finalize_interaction_task_qualification(
    *,
    rack_package_root: Path,
    rack_manifest_path: Path,
    tube_package_root: Path,
    tube_manifest_path: Path,
    runtime_report_path: Path,
) -> dict[str, Any]:
    """Promote one passing, cross-package-bound insertion report."""
    rack_package_root = rack_package_root.resolve()
    rack_manifest_path = rack_manifest_path.resolve()
    tube_package_root = tube_package_root.resolve()
    tube_manifest_path = tube_manifest_path.resolve()
    runtime_report_path = runtime_report_path.resolve()
    if not runtime_report_path.is_file():
        raise InteractionTaskFinalizationError(
            f"runtime report does not exist: {runtime_report_path}"
        )
    rack_manifest, rack_manifest_bytes, rack_binding = _package_binding(
        rack_package_root,
        rack_manifest_path,
        role="rack",
    )
    _validate_base_interaction_gates(rack_manifest, role="rack")
    existing_qualifications = rack_manifest.get("task_qualifications", [])
    if isinstance(existing_qualifications, list) and any(
        isinstance(item, dict)
        and item.get("qualification_id") == QUALIFICATION_ID
        for item in existing_qualifications
    ):
        raise InteractionTaskFinalizationError(
            "manifest already contains an existing tube insertion promotion"
        )
    _tube_manifest, _tube_manifest_bytes, tube_binding = _package_binding(
        tube_package_root,
        tube_manifest_path,
        role="tube",
    )
    try:
        report_bytes = runtime_report_path.read_bytes()
    except OSError as exc:
        raise InteractionTaskFinalizationError(
            "runtime report became unreadable during finalization"
        ) from exc
    report = _json_object_bytes(report_bytes, "runtime report")
    _validate_report(
        report,
        rack_binding=rack_binding,
        tube_binding=tube_binding,
    )
    qualifications = rack_manifest.get("task_qualifications", [])
    if not isinstance(qualifications, list) or not all(
        isinstance(item, dict) for item in qualifications
    ):
        raise InteractionTaskFinalizationError(
            "manifest.task_qualifications must be a list of objects"
        )
    if any(
        item.get("qualification_id") == QUALIFICATION_ID
        for item in qualifications
    ):
        raise InteractionTaskFinalizationError(
            "manifest already contains an existing tube insertion promotion"
        )
    package_report_path = rack_package_root / REPORT_RELATIVE_PATH
    promotion_path = rack_package_root / PROMOTION_RELATIVE_PATH
    for path in (package_report_path, promotion_path):
        _prepare_new_artifact(rack_package_root, path)
    report_sha256 = _sha256_bytes(report_bytes)
    prequalification_manifest_sha256 = _sha256_bytes(rack_manifest_bytes)
    binding = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "qualification_id": QUALIFICATION_ID,
        "status": "pass",
        "report_path": REPORT_RELATIVE_PATH,
        "report_sha256": report_sha256,
        "promotion_path": PROMOTION_RELATIVE_PATH,
        "inputs": {
            "rack": dict(rack_binding),
            "tube": dict(tube_binding),
        },
        "claim_boundary": (
            "The recorded fixed-rack gravity protocol qualified the delivered "
            "rack/tube collider path and bottom contact only; it does not claim "
            "robot-policy or benchmark success."
        ),
    }
    rack_manifest["task_qualifications"] = [*qualifications, binding]
    final_manifest_bytes = _manifest_bytes(rack_manifest)
    final_manifest_sha256 = _sha256_bytes(final_manifest_bytes)
    promotion = {
        "schema_version": PROMOTION_SCHEMA_VERSION,
        "qualification_id": QUALIFICATION_ID,
        "status": "pass",
        "prequalification_manifest_sha256": prequalification_manifest_sha256,
        "final_manifest_sha256": final_manifest_sha256,
        "report_path": REPORT_RELATIVE_PATH,
        "report_sha256": report_sha256,
        "rack": dict(rack_binding),
        "tube": dict(tube_binding),
    }
    _atomic_write(package_report_path, report_bytes)
    _atomic_write(rack_manifest_path, final_manifest_bytes)
    _atomic_write(
        rack_package_root / "evidence" / "manifest.json",
        final_manifest_bytes,
    )
    _atomic_write(
        promotion_path,
        (
            json.dumps(
                promotion,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8"),
    )
    return {
        "status": "pass",
        "qualification_id": QUALIFICATION_ID,
        "package_root": str(rack_package_root),
        "prequalification_manifest_sha256": prequalification_manifest_sha256,
        "final_manifest_sha256": final_manifest_sha256,
        "runtime_report_sha256": report_sha256,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Promote a passing tube-rack insertion qualification."
    )
    parser.add_argument("--rack-package", type=Path, required=True)
    parser.add_argument("--rack-manifest", type=Path, required=True)
    parser.add_argument("--tube-package", type=Path, required=True)
    parser.add_argument("--tube-manifest", type=Path, required=True)
    parser.add_argument("--runtime-report", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = finalize_interaction_task_qualification(
            rack_package_root=args.rack_package,
            rack_manifest_path=args.rack_manifest,
            tube_package_root=args.tube_package,
            tube_manifest_path=args.tube_manifest,
            runtime_report_path=args.runtime_report,
        )
    except InteractionTaskFinalizationError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
