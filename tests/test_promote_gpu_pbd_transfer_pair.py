from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/promote_gpu_pbd_transfer_pair.py"


def _module() -> object:
    spec = importlib.util.spec_from_file_location("promote_gpu_pbd_transfer_pair", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _delivery(tmp_path: Path, *, particle_count: int = 548) -> tuple[Path, Path]:
    fixture = tmp_path / "fixture"
    (fixture / "deps/source").mkdir(parents=True)
    (fixture / "deps/target").mkdir(parents=True)
    (fixture / "deps/source/asset.usd").write_text("source", encoding="utf-8")
    (fixture / "deps/target/asset.usd").write_text("target", encoding="utf-8")
    (fixture / "component.usda").write_text("component", encoding="utf-8")
    (fixture / "qualification.usda").write_text("qualification", encoding="utf-8")
    (fixture / "initial_particle_state.json").write_text("[]\n", encoding="utf-8")
    candidate = {
        "candidate_id": "c03",
        "dwell_seconds": 3.0,
        "rim_gap_m": 0.01,
        "rim_offset_x_m": 0.0,
        "tilt_deg": -115.0,
    }
    profile = {
        "schema_version": "aan.gpu_pbd_transfer_fixture.v1",
        "members": {
            "source": "/World/Transfer/Source",
            "target": "/World/Transfer/Target",
            "particles": "/World/Transfer/ParticleSet",
            "particle_system": "/World/Transfer/ParticleSystem",
        },
        "liquid_parameters": {"particle_count": particle_count},
        "qualification": {
            "minimum_target_reception_ratio": 0.5,
            "required_cold_runs": 3,
            "spill_is_blocking": False,
        },
        "bounded_search": {"candidates": [candidate]},
        "claim_boundary": "Prescribed transfer only; no robot or benchmark claim.",
    }
    profile_path = fixture / "transfer_fixture_profile.json"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    module = _module()
    cold = {
        "overall_status": "pass",
        "particle_readback_attribute": "points",
        "static_hold": {"minimum_source_ratio": 1.0},
        "pour": {
            "particle_count": particle_count,
            "target": int(particle_count * 0.95),
            "target_ratio": 0.95,
        },
        "performance": {"mean_rtx_fps": 80.0},
        "hard_runtime_errors": [],
    }
    report = {
        "schema_version": "aan.gpu_pbd_transfer_admission.v1",
        "overall_status": "pass",
        "selected_candidate": candidate,
        "cold_runs": [dict(cold, run_index=index) for index in range(1, 4)],
        "promotion": {"allowed": True, "claim": "gpu_pbd_prescribed_transfer_pair"},
        "fixture_profile_sha256": module._sha(profile_path),
        "claim_boundary": "Prescribed transfer only; no robot or benchmark claim.",
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return fixture, report_path


def test_promotes_self_contained_prescribed_transfer_pair(tmp_path: Path) -> None:
    module = _module()
    fixture, report = _delivery(tmp_path)

    package = module.promote(
        fixture=fixture,
        report_path=report,
        output=tmp_path / "package",
        package_id="task02-cylinder-to-beaker.gpu-pbd-transfer.r1",
    )

    manifest = json.loads((package / "evidence/manifest.json").read_text())
    assert manifest["overall_status"] == "pass"
    assert manifest["promotion"]["claim"] == "gpu_pbd_prescribed_transfer_pair"
    assert manifest["gpu_pbd_transfer_pair"]["cold_runs"] == 3
    assert manifest["gpu_pbd_transfer_pair"]["particle_count"] == 548
    assert (package / "component.usda").is_file()
    assert (package / "deps/source/asset.usd").is_file()
    assert (package / "deps/target/asset.usd").is_file()


def test_promotes_dynamic_particle_count_from_profile(tmp_path: Path) -> None:
    module = _module()
    fixture, report = _delivery(tmp_path, particle_count=6000)

    package = module.promote(
        fixture=fixture,
        report_path=report,
        output=tmp_path / "package",
        package_id="task02-cylinder-to-beaker.gpu-pbd-transfer.r2",
    )

    manifest = json.loads((package / "evidence/manifest.json").read_text())
    assert manifest["gpu_pbd_transfer_pair"]["particle_count"] == 6000


def test_rejects_transfer_pair_without_three_cold_passes(tmp_path: Path) -> None:
    module = _module()
    fixture, report_path = _delivery(tmp_path)
    report = json.loads(report_path.read_text())
    report["cold_runs"][0]["pour"]["target_ratio"] = 0.49
    report_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="cold run"):
        module.promote(
            fixture=fixture,
            report_path=report_path,
            output=tmp_path / "package",
            package_id="task02-cylinder-to-beaker.gpu-pbd-transfer.r1",
        )
