"""Evidence manifest construction for Asset Application Normalizer milestones."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import (
    MILESTONE_AAN02,
    MILESTONE_AAN03,
    MILESTONE_AAN04,
    MILESTONE_AAN05,
    MILESTONE_AAN06,
    MILESTONE_AAN07,
    MILESTONE_AAN11,
    SCHEMA_VERSION,
    TOOL_VERSION,
    NormalizeAssetRequest,
)


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
    material_closure: list[dict[str, Any]] | None = None,
    material_runtime_closure: dict[str, Any] | None = None,
    physics_closure: dict[str, Any] | None = None,
    articulation_closure: dict[str, Any] | None = None,
    static_usd_report: dict[str, Any] | None = None,
    static_material_report: dict[str, Any] | None = None,
    static_material_runtime_report: dict[str, Any] | None = None,
    static_physics_report: dict[str, Any] | None = None,
    static_articulation_report: dict[str, Any] | None = None,
    stage_gates: list[dict[str, Any]] | None = None,
    runtime_evidence: dict[str, Any] | None = None,
    benchmark_contract: dict[str, Any] | None = None,
    task_contract_report: dict[str, Any] | None = None,
    extra_commands: dict[str, Any] | None = None,
    claims_allowed: list[str] | None = None,
    claims_forbidden: list[str] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    source_sha = sha256_file(request.source_usd)
    blocked_reasons = blocked_reasons or []
    default_prim = request.required_prims[0] if request.required_prims else None
    command_stage_by_milestone = {
        MILESTONE_AAN02: "cli_skeleton",
        MILESTONE_AAN03: "usd_closure",
        MILESTONE_AAN04: "material_closure",
        MILESTONE_AAN05: "physics_static",
        MILESTONE_AAN06: "runtime_smoke",
        MILESTONE_AAN07: "benchmark_contract",
        MILESTONE_AAN11: "material_runtime_closure",
    }
    command_stage = command_stage_by_milestone.get(milestone, "unknown")

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
            "required_prims": "task/required_prims.yaml",
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
            "resolution_records": [],
            "resolution_summary": {
                "mirrored": 0,
                "pruned": 0,
                "waived": 0,
                "blocked": 0,
            },
        },
        "material_closure": material_closure or [],
        "material_runtime_closure": material_runtime_closure
        or {
            "status": "not_run",
            "claim_level": "not_claimed",
            "full_material_parity_claimed": False,
            "root_mdl_assets": [],
            "imported_mdl_modules": [],
            "mdl_texture_assets": [],
            "native_runtime_modules": [],
            "mirror_actions": [],
            "rewrite_actions": [],
            "runtime_compiler": {"status": "not_run"},
            "view_evidence": [],
        },
        "physics_closure": physics_closure or {},
        "articulation_closure": articulation_closure or {},
        "stage_gates": stage_gates or [
            {
                "check_id": MILESTONE_AAN02,
                "stage": "cli_skeleton",
                "status": "pass" if overall_status == "dry_run_incomplete" else "blocked",
                "summary": "AAN-02 CLI accepted the request and wrote an evidence manifest.",
            }
        ],
        "runtime_evidence": runtime_evidence or {},
        "benchmark_contract": benchmark_contract or {},
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
    if extra_commands:
        manifest["commands"].update(extra_commands)
    if static_usd_report is not None:
        manifest["static_usd_report"] = static_usd_report
    if static_material_report is not None:
        manifest["static_material_report"] = static_material_report
    if static_material_runtime_report is not None:
        manifest["static_material_runtime_report"] = static_material_runtime_report
    if static_physics_report is not None:
        manifest["static_physics_report"] = static_physics_report
    if static_articulation_report is not None:
        manifest["static_articulation_report"] = static_articulation_report
    if task_contract_report is not None:
        manifest["task_contract_report"] = task_contract_report
    return manifest


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
