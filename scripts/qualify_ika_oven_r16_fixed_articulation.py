#!/usr/bin/env python3
"""Qualify OVEN 125 r16 articulation, controls, namespaces, and compatibility."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.qualify_ika_oven_r15_instance_layout import (  # noqa: E402
    _fixture,
)
from scripts.qualify_task09_r14_dual_knob_oven import (  # noqa: E402
    INTERACTIVE_MEMBER,
    _extract,
    evaluate_interactive_report,
)


DEFAULT_OUTPUT = (
    REPO_ROOT / "outputs/ika_oven_125_task09_r16_fixed_articulation_20260904"
)
DEFAULT_ISAAC41 = Path(
    "/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/"
    "embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python"
)
DEFAULT_ISAAC45 = Path("/isaac-sim/python.sh")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _run(
    command: list[str], report: Path, *, environment: dict[str, str]
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        check=False,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    report.with_suffix(".stdout.log").write_bytes(completed.stdout)
    report.with_suffix(".stderr.log").write_bytes(completed.stderr)
    if not report.is_file():
        raise RuntimeError(f"qualification emitted no report: {report}")
    payload = json.loads(report.read_text(encoding="utf-8"))
    payload["process_returncode"] = completed.returncode
    return payload


def package_handoff(output: Path = DEFAULT_OUTPUT) -> Path:
    """Create the standalone consumer ZIP after a passing qualification."""

    output = output.resolve()
    receipt = output / "promotion_receipt.json"
    report = output / "qualification/full_report.json"
    if json.loads(receipt.read_text()).get("status") != "promoted":
        raise ValueError("r16 package is not promoted")
    if json.loads(report.read_text()).get("status") != "pass":
        raise ValueError("r16 qualification did not pass")
    handoff_parent = output / "handoff"
    handoff_root = handoff_parent / "ika_oven_125_task09_r16_fixed_articulation"
    if handoff_root.exists():
        raise FileExistsError(f"refusing to replace handoff: {handoff_root}")
    shutil.copytree(output / "package", handoff_root / "package")
    shutil.copy2(receipt, handoff_root / "promotion_receipt.json")
    shutil.copy2(report, handoff_root / "qualification_full_report.json")
    (handoff_root / "README_CN.md").write_text(
        "# OVEN 125 r16 fixed-base articulation\n\n"
        "入口 USD：`package/asset.usd`，入口 prim：`/World/obj_oven`。\n"
        "这是 identity-Xform `/Instance` 的固定基座 articulation；Isaac Sim 4.1 "
        "为正式运行时，4.5 只完成兼容检查。不要在消费者侧增加 kinematic、"
        "关节或物理补丁。\n",
        encoding="utf-8",
    )
    archive = handoff_parent / (handoff_root.name + ".zip")
    shutil.make_archive(
        str(archive.with_suffix("")),
        "zip",
        root_dir=handoff_parent,
        base_dir=handoff_root.name,
    )
    archive.with_suffix(".zip.sha256").write_text(
        _sha(archive) + "  " + archive.name + "\n", encoding="utf-8"
    )
    return archive


def finalize_existing_qualification(output: Path = DEFAULT_OUTPUT) -> Path:
    """Aggregate already-recorded runtime reports without rerunning Isaac."""

    output = output.resolve()
    qualification = output / "qualification"
    asset = output / "package/asset.usd"
    manifest_path = output / "package/evidence/task09_r16_manifest.json"
    articulation_reports = {
        label: json.loads(
            (qualification / f"isaac41_{label}_articulation.json").read_text()
        )
        for label in ("canonical", "prefixed", "vr")
    }
    interactive_evaluations = {
        name: evaluate_interactive_report(
            json.loads((qualification / f"{name}.json").read_text())
        )
        for name in (
            "canonical_primary",
            "canonical_aux",
            "prefixed_aux_scale085",
            "vr_aux_scale115",
        )
    }
    door_report = json.loads((qualification / "vr_door_60deg.json").read_text())
    door_evaluation = {
        "status": door_report.get("status", "blocked"),
        "checks": door_report.get("checks", {}),
    }
    compatibility = json.loads(
        (qualification / "isaac45_vr_articulation.json").read_text()
    )
    formal_pass = (
        all(item.get("status") == "pass" for item in articulation_reports.values())
        and all(item["status"] == "pass" for item in interactive_evaluations.values())
        and door_evaluation["status"] == "pass"
    )
    compatibility_pass = compatibility.get("status") == "pass"
    passed = formal_pass and compatibility_pass
    aggregate = {
        "schema_version": "aan.ika_oven_125_task09_r16_qualification.v1",
        "status": "pass" if passed else "blocked",
        "formal_runtime": "isaac41",
        "compatibility_runtime": "isaac45",
        "asset_sha256": _sha(asset),
        "mount_roots": {
            "canonical": "/World/obj_oven",
            "prefixed": "/World/task_fixture/obj_oven",
            "vr": "/World/_scene/obj_oven",
        },
        "articulation_reports": articulation_reports,
        "interactive_evaluations": interactive_evaluations,
        "door_evaluation": door_evaluation,
        "isaac45_compatibility": compatibility,
        "claim_boundary": (
            "Fixed-base articulation initialization, rest stability, selected oven "
            "task controls, the 60-degree door limit, and namespace/scale composition "
            "are qualified in Isaac Sim 4.1. Isaac Sim 4.5 only receives an "
            "articulation initialization and rest-stability compatibility check. No "
            "robot-policy or benchmark success is claimed."
        ),
    }
    aggregate_path = qualification / "full_report.json"
    _write_json(aggregate_path, aggregate)
    manifest = json.loads(manifest_path.read_text())
    manifest["overall_status"] = aggregate["status"]
    manifest["blocked_reasons"] = [] if passed else ["runtime qualification blocked"]
    manifest["claims"]["task_controls_qualified"] = formal_pass
    manifest["claims"]["runtime_namespace_qualified"] = formal_pass
    manifest["claims"]["isaac45_compatibility_checked"] = compatibility_pass
    manifest["qualification"] = {
        "report": "../../qualification/full_report.json",
        "sha256": _sha(aggregate_path),
    }
    _write_json(manifest_path, manifest)
    if not passed:
        return aggregate_path
    _write_json(
        output / "promotion_receipt.json",
        {
            "schema_version": "aan.fixed_base_articulation_promotion_receipt.v1",
            "status": "promoted",
            "asset_id": "ika_oven_125_task09_r16_fixed_articulation",
            "formal_runtime": "isaac41",
            "compatibility_runtime": "isaac45",
            "asset_sha256": _sha(asset),
            "qualification_sha256": _sha(aggregate_path),
            "claims": manifest["claims"],
        },
    )
    package_handoff(output)
    return aggregate_path


def qualify(
    output: Path = DEFAULT_OUTPUT,
    *,
    isaac41: Path = DEFAULT_ISAAC41,
    isaac45: Path = DEFAULT_ISAAC45,
) -> Path:
    output = output.resolve()
    asset = output / "package/asset.usd"
    manifest_path = output / "package/evidence/task09_r16_manifest.json"
    if not asset.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("r16 fixed-base candidate is incomplete")
    qualification = output / "qualification"
    qualification.mkdir(parents=True, exist_ok=True)
    interactive = qualification / "producer_interactive_smoke.py"
    _extract(INTERACTIVE_MEMBER, interactive)
    auxiliary = qualification / "producer_interactive_smoke_aux.py"
    source = interactive.read_text(encoding="utf-8")
    marker = 'KNOB_ROOT = CP + "/ControlKnob"'
    if source.count(marker) != 1:
        raise ValueError("producer interactive smoke knob marker changed")
    auxiliary.write_text(
        source.replace(marker, 'KNOB_ROOT = CP + "/AuxControlKnob"', 1),
        encoding="utf-8",
    )
    articulation_probe = REPO_ROOT / "scripts/probe_ika_oven_fixed_base_articulation.py"
    door_probe = REPO_ROOT / "scripts/probe_ika_oven_r16_door.py"

    mounts = {
        "canonical": "/World/obj_oven",
        "prefixed": "/World/task_fixture/obj_oven",
        "vr": "/World/_scene/obj_oven",
    }
    fixtures: dict[str, Path] = {}
    for label, mount in mounts.items():
        scale = {"canonical": 1.0, "prefixed": 0.85, "vr": 1.15}[label]
        path = qualification / f"fixtures/{label}.usd"
        _fixture(asset, path, mount, scale)
        fixtures[label] = path

    environment = dict(os.environ)
    environment.update({"ACCEPT_EULA": "Y", "OMNI_KIT_ACCEPT_EULA": "YES"})
    articulation_reports = {}
    for label in mounts:
        report = qualification / f"isaac41_{label}_articulation.json"
        articulation_reports[label] = _run(
            [
                str(isaac41),
                str(articulation_probe),
                "--usd",
                str(fixtures[label]),
                "--root",
                mounts[label],
                "--output",
                str(report),
            ],
            report,
            environment=environment,
        )

    interactive_runs = (
        ("canonical_primary", interactive, "canonical"),
        ("canonical_aux", auxiliary, "canonical"),
        ("prefixed_aux_scale085", auxiliary, "prefixed"),
        ("vr_aux_scale115", auxiliary, "vr"),
    )
    interactive_evaluations = {}
    for name, script, label in interactive_runs:
        report_path = qualification / f"{name}.json"
        report = _run(
            [
                str(isaac41),
                str(script),
                "--usd",
                str(fixtures[label]),
                "--output",
                str(report_path),
                "--root",
                mounts[label] + "/Instance",
                "--/app/omni.graph.scriptnode/opt_in=true",
            ],
            report_path,
            environment=environment,
        )
        interactive_evaluations[name] = evaluate_interactive_report(report)

    door_path = qualification / "vr_door_60deg.json"
    door_report = _run(
        [
            str(isaac41),
            str(door_probe),
            "--usd",
            str(fixtures["vr"]),
            "--output",
            str(door_path),
            "--root",
            mounts["vr"],
        ],
        door_path,
        environment=environment,
    )
    door_evaluation = {
        "status": door_report.get("status", "blocked"),
        "checks": door_report.get("checks", {}),
    }

    compatibility_path = qualification / "isaac45_vr_articulation.json"
    compatibility = _run(
        [
            str(isaac45),
            str(articulation_probe),
            "--usd",
            str(fixtures["vr"]),
            "--root",
            mounts["vr"],
            "--output",
            str(compatibility_path),
        ],
        compatibility_path,
        environment=environment,
    )

    formal_pass = (
        all(item.get("status") == "pass" for item in articulation_reports.values())
        and all(item["status"] == "pass" for item in interactive_evaluations.values())
        and door_evaluation["status"] == "pass"
    )
    compatibility_pass = compatibility.get("status") == "pass"
    passed = formal_pass and compatibility_pass
    aggregate = {
        "schema_version": "aan.ika_oven_125_task09_r16_qualification.v1",
        "status": "pass" if passed else "blocked",
        "formal_runtime": "isaac41",
        "compatibility_runtime": "isaac45",
        "asset_sha256": _sha(asset),
        "mount_roots": mounts,
        "articulation_reports": articulation_reports,
        "interactive_evaluations": interactive_evaluations,
        "door_evaluation": door_evaluation,
        "isaac45_compatibility": compatibility,
        "claim_boundary": (
            "Fixed-base articulation initialization, rest stability, existing oven "
            "controls, the 60-degree door limit, and namespace/scale composition are "
            "qualified in Isaac Sim 4.1. Isaac Sim 4.5 only receives an articulation "
            "initialization and rest-stability compatibility check. No robot-policy "
            "or benchmark success is claimed."
        ),
    }
    aggregate_path = qualification / "full_report.json"
    _write_json(aggregate_path, aggregate)

    manifest = json.loads(manifest_path.read_text())
    manifest["overall_status"] = aggregate["status"]
    manifest["blocked_reasons"] = [] if passed else ["runtime qualification blocked"]
    manifest["claims"].pop("r15_mechanics_preserved", None)
    manifest["claims"]["task_controls_qualified"] = formal_pass
    manifest["claims"]["runtime_namespace_qualified"] = formal_pass
    manifest["claims"]["isaac45_compatibility_checked"] = compatibility_pass
    manifest["qualification"] = {
        "report": "../../qualification/full_report.json",
        "sha256": _sha(aggregate_path),
    }
    _write_json(manifest_path, manifest)
    if passed:
        _write_json(
            output / "promotion_receipt.json",
            {
                "schema_version": "aan.fixed_base_articulation_promotion_receipt.v1",
                "status": "promoted",
                "asset_id": "ika_oven_125_task09_r16_fixed_articulation",
                "formal_runtime": "isaac41",
                "compatibility_runtime": "isaac45",
                "asset_sha256": _sha(asset),
                "qualification_sha256": _sha(aggregate_path),
                "claims": manifest["claims"],
            },
        )
        package_handoff(output)
    return aggregate_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--isaac41-python", type=Path, default=DEFAULT_ISAAC41)
    parser.add_argument("--isaac45-python", type=Path, default=DEFAULT_ISAAC45)
    parser.add_argument("--package-only", action="store_true")
    parser.add_argument("--finalize-existing", action="store_true")
    args = parser.parse_args(argv)
    if args.package_only:
        print(package_handoff(args.output))
    elif args.finalize_existing:
        print(finalize_existing_qualification(args.output))
    else:
        print(
            qualify(
                args.output,
                isaac41=args.isaac41_python,
                isaac45=args.isaac45_python,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
