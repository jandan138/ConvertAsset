#!/usr/bin/env python3
"""Run a bounded transfer search, freeze the winner, and require three cold passes."""

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
from scripts.qualify_gpu_pbd_transfer import hard_runtime_errors


QUALIFIER = Path(__file__).with_name("qualify_gpu_pbd_transfer.py")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def select_candidate(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    passing = [run for run in runs if run.get("overall_status") == "pass"]
    if not passing:
        return None
    return max(
        passing,
        key=lambda run: (
            int(run["pour"]["target"]),
            -int(run["pour"]["spill"]),
            run["candidate_id"],
        ),
    )


def build_report(
    *,
    search_runs: list[dict[str, Any]],
    cold_runs: list[dict[str, Any]],
    selected: dict[str, Any] | None,
) -> dict[str, Any]:
    if selected is None:
        return {
            "schema_version": "aan.gpu_pbd_transfer_admission.v1",
            "overall_status": "blocked",
            "blocked_reason": "bounded_search_found_no_50pct_transfer_candidate",
            "search_runs": search_runs,
            "cold_runs": [],
            "promotion": {"allowed": False, "claim": None},
            "claim_boundary": "No transfer claim; bounded prescribed-trajectory search failed the 50 percent target gate.",
        }
    allowed = len(cold_runs) == 3 and all(
        run.get("overall_status") == "pass" for run in cold_runs
    )
    return {
        "schema_version": "aan.gpu_pbd_transfer_admission.v1",
        "overall_status": "pass" if allowed else "blocked",
        "blocked_reason": None
        if allowed
        else "selected_trajectory_failed_three_cold_runs",
        "search_runs": search_runs,
        "selected_candidate": selected["trajectory"],
        "cold_runs": cold_runs,
        "promotion": {
            "allowed": allowed,
            "claim": "gpu_pbd_prescribed_transfer_pair" if allowed else None,
        },
        "claim_boundary": "Prescribed kinematic transfer feasibility at 50 percent target reception; spill recorded but non-blocking; no robot, policy, benchmark, or 90 percent claim.",
    }


def _run_one(
    *,
    scene: Path,
    profile: Path,
    candidate: dict[str, Any],
    root: Path,
    run_index: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    observation_path = root / "observation.json"
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
        "--fixture-profile",
        str(profile),
        "--candidate-json",
        json.dumps(candidate, sort_keys=True),
        "--run-index",
        str(run_index),
        "--out",
        str(observation_path),
    ]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=QUALIFIER.parents[1],
        env=_environment(root / "runtime"),
        check=False,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - started
    stdout = root / "stdout.log"
    stderr = root / "stderr.log"
    stdout.write_text(completed.stdout, encoding="utf-8")
    stderr.write_text(completed.stderr, encoding="utf-8")
    if observation_path.is_file():
        observation = json.loads(observation_path.read_text(encoding="utf-8"))
    else:
        observation = {
            "schema_version": "aan.gpu_pbd_transfer_observation.v1",
            "candidate_id": candidate["candidate_id"],
            "overall_status": "blocked",
            "blocked_reason": "timeout"
            if completed.returncode == 124
            else "runtime_failed",
            "pour": {"target": 0, "spill": 548},
        }
    errors = list(
        dict.fromkeys(
            [
                *observation.get("hard_runtime_errors", []),
                *hard_runtime_errors(completed.stdout + "\n" + completed.stderr),
            ]
        )
    )
    observation["hard_runtime_errors"] = errors
    if errors:
        observation["overall_status"] = "blocked"
        observation.setdefault("checks", {})["gpu_cooking"] = False
    observation["process"] = {
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
        "timeout_seconds": timeout_seconds,
        "stdout_sha256": _sha(stdout),
        "stderr_sha256": _sha(stderr),
    }
    observation_path.write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return observation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    scene = fixture / "qualification.usda"
    profile_path = fixture / "transfer_fixture_profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    search_runs = []
    for index, candidate in enumerate(profile["bounded_search"]["candidates"], start=1):
        search_runs.append(
            _run_one(
                scene=scene,
                profile=profile_path,
                candidate=candidate,
                root=out / "search" / candidate["candidate_id"],
                run_index=index,
                timeout_seconds=args.timeout_seconds,
            )
        )
    selected = select_candidate(search_runs)
    cold_runs = []
    if selected is not None:
        candidate = selected["trajectory"]
        for index in range(1, 4):
            cold_runs.append(
                _run_one(
                    scene=scene,
                    profile=profile_path,
                    candidate=candidate,
                    root=out / "cold" / f"run_{index:02d}",
                    run_index=index,
                    timeout_seconds=args.timeout_seconds,
                )
            )
    report = build_report(
        search_runs=search_runs, cold_runs=cold_runs, selected=selected
    )
    report["fixture"] = str(fixture)
    report["fixture_profile_sha256"] = _sha(profile_path)
    report["scene_sha256"] = _sha(scene)
    report_path = out / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(report_path)
    return 0 if report["promotion"]["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
