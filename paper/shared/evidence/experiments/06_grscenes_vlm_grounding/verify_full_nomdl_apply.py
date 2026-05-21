#!/usr/bin/env python3
"""Verify that the full GRScenes no-MDL apply run produced usable evidence."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_PLAN = RAW_DIR / "full_nomdl_scratch_plan.json"
DEFAULT_RUN_REPORT = RAW_DIR / "full_nomdl_multi_root_run_report.json"
DEFAULT_OUTPUT = RAW_DIR / "full_nomdl_apply_verification_report.json"
USD_SUFFIXES = {".usd", ".usda", ".usdc"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_maybe_missing(path: str | Path) -> Path:
    return Path(path).resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def _job_by_id(jobs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(job.get("conversion_job_id")): job for job in jobs}


def _path_from_record(record: dict[str, Any], key: str) -> Path:
    return _resolve_maybe_missing(record.get(key, ""))


def _find_source_nomdl_sidecars(source_root: Path, *, max_records: int) -> tuple[list[str], bool]:
    matches: list[str] = []
    truncated = False
    for dirpath, dirnames, filenames in os.walk(source_root, followlinks=False):
        dirnames.sort()
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if "_noMDL" not in filename or path.suffix not in USD_SUFFIXES:
                continue
            if len(matches) >= max_records:
                truncated = True
                return matches, truncated
            matches.append(str(path))
    return matches, truncated


def build_verification_report(
    plan: dict[str, Any],
    run_report: dict[str, Any],
    *,
    max_records: int = 2000,
    scan_source_pollution: bool = True,
) -> dict[str, Any]:
    source_root = _resolve_maybe_missing(plan["source_root"])
    scratch_root = _resolve_maybe_missing(plan["scratch_root"])
    report_source_root = _resolve_maybe_missing(run_report.get("source_root", ""))
    report_scratch_root = _resolve_maybe_missing(run_report.get("scratch_root", ""))
    plan_jobs = list(plan.get("conversion_jobs") or [])
    run_jobs = list(run_report.get("jobs") or [])
    results = list(run_report.get("results") or [])
    plan_jobs_by_id = _job_by_id(plan_jobs)
    run_jobs_by_id = _job_by_id(run_jobs)
    results_by_job = {str(result.get("conversion_job_id")): result for result in results}
    plan_job_ids = set(plan_jobs_by_id)
    run_job_ids = set(run_jobs_by_id)
    result_job_ids = set(results_by_job)

    blockers: list[str] = []
    if not source_root.is_dir():
        blockers.append("source_root_missing")
    if not scratch_root.is_dir():
        blockers.append("scratch_root_missing")
    if source_root == scratch_root or _is_relative_to(source_root, scratch_root) or _is_relative_to(scratch_root, source_root):
        blockers.append("source_scratch_roots_nested")
    if run_report.get("dry_run") is not False:
        blockers.append("run_report_is_dry_run")
    if run_report.get("status") != "completed_full_grscenes_nomdl_multi_root_run":
        blockers.append("run_report_status_not_completed")
    if run_report.get("apply_ready") is not True:
        blockers.append("run_report_not_apply_ready")
    if (run_report.get("safety") or {}).get("remaining_apply_blockers"):
        blockers.append("run_report_has_remaining_blockers")
    if report_source_root != source_root:
        blockers.append("run_report_source_root_mismatch")
    if report_scratch_root != scratch_root:
        blockers.append("run_report_scratch_root_mismatch")
    if (run_report.get("summary") or {}).get("planned_job_count") != len(plan_jobs):
        blockers.append("run_report_planned_job_count_mismatch")
    if run_job_ids != plan_job_ids or len(run_jobs) != len(plan_jobs):
        blockers.append("run_report_job_set_mismatch")
    if result_job_ids != plan_job_ids or len(results) != len(plan_jobs):
        blockers.append("result_job_set_mismatch")
    if len(results) != len(run_jobs):
        blockers.append("result_count_mismatch")

    missing_result_job_ids: list[str] = []
    mismatched_result_outputs: list[dict[str, str]] = []
    mismatched_result_inputs: list[dict[str, str]] = []
    expected_top_outputs: list[str] = []
    missing_top_outputs: list[str] = []
    empty_top_outputs: list[str] = []
    missing_source_usds: list[str] = []
    missing_scratch_inputs: list[str] = []
    source_usds_outside_source_root: list[str] = []
    scratch_inputs_outside_scratch_root: list[str] = []
    run_job_mismatches: list[dict[str, str]] = []
    result_scratch_inputs_outside_scratch_root: list[str] = []
    top_outputs_outside_scratch: list[str] = []

    for job_id, job in sorted(plan_jobs_by_id.items()):
        job_id = str(job.get("conversion_job_id"))
        source_usd = _path_from_record(job, "source_usd")
        scratch_input = _path_from_record(job, "scratch_input_usd")
        expected_output = _path_from_record(job, "expected_top_output_usd")
        source_usd_text = str(source_usd)
        scratch_input_text = str(scratch_input)
        expected_output_text = str(expected_output)
        expected_top_outputs.append(expected_output_text)
        if not _is_relative_to(source_usd, source_root):
            source_usds_outside_source_root.append(source_usd_text)
        elif not source_usd.exists():
            missing_source_usds.append(source_usd_text)
        if not _is_relative_to(scratch_input, scratch_root):
            scratch_inputs_outside_scratch_root.append(scratch_input_text)
        elif not scratch_input.exists():
            missing_scratch_inputs.append(scratch_input_text)
        if not _is_relative_to(expected_output, scratch_root):
            top_outputs_outside_scratch.append(expected_output_text)
        elif not expected_output.exists():
            missing_top_outputs.append(expected_output_text)
        elif expected_output.stat().st_size == 0:
            empty_top_outputs.append(expected_output_text)
        run_job = run_jobs_by_id.get(job_id)
        if run_job is not None:
            for key in ("source_usd", "scratch_input_usd", "expected_top_output_usd"):
                if _path_from_record(run_job, key) != _path_from_record(job, key):
                    run_job_mismatches.append(
                        {
                            "conversion_job_id": job_id,
                            "field": key,
                            "expected": str(_path_from_record(job, key)),
                            "actual": str(_path_from_record(run_job, key)),
                        }
                    )
        result = results_by_job.get(job_id)
        if result is None:
            missing_result_job_ids.append(job_id)
            continue
        result_input = _path_from_record(result, "scratch_input_usd")
        result_output = _resolve_maybe_missing(result.get("top_output_usd", ""))
        if not _is_relative_to(result_input, scratch_root):
            result_scratch_inputs_outside_scratch_root.append(str(result_input))
        if result_input != scratch_input:
            mismatched_result_inputs.append(
                {
                    "conversion_job_id": job_id,
                    "expected_scratch_input_usd": scratch_input_text,
                    "result_scratch_input_usd": str(result_input),
                }
            )
        if result_output != expected_output:
            mismatched_result_outputs.append(
                {
                    "conversion_job_id": job_id,
                    "expected_top_output_usd": expected_output_text,
                    "result_top_output_usd": str(result_output),
                }
            )

    source_pollution: list[str] = []
    source_pollution_truncated = False
    if scan_source_pollution:
        source_pollution, source_pollution_truncated = _find_source_nomdl_sidecars(
            source_root,
            max_records=max_records,
        )

    if missing_result_job_ids:
        blockers.append("results_missing_jobs")
    if run_job_mismatches:
        blockers.append("run_report_jobs_mismatch_plan")
    if mismatched_result_inputs:
        blockers.append("result_scratch_inputs_mismatch_expected")
    if mismatched_result_outputs:
        blockers.append("result_top_outputs_mismatch_expected")
    if missing_source_usds:
        blockers.append("source_usds_missing")
    if missing_scratch_inputs:
        blockers.append("scratch_inputs_missing")
    if source_usds_outside_source_root:
        blockers.append("source_usds_outside_source_root")
    if scratch_inputs_outside_scratch_root:
        blockers.append("scratch_inputs_outside_scratch_root")
    if missing_top_outputs:
        blockers.append("top_outputs_missing")
    if empty_top_outputs:
        blockers.append("top_outputs_empty")
    if top_outputs_outside_scratch:
        blockers.append("top_outputs_outside_scratch_root")
    if result_scratch_inputs_outside_scratch_root:
        blockers.append("result_scratch_inputs_outside_scratch_root")
    if source_pollution:
        blockers.append("source_nomdl_sidecars_present")
    if source_pollution_truncated:
        blockers.append("source_pollution_scan_truncated")

    existing_top_output_count = len(expected_top_outputs) - len(missing_top_outputs)
    blockers = _dedupe_preserve_order(blockers)
    return {
        "schema_version": 1,
        "status": "verified_full_grscenes_nomdl_apply",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/verify_full_nomdl_apply.py",
        "generated_at_utc": _utc_now(),
        "passed": not blockers,
        "blockers": blockers,
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "run_report_status": run_report.get("status"),
        "run_report_dry_run": run_report.get("dry_run"),
        "run_report_apply_ready": run_report.get("apply_ready"),
        "processor_done_count": run_report.get("processor_done_count"),
        "summary": {
            "planned_job_count": len(plan_jobs),
            "run_report_job_count": len(run_jobs),
            "result_count": len(results),
            "expected_top_output_count": len(expected_top_outputs),
            "existing_top_output_count": existing_top_output_count,
            "missing_top_output_count": len(missing_top_outputs),
            "empty_top_output_count": len(empty_top_outputs),
            "missing_source_usd_count": len(missing_source_usds),
            "missing_scratch_input_count": len(missing_scratch_inputs),
            "source_pollution_count": len(source_pollution),
            "source_pollution_scan_truncated": source_pollution_truncated,
        },
        "missing_result_job_ids": missing_result_job_ids[:max_records],
        "run_job_mismatches": run_job_mismatches[:max_records],
        "mismatched_result_inputs": mismatched_result_inputs[:max_records],
        "mismatched_result_outputs": mismatched_result_outputs[:max_records],
        "missing_source_usds": missing_source_usds[:max_records],
        "missing_scratch_inputs": missing_scratch_inputs[:max_records],
        "source_usds_outside_source_root": source_usds_outside_source_root[:max_records],
        "scratch_inputs_outside_scratch_root": scratch_inputs_outside_scratch_root[:max_records],
        "missing_top_outputs": missing_top_outputs[:max_records],
        "empty_top_outputs": empty_top_outputs[:max_records],
        "top_outputs_outside_scratch": top_outputs_outside_scratch[:max_records],
        "result_scratch_inputs_outside_scratch_root": result_scratch_inputs_outside_scratch_root[:max_records],
        "source_pollution": source_pollution,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--run-report", type=Path, default=DEFAULT_RUN_REPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-records", type=int, default=2000)
    parser.add_argument("--skip-source-pollution-scan", action="store_true")
    args = parser.parse_args(argv)

    report = build_verification_report(
        _load_json(args.plan),
        _load_json(args.run_report),
        max_records=args.max_records,
        scan_source_pollution=not args.skip_source_pollution_scan,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} passed={report['passed']} blockers={report['blockers']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
