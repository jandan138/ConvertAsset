#!/usr/bin/env python3
"""Promote a source-bound container after the three-cold GPU-PBD gate."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def validate_report(report: dict[str, Any]) -> None:
    runs = report.get("runs", [])
    if report.get("required_cold_runs") != 3 or len(runs) != 3:
        raise ValueError("promotion requires exactly three cold runs")
    if report.get("overall_status") != "pass":
        raise ValueError("qualification report is not pass")
    for index, run in enumerate(runs, start=1):
        semantics = run.get("resolved_particle_semantics", {})
        hold = run.get("static_hold", {})
        performance = run.get("performance", {})
        valid = (
            run.get("overall_status") == "pass"
            and semantics.get("fluid") is True
            and semantics.get("self_collision") is True
            and hold.get("minimum_inside_ratio", 0.0) >= 0.95
            and hold.get("maximum_below_support") == 0
            and performance.get("mean_rtx_fps", 0.0) >= 40.0
            and not run.get("hard_runtime_errors")
        )
        if not valid:
            raise ValueError(f"cold run {index} does not satisfy promotion gates")


def promote(
    *,
    candidate_package: Path,
    fixture: Path,
    qualification_report: Path,
    visual_evidence: list[Path],
    output: Path,
) -> dict[str, Any]:
    candidate_package = candidate_package.resolve()
    fixture = fixture.resolve()
    qualification_report = qualification_report.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite promoted package: {output}")
    report = json.loads(qualification_report.read_text(encoding="utf-8"))
    validate_report(report)
    fixture_profile = fixture / "fixture_profile.json"
    fixture_points = fixture / "authored_particle_points.json"
    for required in (fixture_profile, fixture_points):
        if not required.is_file():
            raise FileNotFoundError(required)

    shutil.copytree(candidate_package, output)
    evidence = output / "evidence"
    copied_report = evidence / "gpu_pbd_static_qualification_report.json"
    copied_fixture = evidence / "gpu_pbd_static_fixture.json"
    copied_points = evidence / "gpu_pbd_initial_particle_state.json"
    shutil.copy2(qualification_report, copied_report)
    shutil.copy2(fixture_profile, copied_fixture)
    shutil.copy2(fixture_points, copied_points)
    visual_records = []
    visual_root = evidence / "visual"
    visual_root.mkdir(parents=True, exist_ok=True)
    for index, source in enumerate(visual_evidence, start=1):
        source = source.resolve()
        target = visual_root / f"view_{index:02d}{source.suffix.lower()}"
        shutil.copy2(source, target)
        visual_records.append({"path": str(target.relative_to(output)), "sha256": _sha(target)})

    qualification = {
        "report": str(copied_report.relative_to(output)),
        "report_sha256": _sha(copied_report),
        "fixture": str(copied_fixture.relative_to(output)),
        "fixture_sha256": _sha(copied_fixture),
        "initial_particle_state": str(copied_points.relative_to(output)),
        "initial_particle_state_sha256": _sha(copied_points),
        "visual_evidence": visual_records,
        "runtime": "isaac41",
        "cold_runs": 3,
    }
    profile_path = output / "gpu_pbd_static_container_profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["claim"] = "gpu_pbd_static_container"
    profile["promotion"] = {"status": "qualified", **qualification}
    profile["claim_boundary"] = (
        "Static GPU-PBD containment with the bound initial particle state only; "
        "no pour, grasp, robot-policy, benchmark, or arbitrary-fluid-state claim."
    )
    _write_json(profile_path, profile)

    manifest_path = evidence / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["overall_status"] = "pass"
    manifest["gpu_pbd_static_container"] = {
        "status": "qualified",
        "profile": "gpu_pbd_static_container_profile.json",
        **qualification,
    }
    manifest["promotion"] = {
        "allowed": True,
        "claim": "gpu_pbd_static_container",
        "claim_boundary": profile["claim_boundary"],
    }
    _write_json(manifest_path, manifest)
    receipt = {
        "schema_version": "aan.gpu_pbd_static_promotion_receipt.v1",
        "overall_status": "pass",
        "claim": "gpu_pbd_static_container",
        "package": str(output),
        "asset_sha256": _sha(output / "asset.usd"),
        "profile_sha256": _sha(profile_path),
        "manifest_sha256": _sha(manifest_path),
        "qualification": qualification,
        "claim_boundary": profile["claim_boundary"],
    }
    _write_json(evidence / "promotion_receipt.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-package", required=True, type=Path)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--qualification-report", required=True, type=Path)
    parser.add_argument("--visual", action="append", default=[], type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            promote(
                candidate_package=args.candidate_package,
                fixture=args.fixture,
                qualification_report=args.qualification_report,
                visual_evidence=args.visual,
                output=args.out,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
