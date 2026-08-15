from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts/build_gpu_pbd_transfer_fixture.py"
)


def _module() -> object:
    spec = importlib.util.spec_from_file_location(
        "build_gpu_pbd_transfer_fixture", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _package(
    root: Path,
    *,
    entry_prim: str,
    cavity: dict[str, float],
    particle_contact_offset_m: float = 0.005,
) -> Path:
    root.mkdir(parents=True)
    (root / "asset.usd").write_text("usd", encoding="utf-8")
    (root / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(
            {
                "schema_version": "aan.gpu_pbd_static_container_profile.v1",
                "role": "gpu_pbd_static_container",
                "claim": "gpu_pbd_static_container",
                "entrypoint": "asset.usd",
                "entry_prim": entry_prim,
                "cavity": cavity,
                "promotion": {
                    "status": "qualified",
                    "fixture": "evidence/gpu_pbd_static_fixture.json",
                    "initial_particle_state": "evidence/gpu_pbd_initial_particle_state.json",
                },
            }
        ),
        encoding="utf-8",
    )
    evidence = root / "evidence"
    evidence.mkdir()
    (evidence / "gpu_pbd_initial_particle_state.json").write_text(
        json.dumps([[0.0, 0.0, 0.01], [0.001, 0.0, 0.01]]),
        encoding="utf-8",
    )
    (evidence / "gpu_pbd_static_fixture.json").write_text(
        json.dumps(
            {
                "particle_parameters": {
                    "particle_contact_offset_m": particle_contact_offset_m
                }
            }
        ),
        encoding="utf-8",
    )
    return root


def test_builds_fixed_target_kinematic_source_fixture(tmp_path: Path) -> None:
    module = _module()
    source = _package(
        tmp_path / "source",
        entry_prim="/World/GraduatedCylinder250ml",
        cavity={
            "center_xy_m": [0.0, 0.0],
            "radius_m": 0.019185,
            "floor_z_m": 0.011705,
            "rim_z_m": 0.27824,
            "support_z_m": 0.0,
        },
    )
    target = _package(
        tmp_path / "target",
        entry_prim="/World/Beaker325ml",
        cavity={
            "center_xy_m": [0.0, 0.0],
            "radius_m": 0.03527,
            "floor_z_m": 0.003,
            "rim_z_m": 0.11509,
            "support_z_m": 0.0,
        },
        particle_contact_offset_m=0.0015,
    )

    result = module.build_fixture(
        source_package=source,
        target_package=target,
        output=tmp_path / "out",
    )

    assert result["particle_count"] == 2
    component = (tmp_path / "out/component.usda").read_text()
    assert (
        "prepend references = @deps/source/asset.usd@</World/GraduatedCylinder250ml>"
        in component
    )
    assert (
        "prepend references = @deps/target/asset.usd@</World/Beaker325ml>" in component
    )
    assert component.count("bool physics:kinematicEnabled = 1") == 2
    assert "particleContactOffset = 0.0015" in component
    profile = json.loads((tmp_path / "out/transfer_fixture_profile.json").read_text())
    assert profile["target_actor_mode"] == "fixed_kinematic_rigid_body"
    assert profile["source_actor_mode"] == "prescribed_kinematic_trajectory"
    assert (
        profile["liquid_parameters"]["source"]
        == "LabUtopia inputs/usd/scene/liquid_0812/test.usd"
    )
    assert len(profile["bounded_search"]["candidates"]) == 4
    assert profile["qualification"]["minimum_target_reception_ratio"] == 0.5
    assert profile["qualification"]["spill_is_blocking"] is False
    assert profile["liquid_parameters"]["particle_contact_offset_m"] == 0.0015
    assert profile["trajectory_protocol"]["lift_seconds"] == 2.0
    assert profile["trajectory_protocol"]["physics_hz"] == 120
    assert profile["trajectory_protocol"]["high_root_z_m"] == 0.2
    assert profile["trajectory_protocol"]["lateral_approach_seconds"] == 2.0
    assert profile["trajectory_protocol"]["pretilt_degrees"] == -20.0
