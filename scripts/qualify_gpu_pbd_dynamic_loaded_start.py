#!/usr/bin/env python3
"""Qualify a source-bound GPU-PBD container's dynamic loaded start.

The Isaac worker produces one dry-settled entry-root pose, one particle cloud
expressed in that root's local frame, and three cold-start observations.  This
orchestrator validates and hash-binds those artifacts without changing vessel
collision or liquid parameters.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import statistics
import subprocess
from typing import Any, Mapping


REQUIRED_COLD_RUNS = 3
MAXIMUM_OUTSIDE_SOURCE = 2
MAXIMUM_ROOT_TAIL_DRIFT_M = 0.001
MAXIMUM_ROOT_TILT_DEG = 2.0


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def cold_run_checks(
    run: Mapping[str, Any], *, thresholds: Mapping[str, Any]
) -> dict[str, bool]:
    return {
        "particle_count": int(run.get("particle_count", -1))
        == int(thresholds["particle_count"]),
        "outside_source": int(run.get("maximum_outside_source_count", 10**9))
        <= int(thresholds["maximum_outside_source_before_lift"]),
        "entry_root_tail_drift": float(
            run.get("entry_root_tail_drift_m", float("inf"))
        )
        <= float(thresholds["maximum_entry_root_tail_drift_m"]),
        "entry_root_tilt": float(
            run.get("maximum_entry_root_tilt_deg", float("inf"))
        )
        <= float(thresholds["maximum_entry_root_tilt_deg"]),
        "runtime_errors": run.get("hard_runtime_errors") == [],
    }


def cold_run_passes(
    run: Mapping[str, Any], *, thresholds: Mapping[str, Any]
) -> bool:
    return all(cold_run_checks(run, thresholds=thresholds).values())


def dynamic_loaded_start_contract(
    *,
    support_plane_z_m: float,
    stable_pose: Mapping[str, Any],
    particle_state_name: str,
    particle_state_sha256: str,
    particle_count: int,
) -> dict[str, Any]:
    xyz = [float(value) for value in stable_pose["xyz_m"]]
    wxyz = [float(value) for value in stable_pose["wxyz"]]
    return {
        "schema_version": "aan.gpu_pbd_dynamic_loaded_start.v1",
        "support_plane_z_m": float(support_plane_z_m),
        "support_plane_to_entry_root": {
            "xyz_m": [xyz[0], xyz[1], xyz[2] - float(support_plane_z_m)],
            "wxyz": wxyz,
        },
        "particle_state": particle_state_name,
        "particle_state_sha256": particle_state_sha256,
        "particle_count": int(particle_count),
        "qualification": {
            "required_cold_runs": REQUIRED_COLD_RUNS,
            "maximum_outside_source_before_lift": MAXIMUM_OUTSIDE_SOURCE,
            "maximum_entry_root_tail_drift_m": MAXIMUM_ROOT_TAIL_DRIFT_M,
            "maximum_entry_root_tilt_deg": MAXIMUM_ROOT_TILT_DEG,
        },
        "immutable_physics_boundary": {
            "collider_changes": False,
            "rest_offset_changes": False,
            "contact_offset_changes": False,
            "friction_changes": False,
            "particle_parameter_changes": False,
        },
        "claim_boundary": (
            "Dynamic loaded-start initialization on the recorded support plane only; "
            "no robot, pour, benchmark, or general physical-accuracy claim."
        ),
    }


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON mapping: {path}")
    return value


def _run_worker(
    *,
    wrapper: Path,
    worker: Path,
    scene: Path,
    mode: str,
    out: Path,
    support_plane_z_m: float,
    pose: Path | None = None,
    particle_state: Path | None = None,
    run_index: int | None = None,
) -> None:
    command = [
        str(wrapper),
        str(worker),
        "--scene",
        str(scene),
        "--mode",
        mode,
        "--support-plane-z-m",
        str(support_plane_z_m),
        "--out",
        str(out),
    ]
    if pose is not None:
        command.extend(["--pose", str(pose)])
    if particle_state is not None:
        command.extend(["--particle-state", str(particle_state)])
    if run_index is not None:
        command.extend(["--run-index", str(run_index)])
    completed = subprocess.run(command, check=False, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Isaac worker {mode} failed with {completed.returncode}")


def qualify(
    *,
    scene: Path,
    output: Path,
    particle_count: int,
    support_plane_z_m: float,
    wrapper: Path,
    worker: Path,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    dry_runs: list[dict[str, Any]] = []
    for index in range(1, REQUIRED_COLD_RUNS + 1):
        path = output / f"dry_settle_run_{index}.json"
        _run_worker(
            wrapper=wrapper,
            worker=worker,
            scene=scene,
            mode="dry-settle",
            out=path,
            support_plane_z_m=support_plane_z_m,
            run_index=index,
        )
        dry_runs.append(_load(path))
    if any(
        run.get("overall_status") != "pass"
        or not str(run.get("runtime", {}).get("kit_version", "")).startswith("4.1")
        for run in dry_runs
    ):
        raise ValueError("dry-settle run did not stabilize")

    xyz = [
        statistics.median(float(run["stable_pose"]["xyz_m"][axis]) for run in dry_runs)
        for axis in range(3)
    ]
    wxyz = [
        statistics.median(float(run["stable_pose"]["wxyz"][axis]) for run in dry_runs)
        for axis in range(4)
    ]
    pose_path = output / "stable_entry_root_pose.json"
    pose_path.write_text(
        json.dumps({"xyz_m": xyz, "wxyz": wxyz}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    state_path = output / "dynamic_loaded_particle_state.json"
    _run_worker(
        wrapper=wrapper,
        worker=worker,
        scene=scene,
        mode="pre-settle",
        out=state_path,
        support_plane_z_m=support_plane_z_m,
        pose=pose_path,
    )
    state = _load(state_path)
    if (
        state.get("schema_version")
        != "aan.gpu_pbd_source_local_particle_state.v1"
        or state.get("coordinate_space") != "source_entry_root_local"
        or int(state.get("particle_count", -1)) != particle_count
        or int(state.get("outside_source_count", -1)) != 0
        or not str(state.get("runtime", {}).get("kit_version", "")).startswith("4.1")
    ):
        raise ValueError("pre-settled particle state failed static admission")

    contract_path = output / "dynamic_loaded_start_contract.json"
    contract = dynamic_loaded_start_contract(
        support_plane_z_m=support_plane_z_m,
        stable_pose={"xyz_m": xyz, "wxyz": wxyz},
        particle_state_name=state_path.name,
        particle_state_sha256=_sha(state_path),
        particle_count=particle_count,
    )
    contract_path.write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    thresholds = {"particle_count": particle_count, **contract["qualification"]}
    cold_runs: list[dict[str, Any]] = []
    for index in range(1, REQUIRED_COLD_RUNS + 1):
        path = output / f"cold_start_run_{index}.json"
        _run_worker(
            wrapper=wrapper,
            worker=worker,
            scene=scene,
            mode="validate",
            out=path,
            support_plane_z_m=support_plane_z_m,
            pose=pose_path,
            particle_state=state_path,
            run_index=index,
        )
        run = _load(path)
        if not str(run.get("runtime", {}).get("kit_version", "")).startswith("4.1"):
            run["hard_runtime_errors"] = [
                "dynamic-loaded-start qualification requires Isaac Sim 4.1"
            ]
        run["checks"] = cold_run_checks(run, thresholds=thresholds)
        run["overall_status"] = (
            "pass" if cold_run_passes(run, thresholds=thresholds) else "blocked"
        )
        path.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        cold_runs.append(run)
    passed = all(cold_run_passes(run, thresholds=thresholds) for run in cold_runs)
    report = {
        "schema_version": "aan.gpu_pbd_dynamic_loaded_start_report.v1",
        "overall_status": "pass" if passed else "blocked",
        "contract_sha256": _sha(contract_path),
        "particle_state_sha256": _sha(state_path),
        "dry_settle_runs": dry_runs,
        "cold_runs": cold_runs,
        "promotion": {
            "allowed": passed,
            "claim": "gpu_pbd_dynamic_loaded_start",
        },
        "claim_boundary": contract["claim_boundary"],
    }
    report_path = output / "dynamic_loaded_start_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--particle-count", required=True, type=int)
    parser.add_argument("--support-plane-z-m", type=float, default=0.0)
    parser.add_argument(
        "--wrapper",
        type=Path,
        default=Path(__file__).with_name("isaac_python.sh"),
    )
    parser.add_argument(
        "--worker",
        type=Path,
        default=Path(__file__).with_name("observe_gpu_pbd_dynamic_loaded_start.py"),
    )
    args = parser.parse_args()
    report = qualify(
        scene=args.scene.resolve(),
        output=args.out.resolve(),
        particle_count=args.particle_count,
        support_plane_z_m=args.support_plane_z_m,
        wrapper=args.wrapper.resolve(),
        worker=args.worker.resolve(),
    )
    print(args.out.resolve())
    return 0 if report["overall_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
