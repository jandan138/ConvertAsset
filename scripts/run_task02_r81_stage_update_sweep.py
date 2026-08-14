#!/usr/bin/env python3
"""Run cold Isaac 4.1 five-update probes for the Task 02 r8.1 candidates."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any


FORMAL_ISAAC41_PREFIX = Path(
    "/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/"
    "embodied-eval-os-sim-isaacsim41-genmanip-py310"
)
SCRIPT = Path(__file__).with_name("probe_task02_r81_stage_update.py")
_TIMING = re.compile(r"^(APP_READY|OPEN_RETURN|UPDATE_[0-9]{2})_SECONDS=([0-9.]+)$")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _environment(root: Path) -> dict[str, str]:
    directories = {
        "HOME": root / "home",
        "TMPDIR": root / "tmp",
        "XDG_CACHE_HOME": root / "xdg-cache",
        "XDG_CONFIG_HOME": root / "xdg-config",
        "XDG_DATA_HOME": root / "xdg-data",
        "XDG_STATE_HOME": root / "xdg-state",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=False)
    site = FORMAL_ISAAC41_PREFIX / "lib/python3.10/site-packages"
    library_paths = (
        site / "isaacsim/extscache/omni.cuda.libs/bin",
        site / "isaacsim/extscache/omni.gpu_foundation/bin/deps",
        site / "torch/lib",
    )
    return {
        **{name: str(path) for name, path in directories.items()},
        "PATH": f"{FORMAL_ISAAC41_PREFIX / 'bin'}:/usr/local/bin:/usr/bin:/bin",
        "LD_LIBRARY_PATH": ":".join(str(path) for path in library_paths),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "ACCEPT_EULA": "Y",
        "OMNI_KIT_ACCEPT_EULA": "YES",
    }


def classify_probe(
    *, returncode: int, stdout: str, elapsed_seconds: float, timeout_seconds: float
) -> dict[str, Any]:
    timings = {
        match.group(1).lower() + "_seconds": float(match.group(2))
        for line in stdout.splitlines()
        if (match := _TIMING.match(line.strip()))
    }
    opened = "open_return_seconds" in timings
    update_count = sum(key.startswith("update_") for key in timings)
    # Kit may abort during teardown after the observation was already flushed;
    # teardown is outside this narrow stage-update gate.
    if update_count == 5:
        status = "five_updates_completed"
        reason = None
    elif opened and update_count < 5 and elapsed_seconds >= timeout_seconds:
        status = "blocked_update_timeout"
        reason = "five_rtx_updates_did_not_complete_before_timeout"
    else:
        status = "blocked_runtime"
        reason = "probe_process_failed_or_stage_did_not_open"
    return {
        "status": status,
        "blocked_reason": reason,
        "returncode": returncode,
        "elapsed_seconds": elapsed_seconds,
        "timeout_seconds": timeout_seconds,
        "timings": timings,
        "completed_update_count": update_count,
    }


def _summary_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        key: run[key]
        for key in (
            "run_index",
            "status",
            "blocked_reason",
            "completed_update_count",
            "returncode",
            "elapsed_seconds",
            "timeout_seconds",
            "timings",
            "scene_sha256",
            "scene_dependency_sha256",
            "stdout_sha256",
            "stderr_sha256",
        )
    }


def _scene_dependency_sha256(scene: Path) -> dict[str, str]:
    component = scene.parent / "component.usda"
    return {"component.usda": _sha(component)} if component.is_file() else {}


def _run_one(
    *, scene: Path, root: Path, run_index: int, timeout_seconds: float
) -> dict[str, Any]:
    runtime_root = root / f"run_{run_index:02d}" / "runtime"
    output_root = runtime_root.parent
    output_root.mkdir(parents=True, exist_ok=False)
    command = [
        "/usr/bin/timeout",
        "--signal=TERM",
        "--kill-after=10s",
        f"{timeout_seconds}s",
        str(FORMAL_ISAAC41_PREFIX / "bin/python"),
        "-I",
        "-B",
        str(SCRIPT),
        "--scene",
        str(scene),
    ]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=SCRIPT.parents[1],
        env=_environment(runtime_root),
        check=False,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - started
    (output_root / "stdout.log").write_text(completed.stdout, encoding="utf-8")
    (output_root / "stderr.log").write_text(completed.stderr, encoding="utf-8")
    observation = classify_probe(
        returncode=completed.returncode,
        stdout=completed.stdout,
        elapsed_seconds=elapsed,
        timeout_seconds=timeout_seconds,
    )
    observation.update(
        {
            "run_index": run_index,
            "scene": str(scene),
            "scene_sha256": _sha(scene),
            "scene_dependency_sha256": _scene_dependency_sha256(scene),
            "stdout_sha256": _sha(output_root / "stdout.log"),
            "stderr_sha256": _sha(output_root / "stderr.log"),
        }
    )
    (output_root / "observation.json").write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return observation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    args = parser.parse_args()
    candidate_root = args.candidate_root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    candidates: dict[str, Path] = {
        f"p{count}": candidate_root / f"p{count}/qualification_30hz.usda"
        for count in (12, 24, 48)
    }
    candidates["negative_control_no_partitions"] = (
        candidate_root / "p12/diagnostic_no_partitions.usda"
    )
    missing = [str(path) for path in candidates.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing probe scenes: " + ", ".join(missing))
    results: dict[str, list[dict[str, Any]]] = {}
    for name, scene in candidates.items():
        repeat_count = 1 if name.startswith("negative_control") else args.runs
        results[name] = [
            _run_one(
                scene=scene,
                root=out / name,
                run_index=index,
                timeout_seconds=args.timeout_seconds,
            )
            for index in range(1, repeat_count + 1)
        ]
    candidate_failures = {
        name: all(run["status"] == "blocked_update_timeout" for run in runs)
        for name, runs in results.items()
        if not name.startswith("negative_control")
    }
    control_passed = all(
        run["status"] == "five_updates_completed"
        for run in results["negative_control_no_partitions"]
    )
    measured_no_go = control_passed and all(candidate_failures.values())
    report = {
        "schema_version": "aan.task02_r81_stage_update_sweep.v2",
        "overall_status": "measured_no_go" if measured_no_go else "incomplete",
        "candidate_contract": {
            "partition_counts": [12, 24, 48],
            "required_cold_runs_for_promotion": args.runs,
            "timeout_seconds": args.timeout_seconds,
            "runtime": "Isaac Sim 4.1 EOS GenManip managed environment",
        },
        "negative_control_passed": control_passed,
        "candidate_failures": candidate_failures,
        "runs": results,
        "promotion": {
            "allowed": False,
            "reason": (
                "all_partition_candidates_block_before_physics_qualification"
                if measured_no_go
                else "stage_update_sweep_incomplete"
            ),
        },
        "claim_boundary": (
            "Five-update admission only. No static retention, transfer, FPS, robot, "
            "policy, or benchmark success is claimed."
        ),
    }
    (out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = {
        **{key: value for key, value in report.items() if key != "runs"},
        "runs": {
            name: [_summary_run(run) for run in runs] for name, runs in results.items()
        },
        "evidence_root": str(out),
        "full_report_sha256": _sha(out / "report.json"),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(out / "report.json")
    return 2 if measured_no_go else 1


if __name__ == "__main__":
    raise SystemExit(main())
