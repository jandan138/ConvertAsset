"""AAN MVP pipeline entrypoints."""

from __future__ import annotations

from pathlib import Path

from .evidence_manifest import build_manifest, write_manifest
from .material_closure import build_material_closure, build_not_run_material_closure
from .model import (
    ALLOWED_SOURCE_RUNTIMES,
    ALLOWED_TARGET_BENCHMARKS,
    ALLOWED_TARGET_RUNTIMES,
    MILESTONE_AAN04,
    USD_EXTENSIONS,
    NormalizeAssetRequest,
    NormalizeAssetResult,
)
from .package_layout import TargetPackageLayout, default_evidence_out
from .usd_closure import build_usd_closure_package


def _validation_error(message: str) -> NormalizeAssetResult:
    print(f"ERROR: {message}")
    return NormalizeAssetResult(return_code=2, manifest_path=None, overall_status="invalid")


def validate_request(request: NormalizeAssetRequest) -> NormalizeAssetResult | None:
    if not request.source_usd.exists():
        return _validation_error(f"source USD not found: {request.source_usd}")
    if request.source_usd.suffix.lower() not in USD_EXTENSIONS:
        return _validation_error(f"MVP only accepts USD files: {request.source_usd}")
    if request.source_runtime not in ALLOWED_SOURCE_RUNTIMES:
        return _validation_error(f"unsupported source runtime for MVP: {request.source_runtime}")
    if request.target_runtime not in ALLOWED_TARGET_RUNTIMES:
        return _validation_error(f"unsupported target runtime for MVP: {request.target_runtime}")
    if request.target_benchmark not in ALLOWED_TARGET_BENCHMARKS:
        return _validation_error(f"unsupported target benchmark for MVP: {request.target_benchmark}")
    return None


def normalize_asset(request: NormalizeAssetRequest) -> NormalizeAssetResult:
    validation = validate_request(request)
    if validation is not None:
        return validation

    evidence_out = request.evidence_out or default_evidence_out(request.out_dir)
    if request.dry_run:
        manifest = build_manifest(request, overall_status="dry_run_incomplete")
        write_manifest(evidence_out, manifest)
        print(f"AAN-02 dry-run manifest written: {evidence_out}")
        return NormalizeAssetResult(0, evidence_out, "dry_run_incomplete")

    closure = build_usd_closure_package(request)
    if closure.return_code == 0:
        material = build_material_closure(
            TargetPackageLayout(request.out_dir),
            closure.dependency_closure,
            request.material_policy,
        )
    else:
        material = build_not_run_material_closure(
            "AAN-04 material closure was not run because AAN-03 USD dependency closure blocked."
        )
    overall_status = material.overall_status if material.return_code else closure.overall_status
    return_code = material.return_code or closure.return_code
    blocked_reasons = [*closure.blocked_reasons, *material.blocked_reasons]
    stage_gates = [*closure.stage_gates, material.stage_gate]
    material_passed = material.stage_gate["status"] == "pass"
    manifest = build_manifest(
        request,
        overall_status=overall_status,
        blocked_reasons=blocked_reasons,
        milestone=MILESTONE_AAN04,
        root_usd=closure.root_usd_package_path,
        dependency_closure=closure.dependency_closure,
        material_closure=material.material_closure,
        static_usd_report=closure.static_usd_report,
        static_material_report=material.static_material_report,
        stage_gates=stage_gates,
        claims_allowed=[
            "AAN-03 static USD closure inspected the source graph and wrote an evidence manifest.",
            "Package USD asset paths are local when the AAN-03 gate status is pass.",
            *(
                [
                    "AAN-04 material closure recorded package-local source material evidence.",
                    "Source MDL and texture assets are preserved when listed with package hashes.",
                ]
                if material_passed
                else []
            ),
        ],
        claims_forbidden=[
            *([] if material_passed else ["Material closure is complete."]),
            "Physics or articulation closure is complete.",
            "Isaac Sim 4.1 runtime smoke passed.",
            "EBench task readiness is achieved.",
            "Binary USD layers with dependencies are fully supported by AAN-03 text rewriting.",
            "Full visual material parity beyond recorded source-preservation evidence is achieved.",
        ],
    )
    write_manifest(evidence_out, manifest)
    if return_code == 0:
        print(f"AAN-04 material closure package written: {request.out_dir}")
    elif closure.return_code != 0:
        print(f"AAN-04 material closure not run; AAN-03 blocked: {evidence_out}")
    else:
        print(f"AAN-04 material closure blocked; manifest written: {evidence_out}")
    return NormalizeAssetResult(return_code, evidence_out, overall_status)


def parse_gates(raw: str | None) -> list[str]:
    if not raw:
        return ["static"]
    return [item.strip() for item in raw.split(",") if item.strip()]
