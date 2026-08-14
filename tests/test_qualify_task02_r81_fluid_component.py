from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/qualify_task02_r81_fluid_component.py"
)
SWEEP_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts/run_task02_r81_stage_update_sweep.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location("qualify_task02_r81", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sweep_module() -> object:
    spec = importlib.util.spec_from_file_location("sweep_task02_r81", SWEEP_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_classifier_distinguishes_source_target_spill_and_below() -> None:
    import numpy as np

    module = _module()
    source_matrix = np.eye(4)
    source_matrix[3, :3] = [0.16, -0.15, 0.0]
    positions = np.asarray(
        [
            [0.16, -0.15, 0.02],
            [-0.16, -0.17, 0.03],
            [0.4, 0.0, 0.01],
            [0.0, 0.0, -0.01],
        ]
    )

    score = module._classify(positions, source_matrix, np)

    assert score == {
        "source": 1,
        "target": 1,
        "below_support": 1,
        "tabletop_spill": 1,
        "particle_count": 4,
    }


def test_stage_probe_classifies_candidate_timeout_after_partial_updates() -> None:
    module = _sweep_module()

    observation = module.classify_probe(
        returncode=124,
        stdout=(
            "APP_READY_SECONDS=19.25\n"
            "OPEN_RETURN_SECONDS=0.24\n"
            "UPDATE_01_SECONDS=1.20\n"
        ),
        elapsed_seconds=45.01,
        timeout_seconds=45.0,
    )

    assert observation["status"] == "blocked_update_timeout"
    assert observation["timings"]["open_return_seconds"] == 0.24
    assert observation["completed_update_count"] == 1


def test_stage_probe_accepts_five_completed_updates() -> None:
    module = _sweep_module()

    observation = module.classify_probe(
        returncode=-6,
        stdout=(
            "APP_READY_SECONDS=19.25\n"
            "OPEN_RETURN_SECONDS=0.24\n"
            "UPDATE_01_SECONDS=1.75\n"
            "UPDATE_02_SECONDS=0.02\n"
            "UPDATE_03_SECONDS=0.02\n"
            "UPDATE_04_SECONDS=0.02\n"
            "UPDATE_05_SECONDS=0.02\n"
        ),
        elapsed_seconds=21.5,
        timeout_seconds=45.0,
    )

    assert observation["status"] == "five_updates_completed"
    assert observation["completed_update_count"] == 5


def test_stage_probe_does_not_call_partial_fast_run_a_pass() -> None:
    module = _sweep_module()

    observation = module.classify_probe(
        returncode=0,
        stdout=(
            "APP_READY_SECONDS=11.00\n"
            "OPEN_RETURN_SECONDS=0.25\n"
            "UPDATE_01_SECONDS=1.20\n"
        ),
        elapsed_seconds=12.5,
        timeout_seconds=45.0,
    )

    assert observation["status"] == "blocked_runtime"


def test_observation_is_persisted_before_runtime_teardown(tmp_path: Path) -> None:
    module = _module()
    target = tmp_path / "evidence" / "observation.json"

    module._write_observation(target, {"overall_status": "blocked"})

    assert json.loads(target.read_text()) == {"overall_status": "blocked"}


def test_gpu_particle_disable_error_is_a_hard_runtime_error() -> None:
    module = _module()

    errors = module._hard_runtime_errors(
        "Particles feature is only supported on GPU. Please enable GPU dynamics flag"
    )

    assert len(errors) == 1


def test_qualifier_binds_world_to_authored_gpu_physics_scene() -> None:
    text = SCRIPT.read_text()

    assert 'physics_prim_path="/World/PhysicsScene"' in text
    assert "set_defaults=False" in text
    assert "overwrite_gpu_setting(1)" in text
