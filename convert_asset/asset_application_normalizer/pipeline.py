"""AAN MVP pipeline entrypoints."""

from __future__ import annotations

from pathlib import Path

from .evidence_manifest import build_manifest, write_manifest
from .model import (
    ALLOWED_SOURCE_RUNTIMES,
    ALLOWED_TARGET_BENCHMARKS,
    ALLOWED_TARGET_RUNTIMES,
    USD_EXTENSIONS,
    NormalizeAssetRequest,
    NormalizeAssetResult,
)
from .package_layout import default_evidence_out


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

    blocked_reasons = [
        {
            "blocker_id": "aan02_block_non_dry_run_not_implemented",
            "severity": "blocking",
            "summary": "AAN-02 implements the CLI skeleton and dry-run manifest path only.",
            "required_resolution": "Implement AAN-03 USD closure before writing target package contents.",
        }
    ]
    manifest = build_manifest(request, overall_status="blocked", blocked_reasons=blocked_reasons)
    write_manifest(evidence_out, manifest)
    print(f"AAN-02 non-dry-run blocked; manifest written: {evidence_out}")
    return NormalizeAssetResult(5, evidence_out, "blocked")


def parse_gates(raw: str | None) -> list[str]:
    if not raw:
        return ["static"]
    return [item.strip() for item in raw.split(",") if item.strip()]
