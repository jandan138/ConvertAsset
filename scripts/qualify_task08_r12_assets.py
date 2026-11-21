#!/usr/bin/env python3
"""Run and aggregate Task 08 r12 rack/body/cap Isaac Sim qualifications."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "outputs/scientific_workbench_task08_r12_assets_20260901"
DEFAULT_ISAAC = Path(
    "/cpfs/user/zhuzihou/conda-managed/envs/"
    "embodied-eval-os-isaacsim41-py310/bin/python"
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def classify(reports: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    ready = all(
        len(items) == 3 and all(item.get("overall_status") == "pass" for item in items)
        for items in reports.values()
    )
    return {
        "status": "pass" if ready else "blocked",
        "claims": {
            "rack_scaled_sdf_ready": ready,
            "visual_material_variants_ready": ready,
            "thread_interaction_ready": False,
            "task08_success": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }


def _run(
    command: list[str], report: Path, *, environment: dict[str, str]
) -> dict[str, Any]:
    if not report.is_file():
        completed = subprocess.run(
            command,
            check=False,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        report.parent.mkdir(parents=True, exist_ok=True)
        report.with_suffix(".stdout.log").write_bytes(completed.stdout)
        report.with_suffix(".stderr.log").write_bytes(completed.stderr)
    if not report.is_file():
        raise RuntimeError(f"qualification emitted no report: {report}")
    return json.loads(report.read_text(encoding="utf-8"))


def qualify(root: Path = DEFAULT_ROOT, *, isaac: Path = DEFAULT_ISAAC) -> Path:
    root = root.resolve()
    environment = dict(os.environ)
    environment.update({"ACCEPT_EULA": "Y", "OMNI_KIT_ACCEPT_EULA": "YES"})
    reports: dict[str, list[dict[str, Any]]] = {"rack": [], "body": [], "cap": []}
    rack_worker = REPO_ROOT / "scripts/qualify_task08_r12_rack.py"
    dynamic_worker = REPO_ROOT / "scripts/qualify_wangshuai_dynamic_assets.py"
    for index in range(3):
        report = root / f"evidence/runtime/rack/run_{index:02d}.json"
        reports["rack"].append(
            _run(
                [
                    str(isaac),
                    str(rack_worker),
                    "--asset-set",
                    str(root),
                    "--run-index",
                    str(index),
                    "--out",
                    str(report),
                ],
                report,
                environment=environment,
            )
        )
    for label, role in (
        ("body", "task08_r12_body_glass"),
        ("cap", "task08_r12_cap_red"),
    ):
        for index in range(3):
            report = root / f"evidence/runtime/{label}/run_{index:02d}.json"
            reports[label].append(
                _run(
                    [
                        str(isaac),
                        str(dynamic_worker),
                        "--asset-set",
                        str(root),
                        "--asset",
                        role,
                        "--run-index",
                        str(index),
                        "--out",
                        str(report),
                    ],
                    report,
                    environment=environment,
                )
            )
    result = classify(reports)
    aggregate = {
        "schema_version": "aan.task08_r12_asset_qualification.v1",
        **result,
        "runtime": "isaac41",
        "reports": reports,
        "claim_boundary": (
            "Qualification covers baked rack SDF selected-slot stability and visual-only "
            "body/cap variants. It does not qualify thread engagement or Task 08 success."
        ),
    }
    aggregate_path = root / "runtime_qualification_report.json"
    _write_json(aggregate_path, aggregate)
    index_path = root / "asset_set_manifest.json"
    index = json.loads(index_path.read_text())
    index["status"] = result["status"]
    index["claims"] = result["claims"]
    index["qualification"] = {
        "report": "runtime_qualification_report.json",
        "sha256": _sha(aggregate_path),
    }
    _write_json(index_path, index)
    packages = {
        "rack": root / "packages/mixed_rack_18plus4_scaled_sdf_r3",
        "body": root / "packages/tube15_long_neck_threaded_body_glass_v1_2",
        "cap": root / "packages/tube15_long_neck_threaded_closed_cap_red_v1_2",
    }
    for label, package in packages.items():
        manifest_path = package / "evidence/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["overall_status"] = result["status"]
        manifest["blocked_reasons"] = [] if result["status"] == "pass" else [
            "Isaac Sim 4.1 qualification blocked"
        ]
        if label == "rack":
            manifest["claims"]["isaac41_selected_slot_stability"] = result["status"] == "pass"
        else:
            manifest["claims"]["dynamic_runtime_qualified"] = result["status"] == "pass"
        manifest["qualification"] = {
            "aggregate": str(aggregate_path.relative_to(root)),
            "sha256": _sha(aggregate_path),
        }
        _write_json(manifest_path, manifest)
    return aggregate_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--isaac-python", type=Path, default=DEFAULT_ISAAC)
    args = parser.parse_args(argv)
    print(qualify(args.root, isaac=args.isaac_python))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
