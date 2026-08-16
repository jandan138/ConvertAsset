from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/qualify_gpu_pbd_dynamic_loaded_start.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location(
        "qualify_gpu_pbd_dynamic_loaded_start", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cold_run_gate_is_strict_and_uses_all_required_limits() -> None:
    module = _module()
    thresholds = {
        "particle_count": 580,
        "maximum_outside_source_before_lift": 2,
        "maximum_entry_root_tail_drift_m": 0.001,
        "maximum_entry_root_tilt_deg": 2.0,
    }
    passing = {
        "particle_count": 580,
        "maximum_outside_source_count": 2,
        "entry_root_tail_drift_m": 0.001,
        "maximum_entry_root_tilt_deg": 2.0,
        "hard_runtime_errors": [],
    }
    failing = dict(passing, maximum_outside_source_count=3)

    assert module.cold_run_checks(passing, thresholds=thresholds) == {
        "particle_count": True,
        "outside_source": True,
        "entry_root_tail_drift": True,
        "entry_root_tilt": True,
        "runtime_errors": True,
    }
    assert module.cold_run_passes(passing, thresholds=thresholds) is True
    assert module.cold_run_passes(failing, thresholds=thresholds) is False


def test_contract_keeps_pose_and_particles_as_separate_bound_artifacts() -> None:
    module = _module()
    contract = module.dynamic_loaded_start_contract(
        support_plane_z_m=0.755,
        stable_pose={"xyz_m": [0.25, 0.0, 0.7481], "wxyz": [1, 0, 0, 0]},
        particle_state_name="dynamic_loaded_particle_state.json",
        particle_state_sha256="abc",
        particle_count=580,
    )

    assert contract["schema_version"] == "aan.gpu_pbd_dynamic_loaded_start.v1"
    assert contract["support_plane_to_entry_root"]["xyz_m"] == [
        0.25,
        0.0,
        -0.006900000000000017,
    ]
    assert contract["particle_state_sha256"] == "abc"
    assert contract["qualification"]["maximum_outside_source_before_lift"] == 2
    assert contract["claim_boundary"].startswith("Dynamic loaded-start initialization")
