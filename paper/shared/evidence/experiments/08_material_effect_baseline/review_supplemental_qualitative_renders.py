#!/usr/bin/env python3
"""Build machine-check visual QA for supplemental material-effect renders."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/material_effect_baseline"
DEFAULT_MANIFEST = RAW_DIR / "supplemental_qualitative_render_manifest.json"
DEFAULT_OUTPUT = RAW_DIR / "supplemental_qualitative_visual_qa.json"


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


def _image_stats(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "path": str(path),
            "exists": False,
            "bytes": 0,
            "width": None,
            "height": None,
            "mean_rgb": None,
            "std_rgb": None,
            "gray_mean": None,
            "gray_std": None,
            "thumb_unique_colors": 0,
            "thumb_nonwhite_ratio": 0.0,
        }
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        stat = ImageStat.Stat(rgb)
        gray = rgb.convert("L")
        gray_stat = ImageStat.Stat(gray)
        thumb = rgb.resize((80, 60))
        thumb_pixels = list(thumb.getdata())
    return {
        "path": str(path),
        "exists": True,
        "bytes": path.stat().st_size,
        "width": rgb.width,
        "height": rgb.height,
        "mean_rgb": [round(value, 3) for value in stat.mean],
        "std_rgb": [round(value, 3) for value in stat.stddev],
        "gray_mean": round(gray_stat.mean[0], 3),
        "gray_std": round(gray_stat.stddev[0], 3),
        "thumb_unique_colors": len(set(thumb_pixels)),
        "thumb_nonwhite_ratio": round(sum(1 for pixel in thumb_pixels if max(pixel) < 245) / len(thumb_pixels), 6),
    }


def _machine_assessment(record: dict[str, Any], stats: dict[str, Any]) -> tuple[str, str, str]:
    if not stats["exists"]:
        return "FAIL", "missing_image", "Render output image is missing."
    if stats["bytes"] <= 0:
        return "FAIL", "empty_image_file", "Render output image exists but has zero bytes."
    if stats["gray_mean"] is not None and stats["gray_std"] is not None:
        if stats["gray_mean"] < 10 and stats["gray_std"] < 10:
            return "FAIL", "near_black_render", "Image is near black, which is task-breaking for qualitative inspection."
    if record.get("source_condition_status") == "static_gate_failed":
        return "WARN", "static_gate_failed_rendered", "Image exists, but the source condition failed the static material gate."
    if stats["thumb_unique_colors"] <= 2 and stats["gray_std"] is not None and stats["gray_std"] < 2:
        return "WARN", "flat_color_render", "Image is nonblack but nearly flat; inspect manually before using as visual evidence."
    return "PASS", "nonblank_render", "Image is present and passes nonblank machine checks."


def build_supplemental_qualitative_visual_qa(manifest: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    failure_cases: list[dict[str, Any]] = []
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for record in manifest.get("records", []):
        image_path = Path(str((record.get("image") or {}).get("path") or ""))
        stats = _image_stats(image_path)
        verdict, reason, evidence = _machine_assessment(record, stats)
        counts[verdict] += 1
        reviewed = {
            "sample_id": record.get("sample_id"),
            "condition": record.get("condition"),
            "covered_effects": record.get("covered_effects") or [],
            "source_condition_status": record.get("source_condition_status"),
            "machine_verdict": verdict,
            "reason": reason,
            "evidence": evidence,
            "image_stats": stats,
        }
        records.append(reviewed)
        if verdict == "FAIL":
            failure_cases.append(
                {
                    "sample_id": reviewed["sample_id"],
                    "condition": reviewed["condition"],
                    "covered_effects": reviewed["covered_effects"],
                    "reason": reason,
                    "evidence": evidence,
                    "image_path": stats["path"],
                    "source_condition_status": reviewed["source_condition_status"],
                }
            )
    ready_images = sum(1 for record in records if record["image_stats"]["exists"])
    return {
        "schema_version": 1,
        "status": "supplemental_material_effect_qualitative_visual_qa",
        "generated_at_utc": _utc_now(),
        "generated_by": "paper/shared/evidence/experiments/08_material_effect_baseline/review_supplemental_qualitative_renders.py",
        "summary": {
            "image_record_count": len(records),
            "ready_image_count": ready_images,
            "machine_pass_count": counts["PASS"],
            "machine_warn_count": counts["WARN"],
            "machine_fail_count": counts["FAIL"],
            "failure_case_count": len(failure_cases),
            "ready_for_human_visual_review": ready_images == len(records) and bool(records),
            "ready_for_failure_case_writeup": bool(failure_cases),
            "ready_for_full_visual_quality_claim": False,
            "claim_boundary": "Machine QA detects missing/blank/near-black images only; it does not replace human visual review.",
        },
        "records": records,
        "failure_cases": failure_cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    report = build_supplemental_qualitative_visual_qa(_load_json(args.manifest))
    report["inputs"] = {
        "manifest": {"path": str(args.manifest), "hash_sha256": _sha256_file(args.manifest)},
    }
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
        f"Wrote {args.out} images={report['summary']['image_record_count']} "
        f"failures={report['summary']['machine_fail_count']} "
        f"ready_for_review={report['summary']['ready_for_human_visual_review']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
