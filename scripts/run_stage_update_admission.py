#!/usr/bin/env python3
"""Run reusable cold five-update admission for one Isaac Sim 4.1 scene."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from scripts.run_task02_r81_stage_update_sweep import _run_one, _summary_run


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build_report(runs: list[dict[str, Any]], *, required_runs: int) -> dict[str, Any]:
    allowed = len(runs) == required_runs and all(
        run.get("status") == "five_updates_completed" for run in runs
    )
    return {
        "schema_version": "aan.stage_update_admission.v1",
        "overall_status": "pass" if allowed else "blocked",
        "required_cold_runs": required_runs,
        "runs": [_summary_run(run) if "run_index" in run else run for run in runs],
        "promotion": {
            "allowed": allowed,
            "reason": None
            if allowed
            else "one_or_more_cold_runs_failed_five_update_gate",
        },
        "claim_boundary": (
            "Five-update admission only; retention, transfer, FPS, robot, policy, "
            "and benchmark success require later gates."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
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
    path = out / "report.json"
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(path)
    return 0 if report["promotion"]["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
