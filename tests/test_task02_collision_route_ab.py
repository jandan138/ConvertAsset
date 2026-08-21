from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.compare_task02_graduated_cylinder_collision_routes import (
    ROUTES,
    author_variant_overlay,
    evaluate_static_runs,
)
from scripts.observe_task02_vertical_lift import trajectory_height
from scripts.qualify_task02_collision_vertical_lift import evaluate_lift_runs


def _fixture(path: Path) -> Path:
    from pxr import Usd, UsdGeom

    stage = Usd.Stage.CreateNew(str(path))
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    for prim_path in (
        "/World/Transfer/Source/Visual/Source/Hollow_Body/Hollow_Body_Mesh_002",
        "/World/Transfer/Source/Visual/Source/Thickened_Rim/Torus_002",
        "/World/Transfer/Source/Visual/Source/Closed_Inner_Bottom/Cylinder_006",
        "/World/Transfer/Source/Visual/Source/Hex_Base/Cylinder_004",
        "/World/Transfer/Source/Visual/Source/Base_Connector/Cylinder_005",
        "/World/Transfer/Source/Visual/Source/Pour_Spout/Pour_Spout_Mesh_002",
        "/World/Transfer/Source/__aan_pbd_collision_proxy/PBD_Unified_Vessel_Mesh",
    ):
        UsdGeom.Mesh.Define(stage, prim_path)
    stage.GetRootLayer().Save()
    return path


@pytest.mark.parametrize("route", sorted(ROUTES))
def test_variant_overlay_only_changes_declared_collision_route(
    tmp_path: Path, route: str
) -> None:
    scene = _fixture(tmp_path / "fixture.usda")
    overlay = tmp_path / f"{route}.usda"

    evidence = author_variant_overlay(scene=scene, output=overlay, route=route)

    text = overlay.read_text()
    assert evidence["route"] == route
    if route == "qualified_unified_proxy_control":
        assert "PBD_Unified_Vessel_Mesh" not in text
    else:
        assert "PBD_Unified_Vessel_Mesh" in text
        assert "active = false" in text
        assert "Hollow_Body_Mesh_002" in text
    if route == "visual_components_sdf":
        assert 'physics:approximation = "sdf"' in text
    if route == "visual_mesh_direct_convex":
        assert 'physics:approximation = "convexDecomposition"' in text
        assert "physxConvexDecompositionCollision:voxelResolution = 500000" in text


def test_static_gate_is_fail_closed_per_run() -> None:
    passing = {
        "particle_count": 580,
        "outside_source_count": 2,
        "below_source_floor_count": 0,
        "settled_fill_ratio": 0.4,
        "hard_runtime_errors": [],
    }
    failing = dict(passing, outside_source_count=3)

    assert evaluate_static_runs([passing, passing, passing])["overall_status"] == "pass"
    result = evaluate_static_runs([passing, failing, passing])
    assert result["overall_status"] == "blocked"
    assert result["blocked_reasons"] == ["run_2:outside_source_above_2"]


def test_static_gate_accepts_valid_evidence_even_after_teardown_exit() -> None:
    run = {
        "particle_count": 580,
        "outside_source_count": 0,
        "below_source_floor_count": 0,
        "settled_fill_ratio": 0.39,
        "hard_runtime_errors": [],
        "worker_process_exit_code": -6,
    }

    assert evaluate_static_runs([run, run, run])["overall_status"] == "pass"


def test_fixture_profile_is_json_serializable() -> None:
    assert json.loads(json.dumps(ROUTES))["visual_components_sdf"]["cavity_radius_m"] == pytest.approx(
        0.019185
    )


def test_vertical_lift_trajectory_has_the_locked_five_phases() -> None:
    assert trajectory_height(0) == 0.0
    assert trajectory_height(300) == pytest.approx(0.05)
    assert trajectory_height(480) == pytest.approx(0.10)
    assert trajectory_height(660) == pytest.approx(0.05)
    assert trajectory_height(800) == 0.0


def test_lift_gate_requires_three_passing_runs() -> None:
    run = {
        "overall_status": "pass",
        "maximum_outside_source_count": 0,
        "maximum_below_source_floor_count": 0,
        "maximum_root_tracking_error_m": 0.0,
    }

    assert evaluate_lift_runs([run, run, run])["overall_status"] == "pass"
    assert evaluate_lift_runs([run, run])["overall_status"] == "blocked"
