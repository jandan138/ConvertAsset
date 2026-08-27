#!/usr/bin/env python3
"""Promote the Wangshuai dynamic asset set after recorded Isaac 4.1 gates."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any


DYNAMIC_IDS = (
    "tube15_threaded_liquid_dynamic",
    "tube15_threaded_closed_cap_dynamic",
    "funnel_small_v2_liquid_dynamic",
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def qualification_passes(
    rigid: list[dict[str, Any]], pbd: list[dict[str, Any]]
) -> bool:
    runs = rigid + pbd
    return (
        len(rigid) == 9
        and len(pbd) == 3
        and all(
            run.get("overall_status") == "pass"
            and str(run.get("runtime", {}).get("kit_version", "")).startswith("4.1")
            for run in runs
        )
    )


def promote(asset_set: Path) -> Path:
    rigid_paths = sorted((asset_set / "evidence/rigid").glob("*/run_*.json"))
    pbd_paths = sorted((asset_set / "evidence/pbd").glob("run_*.json"))
    rigid = [_load(path) for path in rigid_paths]
    pbd = [_load(path) for path in pbd_paths]
    diagnostic_paths = sorted((asset_set / "evidence/pbd/diagnostics").glob("*.json"))
    diagnostics = [_load(path) for path in diagnostic_paths]
    if not qualification_passes(rigid, pbd):
        raise ValueError("dynamic asset set does not have 9 rigid + 3 PBD Isaac 4.1 passes")

    index_path = asset_set / "asset_set_manifest.json"
    candidate_sha = _sha(index_path)
    report = {
        "schema_version": "aan.wangshuai_dynamic_asset_set_qualification.v1",
        "overall_status": "pass",
        "runtime": "isaac41",
        "candidate_asset_set_manifest_sha256": candidate_sha,
        "rigid_runs": [
            {"path": str(path.relative_to(asset_set)), "sha256": _sha(path)}
            for path in rigid_paths
        ],
        "pbd_runs": [
            {"path": str(path.relative_to(asset_set)), "sha256": _sha(path)}
            for path in pbd_paths
        ],
        "retained_diagnostics": [
            {"path": str(path.relative_to(asset_set)), "sha256": _sha(path)}
            for path in diagnostic_paths
        ],
        "observed_ranges": {
            "funnel_to_tube_capture_ratio": [
                min(run["observations"]["capture_ratio_before_move"] for run in pbd),
                max(run["observations"]["capture_ratio_before_move"] for run in pbd),
            ],
            "moving_open_tube_retention_ratio": [
                min(run["observations"]["capture_ratio_after_move"] for run in pbd),
                max(run["observations"]["capture_ratio_after_move"] for run in pbd),
            ],
        },
        "claims": {
            "effective_kinematic": False,
            "collision_geometry_unchanged": True,
            "dynamic_gravity_response": True,
            "dynamic_fixed_joint_transport": True,
            "dynamic_funnel_to_tube_pbd": True,
            "dynamic_loaded_liquid_transport": not diagnostics and all(
                run.get("checks", {}).get("moving_tube_retention") is True
                for run in pbd
            ),
            "robot_policy_success": False,
            "task_success": False,
            "benchmark_success": False,
            "physical_parameters_measured": False,
        },
        "claim_boundary": (
            "Geometry-derived provisional mass/inertia, robot-free gravity and fixed-joint "
            "transport, and stationary funnel-to-tube GPU-PBD flow. Loaded liquid "
            "transport remains unqualified; no robot, task, benchmark, thread engagement, "
            "or measured-material-parameter claim."
        ),
    }
    report_path = asset_set / "evidence/runtime_qualification_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    report_sha = _sha(report_path)

    index = _load(index_path)
    for item in index["assets"]:
        if item["id"] not in DYNAMIC_IDS:
            continue
        manifest_path = asset_set / item["package"] / "evidence/manifest.json"
        manifest = _load(manifest_path)
        manifest["overall_status"] = "pass"
        manifest["blocked_reasons"] = []
        manifest["claims"]["dynamic_runtime_qualified"] = True
        manifest["claims"]["dynamic_loaded_liquid_transport"] = report["claims"][
            "dynamic_loaded_liquid_transport"
        ]
        manifest["runtime_qualification"] = {
            "runtime": "isaac41",
            "report": os.path.relpath(report_path, manifest_path.parent),
            "report_sha256": report_sha,
            "required_rigid_cold_runs": 3,
            "required_shared_pbd_cold_runs": 3,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        item["overall_status"] = "pass"
        item["producer_manifest_sha256"] = _sha(manifest_path)
    index["overall_status"] = "pass"
    index["status"] = "pass"
    index["blocked_reasons"] = []
    index["claims"]["dynamic_runtime_qualified"] = True
    index["claims"]["dynamic_loaded_liquid_transport"] = report["claims"][
        "dynamic_loaded_liquid_transport"
    ]
    index["runtime_qualification"] = {
        "runtime": "isaac41",
        "report": str(report_path.relative_to(asset_set)),
        "report_sha256": report_sha,
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
