#!/usr/bin/env python3
"""Promote a qualified GPU-PBD prescribed-transfer fixture as a handoff package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any, Mapping


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _tree_sha(path: Path) -> str:
    digest = sha256()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(_sha(item)))
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON mapping: {path}")
    return value


def _valid_cold_run(run: Mapping[str, Any]) -> bool:
    hold = run.get("static_hold")
    pour = run.get("pour")
    performance = run.get("performance")
    return bool(
        run.get("overall_status") == "pass"
        and run.get("particle_readback_attribute") == "points"
        and isinstance(hold, Mapping)
        and float(hold.get("minimum_source_ratio", 0.0)) >= 0.95
        and isinstance(pour, Mapping)
        and pour.get("particle_count") == 548
        and float(pour.get("target_ratio", 0.0)) >= 0.5
        and isinstance(performance, Mapping)
        and float(performance.get("mean_rtx_fps", 0.0)) >= 40.0
        and run.get("hard_runtime_errors") == []
    )


def promote(
    *, fixture: Path, report_path: Path, output: Path, package_id: str
) -> Path:
    fixture = fixture.resolve()
    report_path = report_path.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    profile_path = fixture / "transfer_fixture_profile.json"
    component_path = fixture / "component.usda"
    deps_path = fixture / "deps"
    for required in (profile_path, component_path, deps_path):
        if not required.exists():
            raise ValueError(f"transfer fixture is incomplete: {required}")
    profile = _load(profile_path)
    report = _load(report_path)
    if profile.get("schema_version") != "aan.gpu_pbd_transfer_fixture.v1":
        raise ValueError("unsupported transfer fixture profile")
    promotion = report.get("promotion")
    cold_runs = report.get("cold_runs")
    if (
        report.get("overall_status") != "pass"
        or not isinstance(promotion, Mapping)
        or promotion.get("allowed") is not True
        or promotion.get("claim") != "gpu_pbd_prescribed_transfer_pair"
        or report.get("fixture_profile_sha256") != _sha(profile_path)
    ):
        raise ValueError("transfer admission report is not promotable")
    if (
        not isinstance(cold_runs, list)
        or len(cold_runs) != 3
        or not all(isinstance(run, Mapping) and _valid_cold_run(run) for run in cold_runs)
    ):
        raise ValueError("transfer cold run failed a required gate")
    selected = report.get("selected_candidate")
    candidates = profile.get("bounded_search", {}).get("candidates", [])
    if not isinstance(selected, Mapping) or selected not in candidates:
        raise ValueError("selected transfer candidate is not bound to the fixture")

    shutil.copytree(fixture, output)
    evidence = output / "evidence"
    evidence.mkdir()
    promoted_report = evidence / "gpu_pbd_transfer_admission_report.json"
    shutil.copy2(report_path, promoted_report)
    copied_profile = output / profile_path.name
    copied_component = output / component_path.name
    particle_count = int(profile.get("liquid_parameters", {}).get("particle_count", 0))
    if particle_count != 548:
        raise ValueError("transfer fixture particle_count must be 548")
    manifest = {
        "schema_version": "aan.gpu_pbd_transfer_pair_manifest.v1",
        "package_id": package_id,
        "overall_status": "pass",
        "entrypoints": {
            "root_usd": copied_component.name,
            "asset_entry_prim": "/World/Transfer",
        },
        "gpu_pbd_transfer_pair": {
            "status": "qualified",
            "profile": copied_profile.name,
            "profile_sha256": _sha(copied_profile),
            "report": promoted_report.relative_to(output).as_posix(),
            "report_sha256": _sha(promoted_report),
            "component_sha256": _sha(copied_component),
            "dependency_tree_sha256": _tree_sha(output / "deps"),
            "particle_count": particle_count,
            "cold_runs": 3,
            "runtime": "isaac41",
            "selected_candidate": dict(selected),
        },
        "promotion": {
            "allowed": True,
            "claim": "gpu_pbd_prescribed_transfer_pair",
            "claim_boundary": report.get("claim_boundary"),
        },
    }
    (evidence / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--package-id", required=True)
    args = parser.parse_args()
    print(
        promote(
            fixture=args.fixture,
            report_path=args.report,
            output=args.out,
            package_id=args.package_id,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
