#!/usr/bin/env python3
"""Promote the materialized Task 09 oven with producer interactive evidence."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_task09_r13_materialized_20260831"
DEFAULT_ISAAC = Path(
    "/cpfs/user/zhuzihou/conda-managed/envs/"
    "embodied-eval-os-isaacsim41-py310/bin/python"
)
SOURCE_ARCHIVE = Path(
    "/cpfs/user/zhuzihou/dev/scenario-forge/external_artifacts/incoming/"
    "from_xinyu/ika_oven_125_interactive_v3.7z"
)
INTERACTIVE_MEMBER = (
    "ika_oven_125_interactive_v3/scripts/interactive_smoke_oven125_v3.py"
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def evaluate_producer_report(report: dict[str, Any]) -> dict[str, Any]:
    results = report.get("results", {})
    checks = {
        "producer_overall": report.get("status") == "PASS"
        and report.get("passed") is True,
        "embedded_runtime_graph": bool(
            results.get("embeddedRuntimeGraph", {}).get("passed")
        ),
        "physical_rotor_changes_setpoint": bool(
            results.get("rotorSetpointAndDisplay", {}).get("passed")
            and results.get("rotorSetpointAndDisplay", {}).get(
                "setpointChangedByPhysicalRotation"
            )
        ),
        "physical_knob_press_starts_heating": bool(
            results.get("knobPressStartsHeating", {}).get("passed")
            and results.get("knobPressStartsHeating", {}).get("heatingStarted")
        ),
    }
    return {"status": "pass" if all(checks.values()) else "blocked", "checks": checks}


def _extract_script(destination: Path) -> None:
    completed = subprocess.run(
        ["7z", "x", "-so", str(SOURCE_ARCHIVE), INTERACTIVE_MEMBER],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(completed.stdout)


def qualify(
    output: Path = DEFAULT_OUTPUT,
    *,
    isaac: Path = DEFAULT_ISAAC,
    reuse_existing: bool = True,
) -> Path:
    output = output.resolve()
    asset = output / "package/asset.usd"
    manifest_path = output / "package/evidence/task09_materialized_manifest.json"
    if not asset.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("materialized oven candidate is incomplete")
    script = output / "qualification/producer_interactive_smoke.py"
    _extract_script(script)
    environment = dict(os.environ)
    environment.update({"ACCEPT_EULA": "Y", "OMNI_KIT_ACCEPT_EULA": "YES"})
    reports = []
    evaluations = []
    for index in range(3):
        report_path = output / f"qualification/interactive_smoke_run{index:02d}.json"
        if not (reuse_existing and report_path.is_file()):
            completed = subprocess.run(
                [
                    str(isaac),
                    str(script),
                    "--usd",
                    str(asset),
                    "--output",
                    str(report_path),
                    "--root",
                    "/World/obj_oven",
                    "--/app/omni.graph.scriptnode/opt_in=true",
                ],
                check=False,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (output / f"qualification/run{index:02d}.stdout.log").write_bytes(
                completed.stdout
            )
            (output / f"qualification/run{index:02d}.stderr.log").write_bytes(
                completed.stderr
            )
        if not report_path.is_file():
            raise RuntimeError(f"producer interactive run {index} emitted no report")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        reports.append(report)
        evaluations.append(evaluate_producer_report(report))
    passed = all(item["status"] == "pass" for item in evaluations)
    aggregate = {
        "schema_version": "aan.ika_oven_125_task09_materialized_qualification.v1",
        "status": "pass" if passed else "blocked",
        "runtime": "isaac41",
        "asset_sha256": _sha(asset),
        "producer_script_sha256": _sha(script),
        "run_evaluations": evaluations,
        "run_report_sha256": [
            _sha(output / f"qualification/interactive_smoke_run{index:02d}.json")
            for index in range(3)
        ],
        "claim_boundary": (
            "The materialized /World/obj_oven stage-base package runs its embedded "
            "controller, changes temperature through physical rotor motion, and starts "
            "heating through physical knob press. It must not be consumed by reference."
        ),
    }
    aggregate_path = output / "qualification/full_report.json"
    _write_json(aggregate_path, aggregate)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["overall_status"] = "pass" if passed else "blocked"
    manifest["claims"]["task09_control_sequence"] = passed
    manifest["qualification"] = {
        "status": aggregate["status"],
        "report": "../../qualification/full_report.json",
        "report_sha256": _sha(aggregate_path),
    }
    _write_json(manifest_path, manifest)
    if passed:
        _write_json(
            output / "promotion_receipt.json",
            {
                "schema_version": "aan.articulated_task_scope_promotion_receipt.v1",
                "status": "promoted",
                "asset_id": "ika_oven_125_task09_r13_materialized",
                "task_scope": "scientific_workbench_task09_oven_load_start",
                "runtime": "isaac41",
                "consumer_mode": "materialized_stage_base",
                "asset_sha256": _sha(asset),
                "qualification_sha256": _sha(aggregate_path),
                "claims": manifest["claims"],
            },
        )
    return aggregate_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--isaac-python", type=Path, default=DEFAULT_ISAAC)
    parser.add_argument("--no-reuse-existing", action="store_true")
    args = parser.parse_args(argv)
    print(
        qualify(
            args.output,
            isaac=args.isaac_python,
            reuse_existing=not args.no_reuse_existing,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
