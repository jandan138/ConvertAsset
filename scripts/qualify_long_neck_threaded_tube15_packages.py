#!/usr/bin/env python3
"""Qualify dynamic geometry and preserve the threaded-interaction blocker."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "outputs/tube15_long_neck_threaded_geometry_v1_20260901"
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


def _render_evidence(output: Path, label: str) -> list[dict[str, str]]:
    evidence = []
    for path in sorted((output / f"evidence/render/{label}/asset").glob("*.png")):
        evidence.append(
            {
                "path": str(path.relative_to(output)),
                "sha256": _sha(path),
            }
        )
    return evidence


def classify_asset_set(
    dynamic_reports: dict[str, list[dict[str, Any]]],
    thread_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    dynamic_ready = all(
        report.get("overall_status") == "pass"
        for reports in dynamic_reports.values()
        for report in reports
    ) and all(len(reports) == 3 for reports in dynamic_reports.values())
    thread_ready = bool(thread_reports) and all(
        report.get("overall_status") == "pass" for report in thread_reports
    )
    return {
        "overall_status": "pass" if dynamic_ready else "blocked",
        "claims": {
            "dynamic_geometry_ready": dynamic_ready,
            "sdf_collision_ready": dynamic_ready,
            "thread_interaction_ready": thread_ready,
            "task08_ready": False,
            "liquid_container_ready": False,
            "robot_policy_success": False,
            "benchmark_success": False,
        },
    }


def _thread_fixture(source: Path, destination: Path) -> None:
    from pxr import Sdf

    destination.write_bytes(source.read_bytes())
    layer = Sdf.Layer.FindOrOpen(str(destination))
    layer.subLayerPaths = []
    edits = Sdf.BatchNamespaceEdit()
    edits.Add("/World/tube", "/World/TubeBody")
    edits.Add("/World/cap", "/World/Cap")
    if not layer.Apply(edits):
        raise RuntimeError("cannot build threaded-contact fixture")
    layer.Save()


def qualify(
    output: Path = DEFAULT_OUTPUT,
    *,
    isaac: Path = DEFAULT_ISAAC,
) -> Path:
    output = output.resolve()
    manifest_path = output / "asset_set_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    environment = dict(os.environ)
    environment.update({"ACCEPT_EULA": "Y", "OMNI_KIT_ACCEPT_EULA": "YES"})
    worker = REPO_ROOT / "scripts/qualify_wangshuai_dynamic_assets.py"
    dynamic_reports: dict[str, list[dict[str, Any]]] = {"body": [], "cap": []}
    for label, worker_asset in (
        ("body", "long_neck_threaded_body"),
        ("cap", "long_neck_threaded_cap"),
    ):
        for index in range(3):
            report_path = output / f"evidence/runtime/{label}/run_{index:02d}.json"
            if not report_path.is_file():
                completed = subprocess.run(
                    [
                        str(isaac),
                        str(worker),
                        "--asset-set",
                        str(output),
                        "--asset",
                        worker_asset,
                        "--run-index",
                        str(index),
                        "--out",
                        str(report_path),
                    ],
                    check=False,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                report_path.parent.mkdir(parents=True, exist_ok=True)
                (report_path.parent / f"run_{index:02d}.stdout.log").write_bytes(
                    completed.stdout
                )
                (report_path.parent / f"run_{index:02d}.stderr.log").write_bytes(
                    completed.stderr
                )
            if not report_path.is_file():
                raise RuntimeError(f"dynamic worker emitted no report: {label}/{index}")
            dynamic_reports[label].append(
                json.loads(report_path.read_text(encoding="utf-8"))
            )

    thread_root = output / "evidence/thread_interaction"
    thread_root.mkdir(parents=True, exist_ok=True)
    source = output / "input/source.usd"
    fixture = thread_root / "fixture.usd"
    _thread_fixture(source, fixture)
    contact = REPO_ROOT / "scripts/qualify_threaded_tube15_contact.py"
    authored = thread_root / "qualify_authored_phase.py"
    authored_source = contact.read_text(encoding="utf-8")
    authored_source = authored_source.replace(
        "START_Z_M = 0.1092", "START_Z_M = 0.10998681642541698"
    ).replace(
        "identity = np.asarray([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)",
        "identity = np.asarray([[0.5569506, 0.0, 0.0, 0.8305456]], dtype=np.float32)",
    )
    authored.write_text(authored_source, encoding="utf-8")
    thread_reports = []
    for name, script in (("default_phase", contact), ("author_phase", authored)):
        report_path = thread_root / f"{name}.json"
        if not report_path.is_file():
            completed = subprocess.run(
                [
                    str(isaac),
                    str(script),
                    "--assembly",
                    str(fixture),
                    "--out",
                    str(report_path),
                ],
                check=False,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (thread_root / f"{name}.stdout.log").write_bytes(completed.stdout)
            (thread_root / f"{name}.stderr.log").write_bytes(completed.stderr)
        thread_reports.append(json.loads(report_path.read_text(encoding="utf-8")))

    classification = classify_asset_set(dynamic_reports, thread_reports)
    aggregate = {
        "schema_version": "aan.tube15_long_neck_threaded_qualification.v1",
        **classification,
        "runtime": "isaac41",
        "dynamic_reports": dynamic_reports,
        "thread_reports": thread_reports,
        "claim_boundary": (
            "Body and closed-cap packages are promoted only for provisional dynamic "
            "geometry and SDF collision. Reversible thread interaction remains blocked."
        ),
    }
    aggregate_path = output / "runtime_qualification_report.json"
    _write_json(aggregate_path, aggregate)
    manifest["overall_status"] = classification["overall_status"]
    manifest["claims"] = classification["claims"]
    manifest["qualification"] = {
        "report": "runtime_qualification_report.json",
        "report_sha256": _sha(aggregate_path),
    }
    _write_json(manifest_path, manifest)
    if classification["overall_status"] == "pass":
        for name, package in (
            ("body", output / "packages/tube15_long_neck_threaded_body_v1"),
            ("cap", output / "packages/tube15_long_neck_threaded_closed_cap_v1"),
        ):
            receipt = package / "promotion_receipt.json"
            _write_json(
                receipt,
                {
                    "schema_version": "aan.dynamic_geometry_promotion_receipt.v1",
                    "status": "promoted",
                    "asset_role": name,
                    "runtime": "isaac41",
                    "asset_sha256": _sha(package / "asset.usd"),
                    "qualification_sha256": _sha(aggregate_path),
                    "claims": classification["claims"],
                },
            )
            package_manifest = {
                "schema_version": "aan.dynamic_geometry_package_manifest.v1",
                "overall_status": "pass",
                "asset_role": name,
                "entrypoint": {
                    "root_usd": "asset.usd",
                    "asset_entry_prim": (
                        "/World/Tube15LongNeckThreadedBody"
                        if name == "body"
                        else "/World/Tube15LongNeckThreadedClosedCap"
                    ),
                },
                "source": manifest["source"],
                "runtime": "isaac41",
                "claims": classification["claims"],
                "qualification": {
                    "report": str(aggregate_path.relative_to(output)),
                    "report_sha256": _sha(aggregate_path),
                    "promotion_receipt": "promotion_receipt.json",
                    "promotion_receipt_sha256": _sha(receipt),
                },
                "render_evidence": _render_evidence(output, name),
                "visual_review": (
                    {
                        "path": "evidence/render/visual_review.json",
                        "sha256": _sha(output / "evidence/render/visual_review.json"),
                        "status": "pass_with_warning",
                    }
                    if (output / "evidence/render/visual_review.json").is_file()
                    else {"status": "not_run"}
                ),
                "claim_boundary": aggregate["claim_boundary"],
            }
            _write_json(package / "evidence/manifest.json", package_manifest)
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
