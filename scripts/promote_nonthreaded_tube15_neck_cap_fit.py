#!/usr/bin/env python3
"""Promote the corrected non-threaded tube/cap geometry master."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def runs_pass(runs: list[dict[str, Any]]) -> bool:
    return len(runs) == 3 and all(
        run.get("overall_status") == "pass"
        and str(run.get("runtime", {}).get("kit_version", "")).startswith("4.1")
        for run in runs
    )


def promote(root: Path) -> Path:
    paths = sorted((root / "evidence/runtime").glob("run_*.json"))
    runs = [json.loads(path.read_text()) for path in paths]
    if not runs_pass(runs):
        raise RuntimeError("three Isaac Sim 4.1 runs must pass")
    report = {
        "schema_version": "aan.nonthreaded_tube15_neck_cap_fit_qualification.v1",
        "overall_status": "pass",
        "runtime": "isaac41",
        "runs": [
            {"path": str(path.relative_to(root)), "sha256": _sha(path)}
            for path in paths
        ],
        "claims": {
            "neck_matches_effective_cap_sleeve": True,
            "dynamic_closed_assembly_qualified": True,
            "thread_geometry_present": False,
            "existing_task_packages_replaced": False,
            "robot_policy_success": False,
            "task_success": False,
            "benchmark_success": False,
        },
        "claim_boundary": (
            "Geometry-corrected non-threaded modeling master and robot-free closed-assembly "
            "motion only; no thread, liquid, robot, task, or benchmark claim."
        ),
    }
    report_path = root / "evidence/runtime_qualification_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest_path = root / "asset_set_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["status"] = "pass"
    manifest["blocked_reasons"] = []
    manifest["claims"] = report["claims"]
    manifest["runtime_qualification"] = {
        "report": "evidence/runtime_qualification_report.json",
        "report_sha256": _sha(report_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(promote(args.root.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
