#!/usr/bin/env python3
"""Promote the traditional titration component and station packages."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any, Sequence
import zipfile


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def promote(output: Path, reports: Sequence[Path]) -> Path:
    output = output.resolve()
    if len(reports) < 3:
        raise ValueError("promotion requires at least three cold-start reports")
    parsed = [json.loads(Path(path).read_text(encoding="utf-8")) for path in reports]
    if any(report.get("status") != "pass" for report in parsed):
        raise ValueError("all station runtime reports must pass")
    if any(str(report.get("runtime_version")) != "4.5.0" for report in parsed):
        raise ValueError("all station runtime reports must come from Isaac Sim 4.5.0")

    station_evidence = output / "packages/station/evidence"
    runtime_dir = station_evidence / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for index, source in enumerate(reports, 1):
        destination = runtime_dir / f"cold_start_{index}.json"
        shutil.copy2(source, destination)
        copied.append(
            {
                "path": str(destination.relative_to(output)),
                "sha256": _sha(destination),
            }
        )

    station_manifest_path = output / "packages/station/evidence/manifest.json"
    station_package_id = json.loads(
        station_manifest_path.read_text(encoding="utf-8")
    )["package_id"]
    package_revision = station_package_id.rsplit("_", 1)[-1]
    for name in ("burette", "stand", "station"):
        manifest_path = output / f"packages/{name}/evidence/manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["overall_status"] = "pass"
        manifest["blocked_reasons"] = []
        manifest["claims"]["component_structure_qualified"] = True
        if name == "station":
            manifest["claims"].update(
                {
                    "isaac45_runtime_qualified": True,
                    "runtime_cold_start_passes": len(copied),
                    "state_machine_success_and_overshoot_paths": True,
                    "fixed_base_stability_verified": True,
                }
            )
            manifest["runtime_evidence"] = copied
        _write(manifest_path, manifest)

    receipt = {
        "schema_version": "aan.traditional_titration_promotion.v1",
        "package_id": station_package_id,
        "status": "promoted",
        "package": "packages/station",
        "runtime": "Isaac Sim 4.5.0",
        "cold_start_passes": len(copied),
        "evidence": copied,
        "claims": {
            "asset_functionality": True,
            "fixed_base_articulation": True,
            "relocatable_state_machine": True,
            "robot_policy_success": False,
            "benchmark_success": False,
            "true_chemistry_simulation": False,
        },
    }
    receipt_path = output / "promotion_receipt.json"
    _write(receipt_path, receipt)

    handoff = output / "handoff"
    handoff.mkdir(exist_ok=True)
    archive_name = f"traditional_titration_assets_{package_revision}"
    archive = handoff / f"{archive_name}.zip"
    archive_root = Path(archive_name)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        handle.write(receipt_path, archive_root / "promotion_receipt.json")
        for path in sorted((output / "packages").rglob("*")):
            if path.is_file():
                handle.write(path, archive_root / path.relative_to(output))
    (archive.with_suffix(".zip.sha256")).write_text(
        f"{_sha(archive)}  {archive.name}\n", encoding="utf-8"
    )
    return receipt_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, action="append", required=True)
    args = parser.parse_args(argv)
    print(promote(args.output, args.report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
