#!/usr/bin/env python3
"""Build sample-level condition records for the material-effect baseline."""

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
RAW_ROOT = PROJECT_ROOT / "paper/shared/evidence/raw"
DEFAULT_EFFECT_MANIFEST = RAW_ROOT / "material_effect_baseline/effect_sample_manifest.json"
DEFAULT_NVIDIA_SMOKE = RAW_ROOT / "material_effect_baseline/nvidia_baseline_smoke_manifest.json"
DEFAULT_NOMDL_RUN_REPORT = RAW_ROOT / "grscene_vlm_grounding/full_nomdl_multi_root_run_report.json"
DEFAULT_OUTPUT = RAW_ROOT / "material_effect_baseline/baseline_conversion_manifest.json"
DEFAULT_NVIDIA_OUTPUT_ROOT = Path(
    "/cpfs/user/zhuzihou/assets/convertasset_research/experiments/"
    "material_effect_baseline/nvidia_asset_converter_samples"
)

CONDITION_ORIGINAL = "original_MDL"
CONDITION_CONVERTASSET = "existing_noMDL"
CONDITION_NVIDIA = "nvidia_asset_converter_preview_or_bake"

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


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in text)


def _default_stage_inspector(path: Path) -> dict[str, Any]:
    """Inspect USD material counts when pxr is available."""

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
    except Exception as exc:  # pragma: no cover - depends on Isaac/PXR env
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
    except Exception as exc:  # pragma: no cover - depends on malformed USD
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
        shader_id = id_attr.Get() if id_attr else None
        if shader_id == "UsdPreviewSurface":
            preview_surface_count += 1
        source_attr = prim.GetAttribute("info:implementationSource")
        if source_attr and source_attr.Get() == "sourceAsset":
            source_asset = prim.GetAttribute("info:mdl:sourceAsset")
            if source_asset and source_asset.Get():
                active_mdl_shader_count += 1
    return {
        "inspection_status": "ok",
        "stage_opened": True,
        "shader_count": shader_count,
        "preview_surface_count": preview_surface_count,
        "active_mdl_shader_count": active_mdl_shader_count,
    }


def _nomdl_records_by_scene(run_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    jobs_by_id = {
        str(job.get("conversion_job_id")): job
        for job in run_report.get("jobs", [])
        if job.get("conversion_job_id")
    }
    records: dict[str, dict[str, Any]] = {}
    for result in run_report.get("results", []):
        job_id = str(result.get("conversion_job_id") or "")
        job = jobs_by_id.get(job_id, {})
        scene_id = job.get("source_scene_id")
        if not scene_id and job_id:
            parts = job_id.split(":")
            if len(parts) >= 2:
                scene_id = parts[1]
        if not scene_id:
            continue
        records[str(scene_id)] = {
            "conversion_job_id": job_id,
            "source_scene_id": str(scene_id),
            "source_scene_split": job.get("source_scene_split"),
            "source_usd": job.get("source_usd"),
            "scratch_input_usd": result.get("scratch_input_usd") or job.get("scratch_input_usd"),
            "convertasset_output_usd": result.get("top_output_usd")
            or job.get("expected_top_output_usd"),
            "processor_done_count": result.get("processor_done_count"),
        }
    return records


def _preferred_smoke_attempt(smoke_manifest: dict[str, Any]) -> dict[str, Any] | None:
    usable = (smoke_manifest.get("summary") or {}).get("usable_usd_baseline_attempts") or []
    attempts_by_name = {attempt.get("name"): attempt for attempt in smoke_manifest.get("attempts", [])}
    for name in usable:
        attempt = attempts_by_name.get(name)
        if attempt and str(attempt.get("output_path", name)).lower().endswith((".usd", ".usda", ".usdc")):
            return attempt
        if attempt and name.startswith("usd_to_usd"):
            return attempt
    return None


def _inspect_cached(
    path: Path,
    inspector: StageInspector,
    cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    key = str(path)
    if key not in cache:
        cache[key] = inspector(path)
    return dict(cache[key])


def _sha256_cached(path: Path | None, cache: dict[str, str | None]) -> str | None:
    if path is None:
        return None
    key = str(path)
    if key not in cache:
        cache[key] = _sha256(path)
    return cache[key]


def _static_gate_passed(condition: str, exists: bool, inspection: dict[str, Any]) -> bool:
    if not exists:
        return False
    if inspection.get("inspection_status") != "ok" or not inspection.get("stage_opened"):
        return False
    if condition in {CONDITION_CONVERTASSET, CONDITION_NVIDIA}:
        return (
            (inspection.get("preview_surface_count") or 0) > 0
            and inspection.get("active_mdl_shader_count") == 0
        )
    return (inspection.get("active_mdl_shader_count") or 0) > 0


def _condition_record(
    *,
    condition: str,
    usd_path: Path | None,
    provenance: dict[str, Any],
    stage_inspector: StageInspector,
    inspection_cache: dict[str, dict[str, Any]],
    hash_cache: dict[str, str | None],
    status_override: str | None = None,
    preferred_smoke_attempt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    exists = bool(usd_path and usd_path.exists())
    if usd_path:
        inspection = _inspect_cached(usd_path, stage_inspector, inspection_cache)
    else:
        inspection = {
            "inspection_status": "no_path",
            "stage_opened": False,
            "shader_count": None,
            "preview_surface_count": None,
            "active_mdl_shader_count": None,
        }
    static_gate_passed = _static_gate_passed(condition, exists, inspection)
    if status_override:
        status = status_override
    elif static_gate_passed:
        status = "available"
    elif exists:
        status = "static_gate_failed"
    else:
        status = "missing"

    record = {
        "condition": condition,
        "status": status,
        "usd_path": str(usd_path) if usd_path else None,
        "exists": exists,
        "hash_sha256": _sha256_cached(usd_path, hash_cache),
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
    if preferred_smoke_attempt is not None:
        record["preferred_smoke_attempt"] = preferred_smoke_attempt.get("name")
        record["context_flags"] = preferred_smoke_attempt.get("context_flags") or {}
    return record


def _nvidia_output_path(output_root: Path, source_scene_id: str, smoke_attempt_name: str) -> Path:
    return (
        output_root
        / _slug(source_scene_id)
        / f"start_result_raw_nvidia_{_slug(smoke_attempt_name)}.usd"
    )


def _count_available(samples: list[dict[str, Any]], condition: str) -> int:
    return sum(
        1
        for sample in samples
        if sample["conditions"][condition].get("status") == "available"
    )


def build_baseline_conversion_manifest(
    effect_manifest: dict[str, Any],
    nomdl_run_report: dict[str, Any],
    nvidia_smoke_manifest: dict[str, Any],
    *,
    nvidia_output_root: Path = DEFAULT_NVIDIA_OUTPUT_ROOT,
    stage_inspector: StageInspector = _default_stage_inspector,
    generated_at_utc: str | None = None,
    generator_git_commit: str | None = None,
) -> dict[str, Any]:
    nomdl_by_scene = _nomdl_records_by_scene(nomdl_run_report)
    preferred_attempt = _preferred_smoke_attempt(nvidia_smoke_manifest)
    smoke_ready = bool((nvidia_smoke_manifest.get("summary") or {}).get("ready_for_sample_baseline"))
    inspection_cache: dict[str, dict[str, Any]] = {}
    hash_cache: dict[str, str | None] = {}
    samples: list[dict[str, Any]] = []
    missing_nomdl_scene_ids: list[str] = []
    nvidia_missing_count = 0
    condition_status_counts: dict[str, Counter[str]] = {
        CONDITION_ORIGINAL: Counter(),
        CONDITION_CONVERTASSET: Counter(),
        CONDITION_NVIDIA: Counter(),
    }

    for sample in effect_manifest.get("samples", []):
        source_scene_id = str(sample.get("source_scene_id") or "")
        nomdl_record = nomdl_by_scene.get(source_scene_id)
        if nomdl_record is None:
            missing_nomdl_scene_ids.append(source_scene_id)
        source_usd = Path(nomdl_record["source_usd"]) if nomdl_record and nomdl_record.get("source_usd") else None
        scratch_input_usd = (
            Path(nomdl_record["scratch_input_usd"])
            if nomdl_record and nomdl_record.get("scratch_input_usd")
            else None
        )
        convertasset_usd = (
            Path(nomdl_record["convertasset_output_usd"])
            if nomdl_record and nomdl_record.get("convertasset_output_usd")
            else None
        )
        nvidia_path = (
            _nvidia_output_path(nvidia_output_root, source_scene_id, str(preferred_attempt.get("name")))
            if preferred_attempt and source_scene_id
            else None
        )
        nvidia_status_override = None
        if not smoke_ready or preferred_attempt is None:
            nvidia_status_override = "smoke_not_ready"
        elif nvidia_path is not None and not nvidia_path.exists():
            nvidia_status_override = "planned_output_missing"
            nvidia_missing_count += 1

        conditions = {
            CONDITION_ORIGINAL: _condition_record(
                condition=CONDITION_ORIGINAL,
                usd_path=scratch_input_usd or source_usd,
                provenance={
                    "source": "full_nomdl_multi_root_run_report",
                    "conversion_job_id": nomdl_record.get("conversion_job_id") if nomdl_record else None,
                    "source_usd": str(source_usd) if source_usd else None,
                    "scratch_input_usd": str(scratch_input_usd) if scratch_input_usd else None,
                    "source_scene_split": nomdl_record.get("source_scene_split") if nomdl_record else None,
                },
                stage_inspector=stage_inspector,
                inspection_cache=inspection_cache,
                hash_cache=hash_cache,
            ),
            CONDITION_CONVERTASSET: _condition_record(
                condition=CONDITION_CONVERTASSET,
                usd_path=convertasset_usd,
                provenance={
                    "source": "full_nomdl_multi_root_run_report",
                    "conversion_job_id": nomdl_record.get("conversion_job_id") if nomdl_record else None,
                    "processor_done_count": nomdl_record.get("processor_done_count") if nomdl_record else None,
                },
                stage_inspector=stage_inspector,
                inspection_cache=inspection_cache,
                hash_cache=hash_cache,
            ),
            CONDITION_NVIDIA: _condition_record(
                condition=CONDITION_NVIDIA,
                usd_path=nvidia_path,
                provenance={
                    "source": "nvidia_baseline_smoke_manifest",
                    "output_root": str(nvidia_output_root),
                    "planned_scene_level_output": True,
                },
                stage_inspector=stage_inspector,
                inspection_cache=inspection_cache,
                hash_cache=hash_cache,
                status_override=nvidia_status_override,
                preferred_smoke_attempt=preferred_attempt,
            ),
        }
        for condition, record in conditions.items():
            condition_status_counts[condition][str(record.get("status"))] += 1
        samples.append(
            {
                "sample_id": sample.get("sample_id"),
                "source_scene_id": source_scene_id,
                "target_category": sample.get("target_category"),
                "target_prim_path": (sample.get("material_model") or {}).get("target_prim_path"),
                "present_effects": sample.get("present_effects") or [],
                "conditions": conditions,
            }
        )

    original_available = _count_available(samples, CONDITION_ORIGINAL)
    convertasset_available = _count_available(samples, CONDITION_CONVERTASSET)
    nvidia_available = _count_available(samples, CONDITION_NVIDIA)
    effect_gaps = (effect_manifest.get("summary") or {}).get("effect_gaps") or []
    blockers: list[str] = []
    if missing_nomdl_scene_ids:
        blockers.append("selected_samples_missing_nomdl_run_record")
    if original_available < len(samples) or convertasset_available < len(samples):
        blockers.append("original_or_convertasset_static_gate_incomplete")
    if nvidia_missing_count:
        blockers.append("nvidia_sample_outputs_missing")
    if not smoke_ready or preferred_attempt is None:
        blockers.append("nvidia_smoke_not_ready")
    if effect_gaps:
        blockers.append("effect_groups_need_official_sample_or_more_grscenes_assets")

    return {
        "schema_version": 1,
        "status": "baseline_conversion_manifest_ready",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/build_baseline_conversion_manifest.py",
        "generated_at_utc": generated_at_utc or _utc_now(),
        "generator_git_commit": generator_git_commit or _git_commit(),
        "summary": {
            "sample_count": len(samples),
            "unique_source_scene_count": len({sample["source_scene_id"] for sample in samples}),
            "original_available_count": original_available,
            "convertasset_available_count": convertasset_available,
            "nvidia_available_count": nvidia_available,
            "nvidia_missing_count": nvidia_missing_count,
            "condition_status_counts": {
                condition: dict(sorted(counter.items()))
                for condition, counter in condition_status_counts.items()
            },
            "preferred_nvidia_smoke_attempt": preferred_attempt.get("name") if preferred_attempt else None,
            "effect_gaps": effect_gaps,
            "ready_for_effect_tables": bool(samples),
            "ready_for_full_claim": not blockers,
            "blockers": blockers,
        },
        "samples": samples,
        "missing_nomdl_scene_ids": sorted(set(missing_nomdl_scene_ids)),
        "claim_boundary": {
            "allowed": [
                "This manifest records sample-level condition availability and static material gates."
            ],
            "forbidden": [
                "Do not claim ConvertAsset beats NVIDIA until NVIDIA sample outputs exist and paired render/table artifacts are generated.",
                "Do not claim all material effects are covered when effect_gaps is non-empty.",
            ],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effect-manifest", type=Path, default=DEFAULT_EFFECT_MANIFEST)
    parser.add_argument("--nomdl-run-report", type=Path, default=DEFAULT_NOMDL_RUN_REPORT)
    parser.add_argument("--nvidia-smoke", type=Path, default=DEFAULT_NVIDIA_SMOKE)
    parser.add_argument("--nvidia-output-root", type=Path, default=DEFAULT_NVIDIA_OUTPUT_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_baseline_conversion_manifest(
        _load_json(args.effect_manifest),
        _load_json(args.nomdl_run_report),
        _load_json(args.nvidia_smoke),
        nvidia_output_root=args.nvidia_output_root,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        f"Wrote {args.out} samples={manifest['summary']['sample_count']} "
        f"nvidia_available={manifest['summary']['nvidia_available_count']} "
        f"nvidia_missing={manifest['summary']['nvidia_missing_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
