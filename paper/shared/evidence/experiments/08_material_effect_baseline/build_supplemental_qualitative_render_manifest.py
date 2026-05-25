#!/usr/bin/env python3
"""Build supplemental material-effect qualitative render jobs."""

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
DEFAULT_CONVERSION_MANIFEST = RAW_DIR / "supplemental_conversion_manifest.json"
DEFAULT_OUTPUT_ROOT = RAW_DIR / "supplemental_qualitative_renders"
DEFAULT_OUTPUT = RAW_DIR / "supplemental_qualitative_render_manifest.json"
DEFAULT_WIDTH = 600
DEFAULT_HEIGHT = 450
DEFAULT_RENDERER = "RayTracedLighting"
DEFAULT_WAIT_FRAMES = 8
CONDITION_ORDER = [
    "original_MDL",
    "existing_noMDL",
    "nvidia_asset_converter_preview_or_bake",
]
CONDITION_PREFIX = {
    "original_MDL": "original",
    "existing_noMDL": "convertasset",
    "nvidia_asset_converter_preview_or_bake": "nvidia",
}
CONDITION_CAMERA = {
    "original_MDL": "/World/Camera",
    "existing_noMDL": "/World/Camera",
    # NVIDIA Asset Converter wraps the original camera prim under an Xform.
    "nvidia_asset_converter_preview_or_bake": "/World/Camera/Camera",
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


def _safe_path_part(value: Any) -> str:
    return str(value or "unknown").replace("/", "_").replace(" ", "_")


def _path_exists(path_text: Any) -> bool:
    return bool(path_text) and Path(str(path_text)).is_file()


def _image_record(path: Path, *, width: int, height: int) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "path": str(path),
        "exists": exists,
        "status": "ready" if exists else "missing",
        "hash_sha256": _sha256_file(path) if exists else None,
        "bytes": path.stat().st_size if exists else 0,
        "width": int(width),
        "height": int(height),
    }


def _render_command(
    *,
    usd_path: str,
    camera_prim_path: str,
    output_dir: Path,
    prefix: str,
    width: int,
    height: int,
    renderer: str,
    wait_frames: int,
) -> list[str]:
    return [
        "./scripts/isaac_python.sh",
        "scripts/render_with_viewport_capture.py",
        "--usd-path",
        str(usd_path),
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
        "0",
        "--end-frame",
        "0",
        "--frame-step",
        "1",
        "--renderer",
        renderer,
        "--wait-frames",
        str(wait_frames),
        "--headless",
    ]


def _condition_record(
    *,
    sample: dict[str, Any],
    condition_name: str,
    condition: dict[str, Any],
    output_root: Path,
    width: int,
    height: int,
    renderer: str,
    wait_frames: int,
) -> dict[str, Any]:
    sample_id = str(sample.get("sample_id") or "unknown")
    effects = [str(effect) for effect in sample.get("present_effects") or []]
    prefix = CONDITION_PREFIX[condition_name]
    output_dir = output_root / _safe_path_part(sample_id) / condition_name
    image_path = output_dir / f"{prefix}_0000.png"
    source_status = str(condition.get("status") or "missing")
    usd_path = str(condition.get("usd_path") or "")
    source_exists = _path_exists(usd_path)
    image = _image_record(image_path, width=width, height=height)
    if image["exists"]:
        status = "render_ready"
    elif source_exists:
        status = "render_pending"
    else:
        status = "source_missing"
    camera_prim_path = CONDITION_CAMERA[condition_name]
    return {
        "sample_id": sample_id,
        "pair_id": sample_id,
        "source_scene_id": "supplemental_official_sample_wrapper",
        "target_category": sample.get("target_category") or "supplemental_material_fixture",
        "target_id": sample.get("target_prim_path") or sample_id,
        "target_prim_path": sample.get("target_prim_path"),
        "covered_effects": effects,
        "condition": condition_name,
        "status": status,
        "source_condition_status": source_status,
        "static_gate_passed": bool(condition.get("static_gate_passed")),
        "usd_path": usd_path,
        "usd_exists": source_exists,
        "camera_prim_path": camera_prim_path,
        "camera_stage_path": usd_path,
        "image": image,
        "render_command": _render_command(
            usd_path=usd_path,
            camera_prim_path=camera_prim_path,
            output_dir=output_dir,
            prefix=prefix,
            width=width,
            height=height,
            renderer=renderer,
            wait_frames=wait_frames,
        ),
        "visual_expectation": {
            "target": sample.get("target_prim_path"),
            "effects": effects,
            "same_camera_family": True,
            "note": "Supplemental wrapper render for material-effect qualitative inspection.",
        },
    }


def _condition_statuses(records: list[dict[str, Any]]) -> dict[str, str]:
    return {str(record["condition"]): str(record["status"]) for record in records}


def _ready_case_count(selected_cases: list[dict[str, Any]]) -> int:
    ready = 0
    for case in selected_cases:
        statuses = case.get("condition_statuses") or {}
        if all(statuses.get(condition) == "render_ready" for condition in CONDITION_ORDER):
            ready += 1
    return ready


def build_supplemental_qualitative_render_manifest(
    conversion_manifest: dict[str, Any],
    *,
    output_root: Path,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    renderer: str = DEFAULT_RENDERER,
    wait_frames: int = DEFAULT_WAIT_FRAMES,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    selected_cases: list[dict[str, Any]] = []
    samples = [sample for sample in conversion_manifest.get("samples", []) if sample.get("sample_id")]

    for sample in samples:
        sample_records: list[dict[str, Any]] = []
        conditions = sample.get("conditions") or {}
        for condition_name in CONDITION_ORDER:
            condition = conditions.get(condition_name) or {}
            record = _condition_record(
                sample=sample,
                condition_name=condition_name,
                condition=condition,
                output_root=Path(output_root),
                width=int(width),
                height=int(height),
                renderer=str(renderer),
                wait_frames=int(wait_frames),
            )
            records.append(record)
            sample_records.append(record)

        selected_cases.append(
            {
                "sample_id": str(sample.get("sample_id")),
                "pair_id": str(sample.get("sample_id")),
                "source_scene_id": "supplemental_official_sample_wrapper",
                "target_category": sample.get("target_category") or "supplemental_material_fixture",
                "target_id": sample.get("target_prim_path") or sample.get("sample_id"),
                "target_prim_path": sample.get("target_prim_path"),
                "visual_review": None,
                "covered_effects": [str(effect) for effect in sample.get("present_effects") or []],
                "condition_statuses": _condition_statuses(sample_records),
            }
        )

    ready_image_records = [record for record in records if (record.get("image") or {}).get("status") == "ready"]
    render_pending = [record for record in records if record.get("status") == "render_pending"]
    source_missing = [record for record in records if record.get("status") == "source_missing"]
    nvidia_static_failed = [
        record
        for record in records
        if record.get("condition") == "nvidia_asset_converter_preview_or_bake"
        and record.get("source_condition_status") == "static_gate_failed"
    ]
    ready_case_count = _ready_case_count(selected_cases)
    ready_for_contact_sheet = bool(selected_cases) and ready_case_count == len(selected_cases)
    blockers: list[str] = []
    if render_pending or source_missing:
        blockers.append("supplemental_qualitative_renders_missing")
    if source_missing:
        blockers.append("supplemental_condition_sources_missing")
    if nvidia_static_failed:
        blockers.append("supplemental_nvidia_static_gate_failed")

    return {
        "schema_version": 1,
        "status": "supplemental_material_effect_qualitative_render_manifest",
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/build_supplemental_qualitative_render_manifest.py",
        "generated_at_utc": _utc_now(),
        "generator_git_commit": _git_commit(),
        "condition_order": CONDITION_ORDER,
        "effect_order": ["clearcoat", "procedural_texture"],
        "output_root": str(output_root),
        "renderer_settings": {
            "image_width": int(width),
            "image_height": int(height),
            "renderer": str(renderer),
            "wait_frames": int(wait_frames),
        },
        "summary": {
            "sample_count": len(samples),
            "selected_case_count": len(selected_cases),
            "condition_record_count": len(records),
            "ready_image_record_count": len(ready_image_records),
            "ready_case_count": ready_case_count,
            "render_pending_count": len(render_pending),
            "source_missing_count": len(source_missing),
            "nvidia_static_gate_failed_count": len(nvidia_static_failed),
            "ready_for_contact_sheet": ready_for_contact_sheet,
            "ready_for_visual_review": ready_for_contact_sheet,
            "ready_for_visual_quality_claim": ready_for_contact_sheet and not nvidia_static_failed,
            "blockers": blockers,
        },
        "selected_cases": selected_cases,
        "records": records,
        "claim_boundary": {
            "allowed": [
                "Use ready supplemental renders for qualitative failure review and paper/rebuttal panels.",
                "Use NVIDIA clearcoat as a candidate visual failure only after rendered inspection.",
            ],
            "forbidden": [
                "Do not treat a static-gate-failed NVIDIA condition as a broad error-rate estimate.",
                "Do not claim full material-effect visual quality coverage until supplemental renders are reviewed.",
            ],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conversion-manifest", type=Path, default=DEFAULT_CONVERSION_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--renderer", default=DEFAULT_RENDERER)
    parser.add_argument("--wait-frames", type=int, default=DEFAULT_WAIT_FRAMES)
    args = parser.parse_args(argv)

    manifest = build_supplemental_qualitative_render_manifest(
        _load_json(args.conversion_manifest),
        output_root=args.output_root,
        width=args.width,
        height=args.height,
        renderer=args.renderer,
        wait_frames=args.wait_frames,
    )
    manifest["inputs"] = {
        "conversion_manifest": {
            "path": str(args.conversion_manifest),
            "hash_sha256": _sha256_file(args.conversion_manifest),
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
        f"pending={manifest['summary']['render_pending_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
