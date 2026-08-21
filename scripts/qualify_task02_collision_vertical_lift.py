#!/usr/bin/env python3
"""Run the prescribed vertical-lift gate for statically eligible A/B routes."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping


def evaluate_lift_runs(runs: list[Mapping[str, Any]]) -> dict[str, Any]:
    blockers = []
    if len(runs) != 3:
        blockers.append("required_three_lift_runs")
    for index, run in enumerate(runs, start=1):
        if run.get("overall_status") != "pass":
            blockers.append(f"run_{index}:lift_gate_blocked")
    return {
        "overall_status": "pass" if not blockers else "blocked",
        "blocked_reasons": blockers,
        "run_count": len(runs),
        "maximum_outside_source_count": max(
            (int(run.get("maximum_outside_source_count", 10**9)) for run in runs),
            default=None,
        ),
        "maximum_below_source_floor_count": max(
            (int(run.get("maximum_below_source_floor_count", 10**9)) for run in runs),
            default=None,
        ),
        "maximum_root_tracking_error_m": max(
            (float(run.get("maximum_root_tracking_error_m", float("inf"))) for run in runs),
            default=None,
        ),
    }


def _environment() -> dict[str, str]:
    result = dict(os.environ)
    for name in (
        "PYTHONPATH",
        "LD_LIBRARY_PATH",
        "CARB_APP_PATH",
        "EXP_PATH",
        "ISAAC_PATH",
        "ISAAC_SIM_ROOT",
    ):
        result.pop(name, None)
    result["ACCEPT_EULA"] = "Y"
    result.setdefault("PRIVACY_CONSENT", "Y")
    return result


def qualify(*, ab_root: Path, isaac_python: Path, worker: Path) -> dict[str, Any]:
    static = json.loads((ab_root / "static_ab_report.json").read_text())
    routes = []
    for item in static["routes"]:
        route = item["route"]
        if not item["dynamic_eligible"]:
            routes.append(
                {
                    "route": route,
                    "status": "skipped_static_blocked",
                    "static_validation": item["static_validation"],
                }
            )
            continue
        root = ab_root / route
        runs = []
        for index in range(1, 4):
            destination = root / "evidence" / f"vertical_lift_run_{index}.json"
            completed = subprocess.run(
                [
                    str(isaac_python),
                    str(worker),
                    "--scene",
                    str(root / "scene.usda"),
                    "--fixture",
                    str(root / "transfer_fixture_profile.json"),
                    "--particle-state",
                    str(root / "evidence/static_run_1.json"),
                    "--run-index",
                    str(index),
                    "--out",
                    str(destination),
                ],
                check=False,
                env=_environment(),
            )
            if destination.is_file():
                run = json.loads(destination.read_text())
                run["worker_process_exit_code"] = completed.returncode
                runs.append(run)
            else:
                runs.append({"overall_status": "blocked", "worker_process_exit_code": completed.returncode})
                break
        routes.append(
            {
                "route": route,
                "status": "executed",
                "lift_validation": evaluate_lift_runs(runs),
            }
        )
    report = {
        "schema_version": "aan.task02_collision_route_dynamic_report.v1",
        "routes": routes,
        "claim_boundary": "Prescribed vertical kinematic lift only; no robot or pour claim.",
    }
    destination = ab_root / "dynamic_lift_report.json"
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ab-root", required=True, type=Path)
    parser.add_argument("--isaac-python", required=True, type=Path)
    parser.add_argument(
        "--worker",
        type=Path,
        default=Path(__file__).with_name("observe_task02_vertical_lift.py"),
    )
    args = parser.parse_args()
    report = qualify(
        ab_root=args.ab_root.resolve(),
        isaac_python=args.isaac_python.resolve(),
        worker=args.worker.resolve(),
    )
    print(args.ab_root.resolve())
    control = next(
        item for item in report["routes"] if item["route"] == "qualified_unified_proxy_control"
    )
    return 0 if control["lift_validation"]["overall_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
