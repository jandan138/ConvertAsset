#!/usr/bin/env python3
"""Bind a qualified dynamic-loaded-start contract to an immutable PBD package."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any, Mapping


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON mapping: {path}")
    return value


def _valid_cold_run(
    run: Mapping[str, Any], *, particle_count: int, qualification: Mapping[str, Any]
) -> bool:
    return bool(
        run.get("overall_status") == "pass"
        and int(run.get("particle_count", -1)) == particle_count
        and int(run.get("maximum_outside_source_count", 10**9))
        <= int(qualification["maximum_outside_source_before_lift"])
        and float(run.get("entry_root_tail_drift_m", float("inf")))
        <= float(qualification["maximum_entry_root_tail_drift_m"])
        and float(run.get("maximum_entry_root_tilt_deg", float("inf")))
        <= float(qualification["maximum_entry_root_tilt_deg"])
        and run.get("hard_runtime_errors") == []
    )


def promote(
    *,
    package: Path,
    contract_path: Path,
    particle_state_path: Path,
    report_path: Path,
    output: Path,
    package_id: str,
) -> Path:
    package = package.resolve()
    contract_path = contract_path.resolve()
    particle_state_path = particle_state_path.resolve()
    report_path = report_path.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    manifest_path = package / "evidence/manifest.json"
    manifest = _load(manifest_path)
    contract = _load(contract_path)
    state = _load(particle_state_path)
    report = _load(report_path)
    if manifest.get("overall_status") != "pass":
        raise ValueError("base package is not qualified")
    if contract.get("schema_version") != "aan.gpu_pbd_dynamic_loaded_start.v1":
        raise ValueError("unsupported dynamic loaded-start contract")
    if contract.get("particle_state_sha256") != _sha(particle_state_path):
        raise ValueError("particle state hash does not match contract")
    if state.get("schema_version") != "aan.gpu_pbd_source_local_particle_state.v1":
        raise ValueError("unsupported source-local particle state")
    if report.get("contract_sha256") != _sha(contract_path):
        raise ValueError("contract hash does not match report")
    if report.get("particle_state_sha256") != _sha(particle_state_path):
        raise ValueError("particle state hash does not match report")
    particle_count = int(contract.get("particle_count", -1))
    if (
        int(state.get("particle_count", -1)) != particle_count
        or int(manifest.get("gpu_pbd_transfer_pair", {}).get("particle_count", -1))
        != particle_count
    ):
        raise ValueError("particle count differs across bound artifacts")
    qualification = contract.get("qualification")
    cold_runs = report.get("cold_runs")
    if (
        report.get("overall_status") != "pass"
        or report.get("promotion")
        != {"allowed": True, "claim": "gpu_pbd_dynamic_loaded_start"}
        or not isinstance(qualification, Mapping)
        or not isinstance(cold_runs, list)
        or len(cold_runs) != int(qualification.get("required_cold_runs", -1))
        or len(cold_runs) != 3
        or not all(
            isinstance(run, Mapping)
            and _valid_cold_run(
                run, particle_count=particle_count, qualification=qualification
            )
            for run in cold_runs
        )
    ):
        raise ValueError("dynamic loaded-start cold run failed a required gate")

    shutil.copytree(package, output)
    evidence = output / "evidence/dynamic_loaded_start"
    evidence.mkdir(parents=True)
    destinations = {
        "contract": evidence / contract_path.name,
        "particle_state": evidence / particle_state_path.name,
        "report": evidence / report_path.name,
    }
    shutil.copy2(contract_path, destinations["contract"])
    shutil.copy2(particle_state_path, destinations["particle_state"])
    shutil.copy2(report_path, destinations["report"])
    manifest["package_id"] = package_id
    manifest["gpu_pbd_dynamic_loaded_start"] = {
        "status": "qualified",
        "contract": destinations["contract"].relative_to(output).as_posix(),
        "contract_sha256": _sha(destinations["contract"]),
        "particle_state": destinations["particle_state"].relative_to(output).as_posix(),
        "particle_state_sha256": _sha(destinations["particle_state"]),
        "report": destinations["report"].relative_to(output).as_posix(),
        "report_sha256": _sha(destinations["report"]),
        "particle_count": particle_count,
        "cold_runs": len(cold_runs),
        "maximum_outside_source_before_lift": int(
            qualification["maximum_outside_source_before_lift"]
        ),
        "support_plane_to_entry_root": contract["support_plane_to_entry_root"],
        "runtime": "isaac41",
    }
    (output / "evidence/manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--particle-state", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--package-id", required=True)
    args = parser.parse_args()
    print(
        promote(
            package=args.package,
            contract_path=args.contract,
            particle_state_path=args.particle_state,
            report_path=args.report,
            output=args.out,
            package_id=args.package_id,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
