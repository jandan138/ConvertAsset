#!/usr/bin/env python3
"""Qualify OVEN 125 r17 knob hardening in Isaac 4.5 and regress 4.1."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_ika_oven_r17_teleop_hardened import (  # noqa: E402
    DEFAULT_OUTPUT,
)
from scripts.qualify_ika_oven_r15_instance_layout import _fixture  # noqa: E402
from scripts.qualify_task09_r14_dual_knob_oven import (  # noqa: E402
    evaluate_interactive_report,
)


DEFAULT_ISAAC41 = Path(
    "/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/"
    "embodied-eval-os-sim-isaacsim41-genmanip-py310/bin/python"
)
DEFAULT_ISAAC45 = Path("/isaac-sim/python.sh")
R16_OUTPUT = Path(
    "/cpfs/user/zhuzihou/dev/ConvertAsset/outputs/"
    "ika_oven_125_task09_r16_fixed_articulation_20260904"
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _run(
    command: list[str], report: Path, *, environment: Mapping[str, str]
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        check=False,
        env=dict(environment),
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


def qualification_checks(
    *,
    isaac45_runs: Mapping[str, Mapping[str, Any]],
    negative_control: Mapping[str, Any],
    isaac41_interactive: Mapping[str, Mapping[str, Any]],
    isaac41_articulation: Mapping[str, Any],
    isaac41_door: Mapping[str, Any],
) -> dict[str, bool]:
    expected = {
        f"{knob}_cold_{index}"
        for knob in ("primary", "auxiliary")
        for index in range(1, 4)
    }
    return {
        "isaac45_three_cold_runs_per_knob": set(isaac45_runs) == expected
        and all(report.get("status") == "pass" for report in isaac45_runs.values()),
        "script_trust_negative_control": negative_control.get("status") == "pass",
        "isaac41_primary_and_auxiliary_regression": set(isaac41_interactive)
        == {"primary", "auxiliary"}
        and all(
            report.get("status") == "pass" for report in isaac41_interactive.values()
        ),
        "isaac41_articulation_regression": isaac41_articulation.get("status") == "pass",
        "isaac41_door_regression": isaac41_door.get("status") == "pass",
    }


def _load_existing(
    output: Path,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, Any],
    dict[str, dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    qualification = output / "qualification"
    isaac45_runs = {
        f"{knob}_cold_{index}": json.loads(
            (qualification / f"isaac45_{knob}_cold_{index}.json").read_text()
        )
        for knob in ("primary", "auxiliary")
        for index in range(1, 4)
    }
    negative = json.loads(
        (qualification / "isaac45_script_trust_negative.json").read_text()
    )
    isaac41_interactive = {
        knob: evaluate_interactive_report(
            json.loads((qualification / f"isaac41_{knob}_interactive.json").read_text())
        )
        for knob in ("primary", "auxiliary")
    }
    articulation = json.loads((qualification / "isaac41_articulation.json").read_text())
    door = json.loads((qualification / "isaac41_door_60deg.json").read_text())
    return isaac45_runs, negative, isaac41_interactive, articulation, door


def package_handoff(output: Path = DEFAULT_OUTPUT) -> Path:
    output = output.resolve()
    receipt = output / "promotion_receipt.json"
    report = output / "qualification/full_report.json"
    if json.loads(receipt.read_text()).get("status") != "promoted":
        raise ValueError("r17 package is not promoted")
    if json.loads(report.read_text()).get("status") != "pass":
        raise ValueError("r17 qualification did not pass")
    parent = output / "handoff"
    root = parent / "ika_oven_125_task09_r17_teleop_hardened"
    if root.exists():
        raise FileExistsError(f"refusing to replace handoff: {root}")
    shutil.copytree(output / "package", root / "package")
    shutil.copy2(receipt, root / "promotion_receipt.json")
    shutil.copy2(report, root / "qualification_full_report.json")
    (root / "README_CN.md").write_text(
        "# OVEN 125 r17 VR 旋钮稳定版\n\n"
        "入口 USD：`package/asset.usd`；入口 prim：`/World/obj_oven`。\n\n"
        "r17 保持 r16 fixed-base articulation、全部 prim path、碰撞与关节不变，"
        "只修复旋钮物理 pose 丢样和大角度输入被清零的问题。旋钮仍为 15°/档。"
        "Isaac Sim 4.5 是本次控制器主验收，4.1 已回归。打开可信内部资产时仍需"
        "允许 OmniGraph ScriptNode。不要在消费者侧修改 kinematic、关节或碰撞。\n",
        encoding="utf-8",
    )
    archive = parent / (root.name + ".zip")
    shutil.make_archive(
        str(archive.with_suffix("")), "zip", root_dir=parent, base_dir=root.name
    )
    archive.with_suffix(".zip.sha256").write_text(
        _sha(archive) + "  " + archive.name + "\n", encoding="utf-8"
    )
    return archive


def finalize_existing(output: Path = DEFAULT_OUTPUT) -> Path:
    output = output.resolve()
    (
        isaac45_runs,
        negative,
        isaac41_interactive,
        articulation,
        door,
    ) = _load_existing(output)
    checks = qualification_checks(
        isaac45_runs=isaac45_runs,
        negative_control=negative,
        isaac41_interactive=isaac41_interactive,
        isaac41_articulation=articulation,
        isaac41_door=door,
    )
    passed = all(checks.values())
    asset = output / "package/asset.usd"
    aggregate = {
        "schema_version": "aan.ika_oven_125_task09_r17_qualification.v1",
        "status": "pass" if passed else "blocked",
        "primary_runtime": "isaac45",
        "regression_runtime": "isaac41",
        "asset_sha256": _sha(asset),
        "checks": checks,
        "isaac45_vr_like_runs": isaac45_runs,
        "isaac45_script_trust_negative_control": negative,
        "isaac41_interactive_evaluations": isaac41_interactive,
        "isaac41_articulation": articulation,
        "isaac41_door": door,
        "claim_boundary": (
            "Isaac Sim 4.5 qualifies three cold VR-like joint-drive profiles for "
            "each physical knob: sub-threshold jitter, smooth rotation, rapid "
            "rotation, and pause/resume. Isaac Sim 4.1 regresses articulation, "
            "primary/auxiliary rotation and press, and the 60-degree door. This is "
            "not a headset/controller contact test, robot-policy success, or "
            "benchmark success claim."
        ),
    }
    aggregate_path = output / "qualification/full_report.json"
    _write_json(aggregate_path, aggregate)
    manifest_path = output / "package/evidence/task09_r17_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["overall_status"] = aggregate["status"]
    manifest["blocked_reasons"] = (
        [] if passed else [key for key, value in checks.items() if not value]
    )
    manifest["claims"]["isaac45_teleop_controls_qualified"] = checks[
        "isaac45_three_cold_runs_per_knob"
    ]
    manifest["claims"]["isaac41_regression_passed"] = all(
        checks[key]
        for key in (
            "isaac41_primary_and_auxiliary_regression",
            "isaac41_articulation_regression",
            "isaac41_door_regression",
        )
    )
    manifest["qualification"] = {
        "report": "../../qualification/full_report.json",
        "sha256": _sha(aggregate_path),
    }
    _write_json(manifest_path, manifest)
    if not passed:
        return aggregate_path
    receipt = {
        "schema_version": "aan.oven_teleop_controller_promotion_receipt.v1",
        "status": "promoted",
        "asset_id": "ika_oven_125_task09_r17_teleop_hardened",
        "primary_runtime": "isaac45",
        "regression_runtime": "isaac41",
        "asset_sha256": _sha(asset),
        "qualification_sha256": _sha(aggregate_path),
        "claims": manifest["claims"],
    }
    _write_json(output / "promotion_receipt.json", receipt)
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
    if not asset.is_file():
        raise FileNotFoundError(asset)
    qualification = output / "qualification"
    qualification.mkdir(parents=True, exist_ok=True)
    fixture = qualification / "fixtures/vr.usd"
    _fixture(asset, fixture, "/World/_scene/obj_oven", 1.0)

    source_scripts = R16_OUTPUT / "qualification"
    primary = qualification / "producer_interactive_smoke.py"
    auxiliary = qualification / "producer_interactive_smoke_aux.py"
    shutil.copy2(source_scripts / primary.name, primary)
    shutil.copy2(source_scripts / auxiliary.name, auxiliary)
    teleop_probe = REPO_ROOT / "scripts/probe_ika_oven_r17_knob_teleop.py"
    articulation_probe = REPO_ROOT / "scripts/probe_ika_oven_fixed_base_articulation.py"
    door_probe = REPO_ROOT / "scripts/probe_ika_oven_r16_door.py"
    environment = dict(os.environ)
    environment.update({"ACCEPT_EULA": "Y", "OMNI_KIT_ACCEPT_EULA": "YES"})

    for knob in ("primary", "auxiliary"):
        for index in range(1, 4):
            report = qualification / f"isaac45_{knob}_cold_{index}.json"
            _run(
                [
                    str(isaac45),
                    str(teleop_probe),
                    "--usd",
                    str(fixture),
                    "--root",
                    "/World/_scene/obj_oven",
                    "--knob",
                    knob,
                    "--output",
                    str(report),
                    "--script-opt-in",
                    "true",
                ],
                report,
                environment=environment,
            )

    negative = qualification / "isaac45_script_trust_negative.json"
    _run(
        [
            str(isaac45),
            str(teleop_probe),
            "--usd",
            str(fixture),
            "--root",
            "/World/_scene/obj_oven",
            "--knob",
            "primary",
            "--output",
            str(negative),
            "--script-opt-in",
            "false",
        ],
        negative,
        environment=environment,
    )

    for knob, script in (("primary", primary), ("auxiliary", auxiliary)):
        report = qualification / f"isaac41_{knob}_interactive.json"
        _run(
            [
                str(isaac41),
                str(script),
                "--usd",
                str(fixture),
                "--root",
                "/World/_scene/obj_oven/Instance",
                "--output",
                str(report),
                "--/app/omni.graph.scriptnode/opt_in=true",
            ],
            report,
            environment=environment,
        )

    articulation = qualification / "isaac41_articulation.json"
    _run(
        [
            str(isaac41),
            str(articulation_probe),
            "--usd",
            str(fixture),
            "--root",
            "/World/_scene/obj_oven",
            "--output",
            str(articulation),
        ],
        articulation,
        environment=environment,
    )
    door = qualification / "isaac41_door_60deg.json"
    _run(
        [
            str(isaac41),
            str(door_probe),
            "--usd",
            str(fixture),
            "--root",
            "/World/_scene/obj_oven",
            "--output",
            str(door),
        ],
        door,
        environment=environment,
    )
    return finalize_existing(output)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--isaac41-python", type=Path, default=DEFAULT_ISAAC41)
    parser.add_argument("--isaac45-python", type=Path, default=DEFAULT_ISAAC45)
    parser.add_argument("--finalize-existing", action="store_true")
    args = parser.parse_args(argv)
    if args.finalize_existing:
        print(finalize_existing(args.output))
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
