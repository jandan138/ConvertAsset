from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts/finalize_task02_r82_admission.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location("finalize_task02_r82", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_gpu_cooking_failure_blocks_promotion_and_updates_manifest(
    tmp_path: Path,
) -> None:
    module = _module()
    package = tmp_path / "package"
    stage = package / "evidence/stage/report.json"
    runtime = package / "evidence/runtime/observation.json"
    _write(stage, {"overall_status": "pass", "required_cold_runs": 3})
    _write(
        runtime,
        {
            "overall_status": "blocked",
            "checks": {"gpu_cooking": False, "performance": True},
            "hard_runtime_errors": ["Non-GPU-compatible convex mesh"],
        },
    )
    _write(
        package / "evidence/manifest.json",
        {"claims": {"physics_package_candidate": True}},
    )

    result = module.finalize(
        package=package, stage_report=stage, runtime_observation=runtime
    )

    manifest = json.loads((package / "evidence/manifest.json").read_text())
    assert result["overall_status"] == "blocked"
    assert result["promotion"]["allowed"] is False
    assert (
        "visible_mesh_convex_decomposition_not_gpu_particle_compatible"
        in (result["blocked_reasons"])
    )
    assert manifest["claims"]["physics_package_candidate"] is False
