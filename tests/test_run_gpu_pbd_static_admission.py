from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts/run_gpu_pbd_static_admission.py"
)


def _module():
    spec = importlib.util.spec_from_file_location("run_gpu_pbd_static", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_requires_three_passing_cold_runs() -> None:
    module = _module()
    passing = {
        "overall_status": "pass",
        "qualification_tier": "final",
        "static_hold": {"minimum_inside_ratio": 0.98},
        "performance": {"mean_rtx_fps": 45.0},
        "hard_runtime_errors": [],
    }

    report = module.build_report([passing, passing, passing], required_runs=3)

    assert report["overall_status"] == "pass"
    assert report["promotion"]["allowed"] is True
    blocked = module.build_report(
        [passing, {**passing, "overall_status": "blocked"}], required_runs=3
    )
    assert blocked["overall_status"] == "blocked"
    assert blocked["promotion"]["allowed"] is False


def test_records_candidate_without_allowing_promotion() -> None:
    module = _module()
    candidate = {
        "overall_status": "pass",
        "qualification_tier": "candidate",
        "static_hold": {"minimum_inside_ratio": 0.91},
        "performance": {"mean_rtx_fps": 45.0},
        "hard_runtime_errors": [],
    }

    report = module.build_report([candidate] * 3, required_runs=3)

    assert report["overall_status"] == "candidate"
    assert report["promotion"]["allowed"] is False
    assert report["promotion"]["reason"] == "candidate_retention_only"


def test_parent_log_scan_blocks_gpu_cooking_warning() -> None:
    module = _module()
    observation = {
        "overall_status": "pass",
        "checks": {"gpu_cooking": True, "static_retention": True},
        "hard_runtime_errors": [],
    }

    merged = module.merge_process_runtime_errors(
        observation,
        "ConvexMeshCookingTask: failed to cook GPU-compatible mesh",
    )

    assert merged["overall_status"] == "blocked"
    assert merged["checks"]["gpu_cooking"] is False
    assert merged["hard_runtime_errors"]
