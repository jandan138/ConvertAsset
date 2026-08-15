#!/usr/bin/env python3
"""Run three cold Isaac 4.1 static-retention qualifications."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import time
from typing import Any

from scripts.run_task02_r81_stage_update_sweep import (
    FORMAL_ISAAC41_PREFIX,
    _environment,
)
from scripts.qualify_gpu_pbd_static_container import hard_runtime_errors


QUALIFIER = Path(__file__).with_name("qualify_gpu_pbd_static_container.py")


def merge_process_runtime_errors(
    observation: dict[str, Any], process_log: str
) -> dict[str, Any]:
    errors = list(
        dict.fromkeys(
            [
                *observation.get("hard_runtime_errors", []),
                *hard_runtime_errors(process_log),
            ]
        )
    )
    observation["hard_runtime_errors"] = errors
    observation["runtime_log_capture"] = "parent_process_stdout_stderr"
    if errors:
        observation.setdefault("checks", {})["gpu_cooking"] = False
        observation["overall_status"] = "blocked"
    return observation


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build_report(
    runs: list[dict[str, Any]], *, required_runs: int
) -> dict[str, Any]:
    candidate = len(runs) == required_runs and all(
        run.get("overall_status") == "pass" for run in runs
    )
    allowed = candidate and all(
        run.get("qualification_tier") == "final" for run in runs
    )
    return {
        "schema_version": "aan.gpu_pbd_static_admission.v2",
        "overall_status": "pass" if allowed else "candidate" if candidate else "blocked",
        "qualification_tier": "final" if allowed else "candidate" if candidate else "blocked",
        "required_cold_runs": required_runs,
        "runs": runs,
        "promotion": {
            "allowed": allowed,
            "claim": "gpu_pbd_static_container" if allowed else None,
            "reason": None if allowed else (
                "candidate_retention_only" if candidate else "one_or_more_static_runs_failed"
            ),
        },
        "claim_boundary": (
            "Static GPU-PBD containment only; no pour, grasp, policy, or "
            "benchmark success."
        ),
    }


def _run_one(
    *, scene: Path, root: Path, run_index: int, timeout_seconds: float
) -> dict[str, Any]:
    run_root = root / f"run_{run_index:02d}"
    run_root.mkdir(parents=True, exist_ok=False)
    observation_path = run_root / "observation.json"
    command = [
        "/usr/bin/timeout",
        "--signal=TERM",
        "--kill-after=15s",
        f"{timeout_seconds}s",
        str(FORMAL_ISAAC41_PREFIX / "bin/python"),
        "-I",
        "-B",
        str(QUALIFIER),
        "--scene",
        str(scene),
        "--run-index",
        str(run_index),
        "--out",
        str(observation_path),
    ]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=QUALIFIER.parents[1],
        env=_environment(run_root / "runtime"),
        check=False,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - started
    stdout = run_root / "stdout.log"
    stderr = run_root / "stderr.log"
    stdout.write_text(completed.stdout, encoding="utf-8")
    stderr.write_text(completed.stderr, encoding="utf-8")
    if observation_path.is_file():
        observation = json.loads(observation_path.read_text(encoding="utf-8"))
    else:
        observation = {
            "schema_version": "aan.gpu_pbd_static_observation.v1",
            "run_index": run_index,
            "overall_status": "blocked",
            "blocked_reason": (
                "timeout" if completed.returncode == 124 else "runtime_failed"
            ),
        }
    observation = merge_process_runtime_errors(
        observation, completed.stdout + "\n" + completed.stderr
    )
    observation["process"] = {
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
        "timeout_seconds": timeout_seconds,
        "stdout_sha256": _sha(stdout),
        "stderr_sha256": _sha(stderr),
    }
    observation_path.write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return observation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()
    scene = args.scene.resolve()
    out = args.out.resolve()
    if not scene.is_file():
        raise FileNotFoundError(scene)
    out.mkdir(parents=True, exist_ok=False)
    runs = [
        _run_one(
            scene=scene,
            root=out,
            run_index=index,
            timeout_seconds=args.timeout_seconds,
        )
        for index in range(1, args.runs + 1)
    ]
    report = build_report(runs, required_runs=args.runs)
    report["scene"] = str(scene)
    report["scene_sha256"] = _sha(scene)
    report_path = out / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(report_path)
    return 0 if report["promotion"]["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
