#!/usr/bin/env python3
"""Qualify the Task 09/12 direct-stage IKA OVEN 125 fixed-mount package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "outputs/ika_oven_125_task0912_fixed_benchtop_r1_20260831"
DEFAULT_ISAAC41_PYTHON = Path(
    "/cpfs/user/zhuzihou/conda-managed/envs/"
    "embodied-eval-os-isaacsim41-py310/bin/python"
)
ENTRY_PATH = "/World/Oven125"
MOUNTS: dict[str, dict[str, Any]] = {
    "direct_stage": {
        "root": "/World/Oven125",
        "device_root": "/World/Oven125",
        "translation": [0.0, 0.0, 0.0],
    },
}


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def build_fixtures(package: Path, qualification: Path) -> dict[str, Path]:
    package = package.resolve()
    asset = package / "asset.usd"
    if not asset.is_file():
        raise FileNotFoundError(asset)
    qualification.mkdir(parents=True, exist_ok=True)
    return {"direct_stage": asset}


def evaluate_reports(reports: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    missing = sorted(set(MOUNTS) - set(reports))
    blocked = sorted(
        name
        for name in MOUNTS
        if name not in missing
        and not (
            reports[name].get("status") == "PASS"
            and reports[name].get("passed") is True
        )
    )
    return {
        "schema_version": "aan.ika_oven_125_relocation_qualification.v1",
        "status": "pass" if not missing and not blocked else "blocked",
        "missing_namespaces": missing,
        "blocked_namespaces": blocked,
        "namespaces": {
            name: {
                "root": MOUNTS[name]["root"],
                "device_root": MOUNTS[name]["device_root"],
                "translation": MOUNTS[name]["translation"],
                "producer_status": reports.get(name, {}).get("status"),
                "producer_passed": reports.get(name, {}).get("passed"),
            }
            for name in MOUNTS
        },
        "claim_boundary": (
            "Producer full physical-input and OmniGraph parity in the fixed direct-stage "
            "Task 09/12 mount. The asset is not approved for parent-Xform, rename, "
            "randomization, or VR _scene mounting. No robot-policy, benchmark, thermal "
            "calibration, or safety claim."
        ),
    }


def run_qualification(
    output: Path = DEFAULT_OUTPUT,
    *,
    isaac_python: Path = DEFAULT_ISAAC41_PYTHON,
) -> Path:
    output = output.resolve()
    package = output / "package"
    qualification = output / "qualification"
    script = package / "evidence/producer_interactive_smoke.py"
    if not script.is_file():
        raise FileNotFoundError(script)
    if not isaac_python.is_file():
        raise FileNotFoundError(isaac_python)
    fixtures = build_fixtures(package, qualification)
    reports: dict[str, dict[str, Any]] = {}
    environment = dict(os.environ)
    environment.update(
        {
            "ACCEPT_EULA": "Y",
            "OMNI_KIT_ACCEPT_EULA": "YES",
            "PYTHONNOUSERSITE": "1",
        }
    )
    for name, fixture in fixtures.items():
        report_path = qualification / name / "interactive_smoke.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            str(isaac_python),
            str(script),
            "--usd",
            str(fixture),
            "--output",
            str(report_path),
            "--root",
            MOUNTS[name]["device_root"],
            "--/app/omni.graph.scriptnode/opt_in=true",
        ]
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )
        (report_path.parent / "stdout.log").write_bytes(completed.stdout)
        (report_path.parent / "stderr.log").write_bytes(completed.stderr)
        if not report_path.is_file():
            reports[name] = {
                "status": "ERROR",
                "passed": False,
                "returncode": completed.returncode,
                "reason": "producer smoke emitted no report",
            }
        else:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["subprocess_returncode"] = completed.returncode
            reports[name] = report
    aggregate = evaluate_reports(reports)
    aggregate["reports"] = {
        name: {
            "path": str(
                (qualification / name / "interactive_smoke.json").relative_to(output)
            ),
            "sha256": (
                _sha256_file(qualification / name / "interactive_smoke.json")
                if (qualification / name / "interactive_smoke.json").is_file()
                else None
            ),
        }
        for name in MOUNTS
    }
    aggregate_path = qualification / "full_report.json"
    _write_json(aggregate_path, aggregate)

    manifest_path = package / "evidence/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["qualification"] = {
        "report": "../qualification/full_report.json",
        "report_sha256": _sha256_file(aggregate_path),
        "status": aggregate["status"],
    }
    if aggregate["status"] == "pass":
        manifest["overall_status"] = "pass"
        manifest["claims"]["full_functional_parity_fixed_mount"] = True
        manifest["claims"]["task09_task12_subset"] = True
        _write_json(
            output / "promotion_receipt.json",
            {
                "schema_version": "aan.ika_oven_125_promotion_receipt.v1",
                "status": "promoted",
                "package_id": manifest["package_id"],
                "runtime": "isaac41",
                "qualification_report_sha256": _sha256_file(aggregate_path),
                "claims": manifest["claims"],
            },
        )
    else:
        manifest["overall_status"] = "blocked"
    _write_json(manifest_path, manifest)
    package_manifest_path = output / "package.manifest.json"
    package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    package_manifest.update(
        {
            "overall_status": manifest["overall_status"],
            "claims": manifest["claims"],
            "qualification": manifest["qualification"],
        }
    )
    _write_json(package_manifest_path, package_manifest)
    return aggregate_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--isaac-python", type=Path, default=DEFAULT_ISAAC41_PYTHON)
    args = parser.parse_args(argv)
    report = run_qualification(args.output, isaac_python=args.isaac_python)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
