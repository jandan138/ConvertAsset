from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_stage_update_admission.py"


def _module():
    spec = importlib.util.spec_from_file_location("run_stage_update_admission", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_report_promotes_only_when_every_cold_run_completes() -> None:
    module = _module()
    passed = [{"status": "five_updates_completed"}] * 3
    failed = [*passed[:2], {"status": "blocked_update_timeout"}]

    assert module.build_report(passed, required_runs=3)["promotion"]["allowed"] is True
    assert module.build_report(failed, required_runs=3)["promotion"]["allowed"] is False


def test_generic_scene_without_component_has_empty_dependency_map(
    tmp_path: Path,
) -> None:
    sweep_script = SCRIPT.with_name("run_task02_r81_stage_update_sweep.py")
    spec = importlib.util.spec_from_file_location("task02_sweep", sweep_script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scene = tmp_path / "asset.usd"
    scene.write_text("#usda 1.0\n")

    assert module._scene_dependency_sha256(scene) == {}
