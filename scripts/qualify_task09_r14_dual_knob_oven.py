#!/usr/bin/env python3
"""Qualify dual knobs, scale endpoints, and the 60-degree OVEN 125 door."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_task09_r14_dual_knob_20260831"
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
PHYSICS_MEMBER = "ika_oven_125_interactive_v3/scripts/physics_smoke_oven125_v2.py"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def evaluate_interactive_report(report: dict[str, Any]) -> dict[str, Any]:
    results = report.get("results", {})
    checks = {
        "source_unchanged": report.get("sourceUsdUnchanged") is True,
        "runtime_graph": bool(results.get("embeddedRuntimeGraph", {}).get("passed")),
        "physical_rotation": bool(
            results.get("rotorSetpointAndDisplay", {}).get("passed")
            and results.get("rotorSetpointAndDisplay", {}).get(
                "setpointChangedByPhysicalRotation"
            )
        ),
        "physical_press": bool(
            results.get("knobPressStartsHeating", {}).get("passed")
            and results.get("knobPressStartsHeating", {}).get("heatingStarted")
        ),
    }
    return {"status": "pass" if all(checks.values()) else "blocked", "checks": checks}


def evaluate_door_report(report: dict[str, Any]) -> dict[str, Any]:
    door = report.get("results", {}).get("doorDynamicLimit", {})
    opening = float(door.get("openingPeakDegrees", -1.0))
    dwell = float(door.get("upperDwellPeakDegrees", -1.0))
    checks = {
        "force_calls": int(door.get("successfulForceCalls", 0)) >= 1000,
        "opens_to_60_band": 58.0 <= opening <= 62.0,
        "holds_60_limit": 58.0 <= dwell <= 62.0,
        "closes": float(door.get("closingFinalDegrees", 180.0)) <= 3.0,
        "base_stable": float(door.get("bodyTranslationDriftMeters", 1.0)) <= 1.0e-6,
    }
    return {"status": "pass" if all(checks.values()) else "blocked", "checks": checks}


def _extract(member: str, destination: Path) -> None:
    completed = subprocess.run(
        ["7z", "x", "-so", str(SOURCE_ARCHIVE), member],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(completed.stdout)


def _fixture(source: Path, destination: Path, scale: float) -> None:
    from pxr import Gf, Usd

    shutil.copy2(source, destination)
    stage = Usd.Stage.Open(str(destination))
    stage.GetPrimAtPath("/World/obj_oven").GetAttribute("xformOp:scale").Set(
        Gf.Vec3d(scale)
    )
    stage.GetRootLayer().Save()


def qualify(
    output: Path = DEFAULT_OUTPUT,
    *,
    isaac: Path = DEFAULT_ISAAC,
) -> Path:
    output = output.resolve()
    asset = output / "package/asset.usd"
    manifest_path = output / "package/evidence/task09_r14_manifest.json"
    if not asset.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("r14 dual-knob candidate is incomplete")
    qualification = output / "qualification"
    interactive = qualification / "producer_interactive_smoke.py"
    physics = qualification / "producer_physics_smoke.py"
    _extract(INTERACTIVE_MEMBER, interactive)
    _extract(PHYSICS_MEMBER, physics)
    auxiliary = qualification / "producer_interactive_smoke_aux.py"
    auxiliary_source = interactive.read_text(encoding="utf-8")
    old = 'KNOB_ROOT = CP + "/ControlKnob"'
    if auxiliary_source.count(old) != 1:
        raise ValueError("producer interactive smoke knob root marker changed")
    auxiliary.write_text(
        auxiliary_source.replace(
            old, 'KNOB_ROOT = CP + "/AuxControlKnob"', 1
        ),
        encoding="utf-8",
    )
    fixtures = {}
    for label, scale in (("scale085", 0.85), ("scale100", 1.0), ("scale115", 1.15)):
        path = qualification / "fixtures" / f"{label}.usd"
        path.parent.mkdir(parents=True, exist_ok=True)
        _fixture(asset, path, scale)
        fixtures[label] = path
    environment = dict(os.environ)
    environment.update({"ACCEPT_EULA": "Y", "OMNI_KIT_ACCEPT_EULA": "YES"})
    interactive_runs = (
        ("primary_scale100", interactive, fixtures["scale100"]),
        ("aux_scale085", auxiliary, fixtures["scale085"]),
        ("aux_scale100", auxiliary, fixtures["scale100"]),
        ("aux_scale115", auxiliary, fixtures["scale115"]),
    )
    reports = {}
    evaluations = {}
    for name, script, fixture in interactive_runs:
        report_path = qualification / f"{name}.json"
        if not report_path.is_file():
            completed = subprocess.run(
                [
                    str(isaac),
                    str(script),
                    "--usd",
                    str(fixture),
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
            (qualification / f"{name}.stdout.log").write_bytes(completed.stdout)
            (qualification / f"{name}.stderr.log").write_bytes(completed.stderr)
        if not report_path.is_file():
            raise RuntimeError(f"interactive run emitted no report: {name}")
        reports[name] = json.loads(report_path.read_text(encoding="utf-8"))
        evaluations[name] = evaluate_interactive_report(reports[name])
    door_path = qualification / "door_60deg.json"
    if not door_path.is_file():
        completed = subprocess.run(
            [
                str(isaac),
                str(physics),
                "--usd",
                str(fixtures["scale100"]),
                "--output",
                str(door_path),
                "--root",
                "/World/obj_oven",
                "--/app/omni.graph.scriptnode/opt_in=true",
            ],
            check=False,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        (qualification / "door_60deg.stdout.log").write_bytes(completed.stdout)
        (qualification / "door_60deg.stderr.log").write_bytes(completed.stderr)
    door_report = json.loads(door_path.read_text(encoding="utf-8"))
    door_evaluation = evaluate_door_report(door_report)
    passed = all(value["status"] == "pass" for value in evaluations.values()) and (
        door_evaluation["status"] == "pass"
    )
    aggregate = {
        "schema_version": "aan.ika_oven_125_task09_r14_qualification.v1",
        "status": "pass" if passed else "blocked",
        "runtime": "isaac41",
        "asset_sha256": _sha(asset),
        "interactive_evaluations": evaluations,
        "interactive_report_sha256": {
            name: _sha(qualification / f"{name}.json") for name in evaluations
        },
        "door_evaluation": door_evaluation,
        "door_report_sha256": _sha(door_path),
        "claim_boundary": (
            "Both physical knobs share logical controller state without mechanical "
            "angle coupling. Uniform scale is qualified at 0.85, 1.0, and 1.15. "
            "The door drive damping is 9 and its upper limit is 60 degrees."
        ),
    }
    aggregate_path = qualification / "full_report.json"
    _write_json(aggregate_path, aggregate)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["overall_status"] = "pass" if passed else "blocked"
    manifest["claims"]["dual_physical_knobs"] = passed
    manifest["claims"]["door_60deg_limit"] = passed
    manifest["claims"]["uniform_scale_0p85_1p15"] = passed
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
                "asset_id": "ika_oven_125_task09_r14_dual_knob",
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
    args = parser.parse_args(argv)
    print(qualify(args.output, isaac=args.isaac_python))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
