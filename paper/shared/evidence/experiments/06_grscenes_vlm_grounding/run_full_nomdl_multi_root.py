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


def build_multi_root_run_report(plan: dict[str, Any], *, limit_jobs: int | None = None) -> dict[str, Any]:
    """Build a dry-run readiness report for the full no-MDL multi-root runner."""

    if plan.get("status") != "planned_full_grscenes_nomdl_scratch":
        raise ValueError("plan status must be planned_full_grscenes_nomdl_scratch")
    source_root, scratch_root = _plan_roots(plan)
    jobs = [
        _validated_job(job, source_root=source_root, scratch_root=scratch_root)
        for job in _selected_jobs(plan, limit_jobs=limit_jobs)
    ]

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
    remaining_blockers = [blocker for blocker in plan_blockers if blocker != RUNNER_MISSING_BLOCKER]
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
        },
        "safety": {
            "source_root_immutable": True,
            "safe_to_apply": apply_ready,
            "satisfied_apply_blockers": satisfied_blockers,
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
            "It removes only the runner-missing blocker; dependency closure and recursive output collision scan still need separate evidence.",
            "Use jobs[*].scratch_input_usd as the runner contract; command strings in the source plan are preview text.",
        ],
    }


def run_multi_root_conversion(plan: dict[str, Any], *, limit_jobs: int | None = None) -> dict[str, Any]:
    """Run no-MDL for all ready scratch roots with one shared Processor."""

    report = build_multi_root_run_report(plan, limit_jobs=limit_jobs)
    if not report["apply_ready"]:
        blockers = ", ".join(report["safety"]["remaining_apply_blockers"])
        raise ValueError(f"multi-root no-MDL apply is not ready: {blockers}")

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
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit-jobs", type=int, default=None)
    parser.add_argument("--apply", action="store_true", help="Run conversion only if every readiness blocker is gone")
    args = parser.parse_args()

    plan = _load_json(args.plan)
    output_path = validate_output_path(args.out, plan=plan)
    report = (
        run_multi_root_conversion(plan, limit_jobs=args.limit_jobs)
        if args.apply
        else build_multi_root_run_report(plan, limit_jobs=args.limit_jobs)
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
