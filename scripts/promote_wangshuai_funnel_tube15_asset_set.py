#!/usr/bin/env python3
"""Promote the exact Wangshuai asset set after source and three recomposed runs pass."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


RUNS = ("run_00", "run_01", "run_02")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def promote(root: Path) -> Path:
    root = root.resolve()
    manifest_path = root / "asset_set_manifest.json"
    build_text = manifest_path.read_text()
    build_sha = sha256(build_text.encode()).hexdigest()
    source_baseline = _read(root / "evidence/source_baseline/report.json")
    runs = [
        _read(root / f"evidence/recomposition/{name}/report.json") for name in RUNS
    ]

    def report_passes(report: dict, mode: str) -> bool:
        observations = report.get("observations", {})
        return (
            report.get("status") == "pass"
            and report.get("mode") == mode
            and report.get("asset_set_manifest_sha256") == build_sha
            and observations.get("authored_particle_count") == 1948
            and observations.get("runtime_particle_count") == 1948
            and observations.get("capture_ratio", 0.0) >= 0.95
            and observations.get("below_floor_count") == 0
            and observations.get("nonfinite_count") == 0
            and not observations.get("hard_errors")
        )

    if not report_passes(source_baseline, "source"):
        raise RuntimeError("source baseline is incomplete")
    if not all(report_passes(report, "recomposed") for report in runs):
        raise RuntimeError("three recomposed cold runs must pass")
    source_sha = source_baseline["source_sha256"]
    if any(report.get("source_sha256") != source_sha for report in runs):
        raise RuntimeError("runtime reports do not bind the same source")

    evidence = root / "evidence"
    evidence.mkdir(exist_ok=True)
    build_manifest = evidence / "build_manifest.json"
    build_manifest.write_text(build_text)
    package_records = []
    index = json.loads(build_text)
    for item in index["assets"]:
        package = root / item["package"]
        package_manifest_path = package / "evidence/manifest.json"
        package_manifest = _read(package_manifest_path)
        if package_manifest.get("forbidden_changes_detected"):
            raise RuntimeError(f"forbidden source change in {item['id']}")
        package_manifest["overall_status"] = "pass"
        package_manifest["blocked_reasons"] = []
        package_manifest["claims"]["runtime_recomposition_qualified"] = True
        package_manifest["runtime_qualification"] = {
            "runtime": "isaac41",
            "source_baseline": "../../../evidence/source_baseline/report.json",
            "recomposition_runs": [
                f"../../../evidence/recomposition/{name}/report.json" for name in RUNS
            ],
            "build_manifest_sha256": build_sha,
        }
        package_manifest_path.write_text(
            json.dumps(package_manifest, indent=2, sort_keys=True) + "\n"
        )
        item["overall_status"] = "pass"
        item["producer_manifest"] = (
            Path(item["package"]) / "evidence/manifest.json"
        ).as_posix()
        item["producer_manifest_sha256"] = _sha(package_manifest_path)
        package_records.append(
            {
                "id": item["id"],
                "manifest": item["producer_manifest"],
                "manifest_sha256": item["producer_manifest_sha256"],
            }
        )
    index["status"] = "pass"
    index["claims"]["runtime_recomposition_qualified"] = True
    index["runtime_qualification"] = {
        "runtime": "isaac41",
        "duration_seconds": 16.0,
        "source_baseline": "evidence/source_baseline/report.json",
        "recomposition_runs": [
            f"evidence/recomposition/{name}/report.json" for name in RUNS
        ],
        "build_manifest": "evidence/build_manifest.json",
        "build_manifest_sha256": build_sha,
        "source_capture_ratio": source_baseline["observations"]["capture_ratio"],
        "recomposed_capture_ratios": [
            report["observations"]["capture_ratio"] for report in runs
        ],
    }
    manifest_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    receipt = {
        "schema_version": "aan.wangshuai_funnel_tube15_asset_set_promotion.v1",
        "status": "pass",
        "source_sha256": source_sha,
        "build_manifest_sha256": build_sha,
        "final_manifest_sha256": _sha(manifest_path),
        "packages": package_records,
        "claims": index["claims"],
        "claim_boundary": (
            "Exact-source independent assets and robot-free funnel-to-tube liquid "
            "recomposition only; robot, task, and benchmark success remain false."
        ),
    }
    receipt_path = evidence / "promotion.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(promote(args.root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
