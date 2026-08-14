#!/usr/bin/env python3
"""Finalize a Task 02 r8.2 candidate from measured stage and runtime gates."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def finalize(
    *, package: Path, stage_report: Path, runtime_observation: Path
) -> dict[str, Any]:
    package = package.resolve()
    stage_report = stage_report.resolve()
    runtime_observation = runtime_observation.resolve()
    stage = _load(stage_report)
    runtime = _load(runtime_observation)
    stage_pass = stage.get("overall_status") == "pass"
    runtime_pass = runtime.get("overall_status") == "pass"
    failed_checks = sorted(
        name for name, passed in runtime.get("checks", {}).items() if not passed
    )
    blocked_reasons: list[str] = []
    if not stage_pass:
        blocked_reasons.append("three_cold_five_update_admission_failed")
    if not runtime_pass:
        blocked_reasons.append("fluid_runtime_qualification_failed")
    if not runtime.get("checks", {}).get("gpu_cooking", False):
        blocked_reasons.append(
            "visible_mesh_convex_decomposition_not_gpu_particle_compatible"
        )
    report = {
        "schema_version": "aan.task02_r82_admission_report.v1",
        "overall_status": "pass" if stage_pass and runtime_pass else "blocked",
        "stage_update_admission": {
            "status": stage.get("overall_status"),
            "required_cold_runs": stage.get("required_cold_runs"),
            "report": str(stage_report.relative_to(package)),
            "sha256": _sha(stage_report),
        },
        "runtime_qualification": {
            "status": runtime.get("overall_status"),
            "failed_checks": failed_checks,
            "observation": str(runtime_observation.relative_to(package)),
            "sha256": _sha(runtime_observation),
            "static_retention_ratio": runtime.get("static_hold", {}).get(
                "minimum_source_ratio"
            ),
            "target_ratio": runtime.get("pour", {}).get("target_ratio"),
            "tabletop_spill_ratio": runtime.get("pour", {}).get("tabletop_spill_ratio"),
            "mean_rtx_fps": runtime.get("performance", {}).get("mean_rtx_fps"),
            "hard_runtime_errors": runtime.get("hard_runtime_errors", []),
        },
        "blocked_reasons": blocked_reasons,
        "promotion": {
            "allowed": not blocked_reasons,
            "reason": blocked_reasons[0] if blocked_reasons else None,
        },
        "claim_boundary": (
            "Physics-only admission. A pass would not claim robot grasp, policy, "
            "benchmark, or full task success; this measured candidate is blocked."
        ),
    }
    report_path = package / "evidence/qualification_report.json"
    _write(report_path, report)

    manifest_path = package / "evidence/manifest.json"
    manifest = _load(manifest_path)
    manifest["overall_status"] = report["overall_status"]
    manifest["blocked_reasons"] = blocked_reasons
    manifest["qualification_report"] = {
        "path": str(report_path.relative_to(package)),
        "sha256": _sha(report_path),
    }
    manifest["promotion"] = report["promotion"]
    manifest["claims"]["physics_package_candidate"] = not blocked_reasons
    _write(manifest_path, manifest)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--stage-report", required=True, type=Path)
    parser.add_argument("--runtime-observation", required=True, type=Path)
    args = parser.parse_args()
    report = finalize(
        package=args.package,
        stage_report=args.stage_report,
        runtime_observation=args.runtime_observation,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
