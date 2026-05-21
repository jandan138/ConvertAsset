#!/usr/bin/env python3
"""Build or execute the guarded full-GRScenes multi-root no-MDL run plan.

Default mode is a pure-Python dry-run report. It does not import pxr, does not
import no-MDL modules, does not create scratch assets, and does not convert USDs.

The apply path is intentionally gated. Only after all report blockers are gone
will it lazily import ConvertAsset's no-MDL Processor and reuse one Processor
instance across every planned scratch root.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper" / "shared" / "evidence" / "raw" / "grscene_vlm_grounding"
DEFAULT_PLAN = RAW_DIR / "full_nomdl_scratch_plan.json"
DEFAULT_OUTPUT = RAW_DIR / "full_nomdl_multi_root_run_report.json"
RUNNER_MISSING_BLOCKER = "single_process_multi_root_runner_missing"
CLOSURE_REPORT_NOT_CONSUMED_BLOCKER = "single_process_multi_root_runner_closure_report_not_consumed"
WHOLE_SCENE_CLOSURE_BLOCKER = "whole_scene_dependency_closure_not_scanned"
RECURSIVE_COLLISION_SCAN_BLOCKER = "recursive_nomdl_output_collision_scan_missing"
REQUIRED_CLOSURE_SUMMARY_FIELDS = {
    "expected_top_output_count",
    "scan_truncated",
    "unscanned_usd_queue_count",
    "missing_dependency_count",
    "outside_source_root_ref_count",
    "output_collision_count",
    "scratch_input_missing_count",
}
SCRATCH_CLEANLINESS_BLOCKER = "scratch_cleanliness_not_verified"
REQUIRED_MATERIALIZATION_SUMMARY_FIELDS = {
    "dry_run",
    "tree_action_count",
    "repair_action_count",
    "ignored_convert_action_count",
    "existing_nomdl_output_count",
    "top_level_scratch_input_exists_count",
    "top_level_scratch_input_missing_count",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_maybe_missing(path: Path) -> Path:
    return path.resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        _resolve_maybe_missing(path).relative_to(_resolve_maybe_missing(parent))
    except ValueError:
        return False
    return True


def _assert_root_safety(source_root: Path, scratch_root: Path) -> tuple[Path, Path]:
    source_root = source_root.resolve()
    scratch_root = _resolve_maybe_missing(scratch_root)
    if _is_relative_to(scratch_root, source_root):
        raise ValueError("scratch_root must not be inside source_root")
    if _is_relative_to(source_root, scratch_root):
        raise ValueError("source_root must not be inside scratch_root")
    return source_root, scratch_root


def validate_output_path(output_path: Path, *, plan: dict[str, Any]) -> Path:
    """Return a resolved report path that cannot write into source or scratch."""

    source_root, scratch_root = _plan_roots(plan)
    output_path = _resolve_maybe_missing(output_path)
    if _is_relative_to(output_path, source_root):
        raise ValueError("output path must not be inside source_root")
    if _is_relative_to(output_path, scratch_root):
        raise ValueError("output path must not be inside scratch_root")
    return output_path


def _plan_roots(plan: dict[str, Any]) -> tuple[Path, Path]:
    source_root = Path(str(plan.get("source_root") or ""))
    scratch_root = Path(str(plan.get("scratch_root") or ""))
    if not str(source_root) or not str(scratch_root):
        raise ValueError("plan must define source_root and scratch_root")
    return _assert_root_safety(source_root, scratch_root)


def _require_inside(path_text: str, *, root: Path, label: str, root_label: str) -> Path:
    path = _resolve_maybe_missing(Path(path_text))
    if not _is_relative_to(path, root):
        raise ValueError(f"{label} must be inside {root_label}: {path}")
    return path


def _timestamped_siblings(expected_output: Path) -> list[str]:
    parent = expected_output.parent
    if not parent.exists():
        return []
    suffix = expected_output.suffix or ".usd"
    pattern = f"{expected_output.stem}_*{suffix}"
    return sorted(str(path) for path in parent.glob(pattern) if path.name != expected_output.name)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _same_resolved_path(left: str | Path, right: str | Path) -> bool:
    return _resolve_maybe_missing(Path(left)) == _resolve_maybe_missing(Path(right))


def _closure_jobs_by_id(closure_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    jobs: dict[str, dict[str, Any]] = {}
    for job in closure_report.get("jobs") or []:
        job_id = str(job.get("conversion_job_id") or "")
        if job_id:
            jobs[job_id] = job
    return jobs


def _required_bool(mapping: dict[str, Any], field: str, *, label: str) -> bool:
    value = mapping.get(field)
    if not isinstance(value, bool):
        raise ValueError(f"{label} {field} must be a boolean")
    return value


def _required_nonnegative_int(mapping: dict[str, Any], field: str, *, label: str) -> int:
    value = mapping.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} {field} must be a non-negative integer")
    return value


def _validate_closure_report_shape(
    closure_report: dict[str, Any],
    *,
    plan: dict[str, Any],
    jobs: list[dict[str, Any]],
    source_root: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    if closure_report.get("status") != "planned_full_grscenes_dependency_closure":
        raise ValueError("closure report status must be planned_full_grscenes_dependency_closure")
    if not _same_resolved_path(str(closure_report.get("source_root") or ""), source_root):
        raise ValueError("closure report source_root must match plan")
    if not _same_resolved_path(str(closure_report.get("scratch_root") or ""), scratch_root):
        raise ValueError("closure report scratch_root must match plan")
    if closure_report.get("source_plan_status") != plan.get("status"):
        raise ValueError("closure report source_plan_status must match plan status")

    summary = dict(closure_report.get("summary") or {})
    missing_summary_fields = sorted(field for field in REQUIRED_CLOSURE_SUMMARY_FIELDS if field not in summary)
    if missing_summary_fields:
        raise ValueError(f"closure report summary missing required fields: {missing_summary_fields}")
    _required_nonnegative_int(summary, "expected_top_output_count", label="closure report summary")
    _required_bool(summary, "scan_truncated", label="closure report summary")
    _required_nonnegative_int(summary, "unscanned_usd_queue_count", label="closure report summary")
    _required_nonnegative_int(summary, "missing_dependency_count", label="closure report summary")
    _required_nonnegative_int(summary, "outside_source_root_ref_count", label="closure report summary")
    _required_nonnegative_int(summary, "output_collision_count", label="closure report summary")
    _required_nonnegative_int(summary, "scratch_input_missing_count", label="closure report summary")
    expected_top_count = summary.get("expected_top_output_count")
    plan_total_count = (plan.get("summary") or {}).get("conversion_job_count")
    if plan_total_count == len(jobs) and expected_top_count != len(jobs):
        raise ValueError("closure report expected_top_output_count must match selected jobs")

    closure_jobs = _closure_jobs_by_id(closure_report)
    missing_closure_jobs: list[str] = []
    for job in jobs:
        job_id = str(job.get("conversion_job_id") or "")
        closure_job = closure_jobs.get(job_id)
        if closure_job is None:
            missing_closure_jobs.append(job_id)
            continue
        if not _same_resolved_path(closure_job.get("scratch_input_usd") or "", job["scratch_input_usd"]):
            raise ValueError(f"closure report scratch_input_usd mismatch for job: {job_id}")
        if not _same_resolved_path(closure_job.get("expected_top_output_usd") or "", job["expected_top_output_usd"]):
            raise ValueError(f"closure report expected_top_output_usd mismatch for job: {job_id}")
    if missing_closure_jobs:
        raise ValueError(f"closure report missing selected jobs: {missing_closure_jobs[:5]}")
    return summary


def _closure_gate(
    closure_report: dict[str, Any] | None,
    *,
    plan: dict[str, Any],
    jobs: list[dict[str, Any]],
    source_root: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    if closure_report is None:
        return {
            "provided": False,
            "satisfied_apply_blockers": [],
            "remaining_apply_blockers": [],
            "summary": None,
        }

    summary = _validate_closure_report_shape(
        closure_report,
        plan=plan,
        jobs=jobs,
        source_root=source_root,
        scratch_root=scratch_root,
    )
    satisfied = [CLOSURE_REPORT_NOT_CONSUMED_BLOCKER]
    remaining: list[str] = []

    scan_complete = summary.get("scan_truncated") is False and int(summary.get("unscanned_usd_queue_count") or 0) == 0
    dependencies_clean = (
        int(summary.get("missing_dependency_count") or 0) == 0
        and int(summary.get("outside_source_root_ref_count") or 0) == 0
    )
    collisions_clean = int(summary.get("output_collision_count") or 0) == 0
    scratch_inputs_complete = int(summary.get("scratch_input_missing_count") or 0) == 0

    if scan_complete and dependencies_clean:
        satisfied.append(WHOLE_SCENE_CLOSURE_BLOCKER)
    else:
        remaining.append(WHOLE_SCENE_CLOSURE_BLOCKER)
    if scan_complete and collisions_clean:
        satisfied.append(RECURSIVE_COLLISION_SCAN_BLOCKER)
    else:
        remaining.append(RECURSIVE_COLLISION_SCAN_BLOCKER)
    if not scan_complete:
        remaining.append("dependency_closure_scan_truncated")
    if int(summary.get("missing_dependency_count") or 0):
        remaining.append("missing_dependencies_present")
    if int(summary.get("outside_source_root_ref_count") or 0):
        remaining.append("outside_source_root_refs_present")
    if not collisions_clean:
        remaining.append("recursive_nomdl_output_collisions_present")
    if not scratch_inputs_complete:
        remaining.append("scratch_inputs_missing")

    return {
        "provided": True,
        "satisfied_apply_blockers": _dedupe_preserve_order(satisfied),
        "remaining_apply_blockers": _dedupe_preserve_order(remaining),
        "summary": summary,
    }


def _materialization_gate(
    materialization_report: dict[str, Any] | None,
    *,
    plan: dict[str, Any],
    source_root: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    if materialization_report is None:
        return {
            "provided": False,
            "satisfied_apply_blockers": [],
            "remaining_apply_blockers": [],
            "summary": None,
        }
    if materialization_report.get("status") != "full_grscenes_nomdl_scratch_materialization":
        raise ValueError("materialization report status must be full_grscenes_nomdl_scratch_materialization")
    if not _same_resolved_path(str(materialization_report.get("source_root") or ""), source_root):
        raise ValueError("materialization report source_root must match plan")
    if not _same_resolved_path(str(materialization_report.get("scratch_root") or ""), scratch_root):
        raise ValueError("materialization report scratch_root must match plan")
    if materialization_report.get("source_plan_status") != plan.get("status"):
        raise ValueError("materialization report source_plan_status must match plan status")

    summary = dict(materialization_report.get("summary") or {})
    missing_summary_fields = sorted(field for field in REQUIRED_MATERIALIZATION_SUMMARY_FIELDS if field not in summary)
    if missing_summary_fields:
        raise ValueError(f"materialization report summary missing required fields: {missing_summary_fields}")
    _required_bool(summary, "dry_run", label="materialization report summary")
    _required_nonnegative_int(summary, "tree_action_count", label="materialization report summary")
    _required_nonnegative_int(summary, "repair_action_count", label="materialization report summary")
    _required_nonnegative_int(summary, "ignored_convert_action_count", label="materialization report summary")
    _required_nonnegative_int(summary, "existing_nomdl_output_count", label="materialization report summary")
    _required_nonnegative_int(summary, "top_level_scratch_input_exists_count", label="materialization report summary")
    _required_nonnegative_int(summary, "top_level_scratch_input_missing_count", label="materialization report summary")

    clean = (
        materialization_report.get("dry_run") is False
        and summary.get("dry_run") is False
        and int(summary.get("existing_nomdl_output_count") or 0) == 0
        and int(summary.get("top_level_scratch_input_missing_count") or 0) == 0
    )
    return {
        "provided": True,
        "satisfied_apply_blockers": [SCRATCH_CLEANLINESS_BLOCKER] if clean else [],
        "remaining_apply_blockers": [] if clean else [SCRATCH_CLEANLINESS_BLOCKER],
        "summary": summary,
    }


def _selected_jobs(plan: dict[str, Any], *, limit_jobs: int | None = None) -> list[dict[str, Any]]:
    jobs = list(plan.get("conversion_jobs") or [])
    if limit_jobs is not None:
        if limit_jobs < 0:
            raise ValueError("limit_jobs must be non-negative")
        jobs = jobs[:limit_jobs]
    return jobs


def _validated_job(job: dict[str, Any], *, source_root: Path, scratch_root: Path) -> dict[str, Any]:
    source_usd = _require_inside(
        str(job.get("source_usd") or ""),
        root=source_root,
        label="source_usd",
        root_label="source_root",
    )
    scratch_input = _require_inside(
        str(job.get("scratch_input_usd") or ""),
        root=scratch_root,
        label="scratch_input_usd",
        root_label="scratch_root",
    )
    expected_output = _require_inside(
        str(job.get("expected_top_output_usd") or ""),
        root=scratch_root,
        label="expected_top_output_usd",
        root_label="scratch_root",
    )
    argv = list(job.get("argv") or [])
    if not argv:
        argv = ["./scripts/isaac_python.sh", "./main.py", "no-mdl", "--only-new-usd", str(scratch_input)]
    return {
        **job,
        "source_usd": str(source_usd),
        "scratch_input_usd": str(scratch_input),
        "expected_top_output_usd": str(expected_output),
        "argv": argv,
        "scratch_input_exists": scratch_input.exists(),
        "source_usd_exists": source_usd.exists(),
        "expected_top_output_exists": expected_output.exists(),
        "timestamped_top_output_siblings": _timestamped_siblings(expected_output),
    }


def _job_current_blockers(
    job: dict[str, Any],
    *,
    remaining_blockers: list[str],
    scratch_root_exists: bool,
    duplicate_output_paths: set[str],
) -> list[str]:
    blockers: list[str] = []
    for blocker in remaining_blockers:
        if blocker == "scratch_root_missing":
            if not scratch_root_exists:
                blockers.append(blocker)
        elif blocker == "scratch_inputs_missing":
            if not job["scratch_input_exists"]:
                blockers.append(blocker)
        elif blocker == "source_usds_missing":
            if not job["source_usd_exists"]:
                blockers.append(blocker)
        elif blocker == "top_level_output_collisions_present":
            if job["expected_top_output_exists"] or job["timestamped_top_output_siblings"]:
                blockers.append(blocker)
        elif blocker == "duplicate_top_level_outputs_planned":
            if job["expected_top_output_usd"] in duplicate_output_paths:
                blockers.append(blocker)
        else:
            blockers.append(blocker)
    return blockers


def _with_current_job_safety(
    job: dict[str, Any],
    *,
    remaining_blockers: list[str],
    scratch_root_exists: bool,
    duplicate_output_paths: set[str],
) -> dict[str, Any]:
    blockers = _job_current_blockers(
        job,
        remaining_blockers=remaining_blockers,
        scratch_root_exists=scratch_root_exists,
        duplicate_output_paths=duplicate_output_paths,
    )
    return {
        **job,
        "source_plan_blocked_by": list(job.get("blocked_by") or []),
        "source_plan_safe_to_execute_now": bool(job.get("safe_to_execute_now")),
        "blocked_by": blockers,
        "safe_to_execute_now": not blockers,
    }


def build_multi_root_run_report(
    plan: dict[str, Any],
    *,
    limit_jobs: int | None = None,
    closure_report: dict[str, Any] | None = None,
    materialization_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a dry-run readiness report for the full no-MDL multi-root runner."""

    if plan.get("status") != "planned_full_grscenes_nomdl_scratch":
        raise ValueError("plan status must be planned_full_grscenes_nomdl_scratch")
    source_root, scratch_root = _plan_roots(plan)
    jobs = [
        _validated_job(job, source_root=source_root, scratch_root=scratch_root)
        for job in _selected_jobs(plan, limit_jobs=limit_jobs)
    ]
    closure_gate = _closure_gate(
        closure_report,
        plan=plan,
        jobs=jobs,
        source_root=source_root,
        scratch_root=scratch_root,
    )
    materialization_gate = _materialization_gate(
        materialization_report,
        plan=plan,
        source_root=source_root,
        scratch_root=scratch_root,
    )

    expected_outputs = [job["expected_top_output_usd"] for job in jobs]
    output_counts = Counter(expected_outputs)
    duplicate_output_paths = {path for path, count in output_counts.items() if count > 1}
    duplicate_expected_outputs = sorted(path for path, count in output_counts.items() for _ in range(max(0, count - 1)))
    existing_expected_outputs = sorted(job["expected_top_output_usd"] for job in jobs if job["expected_top_output_exists"])
    timestamped_outputs = sorted(
        sibling
        for job in jobs
        for sibling in job["timestamped_top_output_siblings"]
    )
    missing_scratch_inputs = sorted(job["scratch_input_usd"] for job in jobs if not job["scratch_input_exists"])
    missing_source_usds = sorted(job["source_usd"] for job in jobs if not job["source_usd_exists"])

    plan_blockers = list((plan.get("safety") or {}).get("apply_blockers") or [])
    satisfied_blockers = [RUNNER_MISSING_BLOCKER] if RUNNER_MISSING_BLOCKER in plan_blockers else []
    satisfied_blockers.extend(closure_gate["satisfied_apply_blockers"])
    satisfied_blockers.extend(materialization_gate["satisfied_apply_blockers"])
    satisfied_set = set(satisfied_blockers)
    remaining_blockers = [blocker for blocker in plan_blockers if blocker not in satisfied_set]
    remaining_blockers.extend(closure_gate["remaining_apply_blockers"])
    if materialization_report is not None:
        remaining_blockers = [
            blocker for blocker in remaining_blockers if blocker not in set(materialization_gate["satisfied_apply_blockers"])
        ]
        remaining_blockers.extend(materialization_gate["remaining_apply_blockers"])
    if not scratch_root.exists():
        remaining_blockers.append("scratch_root_missing")
    if missing_scratch_inputs:
        remaining_blockers.append("scratch_inputs_missing")
    if missing_source_usds:
        remaining_blockers.append("source_usds_missing")
    if existing_expected_outputs or timestamped_outputs:
        remaining_blockers.append("top_level_output_collisions_present")
    if duplicate_expected_outputs:
        remaining_blockers.append("duplicate_top_level_outputs_planned")
    remaining_blockers = _dedupe_preserve_order(remaining_blockers)
    apply_ready = not remaining_blockers
    scratch_root_exists = scratch_root.exists()
    jobs = [
        _with_current_job_safety(
            job,
            remaining_blockers=remaining_blockers,
            scratch_root_exists=scratch_root_exists,
            duplicate_output_paths=duplicate_output_paths,
        )
        for job in jobs
    ]

    summary = {
        "planned_job_count": len(jobs),
        "scratch_root_exists": scratch_root_exists,
        "source_usd_missing_count": len(missing_source_usds),
        "scratch_input_missing_count": len(missing_scratch_inputs),
        "existing_expected_top_output_count": len(existing_expected_outputs),
        "existing_timestamped_top_output_count": len(timestamped_outputs),
        "duplicate_expected_top_output_count": len(duplicate_expected_outputs),
        "top_level_output_collision_count": (
            len(existing_expected_outputs)
            + len(timestamped_outputs)
            + len(duplicate_expected_outputs)
        ),
        "apply_ready": apply_ready,
    }
    return {
        "schema_version": 1,
        "status": "planned_full_grscenes_nomdl_multi_root_run",
        "generated_by": "paper/shared/evidence/experiments/06_grscenes_vlm_grounding/run_full_nomdl_multi_root.py",
        "generated_at_utc": _utc_now(),
        "dry_run": True,
        "apply_ready": apply_ready,
        "source_root": str(source_root),
        "scratch_root": str(scratch_root),
        "source_plan_status": plan.get("status"),
        "source_plan_generated_at_utc": plan.get("generated_at_utc"),
        "runner_strategy": {
            "process_model": "single_python_process_one_processor_instance",
            "processor_done_scope": "shared_across_all_selected_roots",
            "only_new_usd": True,
            "imports_no_mdl_on_dry_run": False,
            "apply_imports_processor_after_readiness_gate": True,
            "closure_report_consumed": bool(closure_gate["provided"]),
            "materialization_report_consumed": bool(materialization_gate["provided"]),
        },
        "closure_gate": closure_gate,
        "materialization_gate": materialization_gate,
        "safety": {
            "source_root_immutable": True,
            "safe_to_apply": apply_ready,
            "satisfied_apply_blockers": _dedupe_preserve_order(satisfied_blockers),
            "remaining_apply_blockers": remaining_blockers,
        },
        "summary": summary,
        "collision_scan": {
            "scan_scope": "planned_top_level_outputs_only",
            "existing_expected_top_outputs": existing_expected_outputs,
            "existing_timestamped_top_outputs": timestamped_outputs,
            "duplicate_expected_top_outputs": duplicate_expected_outputs,
            "missing_scratch_inputs": missing_scratch_inputs,
            "missing_source_usds": missing_source_usds,
            "recursive_dependency_outputs": "not_scanned",
        },
        "jobs": jobs,
        "notes": [
            "This report does not convert assets.",
            "When a closure report is supplied, it is consumed as pure JSON before any no-MDL import.",
            "Use jobs[*].scratch_input_usd as the runner contract; command strings in the source plan are preview text.",
        ],
    }


def run_multi_root_conversion(
    plan: dict[str, Any],
    *,
    limit_jobs: int | None = None,
    closure_report: dict[str, Any] | None = None,
    materialization_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run no-MDL for all ready scratch roots with one shared Processor."""

    report = build_multi_root_run_report(
        plan,
        limit_jobs=limit_jobs,
        closure_report=closure_report,
        materialization_report=materialization_report,
    )
    if not report["apply_ready"]:
        blockers = ", ".join(report["safety"]["remaining_apply_blockers"])
        raise ValueError(f"multi-root no-MDL apply is not ready: {blockers}")
    if closure_report is None:
        raise ValueError("closure report is required for multi-root no-MDL apply")

    from convert_asset.no_mdl import processor as processor_module  # pylint: disable=import-error
    from convert_asset.no_mdl.processor import Processor  # pylint: disable=import-error

    processor_module.RUNTIME_ONLY_NEW_USD = True
    processor = Processor()
    results: list[dict[str, Any]] = []
    for job in report["jobs"]:
        output = processor.process(str(job["scratch_input_usd"]))
        results.append(
            {
                "conversion_job_id": job.get("conversion_job_id"),
                "scratch_input_usd": job["scratch_input_usd"],
                "top_output_usd": output,
                "processor_done_count": len(processor.done),
            }
        )
    return {
        **report,
        "dry_run": False,
        "converted_at_utc": _utc_now(),
        "results": results,
        "processor_done_count": len(processor.done),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--closure-report", type=Path, default=None)
    parser.add_argument("--materialization-report", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit-jobs", type=int, default=None)
    parser.add_argument("--apply", action="store_true", help="Run conversion only if every readiness blocker is gone")
    args = parser.parse_args()

    plan = _load_json(args.plan)
    closure_report = _load_json(args.closure_report) if args.closure_report else None
    materialization_report = _load_json(args.materialization_report) if args.materialization_report else None
    output_path = validate_output_path(args.out, plan=plan)
    report = (
        run_multi_root_conversion(
            plan,
            limit_jobs=args.limit_jobs,
            closure_report=closure_report,
            materialization_report=materialization_report,
        )
        if args.apply
        else build_multi_root_run_report(
            plan,
            limit_jobs=args.limit_jobs,
            closure_report=closure_report,
            materialization_report=materialization_report,
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote {output_path} with {report['summary']['planned_job_count']} jobs, "
        f"dry_run={report['dry_run']}, apply_ready={report['apply_ready']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
