#!/usr/bin/env python3
"""Run one original/no-MDL paired render smoke from a render manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageStat


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_RENDER_MANIFEST = RAW_DIR / "render_manifest.json"
DEFAULT_OUTPUT = RAW_DIR / "paired_render_smoke_report.json"
DEFAULT_LOG_DIR = RAW_DIR / "render_logs"
DEFAULT_TIMEOUT_SECONDS = 900
ERROR_TERMS = ("KooPbr", "KooPbr_maps", "Failed to create MDL shade node", "coroutine was never awaited")


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
        output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    return [line for line in output.splitlines() if line]


def _find_pair(render_manifest: dict[str, Any], pair_id: str) -> dict[str, Any]:
    for pair in render_manifest.get("render_pairs", []):
        if pair.get("pair_id") == pair_id:
            return pair
    raise KeyError(f"pair_id not found in render manifest: {pair_id}")


def _count_term(text: str, term: str) -> int:
    if term in {"KooPbr", "KooPbr_maps"}:
        return len(re.findall(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", text))
    return text.count(term)


def _log_summary(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    return {
        "path": str(path),
        "bytes": path.stat().st_size if path.exists() else 0,
        "hash_sha256": _sha256_file(path) if path.exists() else None,
        "line_count": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "contains_saved_frame": "Saved frame" in text or "Saved image" in text,
        "counts": {term: _count_term(text, term) for term in ERROR_TERMS},
    }


def _renderer_script_record(command: list[str]) -> dict[str, Any] | None:
    for item in command[1:]:
        path = Path(item)
        if path.suffix == ".py":
            resolved = path if path.is_absolute() else PROJECT_ROOT / path
            return {
                "path": str(path),
                "resolved_path": str(resolved),
                "hash_sha256": _sha256_file(resolved) if resolved.exists() else None,
            }
    return None


def _image_metrics(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        rgb = rgba.convert("RGB")
        stat = ImageStat.Stat(rgb)
        pixels = rgb.load()
        width, height = rgb.size
        threshold = 10
        xs: list[int] = []
        ys: list[int] = []
        non_dark = 0
        for y in range(height):
            for x in range(width):
                if max(pixels[x, y]) > threshold:
                    non_dark += 1
                    xs.append(x)
                    ys.append(y)
        return {
            "mode": image.mode,
            "width": width,
            "height": height,
            "bytes": path.stat().st_size,
            "hash_sha256": _sha256_file(path),
            "mean_rgb": [round(value, 4) for value in stat.mean],
            "stddev_rgb": [round(value, 4) for value in stat.stddev],
            "non_dark_pixel_threshold": threshold,
            "non_dark_pixel_count": non_dark,
            "non_dark_pixel_bbox_xyxy": [min(xs), min(ys), max(xs), max(ys)] if xs else None,
            "path": str(path),
        }


def _run_condition(
    condition: dict[str, Any],
    *,
    log_dir: Path,
    runner: Callable[..., Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    material_condition = str(condition["material_condition"])
    sample_id = str(condition["sample_id"])
    safe_sample = sample_id.replace("/", "_")
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / f"{safe_sample}.stdout.txt"
    stderr_path = log_dir / f"{safe_sample}.stderr.txt"
    command = [str(item) for item in condition["render_command"]]
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        completed = runner(
            command,
            cwd=str(PROJECT_ROOT),
            stdout=stdout,
            stderr=stderr,
            text=True,
            timeout=timeout_seconds,
        )
    image_path = Path(str(condition["output_image"]))
    return {
        "sample_id": sample_id,
        "material_condition": material_condition,
        "exit_code": int(completed.returncode),
        "render_command": command,
        "renderer_script": _renderer_script_record(command),
        "image": _image_metrics(image_path),
        "stdout_summary": _log_summary(stdout_path),
        "stderr_summary": _log_summary(stderr_path),
    }


def _condition(records: list[dict[str, Any]], material_condition: str) -> dict[str, Any]:
    for record in records:
        if record.get("material_condition") == material_condition:
            return record
    raise KeyError(f"condition missing from smoke records: {material_condition}")


def _mdl_error_signal(record: dict[str, Any]) -> int:
    counts = record["stderr_summary"]["counts"]
    return int(counts.get("KooPbr", 0)) + int(counts.get("KooPbr_maps", 0))


def _interpretation(original: dict[str, Any], converted: dict[str, Any]) -> str:
    original_pixels = (original.get("image") or {}).get("non_dark_pixel_count")
    converted_pixels = (converted.get("image") or {}).get("non_dark_pixel_count")
    original_errors = _mdl_error_signal(original)
    converted_errors = _mdl_error_signal(converted)
    if original_pixels == 0 and converted_pixels and converted_pixels > 0:
        return (
            "Converted render is visible for this view; the paired original exits but captures an all-black "
            "image with MDL/KooPbr errors. Treat as smoke evidence, not final VLM metric evidence."
        )
    if original_pixels and converted_pixels:
        return (
            "Both paired renders contain visible pixels for this view. The original render still reports "
            f"MDL/KooPbr error signal {original_errors}, while the converted render reports {converted_errors}. "
            "Treat as render-stack smoke evidence only; final VLM claims require visibility-aware batch renders, "
            "image-space labels, predictions, and score summaries."
        )
    return (
        "At least one paired render did not produce a visible image. Treat this as failed or inconclusive smoke "
        "evidence until the render pipeline is retaken."
    )


def build_smoke_report(
    render_manifest: dict[str, Any],
    *,
    pair_id: str,
    render_manifest_path: Path,
    report_path: Path,
    log_dir: Path,
    runner: Callable[..., Any] = subprocess.run,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    pair = _find_pair(render_manifest, pair_id)
    records = [
        _run_condition(
            condition,
            log_dir=log_dir / pair_id,
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
        for condition in pair.get("conditions", [])
    ]
    original = _condition(records, "original")
    converted = _condition(records, "converted")
    renderer_settings = render_manifest.get("renderer_settings") or {}
    return {
        "schema_version": 1,
        "status": "paired_render_smoke_report",
        "generated_at_utc": _utc_now(),
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_paired_render_smoke.py",
        "render_manifest": {
            "path": str(render_manifest_path),
            "hash_sha256": _sha256_file(render_manifest_path),
        },
        "report_path": str(report_path),
        "pair_id": pair_id,
        "target_category": pair.get("target_category") or (pair.get("conditions") or [{}])[0].get("object_category"),
        "source_scene_id": pair.get("source_scene_id"),
        "view_id": (pair.get("view") or {}).get("view_id"),
        "renderer": renderer_settings.get("renderer"),
        "image_width": renderer_settings.get("image_width"),
        "image_height": renderer_settings.get("image_height"),
        "records": records,
        "summary": {
            "both_commands_exit_zero": all(record["exit_code"] == 0 for record in records),
            "both_images_exist": all(record["image"] is not None for record in records),
            "original_non_dark_pixel_count": (original.get("image") or {}).get("non_dark_pixel_count"),
            "converted_non_dark_pixel_count": (converted.get("image") or {}).get("non_dark_pixel_count"),
            "original_mdl_error_signal": _mdl_error_signal(original),
            "converted_mdl_error_signal": _mdl_error_signal(converted),
            "interpretation": _interpretation(original, converted),
            "next_gate": "implement visibility-aware view selection and render more paired images before VLM scoring",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-manifest", type=Path, default=DEFAULT_RENDER_MANIFEST)
    parser.add_argument("--pair-id", required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    render_manifest = _load_json(args.render_manifest)
    report = build_smoke_report(
        render_manifest,
        pair_id=args.pair_id,
        render_manifest_path=args.render_manifest,
        report_path=args.out,
        log_dir=args.log_dir,
        timeout_seconds=args.timeout_seconds,
    )
    report["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} pair_id={args.pair_id} "
        f"both_exit_zero={report['summary']['both_commands_exit_zero']} "
        f"both_images_exist={report['summary']['both_images_exist']}"
    )
    return 0 if report["summary"]["both_commands_exit_zero"] and report["summary"]["both_images_exist"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
