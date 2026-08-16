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
    particle_count: int = 2,
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
        json.dumps([[0.0, 0.0, 0.01] for _ in range(particle_count)]),
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


def test_visible_fill_recipe_falls_back_from_0812_without_changing_r84_parameters(
    tmp_path: Path,
) -> None:
    module = _module()
    source = _package(
        tmp_path / "source",
        entry_prim="/World/GraduatedCylinder250ml",
        cavity={
            "center_xy_m": [0.0, 0.0],
            "radius_m": 0.0165,
            "floor_z_m": 0.016,
            "rim_z_m": 0.27824,
            "support_z_m": 0.0099,
        },
        particle_contact_offset_m=0.0015,
        particle_count=548,
    )
    profile = json.loads(
        (source / "gpu_pbd_static_container_profile.json").read_text()
    )
    profile["collision"] = {"contact_offset_m": 0.005}
    (source / "gpu_pbd_static_container_profile.json").write_text(
        json.dumps(profile), encoding="utf-8"
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
        particle_contact_offset_m=0.005,
    )

    result = module.build_fixture(
        source_package=source,
        target_package=target,
        output=tmp_path / "out",
        target_settled_fill_ratio=0.4,
        initial_packing_fill_ratio=0.75,
    )

    assert result["particle_count"] > 12000
    component = (tmp_path / "out/component.usda").read_text()
    assert "particleContactOffset = 0.0015" in component
    assert "color3f inputs:diffuseColor = (0.32, 0.72, 0.95)" in component
    assert "float inputs:opacity = 0.34" in component
    assert "float inputs:roughness = 0.02" in component
    profile = json.loads((tmp_path / "out/transfer_fixture_profile.json").read_text())
    assert profile["schema_version"] == "aan.gpu_pbd_transfer_fixture.v2"
    selection = profile["liquid_parameters"]["particle_parameter_selection"]
    assert selection["selected_baseline"] == "task02_r84"
    assert selection["attempts"][0]["baseline"] == "labutopia_0812_exact"
    assert selection["attempts"][0]["status"] == "not_applicable"
    assert profile["liquid_parameters"]["target_settled_fill_ratio"] == 0.4
    assert profile["liquid_parameters"]["settled_fill_ratio_tolerance"] == 0.05
    assert profile["liquid_parameters"]["initial_packing_fill_ratio"] == 0.75
    assert profile["qualification"]["target_mean_rtx_fps"] == 30.0
    assert profile["qualification"]["minimum_mean_rtx_fps"] == 20.0


def test_visible_fill_can_reuse_pre_settled_world_space_particle_state(
    tmp_path: Path,
) -> None:
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
        particle_count=2,
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
    )
    state = tmp_path / "settled.json"
    state.write_text(
        json.dumps(
            {
                "schema_version": "aan.gpu_pbd_settled_particle_state.v1",
                "coordinate_space": "world",
                "particle_count": 3,
                "positions": [
                    [0.25, 0.0, 0.02],
                    [0.251, 0.0, 0.02],
                    [0.25, 0.001, 0.02],
                ],
                "source_pose": {
                    "xyz_m": [0.25, 0.0, 0.0],
                    "wxyz": [1.0, 0.0, 0.0, 0.0],
                },
            }
        ),
        encoding="utf-8",
    )

    result = module.build_fixture(
        source_package=source,
        target_package=target,
        output=tmp_path / "out",
        target_settled_fill_ratio=0.4,
        initial_packing_fill_ratio=0.98,
        pre_settled_particle_state=state,
    )

    assert result["particle_count"] == 3
    profile = json.loads((tmp_path / "out/transfer_fixture_profile.json").read_text())
    liquid = profile["liquid_parameters"]
    assert liquid["initial_state_kind"] == "pre_settled_world_space"
    assert liquid["pre_settled_source_sha256"] == module._sha(state)
    authored = json.loads((tmp_path / "out/initial_particle_state.json").read_text())
    assert authored[0] == [0.25, 0.0, 0.02]
