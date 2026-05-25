#!/usr/bin/env python3
"""Build condition records for supplemental material-effect wrapper stages."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline"
DEFAULT_WRAPPER_MANIFEST = RAW_DIR / "supplemental_wrapper_stage_manifest.json"
DEFAULT_OUTPUT = RAW_DIR / "supplemental_conversion_manifest.json"
DEFAULT_NVIDIA_OUTPUT_ROOT = Path(
    "/cpfs/user/zhuzihou/assets/convertasset_research/experiments/"
    "material_effect_baseline/nvidia_asset_converter_supplemental"
)

CONDITION_ORIGINAL = "original_MDL"
CONDITION_CONVERTASSET = "existing_noMDL"
CONDITION_NVIDIA = "nvidia_asset_converter_preview_or_bake"
CONDITIONS = [CONDITION_ORIGINAL, CONDITION_CONVERTASSET, CONDITION_NVIDIA]

StageInspector = Callable[[Path], dict[str, Any]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_size(path: Path | None) -> int | None:
    return path.stat().st_size if path is not None and path.exists() and path.is_file() else None


def _default_stage_inspector(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "inspection_status": "missing_path",
            "stage_opened": False,
            "shader_count": None,
            "preview_surface_count": None,
            "active_mdl_shader_count": None,
            "error": "path_missing",
        }
    try:
        from pxr import Usd
    except Exception as exc:  # pragma: no cover - requires Isaac/PXR env
        return {
            "inspection_status": "pxr_unavailable",
            "stage_opened": None,
            "shader_count": None,
            "preview_surface_count": None,
            "active_mdl_shader_count": None,
            "error": f"pxr_import_failed:{exc}",
        }
    try:
        stage = Usd.Stage.Open(str(path))
    except Exception as exc:  # pragma: no cover - malformed USD only
        return {
            "inspection_status": "stage_open_failed",
            "stage_opened": False,
            "shader_count": None,
            "preview_surface_count": None,
            "active_mdl_shader_count": None,
            "error": f"stage_open_failed:{exc}",
        }
    if stage is None:
        return {
            "inspection_status": "stage_open_returned_none",
            "stage_opened": False,
            "shader_count": None,
            "preview_surface_count": None,
            "active_mdl_shader_count": None,
            "error": "stage_open_returned_none",
        }

    shader_count = 0
    preview_surface_count = 0
    active_mdl_shader_count = 0
    for prim in stage.Traverse():
        if prim.GetTypeName() != "Shader":
            continue
        shader_count += 1
        id_attr = prim.GetAttribute("info:id")
        if id_attr and id_attr.Get() == "UsdPreviewSurface":
            preview_surface_count += 1
        source_attr = prim.GetAttribute("info:implementationSource")
        asset_attr = prim.GetAttribute("info:mdl:sourceAsset")
        if source_attr and source_attr.Get() == "sourceAsset" and asset_attr and asset_attr.Get():
            active_mdl_shader_count += 1
    return {
        "inspection_status": "ok",
        "stage_opened": True,
        "shader_count": shader_count,
        "preview_surface_count": preview_surface_count,
        "active_mdl_shader_count": active_mdl_shader_count,
    }


def _nomdl_path(original_path: Path) -> Path:
    return original_path.with_name(f"{original_path.stem}_noMDL{original_path.suffix}")


def _nvidia_output_path(output_root: Path, effect: str, original_path: Path) -> Path:
    return output_root / effect / f"{original_path.stem}_nvidia_usd_to_usd_preview.usd"


def _static_gate_passed(condition: str, exists: bool, inspection: dict[str, Any]) -> bool:
    if not exists:
        return False
    if inspection.get("inspection_status") != "ok" or not inspection.get("stage_opened"):
        return False
    if condition == CONDITION_ORIGINAL:
        return (inspection.get("active_mdl_shader_count") or 0) > 0
    return (
        (inspection.get("preview_surface_count") or 0) > 0
        and inspection.get("active_mdl_shader_count") == 0
    )


def _condition_record(
    *,
    condition: str,
    usd_path: Path,
    provenance: dict[str, Any],
    stage_inspector: StageInspector,
) -> dict[str, Any]:
    exists = usd_path.exists()
    inspection = stage_inspector(usd_path) if exists else {
        "inspection_status": "missing_path",
        "stage_opened": False,
        "shader_count": None,
        "preview_surface_count": None,
        "active_mdl_shader_count": None,
        "error": "path_missing",
    }
    static_gate_passed = _static_gate_passed(condition, exists, inspection)
    if static_gate_passed:
        status = "available"
    elif exists:
        status = "static_gate_failed"
    else:
        status = "missing"
    record = {
        "condition": condition,
        "status": status,
        "usd_path": str(usd_path),
        "exists": exists,
        "hash_sha256": _sha256(usd_path),
        "size_bytes": _file_size(usd_path),
        "static_gate_passed": static_gate_passed,
        "inspection_status": inspection.get("inspection_status"),
        "stage_opened": inspection.get("stage_opened"),
        "shader_count": inspection.get("shader_count"),
        "preview_surface_count": inspection.get("preview_surface_count"),
        "active_mdl_shader_count": inspection.get("active_mdl_shader_count"),
        "provenance": provenance,
    }
    if "error" in inspection:
        record["inspection_error"] = inspection["error"]
    return record


def _failure_case(sample_id: str, effect: str, condition: str, status: str) -> dict[str, str]:
    return {
        "sample_id": sample_id,
        "effect": effect,
        "condition": condition,
        "status": status,
        "reason": "supplemental_condition_static_gate_failed"
        if status == "static_gate_failed"
        else "supplemental_condition_missing",
    }


def build_supplemental_conversion_manifest(
    wrapper_manifest: dict[str, Any],
    *,
    nvidia_output_root: Path = DEFAULT_NVIDIA_OUTPUT_ROOT,
    stage_inspector: StageInspector = _default_stage_inspector,
    generated_at_utc: str | None = None,
    generator_git_commit: str | None = None,
) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    failure_cases: list[dict[str, str]] = []
    condition_status_counts: dict[str, Counter[str]] = {condition: Counter() for condition in CONDITIONS}

    for wrapper in wrapper_manifest.get("wrappers", []):
        sample_id = str(wrapper.get("wrapper_id"))
        effect = str(wrapper.get("effect"))
        original_path = Path(str(wrapper.get("wrapper_stage")))
        nomdl_path = _nomdl_path(original_path)
        nvidia_path = _nvidia_output_path(nvidia_output_root, effect, original_path)
        conditions = {
            CONDITION_ORIGINAL: _condition_record(
                condition=CONDITION_ORIGINAL,
                usd_path=original_path,
                provenance={"source": "supplemental_wrapper_stage_manifest"},
                stage_inspector=stage_inspector,
            ),
            CONDITION_CONVERTASSET: _condition_record(
                condition=CONDITION_CONVERTASSET,
                usd_path=nomdl_path,
                provenance={"source": "ConvertAsset no-mdl CLI", "input_usd": str(original_path)},
                stage_inspector=stage_inspector,
            ),
            CONDITION_NVIDIA: _condition_record(
                condition=CONDITION_NVIDIA,
                usd_path=nvidia_path,
                provenance={
                    "source": "NVIDIA omni.kit.asset_converter",
                    "input_usd": str(original_path),
                    "preferred_route": "usd_to_usd_preview",
                },
                stage_inspector=stage_inspector,
            ),
        }
        for condition, record in conditions.items():
            condition_status_counts[condition][str(record["status"])] += 1
            if condition != CONDITION_ORIGINAL and record["status"] != "available":
                failure_cases.append(_failure_case(sample_id, effect, condition, str(record["status"])))
        samples.append(
            {
                "sample_id": sample_id,
                "source": "supplemental_official_sample_wrapper",
                "target_category": "supplemental_material_fixture",
                "present_effects": [effect],
                "material_path": wrapper.get("material_path"),
                "target_prim_path": wrapper.get("target_prim_path"),
                "conditions": conditions,
            }
        )

    original_available = sum(1 for sample in samples if sample["conditions"][CONDITION_ORIGINAL]["status"] == "available")
    convertasset_available = sum(1 for sample in samples if sample["conditions"][CONDITION_CONVERTASSET]["status"] == "available")
    nvidia_available = sum(1 for sample in samples if sample["conditions"][CONDITION_NVIDIA]["status"] == "available")
    nvidia_static_failed = sum(
        1 for sample in samples if sample["conditions"][CONDITION_NVIDIA]["status"] == "static_gate_failed"
    )
    missing_outputs = [
        case
        for case in failure_cases
        if case["status"] == "missing"
    ]
    blockers: list[str] = []
    if missing_outputs:
        blockers.append("supplemental_condition_outputs_missing")
    if nvidia_static_failed:
        blockers.append("supplemental_nvidia_static_gate_failed")
    if not samples:
        blockers.append("no_supplemental_wrappers")

    ready_for_effect_table = bool(samples) and not missing_outputs

    return {
        "schema_version": 1,
        "status": "supplemental_conversion_manifest",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_conversion_manifest.py",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "generator_git_commit": generator_git_commit or _git_commit(),
        "summary": {
            "sample_count": len(samples),
            "original_available_count": original_available,
            "convertasset_available_count": convertasset_available,
            "nvidia_available_count": nvidia_available,
            "nvidia_static_gate_failed_count": nvidia_static_failed,
            "failure_case_count": len(failure_cases),
            "condition_status_counts": {
                condition: dict(sorted(counter.items()))
                for condition, counter in condition_status_counts.items()
            },
            "ready_for_effect_table_regeneration": ready_for_effect_table,
            "ready_for_full_claim": False,
            "blockers": blockers,
        },
        "samples": samples,
        "failure_cases": failure_cases,
        "claim_boundary": {
            "allowed": [
                "This manifest records original, ConvertAsset no-MDL, and NVIDIA condition availability for supplemental clearcoat/procedural wrappers.",
                "Static-gate failures can seed reviewer-facing failure-case review.",
            ],
            "forbidden": [
                "Do not treat static gates as visual quality evidence.",
                "Do not claim all material effects are reliable until rendered qualitative evidence is reviewed.",
            ],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wrapper-manifest", type=Path, default=DEFAULT_WRAPPER_MANIFEST)
    parser.add_argument("--nvidia-output-root", type=Path, default=DEFAULT_NVIDIA_OUTPUT_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    manifest = build_supplemental_conversion_manifest(
        _load_json(args.wrapper_manifest),
        nvidia_output_root=args.nvidia_output_root,
    )
    manifest["inputs"] = {
        "wrapper_manifest": {
            "path": str(args.wrapper_manifest),
            "hash_sha256": _sha256(args.wrapper_manifest),
        },
        "nvidia_output_root": str(args.nvidia_output_root),
    }
    manifest["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256(Path(__file__).resolve()),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} samples={manifest['summary']['sample_count']} "
        f"nvidia_available={manifest['summary']['nvidia_available_count']} "
        f"nvidia_static_failed={manifest['summary']['nvidia_static_gate_failed_count']}"
    )
    return 0 if manifest["summary"]["ready_for_effect_table_regeneration"] else 1


if __name__ == "__main__":
    import sys

    raise SystemExit(main())
