from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/promote_gpu_pbd_static_container.py"


def _module():
    spec = importlib.util.spec_from_file_location("promote_gpu_pbd", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_promotes_only_three_cold_run_static_claim(tmp_path: Path) -> None:
    module = _module()
    candidate = tmp_path / "candidate"
    (candidate / "evidence").mkdir(parents=True)
    (candidate / "asset.usd").write_text("#usda 1.0\n")
    (candidate / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps({"role": "gpu_pbd_static_container", "promotion": {"status": "candidate"}})
    )
    (candidate / "evidence/manifest.json").write_text(
        json.dumps({"overall_status": "candidate", "gpu_pbd_static_container": {}})
    )
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    (fixture / "fixture_profile.json").write_text(json.dumps({"particle_count": 548}))
    (fixture / "authored_particle_points.json").write_text(json.dumps([[0, 0, 0]]))
    report = tmp_path / "report.json"
    run = {
        "overall_status": "pass",
        "particle_readback_attribute": "points",
        "resolved_particle_semantics": {"fluid": True, "self_collision": True},
        "static_hold": {"minimum_inside_ratio": 1.0, "maximum_below_support": 0},
        "performance": {"mean_rtx_fps": 80.0},
        "hard_runtime_errors": [],
    }
    report.write_text(
        json.dumps({"overall_status": "pass", "required_cold_runs": 3, "runs": [run, run, run]})
    )
    visual = tmp_path / "visual.png"
    visual.write_bytes(b"png")

    result = module.promote(
        candidate_package=candidate,
        fixture=fixture,
        qualification_report=report,
        visual_evidence=[visual],
        output=tmp_path / "final",
    )

    assert result["overall_status"] == "pass"
    manifest = json.loads((tmp_path / "final/evidence/manifest.json").read_text())
    assert manifest["promotion"]["allowed"] is True
    assert manifest["gpu_pbd_static_container"]["status"] == "qualified"
    profile = json.loads((tmp_path / "final/gpu_pbd_static_container_profile.json").read_text())
    assert profile["promotion"]["status"] == "qualified"
    assert profile["claim"] == "gpu_pbd_static_container"


def test_rejects_less_than_three_runs(tmp_path: Path) -> None:
    module = _module()
    report = {"overall_status": "pass", "required_cold_runs": 1, "runs": []}
    try:
        module.validate_report(report)
    except ValueError as exc:
        assert "three cold" in str(exc)
    else:
        raise AssertionError("expected report rejection")


def test_rejects_rest_state_particle_readback() -> None:
    module = _module()
    run = {
        "overall_status": "pass",
        "particle_readback_attribute": "physxParticle:simulationPoints",
        "resolved_particle_semantics": {"fluid": True, "self_collision": True},
        "static_hold": {"minimum_inside_ratio": 1.0, "maximum_below_support": 0},
        "performance": {"mean_rtx_fps": 80.0},
        "hard_runtime_errors": [],
    }
    report = {
        "overall_status": "pass",
        "required_cold_runs": 3,
        "runs": [run, run, run],
    }

    try:
        module.validate_report(report)
    except ValueError as exc:
        assert "cold run 1" in str(exc)
    else:
        raise AssertionError("expected rest-state readback rejection")
