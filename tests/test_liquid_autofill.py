from __future__ import annotations

import json
from pathlib import Path

import pytest

from convert_asset.liquid_autofill import (
    AUTOFILL_RECIPE_ID,
    LiquidAutofillError,
    build_particle_lattice,
    build_request,
    recipe_payload,
    settled_fill_ratio,
    validate_request,
)
from convert_asset.liquid_autofill_runtime import (
    _mesh_cavity_candidate,
    analyze_container,
    build_autofill_candidate,
)


def test_task02_r103_recipe_is_versioned_and_exact() -> None:
    recipe = recipe_payload()

    assert recipe["recipe_id"] == AUTOFILL_RECIPE_ID
    assert recipe["particle_system"]["particle_contact_offset_m"] == 0.005
    assert recipe["particle_system"]["effective_rest_offset_m"] == 0.009
    assert recipe["particle_system"]["grid_smoothing_radius_m"] == 0.005
    assert recipe["particle_set"]["width_m"] == 0.00594
    assert recipe["particle_set"]["maximum_count"] == 10_000
    assert recipe["material"]["diffuse_color"] == [0.32, 0.72, 0.95]
    assert recipe["evidence"]["particle_readback_attribute"] == "points"


def test_request_rejects_fill_outside_supported_band(tmp_path: Path) -> None:
    scene = tmp_path / "scene.usd"
    scene.write_text("#usda 1.0\n", encoding="utf-8")
    request = build_request(scene=scene, container="/World/Beaker", fill=0.9)

    with pytest.raises(LiquidAutofillError, match="0.10 through 0.80"):
        validate_request(request)


def test_request_requires_absolute_prim_path(tmp_path: Path) -> None:
    scene = tmp_path / "scene.usd"
    scene.write_text("#usda 1.0\n", encoding="utf-8")
    request = build_request(scene=scene, container="World/Beaker", fill=0.4)

    with pytest.raises(LiquidAutofillError, match="absolute USD prim path"):
        validate_request(request)


def test_particle_lattice_targets_q95_height_and_is_deterministic() -> None:
    cavity = {
        "center_xy_m": [0.0, 0.0],
        "radius_x_m": 0.030,
        "radius_y_m": 0.025,
        "floor_m": 0.010,
        "rim_m": 0.210,
    }

    first = build_particle_lattice(cavity, fill=0.60)
    second = build_particle_lattice(cavity, fill=0.60)

    assert first == second
    assert 0 < len(first) < 10_000
    assert settled_fill_ratio(first, cavity) == pytest.approx(0.60, abs=0.01)
    assert min(point[2] for point in first) >= cavity["floor_m"]


def test_particle_lattice_blocks_the_fixed_budget() -> None:
    cavity = {
        "center_xy_m": [0.0, 0.0],
        "radius_x_m": 0.5,
        "radius_y_m": 0.5,
        "floor_m": 0.0,
        "rim_m": 1.0,
    }

    with pytest.raises(LiquidAutofillError, match="10,000"):
        build_particle_lattice(cavity, fill=0.8)


def test_two_ring_hollow_body_matches_the_task02_mesh_topology() -> None:
    import math

    points = [
        [radius * math.cos(index * math.tau / 96),
         radius * math.sin(index * math.tau / 96), z]
        for z in (0.0099, 0.27659)
        for radius in (0.019185, 0.02099)
        for index in range(96)
    ]

    cavity = _mesh_cavity_candidate(points, prim_path="/World/Vessel/Hollow_Body")

    assert cavity is not None
    assert cavity["radius_x_m"] == pytest.approx(0.019185, rel=0.02)
    assert cavity["floor_m"] > 0.0099
    assert cavity["rim_m"] < 0.27659


def test_request_document_is_json_serializable(tmp_path: Path) -> None:
    scene = tmp_path / "scene.usd"
    scene.write_text("#usda 1.0\n", encoding="utf-8")
    payload = build_request(scene=scene, container="/World/Beaker", fill=0.4)

    assert json.loads(json.dumps(payload))["schema_version"] == (
        "aan.gpu_pbd_autofill_request.v1"
    )


def _write_hollow_axial_fixture(path: Path) -> None:
    pxr = pytest.importorskip("pxr")
    del pxr
    from pxr import Gf, Usd, UsdGeom

    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.Xform.Define(stage, "/World/Beaker")
    mesh = UsdGeom.Mesh.Define(stage, "/World/Beaker/HollowBody")
    points = []
    for z in (0.0, 0.05, 0.10, 0.15, 0.20):
        for radius in (0.027, 0.030):
            for index in range(32):
                angle = 2.0 * 3.141592653589793 * index / 32
                points.append(
                    Gf.Vec3f(radius * __import__("math").cos(angle), radius * __import__("math").sin(angle), z)
                )
    mesh.GetPointsAttr().Set(points)
    mesh.GetFaceVertexCountsAttr().Set([])
    mesh.GetFaceVertexIndicesAttr().Set([])
    stage.GetRootLayer().Save()


def test_runtime_analysis_and_candidate_build_fail_closed_but_need_no_scene_patch(
    tmp_path: Path,
) -> None:
    scene = tmp_path / "scene.usda"
    _write_hollow_axial_fixture(scene)

    analysis = analyze_container(scene, "/World/Beaker")
    assert analysis["confidence"] == "high"
    assert analysis["cavity_candidate_count"] == 1
    assert analysis["cavity"]["radius_x_m"] == pytest.approx(0.027, rel=0.08)

    request = build_request(scene=scene, container="/World/Beaker", fill=0.4)
    package = tmp_path / "producer"
    result = build_autofill_candidate(request=request, output=package)

    assert result["overall_status"] == "candidate"
    assert result["qualification"] == {"status": "not_run"}
    initial_seed = json.loads((package / "initial_seed.json").read_text())
    assert initial_seed["state_semantics"] == "deterministic_pre_simulation_lattice"
    assert not (package / "settled_seed.json").exists()
    assert scene.read_text(encoding="utf-8").startswith("#usda")
    overlay = (package / "producer_overlay.usda").read_text(encoding="utf-8")
    assert "PhysxParticleSetAPI" in overlay
    assert "restOffset = 0.009" in overlay
    assert "gridSmoothingRadius = 0.005" in overlay
