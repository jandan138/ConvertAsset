#!/usr/bin/env python3
"""Diagnose supplemental material-effect preservation failures."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline"
DEFAULT_CONVERSION_MANIFEST = RAW_DIR / "supplemental_conversion_manifest.json"
DEFAULT_OUTPUT = RAW_DIR / "supplemental_material_preservation_diagnostic.json"

CONDITION_ORDER = [
    "original_MDL",
    "existing_noMDL",
    "nvidia_asset_converter_preview_or_bake",
]

StageInspector = Callable[[Path, str], dict[str, Any]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return "unknown"


def _git_status_porcelain() -> list[str]:
    try:
        tracked_output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        untracked_output = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    lines = [line for line in tracked_output.splitlines() if line]
    untracked_count = len([line for line in untracked_output.splitlines() if line])
    if untracked_count:
        lines.append(f"?? {untracked_count} untracked files omitted from provenance")
    return lines


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        try:
            return [float(item) for item in value]
        except Exception:
            pass
    try:
        return float(value)
    except Exception:
        return str(value)


def _default_stage_inspector(path: Path, target_prim_path: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "inspection_status": "missing_path",
            "stage_opened": False,
            "target_exists": False,
            "error": "path_missing",
        }
    try:
        from pxr import Usd, UsdShade
    except Exception as exc:  # pragma: no cover - requires Isaac/PXR env
        return {
            "inspection_status": "pxr_unavailable",
            "stage_opened": None,
            "target_exists": None,
            "error": f"pxr_import_failed:{exc}",
        }
    try:
        stage = Usd.Stage.Open(str(path))
    except Exception as exc:  # pragma: no cover - malformed USD only
        return {
            "inspection_status": "stage_open_failed",
            "stage_opened": False,
            "target_exists": None,
            "error": f"stage_open_failed:{exc}",
        }
    if stage is None:
        return {
            "inspection_status": "stage_open_returned_none",
            "stage_opened": False,
            "target_exists": None,
            "error": "stage_open_returned_none",
        }

    target = stage.GetPrimAtPath(target_prim_path)
    target_exists = bool(target and target.IsValid())
    target_child_count = len(target.GetChildren()) if target_exists else 0
    shader_count = 0
    preview_surface_count = 0
    active_mdl_shader_count = 0
    basecolor_texture_file_count = 0
    texture_files: list[str] = []
    diffuse_color_connected = False
    diffuse_color_value = None
    mdl_checker_enabled = False
    mdl_checker_scale = None
    mdl_texture_inputs: list[str] = []

    for prim in stage.Traverse():
        if prim.GetTypeName() != "Shader":
            continue
        shader_count += 1
        shader = UsdShade.Shader(prim)
        shader_id = shader.GetIdAttr().Get()
        if shader_id == "UsdPreviewSurface":
            preview_surface_count += 1
            diffuse = shader.GetInput("diffuseColor")
            if diffuse:
                diffuse_color_connected = diffuse_color_connected or diffuse.HasConnectedSource()
                if diffuse.Get() is not None:
                    diffuse_color_value = _json_value(diffuse.Get())
        source_attr = prim.GetAttribute("info:implementationSource")
        asset_attr = prim.GetAttribute("info:mdl:sourceAsset")
        if source_attr and source_attr.Get() == "sourceAsset" and asset_attr and asset_attr.Get():
            active_mdl_shader_count += 1
            for shader_input in shader.GetInputs():
                base_name = shader_input.GetBaseName()
                value = shader_input.Get()
                if base_name == "add_checker" and value not in (None, 0, "None"):
                    mdl_checker_enabled = True
                if base_name == "checker_scale" and value is not None:
                    mdl_checker_scale = _json_value(value)
                if base_name == "tex" and value:
                    mdl_texture_inputs.append(base_name)
        if shader_id == "UsdUVTexture":
            file_input = shader.GetInput("file")
            file_value = file_input.Get() if file_input else None
            if file_value:
                texture_files.append(str(file_value))
                if "basecolor" in prim.GetName().lower() or "base_color" in prim.GetName().lower():
                    basecolor_texture_file_count += 1

    return {
        "inspection_status": "ok",
        "stage_opened": True,
        "target_exists": target_exists,
        "target_prim_type": target.GetTypeName() if target_exists else None,
        "target_child_count": target_child_count,
        "shader_count": shader_count,
        "preview_surface_count": preview_surface_count,
        "active_mdl_shader_count": active_mdl_shader_count,
        "basecolor_texture_file_count": basecolor_texture_file_count,
        "texture_files": texture_files,
        "diffuse_color_connected": diffuse_color_connected,
        "diffuse_color_value": diffuse_color_value,
        "mdl_checker_enabled": mdl_checker_enabled,
        "mdl_checker_scale": mdl_checker_scale,
        "mdl_texture_inputs": mdl_texture_inputs,
    }


def _verdict_rank(verdict: str) -> int:
    return {"PASS": 0, "WARN": 1, "FAIL": 2}.get(verdict, 2)


def _source_checker_authored(original_inspection: dict[str, Any]) -> bool:
    return bool(
        original_inspection.get("mdl_checker_enabled")
        or original_inspection.get("mdl_texture_inputs")
    )


def _condition_diagnostic(
    *,
    effect: str,
    condition: str,
    source_status: str,
    inspection: dict[str, Any],
    source_checker_authored: bool,
) -> dict[str, Any]:
    target_exists = inspection.get("target_exists")
    if target_exists is False:
        return {
            "verdict": "FAIL",
            "diagnostic_reason": "converted_stage_missing_target_prim",
            "retake_action": "camera_retake_insufficient_rerun_or_treat_as_failure",
        }
    if inspection.get("inspection_status") != "ok":
        return {
            "verdict": "FAIL",
            "diagnostic_reason": str(inspection.get("inspection_status") or "inspection_failed"),
            "retake_action": "fix_or_rerun_stage_inspection",
        }
    if effect == "procedural_texture" and condition == "original_MDL" and source_checker_authored:
        return {
            "verdict": "PASS",
            "diagnostic_reason": "source_checker_authored",
            "retake_action": "none",
        }
    if effect == "procedural_texture" and condition != "original_MDL" and source_checker_authored:
        has_texture = (inspection.get("basecolor_texture_file_count") or 0) > 0
        has_diffuse_connection = bool(inspection.get("diffuse_color_connected"))
        if not has_texture and not has_diffuse_connection:
            return {
                "verdict": "FAIL",
                "diagnostic_reason": "converted_preview_surface_lacks_checker_texture",
                "retake_action": "investigate_or_bake_procedural_texture_before_success_claim",
            }
        return {
            "verdict": "PASS",
            "diagnostic_reason": "converted_preview_surface_has_texture_evidence",
            "retake_action": "none",
        }
    if effect == "clearcoat" and condition != "original_MDL":
        return {
            "verdict": "WARN",
            "diagnostic_reason": "clearcoat_approximated_by_preview_surface",
            "retake_action": "review_visual_result_before_success_claim",
        }
    return {
        "verdict": "PASS" if source_status == "available" else "WARN",
        "diagnostic_reason": "no_static_material_preservation_issue_detected",
        "retake_action": "none",
    }


def build_supplemental_material_diagnostics(
    conversion_manifest: dict[str, Any],
    *,
    stage_inspector: StageInspector = _default_stage_inspector,
    generated_at_utc: str | None = None,
    generator_git_commit: str | None = None,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    nvidia_target_missing_count = 0
    converted_procedural_checker_loss_count = 0
    blockers: set[str] = set()

    for sample in conversion_manifest.get("samples", []):
        sample_id = str(sample.get("sample_id"))
        effect = str((sample.get("present_effects") or ["unknown"])[0])
        target_prim_path = str(sample.get("target_prim_path") or "")
        raw_conditions = sample.get("conditions") or {}
        inspected_conditions: dict[str, dict[str, Any]] = {}
        for condition in CONDITION_ORDER:
            condition_record = raw_conditions.get(condition) or {}
            usd_path = Path(str(condition_record.get("usd_path") or ""))
            inspection = stage_inspector(usd_path, target_prim_path)
            inspected_conditions[condition] = {
                "source_status": condition_record.get("status"),
                "usd_path": str(usd_path),
                "inspection": inspection,
            }

        source_checker = _source_checker_authored(
            inspected_conditions.get("original_MDL", {}).get("inspection") or {}
        )
        condition_outputs: dict[str, dict[str, Any]] = {}
        case_verdict = "PASS"
        for condition in CONDITION_ORDER:
            inspected = inspected_conditions[condition]
            diagnostic = _condition_diagnostic(
                effect=effect,
                condition=condition,
                source_status=str(inspected.get("source_status") or "missing"),
                inspection=inspected["inspection"],
                source_checker_authored=source_checker,
            )
            if _verdict_rank(diagnostic["verdict"]) > _verdict_rank(case_verdict):
                case_verdict = diagnostic["verdict"]
            if (
                condition == "nvidia_asset_converter_preview_or_bake"
                and inspected["inspection"].get("target_exists") is False
            ):
                nvidia_target_missing_count += 1
                blockers.add("nvidia_clearcoat_target_missing")
            if diagnostic["diagnostic_reason"] == "converted_preview_surface_lacks_checker_texture":
                converted_procedural_checker_loss_count += 1
                blockers.add("procedural_checker_not_preserved_in_converted_conditions")
            condition_outputs[condition] = {
                **diagnostic,
                "source_status": inspected.get("source_status"),
                "usd_path": inspected.get("usd_path"),
                "inspection": inspected["inspection"],
            }
        cases.append(
            {
                "sample_id": sample_id,
                "effect": effect,
                "target_prim_path": target_prim_path,
                "case_verdict": case_verdict,
                "source_checker_authored": source_checker,
                "conditions": condition_outputs,
            }
        )

    fail_count = sum(1 for case in cases if case["case_verdict"] == "FAIL")
    warn_count = sum(1 for case in cases if case["case_verdict"] == "WARN")
    pass_count = sum(1 for case in cases if case["case_verdict"] == "PASS")
    return {
        "schema_version": 1,
        "status": "supplemental_material_preservation_diagnostic",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/diagnose_supplemental_material_preservation.py",
        "generator_git_commit": generator_git_commit or _git_commit(),
        "summary": {
            "case_count": len(cases),
            "pass_count": pass_count,
            "warn_count": warn_count,
            "fail_count": fail_count,
            "nvidia_target_missing_count": nvidia_target_missing_count,
            "converted_procedural_checker_loss_count": converted_procedural_checker_loss_count,
            "ready_for_success_panel": bool(cases) and fail_count == 0,
            "ready_for_failure_case_writeup": fail_count > 0,
            "ready_for_full_visual_quality_claim": False,
            "blockers": sorted(blockers),
        },
        "cases": cases,
        "claim_boundary": {
            "allowed": [
                "Use this as static USD-network diagnosis for the two supplemental missing-bin fixtures.",
                "Use target-missing and checker-loss findings to guide retakes, implementation work, or bounded failure-case writeup.",
            ],
            "forbidden": [
                "Do not treat this two-case diagnostic as a population-level material-effect failure rate.",
                "Do not use a passing static gate alone as proof of visual material preservation.",
            ],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conversion-manifest", type=Path, default=DEFAULT_CONVERSION_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    report = build_supplemental_material_diagnostics(_load_json(args.conversion_manifest))
    report["inputs"] = {
        "conversion_manifest": {
            "path": str(args.conversion_manifest),
            "hash_sha256": _sha256(args.conversion_manifest),
        }
    }
    report["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256(Path(__file__).resolve()),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} cases={report['summary']['case_count']} "
        f"failures={report['summary']['fail_count']} "
        f"blockers={','.join(report['summary']['blockers'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
