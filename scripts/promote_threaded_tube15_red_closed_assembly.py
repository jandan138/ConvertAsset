#!/usr/bin/env python3
"""Promote the one-rigid-body threaded 15 mL closed assembly."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


PACKAGE_ID = "threaded_tube15_red_closed_assembly"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def runs_pass(runs: list[dict[str, Any]]) -> bool:
    return len(runs) == 3 and all(
        run.get("overall_status") == "pass"
        and str(run.get("runtime", {}).get("kit_version", "")).startswith("4.1")
        for run in runs
    )


def promote(asset_set: Path) -> Path:
    paths = sorted((asset_set / "evidence/runtime").glob("run_*.json"))
    runs = [json.loads(path.read_text()) for path in paths]
    if not runs_pass(runs):
        raise RuntimeError("three Isaac Sim 4.1 assembly runs must pass")
    package = asset_set / "packages" / PACKAGE_ID
    report = {
        "schema_version": "aan.threaded_tube15_red_closed_qualification.v1",
        "overall_status": "pass",
        "runtime": "isaac41",
        "runs": [
            {"path": str(path.relative_to(asset_set)), "sha256": _sha(path)}
            for path in paths
        ],
        "claims": {
            "single_rigid_body_closed_assembly": True,
            "dynamic_runtime_qualified": True,
            "gravity_response": True,
            "fixed_carrier_transport": True,
            "cap_relative_pose_invariant": True,
            "target_slot_insertion": False,
            "robot_policy_success": False,
            "task_success": False,
            "benchmark_success": False,
        },
        "claim_boundary": (
            "Robot-free dynamic motion of the fixed closed assembly only; slot/rack fit, "
            "cap tightening, robot policy, task and benchmark success are not claimed."
        ),
    }
    report_path = asset_set / "evidence/runtime_qualification_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest_path = package / "evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["overall_status"] = "pass"
    manifest["blocked_reasons"] = []
    manifest["claims"]["dynamic_runtime_qualified"] = True
    manifest["runtime_qualification"] = {
        "report": "../../../evidence/runtime_qualification_report.json",
        "report_sha256": _sha(report_path),
        "runtime": "isaac41",
        "cold_runs": 3,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    index_path = asset_set / "asset_set_manifest.json"
    index = json.loads(index_path.read_text())
    index["status"] = "pass"
    index["assets"][0]["overall_status"] = "pass"
    index["assets"][0]["producer_manifest_sha256"] = _sha(manifest_path)
    index["claims"] = manifest["claims"]
    index["runtime_qualification"] = {
        "report": "evidence/runtime_qualification_report.json",
        "report_sha256": _sha(report_path),
        "runtime": "isaac41",
    }
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-set", type=Path, required=True)
    args = parser.parse_args()
    print(promote(args.asset_set.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
