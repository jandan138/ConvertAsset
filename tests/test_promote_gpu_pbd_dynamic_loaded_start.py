from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/promote_gpu_pbd_dynamic_loaded_start.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location(
        "promote_gpu_pbd_dynamic_loaded_start", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _delivery(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    package = tmp_path / "package"
    (package / "evidence").mkdir(parents=True)
    (package / "component.usda").write_text("component", encoding="utf-8")
    (package / "evidence/manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "aan.gpu_pbd_transfer_pair_manifest.v1",
                "package_id": "task02.r4",
                "overall_status": "pass",
                "entrypoints": {
                    "root_usd": "component.usda",
                    "asset_entry_prim": "/World/Transfer",
                },
                "gpu_pbd_transfer_pair": {
                    "status": "qualified",
                    "particle_count": 580,
                },
            }
        ),
        encoding="utf-8",
    )
    state = tmp_path / "dynamic_loaded_particle_state.json"
    state.write_text(
        json.dumps(
            {
                "schema_version": "aan.gpu_pbd_source_local_particle_state.v1",
                "coordinate_space": "source_entry_root_local",
                "particle_count": 580,
                "positions": [[0.0, 0.0, 0.02]] * 580,
            }
        ),
        encoding="utf-8",
    )
    module = _module()
    contract = tmp_path / "dynamic_loaded_start_contract.json"
    contract.write_text(
        json.dumps(
            {
                "schema_version": "aan.gpu_pbd_dynamic_loaded_start.v1",
                "support_plane_z_m": 0.0,
                "support_plane_to_entry_root": {
                    "xyz_m": [0.25, 0.0, -0.0069],
                    "wxyz": [1.0, 0.0, 0.0, 0.0],
                },
                "particle_state": state.name,
                "particle_state_sha256": module._sha(state),
                "particle_count": 580,
                "qualification": {
                    "required_cold_runs": 3,
                    "maximum_outside_source_before_lift": 2,
                    "maximum_entry_root_tail_drift_m": 0.001,
                    "maximum_entry_root_tilt_deg": 2.0,
                },
            }
        ),
        encoding="utf-8",
    )
    report = tmp_path / "dynamic_loaded_start_report.json"
    run = {
        "overall_status": "pass",
        "particle_count": 580,
        "maximum_outside_source_count": 1,
        "entry_root_tail_drift_m": 0.0004,
        "maximum_entry_root_tilt_deg": 0.3,
        "hard_runtime_errors": [],
    }
    report.write_text(
        json.dumps(
            {
                "schema_version": "aan.gpu_pbd_dynamic_loaded_start_report.v1",
                "overall_status": "pass",
                "contract_sha256": module._sha(contract),
                "particle_state_sha256": module._sha(state),
                "cold_runs": [dict(run, run_index=index) for index in range(1, 4)],
                "promotion": {
                    "allowed": True,
                    "claim": "gpu_pbd_dynamic_loaded_start",
                },
            }
        ),
        encoding="utf-8",
    )
    return package, contract, state, report


def test_binds_dynamic_loaded_start_to_a_new_immutable_package(tmp_path: Path) -> None:
    module = _module()
    package, contract, state, report = _delivery(tmp_path)

    promoted = module.promote(
        package=package,
        contract_path=contract,
        particle_state_path=state,
        report_path=report,
        output=tmp_path / "promoted",
        package_id="task02.r5",
    )

    manifest = json.loads((promoted / "evidence/manifest.json").read_text())
    binding = manifest["gpu_pbd_dynamic_loaded_start"]
    assert manifest["package_id"] == "task02.r5"
    assert binding["status"] == "qualified"
    assert binding["particle_count"] == 580
    assert binding["cold_runs"] == 3
    assert binding["maximum_outside_source_before_lift"] == 2
    assert (promoted / binding["contract"]).is_file()
    assert (promoted / binding["particle_state"]).is_file()
    assert (promoted / binding["report"]).is_file()
    assert json.loads((package / "evidence/manifest.json").read_text())["package_id"] == "task02.r4"


def test_rejects_a_cold_run_with_more_than_two_outside_particles(
    tmp_path: Path,
) -> None:
    module = _module()
    package, contract, state, report_path = _delivery(tmp_path)
    report = json.loads(report_path.read_text())
    report["cold_runs"][1]["maximum_outside_source_count"] = 3
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="cold run"):
        module.promote(
            package=package,
            contract_path=contract,
            particle_state_path=state,
            report_path=report_path,
            output=tmp_path / "promoted",
            package_id="task02.r5",
        )


def test_rejects_unbound_particle_state(tmp_path: Path) -> None:
    module = _module()
    package, contract, state, report = _delivery(tmp_path)
    state.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="particle state hash"):
        module.promote(
            package=package,
            contract_path=contract,
            particle_state_path=state,
            report_path=report,
            output=tmp_path / "promoted",
            package_id="task02.r5",
        )
