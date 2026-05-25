#!/usr/bin/env python3
"""Build selected three-condition qualitative render jobs for material effects."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline"
GRSCENES_RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_EFFECT_MANIFEST = RAW_DIR / "effect_sample_manifest.json"
DEFAULT_BASELINE_MANIFEST = RAW_DIR / "baseline_conversion_manifest.json"
DEFAULT_STRESS_RENDER_MANIFEST = GRSCENES_RAW_DIR / "retake_zoom_render_manifest.json"
DEFAULT_OUTPUT_ROOT = RAW_DIR / "qualitative_renders"
DEFAULT_OUTPUT = RAW_DIR / "qualitative_render_manifest.json"
DEFAULT_MAX_CASES = 6
DEFAULT_MIN_CASES = 4
EFFECT_ORDER = [
    "clearcoat",
    "opacity_transparency",
    "emission",
    "procedural_texture",
    "normal_bump",
    "displacement_height",
]
CONDITION_ORDER = [
    "original_MDL",
    "existing_noMDL",
    "nvidia_asset_converter_preview_or_bake",
]
STRESS_CONDITION_BY_BASELINE = {
    "original_MDL": "original",
    "existing_noMDL": "converted",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


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


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _effect_order(effect_manifest: dict[str, Any]) -> list[str]:
    order = effect_manifest.get("effect_order") or EFFECT_ORDER
    return [effect for effect in order if isinstance(effect, str)]


def _present_effects(sample: dict[str, Any], effect_order: list[str]) -> list[str]:
    present = set(sample.get("present_effects") or [])
    return [effect for effect in effect_order if effect in present]


def _sample_sort_key(sample: dict[str, Any]) -> tuple[int, str, str, str]:
    verdict = str((sample.get("visual_review") or {}).get("verdict") or "")
    verdict_score = {"PASS": 0, "WARN": 1}.get(verdict, 2)
    return (
        verdict_score,
        str(sample.get("target_category") or ""),
        str(sample.get("source_scene_id") or ""),
        str(sample.get("sample_id") or sample.get("pair_id") or ""),
    )


def _baseline_by_sample(baseline_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(sample.get("sample_id")): sample for sample in baseline_manifest.get("samples", [])}


def _stress_record_lookup(stress_render_manifest: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for record in stress_render_manifest.get("records", []):
        out[(str(record.get("pair_id")), str(record.get("material_condition")))] = record
    return out


def _has_available_conditions(baseline_sample: dict[str, Any] | None) -> bool:
    if not baseline_sample:
        return False
    conditions = baseline_sample.get("conditions") or {}
    return all((conditions.get(condition) or {}).get("status") == "available" for condition in CONDITION_ORDER)


def select_representative_cases(
    effect_manifest: dict[str, Any],
    baseline_manifest: dict[str, Any],
    stress_render_manifest: dict[str, Any],
    *,
    max_cases: int = DEFAULT_MAX_CASES,
    min_cases: int = DEFAULT_MIN_CASES,
) -> list[dict[str, Any]]:
    if max_cases <= 0:
        raise ValueError("max_cases must be positive")
    max_cases = int(max_cases)
    min_cases = max(0, min(int(min_cases), max_cases))
    effect_order = _effect_order(effect_manifest)
    gaps = set((effect_manifest.get("summary") or {}).get("effect_gaps") or [])
    covered_bins = [effect for effect in effect_order if effect not in gaps]
    baseline_lookup = _baseline_by_sample(baseline_manifest)
    stress_lookup = _stress_record_lookup(stress_render_manifest)
    eligible: list[dict[str, Any]] = []
    for sample in effect_manifest.get("samples", []):
        sample_id = str(sample.get("sample_id") or "")
        pair_id = str(sample.get("pair_id") or sample_id)
        if not sample_id or not _has_available_conditions(baseline_lookup.get(sample_id)):
            continue
        if (pair_id, "original") not in stress_lookup or (pair_id, "converted") not in stress_lookup:
            continue
        effects = [effect for effect in _present_effects(sample, effect_order) if effect in covered_bins]
        if not effects:
            continue
        eligible.append({**sample, "covered_effects": effects})

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    covered: set[str] = set()

    def add_case(sample: dict[str, Any]) -> None:
        sample_id = str(sample.get("sample_id"))
        if sample_id in selected_ids or len(selected) >= max_cases:
            return
        selected.append(sample)
        selected_ids.add(sample_id)
        covered.update(sample.get("covered_effects") or [])

    for effect in covered_bins:
        if effect in covered:
            continue
        candidates = [sample for sample in eligible if effect in sample.get("covered_effects", [])]
        if candidates:
            add_case(sorted(candidates, key=_sample_sort_key)[0])

    while len(selected) < min_cases:
        used_categories = {str(sample.get("target_category") or "") for sample in selected}
        remaining = [sample for sample in eligible if str(sample.get("sample_id")) not in selected_ids]
        if not remaining:
            break
        sample = sorted(
            remaining,
            key=lambda item: (
                0 if str(item.get("target_category") or "") not in used_categories else 1,
                *_sample_sort_key(item),
            ),
        )[0]
        add_case(sample)
    return selected


def _image_record(path: str | Path, *, width: int | None = None, height: int | None = None) -> dict[str, Any]:
    image_path = Path(path)
    exists = image_path.is_file()
    return {
        "path": str(image_path),
        "exists": exists,
        "status": "ready" if exists else "missing",
        "hash_sha256": _sha256_file(image_path) if exists else None,
        "bytes": image_path.stat().st_size if exists else 0,
        "width": width,
        "height": height,
    }


def _safe_path_part(value: Any) -> str:
    return str(value or "unknown").replace("/", "_").replace(" ", "_")


def _render_command(
    *,
    camera_stage_path: Path,
    camera_prim_path: str,
    output_dir: Path,
    prefix: str,
    width: int,
    height: int,
    start_frame: int,
    end_frame: int,
    renderer: str,
    wait_frames: int,
) -> list[str]:
    return [
        "./scripts/isaac_python.sh",
        "scripts/render_with_viewport_capture.py",
        "--usd-path",
        str(camera_stage_path),
        "--camera",
        camera_prim_path,
        "--output-dir",
        str(output_dir),
        "--prefix",
        prefix,
        "--ext",
        "png",
        "--width",
        str(width),
        "--height",
        str(height),
        "--start-frame",
        str(start_frame),
        "--end-frame",
        str(end_frame),
        "--frame-step",
        "1",
        "--renderer",
        renderer,
        "--wait-frames",
        str(wait_frames),
        "--headless",
    ]


def _existing_condition_record(
    *,
    selected: dict[str, Any],
    baseline_sample: dict[str, Any],
    stress_record: dict[str, Any],
    baseline_condition: str,
    width: int,
    height: int,
) -> dict[str, Any]:
    image_path = stress_record.get("output_image") or (stress_record.get("image") or {}).get("path")
    image = _image_record(image_path, width=width, height=height)
    condition = (baseline_sample.get("conditions") or {}).get(baseline_condition) or {}
    return {
        "sample_id": selected.get("sample_id"),
        "pair_id": selected.get("pair_id"),
        "source_scene_id": selected.get("source_scene_id"),
        "target_category": selected.get("target_category"),
        "target_id": selected.get("target_id"),
        "covered_effects": selected.get("covered_effects"),
        "condition": baseline_condition,
        "status": "image_ready" if image["exists"] else "image_missing",
        "usd_path": condition.get("usd_path") or stress_record.get("usd_path"),
        "camera": stress_record.get("camera"),
        "camera_stage_path": stress_record.get("camera_stage_path"),
        "image": image,
        "source_record": {
            "material_condition": stress_record.get("material_condition"),
            "sample_id": stress_record.get("sample_id"),
        },
    }


def _nvidia_condition_record(
    *,
    selected: dict[str, Any],
    baseline_sample: dict[str, Any],
    source_stress_record: dict[str, Any],
    output_root: Path,
    renderer_settings: dict[str, Any],
) -> dict[str, Any]:
    pair_id = str(selected.get("pair_id") or selected.get("sample_id"))
    camera = dict(source_stress_record.get("camera") or {})
    view_id = str(camera.get("view_id") or pair_id.split(".")[-1] or "view")
    scene = _safe_path_part(selected.get("source_scene_id"))
    target = _safe_path_part(selected.get("target_id"))
    output_dir = output_root / scene / target / view_id / "nvidia"
    camera_stage_path = output_dir / "nvidia_camera.usd"
    image_path = output_dir / "nvidia_0000.png"
    width = int(renderer_settings.get("image_width") or (source_stress_record.get("image") or {}).get("width") or 600)
    height = int(renderer_settings.get("image_height") or (source_stress_record.get("image") or {}).get("height") or 450)
    renderer = str(renderer_settings.get("renderer") or "RayTracedLighting")
    wait_frames = int(renderer_settings.get("wait_frames") or 8)
    start_frame = int(camera.get("start_frame", 0))
    end_frame = int(camera.get("end_frame", 0))
    condition = (baseline_sample.get("conditions") or {}).get("nvidia_asset_converter_preview_or_bake") or {}
    image = _image_record(image_path, width=width, height=height)
    return {
        "sample_id": selected.get("sample_id"),
        "pair_id": selected.get("pair_id"),
        "source_scene_id": selected.get("source_scene_id"),
        "target_category": selected.get("target_category"),
        "target_id": selected.get("target_id"),
        "covered_effects": selected.get("covered_effects"),
        "condition": "nvidia_asset_converter_preview_or_bake",
        "status": "render_ready" if image["exists"] else "render_pending",
        "usd_path": condition.get("usd_path"),
        "preferred_smoke_attempt": condition.get("preferred_smoke_attempt"),
        "camera": camera,
        "camera_stage_path": str(camera_stage_path),
        "camera_stage_exists": camera_stage_path.is_file(),
        "image": image,
        "render_command": _render_command(
            camera_stage_path=camera_stage_path,
            camera_prim_path=str(camera.get("camera_prim_path") or "/World/GRScenesVLMTargetCamera"),
            output_dir=output_dir,
            prefix="nvidia",
            width=width,
            height=height,
            start_frame=start_frame,
            end_frame=end_frame,
            renderer=renderer,
            wait_frames=wait_frames,
        ),
    }


def build_qualitative_render_manifest(
    effect_manifest: dict[str, Any],
    baseline_manifest: dict[str, Any],
    stress_render_manifest: dict[str, Any],
    *,
    output_root: Path,
    max_cases: int = DEFAULT_MAX_CASES,
    min_cases: int = DEFAULT_MIN_CASES,
) -> dict[str, Any]:
    effect_order = _effect_order(effect_manifest)
    selected = select_representative_cases(
        effect_manifest,
        baseline_manifest,
        stress_render_manifest,
        max_cases=max_cases,
        min_cases=min_cases,
    )
    baseline_lookup = _baseline_by_sample(baseline_manifest)
    stress_lookup = _stress_record_lookup(stress_render_manifest)
    renderer_settings = stress_render_manifest.get("renderer_settings") or {}
    width = int(renderer_settings.get("image_width") or 600)
    height = int(renderer_settings.get("image_height") or 450)

    records: list[dict[str, Any]] = []
    selected_cases: list[dict[str, Any]] = []
    for sample in selected:
        sample_id = str(sample.get("sample_id"))
        pair_id = str(sample.get("pair_id") or sample_id)
        baseline_sample = baseline_lookup[sample_id]
        original_record = stress_lookup[(pair_id, "original")]
        converted_record = stress_lookup[(pair_id, "converted")]
        case_records = [
            _existing_condition_record(
                selected=sample,
                baseline_sample=baseline_sample,
                stress_record=original_record,
                baseline_condition="original_MDL",
                width=width,
                height=height,
            ),
            _existing_condition_record(
                selected=sample,
                baseline_sample=baseline_sample,
                stress_record=converted_record,
                baseline_condition="existing_noMDL",
                width=width,
                height=height,
            ),
            _nvidia_condition_record(
                selected=sample,
                baseline_sample=baseline_sample,
                source_stress_record=original_record,
                output_root=Path(output_root),
                renderer_settings=renderer_settings,
            ),
        ]
        records.extend(case_records)
        selected_cases.append(
            {
                "sample_id": sample_id,
                "pair_id": pair_id,
                "source_scene_id": sample.get("source_scene_id"),
                "target_category": sample.get("target_category"),
                "target_id": sample.get("target_id"),
                "visual_review": sample.get("visual_review"),
                "covered_effects": sample.get("covered_effects"),
                "condition_statuses": {record["condition"]: record["status"] for record in case_records},
            }
        )

    ready_image_records = [record for record in records if record.get("image", {}).get("status") == "ready"]
    nvidia_pending = [
        record
        for record in records
        if record["condition"] == "nvidia_asset_converter_preview_or_bake" and record["status"] != "render_ready"
    ]
    ready_case_count = 0
    for case in selected_cases:
        statuses = case["condition_statuses"]
        if statuses.get("original_MDL") == "image_ready" and statuses.get("existing_noMDL") == "image_ready" and statuses.get("nvidia_asset_converter_preview_or_bake") == "render_ready":
            ready_case_count += 1

    selected_effect_counts = {effect: 0 for effect in effect_order}
    for case in selected_cases:
        for effect in case.get("covered_effects") or []:
            selected_effect_counts[effect] = selected_effect_counts.get(effect, 0) + 1

    blockers: list[str] = []
    if not selected_cases:
        blockers.append("no_representative_cases")
    if nvidia_pending:
        blockers.append("nvidia_qualitative_renders_missing")
    effect_gaps = list((effect_manifest.get("summary") or {}).get("effect_gaps") or [])
    if effect_gaps:
        blockers.append("effect_groups_need_official_sample_or_more_grscenes_assets")

    ready_for_contact_sheet = bool(selected_cases) and ready_case_count == len(selected_cases)
    return {
        "schema_version": 1,
        "status": "material_effect_qualitative_render_manifest",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/build_qualitative_render_manifest.py",
        "generated_at_utc": _utc_now(),
        "generator_git_commit": _git_commit(),
        "condition_order": CONDITION_ORDER,
        "effect_order": effect_order,
        "output_root": str(output_root),
        "summary": {
            "selected_case_count": len(selected_cases),
            "ready_case_count": ready_case_count,
            "condition_record_count": len(records),
            "ready_image_record_count": len(ready_image_records),
            "nvidia_render_pending_count": len(nvidia_pending),
            "selected_effect_counts": selected_effect_counts,
            "effect_gaps": effect_gaps,
            "ready_for_contact_sheet": ready_for_contact_sheet,
            "ready_for_visual_quality_claim": ready_for_contact_sheet and not effect_gaps,
            "blockers": _dedupe(blockers),
        },
        "selected_cases": selected_cases,
        "records": records,
        "claim_boundary": {
            "qualitative_only": True,
            "full_effect_coverage_requires": ["clearcoat", "procedural_texture"],
            "nvidia_visual_comparison_requires": "all selected NVIDIA render records must be render_ready",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effect-manifest", type=Path, default=DEFAULT_EFFECT_MANIFEST)
    parser.add_argument("--baseline-manifest", type=Path, default=DEFAULT_BASELINE_MANIFEST)
    parser.add_argument("--stress-render-manifest", type=Path, default=DEFAULT_STRESS_RENDER_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-cases", type=int, default=DEFAULT_MAX_CASES)
    parser.add_argument("--min-cases", type=int, default=DEFAULT_MIN_CASES)
    args = parser.parse_args(argv)

    manifest = build_qualitative_render_manifest(
        _load_json(args.effect_manifest),
        _load_json(args.baseline_manifest),
        _load_json(args.stress_render_manifest),
        output_root=args.output_root,
        max_cases=args.max_cases,
        min_cases=args.min_cases,
    )
    manifest["inputs"] = {
        "effect_manifest": {"path": str(args.effect_manifest), "hash_sha256": _sha256_file(args.effect_manifest)},
        "baseline_manifest": {"path": str(args.baseline_manifest), "hash_sha256": _sha256_file(args.baseline_manifest)},
        "stress_render_manifest": {
            "path": str(args.stress_render_manifest),
            "hash_sha256": _sha256_file(args.stress_render_manifest),
        },
    }
    manifest["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} selected={manifest['summary']['selected_case_count']} "
        f"ready_cases={manifest['summary']['ready_case_count']} "
        f"nvidia_pending={manifest['summary']['nvidia_render_pending_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
