"""Evidence manifest construction for Asset Application Normalizer milestones."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import MILESTONE_AAN02, SCHEMA_VERSION, TOOL_VERSION, NormalizeAssetRequest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_prim_records(required_prims: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "name": f"required_prim_{idx}",
            "path": prim,
            "role": "contract_required_prim",
            "required": True,
        }
        for idx, prim in enumerate(required_prims)
    ]


def build_manifest(
    request: NormalizeAssetRequest,
    *,
    overall_status: str,
    blocked_reasons: list[dict[str, Any]] | None = None,
    milestone: str = MILESTONE_AAN02,
    root_usd: str = "asset.usd",
    dependency_closure: dict[str, Any] | None = None,
    static_usd_report: dict[str, Any] | None = None,
    stage_gates: list[dict[str, Any]] | None = None,
    claims_allowed: list[str] | None = None,
    claims_forbidden: list[str] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    source_sha = sha256_file(request.source_usd)
    blocked_reasons = blocked_reasons or []
    default_prim = request.required_prims[0] if request.required_prims else None
    command_stage = "cli_skeleton" if milestone == MILESTONE_AAN02 else "usd_closure"

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "package_id": f"{request.asset_id.lower()}_{request.target_benchmark}_{request.target_runtime}",
        "asset_id": request.asset_id,
        "task_id": request.task_id,
        "milestone": milestone,
        "overall_status": overall_status,
        "source": {
            "path": str(request.source_usd),
            "sha256": source_sha,
            "source_format": "usd",
            "source_runtime_lineage": request.source_runtime,
        },
        "target": {
            "target_runtime_profile": request.target_runtime,
            "target_benchmark_profile": request.target_benchmark,
        },
        "entrypoints": {
            "root_usd": root_usd,
            "default_prim": default_prim,
            "task_config": "task/task_config.yaml",
            "metric_evaluator": "task/evaluator.yaml",
        },
        "normalization_policy": {
            "material": "preserve_source_then_add_compatibility_fallback",
            "physics": "preserve_authored_then_generate_with_provenance",
            "allowed_value_sources": ["authored", "derived", "template", "manual_override"],
        },
        "required_prim_paths": _required_prim_records(request.required_prims),
        "dependency_closure": dependency_closure or {
            "local_files": [],
            "missing": [],
            "remote_uri": [],
            "unauthorized_remote_uri": [],
        },
        "material_closure": [],
        "physics_closure": {},
        "articulation_closure": {},
        "stage_gates": stage_gates or [
            {
                "check_id": MILESTONE_AAN02,
                "stage": "cli_skeleton",
                "status": "pass" if overall_status == "dry_run_incomplete" else "blocked",
                "summary": "AAN-02 CLI accepted the request and wrote an evidence manifest.",
            }
        ],
        "runtime_evidence": {},
        "environment": {},
        "waivers": [],
        "blocked_reasons": blocked_reasons,
        "claims_allowed": claims_allowed or [
            "AAN-02 CLI skeleton parsed the request and wrote a schema-compatible manifest."
        ],
        "claims_forbidden": claims_forbidden or [
            "Asset package contents were produced.",
            "USD dependency closure is complete.",
            "Material closure is complete.",
            "Physics or articulation closure is complete.",
            "Isaac Sim 4.1 runtime smoke passed.",
            "EBench task readiness is achieved.",
        ],
        "commands": {
            "normalize_asset": {
                "stage": command_stage,
                "dry_run": request.dry_run,
                "gates": request.gates,
                "material_policy": request.material_policy,
                "contract": str(request.contract) if request.contract else None,
                "allow_waiver": str(request.allow_waiver) if request.allow_waiver else None,
            }
        },
        "created_at": now,
        "tool_version": TOOL_VERSION,
        "git_commit": None,
    }
    if static_usd_report is not None:
        manifest["static_usd_report"] = static_usd_report
    return manifest


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
