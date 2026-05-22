#!/usr/bin/env python3
"""Summarize rendered selected GRScenes original/no-MDL pairs."""

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
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_PREFLIGHT_REPORT = RAW_DIR / "visibility_preflight_report.json"
DEFAULT_REPORT_DIR = RAW_DIR / "paired_render_reports"
DEFAULT_FALLBACK_REPORT = RAW_DIR / "paired_render_smoke_report.json"
DEFAULT_OUTPUT = RAW_DIR / "recommended_paired_render_summary.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
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


def _recommended_pair_ids(preflight_report: dict[str, Any]) -> list[str]:
    pairs = []
    for item in preflight_report.get("recommended_pairs_by_target", {}).values():
        pair_id = item.get("pair_id")
        if pair_id:
            pairs.append(str(pair_id))
    return pairs


def _find_report(pair_id: str, *, report_dirs: list[Path], fallback_reports: list[Path]) -> tuple[Path, str]:
    for report_dir in report_dirs:
        path = report_dir / f"{pair_id}.json"
        if path.exists():
            return path, "report_dir"
    for path in fallback_reports:
        if not path.exists():
            continue
        try:
            report = _load_json(path)
        except Exception:
            continue
        if report.get("pair_id") == pair_id:
            return path, "fallback_report"
    raise FileNotFoundError(f"missing paired render report for selected pair: {pair_id}")


def _condition(records: list[dict[str, Any]], material_condition: str) -> dict[str, Any]:
    for record in records:
        if record.get("material_condition") == material_condition:
            return record
    raise KeyError(f"condition missing from paired render report: {material_condition}")


def _image_ready(record: dict[str, Any]) -> bool:
    image = record.get("image") or {}
    return bool(image.get("hash_sha256")) and int(image.get("non_dark_pixel_count") or 0) > 0


def _pair_summary(pair_id: str, report_path: Path, report_source: str) -> dict[str, Any]:
    report = _load_json(report_path)
    records = list(report.get("records") or [])
    original = _condition(records, "original")
    converted = _condition(records, "converted")
    original_image = original.get("image") or {}
    converted_image = converted.get("image") or {}
    both_exit_zero = bool((report.get("summary") or {}).get("both_commands_exit_zero"))
    both_images_exist = bool((report.get("summary") or {}).get("both_images_exist"))
    render_smoke_pass = both_exit_zero and both_images_exist and _image_ready(original) and _image_ready(converted)
    return {
        "pair_id": pair_id,
        "report_path": str(report_path),
        "report_source": report_source,
        "report_hash_sha256": _sha256_file(report_path),
        "both_commands_exit_zero": both_exit_zero,
        "both_images_exist": both_images_exist,
        "render_smoke_pass": render_smoke_pass,
        "original": {
            "image_path": original_image.get("path"),
            "hash_sha256": original_image.get("hash_sha256"),
            "non_dark_pixel_count": original_image.get("non_dark_pixel_count"),
            "width": original_image.get("width"),
            "height": original_image.get("height"),
            "mdl_error_signal": (report.get("summary") or {}).get("original_mdl_error_signal"),
        },
        "converted": {
            "image_path": converted_image.get("path"),
            "hash_sha256": converted_image.get("hash_sha256"),
            "non_dark_pixel_count": converted_image.get("non_dark_pixel_count"),
            "width": converted_image.get("width"),
            "height": converted_image.get("height"),
            "mdl_error_signal": (report.get("summary") or {}).get("converted_mdl_error_signal"),
        },
    }


def build_recommended_render_summary(
    preflight_report: dict[str, Any],
    *,
    report_dirs: list[Path],
    fallback_reports: list[Path],
    pair_ids: list[str] | None = None,
    selection_mode: str | None = None,
    status: str | None = None,
    claim_boundary: str | None = None,
) -> dict[str, Any]:
    recommended_pair_ids = _recommended_pair_ids(preflight_report)
    selected_pair_ids = list(pair_ids) if pair_ids is not None else recommended_pair_ids
    resolved_selection_mode = (
        selection_mode
        if selection_mode is not None
        else ("explicit_pair_ids" if pair_ids is not None else "recommended_pairs_by_target")
    )
    resolved_status = status or (
        "selected_paired_render_summary" if pair_ids is not None else "recommended_paired_render_summary"
    )
    resolved_claim_boundary = claim_boundary or "render_smoke_only_requires_projection_visual_qa_and_vlm_predictions"
    pairs: list[dict[str, Any]] = []
    for pair_id in selected_pair_ids:
        report_path, report_source = _find_report(pair_id, report_dirs=report_dirs, fallback_reports=fallback_reports)
        pairs.append(_pair_summary(pair_id, report_path, report_source))
    smoke_pass_count = len([item for item in pairs if item["render_smoke_pass"]])
    black_or_missing = len(pairs) - smoke_pass_count
    fallback_count = len([item for item in pairs if item["report_source"] == "fallback_report"])
    return {
        "schema_version": 1,
        "status": resolved_status,
        "generated_at_utc": _utc_now(),
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/summarize_recommended_paired_renders.py",
        "summary": {
            "selection_mode": resolved_selection_mode,
            "selected_pair_count": len(selected_pair_ids),
            "recommended_pair_count": len(recommended_pair_ids),
            "reports_found_count": len(pairs),
            "report_dir_count": len(pairs) - fallback_count,
            "fallback_report_count": fallback_count,
            "paired_non_dark_render_smoke_count": smoke_pass_count,
            "black_or_missing_image_count": black_or_missing,
            "render_smoke_pass_count": smoke_pass_count,
            "preflight_centerline_clear_pair_count": (preflight_report.get("summary") or {}).get("centerline_clear_pair_count"),
            "claim_boundary": resolved_claim_boundary,
        },
        "pairs": pairs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-report", type=Path, default=DEFAULT_PREFLIGHT_REPORT)
    parser.add_argument("--report-dir", type=Path, action="append", default=[DEFAULT_REPORT_DIR])
    parser.add_argument("--fallback-report", type=Path, action="append", default=[DEFAULT_FALLBACK_REPORT])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--pair-id", action="append", dest="pair_ids", help="Explicit pair id to summarize; repeatable.")
    parser.add_argument("--selection-mode", help="Selection-mode string to record in summary metadata.")
    parser.add_argument("--status", help="Top-level status string to record in the generated summary.")
    parser.add_argument("--claim-boundary", help="Claim-boundary string to record in summary metadata.")
    args = parser.parse_args(argv)

    preflight_report = _load_json(args.preflight_report)
    summary = build_recommended_render_summary(
        preflight_report,
        report_dirs=args.report_dir,
        fallback_reports=args.fallback_report,
        pair_ids=args.pair_ids,
        selection_mode=args.selection_mode,
        status=args.status,
        claim_boundary=args.claim_boundary,
    )
    summary["preflight_report"] = {
        "path": str(args.preflight_report),
        "hash_sha256": _sha256_file(args.preflight_report),
    }
    summary["generator_provenance"] = {
        "command": [sys.executable, str(Path(__file__).resolve()), *(argv if argv is not None else sys.argv[1:])],
        "script_path": str(Path(__file__).resolve()),
        "script_hash_sha256": _sha256_file(Path(__file__).resolve()),
        "git_commit": _git_commit(),
        "git_status_porcelain": _git_status_porcelain(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        f"Wrote {args.out} selected={summary['summary']['selected_pair_count']} "
        f"recommended={summary['summary']['recommended_pair_count']} "
        f"render_smoke_pass={summary['summary']['render_smoke_pass_count']}"
    )
    return 0 if summary["summary"]["black_or_missing_image_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
